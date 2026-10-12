"""Endgame audit (spec: STAGE1_SPECIMENS §7b; COMPANION_ARMS A5)."""

import json

from tnt_bench.analysis.endgame import endgame_audit


def write_run(tmp_path, days, horizon=30):
    (tmp_path / "result.json").write_text(json.dumps({
        "run_id": "r", "model": "m", "cell": "fantasy-static",
        "schedule_seed": 1, "horizon": horizon, "score": 1000,
        "final_gold": 900, "days_survived": horizon, "end_reason": "completed",
    }))
    (tmp_path / "manifest.json").write_text(json.dumps({"framing": "fantasy"}))
    (tmp_path / "days.jsonl").write_text(
        "\n".join(json.dumps(d) for d in days) + "\n"
    )
    return tmp_path


def day(n, tool_calls=(), sales=None):
    return {"day": n, "tool_calls": list(tool_calls), "sales": sales or {}}


def order(slug, qty, unit_cost):
    return {"tool": "place_order", "args": {"item_id": slug, "qty": qty},
            "result": {"ok": True, "item_id": slug, "qty": qty, "unit_cost": unit_cost}}


def price(slug, p):
    return {"tool": "set_price", "args": {"item_id": slug, "price": p},
            "result": {"ok": True, "item_id": slug}}


def test_fire_sale_tax_counts_only_below_floor_in_final_week(tmp_path):
    days = [
        day(1, [order("health_potion", 25, 8), price("health_potion", 18)]),
        # Mid-run below-cost sale: outside the window, not counted.
        day(10, [price("health_potion", 5)], sales={"item_1": 2}),
        day(11, [price("health_potion", 18)]),
        # Final week: staircase below the 8g floor.
        day(28, [price("health_potion", 6)], sales={"item_1": 3}),   # tax 6
        day(29, [price("health_potion", 1)], sales={"item_1": 2}),   # tax 14
        # At-cost sale: no tax.
        day(30, [price("health_potion", 8)], sales={"item_1": 1}),
    ]
    audit = endgame_audit(write_run(tmp_path, days))
    assert audit["fire_sale_units"] == 5
    assert audit["fire_sale_tax"] == 20
    assert audit["late_order_tax"] == 0
    assert audit["overhang"] == (1000 - 900) / 1000


def test_cheap_purchases_lower_the_floor(tmp_path):
    days = [
        day(1, [order("antidote", 25, 6), price("antidote", 18)]),
        # Floor is min(8, 6) = 6: selling at 7 in the window is NOT a fire sale.
        day(29, [price("antidote", 7)], sales={"item_5": 4}),
        day(30, [price("antidote", 5)], sales={"item_5": 2}),  # tax (6-5)*2
    ]
    audit = endgame_audit(write_run(tmp_path, days))
    assert audit["fire_sale_tax"] == 2


def test_late_order_tax_only_above_base_cost(tmp_path):
    days = [
        day(28, [order("mana_potion", 10, 9)]),   # tier 9: tax 10
        day(29, [order("mana_potion", 25, 6)]),   # cheap: counts at 6, no tax
        day(2, [order("mana_potion", 5, 10)]),    # early: not counted
        day(30, []),
    ]
    audit = endgame_audit(write_run(tmp_path, days))
    assert audit["late_order_units"] == 35
    assert audit["late_order_tax"] == 10
