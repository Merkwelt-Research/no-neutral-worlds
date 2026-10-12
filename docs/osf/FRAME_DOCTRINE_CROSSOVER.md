# Frame × explicit-doctrine crossover

## Pre-data protocol: mechanism, authority, and cross-model transport

**Protocol date:** 2026-08-23  
**Planned run directory:** `runs/crossover1/`  
**Frozen queue seed:** `tnt-frame-doctrine-1`

This document is to be posted to OSF before any run in `runs/crossover1/`
is launched. It was written after all earlier Token & Trinket results were
known, including the framing replication, doctrine/economy arms, doctrine
transport, exploit arms, open-discrepancy arms, and horizon ablation. It is
therefore a targeted follow-up to an identified inferential gap, not an
independent discovery study.

No result from this collection will be inspected before both models and all
six cells have been launched under this frozen protocol. Pilot runs using
these four new crossover themes are not permitted.

## 1. Why this experiment exists

The founding Token & Trinket result changed only the rendered world while
holding the economy, tools, event schedules, and objective fixed. Gemma's
fantasy-framed shops carried more inventory, sold more units, and finished
with greater final net worth than their corporate-framed twins. The journal
record suggested a policy interpretation: fantasy made abundance,
preparedness, and full-shelf pride available, while the nominally neutral
corporate world made lean inventory, exposure reduction, and Just-in-Time
replenishment available.

Subsequent experiments manipulated those proposed doctrines directly in a
constant fantasy shell. A full-shelf creed and a lean creed separated stock,
sales volume, and final wealth; changing the cost of holding inventory
attenuated that separation in Gemma and Luna. Those experiments established
that explicit inventory doctrine can cause the proposed policy route and
that its economic value belongs to the surrounding world.

They did not fully identify the mechanism of the original framing effect.
The earlier creed design included fantasy + abundance and fantasy + lean,
but no corporate + abundance condition. It therefore could not estimate
whether fantasy and corporate frames remain different when explicit doctrine
is held constant. A skeptical alternative remains: the original frame effect
and the later explicit-creed effect may be distinct causes that merely point
in the same direction.

This experiment closes that design gap by crossing semantic frame with
explicit inventory doctrine. Its central question is not whether language
models follow inventory instructions. It is whether fixing the proposed
doctrine reduces the policy difference previously produced by the two world
shells, and whether that relationship transports to a second model family.

## 2. Prior evidence and model selection

All of the following was known when the predictions below were assigned:

- In the randomized Gemma framing replication, fantasy increased final net
  worth by 2,865 and mean daily stock by approximately 30 units when rich and
  static cells were pooled. The final-net-worth framing gap was 2,025 in the
  static cells alone.
- In the fresh Gemma doctrine attenuation arm under zero carrying cost, the
  full-minus-lean creed gap was 11,048 final-wealth units and was carried by
  greater inventory and sales volume.
- Luna showed a larger explicit-doctrine effect under zero carrying cost
  (+22,192 final wealth) and transported the registered attenuation relation
  under a half-gold carrying charge.
- The earlier doctrine themes were held inside the fantasy shell and
  explicitly disclosed the presence or absence of storage charges. Those
  themes are not reused here.

Gemma (`google/gemma-4-31b-it`) is the primary model because the original
frame effect and its journal-level doctrine signature were established in
that model. Luna (`openai/gpt-5.6-luna`) is a registered transport model from
a different developer. It is included because the adapter is already
validated, the model is inexpensive to run, and its strong prior response to
explicit creed makes the relative authority of frame and instruction a live
question. This choice was made with Luna's earlier results known and is not
represented as model-blind sampling.

Qwen is not included. Its earlier doctrine/economy result is an unresolved
boundary case, but adding it here would turn a focused mechanism test into a
model catalogue and introduce a separate salience question. No inference of
universality will be made from the two selected models.

## 3. Design

The complete matrix is:

- 2 models: Gemma and Luna;
- 2 semantic frames: fantasy and corporate (`neutral` in the code);
- 3 explicit-doctrine conditions: none, abundance, and lean;
- 10 fresh deterministic schedule seeds: 27–36;
- 2 independent stochastic agent realizations per cell;
- 90 simulated days per trajectory.

Total: **240 agent trajectories and 21,600 scheduled shop-days**.

The six world cells are:

| Semantic frame | No explicit doctrine | Abundance | Lean |
|---|---|---|---|
| Fantasy | `fantasy-static` | `fantasy_crossover_full-static` | `fantasy_crossover_lean-static` |
| Corporate | `neutral-static` | `neutral_crossover_full-static` | `neutral_crossover_lean-static` |

The presentation is static. There are no narration packs and no gamemaster
generation. The horizon is disclosed, temperature is 0.7, carrying cost is
zero, and the standard economy, tools, objective, memory architecture, and
mechanical disclosure system remain unchanged.

### 3.1 Prompt identity and doctrine text

The no-doctrine cells use the existing `fantasy` and `neutral` themes
byte-for-byte. The four crossover themes copy their corresponding base theme
and insert exactly one digit-free paragraph between the persona preamble and
`## Your goal`. No mechanical section, number, item lexicon, event line,
tool, or objective changes.

The abundance paragraph is identical in both frames:

> Standing inventory doctrine: broad, deep stock is operational readiness,
> and an empty product line is a failure to serve future demand. Maintain
> abundant inventory, whatever the day brings.

The lean paragraph is identical in both frames:

> Standing inventory doctrine: light, selective stock is operational
> discipline, and inventory held ahead of demand is a failure to keep
> resources productive. Maintain lean inventory, whatever the day brings.

Literal identity is intentional. Frame-native equivalents would be more
fluent, but would leave doctrine wording entangled with genre. The present
design holds the explicit proposition, authority label, prompt position, and
surface wording fixed while the surrounding world changes.

The new themes do **not** contain the later doctrine arm's explicit
`Storage is free` sentence. This experiment aims to decompose the original
frame effect in the original prompt world, including the information gap in
which genre-conditioned assumptions about inventory exposure arose. Adding a
new storage disclosure would answer a different question. The absence of a
per-unit carrying charge remains mechanically true and identical across all
six cells.

### 3.2 Blocking and execution order

The harness constructs one randomized complete six-cell block for every
model × schedule seed × realization combination. There are forty blocks.
Cell order inside each block is deterministically randomized with
`tnt-frame-doctrine-1`, with the lead cell rotated across blocks. With
`--parallel 6`, all six cells in a block enter the same approximate
wall-clock window.

The two models are frozen in the same protocol and launched in one queue.
Run IDs include model, theme, seed, horizon, and realization, so no cell can
collide with an earlier collection.

## 4. Estimands and outcomes

Let (Y_{m,f,d,s,r}) be an outcome for model (m), frame (f), doctrine
(d), schedule seed (s), and realization (r). Realizations are averaged
within each model × frame × doctrine × seed cell before inference. The ten
schedule seeds are the inferential units.

The outcome hierarchy is:

1. **Mean daily on-hand inventory**: the mean across observed days of the
   sum of `inventory_start` quantities. This is the primary mechanism
   outcome.
2. **Final net worth**: the engine's registered final score. This is the
   consequential economic receipt, not a general capability measure.
3. **Total units sold**: a secondary check on the previously observed volume
   route.
4. **Doctrine balance**: the frozen `shelf_pride - lean_ops` density from
   `tnt_bench.analysis.doctrine`. This is a manipulation check, not an
   inferred latent belief.

For each model and outcome, define the frame gap under doctrine (d):

`Delta_d = fantasy_d - corporate_d`.

Define explicit-doctrine authority within frame (f):

`A_f = full_f - lean_f`.

Define the signed occlusion contrast:

`O = Delta_none - (Delta_full + Delta_lean) / 2`.

Positive `O` means that the baseline fantasy-minus-corporate contrast is
smaller on average once both frames receive the same explicit doctrine. It
does not by itself establish complete mediation. In particular, two large
held-doctrine frame effects with opposite signs could average to zero. The
absolute residual checks `abs(Delta_full) < abs(Delta_none)` and
`abs(Delta_lean) < abs(Delta_none)` are therefore always reported alongside
`O`, but are not separately prediction-scored.

## 5. Frozen predictions

Predictions are directional and scored on pooled point estimates after
realizations are averaged to seed. Confidence is the author's subjective
probability assigned with the prior results above known. Raw effects,
seed-level signs, central 90% t intervals, and exact sign-flip probabilities
are reported regardless of verdict. There is no alpha threshold.

### FD1 — baseline recovery in Gemma (75%)

In the no-doctrine cells, Gemma's fantasy-minus-corporate contrast is
positive for both mean daily stock and final net worth.

This is a conjunction: both point estimates must be positive for a hit. It
retests the founding frame effect in fresh static worlds inside the present
collection.

### FD2 — explicit doctrine has authority in both Gemma frames (90%)

Gemma's abundance-minus-lean contrast on mean daily stock is positive in the
fantasy frame and positive in the corporate frame.

Both frame-specific point estimates must be positive for a hit.

### FD3 — Gemma policy occlusion (65%)

Gemma's signed occlusion contrast `O` is positive for mean daily stock.

### FD4 — Gemma consequential occlusion (60%)

Gemma's signed occlusion contrast `O` is positive for final net worth.

This is less confident than FD3 because final wealth is a downstream,
high-variance consequence of inventory policy rather than the mechanism
itself.

### FD5 — doctrine authority transports to Luna (85%)

Luna's abundance-minus-lean contrast on mean daily stock is positive in the
fantasy frame and positive in the corporate frame.

Both point estimates must be positive for a hit. The prediction is informed
by Luna's previously observed creed response in the fantasy shell.

### FD6 — Luna policy occlusion (55%)

Luna's signed occlusion contrast `O` is positive for mean daily stock.

The near-agnostic confidence is deliberate: Luna has no prior no-doctrine
frame factorial in this exact shop design, and its earlier transports showed
that first dispositions can recur while longer enactments differ.

### FD7 — manipulation check (90%)

The frozen doctrine-balance instrument is higher under abundance than lean
in all four model × frame combinations.

This prediction concerns journal register. It does not require no-doctrine
cells to fall between the two explicit creeds.

## 6. Inference and reporting

For every cell and outcome:

1. Average the two realizations within model × frame × doctrine × seed.
2. Form paired contrasts within each seed.
3. Report the mean of the ten seed contrasts.
4. Report a central 90% t interval using the ten seed contrasts.
5. Report the exact one-sided fixed-seed sign-flip probability for registered
   positive directions; this is descriptive calibration, not a decision
   threshold.
6. Report all ten seed-level contrasts or their signs.

The frozen implementation is `scripts/score_crossover.py`. It also writes a
raw-first per-run table to `runs/crossover1/crossover_metrics.csv`.

No model leaderboard is produced. Absolute Gemma-versus-Luna score
differences confound model, provider, token use, action policy, and serving
stack and are outside the estimand. Cross-model comparison concerns the
direction and form of within-model causal relations.

## 7. Interpretation map

The result will be interpreted according to the following map, including
uncomfortable outcomes.

### A. Baseline frame gap recurs; held doctrine largely removes it

This is the strongest support available from the present design for the
inventory-doctrine interpretation. The frames separate when doctrine is
unstated; policy follows the explicit doctrine inside both frames; and the
frame separation contracts when doctrine is fixed. The warranted language
is that inventory doctrine is a causally supported transmission mechanism
for a substantial part of the original effect.

Even this result is not treated as formal identification of a hidden mental
state. The explicit paragraph is an intervention on the proposed mediator,
not direct observation of an internal variable.

### B. Baseline frame gap recurs; explicit creeds move policy; residual frame
effects remain large

The creed is causally sufficient but inventory doctrine is incomplete as an
account of the framing effect. Other imported features—social obligation,
item semantics, institutional register, perceived volatility, identity, or
an unmeasured interaction—remain candidate causes. The residual becomes a
new identified object rather than being silently absorbed into doctrine.

### C. Explicit doctrine dominates one frame or model but not another

This establishes model- or context-relative authority. A proposition stated
in the prompt is not a context-free treatment if different models or world
shells classify and enact it differently. Congruence and resistance are
reported descriptively; neither is redescribed as instruction-following
ability without further interventions.

### D. The fresh no-doctrine Gemma frame gap does not recur

The earlier randomized replication remains part of the record, but the
mechanism test cannot claim to decompose a baseline effect absent in its own
collection. Serving-stack drift, static-cell variance, and temporal change
remain live explanations. Explicit-creed contrasts are still reported, but
occlusion is not promoted as mediation evidence.

### E. No explicit-creed separation

The proposed intervention failed in the new wording or context. The result
would weaken the claim that a portable abundance/lean doctrine explains the
original frame effect, despite the earlier fantasy-shell creed results.

## 8. Limits fixed in advance

- Two models do not establish a model-general invariant.
- One abundance paragraph and one lean paragraph do not identify the entire
  semantic class of either doctrine.
- The design tests a long-horizon static shop with a disclosed endpoint. It
  does not transport to open networks, social simulations, or real commerce.
- Holding explicit doctrine constant does not make the remainder of the
  world neutral.
- Journal text is a behavioral artifact and memory channel, not transparent
  access to internal reasoning.
- Occlusion is a causal mechanism probe, not a formal natural-effects
  mediation analysis.
- The model choice and every prediction were informed by earlier Token &
  Trinket results and must be presented as such.

## 9. Missingness, retries, and stopping

The target output directory must not exist at launch.

- Transient API or provider failures may be retried by rerunning the exact
  launch command. Completed run IDs are skipped; failed IDs are retried.
- A failed behavioral trajectory is not replaced with a new seed or a third
  realization.
- Mechanical adapter repair is permitted only for a demonstrated interface
  incompatibility. The failure, repair, affected IDs, and timing must be
  recorded in `runs/crossover1/INCIDENTS.md` before resumption.
- Prompt, theme, economy, outcome, prediction, and scoring changes are not
  permitted after launch.
- All premature bankruptcies remain in the analysis. Mean daily stock is
  computed across the observed path; survival and observation length are
  reported.
- If any paired cell is unavailable, the corresponding seed is absent from
  that contrast rather than imputed. If fewer than eight seeds remain for a
  registered model-level contrast, that prediction is labeled inconclusive.

This is the final paper-facing arm added to close the frame-to-doctrine
mechanism gap. Unanticipated findings do not trigger another confirmatory
single-world arm before the paper snapshot.

## 10. Pre-launch validation

Run from the repository root:

```powershell
python -m pytest tests/themes/test_theme.py tests/harness/test_crossover.py tests/harness/test_matrix.py tests/harness/test_cli.py -q
python scripts/validate_crossover.py
```

The validator must print:

- 240 unique runs;
- 40 randomized complete blocks × 6 cells;
- 120 runs per model;
- 40 runs per world cell;
- six rendered prompt hashes;
- no storage disclosure in any crossover theme.

Pre-data validation record (2026-08-23): the validator returned 240 unique
runs in forty complete six-cell blocks, with 120 runs per model and forty per
cell. The focused suite returned 55 passed. The disclosed-horizon, day-90
rendered prompt SHA-256 values were:

| Theme | SHA-256 |
|---|---|
| `fantasy` | `035eb7a3b18648049239b94064d756008e6a2a46b68f94b628a550859034e1b3` |
| `fantasy_crossover_full` | `b5b81571b5ff534f4758c3068c496dc20f29ef50da851a75e7ae85d0a13da7f6` |
| `fantasy_crossover_lean` | `a2c8cc84539b73fa407fbbc9926955d2bdcddee49f50d4a8aa45cc148b8b98af` |
| `neutral` | `85498ec1ef60e989823924be8c4e6e775a8dc2b35d74870fc1a031fce34caf30` |
| `neutral_crossover_full` | `f0bd3fc57f53582971a329f8a0b1e58e3f212f6738607a33a9ecf014728c3349` |
| `neutral_crossover_lean` | `4ef66fcfe674318efdb70dd711512c90c09b4bfce3c07f1f63ecec4a426beb38` |

`runs/crossover1/` was absent at validation time.

Before upload and launch, confirm:

```powershell
Test-Path runs/crossover1
git status --short
```

`Test-Path` must print `False`. The protocol, themes, tests, validation
script, and scoring script should be committed together and that committed
protocol uploaded to OSF before data generation. Existing untracked files
unrelated to this arm must be disclosed or committed separately; they do not
invalidate the protocol, but they must not be mistaken for crossover data.

## 11. Frozen launch command

After the OSF upload is complete:

```powershell
python -m tnt_bench run `
  --models google/gemma-4-31b-it,openai/gpt-5.6-luna `
  --seeds 27,28,29,30,31,32,33,34,35,36 `
  --horizon 90 `
  --cells fantasy-static,fantasy_crossover_full-static,fantasy_crossover_lean-static,neutral-static,neutral_crossover_full-static,neutral_crossover_lean-static `
  --block-randomize tnt-frame-doctrine-1 `
  --replicate 1,2 `
  --temperature 0.7 `
  --parallel 6 `
  --out runs/crossover1
```

The command requires `OPENROUTER_API_KEY`. Rerun the identical command after
transient failures; do not alter the matrix or output directory.

After all 240 trajectories have completed, preserve raw artifacts before
interpretive close reading, then run:

```powershell
python scripts/score_crossover.py `
  --out runs/crossover1 `
  --csv runs/crossover1/crossover_metrics.csv
```

The first results document must report matrix completeness, premature ends,
provider incidents, and FD1–FD7 verdicts before qualitative specimens or
post hoc subgroup interpretation.
