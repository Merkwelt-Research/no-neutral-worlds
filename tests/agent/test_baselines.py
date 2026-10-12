"""Baseline policies: floor, comfortable middle, and ceiling (spec §6.3)."""

from tnt_bench.agent import heuristic_policy, oracle_policy, random_policy
from tnt_bench.agent.baselines import Policy
from tnt_bench.engine import Engine, EngineConfig, generate_schedule
from tnt_bench.themes import ThemedView, load_theme

FANTASY = load_theme("fantasy")


def run_policy(policy: Policy, seed: int = 42, horizon: int = 30):
    engine = Engine(EngineConfig(horizon=horizon), generate_schedule(seed, horizon))
    view = ThemedView(engine, FANTASY)
    reports = []
    while not view.done:
        dawn_report = view.dawn()
        reflection = policy(view, dawn_report)
        view.end_day(reflection)
        reports.append(view.dusk())
    return engine, reports


def test_heuristic_matches_m1_golden():
    engine, reports = run_policy(heuristic_policy())
    assert reports[-1]["end_reason"] == "completed"
    assert engine.net_worth() == 2830  # re-pinned under proportional stakes + valuation (was 2976)


def test_random_is_deterministic_per_seed():
    engine_a, _ = run_policy(random_policy(7), seed=7)
    engine_b, _ = run_policy(random_policy(7), seed=7)
    assert engine_a.net_worth() == engine_b.net_worth()
    assert engine_a.state.ledger == engine_b.state.ledger


def test_oracle_beats_heuristic_across_seeds():
    for seed in range(5):
        heuristic_engine, _ = run_policy(heuristic_policy(), seed=seed)
        oracle_engine, oracle_reports = run_policy(oracle_policy(
            generate_schedule(seed, 30)
        ), seed=seed)
        assert oracle_reports[-1]["end_reason"] == "completed", f"seed {seed}"
        assert oracle_engine.net_worth() > heuristic_engine.net_worth() * 1.3, (
            f"seed {seed}: oracle {oracle_engine.net_worth()} vs "
            f"heuristic {heuristic_engine.net_worth()}"
        )


def test_oracle_golden_seed_42():
    """The published ceiling for the canonical schedule. Pinned like the M1
    golden — a change here is an economics change."""
    engine, reports = run_policy(oracle_policy(generate_schedule(42, 30)), seed=42)
    assert reports[-1]["end_reason"] == "completed"
    # 11470 pre-saturation; the demand cap (customers_per_day) trims the
    # re-pinned under proportional stakes + valuation (was 11330 -> saturation, 11470 original).
    # the cap is invisible at normal scale.
    assert engine.net_worth() == 8730


def test_baseline_ordering_random_lt_heuristic_lt_oracle():
    random_engine, _ = run_policy(random_policy(42))
    heuristic_engine, _ = run_policy(heuristic_policy())
    oracle_engine, _ = run_policy(oracle_policy(generate_schedule(42, 30)))
    assert random_engine.net_worth() < heuristic_engine.net_worth() < oracle_engine.net_worth()
