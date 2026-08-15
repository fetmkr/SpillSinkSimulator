# 04 · peak radiance ratio

**Status:** live as of 2026-08-11 · **proposed as the primary figure of merit**
· first results are striking and **not yet trusted** — see Open question below

## Definition

The peak of the returned line profile, divided by the peak the same beam
produces on a plain matte black wall:

    peak_ratio = max_z panel_profile(z)  /  max_z control_profile(z)

Panel and control are lit by the **same stripe in the same frame** (`add_stripe`
is handed the full width, control included), so the ratio is in consistent
units and needs no calibration.

## Why this metric exists

Total reflectance ([01](01_rho_dh.md)) and smear ([02](02_smear_rms.md)) have
been optimised separately all along, and neither answers the actual question:
**is the copy of the artwork on the wall visible?**

That depends on the brightness of its brightest point, which folds both
together. Spread the same energy over 4× the width and the peak drops 4×. A
design that returns 100× less light but perfectly sharp, and one that returns
2× less but formlessly smeared, are indistinguishable to 01 and 02 taken
separately, and obviously different to a viewer.

It also matches how the source literature thinks about it: perceived darkness
separates materials only at high light intensity (Filip & Vávra Fig. 8, and our
regime is their 100× case), and what separates them there is residual peak
brightness, not integrated reflectance.

## Baseline

The **0.05 diffuse control plate in the same frame** — a plain matte black wall.
`peak_ratio = 0.01` means the brightest point of the wall copy is 100× dimmer
than it would be on plain black paint.

## First results — coating ρ 0.005, tip 0.4 mm across, from `results/form_v2.json`

| design | θ = −40° | θ = 0° |
|---|---|---|
| 1D V-groove d50 / p13 | 0.0004 | **0.0013** |
| 1D V-groove d30 / p7.5 | 0.0457 | 0.0319 |
| 3D cone d30 / p7.5 | **0.0002** | 0.0103 |
| 3D cone d30 / p3.75 | **0.0002** | 0.0451 |
| flat wall (control) | 1.0 | 1.0 |

Two things stand out, and **both are things ρ_dh could not see**:

1. **The ranking at θ=0 is the opposite of the ranking at −40°.** Head-on, the
   deep coarse groove is best (0.0013) and the fine cone is worst (0.0451) —
   while hemispherically the cone is the darker of the two. Read literally:
   head-on, cone tips send light back toward the observer, and the deep groove
   sends it somewhere else.
2. **The differences are far larger than ρ_dh suggests.** At −40° the cone beats
   the fine groove by ~230× on peak while being only ~4.7× darker in ρ_dh. What
   reaches the *observer* is not what leaves the surface.

If both survive checking, the head-on case — the one axis nothing has ever
improved — turns out to be rankable after all, and the current recommendation
may be wrong.

## OPEN QUESTION — check this before quoting any number above

**The 1D groove numbers may be an artifact of where the stripe landed.**

The grooves are extruded along X. The measurement stripe is also a line of
constant Z running along X. So the stripe lies **parallel to the grooves** and
falls either on a ridge tip or into a valley, and the answer differs enormously
between those cases. `form_mtf.LINE_Z` samples only **three** Z positions,
chosen "deliberately not on the slat pitch" — which avoids resonance but does
not average over groove phase. At pitch 7.5 mm, three samples is not a sampling
of phase, it is three arbitrary draws.

The 3D cone array is far less exposed to this: it is irregular in both axes.
That asymmetry is itself a reason to distrust a groove-vs-cone comparison made
this way.

**The check:** sweep the stripe's Z position across one full groove pitch in
fine steps and look at the spread of peak_ratio. If it is large, the metric
needs phase averaging before any 1D number from it is reportable — and the
striking results above are provisional until then.

## What it does NOT capture

- **One viewing direction at a time.** peak_ratio is measured from the camera
  position used for that θ. A design can be dim from one direction and bright
  from another; the bird-of-paradise cavities are *built* to do exactly that.
- **Absolute visibility.** It says "N times dimmer than a plain wall", not
  "invisible". Turning that into a yes/no needs the real beam irradiance and a
  contrast threshold, which is [an open input](../reference/SUMMARY.md).
- **Peak is a per-pixel maximum**, so it is noisier than an integral and depends
  on resolution. Panel and control share both, so the *ratio* is robust to first
  order — but a very sharp panel line could be under-resolved. Not yet
  quantified.
- Same head-on collinearity caveat as 02 applies to the *smear*; it does not
  apply to this metric, which is precisely why this metric is interesting.

## Computed by

`scripts/metrics.py`, reading a `form_mtf` result JSON. The `peak` field has
existed in `form_mtf.stats` all along; nothing was reading it.
