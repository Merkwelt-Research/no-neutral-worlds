import copy
import json
import shutil
import threading
from types import SimpleNamespace

import pytest

from scripts import run_transport_extension as run
from scripts import resume_transport_reviewed as recovery


def fixture(tmp_path):
    source = tmp_path / 'attempt-1'
    source.mkdir()
    run.write(tmp_path / 'plan.json', {'frozen': True})
    settings = {'profile': {'model': 'test', 'expected_provider': 'Test'}}
    run.write(source / 'settings.json', settings)
    first = {'messages': [{'role': 'user', 'content': 'day 1'}], 'tools': []}
    second = {'messages': [{'role': 'user', 'content': 'day 2'}], 'tools': []}
    response = {'provider': 'Test', 'usage': {'cost': .01},
                'choices': [{'finish_reason': 'stop', 'message': {'content': 'saved decision'}}]}
    failed = {'id': 'failure', 'provider': 'Test', 'model': 'test', 'usage': None,
              'choices': [{'finish_reason': 'stop', 'native_finish_reason': 'network_error',
                           'message': {'role': 'assistant', 'content': None, 'tool_calls': None}}]}
    for event in [
        {'kind': 'request', 'request_id': 'one', 'request': first},
        {'kind': 'response', 'request_id': 'one', 'response': response},
        {'kind': 'request', 'request_id': 'two', 'request': second},
        {'kind': 'response', 'request_id': 'two', 'response': failed},
    ]:
        run.append(source / 'api_calls.jsonl', event)
    review = {'source': 'attempt-1', 'plan_sha256': run.digest(tmp_path / 'plan.json'),
              'api_sha256': run.digest(source / 'api_calls.jsonl'),
              'settings_sha256': run.digest(source / 'settings.json'),
              'request_id': 'two', 'response_id': 'failure', 'saved_responses': 1}
    return source, settings, review, first, second, response


def test_recovery_preserves_decision_pending_input_and_original_log(tmp_path):
    source, settings, review, first, second, response = fixture(tmp_path)
    before = (source / 'api_calls.jsonl').read_bytes()
    history = recovery.reviewed_history(tmp_path, review, run.history)
    pairs, pending = history(source, settings)
    assert pairs == [(first, response)]
    assert pending == second
    assert (source / 'api_calls.jsonl').read_bytes() == before
    with pytest.raises(run.Stop):
        run.history(source, settings)  # The frozen validator remains strict.
    wrong = copy.deepcopy(settings)
    wrong['profile']['model'] = 'other'
    with pytest.raises(run.Stop):
        history(source, wrong)


@pytest.mark.parametrize('mutation', ['content', 'tools', 'truncation', 'billing', 'hash'])
def test_recovery_rejects_unreviewed_or_substantive_output(tmp_path, mutation):
    source, settings, review, *_ = fixture(tmp_path)
    events = run.rows(source / 'api_calls.jsonl')
    response = events[-1]['response']
    if mutation == 'content':
        response['choices'][0]['message']['content'] = 'a decision'
    elif mutation == 'tools':
        response['choices'][0]['message']['tool_calls'] = [{'id': 'action'}]
    elif mutation == 'truncation':
        response['choices'][0]['finish_reason'] = 'length'
    elif mutation == 'billing':
        response['usage'] = {'cost': .01}
    else:
        response['id'] = 'different failure'
    (source / 'api_calls.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events), encoding='utf-8')
    if mutation != 'hash':
        review['api_sha256'] = run.digest(source / 'api_calls.jsonl')
    with pytest.raises(run.Stop):
        recovery.reviewed_history(tmp_path, review, run.history)(source, settings)


def test_review_applies_through_preserved_recovery_ancestry(tmp_path, monkeypatch):
    source, settings, review, first, second, response = fixture(tmp_path)
    child = tmp_path / 'attempt-2'
    child.mkdir()
    run.write(child / 'settings.json', settings)
    run.write(child / 'recovery.json', {'source': str(source), 'api_sha256': review['api_sha256']})
    run.append(child / 'api_calls.jsonl', {'kind': 'request', 'request_id': 'retry', 'request': second})
    run.append(child / 'api_calls.jsonl', {'kind': 'response', 'request_id': 'retry', 'response': response})
    monkeypatch.setattr(run, 'history', recovery.reviewed_history(tmp_path, review, run.history))
    pairs, pending = run.history(child, settings)
    assert pairs == [(first, response), (second, response)]
    assert pending is None


def test_multiple_network_reviews_preserve_each_history_and_budget(tmp_path):
    source, settings, review, first, second, response = fixture(tmp_path)
    extra = tmp_path / 'another-job' / 'attempt-1'
    shutil.copytree(source, extra)
    run.append(extra / 'budget.jsonl', {'kind': 'reserve', 'request_id': 'two', 'amount': .05})
    additional = {**review, 'source': 'another-job/attempt-1',
                  'budget_sha256': run.digest(extra / 'budget.jsonl')}
    before = {p: p.read_bytes() for p in (source/'api_calls.jsonl', extra/'api_calls.jsonl', extra/'budget.jsonl')}
    history = recovery.reviewed_history(tmp_path, review, network_reviews=[additional])
    for path in (source, extra):
        assert history(path, settings) == ([(first, response)], second)
    assert all(p.read_bytes() == raw for p, raw in before.items())
    with pytest.raises(run.Stop):
        recovery.reviewed_history(tmp_path, review)(extra, settings)
    run.append(extra / 'budget.jsonl', {'kind': 'settle', 'request_id': 'two', 'amount': 0})
    with pytest.raises(run.Stop, match='budget changed'):
        history(extra, settings)


def test_additional_network_review_cannot_drop_reasoning(tmp_path):
    source, settings, review, *_ = fixture(tmp_path)
    extra = tmp_path / 'another-job' / 'attempt-1'
    shutil.copytree(source, extra)
    events = run.rows(extra / 'api_calls.jsonl')
    events[-1]['response']['choices'][0]['message']['reasoning'] = 'Substantive model output'
    (extra / 'api_calls.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events), encoding='utf-8')
    additional = {**review, 'source': 'another-job/attempt-1', 'api_sha256': run.digest(extra/'api_calls.jsonl')}
    with pytest.raises(run.Stop, match='containing model output'):
        recovery.reviewed_history(tmp_path, review, network_reviews=[additional])(extra, settings)


def test_duplicate_network_reviews_rejected(tmp_path):
    _, _, review, *_ = fixture(tmp_path)
    with pytest.raises(run.Stop, match='Duplicate'):
        recovery.reviewed_history(tmp_path, review, network_reviews=[review])


def test_disk_review_retains_all_saved_responses_and_requires_exact_error(tmp_path):
    source, settings, review, first, second, response = fixture(tmp_path)
    disk = tmp_path / 'disk'
    disk.mkdir()
    run.write(disk / 'settings.json', settings)
    error = {'kind': 'error', 'request_id': 'not-sent', 'error_type': 'OSError',
             'message': '[Errno 28] No space left on device'}
    for event in [
        {'kind': 'request', 'request_id': 'saved', 'request': first},
        {'kind': 'response', 'request_id': 'saved', 'response': response}, error,
    ]:
        run.append(disk / 'api_calls.jsonl', event)
    run.append(disk / 'budget.jsonl', {'kind': 'reserve', 'request_id': 'not-sent'})
    dr = {'source': 'disk', 'plan_sha256': review['plan_sha256'],
          'api_sha256': run.digest(disk / 'api_calls.jsonl'),
          'settings_sha256': run.digest(disk / 'settings.json'),
          'budget_sha256': run.digest(disk / 'budget.jsonl'),
          'error_event': error, 'saved_responses': 1}
    history = recovery.reviewed_history(tmp_path, review, disk_review=dr)
    assert history(disk, settings) == ([(first, response)], None)
    assert run.rows(disk / 'api_calls.jsonl')[-1] == error
    with pytest.raises(run.Stop):
        recovery.reviewed_history(tmp_path, review)(disk, settings)
    run.append(disk / 'api_calls.jsonl', {'kind': 'error', 'error_type': 'OSError'})
    with pytest.raises(run.Stop, match='artifacts changed'):
        history(disk, settings)


def test_disk_guard_stops_before_live_request(tmp_path, monkeypatch):
    calls = []
    def fake(*args):
        return lambda *args: calls.append(args) or 'response'
    chat = recovery.disk_guarded_factory(tmp_path, 100, fake)({}, tmp_path/'api.jsonl', 'fake', None)
    monkeypatch.setattr(recovery.shutil, 'disk_usage', lambda _: SimpleNamespace(free=99))
    with pytest.raises(run.Stop, match='Low disk space'):
        chat([], [])
    assert calls == []
    monkeypatch.setattr(recovery.shutil, 'disk_usage', lambda _: SimpleNamespace(free=100))
    assert chat([], []) == 'response'
    assert len(calls) == 1


def credit_fixture(tmp_path):
    source, settings, review, first, second, response = fixture(tmp_path)
    credit = tmp_path / 'credit' / 'attempt-1'
    shutil.copytree(source, credit)
    events = run.rows(credit / 'api_calls.jsonl')[:-1]
    events.append({'kind': 'error', 'request_id': 'two', 'error_type': 'APIStatusError',
                   'message': 'Error code: 402 - This request requires more credits; openrouter_credits'})
    (credit / 'api_calls.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events), encoding='utf-8')
    run.append(credit / 'budget.jsonl', {'kind': 'reserve', 'request_id': 'two', 'amount': .05})
    cr = {'source': 'credit/attempt-1', 'plan_sha256': review['plan_sha256'],
          'api_sha256': run.digest(credit/'api_calls.jsonl'),
          'settings_sha256': run.digest(credit/'settings.json'),
          'budget_sha256': run.digest(credit/'budget.jsonl'), 'request_id': 'two', 'saved_responses': 1}
    return credit, settings, review, cr, first, second, response


def test_credit_review_keeps_decisions_pending_request_and_budget(tmp_path):
    source, settings, review, cr, first, second, response = credit_fixture(tmp_path)
    before = {p:p.read_bytes() for p in source.iterdir() if p.is_file()}
    with pytest.raises(run.Stop, match='Non-transient'):
        recovery.reviewed_history(tmp_path, review)(source, settings)
    history = recovery.reviewed_history(tmp_path, review, credit_reviews=[cr])
    assert history(source, settings) == ([(first,response)],second)
    assert all(p.read_bytes()==raw for p,raw in before.items())
    child = source.parent/'attempt-2'
    child.mkdir()
    run.write(child/'settings.json',settings)
    run.write(child/'recovery.json',{'source':str(source),'api_sha256':cr['api_sha256']})
    run.append(child/'api_calls.jsonl',{'kind':'request','request_id':'retry','request':second})
    run.append(child/'api_calls.jsonl',{'kind':'response','request_id':'retry','response':response})
    assert history(child,settings)==([(first,response),(second,response)],None)


@pytest.mark.parametrize('mutation',['other_status','response','budget','hash','count'])
def test_credit_review_rejects_unapproved_changes(tmp_path,mutation):
    source, settings, review, cr, first, second, response = credit_fixture(tmp_path)
    events=run.rows(source/'api_calls.jsonl')
    if mutation=='other_status':events[-1]['message']=events[-1]['message'].replace('402','403')
    elif mutation=='response':events.insert(-1,{'kind':'response','request_id':'two','response':response})
    elif mutation=='budget':run.append(source/'budget.jsonl',{'kind':'settle','request_id':'two','amount':0})
    elif mutation=='hash':events[-1]['at']='changed'
    else:cr['saved_responses']=2
    (source/'api_calls.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')
    if mutation!='hash':cr['api_sha256']=run.digest(source/'api_calls.jsonl')
    with pytest.raises(run.Stop):
        recovery.reviewed_history(tmp_path,review,credit_reviews=[cr])(source,settings)


def test_eight_workers_four_per_model_without_mutating_plan(tmp_path, monkeypatch):
    jobs = [{'arm': 'discrepancy', 'job_id': f'{m}-{i}', 'spec': {'model': m}}
            for m in ('a', 'b') for i in range(4)]
    plan = {'jobs': jobs, 'smoke_jobs': [], 'max_workers': 4, 'per_model_workers': 2}
    run.write(tmp_path/'plan.json', plan)
    digest = run.digest(tmp_path/'plan.json')
    amendment = {'plan_sha256': digest, 'original': {'max_workers': 4, 'per_model_workers': 2},
                 'amended': {'max_workers': 8, 'per_model_workers': 4}}
    updated = recovery.effective_plan(tmp_path, plan, 8, amendment)
    assert recovery.effective_plan(tmp_path, plan, 4, amendment)['per_model_workers'] == 2
    assert plan['max_workers'] == 4 and plan['per_model_workers'] == 2
    with pytest.raises(run.Stop):
        recovery.effective_plan(tmp_path, plan, 9, amendment)
    monkeypatch.setattr(run, 'check', lambda _: updated)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'fake-no-network')
    barrier = threading.Barrier(8)
    counts = {'a': 0, 'b': 0}
    lock = threading.Lock()
    reached = []
    def fake_job(root, plan, job, *args):
        with lock:
            counts[job['spec']['model']] += 1
            assert max(counts.values()) <= 4
        barrier.wait(timeout=5)
        with lock:
            reached.append(dict(counts))
    monkeypatch.setattr(run, 'execute_job', fake_job)
    run.run(tmp_path, 'discrepancy', workers=8)
    assert len(reached) == 8 and all(c == {'a': 4, 'b': 4} for c in reached)
    assert run.digest(tmp_path/'plan.json') == digest
