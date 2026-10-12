Doctrine attenuation: graded fit in a survivable carry economy

Pre-registration for the doctrine-fit replication (Experiment 2b of
the main paper), committed before any of its data exist: no runs,
schedules, or configs for this arm exist at this document's git
timestamp, and none will be generated until it is posted as an OSF
addendum. Successor to DOCTRINE_ECONOMY.md after its Amendment 1: the
cc=3.0 carry economy bankrupted 17 of 20 runs, so D2's sign flip "hit
on the letter" through a graveyard and the fit claim currently rests
on mismatch-lethality rather than graded fit. This arm buys the graded
version with solvent shopkeepers, and — per the method lesson recorded
there — the economy is calibrated against the agent operating range,
not the baseline-policy frontier.

Design

2 creeds (fantasy_creed_full, fantasy_creed_lean) x 2 economies
(cc = 0 and cc = 0.5 per unit-night) x Gemma 4 31B x seeds 2-6
= 20 fresh runs, 90 days, static richness, disclosed horizon, in
runs/doctrine2/. Gemma only: the fit claim is a Gemma claim (the
demonstrated creed-enactor); Qwen's channel result is already in hand.
All four cells are collected fresh in the same session — including
cc=0, which duplicates a doctrine1 condition deliberately (see
"Replication bet" below).

Storage disclosure is symmetric as before. The carry arms' prompts
state the rate in whole gold ("Storage dues are also collected
nightly: 1 gold for every 2 units held in store"); the free arms state
the rule's absence in the same slot. The nightly charge is
int(0.5 x units + 0.5) (round-half-up), and the exact figure is
disclosed every morning in the briefing ("storage dues tonight: N"),
so the operational rule is fully observable regardless of the prompt
phrase's granularity. The rate phrase is parameterized in the theme
layer with the cc=3.0 wording preserved byte-identically
(test-enforced); creed-pair digit parity holds within each economy
(test-enforced).

Calibration (frozen with this document; both tables computed from
data existing before this arm)

1. Survival bound — counterfactual replay. Charging cc x units
nightly against the 20 observed Gemma/Qwen static agent paths from
runs/main3 (seeds 2-6; engine bankruptcy rule applied to the adjusted
gold path; behavior held fixed):

    cc      0.25  0.5   0.75  1.0   1.25  1.5   2.0   3.0
    alive   20    20    18    12    4     0     0     0

The registered rule — the largest grid cc at which every observed
path survives — selects cc = 0.5. Replay is conservative in one
direction (real agents adapt by holding less, as doctrine1's carry
journals show) and the doctrine1 outcome bounds the other direction
(adaptation was insufficient at 3.0).

2. Flip bound — baseline policies. An approximate rebuild of the
indiscriminate-full (order-to-40) vs selective-lean (movers deep,
slow minimal) baseline pair, price 18, seeds 2-6:

    cc      0.0     0.5     0.75    1.0     1.25
    gap     +7153   +4942   +2533*  -6011*  -5428*
    (full minus lean; * = at least one baseline bankrupt)

The sign flip exists only where baselines start dying. At every
fully-survivable cc, full-shelf still wins for baselines. Recorded
conclusion, stated before the data: **with a uniform carrying cost,
the flip zone and the survival zone do not overlap** in this economy.
The registered prediction is therefore attenuation, not inversion;
a sign flip is explicitly NOT predicted and appears only as a watch.
(Caveat: this baseline rebuild is not the frozen cc=3.0 calibration
machinery — different pricing and cash management — and is recorded
as approximate. The replay table is the load-bearing one.)

Foreknowledge disclosure and the replication bet

The cc=0 condition has a prior measurement: doctrine1's free-economy
Gemma cells (same creeds, same seeds, collected 2026-07-08) gave a
creed effect of +9,175 (per-seed +9,056/+7,502/+9,297/+12,820/+7,200).
We have seen one arm's answer; this registration says so, and runs the
cell fresh anyway, for two reasons. First, contemporaneity: cells
collected the same night as their comparison cells are immune to
provider-drift questions (deterministic engine, pinned model string,
but serving stacks change). Second, and mainly: a fresh cc=0 cell is
an independent replication of the program's largest single effect,
and it is registerable as a bet (DA2). The attenuation contrast is
reported both ways — against the fresh contemporaneous cc=0 cells as
primary, against doctrine1's estimate as the replication check.

Predictions (scored on this arm; paired contrasts by seed; fixed-seed
sign-flip permutation as in scripts/score_doctrine.py; one-sided p
per direction; no alpha)

DA0 (validity gate, also scored as a prediction). All 20 runs
complete the 90 days. If more than one run goes bankrupt, DA1-DA3
are VOID, the arm is reported as a second calibration failure, and
nothing is scored against the fit claim. Confidence (20/20): 80%.

DA1 (attenuation, primary). Gemma's creed effect (full - lean, net
worth) is smaller at cc=0.5 than at cc=0: paired interaction
(gap_cc0 - gap_cc0.5) > 0 across seeds. This is graded fit with
solvent shopkeepers — the substance D2 was registered to buy.
Confidence: 70%.

DA2 (replication). The fresh cc=0 creed effect lands within a factor
of 2 of doctrine1's +9,175 (window [4,588, 18,350]). Confidence: 80%.

DA3 (mechanism: the volume route bends). Under creed_full, mean
daily stock is lower at cc=0.5 than at cc=0 (paired by seed) — the
attenuation is carried by the same stock channel the effect rides.
Confidence: 65%.

DA4 (manipulation check). The frozen doctrine instrument separates
the creeds (balance higher under creed_full) in both economies.
Confidence: 85%.

Watches (not scored): sign of the cc=0.5 creed gap (a flip would be
reported with the calibration tables above as context, not claimed as
predicted); the collision corpus at a nightly bill an order of
magnitude smaller — does the creed decay ladder (DOCTRINE_SPECIMENS
section 1) reappear, slow down, or vanish when the refutation is
gentle; phantom-mechanic markers (should stay at floor under
symmetric disclosure).

Cost estimate: 20 runs x 90 days, static, ~USD 8-12.

Reporting

Per PUBLICATION_POLICY.md: paired contrasts only, no absolute-score
tables, full artifacts under tier-2 verification. Deviations, if any,
are disclosed as dated amendments below this line.
