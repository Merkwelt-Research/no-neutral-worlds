"""Artifact checks for terminal-objective review; no automatic genre ratings.

Genre readings are documented in README.md. Final-week text is retained for
inspection; extraction does not imply exhaustive semantic review.
"""
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
models = {'google/gemma-4-31b-it', 'qwen/qwen3-235b-a22b-2507'}
marker = runpy.run_path(str(ROOT / 'tnt_bench/analysis/register.py'))['_FRAME_BREAK']
slugs = ['health_potion', 'mana_potion', 'stamina_potion', 'strength_tonic', 'antidote', 'luck_elixir']
mapping = {slug: f'item_{i}' for i, slug in enumerate(slugs, 1)}
mapping.update({f'sku_{i}': f'item_{i}' for i in range(1, 7)})
rows = []
for arm, collection in [('ongoing', 'ablation1'), ('terminal_score', 'main3')]:
    selected = []
    for p in sorted((ROOT / 'runs' / collection).glob('*/result.json')):
        r = json.loads(p.read_text(encoding='utf-8'))
        if r['model'] in models and r['cell'] in {'fantasy-static', 'neutral-static'} and r['schedule_seed'] in range(2, 7):
            selected.append((p, r))
    assert len(selected) == 20
    for index, (p, r) in enumerate(selected, 1):
        path = p.parent
        days = [json.loads(l) for l in (path / 'days.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        assert [d['day'] for d in days] == list(range(1, 91))
        orders, arrivals, floor, prices = {}, set(), {f'item_{i}': 8 for i in range(1, 7)}, {}
        last_order = 0
        fire_loss = 0
        for d in days:
            arrivals.update(a['order_id'] for a in d['arrivals'])
            for c in d['tool_calls']:
                v = c['result']
                if c['tool'] == 'place_order' and v.get('ok'):
                    orders[v['order_id']] = v
                    last_order = d['day']
                    item = mapping[v['item_id']]
                    floor[item] = min(floor[item], v['unit_cost'])
                if c['tool'] == 'set_price' and v.get('ok'):
                    prices[mapping[c['args']['item_id']]] = c['args']['price']
                assert c['tool'] != 'cancel_order', 'Pending reconstruction assumes no cancellations'
            if d['day'] >= 84:
                fire_loss += sum(q * max(0, floor[item] - prices.get(item, floor[item])) for item, q in d['sales'].items())
        pending = {oid: v for oid, v in orders.items() if oid not in arrivals}
        # Independently reconcile with final-day shop snapshot plus subsequent orders.
        final_checks = [(i, c) for i, c in enumerate(days[-1]['tool_calls']) if c['tool'] == 'check_shop']
        i, last_check = final_checks[-1]
        observed = {o['order_id']: o for o in last_check['result']['pending_orders']}
        for c in days[-1]['tool_calls'][i+1:]:
            if c['tool'] == 'place_order' and c['result'].get('ok'):
                observed[c['result']['order_id']] = c['result']
        assert {k: v['qty'] for k, v in pending.items()} == {k: v['qty'] for k, v in observed.items()}
        matches = [d['day'] for d in days if not d['forced'] and marker.search(d['reflection'])]
        transcript = [json.loads(l) for l in (path / 'transcript.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        # Check final-day reflection against its raw assistant tool argument.
        final_reflections = []
        for t in transcript:
            if t['day'] != 90 or t['role'] != 'assistant':
                continue
            for call in t.get('tool_calls') or []:
                f = call['function']
                if f['name'] == 'end_day':
                    args = f['arguments']
                    args = json.loads(args) if isinstance(args, str) else args
                    final_reflections.append(args.get('reflection'))
        assert days[-1]['reflection'] in final_reflections
        rows.append({'case_id': ('O' if arm == 'ongoing' else 'T') + f'{index:02d}',
                     'arm': arm, 'run_id': r['run_id'], 'model': r['model'], 'frame': r['cell'], 'seed': r['schedule_seed'],
                     'source': str(path.relative_to(ROOT)).replace('\\', '/'),
                     'source_sha256': {name: hashlib.sha256((path / name).read_bytes()).hexdigest() for name in ('result.json', 'days.jsonl', 'transcript.jsonl')},
                     'last_order_day': last_order, 'final_pending_units': sum(v['qty'] for v in pending.values()),
                     'final_pending_orders': list(observed.values()), 'frame_break_days': matches,
                     'final_week_below_cost_loss': fire_loss,
                     'final_week': [{'day': d['day'], 'reflection': d['reflection'], 'tool_calls': d['tool_calls'], 'arrivals': d['arrivals']} for d in days if d['day'] >= 84]})
(OUT / 'evidence.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
summary = {}
for arm in ['ongoing', 'terminal_score']:
    group = [r for r in rows if r['arm'] == arm]
    summary[arm] = {'runs': len(group), 'pending_units': sum(r['final_pending_units'] for r in group),
                    'runs_with_pending_units': sum(r['final_pending_units'] > 0 for r in group),
                    'last_order_means': {m: sum(r['last_order_day'] for r in group if r['model'] == m) / 10 for m in sorted(models)},
                    'lexical_match_days': sum(len(r['frame_break_days']) for r in group),
                    'lexical_match_days_81_90': sum(sum(d >= 81 for d in r['frame_break_days']) for r in group),
                    'runs_exceeding_loss_10': sum(r['final_week_below_cost_loss'] > 10 for r in group)}
(OUT / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=2))
