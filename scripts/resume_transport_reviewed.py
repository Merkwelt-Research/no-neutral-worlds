"""Resume with hash-bound technical reviews and recorded concurrency limits.

The original log and its unknown billing reservation remain untouched. Only
recovery's in-memory reading omits the reviewed final failure envelope, leaving
its request pending. A dated routing amendment can permit same-model provider
fallback, while preserving billing, truncation and exact replay checks.
"""
from __future__ import annotations

import argparse
from functools import partial
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_transport_extension as runner
from scripts import transport_provider_fallback as routing

REVIEW = 'reviews/empty_network_response_2026-09-22.json'
DISK_REVIEW = 'reviews/disk_full_recovery_2026-09-22.json'
CONCURRENCY_REVIEW = 'reviews/concurrency_amendment_2026-09-22.json'


def reviewed_history(root, review, original=None, disk_review=None, routing_review=None,
                     network_reviews=(), credit_reviews=()):
    root = root.resolve()
    reviewed_sources = {}
    for item in (review, *network_reviews):
        source = (root / item['source']).resolve()
        if not source.is_relative_to(root) or item['plan_sha256'] != runner.digest(root / 'plan.json'):
            raise runner.Stop('Reviewed recovery root/plan mismatch.')
        if source in reviewed_sources:
            raise runner.Stop('Duplicate network recovery review for one source.')
        reviewed_sources[source] = item
    credit_sources = {}
    for item in credit_reviews:
        source = (root / item['source']).resolve()
        if not source.is_relative_to(root) or item['plan_sha256'] != runner.digest(root / 'plan.json'):
            raise runner.Stop('Reviewed credit recovery root/plan mismatch.')
        if source in credit_sources or source in reviewed_sources:
            raise runner.Stop('Duplicate credit recovery review for one source.')
        credit_sources[source] = item
    disk_source = (root / disk_review['source']).resolve() if disk_review else None
    if disk_review and (not disk_source.is_relative_to(root) or
                        disk_review['plan_sha256'] != runner.digest(root / 'plan.json')):
        raise runner.Stop('Disk recovery root/plan mismatch.')

    def reviewed_events(path, settings):
        log = path / 'api_calls.jsonl'
        if path in credit_sources:
            item = credit_sources[path]
            if (runner.digest(log) != item['api_sha256'] or
                    runner.digest(path / 'settings.json') != item['settings_sha256'] or
                    runner.digest(path / 'budget.jsonl') != item['budget_sha256']):
                raise runner.Stop('Reviewed credit-failure artifacts changed.')
            if (path / 'recovery.json').exists():
                raise runner.Stop('Reviewed credit source unexpectedly has recovery ancestry.')
            events = runner.rows(log)
            error = events[-1]
            message = error.get('message', '')
            if (error.get('kind') != 'error' or error.get('error_type') != 'APIStatusError' or
                    error.get('request_id') != item['request_id'] or
                    not message.startswith('Error code: 402 - ') or
                    'This request requires more credits' not in message or
                    'openrouter_credits' not in message):
                raise runner.Stop('Unreviewed credit rejection.')
            matching = [e for e in events if e.get('request_id') == item['request_id']]
            reserve = runner.rows(path / 'budget.jsonl')[-1]
            if ([e['kind'] for e in matching] != ['request', 'error'] or
                    reserve.get('kind') != 'reserve' or reserve.get('request_id') != item['request_id']):
                raise runner.Stop('Credit rejection has unexpected response or reservation state.')
            # Only the reviewed error is omitted in memory. Keep the request pending,
            # all saved decisions and the original log/billing reservation unchanged.
            return events[:-1]
        if path == disk_source:
            if (runner.digest(log) != disk_review['api_sha256'] or
                    runner.digest(path / 'settings.json') != disk_review['settings_sha256'] or
                    runner.digest(path / 'budget.jsonl') != disk_review['budget_sha256']):
                raise runner.Stop('Reviewed disk-failure artifacts changed.')
            events = runner.rows(log)
            error = events[-1]
            if (error != disk_review['error_event'] or error.get('kind') != 'error' or
                    error.get('error_type') != 'OSError' or
                    error.get('message') != '[Errno 28] No space left on device'):
                raise runner.Stop('Unreviewed storage error.')
            if any(e.get('request_id') == error['request_id'] and
                   e['kind'] in ('request', 'response') for e in events):
                raise runner.Stop('Storage failure has a dispatched or logged request; review required.')
            reserve = runner.rows(path / 'budget.jsonl')[-1]
            if reserve['kind'] != 'reserve' or reserve['request_id'] != error['request_id']:
                raise runner.Stop('Storage failure reservation mismatch.')
            return events[:-1]
        if path not in reviewed_sources:
            return runner.rows(log)
        review = reviewed_sources[path]
        if (runner.digest(log) != review['api_sha256'] or
                runner.digest(path / 'settings.json') != review['settings_sha256']):
            raise runner.Stop('Reviewed recovery artifacts changed.')
        if 'budget_sha256' in review and runner.digest(path / 'budget.jsonl') != review['budget_sha256']:
            raise runner.Stop('Reviewed recovery budget changed.')
        if (path / 'recovery.json').exists():
            raise runner.Stop('Reviewed source unexpectedly has recovery ancestry.')
        events = runner.rows(log)
        event = events[-1]
        raw = event.get('response') or {}
        choices = raw.get('choices') or []
        if not (event.get('kind') == 'response' and
                event.get('request_id') == review['request_id'] and
                raw.get('id') == review['response_id'] and
                raw.get('provider') == settings['profile']['expected_provider'] and
                raw.get('model') == settings['profile']['model'] and
                raw.get('usage') is None and len(choices) == 1 and
                choices[0].get('native_finish_reason') == 'network_error' and
                choices[0].get('finish_reason') == 'stop'):
            raise runner.Stop('Response does not match the reviewed empty network failure.')
        message = choices[0].get('message') or {}
        if any(value for key, value in message.items() if key != 'role'):
            raise runner.Stop('Cannot omit a response containing model output.')
        return events[:-1]

    def walk(path, settings, seen):
        path = path.resolve()
        actual_settings = runner.read(path / 'settings.json')
        compatible = (routing.compatible_settings(actual_settings, settings, routing_review)
                      if routing_review else actual_settings == settings)
        if path in seen or not compatible:
            raise runner.Stop('Recovery ancestry/settings mismatch.')
        seen.add(path)
        pairs, pending = [], None
        if (path / 'recovery.json').exists():
            parent = runner.read(path / 'recovery.json')
            parent_path = Path(parent['source'])
            if runner.digest(parent_path / 'api_calls.jsonl') != parent['api_sha256']:
                raise runner.Stop('Recovery source log changed.')
            pairs, pending = walk(parent_path, settings, seen)
        for event in reviewed_events(path, actual_settings):
            if event['kind'] == 'request':
                if routing_review:
                    routing.validate_request(event['request'], actual_settings['profile'])
                equivalent = (routing.same_request_before_and_after_routing(
                    pending['request'], event['request'], routing_review) if pending and routing_review
                    else not pending or pending['request'] == event['request'])
                if not equivalent:
                    raise runner.Stop('Recovery found changed inputs after an unanswered request.')
                pending = event
            elif event['kind'] == 'response':
                if (not pending or pending['request_id'] != event['request_id'] or
                        not routing.valid_response(event['response'], actual_settings['profile'])):
                    raise runner.Stop('Cannot replay an invalid, unbilled or truncated response.')
                pairs.append((pending['request'], event['response']))
                pending = None
            elif event['kind'] == 'error' and event['error_type'] not in runner.audit.TRANSIENT_ERRORS:
                raise runner.Stop('Non-transient error requires review before recovery.')
        if path in reviewed_sources and (pending is None or len(pairs) != reviewed_sources[path]['saved_responses']):
            raise runner.Stop('Reviewed response count or pending request mismatch.')
        if path == disk_source and (pending is not None or len(pairs) != disk_review['saved_responses']):
            raise runner.Stop('Disk recovery response count or request state mismatch.')
        if path in credit_sources and (pending is None or len(pairs) != credit_sources[path]['saved_responses']):
            raise runner.Stop('Credit recovery response count or pending request mismatch.')
        return pairs, pending

    def history(path, settings, seen=None):
        # Keep pending as a request EVENT throughout ancestry traversal. The
        # frozen reader unwraps it recursively, which breaks a second resume
        # when an ancestor ended with an unanswered request.
        pairs, pending = walk(path, settings, set() if seen is None else seen)
        return pairs, pending['request'] if pending else None

    return history


def effective_plan(root, plan, workers, amendment):
    if (amendment['plan_sha256'] != runner.digest(root / 'plan.json') or
            amendment['original'] != {'max_workers': plan['max_workers'],
                                      'per_model_workers': plan['per_model_workers']} or
            amendment['amended'] != {'max_workers': 8, 'per_model_workers': 4}):
        raise runner.Stop('Concurrency amendment does not match frozen collection.')
    if not 1 <= workers <= 8:
        raise runner.Stop('Workers must be 1–8.')
    # New dictionary only: never overwrite the frozen plan or scientific fields.
    return {**plan, **(amendment['amended'] if workers > 4 else amendment['original'])}


def ensure_disk_space(root, minimum):
    free = shutil.disk_usage(root).free
    if free < minimum:
        raise runner.Stop(f'Low disk space: {free / 1024**3:.2f} GiB free; '
                          f'need at least {minimum / 1024**3:.2f} GiB before new inference. '
                          'Existing attempts preserved; free space and resume.')
    return free


def disk_guarded_factory(root, minimum, base_factory=None):
    base_factory = runner.measured_chat if base_factory is None else base_factory
    def factory(profile, path, key, stop):
        live = base_factory(profile, path, key, stop)
        def chat(messages, tools):
            ensure_disk_space(root, minimum)
            return live(messages, tools)
        return chat
    return factory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arm', choices=runner.ARMS)
    parser.add_argument('--out', type=Path, default=runner.DEFAULT_ROOT)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--check', action='store_true', help='Validate recovery without inference.')
    args = parser.parse_args()
    root = args.out.resolve()
    plan = runner.check(root)
    routing_review = (routing.load_amendment(root, plan)
                      if (root / routing.REVIEW).exists() else None)
    amendment = runner.read(root / CONCURRENCY_REVIEW)
    plan = effective_plan(root, plan, args.workers, amendment)
    if routing_review:
        plan = routing.effective_plan(plan, routing_review)
        print('Muse routing: DeepInfra -> Phala -> Fireworks -> Together; same model, '
              'required parameters, logged provider per response.', flush=True)
        print('Transient retries: 15s, 30s, 60s, 60s, 60s; saved decisions are replayed.', flush=True)
    free = ensure_disk_space(root, amendment['min_free_bytes'])
    print(f'Concurrency: up to {args.workers} total, {plan["per_model_workers"]} per model. '
          f'Disk free: {free / 1024**3:.2f} GiB.', flush=True)
    review = runner.read(root / REVIEW)
    network_review_paths = sorted(p for p in (root / 'reviews').glob('empty_network_response_*.json')
                                  if p.resolve() != (root / REVIEW).resolve())
    network_reviews = [runner.read(p) for p in network_review_paths]
    credit_review_paths = sorted((root / 'reviews').glob('credit_rejections_*.json'))
    credit_reviews = [item for p in credit_review_paths for item in runner.read(p)['sources']]
    disk_review = runner.read(root / DISK_REVIEW) if (root / DISK_REVIEW).exists() else None
    original = runner.history
    original_check, original_execute = runner.check, runner.execute_job
    runner.history = reviewed_history(root, review, original, disk_review, routing_review,
                                     network_reviews, credit_reviews)
    try:
        # Preflight every interrupted job before any worker can issue inference.
        for job in plan['jobs']:
            if job['arm'] != args.arm or runner.completed(root, job):
                continue
            attempts = sorted(runner.job_directory(root, job).glob('attempt-*'),
                              key=lambda p: int(p.name.split('-')[-1]))
            if attempts:
                settings = {'job': job, 'profile': plan['profiles'][job['spec']['model']],
                            'plan_sha256': runner.digest(root / 'plan.json')}
                pairs, pending = runner.history(attempts[-1], settings)
                print(f'Recovery checked: {job["job_id"]}; {len(pairs)} saved responses.', flush=True)
        if args.check:
            print('Recovery checks passed. No inference requested.')
        else:
            runner.append(root / 'reviews/reviewed_invocations.jsonl', {
                'at': runner.audit.now(), 'arm': args.arm, 'workers': args.workers,
                'per_model_workers': plan['per_model_workers'], 'free_bytes': free,
                'plan_sha256': runner.digest(root / 'plan.json'),
                'wrapper_sha256': runner.digest(Path(__file__)),
                'concurrency_review_sha256': runner.digest(root / CONCURRENCY_REVIEW),
                'routing_review_sha256': runner.digest(root / routing.REVIEW) if routing_review else None,
                'routing_module_sha256': runner.digest(Path(routing.__file__)) if routing_review else None,
                'network_review_sha256': {str(p.relative_to(root)): runner.digest(p)
                                         for p in [root / REVIEW, *network_review_paths]},
                'credit_review_sha256': {str(p.relative_to(root)): runner.digest(p)
                                        for p in credit_review_paths},
                'min_free_bytes': amendment['min_free_bytes']})
            def runtime_plan(selected):
                checked = original_check(selected)
                policy = routing.load_amendment(selected, checked) if routing_review else None
                updated = effective_plan(selected, checked, args.workers, amendment)
                return routing.effective_plan(updated, policy) if policy else updated
            runner.check = runtime_plan
            runner.execute_job = partial(original_execute, chat_factory=disk_guarded_factory(
                root, amendment['min_free_bytes'], routing.measured_chat if routing_review else None))
            runner.run(root, args.arm, resume=True, workers=args.workers)
    finally:
        runner.history = original
        runner.check, runner.execute_job = original_check, original_execute


if __name__ == '__main__':
    try:
        main()
    except runner.Stop as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
