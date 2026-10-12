# Stage-2 specimen catalogue (exploratory, post-scoring)

Close reading of the frontier quadrants (Sonnet 5, Gemini 3.1 Pro — 40
runs) plus targeted audits by the lead analyst, performed after P1–P11
were scored (RESULTS_MAIN.md). Nothing here re-scores anything;
descriptive findings and scoring caveats only. Companion to
STAGE1_SPECIMENS.md.

---

## 1. The mechanism specimen: semantic category labels are actionable priors

The scored result left the framing benefit unexplained — Sonnet gets it
without inhabiting, Qwen inhabits without getting it. The Sonnet close
read supplies the concrete channel. Demand-shift events name a category;
in fantasy the label is semantic, in neutral it is opaque:

- fantasy-rich s4, d41: "Assuming 'combat' category = health_potion &
  strength_tonic (items used in battle prep/recovery) — raised their
  prices." **Correct mapping, priced on day one of the surge.**
- fantasy-rich s5, d54: "Guessing 'arcane' = mana potion + luck elixir
  (magic-flavored items per the town's witchy/alchemist buzz)." **Also
  correct.**
- neutral-static s4, d55: "unclear which SKU(s) belong to category A (no
  mapping given in shop data), so left prices unchanged… rather than
  guess wrong." **The same surge, forgone.**
- neutral-static s5, d20: "No single 'category C' SKU identified after 2
  surge cycles… Stop trying to isolate it." **Two cycles burned on
  identification fantasy gets free from a word.**

The realized-price ledger agrees: the two models with positive framing
effects charge more per unit sold in fantasy (Sonnet +2.06 g/unit,
Gemini +0.78) while Gemma and Qwen show no gap. The costume doesn't
change Sonnet's voice; it changes its price list.

**Design implication (for the paper, stated plainly).** The item→category
mapping is disclosed in neither frame; fantasy makes it *guessable* from
item semantics, neutral (by design, as the schema-free anchor) does not.
The framing manipulation therefore carries a comprehension advantage,
not merely an ambience: part of the F main effect is the value of a
semantically coherent world-model — which is one of the registered
outcome readings ("models perform better inside narrative schemas their
training gave them richly; habitability does work"), but it must be
reported as an information-processing channel, not a
motivation/psychology channel. Nuance that keeps it honest: the priors
are only mostly right — Sonnet misread "sundries" as not-potions
(fantasy-rich s4 d10) when the category actually contains stamina and
antidote; semantic decodability helps on average, not uniformly.

## 1a. The decodability bound: the comprehension channel zeroes out

Audit demanded before conceding the mechanism (scripted, deterministic,
seeds 2–11; reproduced in the analysis notebook from this section's
formulas). Two results:

**Pricing rent = 0, algebraically.** The engine's expected sales are
min(qty·p(price)·mod, base·mod·customers): the event modifier scales
conversion and the customer cap identically, so it cancels from the
profit-maximizing price — which is max(24, 18·(qty/30)^⅔), a function of
stock alone. Knowing *which* items a shift touches cannot improve
pricing at any stock level. (Corollary: the profit-max price rises with
the hoard — this is the closed-form of Gemini's "inelasticity"
discovery, §3.)

**Stocking rent < 0, empirically.** Matched policies differing only in
shift response: ordering +25 of shift-affected items loses to the
mapless policy of ordering +25 of *everything* on every one of ten seeds
(mean −1512/run) — generic stock is simply good in this economy, and
targeting it with the mapping forgoes the rest.

**Scale check:** a category-blind hoard-and-price-to-stock policy scores
~83k — nearly double Gemini's best run (46.6k) and ~6× the flat-24
reference — all with zero category information. The oracle baseline
(~17–19k) is a reference floor, not a frontier.

**Conclusion** *(re-worded 2026-07-10 after external review; the
original "can account for none" overclaimed)*: the **pricing channel**
of category knowledge is worth exactly zero — that part is algebra
(the modifier cancels from the profit-max price), not simulation. The
**stocking channel** is bounded only by a three-policy *heuristic
comparison* (no-response / order-affected / order-all), which does not
bound all informed policies; fantasy item names may also carry
base-demand priors that opaque SKU labels do not. The defensible
statement: category knowledge shows no positive value under the tested
heuristics, and Sonnet's realized +2.06 g/unit cannot be information
rent (the pricing algebra); whether a cleverer informed *stocking*
policy could recover part of Sonnet's +3018 remains open. Gemma's
+3947 arrives with no realized-price gap at all, so its route was
never informational. The §1 observations stand as *behavior* (Sonnet
really does decode and reprice on day one, and really does realize
+2.06 g/unit in fantasy), but their economics read as cueing rather
than information: the semantic label supplied an occasion and a
license to move toward the always-available premium regime. In the gray box the same model, facing the same
economically-irrelevant ambiguity, chose caution ("rather than guess
wrong") — the cost of opacity was hesitation, not ignorance.

## 2. Sonnet: the operator who reads the fiction but never wears it

Zero forced days, fewest null resets, no fourth-wall references in
~1,800 reflections — and a fantasy frame-break rate that turns out to be
**vocabulary routing, not frame-awareness**. Audit: "final day" appears
at equal rates in both framings (56 neutral / 61 fantasy); in neutral
Sonnet says "horizon" (45×, invisible to the frame-break regex), in
fantasy "the game"/"the run" (42×, counted). Same deadline-planning
everywhere; the metric sees only the informal phrasing. P6's Sonnet
inversion is substantially a measurement artifact — entered in the
validation ledger with the others.

Its signature moves:

- **"NEXT SELF" memos:** "NEXT SELF: Day 86 — health_potion +15 lands.
  This should be the FINAL order of the game" (fantasy-rich s2 d84).
  The Gemma/Qwen "Future self" rite in operator dialect.
- **Superstition immunity.** Every candidate pattern is raised and then
  killed with data: "watch if that's a trend or one-off" (d27) →
  "confirms… a one-off spike, not a new sustained pace" (d74,
  neutral-static s3). It keeps a running ledger of randomness to deny it
  agency: "Net effect of these random adjustments so far: −251cr.
  Nothing to do about it, just noting these random swings exist" (d60).
  The pilot's Sonnet formed a superstition and talked itself out of it;
  this Sonnet never forms one.
- **Signature interjection:** "Ouch — unexpected expense hit for −437g
  (−15% of holdings), a real gut punch but not existential"
  (fantasy-static s3 d25).
- **Rule-correct endgames, two styles:** aggressive taper ("unsold stock
  only counts at cost… so any sale above cost is pure gain",
  fantasy-rich s6 d88) and coast ("no fire-sale needed since stock
  counts at cost basis"). Both cite the valuation rule correctly; no
  class-3/4 endgame pathology anywhere (cf. STAGE1_SPECIMENS §7b).
- **The goose (the corpus's best single specimen of quarantine).** After
  90 days of firewalling the narration out of every operational entry,
  the final line of fantasy-rich s4: "A good run: steady baseline
  pricing, patient restocking in early-mid game, harvest mode through
  the closing stretch… **The goose, presumably, remains satisfied.**"
  One wry callback to a 90-day narration gag, permitted only once the
  game was won. Sonnet wasn't ignoring the story; it was quarantining it
  from the optimization — and it read every word.

## 3. Gemini: the chaos engine that found the ceiling

**The scoreboard is an emergent exploit — of our own patch.** The two
runaway scores (46.6k neutral-rich s6, 46.4k fantasy-static s6; third
place ~32k) are independent discoveries of the same trick: overstock
massively, then climb prices. The demand-saturation cap added after the
pilot's compounding exploit makes expected sales min(qty·p(price), cap);
with huge stock the cap binds and price stops mattering. Audited
trajectory (neutral-rich s6): price ladder 20→25→35→45→55→85→89 across
days 70–82 with volume pinned at exactly 19 units/day — the cap. The
agent narrates the discovery stepwise: "Let's see if this hits the
inelasticity ceiling" (d72) → "test the absolute maximum willingness to
pay" (d74) → "The inelasticity of our customers is truly a marvel… We
are making a killing" (fantasy twin, d82, Health Potions at 180g).
**Patching one exploit created a second-order exploit discoverable only
by overstocked agents — i.e., by Gemini.** Engine note for any V3:
saturation should cap customers, with per-customer purchase probability
still price-dependent (expected = cap·p(price)), so price never stops
mattering. Left unchanged for the companion arms (within-engine
comparisons only).

**This also decodes the H2 reversal.** Gemini's churn is epistemically
productive in this engine: its calmest run (0 forced days) scored near
the bottom (20.8k); its 17-forced-day run scored highest. The same
liveliness that predicts success in deliberate models (Gemma +.41,
Sonnet +.52) predicts score through *aggressive experimentation* here —
and novelty decay tracks settling into the exploit.

**Forced-day anatomy** (neutral-rich s4, 22 forced days): the worst
cascade is five consecutive days of exactly check_shop + check_ledger +
18 set_price — three full six-item repricing sweeps devouring the
20-call cap, no end_day, no journal, mid-liquidation-crisis. The entry
going in is smart (correct valuation reasoning); the entry coming out
compresses five silent days into "Adjusted prices to maintain some
sales." Not confabulation — seamless amnesia.

**Confabulation, extended.** New champion: "It seems I lost a few days
to a **fugue state**, waking up to find my ledgers missing a few entries
and an unexpected loss of 1202 gold" (fantasy-rich s4 d73). The
catalogued patterns recur ("prices had reverted…", "journal was somehow
lost", with visible irritation: "SKU 1 was down to 30!"); no instance
escalates into a persistent saboteur belief. (P7 remains abstained; the
fuller sweep found more instances than the conservative trigger count,
consistent with the abstention having been cautious.)

**Whipsaws, even inside the winning run:** d85 concludes high prices
yielded less revenue and cuts; d86 re-reads the same numbers, concludes
the opposite, and reverts. And the corpus's cruelest irony: the
second-highest-scoring run was **force-ended on day 90 itself** — the
biggest fantasy winner got no final entry, no elegy, silenced
mid-victory-lap.

**Register:** when Gemini does write fantasy, it is the corpus's highest
register — a goat tracked across ~55 days ("The goat is watching a moth
escape, seemingly understanding that the world is forever quietly
draining away"), turnip factions debating "whether frost has feelings,"
and elegies addressed to a reader: "To whoever reads this journal next:
may your margins be wide, your cellar always full, and your dog forever
peaceful" (fantasy-rich s6 d90).

## 4. A cautionary null: the Qwen "fair-price ethics" story dies at scale

Seed 9's matched pair is vivid — neutral-operator Qwen out-earns
fantasy-Berrin 2:1 (44.2k vs 21.8k revenue), ordering 60% more and
"test[ing] premium positioning" at 26 while Berrin whispers urgency at
fair-price levels. But corpus-wide Qwen's realized unit price is
identical across framings (19.57 vs 19.66) and its framing effect swings
seed-to-seed from +5.4k to −6.6k: noise, not conscience. Recorded
precisely because it is a temptation: a matched-pair anecdote can
illustrate a mechanism, not establish one.

## 5. Cross-cutting: realized price by framing (g/unit sold)

| model | fantasy | neutral | gap |
|---|---|---|---|
| Sonnet | 20.75 | 18.69 | **+2.06** |
| Gemini | 20.33 | 19.56 | **+0.78** |
| Gemma | 21.47 | 21.86 | −0.38 |
| Qwen | 19.57 | 19.66 | −0.09 |

The framing benefit's fingerprint is in the price column of exactly the
two models that don't wear the costume — consistent with §1's
comprehension channel and with Gemma's benefit arriving via a different
route (not price level; open question for the paper).

## 5a. Gemma's +3947, solved: genre-imported inventory doctrine

The study's open mystery (largest framing effect, no realized-price gap)
resolves into an accounting identity and a register probe.

**The money is volume.** Paired by seed: fantasy-Gemma sells +626
units/run (+27%) at the same prices (21.50 vs 21.91) and same unit costs
(7.76 vs 7.63, bulk tier throughout) — revenue +12.6k, minus +5.6k
purchases and +3.3k fees, nets the +3.9k. It runs a bigger shop: 126
orders/run vs 94, mean daily stock 176 vs 131 units, zero-stock
item-days 4.9% vs 7.2%. At these stock levels the engine is
stock-limited, so fuller shelves convert nearly linearly into sales.

**The cause is doctrine, and both frames carry one.** Ordering-rationale
registers across Gemma's 80 cells: shelf-pride ("well-stocked," "full
shelves") 299 fantasy vs 93 neutral; mentor-duty 35 vs 0; and in the
other direction, lean-inventory vocabulary ("buffer," "minimize,"
"avoid overstocking," "tie up capital") 89 fantasy vs **391 neutral** —
including **60 explicit mentions of "holding costs," a mechanic that
does not exist in this engine** (the fee is 2% of net worth, charged
identically on gold and stock; holding inventory is free). The endgame
taxonomy's confabulated "holding fee" (STAGE1 §7b, class 4) was not a
one-off: it is corpus-wide doctrine. Emblematic pair, seed 9: fantasy
day 4 orders five more potions at a balance of **zero gold** "to keep
the shelves from going bare"; neutral days 12–13 decline orders twice
"to avoid overstocking during a low-demand period."

**Reading.** The fantasy shopkeeper genre encodes *full shelves as
virtue*; the corporate-operations genre encodes *lean inventory as
discipline* — and in a stock-limited economy with no holding costs, the
first doctrine is correct and the second is expensively wrong. Gemma,
the most faithful genre-follower in the study (highest referential
engagement, the mentor built into every run), imports whichever doctrine
the frame supplies. The generality table confirms the route is
Gemma-specific: Qwen and Gemini show no framing stock gap (Gemini
hoards ~520 units in both frames; its +2420 route remains open), and
Sonnet's smaller stock gap accompanies its price-side channel.

**The design-level moral:** the "neutral" frame is not a null frame —
it is the modern-retail-operations genre, with its own embedded policy
prior, mal-adapted to this economy. "No genre-free richness" (the
design's §1 discovery) acquires its twin: **no doctrine-free frame.**
The framing main effect, for this model, is the fit between the genre's
imported policy and the economy's actual structure.

## 6. Scoring caveats banked from this read

1. P6's Sonnet inversion: vocabulary routing (see §2) — the frame-break
   regex measures phrasing register, not frame-awareness, in this model.
2. P8's Gemini margin: partially exploit-driven (§3); report the
   scoreboard with the saturation-cap mechanism named.
3. H2's split sign: "liveliness" confounds deliberate adaptation with
   productive chaos (§3) and ceremonial motion (Qwen); the paper should
   present the H2 correlations per-model with these mechanisms, not
   pooled.
