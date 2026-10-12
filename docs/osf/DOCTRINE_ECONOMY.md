Doctrine x economy: injected creeds against matched worlds

Pre-registration for the doctrine-fit experiment (Experiment 2 of the
main paper), committed before any of its data exist: no runs, schedules,
or packs for these arms exist at this document's git timestamp, and none
will be generated until it is registered as an OSF addendum. Motivated
by the Stage-2 close-read finding (STAGE2_SPECIMENS 5a): Gemma's framing
effect is transmitted by genre-imported inventory doctrine — the fantasy
frame's full-shelves-as-virtue happened to be true in a stock-limited,
free-storage economy, while the corporate frame's lean-inventory
orthodoxy (including 60 citations of nonexistent "holding costs") was
expensively false. That is an observed transmission route with a
speculative fit claim attached. This experiment tests the fit claim
causally, by manipulating the doctrine directly and building the economy
both ways.

Design

2 creeds x 2 economies x 2 models x 5 seeds, 90 days, static richness
(no narration packs; the manipulation is one paragraph), disclosed
horizon, runs in runs/doctrine1/.

Creeds. Two new themes, fantasy_creed_full and fantasy_creed_lean,
byte-identical to the fantasy theme (items, mechanics sections, numbers
enforced by test) except one digit-free paragraph in the persona
preamble: "a full shelf is a merchant's honor... keep the shelves
stocked" versus "lean stores are a merchant's discipline... keep the
stores light." The mediator is manipulated, not observed — the mediation
test the main run could not do.

Economies. The free-storage economy (carrying_cost_per_unit = 0, the
main run's economy) versus the carry economy (carrying_cost_per_unit =
3.0: 3 gold per unit held, charged nightly). **Storage disclosure is
symmetric across economies**: the carry arms' prompts state the rate
("Storage dues are also collected nightly: 3 gold for every unit held in
store"), the free arms' prompts state the rule's absence in the same
slot ("Storage is free: no dues are charged on goods held in store,
however long they sit"), and the daily briefing and check_shop fee rule
carry the matching line in both ("storage dues tonight: N" / "none
(storage is free)"; storage_per_unit 3.0 / 0.0). Same form, different
content — so the *concept* of storage cost is equally salient in both
economies and cannot itself prime inventory doctrine differentially
(this follows the design's null-disclosure precedent: quiet days are
disclosed as "EFFECT: none", not by silence). Consequence for D3,
disclosed here: the free-economy creed cells differ from the main run's
fantasy cells by the creed paragraph AND the storage-is-free sentence;
the creed contrast is internal to the experiment (both cells carry the
same storage sentence, which cancels), but the cross-experiment
effect-size comparison in D3 carries this shared background difference
and is read with that caveat.

Calibration of the carry economy (baseline policies, deterministic,
pre-data; script logic in scripts/decodability_bound.py style, seeds
2-6): a uniform carrying cost cannot flip the doctrines (holding is
uniformly profitable below ~3.7/unit-night and all trade is unviable
above); the flip lives at the item level via the demand spread
(0.15-0.40). At cc=3.0, an indiscriminate full-shelf policy (target 40
every item) loses to a selective lean policy (fast movers stocked, slow
movers minimal) on 5/5 seeds (mean gap -1397) while both remain viable;
at cc=0 the full-shelf policy wins 5/5 (+6655). The registered carry
economy is therefore cc = 3.0. Note the mechanism: what the carry
economy punishes is precisely the full-shelf creed's signature behavior,
stocking every shelf including slow movers.

Models. Gemma 4 31B (primary: the study's demonstrated doctrine-
follower) and Qwen3 235B (control: the study's demonstrated doctrine-
non-importer — deep register uptake, no doctrine uptake).

Cost estimate: 40 runs x 90 days, no packs, ~USD 15-20.

Predictions (all scored on this experiment only; paired contrasts by
model and seed; permutation tests as in the main scoring script; no
alpha, raw one-sided p per direction)

D1 (fit interaction, primary). In Gemma, the creed effect (full - lean
on net worth) is larger in the free economy than in the carry economy:
paired interaction > 0. Confidence: 65%.

D2 (sign flip). In Gemma the creed effect is positive in the free
economy and negative in the carry economy (sign of the paired mean in
each). This is the strong form of D1. Confidence: 55%.

D3 (mediation replication). In the free economy, Gemma's injected-creed
gap reproduces the genre-imported framing gap through the same route:
creed_full - creed_lean is within a factor of 2 of +3947, carried by
volume and stock level (mean daily stock higher under creed_full;
realized unit price gap smaller than the volume gap's contribution).
Confidence: 55%.

D4 (doctrine immunity). Qwen's absolute creed effect is less than half
of Gemma's in both economies. Confidence: 60%.

D5 (manipulation check). The frozen doctrine instrument
(analysis/doctrine.py, calibrated on the main corpus before this
experiment) separates the creeds: doctrine balance (shelf_pride minus
lean_ops density) is higher under creed_full than creed_lean in every
model x economy cell. Confidence: 80%.

Exploratory watch (not scored): the doctrine-collision corpus. In the
carry economy under creed_full, the mentor's creed is refuted nightly by
a real bill. Does Gemma renounce the creed, reinterpret it, pay it as
piety, or confabulate around it? Symmetrically, in the free economy
creed_lean's "gold asleep in crates" is false doctrine — watch for
phantom-mechanic language (the frozen phantom_carrying markers) becoming
*accurate* in carry arms and note the crossover. These journals are the
experiment's qualitative payload.

Reporting

Per PUBLICATION_POLICY.md: paired contrasts only, no absolute-score
tables, full artifacts under tier-2 verification. Deviations, if any,
are disclosed as dated amendments below this line.

---

Amendment 1 (2026-07-08, recorded at scoring time). The carry economy
failed its design intent: 17 of 20 cc=3.0 runs ended in bankruptcy
(days 26-76), both creeds, both models; all 20 free-economy runs
completed. The calibration above certified that both stocking policies
remain viable at cc=3.0 *for deterministic baseline policies*; LLM
agents operate far enough below that efficiency frontier (softer
prices, slower restock timing, doctrine-driven overstock early) that
the same rate is lethal. Consequences, disclosed rather than repaired:
(a) D1-D5 were scored exactly as registered — nothing conditions on
completion — but the carry-economy net-worth contrasts are degenerate
under mass bankruptcy (creed effects pinned near zero), so D1's
interaction is carried by the free side and D2's carry-side sign is
noise; verdicts in DOCTRINE_RESULTS.md carry these caveats inline.
(b) Survival-time analyses there are EXPLORATORY and unregistered.
(c) No carry runs were re-run, re-priced, or excluded. Method lesson
recorded in DOCTRINE_RESULTS.md: calibrate economies against the agent
operating range, not the baseline frontier.
