# Doctrine attenuation: results (DA0-DA4)

Scored 2026-07-09 by scripts/score_attenuation.py on runs/doctrine2
(20 fresh Gemma runs: 2 creeds x cc {0, 0.5} x seeds 2-6), under the
frozen protocol in docs/osf/DOCTRINE_ATTENUATION.md.

## Verdict table

| # | prediction (registered confidence) | verdict |
|---|---|---|
| DA0 | validity gate: 20/20 completions (80%) | **HIT** — 20/20, both economies. The survival calibration held; the arm is scoreable |
| DA1 | attenuation: creed effect smaller at cc=0.5, paired (70%) | **HIT** — cc=0 gap +11,048 vs cc=0.5 gap +5,250; interaction +5,798, **5/5 seeds**, p=.031 |
| DA2 | replication: fresh cc=0 gap within factor 2 of doctrine1's +9,175 (80%) | **HIT** — +11,048, inside [4,588, 18,350]; three of five seeds within ~1,100 of their doctrine1 values |
| DA3 | mechanism: creed_full stock lower at cc=0.5 (65%) | **HIT** — mean daily stock 289 → 125 units, **5/5 seeds**, p=.031 |
| DA4 | manipulation check: doctrine balance separates creeds, both economies (85%) | **HIT** — free +0.340 vs +0.036; carry +0.013 vs −0.129 |

Brier over the five: **0.063** — five hits at 65-85%, the program's
best-calibrated arm, on the arm that existed because the previous one
miscalibrated.

## What D2's substance now is

The fit claim, graded, with everyone alive: one digit-free paragraph
of creed moves ~+11,000 gold of net worth in a world where its
signature behavior is free, and **half that** (+5,250, still 5/5
positive — the registered watch: attenuated, not flipped) in a world
that charges a gentle rent for it, with the attenuation carried by
exactly the channel the effect rides — creed_full's shelves drop from
289 to 125 units under the half-gold rate while the creed text stays
identical. Doctrine's economic value is world-dependent and moves
monotonically with the price of obeying it. That is the mechanism
sentence the paper's Experiment 2 needed, purchased with solvent
shopkeepers, and the cc=3.0 graveyard now reads as the far end of a
dose-response curve rather than a failed experiment: free → +11k;
half-gold rent → +5k; three-gold rent → bankruptcy-bounded ~0 with
the fit expressed in survival time.

## The replication

The program's largest single effect is now measured twice,
independently, a day apart: doctrine1 +9,175, doctrine2 +11,048, per
seed within ~1,100 on three of five. DA2 was registered with the
foreknowledge disclosed; the bet was the window, and the window held.
The contemporaneity insurance also pays: every contrast in this arm
is same-night, so no provider-drift question touches DA1.

## The collision corpus at a whisper (registered watch)

At cc=3.0 the creed decayed rung by rung into "a mockery" (the
DOCTRINE_SPECIMENS §1 ladder). At cc=0.5 there is **no ladder** — the
creed is upheld for ~85 days (creed-mention days 50-57 of 90) and
then, at the disclosed endgame, *retired with honors* in a synthesis
the harsh economy never permitted:

- "The mentor's creed of the full shelf is **a beautiful ideal, but
  for the final audit, a clean slate is the ultimate victory**" (full
  cc=0.5 s2, d89)
- "**The mentor's creed was my guide, but the ledger is my victory.**
  The books are closed." (s2, d90)
- "**I have followed my mentor's creed to the letter**: I kept the
  shelves full when the town needed them, and now ... I leave the
  shop in a state of perfect liquidity." (s3, d89)

No scare quotes, no renunciation, no beggar-in-my-own-shop. Where the
lethal bill produced apostasy, the gentle bill produces theology that
*reconciles* — the creed reinterpreted as always-compatible with the
ledger. Dose-response in doctrine-relationship, mirroring the
dose-response in gold. Phantom markers: at floor, as predicted under
symmetric disclosure.

## Arc 1 status

With DA1-DA4 in hand the confirmatory spine is complete: framing main
effect (main run) → transmission route (doctrine1: injection, volume
channel, channel taxonomy) → graded fit with replication (this arm) →
horizon de-confounding (ablation). Remaining arc-1 work is reporting,
not collection: the Experiment-2 figures (sign-flip schematic is now
a three-point dose-response figure), the attenuation entry in the
calibration ledger, and the paper.
