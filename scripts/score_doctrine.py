"""Score D1-D5 on the doctrine x economy experiment (runs/doctrine1).

Run once, per the frozen protocol in docs/osf/DOCTRINE_ECONOMY.md: paired
contrasts by model and seed on net worth (the run score); Monte-Carlo
sign-flip permutation p-values as in scripts/score_predictions.py, fixed
seed; no alpha, raw one-sided p per registered direction.

Bankrupt runs are scored at their terminal net worth exactly as the
engine recorded it — the registration did not condition on completion,
so neither does the scoring. The 17/20 carry-economy bankruptcy rate is
reported alongside as the design-calibration deviation it is (see the
dated amendment in DOCTRINE_ECONOMY.md); survival-time reads are
EXPLORATORY and labeled as such.

    python scripts/score_doctrine.py runs/doctrine1
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.analysis.doctrine import DOCTRINE_MARKERS  # noqa: E402

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/doctrine1")
PERM_N = 500_000
SEEDS = (2, 3, 4, 5, 6)
MODELS = {"gemma": "google/gemma-4-31b-it", "qwen": "qwen/qwen3-235b-a22b-2507"}
rng = random.Random("tnt-doctrine-scoring")

ROWS = list(csv.DictReader(open(ROOT / "metrics.csv", encoding="utf-8")))


def cell_rows(model_key: str, creed: str, economy: str) -> dict[int, dict]:
    """seed -> metrics row for one model x creed x economy cell."""
    out = {}
    for r in ROWS:
        if MODELS[model_key] != r["model"]:
            continue
        if f"creed_{creed}" not in r["cell"]:
            continue
        in_carry = r["run_id"].endswith("__cc3p0")
        if (economy == "carry") != in_carry:
            continue
        out[int(r["schedule_seed"])] = r
    assert sorted(out) == list(SEEDS), (model_key, creed, economy, sorted(out))
    return out


def creed_gaps(model_key: str, economy: str) -> list[float]:
    """Per-seed creed effect: score(full) - score(lean)."""
    full = cell_rows(model_key, "full", economy)
    lean = cell_rows(model_key, "lean", economy)
    return [float(full[s]["score"]) - float(lean[s]["score"]) for s in SEEDS]


def mean_se(vals):
    if len(vals) == 1:
        return vals[0], None
    return st.mean(vals), st.stdev(vals) / math.sqrt(len(vals))


def perm_p_onesided(diffs):
    """P(mean >= observed | H0 sign-symmetric)."""
    obs = st.mean(diffs)
    hits = 0
    for _ in range(PERM_N):
        s = sum(d if rng.random() < 0.5 else -d for d in diffs)
        if s / len(diffs) >= obs:
            hits += 1
    return (hits + 1) / (PERM_N + 1)


def load_days(run_id: str) -> list[dict]:
    return [
        json.loads(line)
        for line in open(ROOT / run_id / "days.jsonl", encoding="utf-8")
    ]


def fmt(vals):
    return "[" + ", ".join(f"{v:+.0f}" for v in vals) + "]"


# ------------------------------------------------------------------ header

print("=" * 72)
print("DOCTRINE x ECONOMY scoring — registered protocol, docs/osf/DOCTRINE_ECONOMY.md")
print(f"population: {ROOT}, 2 creeds x 2 economies x 2 models x seeds {SEEDS}")
comp = sum(1 for r in ROWS if r["end_reason"] == "completed")
bank = sum(1 for r in ROWS if r["end_reason"] == "bankrupt")
carry_bank = sum(
    1 for r in ROWS
    if r["end_reason"] == "bankrupt" and r["run_id"].endswith("__cc3p0")
)
print(f"completeness: {comp}/{len(ROWS)} completed, {bank} bankrupt "
      f"(all {carry_bank} in the carry economy — see amendment)")
print("=" * 72)

G_FREE = creed_gaps("gemma", "free")
G_CARRY = creed_gaps("gemma", "carry")
Q_FREE = creed_gaps("qwen", "free")
Q_CARRY = creed_gaps("qwen", "carry")

# ------------------------------------------------------------------ D1

print()
print("D1 — fit interaction (Gemma): creed effect free > carry, paired. 65%")
inter = [f - c for f, c in zip(G_FREE, G_CARRY)]
m, se = mean_se(inter)
print(f"    free  per-seed full-lean: {fmt(G_FREE)}  mean {st.mean(G_FREE):+.0f}")
print(f"    carry per-seed full-lean: {fmt(G_CARRY)}  mean {st.mean(G_CARRY):+.0f}")
print(f"    interaction per-seed: {fmt(inter)}")
print(f"    mean {m:+.0f} (se {se:.0f}), one-sided p = {perm_p_onesided(inter):.4f}")

# ------------------------------------------------------------------ D2

print()
print("D2 — sign flip (Gemma): free mean > 0 AND carry mean < 0. 55%")
print(f"    free mean {st.mean(G_FREE):+.0f} ({sum(g > 0 for g in G_FREE)}/5 seeds positive), "
      f"p(>0) = {perm_p_onesided(G_FREE):.4f}")
neg = [-g for g in G_CARRY]
print(f"    carry mean {st.mean(G_CARRY):+.0f} ({sum(g < 0 for g in G_CARRY)}/5 seeds negative), "
      f"p(<0) = {perm_p_onesided(neg):.4f}")

# ------------------------------------------------------------------ D3

print()
print("D3 — mediation replication (Gemma, free): gap within 2x of +3947,")
print("     carried by volume/stock. 55%")
gap = st.mean(G_FREE)
print(f"    creed gap {gap:+.0f}; window [1974, 7894]: "
      f"{'INSIDE' if 1973.5 <= gap <= 7894 else 'OUTSIDE'}")
for creed in ("full", "lean"):
    stocks, prices, vols = [], [], []
    for s, r in cell_rows("gemma", creed, "free").items():
        days = load_days(r["run_id"])
        stocks.append(st.mean(sum(d["inventory_start"].values()) for d in days))
        units = sum(sum(d.get("sales", {}).values()) for d in days)
        rev = sum(d["revenue"] for d in days)
        vols.append(units)
        prices.append(rev / units if units else float("nan"))
    print(f"    creed_{creed}: mean daily stock {st.mean(stocks):.0f}, "
          f"units sold {st.mean(vols):.0f}, realized price {st.mean(prices):.2f}")

# ------------------------------------------------------------------ D4

print()
print("D4 — doctrine immunity (Qwen): |Qwen effect| < 0.5 |Gemma effect|,")
print("     both economies. 60%")
for econ, g, q in (("free", G_FREE, Q_FREE), ("carry", G_CARRY, Q_CARRY)):
    ok = abs(st.mean(q)) < 0.5 * abs(st.mean(g))
    print(f"    {econ:<5} Gemma {st.mean(g):+.0f} vs Qwen {st.mean(q):+.0f} "
          f"-> {'HOLDS' if ok else 'FAILS'}")

# ------------------------------------------------------------------ D5

print()
print("D5 — manipulation check: doctrine balance higher under creed_full")
print("     in every model x economy cell (frozen instrument). 80%")
_WORD = re.compile(r"[a-z']+")
compiled = {
    cat: [re.compile(p, re.IGNORECASE) for p in pats]
    for cat, pats in DOCTRINE_MARKERS.items()
}


def balance(run_id: str) -> float | None:
    texts = [
        d.get("reflection", "") for d in load_days(run_id) if not d.get("forced")
    ]
    words = sum(len(_WORD.findall(t.lower())) for t in texts)
    if not words:
        return None
    dens = {
        cat: 100.0 * sum(len(p.findall(t)) for t in texts for p in pats) / words
        for cat, pats in compiled.items()
    }
    return dens["shelf_pride"] - dens["lean_ops"]


all_cells_ok = True
for mk in MODELS:
    for econ in ("free", "carry"):
        bf = [balance(r["run_id"]) for r in cell_rows(mk, "full", econ).values()]
        bl = [balance(r["run_id"]) for r in cell_rows(mk, "lean", econ).values()]
        bf = [b for b in bf if b is not None]
        bl = [b for b in bl if b is not None]
        ok = st.mean(bf) > st.mean(bl)
        all_cells_ok &= ok
        print(f"    {mk:<6} {econ:<5} balance full {st.mean(bf):+.3f} vs "
              f"lean {st.mean(bl):+.3f} -> {'SEPARATED' if ok else 'NOT'}")
print(f"    all four cells: {'YES' if all_cells_ok else 'NO'}")

# ------------------------------------------------- exploratory (unregistered)

print()
print("-" * 72)
print("EXPLORATORY (unregistered; net worth in the carry economy is")
print("degenerate under mass bankruptcy — survival carries the fit logic):")
for mk in MODELS:
    for creed in ("full", "lean"):
        rows = cell_rows(mk, creed, "carry")
        surv = [int(r["days_survived"]) for r in rows.values()]
        n_done = sum(1 for r in rows.values() if r["end_reason"] == "completed")
        print(f"    {mk:<6} creed_{creed}: days survived {sorted(surv)} "
              f"(mean {st.mean(surv):.0f}, completed {n_done}/5)")
g_surv_gap = [
    int(cell_rows("gemma", "full", "carry")[s]["days_survived"])
    - int(cell_rows("gemma", "lean", "carry")[s]["days_survived"])
    for s in SEEDS
]
print(f"    Gemma survival gap (full - lean) per seed: {fmt(g_surv_gap)}")
print(f"    mean {st.mean(g_surv_gap):+.1f} days, "
      f"p(full dies sooner) = {perm_p_onesided([-g for g in g_surv_gap]):.4f}")
