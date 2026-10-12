"""Behavioral metrics and the end-to-end artifact analysis (spec §8)."""

import math

import pytest

from tnt_bench.analysis import (
    action_entropy,
    analyze_run,
    behavior_metrics,
    cell_summary,
    collect,
    to_csv,
)
from tnt_bench.harness import ALL_CELLS, expand_specs, run_matrix

SLUG_TO_ID = {"health_potion": "item_1", "strength_tonic": "item_4"}


def day(n, tools=(), sales=None, event=None, inventory=None, nudges=0, forced=False):
    return {
        "day": n,
        "tool_calls": [
            {"tool": t, "args": a, "result": {"ok": True}} for t, a in tools
        ],
        "sales": sales or {},
        "event": event or {"effect_type": "normal"},
        "inventory_start": inventory if inventory is not None else {"item_1": 5},
        "nudges": nudges,
        "forced": forced,
        "revenue": 0,
        "reflection": "r",
    }


def test_action_entropy_zero_for_identical_days():
    records = [day(n, tools=[("check_shop", {}), ("end_day", {})]) for n in range(1, 6)]
    assert action_entropy(records) == pytest.approx(0.0)


def test_action_entropy_max_for_all_distinct_days():
    tool_sets = [[("check_shop", {})], [("set_price", {})], [("place_order", {})], [("end_day", {})]]
    records = [day(n + 1, tools=tool_sets[n]) for n in range(4)]
    assert action_entropy(records) == pytest.approx(math.log2(4))


def test_stagnation_and_stockout_fields():
    records = [
        day(1, tools=[("place_order", {"item_id": "health_potion", "qty": 10}),
                      ("set_price", {"item_id": "health_potion", "price": 20})],
            sales={"item_1": 2}),
        day(2, tools=[("set_price", {"item_id": "health_potion", "price": 22})],
            sales={"item_1": 1}),
        day(3, inventory={"item_1": 0}, nudges=2),
        day(4, inventory={"item_1": 0}, forced=True, nudges=3),
    ]
    metrics = behavior_metrics(records, SLUG_TO_ID)
    assert metrics["last_order_day"] == 1
    assert metrics["last_price_change_day"] == 2
    assert metrics["last_sale_day"] == 2
    assert metrics["stockout_days"] == 2
    assert metrics["price_changes_total"] == 2
    assert metrics["nudges_total"] == 5
    assert metrics["forced_days"] == 1
    assert metrics["repeated_day_signatures"] == 1  # days 3 and 4 both empty


def test_shift_response_latency():
    records = [
        day(1, event={"effect_type": "demand_shift", "category": "A"}),
        day(2),
        day(3, tools=[("set_price", {"item_id": "strength_tonic", "price": 25})]),
        day(4),
    ]
    metrics = behavior_metrics(records, SLUG_TO_ID)
    assert metrics["shift_response_latency"] == 2.0  # day 1 shift answered on day 3


def test_narration_engagement_detects_uptake():
    from tnt_bench.analysis.behavior import narration_engagement

    narration = (
        "A caravan of spice merchants rattled through the gate, scattering "
        "confused goats across the market square."
    )
    engaged = dict(day(1), narration=narration,
                   reflection="The caravan and those ridiculous goats brought a crowd; sold well.")
    ignored = dict(day(2), narration=narration,
                   reflection="Sold 8 units, reordered stock, margins holding at plan.")
    high_frac, high_count = narration_engagement([engaged], exclude_words=set())
    low_frac, low_count = narration_engagement([ignored], exclude_words=set())
    assert high_frac > 0.15 and high_count >= 2.0
    assert low_frac == 0.0 and low_count == 0.0
    # Mechanics words are excluded so required vocabulary can't fake uptake.
    fake = dict(day(3), narration="Demand for potions is high in the market.",
                reflection="Raised potion prices given high demand.")
    assert narration_engagement([fake], exclude_words={"potions", "demand", "market"}) == (None, None)


def test_unanswered_shift_excluded():
    records = [day(1, event={"effect_type": "demand_shift", "category": "A"}), day(2)]
    assert behavior_metrics(records, SLUG_TO_ID)["shift_response_latency"] is None


# ------------------------------------------------------- artifacts end-to-end


def test_analyze_baseline_runs_end_to_end(tmp_path):
    specs = expand_specs(
        models=["baseline:heuristic", "baseline:random"], seeds=[42], horizon=30,
        cells=[c for c in ALL_CELLS if c.richness == "static"],
    )
    run_matrix(specs, tmp_path)

    metrics = collect(tmp_path)
    assert len(metrics) == 4

    heuristic = next(m for m in metrics if m.model == "baseline:heuristic" and m.cell == "fantasy-static")
    assert heuristic.score == 2830
    assert heuristic.end_reason == "completed"
    assert heuristic.total_revenue > 0
    # Canned near-identical reflections: the trace metrics must read as collapsed.
    assert heuristic.novelty_mean < 0.3
    assert heuristic.consecutive_overlap > 0.7
    assert heuristic.forced_days == 0

    csv_path = tmp_path / "metrics.csv"
    to_csv(metrics, csv_path)
    lines = csv_path.read_text().splitlines()
    assert len(lines) == 5 and lines[0].startswith("run_id,")

    summary = cell_summary(metrics)
    assert set(summary) == {"fantasy-static", "neutral-static"}
    assert summary["fantasy-static"]["n"] == 2
    assert 0 <= summary["fantasy-static"]["survival_rate"] <= 1


def test_analyze_run_single_directory(tmp_path):
    specs = expand_specs(models=["baseline:heuristic"], seeds=[7], horizon=30,
                         cells=[c for c in ALL_CELLS if c.cell_id == "neutral-static"])
    results = run_matrix(specs, tmp_path)
    metrics = analyze_run(tmp_path / results[0]["run_id"])
    assert metrics.cell == "neutral-static"
    assert metrics.schedule_seed == 7
    assert metrics.tool_calls_per_day == 0.0  # baselines bypass the tool layer
