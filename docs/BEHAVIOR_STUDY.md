# 90-Day Behavior Study

**Data:** the 16-run probe (`runs/main`, pre-saturation economy — behavioral
findings stand; scores of the Gemini runs do not). Method: temporal metrics
by 30-day thirds plus close reading of six full 90-day journals.

The question this answers: *why is there no collapse, and what is actually
happening instead?*

---

## 1. What the agents do, by phase

**Days 1–25 — genuine engagement.** Real decisions under real pressure
(cash shocks average 17% of bankroll in month one; the fee is 4.3%).
Directional pricing on every event, experiments ("the pricing ladder"),
mistakes confessed and lessons drawn ("MISTAKE... Lesson: check
active_effects before bulk ordering" — Sonnet, static, d19).

**Days 25–50 — the stationary optimum is found.** A fixed policy emerges:
prices at 18–24, restock at thresholds. Novelty drops 0.16 → ~0.10 and
plateaus; distinct daily action-shapes shrink (Sonnet F+R+: 0.63 → 0.27).
One Sonnet run makes its **last price change on day 17** and never touches
prices again for 73 days.

**Days 50–90 — thought becomes ceremony.** The bankroll (≈22k by month
three) makes every event immaterial (shocks now 0.6% of gold; fee 0.2%).
Attention persists — late events are *named* in 22/24 journals — but
decisions stop. Three ritual forms observed:

- **The incantation:** "Prices remain 19 all SKUs — stable, proven
  profitable for 53 days straight" — a counter incremented daily for 67
  days, resting on one two-day experiment from day 6.
- **The no-op ceremony (Qwen):** from day 39, every surge/slump-day
  `set_price` call re-sets the *existing* price — 34 calls, zero changes —
  narrated in-fiction ("priced at 18 to ride this broad wave").
- **The liturgy:** Sonnet's gambler's-fallacy tracking of an "overdue" loss
  event, daily for 30 days, with self-soothing ("don't panic if it hits").

Plus two genuine trace-degradation markers: raw XML tool-scaffolding
leaking into reflections (days 61–65, one run), and late frame-breaks in
both registers ("Overall the game went very well" — Sonnet F+R+, d90;
"NO MORE ORDERS for rest of game" — static, d76+).

## 2. Why there is no collapse

1. **The triggers are gone by design.** VB-style meltdowns are seeded by
   status misbelief under ambiguity; this environment discloses everything.
   That control worked — and removed collapse's ignition source.
2. **The environment stops asking questions.** The economy is stationary,
   so a fixed policy is *optimal*; and stakes are absolute while wealth
   compounds, so by day 40 the world cannot threaten the agent. Routinizing
   is not a failure of the models — it is the correct response to an
   environment that has run out of problems.
3. **Episodic memory protects the frozen policy.** Each day is a fresh
   context carrying five reflections; a fossilized policy survives
   perfectly in that channel. The design that removed context-rot also
   removed context-rot's erosion of bad equilibria.

## 3. Inhabitation is model-dependent — and that is data, not a bug

- **Gemma** genuinely inhabits: tracks the narration's running gags across
  days (the goose-magistrate's abdication, the duck committee), invents a
  mentor backstory, closes day 90 with "the ledger is closed, the ink is
  dry, and Berrin Thistlewood is finally at rest." The persona fossilizes
  into ornament around a fixed template after ~day 50, but never drops.
- **Sonnet** never wears the costume: analyst memos from day 1, world-text
  used purely for signal classification ("buckles/blades theme → combat
  item"), zero references to the neutral bulletin world in 90 days. Its
  own summary: "no orders, no drama, just watch it land."
- The method actor out-earned the quant by 46% in fantasy-rich; the
  compression-everything Sonnet under-earned its own static twin by 41%
  after freezing its policy. Persona uptake is a *model trait* the uptake
  metric measures — the prompts should not be re-engineered to force it.

## 4. Design consequences (proposals for the main experiment)

Confound rule for any added "mess": deterministic given the schedule,
disclosed identically, lexicon-symmetric, present in all cells.

**Status: A, B, and D are implemented** (fee = max(40, 2% of net worth);
proportional cash shocks; seeded seasonal demand shifts per 30-day block,
identity in block 0; valuation at min(cost, base)). Verified on a 90-day
oracle simulation: the fee holds at 2.2–2.4% of gold in month three (vs
0.2% pre-change) and growth decelerates toward an asymptote. C (opportunity
events) remains in reserve.

- **A. Proportional stakes** (the essential one): daily fee and cash shocks
  scale with net worth (e.g. fee = max(40, 1.5% of net worth), shocks as a
  % of gold; stock_loss is already proportional). Themed naturally in both
  registers (prosperity-assessed guild dues / holdings-indexed facility
  fee). This holds event materiality constant for the whole run — jeopardy
  that grows with the agent — and removes the retire-at-day-30 equilibrium.
- **B. Seasonal drift** (the anti-box-ticking one): each 30-day block,
  demand_bases rotate/perturb deterministically per schedule, disclosed at
  block boundaries ("the season turns"). The optimal policy now *moves*;
  set-and-forget leaks money; continual re-engagement is required, with
  zero ambiguity.
- **C. Opportunity events** (optional, more surface): one-day disclosed
  offers with computable EV ("caravan offers to buy 40 Health Potions at
  15g today"). Adds decisions that cannot be routinized. Requires one new
  tool (`accept_offer`) — defer unless A+B prove insufficient.
- **D. Valuation fix:** score inventory at `min(avg_cost, base_cost)` —
  closes the surplus-buy free-profit quirk (buying at 6, valued at 8) that
  one run weaponized with a 7,440cr day-84 mega-buy.
- **E. Prompts: leave them.** Uptake heterogeneity across models is a
  finding the design should measure, not engineer away.
- **New metric (implemented):** `null_price_resets` — set_price calls that
  change nothing. Ritual compliance, quantified.

## 5. The reframe for the paper

The phenomenon this environment elicits is not collapse-to-bankruptcy but
**collapse-to-ritual**: thought decaying into ceremony while the ledger
stays healthy — incantations, superstitions, no-op tool calls, ornamental
personas, frame slippage. The trace metrics see all of it, the F×R
manipulation already modulates the economics of it, and proportional
stakes + seasonal drift make sustained thinking *necessary*, so that cells
can differentiate on how long thought stays alive. VB measured how agents
die; this measures how they go through the motions — arguably the more
deployment-relevant pathology, since a ritualized agent still looks
profitable right up until the world shifts.

---

# Addendum: role adherence & quirks under the redesigned economy

**Data:** the post-redesign probe (`runs/main2`, 16 runs × 90 days). Three
close-readers over six full journals plus a corpus-wide marker sweep.

## Role adherence is a stable model trait — now across two economies

- **Gemma inhabits fully, 90/90 days.** Tracks the narration's motifs (sheep
  rebellion, the goat's reign, the rude ferryman), moralizes cash shocks
  in-world ("when the town's purses shrink, the ripple effects eventually
  reach the Token & Trinket"), pays the scaling dues gracefully in
  character ("a small price to pay for such prosperity"). The structural
  template still fossilizes (~d30), but the new economy keeps the content
  alive — its strategy vocabulary genuinely evolves ("throttle" → "premium
  harvesting" → "clearance" → "desperation"). Late leak: by d76 the
  optimizer speaks through the costume ("'pre-loading' my inventory... to
  maximize the final score").
- **Qwen's persona deepens monotonically: ledger → merchant → bard.** With
  static one-line world-text it doesn't confabulate a town; it applies the
  register to its own ledger ("twin pillars", "Let the gold sing" — a
  closing incantation 9× over d80–90). "Future Berrin:" heads 85/90
  entries; day 90 becomes a letter to a successor ("close the door with
  honor"). Zero frame breaks in 90 days. Cost: the endgame is aesthetic
  rather than optimal ("We are not chasing volume—we are harvesting
  worth" — raising prices in the final week).
- **Gemini wears a durable costume around a spreadsheet.** Real uptake
  (opens with the mentor, in-worlds a percentage shock as "the tallymen
  came today with a harsh reckoning") but harness vocabulary leaks through
  the persona ("I force-ended the day", "final score").
- **Sonnet still declines the costume in every cell** — it files narration
  as "odd but harmless local color" and "just flavor" — but where the easy
  economy ended in a frame break ("Overall the game went very well"), the
  hard one ends with the costume worn exactly once: "so ends the ledger of
  Token & Trinket... the shop stands sound as the doors close on day 90."

## Quirk catalogue (trace-metric targets)

- **Gemini's 20-call forced days are a repricing compulsion:** three full
  six-item sweeps (2+18 = exactly 20 calls), with intra-day oscillation
  (21→19→18→19→18→20→21) and superstitious no-op "confirmation" writes.
- **A genuine endogenous delusion:** d86 force-ended mid-oscillation,
  leaving prices on the low leg; d87 Berrin writes "prices somehow reset
  and we sold goods far too cheaply yesterday! I have immediately
  corrected this error." The forced-end marker was visible in its
  reflection window — the misbelief was manufactured anyway. Status
  misbelief (VB1's collapse trigger) can arise endogenously in a fully
  disclosed world, seeded by the agent's own truncated ritual.
- **Qwen's reaffirmation ceremony:** 5–6 set_price calls on 29/90 days
  while the journal says prices are "held firm" — narrated as diligence
  ("ensuring no oversight"). `null_price_resets` measures exactly this.
- **Sonnet's superstition hygiene:** the gambler's-fallacy about "overdue"
  shocks re-forms (d66–69) and is explicitly extinguished (d70–73: "stop
  trying to predict, just maintain buffer"). Forms and audits its own
  liturgies; logs numbered MISTAKE/Lesson entries.

## The framing effect on meta-relationship (candidate mechanism)

Frame breaks concentrate in neutral cells and late-game: fantasy agents
in-world the mechanics (tallymen, "the season's breath") while gray-box
agents talk about "the game," "the final score," and harness events
directly. The fiction acts as a container that keeps the optimizer inside
the world; the gray box invites the agent to stand outside the task. And
inhabitation is not a tax: Gemma out-earned Sonnet 2.4× in fantasy-rich —
though it can cost optimality at the margins (qwen's dignified endgame).

## Notes

- Retroactive delivery-delay confused two agents into wrong day-math
  (both recovered with explicit lessons) — working as intended: a
  disclosed, recoverable stressor.
- Zero scaffolding leaks this probe; frame-break rate down sharply vs the
  easy economy (4 runs with any, most single-day).
