# The angle-in / angle-out map, and two defects that full-face windowing exposed

2026-08-20. New metric: `metrics/08_brdf_slice.md`. Code: `scripts/bidir.py`,
`scripts/gate_bidir.py`, `scripts/sweep_bidir.py`, `scripts/plot_bidir.py`.

## Why

Every published number in this study integrates over exit direction, and
`metrics/01` names that as its own blind spot. Phase 10 changed the question
from *absorb* to *reroute*, and answered it with a hand-typed 5 × 4 grid in
`probe_tiltsweep.py` that writes no CSV, records no conditions and carries no
control plate. That grid found a real result — the tilt law
`obs = -(beam + 2·tilt)` — which is the argument for making it an instrument
rather than for leaving it as a script.

## The measurement

Sun at θ_in, orthographic camera at θ_out, both in the sign convention
`blender_render` already uses. The flat Lambertian control plate in every frame
does the whole normalisation analytically:

```
L_c = (ρ_c/π)·E·cos θ_in        L_p = f_r(θ_in,θ_out)·E·cos θ_in
  ⇒  f_r = (L_p/L_c)·ρ_c/π      [1/sr]
```

E and cos θ_in cancel, so there is no bin solid angle, no cos θ_out division and
no source calibration anywhere in it. The sun's angular **diameter** is set to
the θ_in step, which makes a column an honest bin average rather than a delta
with a fudge — `add_sun`'s own docstring is the reason that matters.

**It is a beam-and-camera measurement, not a reciprocity one, and that is
forced.** `metrics/01` adopted reciprocity precisely because it integrates the
hemisphere in one shot. This metric resolves the axis reciprocity erases.

## What the rig reads

A genuinely flat Lambertian plate of ρ₀ = 0.20 reads **ρ₀/π to 0.00 % in every
cell** — every incidence, every observation angle. The 0.05 control reads its
own closed form to 0.00 % for |θ_out| ≤ 40 and 0.23 % at ±80. The instrument has
no residual of its own worth the name.

Getting there took two defects and one dead end.

## Defect 1 — the flat plate did not cover its own window

`lock.py CASES["flat_coating"]` is a degenerate ridge: pitch 50, depth 0.001, on
a 100 mm face. It lays its two periods over **z −25..+75**, not −50..+50. Under
a full-face window that reads 25 % background as if it were sample.

Measured: the Lambertian 0.20 plate came back **0.047654 against the 0.063662 it
owes — 0.7485, exactly the coverage fraction.**

The stock rig never saw it. `measurement_windows` insets 30 % in z, so the old
window ran z −20..+20, which sits inside the covered band. **Opening the window
(rig_v2 D3) is what exposed it**, which is the same shape as the audit's own
finding that a fix can uncover the next defect down.

Nothing in the rig asked the question: `assert_clear` checks the panel field
does not reach the *control*, `assert_window_in_frame` checks the window fits
the *image*. Neither asks whether the *sample* is under the window. Added:
`rig_v2.assert_window_covered`, which raises rather than measuring background.

**Anything measured full-face on a geometry whose margin is proportional to a
near-zero depth is suspect until it passes that assertion.**

## Defect 2 — the control plate read 0.3–0.4 % high

`make_flat_plate` builds the control as exactly the face rectangle. A full-face
window therefore ends on the plate's own edge, its outermost pixels are half
background, and `window_stats`' `int()` truncation of the float pixel bounds
drops them — so the plate reads *high*.

Measured: **+0.42 % at θ_out 0 and ±80, +0.30 % at ±40** — the signature of a
one-pixel quantisation on a 465 px window, moving with the tilt because the tilt
changes where the window edge falls between pixels.

That number lands directly in the denominator of every cell of this metric.
Fixed with two pixels of inset on the **control** window only; the panel keeps
inset 0 because `assert_window_covered` now guarantees it runs past its own
window. After the fix the panel reads a Lambertian's ρ/π to 0.00 %.

Same class as defect 1: invisible while the window was inset by a fraction of
the sample, visible the moment the window was honest.

## The dead end — a degenerate structure is not a flat plate

Before the quad, a near-flat floor pyramid was tried. It gets *worse* as it gets
flatter:

| depth | facet slope | error against ρ/π |
|---|---|---|
| 0.01 mm | 0.286° | −1.7 % to −2.7 % |
| 0.001 mm | 0.029° | −20.6 % |
| 0.0001 mm | 0.003° | −75.5 % |

Not a facet effect — a facet effect would shrink with the slope. Surfaces 1e-4 mm
apart over a 100 mm span are numerically the same surface, and the render breaks
down. **The flat reference is now a single quad** through `build_scene`'s
`prebuilt_mesh` door (`bidir.flat_plate()`), which has no such parameter.

## The finding: the fitted coating is not a reciprocal BRDF

Gate check G6 asks whether the map integrates back to the project's primary
scalar. At normal incidence the BRDF is azimuthally symmetric, so the in-plane
slice determines the whole hemisphere and

    rho_dh(0) = 2*pi * INT_0^{pi/2} f(0,theta) cos(theta) sin(theta) dtheta

closes against `materials.Material.rho_dh(0)`, itself verified to 0.04 % against
Cycles. Measured, **identical geometry, identical quadrature, identical code
path, only the material swapped**:

| material | integral | closed form | error |
|---|---|---|---|
| Lambertian ρ₀ = 0.20 | 0.198033 | 0.200000 | **−0.98 %** |
| `musou_fit` | 0.012270 | 0.009962 | **+23.17 %** |

The Lambertian's −0.98 % is the 85–90° truncation, predicted in advance
(sin²85° = 0.9924). **So the rig and the quadrature are not what fails.**

### The mechanism, measured rather than assumed

At θ_in = 0, a reciprocal material's off-lobe level must be flat in θ_out. The
Lambertian's is, to five digits:

    f(0,out)  Lambertian   0:0.06366  20:0.06366  40:0.06366  60:0.06366
    f(0,out)  musou_fit    0:0.02487  20:0.00363  40:0.00320  60:0.00347  80:0.00361

The coating's dips and rises again — a 12 % spread where there should be none.
It is built as `mix(diffuse, glossy, fac)` with `fac` from a Fresnel node, and
that node keys off the **view** direction, so the diffuse arm is attenuated by
an amount that depends on where the camera is.

Directly: **f(a,b) ≠ f(b,a)**. Off the lobe, at 1024 spp with a 5° sun, where
sampling cannot explain it:

    f(0,80)/f(80,0)   = 0.681
    f(0,60)/f(60,0)   = 0.707
    f(20,80)/f(80,20) = 0.816

This also explains G3: the 20.7 % median reciprocity residual on the coarse map
is not only the asymmetric bin widths, as pre-registered — a real part of it is
the material.

### Why it matters beyond this metric

`metrics/01` reads ρ_dh **by Helmholtz reciprocity** — uniform world, tilted
camera — and that identity requires a reciprocal BRDF. What `hemi_view` actually
reads is the *hemispherical-directional* reflectance, which equals the
*directional-hemispherical* one only under reciprocity.

Stated carefully, because it is easy to overclaim: `Material.rho_dh()` was
fitted and verified against that same `hemi_view` configuration, so it describes
what the rig reads self-consistently, and no published number is shown to be
wrong here. **What is now open is whether those two reflectances are the same
number for this material model, and by how much.** The measurement above bounds
the asymmetry at roughly 1.5× off-lobe on a flat plate.

G6 therefore gates on the Lambertian, which must close and does, and *reports*
the coating's non-closure as the size of the effect. Failing the rig for a
property of the material is how a real finding gets suppressed.

## What this metric cannot say

Stated here as well as in `metrics/08`, because it will be read off a picture.

- **The coating's BRDF *shape* is unvalidated, and that is exactly what this
  metric reads.** `metrics/01` says the fit constrains only ρ_dh of a flat
  plate. Every other metric integrates over the unconstrained axis; this one
  resolves it. The map's *structure* is a geometric result and stands. **No
  absolute cell value is quotable until a coupon is measured on a goniometer.**
  This is the strongest argument the project has yet produced for closing README
  open item 4.
- **One azimuth plane**, so no hemisphere integral and no TIS — except at normal
  incidence, where azimuthal symmetry closes it and `gate_bidir` G6 uses
  `materials.Material.rho_dh(0)` as the closed form.
- **Asymmetric bins**: θ_in is bin-averaged by the sun's width, θ_out is a delta
  direction. Reciprocity is therefore approximate *by construction*, and its
  residual is a sampling diagnostic, not a physics one.

## First measured maps, and the pre-registrations scored

`--quick` grid (9 × 9 at 20°), `musou_fit`, 256 spp, sun diameter 20°.
`results/sweep_bidir_flat.csv`, `results/sweep_bidir_pyramid_p4_d22.csv`,
picture in `results/bidir_flat_vs_pyramid_p4_d22.png`.

The flat plate reproduces gate G2 independently — peak 2.384 /sr against the
gate's 2.38404, audience row 0.014811 against 0.01481. Two code paths, same
numbers.

**S1 — HELD.** The flat plate peaks on the mirror direction at every incidence,
and the peak grows 0.01481 → 2.38404 /sr from head-on to 80°, a **161× rise**.

**S2 — HELD, and the interesting half was the part left open.** The pyramid's
peak is below the flat plate's at every incidence, worst column 19× darker,
248× at the best. I deliberately did *not* predict where it would land, because
"ridge survives, reduced" means the structure only dims and "ridge moves" means
it reroutes. **It moves, and not to either line anyone was watching:**

| θ_in | pyramid peaks at θ_out | mirror | retro |
|---|---|---|---|
| −60° | **−80°** | +60° | −60° |
| −40° | **−80°** | +40° | −40° |
| −20° | **−80°** | +20° | −20° |
| 0° | 0° | 0° | 0° |
| +20° | **+80°** | −20° | +20° |
| +40° | **+80°** | −40° | +40° |
| +60° | **+80°** | −60° | +60° |

The residual light goes to **grazing, on the same side the beam came from** —
past retro, away from both the projector and the audience. That is rerouting in
the Phase 10 sense, and no scalar metric in this project could have seen it: ρ_dh
integrates it away and the smear metrics only look near the specular return.

**S3 — HELD.** On the audience line the pyramid is below the flat plate at every
incidence, by 6.9× at grazing to **29.1× head-on**, median 8×.

**S5 — the residual is dominated by the material, as G6 found.** Median
reciprocity residual 20.7 % on the flat plate and 15.2 % on the pyramid at this
coarse grid. Part is the asymmetric bin widths as pre-registered; the rest is
the coating's own non-reciprocity, measured above.

**S4 is unscored** — the honeycomb-over-flat-base case has not been run. It is
the slowest of the three (253 k verts) and is left for the queue.

## Open

- The corner-reflector prediction from the ray-tracer session: honeycomb over a
  flat base is two perpendicular mirror classes, so its specular arm must land
  on **both** diagonals of the map at every incidence. Their caveat is adopted —
  the library finishes are 76–85 % Lambertian, so the honest prediction is an
  *excess* on the diagonals over a smooth background carrying roughly the
  specular share, not "bright only on the diagonals". Pre-registered as S4 in
  `sweep_bidir.py`.
- Their tracer sits at 0.57–0.68× of Cycles on the honeycomb while being exact
  on a flat plate. This map resolves exit direction, so it can say whether the
  missing light is missing from a *direction* or uniformly.
- Azimuth. It is the one axis between this metric and metric 05.
