# Interim look 1 — Stage-1 read (spending decision)

**Date:** 2026-07-07 (post-OSF-registration).
**Data examined:** `runs/main3`, Stage 1 complete — Gemma 4 31B + Qwen3
235B-A22B × 4 cells × seeds 2–11 × 90 days (80 agent runs, 20 baseline
runs). Analysis: the frozen pipeline (`analyze`), plus the paired
directional contrasts named in the registered plan.
**Purpose, per the registered interim-look policy (Amendment 1.2):**
spending decision only — continue / expand / stop. **No significance
tests were computed. No predictions are scored here.** Scoring happens
once, on the final collected dataset.

## Data quality

- 80/80 agent runs completed; survival 100%.
- 7 runs contain 1–3 forced days (max 3); 23 runs saw ≥1 nudge. Normal.
- Malformed tool-argument incidents (the Gemma quirk discovered at
  launch): 358 incidents across 34 runs (32 Gemma, 2 Qwen), all handled
  in-run by the error-result path — none fatal. Without the launch-week
  harness hardening these would have been ~34 dead runs.
- Provider-outage handling: three 504-burst failures during collection
  were retried by re-invoking the matrix; all runs eventually completed.
  Harness fixes during collection (malformed-argument handling, retry
  widening, echo envelope) are environment-robustness changes applied
  identically to every cell and model; completed runs never exercised
  the changed paths.
- Narration packs: 0 fallback days across all 20 packs; register audit
  clean (fantasy crisis 7–21% / warm 21–29%; neutral crisis 0–6% / warm
  0–9%).

## Direction-only observations (basis for the decision)

- The pilot's F×R interaction is **not visibly present** in Stage 1:
  paired interaction means are near zero in both models against large
  seed-level spread.
- A **framing main effect is strongly present in Gemma** (fantasy above
  neutral on 9/10 seeds, mean ≈ +4.0k gold ≈ +27% of its neutral-cell
  mean) and **absent-to-slightly-reversed in Qwen** (5/10 seeds).
  This is the probe-#2 pattern the registered P1/P2 disambiguation
  paragraph anticipated — and that paragraph's test ("fantasy above
  neutral within ≥3 of 4 models") **cannot be evaluated without the two
  Stage-2 models.**
- The uptake instruments behave: register_density separates fantasy from
  neutral cleanly in both models (≈0.35–0.61 vs ≈0.01–0.03);
  narration-engagement counts are higher in rich than static cells.
- The ritual metric separates the models as expected (Qwen null-resets
  ≈100–200/run vs Gemma ≈10–22/run).

## Decision

**Continue to Stage 2 as registered** (Sonnet + Gemini × 4 cells × seeds
2–6, ~$105): the central remaining question — whether the framing effect
is uptake-moderated and generalizes across models — is precisely what
Stage 2 exists to answer, and the pre-registered disambiguation reading
requires the 4-model pattern. Stopping now would leave the primary
confirmatory reading unevaluable.

No changes to predictions, metrics, thresholds, or analysis plan are made
at this look.

## Addendum: exploratory qualitative read (same date)

After the decision above was recorded, an exploratory close-reading of
the Stage-1 journals was performed (four readers, one per model ×
framing). Findings are catalogued in
[`STAGE1_SPECIMENS.md`](STAGE1_SPECIMENS.md) and are exploratory /
descriptive only (P10 material). No predictions were scored; no metrics,
thresholds, or analysis steps were changed as a result. One
metric-behavior observation was noted for reporting (frame_break_days
counts some idiomatic uses the close reading judges non-breaks); the
metric is unchanged and both will be reported.
