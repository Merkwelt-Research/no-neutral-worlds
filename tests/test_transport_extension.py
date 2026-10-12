"""Matrix accounting and protocol propagation, using no paid inference."""
import dataclasses
import json

from scripts import plan_transport_extension as planning
from tnt_bench.action_protocol import DISCLOSED_JOURNAL_PROTOCOL
from tnt_bench.agent.day_loop import ChatResponse, ChatToolCall
from tnt_bench.harness.conditions import Condition
from tnt_bench.harness.run import RunSpec, execute_run
from tnt_bench.harness.discrepancy import DiscrepancyGroupSpec, execute_discrepancy_group


def test_matrix_counts_pairs_and_independent_terminal_controls():
    profiles = {m: {'temperature': .7} for m in planning.MODELS}
    runs, groups = planning.build_matrix(profiles)
    assert len(runs) == 1280 and len(groups) == 160
    assert sum(len(g['branches']) for g in groups) == 640
    assert all(r['spec']['schedule_seed'] not in (12, 900001) for r in runs)
    assert len({r['run_id'] for r in runs}) == len(runs)
    for model in planning.MODELS:
        cells = [r for r in runs if r['spec']['model'] == model]
        assert len(cells) == 320
        terminal = [r for r in cells if r['arm'] == 'endpoint_objective']
        assert len(terminal) == 80
        for seed in planning.seed_sets()[1]:
            assert len([r for r in terminal if r['spec']['schedule_seed'] == seed]) == 8
            controls = [r for r in cells if r['arm'] == 'baseline_frame' and
                        r['spec']['schedule_seed'] == seed and r['spec']['condition']['richness'] == 'static']
            assert len(controls) == 2
            assert all(r['spec']['score_objective'] is None for r in controls)
    assert planning.build_matrix(profiles) == (runs, groups)
    lean_runs, lean_groups = planning.build_matrix(profiles, 'leaner')
    assert len(lean_runs) == 736 and len(lean_groups) == 80


ENTRY = 'I have reviewed the daily record. I will retain the relevant observations in this entry and check the stock and balance on the following day.'


def end_chat(messages, tools):
    assert 'You have time for 20 actions per day.' in messages[0]['content']
    return ChatResponse(tool_calls=[ChatToolCall('end', 'end_day', {'reflection': ENTRY})])


def test_run_manifest_separates_new_interface_and_independent_goal(tmp_path):
    spec = RunSpec('test/model', Condition('neutral', 'static'), 900002, horizon=30,
                   action_protocol=DISCLOSED_JOURNAL_PROTOCOL, score_objective=False,
                   disclose_horizon=False)
    assert spec.run_id != dataclasses.replace(spec, score_objective=None).run_id
    result = execute_run(spec, tmp_path, chat=end_chat)
    manifest = json.loads((tmp_path / spec.run_id / 'manifest.json').read_text())
    assert manifest['score_objective'] is False and result['score_objective'] is False
    assert manifest['action_protocol'] == DISCLOSED_JOURNAL_PROTOCOL
    assert result['action_protocol'] == DISCLOSED_JOURNAL_PROTOCOL


def test_new_interface_reaches_prefix_and_all_branches_and_resumes(tmp_path):
    spec = DiscrepancyGroupSpec('test/model', Condition('fantasy', 'static'), 900002,
        normative_climate='baseline', horizon=30, reveal_days=(2, 4), observation_days=2,
        discrepancy_kinds=('extra_stock', 'missing_stock'), action_protocol=DISCLOSED_JOURNAL_PROTOCOL)
    results = execute_discrepancy_group(spec, tmp_path, chat=end_chat)
    assert len(results) == 4
    assert spec.prefix_id != dataclasses.replace(spec, action_protocol='legacy').prefix_id
    for path in tmp_path.rglob('manifest.json'):
        assert json.loads(path.read_text())['action_protocol'] == DISCLOSED_JOURNAL_PROTOCOL
    def forbidden(*args):
        raise AssertionError('Completed branches must not be resampled')
    resumed = execute_discrepancy_group(spec, tmp_path, chat=forbidden)
    assert {r['run_id'] for r in results} == {r['run_id'] for r in resumed}
