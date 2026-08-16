# Phase 9.2 — tops-only paint: totals yes, head-on NO

2026-08-17. Data: `sweep_phase92.csv` (46 rows), `form_phase92.json`.
Predictions pre-registered in `scripts/sweep_phase92.py`. Anchor
P5_j00 d100@−40 = 0.13392 % — equals the book to all digits.

The user's question: paint only the tip region from the front
(도료비 1/16). The registered decision rule: ship iff paint_depth 5
gives total ≤ 0.35 % AND head-on ≤ 0.06 (beam 7.5 mm).

## Grades — every prediction missed high, and the miss is the finding

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 top 2 mm (1 % of area) | 0.55 ± 0.20 % | 0.829 % | MISS high |
| P2 top 5 mm (6 % of area) | 0.35 ± 0.15 % | 0.561 % | MISS high |
| P3 top 10 mm (25 % of area) | 0.22 ± 0.05 % | 0.290 % | marginal MISS |
| P4 head-on at top-5 (beam 7.5 mm) | 0.05 ± 0.02 | **0.113** | **MISS ×2.3 — unchanged from bare 0.107** |
| (smear at top-5, beam 7.5 mm) | recorded | 1.202 | — |

Bounds for reference (book): bare 0.907 % / 0.107; full Musou
0.177 % / 0.040.

**Decision rule: FAILED on both counts. The front-spray tier does not
ship.**

## The law the misses bought: the two axes weight depth OPPOSITELY

- **Totals are earned at the TOP.** At oblique incidence the beam-facing
  flank shadows the cell; lit area and sky-view (escape) both
  concentrate near the tips. Measured: top-10 paint (25 % of area)
  buys 0.29 % — far better than area-proportional (0.72 % by the
  ρ-average model). Partial paint IS leveraged for totals.
- **Head-on is earned EVERYWHERE (area-weighted), i.e. mostly at the
  BOTTOM.** At normal incidence nothing shadows: the stripe lights the
  whole face down to the valley, the camera sees that whole face, and
  each element returns ρ/π toward it in one bounce. The visible-area
  ρ-average predicts head-on almost exactly: top-5 leaves 94 % of the
  area bare → 0.107 × (4.75/5) = 0.102 ≈ measured 0.113. Painting the
  cheap 6 % cannot move a number owned by the expensive 94 %.
- Consistency check the other way: the totals CAN'T be area-weighted
  (0.29 ≠ 0.72) and the head-on CAN'T be top-weighted (0.113 ≠ 0.05)
  — the two axes genuinely invert the depth weighting. This also
  retro-explains the tip ladder: tip flats moved head-on because they
  add FLAT area facing the camera, not because the top is special.

## What survives for the 100-panel plan

The two-tier menu stands unchanged, now with its middle option
measured and priced out:

| tier | total | head-on (beam 7.5 mm) | paint |
|---|---|---|---|
| full Musou (critical zones) | 0.177 % | 0.040 | 100 % |
| top-10 front-spray | 0.290 % | ~0.11 (deep-owned) | 25 % |
| bare black ρ0.05 | 0.907 % | 0.107 | 0 % |

Front-spray buys totals only. Since bare's weak axis is ALSO head-on
(0.107), a zone that tolerates bare head-on tolerates bare totals in
practice — the middle tier earns its paint bill only where a zone
needs tighter TOTALS specifically (e.g. integrating-glow-limited
scenes) while its head-on is unseen. Named a niche, not a tier.

## Scope notes

- Deep material: Lambertian ρ 0.05 (the 9.1 bare-black assumption).
- Sharp paint boundary (paint_fade 0); a real spray fades — softer
  boundary can only interpolate between the measured points.
- Smear at top-5 (1.20, beam 7.5 mm) sits between bare (1.38) and
  full (1.42) — no new information on that axis.
