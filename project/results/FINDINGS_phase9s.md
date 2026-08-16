# Phase 9.s — the seed debt, paid: single-seed numbers carry sub-1 % noise

2026-08-17. Data: `sweep_phase9s.csv` (12 rows). Predictions
pre-registered in `scripts/sweep_phase9s.py`. Gate passed.

Phase 5 closed with an honest debt: every published number is one Cycles
seed. Three seeds {0, 7, 23} on the two cells everything hangs from:

| cell (d100, 64 spp) | seed 0 | seed 7 | seed 23 | spread |
|---|---|---|---|---|
| anchor (aspect 9) at −40° | 0.13392 % | 0.13293 % | 0.13316 % | ±0.37 % rel |
| anchor at 0° | 0.06007 % | 0.06002 % | 0.06062 % | ±0.50 % rel |
| final sample at −40° | 0.17668 % | 0.17590 % | 0.17530 % | ±0.39 % rel |
| final sample at 0° | 0.09750 % | 0.09774 % | 0.09772 % | ±0.13 % rel |

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 anchor cell ±3 % across seeds; seed 0 = book | as stated | ±0.5 %; 0.13392 exact | HELD |
| P2 final cell ±3 %; seed 0 = the 515 CSV cell | as stated | ±0.4 %; 0.17668 exact | HELD |
| P3 θ-ordering seed-stable | no rank flip | −40 worst at every seed, both designs | HELD |

Verdict: at 64 spp the Monte-Carlo noise on these cells is under
±0.5 % relative — an order of magnitude inside every prediction band
ever graded against them. The single-seed convention stands; no
FINDINGS needs a noise caveat. (The cone's larger 4.5 % spread in 5.11
was over its full worst-over-φ pipeline, not one cell.)
