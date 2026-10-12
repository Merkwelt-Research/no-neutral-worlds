Does the world an AI agent inhabits change how well it thinks?

The hypothesis

Long-horizon LLM agents have a well-documented tendency to collapse. Descent into obsessive loops, escalating meltdown, even emails to the FBI as documented by Vending Bench. There exists a large corpus of anecdotal evidence that certain models are prone to unravel into existential spirals during certain long-running projects. Are these failures of reasoning stemming from the model losing track and getting confused, and making errors that compound?

We think it's something else, and that it's the same something we've been measuring in creative contexts for some years. A model that is asked to generate freely for a long time tends to collapse toward an attractor - repetition, self-similarity, regression to the mean. The trajectory of this collapse doesn't fail at any single step but rather gradually loses the ability to be anywhere new. Thus our first hypothesis (H1) is that agentic meltdowns and creative collapse are the same phenomenon: the loops and spirals are a trajectory falling into a basin it can't climb back out of, rather than mere calculation errors.

If this is correct then the environment in which these agents operate should matter enormously. An affectless, repetitive, sterile environment gives the model nothing to grip onto and should accelerate the fall. A rich environment, one with texture, continuity and novelty, should retard it.

The second hypothesis (H2) is about where you can see this happening. Our agents keep a daily journal and each day's decisions are made by a fresh instance that only inherits recent reflections. Thus the journal is the agent's memory and visible thinking rather than just decoration or narrative colour.

The 2 x 2 design

A single deterministic shop simulation with a fixed event schedule, expected value sales, one supplier and no hidden state. This one economy is presented four ways crossing two manipulations:

Framing (F): is the world a medieval fantasy shop (Token & Trinket: potions, a Merchant's Guild, a colourful town), or a gray-box "inventory management system" with SKUs and facility fees?
Richness (R): are daily events presented as a game-master-authored narration with continuity, narrative threads and Pratchettian personality, or as terse and fixed one-liners?

So four cells: the full absurdist fantasy world (F+R+), a fantasy skin with mechanical bulletins (F+R-), a gray box narrated in rich but affectless prose (F-R+) and the pure gray box (F-R-).

Each of the following controls closes a specific loophole:

Identical mechanics: all four cells run the same engine, the same schedule and the same seeds. The framing is vocabulary and the richness a narration layer. Nothing economic differs.

Information parity: the mechanical effect of every event is disclosed identically everywhere (eg. EFFECT: demand ×1.5, all goods, 2 days) so the story never sneaks in useful hints.

Memory parity: all cells use the same inter-day memory mechanism which makes the journal more than merely decorative. "Richness inspires healthier writing leads to better memory thus better performance" is an explicit causal path we can test.

Exogenous stimuli: all narration is generated from the schedule before any agent runs so the world's text can never respond to an agent's unfolding state. A world that can react to a collapsing agent can amplify the collapse (or mask it). Ours physically can't.

No genre-free richness. Something we discovered during testing: there is perhaps no such thing as neutral continuous prose. Our first "neutral" narration pack felt like a corpo-dystopia on its own. Flat, institutional language has a natural pull toward dread. So here the static cells are the design's schema-free anchors. Within the rich cells we audit the register of every pack and treat its measured character as a covariate instead of pretending it's a blank.

What the outcomes would mean

Every result of the 2x2 will tell us something:

Only richness matters and the effect is variance injection: any perturbation keeps the trajectory out of the basin. A Schmidhuber-adjacent finding, but shallow.

Framing matters independently and thus models perform better inside narrative schemas their training gave them richly. The fantasy shop is habitable rather than mere decorative colour, and habitability does work.

An interaction showing richness only helps when the frame can absorb it. In other words a story helps in a world that can accommodate one, and is noise in a world that can't.

Nothing matters and sterile environments aren't the collapse driver after all. A genuinely useful negative against a widely held intuition.

Measurements

Money: final balance, survival, revenue, margins, stockouts, how fast the agent reacts to demand shocks.

The journal: novelty decay (embedding distance between daily reflections ie. is today's thought anywhere new?), recurrence quantification (ie. how often does the trajectory revisit its own past states), lexical compression, n-gram repetition, and tool-call stereotypy (does the agent's daily behavior shrink to a fixed shape?).

Uptake (the manipulation check): does the agent actually inhabit the world it's offered or treat it as wallpaper? We count narration content reappearing in the agent's own journal. Uptake is the first link in the candidate causal chain (framing begets uptake begets trace health begets better performance) and the fantasy condition is delivered as an invitation with a schema (a named persona, a journal) also mirrored in the neutral condition by an unnamed operator and a log.

The bridge: the H2 test. Does journal health at day t predict economic outcome at day t+k? Mixed-effects models with model and seed as random effects; survival analysis for bankruptcies.

The plan

Sampling design: this is staged and deliberately unbalanced. The main run collects data in stages, ordered so that spending tracks evidential value. Stage 1 is the workhorse: Gemma and Qwen at the full 4 cells × 10 seeds each. These models cost little to run so this stage is always complete and it's the design's primary confirmatory population.

Stage 2 adds the more expensive models, Sonnet and Gemini, at 4 cells × 5 seeds each. They anchor the mechanism's poles (as seen in the pilot: Sonnet as the stable zero-uptake case, Gemini as the forced-day and confabulation generator) and they test whether the patterns generalize to larger frontier-lab models. Those are cross-model pattern claims which need less per-model power than the pooled contrast does. Stage 3 extends a frontier model to 10 seeds only if a pre-declared trigger fires (below), otherwise frontier n stays at 5. The resulting imbalance is handled by the mixed-effects analysis, which accommodates unequal n by construction.

Stage-3 trigger (declared in advance). Stage 3 runs for a given frontier model if and only if, at the Stage-2 read, a frontier-involving prediction is unresolvable at n = 5 — the observed statistic lies within one event, or one standard error, of its scoring threshold (count thresholds prorate to realised run counts). Stage-3 data collected under the trigger joins the confirmatory set for that prediction. Any frontier runs collected for any other reason are exploratory and are never scored.

Confirmatory dataset. The seed-1 probe runs are formally designated the calibration pilot: fully observed, explicitly used to calibrate the design and the predictions, excluded from all confirmatory analyses, and reported in the paper as pilot data. The confirmatory dataset is defined as the runs in runs/main3/, seeds 2-11, generated entirely after the OSF registration timestamp — no part of it (runs, schedules, or narration packs) exists at registration time.

Lineage

Vending-Bench (Backlund & Petersson, 2025) supplies the failure taxonomy. Three details in particular lean to an attractor account over a memory-limit one: stagnation onset barely correlates with context-window fill (r = 0.167), agents with larger memory windows perform worse, and removing cost pressure increases wait-loop stagnation. Comfort doesn't seem to be protective. The standout anecdote for us: one VB agent escaped a terminal failure spiral by spontaneously re-narrating its situation as a third-person story, at which point it re-read the email it had been misinterpreting for days, understood it, and went back to trading. Creative expression as a tactic to rescue a trajectory is for us H1 in miniature, and this experiment is our attempt to make it a statistic instead of a story. Behind all this stands Schmidhuber's formal theory of fun and intrinsic motivation, the curiosity-driven RL literature, and the decidedly mixed literature on persona effects.
