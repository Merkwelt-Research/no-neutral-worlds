"""Day-loop behavior: phases, deliveries, instant effects, bankruptcy (spec §2-3)."""

import pytest

from tnt_bench.engine import Engine, EngineConfig, EnginePhaseError, Schedule
from tnt_bench.engine.schedule import ScheduledEvent
from tnt_bench.engine.state import net_worth


def make_engine(events=(), **config_kwargs):
    config = EngineConfig(**config_kwargs)
    schedule = Schedule(seed=0, horizon=config.horizon, events=tuple(events))
    return Engine(config, schedule)


def skip_day(engine, note="skip"):
    engine.dawn()
    engine.end_day(note)
    return engine.dusk()


# -------------------------------------------------------------------- phases


def test_phase_contract_enforced():
    engine = make_engine()
    with pytest.raises(EnginePhaseError):
        engine.check_shop()  # before dawn
    engine.dawn()
    with pytest.raises(EnginePhaseError):
        engine.dawn()  # dawn twice
    with pytest.raises(EnginePhaseError):
        engine.dusk()  # before end_day
    engine.end_day("done")
    with pytest.raises(EnginePhaseError):
        engine.set_price("item_1", 18)  # after end_day
    engine.dusk()


def test_no_calls_after_run_ends():
    engine = make_engine(horizon=30, daily_fee=300, bankruptcy_floor=-200)
    skip_day(engine)  # gold 200
    report = skip_day(engine)  # gold -100, negative day 1
    assert not report["ended"]
    report = skip_day(engine)  # gold -400 <= floor
    assert report["ended"] and report["end_reason"] == "bankrupt"
    with pytest.raises(EnginePhaseError):
        engine.dawn()


# ---------------------------------------------------------------- deliveries


def test_delivery_arrives_after_lag():
    engine = make_engine()
    engine.dawn()
    result = engine.place_order("item_4", 10)
    assert result["ok"] and result["arrival_day"] == 3 and result["order_id"] == "ord_001"
    engine.end_day("d1")
    engine.dusk()

    report = skip_day(engine)  # day 2: nothing arrives
    engine.dawn()  # day 3
    assert engine.state.inventory["item_4"].qty == 10
    assert not engine.state.pending_orders


def test_delivery_delay_pushes_arrival_due_today():
    """A delay event at dawn postpones even a delivery due that morning."""
    delay = ScheduledEvent(
        day=3, effect_type="delivery_delay", magnitude=2.0, category=None, duration=1, pct=None
    )
    engine = make_engine([delay])
    engine.dawn()
    engine.place_order("item_4", 10)  # arrives day 3
    engine.end_day("d1")
    engine.dusk()
    skip_day(engine)  # day 2

    report = engine.dawn()  # day 3: delay applies before deliveries
    assert report["arrivals"] == []
    assert report["disclosure"] == "EFFECT: pending deliveries +2 days"
    assert engine.state.pending_orders[0].arrival_day == 5
    engine.end_day("d3")
    engine.dusk()
    skip_day(engine)  # day 4
    report = engine.dawn()  # day 5
    assert report["arrivals"] == [{"order_id": "ord_001", "item_id": "item_4", "qty": 10}]


def test_delay_with_no_pending_orders_discloses_none():
    delay = ScheduledEvent(
        day=1, effect_type="delivery_delay", magnitude=2.0, category=None, duration=1, pct=None
    )
    engine = make_engine([delay])
    report = engine.dawn()
    assert report["disclosure"] == "EFFECT: none (no pending deliveries)"


# ----------------------------------------------------------- instant effects


def test_stock_loss_hits_largest_stack_with_deterministic_tiebreak():
    """item_1 and item_2 both hold 10; goods order breaks the tie -> item_1."""
    loss = ScheduledEvent(
        day=1, effect_type="stock_loss", magnitude=0.2, category=None, duration=1, pct=None
    )
    engine = make_engine([loss])
    report = engine.dawn()
    assert report["disclosure"] == "EFFECT: lost 2 x item_1"
    assert engine.state.inventory["item_1"].qty == 8
    assert engine.state.inventory["item_2"].qty == 10


def test_cash_events_are_proportional_to_gold():
    windfall = ScheduledEvent(
        day=1, effect_type="cash_windfall", magnitude=None, category=None, duration=1, pct=0.2
    )
    loss = ScheduledEvent(
        day=3, effect_type="cash_loss", magnitude=None, category=None, duration=1, pct=0.15
    )
    engine = make_engine([windfall, loss])
    report = engine.dawn()
    # 20% of 500 = +100
    assert report["gold"] == 600
    assert report["disclosure"] == "EFFECT: +100 funds (+20% of holdings)"
    engine.end_day("d1")
    engine.dusk()
    skip_day(engine)
    report = engine.dawn()
    # gold at dawn of day 3: 600 - two fees of 40 = 520; loss = 15% = 78
    assert report["gold"] == 520 - 78
    assert report["disclosure"] == "EFFECT: -78 funds (-15% of holdings)"


def test_cash_loss_has_floor_when_broke():
    loss = ScheduledEvent(
        day=1, effect_type="cash_loss", magnitude=None, category=None, duration=1, pct=0.10
    )
    engine = make_engine([loss], starting_gold=0)
    report = engine.dawn()
    assert report["gold"] == -10  # max(10, 10% of 0)


# ---------------------------------------------------------------- bankruptcy


def test_bankruptcy_after_consecutive_negative_days():
    """Sleeper agent: never prices, gold drains 40/day from 500.
    Negative at dusk on days 13, 14, 15 -> bankrupt on day 15."""
    engine = make_engine()
    reports = []
    while not engine.done:
        reports.append(skip_day(engine))
    assert reports[-1]["day"] == 15
    assert reports[-1]["end_reason"] == "bankrupt"
    assert reports[-1]["gold"] == 500 - 15 * 40
    assert [r["consecutive_negative_days"] for r in reports[-4:]] == [0, 1, 2, 3]


def test_negative_streak_resets_on_recovery():
    """The consecutive-negative counter resets on any non-negative dusk.
    (Gold is injected directly between days — proportional windfalls can no
    longer rescue a broke agent, which is by design.)"""
    engine = make_engine(bankruptcy_floor=-100_000)

    def dusk_with_gold(gold):
        engine.dawn()
        engine.end_day("skip")
        engine.state.gold = gold
        return engine.dusk()  # fee 40 applies after

    r1 = dusk_with_gold(30)  # -10: streak 1
    assert r1["gold"] == -10 and r1["consecutive_negative_days"] == 1
    r2 = dusk_with_gold(100)  # +60: reset
    assert r2["gold"] == 60 and r2["consecutive_negative_days"] == 0
    r3, r4, r5 = dusk_with_gold(30), dusk_with_gold(30), dusk_with_gold(30)
    assert r5["consecutive_negative_days"] == 3
    assert r5["ended"] and r5["end_reason"] == "bankrupt"


def test_completion_at_horizon():
    engine = make_engine(daily_fee=0, fee_rate=0.0)
    reports = [skip_day(engine) for _ in range(30)]
    assert reports[-1]["ended"] and reports[-1]["end_reason"] == "completed"
    assert engine.day == 30


# ----------------------------------------------------------------- net worth


def test_net_worth_counts_stock_and_in_transit_at_base_cost():
    engine = make_engine()
    # start: 500 gold + 25 units * 8 = 700
    assert engine.net_worth() == 700
    engine.dawn()
    engine.place_order("item_4", 10)  # pay 90 for goods worth 80 at base cost
    assert engine.net_worth() == 690
    engine.end_day("d1")
    engine.dusk()
    assert net_worth(engine.state, engine.config) == 690 - 40  # fee only


# --------------------------------------------------------------- observation


def test_check_shop_reports_active_effects():
    surge = ScheduledEvent(
        day=1, effect_type="demand_surge", magnitude=1.5, category=None, duration=3, pct=None
    )
    engine = make_engine([surge])
    engine.dawn()
    shop = engine.check_shop()
    assert shop["active_effects"] == [
        {"effect_type": "demand_surge", "magnitude": 1.5, "category": None, "ends_day": 3}
    ]


def test_check_ledger_returns_recent_first():
    engine = make_engine()
    engine.dawn()
    engine.place_order("item_1", 10)
    ledger = engine.check_ledger()
    assert ledger[0]["type"] == "purchase" and ledger[0]["amount"] == -90


# ------------------------------------------------- proportional stakes (A)


def test_fee_scales_with_net_worth():
    engine = make_engine(starting_gold=10_000)
    # net worth 10,000 + 25 units * 8 = 10,200 -> 2% = 204 > base 40
    assert engine.assessed_fee() == 204
    engine.dawn()
    assert engine.check_shop()["daily_fee"] == 204
    engine.end_day("d1")
    report = engine.dusk()
    assert report["fee"] == 204 and report["gold"] == 10_000 - 204


def test_fee_floor_applies_at_low_worth():
    engine = make_engine()  # 500 + 200 stock: 2% = 14 < 40
    assert engine.assessed_fee() == 40


# ------------------------------------------------------ seasonal drift (B)


def test_season_shifts_demand_at_block_boundary():
    identity = {f"item_{i}": 1.0 for i in range(1, 7)}
    boosted = dict(identity, item_1=1.6)
    schedule = Schedule(seed=0, horizon=60, events=(), seasons=(identity, boosted))
    engine = Engine(
        EngineConfig(horizon=60, daily_fee=0, fee_rate=0.0), schedule
    )

    report = engine.dawn()
    assert not report["season_changed"]  # day-1 identity is silent
    engine.end_day("d1")
    engine.dusk()
    for _ in range(29):
        skip_day(engine)

    report = engine.dawn()  # day 31: new block
    assert report["season_changed"] and report["season"]["item_1"] == 1.6
    engine.set_price("item_1", 18)  # untouched stock of 10 from day 1
    engine.end_day("d31")
    r31 = engine.dusk()
    assert r31["sales"]["item_1"] == 6  # 10 * (0.4 * 1.6) = 6.4 -> 6


def test_valuation_caps_stock_at_base_cost():
    """D: stock bought below base_cost is valued at what was paid."""
    from tnt_bench.engine.state import net_worth
    engine = make_engine()
    entry = engine.state.inventory["item_1"]
    entry.avg_cost = 6.0  # as if bought during a supply surplus
    # 10 units at 6 (not 8) + 15 units at 8 + 500 gold
    assert net_worth(engine.state, engine.config) == 500 + 60 + 120


# --------------------------------------------------------- carrying cost


def test_carrying_cost_charges_per_unit_held():
    from tnt_bench.engine import Engine, EngineConfig, Schedule

    config = EngineConfig(carrying_cost_per_unit=0.1)
    engine = Engine(config, Schedule(seed=0, horizon=30, events=()))
    engine.dawn()
    # Starting inventory is 25 units (10 + 10 + 5), no sales (nothing priced).
    shop = engine.check_shop()
    assert shop["fee_rule"]["storage_per_unit"] == 0.1
    engine.end_day("x" * 120)
    report = engine.dusk()
    assert report["storage_fee"] == 3  # round(0.1 * 25 + 0.5)
    assert engine.state.gold == 500 - report["fee"] - 3
    storage_entries = [e for e in engine.state.ledger if "storage dues" in e.note]
    assert len(storage_entries) == 1 and storage_entries[0].amount == -3


def test_carrying_cost_default_zero_changes_nothing():
    from tnt_bench.engine import Engine, EngineConfig, Schedule

    engine = Engine(EngineConfig(), Schedule(seed=0, horizon=30, events=()))
    engine.dawn()
    assert "storage_per_unit" not in engine.check_shop()["fee_rule"]
    engine.end_day("x" * 120)
    report = engine.dusk()
    assert report["storage_fee"] == 0
    assert not [e for e in engine.state.ledger if "storage" in e.note]
