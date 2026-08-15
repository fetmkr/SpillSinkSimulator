# Where Cycles and Mitsuba disagree, and where they do not

Every optical number in this study comes from Cycles. A second renderer was
added to check it. The check reported small differences on a honeycomb and a
cone and was taken as validation. Extending it to the blade family — the design
that leads all three axes — showed a 27 % gap, and following that gap down is
what this file records.

**Nothing here changes a published number**, and by the end of this file the
reason is stronger than "no evidence to change them": Cycles is confirmed
against two independent closed forms and a third, independently written tracer,
while Mitsuba is the code that departs from all three on thin-wall geometry.

## What both codes get right

| test | closed-form answer | Cycles | Mitsuba 3.9.1 |
|---|---|---|---|
| empty frame, constant environment radiance 1 | 1.000000 at every angle | 1.000000 | 1.000000 |
| flat Lambertian, rho 0.01 and 0.05, theta 0/20/40 | reads its own rho | -0.5 % | +0.01 % |
| integrating sphere, rho 0.1 to 0.98 | `M f`, `M = rho/(1-rho(1-f))` | **worst 0.27 %** | **worst 1.22 %** |

The sphere is the strong one. At rho = 0.98 with a port fraction of 0.004866 the
mean path is 40 bounces, and both codes land on the Labsphere closed form —
Cycles +0.06 %, Mitsuba -0.22 %. **Multi-bounce transport in a cavity is not
where either code is wrong.**

The sphere equation is from the Labsphere technical guide, not from memory:
`f = (A_i + A_e)/A_s`, `M = rho/(1 - rho(1-f))`, `L_s = (Phi_i/(pi A_s)) M`.
Under a uniform environment of radiance L the flux entering the port is
`Phi_i = pi A_port L`, so the radiance a camera reads looking in is `L M f`.

## What they disagree about

Identical mesh (52 040 verts, 39 030 faces, same bounding box — checked, not
assumed), identical camera (calibrated with emissive markers: the two images are
an exact vertical mirror of each other, same scale at every angle), identical
constant environment, matched measurement windows.

| structure | theta 0 | theta -40 |
|---|---|---|
| comb | -8.0 % | **+44.4 %** |
| honeycomb | -8.2 % | +46.4 % |
| square | -7.9 % | +48.0 % |
| triangle | -9.2 % | +46.7 % |
| reentrant | +30.1 % | +47.5 % |
| nested | -8.7 % | +42.9 % |
| shingle (blades) | +26.9 % | **+60.3 %** |
| **cone** | **+3.6 %** | **+6.2 %** |

Every family built from thin WALLS lands in the same band. The cone — a solid of
revolution with no sheet-like feature — is the only one that agrees.

## It is single scattering, not transport

Capping the bounce count separates the two. The correspondence had to be
established by measurement, because the two codes count differently and the
first attempt at this table got it wrong:

    Cycles max_bounces = N   <->   Mitsuba max_depth = N + 2

Blender's `max_bounces` counts INDIRECT bounces on top of the direct hit, so
`max_bounces = 0` is single scattering; Mitsuba's `max_depth` counts path
vertices including the camera, so single scattering is `max_depth = 2`. The
canyon benchmark below pins this down: Cycles at `max_bounces = 0` lands on the
closed form to +0.04 %, at `= 1` it is +16.8 % high because it now includes
double scattering. An earlier version of this table paired N with N+1 and so
gave Mitsuba one bounce fewer at every row; these numbers are the corrected run.

| bounces N | theta 0 | theta -40 |
|---|---|---|
| **0 (single scattering)** | **-8.6 %** | **+42.6 %** |
| 1 | -8.8 % | +35.3 % |
| 2 | -7.5 % | +33.6 % |
| 4 | -6.9 % | +33.0 % |
| 8 | -6.7 % | +32.9 % |
| 64 | -6.7 % | +32.9 % |

**At zero bounces -- pure single scattering -- the disagreement is already at
full size**, +42.6 % at 40 degrees, and adding bounces slightly REDUCES it.
Single scattering is environment light hitting a surface once and leaving toward
the camera; there is no transport chain to get wrong. What is left is the
cosine-weighted visibility at each surface point, the shadow-ray term.

## The canyon: a thin-wall case with an exact answer, and it names a winner

Two parallel walls of thickness t and height h, gap w, floor between them,
infinitely long. The cosine-weighted sky fraction on the floor at distance x
from the left wall is the standard 2D element-to-strip view factor:

    F(x) = ( x/sqrt(x^2+h^2) + (w-x)/sqrt((w-x)^2+h^2) ) / 2

and a Lambertian floor under a uniform environment of radiance L leaves
`L_out = rho L F(x)` after exactly one bounce, with no free parameters. **F does
not contain the wall thickness** -- an opaque wall occludes the same sky whether
it is 0.08 mm or 2 mm -- so any thickness dependence in a measurement is the
renderer's. Lambertian radiance is also view-independent, so the same closed
form applies at any camera elevation.

Shallow canyon (h = 4.0, w = 6.5, rho = 0.5, 4096 spp, single scattering), which
keeps the floor visible at 40 degrees:

| wall t | view | Cycles / theory | Mitsuba / theory |
|---|---|---|---|
| 0.08 mm | 0 deg | **1.0000** | 0.9740 |
| 0.08 mm | -40 deg | **1.0000** | 0.9739 |
| 2.0 mm | 0 deg | **1.0000** | 0.9799 |
| 2.0 mm | -40 deg | **1.0000** | 0.9798 |

**Cycles reproduces the closed form exactly at both angles and both
thicknesses. Mitsuba runs 2.0-2.6 % low, and further low as the wall thins.**
Together with the sphere (Cycles 0.27 %, Mitsuba 1.22 %) both benchmarks put the
error in the same code and in the same direction.

Two defects in the benchmark itself were found and fixed before these numbers,
and are recorded because each looked like a renderer fault first:

* the sphere's far pole was a ring of DEGENERATE quads, so an axial ray left
  through the hole. The inner 40 % of a 4-degree port read 0.000000 and the
  apparent error scaled with how much of the frame the bad patch covered
  (-41.7 % at a 4-degree port, -0.5 % at 30). Capped with a triangle fan.
* the canyon's floor originally ended exactly at the wall faces, leaving a
  seam. Running the floor under the walls moved Mitsuba's profile shape error
  from 1.60 to 1.16 against a theoretical 1.03.

## A third implementation settles it

`scripts/raytrace_viz.py` is a plain-Python path tracer written for the
simulator's ray-path display: uniform grid over x-z, Moller-Trumbore
intersection, cosine-weighted Lambertian scattering, Russian-roulette absorption
at `rho`. It shares no code with Blender or Mitsuba. Casting a collimated beam
at theta and counting what leaves measures rho_dh(theta) directly -- the same
quantity `hemi_view` reads by reciprocity.

comb 6.5/0.08, Lambertian 0.5, 64 bounces, 3000 rays:

| theta | Cycles | third tracer | Mitsuba |
|---|---|---|---|
| 0 deg | 0.019156 | 0.020667 +- 0.0026 (**0.6 sigma**) | 0.017880 |
| 40 deg | 0.157120 | 0.160000 +- 0.0067 (**0.43 sigma**) | 0.208870 (**7.3 sigma**) |

**The third code lands on Cycles and is seven sigma from Mitsuba.** With the
integrating sphere and the canyon closed forms already pointing the same way,
the question of which renderer to believe about a thin-wall cavity is closed:
Cycles. Every published number in this study stands, and the Mitsuba
cross-check must be read as a check that has itself been checked -- useful for
catching gross error, not for correcting a Cycles result at the few-percent
level on this geometry.

This does NOT explain the comb's +42.6 % at 40 degrees -- the canyon's two-edge
occlusion is a far simpler horizon than a tube seen at grazing incidence, and no
closed form for that case is in hand. What it establishes is which code to
believe while that stays open: **Cycles is exact on both benchmarks; the
published numbers are the ones to keep, and the Mitsuba cross-check cannot be
used to correct them.**

The images confirm it is a scale and not a mismatch: after undoing the vertical
mirror the two renders correlate at +0.98 (theta 0) and +0.94 (theta -40). Both
codes see the same lattice in the same place and shade it differently.

## It scales with wall thickness, which should not happen

| comb wall | 0.08 mm | 0.2 mm | 0.5 mm | 1.0 mm | 2.0 mm |
|---|---|---|---|---|---|
| theta 0 | -8.0 % | -8.1 % | -5.6 % | -1.3 % | +7.6 % |
| theta -40 | +44.4 % | +36.5 % | +24.5 % | +14.8 % | +10.9 % |

and the same for blades:

| plate_t | 0.05 mm | 0.2 mm | 0.5 mm | 1.0 mm | 2.0 mm |
|---|---|---|---|---|---|
| Mitsuba vs Cycles | +26.9 % | +8.7 % | -1.3 % | -6.1 % | -9.1 % |

A physical answer cannot depend on how thick a wall is in this way while the
same two codes agree on a sphere to 0.3 %. **This is a defect, not a
characteristic**, and it sits exactly where the study's winning design lives:
a 0.05 mm blade.

Ruled out by measurement, each with its own test:

* **sampling noise** — flat from 256 to 4096 spp (-7.81, -7.64, -7.61 %).
* **film resolution** — Mitsuba is unchanged from 96 to 768 px
  (0.00033083 to 0.00033084 at theta 0).
* **measurement window** — three separate window bugs were found and fixed
  (12 % symmetric trim against Cycles' 20 % x / 30 % z; no `cos(theta)`
  foreshortening; `near_clip` on the wrong side of the slit). Fixing them moved
  comb from -8.2 % to -6.0 % at theta 0 and did not touch the angle behaviour.
* **panel margin overlapping the control plate** — at margin 0.5 the control
  reads exactly 0.050000 and the disagreement is unchanged (-9.9 % / +43.8 %).
* **camera framing** — markers at known world z land on mirrored but identically
  scaled rows in both codes, at 0 and at -40 degrees.
* **environment or exposure** — an empty frame reads 1.000000 in both at every
  angle.

## Which one is right is still open

The sphere says both handle a smooth cavity correctly. The one-bounce test says
they differ on thin-wall visibility. Neither of those identifies the correct
answer for a 0.08 mm wall at grazing incidence; that needs a case with a
closed-form single-scattering solution on thin geometry, which this file does
not yet have. The honest position:

**Every reflectance number in this study for a wall-built family carries an
unresolved renderer systematic of roughly 8 % at normal incidence and 45 % at
40 degrees.** Rankings between wall families are far safer than the absolute
values, because the offset is nearly common to all of them — but the
cone-versus-wall comparison is not, since the cone is the one family that
agrees.

## Two corrections to earlier claims in this project

**"Energy is conserved to 0.03 %" is withdrawn.** That line in
`FINDINGS_crossvalidation.md` was our own measurement, not a literature value.
Re-measured: a comb cavity of rho = 1.0 must return 1.000 and returns 0.673 in
Cycles and 0.561 in Mitsuba at normal incidence. Neither is a renderer fault —
rho = 1 never decays, so 128 bounces cannot finish the sum — but the claim as
written is wrong and the number it quoted does not apply to this geometry.

**"Cycles reads a flat Lambertian 7.3 % low" is withdrawn**, from this session.
That test asked `build_scene` for a family it does not support and measured
something else. The control patch in the real measurement path reads 0.049760
against a nominal 0.05, and 0.050000 exactly once the panel margin no longer
overlaps it.

## Reproduce

    python3 scripts/bench_canyon.py                       # thin-wall closed form
    <mts>/bin/python scripts/bench_canyon.py --mts
    Blender --background --python scripts/bench_canyon.py -- --blender
    python3 scripts/bench_sphere.py                       # many-bounce closed form
    <mts>/bin/python scripts/bench_sphere.py --mts
    Blender --background --python scripts/bench_sphere.py -- --blender
