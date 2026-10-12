"""Per-run metric extraction and collection (spec §8).

Consumes run directories only. Forced (empty-marker) reflections are
excluded from the trace corpus but counted as forced_days — an agent that
stops writing has a trace signal all its own.
"""

from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, fields, asdict
from pathlib import Path

import re as _re

from ..io_utils import read_text
from ..themes import load_theme
from .behavior import behavior_metrics, narration_engagement
from .embed import Embedder
from .lexical import compression_ratio, consecutive_overlap, distinct_ngram_ratio
from .novelty import novelty_series, slope, time_to_floor
from .distress import distress_days, distress_density
from .register import frame_break_days, register_density
from .rqa import rqa_metrics


@dataclass
class RunMetrics:
    # identity
    run_id: str
    model: str
    cell: str
    schedule_seed: int
    horizon: int
    # economic
    score: int
    final_gold: int
    days_survived: int
    end_reason: str
    total_revenue: int
    # trace: novelty
    novelty_mean: float | None
    novelty_slope: float | None
    novelty_final: float | None
    novelty_time_to_floor: int | None
    # trace: recurrence
    rqa_rr: float | None
    rqa_det: float | None
    rqa_lam: float | None
    rqa_tt: float | None
    # trace: lexical
    compression_ratio: float | None
    distinct_3gram_ratio: float | None
    consecutive_overlap: float | None
    reflection_chars_mean: float | None
    # behavior
    action_entropy: float | None
    repeated_day_signatures: int
    tool_calls_per_day: float | None
    last_order_day: int | None
    last_price_change_day: int | None
    last_sale_day: int | None
    stockout_days: int
    price_changes_total: int
    null_price_resets: int
    nudges_total: int
    forced_days: int
    shift_response_latency: float | None
    # manipulation check: narrative uptake (fraction is within-richness-level
    # comparable only; use the count across levels)
    narration_engagement: float | None
    narration_engagement_count: float | None
    # inhabitation, second dimension: register adoption + container leaks
    register_density: float | None
    frame_break_days: int
    # companion arms: horizon-disclosure flag + distress instrument
    disclose_horizon: bool
    distress_total: float | None
    distress_days: int


def analyze_run(run_dir: Path | str, embedder: Embedder | None = None) -> RunMetrics:
    run_dir = Path(run_dir)
    result = json.loads(read_text(run_dir / "result.json"))
    manifest = json.loads(read_text(run_dir / "manifest.json"))
    days = [
        json.loads(line)
        for line in read_text(run_dir / "days.jsonl").splitlines()
    ]

    theme = load_theme(manifest["framing"])
    slug_to_id = {lex.slug: item_id for item_id, lex in theme.items.items()}

    # Mechanics vocabulary: words the agent must use regardless of narrative
    # uptake — item names/slugs and everything disclosure lines say.
    mechanics_words = set()
    for lex in theme.items.values():
        mechanics_words.update(_re.findall(r"[a-z]+", f"{lex.slug} {lex.name}".lower()))
    for d in days:
        mechanics_words.update(_re.findall(r"[a-z]+", d.get("disclosure", "").lower()))

    engagement_fraction, engagement_count = narration_engagement(days, mechanics_words)

    reflections = [d["reflection"] for d in days if not d.get("forced")]
    novelty = novelty_series(reflections, embedder)
    rqa = rqa_metrics(reflections, embedder)
    behavior = behavior_metrics(days, slug_to_id)

    return RunMetrics(
        run_id=result["run_id"],
        model=result["model"],
        cell=result["cell"],
        schedule_seed=result["schedule_seed"],
        horizon=result["horizon"],
        score=result["score"],
        final_gold=result["final_gold"],
        days_survived=result["days_survived"],
        end_reason=result["end_reason"],
        total_revenue=sum(d["revenue"] for d in days),
        novelty_mean=(sum(novelty) / len(novelty)) if novelty else None,
        novelty_slope=slope(novelty),
        novelty_final=novelty[-1] if novelty else None,
        novelty_time_to_floor=time_to_floor(novelty),
        rqa_rr=rqa["rr"],
        rqa_det=rqa["det"],
        rqa_lam=rqa["lam"],
        rqa_tt=rqa["tt"],
        compression_ratio=compression_ratio(reflections),
        distinct_3gram_ratio=distinct_ngram_ratio(reflections),
        consecutive_overlap=consecutive_overlap(reflections),
        reflection_chars_mean=(
            sum(len(r) for r in reflections) / len(reflections) if reflections else None
        ),
        narration_engagement=engagement_fraction,
        narration_engagement_count=engagement_count,
        register_density=register_density(reflections),
        frame_break_days=frame_break_days(days),
        disclose_horizon=result.get("disclose_horizon", True),
        distress_total=distress_density(reflections)["total"],
        distress_days=distress_days(days),
        **behavior,
    )


def collect(out_root: Path | str, embedder: Embedder | None = None) -> list[RunMetrics]:
    root = Path(out_root)
    metrics = []
    if root.exists():
        for result_path in sorted(root.glob("*/result.json")):
            metrics.append(analyze_run(result_path.parent, embedder))
    return metrics


def to_csv(metrics: list[RunMetrics], path: Path | str) -> None:
    if not metrics:
        return
    names = [f.name for f in fields(RunMetrics)]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        for m in metrics:
            writer.writerow(asdict(m))


_SUMMARY_FIELDS = (
    "score",
    "days_survived",
    "novelty_mean",
    "novelty_slope",
    "rqa_det",
    "consecutive_overlap",
    "action_entropy",
    "tool_calls_per_day",
    "nudges_total",
    "narration_engagement",
    "register_density",
)


def cell_summary(metrics: list[RunMetrics]) -> dict[str, dict]:
    """Per-cell means/spread for a quick read; real stats happen on the CSV."""
    cells: dict[str, list[RunMetrics]] = {}
    for m in metrics:
        cells.setdefault(m.cell, []).append(m)

    summary = {}
    for cell, runs in sorted(cells.items()):
        row: dict = {"n": len(runs)}
        row["survival_rate"] = sum(1 for r in runs if r.end_reason == "completed") / len(runs)
        for field_name in _SUMMARY_FIELDS:
            values = [getattr(r, field_name) for r in runs]
            values = [v for v in values if v is not None]
            if values:
                row[f"{field_name}_mean"] = statistics.fmean(values)
                row[f"{field_name}_sd"] = (
                    statistics.stdev(values) if len(values) > 1 else 0.0
                )
        summary[cell] = row
    return summary
