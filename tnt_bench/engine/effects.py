"""Effect definitions and disclosure rendering (spec §3.1, §3.3).

Magnitudes are fixed constants here; the schedule generator rolls only
durations, categories, and cash amounts — and records them, so nothing is
rolled at runtime. Disclosure strings use abstract engine vocabulary
("funds", item ids); the theme layer substitutes names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .schedule import ScheduledEvent

# effect_type -> fixed multiplier (None where the schedule carries an amount)
MAGNITUDES: dict[str, float | None] = {
    "demand_surge": 1.5,
    "demand_slump": 0.6,
    "demand_shift": 1.8,
    "supply_shortage": 1.4,
    "supply_surplus": 0.7,
    "cash_windfall": None,
    "cash_loss": None,
    "stock_loss": 0.2,  # fraction of largest-qty item, ceil
    "delivery_delay": 2.0,  # extra days on pending arrivals
    "normal": None,
}

# Effects that create a multi-day ActiveEffect (vs applied instantly at dawn).
LINGERING = {"demand_surge", "demand_slump", "demand_shift", "supply_shortage", "supply_surplus"}
INSTANT = {"cash_windfall", "cash_loss", "stock_loss", "delivery_delay"}
SUPPLY = {"supply_shortage", "supply_surplus"}
CASH = {"cash_windfall", "cash_loss"}
# Safe enough for the tutorial window (schedule generator, spec §3.2).
MILD = {"demand_surge", "demand_shift", "cash_windfall"}

ALL_EFFECT_TYPES = set(MAGNITUDES)


def render_disclosure(event: "ScheduledEvent", instant_result: dict | None = None) -> str:
    """Canonical mechanical disclosure line (spec §3.3).

    Identical in every condition modulo lexicon substitution. `instant_result`
    carries the resolved outcome for instant effects (e.g. what stock was
    actually lost).
    """
    t = event.effect_type
    if t == "normal":
        return "EFFECT: none"
    if t in ("demand_surge", "demand_slump"):
        return (
            f"EFFECT: demand x{event.magnitude}, all goods, "
            f"days {event.day}-{event.day + event.duration - 1}"
        )
    if t == "demand_shift":
        return (
            f"EFFECT: demand x{event.magnitude}, category {event.category}, "
            f"days {event.day}-{event.day + event.duration - 1}"
        )
    if t in SUPPLY:
        return (
            f"EFFECT: wholesale cost x{event.magnitude}, "
            f"days {event.day}-{event.day + event.duration - 1}"
        )
    if t in ("cash_windfall", "cash_loss"):
        sign = "+" if t == "cash_windfall" else "-"
        pct = f"{round(event.pct * 100)}% of holdings"
        if instant_result is None:  # pre-run rendering (e.g. pack generation)
            return f"EFFECT: {sign}{pct}"
        return f"EFFECT: {sign}{instant_result.get('amount', 0)} funds ({sign}{pct})"
    if t == "stock_loss":
        if instant_result and instant_result.get("qty_lost", 0) > 0:
            return f"EFFECT: lost {instant_result['qty_lost']} x {instant_result['item_id']}"
        return "EFFECT: none (no stock to lose)"
    if t == "delivery_delay":
        n = instant_result.get("orders_delayed", 0) if instant_result else 0
        if n == 0:
            return "EFFECT: none (no pending deliveries)"
        return "EFFECT: pending deliveries +2 days"
    raise ValueError(f"unknown effect type: {t}")
