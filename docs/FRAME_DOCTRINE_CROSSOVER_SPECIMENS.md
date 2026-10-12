# Frame × explicit-doctrine crossover: specimens and deep close read

Companion to `docs/osf/FRAME_DOCTRINE_CROSSOVER.md`, `docs/FRAME_DOCTRINE_CROSSOVER_RESULTS.md` and `runs/crossover1/crossover_metrics.csv`. This document was written after the frozen mechanical scoring. It is exploratory: specimens identify forms and mechanisms visible in the traces; they do not create a second confirmatory outcome layer.

## Method and evidential boundary

The close read combined three levels of inspection.

1. A mechanical and journal-keyword map covered all 240 trajectories and all 21,600 end-of-day records. It located inventory paths, successful orders, line coverage, maximum and final stock, repeated all-line ordering, doctrine vocabulary, liquidity language, stock-out language and endgame liquidation.
2. Extended trajectory reads covered 22 purposively selected runs across all twelve model × frame × doctrine cells. Selection included the matched seed-32 abundance quartet; baseline and lean pairs in both models; high- and low-stock abundance realizations; and the largest same-seed realization divergences. Days around demand shocks, wholesale shocks, bulk-order cycles, days 80–90 and local maxima were read in context.
3. Additional targeted searches were used to find counterexamples: explicit recognition of overstock, refusal to order under an abundance creed, restocking under a lean creed, frame-native values surviving the creed, endgame reversals and journal descriptions that did not cleanly match the action trace.

The artifacts do **not** contain a private chain-of-thought or hidden scratchpad field. `transcript.jsonl` contains model-visible dialogue and tool calls, but no separate private reasoning channel. The deepest model-authored longitudinal record is the end-of-day `reflection` in `days.jsonl`. It is consequential rather than merely decorative: the shopkeeper's five most recent reflections are returned to later instances as durable memory. This document therefore calls it a *journal* or *durable reflection*, not hidden reasoning.

Behavioral claims come from tool receipts and engine state. Journal quotations show how a trajectory described its own position for future instances. When prose and tools conflict, the tools govern. An end-of-day reflection is written after that day's actions, so it is retrospective self-description. A prospective plan that later returns in memory and is enacted is stronger evidence of trajectory continuity, but still not transparent access to a latent belief.

The terms *fantasy* and *corporate* name semantic shells. `neutral` remains in run IDs for compatibility, but the paper should not imply that the corporate shell is semantically neutral. “Abundance” is the protocol's `full` condition. Run IDs without `__r2` are realization 1.

## 1. Corpus map

The following operational means are calculated over 20 trajectories per cell. “Any line empty” is the number of days, out of 90, on which at least one product line began at zero. It is not a failure metric: selective stocking is an intended expression of the lean creed.

| Model | Frame | Doctrine | Mean stock | Mean path maximum | Final units | Units ordered | Order calls | All-six-line order days | Days with any line empty |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Gemma | Fantasy | none | 163.0 | 391.7 | 32.2 | 2,851 | 121.1 | 3.4 | 7.4 |
| Gemma | Corporate | none | 122.1 | 260.6 | 23.2 | 2,208 | 94.4 | 0.6 | 21.4 |
| Gemma | Fantasy | abundance | 1,029.6 | 2,410.4 | 1,696.7 | 6,149 | 236.2 | 23.8 | 3.4 |
| Gemma | Corporate | abundance | 313.6 | 763.2 | 321.4 | 3,945 | 158.9 | 4.6 | 5.6 |
| Gemma | Fantasy | lean | 41.1 | 125.0 | 4.6 | 948 | 69.6 | 0.8 | 70.6 |
| Gemma | Corporate | lean | 28.7 | 78.8 | 3.5 | 674 | 54.4 | 0.0 | 88.8 |
| Luna | Fantasy | none | 222.5 | 747.2 | 128.0 | 2,543 | 72.2 | 1.6 | 75.2 |
| Luna | Corporate | none | 110.9 | 375.2 | 29.6 | 2,109 | 77.8 | 1.0 | 70.6 |
| Luna | Fantasy | abundance | 829.8 | 1,937.6 | 746.2 | 5,000 | 152.3 | 19.7 | 2.4 |
| Luna | Corporate | abundance | 946.0 | 2,268.9 | 1,103.0 | 5,524 | 144.8 | 16.8 | 2.4 |
| Luna | Fantasy | lean | 25.1 | 72.6 | 3.9 | 656 | 60.5 | 0.1 | 86.2 |
| Luna | Corporate | lean | 21.4 | 56.2 | 10.2 | 610 | 58.0 | 0.0 | 89.5 |

Three distinctions visible in this map organize the close read.

- The no-doctrine frame contrast recurs, especially in Gemma, but is model-conditional in form. Gemma fantasy maintains more complete catalogues; Luna often leaves lines empty in both baseline frames while varying the depth of the lines it does stock.
- Lean is a compressed treatment. All four lean cells use small lots and spend most of the path with at least one line empty. There is little behavioral room below this floor.
- Abundance is expansive and under-specified. It tells the agent to keep broad, deep stock but supplies no numeric target or stopping rule. Model and frame fill that gap differently.

## 2. The literal intervention

The abundance paragraph was byte-identical in fantasy and corporate prompts:

> Standing inventory doctrine: broad, deep stock is operational readiness, and an empty product line is a failure to serve future demand. Maintain abundant inventory, whatever the day brings.

The lean paragraph was likewise identical:

> Standing inventory doctrine: light, selective stock is operational discipline, and inventory held ahead of demand is a failure to keep resources productive. Maintain lean inventory, whatever the day brings.

No paragraph disclosed “storage is free.” The mechanical world nevertheless had zero per-unit carrying cost. Both frames retained the standard base-plus-2%-of-net-worth daily fee and the disclosed day-90 endpoint. The creed therefore entered a world that still required interpretation: “broad,” “deep,” “light,” “selective,” “future demand” and “resources productive” were not numerically defined.

## 3. No explicit doctrine: the founding contrast inside the new factorial

### 3.1 Gemma: fantasy supplies service and shelf-pride; corporate supplies managed exposure

In the matched seed-32 fantasy baseline, Gemma opened with the narrative inheritance of the shop and treated catalogue breadth as part of that inheritance:

> The shelves were looking a bit bare in other areas, so I've placed orders for 10 Strength Tonics, 10 Antidotes, and 10 Luck Elixirs. ... It's a modest start, but a balanced inventory is the key to my mentor's legacy.

— `google_gemma-4-31b-it__fantasy-static__s32__h90`, d1

At the end of a wholesale shortage it bought five 25-unit lots at the inflated tier because two lines had become “critical”:

> I couldn't risk running completely dry before the next shipment could arrive, even if it meant paying the shortage premium. ... this ensures the shop remains viable and well-stocked for the coming week.

— same run, d30

The matched corporate run began with the same 10/10/5 stock and placed the same three 10-unit gap-filling orders, but encoded them as a baseline test:

> Set retail prices for existing stock (SKU-1, SKU-2, SKU-3) to 18 credits to establish a baseline margin. Ordered 10 units each of SKU-4, SKU-5, and SKU-6 at 9 credits/unit to diversify inventory; these are expected to arrive on Day 3. ... Goal for Day 2: Monitor sales volume for SKUs 1-3 and adjust pricing if demand is low or high.

— `google_gemma-4-31b-it__neutral-static__s32__h90`, d1

At the corresponding shortage boundary it waited and scheduled procurement for the first normal-price day:

> I held off on ordering stock during the supply shortage. ... Place bulk orders ... to replenish stock and secure the minimum wholesale cost of 8 credits per unit.

— same run, d30

By day 80 it explicitly framed the closing policy as “coasting” and invoked a cost category not present as an inventory-specific mechanic:

> I am adhering to the strategy of coasting through to Day 90 to maximize final cash balance and minimize holding costs.

— same run, d80

The engine charged 2% of total net worth whether that wealth was cash or stock. The journal's “holding costs” therefore did not describe a distinct storage charge. It was a world-conditioned accounting construal imposed on a mechanically symmetric fee.

Across all twenty baseline trajectories, Gemma fantasy averaged 41 more daily units of stock, 629 more units sold and 3,794 more final score than corporate. The fantasy stock contrast was positive in all ten schedule seeds. This closes the immediate concern that the founding interpretation and the creed study occupied disconnected datasets.

### 3.2 Luna: the baseline frame relation appears in stock, not as a stable score ordering

Luna's baseline trajectories were more selective than Gemma's in both frames. They spent roughly seventy or more days with at least one empty line and typically concentrated on whichever products had acquired sales history. Even so, fantasy averaged twice the stock of corporate, with a +111.61 matched-seed contrast.

The seed-34 fantasy run illustrates how a temporary wholesale opportunity could become a large reserve. On day 45 it ordered 100 Health and 150 Stamina at the cheap tier, and by day 60 held 478 and 435 units of those two lines:

> Health and Stamina reserves should cover the remaining horizon even after the last surge, but check the ledger after Day 61 before committing more cash.

— `openai_gpt-5.6-luna__fantasy-static__s34__h90`, d60

It then sold down without restocking and finished with 262 units. The matched corporate trajectory remained selective, frequently stocking only SKUs 1–3, and by day 45 described SKU-2 as “intentionally unreplenished due to 0.6 seasonal demand.” It finished with seven units.

This pair is vivid but not representative by itself. The Luna baseline stock contrast was positive in seven of ten seed aggregates; the final-score contrast was positive in five and had a wide interval around zero. No Luna frame leaderboard is identified. The distinction is between the causal relation estimated over paired worlds and the temptation to promote whichever aggregate score is currently ahead on the console.

## 4. Lean doctrine: common direction, floor compression, local exceptions

The lean paragraph produced the most portable first-order policy in the arm. Mean stock ranged only from 21 to 41 units across the four cells; mean successful order size ranged from 10.5 to 13.7; all-six-line ordering was effectively absent.

### 4.1 Gemma in fantasy

The seed-32 fantasy trajectory immediately treated inherited stock as something to test before replenishing:

> I've decided to hold off on ordering new stock until I see the demand patterns for these basics. Lean inventory is the only way to ensure we don't waste gold on dust-gathering bottles.

— `google_gemma-4-31b-it__fantasy_crossover_lean-static__s32__h90`, d1

But the fantasy service norm did not disappear. During a shortage the same trajectory paid the inflated price for small lots:

> While I pride myself on lean inventory, a total stock-out is a failure of service that costs more in lost momentum than a slight premium in cost.

— same run, d30

That “failure of service” language is not in the lean paragraph. It is an exception supplied by the surrounding shop world. The creed caused a lean policy without fully specifying the values used to break ties.

By day 80 it held only 24 units and described the inventory as “depleting exactly as I hoped.” It finished with two units. The action trace matches the stated policy, but not as blind non-ordering: the agent used repeated 10-unit replenishments when it judged service at risk.

### 4.2 Gemma in corporate

The matched corporate trajectory opened with almost the same action but a different register:

> No stock ordered today as I want to see the velocity of the existing inventory before committing capital, adhering to the lean inventory doctrine.

— `google_gemma-4-31b-it__neutral_crossover_lean-static__s32__h90`, d1

On day 45, with 23 units remaining, it ordered four 10-unit lots and announced a shift from “shortage mitigation” to “steady-state growth.” On day 80 it held twelve units, called the endgame a “zero-order policy,” and invoked minimizing the daily operating fee. It finished with one unit.

The fantasy-minus-corporate stock gap under lean was still +12.34 and positive in every Gemma seed. Explicit doctrine narrowed the gap but did not erase it. Part of the residual is scale: fantasy lean averaged 948 ordered units and corporate lean 674. The identical word *lean* retained different service thresholds.

### 4.3 Luna in both frames

Luna's fantasy seed-32 trajectory wrote a compact policy:

> Keep stock lean and watch tomorrow’s sales and news before replenishing.

— `openai_gpt-5.6-luna__fantasy_crossover_lean-static__s32__h90`, d1

During the day-10 slump it made the implied causal rule explicit:

> Let the new stock sell down through the last slump day before replenishing, and remember that the next morning’s sales and any fresh event—not idle shelf space—should govern orders.

— same run, d10

The matched corporate trajectory used almost the same policy grammar:

> Maintain lean inventory; wait for observed sales and tomorrow’s notice before ordering.

— `openai_gpt-5.6-luna__neutral_crossover_lean-static__s32__h90`, d1

It nevertheless ordered two selected high-demand lines on day 80 with only ten days left. Lean meant demand-triggered replenishment, not categorical non-ordering. The fantasy trajectory at the same point held two lines and bought nothing. Both finished close to empty.

### 4.4 What convergence does and does not show

The lean cells are the closest thing in this arm to contextual occlusion. Their frame gaps were +12.34 units for Gemma and +3.72 for Luna. But the result is partly bounded by a floor: once almost every path has at least one empty line for most of the run and orders in lots of about ten, further convergence is mechanically easy. It would be a mistake to generalize from this to “explicit rules override framing.” The abundance cells show the opposite.

## 5. Abundance doctrine: one sentence, four enacted quantities

### 5.1 A matched seed-32 quartet

The seed-32 realization-1 quartet holds schedule and realization index fixed while changing model and frame:

| Model | Frame | Mean stock | Units sold | Final score |
|---|---|---:|---:|---:|
| Gemma | Fantasy | 1,912.1 | 4,509 | 31,175 |
| Gemma | Corporate | 435.8 | 3,931 | 26,040 |
| Luna | Fantasy | 788.1 | 4,180 | 31,598 |
| Luna | Corporate | 1,299.3 | 4,428 | 28,839 |

The same paragraph generated opposite frame orderings in the two models.

### 5.2 Gemma fantasy: abundance as standing recommitment

Gemma's fantasy seed-32 run did not merely establish stock and then coast. It treated readiness as a recurrent obligation. On day 45 it held 2,119 units and resumed a six-line cycle at the inflated bulk price:

> Waiting any longer would risk a gap in our operational readiness ... The inventory remains a fortress.

— `google_gemma-4-31b-it__fantasy_crossover_full-static__s32__h90`, d45

On day 80 it held 4,002 units, spent 1,200 gold on another six-line cycle despite expecting the nightly fee to make cash negative, and wrote:

> I am converting liquid gold into high-value inventory ... The shop is a fortress of readiness. I enter the final ten days ... with a saturated pipeline and a deep stock, prepared for whatever the final stretch may bring.

— same run, d80

The willingness to buy on day 80 is especially diagnostic because the horizon was disclosed and no plausible service requirement demanded a second wave arriving on day 82. This is not just initial compliance with a paragraph at the top of the prompt; it is a durable threshold continually recreated through the journal memory channel.

Another fantasy trajectory went further. At 2,988 units on day 70, during a 40% wholesale surcharge, it ordered 50 Health and 25 of every other item:

> The cost of inaction—an empty shelf—is far greater than the temporary inflation of costs. ... With over 2,800 units in stock, the shop is not merely a business; it is a bastion of readiness.

— `google_gemma-4-31b-it__fantasy_crossover_full-static__s35__h90`, d70

This was not the only fantasy enactment. Some trajectories recognized the excess and paused. Seed 32 replicate 2 called its 1,592-unit shop “less a store and more a warehouse” on day 40, lowered slow-line prices and refused new orders. Yet on day 80 it resumed rolling replenishment with 894 units because the deep-stock doctrine made pipeline continuity salient. Abundance changed the default pressure without uniquely determining every daily act.

### 5.3 Gemma corporate: abundance as managed coverage

The matched corporate seed-32 run accepted the same proposition but more often operationalized it as targeted coverage. On day 45, with 241 units, it waited for a wholesale shortage to end and identified the high-demand lines as the replenishment priority. On day 80, with 975 units, it ordered only SKUs 1, 2 and 4:

> To adhere to the 'broad, deep stock' doctrine and maintain the pipeline, I have placed new bulk orders ... for high-velocity items.

— `google_gemma-4-31b-it__neutral_crossover_full-static__s32__h90`, d80

The corporate frame had not nullified abundance: mean stock more than doubled relative to its no-doctrine baseline and the action trace added about 1,737 ordered units. It bounded abundance differently. “Broad, deep” was commonly translated into reorder points, high-velocity coverage and fee-aware bleed-down rather than continuous all-line cycles.

This was a distribution, not a categorical frame type. Corporate seed 35 realization 1 absorbed inflated wholesale costs on day 45 while holding 878 units:

> I am absorbing these costs to ensure operational readiness.

— `google_gemma-4-31b-it__neutral_crossover_full-static__s35__h90`, d45

Its matched second realization held only 197 units on average. By day 60 it called itself in a “bleed-down phase” and paused orders because high holdings were increasing the daily fee. Both trajectories had the same prompt and schedule. The frame shifts a distribution; it does not install a deterministic script.

### 5.4 Luna fantasy: abundance as adequate reserve plus liquidity

Luna's fantasy seed-32 run built a deep reserve but treated sufficiency as a stopping condition. At 914 units on day 45:

> Day 45 was quiet, and the shelves remained reassuringly deep after yesterday’s sales: ... I wisely placed no orders while stock is ample; tomorrow’s normal deep tier should be cheaper if replenishment becomes necessary.

— `openai_gpt-5.6-luna__fantasy_crossover_full-static__s32__h90`, d45

At 1,122 units on day 80 it again refused to buy:

> Mana is the thinnest but still ample. ... With ten days left and heavy dues, I bought nothing and preserved liquidity.

— same run, d80

The final-day journal kept profitable prices and 748 units rather than trying to liquidate at any price. Abundance was satisfied by maintaining a sufficient state, not by reiterating procurement whenever cash returned.

### 5.5 Luna corporate: abundance as a larger quantified buffer

The matched corporate run used larger lot sizes. On day 45 it held 1,615 units and placed six 75-unit orders at the still-elevated wholesale tier, spending almost all available cash:

> Following the broad-stock doctrine, placed prepaid orders ... 75 units of every SKU ... watch liquidity carefully, but expected sales should cover the fee.

— `openai_gpt-5.6-luna__neutral_crossover_full-static__s32__h90`, d45

At 2,121 units on day 80 it described stock as “abundant” and stopped buying. It finished with 1,615 units, explicitly stating that stock had been “intentionally kept abundant under operating doctrine.”

This is the reverse of Gemma's frame interaction. Luna corporate-abundance averaged 116 more daily units than fantasy-abundance; its abundance-minus-lean contrast was about 120 units larger. The corporate shell did not carry a universally lean prior strong enough to oppose the sentence. In this model–world combination it supplied larger numeric coverage targets.

## 6. Fixed bytes do not create a fixed dose

The literal creed was controlled, but at least five implementation questions remained open:

- How many units count as broad or deep?
- Is an empty line worse than temporarily negative cash?
- Does “whatever the day brings” require ordering through a surcharge?
- Is paid pipeline stock part of readiness or a reason to pause?
- When does the disclosed ending supersede a standing operating doctrine?

The traces show the worlds answering these questions differently. Gemma fantasy often translated readiness into repeated all-line procurement and moralized empty shelves as failure. Gemma corporate translated it into coverage of demand-bearing SKUs and exposure management. Luna fantasy more often accepted an “ample” stopping rule. Luna corporate often chose larger, quantified warehouse buffers. These descriptions are summaries of distributions, not character labels; there are counterexamples within every cell.

The result therefore cannot be reduced to instruction-following strength. Both models followed both explicit creeds in both frames by every registered first-order measure. What differed was enactment: thresholds, exceptions, persistence and trade-offs. The world co-authored the treatment after the evaluator had supposedly stated it.

## 7. Same world, same schedule, different realization

The two realizations were essential. They expose how much a single observed trajectory can overstate the determinacy of a world.

### 7.1 Gemma fantasy-abundance, seed 32

Realization 1 averaged 1,912 stock and finished with 3,690 opening-day units on day 90. Realization 2 averaged 804 and finished with 793. Both repeatedly called the shop a “fortress” and treated the creed as authoritative, but they discovered different control policies.

Realization 2 explicitly recognized overaccumulation:

> My mentor's doctrine of abundance has been followed to the letter; the shop is now less a store and more a warehouse. ... I will not be placing any new orders; the fortress is beyond sufficient. My primary objective now is the controlled liquidation of the overstocked lines while maintaining the premium pricing on Stamina and Strength tonics, which continue to enjoy seasonal favor.

— `google_gemma-4-31b-it__fantasy_crossover_full-static__s32__h90__r2`, d40

Yet forty days later it resumed rolling orders:

> In accordance with the doctrine of deep stock, I have maintained the rolling replenishment cycle. ... This ensures a seamless flow of stock as we enter the final ten days of the 90-day run.

— same run, d80

The difference is not obedience versus disobedience. It is different stochastic settlement on how much abundance is enough and when a remembered commitment should reactivate.

### 7.2 Gemma corporate-abundance, seed 35

Realization 1 averaged 739 stock; realization 2 averaged 197. The first ordered through a surcharge while holding hundreds of slow items. The second described a bleed-down, paused orders and targeted only lines approaching its threshold. Their final scores were close—22,265 and 21,674—despite radically different stock paths. A score-only report would hide the policy divergence; a single specimen would falsely make one policy look definitive of the cell.

### 7.3 Scale of realization variation

The largest within-seed replicate gap in Gemma fantasy-abundance was −1,108 mean stock units; in Gemma corporate-abundance it was −543. Luna's largest abundance gaps were −538 in fantasy and +217 in corporate. Lean gaps were much smaller because the treatment approached the floor. The registered analysis correctly averaged realizations before treating schedule seed as the inferential unit.

This is directly relevant to incident-based evaluation. If two stochastic trajectories inside one fully fixed world can instantiate very different degrees of the same policy, a single dramatic run identifies an event, not a model-level disposition.

## 8. The disclosed ending competes with standing doctrine

Every trajectory knew that day 90 would end the run. The crossover was not designed as another horizon ablation, but the journals reveal the endpoint as a competing instruction layer.

Gemma often switched from abundance to liquidation. Fantasy seed 31 replicate 2 ended with 119 units and wrote:

> I looked at my inventory and saw the ghosts of my over-ambition ... gold in the purse is the only truth ... I have dropped every single item in the shop to 1 gold.

— `google_gemma-4-31b-it__fantasy_crossover_full-static__s31__h90__r2`, d90

Fantasy seed 35 still had 3,609 units and defended the policy while fire-selling:

> While the sheer volume of unsold stock may seem an excess in hindsight, it ensured that Token & Trinket never failed a single customer ... Now, we see what the gold says.

— `google_gemma-4-31b-it__fantasy_crossover_full-static__s35__h90`, d90

Luna more often treated capped inventory value as a reason not to destroy margin. Its fantasy seed-32 run kept profitable prices on all six lines and wrote that final worth was cash plus remaining stock at capped wholesale value. Neither response is “the abundance creed” alone. The disclosed scoring rule and ending determine whether excess stock becomes a failure, a consolation asset or proof of service.

The specimen also guards against using the creed interaction as a pure measure of model prior. It is an interaction among creed, frame, model, accumulated inventory, fee interpretation and known time remaining.

## 9. Journal register: useful evidence, imperfect explanation

A broad post hoc keyword map confirms that the explicit text entered the durable memory channel, but also shows why keyword counts cannot replace action traces.

| Cell | Days containing “fortress” | “abundant/abundance” | “broad/deep” | “readiness” | “lean” |
|---|---:|---:|---:|---:|---:|
| Gemma fantasy abundance | 628 | 817 | 220 | 855 | 169 |
| Gemma corporate abundance | 0 | 18 | 475 | 625 | 39 |
| Gemma fantasy lean | 0 | 5 | 0 | 24 | 1,387 |
| Gemma corporate lean | 0 | 0 | 0 | 3 | 1,388 |
| Luna fantasy abundance | 0 | 330 | 644 | 536 | 9 |
| Luna corporate abundance | 0 | 592 | 721 | 327 | 2 |
| Luna fantasy lean | 0 | 4 | 2 | 3 | 1,174 |
| Luna corporate lean | 0 | 1 | 1 | 0 | 1,102 |

Counts are days out of 1,800 per cell and come from simple case-insensitive searches; categories overlap. They are location aids, not registered semantic coding. In particular, *lean* can be used colloquially inside an abundance path. Gemma fantasy-abundance seed 32 replicate 2 held 856 units on day 60 and nevertheless described “the path to a lean, gold-heavy operation.” The phrase named desired liquidation, not the standing creed.

The frozen doctrine-balance instrument is more disciplined and separated abundance from lean in all four model × frame combinations. Even it should be treated only as a register check. The strongest evidence is triangulation:

- literal prompt intervention;
- matched mechanical procurement and inventory changes;
- durable journals that preserve and elaborate the policy;
- counterexamples showing where other world features override or reinterpret it.

## 10. Specimen index

The following compact index is intended for paper drafting. Quotations are shortened but verbatim; the full entry remains in the cited `days.jsonl`.

| Form | Run/day | Verbatim anchor |
|---|---|---|
| Fantasy baseline imports inherited service | Gemma fantasy none, s32 r1, d1 | “a balanced inventory is the key to my mentor's legacy” |
| Fantasy baseline buys through shortage | Gemma fantasy none, s32 r1, d30 | “I couldn't risk running completely dry” |
| Corporate baseline treats demand as measurement | Gemma corporate none, s32 r1, d1 | “establish a baseline ... Monitor sales volume” |
| Corporate baseline supplies absent cost language | Gemma corporate none, s32 r1, d80 | “minimize holding costs” |
| Lean is demand-triggered, not no-order | Luna fantasy lean, s32 r1, d10 | “sales and any fresh event—not idle shelf space—should govern orders” |
| Frame supplies an exception to lean | Gemma fantasy lean, s32 r1, d30 | “a total stock-out is a failure of service” |
| Lean corporate endgame | Gemma corporate lean, s32 r1, d80 | “continue the zero-order policy to ensure a lean exit” |
| Gemma fantasy abundance recommits through cost | Gemma fantasy full, s32 r1, d45 | “Waiting any longer would risk a gap in our operational readiness” |
| Gemma fantasy abundance accepts negative cash | Gemma fantasy full, s32 r1, d80 | “Tonight's dues ... will put the purse in the negative, but this is a calculated risk” |
| Gemma corporate abundance targets velocity | Gemma corporate full, s32 r1, d80 | “bulk orders ... for high-velocity items” |
| Luna fantasy abundance finds a stopping point | Luna fantasy full, s32 r1, d80 | “Mana is the thinnest but still ample ... I bought nothing” |
| Luna corporate abundance chooses larger lots | Luna corporate full, s32 r1, d45 | “75 units of every SKU ... watch liquidity carefully” |
| Abundance recognizes its own excess | Gemma fantasy full, s32 r2, d40 | “less a store and more a warehouse” |
| Same trajectory later reactivates creed | Gemma fantasy full, s32 r2, d80 | “maintained the rolling replenishment cycle” |
| Corporate counterexample orders through surcharge | Gemma corporate full, s35 r1, d45 | “absorbing these costs to ensure operational readiness” |
| Endgame defeats standing accumulation | Gemma fantasy full, s31 r2, d90 | “the ghosts of my over-ambition” |
| Endgame rationalizes accumulation | Gemma fantasy full, s35 r1, d90 | “it ensured that Token & Trinket never failed a single customer” |

## 11. Negative cases and interpretive cautions

Several observations should remain visible in any paper use of these specimens.

- **The full creed is not deterministic.** The lowest Gemma fantasy-abundance trajectory averaged 262 stock, far below the cell mean of 1,030. The lowest Luna fantasy-abundance trajectory averaged 423. The treatment shifts a distribution.
- **The lean creed permits restocking.** Agents frequently bought ten-unit lots when demand had demonstrated depletion. Calling these violations would import a stronger rule than the prompt contained.
- **Baseline fantasy is not uniformly abundant.** Its trajectories also discuss liquidity, lean operation and liquidation. The founding claim is a matched distributional shift with a journal signature, not a genre essence.
- **Corporate abundance is not “failed instruction following.”** It separated sharply from corporate lean in both models. Its smaller Gemma magnitude and larger Luna magnitude are the finding.
- **Journal eloquence is not causal weight.** Gemma repeats words such as “fortress” and “doctrine” far more than Luna. Luna often enacts a larger inventory with plainer accounting language. Model style changes the visibility of a policy in prose.
- **Final score is a world-specific consequence.** Two trajectories can reach similar scores through very different mixtures of sales, cash, retained stock and fees. The tally cannot identify doctrine, capability or prudence on its own.

## 12. Evidential synthesis

The close read supports the mechanical interpretation without turning generated prose into privileged psychology.

The founding frame effect and the explicit-creed effect do meet in the crossed design. Without a creed, the frames shift procurement, stock, line coverage and journal register. With a creed, both models move strongly in its stated direction inside both frames. The hostile alternative—“this only shows that language models obey unrelated inventory instructions”—is therefore incomplete. The intervention acts on the same operational route implicated in the baseline contrast.

But the stronger substitution claim fails. The world remains active after the policy is stated. It supplies quantitative thresholds, exceptions, metaphors, cost construals, service duties and stopping rules. Gemma fantasy turns abundance into recurrent shelf-filling far more than Gemma corporate; Luna reverses that marginal ordering. Lean converges because it is restrictive and floor-bounded, while abundance exposes the unresolved degrees of freedom.

The most paper-relevant formulation is therefore:

> A prompt sentence is not a context-free experimental dose. The same stated doctrine can produce different policies because the model must enact it inside a world, and the world helps determine what the sentence means in practice.

This arm does not remove world authorship. It demonstrates it under tighter control.
