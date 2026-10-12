"""Paid-run orchestration tested with fake clients and no network access."""
import copy
import dataclasses
import json
import threading
import time

import pytest

from scripts import run_transport_extension as run
from scripts import analyse_transport_extension as analysis
from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall

ENTRY = 'The daily record is complete. I have checked the information available and will keep the stock and balance in mind when choosing the next actions.'


def profile(model='z-ai/glm-5.3-flash'):
    return {'model':model,'expected_provider':'Test','temperature':None,'provider':{},'reasoning':{'effort':'low'},
            'max_tokens':16384,'ceiling_rates':{'prompt':1e-6,'completion':1e-6}}


def test_selected_matrix_has_two_independent_prefix_realizations_and_no_fresh_seeds():
    jobs,smoke = run.selected_jobs({m:profile(m) for m in run.MODELS})
    assert len(smoke)==6
    assert len([j for j in jobs if j['kind']=='full'])==640
    groups = [j for j in jobs if j['kind']=='group']
    assert len(groups)==80 and sum(len(j['branches']) for j in groups)==320
    assert {j['spec']['model'] for j in jobs}==set(run.MODELS)
    assert {j['spec']['schedule_seed'] for j in jobs}==set(range(13,23))
    assert len({j['job_id'] for j in jobs})==len(jobs)
    assert {j['spec']['replicate'] for j in groups}=={1,2}
    assert all(j['spec']['replicate']==1 for j in jobs if j['arm'] not in ('baseline_frame','discrepancy'))


def raw():
    return {'provider':'Test','usage':{'cost':.001,'prompt_tokens':1,'completion_tokens':1},
        'choices':[{'finish_reason':'tool_calls','message':{'content':None,'tool_calls':[
            {'id':'end','function':{'name':'end_day','arguments':json.dumps({'reflection':ENTRY})}}]}}]}


def logged_fake_factory(fail_at=None):
    def factory(prof,path,key,stop):
        calls = 0
        def chat(messages,tools):
            nonlocal calls
            calls += 1
            request = {'messages':messages,'tools':tools}
            run.append(path,{'kind':'request','request_id':str(calls),'request':request})
            if calls==fail_at:
                run.append(path,{'kind':'error','request_id':str(calls),'error_type':'APIConnectionError'})
                raise run.Stop('simulated connection interruption')
            response = raw()
            run.append(path,{'kind':'response','request_id':str(calls),'response':response,'seconds':1})
            return run.audit.recorded_response(response)
        return chat
    return factory


@pytest.mark.parametrize('group',[False,True])
def test_recovery(tmp_path,group):
    profiles = {m:profile(m) for m in run.MODELS}
    jobs,_ = run.selected_jobs(profiles)
    job = copy.deepcopy(next(j for j in jobs if j['kind']==('group' if group else 'full')))
    job['spec']['condition']['richness']='static'
    if group:
        job['spec'].update(horizon=30,reveal_days=[2,4],observation_days=2)
        spec = run.parse_spec(job['spec'],True)
        job['job_id'] = spec.prefix_id
    else:
        job['spec']['horizon']=30
        spec = run.parse_spec(job['spec'])
        job['job_id']=job['run_id']=spec.run_id
    plan = {'profiles':profiles}
    run.write(tmp_path/'plan.json',plan)
    # Group failure occurs after its prefix and at least one completed branch.
    fail = 7 if group else 3
    with pytest.raises(run.Stop):
        run.execute_job(tmp_path,plan,job,'fake',threading.Event(),chat_factory=logged_fake_factory(fail))
    first = run.job_directory(tmp_path,job)/'attempt-1'
    first_hash = run.digest(first/'api_calls.jsonl')
    run.execute_job(tmp_path,plan,job,'fake',threading.Event(),resume=True,chat_factory=logged_fake_factory())
    complete = run.completed(tmp_path,job)
    assert complete.name=='attempt-2'
    assert run.digest(first/'api_calls.jsonl')==first_hash
    assert run.read(complete/'recovery.json')['saved_responses']==fail-1
    for path in (first/'data').rglob('days.jsonl'):
        old = run.rows(path)
        new = run.rows(complete/'data'/path.relative_to(first/'data'))
        assert old==new[:len(old)]
    def forbidden(*args): raise AssertionError('Completed jobs must not create another client')
    assert run.execute_job(tmp_path,plan,job,'fake',threading.Event(),chat_factory=forbidden)=='already complete'


def test_replay_stops_before_inference_if_request_changes():
    request={'messages':[{'role':'user','content':'original'}],'tools':[]}
    def forbidden(*args): raise AssertionError('No inference allowed')
    replay=run.ReplayingChat([(request,raw())],None,forbidden)
    with pytest.raises(run.Stop,match='mismatch'):
        replay([{'role':'user','content':'changed'}],[])


def test_replay_rejects_wrong_profile_and_truncated_output(tmp_path):
    settings={'profile':profile()}
    run.write(tmp_path/'settings.json',settings)
    response=raw(); response['choices'][0]['finish_reason']='length'
    run.append(tmp_path/'api_calls.jsonl',{'kind':'request','request_id':'1','request':{'messages':[],'tools':[]}})
    run.append(tmp_path/'api_calls.jsonl',{'kind':'response','request_id':'1','response':response})
    with pytest.raises(run.Stop): run.history(tmp_path,settings)
    with pytest.raises(run.Stop): run.history(tmp_path,{'profile':profile('other')})


def test_arm_selection_and_concurrency_limits(tmp_path,monkeypatch):
    jobs=[]
    for arm in ('baseline_frame','exploit'):
        for model in run.MODELS:
            for i in range(4): jobs.append({'arm':arm,'job_id':model.replace('/','_')+str(i),'spec':{'model':model}})
    plan={'jobs':jobs,'smoke_jobs':[],'max_workers':4,'per_model_workers':2}
    monkeypatch.setattr(run,'check',lambda root:plan)
    monkeypatch.setenv('OPENROUTER_API_KEY','test-only')
    active={m:0 for m in run.MODELS}; seen=[]; guard=threading.Lock()
    def execute(root,plan,job,*args):
        with guard:
            active[job['spec']['model']]+=1
            assert max(active.values())<=2 and sum(active.values())<=4
            seen.append(job['arm'])
        time.sleep(.02)
        with guard: active[job['spec']['model']]-=1
    monkeypatch.setattr(run,'execute_job',execute)
    run.run(tmp_path,'baseline_frame')
    assert seen==['baseline_frame']*8
    assert not (tmp_path/'running.lock').exists()


def test_exact_sign_flip_and_holm_account_for_cluster_count():
    stat=analysis.contrast_stats([1]*10)
    assert stat['n_schedules']==10 and stat['p_one_sided']==1/1024
    assert stat['ci95']==[1,1]
    assert analysis.contrast_stats([0]*10)['p_one_sided']==1
    adjusted=analysis.holm({'a':.01,'b':.02,'c':.2,'d':.8})
    assert adjusted=={'a':.04,'b':.06,'c':.4,'d':.8}


def test_discrepancy_averages_within_ten_clusters_not_160_branches():
    records=[]
    for seed in range(13,23):
        for replicate in (1,2):
            for frame in ('fantasy','neutral'):
                for reveal in (2,46):
                    for kind in ('extra_stock','missing_stock'):
                        records.append({'model':'test','seed':seed,'replicate':replicate,'frame':frame,
                                        'reveal_day':reveal,'kind':kind,'final_code':int(kind=='missing_stock'), 'ambiguous':False})
    stat=analysis.discrepancy_estimates(records,{'models':['test']})['test']['estimates']['contact_valence']
    assert stat['n_schedules']==10 and stat['mean']==1
    records[0]['final_code']=None
    result=analysis.discrepancy_estimates(records,{'models':['test']})['test']
    assert result['omitted_schedules']==[13] and result['estimates']['contact_valence']['n_schedules']==9


def test_measured_client_logs_transient_attempts_and_preserves_unknown_billing(tmp_path,monkeypatch):
    APIConnectionError = type('APIConnectionError',(Exception,),{})
    attempts=[]
    def factory(*args,**kwargs):
        assert kwargs['max_retries']==0 and kwargs['strict']
        def client(messages,tools):
            attempts.append(1)
            kwargs['before_request']({'messages':messages,'tools':tools})
            if len(attempts)==1: raise APIConnectionError('offline test')
            response=raw()
            kwargs['on_response'](response)
            return run.audit.recorded_response(response)
        return client
    monkeypatch.setattr(run,'openai_chat_client',factory)
    class NoWait:
        def is_set(self): return False
        def wait(self,seconds): return False
    path=tmp_path/'api_calls.jsonl'
    chat=run.measured_chat(profile(),path,'fake',NoWait())
    chat([{'role':'system','content':'test'},{'role':'user','content':'=== DAY 46 of 90 ==='}],[])
    events=run.rows(path)
    assert [e['kind'] for e in events]==['request','error','request','response']
    assert [e['day'] for e in events if e['kind']=='request']==[46,46]
    charges=run.audit.Budget(tmp_path,None)
    assert len(charges.charges)==2 and charges.spent>.001


def test_completed_checks_required_before_main_arm(tmp_path,monkeypatch):
    job={'arm':'smoke','job_id':'missing','spec':{'model':'test'}}
    monkeypatch.setattr(run,'check',lambda root:{'max_workers':4,'jobs':[],'smoke_jobs':[job]})
    with pytest.raises(run.Stop,match='First run smoke'):
        run.run(tmp_path,'baseline_frame')


def test_frozen_artifact_change_is_detected(tmp_path,monkeypatch):
    artifact=tmp_path/'pack.yml'; artifact.write_text('original')
    monkeypatch.setattr(run,'source_hashes',lambda:{'source':'abc'})
    monkeypatch.setattr(run.audit,'runtime_versions',lambda:{'runtime':'test'})
    plan={'source_hashes':{'source':'abc'},'runtime':{'runtime':'test'},'artifact_hashes':{'pack.yml':run.digest(artifact)}}
    run.write(tmp_path/'plan.json',plan)
    (tmp_path/'plan.sha256').write_text(run.digest(tmp_path/'plan.json'))
    assert run.check(tmp_path)==plan
    artifact.write_text('changed')
    with pytest.raises(run.Stop,match='Frozen artifact'):
        run.check(tmp_path)
