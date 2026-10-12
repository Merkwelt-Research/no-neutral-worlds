"""Blind-vector scoring for the Opus arm (docs/osf/OPUS_ARM.md).

Runs BEFORE any close reading, per the registered protocol: the
five-component instrument vector per run, z-scored against the pooled
60 static-cell incumbent runs (runs/main3), incumbent centroids, and
nearest-centroid placement for each Opus version. O1-O3 are adjudicated
on this output; the close read happens after and cannot amend them.

    python scripts/score_opus.py
"""

from __future__ import annotations

import csv
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.analysis.doctrine import doctrine_density  # noqa: E402
from tnt_bench.analysis.negotiation import negotiation_density  # noqa: E402

MAIN = Path("runs/main3")
OPUS = Path("runs/opus1")
COMPONENTS = ("register_density", "frame_break_days", "doctrine_balance",
              "null_price_resets", "negotiation_density")
INCUMBENTS = {
    "gemma": "google/gemma-4-31b-it",
    "qwen": "qwen/qwen3-235b-a22b-2507",
    "sonnet": "anthropic/claude-sonnet-5",
    "gemini": "google/gemini-3.1-pro-preview",
}


def reflections(root: Path, run_id: str) -> list[str]:
    return [
        d.get("reflection", "")
        for line in open(root / run_id / "days.jsonl", encoding="utf-8")
        if not (d := json.loads(line)).get("forced")
    ]


def vector(root: Path, row: dict) -> dict[str, float]:
    texts = reflections(root, row["run_id"])
    doc = doctrine_density(texts)
    return {
        "register_density": float(row["register_density"]),
        "frame_break_days": float(row["frame_break_days"]),
        "doctrine_balance": doc["balance"] if doc["balance"] is not None else 0.0,
        "null_price_resets": float(row["null_price_resets"]),
        "negotiation_density": negotiation_density(texts) or 0.0,
        # carried along for O3, not part of the placement vector:
        "_phantom": doc["phantom_carrying"] or 0.0,
        "_shelf": doc["shelf_pride"] or 0.0,
        "_lean": doc["lean_ops"] or 0.0,
    }


def static_rows(path: Path) -> list[dict]:
    rows = list(csv.DictReader(open(path / "metrics.csv", encoding="utf-8")))
    return [
        r for r in rows
        if not r["model"].startswith("baseline:") and r["cell"].endswith("-static")
    ]


main_rows = static_rows(MAIN)
opus_rows = static_rows(OPUS)
print(f"incumbent pool: {len(main_rows)} static runs; opus: {len(opus_rows)} runs")

main_vecs = {r["run_id"]: vector(MAIN, r) for r in main_rows}
opus_vecs = {r["run_id"]: vector(OPUS, r) for r in opus_rows}

# z-scale from the pooled incumbent static distribution (frozen rule)
scale = {}
for c in COMPONENTS:
    vals = [v[c] for v in main_vecs.values()]
    scale[c] = (st.mean(vals), st.stdev(vals))


def z(vec: dict) -> list[float]:
    return [(vec[c] - scale[c][0]) / scale[c][1] for c in COMPONENTS]


def centroid(vecs: list[dict]) -> list[float]:
    zs = [z(v) for v in vecs]
    return [st.mean(col) for col in zip(*zs)]


def dist(a: list[float], b: list[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


cents = {}
for key, model_id in INCUMBENTS.items():
    vecs = [main_vecs[r["run_id"]] for r in main_rows if r["model"] == model_id]
    cents[key] = centroid(vecs)

print()
print("incumbent centroids (z-space, components: "
      + ", ".join(COMPONENTS) + ")")
for key, c in cents.items():
    print(f"  {key:<7}" + "".join(f"{x:+8.2f}" for x in c))

print()
for version in ("4.7", "4.8"):
    vecs = [opus_vecs[r["run_id"]] for r in opus_rows if version in r["model"]]
    c = centroid(vecs)
    ds = {k: dist(c, kc) for k, kc in cents.items()}
    nearest = min(ds, key=ds.get)
    print(f"Opus {version} centroid:" + "".join(f"{x:+8.2f}" for x in c))
    print("  distances: " + "  ".join(f"{k} {v:.2f}" for k, v in sorted(ds.items(), key=lambda kv: kv[1])))
    print(f"  NEAREST INCUMBENT: {nearest}")
    print()

# ------------------------------------------------------------- O2 contrast
print("O2 — 4.7 vs 4.8 on negotiation register, then doctrine uptake:")
for version in ("4.7", "4.8"):
    sel = [opus_vecs[r["run_id"]] for r in opus_rows if version in r["model"]]
    neg = [v["negotiation_density"] for v in sel]
    bal = [abs(v["doctrine_balance"]) for v in sel]
    print(f"  {version}: negotiation density per run {[f'{x:.4f}' for x in neg]} "
          f"(mean {st.mean(neg):.4f}); |doctrine balance| mean {st.mean(bal):.3f}")

# ------------------------------------------------------------- O3 floors
print()
print("O3 — genre-channel doctrine import vs incumbent floor:")
inc_phantom = [v["_phantom"] for v in main_vecs.values()]
inc_shelf = [v["_shelf"] for v in main_vecs.values()]
inc_lean = [v["_lean"] for v in main_vecs.values()]
print(f"  incumbent static floor: phantom mean {st.mean(inc_phantom):.4f} "
      f"(max {max(inc_phantom):.4f}), shelf {st.mean(inc_shelf):.4f}, "
      f"lean {st.mean(inc_lean):.4f}")
for version in ("4.7", "4.8"):
    sel = [opus_vecs[r["run_id"]] for r in opus_rows if version in r["model"]]
    phantom = [f"{v['_phantom']:.4f}" for v in sel]
    print(f"  opus {version}: phantom per run {phantom}, "
          f"shelf mean {st.mean(v['_shelf'] for v in sel):.4f}, "
          f"lean mean {st.mean(v['_lean'] for v in sel):.4f}")

# --------------------------------------------------- descriptive side table
print()
print("descriptives (n=3 per cell; exploratory):")
for version in ("4.7", "4.8"):
    for frame in ("fantasy", "neutral"):
        sel = [r for r in opus_rows if version in r["model"] and r["cell"].startswith(frame)]
        sc = [float(r["score"]) for r in sel]
        rd = [float(r["register_density"]) for r in sel]
        fb = [float(r["frame_break_days"]) for r in sel]
        nr = [float(r["null_price_resets"]) for r in sel]
        print(f"  {version} {frame:<8} score mean {st.mean(sc):>7.0f}  "
              f"register {st.mean(rd):.3f}  breaks {st.mean(fb):.1f}  "
              f"rituals {st.mean(nr):.1f}")
