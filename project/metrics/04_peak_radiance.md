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


## MEASUREMENT CONDITIONS (added 2026-08-20 — this axis is the fragile one)

This is a **PEAK**, and that makes it behave unlike the other two axes. An area
average (metric 01) and a ratio of two widths in one frame (metric 02) both
survive a coarse pixel, because the coarsening happens to numerator and
denominator alike. A peak has nothing to cancel against: enlarge the pixel and
the peak is averaged with the darkness beside it, always downward, on the one
axis that says whether the audience is dazzled.

Measured, order spec, panel 100 mm:

| density | smear (metric 02) | head-on (this metric) |
|---|---|---|
| 0.215 mm/px | 2.238 | 0.1835 |
| 0.600 | 2.232 | 0.1064 |
| 1.200 | 2.227 | 0.0821 |

**The peak comes from the smallest observer-facing feature** — a pyramid's tip
flat, a honeycomb's wall top, a blade's edge — so the density that matters is a
ratio to THAT, not a global constant:

> **mm per pixel = min feature / 4**

The 4 is measured, not chosen: pixels-across-the-tip was swept 1, 2, 4, 8, 16
and the answer settled at 4 (0.15024 / 0.16979 / 0.18898 / 0.18907 / 0.18874).

At the old 0.215 mm/px protocol:

| design | min feature | pixels across it | under-resolved by |
|---|---|---|---|
| pyramid p4 / tip 0.4 | 0.40 mm | 1.86 | 2.1x |
| pyramid p4 / tip 0.1 | 0.10 mm | 0.47 | 8.6x |
| honeycomb 6.5 / wall 0.08 | 0.08 mm | 0.37 | 10.8x |
| blade 0.1 | 0.10 mm | 0.47 | 8.6x |

Three of those are SUB-PIXEL. **Every published head-on is low, and the finer
the feature the lower**, which distorts comparisons between designs and not
just their absolute values:

| design | published | resolved |
|---|---|---|
| pyramid tip 0.4 (order spec) | 0.173 | **0.189** |
| pyramid tip 0.1 (study std) | 0.040 | **0.0677** |
| the penalty for relaxing the tip | 4.3x | **2.8x** |

**Measure it on a 10-cell patch, not the panel.** A peak is local, and this was
checked rather than assumed: a 40 mm patch returns 0.18919 against 0.18881 and
0.18895 from full 100 and 200 mm panels at the same density -- 0.2 %, and 25x
faster. Resolving a honeycomb wall across a 400 mm panel is 15 000 px and hours
per row; ten cells of it is minutes.

**Panel size does not matter once the feature is resolved** (0.18881 at 100 mm,
0.18895 at 200 mm). What looked like a sample-size dependence was the pixel
coarsening as the scene grew.

**Measure at theta = 0.** It is in the name and it is easy to get wrong; a
-40 deg peak ratio for the order spec reads 0.0466 against 0.189 head-on.

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
