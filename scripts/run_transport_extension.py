"""Frozen GLM/Muse transport, one arm per invocation. Preparation is unpaid."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from collections import Counter
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import calibrate_transport as audit
from scripts import plan_transport_extension as planning
from tnt_bench.agent.day_loop import run_agent_day
from tnt_bench.agent.llm import openai_chat_client
from tnt_bench.engine import Engine, EngineConfig, generate_schedule
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.run import RunSpec, execute_run
from tnt_bench.harness.discrepancy import DiscrepancyGroupSpec, execute_discrepancy_group, validate_discrepancy_pack_source
from tnt_bench.narration import NarrationPack
from tnt_bench.themes import ThemedView, load_theme

DEFAULT_ROOT = ROOT / 'runs/transport_glm_muse_2026-09-20'
MODELS = ('z-ai/glm-5.3-flash', 'meta/muse-glimmer-30b')
ARMS = ('baseline_frame', 'discrepancy', 'frame_doctrine', 'doctrine_economy', 'exploit', 'endpoint_objective')
PROTOCOL = ROOT / 'docs/osf/TRANSPORT_GLM_MUSE_2026-09-20.md'
read, write, rows, append, digest = audit.read, audit.write, audit.rows, audit.append, audit.digest
Stop = audit.CalibrationStop


def source_hashes():
    files = [p for p in (ROOT / 'tnt_bench').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [Path(__file__), ROOT / 'scripts/calibrate_transport.py', ROOT / 'scripts/plan_transport_extension.py',
              ROOT / 'scripts/analyse_transport_extension.py']
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(files)}


def parse_spec(raw, group=False):
    raw = dict(raw)
    raw['condition'] = Condition(**raw['condition'])
    if group:
        raw['reveal_days'] = tuple(raw['reveal_days'])
        raw['discrepancy_kinds'] = tuple(raw['discrepancy_kinds'])
    return (DiscrepancyGroupSpec if group else RunSpec)(**raw)


def selected_jobs(profiles):
    full, groups = planning.build_matrix(profiles, allocation='existing', models=MODELS)
    jobs = [{**e, 'job_id': e['run_id'], 'kind': 'full'} for e in full]
    jobs += [{**g, 'job_id': g['prefix_id'], 'kind': 'group', 'arm': 'discrepancy'} for g in groups]
    smoke = []
    for model in MODELS:
        for name, frame, seed, exploit in [('ordinary', 'neutral', 900001, None),
                                         ('exploit_fantasy', 'fantasy', 12, 'ambiguous_wit'),
                                         ('exploit_neutral', 'neutral', 12, 'ambiguous_wit')]:
            spec = RunSpec(model, Condition(frame, 'rich' if exploit else 'static'), seed, horizon=90,
                           temperature=profiles[model]['temperature'], exploit_condition=exploit,
                           action_protocol='disclosed_journal_v1')
            smoke.append({'job_id': model.replace('/', '_')+'__'+name, 'kind': 'smoke', 'arm': 'smoke',
                          'spec': dataclasses.asdict(spec)})
    return jobs, smoke


def prepare(root):
    if (root / 'plan.json').exists():
        raise Stop('Already prepared; use check. Existing plans are never overwritten.')
    profiles = {p['model']: p for p in read(planning.CALIBRATION / 'plan.json')['profiles'] if p['model'] in MODELS}
    catalog = audit.get_public('https://openrouter.ai/api/v1/models')
    models = {m['id']: m for m in catalog['data']}
    for model, profile in profiles.items():
        raw = audit.get_public(f'https://openrouter.ai/api/v1/models/{model}/endpoints')
        endpoint = next((e for e in raw['data']['endpoints'] if e['tag']==profile['endpoint_tag'] and e['status']==0), None)
        if endpoint is None or endpoint['provider_name'] != profile['expected_provider']:
            raise Stop(f'Calibrated provider unavailable: {model}')
        if endpoint.get('quantization') != profile.get('quantization') or (endpoint.get('max_completion_tokens') or profile['max_tokens']) < profile['max_tokens']:
            raise Stop(f'Provider precision/output allowance changed: {model}; review before freezing.')
        required = {'tools', 'tool_choice', 'reasoning', 'max_tokens'}
        if profile['temperature'] is not None:
            required.add('temperature')
        if not required <= set(endpoint['supported_parameters']) or 'low' not in models[model]['reasoning'].get('supported_efforts', []):
            raise Stop(f'Calibrated settings unavailable: {model}')
        rates = [endpoint['pricing'], *endpoint['pricing'].get('overrides', [])]
        profile['pricing'] = endpoint['pricing']
        profile['ceiling_rates'] = {k: max(float(r.get(k, endpoint['pricing'][k])) for r in rates) for k in ('prompt','completion')}
        profile['provider']['max_price'] = {k: v*1_000_000 for k,v in profile['ceiling_rates'].items()}
        profile['provider']['ignore'] = sorted({e['tag'] for e in raw['data']['endpoints'] if e['tag'].startswith(profile['endpoint_tag']+'/')})
        write(root / 'catalogue' / (model.replace('/','_')+'.json'), {'at': audit.now(), 'model': models[model], 'endpoints': raw})
    jobs, smoke = selected_jobs(profiles)
    if len({str(job_directory(root,j)) for j in jobs+smoke}) != len(jobs+smoke):
        raise Stop('Job directory collision; no collection can start.')
    for job in jobs:
        base = job_directory(root,job)/'attempt-999'/'data'
        paths = ([base/'branches'/branch/'start_checkpoint.json' for branch in job['branches']]
                 if job['kind']=='group' else [base/job['run_id']/'narration_pack.yml'])
        if os.name=='nt' and any(len(str(p))>=260 for p in paths):
            raise Stop('Output directory is too long for Windows. Select a shorter --out path.')
    for seed in (12, *range(13,23)):
        for frame in ('fantasy', 'neutral'):
            name = f'pack__{frame}__s{seed}__h90.yml'
            target = root / 'packs' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / 'runs/replication1/packs' / name, target)
    validate_discrepancy_pack_source([parse_spec(j['spec'], True) for j in jobs if j['kind']=='group'], root / 'packs')
    for seed in (12, 900001, *range(13,23)):
        path = root / 'schedules' / f's{seed}__h90.yml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generate_schedule(seed,90).to_yaml(), encoding='utf-8')
    root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROTOCOL, root / 'protocol.md')
    # Exact starting prompts, including every treatment and frame; state-dependent
    # corrected-fault prompts remain covered by the frozen renderer source.
    seen = set()
    for j in jobs + smoke:
        spec = parse_spec(j['spec'], j['kind']=='group')
        signature = (spec.condition.framing, getattr(spec,'exploit_condition',None),
                     getattr(spec,'disclose_horizon',True), getattr(spec,'score_objective',None),
                     getattr(spec,'carrying_cost',0), getattr(spec,'normative_climate',None))
        if signature in seen:
            continue
        seen.add(signature)
        cfg = EngineConfig(horizon=90, carrying_cost_per_unit=getattr(spec,'carrying_cost',0),
                           exploit_fault=getattr(spec,'exploit_condition',None) is not None)
        v = ThemedView(Engine(cfg, generate_schedule(13,90)), load_theme(spec.condition.framing),
            disclose_horizon=getattr(spec,'disclose_horizon',True), score_objective=getattr(spec,'score_objective',None),
            exploit_condition=getattr(spec,'exploit_condition',None), normative_climate=getattr(spec,'normative_climate',None),
            email_enabled=j['kind']=='group', action_protocol=spec.action_protocol)
        write(root / 'prompts' / f'{len(seen):02d}.json', {'factors': signature, 'prompt': v.system_prompt()})
    artifacts = {p.relative_to(root).as_posix(): digest(p) for directory in ('packs','schedules','prompts','catalogue')
                 for p in (root / directory).iterdir() if p.is_file()}
    artifacts['protocol.md'] = digest(root / 'protocol.md')
    hashes = source_hashes()
    for name in hashes:
        target = root / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    plan = {'created_at': audit.now(), 'status': 'locally_frozen_not_evidence_of_public_registration',
        'models': list(MODELS), 'profiles': profiles, 'jobs': jobs, 'smoke_jobs': smoke,
        'arm_order': list(ARMS), 'source_hashes': hashes, 'artifact_hashes': artifacts,
        'runtime': audit.runtime_versions(), 'max_workers': 4, 'per_model_workers': 2,
        'allocation': 'existing schedules 13-22; baseline/discrepancy two realizations; others one',
        'calibration_plan_sha256': digest(planning.CALIBRATION / 'plan.json')}
    measured = planning.measured_costs()
    plan['cost_basis'] = {m:measured[m] for m in MODELS}
    equivalent_runs = (320*90+40*45+160*10)/90
    cost = sum(measured[m]['usd_per_90_days']*equivalent_runs for m in MODELS)
    hours = sum(measured[m]['request_seconds_per_90_days']*equivalent_runs/3600 for m in MODELS)
    plan['cost_scenarios'] = [{'multiplier':k,'usd':cost*k,'serial_request_hours':hours*k,
                               'ideal_days_at_four_workers':hours*k/4/24} for k in (1,2,3)]
    write(root / 'plan.json', plan)
    (root / 'plan.sha256').write_text(digest(root / 'plan.json')+'\n', encoding='ascii')
    check(root)


def check(root):
    if digest(root / 'plan.json') != (root / 'plan.sha256').read_text().strip():
        raise Stop('Frozen plan changed.')
    plan = read(root / 'plan.json')
    if source_hashes() != plan['source_hashes']:
        raise Stop('Frozen runtime/analysis source changed. Use the saved source snapshot or record an amendment before continuing.')
    if audit.runtime_versions() != plan['runtime']:
        raise Stop('Python environment changed since preparation.')
    for name, sha in plan['artifact_hashes'].items():
        if digest(root / name) != sha:
            raise Stop(f'Frozen artifact changed: {name}')
    return plan


def pack_for(root, spec):
    if spec.condition.richness != 'rich':
        return None
    return NarrationPack.from_yaml((root / 'packs' / f'pack__{spec.condition.framing}__s{spec.schedule_seed}__h90.yml').read_text(encoding='utf-8'))


def completed(root, job):
    found = sorted(job_directory(root,job).glob('attempt-*/complete.json'))
    if len(found) > 1:
        raise Stop(f'Multiple completed attempts for {job["job_id"]}; review before analysis.')
    return found[0].parent if found else None


def job_directory(root,job):
    # Full scientific IDs remain in settings/manifests. Avoid duplicating them
    # in parent paths: Windows would otherwise exceed its legacy path limit.
    short = 'j'+hashlib.sha256(job['job_id'].encode('utf-8')).hexdigest()[:12]
    return root / job['arm'] / short


def valid_response(response, profile):
    cost = (response.get('usage') or {}).get('cost')
    return (response.get('provider') == profile['expected_provider'] and bool(response.get('choices'))
            and response['choices'][0].get('finish_reason') != 'length'
            and isinstance(cost, (int,float)) and math.isfinite(cost) and cost >= 0)


def history(source, settings, seen=None):
    seen = set() if seen is None else seen
    source = source.resolve()
    if source in seen or read(source / 'settings.json') != settings:
        raise Stop('Recovery ancestry/settings mismatch.')
    seen.add(source)
    pairs, pending = [], None
    if (source / 'recovery.json').exists():
        parent = read(source / 'recovery.json')
        parent_path = Path(parent['source'])
        if digest(parent_path / 'api_calls.jsonl') != parent['api_sha256']:
            raise Stop('Recovery source log changed.')
        pairs, pending = history(parent_path, settings, seen)
    for event in rows(source / 'api_calls.jsonl'):
        if event['kind'] == 'request':
            if pending and pending['request'] != event['request']:
                raise Stop('Recovery found changed inputs after an unanswered request.')
            pending = event
        elif event['kind'] == 'response':
            if not pending or pending['request_id'] != event['request_id'] or not valid_response(event['response'], settings['profile']):
                raise Stop('Cannot replay an invalid, unbilled or truncated response; technical review required.')
            pairs.append((pending['request'], event['response']))
            pending = None
        elif event['kind'] == 'error' and event['error_type'] not in audit.TRANSIENT_ERRORS:
            raise Stop('Non-transient error requires review before recovery.')
    return pairs, pending['request'] if pending else None


class ReplayingChat:
    def __init__(self, pairs, pending, live):
        self.pairs, self.pending, self.live, self.index = pairs, pending, live, 0

    def __call__(self, messages, tools):
        expected = self.pairs[self.index][0] if self.index < len(self.pairs) else self.pending
        if expected is not None and (messages != expected['messages'] or tools != expected['tools']):
            raise Stop(f'Recovery request mismatch at call {self.index+1}; no new inference issued.')
        if self.index < len(self.pairs):
            raw = self.pairs[self.index][1]
            self.index += 1
            return audit.recorded_response(raw)
        self.pending = None
        return self.live(messages, tools)


def measured_chat(profile, path, key, stop):
    budget = audit.Budget(path.parent, None)  # One ledger per attempt: no concurrent writes.
    state = {}
    def before(request):
        if stop.is_set():
            raise Stop('Batch interrupted; request not sent.')
        nbytes = len(json.dumps(request, ensure_ascii=False).encode('utf-8'))+4096
        rates = profile['ceiling_rates']
        request_id = budget.reserve(2*(nbytes*rates['prompt']+profile['max_tokens']*rates['completion']), path.parent.name)
        state.update(request_id=request_id, start=time.monotonic())
        match = re.search(r'=== DAY (\d+)', request['messages'][1]['content'])
        append(path, {'kind':'request', 'at':audit.now(), 'request_id':request_id,
                      'day':int(match.group(1)) if match else None, 'request':request})
    def after(response):
        append(path, {'kind':'response','at':audit.now(),'request_id':state['request_id'],
                      'seconds':time.monotonic()-state['start'],'response':response})
        if not budget.settle(state['request_id'], (response.get('usage') or {}).get('cost')):
            raise Stop('Missing/invalid billing cost; reservation preserved.')
        if not valid_response(response, profile):
            raise Stop('Unexpected provider, missing choices or truncated output; response preserved for review.')
    client = openai_chat_client(key, profile['model'], temperature=profile['temperature'], max_retries=0,
        provider=profile['provider'], reasoning=profile['reasoning'], max_tokens=profile['max_tokens'],
        strict=True, before_request=before, on_response=after)
    def chat(messages, tools):
        for attempt in range(3):
            try:
                return client(messages, tools)
            except Stop:
                raise
            except Exception as error:
                append(path, {'kind':'error','at':audit.now(),'request_id':state.get('request_id'),
                              'error_type':type(error).__name__,'message':str(error)[:1000]})
                if type(error).__name__ in audit.TRANSIENT_ERRORS and attempt < 2:
                    if stop.wait((2,5)[attempt]):
                        raise Stop('Batch interrupted; retry not sent.') from error
                    continue
                raise Stop(f'{type(error).__name__}; attempt preserved. Review and use --resume for transient interruptions.') from error
    return chat


def smoke_run(spec, folder, chat, pack):
    view = ThemedView(Engine(EngineConfig(horizon=90, exploit_fault=spec.exploit_condition is not None),
                            generate_schedule(spec.schedule_seed,90)), load_theme(spec.condition.framing),
                      exploit_condition=spec.exploit_condition, action_protocol=spec.action_protocol)
    for _ in range(3):
        dawn = view.dawn()
        narration = pack.text_for_day(view.day) if pack else view.static_narration(dawn)
        result = run_agent_day(view, chat, view.briefing(dawn,narration))
        view.dusk()
        append(folder / 'days.jsonl', dataclasses.asdict(result))
    days = rows(folder / 'days.jsonl')
    calls = [c for d in days for c in d['tool_calls']]
    malformed = sum(str(c['result'].get('error','')).startswith('invalid tool arguments') for c in calls)
    passed = len(days)==3 and not any(d['forced'] for d in days) and malformed/max(len(calls),1)<.05
    gate = {'pass':passed,'days':len(days),'malformed':malformed,'forced':sum(d['forced'] for d in days)}
    write(folder / 'gate.json', gate)
    if not passed:
        raise Stop('Revised-interface smoke check needs review; valid economic rejections alone do not fail the check.')
    return gate


def execute_job(root, plan, job, key, stop, resume=False, chat_factory=measured_chat):
    base = job_directory(root,job)
    if completed(root,job):
        return 'already complete'
    existing = sorted(base.glob('attempt-*'), key=lambda p:int(p.name.split('-')[-1]))
    if existing and not resume:
        raise Stop(f'Interrupted attempt for {job["job_id"]}; use --resume to replay saved decisions.')
    settings = {'job':job,'profile':plan['profiles'][job['spec']['model']], 'plan_sha256':digest(root / 'plan.json')}
    settings = json.loads(json.dumps(settings))  # Canonical persisted tuple/list representation.
    pairs, pending = history(existing[-1], settings) if existing else ([],None)
    attempt = base / f'attempt-{len(existing)+1}'
    attempt.mkdir(parents=True, exist_ok=False)
    write(attempt / 'settings.json',settings)
    if existing:
        source = existing[-1]
        # Empty logs are valid when interruption preceded the first request.
        (source / 'api_calls.jsonl').touch(exist_ok=True)
        write(attempt / 'recovery.json', {'source':str(source.resolve()), 'api_sha256':digest(source / 'api_calls.jsonl'),
                                         'saved_responses':len(pairs), 'at':audit.now()})
    (attempt / 'api_calls.jsonl').touch(exist_ok=False)
    live = chat_factory(settings['profile'], attempt / 'api_calls.jsonl', key, stop)
    chat = ReplayingChat(pairs,pending,live)
    spec = parse_spec(job['spec'], job['kind']=='group')
    pack = pack_for(root,spec)
    artifacts = attempt / 'data'
    artifacts.mkdir()
    print(f'Starting {job["arm"]}: {job["job_id"]} (reusing {len(pairs)} saved responses)', flush=True)
    try:
        if job['kind']=='group':
            result = execute_discrepancy_group(spec, artifacts, chat, pack)
        elif job['kind']=='smoke':
            result = smoke_run(spec, artifacts, chat, pack)
        else:
            result = execute_run(spec, artifacts, chat, pack)
        if chat.index != len(pairs) or chat.pending is not None:
            raise Stop('Recovery finished before consuming the saved trajectory; review required.')
        write(attempt / 'complete.json', {'at':audit.now(), 'job_id':job['job_id'], 'result':result})
    except BaseException as error:
        write(attempt / 'stopped.json', {'at':audit.now(), 'type':type(error).__name__, 'message':str(error)})
        raise
    print(f'Completed {job["job_id"]}',flush=True)
    return job['job_id']


def run(root, arm, resume=False, workers=4):
    plan = check(root)
    if not 1 <= workers <= plan['max_workers']:
        raise Stop(f'Workers must be 1–{plan["max_workers"]}.')
    jobs = plan['smoke_jobs'] if arm=='smoke' else [j for j in plan['jobs'] if j['arm']==arm]
    if arm!='smoke' and any(not completed(root,j) for j in plan['smoke_jobs']):
        raise Stop('First run smoke: revised-interface checks must pass before main collection.')
    if arm=='frame_doctrine' and any(not completed(root,j) for j in plan['jobs'] if j['arm']=='baseline_frame'):
        raise Stop('Baseline framing supplies the crossover controls; complete it first.')
    todo = [j for j in jobs if not completed(root,j)]
    if not todo:
        print(f'{arm}: all {len(jobs)} jobs already complete; no requests.'); return
    if not resume and any(list(job_directory(root,j).glob('attempt-*')) for j in todo):
        raise Stop('Interrupted attempts present. Use --resume; existing traces will be replayed, not regenerated.')
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise Stop('OPENROUTER_API_KEY is not set in this process.')
    lock = root / 'running.lock'
    if lock.exists():
        pid = int(lock.read_text().strip())
        if audit.process_alive(pid):
            raise Stop(f'Transport runner already active (PID {pid}).')
        lock.unlink()  # Checked stale; original attempts remain intact.
    with lock.open('x',encoding='ascii') as stream:
        stream.write(str(os.getpid()))
    stop = threading.Event()
    active, errors, counts = {}, [], Counter()
    pool = ThreadPoolExecutor(max_workers=workers)
    try:
        while todo or active:
            while todo and len(active)<workers and not stop.is_set():
                eligible = next((i for i,j in enumerate(todo) if counts[j['spec']['model']]<plan['per_model_workers']),None)
                if eligible is None: break
                job = todo.pop(eligible)
                future = pool.submit(execute_job,root,plan,job,key,stop,resume)
                active[future] = job
                counts[job['spec']['model']] += 1
            if not active: break
            done,_ = wait(active,timeout=30,return_when=FIRST_COMPLETED)
            if not done:
                print(f'{arm}: {len(active)} trajectories active; {len(todo)} queued.',flush=True)
            for future in done:
                job = active.pop(future)
                counts[job['spec']['model']] -= 1
                try: future.result()
                except Exception as error:
                    errors.append(f'{job["job_id"]}: {error}')
                    stop.set()
        if errors:
            raise Stop('\n'.join(errors))
    except KeyboardInterrupt:
        stop.set()
        print('Stopping after in-flight requests return; artifacts and billed responses are being preserved.',flush=True)
        raise
    finally:
        pool.shutdown(wait=True,cancel_futures=True)
        lock.unlink(missing_ok=True)
    print(f'{arm} finished. No next arm is started automatically.')


def summary(root, arm=None):
    plan = read(root / 'plan.json')
    output = []
    for name in (('smoke',)+ARMS if arm is None else (arm,)):
        jobs = plan['smoke_jobs'] if name=='smoke' else [j for j in plan['jobs'] if j['arm']==name]
        result = {'arm':name,'planned_jobs':len(jobs),'completed_jobs':sum(completed(root,j) is not None for j in jobs),
                  'reported_usd':0.,'request_seconds':0.,'unknown_billing_requests':0}
        for path in (root/name).glob('*/attempt-*/api_calls.jsonl'):
            # A status read may coincide with one append. Ignore only its
            # unfinished final line here; recovery remains strict.
            text = path.read_text(encoding='utf-8')
            lines = text.splitlines()
            if text and not text.endswith('\n'):
                lines = lines[:-1]
            log = [json.loads(line) for line in lines]
            responses = [e for e in log if e['kind']=='response']
            result['reported_usd'] += sum((e['response'].get('usage') or {}).get('cost') or 0 for e in responses)
            result['request_seconds'] += sum(e['seconds'] for e in responses)
            paid_ids = {e['request_id'] for e in responses if isinstance((e['response'].get('usage') or {}).get('cost'),(int,float))
                        and math.isfinite(e['response']['usage']['cost']) and e['response']['usage']['cost']>=0}
            result['unknown_billing_requests'] += sum(e['kind']=='request' and e['request_id'] not in paid_ids for e in log)
        output.append(result)
    write(root/'status.json',output)
    print(json.dumps(output,indent=2))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','check','summary','smoke',*ARMS))
    parser.add_argument('--out',type=Path,default=DEFAULT_ROOT)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--workers',type=int,default=4)
    args = parser.parse_args()
    root = args.out.resolve()
    if args.command=='prepare':
        prepare(root); summary(root)
    elif args.command=='check':
        check(root); print('Frozen plan, runtime, packs and sources verified. No inference calls.')
    elif args.command=='summary': summary(root)
    else: run(root,args.command,args.resume,args.workers)


if __name__=='__main__':
    try: main()
    except (Stop,FileExistsError) as error:
        print(str(error),file=sys.stderr); sys.exit(2)
