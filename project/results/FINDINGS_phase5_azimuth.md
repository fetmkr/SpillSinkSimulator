# Phase 5 — azimuth of incidence, the axis nobody measured

Every number in phases 1-4 was taken at a single azimuth. `hemi_view` tilts the
camera in one plane, so theta was swept 0/+-20/+-40 and phi was silently zero.
The brief says the beam direction is unknown and effectively omnidirectional.

`blender_render.build_scene` now takes `phi_deg` and rotates the PANEL about its
own normal, which is equivalent to moving the source in azimuth and leaves the
control plate, the camera and the measurement windows untouched. The control
reads 0.0500 at every phi, which is the check that the rotation is sound.

## The result that matters: the ranking's top is safe

worst-theta rho_dh (%), worst over three coatings, mean over three seeds:

| design | phi 0 | 30 | 60 | 90 | spread |
|---|---|---|---|---|---|
| cone 5.5, jittered | 0.2160 | 0.2129 | 0.2167 | 0.2069 | **1.05x** |
| honeycomb 6.5/0.08 | 0.2228 | 0.2354 | 0.2282 | 0.2281 | **1.06x** |
| **blade 0.05, slotted grid** | **0.2065** | 0.2171 | 0.2153 | 0.2061 | **1.06x** |
| blade 0.05, all parallel | 0.2742 | 0.2535 | 0.2474 | **1.2422** | 5.02x |
| V-groove 13 mm | 0.3553 | 0.3363 | 0.2583 | **0.1777** | 2.00x |

**The three-axis leader is azimuth-safe.** Its published 0.2065 % is not one
lucky orientation; it holds to 6 % all the way round. So is the cone, and so is
the bought honeycomb. Nothing in the top of the ranking has to be re-scored on
a worst-over-phi basis.

Predicted before the render: cone <1.03x (FAILED, 1.05 -- jitter does not buy
full isotropy), honeycomb <1.10x (held), grid 1.10-1.30x (held, and better than
predicted at 1.06), parallel ~1.8x, V-groove the largest of the five (FAILED --
2.00x, and beaten by the parallel blade's 5.02x).

## An all-parallel blade array is a light pipe at one azimuth

The parallel array's 5.02x is one point, phi 90, and it is real -- not an edge
artifact. Tripling the margin from 2.0 to 6.0 depths moves it 2 % (1.26144 ->
1.23324 %); a margin artifact collapses instead, as the V-groove's did.

Two signatures name the mechanism:

    coating  d00 (pure specular) 1.26 %   d100 (pure diffuse) 0.07 %
    theta    0 deg 0.248 %   +-20 0.26 %   +-40 1.26 %

At phi 90 the blades lie along the tilt plane and form corridors. A ray
entering at 40 degrees runs down a corridor at grazing incidence, and grazing
is exactly where this coating's Fresnel term is largest, so a purely specular
ray survives many bounces and leaves. Add diffuse scattering and each bounce
kills it.

**This is the mechanism behind a phase 2 number that had none.** The slotted
grid beat the parallel array by 33 % and nobody could say why. Crossed slots
have no corridors.

## V-groove: opposite in sign to the prediction

phi 90 -- incidence ALONG the grooves -- is the DARKEST at 0.1777 %, half of
phi 0's 0.3553 %. Light that enters along a groove is trapped better, not
worse. This is the reverse of the intuition that an extruded profile leaks
along its own axis.

## The defect this sweep uncovered, and its blast radius

Rotating the V-groove 90 degrees made it read 28 % against a 1.14 % flat plate.
`loops_to_object` extruded the cross-section exactly `face_w` long: the 1D
families have `margin_depths` in Z and nothing along the extrusion axis, so a
rotated panel ran out before the window did.

**It was wrong at phi = 0 too.** With the overrun added:

| V-groove | voided | fixed | |
|---|---|---|---|
| 13 mm, tip 0.4 | 0.38628 % | 0.35532 % | -8.0 % |
| 7.5 mm, tip 0.4 | 0.35249 % | 0.34066 % | -3.4 % |
| serrated 20 mm | 0.45082 % | 0.40759 % | -9.6 % |
| **cone (control)** | 0.21599 % | **0.21599 %** | **+0.0 %** |

The cone is unchanged to every digit, and every 3D family differs from the
voided run by ~1e-7 relative -- the last bit of a float32 render buffer, not
geometry. The fix touched the extruded families and nothing else.

**665 rows across six sweeps were measured through `loops_to_object`** and are
high by roughly 3-10 %: `sweep_ridge*`, `sweep_v2`, `sweep_fairfight`,
`sweep_final4`, `sweep_cone3d`'s ridge rows, and phase 1. Phases 2, 3 and 4 are
untouched -- no 3D family goes through that path. Details in
`__void__README_extrusion.md`.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_azimuth.py
    Blender --background --factory-startup --python scripts/sweep_phase1.py
    python3 scripts/gate_sweep.py
