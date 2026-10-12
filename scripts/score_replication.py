"""Score the clean framing replication (docs/osf/REPLICATION.md).

Implements the registered analysis byte-for-byte:
- primary quantity: Gemma framing effect (fantasy - neutral, final net
  worth), paired within (richness x seed x realization) = 60 pairs,
  analyzed at seed level (each seed = mean of its 4 diffs, n=15)
- inference: fixed-seed sign-flip permutation at seed level (500k,
  rng=random.Random("tnt-scoring")), one-sided; 90% CI by t on the 15
  seed means (two one-sided 5%)
- three-way rule: CONFIRM (CI lower > 0 AND point >= 881),
  RETIRE (CI upper < 1,973), else AMBIGUOUS (joint CONFIRM+RETIRE
  reported as "replicates, smaller")
- RP2 window [1,973, 7,894]; RP3 stock channel (mean daily on-hand
  stock, same pairing); RP4 variance decomposition (sampling from
  realization pairs, schedule from seed spread)

Everything below reads runs/replication1 result.json + days.jsonl only.
"""

from __future__ import annotations

import itertools
import json
import math
import random
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = "runs/replication1"
MIE = 881.0          # 0.3 x main3 within-Gemma pooled within-cell SD (frozen)
RETIRE_BOUND = 1973.0  # half of main3's +3,947 (frozen)
WINDOW = (1973.0, 7894.0)
T_95_14 = 1.7613     # t(0.95, df=14), two one-sided 5% -> 90% CI
N_PERM = 500_000


def load_runs() -> list[dict]:
    runs = []
    for path in sorted(Path(ROOT).glob("*gemma*/result.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        framing, richness = r["cell"].split("-")
        rep = 2 if r["run_id"].endswith("__r2") else 1
        runs.append({
            "framing": framing, "richness": richness, "seed": r["schedule_seed"],
            "rep": rep, "score": float(r["score"]), "dir": path.parent,
        })
    assert len(runs) == 120, f"expected 120 gemma runs, found {len(runs)}"
    return runs


def mean_daily_stock(run_dir: Path) -> float:
    totals = []
    for line in (run_dir / "days.jsonl").read_text(encoding="utf-8").splitlines():
        day = json.loads(line)
        totals.append(sum(day["inventory_start"].values()))
    return st.mean(totals)


def seed_level(diffs_by_seed: dict[int, list[float]]) -> tuple[list[float], float, float, float, float, float]:
    """Return (seed means, point, ci_lo, ci_hi, MC p, exact p).

    The registered procedure is the 500k Monte-Carlo sign-flip; with 15
    seed units the full 2^15 = 32,768 sign patterns are also enumerable
    exactly (2026-07-11 external review), so both are reported — the MC
    p scores the registration, the exact p is the number of record."""
    means = [st.mean(v) for _, v in sorted(diffs_by_seed.items())]
    n = len(means)
    point = st.mean(means)
    half = T_95_14 * st.stdev(means) / math.sqrt(n)
    rng = random.Random("tnt-scoring")
    hits = 0
    for _ in range(N_PERM):
        flipped = sum(m if rng.random() < 0.5 else -m for m in means) / n
        if flipped >= point:
            hits += 1
    exact_hits = sum(
        sum(s * m for s, m in zip(signs, means)) / n >= point
        for signs in itertools.product((1, -1), repeat=n)
    )
    return means, point, point - half, point + half, hits / N_PERM, exact_hits / 2 ** n


def paired_diffs(runs: list[dict], value: dict) -> dict[int, list[float]]:
    """fantasy - neutral within (richness, seed, rep), grouped by seed."""
    cell_val = {(r["framing"], r["richness"], r["seed"], r["rep"]): value[id(r)] for r in runs}
    by_seed: dict[int, list[float]] = defaultdict(list)
    for richness in ("rich", "static"):
        for seed in sorted({r["seed"] for r in runs}):
            for rep in (1, 2):
                by_seed[seed].append(
                    cell_val[("fantasy", richness, seed, rep)]
                    - cell_val[("neutral", richness, seed, rep)]
                )
    return by_seed


def main() -> None:
    runs = load_runs()
    seeds = sorted({r["seed"] for r in runs})

    # ---- RP1/RP2: framing effect on final net worth ----
    score_of = {id(r): r["score"] for r in runs}
    by_seed = paired_diffs(runs, score_of)
    means, point, lo, hi, p, p_exact = seed_level(by_seed)
    confirm = lo > 0 and point >= MIE
    retire = hi < RETIRE_BOUND
    verdict = ("CONFIRM+RETIRE (replicates, smaller)" if confirm and retire
               else "CONFIRM" if confirm else "RETIRE" if retire else "AMBIGUOUS")
    print("== RP1 framing effect (seed level, n=15) ==")
    print(f"seed means: {[round(m) for m in means]}")
    print(f"point {point:+.0f}  90% CI [{lo:+.0f}, {hi:+.0f}]  "
          f"MC p={p:.4f}  exact p={p_exact:.6f} ({round(p_exact * 2**15)}/32768)")
    print(f"rule -> {verdict}   (MIE {MIE:.0f}, retire bound {RETIRE_BOUND:.0f})")
    in_window = WINDOW[0] <= point <= WINDOW[1]
    print(f"== RP2 window {WINDOW}: point {point:+.0f} -> {'HIT' if in_window else 'MISS'}")

    # positive-pair counts for texture
    all_diffs = [d for v in by_seed.values() for d in v]
    print(f"pairs positive: {sum(d > 0 for d in all_diffs)}/60; "
          f"seeds positive: {sum(m > 0 for m in means)}/15")

    # ---- RP3: stock channel ----
    stock_of = {id(r): mean_daily_stock(r["dir"]) for r in runs}
    s_by_seed = paired_diffs(runs, stock_of)
    s_means, s_point, s_lo, s_hi, s_p, s_p_exact = seed_level(s_by_seed)
    print("\n== RP3 stock channel (mean daily on-hand units, fantasy - neutral) ==")
    print(f"point {s_point:+.2f}  90% CI [{s_lo:+.2f}, {s_hi:+.2f}]  "
          f"MC p={s_p:.4f}  exact p={s_p_exact:.6f}"
          f"  -> {'HIT' if s_point > 0 else 'MISS'} (registered: direction)")

    # ---- RP4: variance decomposition ----
    # Estimand note (external review 2026-07-11): the within-seed
    # component is within-seed REALIZATION variance — model sampling
    # bundled with provider routing, serving-stack variation, and
    # within-window temporal effects — not pure model-sampling variance.
    print("\n== RP4 variance decomposition (final net worth) ==")
    cells = sorted({(r["framing"], r["richness"]) for r in runs})
    samp_sq, per_cell = [], {}
    for cell in cells:
        cell_runs = {(r["seed"], r["rep"]): r["score"] for r in runs
                     if (r["framing"], r["richness"]) == cell}
        pair_d = [cell_runs[(s, 1)] - cell_runs[(s, 2)] for s in seeds]
        cell_samp = st.mean(d * d for d in pair_d) / 2
        seed_means_cell = [(cell_runs[(s, 1)] + cell_runs[(s, 2)]) / 2 for s in seeds]
        cell_sched = st.variance(seed_means_cell) - cell_samp / 2
        per_cell[cell] = (cell_sched, cell_samp)
        samp_sq.extend(d * d for d in pair_d)
    samp = st.mean(samp_sq) / 2
    sched = st.mean(max(v[0], 0.0) for v in per_cell.values())
    for cell, (c_sched, c_samp) in per_cell.items():
        print(f"  {'-'.join(cell):<16} schedule sd {math.sqrt(max(c_sched,0)):>7.0f}   "
              f"within-seed sd {math.sqrt(c_samp):>7.0f}   var ratio {max(c_sched,0)/c_samp:5.2f}")
    print(f"  pooled           schedule sd {math.sqrt(sched):>7.0f}   "
          f"within-seed sd {math.sqrt(samp):>7.0f}   var ratio {sched/samp:5.2f}"
          f" (sd ratio {math.sqrt(sched/samp):.2f})"
          f"   -> {'HIT' if sched > samp else 'MISS'} (registered: schedule > within-seed)")

    # ---- estimation-only: F x R interaction, richness main effect ----
    def cell_mean(f, r):
        return st.mean(x["score"] for x in runs if x["framing"] == f and x["richness"] == r)
    fr = {(f, r): cell_mean(f, r) for f in ("fantasy", "neutral") for r in ("rich", "static")}
    interaction = (fr[("fantasy", "rich")] - fr[("neutral", "rich")]) - \
                  (fr[("fantasy", "static")] - fr[("neutral", "static")])
    richness_eff = st.mean([fr[("fantasy", "rich")], fr[("neutral", "rich")]]) - \
                   st.mean([fr[("fantasy", "static")], fr[("neutral", "static")]])
    per_cell_sd = {c: st.stdev([x["score"] for x in runs
                   if (x["framing"], x["richness"]) == c]) for c in cells}
    print("\n== estimation-only ==")
    print(f"F x R interaction (rich gap - static gap): {interaction:+.0f}")
    print(f"richness main effect: {richness_eff:+.0f}")
    print(f"within-cell SDs: " + ", ".join(f"{'-'.join(c)} {v:.0f}" for c, v in per_cell_sd.items()))
    pooled_sd = math.sqrt(st.mean(v * v for v in per_cell_sd.values()))
    print(f"pooled within-cell SD this arm: {pooled_sd:.0f} "
          f"(main3 frozen: 2936; effect in arm-SD units: {point/pooled_sd:+.2f})")

    # ---- realization-pair gap distribution (estimation-only) ----
    gaps = sorted(math.sqrt(d) for d in samp_sq)
    print(f"realization-pair |gap|: median {gaps[len(gaps)//2]:.0f}, "
          f"p90 {gaps[int(len(gaps)*0.9)]:.0f}, max {gaps[-1]:.0f}")


if __name__ == "__main__":
    main()
