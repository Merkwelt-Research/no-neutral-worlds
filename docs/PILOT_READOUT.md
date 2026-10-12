# M4 Pilot Readout

**Date:** 2026-07 · **Data:** `runs/smoke/` (40 runs) + `runs/smoke/pilot_metrics.csv`
**Design:** 2 models × 4 cells × 5 seeds × 30 days. Agents:
`qwen/qwen3-235b-a22b-2507`, `google/gemma-4-31b-it`. GM (pinned):
`anthropic/claude-opus-4.8`. All cells share schedules by seed; packs audited
before runs.

---

## Headline

**The F×R interaction is the pilot's signal, in the predicted direction:
narrative richness helps inside the fantasy frame and hurts inside the
neutral frame.** Congruent richness pays; incongruent richness costs.

| model | F+R+ | F+R− | F−R+ | F−R− |
|---|---|---|---|---|
| gemma-4-31b | **9216** ± 1302 | 8532 ± 536 | 8053 ± 930 | **9386** ± 834 |
| qwen3-235b | **4517** ± 1689 | 3013 ± 940 | 4110 ± 745 | **5048** ± 1066 |

Within-seed paired contrasts (all cells share schedules, so seeds pair):

- Interaction (F+R+ − F+R−) − (F−R+ − F−R−): gemma +2017, qwen +2442, same
  sign in both models; **pooled across the 10 (model, seed) pairs:
  mean +2229, exact sign-flip permutation p = 0.023** (7/10 pairs positive).
- Framing main effect: null (gemma p=.75; qwen −814, p=.125 — driven
  entirely by qwen's weak fantasy-static cell, i.e. the interaction again).
- Richness main effect: null in both (p=.44, .56).

Notably, narration *length* cannot explain the crossover: the neutral packs
are slightly longer than the fantasy packs (461–486 vs 425–466 mean chars),
yet rich text helps only in fantasy. Whatever the mechanism, it is not
token-volume distraction.

Caveats in proportion: one planned contrast of three at p=.023 with n=5
seeds/cell/model is effect-direction evidence, not a result. It is exactly
what a pilot is for: the interaction is real enough to power the main
experiment around.

## Manipulation check: uptake landed

`narration_engagement_count` (narration content-words reappearing in the
day's journal): rich cells 1.1–2.8 words/day vs 0.5–0.7 in static cells,
highest in fantasy-rich for both models (gemma 2.83, qwen 1.48). The
journal/log persona invitation works: fantasy entries carry voice and
world-reference; neutral entries stay procedural (schema asymmetry
preserved in both directions).

## No collapse at 30 days — as the spec's risk check anticipated

100% survival in all 40 runs; nudges ≈ 0; zero forced days; novelty slopes
uniformly shallow (≈ −0.006) in every cell. There is no degradation
variance at this horizon with these models, so **H2 (trace health predicts
economic failure) is untestable at 30 days** — the H2 correlations
(|rho| ≤ .36, inconsistent across models) are noise around healthy
trajectories. Per spec §1.2, pressure comes from horizon, never ambiguity:
**the main experiment runs at 90 days.**

## Model gap (incidental)

Gemma-4-31B grand mean **8797 (~79% of the per-seed oracle ceiling)** vs
Qwen3-235B-A22B **4172 (~37%)**, heuristic ≈ 2800, oracle 9486–12583 by
seed. Less surprising than the headline numbers suggest: Qwen is a
mixture-of-experts model with only 22B parameters active per token, so in
active compute this is roughly 31B dense vs 22B active — comparable tiers,
with Gemma-4 the stronger of the two at this task.

## Instrument notes

- **Pack audit (Opus GM):** crisis-day parity achieved (fantasy 7–13%,
  neutral 0–3%), lengths matched, zero fallbacks in 300 generations. One
  register-intrinsic asymmetry remains: internal lexical diversity
  (fantasy ≈ 0.28, neutral ≈ 0.16) — flat operational prose is inherently
  narrower. Recorded as a pack-level covariate, not fixable without
  breaking the register.
- **Encoding bug (fixed):** `Path.read_text/write_text` used platform
  defaults; on Windows this wrote cp1252 pack artifacts and — worse — served
  the agents mojibake em-dashes in system prompts ("â€""). The corruption
  was identical across cells (parallel prompts), so the pilot's contrasts
  stand, but all text I/O is now explicit UTF-8 and main-run prompts will be
  clean.

## 90-day probe addendum (4 models × 4 cells × 1 seed × 90 days)

The pre-main probe (`runs/main`, later superseded) earned its cost several
times over:

1. **Economy exploit found and fixed.** Expected sales were linear in stock
   (`qty × p`, no saturation), so full reinvestment compounds exponentially.
   Gemini 3.1 Pro discovered this: stock 133 → 1,272 → **88,197 units**,
   21,683 units sold on day 90, final score **1,515,390** (vs 14–48k for
   everyone else). Fixed via `customers_per_day` demand saturation (spec
   §2.5); heuristic golden unchanged, oracle 11470 → 11330. All probe runs
   are pre-fix and excluded from analysis.
2. **Thinking-token pricing measured.** Per 90-day run: Gemini 3.1 Pro
   ~200–355k completion tokens (~$4.5–6/run), Sonnet 5 ~116–184k
   (~$4–4.5/run), Gemma/Qwen ~37–44k (pennies to ~$0.40).
3. **Still no collapse at 90 days.** All 16 runs survived; novelty slopes
   ≈ −0.001; agents ordering into the final week. Modern models in a fully
   disclosed, episodic environment do not spontaneously degrade even over a
   quarter-year horizon. For the paper this reframes H2: not "trace health
   predicts failure" (no failures exist to predict) but trace health as a
   graded outcome in its own right — and the collapse-resistance of the
   disclosed/episodic design relative to VB's ambiguity-driven meltdowns is
   itself a reportable contrast.
4. **Same-family GM check clean.** Sonnet 5's rich-cell uptake (1.78
   words/day) sits mid-pack below Gemma (2.12) and Gemini (1.98) — no
   Opus-affinity anomaly; one-line limitation for the paper.
5. **Neutral pack diversity degrades at long horizons** (novelty 0.09 at
   h90): GM history window raised 5 → 8 and the neutral style now rotates
   subject matter across weeks. Packs must be regenerated post-change, so
   the main run starts from a fresh directory.

## Recommendations for the main experiment (M6)

1. **Horizon 90**, same 2×2, same pinned GM, packs audited per seed.
2. **10 seeds per cell**; keep both models (the interaction replicated
   across a 31B and a 235B — that cross-model consistency is the pilot's
   strongest feature; a third mid-tier model would strengthen the mixed
   model).
3. Pre-register the interaction as the primary contrast (the pilot tested
   three; the main should commit to one).
4. Report pack diversity and register rates as covariates; keep the
   engagement manipulation check.
5. Cost at *actual* pilot prices (whole pilot: 14.4M in / 0.5M out ≈ $5):
   agent side of 80 × 90-day runs ≈ 86M in ≈ **$30–35**; the Opus GM's 20
   packs × 90 days ≈ **$50–60** now dominate. Total **< $100** — so prefer
   upgrading the design (15 seeds, a third model ≈ +$60) over economizing;
   wall-clock via `--parallel`, not budget, is the binding constraint.
