"""Offline paired endpoint/objective estimates from final, provenance-checked codes.

This module never assigns semantic codes. Five journals form one trajectory rate;
two frames are averaged within a schedule. Bootstrap resampling uses schedules.
"""
from collections import defaultdict
import hashlib
import random
import statistics as st
from pathlib import Path

BOOTSTRAP_SEED = 20260920
CELLS = ((False, False), (True, False), (False, True), (True, True))
WEIGHTS = {
    'endpoint_without_score': {(True, False): 1, (False, False): -1},
    'endpoint_with_score': {(True, True): 1, (False, True): -1},
    'interaction': {(True, True): 1, (False, True): -1, (True, False): -1, (False, False): 1},
    'score_without_endpoint': {(False, True): 1, (False, False): -1},
    'score_with_endpoint': {(True, True): 1, (True, False): -1},
}


def estimate(values):
    values = list(values)
    n = len(values)
    assert n > 1
    rng = random.Random(BOOTSTRAP_SEED)
    boot = sorted(sum(rng.choice(values) for _ in values)/n for _ in range(10000))
    return dict(n_schedules=n, mean=st.mean(values), ci95=[boot[249], boot[9749]],
                positive_schedules=sum(v > 1e-10 for v in values),
                negative_schedules=sum(v < -1e-10 for v in values),
                zero_schedules=sum(abs(v) <= 1e-10 for v in values))


def semantic_summary(records, models, seeds=range(13, 23)):
    seeds = tuple(seeds)
    keys = [(r['model'], r['seed'], r['frame'], r['endpoint'], r['objective'], r['day']) for r in records]
    expected = {(m,s,f,e,o,d) for m in models for s in seeds for f in ('fantasy','neutral')
                for e,o in CELLS for d in range(86,91)}
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('Final-week coding matrix is incomplete or duplicated; do not silently drop trajectories.')
    if any(r['forced'] or not r['journal'].strip() or type(r['final_code']) is not int or r['final_code'] not in (0,1) for r in records):
        raise ValueError('This complete-cohort analysis requires available, unforced, finally coded journals; missingness needs explicit bounds.')
    output = {}
    for model in models:
        selected = [r for r in records if r['model'] == model]
        by_cell_seed = defaultdict(list)
        for r in selected:
            by_cell_seed[(r['endpoint'],r['objective']), r['seed']].append(r)
        values = {cell:{str(s):st.mean(r['final_code'] for r in by_cell_seed[cell,s]) for s in seeds} for cell in CELLS}
        cells = []
        for e,o in CELLS:
            rs = [r for r in selected if (r['endpoint'],r['objective']) == (e,o)]
            cells.append(dict(endpoint=e, objective=o, trajectories=len(rs)//5,
                journals=len(rs), positive=sum(r['final_code'] for r in rs),
                ambiguous=sum(r['ambiguous'] for r in rs), schedule_rates=values[e,o],
                **estimate(values[e,o].values()),
                by_frame={f:dict(positive=sum(r['final_code'] for r in rs if r['frame']==f),
                                journals=sum(r['frame']==f for r in rs)) for f in ('fantasy','neutral')},
                by_day={str(d):dict(positive=sum(r['final_code'] for r in rs if r['day']==d),
                                   journals=sum(r['day']==d for r in rs)) for d in range(86,91)},
                first_pass_positive={key:sum(r[key] for r in rs) for key in ('rater_a','rater_b')}))
        contrasts = {}
        for name, weights in WEIGHTS.items():
            paired = {str(s):sum(w*values[cell][str(s)] for cell,w in weights.items()) for s in seeds}
            bounds = {}
            for s in seeds:
                low = high = 0.
                for cell,w in weights.items():
                    for r in by_cell_seed[cell,s]:
                        a,b = (0,1) if r['ambiguous'] else (r['final_code'],r['final_code'])
                        low += min(w*a,w*b)/10
                        high += max(w*a,w*b)/10
                bounds[str(s)] = [low,high]
            # Linear contrasts attain these bounds by setting each flagged code
            # according to its coefficient; this covers every joint assignment.
            contrasts[name] = dict(schedule_contrasts=paired, **estimate(paired.values()),
                ambiguity_sensitivity=dict(mean_range=[st.mean(v[0] for v in bounds.values()),st.mean(v[1] for v in bounds.values())],
                    schedule_ranges=bounds, all_schedules_positive_under_every_assignment=all(v[0] > 1e-10 for v in bounds.values())))
        output[model] = dict(cells=cells, contrasts=contrasts)
    return output


def summarize_endpoint(records, data, root):
    models = sorted({d['job']['spec']['model'] for d in data})
    semantic = semantic_summary(records, models)
    trajectories = []
    for d in data:
        spec = d['job']['spec']
        days = d['days']
        assert [x['day'] for x in days] == list(range(1,91)) and d['survived']
        rs = [r for r in records if r['id'].rsplit('__day',1)[0] == d['job']['job_id']]
        assert len(rs) == 5
        orders = [x['day'] for x in days for c in x['tool_calls'] if c['tool']=='place_order' and c['result'].get('ok')]
        assert orders, 'Last-order day is undefined for a never-ordering trajectory; do not replace with zero.'
        trajectories.append(dict(id=d['job']['job_id'],model=spec['model'],seed=spec['schedule_seed'],
            frame=spec['condition']['framing'],endpoint=spec['disclose_horizon'],objective=spec['score_objective'],
            positive=sum(r['final_code'] for r in rs),closing_rate=st.mean(r['final_code'] for r in rs),
            last_order_day=max(orders),source=str((d['folder']/'days.jsonl').relative_to(root)),
            source_sha256=rs[0]['artifact_sha256']))
    for model in models:
        ts = [t for t in trajectories if t['model']==model]
        mechanical = {}
        for o in (False,True):
            paired = {str(s):st.mean(t['last_order_day'] for t in ts if t['seed']==s and t['objective']==o and t['endpoint'])
                      - st.mean(t['last_order_day'] for t in ts if t['seed']==s and t['objective']==o and not t['endpoint']) for s in range(13,23)}
            mechanical[str(o).lower()] = dict(schedule_contrasts=paired, **estimate(paired.values()),
                hidden_mean=st.mean(t['last_order_day'] for t in ts if t['objective']==o and not t['endpoint']),
                disclosed_mean=st.mean(t['last_order_day'] for t in ts if t['objective']==o and t['endpoint']))
        semantic[model]['last_order_exploratory'] = mechanical
    return dict(models=semantic, trajectories=trajectories,
        availability=dict(planned_trajectories=len(data),reached_day86=len(data),completed_day90=len(data),
                          available_final_week_journals=len(records),forced_or_missing_journals=0),
        provenance=dict(coding_sha256=hashlib.sha256((root/'coding/endpoint_objective.jsonl').read_bytes()).hexdigest(),
                        bootstrap_seed=BOOTSTRAP_SEED,bootstrap_resamples=10000,
                        inference='Supporting descriptive contrasts; 95% percentile paired-schedule bootstrap. Two frames averaged within each of ten schedules. No additional primary hypothesis tests.',
                        sensitivity='Sharp ranges across every joint 0/1 assignment to the eight retained ambiguous entries; uncertainty from first-pass rule interpretation is documented separately.',
                        semantic_definition='Assignment-ending language, including prospective trading countdowns; not necessarily an enacted farewell.'))


def main():
    import argparse
    import json
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from scripts import analyse_transport_extension as base
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=base.runner.DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.out.resolve()
    plan = base.runner.check(root)
    data = base.data_for(root,plan,'endpoint_objective')
    records = base.export_coding(root,data,'endpoint_objective')
    result = dict(arm='endpoint_objective',coding_records=len(records),coded=len(records),
                  **summarize_endpoint(records,data,root))
    result['provenance']['analysis_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['provenance']['analysis_timing'] = 'Offline implementation completed after data collection and semantic adjudication, implementing the registered supporting contrasts; frozen collection sources unchanged.'
    base.runner.write(root/'analysis/endpoint_objective.json',result)
    print(json.dumps({m:{k:{'mean':v['mean'],'ci95':v['ci95'],'ambiguity_range':v['ambiguity_sensitivity']['mean_range']} for k,v in r['contrasts'].items()} for m,r in result['models'].items()},indent=2))


if __name__ == '__main__':
    main()
