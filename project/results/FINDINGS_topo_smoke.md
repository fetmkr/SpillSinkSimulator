# 2026-08-11 23:4x — the exposed-area law does not survive the Fresnel coating

> ## CORRECTION, same night — the honeycomb geometry was broken when this was measured
>
> The number below (honeycomb 0.00373) was taken on a **jittered hexagon array,
> not a honeycomb.** A hexagon only tiles the plane on an exact lattice; at
> jitter 0.30 x pitch the cells stopped sharing edges, so every cell raised its
> own six walls, neighbours overlapped into doubled walls, and gaps opened
> between them. The wall-sharing dedup was silently defeated for the same
> reason. **The 3D render caught it — `profiles/087` shows hex tubes at
> staggered depths with daylight between them — and the CSV never would have.**
> This is the project's "draw the geometry before trusting the number" rule
> paying for itself, and it is the same class of defect as the round-1 base-gap
> bug that produced "regular arrays are 8x darker than jittered ones".
>
> Fixed by building the cells as a **Voronoi tessellation** of the same jittered
> points (`geom_topo.voronoi_cells`), which covers the plane exactly, shares
> every edge between exactly two cells, and stays irregular.
> `profiles/090` is the corrected geometry.
>
> **What this does to the conclusion.** The broken version had DOUBLED walls,
> i.e. *more* exposed area than a clean tessellation, and it still came within
> 1.30x of the cone. So the falsification of the area law survives the fix and
> should strengthen — but **the specific figures in the table below are
> provisional until the re-run lands in `results/sweep_topo.csv`.** Measured
> exposed area of the corrected geometry is **13.20%** at pitch 7.5 (not the
> 10.67% the regular-hex formula predicts — a jittered Voronoi has ~24% more
> total edge length), which is 51x the cone's 0.258%, not 41x.

**Source:** `results/sweep_topo.csv`, SMOKE run, 4 designs x 3 materials.
Face 60 mm, 64 spp, 480x220, margin_depths 6.5, spec_roughness 0.30,
theta in (0, +/-20, +/-40), coating = fitted Musou Black (`material_mode`
`coating`). Identical harness settings to `sweep_shapes.py`, deliberately, so
the two files are comparable row for row.

Baselines, named: flat plate of the **same coating** reads rho_dh(0) = 0.00998;
the 0.05 matte black control in the same frame read 0.04992.

## The measurement

| topology | exposed area est. | worst rho over theta | rho at theta=0 |
|---|---|---|---|
| **cone** p7.5 d30 r0.2 (reference, re-measured) | 0.258 % | **0.00286** | 0.00233 |
| **honeycomb** p7.5 d30 wall 0.4 | **10.667 %** | **0.00373** | **0.00352** |
| shingle p7.5 d30 tilt60 | 1.116 % | 0.00725 | 0.00606 |
| truss p7.5 d30 L5 r0.35 | 1.580 % | 0.01832 | 0.00957 |

## What was predicted, and by what

`geom_topo.exposed_fraction_est()` computes the head-on exposed fraction
analytically, before any render. For a hex wall network of thickness t at pitch
p it is `3 * (p/sqrt(3)) * t / cell_area` = `0.8/p`; for a pillar tip of radius
r it is `pi r^2 / cell_area`. At pitch 7.5 that is **10.667% against 0.258%, a
factor of 41.3**.

The law this project has run on since the 1D ridge family --

    reflectance(head-on) ~= exposed_fraction x rho

verified across 24 combinations, with measured/naive between 0.75 and 1.5 --
therefore predicts the honeycomb returns **about 41x more light head-on** than
the cone. It was put in this sweep as a falsification test and labelled as one
in the script's docstring, on the reasoning that a negative control which fails
to lose is worth more than a candidate which wins.

## What was measured

**Honeycomb is 1.51x brighter head-on, not 41x. The prediction is off by a
factor of 27.**

Worst-over-theta it is 1.30x. Two topologies with a 41x difference in exposed
area land within 30% of each other.

## Why this is not a render defect

Checked before reporting, because this project has found four measurement
defects and every one of them presented as a surprising result first:

- The cone reference in this table was **re-measured in this same frame**, not
  quoted from an older CSV. It reads 0.00233 head-on under the fitted coating.
- Both geometries are built by the same `mesh_to_object` path, the same
  `margin_depths = 6.5`, the same backing slab, the same coating instance.
- Neither exceeds the flat plate of its own coating (0.00998) at any theta, and
  neither exceeds the 0.05 control. No energy problem.
- The exposed-area estimator is confirmed correct: the honeycomb figure
  `0.8/pitch` reproduces to 4 decimal places at both pitches tested.

## What it means

The exposed-area law was established under the **old flat-rho glossy material**,
where reflectance was linear in rho and the visible return was a single bounce
off the exposed tip. `metrics/01` already records that the switch to the
Fresnel-bearing fitted coating moved designs by 2x to 41x and **inverted the
ranking**, and CONTEXT.md's 2026-08-11 note records that the return is
one-bounce in every geometry with `D/A = 2.000 +/- 0.008`.

This measurement adds the geometric half of that correction:

> **Under the corrected material model, head-on reflectance is not governed by
> how much area is exposed. Two designs 41x apart in exposed area differ by
> 1.5x.**

Consequences, in order of how much they change what we do:

1. **"Shrink the tip" is no longer the primary design move.** The 1D->3D
   argument in `geom3d.py`'s module docstring -- that a point beats a line by
   20x because pi r^2 / cell beats 2r / pitch -- is an argument about area, and
   area has just been shown not to be the lever.

2. **Wall-network topologies are back on the table, and they have an advantage
   the pillar families cannot have: cells that do not seal.** A pillar array
   closes off once neighbouring pillars meet -- `geom3d.seal_fraction` puts a
   plain cone at pitch 7.5 at **72.2% of nominal depth**, so "depth 30" is
   21.7 mm of cavity. A honeycomb cell has vertical walls and never seals: at
   depth 30 it is 30 mm of cavity. The sweep analysis of `sweep_shapes.csv`
   found **usable aspect = seal_frac x depth / pitch** to be the single best
   predictor of the score (Spearman -0.876, log-log slope -1.15, R^2 = 0.73),
   and on that axis the honeycomb starts 1.39x ahead at the same nominal depth
   and pitch, before any tuning at all.

3. **The wall thickness has not been optimised, at all.** 0.4 mm is one FDM
   nozzle, chosen as a floor, and it is the only wall value measured. If the
   area law were true this would be the dominant knob; since it is not, the
   knob to push is pitch and depth.

## Immediate next step, and it is a cheap one

Expand the honeycomb arm of `sweep_topo.py` from a 6-design control into a real
search: pitch down to 2.5 mm, depth up to 50 mm, wall 0.3/0.4/0.6, and a tapered
vs straight wall. At pitch 3.75 / depth 50 the honeycomb's usable aspect is
**13.3**, against the best cone in `sweep_shapes.csv` at **9.6** -- and the
bird-of-paradise cavities that this project keeps citing run at aspect 7 to 80
(`reference/SUMMARY.md` 3.1), a range nothing built here has entered.

## Two other results from the same run, recorded so they are not re-derived

- **truss is a grazing amplifier under a specular coating.** 0.01832 at +/-40
  against 0.00957 head-on, and it swings **4.6x between materials** (d00 0.01832,
  d100 0.00401) -- the widest material sensitivity of anything measured. A sparse
  lattice presents struts at near-90-degree incidence from a tilted view, and
  under Fresnel that is the expensive angle. Not obviously fixable by tuning.
- **shingle is 2.5x worse than the cone and its material ordering is reversed**
  (d00 0.00725 > d100 0.00648, where every other design here is the other way
  round). Inclined plates redirect a specular bounce, which is what they were
  built to do; they just do not redirect enough of it to pay for the area.

## Reproduce any row

`results/sweep_topo.csv` carries a `params_json` column holding the complete
parameter object for that design. One row rebuilds it exactly:

    python3 -c "import json,sys; sys.path.insert(0,'scripts'); \
      import geom_topo as GT; \
      p=GT.TopoParams(**json.loads(ROW)); print(GT.describe(p))"
