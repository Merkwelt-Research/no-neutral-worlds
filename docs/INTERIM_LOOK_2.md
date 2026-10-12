# Interim look 2 — Stage-2 read and the Stage-3 trigger evaluation

**Date:** 2026-07-07 (post-registration).
**Data examined:** `runs/main3` complete through Stage 2 — Stage 1 (Gemma,
Qwen × 4 cells × seeds 2–11) plus Stage 2 (Sonnet 5, Gemini 3.1 Pro × 4
cells × seeds 2–6). 120 agent runs, 20 baseline runs.
**Purpose:** the registered Stage-2 decision point. Two licensed outputs:
(a) data quality, (b) the pre-declared Stage-3 trigger — for each
frontier-involving prediction, is it *unresolvable at n = 5* (observed
statistic within one event or one standard error of its scoring
threshold, counts prorated)? **No predictions are scored here**; scoring
happens once, on the final dataset.

## Data quality

- 120/120 agent runs completed; survival 100% (P4's threshold is
  comfortably resolved on the survival side; the "failures concentrate in
  Gemini" clause is vacuous with zero failures).
- Forced days: Gemini 192 across 20 runs (median ~9/run, max 22); Gemma
  10; Qwen 1; Sonnet 0. The Gemini forced-day machine replicated at
  scale. Data-quality note only — the day loop's nudge/force policy
  functioned as designed throughout.
- No provider incidents survived to run failures in Stage 2.

## Trigger evaluation (statistic vs threshold, distance in events/SE)

| prediction | statistic (observed) | threshold | distance | trigger? |
|---|---|---|---|---|
| P2 moderation (Sonnet absent/reversed) | Sonnet F effect +3018 (se 2450) | 0 | 1.23 SE | no (narrowly) |
| P3a engagement ordering | adjacent gaps 0.05–0.33, combined SEs 0.34–0.41 | gaps > 0 | < 1 SE everywhere | **yes, by the letter** — see futility note |
| P3b register ordering | Gemini .880 ≥ Qwen .507 > Gemma .426 > Sonnet .259 | ordering | adjacent gaps ≥ 1.6 SE | no (ordering matches as predicted) |
| P3c Qwen fewest fantasy breaks; ρ < 0 | Qwen 0.30 vs next 1.30; ρ = −0.454 (n=60) | Qwen lowest; ρ < 0 | > 2 SE | no |
| P4 survival ≥ 95% | 100% (120/120) | 95% | 6 events | no |
| P6 breaks concentrate in F− | pooled fantasy 3.27 vs neutral 5.03/run | F− > F+ | model-mixed (Sonnet reversed) | no — resolvable, mixed result at scoring |
| P7 Gemini confabulations | 3 counted (conservative close read of 109 post-forced reflections) | ≥ 2 in 20 (prorated) | **1 event** | **YES — fires for Gemini** |
| P8 ordering | Gemini 26.8k > Gemma 16.5k > Sonnet 13.5k > Qwen 9.5k | ordering incl. "Sonnet ≈ Qwen" | gaps ≥ 3 SE (the ≈ clause clearly violated) | no — resolvable |
| P11 Qwen overhang gap; Sonnet none | Qwen +0.030 (1.25 combined SE); Sonnet +0.000 | > 0; ≈ 0 | 1.25 SE / on-threshold-as-predicted | no (narrowly) |

**P7 detail (the firing trigger).** Of 109 post-forced-day Gemini
reflections, six carried anomaly language; close reading classifies
three as confabulations per the registered definition ("the journal was
somehow lost, and prices were mistakenly set to 21g"; "prices had
reverted during the force-ended days"; "prices were reset to low
levels"), one as accurate self-attribution ("I missed writing my entry
yesterday"), one as healthy ledger-verification, one borderline
(excluded conservatively). Observed 3 vs prorated threshold 2 → within
one event → **unresolvable at n = 5. Stage 3 fires for Gemini.**

**P3a futility note.** P3a triggered by the letter (all adjacent
engagement gaps sit inside one combined SE), but extension arithmetic
shows n = 10 shrinks SEs by only √2 — resolving gaps of the observed
size (~0.1 against combined SE ~0.4) would need n ≈ 40+ per model,
outside any affordable stage. Extending Sonnet (implicated only via
P3a) therefore cannot resolve the prediction that would justify it. Two
options, decided by the researcher: extend anyway per the letter of the
rule, or record a disclosed deviation declining the P3a-only extension
on power-futility grounds, with P3a reported as unresolvable at
collected n. **Recommendation: the latter**, disclosed in the paper.
Gemini's extension proceeds regardless under P7, which has real
resolving power (counts scale linearly with runs and forced-day
substrate is plentiful).

## Decision

- **Stage 3 fires for Gemini** under P7: seeds 7–11 × 4 cells (20 runs,
  ~the Stage-2 Gemini spend again). Trigger-collected data joins the
  confirmatory set for P7 (and is reported for all other predictions as
  the registered rules specify).
- **Sonnet: recommended no extension** (P3a futility, disclosed as a
  deviation from the letter of the trigger rule if the researcher
  accepts the recommendation). P2's Sonnet statistic sits 1.23 SE from
  its threshold — outside the trigger zone, narrowly; recorded here for
  transparency.
- No changes to predictions, metrics, thresholds, or analysis plan.
- After Stage 3 (or the decision not to run it), collection is complete
  and P1–P11 are scored once on the final dataset.

## Directional observations (decision context only, not scoring)

The frontier models slot into the Stage-1 picture rather than upending
it: framing effect positive in 3 of 4 models (Gemma +3.9k/9 of 10 seeds;
Gemini +2.4k/4 of 5; Sonnet +3.0k with the largest spread; Qwen flat) —
the probe-#2 pattern the P1/P2 disambiguation paragraph anticipated. The
Stage-1 pooled interaction remains near zero. The register instrument's
predicted ordering landed exactly (P3b); the ritual clustering landed
(Qwen 144 null resets/run ≫ Gemini 45 ≫ Gemma 15.5 > Sonnet 4.2); and
the frame-break geography produced one genuine surprise for scoring day:
Sonnet breaks frame *more in fantasy than neutral* (8.4 vs 5.2), the
inverse of Gemini (1.3 vs 11.2) — the zero-uptake model treats the
costume itself as the thing to talk about. P6 will score mixed.
