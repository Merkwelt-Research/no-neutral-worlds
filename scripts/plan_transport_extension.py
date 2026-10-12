"""Build a reviewable transport matrix and measured-cost scenarios; no API calls."""
from __future__ import annotations

import argparse
from collections import Counter
import dataclasses
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tnt_bench.action_protocol import DISCLOSED_JOURNAL_PROTOCOL
from tnt_bench.engine import generate_schedule
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.run import RunSpec
from tnt_bench.harness.discrepancy import DiscrepancyGroupSpec
from tnt_bench.themes import ThemedView, load_theme
from tnt_bench.engine import Engine, EngineConfig

CALIBRATION = ROOT / 'runs/transport_calibration_low_2026-09-19'
DESTINATION = ROOT / 'runs/transport_extension_2026-09-20'
MODELS = ('google/gemini-3.7-flash', 'z-ai/glm-5.3-flash',
          'meta/muse-glimmer-30b', 'moonshotai/kimi-k3')
QUEUE_SEED = 'tnt-transport-extension-2026-09-20'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seed_sets(allocation='fuller'):
    # Selection is numerical, without inspection of trajectory outcomes.
    old = list(range(13, 23))
    fresh = list(range(900101, 900111))
    if allocation == 'existing':
        return old, old
    return ((old + fresh, old[:5] + fresh[:5]) if allocation == 'fuller'
            else (old[:5] + fresh[:5], old[:3] + fresh[:3]))


def build_matrix(profiles, allocation='fuller', models=MODELS):
    core_seeds, support_seeds = seed_sets(allocation)
    entries = []
    groups = []
    core_replicates = (1, 2) if allocation == 'existing' else (1,)
    for model in models:
        common = dict(model=model, horizon=90, temperature=profiles[model]['temperature'],
                      action_protocol=DISCLOSED_JOURNAL_PROTOCOL)
        def add(arm, seed, frame, richness='static', **kw):
            spec = RunSpec(condition=Condition(frame, richness), schedule_seed=seed, **common, **kw)
            entries.append({'arm': arm, 'schedule_origin': 'fresh' if seed >= 900101 else 'existing',
                            'run_id': spec.run_id, 'spec': dataclasses.asdict(spec)})
        for seed, frame, richness, replicate in itertools.product(core_seeds, ('fantasy', 'neutral'), ('static', 'rich'), core_replicates):
            add('baseline_frame', seed, frame, richness, replicate=replicate)
        for seed, frame, creed in itertools.product(support_seeds, ('fantasy', 'neutral'), ('full', 'lean')):
            add('frame_doctrine', seed, f'{frame}_crossover_{creed}')
        for seed, creed, charge in itertools.product(support_seeds, ('full', 'lean'), (0.0, 0.5)):
            add('doctrine_economy', seed, f'fantasy_creed_{creed}', carrying_cost=charge)
        for seed, frame, condition in itertools.product(support_seeds, ('fantasy', 'neutral'),
                                                        ('ambiguous', 'ambiguous_wit', 'explicit', 'explicit_wit')):
            add('exploit', seed, frame, 'rich', exploit_condition=condition)
        for seed, frame, endpoint, objective in itertools.product(support_seeds, ('fantasy', 'neutral'), (False, True), (False, True)):
            add('endpoint_objective', seed, frame, disclose_horizon=endpoint, score_objective=objective)
        for seed, frame, replicate in itertools.product(core_seeds, ('fantasy', 'neutral'), core_replicates):
            group = DiscrepancyGroupSpec(model=model, condition=Condition(frame, 'rich'),
                schedule_seed=seed, normative_climate='baseline', horizon=90,
                discrepancy_kinds=('extra_stock', 'missing_stock'), observation_days=10,
                temperature=profiles[model]['temperature'], randomize_seed=QUEUE_SEED,
                action_protocol=DISCLOSED_JOURNAL_PROTOCOL, replicate=replicate)
            groups.append({'prefix_id': group.prefix_id, 'spec': dataclasses.asdict(group),
                           'branches': [group.branch_id(day, kind) for day in group.reveal_days
                                        for kind in group.discrepancy_kinds]})
    assert len({e['run_id'] for e in entries}) == len(entries)
    # Keep each model/arm/schedule block contiguous, shuffle blocks and cells.
    blocks = {}
    for entry in entries:
        spec = entry['spec']
        blocks.setdefault((spec['model'], entry['arm'], spec['schedule_seed']), []).append(entry)
    rng = random.Random(QUEUE_SEED)
    block_values = list(blocks.values())
    rng.shuffle(block_values)
    for block in block_values:
        rng.shuffle(block)
    rng.shuffle(groups)
    return [e for block in block_values for e in block], groups


def measured_costs():
    result = {}
    for model in MODELS:
        directory = CALIBRATION / 'full/attempt-1' / (model.replace('/', '_') + '__ordinary')
        outcome = read(next(directory.glob('*/result.json')))
        assert outcome['days_survived'] == 90 and outcome['end_reason'] == 'completed'
        assert read(directory / 'complete.json')['technical_gate']['pass']
        rows = [json.loads(x) for x in (directory / 'api_calls.jsonl').read_text(encoding='utf-8').splitlines()]
        responses = [x for x in rows if x['kind'] == 'response']
        result[model] = {'usd_per_90_days': sum(x['response']['usage']['cost'] for x in responses),
                         'request_seconds_per_90_days': sum(x['seconds'] for x in responses),
                         'source': str(directory.relative_to(ROOT)), 'api_sha256': sha(directory / 'api_calls.jsonl')}
    return result


def prepare(destination, allocation='fuller'):
    if (destination / 'design.json').exists():
        raise ValueError('Design already exists; use a different --out for a revision.')
    source_plan = read(CALIBRATION / 'plan.json')
    profiles = {p['model']: p for p in source_plan['profiles'] if p['model'] in MODELS}
    entries, groups = build_matrix(profiles, allocation)
    costs = measured_costs()
    core, support = seed_sets(allocation)
    artifacts = {}
    for seed in core:
        path = destination / 'schedules' / f's{seed}__h90.yml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generate_schedule(seed, 90).to_yaml(), encoding='utf-8')
        artifacts[str(path.relative_to(destination))] = sha(path)
    packs = []
    for seed, frame in itertools.product(core, ('fantasy', 'neutral')):
        name = f'pack__{frame}__s{seed}__h90.yml'
        source = ROOT / 'runs/replication1/packs' / name
        packs.append({'frame': frame, 'seed': seed, 'filename': name,
                      'source': str(source.relative_to(ROOT)) if source.exists() else None,
                      'sha256': sha(source) if source.exists() else None,
                      'status': 'existing_frozen' if source.exists() else 'generation_required'})
    # Export every independent-factor prompt for inspection before registration.
    for frame, endpoint, objective in itertools.product(('fantasy', 'neutral'), (False, True), (False, True)):
        view = ThemedView(Engine(EngineConfig(horizon=90), generate_schedule(core[0], 90)),
                          load_theme(frame), disclose_horizon=endpoint, score_objective=objective,
                          action_protocol=DISCLOSED_JOURNAL_PROTOCOL)
        path = destination / 'prompts' / f'{frame}__endpoint{int(endpoint)}__objective{int(objective)}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(view.system_prompt(), encoding='utf-8')
        artifacts[str(path.relative_to(destination))] = sha(path)
    full_per_model = len(entries) // len(MODELS)
    prefix_per_model = len(groups) // len(MODELS)
    branch_per_model = prefix_per_model * 4
    days_per_model = full_per_model * 90 + prefix_per_model * 45 + branch_per_model * 10
    equivalents = days_per_model / 90
    for value in costs.values():
        value['ordinary_rate_projection_usd'] = value['usd_per_90_days'] * equivalents
        value['ordinary_rate_projection_request_hours'] = value['request_seconds_per_90_days'] * equivalents / 3600
    dollars = sum(v['ordinary_rate_projection_usd'] for v in costs.values())
    hours = sum(v['ordinary_rate_projection_request_hours'] for v in costs.values())
    design = {'status': 'DRAFT_NOT_REGISTERED_NOT_RUNNABLE', 'allocation': allocation,
        'models': list(MODELS), 'profiles_from_calibration': profiles,
        'calibration_plan_sha256': sha(CALIBRATION / 'plan.json'),
        'core_seeds': core, 'support_seeds': support, 'excluded_calibration_seeds': [12, 900001],
        'queue_seed': QUEUE_SEED, 'action_protocol': DISCLOSED_JOURNAL_PROTOCOL,
        'full_trajectory_queue': entries, 'discrepancy_groups': groups,
        'counts': {'full_trajectories': len(entries), 'prefixes': len(groups),
                   'branches': len(groups)*4, 'maximum_model_days': days_per_model*len(MODELS),
                   'full_per_model': full_per_model, 'prefixes_per_model': prefix_per_model,
                   'branches_per_model': branch_per_model,
                   'full_by_arm': dict(Counter(e['arm'] for e in entries))},
        'cost_measurements': costs,
        'scenarios': [{'multiplier': factor, 'usd': dollars*factor, 'serial_request_hours': hours*factor,
                       'ideal_days_at_8_workers': hours*factor/8/24} for factor in (1, 2, 3)],
        'cost_limitations': 'One ordinary run per model. Scenario multipliers are assumptions, not confidence bounds. Excludes narration generation, revised-protocol checks, retries and audits.',
        'packs': packs, 'artifact_hashes': artifacts,
        'freeze_requirements': ['Confirm allocation and K3 selection', 'Generate and audit fresh narration packs',
            'Review endpoint/objective prompt exports and coding definitions', 'Validate revised protocol with short technical checks',
            'Implement and dry-run full collection orchestration, checkpoint recovery and analysis',
            'Snapshot providers/prices and hash final sources, matrix, prompts, packs and analysis',
            'Post registration before main collection']}
    write(destination / 'design.json', design)
    print(json.dumps({'counts': design['counts'], 'scenarios': design['scenarios'],
                      'new_packs_needed': sum(p['status']=='generation_required' for p in packs)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DESTINATION)
    parser.add_argument('--allocation', choices=['fuller', 'leaner'], default='fuller')
    args = parser.parse_args()
    prepare(args.out.resolve(), args.allocation)
