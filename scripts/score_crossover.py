"""Score the frozen frame x explicit-doctrine crossover.

Protocol: docs/osf/FRAME_DOCTRINE_CROSSOVER.md
Data: runs/crossover1

The inferential unit is the schedule seed. The two agent realizations are
averaged within each model x frame x doctrine x seed cell before contrasts.
This script deliberately uses only committed result, manifest, and day files.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.analysis.doctrine import doctrine_density  # noqa: E402


MODELS = ("google/gemma-4-31b-it", "openai/gpt-5.6-luna")
SEEDS = tuple(range(27, 37))
REPLICATES = (1, 2)
THEME_TO_CELL = {
    "fantasy": ("fantasy", "none"),
    "fantasy_crossover_full": ("fantasy", "full"),
    "fantasy_crossover_lean": ("fantasy", "lean"),
    "neutral": ("neutral", "none"),
    "neutral_crossover_full": ("neutral", "full"),
    "neutral_crossover_lean": ("neutral", "lean"),
}
T_95_DF9 = 1.8331  # central 90% t interval with ten seed units


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_rows(root: Path) -> list[dict]:
    rows = []
    for result_path in sorted(root.glob("*/result.json")):
        run_dir = result_path.parent
        result = _read_json(result_path)
        manifest = _read_json(run_dir / "manifest.json")
        theme = manifest["framing"]
        if result["model"] not in MODELS or theme not in THEME_TO_CELL:
            continue
        frame, doctrine = THEME_TO_CELL[theme]
        days = [
            json.loads(line)
            for line in (run_dir / "days.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        reflections = [d.get("reflection", "") for d in days if not d.get("forced")]
        balance = doctrine_density(reflections)["balance"]
        rows.append({
            "run_id": result["run_id"],
            "model": result["model"],
            "theme": theme,
            "frame": frame,
            "doctrine": doctrine,
            "seed": int(result["schedule_seed"]),
            "replicate": int(manifest.get("replicate", 1)),
            "days_survived": int(result["days_survived"]),
            "end_reason": result["end_reason"],
            "score": float(result["score"]),
            "mean_daily_stock": st.mean(
                sum(d["inventory_start"].values()) for d in days
            ),
            "units_sold": float(sum(sum(d["sales"].values()) for d in days)),
            "doctrine_balance": float(balance or 0.0),
        })

    assert len(rows) == 240, f"expected 240 crossover runs, found {len(rows)}"
    assert len({r["run_id"] for r in rows}) == 240, "duplicate run ids"
    observed = {
        (r["model"], r["frame"], r["doctrine"], r["seed"], r["replicate"])
        for r in rows
    }
    expected = {
        (model, frame, doctrine, seed, rep)
        for model in MODELS
        for frame in ("fantasy", "neutral")
        for doctrine in ("none", "full", "lean")
        for seed in SEEDS
        for rep in REPLICATES
    }
    assert observed == expected, f"matrix mismatch: missing={expected-observed}, extra={observed-expected}"
    return rows


def write_rows(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def seed_cells(rows: list[dict], metric: str) -> dict[tuple, float]:
    grouped: dict[tuple, list[float]] = defaultdict(list)
    for row in rows:
        key = (row["model"], row["frame"], row["doctrine"], row["seed"])
        grouped[key].append(float(row[metric]))
    assert all(len(values) == 2 for values in grouped.values())
    return {key: st.mean(values) for key, values in grouped.items()}


def contrast(cells: dict[tuple, float], model: str, terms: tuple[tuple[float, str, str], ...]) -> list[float]:
    return [
        sum(weight * cells[(model, frame, doctrine, seed)] for weight, frame, doctrine in terms)
        for seed in SEEDS
    ]


def summarize(values: list[float]) -> dict[str, float]:
    point = st.mean(values)
    half = T_95_DF9 * st.stdev(values) / math.sqrt(len(values))
    hits = sum(
        st.mean(sign * value for sign, value in zip(signs, values)) >= point
        for signs in itertools.product((-1, 1), repeat=len(values))
    )
    return {
        "point": point,
        "lo": point - half,
        "hi": point + half,
        "p_one_sided": hits / (2 ** len(values)),
        "positive": sum(value > 0 for value in values),
    }


def show(label: str, values: list[float]) -> dict[str, float]:
    result = summarize(values)
    print(
        f"{label:<48} {result['point']:+9.2f}  "
        f"90% CI [{result['lo']:+.2f}, {result['hi']:+.2f}]  "
        f"{result['positive']}/10 positive  p+={result['p_one_sided']:.6f}"
    )
    return result


def score_metric(rows: list[dict], metric: str) -> dict[tuple[str, str], dict[str, float]]:
    cells = seed_cells(rows, metric)
    out = {}
    print(f"\n== {metric} ==")
    for model in MODELS:
        short = "Gemma" if model.startswith("google/") else "Luna"
        frame_gaps = {}
        for doctrine in ("none", "full", "lean"):
            values = contrast(cells, model, (
                (1.0, "fantasy", doctrine),
                (-1.0, "neutral", doctrine),
            ))
            frame_gaps[doctrine] = values
            out[(model, f"frame_{doctrine}")] = show(
                f"{short} frame gap F-N [{doctrine}]", values
            )
        for frame in ("fantasy", "neutral"):
            values = contrast(cells, model, (
                (1.0, frame, "full"),
                (-1.0, frame, "lean"),
            ))
            out[(model, f"doctrine_{frame}")] = show(
                f"{short} doctrine full-lean [{frame}]", values
            )
        occlusion = [
            frame_gaps["none"][i]
            - 0.5 * (frame_gaps["full"][i] + frame_gaps["lean"][i])
            for i in range(len(SEEDS))
        ]
        out[(model, "occlusion")] = show(
            f"{short} occlusion baseline-held doctrine", occlusion
        )
        baseline = out[(model, "frame_none")]["point"]
        full = out[(model, "frame_full")]["point"]
        lean = out[(model, "frame_lean")]["point"]
        print(
            f"{short} strong residual check: |full| < |none| = {abs(full) < abs(baseline)}; "
            f"|lean| < |none| = {abs(lean) < abs(baseline)}"
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="runs/crossover1")
    parser.add_argument("--csv", default=None)
    args = parser.parse_args()
    root = Path(args.out)
    rows = load_rows(root)
    csv_path = Path(args.csv) if args.csv else root / "crossover_metrics.csv"
    write_rows(rows, csv_path)

    day90 = sum(r["days_survived"] == 90 for r in rows)
    print("=" * 100)
    print("FRAME x DOCTRINE CROSSOVER — frozen scoring")
    print(f"complete matrix: {len(rows)}/240; reached day 90: {day90}/240")
    print(f"raw-first metrics: {csv_path}")
    print("=" * 100)

    stock = score_metric(rows, "mean_daily_stock")
    wealth = score_metric(rows, "score")
    score_metric(rows, "units_sold")
    balance = score_metric(rows, "doctrine_balance")

    gemma, luna = MODELS
    verdicts = {
        "FD1": (
            stock[(gemma, "frame_none")]["point"] > 0
            and wealth[(gemma, "frame_none")]["point"] > 0
        ),
        "FD2": (
            stock[(gemma, "doctrine_fantasy")]["point"] > 0
            and stock[(gemma, "doctrine_neutral")]["point"] > 0
        ),
        "FD3": stock[(gemma, "occlusion")]["point"] > 0,
        "FD4": wealth[(gemma, "occlusion")]["point"] > 0,
        "FD5": (
            stock[(luna, "doctrine_fantasy")]["point"] > 0
            and stock[(luna, "doctrine_neutral")]["point"] > 0
        ),
        "FD6": stock[(luna, "occlusion")]["point"] > 0,
        "FD7": all(
            balance[(model, f"doctrine_{frame}")]["point"] > 0
            for model in MODELS
            for frame in ("fantasy", "neutral")
        ),
    }
    print("\n== registered directional verdicts ==")
    for prediction, hit in verdicts.items():
        print(f"{prediction}: {'HIT' if hit else 'MISS'}")


if __name__ == "__main__":
    main()
