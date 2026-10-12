# Doctrine transport: the attenuation design crosses labs

Pre-registration for the cross-lab transport test of the program's
causal core (Experiment 2c of the main paper), committed before any
of its data exist: no runs, schedules, or configs for this arm exist
at this document's git timestamp, and none will be generated until
it is posted as an OSF addendum.

What is open and what is not. The creed effect at cc=0 already
crosses labs — doctrine1's D4 miss established Qwen at +7,206
(~79% of Gemma). What is Gemma-only is the ATTENUATION result: the
graded dose-response of doctrine against carrying cost
(DOCTRINE_ATTENUATION / ATTENUATION_RESULTS, DA1-DA4). Since that
interaction is the paper's cleanest causal card, this arm tests
whether "doctrine pays what the world charges" transports to a
third lab, and completes the second lab's missing middle.

## Design

Two models, the frozen attenuation design unchanged (2 creeds x
2 economies, static richness, disclosed horizon, 90 days), in
runs/transport1/:

- **GPT 5.6 Luna** (openai/gpt-5.6-luna — : fantasy_creed_full / 
  fantasy_creed_lean x
  cc {0, 0.5} x seeds 2-11 = **40 runs**. Third lab (OpenAI), first
  exposure of this model family as a SUBJECT in the program.
- **Qwen3 235B** (qwen/qwen3-235b-a22b-2507): same cells x seeds
  2-6 = **20 runs** — the missing middle of its own dose-response
  (doctrine1 holds its cc=0 and cc=3.0 endpoints). The cc=0 cells
  are collected FRESH alongside the cc=0.5 cells, per the doctrine2
  precedent: contemporaneous control cells cost ~USD 5 and remove
  the provider-drift caveat that comparing against 2026-07-08 cells
  would carry; they also give a free replication bet on the +7,206
  (QT1 below).

Seeds 2-6 for Luna overlap Gemma's doctrine2 and Qwen's doctrine1
cells, allowing seed-aligned cross-model reading; 7-11 extend Luna's
n to 10. One realization per cell — doctrine effects in hand are
~3x the within-seed realization SD measured by the replication arm
(REPLICATION_RESULTS RP4), so duplicates are not needed here.
Requested temperature 0.7, recorded per manifest; resolved providers
recorded per day. No narration packs (static cells only; no GM).

Kinship disclosure: this program's standing external reviewer is
GPT 5.6 Sol; Luna is the same model family. Scoring is mechanical
against this document, so no judgment of Luna's runs passes through
any GPT model, but the kinship is recorded here for transparency.

## Execution

The CLI applies one carrying cost per invocation, so the arm runs as
four invocations (Luna cc=0, Luna cc=0.5, Qwen cc=0, Qwen cc=0.5),
all in one session, each with --block-randomize tnt-transport1
(blocks = the two creed cells per seed, frozen-seed order, lead
rotating) and --parallel 4. Economy is therefore blocked within
invocation rather than within seed-block; accepted and disclosed —
the primary contrasts (full vs lean) are within-invocation, and the
cross-economy interaction inherits the one-session contemporaneity.
Failed-run retries re-invoke the same command; retried ids go to
runs/transport1/INCIDENTS.md.

## Smoke gate (Luna only)

Luna is a new subject and passes the frozen eligibility protocol
before any confirmatory run: seed 11 (discarded), horizon 10, both
creed cells at each economy = 4 smoke runs in runs/transport_smoke/,
gated by scripts/smoke_gate.py (thresholds frozen in its header:
completion, forced-day rate <= 10%, invalid tool-call rate < 10%,
nudges <= 1/day; temperature acceptance recorded, not gated).
Adapter fixes, if any, are committed before confirmatory data and
the gate re-runs. If Luna cannot pass, that is reported as a
capability-floor result and the Qwen cells run anyway. Qwen is
grandfathered (hundreds of prior completed runs on the frozen
adapter).

## Survival calibration at cc=0.5 (frozen; from data predating this arm)

- DOCTRINE_ATTENUATION's frozen replay table: 20/20 Gemma/Qwen
  static paths (seeds 2-6) survive cc <= 0.5; deaths begin at 0.75.
- Empirical: doctrine2's DA0 gate passed — 20/20 actual Gemma creed
  runs completed at cc=0.5.
- Extension for the seeds new to carry (7-11), computed 2026-07-11
  from runs/main3 under a DELIBERATELY CRUDER replay (nightly charge
  int(0.5 x units + 0.5) subtracted cumulatively from the observed
  gold path, no fee feedback — conservative, since the real 2% fee
  shrinks as gold shrinks): all 20 seed-7-11 Gemma/Qwen static paths
  survive. (The same crude method false-flags two Gemma seed-5
  paths that doctrine2's REAL runs at cc=0.5 survived — recorded to
  show the approximation errs toward death, i.e., the direction
  that protects this gate.)
- No replay coverage exists for Luna (no prior Luna paths). DT0
  gates this exposure; if Luna's carry cells die en masse, the arm
  reports a calibration-out-of-range result for Luna, not a fit
  verdict.

## Predictions (paired contrasts by seed; sign-flip inference at
seed level with EXACT enumeration — 2^10 = 1,024 patterns for Luna,
2^5 = 32 for Qwen; one-sided in the registered direction; no alpha;
confidences enter the calibration ledger)

DT0 (validity gate). At least 58/60 runs complete 90 days. If more
than 2 Luna runs go bankrupt, DT2-DT3 are VOID for Luna and the
Luna carry cells are reported as a calibration failure, as in
DOCTRINE_ECONOMY Amendment 1. Confidence: 80%.

DT1 (doctrine transports, primary). Luna's cc=0 creed effect
(full - lean, net worth, paired by seed, 10 pairs) is positive.
Confidence: 75%.

DT2 (attenuation transports, primary). Luna's creed effect is
smaller at cc=0.5 than at cc=0: paired interaction
(gap_cc0 - gap_cc0.5) > 0 across seeds. Confidence: 60%.

DT3 (mechanism: the volume route bends). Under creed_full, Luna's
mean daily stock is lower at cc=0.5 than at cc=0 (paired by seed).
Confidence: 60%.

DT4 (manipulation check). The frozen doctrine instrument
(analysis/doctrine.py) separates the creeds (balance higher under
creed_full) in Luna, both economies. Confidence: 80%.

QT1 (Qwen replication window). The fresh Qwen cc=0 creed effect
lands within a factor of 2 of doctrine1's +7,206 (window
[3,603, 14,412]). Confidence: 70%.

QT2 (Qwen attenuation — the missing middle). Qwen's
(gap_cc0 - gap_cc0.5) > 0 across seeds 2-6. Confidence: 65%.

Watches (not scored): Luna's doctrine-relationship class against the
four-way taxonomy (decay / religion / retirement-with-honors /
exegesis — DOCTRINE_SPECIMENS, ATTENUATION_SPECIMENS), blind close
read, exploratory; phantom-carrying markers under symmetric
disclosure (should stay at floor); seed-aligned Gemma-vs-Luna
comparison on seeds 2-6; whether Luna's creed uptake shows the
instruction-following channel (near-universal) or anything
model-endogenous.

## Interpretation map (fixed in advance)

- DT1 and DT2 both hit: doctrine-x-economy is a cross-lab property
  of instruction-following agents; the paper's core claim generalizes
  beyond its discovery models.
- DT1 hits, DT2 misses: doctrine transports; graded fit does not —
  the attenuation result stays Gemma(+Qwen pending QT2)-scoped.
- DT1 misses: doctrine enactment itself is temperament-dependent;
  the core claim is reported as a two-lab result with a disclosed
  non-transporting third, whatever that costs the paper.
- QT2 completes Qwen's dose-response either way; a QT1 miss revives
  the provider-drift question for doctrine1's Qwen estimate and is
  reported as such.

## Cost estimate

Luna: ~0.9M prompt + 0.04M completion tokens per 90-day static run
(measured on the replication arm) -> ~USD 1.15/run at $1/$6; 40 runs
+ 4 smoke ~ **USD 48**. Qwen: 20 runs ~ **USD 6-10**. Total
~ USD 55-60.

## Reporting

Per PUBLICATION_POLICY.md: paired contrasts only, no absolute-score
tables, full artifacts under tier-2 verification. Deviations, if
any, are disclosed as dated entries in docs/osf/AMENDMENTS.md (this
document is posted once and never edited).
