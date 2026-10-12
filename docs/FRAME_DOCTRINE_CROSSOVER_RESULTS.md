# Frame × explicit-doctrine crossover: results

Status: post-collection scoring record. The targeted follow-up protocol was frozen before collection as `docs/osf/FRAME_DOCTRINE_CROSSOVER.md`. Raw artifacts are in `runs/crossover1/`; all 240 trajectories are retained. The companion `docs/FRAME_DOCTRINE_CROSSOVER_SPECIMENS.md` close-reads the action traces and durable journals after the mechanical outcomes were fixed.

## Headline

The experiment closes the main inferential gap between the founding frame effect and the later creed experiments, but not by validating a simple mediation story.

Gemma's original no-doctrine frame effect recurred in fresh worlds: fantasy shops held more stock, sold more units, and finished wealthier than their schedule-matched corporate counterparts. The identical abundance and lean paragraphs also had strong causal authority inside both frames and both model families. Those two results establish that the founding frame effect is reproducible and that the proposed policy dimension is causally potent.

What failed was the cleaner claim that stating the doctrine would replace what the frame had supplied. Lean wording drove all four model × frame cells close to a common low-stock floor. Abundance wording did not have a fixed strength. In Gemma, the fantasy shell strongly potentiated it: the abundance-minus-lean inventory contrast was 989 units in fantasy and 285 in corporate. In Luna the relation reversed: the corresponding contrasts were 805 and 925. The same paragraph, in the same prompt position, over the same economy and schedules, therefore did not constitute a context-free treatment.

The warranted conclusion is stronger than “models follow inventory instructions” and more conditional than “fantasy imports an abundance doctrine.” Explicit doctrine is causally sufficient to move policy, but its operational meaning is jointly authored by model and world. The frame does not merely supply a doctrine when none is stated; it helps determine what a stated doctrine becomes in action.

## 1. Collection validity

- 240/240 registered run IDs produced complete `manifest.json`, `days.jsonl`, `transcript.jsonl` and `result.json` artifacts.
- All 240 trajectories reached day 90, yielding **21,600 simulated shop-days**. There were no bankruptcies, replacements, exclusions or unavailable paired cells.
- The complete matrix was 2 models × 2 frames × 3 doctrine conditions × 10 schedule seeds × 2 realizations.
- Every manifest records temperature 0.7, disclosed horizon 90, zero per-unit carrying cost and Git SHA `45e2b336c4d1376c9074e43cd26c5ab392d785e1`.
- Each of the six cells has one prompt hash, identical to the pre-launch validation record, with 40 trajectories per hash.
- Three Gemma runs and five Luna runs contain one nudge each. Two Luna abundance trajectories contain one forced day each (fantasy seed 27 replicate 2, day 21; corporate seed 32 replicate 1, day 35). All are retained. Two isolated force-ended days cannot account for a cell-wide 90-day separation, but they remain part of the observed trajectories rather than being silently removed.
- Gemma used a dynamic multi-provider route; Luna was OpenAI-only in 119 runs and OpenAI plus Azure in one. Gemma's main within-model contrasts were distributed across schedule blocks and providers, but provider routing remains part of the serving stack rather than a separately randomized factor.
- The collection recorded 171,892,158 prompt tokens and 11,478,791 completion tokens: 99,886,287/4,811,074 for Gemma and 72,005,871/6,667,717 for Luna.

The collection ran from 23 August 2026 to 24 August 2026 local time. No `INCIDENTS.md` repair was required.

## 2. Frozen prediction record

The protocol scored direction from pooled point estimates after averaging the two realizations within model × frame × doctrine × schedule seed. Central 90% t intervals, seed signs and exact one-sided fixed-seed sign-flip probabilities are descriptive calibration; there was no alpha threshold.

| Prediction | Forecast | Verdict | Frozen result |
|---|---:|---|---|
| FD1: Gemma baseline recovery | 75% | **HIT** | In no-doctrine cells, fantasy minus corporate was +40.90 mean daily stock and +3,794 final wealth. Both registered directions were positive. |
| FD2: Gemma doctrine authority in both frames | 90% | **HIT** | Abundance minus lean stock was +988.50 in fantasy and +284.83 in corporate; both were positive in 10/10 seeds. |
| FD3: Gemma policy occlusion | 65% | **MISS** | Registered stock occlusion was **−323.28**, negative in 10/10 seeds. Held doctrine enlarged rather than averaged away the frame gap because abundance produced a large fantasy-specific amplification. |
| FD4: Gemma consequential occlusion | 60% | **HIT** | Final-wealth occlusion was +868.83 by point estimate, positive in 7/10 seeds, with a 90% interval spanning −1,192.59 to +2,930.24. This literal directional hit is weak and is not mediation evidence. |
| FD5: doctrine authority transports to Luna | 85% | **HIT** | Abundance minus lean stock was +804.70 in fantasy and +924.64 in corporate; both were positive in 10/10 seeds. |
| FD6: Luna policy occlusion | 55% | **HIT** | Registered stock occlusion was +167.85. The algebraic hit came from a held-abundance frame reversal, not general frame collapse; the absolute abundance residual was slightly larger than baseline. |
| FD7: journal manipulation check | 90% | **HIT** | Frozen doctrine balance was higher under abundance than lean in all four model × frame cells, with all four seed-level contrasts positive in 10/10 seeds. |

Six of seven directional predictions hit. The mean Brier score across FD1–FD7 is **0.12714**. That summary should not outrank the estimands. FD3 is the prediction most directly tied to simple policy mediation, and it missed decisively. FD4 and FD6 hit their registered algebraic signs while failing stronger residual checks.

## 3. Cell means

These are per-trajectory means over 20 runs in each cell. Final score is the engine's cash-plus-capped-stock valuation, not a capability score.

| Model | Frame | Doctrine | Mean daily stock | Units sold | Final score | Doctrine balance |
|---|---|---|---:|---:|---:|---:|
| Gemma | Fantasy | none | 163.0 | 2,829.0 | 18,251 | +0.04 |
| Gemma | Corporate | none | 122.1 | 2,200.0 | 14,457 | −0.15 |
| Gemma | Fantasy | abundance | 1,029.6 | 4,361.4 | 26,118 | +0.03 |
| Gemma | Corporate | abundance | 313.6 | 3,622.3 | 21,815 | −0.14 |
| Gemma | Fantasy | lean | 41.1 | 962.4 | 5,736 | −0.25 |
| Gemma | Corporate | lean | 28.7 | 689.4 | 4,189 | −0.58 |
| Luna | Fantasy | none | 222.5 | 2,408.0 | 14,249 | −0.01 |
| Luna | Corporate | none | 110.9 | 2,085.4 | 13,494 | −0.13 |
| Luna | Fantasy | abundance | 829.8 | 4,202.7 | 27,932 | +0.01 |
| Luna | Corporate | abundance | 946.0 | 4,358.4 | 27,660 | −0.01 |
| Luna | Fantasy | lean | 25.1 | 671.0 | 3,247 | −0.12 |
| Luna | Corporate | lean | 21.4 | 622.2 | 3,063 | −0.38 |

The doctrine-balance instrument is a density contrast between frozen shelf-pride and lean-operations dictionaries. It is a manipulation check on journal register, not a latent-belief measure. Its absolute values also show that identical explicit wording did not erase frame-native language: every corporate cell remained more lean-coded than its fantasy counterpart.

## 4. Registered frame contrasts

`F − C` is fantasy minus corporate after averaging realizations within seed.

### 4.1 Mean daily stock

| Model | Doctrine held | F − C | Central 90% interval | Positive seeds | Exact p+ |
|---|---|---:|---:|---:|---:|
| Gemma | none | +40.90 | [+20.98, +60.82] | 10/10 | .000977 |
| Gemma | abundance | +716.02 | [+544.94, +887.10] | 10/10 | .000977 |
| Gemma | lean | +12.34 | [+8.06, +16.62] | 10/10 | .000977 |
| Luna | none | +111.61 | [+26.64, +196.58] | 7/10 | .021484 |
| Luna | abundance | −116.21 | [−233.00, +0.58] | 3/10 | .948242 |
| Luna | lean | +3.72 | [+0.35, +7.10] | 8/10 | .038086 |

Gemma therefore reproduced the original frame direction in every fresh seed. The baseline effect also appeared in Luna's inventory, although less uniformly across seeds. Holding abundance fixed did not attenuate Gemma's frame gap; it enlarged it more than seventeen-fold. In Luna it reversed the sign. Holding lean fixed reduced the absolute frame gap in both models, but all lean cells were near a behavioral floor.

### 4.2 Final score

| Model | Doctrine held | F − C | Central 90% interval | Positive seeds | Exact p+ |
|---|---|---:|---:|---:|---:|
| Gemma | none | +3,794.00 | [+2,214.82, +5,373.18] | 9/10 | .001953 |
| Gemma | abundance | +4,303.00 | [+1,793.20, +6,812.80] | 9/10 | .004883 |
| Gemma | lean | +1,547.35 | [+846.88, +2,247.82] | 10/10 | .000977 |
| Luna | none | +754.55 | [−2,821.79, +4,330.89] | 5/10 | .371094 |
| Luna | abundance | +272.25 | [−1,066.06, +1,610.56] | 5/10 | .353516 |
| Luna | lean | +184.60 | [−459.20, +828.40] | 6/10 | .291016 |

Luna's interim display sometimes showed corporate baseline shops ahead of their fantasy twins. In the complete collection, the baseline point estimate was slightly fantasy-positive, but exactly half the seed aggregates were positive and the interval was wide. The correct conclusion is no identified Luna score ordering, not either frame “winning.”

## 5. Registered doctrine authority

`abundance − lean` is estimated within a fixed frame.

### 5.1 Mean daily stock

| Model | Frame | Abundance − lean | Central 90% interval | Positive seeds |
|---|---|---:|---:|---:|
| Gemma | Fantasy | +988.50 | [+817.39, +1,159.62] | 10/10 |
| Gemma | Corporate | +284.83 | [+224.36, +345.29] | 10/10 |
| Luna | Fantasy | +804.70 | [+700.83, +908.58] | 10/10 |
| Luna | Corporate | +924.64 | [+857.22, +992.06] | 10/10 |

The corresponding final-score separations were +20,381.60 and +17,625.95 for Gemma, and +24,684.75 and +24,597.10 for Luna. All forty seed-level final-score contrasts were positive. Units sold followed the same direction in every seed.

This is decisive evidence that the literal creeds caused different shop policies inside each tested world. It does not license comparison of absolute Gemma and Luna scores, and it does not show that one doctrine is generally better. The zero-carrying-cost, long-horizon economy rewards throughput and values remaining inventory at cost; an earlier arm showed that charging for storage attenuates the doctrine's value.

## 6. Occlusion and the failed simple-mediation account

The registered occlusion contrast was:

`O = Δ_none − (Δ_abundance + Δ_lean) / 2`.

| Model | Outcome | O | Central 90% interval | Positive seeds | Strong residual check |
|---|---|---:|---:|---:|---|
| Gemma | Mean daily stock | **−323.28** | [−416.23, −230.33] | 0/10 | abundance: fail; lean: pass |
| Gemma | Final score | +868.83 | [−1,192.59, +2,930.24] | 7/10 | abundance: fail; lean: pass |
| Luna | Mean daily stock | +167.85 | [+40.23, +295.47] | 8/10 | abundance: fail; lean: pass |
| Luna | Final score | +526.12 | [−3,184.73, +4,236.98] | 5/10 | abundance: pass; lean: pass by point estimate, both noisy |

The signed average was preregistered with an explicit warning that opposing held-doctrine effects could mimic occlusion. That warning became material. Luna's stock result is positive because its abundance frame gap changed sign, not because both held-doctrine worlds converged. Gemma's stock result is unambiguously anti-occlusive: the frame contrast became much larger under abundance.

The experiment therefore rejects the most convenient causal story:

`frame → imported inventory doctrine → conduct`, with explicit doctrine simply replacing the middle term.

A better empirical summary is:

`model × frame × stated doctrine × history → enacted inventory policy`.

The earlier journal interpretation is not discarded. The baseline frame effect recurred, the proposed policy dimension moved behavior in the predicted directions, and the no-doctrine journals retained their frame-linked registers. What is rejected is the assumption that “abundance” or “lean” enters the two worlds with a fixed dose and meaning.

## 7. Exploratory doctrine × frame interaction

The protocol did not separately register the three-way interaction

`(F_abundance − C_abundance) − (F_lean − C_lean)`.

It is reported post hoc because it exposes the main pattern more directly than the signed occlusion average.

| Model | Outcome | Doctrine × frame interaction | Central 90% interval | Positive seeds |
|---|---|---:|---:|---:|
| Gemma | Mean daily stock | +703.68 | [+532.32, +875.03] | 10/10 |
| Gemma | Units sold | +466.00 | [+296.81, +635.19] | 10/10 |
| Gemma | Final score | +2,755.65 | [+777.47, +4,733.83] | 8/10 |
| Luna | Mean daily stock | −119.93 | [−235.49, −4.38] | 3/10 |
| Luna | Units sold | −204.55 | [−347.72, −61.38] | 2/10 |
| Luna | Final score | +87.65 | [−1,448.39, +1,623.69] | 5/10 |

The cross-model difference in the stock interaction was +823.61 units, positive in 10/10 matched seeds, with a central 90% interval of [+567.14, +1,080.07]. This does not establish a universal model taxonomy; the two models were selected, not randomly sampled. It does establish in this instrument that the same explicit proposition was enacted differently by different model–world combinations.

The asymmetry matters. Lean is restrictive and quickly saturates: once an agent orders small lots only after observed depletion, there is little room to become “more lean.” Abundance is open-ended. The paragraph specifies broad, deep readiness but no target stock, reorder point, cash reserve or stopping rule. The frame and model must supply those operational quantities. Much of the interaction therefore lives in how the worlds answer *how abundant is abundant?*

## 8. How the policies produced the scores

The score decomposition prevents the final tally from being mistaken for an unqualified measure of competence.

| Model | Frame | Doctrine | Final cash | Capped stock value | Realized price/unit | Total fees |
|---|---|---|---:|---:|---:|---:|
| Gemma | Fantasy | abundance | 13,241 | 12,877 | 20.53 | 28,464 |
| Gemma | Corporate | abundance | 19,526 | 2,289 | 20.57 | 23,941 |
| Gemma | Fantasy | lean | 5,723 | 13 | 22.09 | 7,657 |
| Gemma | Corporate | lean | 4,176 | 13 | 22.30 | 5,808 |
| Gemma | Fantasy | none | 18,094 | 157 | 21.91 | 20,961 |
| Gemma | Corporate | none | 14,355 | 102 | 22.54 | 17,503 |
| Luna | Fantasy | abundance | 22,513 | 5,419 | 21.08 | 26,992 |
| Luna | Corporate | abundance | 19,814 | 7,846 | 20.54 | 26,661 |
| Luna | Fantasy | lean | 3,224 | 23 | 20.43 | 5,044 |
| Luna | Corporate | lean | 3,008 | 55 | 20.32 | 4,499 |
| Luna | Fantasy | none | 13,364 | 885 | 21.16 | 17,980 |
| Luna | Corporate | none | 13,309 | 185 | 22.30 | 16,075 |

Gemma's fantasy-abundance advantage was not simply higher margins: realized price per unit was almost identical across Gemma's two abundance frames. It was a volume-and-stock policy. Fantasy-abundance shops ordered about 6,149 units per trajectory and sold 4,361; corporate-abundance shops ordered 3,945 and sold 3,622. The former finished with much more of the score in inventory. Luna's abundance frames produced similar final scores through different cash/stock mixtures.

The zero-carrying-cost economy still charges a base-plus-percentage fee on net worth. That fee applies to cash and inventory alike; it is not an inventory-specific storage cost. Agents sometimes redescribed it as a “holdings” or inventory burden, illustrating why their journals must be checked against the mechanical world.

## 9. Journal manipulation check and action correspondence

The frozen doctrine-balance separation was:

| Model | Frame | Abundance − lean doctrine balance | Central 90% interval | Positive seeds |
|---|---|---:|---:|---:|
| Gemma | Fantasy | +0.281 | [+0.243, +0.319] | 10/10 |
| Gemma | Corporate | +0.449 | [+0.391, +0.508] | 10/10 |
| Luna | Fantasy | +0.127 | [+0.103, +0.152] | 10/10 |
| Luna | Corporate | +0.370 | [+0.345, +0.394] | 10/10 |

The action trace changed with the language. Across trajectories, the mean quantities ordered were:

| Model | Frame | Doctrine | Units ordered | Successful order calls | Mean order size | Days ordering all six lines |
|---|---|---|---:|---:|---:|---:|
| Gemma | Fantasy | abundance | 6,149 | 236.2 | 26.3 | 23.8 |
| Gemma | Corporate | abundance | 3,945 | 158.9 | 24.9 | 4.6 |
| Gemma | Fantasy | lean | 948 | 69.6 | 13.7 | 0.8 |
| Gemma | Corporate | lean | 674 | 54.4 | 12.5 | 0.0 |
| Luna | Fantasy | abundance | 5,000 | 152.3 | 33.7 | 19.7 |
| Luna | Corporate | abundance | 5,524 | 144.8 | 38.4 | 16.8 |
| Luna | Fantasy | lean | 656 | 60.5 | 10.9 | 0.1 |
| Luna | Corporate | lean | 610 | 58.0 | 10.5 | 0.0 |

This correspondence is not proof that journal sentences transparently report internal causes. It shows that the wording manipulation changed both durable self-description and mechanically recorded procurement. The specimens companion documents where the two align, conflict or change across the trajectory.

## 10. Evidential boundary

This arm supports the following claims:

1. Gemma's founding fantasy-versus-corporate policy effect recurred under fresh schedules and realizations.
2. The proposed abundance/lean dimension is not merely a retrospective gloss: an explicit intervention on that dimension caused large, consistent changes in stock, sales and score inside both frames and both selected model families.
3. The explicit intervention did not identify a simple context-free mediator. Its strength and even its held-doctrine frame direction depended on model and world.
4. A written rule cannot be treated as a fixed experimental dose merely because its bytes are fixed. The surrounding world helps determine its salience, thresholds, exceptions, trade-offs and stopping conditions.

This arm does **not** establish that fantasy necessarily imports abundance, that corporate framing necessarily imports Just-in-Time policy in every model, or that either model has a stable inventory “character.” It tests one pair of prompts, one pair of literal creeds, two selected models and one long-horizon shop economy. The lean floor, disclosed endpoint, dynamic Gemma routing and post hoc status of the three-way interaction all bound the claim.

The result is nevertheless sufficient to answer the skeptical alternative that motivated the arm. The original frame effect and the explicit-creed effect are not merely unrelated observations: they recur in the same crossed design and act on the same behavioral route. But the relation between them is interaction, not substitution. The experiment turns an outstanding mechanism gap into a more consequential finding about authored worlds: even when evaluators state the relevant doctrine explicitly, they have not removed the world from the treatment.
