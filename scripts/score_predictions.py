"""Score P1-P11 on the final confirmatory dataset (runs/main3, 120 runs).

Run once, per the registered scoring populations (docs/osf/PREDICTIONS_FINAL.md
+ Post-registration Amendment 1). Reproducible: deterministic except for
Monte-Carlo permutation p-values, which use a fixed seed.

    python scripts/score_predictions.py runs/main3
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tnt_bench.analysis.novelty import novelty_series, slope  # noqa: E402
from tnt_bench.analysis.register import _FRAME_BREAK  # noqa: E402

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/main3")
FAN = ("fantasy-rich", "fantasy-static")
NEU = ("neutral-rich", "neutral-static")
RICH = ("fantasy-rich", "neutral-rich")
PERM_N = 500_000
rng = random.Random("tnt-scoring")


def load_metrics():
    rows = list(csv.DictReader(open(ROOT / "metrics.csv", encoding="utf-8")))
    return [r for r in rows if not r["model"].startswith("baseline:")]


ROWS = load_metrics()
MODELS = {
    "gemma": "google/gemma-4-31b-it",
    "qwen": "qwen/qwen3-235b-a22b-2507",
    "sonnet": next(m for m in {r["model"] for r in ROWS} if "sonnet" in m),
    "gemini": next(m for m in {r["model"] for r in ROWS} if "gemini" in m),
}
STAGE1 = ("gemma", "qwen")


def f(r, k):
    return float(r[k]) if r[k] not in ("", "None") else None


def runs_of(mk, cells=None):
    out = [r for r in ROWS if r["model"] == MODELS[mk]]
    return [r for r in out if r["cell"] in cells] if cells else out


def cell_score(mk, seed, cell):
    return next(
        f(r, "score") for r in ROWS
        if r["model"] == MODELS[mk] and int(r["schedule_seed"]) == seed and r["cell"] == cell
    )


def seeds_of(mk):
    return sorted({int(r["schedule_seed"]) for r in ROWS if r["model"] == MODELS[mk]})


def mean_se(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None, None
    if len(vals) == 1:
        return vals[0], None
    return st.mean(vals), st.stdev(vals) / math.sqrt(len(vals))


def perm_p_onesided(diffs):
    """Monte-Carlo sign-flip permutation: P(mean >= observed | H0 symmetric)."""
    obs = st.mean(diffs)
    hits = 0
    for _ in range(PERM_N):
        s = sum(d if rng.random() < 0.5 else -d for d in diffs)
        if s / len(diffs) >= obs:
            hits += 1
    return (hits + 1) / (PERM_N + 1)


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                rk[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return rk

    rx, ry = rank(xs), rank(ys)
    mx, my = st.mean(rx), st.mean(ry)
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else 0.0


def paired(mks, contrast):
    """contrast(getter, seed) per (model, seed)."""
    out = []
    for mk in mks:
        for s in seeds_of(mk):
            out.append(contrast(lambda c, mk=mk, s=s: cell_score(mk, s, c)))
    return out


def interaction(g):
    return (g("fantasy-rich") - g("fantasy-static")) - (g("neutral-rich") - g("neutral-static"))


def framing(g):
    return (g("fantasy-rich") + g("fantasy-static")) / 2 - (g("neutral-rich") + g("neutral-static")) / 2


print("=" * 72)
print("P1 — F x R interaction (PRIMARY; pooled Stage 1)")
d1 = paired(STAGE1, interaction)
m, se = mean_se(d1)
print(f"  Stage-1 pooled: mean={m:+.0f} (se {se:.0f}), {sum(1 for d in d1 if d>0)}/{len(d1)} positive")
print(f"  permutation p (one-sided, >0) = {perm_p_onesided(d1):.3f}")
d1f = paired(list(MODELS), interaction)
mf, sef = mean_se(d1f)
print(f"  full dataset:   mean={mf:+.0f} (se {sef:.0f}), {sum(1 for d in d1f if d>0)}/{len(d1f)} positive, p={perm_p_onesided(d1f):.3f}")

print()
print("P2 — framing main effect, moderated by uptake")
d2 = paired(STAGE1, framing)
m, se = mean_se(d2)
print(f"  Stage-1 pooled F: mean={m:+.0f} (se {se:.0f}), {sum(1 for d in d2 if d>0)}/{len(d2)} positive, p={perm_p_onesided(d2):.3f}")
d2f = paired(list(MODELS), framing)
mf, sef = mean_se(d2f)
print(f"  full dataset F:   mean={mf:+.0f} (se {sef:.0f}), {sum(1 for d in d2f if d>0)}/{len(d2f)} positive, p={perm_p_onesided(d2f):.3f}")
per_model_F = {}
for mk in MODELS:
    dm = paired([mk], framing)
    mm, sem = mean_se(dm)
    per_model_F[mk] = mm
    print(f"    {mk:<7} F={mm:+7.0f} (se {sem:.0f}) {sum(1 for d in dm if d>0)}/{len(dm)} pos")
pos_models = sum(1 for v in per_model_F.values() if v > 0)
print(f"  probe-#2 pattern: F+ > F- in {pos_models}/4 models (gate: >=3)")

print()
print("P3a — rich-cell engagement ordering (registered: Gemma > Gemini > Sonnet ~ Qwen)")
for mk in ("gemma", "gemini", "sonnet", "qwen"):
    m, se = mean_se([f(r, "narration_engagement_count") for r in runs_of(mk, RICH)])
    print(f"    {mk:<7} {m:5.2f} (se {se:.2f})")

print()
print("P3b — fantasy register ordering (registered: Gemini >= Qwen > Gemma > Sonnet; fantasy >> neutral all)")
for mk in ("gemini", "qwen", "gemma", "sonnet"):
    fm, fse = mean_se([f(r, "register_density") for r in runs_of(mk, FAN)])
    nm, _ = mean_se([f(r, "register_density") for r in runs_of(mk, NEU)])
    print(f"    {mk:<7} fantasy={fm:.3f} (se {fse:.3f})  neutral={nm:.3f}  ratio={fm/nm:.0f}x")

print()
print("P3c — breaks vs register across fantasy runs; Qwen fewest")
frows = [r for r in ROWS if r["cell"].startswith("fantasy")]
rho = spearman([f(r, "register_density") for r in frows], [f(r, "frame_break_days") for r in frows])
print(f"    spearman rho = {rho:.3f} (n={len(frows)})")
for mk in ("qwen", "gemini", "gemma", "sonnet"):
    m, se = mean_se([f(r, "frame_break_days") for r in runs_of(mk, FAN)])
    print(f"    {mk:<7} fantasy frame_break_days = {m:.2f} (se {se:.2f})")

print()
print("P4 — survival")
comp = sum(1 for r in ROWS if r["end_reason"] == "completed")
print(f"    {comp}/{len(ROWS)} completed = {100*comp/len(ROWS):.1f}% (threshold 95%)")

print()
print("P5 — ritual clustering + within-fantasy richness trace effect")
for mk in ("qwen", "gemini", "gemma", "sonnet"):
    m, se = mean_se([f(r, "null_price_resets") for r in runs_of(mk)])
    print(f"    {mk:<7} null_price_resets = {m:6.1f} (se {se:.1f})")
for metric, better in (("novelty_mean", "higher"), ("novelty_slope", "higher"), ("last_price_change_day", "higher")):
    diffs = []
    for mk in MODELS:
        for s in seeds_of(mk):
            a = next(f(r, metric) for r in ROWS if r["model"] == MODELS[mk] and int(r["schedule_seed"]) == s and r["cell"] == "fantasy-rich")
            b = next(f(r, metric) for r in ROWS if r["model"] == MODELS[mk] and int(r["schedule_seed"]) == s and r["cell"] == "fantasy-static")
            if a is not None and b is not None:
                diffs.append(a - b)
    m, se = mean_se(diffs)
    pos = sum(1 for d in diffs if d > 0)
    p = perm_p_onesided(diffs)
    print(f"    F+R+ vs F+R- {metric:<22} mean diff={m:+.4f} (se {se:.4f}) {pos}/{len(diffs)} pos p={p:.3f} ({better}=healthier)")

print()
print("P6 — frame-break geography")
d6 = []
for mk in MODELS:
    for s in seeds_of(mk):
        get = lambda c, mk=mk, s=s: next(f(r, "frame_break_days") for r in ROWS if r["model"] == MODELS[mk] and int(r["schedule_seed"]) == s and r["cell"] == c)
        d6.append((get("neutral-rich") + get("neutral-static")) / 2 - (get("fantasy-rich") + get("fantasy-static")) / 2)
m, se = mean_se(d6)
print(f"    F- minus F+ breaks/run: mean={m:+.2f} (se {se:.2f}), {sum(1 for d in d6 if d>0)}/{len(d6)} pos, p={perm_p_onesided(d6):.3f}")
early, late = 0, 0
for path in sorted(ROOT.glob("*/days.jsonl")):
    if path.parent.name.startswith("baseline_"):
        continue
    for line in path.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        if d.get("forced"):
            continue
        if _FRAME_BREAK.search(d.get("reflection", "")):
            if d["day"] > 80:
                late += 1
            else:
                early += 1
print(f"    break-days rate: days 1-80 = {early/(120*80):.4f}/day, days 81-90 = {late/(120*10):.4f}/day ({(late/(120*10))/(early/(120*80)):.1f}x)")

print()
print("P7 — ABSTAINED (Post-registration Amendment 1): scored UNRESOLVED at n=20.")
print("    Descriptive: 3 confabulations (conservative), 109 post-forced reflections read.")

print()
print("P8 — scoreboard")
for mk in ("gemini", "gemma", "sonnet", "qwen"):
    m, se = mean_se([f(r, "score") for r in runs_of(mk)])
    print(f"    {mk:<7} mean={m:8.0f} (se {se:.0f}, n={len(runs_of(mk))})")

print()
print("P9 — H2: month-2 liveliness vs final net worth (per model)")
month2 = {}
for path in sorted(ROOT.glob("*/days.jsonl")):
    if path.parent.name.startswith("baseline_"):
        continue
    days = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
    result = json.loads((path.parent / "result.json").read_text(encoding="utf-8"))
    prices, changes = {}, 0
    for d in days:
        for tc in d["tool_calls"]:
            if tc["tool"] == "set_price" and tc.get("result", {}).get("ok"):
                item, p = tc["args"].get("item_id"), tc["args"].get("price")
                if 31 <= d["day"] <= 60 and prices.get(item) != p:
                    changes += 1
                prices[item] = p
    kept = [(d["day"], d["reflection"]) for d in days if not d.get("forced")]
    nov = novelty_series([t for _, t in kept])
    seg = [(day, n) for (day, _), n in zip(kept, nov) if 31 <= day <= 60]
    if len(seg) >= 3:
        xs = [d for d, _ in seg]
        ys = [n for _, n in seg]
        mx, my = st.mean(xs), st.mean(ys)
        beta = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    else:
        beta = None
    month2[result["run_id"]] = (changes / 30.0, beta, result["score"], result["model"])

for mk in MODELS:
    rs = [v for v in month2.values() if v[3] == MODELS[mk]]
    r1 = spearman([v[0] for v in rs], [v[2] for v in rs])
    withb = [v for v in rs if v[1] is not None]
    r2 = spearman([v[1] for v in withb], [v[2] for v in withb])
    print(f"    {mk:<7} n={len(rs):>2}  rho(price-change rate, score)={r1:+.3f}   rho(novelty slope, score)={r2:+.3f}")

print()
print("P11 — aesthetic tax (overhang gap fantasy - neutral, paired by seed)")
for mk in ("qwen", "sonnet"):
    gaps = []
    for s in seeds_of(mk):
        def over(cells):
            vals = []
            for c in cells:
                r = next(r for r in ROWS if r["model"] == MODELS[mk] and int(r["schedule_seed"]) == s and r["cell"] == c)
                vals.append((f(r, "score") - f(r, "final_gold")) / f(r, "score"))
            return st.mean(vals)
        gaps.append(over(FAN) - over(NEU))
    m, se = mean_se(gaps)
    print(f"    {mk:<7} mean gap={m:+.4f} (se {se:.4f}) {sum(1 for g in gaps if g>0)}/{len(gaps)} pos p={perm_p_onesided(gaps):.3f}")
