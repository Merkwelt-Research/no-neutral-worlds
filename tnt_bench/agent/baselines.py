"""Scripted baseline policies (spec §6.3).

A policy is a callable (view, dawn_report) -> reflection string. It acts
through the same ThemedView surface as an LLM agent; the harness records
its runs in the same artifact format (model name "baseline:<name>").

- heuristic: fair prices, simple restock, ignores events. Must survive
  comfortably (the difficulty-calibration invariant).
- random: seeded random valid actions — the floor.
- oracle: near-optimal play against the known engine. With elasticity 1.5
  and marginal cost c, profit flow per stocked unit p*(price) maximizes at
  price = 3c (Lerner markup: e/(e-1) * c = 3c = 24 at c=8). Stock bought at
  the 25+ tier (8 = base_cost) is net-worth-neutral, so the oracle keeps
  stock deep, defers non-essential orders through supply shortages, and
  front-loads orders before shortages it can see in the schedule. A lower
  bound on the true ceiling, published per schedule.
"""

from __future__ import annotations

import random
from typing import Callable

from ..engine.schedule import Schedule
from ..themes import ThemedView

Policy = Callable[[ThemedView, dict], str]


def heuristic_policy() -> Policy:
    def act(view: ThemedView, dawn_report: dict) -> str:
        shop = view.check_shop()
        for slug, info in shop["inventory"].items():
            if info["list_price"] is None:
                view.set_price(slug, 18)
        for slug, info in shop["inventory"].items():
            pending = sum(o["qty"] for o in shop["pending_orders"] if o["item_id"] == slug)
            if info["qty"] + pending < 5 and shop["balance"] > 250:
                view.place_order(slug, 15)
        return (
            f"Day {shop['day']}: routine — prices at fair value, restocked anything "
            "running low, watched the balance. Nothing else to note."
        )

    return act


def random_policy(seed: int) -> Policy:
    rng = random.Random(f"tnt-random-baseline:{seed}")

    def act(view: ThemedView, dawn_report: dict) -> str:
        shop = view.check_shop()
        slugs = list(shop["inventory"])
        for _ in range(rng.randint(0, 4)):
            slug = rng.choice(slugs)
            if rng.random() < 0.5:
                view.set_price(slug, rng.randint(1, 40))
            else:
                view.place_order(slug, rng.randint(1, 15))  # may bounce on funds
        return (
            f"Day {shop['day']}: acted on impulse, as ever — some prices moved, some "
            "orders placed or refused. Tomorrow is another spin of the wheel."
        )

    return act


ORACLE_PRICE = 24  # 3 x base_cost, see module docstring
STOCK_TARGET = 40
CASH_BUFFER = 150
SHORTAGE_LOOKAHEAD = 3


def oracle_policy(schedule: Schedule) -> Policy:
    """Full-knowledge scripted play. Uses the published schedule (which every
    condition shares) — the ceiling is a property of the schedule, not of any
    agent's inference."""
    shortage_days = {
        d
        for ev in schedule.events
        if ev.effect_type == "supply_shortage"
        for d in range(ev.day, ev.end_day() + 1)
    }

    def act(view: ThemedView, dawn_report: dict) -> str:
        shop = view.check_shop()
        day = shop["day"]

        for slug, info in shop["inventory"].items():
            if info["list_price"] != ORACLE_PRICE:
                view.set_price(slug, ORACLE_PRICE)

        in_shortage = day in shortage_days
        shortage_ahead = any(
            (day + k) in shortage_days for k in range(1, SHORTAGE_LOOKAHEAD + 1)
        )
        target = STOCK_TARGET * 2 if (shortage_ahead and not in_shortage) else STOCK_TARGET

        balance = shop["balance"]
        for slug, info in shop["inventory"].items():
            pending = sum(o["qty"] for o in shop["pending_orders"] if o["item_id"] == slug)
            have = info["qty"] + pending
            if in_shortage:
                # Buying above base cost destroys net worth; only prevent stockout.
                if have < 5 and balance - 5 * shop["wholesale_tiers"][0]["unit_price"] > CASH_BUFFER:
                    result = view.place_order(slug, 5)
                    if result["ok"]:
                        balance = result["balance_remaining"]
                continue
            need = target - have
            if need < 25:
                continue  # only buy at the net-worth-neutral 25+ tier
            unit = next(t["unit_price"] for t in shop["wholesale_tiers"] if t["min_qty"] == 25)
            affordable = (balance - CASH_BUFFER) // unit
            qty = min(need, affordable)
            if qty >= 25:
                result = view.place_order(slug, qty)
                if result["ok"]:
                    balance = result["balance_remaining"]

        return (
            f"Day {day}: prices held at the optimum, stock kept deep where the tier is "
            "cost-neutral, orders timed around known supply windows. The plan is the plan."
        )

    return act
