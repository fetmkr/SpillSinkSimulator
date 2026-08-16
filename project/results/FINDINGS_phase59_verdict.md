# Phase 5.9 — pyramid vs cone at the worst azimuth: a split decision, settled by which axis survives the real beam

2026-08-16. Data: `sweep_phase59.csv` (45 rows), `form_phase59.json` (3 full
form runs). Predictions and the verdict rule pre-registered in
`scripts/sweep_phase59.py`. `form_buildable.run_case` gained `entry["phi"]`
(panel rotates; stripe, control, windows fixed; phi-0 guard reproduced
smear 4.104 / head-on 0.02723 exactly — P1 HELD).

## Measurements

| | pyramid p2/d18 | thin cone p2/d18.2 | cone p5.5/d50 |
|---|---|---|---|
| total, φ0 | 0.13015 % | 0.21463 % | 0.21548 % (rewind: 0.2160, −0.2 %) |
| total, worst-φ | 0.22597 % (φ30) | ~0.215–0.225 (symmetric, jitter spread 1.05×) | same |
| smear φ0 / φ30 | 4.104 / **2.438** | 2.773 / — (φ-invariant) | 4.055 / — |
| head-on φ0 / φ30 | 0.02723 / **0.02718** | 0.04640 / — | 0.05951 / — |
| span@0 | 1.01× | 1.23× | — |
| panel incl. backing | 20 mm | 20.2 mm | 52 mm |

## Prediction grading

- P1 guard — HELD (exact).
- P2 head-on survives the worst azimuth — **HELD dead-centre** (0.02718
  vs 0.027 ± 0.008). At θ0 the beam runs along the rotation axis; azimuth
  cannot touch it, and now that symmetry argument is measurement.
- P3 smear degrades at φ30 — direction right, band missed (2.438 vs
  2.6–3.8). The grazing transport that inflated the φ30 totals takes the
  smear down with it.
- P4 cone anchor — HELD (−0.2 %).
- P5 cone scale invariance — HELD (0.21463 vs 0.216 ± 0.015). **A 20 mm
  cone panel exists**; the cone's only disadvantage (50 mm bulk) is gone.
- P6 thin-cone form — half: head-on 0.0464 in band; smear 2.773 far below
  the 4.0 ± 0.6 carried over from the big cone. Shrinking the cone against
  a fixed 2 mm stripe cuts its smear the same way it cut the pyramid's at
  coarse pitch — the beam/pitch class matters for every family.

## The verdict, by the pre-registered rule (worst-over-φ, win = >8 %)

- **Total**: pyramid 0.2260 vs cone 0.2146 → 5.3 % apart → **TIE**.
- **Smear**: cone 2.773 vs pyramid's worst-φ 2.438 → 13.7 % → **cone**.
- **Head-on**: pyramid 0.0272 vs cone 0.0464 → 41 % → **pyramid**.
- Axes 1:1:1 → tiebreak "thinner panel": 20.0 vs 20.2 mm — no
  discrimination. The pre-registered rule ends in a genuine draw.

## Breaking the draw with what Phase 5.5 already measured

The smear edge (cone's) is **protocol-conditioned**: at the real beam
(7–14 mm at the wall, LaserCube Ultra MK2), Phase 5.5 measured that smear
ratios compress toward ~1 for every design — the 2.4-vs-2.8 difference
will largely evaporate in deployment. The head-on edge (pyramid's) is
**beam-independent** (5.5 P2, held across every width) and now
azimuth-independent (5.9 P2). One edge survives contact with reality;
the other does not.

**Recommendation: the pyramid keeps the crown — p2/d18, tip ≤ 0.05 mm,
20 mm panel — with the honest caveat that its worst-azimuth total
(0.226 %) is cone-equal, not cone-beating. The thin cone (p2/d18.2) is a
fully valid alternate: azimuth-immune by construction, same panel, same
total, 1.7× brighter head-on.** If the die for sharp square tips proves
harder than a mould for jittered cones, switching costs one axis, not the
project.

Remaining unbought: one painted coupon (roughness → the 3–12× multiplier),
one beam-spot measurement, and the physical print of either field.
