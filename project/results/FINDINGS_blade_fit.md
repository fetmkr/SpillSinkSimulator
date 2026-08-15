# Q8 — the winner cannot be assembled as drawn, and the fix is free

`results/QUESTIONS.md` Q8 has stood tagged `[추측]` since it was written: blades
6.3 mm wide dropped on a 5.5 mm lattice at mixed azimuth must physically
collide, because two 0.05 mm steel plates cannot occupy the same space, and
`SAMPLES.md` sends a supplier a drawing that does not mention it. `geom_topo`
states the assumption openly at the line that builds them — *"overlap is free:
the union is the geometry"* — which is true of a union of solids and false of
sheet metal.

Nobody had counted. This counts them, and then solves it: the array IS
buildable, with half-lap notches, at no optical cost and without giving up the
azimuth, the jitter or the overlap. The count and the two bad escapes come
first because they are what makes the third one worth the trouble.

## The count

Each blade hangs from a top edge of length `plate_over × pitch`, centred on a
jittered lattice point, running along its azimuth and leaning by `tilt`. At any
depth its cross-section is that segment displaced by the lean. Two blades
interfere when their cross-sections cross at any shared depth. 193 blades on a
60 mm face, pitch 5.5, tilt 2°, `plate_t` 0.05.

| plate_over | grid | random | parallel |
|---|---|---|---|
| 0.70 | 15 collisions, 15.0 % of blades | 22, 22.3 % | **0** |
| 1.00 | 34, 31.1 % | 47, 42.5 % | **0** |
| **1.15 (published)** | **55, 46.1 %** | 68, 56.0 % | **0** |
| 1.45 | 91, 64.8 % | 121, 78.2 % | **0** |

**At the published setting, 89 of 193 blades are in at least one collision.**
The premise of Q8 is confirmed and it is not marginal.

It is not the blade width alone. Narrowing to `plate_over = 0.70` still leaves
15 % colliding, because the 0.30 lattice jitter brings neighbours close enough
that differently-oriented blades cross whatever their length. Removing the
jitter separates the two causes cleanly:

| plate_over, grid, jitter 0 | 1.00 | 1.15 | 1.45 |
|---|---|---|---|
| collisions | **0** | 43 | 125 |

**On a regular lattice the interference-free limit is exactly `plate_over =
1.00`** — blades that meet edge to edge and never overlap. Jitter is what breaks
it below that.

So there are exactly two ways to make the array buildable, and each surrenders
something the study asked for:

* **parallel azimuth** — zero collisions at any width, because parallel blades
  cannot cross. It is a slat array, one axis only, and azimuthal scattering is
  the reason the blade family beat the V-groove in the first place.
* **jitter 0 with `plate_over ≤ 1.00`** — zero collisions, and PERIODIC, which
  this project bans outright: a scanning beam over a periodic array produces
  periodic bright spots.

## What each escape costs

Standard protocol, 5 angles × 3 coating models, worst case, on the published
blade-plus-pyramid stack.

| design | worst ρ | θ = 0 | vs published | buildable |
|---|---|---|---|---|
| published — over 1.15, grid, jitter 0.30 | 0.18419 % | 0.05071 % | — | **no** |
| parallel, over 1.15 | 0.27635 % | 0.07027 % | **+50.0 %** | yes |
| **grid, over 1.00, jitter 0** | **0.18815 %** | 0.05205 % | **+2.2 %** | **yes** |
| grid, over 1.00, jitter 0.30 | 0.18267 % | 0.05190 % | −0.8 % | no |

Two of the three pre-registered predictions were wrong, and the interesting one
was wrong in the direction that matters:

* prediction 1 — parallel worse by 10–30 %. **It is worse by 50 %**, the right
  direction and twice the size.
* prediction 2 — the periodic array worst of the three by 20–50 %. **Wrong. It
  costs 2.2 %**, and the run at over 1.00 WITH jitter is 0.8 % better than the
  published design.
* prediction 3 — all three within a factor of two. Held; the spread is 1.5×.

## The overlap is not paying for itself

`plate_over = 1.15` is what makes the array unbuildable — it is the reason 46 %
of blades collide — and on total reflectance it buys nothing. At `over = 1.00`
the same array reads 0.18267 % jittered and 0.18815 % regular, against
0.18419 % published: one better, one 2.2 % worse, both inside the range a seed
change moves this family. **The design pays its entire manufacturability for a
difference it cannot demonstrate on this axis.**

That does not settle the design. `plate_over > 1` was chosen for the FORM axis —
a blade covering its neighbour's mouth is what makes the pocket reachable only
through a slot — and this sweep measures total reflectance only. The honest
statement is that the overlap must now justify itself on smear and head-on or be
dropped, because on total reflectance it is free to remove and it is the whole
of the assembly problem.

## The solve: half-lap notches, which is how the industry does it

"It cannot be built" is not an answer. Intersecting sheet strips are assembled
with **half-lap notches** -- slots cut to half the grid depth, opening downward
in one set and upward in the other, so the two interlock and finish coplanar.
It is the standard egg-crate construction for lighting louvers and grid
assemblies: US4849867 describes "downwardly opening slots in longitudinal
louvers and upwardly opening slots in transverse louvers ... all louvers
brought together with flanges coplanar", and US4714585 an interlocking
egg-crate grid whose slots are "dimensioned to accommodate complementary tabs
in the interlocking strips", assembled so no face carries a double thickness of
metal.

Applied to the published field (grid azimuth, jitter 0.30, over 1.15, the full
margined measurement field of 2518 blades):

| | |
|---|---|
| crossings | 722 |
| **unresolved after notching** | **0** |
| notches cut | 1444 |
| blade area removed | 3.46 % |

and measured against the same field un-notched, standard protocol:

| design | worst ρ | buildable |
|---|---|---|
| un-notched | 0.17136 % | no |
| **half-lap notched** | **0.16670 %** | **yes** |
| difference | **−2.72 %** | |

**The notched array is slightly DARKER, not worse.** Prediction 3 said it would
rise and said that a fall would need explaining rather than celebrating, so:
half of every crossing is notched from the TOP, which removes blade top-edge
material, and the top edge is exactly what faces a head-on viewer. Losing
3.46 % of blade area, roughly half of it from the mouth, buys back a little
more than the notches leak. The effect is small and the honest reading is
**notching is free**, not that it is an improvement worth chasing.

Two limits, stated:

* the notch schedule must be computed over DEPTH, not at the mouth. Blades
  lean 2 degrees, so the crossing travels 1.6 mm down a 47 mm blade; a schedule
  built from top-edge intersections alone found 29 of the 55 clashes in the
  preview field and would have left 26 pairs interpenetrating.
* **random azimuth is not solved by this.** The up/down assignment here comes
  from each blade's own direction, which works when every crossing is between a
  blade along x and one along z. With free azimuth the crossing graph is not
  two-coloured by direction and 28 of 73 crossings come out same-side. A proper
  two-colouring of the crossing graph would fix most of them, and any odd cycle
  in that graph cannot be fixed at all without moving a blade.

## Q8, answered

The published design is buildable as drawn, with a notch schedule, at no
optical cost. Nothing about the azimuth, the jitter or the overlap has to be
given up. What `SAMPLES.md` is missing is not a different design but a
manufacturing drawing: 1444 slots, each 0.09 mm wide and 23.5 mm deep, at
computed positions.

## A correction this sweep forced

The anchor `BH_p055_t02_grid_s23` was re-measured here with the identical
`params_json` `sweep_bladehood.csv` recorded, and came out **0.76 % different
per row**. Cycles is not the cause: three consecutive renders of the same design
on this machine are bit-identical, spread 0.00e+00.

The cause is a fix made earlier in this session. `geom_floor.margin_min` was
added so a shaped floor reaches the tube standing on it; for a blade field at
face 60 the tube overhangs by 103.42 mm where the old rule gave the floor
100.00 mm, so the floor grew by 3.42 mm. **Every published blade-stack number
was measured with a floor that stopped 3.42 mm short of the blades above it.**
The error is under 1 % and does not reorder anything, but it is real and it is
now recorded rather than absorbed: `margin_min` is written into `params_json`,
so gate check 8 reports these files as measuring different geometry from
`sweep_bladehood.csv` instead of silently comparing them — the same failure
`plate_over` caused when it went unrecorded.

Affected: any sweep with a wide-field top over a shaped floor, which is
`sweep_bladehood.csv`, the blade rows of `sweep_floor.csv`, and
`sweep_coatrobust.csv`. None is voided; the offset is bounded at 0.8 %.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_blade_fit.py
    Blender --background --factory-startup --python scripts/sweep_blade_fit2.py
    python3 scripts/gate_sweep.py
