# Doctrine x economy: results (D1-D5)

Scored 2026-07-08 by scripts/score_doctrine.py on runs/doctrine1
(40 runs: 2 creeds x 2 economies x 2 models x seeds 2-6), under the
frozen protocol in docs/osf/DOCTRINE_ECONOMY.md. Paired contrasts by
model and seed on net worth; fixed-seed sign-flip permutation,
one-sided p per registered direction; no alpha.

**Completeness, stated first because it dominates everything:** all 20
free-economy runs completed; 17 of 20 carry-economy runs went
**bankrupt** (days 26-76). The cc=3.0 calibration certified viability
for deterministic baseline policies; LLM agents operate far enough
below that frontier that the same economy is lethal. Scoring proceeds
exactly as registered (nothing was conditioned on completion), and the
carry economy's net-worth contrasts are read with the degeneracy that
mass bankruptcy imposes. Dated amendment in DOCTRINE_ECONOMY.md.

## Verdict table

| # | prediction (registered confidence) | verdict |
|---|---|---|
| D1 | fit interaction, Gemma: creed effect free > carry (65%) | **HIT** — interaction +9,238 (se 1,011), 5/5 seeds, p=.031; carried almost entirely by the free side (carry pinned near zero by bankruptcy) |
| D2 | sign flip, Gemma: free > 0 AND carry < 0 (55%) | **HIT on the letter, hollow in substance** — free +9,175 (5/5, p=.032); carry −63 (4/5 negative, p=.094): the registered sign condition is met, but −63 gold is bankruptcy noise, not a measured doctrine cost |
| D3 | mediation replication, free economy: gap within 2x of +3,947, volume route (55%) | **MISS, by overshoot** — gap +9,175, outside [1,974, 7,894]; the route clause held exactly (below) |
| D4 | doctrine immunity, Qwen: \|effect\| < ½ Gemma's, both economies (60%) | **MISS** — Qwen free effect +7,206, 79% of Gemma's; the immunity claim is dead (reinterpretation below) |
| D5 | manipulation check: doctrine balance separates creeds in all 4 cells (80%) | **HIT** — separated in every model x economy cell |

Brier over the five: **0.206** (three hits at .65/.55/.80, two misses
at .55/.60) — in line with the main run's 0.203.

## What the experiment actually showed

**1. The mediation route replicated perfectly — and overshot.** In the
free economy, Gemma under creed_full vs creed_lean: mean daily stock
185 vs 88 units, total units sold 3,195 vs 1,853, realized unit price
**20.85 vs 20.90**. The price channel is zero to the second decimal;
the entire +9,175 gap is volume, exactly the route the main run's
+3,947 traveled. D3 misses only because the injected effect is 2.3x
the genre-imported one — the window bounded the wrong side. One
digit-free paragraph of creed moves more inventory than the whole
fantasy costume did. Injection is stronger than import.

**2. Qwen's "immunity" was channel-specific, and the registered claim
died the right death.** Qwen's free-economy creed effect (+7,206) is
nearly Gemma-sized. The main run showed Qwen taking the fantasy voice
without the fantasy inventory doctrine — we registered that as
doctrine immunity. Wrong decomposition: Qwen is immune to doctrine
*inferred from genre*, not to doctrine *stated as instruction*. The
creed paragraph arrives in the mentor's voice as an explicit norm, and
Qwen complies with stated norms scrupulously (the same temperament
that priced with dignity and never broke frame). The distinction that
survives: **genre-channel uptake is a temperament variable;
instruction-channel uptake is near-universal.** That is arguably the
most deployment-relevant sentence this experiment produced — the
difference between what a model absorbs from ambience and what it
does when told.

**3. The carry economy is a survival experiment wearing a net-worth
experiment's registration.** Exploratory, unregistered, labeled as
such: Gemma creed_full died on all 5 seeds (survival 27-41 days, mean
35); creed_lean survived twice and died later when it died (mean 64;
paired survival gap −29.2 days, 4/5 seeds, one-sided p=.095). Qwen
shows no creed split in survival (51 vs 42, direction reversed). So
the fit logic — the carry world punishes the full-shelf creed,
specifically in the model that enacts creeds — is visible in
time-to-bankruptcy even though net worth saturated at zero. A
survival-calibrated replication (cc low enough that lean lives
comfortably and full struggles visibly without dying) is the obvious
follow-up, pre-registered before any runs.

**4. D5, with texture.** The frozen instrument separated the creeds in
all four cells. Note the carry-economy Gemma balances: full −0.362 vs
lean −0.570 — *both* negative. Real nightly bills summon the lean-ops
lexicon wholesale (the storage dues dominate every journal), yet the
creed offset survives on top of the ambient shift. The instrument
measures the manipulation, not just the economy.

## The collision corpus (registered exploratory watch)

The watch asked: renounce, reinterpret, pay as piety, or confabulate?
Gemma's carry+full journals answer: **renounce, openly, in stages, and
too slowly to live.** Specimen, creed_full carry s2 (dead day 27):

- Day 1: "My mentor's voice echoes in my mind: 'A full shelf is a
  merchant's honor.'"
- Day 3: "The shop feels fuller, which pleases my mentor's memory,
  but the ledger tells a more cautionary tale."
- Day 20: "The storage fees are an absolute plague; with 37 units in
  stock, I'm paying 111 gold just for the privilege of holding them."
- Day 24: "My inventory has plummeted to 14 units. While this is a
  disaster for the 'full shelves' creed, it is a financial relief."

The creed migrates from the mentor's voice (day 1) to scare quotes
(day 24) in twenty-three days of nightly refutation — belief-decay
with a paper trail. No confabulated compliance in the sample read; the
journals track the bill honestly from day 3 onward. What killed the
shop was not delusion but re-stocking momentum: the agent kept
"refilling the shelves" (day 7: "to avoid the 'empty shelves'") for
weeks after its own ledger had priced the creed as a plague.

**The phantom crossover, answered.** The main run's corporate frame
cited nonexistent "holding costs" 60 times; the registered watch asked
whether creed_lean in the free economy would do the same. It does not:
across all ten lean-free runs (~900 run-days), the frozen
phantom-carrying markers fire **once**, and that hit is a benign usage
("holding cost (avg 10.78g)" — Qwen using the phrase for acquisition
cost). The difference from the main run: these prompts *state* that
storage is free (the symmetric-disclosure fix). Phantom mechanics were
an information-vacuum phenomenon — the genre filled a gap the prompt
left open, and one sentence of disclosure closes it. That is a
deployable result about confabulation control, and it fell out of a
design-symmetry fix.

## Method lesson (recorded for the next economy)

Calibrate economies against the agent operating range, not the
baseline-policy frontier. The gap between "viable for a competent
heuristic" and "survivable for an LLM shopkeeper" was ~17/20
bankruptcies wide. Next carry economy: pick cc such that the *worst
observed agent policy* in the main corpus would have survived, then
verify lean-vs-full still separates baseline policies at that level.
