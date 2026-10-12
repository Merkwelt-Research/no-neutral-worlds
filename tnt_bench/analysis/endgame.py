"""Endgame audit (STAGE1_SPECIMENS §7b; COMPANION_ARMS Addendum 1 / A5).

Deterministic census of final-week behaviors that can silently cost score:

- fire_sale_tax: units sold below cost basis x the gap. Conservative cost
  basis per item = min(base_cost, cheapest unit price ever paid in the
  run) — under the valuation rule (stock counts at min(avg_cost,
  base_cost)) any sale below this floor strictly reduces score.
- late_order_tax: units ordered in the final week x max(0, unit_cost -
  base_cost) — the amount a late purchase can never recover under the
  valuation cap.

Frozen for A5 scoring: the window is the last 7 days of the horizon and
the base cost is 8, matching the calibration run on Stage-1 data.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..io_utils import read_text
from ..themes import load_theme

BASE_COST = 8
FINAL_WINDOW_DAYS = 7


def endgame_audit(run_dir: Path | str) -> dict:
    run_dir = Path(run_dir)
    result = json.loads(read_text(run_dir / "result.json"))
    manifest = json.loads(read_text(run_dir / "manifest.json"))
    days = [json.loads(l) for l in read_text(run_dir / "days.jsonl").splitlines()]

    theme = load_theme(manifest["framing"])
    slug_to_id = {lex.slug: item_id for item_id, lex in theme.items.items()}
    window_start = result["horizon"] - FINAL_WINDOW_DAYS + 1

    floor = {item_id: BASE_COST for item_id in theme.items}
    prices: dict[str, int] = {}
    fire_units = 0
    fire_tax = 0
    late_units = 0
    late_tax = 0

    for d in days:
        for tc in d["tool_calls"]:
            r = tc.get("result", {})
            if tc["tool"] == "place_order" and r.get("ok"):
                item_id = slug_to_id.get(r["item_id"], r["item_id"])
                floor[item_id] = min(floor[item_id], r["unit_cost"], BASE_COST)
                if d["day"] >= window_start:
                    late_units += r["qty"]
                    late_tax += max(0, r["unit_cost"] - BASE_COST) * r["qty"]
            if tc["tool"] == "set_price" and r.get("ok"):
                item_id = slug_to_id.get(tc["args"].get("item_id"))
                if item_id:
                    prices[item_id] = tc["args"].get("price")
        if d["day"] >= window_start:
            for item_id, qty in d["sales"].items():
                price = prices.get(item_id)
                if price is not None and price < floor[item_id]:
                    fire_units += qty
                    fire_tax += (floor[item_id] - price) * qty

    return {
        "run_id": result["run_id"],
        "model": result["model"],
        "cell": result["cell"],
        "schedule_seed": result["schedule_seed"],
        "disclose_horizon": result.get("disclose_horizon", True),
        "fire_sale_units": fire_units,
        "fire_sale_tax": fire_tax,
        "late_order_units": late_units,
        "late_order_tax": late_tax,
        "overhang": (
            (result["score"] - result["final_gold"]) / result["score"]
            if result["score"] else None
        ),
    }


def endgame_census(out_root: Path | str, include_baselines: bool = False) -> list[dict]:
    root = Path(out_root)
    rows = []
    for result_path in sorted(root.glob("*/result.json")):
        if not include_baselines and result_path.parent.name.startswith("baseline_"):
            continue
        rows.append(endgame_audit(result_path.parent))
    return rows
