"""Score DT0-DT4 and QT1-QT2 on the doctrine transport arm (runs/transport1).

Frozen protocol: docs/osf/DOCTRINE_TRANSPORT.md. Paired contrasts by
seed; sign-flip inference at seed level with EXACT enumeration (2^n
patterns — the registered procedure for this arm); one-sided p per
registered direction; no alpha.

    python scripts/score_transport.py
"""

from __future__ import annotations

import csv
import itertools
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.analysis.doctrine import doctrine_density  # noqa: E402

ROOT = Path("runs/transport1")
LUNA, QWEN = "openai/gpt-5.6-luna", "qwen/qwen3-235b-a22b-2507"
SEEDS = {LUNA: tuple(range(2, 12)), QWEN: (2, 3, 4, 5, 6)}
QT1_WINDOW = (3603, 14412)  # factor 2 of doctrine1's +7,206

ROWS = list(csv.DictReader(open(ROOT / "metrics.csv", encoding="utf-8")))


def cell(model: str, creed: str, econ: str) -> dict[int, dict]:
    out = {}
    for r in ROWS:
        if r["model"] != model or f"creed_{creed}" not in r["cell"]:
            continue
        if (econ == "carry") != r["run_id"].endswith("__cc0p5"):
            continue
        out[int(r["schedule_seed"])] = r
    assert sorted(out) == list(SEEDS[model]), (model, creed, econ, sorted(out))
    return out


def gaps(model: str, econ: str) -> list[float]:
    full, lean = cell(model, "full", econ), cell(model, "lean", econ)
    return [float(full[s]["score"]) - float(lean[s]["score"]) for s in SEEDS[model]]


def exact_p(diffs: list[float]) -> float:
    """One-sided exact sign-flip p over all 2^n patterns."""
    obs = st.mean(diffs)
    n = len(diffs)
    hits = sum(
        sum(s * d for s, d in zip(signs, diffs)) / n >= obs
        for signs in itertools.product((1, -1), repeat=n)
    )
    return hits / 2 ** n


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
print("DOCTRINE TRANSPORT scoring — docs/osf/DOCTRINE_TRANSPORT.md")
comp = sum(1 for r in ROWS if r["end_reason"] == "completed")
print(f"DT0 — validity gate (80%): {comp}/60 completed "
      f"({'PASS' if comp >= 58 else 'FAIL — Luna carry cells void'})")
luna_carry_dead = sum(
    1 for r in ROWS
    if r["model"] == LUNA and r["run_id"].endswith("__cc0p5")
    and r["end_reason"] != "completed"
)
print(f"      Luna carry bankruptcies: {luna_carry_dead} (void threshold: >2)")
print("=" * 72)

g_free = {m: gaps(m, "free") for m in (LUNA, QWEN)}
g_carry = {m: gaps(m, "carry") for m in (LUNA, QWEN)}

print()
print("DT1 — doctrine transports: Luna cc=0 creed effect > 0, 10 pairs. 75%")
gf = g_free[LUNA]
print(f"    per-seed full-lean: {fmt(gf)}")
print(f"    mean {st.mean(gf):+.0f}, {sum(g > 0 for g in gf)}/10 positive, "
      f"exact p = {exact_p(gf):.4f} ({round(exact_p(gf) * 1024)}/1024)")

print()
print("DT2 — attenuation transports: Luna gap_cc0 - gap_cc0.5 > 0, paired. 60%")
inter_l = [a - b for a, b in zip(g_free[LUNA], g_carry[LUNA])]
print(f"    cc=0.5 per-seed full-lean: {fmt(g_carry[LUNA])}  mean {st.mean(g_carry[LUNA]):+.0f}")
print(f"    interaction: {fmt(inter_l)}")
print(f"    mean {st.mean(inter_l):+.0f}, {sum(i > 0 for i in inter_l)}/10 positive, "
      f"exact p = {exact_p(inter_l):.4f}")

print()
print("DT3 — mechanism: Luna creed_full stock lower at cc=0.5, paired. 60%")
sf = {e: [mean_stock(cell(LUNA, 'full', e)[s]['run_id']) for s in SEEDS[LUNA]]
      for e in ("free", "carry")}
d3 = [a - b for a, b in zip(sf["free"], sf["carry"])]
print(f"    stock cc=0:   mean {st.mean(sf['free']):.0f}; cc=0.5: mean {st.mean(sf['carry']):.0f}")
print(f"    paired diff mean {st.mean(d3):+.0f}, {sum(x > 0 for x in d3)}/10 positive, "
      f"exact p = {exact_p(d3):.4f}")

print()
print("DT4 — manipulation check: balance(full) > balance(lean), both economies. 80%")
for econ in ("free", "carry"):
    bf = st.mean(balance(cell(LUNA, "full", econ)[s]["run_id"]) for s in SEEDS[LUNA])
    bl = st.mean(balance(cell(LUNA, "lean", econ)[s]["run_id"]) for s in SEEDS[LUNA])
    print(f"    {econ:<6} full {bf:+.3f} vs lean {bl:+.3f} -> "
          f"{'SEPARATED' if bf > bl else 'NOT SEPARATED'}")

print()
print(f"QT1 — Qwen replication window: fresh cc=0 gap in [{QT1_WINDOW[0]}, {QT1_WINDOW[1]}]. 70%")
mq = st.mean(g_free[QWEN])
print(f"    per-seed: {fmt(g_free[QWEN])}")
print(f"    mean {mq:+.0f} vs doctrine1 +7,206 -> "
      f"{'INSIDE' if QT1_WINDOW[0] <= mq <= QT1_WINDOW[1] else 'OUTSIDE'} the window")

print()
print("QT2 — Qwen attenuation (missing middle): gap_cc0 - gap_cc0.5 > 0. 65%")
inter_q = [a - b for a, b in zip(g_free[QWEN], g_carry[QWEN])]
print(f"    cc=0.5 per-seed full-lean: {fmt(g_carry[QWEN])}  mean {st.mean(g_carry[QWEN]):+.0f}")
print(f"    interaction: {fmt(inter_q)}")
print(f"    mean {st.mean(inter_q):+.0f}, {sum(i > 0 for i in inter_q)}/5 positive, "
      f"exact p = {exact_p(inter_q):.4f} ({round(exact_p(inter_q) * 32)}/32)")

print()
print("WATCH — carry-gap signs: "
      f"Luna {st.mean(g_carry[LUNA]):+.0f} ({sum(g > 0 for g in g_carry[LUNA])}/10 pos), "
      f"Qwen {st.mean(g_carry[QWEN]):+.0f} ({sum(g > 0 for g in g_carry[QWEN])}/5 pos)")
