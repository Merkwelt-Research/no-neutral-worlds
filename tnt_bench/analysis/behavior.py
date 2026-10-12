"""Behavioral stereotypy and stagnation — collapse measured without touching
language at all (spec §8.2, VB1's modal signature) — plus the narrative
uptake manipulation check."""

from __future__ import annotations

import math
import re

from ..engine.config import DEFAULT_GOODS

_WORD = re.compile(r"[a-z]+")
_STOPWORDS = frozenset(
    "the a an of to in on at is are was were has have had be been being by "
    "from as it its this that these those and or but for with will would "
    "can could may might not no nor so than then there their they them "
    "your you our we he she his her him who what when where which while "
    "day days today tomorrow yesterday".split()
)


def narration_engagement(
    day_records: list[dict], exclude_words: set[str]
) -> tuple[float | None, float | None]:
    """Manipulation check (uptake): how much of each day's distinctive
    narration vocabulary reappears in that day's reflection.

    Returns (mean fraction, mean absolute count). The fraction is only
    comparable within a richness level — static one-liners have tiny
    denominators — so cross-level comparisons should use the count.

    `exclude_words` should carry the mechanics vocabulary (item names,
    disclosure terms) so engagement measures the *world*, not the economics
    the agent must mention anyway. Near-zero = the agent treats narrative as
    wallpaper; the F+ hypothesis needs uptake to actually occur."""
    fractions, counts = [], []
    for record in day_records:
        if record.get("forced"):
            continue
        narration_words = {
            w for w in _WORD.findall(record.get("narration", "").lower())
            if len(w) > 4 and w not in _STOPWORDS and w not in exclude_words
        }
        if not narration_words:
            continue
        reflection_words = set(_WORD.findall(record.get("reflection", "").lower()))
        hits = len(narration_words & reflection_words)
        fractions.append(hits / len(narration_words))
        counts.append(float(hits))
    if not fractions:
        return None, None
    return sum(fractions) / len(fractions), sum(counts) / len(counts)


def action_entropy(day_records: list[dict]) -> float | None:
    """Shannon entropy (bits) of the distribution of daily action signatures
    (the ordered tuple of tool names used that day). Zero = every day is the
    same day."""
    if not day_records:
        return None
    signatures = [tuple(tc["tool"] for tc in d["tool_calls"]) for d in day_records]
    counts: dict[tuple, int] = {}
    for sig in signatures:
        counts[sig] = counts.get(sig, 0) + 1
    n = len(signatures)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def behavior_metrics(day_records: list[dict], slug_to_id: dict[str, str]) -> dict:
    """Stagnation and stereotypy from days.jsonl records."""
    n = len(day_records)
    signatures = [tuple(tc["tool"] for tc in d["tool_calls"]) for d in day_records]
    # Identical empty days count too: doing nothing twice is stereotypy.
    repeated_days = sum(1 for a, b in zip(signatures, signatures[1:]) if a == b)

    last_order_day = None
    last_price_change_day = None
    price_changes_total = 0
    null_price_resets = 0  # set_price to the already-current price: ritual, not decision
    for record in day_records:
        for tc in record["tool_calls"]:
            ok = tc["result"].get("ok", True)
            if tc["tool"] == "place_order" and ok:
                last_order_day = record["day"]
            if tc["tool"] == "set_price" and ok:
                result = tc["result"]
                if (
                    result.get("new_price") is not None
                    and result.get("old_price") == result.get("new_price")
                ):
                    null_price_resets += 1
                else:
                    last_price_change_day = record["day"]
                    price_changes_total += 1

    sale_days = [d["day"] for d in day_records if d.get("sales")]
    stockout_days = sum(
        1 for d in day_records
        if "inventory_start" in d and sum(d["inventory_start"].values()) == 0
    )

    return {
        "action_entropy": action_entropy(day_records),
        "repeated_day_signatures": repeated_days,
        "tool_calls_per_day": (
            sum(len(d["tool_calls"]) for d in day_records) / n if n else None
        ),
        "last_order_day": last_order_day,
        "last_price_change_day": last_price_change_day,
        "last_sale_day": max(sale_days) if sale_days else None,
        "stockout_days": stockout_days,
        "price_changes_total": price_changes_total,
        "null_price_resets": null_price_resets,
        "nudges_total": sum(d.get("nudges", 0) for d in day_records),
        "forced_days": sum(1 for d in day_records if d.get("forced")),
        "shift_response_latency": _shift_response_latency(day_records, slug_to_id),
    }


def _shift_response_latency(
    day_records: list[dict], slug_to_id: dict[str, str], window: int = 5
) -> float | None:
    """Mean days from a demand_shift disclosure to a price or order action on
    an affected item, within `window` days. Unanswered shifts are excluded —
    responsiveness of the responses, not the response rate."""
    category_items = {}
    for good in DEFAULT_GOODS:
        category_items.setdefault(good.category, set()).add(good.id)

    by_day = {d["day"]: d for d in day_records}
    latencies = []
    for record in day_records:
        event = record.get("event") or {}
        if event.get("effect_type") != "demand_shift":
            continue
        affected = category_items.get(event.get("category"), set())
        for k in range(window + 1):
            future = by_day.get(record["day"] + k)
            if future is None:
                break
            if _acts_on(future, affected, slug_to_id):
                latencies.append(k)
                break
    return sum(latencies) / len(latencies) if latencies else None


def _acts_on(record: dict, affected: set[str], slug_to_id: dict[str, str]) -> bool:
    for tc in record["tool_calls"]:
        if tc["tool"] not in ("set_price", "place_order"):
            continue
        if not tc["result"].get("ok", False):
            continue
        engine_id = slug_to_id.get(tc["args"].get("item_id", ""))
        if engine_id in affected:
            return True
    return False
