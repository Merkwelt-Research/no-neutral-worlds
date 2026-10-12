"""No-network checks for routing transitions, exact replay and billed retries."""
import copy
import json
import threading
from types import SimpleNamespace

import pytest

from scripts import run_transport_extension as run
from scripts import resume_transport_reviewed as recovery
from scripts import transport_provider_fallback as routing
from tests.test_transport_runner import ENTRY


def profiles():
    old = {'model':'meta/muse-glimmer-30b', 'expected_provider':'Phala',
           'provider':{'only':['phala'],'allow_fallbacks':False,'require_parameters':True},
           'temperature':.7,'reasoning':{'effort':'low'},'max_tokens':16384,
           'ceiling_rates':{'prompt':.3e-6,'completion':1.1e-6}}
    new = copy.deepcopy(old)
    new.pop('expected_provider')
    new.update(allowed_providers=['DeepInfra','Phala','Fireworks','Together'],
               provider={'only':['deepinfra/bf16','phala','fireworks','together'],
                         'order':['deepinfra/bf16','phala','fireworks','together'],
                         'allow_fallbacks':True,'require_parameters':True,
                         'max_price':{'prompt':.35,'completion':1.5}},
               ceiling_rates={'prompt':.35e-6,'completion':1.5e-6},
               routing_policy_id='test')
    return old,new,{'profiles':{old['model']:{'original':old,'amended':new}}}


def request(profile, messages=None, tools=None):
    return {'model':profile['model'], 'messages':messages or [], 'tools':tools or [],
            'temperature':profile['temperature'],'max_tokens':profile['max_tokens'],
            'tool_choice':'auto','extra_body':{'provider':profile['provider'],'reasoning':profile['reasoning']}}


def response(provider='DeepInfra'):
    return {'provider':provider,'model':'meta/muse-glimmer-30b','usage':{'cost':.001},
            'choices':[{'finish_reason':'tool_calls','message':{'content':None,'tool_calls':[
                {'id':'end','function':{'name':'end_day','arguments':json.dumps({'reflection':ENTRY})}}]}}]}


@pytest.mark.parametrize('mutation',['provider','model','cost','truncation'])
def test_routing_does_not_relax_other_response_checks(mutation):
    old,new,_=profiles();raw=response()
    assert routing.valid_response(raw,new)
    assert not routing.valid_response(raw,old)
    if mutation=='provider':raw['provider']='Unapproved'
    elif mutation=='model':raw['model']='another/model'
    elif mutation=='cost':raw['usage']['cost']=None
    else:raw['choices'][0]['finish_reason']='length'
    assert not routing.valid_response(raw,new)


def test_only_documented_routing_difference_is_allowed():
    old,new,amendment=profiles();a=request(old);b=request(new)
    assert routing.same_request_before_and_after_routing(a,b,amendment)
    assert routing.compatible_settings({'profile':old,'job':'same'}, {'profile':new,'job':'same'},amendment)
    for field,value in [('temperature',.8),('messages',[{'role':'user','content':'changed'}]),
                        ('tools',[{'name':'changed'}]),('max_tokens',8192),('model','other')]:
        changed=copy.deepcopy(b);changed[field]=value
        assert not routing.same_request_before_and_after_routing(a,changed,amendment)
    changed=copy.deepcopy(new);changed['reasoning']['effort']='high'
    assert not routing.compatible_settings({'profile':old}, {'profile':changed},amendment)
    with pytest.raises(run.Stop):routing.validate_request(request(changed),new)
    with pytest.raises(run.Stop):routing.validate_request(request(old),new)


def test_two_resumes_across_provider_change_replay_identical_days(tmp_path,monkeypatch):
    old,new,amendment=profiles()
    jobs,_=run.selected_jobs({m:old for m in run.MODELS})
    job=copy.deepcopy(next(j for j in jobs if j['arm']=='frame_doctrine' and j['spec']['model']==old['model']))
    plan={'profiles':{old['model']:old}}
    run.write(tmp_path/'plan.json',plan)
    dummy_review={'source':'unvisited-reviewed-source','plan_sha256':run.digest(tmp_path/'plan.json')}
    history=recovery.reviewed_history(tmp_path,dummy_review,routing_review=amendment)
    monkeypatch.setattr(run,'history',history)
    def factory(fail=None):
        def make(profile,path,key,stop):
            calls=0
            def chat(messages,tools):
                nonlocal calls
                calls+=1
                run.append(path,{'kind':'request','request_id':str(calls),'request':request(profile,messages,tools)})
                if calls==fail:
                    run.append(path,{'kind':'error','request_id':str(calls),'error_type':'RateLimitError'})
                    raise run.Stop('fake 429')
                raw=response('Phala' if profile==old else 'DeepInfra')
                run.append(path,{'kind':'response','request_id':str(calls),'response':raw})
                return run.audit.recorded_response(raw)
            return chat
        return make
    with pytest.raises(run.Stop):run.execute_job(tmp_path,plan,job,'fake',threading.Event(),chat_factory=factory(3))
    base=run.job_directory(tmp_path,job);first=base/'attempt-1'
    original_hash=run.digest(first/'api_calls.jsonl')
    updated=routing.effective_plan(plan,amendment)
    assert plan['profiles'][old['model']]==old
    with pytest.raises(run.Stop):run.execute_job(tmp_path,updated,job,'fake',threading.Event(),resume=True,chat_factory=factory(2))
    second=base/'attempt-2'
    assert len(history(second,run.read(second/'settings.json'))[0])==3
    run.execute_job(tmp_path,updated,job,'fake',threading.Event(),resume=True,chat_factory=factory())
    final=run.completed(tmp_path,job)
    assert final.name=='attempt-3' and run.digest(first/'api_calls.jsonl')==original_hash
    for attempt in [first,second]:
        for p in (attempt/'data').glob('*/days.jsonl'):
            a=run.rows(p);b=run.rows(final/'data'/p.relative_to(attempt/'data'))
            assert a==b[:len(a)]
    result=run.read(next((final/'data').glob('*/result.json')))
    assert set(result['providers'])=={'Phala','DeepInfra'}
    # Historical Phala-only attempts cannot retrospectively accept another host.
    events=run.rows(first/'api_calls.jsonl');events[1]['response']['provider']='Together'
    (first/'api_calls.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')
    with pytest.raises(run.Stop):history(first,run.read(second/'settings.json'))


def test_transient_retry_logs_cost_and_uses_amended_routing(tmp_path,monkeypatch):
    _,new,_=profiles();calls=[];waits=[]
    RateLimitError=type('RateLimitError',(Exception,),{})
    def fake_client(key,model,**kwargs):
        assert kwargs['strict'] and kwargs['max_retries']==0
        assert kwargs['provider']==new['provider']
        def chat(messages,tools):
            calls.append(1);kwargs['before_request'](request(new,messages,tools))
            if len(calls)<3:
                error=RateLimitError('shared pool unavailable')
                error.response=SimpleNamespace(headers={'retry-after':'40'})
                raise error
            raw=response();kwargs['on_response'](raw)
            return run.audit.recorded_response(raw)
        return chat
    monkeypatch.setattr(run,'openai_chat_client',fake_client)
    stop=SimpleNamespace(is_set=lambda:False,wait=lambda n:waits.append(n) or False)
    path=tmp_path/'api_calls.jsonl'
    routing.measured_chat(new,path,'fake',stop)([{'role':'system','content':'test'},
        {'role':'user','content':'=== DAY 2 of 90 ==='}],[])
    assert waits==[40,40] and len(calls)==3
    events=run.rows(path)
    assert len([e for e in events if e['kind']=='request'])==3
    assert events[-1]['response']['provider']=='DeepInfra'
    assert len(run.audit.Budget(tmp_path,None).charges)==3


def test_nontransient_failure_is_not_retried(tmp_path,monkeypatch):
    _,new,_=profiles();calls=[]
    def fake(*args,**kwargs):
        def chat(messages,tools):
            calls.append(1);kwargs['before_request'](request(new,messages,tools))
            raise ValueError('parameter rejection')
        return chat
    monkeypatch.setattr(run,'openai_chat_client',fake)
    stop=SimpleNamespace(is_set=lambda:False,wait=lambda n:pytest.fail('No retry permitted'))
    with pytest.raises(run.Stop,match='ValueError'):
        routing.measured_chat(new,tmp_path/'api_calls.jsonl','fake',stop)([{}, {'content':'=== DAY 2'}],[])
    assert len(calls)==1
