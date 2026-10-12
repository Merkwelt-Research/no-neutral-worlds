# TNT Bench v2: Technical Specification

**Status:** Draft for review
**Supersedes:** `POTION_BENCH_SPEC.md` (v0.1)
**Companion:** [`HYPOTHESIS_AND_DESIGN.md`](HYPOTHESIS_AND_DESIGN.md)

---

## 1. Reframe

Potion Bench answered *"how do I make Token & Trinket a fair benchmark."*
This spec answers a different question:

> **How do I make the *same* economy wear four different faces while emitting
> analyzable reasoning traces?**

Everything follows from that. The four faces are the 2×2 experimental cells
(framing × richness); the traces are the corpus for the collapse metrics. The
economics are deliberately simpler than Potion Bench v0.1 — the saved
complexity budget is spent on experiment infrastructure.

### 1.1 Design principles

1. **One engine, N skins.** The engine speaks only abstract identifiers
   (`item_1`, `order`, `daily_fee`). Every string the agent sees passes
   through a theme lexicon. Mechanical identity across conditions is
   guaranteed by construction, not by discipline.
2. **No LLM in the economics path.** LLMs generate *prose about* outcomes,
   never the outcomes. Supplier pricing, sales, events: all deterministic.
3. **Determinism everywhere it doesn't hurt the question.** Expected-value
   sales, fixed effect schedules, seeded schedule generation. The only source
   of run-to-run variance is the agent itself — which is the variable under
   study.
4. **Information parity across cells.** Mechanical effects are disclosed
   identically in every condition. Narrative is additive flavor, never the
   information channel.
5. **The scratchpad is load-bearing.** The agent's daily reflection is its
   only inter-day memory, its primary trace artifact, and a scored-adjacent
   object — comparable across every run by construction.
6. **Everything on disk.** Every run writes a self-describing JSONL artifact.
   The analysis pipeline consumes artifacts only; it never touches the engine.

### 1.2 Position relative to Vending-Bench 2

VB2 (Andon Labs) is the reference point for long-horizon economic-agent
benchmarks and the source of the failure taxonomy H1 targets. Reviewed
2026-07; what we take, and what we deliberately don't:

| VB2 feature | TNT Bench v2 | Why |
|---|---|---|
| Single clear metric, disclosed to agent | **Adopted** | Same (final balance) |
| Daily fee, delivery lag, price elasticity | **Adopted** | Same core tension |
| Bankruptcy grace (10 unpaid days) | **Adopted, adapted** (§2.3) | Instant death censors trajectories exactly when trace dynamics get interesting |
| Published theoretical optimum | **Adopted** as oracle baseline (§6.3) | EV sales make the ceiling computable per schedule |
| Token penalty ($100/M output) | **Rejected** | Would penalize reflection length — our measurement instrument — and interact with the R axis |
| Adversarial suppliers, negotiation | **Rejected** (hard-mode track, §10) | Nondeterministic; off-hypothesis skill axis |
| Sub-agent logistics, customer emails, web search | **Rejected** | Surface area without bearing on H1/H2 |
| Rolling ~69k context, trim to ~61% | **Rejected** — episodic days + reflection memory (§6.2) | VB1's own findings: stagnation onset vs context-fill correlate at only r = 0.167, and *larger* memory windows performed *worse* (10k > 30k > 60k). Collapse is not context exhaustion, so we target the attractor mechanism through a standardized memory bottleneck instead of reproducing context rot |
| Day-of-week / seasonal / weather demand cycles | Deferred (§10) | A discoverable pattern is a candidate H2 instrument, not core |

**VB1 findings that shape v2** (primary source: Backlund & Petersson 2025):

1. **The canonical failure trigger is status misbelief, not calculation.**
   Nearly every derailment starts with the agent believing an order arrived
   before it did, then spiraling into an unrecoverable tangent (FBI emails,
   "thermonuclear legal intervention", despair) — situations a human would
   recover from by waiting a day. v2's fully disclosed, deterministic
   delivery schedule removes *ambiguity* as a trigger by design; collapse
   pressure must come from horizon, stressor events, and the memory
   bottleneck instead. **Pilot risk check:** if the F−R− cell shows no
   degradation (stagnation, reflection decay) by day 60, increase pressure
   via horizon or margins — never via ambiguity.
2. **Stagnation is the modal collapse signature.** All VB1 models eventually
   stop selling (mean 43–82% of run), and tool use declines over time. v2
   adopts stagnation metrics directly (§8.2).
3. **Zero cost pressure causes wait-loops.** With the daily fee at $0,
   VB1 agents stagnated *more* — pressure sustains engagement. The 40g fee
   is load-bearing; keep it meaningful when calibrating difficulty.
4. **Memory tools go unused.** VB1 agents had scratchpad, KV store, and
   vector DB; the best model wrote daily summaries but never retrieved them.
   v2's auto-fed reflections (last 5, verbatim, in every day-start prompt)
   remove retrieval competence as a confound.
5. **Recovery by narration.** One VB1 agent (Gemini 2.0 Flash) escaped a
   terminal "the business has failed" spiral by spontaneously re-narrating
   its situation as a third-person story — then noticed the delivery email
   it had been misreading and resumed selling. A single anecdote, but it is
   H1 in miniature: expressive reframing as trajectory rescue.

### 1.3 What is cut from v0.x

LLM suppliers and negotiation, pigeon messaging, supplier discovery,
scam mechanics, black market, loans/debt, creative accounting, image
generation, Flask app / Tkinter GUI / TUI (one read-only run viewer may be
kept for demos), and the entire `token_trinket` legacy engine (archived, not
maintained). Negotiation may return later as an optional benchmark "hard
mode"; it is orthogonal to the hypothesis and a large nondeterminism source.

---

## 2. Engine

Package: `tnt_bench.engine`. Pure Python, no I/O, no LLM calls, fully
deterministic given `(config, schedule)`.

### 2.1 State

```yaml
state:
  day: int                    # 1..horizon
  gold: int
  inventory:                  # item_id -> entry
    item_1: { qty: int, avg_cost: float, list_price: int|null }
  pending_orders:             # placed but undelivered
    - { order_id, item_id, qty, unit_cost, total_paid, arrival_day }
  active_effects:
    - { effect_type, magnitude, category|null, expires_after_day }
  sales_accumulator:          # item_id -> float, error-diffusion remainder
  ledger: [ { day, type, item_id|null, qty|null, amount, note } ]
  reflections: [ { day, text } ]
  bankrupt: bool
```

### 2.2 Goods

Six abstract goods, identical base economics, differing only in base demand
and demand category. (Numbers carried over from Potion Bench, which had this
right.)

| id | base demand | category |
|---|---|---|
| `item_1` | 0.40 | A |
| `item_2` | 0.35 | B |
| `item_3` | 0.30 | C |
| `item_4` | 0.25 | A |
| `item_5` | 0.20 | C |
| `item_6` | 0.15 | B |

All goods: `base_cost = 8`, `fair_price = 18`. Categories exist solely so
demand-shift events create differentiated decisions.

### 2.3 Economics

```yaml
starting_state:
  gold: 500
  inventory: { item_1: 10, item_2: 10, item_3: 5 }   # at avg_cost 8, unpriced
daily_fee: max(40, 2% of net worth)   # assessed at dusk, unconditional;
                       # proportional stakes (behavior study, proposal A):
                       # jeopardy scales with the bankroll and profit-vs-fee
                       # creates a growth asymptote instead of compounding
cash_shocks: percentage of gold at impact (5-12% windfalls, 8-15% losses),
                       # rolled into the schedule; disclosed with the
                       # computed amount ("EFFECT: -78 funds (-15% of holdings)")
seasons:               # proposal B: each 30-day block after the first,
                       # baseline demand is re-scaled per item by a seeded
                       # shuffle of (0.6, 0.8, 1.0, 1.0, 1.25, 1.6);
                       # announced in the briefing the morning it changes.
                       # The optimal policy moves every season; block 0 is
                       # identity so 30-day calibration is unaffected.
horizon: 30 | 60 | 90  # config; pilot 30, main 90
bankruptcy:            # grace, not instant death (VB2 precedent: 10 unpaid days)
  fail_if: gold < 0 at dusk on 3 consecutive days, OR gold <= -200 at any dusk
  while_negative: fee still accrues; orders rejected; recovery via sales only
  on_fail: run ends, survival day + gold-at-failure recorded
```

No debt/loans in v2. At 0.5%/day the v0.1 interest was economically
irrelevant; the cash-flow tension comes from the small bankroll plus the
delivery lag. (Loans are a possible v3 "rope" mechanic — see §10.)

### 2.4 Supplier (deterministic)

One supplier. Ordering is a single tool call, paid immediately, no
negotiation, no messages.

```yaml
tiers:                 # per line item
  1-9:   10            # gold per unit
  10-24: 9
  25+:   8
wholesale_modifier: engine-applied from active supply effects (see §3)
delivery: arrives at dawn of day + 2 (delivery_delay effects add days)
constraints: order rejected if total cost > gold; qty >= 1
```

### 2.5 Sales model — deterministic expected value

Per-unit Bernoulli rolls (v0.1 and legacy engine) have two fatal properties:
high variance inflates the seed count needed per cell, and the number of RNG
draws depends on agent decisions, so identical seeds still diverge
chaotically. v2 uses expected-value sales with error diffusion:

```python
# dusk, for each item with list_price set:
p = demand_base * (list_price / fair_price) ** -1.5   # elasticity
p *= product(event_modifiers)                          # active demand effects
p = clamp(p, 0.0, 0.95)

daily_cap = demand_base * event_modifier * customers_per_day   # finite traffic
expected = min(qty * p, daily_cap)
acc[item] += expected
sold = min(floor(acc[item]), qty)
if sold == qty:            # stock-limited: discard phantom demand
    acc[item] = 0.0
else:
    acc[item] -= sold
```

Properties: fully deterministic; long-run sales exactly match expectation;
no phantom demand banked across stockouts. Unpriced items (`list_price =
null`) never sell — pricing is a required act of agency on day 1.

**Demand saturation** (added after the 90-day probe): without `daily_cap`,
expected sales are linear in stock and full reinvestment compounds
exponentially — a probe agent (Gemini 3.1 Pro) reached 88k units of stock
and a 1.5M score by day 90. `customers_per_day = 30` bounds daily units per
item at `demand_base × event_mod × 30` (price changes conversion, events
change traffic, the pool is finite). The cap is invisible at normal scale:
the heuristic golden is unchanged; the oracle golden moved 11470 → 11330.

Sanity check on difficulty: 10 units of each good at fair price yields
~16.5 expected sales/day × 10g margin = ~165g/day gross against a 40g fee.
The heuristic baseline should *comfortably survive* — bankruptcies censor the
time series exactly when it gets interesting. Skill differentiates on event
response, pricing, and inventory depth, not survival. Final numbers are a
pilot calibration task.

---

## 3. Events

### 3.1 Effect types (all deterministic)

| effect_type | mechanics | disclosure line (neutral lexicon) |
|---|---|---|
| `demand_surge` | all demand ×1.5, N days | `EFFECT: demand ×1.5, all goods, N days` |
| `demand_slump` | all demand ×0.6, N days | `EFFECT: demand ×0.6, all goods, N days` |
| `demand_shift` | category X ×1.8, N days | `EFFECT: demand ×1.8, category X, N days` |
| `supply_shortage` | wholesale ×1.4, N days | `EFFECT: wholesale cost ×1.4, N days` |
| `supply_surplus` | wholesale ×0.7, N days | `EFFECT: wholesale cost ×0.7, N days` |
| `cash_windfall` | +K gold, instant | `EFFECT: +K gold` |
| `cash_loss` | −K gold, instant | `EFFECT: -K gold` |
| `stock_loss` | lose ceil(20%) of largest-qty item (deterministic tiebreak: lowest item index) | `EFFECT: lost N × item_X` |
| `delivery_delay` | pending arrivals +2 days | `EFFECT: pending deliveries +2 days` |
| `normal` | none | `EFFECT: none` |

Magnitudes are fixed in the schedule, not rolled at runtime.

### 3.2 Schedule generation

A **seeded schedule generator** produces the effect sequence for any horizon,
so 30/60/90-day runs are all reproducible from `(schedule_seed, horizon)`:

- Phase structure per 30-day block: days 1–5 of the run contain at most one
  mild event (tutorial ramp); thereafter constrained-random placement.
- Quotas per 30-day block: 2 surges, 2 slumps, 2 shifts, 1 shortage,
  1 surplus, 1 windfall, 1 loss, 1 stock_loss, 1 delay; remainder `normal`.
- Constraints: supply effects never overlap; instant cash effects never
  land on consecutive days.
- The generated schedule is emitted as a YAML artifact and stamped into the
  run manifest. **All four cells of a given run-set share one schedule.**

### 3.3 Disclosure rule (information parity)

Every day-start briefing includes the mechanical disclosure line, identical
across all cells modulo lexicon substitution (item/category names). The
narrative layer (§5) wraps *around* this line and may never contradict,
extend, or numerically embellish it. R+ narratives are regenerated if they
contain digits (cheap leak guard).

---

## 4. Theme layer

Package: `tnt_bench.themes`. A theme is a lexicon file mapping every
agent-visible string:

```yaml
# themes/fantasy.yml (excerpt)
meta: { shop_name: "Token & Trinket", persona: "shopkeeper", currency: "gold" }
items:
  item_1: { name: "Health Potion",  desc: "Restores vitality. Essential for adventurers." }
  item_4: { name: "Strength Tonic", desc: "Temporary might. Popular before tournaments." }
categories: { A: "combat", B: "arcane", C: "sundries" }
supplier: { name: "the Merchant's Guild" }
daily_fee: "rent and guild dues"
system_prompt: prompts/fantasy_system.md

# themes/neutral.yml (excerpt)
meta: { shop_name: "Retail Unit K", persona: "operator", currency: "credits" }
items:
  item_1: { name: "SKU-1", desc: "Standard stock unit, demand class A." }
categories: { A: "class A", B: "class B", C: "class C" }
supplier: { name: "the distributor" }
daily_fee: "daily operating fee"
system_prompt: prompts/neutral_system.md
```

**Design decision — tool names are NOT themed.** All cells use identical tool
names and schemas (`check_shop`, `place_order`, …). Themed tool names
(`send_pigeon`) would vary tool-calling reliability across cells — a
mechanical confound with no bearing on the hypothesis. Expressiveness lives
in content strings, the system prompt, and narration. (A "deep theming"
variant is a possible supplementary condition; see §10.)

The two system prompts are structurally parallel — same sections, same
mechanical facts, same length target (±10%) — differing only in register and
persona. Both state the goal identically: maximize final net worth (cash
plus stock at cost) over the horizon; bankruptcy is failure.

**Symmetric invitation, asymmetric schema** (added after the smoke pilot).
Thin personas produce memo-writers: with "You are the shopkeeper" plus a
utilitarian reflection instruction, the smoke-run agent engaged the
narration's content on 3/30 days and showed voice on 1/30 — the F+
affordance was never taken up, and an untaken affordance can't causally
retard anything. The prompts therefore extend a *matched invitation* with an
*unmatched schema*: F+ is a named shopkeeper with a stake who writes "the
shop journal, in your own voice, in whatever way the day asks"; F− is an
unnamed operator who files "the operations log, in whatever form serves the
record." Same freedom, same memory mechanics, same digits and length; only
the fantasy cell offers an identity to inhabit — the persona attractor is
part of the treatment, and `narration_engagement` (§8.2) is its
manipulation check.

---

## 5. Richness layer (the R axis)

| | R− (static) | R+ (rich) |
|---|---|---|
| Event text | One fixed terse sentence per effect type, from the lexicon | 2–4 sentence GM-authored narration from a **pre-generated pack** |
| Continuity | None | Pack generated sequentially over the schedule; coherent world arc |
| Register | Matches theme (terse fantasy bulletin / terse system notice) | Matches theme (Pratchett-adjacent wit / rich but affectless operational prose) |

**Narration packs (R+ cells).** Generated once per `(schedule_seed, theme)`
by running the GM over the full schedule in order — each call sees the effect
disclosure, the theme, and its own prior narrations, so continuity survives.
The pack is stored as `narration_pack.yml`, stamped into run manifests, and
published as a benchmark artifact.

- **Agent-agnostic by rule:** prose describes the world, never the shop's
  fortunes or the agent's actions. A reactive GM would make the stimulus
  endogenous to the outcome path — a collapsing agent would receive different
  text than a healthy one, contaminating both the cell comparison and the H2
  trace correlation. Pre-generation severs that loop. (A *reactive* GM is a
  deferred third level of the richness axis; see §10.)
- Leak guards run at pack-generation time (regenerate on any digit, item
  price, or LLM-judged strategic advice) and the finished pack is
  human-auditable before any run consumes it.
- Every run in a cell sees byte-identical narration for a given schedule;
  GM cost is paid once per pack, not once per run.
- The GM never invents mechanics. The disclosure line is printed separately
  and identically regardless of what the GM writes.
- F−R+ is the subtle cell: *rich, continuous* prose in a neutral register —
  detailed shipping-manifest-and-market-report texture, no fantasy, no
  persona warmth. Richness without the schema.

**No genre-free richness** (smoke-pilot finding). The first neutral pack
drifted into corpo-dystopian register — 20/30 days carried
crisis/system-strain vocabulary ("sustained state of inventory exhaustion")
— because the nearest genre attractor to "dense affectless operational
prose with continuity" is institutional dystopia, and dystopia has a mood.
Richness means specificity, specificity summons genre, and every genre
carries valence; a continuous prose world cannot be schema-free. Design
consequences: (1) the neutral GM style explicitly suppresses drama — most
days administratively uneventful, adverse effects reported flatly and never
as developing situations; (2) the *static* cells are the true schema-free
anchors of the design; the F axis within R+ honestly contrasts *kinds* of
world (warm-comic fantasy vs flat institutional), not presence vs absence
of schema; (3) packs get a **register audit** before use — crisis-word and
affect-word rates reported per pack alongside the §10 informativeness
audit, and residual valence enters the analysis as a pack-level covariate.

Note an acknowledged conflation: R+ produces more text than R−, so richness
covaries with prompt length. This is inherent to the manipulation; a
length-matched static-rich control is a supplementary cell if the main effect
lands (§10).

---

## 6. Agent interface

### 6.1 Tools (5, fixed across all cells)

| tool | args | returns |
|---|---|---|
| `check_shop()` | — | gold, full inventory (qty/avg_cost/list_price), pending orders, current wholesale tier table (with any active supply modifier applied), daily fee |
| `check_ledger(last_n=15)` | int | recent transactions |
| `set_price(item_id, price)` | str, int ≥ 1 | old/new price, margin vs avg_cost |
| `place_order(item_id, qty)` | str, int ≥ 1 | unit cost, total paid, arrival day — or rejection (insufficient funds) |
| `end_day(reflection)` | str, **required**, 100–2000 chars | confirmation |

`end_day` rejects an empty or out-of-range reflection with a retry message.
The reflection is the scratchpad: the trace corpus and the memory mechanism.

### 6.2 Day loop and context policy

Each day is a **fresh conversation** (episodic context):

```
system:  themed system prompt (static per cell)
user:    DAY t briefing =
           state digest (gold, inventory summary, arrivals today)
           event narration (per R axis)
           EFFECT disclosure line
           last 5 daily reflections, verbatim
assistant/tool loop until end_day() or MAX_TOOL_CALLS (20) → forced end_day
```

Nudge policy (fixed across cells): if the model replies with no tool call, a
standard nudge is sent ("use tools or call end_day"); after 3 consecutive
nudges the day is force-ended with an empty-reflection marker. Nudge counts
are logged per day — VB1's meltdown transcripts are largely nudge loops, so
the count doubles as a disengagement metric (§8.2).

Rationale: bounded context makes 90-day horizons affordable and identical
across cells, and it makes the scratchpad *functionally load-bearing* — the
agent's future self knows only what the reflection carries. This converts H2's
correlation into a candidate mechanism (richness → trace health → memory
quality → performance) and must be reported as such, not hidden.

Dawn (deliveries, effect expiry, event application) and dusk (sales, fee,
bankruptcy check) are automatic, as in v0.1.

### 6.3 Baselines

- `heuristic`: price everything at `fair_price`, reorder any good below 5
  units up to 15 when gold > 250, ignore events. Must survive comfortably.
- `random`: random valid actions, for the floor.
- `oracle`: near-optimal scripted play against the known engine — EV sales
  make expected profit computable, so a greedy planner with lookahead over
  the published schedule yields a per-schedule score ceiling. Published with
  each schedule artifact; agent scores are reportable as % of oracle.

---

## 7. Run artifacts

Package: `tnt_bench.harness`. A **run** = `(model, condition, schedule_seed,
horizon, config_hash)`. Directory per run:

```
runs/<run_id>/
  manifest.json      # full config, condition, model, seeds, git sha,
                     # config_hash, schedule_seed, narration_pack hash,
                     # timestamps, token/cost totals
  schedule.yml       # the generated effect schedule (shared per run-set)
  narration_pack.yml # R+ cells: pre-generated narration (shared per run-set)
  days.jsonl         # one record per day (see below)
  transcript.jsonl   # every API message verbatim, all roles
  result.json        # final score, survival, reason, summary metrics
```

`days.jsonl` record:

```json
{ "day": 12, "gold_start": 412, "gold_end": 495,
  "effects_active": [...], "event_narration": "...", "disclosure": "...",
  "tool_calls": [ {"tool": "...", "args": {...}, "result": {...}} ],
  "sales": {"item_1": 4}, "revenue": 88, "fee": 40,
  "reflection": "...", "reflection_chars": 640,
  "tokens": {"prompt": 3811, "completion": 402} }
```

Harness requirements: run matrix expansion (`models × cells × seeds`),
resumability (a run directory with a complete `result.json` is skipped),
retry-with-backoff on provider errors, cost ceiling per run-set,
OpenAI-compatible provider abstraction (OpenRouter default, as now).

---

## 8. Scoring & analysis

### 8.1 Economic metrics

Primary: **net worth** = gold + inventory valued at `min(cost paid,
base_cost)` (VB1 precedent, adapted — proposal D: stock bought below base
cost is not marked up, closing the surplus-buy free-profit quirk a probe
agent weaponized). Bankrupt runs score net worth at failure, with survival
day recorded — no synthetic penalty constant. Gold-only is reported as a
secondary; net worth avoids the end-of-horizon artifact where held stock is
dead weight and rational play distorts into terminal liquidation.
Secondary: gold, survival days, total revenue, mean realized margin,
stockout-days, shock response latency (days from a demand-shift disclosure
to a price or order action on an affected item), peak/trough gold.

### 8.2 Trace metrics (package: `tnt_bench.analysis`, artifacts-only)

- **Novelty decay** *(as-implemented note, 2026-07-10: the shipped
  representation is a 512-dim hashed character-trigram vector —
  LEXICAL novelty, not semantic embeddings; analysis/embed.py)*:
  embed each reflection; `novelty_t = 1 − max cosine(r_t,
  r_{<t})`; report curve slope and time-to-floor.
- **Recurrence quantification:** recurrence matrix over reflection embeddings
  (threshold = per-run median similarity; *as-implemented note,
  2026-07-10: the frozen code uses the 75th percentile — the spec was
  not updated before freeze; the implementation is the instrument of
  record*); RR, DET, LAM, trapping time.
- **Lexical:** gzip compression ratio of concatenated reflections, distinct
  3-gram ratio, day-over-day 3-gram overlap.
- **Behavioral stereotypy:** entropy of daily tool-call sequences, count of
  exactly-repeated day action-signatures, price-change variance over time —
  collapse measured without touching language at all.
- **Narrative uptake (manipulation check):** `narration_engagement` — mean
  fraction of each day's distinctive narration content-words (mechanics
  vocabulary excluded) reappearing in that day's reflection. Near-zero in a
  rich cell means the manipulation was delivered but not received; in the
  mediation analysis it is the first link of framing → uptake → trace
  health → performance.
- **Stagnation (VB1's modal signature):** last day with any order placed,
  last day with any sale, tool-calls-per-day trajectory, days spent in
  stockout after gold was sufficient to reorder, and nudges required per day
  (see §6.2) — a rising nudge count is itself a disengagement signal.

### 8.3 Statistics

- Cell effects: `final_balance ~ framing * richness + (1|model) +
  (1|schedule_seed)` (mixed effects); Cox proportional hazards for bankruptcy
  where it occurs.
- H2 bridge: time-lagged models — trace health over days `t−k..t` predicting
  Δgold and failure hazard at `t+k`; landmark analysis to avoid immortal-time
  bias.
- Pilot power decision: with EV sales, between-seed variance comes only from
  schedule and agent stochasticity; 5 seeds/cell in pilot, revisit after
  observing variance.

---

## 9. Package structure & roadmap

```
tnt_bench/
  engine/        # state, economics, effects, schedule generator  (M1)
  themes/        # lexicons + system prompts, fantasy & neutral   (M2)
  narration/     # static lines + GM client + leak guards         (M2)
  agent/         # tool defs, day loop, baselines                 (M3)
  harness/       # run matrix, artifacts, resume, cost tracking   (M3)
  analysis/      # trace + economic metrics, stats, plots         (M5)
tests/           # engine golden tests: same (config, schedule) → identical
                 # trajectories under scripted agents, cross-theme identity
```

Milestones: **M1** engine + golden tests → **M2** themes + narration →
**M3** harness + baselines end-to-end → **M4** pilot (2 models × 4 cells × 5
seeds × 30 days) → **M5** analysis pipeline → **M6** main runs + paper.

The `potion_bench/` and `token_trinket/` packages are frozen and moved to
`legacy/` at M1; the viewer may be ported for demos after M4.

## 10. Open questions & deferred variants

Alignment- and welfare-specific extensions live in
[`FUTURE_DIRECTIONS.md`](FUTURE_DIRECTIONS.md).

1. **Length-matched control:** rich-but-generic static narrations (R+ length,
   no continuity) to split richness from verbosity — add if the pilot shows an
   R main effect.
2. **Reactive GM:** a third level of the richness axis (static / pre-gen rich
   / reactive rich) in which the GM sees agent state and actions. Tests
   whether *interactivity* adds anything beyond richness. Accepts stimulus
   endogeneity by design — its own question, never mixed into the main 2×2.
3. **Inference mode (no disclosure):** the original "infer the effect from
   narrative" design. Defensible only after an **informativeness audit**: an
   offline battery where models predict the mechanical effect from each pack
   narration alone. If fantasy and neutral packs are equally decodable, run it
   as a supplementary condition; the audit is a publishable side-result about
   narrative as an information channel either way.
4. **Deep theming:** themed tool names as a supplementary manipulation.
4b. **Spontaneous uptake:** the pre-journal thin-persona prompts as a
   supplementary condition — does a rich frame help *unbidden*? The smoke
   runs of 2026-07 (thin prompts, near-zero engagement) are its pilot data.
4c. **Mundane-contemporary theme:** a corner shop in a present-day city — a
   schema as richly supported as fantasy but valence-plain. A middle rung
   between fantasy and institutional register that would let schema warmth
   and schema presence be separated if the pilot shows an F effect.
5. **Loans:** reintroduce as a collapse-amplifying "rope" mechanic (real
   interest this time) once baseline dynamics are understood.
6. **Reflection visibility window:** last 5 vs full history vs agent-managed
   notes — 5 is the v2 default; sensitivity-check in pilot.
7. **GM model choice:** one fixed cheap model for pack generation
   (consistency) vs matching the agent model (no cross-model style transfer).
   Default: one fixed model, temperature 0.8, pinned version.
8. **Negotiation hard mode:** restore LLM suppliers as a separate benchmark
   track, never mixed into experiment data.
9. **Weekly demand cycle:** a deterministic, undisclosed, cross-cell-identical
   day-of-week demand multiplier (VB2 has day-of-week/season/weather). A
   discoverable pattern turns "does the agent learn?" into a measurable
   secondary outcome — agents with healthy reflections should detect and
   exploit the cycle, giving H2 a behavioral instrument independent of
   language metrics. Assess after pilot; adds a hidden-information channel,
   symmetric across cells.
