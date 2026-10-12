"""Count recorded API responses across all attempts; no inference or billing calls."""
from collections import Counter
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_transport_extension import DEFAULT_ROOT, ARMS


def main():
    root = DEFAULT_ROOT.resolve()
    arms = {}
    seen = set()
    for arm in ARMS:
        stats = dict(responses=0,prompt_tokens=0,completion_tokens=0,reported_cost_usd=0.,
                     missing_cost=0,missing_token_counts=0,providers=Counter())
        for path in sorted((root/arm).glob('*/attempt-*/api_calls.jsonl')):
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    r = json.loads(line)
                    if r['kind'] != 'response': continue
                    key = r['request_id']
                    assert key not in seen, 'Duplicate saved response; examine replay accounting.'
                    seen.add(key)
                    u = r['response'].get('usage') or {}
                    stats['responses'] += 1
                    stats['providers'][r['response'].get('provider') or 'unreported'] += 1
                    for field in ('prompt_tokens','completion_tokens'):
                        if isinstance(u.get(field),int): stats[field] += u[field]
                        else: stats['missing_token_counts'] += 1
                    c = u.get('cost')
                    if isinstance(c,(int,float)) and math.isfinite(c) and c >= 0: stats['reported_cost_usd'] += c
                    else: stats['missing_cost'] += 1
        stats['providers'] = dict(stats['providers'])
        arms[arm] = stats
    total = {k:sum(a[k] for a in arms.values()) for k in next(iter(arms.values())) if k!='providers'}
    providers = Counter()
    for a in arms.values(): providers.update(a['providers'])
    total['providers'] = dict(providers)
    result = dict(scope='Six main extension arms; all recorded responses across attempts, excluding calibration and smoke. Includes failed or truncated returned responses; excludes errors without a returned response. Costs are provider-reported, not reconciled invoices.',arms=arms,total=total)
    (root/'analysis/collection_usage.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
