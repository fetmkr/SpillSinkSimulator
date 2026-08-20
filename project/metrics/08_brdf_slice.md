# 08 · in-plane BRDF slice — where the light goes

**Status:** live · **The first directional metric in the project**

## Definition

The bidirectional reflectance distribution function, in 1/sr, sampled on a grid
of incidence angle against observation angle, both in one azimuth plane:

    f_r(θ_in, θ_out)   for θ_in ∈ [-80, 80], θ_out ∈ [-85, 85]

Both angles are measured from the panel normal, positive = above, the same
convention `blender_render.setup_camera` and `sun_rotation_for` already use. On
the resulting map three questions are three straight lines:

| line | what it is |
|---|---|
| θ_out = +θ_in | **retro** — straight back at the projector |
| θ_out = −θ_in | the flat-mirror specular direction |
| θ_out = 0 | **the audience** |

This is the metric `metrics/01` names as its own blind spot:

> **Where the light goes.** ρ_dh is a single scalar; a design that returns the
> same energy as a sharp line and one that returns it as a wide smear score
> identically.

## How it is measured

A sun at θ_in and an orthographic camera at θ_out — the beam-and-camera
geometry, *not* the reciprocity trick, because reciprocity integrates over
exactly the axis this metric resolves.

**The flat Lambertian control plate in every frame does the whole
normalisation, analytically.** A Blender sun of energy E delivers E W/m² to a
surface facing it, so a panel whose normal is +Y receives E·cos θ_in, and:

```
control radiance   L_c = (ρ_c/π) · E · cos θ_in
panel radiance     L_p = f_r(θ_in, θ_out) · E · cos θ_in

  ⇒   f_r  =  (L_p / L_c) · ρ_c / π        [1/sr]
```

E and cos θ_in cancel. There is **no bin solid angle, no cos θ_out division and
no source calibration** — the BRDF comes out absolute from a ratio of two window
means in one frame, the same shape as every other number in this study. Both
forms are recorded per cell: `brdf` through the measured control, and
`brdf_analytic` through the closed form, so the two can be compared and a
shadowed or clipped control cannot pass unseen.

**The bin width is the sun's angular size.** `add_sun`'s own docstring records
why a delta source against a specular surface is unusable. Here the source
diameter is set equal to the θ_in sampling step, which makes each column an
honest bin average instead of a delta with a fudge factor. It is written into
every row.

Windows are `rig_v2`'s full-face ones. The world is 0.0, so there is no sky to
shield against — rig_v2's own docstring says full-face is correct for a
black-world path "and only there", and this is one.

Computed by `scripts/bidir.py`, swept by `scripts/sweep_bidir.py`, drawn by
`scripts/plot_bidir.py`, gated by `scripts/gate_bidir.py`.

## Baseline

Absolute, in 1/sr. No baseline needed to state a cell.

When a ratio is quoted it must name its baseline, and it is one of:

- **a flat plate of the same coating** — `bidir.flat_plate()`, a single quad
  through `build_scene`'s `prebuilt_mesh` door
- **a perfect Lambertian** — f_r = ρ/π, the same in every direction

## What it does NOT capture

- **THE COATING'S BRDF SHAPE IS UNVALIDATED, AND THAT IS EXACTLY WHAT THIS
  METRIC READS.** `metrics/01` states it plainly: *"the coating fit constrains
  only ρ_dh(θ) of a flat plate. Nothing in it constrains BRDF shape or
  multi-bounce behaviour."* Every other metric here integrates over the
  unconstrained axis; this one resolves it. The *structure* of a map — where
  the ridges are, whether the retro line is populated, whether a feature moves
  when the geometry moves — is a geometric result and stands. **No absolute
  cell value is quotable until a coating coupon is measured on a goniometer.**
  This is the strongest argument the project has yet produced for closing
  README open item 4.
- **AN IN-PLANE SLICE CANNOT ANSWER A QUESTION ABOUT A ROOM.** This is the
  right instrument for characterising a surface and the wrong one for
  predicting what an audience sees, because a room lights every point from
  every azimuth at once. On the laser rig this study is for, only 24.5 % of the
  light reaching an eye arrives near retro and 17.7 % near specular — the two
  directions a slice can reach — while the mode sits at Δφ = 150°. Publishing
  an audience figure off a slice produced a number wrong by 3.5×
  (`results/FINDINGS_audience_azimuth_2026_08_21.md`). `add_sun` now takes a
  `phi_deg`; use `metrics/09` for anything room-shaped.
- **One azimuth plane.** There is no hemisphere integral in a slice, so no TIS
  — `metrics/05` stays planned until an azimuth axis is added. The single
  exception is normal incidence, where the BRDF is azimuthally symmetric and
  the integral closes; `gate_bidir` G6 uses it.
- **THE COATING MODEL IS NOT RECIPROCAL, and this metric is what shows it.**
  Measured on a flat plate: f(0,80)/f(80,0) = 0.681 off the lobe at 1024 spp.
  The Fresnel mix keys off the view direction, so the diffuse arm's weight
  follows the camera. A Lambertian's slice integrates back to ρ_dh(0) to
  −0.98 %; the coating's to +23.17 %, same rig, same quadrature. Reciprocity
  residuals in this map are therefore *partly the material*, not only sampling
  — and `metrics/01`'s reciprocity trick rests on the property that fails.
  See `results/FINDINGS_bidir_2026_08_20.md`.
- **Asymmetric bin widths.** θ_in is bin-averaged by the sun's angular size;
  θ_out is a delta direction. Reciprocity is therefore approximate by
  construction, and its residual is a *sampling* diagnostic rather than a
  physics one.
- **Wavelength and polarisation.** One broadband grey channel, no polarisation,
  as everywhere else in this study.
- **The observer's solid angle.** A cell is a BRDF, not a brightness. Turning it
  into "how bright does this look" needs the rig's real beam and pupil, which is
  README open item 1.

## Validation

Measured 2026-08-20, `scripts/gate_bidir.py`:

- **A flat Lambertian reads ρ0/π in every cell, to 0.00 %** — at every
  incidence and every observation angle, on a single-quad plate of ρ0 = 0.20.
  The rig has no residual of its own.
- **The 0.05 control plate reads ρ_c/π·cos θ_in** to 0.00 % for |θ_out| ≤ 40
  and 0.23 % at ±80, the remaining figure being one pixel of quantisation on a
  window the tilt has compressed.
- **G2** the fitted coating's flat plate peaks on the mirror direction, and the
  peak grows toward grazing (the Fresnel behaviour `metrics/01` quotes as
  0.998 % → 3.086 % between 0 and 80°).
- **G3** reciprocity across the map, reported as a residual with its cause
  named rather than as a pass mark.
- **G4** density indifference — a window mean under a directional source is an
  area average, so it should behave like the totals axis (0.9 % over 13×) and
  not like head-on (55 % over 5.6×).
- **G5** margin on the **illumination** side, which nothing in this repo had
  ever checked.
- **G6** at normal incidence the slice integrates back to
  `materials.Material.rho_dh(0)` for a **reciprocal** material — measured
  −0.98 % on a Lambertian, the predicted truncation. The fitted coating comes
  in at +23.17 %, and G6 reports that as the size of the coating's
  non-reciprocity rather than as a rig failure.
- **G7** off-lobe reciprocity of the material itself, reported never gated.

## Known defects, fixed

- **The flat plate did not cover its own window.** `lock.py`'s
  `CASES["flat_coating"]` — a degenerate ridge, pitch 50 on a 100 mm face —
  lays its two periods over z −25..+75, so a full-face window reads 25 %
  background as if it were sample. Measured: a Lambertian 0.20 read 0.047654
  against the 0.063662 it owes, exactly the 0.7485 coverage. The stock rig's
  30 % z inset hid it, because z −20..+20 sits inside the covered band; opening
  the window (rig_v2 D3) is what exposed it. Now refused by
  `rig_v2.assert_window_covered`.
- **The control plate read 0.3–0.4 % high.** `make_flat_plate` builds it as
  exactly the face rectangle, so a full-face window ends on the plate's own edge
  and its outermost pixels are half background; `int()` truncation of the float
  bounds then drops them. Measured +0.42 % at θ_out 0 and ±80, +0.30 % at ±40 —
  a one-pixel quantisation on a 465 px window, landing straight in the
  denominator of every cell. Fixed with two pixels of inset on the control
  window only.
- **Degenerate "flat plates" are not flat.** A floor pyramid at depth 0.01 mm
  reads 1.7–2.7 % off a Lambertian's closed form, and *worse* as the depth
  shrinks — 20.6 % at 0.001 mm, 75.5 % at 0.0001 mm — because surfaces 1e-4 mm
  apart over a 100 mm span are numerically the same surface. The flat reference
  is a single quad, which has no such parameter.
