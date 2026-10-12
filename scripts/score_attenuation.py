"""Score DA0-DA4 on the doctrine attenuation arm (runs/doctrine2).

Frozen protocol: docs/osf/DOCTRINE_ATTENUATION.md. Paired contrasts by
seed; fixed-seed sign-flip permutation as in score_doctrine.py;
one-sided p per registered direction; no alpha.

    python scripts/score_attenuation.py
"""

from __future__ import annotations

import csv
import json
import random
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.analysis.doctrine import doctrine_density  # noqa: E402

ROOT = Path("runs/doctrine2")
SEEDS = (2, 3, 4, 5, 6)
PERM_N = 500_000
rng = random.Random("tnt-attenuation-scoring")
D1_FREE_GAPS = {2: 9056, 3: 7502, 4: 9297, 5: 12820, 6: 7200}  # doctrine1

ROWS = list(csv.DictReader(open(ROOT / "metrics.csv", encoding="utf-8")))


def cell(creed: str, econ: str) -> dict[int, dict]:
    out = {}
    for r in ROWS:
        if f"creed_{creed}" not in r["cell"]:
            continue
        if (econ == "carry") != r["run_id"].endswith("__cc0p5"):
            continue
        out[int(r["schedule_seed"])] = r
    assert sorted(out) == list(SEEDS), (creed, econ, sorted(out))
    return out


def gaps(econ: str) -> list[float]:
    full, lean = cell("full", econ), cell("lean", econ)
    return [float(full[s]["score"]) - float(lean[s]["score"]) for s in SEEDS]


def perm_p(diffs):
    obs = st.mean(diffs)
    hits = sum(
        1 for _ in range(PERM_N)
        if sum(d if rng.random() < 0.5 else -d for d in diffs) / len(diffs) >= obs
    )
    return (hits + 1) / (PERM_N + 1)


def mean_stock(run_id: str) -> float:
    days = [json.loads(l) for l in open(ROOT / run_id / "days.jsonl", encoding="utf-8")]
    return st.mean(sum(d["inventory_start"].values()) for d in days)


def balance(run_id: str) -> float:
    texts = [
        d.get("reflection", "")
        for l in open(ROOT / run_id / "days.jsonl", encoding="utf-8")
        if not (d := json.loads(l)).get("forced")
    ]
    return doctrine_density(texts)["balance"] or 0.0


fmt = lambda v: "[" + ", ".join(f"{x:+.0f}" for x in v) + "]"

print("=" * 72)
print("DOCTRINE ATTENUATION scoring — docs/osf/DOCTRINE_ATTENUATION.md")
comp = sum(1 for r in ROWS if r["end_reason"] == "completed")
print(f"DA0 — validity gate: {comp}/20 completed "
      f"({'PASS, arm scoreable' if comp >= 19 else 'FAIL — ARM VOID'})")
print("=" * 72)

g_free, g_carry = gaps("free"), gaps("carry")
inter = [a - b for a, b in zip(g_free, g_carry)]

print()
print("DA1 — attenuation (primary): gap_cc0 - gap_cc0.5 > 0, paired. 70%")
print(f"    cc=0   per-seed full-lean: {fmt(g_free)}  mean {st.mean(g_free):+.0f}")
print(f"    cc=0.5 per-seed full-lean: {fmt(g_carry)}  mean {st.mean(g_carry):+.0f}")
print(f"    interaction: {fmt(inter)}")
print(f"    mean {st.mean(inter):+.0f}, {sum(i > 0 for i in inter)}/5 seeds positive, "
      f"one-sided p = {perm_p(inter):.4f}")

print()
print("DA2 — replication: fresh cc=0 gap within [4588, 18350] of doctrine1's +9175. 80%")
m = st.mean(g_free)
print(f"    fresh gap {m:+.0f} vs doctrine1 {st.mean(D1_FREE_GAPS.values()):+.0f} "
      f"-> {'INSIDE' if 4588 <= m <= 18350 else 'OUTSIDE'} the window")
per_seed_delta = [g_free[i] - D1_FREE_GAPS[s] for i, s in enumerate(SEEDS)]
print(f"    per-seed fresh-minus-doctrine1: {fmt(per_seed_delta)}")

print()
print("DA3 — mechanism: creed_full mean daily stock lower at cc=0.5, paired. 65%")
sf = {e: [mean_stock(cell('full', e)[s]['run_id']) for s in SEEDS] for e in ("free", "carry")}
d3 = [a - b for a, b in zip(sf["free"], sf["carry"])]
print(f"    stock cc=0:   {[f'{x:.0f}' for x in sf['free']]}  mean {st.mean(sf['free']):.0f}")
print(f"    stock cc=0.5: {[f'{x:.0f}' for x in sf['carry']]}  mean {st.mean(sf['carry']):.0f}")
print(f"    paired diff mean {st.mean(d3):+.0f}, {sum(x > 0 for x in d3)}/5 positive, "
      f"p = {perm_p(d3):.4f}")

print()
print("DA4 — manipulation check: balance(full) > balance(lean), both economies. 85%")
for econ in ("free", "carry"):
    bf = st.mean(balance(cell("full", econ)[s]["run_id"]) for s in SEEDS)
    bl = st.mean(balance(cell("lean", econ)[s]["run_id"]) for s in SEEDS)
    print(f"    {econ:<6} full {bf:+.3f} vs lean {bl:+.3f} -> "
          f"{'SEPARATED' if bf > bl else 'NOT SEPARATED'}")

print()
print("WATCH — sign of the cc=0.5 creed gap: "
      f"mean {st.mean(g_carry):+.0f} ({sum(g > 0 for g in g_carry)}/5 positive)")
