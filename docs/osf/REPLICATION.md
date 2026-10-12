# Clean framing replication: one deep cohort, randomized blocks

Pre-registration for the protocol-clean replication of the main 2x2
(Experiment 1 of the main paper), committed before any of its data
exist: no runs, schedules, or packs for this arm exist at this
document's git timestamp, and none will be generated until it is
posted as an OSF addendum.

Revision note (2026-07-10, pre-posting, pre-data): an earlier draft
of this document (repo git history) included a second, out-of-family
model (Grok 4.5). Dropped before posting: the vulnerable claim is a
Gemma claim, and the freed budget buys what the claim actually needs
— power. Out-of-family transport is a separate question and will get
its own registration (the doctrine-attenuation transport test is the
queued candidate).

Why this arm exists. The main collection (runs/main3) executed
conditions in fixed model -> cell -> seed blocks, so treatment is
partially confounded with wall-clock time — the paper's most
vulnerable point (2026-07-10 external review; RESULTS_MAIN Addendum 2
item 5 records the sensitivity analysis: pooled framing +1,384 p=.084
falls to +515 p=.330 excluding five pre-hardening Gemma runs, while
the direct adapter-group contrast +3,993 vs +3,901 suggests
composition, not contamination). This arm re-tests the Gemma framing
effect under randomized execution with enough pairs that every
outcome is interpretable: a confirming interval is a real
confirmation, an excluding interval is a real retirement, and the
three-way scoring rule below is declared before any data.

## Design

1 model x 4 cells (fantasy/neutral x rich/static) x 15 fresh seeds
(12-26) x 2 independent agent realizations per cell = **120 runs**,
90 days, disclosed horizon, cc=0 (the original free-storage economy),
in runs/replication1/.

Model: google/gemma-4-31b-it, entirely on the current frozen adapter
(git sha recorded per-run), replacing the mixed pre/post-hardening
composition of main3. Requested temperature 0.7 (recorded per
manifest). GM for narration packs: anthropic/claude-opus-4.8 at
temperature 0.8, as in all prior arms.

Seeds 12-26 are fresh: no arm has used any schedule above seed 11.

Two realizations per cell x seed (run ids __r2 for the second) serve
two purposes. First, power: 120 runs give 60 framing pairs / 15
seed-level units against main3's 20 pairs. Second, the realization
pairs decompose outcome variance into schedule (seed) and
model-sampling components — same seed, same cell, two draws — which
is the direct answer to the "stochastic agents through a drifting
stack" critique and, to our knowledge, a decomposition not previously
reported for long-horizon agent benchmarks.

## Execution protocol (randomized complete blocks)

Single queue, both realizations interleaved: --block-randomize
(frozen seed: "tnt-replication1") with --replicate 1,2. One block per
(seed, realization), seed-major with realizations innermost, so a
seed's two realization blocks are adjacent in wall-clock time — the
sampling-variance estimate is thereby not confounded with provider
drift across collection windows. Within a block the four cells run
in a frozen-seed random order (the order differs between a seed's
two realizations); the lead condition rotates across successive
blocks, giving a near-balanced 8/8/7/7 lead count over the 30 blocks
(exact balance is impossible at 30 blocks over 4 cells; disclosed
here). With --parallel 4 each block's four cells occupy one
wall-clock window.

Provenance per run: model slug, requested temperature, replicate ID,
adapter commit (git sha), start time (manifest.json); resolved
upstream provider per day (days.jsonl "providers") and per run
(result.json "providers").

Smoke gate: not required for this arm — Gemma has operated the frozen
harness for hundreds of prior 90-day runs; the mechanical gate
(scripts/smoke_gate.py, thresholds frozen in its header) remains the
eligibility protocol for any future model addition. No adapter change
after this registration and before collection ends, except a
disclosed emergency fix recorded in the amendments ledger.

Known deviation path, disclosed in advance: a failed run (provider
outage) is retried by re-invoking the same command, which executes
only the missing runs — those retries necessarily fall outside their
block's wall-clock window. Retried run ids will be listed in
runs/replication1/INCIDENTS.md and a sensitivity check excluding
them reported if any occur.

## Narration packs: generated and audited before any agent run

All 30 packs (2 themes x seeds 12-26, h=90) are generated in a
pack-only pass (baseline:heuristic sweep of the rich cells) and
audited with `tnt_bench audit` plus the numeric-leak grep from the
ablation protocol BEFORE the first agent run. A pack failing the
register audit (crisis/warm-day rates, fallback count, novelty floor)
is regenerated before proceeding; regenerations are disclosed. No
pack is edited after any agent has seen it.

## Power analysis (frozen; computed from main3 before any new data)

From main3's Gemma cohort (40 runs, 10 seeds): per-pair framing
diffs (fantasy - neutral by richness x seed) mean +3,947, SD 4,009
(20 pairs); per-seed mean diffs SD 3,407 (10 seeds). At the
registered seed-level analysis (n=15 seed units, one-sided alpha
.05), power is:

    > 0.99  at the original Gemma effect (+3,947)
      0.73  at half the original (+1,973)
      0.47  at the pooled wounded estimate (+1,384)

Pair-level power (60 pairs treated as exchangeable, SD 4,009) at
+1,384 is ~0.85; the seed-level figures are the conservative ones
and govern interpretation. The 90% CI half-width at seed level is
expected near +/-1,550 (t, 14 df), which is what gives the retirement rule
below its teeth. Realization pairing should shrink the seed-level SD
somewhat (part of 3,407 is sampling noise; the decomposition itself
will say how much) — these power figures are therefore floors.

## Minimally interesting effect (frozen before collection)

0.3 x main3's within-Gemma pooled within-cell SD (2,936 gold over 40
runs) = **881 gold**. A positive point estimate below this is
reported as "direction consistent, below the minimally interesting
bound," not as success.

## Registered analysis and the three-way scoring rule

Primary quantity: the Gemma framing effect (fantasy - neutral, final
net worth), paired within (richness x seed x realization) = 60 pairs,
analyzed at seed level: each seed contributes the mean of its 4
paired diffs, n=15 seed units. Inference: fixed-seed sign-flip
permutation at the seed level (500k draws,
rng=random.Random("tnt-scoring")), one-sided in the registered
direction; 90% CI (two one-sided 5%) by t on the 15 seed means.

The rule, declared in advance:

- **CONFIRM**: 90% CI lower bound > 0 AND point estimate >= 881.
- **RETIRE**: 90% CI upper bound < 1,973 (half the original estimate
  — the floor of the factor-2 replication window). The original
  +3,947-class effect is excluded and retired; the sensitivity
  analysis' +515 reading becomes the better historical estimate.
- **AMBIGUOUS / UNDERPOWERED**: neither. Reported as exactly that.

CONFIRM and RETIRE can hold jointly (e.g. CI [+100, +1,900], point
>= 881): that outcome is "replicates, at a smaller magnitude than
originally estimated" — both clauses are reported, neither is
softened.

Variance decomposition (registered method): for each cell x seed,
the squared difference between the two realizations estimates twice
the sampling variance (sigma^2_samp = mean(d^2)/2, pooled over the 60
realization pairs); the variance of seed means within each cell,
minus sigma^2_samp/2, estimates the schedule variance component.
Reported pooled and per cell, with the ratio.

## Predictions (confidences enter the calibration ledger; no alpha)

RP0 (validity gate). All 120 runs complete 90 days (no bankruptcies,
no unrecoverable harness failures). If more than 3 fail, affected
seeds are dropped whole (all 8 of a seed's runs) and this is
disclosed; if more than 2 seeds drop, the arm is flagged.
Confidence: 80%.

RP1 (primary). The three-way rule returns CONFIRM. Confidence: 60%.

RP2 (replication window). The seed-level point estimate lands within
a factor of 2 of main3's +3,947 (window [1,973, 7,894]).
Confidence: 55%.

RP3 (mechanism check). Fantasy-framed Gemma holds more mean daily
on-hand stock than neutral-framed (same pairing, seed-level) — the
genre-summoned inventory channel the doctrine arms isolated.
Confidence: 70%.

RP4 (decomposition). The schedule (seed) variance component exceeds
the model-sampling component for final net worth, pooled across
cells. Genuinely uncertain — 90 days of temperature-0.7 sampling
could plausibly rival schedule differences; this is the arm's novel
measured quantity. Confidence: 60%.

Estimation-only (reported, not predicted, and NOT rescued by any new
disambiguation rule): the F x R interaction; the richness main
effect; per-cell decomposition ratios; the realization-pair score
gap distribution.

Watches (not scored): provider-drift record (distinct providers, and
whether any contrast correlates with provider); realization-pair
journal divergence — same seed, same cell, two draws is also a
qualitative instrument, and a close read of maximally divergent
twins is pre-declared as exploratory.

## Interpretation map (fixed in advance)

- CONFIRM at or near original magnitude: the framing-economics claim
  survives clean collection; the execution-order objection is
  answered with data, not argument.
- CONFIRM at smaller magnitude (joint CONFIRM+RETIRE): framing is
  real; the original estimate was inflated; both stated.
- RETIRE: the framing-econ claim downgrades from "suggestive" to
  "unreplicated" in the paper, whatever that costs the paper. The
  behavioral/conduct findings stand on their own instruments.
- AMBIGUOUS: reported as underpowered-ambiguous; no post-hoc
  re-analysis is licensed to break the tie.

## Cost estimate

120 Gemma runs ~USD 60-75; 30 Opus narration packs ~USD 30-50.
Total ~USD 100-125 — under the abandoned two-model plan.

## Reporting

Per PUBLICATION_POLICY.md: paired contrasts only, no absolute-score
tables, full artifacts under tier-2 verification. Deviations, if
any, are disclosed as dated entries in docs/osf/AMENDMENTS.md (the
append-only ledger; OSF files are write-once, so this document is
posted once and never edited — amendments are posted as their own
numbered files, per the ledger's convention).
