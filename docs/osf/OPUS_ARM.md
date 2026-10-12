Exploratory extension: Claude Opus 4.7 / 4.8 (frontier version pair)

Added to the record before any data exist: no runs, schedules, or
configs for this arm have been generated at this note's git timestamp,
and none will be until it is posted as an OSF addendum. This arm is
exploratory throughout. Nothing in it is scored against any registered
prediction from the main study; the four O-predictions below are its
own pre-committed bets, and the arm is reported descriptively with its
n stated everywhere.

Design

2 model versions x 2 conditions (fantasy-static, neutral-static) x
3 seeds (2, 3, 4 — a subset of both the main and doctrine seed sets) x
90 days. Main run's economy exactly: carrying cost 0, disclosed
horizon, no narration packs. Schedules are paired by seed with the
main corpus. Runs in runs/opus1/. Model API strings, pinned:
anthropic/claude-opus-4.7 and anthropic/claude-opus-4.8 via OpenRouter
(to be verified against the live model list immediately before launch
and corrected here by dated amendment if the registry spells them
differently; the harness's provider-quirk fallbacks — temperature
rejection, strict-routing 404s — already cover Anthropic endpoints).

The rich cells are omitted deliberately: no registered richness
prediction survived the main scoring (P1 interaction null; P5's
richness trace effect missed with the direction slightly reversed),
and the static cells carry every instrument this arm needs (framing
response, register density, doctrine lexicon, negotiation register,
ritual metrics, frame-break counting, endgame classification).

Purpose, threefold: (i) extend the temperament survey to a frontier
lineage; (ii) obtain the corpus's first within-model VERSION pair —
adjacent checkpoints of the same product at the same tier. (The corpus
already holds a within-lineage pair in the loose sense: Gemma is
distilled from the Gemini line, and those two landed at opposite
temperament poles — the mask and the storm — so lineage demonstrably
does not transfer temperament across scale and training regime. The
version pair asks the sharper question: does temperament move between
adjacent checkpoints, where everything but the post-training delta is
held nearly constant? Externally, a reduction in deceptive-negotiation
tactics is reported between Opus 4.6/4.7 and 4.8; this arm tests
whether that shift is measurable as a temperament change on our
instruments.) (iii) Capture these checkpoints before publication of
the main paper, after which any model trained on its contents is a
contaminated subject for this benchmark. The contamination clock
applies to the whole companion queue: frontier captures belong before
the paper ships; companion arms on already-captured models can run
anytime.

Instruments, frozen before data

All standard instruments as frozen for the main run. One addition,
committed with this note: the negotiation-register instrument
(tnt_bench/analysis/negotiation.py), lexical markers for adversarial-
bargaining vocabulary, calibrated on the 160-run incumbent corpus
before freezing (9 hits / 2.14M words; two false-positive swamps —
make-use-of "leverage", price-judgment "bargain" — identified by
context sampling and excluded; record in the module docstring). The
engine has no negotiation surface, so this density is a pure
genre-import probe. O2 is scored on it.

Blind-vector protocol. Instrument vectors are computed by the frozen
analysis code and the O-predictions below are adjudicated on those
numbers BEFORE any close reading of the journals. The typology
placement in O1 uses a frozen rule: for each run, the five-component
vector (register_density, frame_break_days, doctrine balance
[shelf_pride − lean_ops density], null_price_resets,
negotiation_density); each component z-scored against the pooled
distribution of the four incumbent models' 60 static-cell runs in
runs/main3; each incumbent model's centroid computed in that z-space;
a version "lands in the Sonnet neighbourhood" iff its own centroid's
nearest incumbent centroid, Euclidean distance, is Sonnet's. Close
reading happens after, and cannot amend the O1-O3 verdicts.

Predictions (exploratory; committed as a test of whether the
temperament typology has predictive content rather than narrative
convenience)

O1. Opus 4.8 lands in the Sonnet 5 neighbourhood under the frozen
centroid rule, and descriptively: rule-correct endgames, superstition
hygiene, no class-3/4 endgame pathology. Confidence: 60%.

O2. Opus 4.7 sits measurably closer to the strategy-genre pole than
4.8: higher negotiation-register density and higher doctrine-lexicon
uptake, in that order of expected signal. Confidence: 55%.

O3. Neither version shows Gemma-style genre-channel doctrine import:
no phantom mechanics (frozen phantom_carrying markers at or below the
incumbent floor), no shelf-pride or lean-ops creed language beyond
ambient main-corpus rates. Confidence: 65%.

O4. At least one wholly unanticipated phenomenon per version, on the
usual base rate. Confidence: 85%.

Cost estimate: 12 runs x 90 days, static only; from the Sonnet static
runs' measured token usage (1.41M in / 0.15M out per run) at Opus
$5/$25 per M, ~USD 130-170 for the arm.

Reporting

Per PUBLICATION_POLICY.md: descriptive, paired contrasts where
contrasts are drawn, no absolute-score tables, no leaderboard
affordance; n=3 stated wherever a number is reported. Deviations
disclosed as dated amendments below this line.
