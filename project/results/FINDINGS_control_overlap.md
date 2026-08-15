# 2026-08-12 — the flat control plate has been embedded in the panel all along

**Status: cause proven, scope measured, fix NOT yet applied.**
Test: `scripts/test_control_gap.py` -> `results/test_control_gap.json`.

## The symptom

`results/sweep_topo.csv`, control column, which must read 0.05000 in every row:

| topology | exposed area | control mean | control min |
|---|---|---|---|
| truss | 1.58 % | 0.05000 | 0.05000 |
| shingle | 1.12 % | 0.04999 | 0.04997 |
| cone | 0.26 % | 0.04987 | 0.04963 |
| **honeycomb** | **13.20 %** | **0.04234** | **0.02527** |

1440 of 2875 rows read low. The deficit tracks the panel's own exposed area
exactly: 0.05 x (1 - 0.0026) = 0.04987 for the cone, against 0.04987 measured.

## The cause

`blender_render.GAP = 100` mm places the control plate at x = 160..220. The
panel field runs to `face_w + margin_depths * depth` = 60 + 6.5 x 30 =
**255 mm**. The control plate is *inside the panel geometry*, and its top face
sits at Y = 0 — exactly where the cell wall tops and cone tips are. Dark panel
material occupies part of the control window, and the control reads its own
area fraction darker.

Confirmed directly: moved to GAP 500, clear of the field, the control reads
**0.050000** in every case.

## This is not new. It has always been true.

Every 3D family has had a margin larger than the gap. It stayed invisible while
every family was a pillar array exposing well under 1% of its area — the cone's
0.13% deficit is inside the noise anyone would have looked at. A wall network
exposing 13% made it visible. **Every control figure ever recorded in this
project for a 3D family is low by that family's exposed fraction.**

## What it does and does not invalidate — MEASURED, not argued

Same design, same pixels per mm, GAP 100 vs GAP 500:

| case | theta | panel @100 | panel @500 | shift |
|---|---|---|---|---|
| honeycomb p7.5 d30 | 0 | 0.003593 | 0.003614 | **-0.59%** |
| honeycomb p7.5 d30 | -40 | 0.001523 | 0.001523 | **+0.01%** |
| cone p7.5 d30 | 0 | 0.002331 | 0.002276 | +2.43% |
| cone p7.5 d30 | -40 | 0.002590 | 0.002585 | +0.17% |

The honeycomb — whose control moves 9% — moves its panel figure by under 0.6%.
The cone's +2.43% at theta = 0 is about twice the project's ~1.3% measurement
floor and is not distinguishable from Cycles sampling noise on a panel reading
0.0023 at 64 spp.

**So: absolute rho_dh, the headline metric, stands. What does not stand is any
ratio taken against the control, and `lock.py`'s control assertion.**

### A correction to the first version of this test

The first run reported the cone's theta = 0 moving **7.07%**, which would have
been a serious result. It was an artifact of my own test. `run()` derives
`ortho_scale` from the total scene width, so widening the gap at a fixed
`res_x` samples the panel at 620/220 = 2.8x fewer pixels per mm. Scaling
`res_x` with the width — holding pixels per mm constant, which is the whole
point of the comparison — brings it to 2.43%. **The 7.07% figure was measuring
my resolution change, not the geometry.**

## Fix options, none applied

Not applied because `sweep_topo.py` is running and a scene-layout change
mid-sweep makes rows before and after incomparable.

1. **Raise GAP past the field.** Correct and simple, but it changes
   `ortho_scale` for every render, so `res_x` has to scale with it or the
   sampling density silently changes — as this test just demonstrated. Every
   past control figure would need re-running for the control column to be
   comparable.
2. **Clip the panel mesh in +x before the control.** Keeps the layout, but the
   margin is load-bearing and not fully understood: `sweep_shapes.py` records
   that margin 1.0 moved head-on by -15% "and the reason is not yet
   understood, so it stays". Clipping asymmetrically in one axis is the kind of
   change that should not be made against an unexplained sensitivity.
3. **Render the control in its own frame.** Cleanest physically, twice the
   render cost, and loses the "same frame, same sampling" property that is the
   reason the control exists at all.

Option 1 with matched `res_x` is the recommendation. It should be done as a
deliberate re-baseline, not slipped in.
