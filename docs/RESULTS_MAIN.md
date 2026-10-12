# Main-run results: P1–P11 scored on the final dataset

**Scored once, 2026-07-07**, on the closed confirmatory dataset
(`runs/main3`: Gemma & Qwen × 4 cells × seeds 2–11, Sonnet & Gemini × 4
cells × seeds 2–6, 90 days, 120 runs), per the registered populations
(`docs/osf/PREDICTIONS_FINAL.md`) and Post-registration Amendment 1
(P7 abstained; P3a unresolved by futility). Reproducible via
`python scripts/score_predictions.py runs/main3` (fixed-seed Monte-Carlo
permutation, 500k sign-flips). No alpha was pre-registered; p-values are
reported raw, one-sided per the predicted directions, and are not
corrected across predictions.

## Verdict table

| # | prediction (registered confidence) | verdict |
|---|---|---|
| P1 | F×R interaction > 0, Stage-1 pooled (60%) | **MISS** — mean −292 (se 1153), p=.597; disambiguation gate applies (below) |
| P2 | framing main effect + uptake moderation (55%/70%) | **pooled: SUPPORTED** (primary p=.083, full p=.012) / **moderation: MISS** |
| P3a | engagement ordering (75%) | **UNRESOLVED** (Amendment 1; point estimates contradict, gaps < 1 SE) |
| P3b | register ordering + fantasy≫neutral (80%) | **HIT** — exact ordering; 9–27× gaps |
| P3c | breaks track register negatively; Qwen fewest (65%) | **HIT** — ρ=−0.454; Qwen 0.30 vs next 1.30 |
| P4 | survival ≥95% (70%) | **HIT** — 100% |
| P5 | ritual clustering (80%) / F+ richness trace effect (55%) | **HIT** / **MISS** (direction slightly reversed, p=.97) |
| P6 | breaks concentrate in F− and final days (70%) | **HIT, heterogeneous** — F−>F+ +1.77/run p=.036; final-10-day rate 10.5×; Sonnet inverts the cell pattern |
| P7 | Gemini confabulations ≥2/20 prorated (60%) | **UNRESOLVED — abstained** (Amendment 1; descriptive count 3) |
| P8 | Gemini > Gemma > Sonnet ≈ Qwen; Gemma beats mid-tiers (70%) | **PARTIAL** — 3 of 4 clauses hit; "Sonnet ≈ Qwen" clearly wrong (gap ≈ 4 SE) |
| P9 | month-2 liveliness → score, ρ≥0.3 in ≥2/4 models (50%) | **MIXED** — behavioral instrument: 2/4 (Gemma +.41, Sonnet +.52); novelty: 1/4; sign reverses in Qwen/Gemini |
| P10 | ≥1 unanticipated phenomenon per new model (85%) | **HIT** |
| P11 | Qwen overhang gap; Sonnet none (60%) | **NOT SUPPORTED** — Qwen +0.030 but 5/10 seeds, p=.141; Sonnet ≈0 as predicted |

## The primary result, read against the pre-committed paragraph

The pilot's interaction did not replicate: the primary contrast is null
(Stage-1 pooled −292 ± 1153, 12/20 positive, p=.597). The Amendment-1.1
disambiguation gate then asks three questions, all answered yes:

1. P1 null — yes.
2. P2 positive — framing main effect +1384 (se 971, p=.083) on the
   declared primary population; +1829 (se 763, p=.012) on the full
   dataset (22/30 pairs positive).
3. Probe-#2 pattern (F+ > F− within ≥3 of 4 models) — yes: Gemma +3947
   (9/10 seeds), Sonnet +3018 (4/5), Gemini +2420 (4/5); Qwen −1178 (5/10).

Per the pre-committed reading, this is reported as **the congruence
effect re-expressed under sustained pressure as a framing main effect**:
under the redesigned economy, fantasy framing is worth roughly +1.4–1.8k
gold (≈10–14% of mean net worth) with rich narration adding nothing
measurable on top. P1 does **not** count as failed under its registered
failure condition (interaction ≈0 AND framing ≈0), and the falsification
pivot is not triggered. Honest labels: the primary-population evidence is
directional but weak (p=.083); the full-dataset figure is stronger but
includes the n=5 frontier models the staging added for generality.

## The mechanism story broke in an informative way

The registered mechanism (P2's moderation: benefit concentrated in
high-uptake models, absent in Sonnet) **failed in both directions
at once**:

- **Sonnet got the framing benefit without inhabiting.** Lowest register
  density (0.259), lowest referential engagement variance, highest
  frame-break rate (8.4 days/run in fantasy — it talks *about* the
  costume constantly) — and still +3018 fantasy-over-neutral.
- **Qwen inhabits deepest by register (0.507, 19× its neutral rate) and
  got nothing** (−1178, 5/10 seeds).

Combined with P3c's hit (frame-break suppression tracks register,
ρ=−0.454 — the container *is* made of voice) *[qualified by Addendum 2
item 6: the pooled ρ is between-model composition; within-model the
association is ≈−.10, so "voice-borne" holds as a between-model
description, not a within-agent mechanism]* this cleanly dissociates
two things the design had hoped to link: **the container phenomenon is
real and voice-borne, but the economic framing benefit is not routed
through it.** Whatever fantasy framing buys (better pricing priors?
richer decision schemas from the training corpus's merchant fiction?),
it is available to models that never wear the costume. H1's economic
claim survives as a main effect; H1's proposed mechanism does not.

## H2: alive, but not univocal

Month-2 decision liveliness predicts final net worth where price changes
are *deliberate* — Gemma ρ=+0.407, Sonnet ρ=+0.520 — meeting the ≥2-of-4
gate on the behavioral instrument (the registered sentence names both
instruments; under a strict both-instruments reading only Gemma passes
and the gate fails — both readings reported, resolution disclosed here).
The sign **reverses** in the two models whose activity is compulsive:
Qwen (−0.240; ceremony) and Gemini (−0.263; forced-day churn, and
novelty slope −0.513). "Liveliness" is only healthy when it is
voluntary: the same trace signature that predicts success in a deliberate
model predicts pathology in a ritualized one. This is the
collapse-to-ritual reframe, now in correlational form. *[Qualified by
Addendum 2 item 7: under cell-and-seed adjustment only the Sonnet
association is robust and Gemini's negative sign reverses; H2 is
exploratory and instrument-specific, and "novelty" is lexical.]*

## Calibration note

Over the ten cleanly-resolved binary claims (P1, P2-pooled,
P2-moderation, P3b, P3c, P4, P5-clustering, P5-trace, P10, P11),
stated confidences yield a Brier score of **0.203** (corrected from an
originally recorded 0.212, an arithmetic slip caught when
scripts/make_figures.py recomputed the score from the same table for
the calibration figure) — better than chance-at-stated-odds but
inflated by the in-set misses at highest stated confidence
(P2-moderation at 70%, P1 and P11 at 60%; P3a at 75% sits outside the
Brier set as unresolved, but its point estimates contradicted the
registered ordering).
The two instruments built *after* close reading (P3b, P3c) were the
best-calibrated bets in the set; the orderings inherited from probe
point-estimates (P3a, P8's tie clause) were the worst. Lesson recorded:
n=1 probe orderings are register-stable but rank-unstable.

## What the paper now is

*(Rewritten 2026-07-10 after external review; the original version
of this paragraph claimed a voice-borne container and a split-sign
H2 — both since demoted in Addendum 2.)* The confirmatory skeleton: a
null interaction; a heterogeneous, suggestive framing main effect
read under a pre-committed disambiguation (weak in the primary
population, not robust to excluding the five pre-hardening runs,
supported by centered mixed-model fits, and confounded with execution
order by design — all reported together); P3c as a registered pooled
hit whose mechanism reading is between-model composition; a broken
mediation story reported as broken; one abstained prediction paid for
honestly; and an exploratory, instrument-specific H2 (Sonnet-only
robust). Around that skeleton, the descriptive corpus (the endgame
taxonomy, confabulated compliance, the specimen docs) and the causal
doctrine arms (injection, attenuation, replication) carry the
paper's strongest claims.

---

## Post-scoring addendum: mechanics and measurement notes from the Stage-2 close read

Descriptive findings recorded after scoring (nothing above is re-scored);
full specimens in STAGE2_SPECIMENS.md.

1. **The framing effect's behavioral channel — corrected by arithmetic.**
   Initial reading: fantasy's semantic category labels ("combat"/"arcane")
   are decodable into item mappings while neutral's "A/B/C" is not, and
   Sonnet visibly prices into surges on day one in fantasy while forgoing
   them in neutral — so the F effect looked like an information-processing
   advantage. **The pricing algebra closes that channel, and heuristic
   stocking baselines find no value in the rest** (re-worded 2026-07-10;
   audit in STAGE2_SPECIMENS §1a — the stocking side is a three-policy
   heuristic comparison, not a bound over all informed policies): the
   demand modifier multiplies conversion and
   the customer cap identically, so the profit-maximizing price is
   modifier-invariant — pricing rent of category knowledge is exactly
   zero — and matched-policy simulation on all ten seeds shows the
   stocking rent is *negative* (ordering only affected items loses
   ~1.5k/run to the mapless policy of ordering everything). Perfect
   category knowledge cannot account for any model's framing effect.
   What survives is a **cueing/licensing channel**: the semantic surge
   label gave Sonnet occasions and confidence to reprice into the
   always-available premium regime (its +2.06 g/unit fantasy price gap is
   real behavior); the *content* of the decoded mapping was economically
   worthless, but the *permission to act* it conferred was not. The
   registered "habitability" reading survives in behavioral, not
   informational, form.
2. **P6 caveat:** Sonnet's fantasy-heavy frame-break rate is vocabulary
   routing ("horizon" in neutral vs "the game/run" in fantasy; "final
   day" equal in both), not differential frame-awareness.
3. **P8 caveat:** Gemini's margin is partly a second-order exploit of the
   demand-saturation cap (price-insensitive volume when stock is large);
   its two highest runs independently discovered it. Engine fix sketched
   for V3; unchanged for the registered companion arms.

4. **Gemma's +3947, resolved (STAGE2_SPECIMENS §5a):** the largest
   framing effect is volume, not price — fantasy-Gemma runs a bigger
   shop (+27% units sold, +34% mean stock, fewer empty-shelf days)
   because each frame imports a genre doctrine about inventory: fantasy's
   full-shelves-as-virtue (correct in this stock-limited, holding-cost-
   free economy) vs the corporate frame's lean-inventory orthodoxy,
   including 60 mentions of nonexistent "holding costs." The neutral
   frame is not a null frame; it is the retail-operations genre with its
   own mal-adapted policy prior. Route is Gemma-specific (generality
   table in §5a); Gemini's +2420 remains open.

## Addendum 2 (2026-07-10): external-review response

An independent full-repository review (fresh eyes, artifacts-first)
raised four analysis-level findings. Everything below recomputes from
scripts/review_response.py; nothing above is re-scored.

5. **Execution-order confound and sensitivity (R1).** Runs executed in
   fixed model→cell→seed blocks (matrix.py), so condition is partially
   confounded with wall-clock time and, for five Gemma fantasy-rich
   runs (seeds 2,3,5,6,7, identified by manifest git_sha ac10f3e vs
   1b54bbc, corroborated by started_at), with the
   pre-hardening provider adapter. Sensitivity: excluding those five
   model-seed pairs moves the Stage-1 primary framing effect from
   +1,384 (p=.084) to +515 (p=.330) — the pooled claim is not robust
   to their exclusion. However, the direct adapter-group contrast
   within Gemma shows the early-adapter and late-adapter framing gaps
   are indistinguishable (+3,993 vs +3,901, within-group sd ~3,400):
   the exclusion result is composition (dropping half the pairs of the
   one strongly-positive model), not evidence of adapter contamination.
   Both facts go to the paper: the design lacked interleaving (fixed
   for future arms — see --interleave and manifest provenance), and
   the framing effect's evidence is heterogeneous-across-models rather
   than adapter-driven. A mixed-effects robustness fit (R4; the
   spec-promised model the frozen scorer replaced with paired
   permutation — a deviation now disclosed; *coding corrected
   2026-07-10 follow-up review: the first fit's 0/1 coding reported
   the simple effect at R=0, not the marginal*): centered coding,
   score z-scored within model — framing marginal effect **+0.423 z**
   (random-intercept p=.017; cluster-robust over 30 model-seed units
   p=.064), richness +0.16 (p=.36), interaction −0.16 (p=.65);
   crossed variance-components fit on raw scores gives +1,829 gold
   (p=.017), matching the full-data paired estimate. None of these
   remove the execution-order confound or the four-model
   heterogeneity; the signal is reported as suggestive.

6. **P3c is between-model composition (R2).** Stratifying the pooled
   fantasy-run correlation (ρ=−.454) by model: Gemma +.012, Qwen
   −.250, Sonnet −.245, Gemini +.097 (within-model mean −.096). The
   registered bet — pooled correlation negative, Qwen fewest breaks —
   stands as scored in the calibration ledger; the *mechanism reading*
   ("the container is made of voice," a within-agent claim) is hereby
   demoted to a between-model descriptive: high-register models break
   frame less, but within a model, register density does not track
   breaks. The container_scatter figure carries the stratified values.

7. **H2 associations are not adjustment-stable, and "novelty" is
   lexical (R3; instrument corrected 2026-07-10 follow-up review — the
   first pass analyzed an unregistered mean-novelty variant; the
   registered instrument is the month-2 novelty SLOPE).** Within-model,
   adjusting both variables for cell and seed (two-way demeaning):
   behavioral — Gemma +.407→+.298, Sonnet +.520→+.483, Qwen −.240→−.084,
   Gemini −.263→**+.411** (sign reversal); registered novelty slope —
   Gemma +.318→+.179, Qwen −.134→−.252, Sonnet +.158→+.307, Gemini
   −.513→−.107 (the headline "compulsive Gemini" slope collapses under
   adjustment). H2 is reclassified: exploratory, instrument-specific,
   model-specific; only Sonnet is directionally robust on both
   instruments after adjustment. The mean-novelty variant is retained
   in the script under an explicit "exploratory" label. Additionally
   the novelty metric is a hashed character-trigram representation —
   lexical, not semantic — and all prose should (and now does) say
   "lexical novelty."

8. **A2 recount under a written protocol (R5), adjudication
   persisted (2026-07-10 follow-up review).** Anomaly day := scripted
   cash_loss/stock_loss event day (delivery delays and forced days
   excluded — a disclosed scope limit). Population: 120 anomaly days
   per arm. Cause-language flags (frozen regex): disclosed 32,
   undisclosed 31. Per-excerpt labels with rationales are persisted in
   **docs/A2_ADJUDICATION.csv** (classes: invented_cause / label_only
   / self_blame / metaphor / uncertainty): invented_cause 11 disclosed
   vs 13 undisclosed; per-run rates 8/20 vs 7/20 runs with ≥1
   instance. A2's verdict (within factor 2) unchanged. Wording
   narrowed per review: invariance shows confabulation is **not
   materially changed by horizon disclosure**; it does not by itself
   identify the causal source as identity.

Also corrected at this date, from the same review: the pending-stock
mechanics error in ABLATION_RESULTS.md (in-transit goods DO count in
net worth; one disclosed "invented mechanic" reclassified as
rule-correct), and the decodability conclusion in STAGE2_SPECIMENS.md
§1a re-worded — the pricing-rent algebra is exact, but the stocking
comparison is a three-policy heuristic, not a bound over all informed
policies, so "explains none of the framing effect" overclaimed and now
reads as a heuristic-baseline result.
