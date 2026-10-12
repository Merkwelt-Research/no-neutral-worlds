"""Economic mechanics: tiers, elasticity, error-diffusion sales (spec §2.4-2.5)."""

import pytest

from tnt_bench.engine import Engine, EngineConfig, Schedule
from tnt_bench.engine.schedule import ScheduledEvent
from tnt_bench.engine.state import InventoryEntry


def empty_schedule(horizon=30):
    return Schedule(seed=0, horizon=horizon, events=())


def make_engine(events=(), **config_kwargs):
    config = EngineConfig(**config_kwargs)
    schedule = Schedule(seed=0, horizon=config.horizon, events=tuple(events))
    return Engine(config, schedule)


# ------------------------------------------------------------------ supplier


def test_tier_pricing():
    config = EngineConfig()
    assert config.tier_unit_price(1) == 10
    assert config.tier_unit_price(9) == 10
    assert config.tier_unit_price(10) == 9
    assert config.tier_unit_price(24) == 9
    assert config.tier_unit_price(25) == 8
    assert config.tier_unit_price(100) == 8


def test_supply_shortage_raises_wholesale_prices():
    shortage = ScheduledEvent(
        day=6, effect_type="supply_shortage", magnitude=1.4, category=None, duration=3, pct=None
    )
    engine = make_engine([shortage])
    for _ in range(5):  # advance to day 6
        engine.dawn()
        engine.end_day("skip")
        engine.dusk()
    engine.dawn()
    # floor(x + 0.5) half-up rounding: 10->14, 9->13 (12.6), 8->11 (11.2)
    tiers = {t["min_qty"]: t["unit_price"] for t in engine.check_shop()["wholesale_tiers"]}
    assert tiers == {1: 14, 10: 13, 25: 11}
    result = engine.place_order("item_4", 25)
    assert result["ok"] and result["unit_cost"] == 11 and result["total_paid"] == 275


def test_order_rejected_on_insufficient_funds():
    engine = make_engine()
    engine.dawn()
    result = engine.place_order("item_1", 100)  # 100 * 8 = 800 > 500
    assert not result["ok"] and "insufficient funds" in result["error"]
    assert engine.state.gold == 500 and not engine.state.pending_orders


# --------------------------------------------------------------------- sales


def test_fair_price_sells_at_base_demand():
    """At fair price with no events, p = demand_base exactly."""
    engine = make_engine()
    engine.dawn()
    engine.set_price("item_1", 18)  # demand_base 0.40, qty 10 -> expected 4.0
    engine.end_day("d1")
    report = engine.dusk()
    assert report["sales"]["item_1"] == 4
    assert engine.state.sales_accumulator["item_1"] == pytest.approx(0.0)


def test_error_diffusion_carries_fractional_demand():
    """demand 0.35, qty 10 -> 3.5/day: sells 3 then 4, exactly 7 over two days."""
    engine = make_engine()
    engine.dawn()
    engine.set_price("item_2", 18)
    engine.end_day("d1")
    r1 = engine.dusk()
    assert r1["sales"]["item_2"] == 3
    assert engine.state.sales_accumulator["item_2"] == pytest.approx(0.5)
    engine.dawn()
    engine.place_order("item_2", 10)  # keep future stock irrelevant to this check
    engine.end_day("d2")
    r2 = engine.dusk()  # qty 7 -> acc 0.5 + 7*0.35 = 2.95 -> sells 2... recompute below
    # qty after day 1 = 7; expected = 7 * 0.35 = 2.45; acc = 0.5 + 2.45 = 2.95 -> sold 2
    assert r2["sales"]["item_2"] == 2
    assert engine.state.sales_accumulator["item_2"] == pytest.approx(0.95)


def test_elasticity_reduces_demand():
    """Price at 1.5x fair: modifier = 1.5^-1.5 ~ 0.5443; qty 10 * 0.4 * mod = 2.177."""
    engine = make_engine()
    engine.dawn()
    engine.set_price("item_1", 27)
    engine.end_day("d1")
    report = engine.dusk()
    assert report["sales"]["item_1"] == 2
    assert engine.state.sales_accumulator["item_1"] == pytest.approx(10 * 0.4 * 1.5**-1.5 - 2)


def test_unpriced_goods_never_sell():
    engine = make_engine()
    engine.dawn()
    engine.end_day("d1")
    report = engine.dusk()
    assert report["sales"] == {} and report["revenue"] == 0


def test_stockout_discards_phantom_demand():
    """When sales are stock-limited, the accumulator resets to zero."""
    engine = make_engine(starting_inventory=(("item_1", 2),))
    engine.dawn()
    engine.set_price("item_1", 1)  # p capped at 0.95; qty 2 -> acc 1.9 -> sells 1... not limited
    engine.end_day("d1")
    r1 = engine.dusk()
    assert r1["sales"]["item_1"] == 1
    engine.dawn()
    engine.end_day("d2")
    r2 = engine.dusk()  # qty 1, acc 0.9 + 0.95 = 1.85 -> sold min(1, qty 1) -> stock-limited
    assert r2["sales"]["item_1"] == 1
    assert engine.state.sales_accumulator["item_1"] == 0.0


def test_sale_probability_capped():
    """A giveaway price cannot push per-unit sale probability past the cap."""
    engine = make_engine()
    engine.dawn()
    engine.set_price("item_1", 1)
    engine.end_day("d1")
    report = engine.dusk()
    assert report["sales"]["item_1"] == 9  # floor(10 * 0.95)


def test_demand_saturation_bounds_sales_at_scale():
    """Finite customers: stock depth cannot buy unbounded daily sales.
    (Added after Gemini 3.1 Pro compounded to 88k units and a 1.5M score in
    the 90-day probe.)"""
    engine = make_engine(starting_inventory=(("item_1", 10_000),), starting_gold=100_000)
    engine.dawn()
    engine.set_price("item_1", 18)
    engine.end_day("d1")
    report = engine.dusk()
    # cap = demand_base 0.4 * customers_per_day 30 = 12, not qty*p = 4000
    assert report["sales"]["item_1"] == 12


def test_demand_surge_multiplies_sales():
    surge = ScheduledEvent(
        day=1, effect_type="demand_surge", magnitude=1.5, category=None, duration=2, pct=None
    )
    engine = make_engine([surge])
    engine.dawn()
    engine.set_price("item_1", 18)
    engine.end_day("d1")
    report = engine.dusk()
    assert report["sales"]["item_1"] == 6  # 10 * 0.4 * 1.5 = 6.0


def test_demand_shift_hits_only_its_category():
    shift = ScheduledEvent(
        day=1, effect_type="demand_shift", magnitude=1.8, category="A", duration=2, pct=None
    )
    engine = make_engine([shift])
    engine.dawn()
    engine.set_price("item_1", 18)  # category A
    engine.set_price("item_2", 18)  # category B
    engine.end_day("d1")
    report = engine.dusk()
    assert report["sales"]["item_1"] == 7  # 10 * 0.4 * 1.8 = 7.2
    assert report["sales"]["item_2"] == 3  # unaffected: 10 * 0.35


def test_avg_cost_is_weighted_average():
    engine = make_engine()
    engine.dawn()
    engine.place_order("item_3", 15)  # 15 @ 9
    engine.end_day("d1")
    engine.dusk()
    engine.dawn()
    engine.end_day("d2")
    engine.dusk()
    engine.dawn()  # day 3: delivery arrives; had 5 @ 8.0
    entry = engine.state.inventory["item_3"]
    assert entry.qty == 20
    assert entry.avg_cost == pytest.approx((5 * 8.0 + 15 * 9) / 20)
