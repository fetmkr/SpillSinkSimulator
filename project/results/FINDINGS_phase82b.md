# Phase 8.2b — the 35-degree build, measured; the top strip found

2026-08-17. Data: `sweep_phase82b.csv` (20 rows), `form_phase82b.json`.
Predictions pre-registered in `scripts/sweep_phase82b.py`. Anchor
P5_j00 d100@−40 = 0.13392 % — equals the book.

Why this ran: report 8.3 grew the device tilt from the measured 25° to
35° on mirror arithmetic alone. Directions are arithmetic; the measured
quantities moved in ways the arithmetic did not predict.

## Grades (R 1 % per surface; geometry: plate 155, void 130)

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 hemi θ0 | 0.40 ± 0.15 % | **0.000 %** | MISS low — see the top-strip finding |
| P2 hemi θ−20 | 1.0 ± 0.3 % | 2.006 % | MISS ×2 (under-edge back-face path dominates) |
| P2 hemi θ−40 | 1.2–2.0 % | 1.996 % | HELD (at band edge) |
| P3 hemi θ +20/+40/+50/+70 | < 0.05 % | 0.001 / 0.000 / 0.000 / 0.000 % | HELD |
| P4 danger spike at θ−70 | ratio > 100 | **0.000** (and ≤ 0.001 everywhere scanned, −75…+70) | MISS — the spike VANISHED from the window; see below |
| P5 form head-on (beam 7.5 mm) | < 0.001 | 0.0000015 | HELD |
| P5 smear | not gradeable (zero return), pre-registered | NaN | as registered |
| P6 system θ0 / +20 / +40 | 0.55±0.25 / 0.15±0.08 / 0.05±0.04 % | **0.030 / 0.038 / 0.005 %** | θ0 MISS ×18 GOOD direction; +20/+40 HELD |

## The finding: at 35° everything interesting retreats to a TOP STRIP

The renders (not the window numbers) explain every miss. The
measurement window samples the central 40 % of the face (the standard
30 % z-inset, same convention as every published number, including
tilt 25's). At tilt 35:

- The mirror path of a level sightline (elev −70) clears the box sill
  only from the TOP ~25 % of the glass (z above ~+24 of ±50). The
  render shows exactly that: a 2R speckle band at the top, black
  everywhere below. The band lies entirely above the window → 0.000 %.
  At tilt 25 the same threshold sat below the window → 1.85 %.
- The danger glint (beam from −70 mirrored to a level viewer) needs the
  same strip AND a beam that first clears the sill from below — the
  scan found nothing at any angle because the strip is outside the
  window and the sill eats the deep paths. The spike did not move from
  −50 to −70; it left the sampled field entirely.
- Below-horizon observers (−20/−40) still read full 2R through the
  under-edge back-face path (2.00 %, as at tilt 25). Physical
  deployment: those sightlines rise from the floor.

**Design consequence, adopted into 8.3: extend the rim cover lip over
the top 25 % of the glass.** The strip is the ONLY place where (a) the
residual can exit toward the room and (b) a level viewer can catch a
mirror. A tile-clad lip over it removes both, the shelf becomes
optional, and the unit is fully self-contained. Cost: the glass and
aperture grow ~25 % taller than the optical opening.

## System numbers (in-window, worst case uniform world)

0.030 % (θ0) / 0.038 % (+20) / 0.005 % (+40) — all under the 0.05 %
audience-visible target that report 8.1 registered, and 5–35× below
the pyramid wall's own 0.177 % on the same axis. Form head-on
0.0000015 at beam 7.5 mm.

## 8.2c chained check — the lip, measured same day

Predictions registered in the chained script before render (lip covers
z +22 to +79.5, idealised black; the real lip is tile-clad):

| claim | prediction | measured | grade |
|---|---|---|---|
| C1 hemi θ0 with lip | 0.000 %, top speckle band GONE in render | 0.000 %, band gone (render checked by eye) | HELD |
| C2 hemi θ−20 / −40 | unchanged 1.9–2.1 % | 2.006 / 1.711 % | −20 HELD; −40 slightly BELOW band (lip clips part of the under-path — good direction) |
| C3 scan θ−70 with lip | 0.000 | 0.000 | HELD |
| C4 system θ0 with lip | 0.030 ± 0.010 % | 0.022 % | HELD |

The lip closes the strip in the render, not just in the window
statistics. With it the unit has no residual exit, no danger direction,
and the shelf drops to optional.

## Honest scope

- In-window numbers sample the central 40 % of the aperture. The top
  strip was caught qualitatively (speckle in the render); the 8.2c lip
  runs then removed it and the render confirms the band gone, so the
  lip-closed unit's whole aperture now behaves like the window.
- Constant-R model as before; museum-glass R(θ=35°) and the dust
  coupon remain the physical gates.
