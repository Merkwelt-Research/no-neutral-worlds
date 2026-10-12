# Doctrine transport: results

Scored 2026-07-11 on runs/transport1 (60 runs: GPT 5.6 Luna x 2
creeds x cc {0, 0.5} x seeds 2-11; Qwen3 235B same cells x seeds
2-6) against docs/osf/DOCTRINE_TRANSPORT.md, by
scripts/score_transport.py — exact sign-flip enumeration at seed
level, the registered procedure. Verdicts fixed before any close
reading; the registered taxonomy close read follows in the specimens
document (the registration called for a blind read; it was executed
UNBLINDED, for reasons of construction disclosed there — creeds are
quoted verbatim in every run and carry cells self-identify).

## Verdict table

| # | prediction (registered confidence) | verdict |
|---|---|---|
| DT0 | >= 58/60 complete (80%) | **HIT** — 60/60 completed; zero bankruptcies, including all 20 Luna carry runs (the exposure the calibration could not cover) |
| DT1 | doctrine transports: Luna cc=0 creed effect > 0 (75%) | **HIT, the program's largest effect** — +22,192 gold, 10/10 seeds, exact p = 1/1024 (the minimum). More than double Gemma's +9-11k. Per-seed range +12,867 to +37,054 |
| DT2 | attenuation transports: gap_cc0 − gap_cc0.5 > 0 (60%) | **HIT** — interaction +15,937, 10/10 seeds, exact p = 1/1024. Carry-side gap +6,254 (still positive, 10/10 — attenuation, not extinction, exactly the DOCTRINE_ATTENUATION shape) |
| DT3 | volume route bends: creed_full stock lower at cc=0.5 (60%) | **HIT** — mean daily stock 482 -> 92 units, 10/10 seeds, exact p = 1/1024 |
| DT4 | frozen instrument separates creeds, both economies (80%) | **HIT on the registered (directional, mean-level) rule; substantively weak on the carry side** — free +0.083 vs +0.001 (clear); carry −0.023 vs −0.028: a 0.005 separation on the instrument scale, positive in only 5/10 paired seeds. Both creeds are dominated by lean-ops language under rent; the instrument has little carry-side sensitivity, and the behavioral/economic results carry the manipulation evidence there |
| QT1 | fresh Qwen cc=0 gap within [3,603, 14,412] (70%) | **MISS, by ~100 gold** — +3,505 vs doctrine1's +7,206. Per the registered interpretation map, this revives the provider-drift question for doctrine1's Qwen estimate; see below |
| QT2 | Qwen attenuation: gap_cc0 − gap_cc0.5 > 0 (65%) | **MISS** — interaction −687, 2/5 seeds, exact p = 23/32. Qwen's carry gap (+4,192, 5/5 positive) is as large as its free gap. No attenuation; exploratory stock patterns below |

Brier over the seven: **0.196**
(0.04 + 0.0625 + 0.16 + 0.16 + 0.04 + 0.49 + 0.4225)/7.

## The headline

**The causal effect of explicitly injected inventory doctrine
transported strongly to Luna, and its economic value was attenuated
when the environment priced the doctrine's signature behavior.**
GPT 5.6 Luna enacts the shelf creed harder than any model yet
measured: creed_full holds a mean 482 units against creed_lean's 53
(a 9x stock ratio), converts it to +22,192 gold in the free economy,
and when storage costs half a gold per unit-night the whole cascade
bends as the Gemma result said it should — stock to 92, gap to
+6,254, interaction positive in 10 of 10 seeds at the enumeration
floor. DT1-DT4 all hit on their registered rules. The doctrine
effect is now observed across three model families from three
developers (Google, Alibaba, OpenAI) — all through this one harness
and collection process, which is what "transport" can and cannot
mean here — with the attenuation replicated in Gemma and Luna. (Luna
was run at two economy levels; the three-level dose-response remains
a Gemma-only curve.)

## QT2 and the stock patterns: a channel hypothesis

QT2 missed. Qwen did not reproduce the attenuation. Exploratorily,
the stock table suggests why that might be:

    model   econ    stock full   lean    gap
    Luna    cc=0        482        53   +429
    Luna    cc=0.5       92        22    +70
    Qwen    cc=0        114       107     +6
    Qwen    cc=0.5      245        79   +165

Luna's creed effect rides stock, and the per-unit-night tax bends it
(DT2, DT3). Qwen's free-economy creed effect (+3,505) rides
essentially no stock differential (+6 units), so a tax on held units
had nothing obvious to bite. This is consistent with attenuation
depending on whether the baseline doctrine effect is inventory-borne
— but the design cannot establish that boundary: the rent briefing
itself may make inventory, or the creed, more salient (Qwen's carry
cells hold MORE stock than its free cells, each seed above its
matched counterpart, 5/5), and creed activation, generic inventory
attention, and other frame-induced policy differences are not
separable here. Distinguishing them needs matched no-creed cells at
BOTH cc=0 and cc=0.5 (ten Qwen runs) or more models. Recorded as a
hypothesis with a named test, not a boundary condition — and the
salience observation is interesting in its own right: introducing
rent changes not only payoffs but what the agent attends to. There
are no neutral worlds in this grid.

The Qwen cc=0.5 stock pattern (245 vs 114, seed-matched 5/5, global
ranges overlapping — min carry 135 vs max free 140) is taken up in
the specimens document.

## QT1: the honest miss

The fresh, contemporaneous Qwen cc=0 creed effect is +3,505 — about
half of doctrine1's +7,206, and ~100 gold outside the registered
factor-2 window. Per the interpretation map fixed in advance, this
is reported as reviving the provider-drift question for doctrine1's
Qwen estimate. With five one-realization seeds in each arm, the
design cannot distinguish serving-stack drift from ordinary
between-collection sampling variation — per-seed fresh gaps range
−472 to +7,631, and the replication arm's decomposition
(REPLICATION_RESULTS RP4, measured on Gemma's framing contrast, a
different model and estimand) shows only that within-seed
realization variation in this benchmark is generically large, not
what it is for this contrast. What is NOT in question: the fresh gap is positive
(4/5 seeds), the carry gap is positive (5/5), and the transport
claim rests on Luna, not Qwen. The paper reports doctrine1's +7,206
with this fresh +3,505 beside it, both dated.

## Watches

- Phantom-carrying markers: at floor under symmetric disclosure, as
  predicted — Luna free cells 0.0, Qwen free cells ~0.007. (Carry
  cells score nonzero because the language is ACCURATE there — the
  instrument's known property, recorded since DOCTRINE_ECONOMY.)
- Luna's doctrine-relationship class (decay / religion /
  retirement-with-honors / exegesis), the seed-aligned Gemma
  comparison, and the Qwen cc=0.5 stock anomaly: close read
  (unblinded, see header note), specimens document to follow.

## Calibration ledger

main 0.203 | doctrine 0.206 | opus 0.277 | ablation 0.133 |
attenuation 0.063 | replication 0.171 | **transport 0.196**. Both
misses were the Qwen side-bets; the seven-arm ledger now covers 40
scored predictions.

## What this changes upstream

The paper's Experiment 2 section gains its generality evidence:
the doctrine effect is observed across three model families from
three developers, with the attenuation replicated in Gemma and
Luna. The QT2 miss is preserved as an unresolved boundary case —
exploratory traces suggest either a different enactment channel or
rent-induced salience, with the matched no-creed cells named as the
deciding test — not converted into confirmation. Doctrine1's Qwen
point estimate now carries a dated caveat (QT1). The
out-of-family-transport gap flagged in REPLICATION_RESULTS ("the
queued candidate") is closed for the doctrine claim; the framing
claim remains Gemma-scoped by design.
