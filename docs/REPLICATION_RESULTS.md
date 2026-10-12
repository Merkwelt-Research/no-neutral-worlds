# Clean framing replication: results

Scored 2026-07-11 on runs/replication1 (120 Gemma runs: 4 cells x
seeds 12-26 x 2 realizations, 90 days, block-randomized execution,
--block-randomize tnt-replication1 --replicate 1,2) against
docs/osf/REPLICATION.md, by scripts/score_replication.py — the
registered analysis run before any close reading. RP0 checked first;
the three-way rule computed mechanically; verdicts fixed before any
journal was opened.

## Verdict table

| # | prediction (registered confidence) | verdict |
|---|---|---|
| RP0 | all 120 runs complete 90 days (80%) | **HIT** — 120/120 completed; zero bankruptcies; 2 forced days in 10,800; no retries, so no INCIDENTS.md |
| RP1 | three-way rule returns CONFIRM (60%) | **HIT — CONFIRM.** Framing effect +2,865 gold, 90% CI [+1,872, +3,858], permutation p=.0003 (seed-level, n=15). CI lower bound clears zero by a wide margin and the MIE (881) entirely; 13/15 seeds positive, 47/60 pairs. Not joint-RETIRE (upper 3,858 >> 1,973) |
| RP2 | point within factor 2 of main3's +3,947, window [1,973, 7,894] (55%) | **HIT** — +2,865. Smaller than the original, inside the window; consistent with mild inflation in the confounded estimate, not with an artifact |
| RP3 | stock channel: fantasy holds more mean daily stock (70%) | **HIT, overwhelming** — +30.0 units, 90% CI [+21.9, +38.2], p<.0001. The genre-summoned inventory doctrine travels with the frame, again |
| RP4 | schedule variance > sampling variance (60%) | **MISS, and the miss is the finding** — pooled schedule SD 1,327 vs within-seed realization SD 2,782 (variance ratio 0.23; SD ratio 0.48). Within-seed realization variance dominates schedule structure by ~4:1 in variance |

Brier over the five: **0.171** (0.04 + 0.16 + 0.2025 + 0.09 + 0.36)/5.

## The headline

**The framing effect survives clean collection.** Under randomized
complete blocks, fresh seeds, a frozen adapter, and one collection
window, fantasy-framed Gemma out-earns neutral-framed Gemma by
+2,865 gold (+0.93 of this arm's within-cell SD), p=.0003 at the
conservative seed level (exact enumeration of all 32,768 seed-level
sign patterns gives 11/32,768 = .000336; the registered 500k
Monte-Carlo procedure agrees). Leave-one-seed-out estimates stay
within [+2,621, +3,133] (2026-07-11 external verification) — no
single schedule carries the result. The new provenance capture
records mixed-provider routing across nine upstream hosts, 117/120
runs served by more than one (DeepInfra, Together, SambaNova, Novita,
Chutes, Parasail, SiliconFlow, Venice, ModelRun) — recorded as a
nuisance source the effect survives, NOT as nine independent
provider replications (providers were routed within trajectories,
not assigned as a factor). The execution-order objection to the
original estimate is now answered with data: the effect is smaller
than main3's +3,947 but lands inside the registered window, above
the minimally-interesting bound with its whole confidence interval.
This is the arm's registered purpose, achieved: a confirming
interval that is a real confirmation.

**The inventory channel co-replicated** (RP3): fantasy Gemma carries
~30 more units of stock per day, CI nowhere near zero — framing
increased both inventory held and final wealth, consistent with, but
not by itself identifying, the proposed inventory-mediated mechanism
(stock and wealth could in principle be parallel consequences of
other frame-induced policy differences). Two things narrow the
alternatives without closing them. Exploratory, computed at review
time: the realized-price channel is flat — fantasy sold 2,720 units
per run vs neutral's 2,300 (+18%) at realized prices of 22.03 vs
22.27 per unit — so the gap is volume-carried, not margin-carried.
And the mediator itself was manipulated directly in the doctrine
arms (creed_full vs creed_lean, dose-response under carrying cost —
DOCTRINE_RESULTS, ATTENUATION_RESULTS), which is where the causal
status of doctrine -> stock -> gold rests. What remains
unidentified is whether the FRAMING effect specifically travels
that same path; the frame x mechanical-key decomposition remains
the queued experiment for it.

## RP4: the decomposition nobody reports, and what it said

The registered bet — that deterministic schedule differences would
outweigh the residual within-seed variation — was WRONG, and wrong
by a factor, not a whisker:

    cell             schedule SD   within-seed SD   var ratio
    fantasy-rich          1,446        3,075         0.22
    fantasy-static           ~0        3,213         0.00 (floor)
    neutral-rich            807        2,719         0.09
    neutral-static        2,074        1,946         1.14
    pooled                1,327        2,782         0.23

(Ratios are VARIANCE ratios; the pooled SD ratio is 0.48.) Estimand
note, tightened at external review (2026-07-11): the within-seed
component is **within-seed realization variance**, not pure
model-sampling variance — the residual bundles model sampling with
upstream-provider routing, serving-stack variation, and any
within-window temporal effects (117/120 runs were served by more
than one provider, so routing cannot be separated from sampling
here). The ORDERING is robust: an external seed-bootstrap on the
pooled variance ratio gave a 95% interval of roughly 0.05-0.61,
entirely below 1. The attribution to sampling alone would need
single-provider pinning, which this arm did not do.

Same seed, same cell, two draws: the median realization pair differs
by |2,262| gold, the 90th percentile by 7,149, the maximum by 9,964
— a same-everything pair can differ by more than three framing
effects. Long-horizon agent outcomes at temperature 0.7 through a
heterogeneous serving stack are dominated by within-seed realization
variance, not by the world's dealt hand. (Per-cell schedule
components are noisy at n=15 — fantasy-static's estimate hit the
zero floor — but the pooled ordering is not close.)

Three consequences, stated plainly:

1. **Design**: seeds are a weaker blocking variable than assumed —
   most of what a seed-paired design absorbs is not the schedule.
   NOTE (corrected at external review): this does NOT mean future
   budgets should favor realizations over seeds. A fresh seed also
   supplies a fresh realization draw, and at fixed run count the
   fitted components imply 30 seeds x 1 realization would have been
   approximately as efficient as 15 x 2 (slightly more). The
   duplicates earned their cost by making this decomposition
   measurable at all — that, not a precision advantage, is their
   justification.
2. **Reading past arms**: per-seed effect heterogeneity anywhere in
   this program (main3's per-seed framing diffs, doctrine1's per-seed
   creed effects) should not be over-interpreted as seed-specific
   mechanism — much of it is one-draw noise around the cell mean.
3. **The field**: single-run-per-cell agent benchmarks are measuring
   a coin flip on top of their construct. The decomposition is cheap
   (one duplicate realization) and, to our knowledge, unreported
   elsewhere; it belongs in the methods section of the paper.

## Estimation-only quantities (registered as reported-not-predicted)

- F x R interaction: +1,679 (framing gap +3,704 in rich cells vs
  +2,025 in static). [Corrected at external review, 2026-07-11: an
  earlier phrasing said this "matches main3" — it does not. main3's
  Gemma interaction was -77 and the registered pooled Stage-1
  interaction -292. The positive sign matches the original
  pilot-era/theoretical expectation that narration amplifies the
  frame, and disagrees with main3's near-zero estimate.] Per the
  registration this is reported without any new disambiguation
  rule.
- Richness main effect: +449 (small, sign consistent with null-ish
  main3 richness verdicts).
- Within-cell SDs: 2,818-3,388 (pooled 3,068; main3's frozen 2,936 —
  the noise regime transported cleanly).

## Provenance notes

Two pack fallback days disclosed pre-launch (fantasy_s12, neutral_s17,
1 day of 90 each — static-line text; leak grep clean). Requested
temperature 0.7 recorded in every manifest. Zero failed runs, so the
block structure was never broken by retries: every seed's eight runs,
both realizations, executed inside their registered wall-clock
windows.

## Calibration ledger

main 0.203 | doctrine 0.206 | opus 0.277 | ablation 0.133 |
attenuation 0.063 | **replication 0.171**. The RP4 miss carries the
arm's Brier: registered 60% on the wrong side of a 4:1 fact. Scored
and kept — the decomposition was registered precisely because the
answer was genuinely unknown.

## What this changes upstream

RESULTS_MAIN's framing-economics claim upgrades from "suggestive,
heterogeneous" to "replicated in the demonstrated enactor under
randomized execution" — Gemma-specific, as registered; the
out-of-family transport question remains open and queued. The paper's
Experiment 1 now has the shape the external review asked for: original
estimate, confound disclosed, sensitivity analysis, and a
pre-registered clean replication that landed inside its window.
