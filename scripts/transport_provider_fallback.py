"""Documented provider routing and bounded retries for the transport wrapper.

The frozen runner remains unchanged. Each new attempt stores its effective
profile; recovery accepts only the exact original/amended profile pair.
"""
from __future__ import annotations

import copy
import json
import re
import time

from scripts import run_transport_extension as runner

REVIEW = 'reviews/provider_routing_amendment_2026-09-23.json'
RETRY_DELAYS = (15, 30, 60, 60, 60)
TRANSPORT_FIELDS = {'provider', 'endpoint_tag', 'endpoint_tags', 'expected_provider',
                    'allowed_providers', 'quantization', 'pricing', 'ceiling_rates',
                    'routing_policy_id', 'provider_catalogue'}


def load_amendment(root, plan):
    amendment = runner.read(root / REVIEW)
    if amendment['plan_sha256'] != runner.digest(root / 'plan.json'):
        raise runner.Stop('Provider amendment does not match frozen plan.')
    snapshot = root / amendment['catalogue_path']
    if runner.digest(snapshot) != amendment['catalogue_sha256']:
        raise runner.Stop('Provider catalogue snapshot changed.')
    for model, profiles in amendment['profiles'].items():
        old, new = profiles['original'], profiles['amended']
        if plan['profiles'][model] != old:
            raise runner.Stop('Provider amendment original profile mismatch.')
        unchanged = lambda p: {k: v for k, v in p.items() if k not in TRANSPORT_FIELDS}
        if unchanged(old) != unchanged(new):
            raise runner.Stop('Provider amendment changes scientific sampling settings.')
        if new['model'] != model or new['provider']['require_parameters'] is not True:
            raise runner.Stop('Invalid model or parameter requirements in routing amendment.')
    return amendment


def effective_plan(plan, amendment):
    updated = copy.deepcopy(plan)
    for model, profiles in amendment['profiles'].items():
        if plan['profiles'][model] != profiles['original']:
            raise runner.Stop('Unexpected starting provider profile.')
        updated['profiles'][model] = copy.deepcopy(profiles['amended'])
    return updated


def compatible_settings(actual, expected, amendment):
    if actual == expected:
        return True
    if {k:v for k,v in actual.items() if k != 'profile'} != {k:v for k,v in expected.items() if k != 'profile'}:
        return False
    profiles = amendment['profiles'].get(expected['profile']['model'])
    return bool(profiles and expected['profile'] == profiles['amended'] and
                actual['profile'] == profiles['original'])


def valid_response(response, profile):
    if 'allowed_providers' not in profile:
        return runner.valid_response(response, profile)
    if (response.get('provider') not in profile['allowed_providers'] or
            response.get('model') != profile['model']):
        return False
    # Retain the frozen billing/finish checks; only provider membership differs.
    return runner.valid_response(response, {**profile, 'expected_provider': response['provider']})


def validate_request(request, profile):
    """Ensure routing metadata and recorded request agree, before replay."""
    expected = {'model': profile['model'], 'temperature': profile['temperature'],
                'max_tokens': profile['max_tokens']}
    body = request.get('extra_body') or {}
    if (any(request.get(k) != v for k,v in expected.items()) or
            body.get('provider') != profile['provider'] or
            body.get('reasoning') != profile['reasoning']):
        raise runner.Stop('Recorded request differs from its provider/sampling profile.')


def same_request_before_and_after_routing(left, right, amendment):
    if left == right:
        return True
    profiles = amendment['profiles'].get(left.get('model'))
    if not profiles or left.get('model') != right.get('model'):
        return False
    a, b = copy.deepcopy(left), copy.deepcopy(right)
    old_provider = (a.get('extra_body') or {}).pop('provider', None)
    new_provider = (b.get('extra_body') or {}).pop('provider', None)
    return (a == b and old_provider == profiles['original']['provider'] and
            new_provider == profiles['amended']['provider'])


def measured_chat(profile, path, key, stop):
    """Log every actual request/response; retry transient failures up to six times."""
    budget = runner.audit.Budget(path.parent, None)
    state = {}

    def before(request):
        if stop.is_set():
            raise runner.Stop('Batch interrupted; request not sent.')
        nbytes = len(json.dumps(request, ensure_ascii=False).encode('utf-8')) + 4096
        rates = profile['ceiling_rates']
        request_id = budget.reserve(2*(nbytes*rates['prompt'] + profile['max_tokens']*rates['completion']), path.parent.name)
        state.update(request_id=request_id, start=time.monotonic())
        match = re.search(r'=== DAY (\d+)', request['messages'][1]['content'])
        runner.append(path, {'kind':'request', 'at':runner.audit.now(), 'request_id':request_id,
                            'day':int(match.group(1)) if match else None, 'request':request})

    def after(response):
        runner.append(path, {'kind':'response', 'at':runner.audit.now(), 'request_id':state['request_id'],
                            'seconds':time.monotonic()-state['start'], 'response':response})
        if not budget.settle(state['request_id'], (response.get('usage') or {}).get('cost')):
            raise runner.Stop('Missing/invalid billing cost; reservation preserved.')
        if not valid_response(response, profile):
            raise runner.Stop('Unexpected provider/model, missing choices or truncated output; response preserved for review.')

    client = runner.openai_chat_client(key, profile['model'], temperature=profile['temperature'], max_retries=0,
        provider=profile['provider'], reasoning=profile['reasoning'], max_tokens=profile['max_tokens'],
        strict=True, before_request=before, on_response=after)

    def chat(messages, tools):
        for attempt in range(len(RETRY_DELAYS)+1):
            try:
                return client(messages, tools)
            except runner.Stop:
                raise
            except Exception as error:
                runner.append(path, {'kind':'error', 'at':runner.audit.now(),
                    'request_id':state.get('request_id'), 'error_type':type(error).__name__,
                    'message':str(error)[:1000]})
                if type(error).__name__ not in runner.audit.TRANSIENT_ERRORS or attempt == len(RETRY_DELAYS):
                    raise runner.Stop(f'{type(error).__name__}; attempt preserved. Resume after the service recovers.') from error
                delay = RETRY_DELAYS[attempt]
                # Honour short Retry-After headers; all waits remain <=60 seconds.
                headers = getattr(getattr(error, 'response', None), 'headers', {}) or {}
                try:
                    delay = max(delay, min(60, float(headers.get('retry-after', 0))))
                except (TypeError, ValueError):
                    pass
                runner.append(path, {'kind':'retry_wait', 'at':runner.audit.now(),
                    'request_id':state.get('request_id'), 'seconds':delay, 'retry':attempt+1})
                print(f'{profile["model"]}: {type(error).__name__}; waiting {delay:g}s before retry {attempt+1}/{len(RETRY_DELAYS)}.', flush=True)
                if stop.wait(delay):
                    raise runner.Stop('Batch interrupted; retry not sent.') from error
    return chat
