# Phase 3 — the top layer owns form, the bottom layer owns head-on

**Status: complete, and RE-MEASURED 2026-08-14 after a geometry defect.**
Report: `report/2026-08-14/report.html`.

> ## The rebuild
>
> Everything below the first table was re-measured. `geom_topo._build_comb`
> stepped its hexagon lattice along the wrong two axes: no cell shared an edge
> with any neighbour and **30.1 % of the panel face was open channel straight
> down to the flat backing slab**. Nothing crashed, the CSV looked fine, and the
> render still read as a honeycomb — the user caught it by eye in this report's
> own gallery. `results/__void__README_lattice.md` has the arithmetic and the
> voided files; `geom_topo._assert_tessellates` now fails the build instead.
>
> One conclusion reversed (stacking DOES win on total reflectance, narrowly and
> only honeycomb-on-honeycomb). Two survived, and the rebuild handed the
> important one a control it did not have before.

Source: `results/sweep_stack.csv`, `scripts/geom_stack.py`, `sweep_stack.py`.
Depth held at **50 mm total** and split between the layers, so a stack is
compared against single layers at equal envelope rather than being handed twice
the wall.

## The prediction, written before the render

Phase 2 left no single layer good on all three axes:

| | total | form | head-on |
|---|---|---|---|
| commercial honeycomb | #2 | #11 | #11 |
| cone | #5 | #1 | #1 |
| blade array (grid) | #3 | #2 | #4 |

`geom_stack.py`'s docstring recorded the prediction up front: **only the TOP
layer is exposed head-on, because a stack cannot hide its own first surface.**
So honeycomb-over-cone should inherit the honeycomb's head-on failure, and
cone-over-honeycomb should inherit the cone's win. If that holds, the finding is
not "stacking works" but "the top layer decides two of the three axes."

Total reflectance was not predicted either way.

## Total reflectance — measured

| top / bottom | split | worst ρ_dh | vs flat | exposed |
|---|---|---|---|---|
| blades / honeycomb | 50:50 | **0.2193 %** | 5.2× | 3.04 % |
| honeycomb / honeycomb (fine under) | 50:50 | 0.2215 % | 5.2× | 3.37 % |
| honeycomb / cone | 25:75 | 0.2221 % | 5.1× | 3.28 % |
| honeycomb / cone | 75:25 | 0.2226 % | 5.1× | 3.28 % |
| honeycomb / cone | 50:50 | 0.2233 % | 5.1× | 3.28 % |
| honeycomb / blades | 50:50 | 0.2233 % | 5.1× | 3.28 % |
| cone / honeycomb | 75:25 | 0.2380 % | 4.8× | 0.48 % |
| cone / honeycomb | 50:50 | 0.2709 % | 4.2× | 0.48 % |
| cone / honeycomb | 25:75 | **0.4268 %** | 2.7× | 0.48 % |

**Single layers at the same 50 mm depth, from phase 2:**

    blade array, slotted grid   0.2137 %   5.3x
    cone 5.5 / tip 0.4          0.2170 %   5.3x
    commercial honeycomb        0.2212 %   5.2x

**Every stack is worse than the best single layer.** The best stack (0.2193 %)
loses to the best single layer (0.2137 %) by 2.6 %, which is inside the ~3.5 %
realisation spread — so at best a tie, never a win.

## The one large effect, and it is a loss

**Cone on top degrades fast as its share of the depth shrinks.**

    cone share  75%      50%      25%
    rho_dh      0.2380   0.2709   0.4268 %

At 25 % the stack reads **twice** the single-layer cone. A 12.5 mm cone on a
5.5 mm pitch has an aspect ratio of 2.3 against the single layer's 9.1, and the
honeycomb underneath does not recover what the shortened cone lets out. Depth
inside one continuous cavity is not interchangeable with depth split across
two.

The reverse ordering barely moves at all (0.2221 / 0.2233 / 0.2226 across the
same three splits) because the honeycomb's own performance is nearly
depth-independent in this range — it is a light *trap*, not a light *mover*, and
a trap that is already deep enough gains nothing from more.

## The three axes, re-measured on geometry that tessellates

| design | total | smear | head-on | buildable |
|---|---|---|---|---|
| honeycomb / finer honeycomb | **0.1951 %** | 0.98x | 1.640 | NO, 0.04 mm foil |
| blade array grid 0.05, single | 0.2065 % | - | - | yes |
| blade array grid 0.10, single | 0.2137 % | 3.44x | 1.150 | yes |
| cone 5.5, single | 0.2170 % | **4.11x** | 0.068 | yes |
| blades / honeycomb | 0.2193 % | 3.18x | 1.373 | yes |
| honeycomb 5.2/0.04, single | 0.2201 % | 0.98x | 1.639 | NO, 0.04 mm foil |
| honeycomb / cone | 0.2255 % | 0.99x | 0.121 | yes |
| cone / honeycomb | 0.2709 % | 3.92x | **0.060** | yes |

### 1. REVERSED — stacking wins on total reflectance, but only like on like

`ST_comb-comb_50` (6.5 mm cells over 3.17 mm cells) reads 0.1951 % against
0.1967 % for the best single layer, `CB_p0317_f040_x10`. Both are periodic and
deterministic -- comb has jitter 0, so all three "seeds" build the identical
mesh and the 0.00 % spread is sampling noise, NOT realisation spread. The
0.8 % margin is real for these exact geometries and far inside the 1.7-4.1 %
spread every non-periodic family shows.

Every stack that mixes two DIFFERENT families still loses. The cone is why: it
needs its depth in one continuous cavity.

    cone's share of 50 mm   100%     75%      50%      25%
    total reflectance       0.2170   0.2380   0.2709   0.4268 %
    aspect ratio             9.1      6.8      4.5      2.3

Honeycomb on top stays inside 0.2255-0.2287 % across the same three splits: a
trap deep enough already gains nothing from more depth. Two honeycombs stack
because neither layer had depth it could not spare.

### 2. SURVIVED — form is set by the TOP layer

    honeycomb on top   0.98x / 0.99x    honeycomb alone   0.98x
    cone on top        3.92x            cone alone        4.11x
    blades on top      3.18x            blades alone      3.44x

Four pairs, four matches. Whether a returned line spreads sideways is settled
by the first surface the light meets.

### 3. SURVIVED, AND NOW HAS A CONTROL — head-on is set by the BOTTOM layer

    honeycomb alone                   1.639
    honeycomb over FINER HONEYCOMB    1.640      <- control: no change
    honeycomb over CONE               0.121      <- 13.6x better

The top layer is byte-for-byte identical in all three. The control is what the
first version of this report lacked: over a finer honeycomb the tube still ends
in a flat floor and the number does not move at all; over cones the floor is
gone and it collapses. Same cell mouth, same wall tops, same everything a
viewer can see.

## The mechanism published in phase 2 was wrong, and this now proves it

The phase 2 report and `sweep_stack.py`'s docstring both said:

> the honeycomb's flat wall TOPS face a viewer exactly like the flat plate it
> replaced

**A honeycomb cell is a tube pointing at the viewer, and at the end of it is
the flat backing slab.** Head-on you look straight down the tube at that slab.
The walls are edge-on and contribute almost nothing. Change only the floor and
92 % of the brightness goes.

This also explains a phase 2 result that had no explanation. Six cell
topologies -- hex at three pitches, square, triangle, Voronoi-mixed -- land
inside a **0.14 % spread**, 1.6387 to 1.6410. They differ in wall shape, wall
count, pitch and wall thickness, and they share a flat floor. The only two that
break the pattern are exactly the two that occlude their own floor:

    B_CELLNEST_p1100    1.4529      a second wall inside each cell
    B_CELLREEN_p0650    0.5361      walls DIVERGE with depth, hiding the floor

Both were logged in phase 2 as unexplained oddities.

## What this says

**Phase 3 is a decomposition, not a design.** Top layer owns form, bottom layer
owns head-on, and only same-family stacks help on total. That says which knob
to turn for which complaint.

**The recommendation is still the single cone** -- 0.068 head-on, 4.11x smear,
0.2170 %, moulded at a 0.4 mm tip. The two designs that beat it on total are
both 0.04 mm foil, below the 0.05 mm handling floor the user set ("너무 얇으면
손으로 쉽게 찌그러지니"). At that floor the darkest buildable design in the
whole study is `BL_FLAT_t050_p0550_a02_grid` at 0.2065 %, a blade array.

**Phase 4 is not another stack.** It is a full-depth 50 mm honeycomb with only
the last 2-3 mm of each cell shaped -- no depth taken from the tube, the floor
replaced. That would take the honeycomb's total and the cone's head-on at once,
and nothing measured so far rules it out.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_comb.py
    Blender --background --factory-startup --python scripts/sweep_stack.py
    Blender --background --factory-startup --python scripts/form_buildable.py
    Blender --background --factory-startup --python scripts/build_report_phase3.py

Renders: `report/2026-08-14/shots/`. All were re-rendered after the lattice
fix; the pre-fix images showed a honeycomb with holes in it.
