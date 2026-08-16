# Phase 9.c — the wall-floor corner needs no special treatment

2026-08-17. Data: `sweep_phase9c.csv` (13 rows). Predictions
pre-registered in `scripts/sweep_phase9c.py` (two d00/+20 preview cells
marked postdictions there). Gate passed. Anchor 0.13392 % — book exact.

The venue photo shows spill brightest along wall-floor junctions, and
design law 1 says smooth concave ~90° corners are retroreflectors. Two
pyramid panels butting at 90° were never measured. Scene: wall field +
floor field running toward the camera; observers at +20/+40 (audience
eyes sit above the corner); window reads the corner-zone assembly;
control drifts ~3 % (floor shades a sky slice, as in 8.3) — absolute
panel means are the record.

## Measured (worst over d00/d100 × +20/+40)

| scene | worst | cells |
|---|---|---|
| pyramid wall alone (reference) | 0.175 % | d100@40 owns it |
| pyramid corner | **0.146 %** | ×0.84 of its own wall |
| smooth-Musou corner | 0.519 % | d100@20 owns it |

## Grades

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 smooth corner 1.0–1.6 % | as stated | 0.519 % | MISS LOW — good direction |
| P2 pyramid corner 0.8–1.5× its wall | as stated | ×0.84 | HELD |
| P3 corner penalty ≥3× larger for smooth | as framed | both corners read BELOW their walls; no penalty exists to compare | MISS — the premise died |

## What the misses taught

Under diffuse illumination an inside corner is DARKER than its two
faces in the open: each face blocks half the other's sky near the
junction (mutual shading), and with Musou on both faces the two-bounce
specular retro path multiplies two small factors (the d00 cells bound
it at 0.03–0.12 %). The retroreflector disease of design law 1 belongs
to HIGH-reflectance smooth folds seen against a beam — the zigzag's
1.171 % — not to Musou-coated room corners under ambient-style
transport.

**Registered decision rule, applied: corners need no cove strips, no
fillets, no rules — panels simply butt at 90°.** The build sheet
stays one line shorter.

## Addendum 2026-08-17 — the VERTICAL (wall-wall) corner is covered by symmetry

The venue photo also shows wall-wall junctions. No new measurement is
needed: under the uniform (isotropic) world, rotating the entire
wall-floor corner scene 90° about the VIEW axis turns it into the
wall-wall corner while leaving every ρ_dh unchanged — the illumination
is direction-free and the camera axis does not move. The 9.c numbers
therefore apply to vertical corners verbatim. The two mechanisms behind
them (mutual sky-shading near the junction; the Musou two-bounce
product) are orientation-free as well. A draft vertical-corner scene
was built, previewed, found to have a 60 mm junction gap and an
unframeable geometry for the elevation-tilt camera, and removed in
favor of this exact argument.

## Scope

- Hemi totals at +20/+40 only; a beam aimed exactly into the corner
  bisector still retroreflects its specular residual toward the source
  (the d00 cells bound that class at ≤0.12 % here). No form run: the
  corner zone has no periodic structure of its own.
- The corner scene's window mixes wall and grazing-floor views; the
  numbers are assembly numbers, matching what an elevated viewer of
  the junction sees.
