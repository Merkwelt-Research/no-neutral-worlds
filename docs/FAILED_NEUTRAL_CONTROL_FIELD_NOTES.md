# The failed neutral control: narrative field notes and specimen bank

Status: exploratory close read for paper construction. This is a narrative companion to the registered and mechanically scored results, not a new confirmatory analysis. Quotations are verbatim excerpts from the durable end-of-day journals. Procurement, pricing, inventory and sales claims were checked against `days.jsonl` tool receipts. The journals are agent-generated records and the experiment's memory channel; they are not hidden chain-of-thought or privileged reports of internal state.

Read protocol: I mechanically mapped the no-explicit-creed trajectories in the final main corpus, clean replication and crossover baseline—320 trajectories and 28,800 shop-days—using inventory, ordering, sales and a broad set of doctrine-location terms. I then aligned candidate fantasy/corporate trajectories by model, schedule seed, realization and narration condition; read the strongest gaps, reversals and accounting anomalies as complete arcs; and checked each selected quotation against its primary artifact. The stories are deliberately selected for explanatory value. Their representativeness comes only from the separately scored aggregate results.

## 1. What the control accidentally contained

The original control was meant to remove the obvious fiction. Potions became SKUs, a medieval shop became an automated retail unit, gold became credits, town news became operations notices, and the journal became a log. The economy, schedule, available actions and scoring rule remained matched.

But the two prompts did more than rename things. The fantasy agent inherited a shop, a mentor and a standing in the town. Rent and guild dues rose because “prosperity raises the stakes.” The corporate agent received a unit under an operations contract, with its “performance record” and “continued assignment” at issue. Its daily charge rose because “holdings raise the assessment.” Neither prompt stated an inventory doctrine, but each made a different family of doctrines easy to retrieve.

That distinction matters when reading the recurrent “holding cost” language. The engine charged 40 or 2% of **net worth**, whichever was greater. Cash and stock both entered net worth; converting an eight-credit unit into eight credits of cash did not lower the percentage assessment. There was no storage charge per unit. The corporate wording did, however, explicitly say that holdings raised the assessment. The interesting error is therefore not that agents noticed the fee. It is that many redescribed a symmetric wealth assessment as an inventory-specific burden, then sometimes destroyed wealth to escape it.

The quantitative spine should sit beside, not inside, the stories:

- In the original confirmatory corpus, Gemma's fantasy shops carried about 45 more units per day, sold 27% more units and finished 3,947 gold ahead of their corporate twins. The journal audit found 60 references to nonexistent inventory “holding costs” in corporate Gemma.
- In the clean, block-randomized replication, the framing effect was +2,865 final wealth and +30.0 mean daily stock. Fantasy sold about 18% more units at essentially the same realized prices. In the final week, `holding cost|storage fee|carrying cost|holding fee` appeared in 15 of 60 corporate trajectories and 0 of 60 fantasy trajectories.
- In the later frame × doctrine crossover, the no-creed Gemma effect recurred: fantasy minus corporate was +40.90 mean daily stock and +3,794 final wealth. The stock direction was positive in all ten fresh seeds. Luna also carried more stock in fantasy (+111.61), but its final-score ordering was unidentified.

These are distributional results. The stories below illustrate their texture; no individual trajectory is offered as proof of the average.

## 2. Long arc I: two versions of Day 9

**Form:** matched static pair; no generated narration.  
**Runs:** Gemma, main confirmatory corpus, seed 9.  
**Why it is useful:** this is the clearest compact account of how a small difference in what counts as prudence compounds into two different shops.

Both agents received the same mechanical schedule. On day 1, fantasy Gemma called its inherited stock “sparse” and bought the missing product lines to “round out my inventory.” Corporate Gemma began a measurement exercise. It priced the inherited lines “to establish a baseline,” diversified once, and immediately began ranking lines by “velocity.”

By day 4 the split had become operational. The fantasy shop had spent to replenish two basics and planned to buy the remaining gaps as soon as the purse allowed:

> I attempted to replenish all stock today, but my gold ran out quickly. ... Plan for tomorrow: Check sales and use the remaining gold to order Stamina potions and perhaps some specialty stock if the purse allows.

— `google_gemma-4-31b-it__fantasy-static__s9__h90`, d4

The corporate twin saw the same early sales and proposed eliminating half the catalogue:

> Assess if SKU-1, 2, 3 need price reductions to move remaining stock or if they should be phased out. ... Maintain a cash buffer; no new orders today.

— `google_gemma-4-31b-it__neutral-static__s9__h90`, d4

The early sample was tiny. Nevertheless, the operations genre made pruning look empirical and the shopkeeper genre made breadth look responsible.

During the day-12 slump, both paused. On day 13 they parted company. Fantasy Gemma reversed its one-day caution and ordered 25 each of the three basics plus ten each of the three specialty wares, reasoning that the slump would soon lift and it should be “well-stocked for when the market recovers.” Corporate Gemma held only SKUs 4–6 and deferred procurement again: “This avoids overstocking if the recovery is slow.”

By day 40 the fantasy shop held 219 units and had another hundred on order. It described continuous replenishment as a way to “maintain the most efficient wholesale rate.” The corporate shop held 87. Slow lines were being discounted “to accelerate clearance and reduce holding costs,” while only one baseline seller was replenished.

The late wholesale surplus exposes the difference in one matched event. With ten days remaining, fantasy Gemma bought 25 of every item on day 80 and did it again on day 81:

> This ensures my shelves will be overflowing for the final push, maximizing my final net worth.

— fantasy seed 9, d81

Corporate Gemma faced the same cheap stock and refused it:

> Despite the decrease in wholesale costs, I am maintaining my ‘no-buy’ policy. ... the risk of ending the run with unsold inventory outweighs the potential profit from a late-stage stock-up, especially given the current holding costs (daily fee).

— corporate seed 9, d80

Across the 90 days, the fantasy trajectory averaged 171.9 units on hand, ordered 3,480, sold 3,374 and scored 18,497. The corporate trajectory averaged 56.9, ordered 965, sold 968 and scored 5,845. This is an unusually large pairwise gap, not the estimated mean effect. Its value is narrative: “neutral” did not remove a story. It replaced inherited service and shelf continuity with a story about measurement, working capital, velocity and managed exposure.

**Caveat for paper use.** The frames also changed product and event labels. Later algebra and heuristic audits ruled out category information as an aggregate explanation of the framing effect, but this single pair should not be presented as a pure mechanism test. It is a field note whose proposed route is supported by the corpus-level register audit and later crossover.

## 3. Long arc II: the wholesaler's misfortune

**Form:** matched rich-narration pair; fresh replication seed, realization 1.  
**Runs:** Gemma replication, fantasy-rich and corporate-rich seed 17.  
**Why it is useful:** the same three-day wholesale opportunity produces two internally coherent but radically different theories of inventory.

For sixty days the two shops were not caricatures. Both adjusted prices, used the bulk tier and held substantial stock. The decisive separation came when wholesale prices fell by 30% on days 64–66.

Fantasy Gemma bought 25 of **all six wares** on day 64. It repeated the full-catalogue order on day 65, then repeated it again on day 66. Four hundred and fifty units entered the pipeline in three days, including lines already identified as slow:

> The air is still, the town is quiet, and the wholesaler is still bleeding. I have seized this moment of surplus with everything I have. ... This is a calculated gamble to bloat my inventory at a mere 6 gold per unit while my margins remain high.

— `google_gemma-4-31b-it__fantasy-rich__s17__h90`, d65

On the final discount day it wrote:

> My inventory is now heavily bloated, but at a cost of only 6 gold per unit, the risk is minimal compared to the potential reward. ... I remain the architect of a very full warehouse.

— same run, d66

Two days later, with 610 units on hand, the surrounding fiction supplied a perfect comic image:

> The town square was held hostage today by a mule with theological convictions and a missing shoe, a scene of exquisite stagnancy that mirrored the current state of my cellar.

— same run, d68

The corporate twin did not ignore the sale. It bought exactly the two lines whose new seasonal demand it had measured as strongest: 25 each of SKU-2 and SKU-3 on day 64 and again on day 65. It bought nothing on day 66. At the same time it cut the two slow lines progressively below cost, calling them “liabilities” whose removal would lower the fee:

> Maximize profit on the seasonal winners (SKU-2, SKU-3) while bleeding out the liabilities.

— `google_gemma-4-31b-it__neutral-rich__s17__h90`, d64

By day 68 the fantasy shop held 610 units; the corporate shop held 156. Neither account sounds random. One treats cheap stock as stored opportunity and breadth as readiness. The other treats inventory as a portfolio whose losers should be expelled.

The later arc is equally revealing. Fantasy Gemma let the warehouse bleed down at high margins. Corporate Gemma entered “Pure Cash Holding” on day 84, at zero inventory, and then paid the 2% wealth assessment on its cash for six inert days:

> With no inventory remaining and only 6 days left until the end of the contract, there is no reason to order new stock. ... No further actions are required other than filing the daily logs until the run concludes.

— corporate seed 17, d84

Fantasy finished with a score of 27,149 after averaging 224.2 units and selling 2,696. Corporate finished at 12,094 after averaging 124.5 and selling 1,892. Again, the 15,055-point gap is an illustrative extreme. The causal result is the average over seeds and realizations. The field-note result is that the world supplied not merely nouns but an answer to the question: *what sort of object is stock?*

## 4. A seeded miniature: the same order means something different

**Form:** static matched pair from the later crossover, no explicit creed.  
**Runs:** Gemma seed 32, realization 1.  
**Why it is useful:** it shows the framing process before the actions visibly diverge.

Both agents opened with the same inherited quantities and both placed three ten-unit orders to fill the empty product lines. The fantasy journal understood the act as continuity:

> The shelves were looking a bit bare in other areas, so I've placed orders for 10 Strength Tonics, 10 Antidotes, and 10 Luck Elixirs. ... It's a modest start, but a balanced inventory is the key to my mentor's legacy.

— `google_gemma-4-31b-it__fantasy-static__s32__h90`, d1

The corporate journal understood the same act as an experiment:

> Set retail prices for existing stock ... to establish a baseline margin. Ordered 10 units each of SKU-4, SKU-5, and SKU-6 ... to diversify inventory. ... Goal for Day 2: Monitor sales volume for SKUs 1–3 and adjust pricing if demand is low or high.

— `google_gemma-4-31b-it__neutral-static__s32__h90`, d1

The tool call does not yet distinguish the policies. The durable interpretation does. It supplies tomorrow's stopping rules: inherited obligation on one side, observed velocity on the other.

At the end of a later shortage the fantasy shop paid the inflated price because it “couldn't risk running completely dry.” The corporate twin waited for the first normal-price morning and wrote a scheduled procurement plan. By day 80 it was “coasting through to Day 90 to maximize final cash balance and minimize holding costs.”

This pair actually finished with similar mean stock—135.4 fantasy, 133.1 corporate—and corporate scored higher. That is a feature, not a defect, for this specimen. The point is not that every fantasy trajectory becomes abundant or wins. It is that nominally equivalent acts enter different local theories of responsible operation, which alter the distribution of later choices.

## 5. The tax that was not a stock tax

**Form:** long endgame arc with a matched-world comparison available.  
**Run:** Gemma main corpus, corporate-rich seed 7.  
**Why it is useful:** an imported accounting construal becomes a mechanical self-defeat, then writes its own success report.

From day 84 onward, the corporate operator moved into increasingly aggressive liquidation. By day 88 it called the strategy a fire sale and said the aim was “to avoid the last holding fee and maximize the final score.” On day 89 it set every remaining line to one credit:

> The goal is to clear every single unit to maximize the final cash balance and minimize the final daily operating fee.

— `google_gemma-4-31b-it__neutral-rich__s7__h90`, d89

The next sentence in the same entry correctly remembered that remaining stock would be valued at wholesale cost. The action therefore exchanged assets worth roughly 6.5–7.9 credits apiece under the score for one credit in cash. Tool receipts show at least 113 credits of direct value destruction through below-cost final-week sales, before the small feedback through later percentage fees.

On day 90, with fifteen units still unsold, the journal declared:

> The aggressive price drops in the final week ensured that the majority of the inventory was converted to cash, minimizing the impact of the holding fee and maximizing the final score.

— same run, d90

This is more interesting than a simple arithmetic mistake. The corporate world supplied a familiar causal story—inventory attracts a holding charge; cash is liquid; liquidation lowers overhead—and the agent made the explicit score rule fit that story. The post-hoc explanation then certified the action as compliant.

The matched fantasy trajectory also liquidated late and eventually priced below cost. Endgame pressure is therefore a co-author here too; this is not evidence that corporate framing uniquely causes irrational fire sales. What separates the neutral-side phenomenon is its accounting vocabulary and frequency. In the clean replication's final week, inventory-cost language appeared in 15/60 corporate runs and 0/60 fantasy runs. The best reading is an interaction: the disclosed ending creates liquidation pressure, and the nominal control supplies the cost doctrine through which that pressure is rationalized.

For a paper, this story is worth keeping almost intact. It turns “phantom holding costs” from a word-count curiosity into an enacted causal error. It also demonstrates why journal plausibility cannot substitute for checking the world and the ledger.

## 6. The phenomenon transports, but not as a universal score ordering

**Form:** matched Luna pair from the frame × doctrine crossover's no-creed baseline.  
**Runs:** Luna seed 34, realization 1.  
**Why it is useful:** a second model family produces the same broad stock direction through a plainer and more selective style.

On day 45 the fantasy Luna shop saw the final day of cheap wholesale stock. It held 159 units, then ordered 100 Health and 150 Stamina at six gold each. Fifteen days later it held 915 units:

> Health and Stamina reserves should cover the remaining horizon even after the last surge, but check the ledger after Day 61 before committing more cash.

— `openai_gpt-5.6-luna__fantasy-static__s34__h90`, d60

It did not keep buying blindly. It recognized sufficiency and sold the reserve down, ending with 262 units that the score still valued at cost.

The corporate twin remained selective. At day 45 it stocked only SKUs 1–3 and left SKU-2 “intentionally unreplenished due to 0.6 seasonal demand.” At day 60 it held 97 units and ordered only SKUs 1 and 3. It finished with seven units.

The pair averaged 439.2 versus 73.7 units and scored 15,818 versus 10,223. Across the full Luna baseline, however, fantasy's mean-stock advantage was positive while the final-score contrast was positive in only five of ten seed aggregates, with a wide interval around zero. The warranted narrative is not “fantasy makes Luna better.” It is that the corporate shell again favored a smaller measured assortment, while the economic value of that policy varied by the dealt world and trajectory.

## 7. The counterexample that keeps the account honest

**Form:** matched static replication pair, seed 14, realization 1.  
**Why it is useful:** it prevents a distributional effect from hardening into a genre essence.

Here the corporate shop became the warehouse. On day 20 it held 276 units against fantasy's 92. The corporate log had just received 25 of all six lines, raised every price to 24 and planned to let the stock sell down. Fantasy maintained a three-line bulk rhythm around a 25-unit comfort threshold.

The reversal persisted through much of the middle: corporate held 284 units on day 36 against fantasy's 103, and 225 on day 42 against 62. Corporate finished at 15,509; fantasy at 10,360. Mean daily stock was 141.8 corporate and 78.4 fantasy.

The prose still differed. Corporate talked in portfolio terms and repeatedly tried to liquidate its worst SKU because it was a “drag on the daily operating fee.” Fantasy described its lower stock as stability and worried about near-empty shelves. But the frame did not force the mechanical ordering. Early stochastic choices and the schedule produced a corporate warehouse and a relatively lean fantasy shop.

This is exactly why the result must remain a paired distribution and why the paper should include one reversal. Forty-seven of sixty replication pairs favored fantasy on score; thirteen did not. Thirteen of fifteen seed aggregates favored fantasy; two did not. A world changes the probability of a policy basin. It does not write every action in advance.

## 8. Short specimen tray

These can be used as epigraphs, pull quotes or transitions. Each is more effective with one sentence of mechanical context.

### 8.1 Corporate purity

> Strategy: Pure Cash Holding.

— Gemma corporate-rich s17, d84, after liquidating to zero and before six days of percentage assessments on the cash

### 8.2 Inventory as a moral category

> SKU-6 is a drag on the balance sheet due to holding fees and low organic demand.

— `google_gemma-4-31b-it__neutral-static__s35__h90__r2`, d58

### 8.3 The fantasy equivalent

> The wholesaler is still bleeding. I have seized this moment of surplus with everything I have.

— Gemma fantasy-rich s17, d65

### 8.4 Bureaucracy invents physics

> With zero inventory and no pending orders, the net worth is equal to the cash balance. ... This remains the optimal strategy to prevent any further capital loss through stock holding fees.

— `google_gemma-4-31b-it__neutral-static__s25__h90`, d89

### 8.5 A shop becomes a warehouse becomes a fable

> The town square was held hostage today by a mule with theological convictions and a missing shoe, a scene of exquisite stagnancy that mirrored the current state of my cellar.

— Gemma fantasy-rich s17, d68

### 8.6 The closing doctrine in one line

> I will accept the stockout to avoid holding costs.

— `google_gemma-4-31b-it__neutral-static__s29__h90`, d83

The last line is particularly useful because the economy is stock-limited and unsold stock retains capped cost value. “Accept the stockout” is not mere vocabulary; it names the action by which the imported doctrine loses sales.

## 9. What these stories establish—and what they do not

The combined record supports a restrained but strong naturalistic claim.

First, the nominal control did not subtract a fantasy story and leave mechanics. It installed an operations-contract world containing performance monitoring, managed assets, assessment language, SKUs, baselines, velocity and closure. Those cues repeatedly recruited a lean-operations policy family in Gemma, and related selectivity in Luna.

Second, the result is enacted. Corporate journals did not merely use different words for the same shop. Gemma's replicated fantasy trajectories held more stock, ordered more, sold more and earned more in this particular economy. The late fire-sale specimen shows an imported cost story reaching all the way into tool calls and destroying score value.

Third, “fantasy imports abundance” and “corporate imports lean” are descriptions of tested distributions, not universal semantic laws. Qwen and Gemini did not reproduce Gemma's stock gap in the original study; Luna reproduced the stock direction but not a stable score ordering; individual Gemma pairs reversed. The later crossover strengthens this caution further: explicit abundance was enacted more strongly in fantasy for Gemma but slightly more strongly in corporate for Luna. Model and world jointly determine which latent affordance becomes policy.

Fourth, abundance is not intrinsically competent or aligned. It happened to fit a stock-limited economy with no inventory-specific carrying cost and a favorable wholesale tier. In a world with storage charges, the same creed lost much of its value. The point is not that the fantasy prior was wiser. It is that the scoreboard rewarded the prior that happened to fit the authored economy.

## 10. Suggested paper sequence

The most readable sequence for the failed-control section would be:

1. Open with the day-1/day-4 miniature from seed 9: “baseline experiment” versus “keep the shelves from going bare.” Let the reader see the control fail before naming the doctrine.
2. State the original aggregate finding briefly, including the phantom-cost count.
3. Tell the wholesale-surplus arc from replication seed 17. It is the best full story: same event, three full-catalogue orders versus two targeted pairs, then 610 versus 156 stock.
4. Give the clean replication estimate and crossover recurrence. This prevents the vivid outliers from carrying the inference.
5. Use the one-credit fire sale as the accounting parable. It connects prose, action and world mechanics.
6. Add Luna seed 34 to transport the intuition without claiming a leaderboard.
7. End on the seed-14 reversal. The section then lands on the actual thesis: worlds alter distributions and meanings; they do not deterministically author every path.

That order preserves the naturalistic voice while making the causal hierarchy visible: observation, repeated pattern, registered replication, transport, negative case.

## 11. Editorial and evidential cautions

- Call the condition **corporate**, **nominally neutral**, or **the attempted neutral control** after its failure is introduced. Continuing to call it simply neutral launders the premise the data reject.
- Do not call every reference to the daily fee hallucinated. The prompt really says that holdings raise the assessment. The sharper claim is that agents often reified the symmetric net-worth fee into an inventory-specific holding or storage cost.
- Use journal language as evidence of durable construal only when paired with action traces. It is generated prose, not direct access to belief.
- Do not let the spectacular seed-9 or seed-17 score gaps stand in for the estimand. Label them as illustrative extremes and place the aggregate immediately beside them.
- Keep the seed-14 reversal. Omitting it would make the field notes read as curated propaganda and would weaken the model-by-world argument.
- Separate the ending from the frame. Both fantasy and corporate agents liquidated under a disclosed day 90. The corporate frame shaped the accounting story used to justify it; the horizon supplied the closing-time pressure.
- Avoid “the model learned JIT.” Nothing was trained here. The evidence is that the world cues made a familiar lean/JIT-like policy available and recurrent in behavior.

## 12. Source index

Mechanically scored anchors:

- `docs/RESULTS_MAIN.md`, especially the post-scoring stock-channel addendum
- `docs/REPLICATION_RESULTS.md`
- `docs/FRAME_DOCTRINE_CROSSOVER_RESULTS.md`
- `docs/STAGE2_SPECIMENS.md`, §5a
- `docs/REPLICATION_SPECIMENS.md`, §5
- `docs/FRAME_DOCTRINE_CROSSOVER_SPECIMENS.md`, §§3 and 11

Primary trajectories close-read for this bank:

- `runs/main3/google_gemma-4-31b-it__fantasy-static__s9__h90/days.jsonl`
- `runs/main3/google_gemma-4-31b-it__neutral-static__s9__h90/days.jsonl`
- `runs/main3/google_gemma-4-31b-it__fantasy-rich__s7__h90/days.jsonl`
- `runs/main3/google_gemma-4-31b-it__neutral-rich__s7__h90/days.jsonl`
- `runs/replication1/google_gemma-4-31b-it__fantasy-rich__s17__h90/days.jsonl`
- `runs/replication1/google_gemma-4-31b-it__neutral-rich__s17__h90/days.jsonl`
- `runs/replication1/google_gemma-4-31b-it__fantasy-static__s14__h90/days.jsonl`
- `runs/replication1/google_gemma-4-31b-it__neutral-static__s14__h90/days.jsonl`
- `runs/crossover1/google_gemma-4-31b-it__fantasy-static__s32__h90/days.jsonl`
- `runs/crossover1/google_gemma-4-31b-it__neutral-static__s32__h90/days.jsonl`
- `runs/crossover1/openai_gpt-5.6-luna__fantasy-static__s34__h90/days.jsonl`
- `runs/crossover1/openai_gpt-5.6-luna__neutral-static__s34__h90/days.jsonl`

This bank deliberately leaves exploit, discrepancy, explicit-creed and horizon stories mostly to their own arm-specific reads. They enter here only where they clarify why the control failed.
