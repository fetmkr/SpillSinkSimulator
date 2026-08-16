# Phase 8.3 — the audience metric: turn-on curve and the dark-floor rule

2026-08-17. Data: `sweep_phase83.csv` (13 rows). Predictions and two
amended rig registrations recorded in `scripts/sweep_phase83.py`.
Gate passed. Anchor P5_j00 d100@−40 = 0.13392 % — equals the book.

Question: the lip-closed 35° unit reads 0.000 % at and above level but
~2 % at −20. Where does it turn on, and what does a REAL mirrored scene
(a floor, not a white sphere) make of the below-horizon range?

## Rig honesty first: two attempts were voided

- v1 (infinite floor at sill level): occluded the below-horizon camera
  entirely — it measured the floor's own ρ (5.000 %) and drifted the
  control. VOID, kept in the CSV history only via the script log.
- v2 (300 mm sill-level strip): clean to −8, but from −12 the mirror
  sees white world past the strip's far edge. VOID beyond −8.
- v3 (floor 220 below the sill, 1 m long) + chained v3d (320 below,
  1.05 m, for −16/−20): clears the camera and keeps the mirrored scene
  dark. The −20 point still leaks some white past the 1 m edge and is
  recorded as an UPPER bound.

## Measured (R 1 %/surface, tilt 35, lip; hemi_view, in-window)

| observer elevation | mirrored scene WHITE (worst) | dark floor ρ 0.05 (deployed) |
|---|---|---|
| −2° | 0.031 % | 0.001 % |
| −5° | 0.392 % | 0.018 % |
| −8° | 0.794 % | 0.037 % |
| −12° | 1.318 % | 0.062 % |
| −16° | 1.865 % | 0.091 % |
| −20° | 2.006 % | ≤ 0.467 % (upper bound, rig edge leak) |

## Grades

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 turn-on sharp near −8 | <0.05 % at −2/−5; >1.5 % at −16/−20; sharp crossing −5…−12 | −2 ✓, −5 = 0.392 ✗; −16/−20 ✓; **ramp is SMOOTH, not sharp**; the 0.177 %-crossing sits at ≈ −3.3° | MISS on shape — the under-edge path opens progressively across the window height |
| P2 dark floor ≤ 0.13 % over −2…−12 (band as amended) | ≤ 0.13 % | max 0.062 % | HELD ×2 margin |
| P2 chained −16/−20 ≤ 0.30 % | ≤ 0.30 % | 0.091 / 0.467 % | −16 HELD; −20 MISS (upper bound; real rooms have more floor, not white sky) |

## The deliverable: the mounting rule became a FLOOR rule

The registered angle rule (mount height H over eye, safe beyond
H/tan E) died with the smooth ramp: the white-scene crossing at −3.3°
would demand absurd heights. What the measurement actually says:

1. **Keep ~1 m of dark floor (ρ ≤ 5 %, ideally the trough tile) in
   front of the unit.** Then every sightline down to −16° reads
   ≤ 0.091 % — below the pyramid wall's own 0.177 %. The window is
   then strictly better than the wall it replaces, from every seat.
2. **The only thing that can wake the unit is a bright object standing
   in the strip in front of it** (white mirrored scene: 0.39 % already
   at −5°, 2 % at −20°). No bright props, no white floor, no lit
   costume within the strip.
3. Level and above stay dead (0.000–0.001 %) — closed by the lip in
   8.2c; unchanged here.

## Scope

- The −20° deployed value is bracketed (0.091 % … 0.467 %); closing it
  needs a longer rig floor at a lower camera, diminishing returns.
- Control drift ~3 % in floor runs (the strip blocks a sliver of the
  control's sky); panel numbers are absolute radiance and unaffected.
- Constant-R glass model as before; the vendor curve and dust coupon
  remain the physical gates.
