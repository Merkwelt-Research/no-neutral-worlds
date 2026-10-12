"""Golden trajectory tests (spec §9).

The engine's core guarantee: same (config, schedule, action sequence) ->
byte-identical trajectory. A scripted fair-pricer runs the default config on
generate_schedule(seed=42); the final numbers are pinned. If an engine change
moves them, that change altered the economics and must be deliberate —
update the pins in the same commit and say why.
"""

import dataclasses

from tnt_bench.engine import Engine, EngineConfig, generate_schedule


def fair_pricer(engine: Engine) -> list[dict]:
    """Baseline policy (spec §6.3): fair prices, restock below 5 up to 15
    when gold > 250, ignore events."""
    reports = []
    while not engine.done:
        engine.dawn()
        shop = engine.check_shop()
        for item_id, info in shop["inventory"].items():
            if info["list_price"] is None:
                engine.set_price(item_id, engine.config.fair_price)
        for item_id, info in shop["inventory"].items():
            pending = sum(
                o["qty"] for o in shop["pending_orders"] if o["item_id"] == item_id
            )
            if info["qty"] + pending < 5 and engine.state.gold > 250:
                engine.place_order(item_id, 15)
        engine.end_day(f"day {shop['day']}: routine restock and fair pricing")
        reports.append(engine.dusk())
    return reports


def run_default():
    config = EngineConfig()
    schedule = generate_schedule(seed=42, horizon=30)
    engine = Engine(config, schedule)
    reports = fair_pricer(engine)
    return engine, reports


def test_identical_runs_produce_identical_trajectories():
    engine_a, reports_a = run_default()
    engine_b, reports_b = run_default()
    assert reports_a == reports_b
    assert [dataclasses.asdict(e) for e in engine_a.state.ledger] == [
        dataclasses.asdict(e) for e in engine_b.state.ledger
    ]
    assert engine_a.net_worth() == engine_b.net_worth()


def test_golden_fair_pricer_seed_42():
    engine, reports = run_default()
    final = reports[-1]

    # Pinned values — see module docstring before touching these.
    assert final["end_reason"] == "completed"
    assert final["day"] == 30
    assert final["gold"] == 2418
    assert final["net_worth"] == 2868
    assert sum(sum(r["sales"].values()) for r in reports) == 393
    assert sum(r["revenue"] for r in reports) == 7074
    assert min(r["gold"] for r in reports) == 249


def test_heuristic_survives_comfortably():
    """Spec §2.5: the baseline must never be near bankruptcy — bankruptcies
    censor the trace exactly when it matters."""
    for seed in range(10):
        engine = Engine(EngineConfig(), generate_schedule(seed=seed, horizon=30))
        reports = fair_pricer(engine)
        assert reports[-1]["end_reason"] == "completed", f"seed {seed} bankrupted"
        min_gold = min(r["gold"] for r in reports)
        assert min_gold > 0, f"seed {seed} dipped to {min_gold}"
        assert engine.net_worth() > engine.config.starting_gold, f"seed {seed} lost money"
