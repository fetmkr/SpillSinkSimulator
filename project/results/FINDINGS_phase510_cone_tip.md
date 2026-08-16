# Phase 5.10 — the cone's weakness is its tip cap (fixable); the pyramid holds to pitch 1 (11 mm panel)

2026-08-16. Data: `sweep_phase510.csv` (90 rows), `form_phase510.json`.
Predictions pre-registered in `scripts/sweep_phase510.py`.

## Part 1 — the cone's head-on decomposed

Question: is the thin cone's 1.7× head-on penalty (0.0464 vs pyramid
0.0272) the rounded TIP CAP or the three-cusp INTERSTICES between bases?

| cone p2/d18.2 | total (worst 3 mats × 5θ) | smear | head-on | span@0 |
|---|---|---|---|---|
| tip r 0.073 (5.9 anchor) | 0.21463 % | 2.773 | 0.04640 | 1.23× |
| **tip r 0.03** | 0.21222 % | 2.684 | **0.03170** | 1.06× |
| tip r 0.15 | 0.22657 % | — | — (not form-run) | — |

- **P1 (head-on = base + k·r², base = pyramid's 0.027): the r 0.03 point
  landed dead in band (0.0317 vs 0.030 ± 0.005) — the TIP CAP owns the
  penalty.** Caveat: the r 0.15 leg of P1 (predicted 0.109) was not
  form-measured this run; the claim is bought at the decision-relevant
  end only.
- P2 HELD: totals move ±8 % max across radii (−1.1 %, +5.6 %).
- P3 near-miss by definition: parity band was "within 15 %", measured
  16.4 % (0.0317 / 0.0272). Physically: the gap shrank from 1.7× to
  1.17×.
- P5 HELD: smear 2.684 (band 2.77 ± 0.5), span 1.06×.

## Part 2 — the pyramid's thin end

| pyramid, aspect 9 | total | panel incl. backing | tip tolerance (5.8 interp.) |
|---|---|---|---|
| p2 / d18 | 0.13015 % | 20 mm | 0.05 mm (measured rule) |
| p1.5 / d13.5 | 0.12974 % | 15.5 mm | ~0.033 mm [추측] |
| p1 / d9 | 0.12952 % | 11 mm | ~0.022 mm [추측] |

P4 HELD twice: the aspect law now spans pitch 1 → 10 (5 confirmations).
**An 11 mm panel exists optically; its price is a 0.022 mm tip.**

## Updated standings (worst-over-φ where measured)

| | pyramid p2/d18 t≤0.05 | cone p2/d18.2 r0.03 |
|---|---|---|
| total, worst-φ | 0.226 % (φ30) | **0.212 %** (φ-invariant) |
| smear (protocol beam) | 2.44 (φ30) | 2.68 |
| head-on | **0.0272** (φ-proof) | 0.0317 |
| span@0 | 1.01× | 1.06× |
| panel | 20 mm | 20.2 mm |
| azimuth behaviour | +74 % hole at φ30 (priced in above) | immune by symmetry |

By the 5.9 rule (>8 %): total tie (6.4 %), smear cone (+10 %,
protocol-conditioned — compresses at the real beam), head-on pyramid
(+14 %, beam- and φ-proof). **Still 1:1:1 — but the gap the pyramid's
crown rests on narrowed from 1.7× to 1.17×, and the cone is the only
design whose worst case needs no azimuth caveat at all.**

Practical read: the choice is now a MANUFACTURING question, not an
optical one — a press die holding a ≤0.05 mm square tip (pyramid) versus
a mould holding a ≤0.03 mm tip radius (cone) [모름: which is easier —
ask the toolmaker, not the simulator]. Optically the two are within 15 %
on every axis that survives deployment.

## Grading

P1 held at the measured end (r 0.15 leg unbought) · P2 HELD · P3 missed
by 1.4 points of a 15 % band · P4 HELD ×2 · P5 HELD.
