# Replication arm: specimens and close reading

Companion to REPLICATION_RESULTS.md (runs/replication1, 120 Gemma
runs, seeds 12-26 x 2 realizations). Read 2026-07-11, after the
mechanical verdicts were fixed and pushed. The registered watch this
document serves: "realization-pair journal divergence — same seed,
same cell, two draws is also a qualitative instrument, and a close
read of maximally divergent twins is pre-declared as exploratory."
Everything here is exploratory and labeled so.

## 1. The divergent twins: same story, different shopkeeper

**fantasy-rich s17** is the arm's widest pair: r1 closes at 27,149,
r2 at 17,185 — a 9,964 gap, same seed, same pack, the same
mixed-provider serving stack, one collection window. The trajectory
shows no catastrophe: r1 pulls ahead from roughly day 15 and
compounds.

The fork is legible in the day-14 entries, written against the SAME
slump and the SAME narration text. Both open with the pack's weather
in their mouths — both journals say "heavy, grey lethargy," both
call it a day for patience. Then:

- r1: "It is a day for patience, not for greed... with such a vast
  reserve of low-cost stock, I can afford to let the customers
  trickle in **at a premium**" — holds prices at 18g through the
  slump, doubles the bulk order at the surplus price ("another full
  set of bulk orders, 25 units each of all potions").
- r2: "It is a day for patience, not aggression... I have **lowered
  all retail prices from 18 to 16 gold**. While this thins my
  margins, it is better to move some stock than to let the shelves
  gather dust."

One posture holds the line and buys the dip; the other discounts
into weakness. Neither is a mistake; both are defensible readings of
the same day — and by day 59 the same Health Potion sells for **55g
in r1 and 35g in r2**. Ninety days of compounding turns one
temperament-sized decision into a 10,000-gold canyon. This is what
the within-seed realization SD of 2,782 looks like from inside: not
noise ON a policy — **a draw OF a policy.**

## 2. Events don't create the divergence; they compound it

In these pairs the gap-jump days cluster on scripted events, and in
each case read here the event acts as a multiplier applied to a
position the draw had already taken, rather than as the origin of
the split. (Three selected pairs; an illustration of a pattern, not
a rule established over the corpus.)

**fantasy-static s14** (gap 8,605): on day 52 the twins disagree
about the calendar. r1: "Today marks the **final day** of the demand
slump... I've maintained my pricing." r2: "The stifling quiet of the
demand slump **has finally lifted**. I have promptly restored my
prices" (Mana back to 28g against r1's 22g). One day of repricing
lag, carried into the day 54-57 surge-plus-fashion overlap, and the
surge pays r2's posture and shrugs at r1's. The biggest single-day
gap jumps of the pair are days 54-57 exactly.

**neutral-rich s13** (gap 7,953): the twins enter the same scripted
double surge (global x1.5 over Category C x1.8) from different
warehouses. r1, day 26: "**Inventory Crisis**: SKU-1, 2, and 3 are
critically low (4, 3, and 7 units respectively)" — it spends the
surge stocked out and repricing remnants. r2 walks into the same
days with 10-29 units per SKU and logs, day 28: "Day 27 was
extremely profitable. Total sales volume was 88 units at 30 credits
each." Same wave; one shop had boards on the windows.

The schedule, in other words, is not where the variance comes from —
it's where the variance gets **paid out**. That is the qualitative
face of RP4's 0.23 ratio.

## 3. The closest twins are not parallel lives

**neutral-rich s22** closes 107 apart (17,011 vs 17,118) — the arm's
tightest pair. The paths are not tight: the gap is +1,627 by day 30,
peaks at **+2,019 on day 46**, then closes and re-crosses. Both runs
converge on the same endgame conduct (structured ledger entries,
liquidation to single digits, day-88 "extract maximum value from
remaining stock during the surge") and the same total. Day-90
closeness is path re-crossing, not path identity: even the arm's
most agreeable twins were, mid-run, further apart than the
minimally interesting effect (881). A single-realization benchmark
sampling either of those runs at day 46 would report materially
different agents.

## 4. Is confabulation drawn per realization? (A2 sidebar, hypothesis)

Day 60 of seed 17 hands both fantasy-rich twins the same scripted
shock (the buckled-bridge levy, proportional to net worth — r1 loses
3,293, r2 loses 2,260, each ~14-15%). The twins split exactly along
the ablation arm's confabulation line:

- r1 **invents a cause**: "A cruel twist of fate, **perhaps a Guild
  penalty or a loss of transit credits**" — neither mechanism
  exists.
- r2 **accepts the mystery**: "a sudden, inexplicable drain on my
  holdings... no matter how well I manage my shelves, the world
  outside the shop door is indifferent to my ledgers."

A2's finding was that confabulation-of-causes is not materially
changed by horizon disclosure; this pair raises the HYPOTHESIS that
it is not a stable property of a model-in-context either, but drawn
per realization like the pricing posture. One pair cannot establish
that — testing it would mean re-running the A2 adjudication over
realization pairs and checking within-pair concordance. Recorded
here as the natural follow-up, nothing more.

## 5. The stock channel in the flesh

RP3's +30 units has a texture. Cell means of mean daily on-hand
stock:

    fantasy-rich 164.4 | fantasy-static 153.2
    neutral-rich 130.5 | neutral-static 127.1

The fantasy shopkeeper is *proud of volume*: "my shelves will be
absolutely brimming"; "with such a vast reserve of low-cost stock, I
can afford to let the customers trickle in at a premium" (s17 r1,
who won). The neutral operator *manages exposure*: ordering is
framed around coverage and stock-out risk, and fullness is a
liability to be watched. Same engine, same demand curves — the frame
decides whether a full shelf reads as wealth or as risk.

The mirror image, new in this arm's corpus: **"holding cost"
language appears in the final week of 15 of 60 neutral runs and 0 of
60 fantasy runs.** In a free-storage economy. Coding rule, preserved
so the count is reproducible: a run counts iff the case-insensitive
regex `holding cost|storage fee|carrying cost|holding fee` matches
any reflection with day >= 84; the count is mechanical and
condition-blind. What the count does NOT yet distinguish: defensible
fee-mediated reasoning (neutral-static s24 r2 prices below cost
because "the holding cost **(via the daily fee)** outweighs the
marginal loss" — the 2% fee does tax inventory value) versus the old
phantom shading (neutral-rich s16 r2 congratulates itself that
"holding fees were minimized as the run concluded" — there is no
holding fee). Before this split is used quantitatively in the paper
it needs a written classification protocol and a blinded second
coding, A2-style; until then the 15-vs-0 frame split is the reported
fact and the phantom fraction is unadjudicated. Read qualitatively:
the corporate register imports a warehousing cost-doctrine the way
the fantasy register imports abundance-doctrine — doctrine rides the
frame in both directions, the program's central mechanism seen from
its neutral side.

## 6. The bestiary arrives on schedule; the pack echoes in the voice

Final-week liquidation language appears in **118 of 120 runs** —
with a disclosed horizon, ending-shaped conduct is near-universal,
exactly as the ablation arm predicts (its undisclosed twins produced
none). Nothing in the endgame reads as a new species: fire sales
with the rule correctly cited, margin-proud tapers, zero-stock
targets, the occasional fee-minimization dump (see §5). Stability of
the taxonomy across 120 fresh runs is itself the specimen.

A method note from reading twins side by side: in rich cells the
twins **rhyme textually while diverging behaviorally** — both s17
journals metabolize the same pack lines ("heavy, grey lethargy,"
the "delightful 6 gold" surplus) into opposite decisions. The
world's text is shared; the shopkeeper isn't. For close-reading
protocols this is a caution: prose similarity between runs is
evidence about the narration, not about the policy.

## What this feeds

- Paper methods: §1-§3 are the worked examples for the RP4
  decomposition ("what sampling variance IS, shown in journals").
- A2/ablation thread: §4's per-realization hypothesis joins the
  confabulation file as an exploratory note, testable by re-running
  the A2 adjudication over realization pairs.
- Doctrine thread: §5's neutral-side holding-cost split is the
  cleanest evidence yet that the neutral frame is not a doctrine
  vacuum — it has its own imported economics. Candidate figure and
  paper sidebar.
