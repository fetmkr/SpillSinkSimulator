# Phase 4 — the floor of the cavity

Three experiments, each with its prediction written into its sweep script
before the render and left unedited afterwards. Every one is anchored to a
design an earlier sweep already measured; gate check 8 compares them per seed
and all agree to 0.00e+00.

    sweep_floor.csv       78 designs   floor kind x depth x tube
    sweep_floorpitch.csv   8 designs   floor feature pitch
    sweep_tipflat.csv     10 designs   pyramid apex flat
    sweep_conefloor.csv    4 designs   does a cone need a floor at all

## 1. Shape, not distance. And 2 mm is enough.

Reflectance at NORMAL INCIDENCE, worst over three coating models, mean over
three seeds. The 50 mm envelope is fixed; the floor is taken out of the tube.

| tube | floor | theta-0 | vs flat floor |
|---|---|---|---|
| honeycomb 6.5/0.08 | flat slab | 0.16401 % | - |
| | pyramid 3 mm | **0.03355 %** | **4.89x** |
| | pyramid 2 mm | 0.03538 % | 4.64x |
| | cone 3 mm | 0.03537 % | 4.64x |
| | wave 3 mm | 0.03868 % | 4.24x |
| | **3 mm air gap** | 0.17040 % | **0.96x -- nothing** |
| blade 0.05/o1.15 | flat slab | 0.20566 % | - |
| | pyramid 3 mm | **0.05383 %** | **3.82x** |

The air gap is the control that matters. Moving the slab back 3 mm and leaving
it flat changes nothing, so DISTANCE is not the mechanism; a ray that meets a
flat surface square-on returns whether it travelled 47 mm or 50 to get there.
Shaping the same 3 mm does the whole job.

The pressed pyramid -- the cheapest of the three to make -- beats the moulded
cone and the smooth egg-carton. Flat facets help; curvature does not.

**Worst-case reflectance over +-40 deg is unchanged to four decimals** in every
row above. At 40 degrees a ray never reaches the floor. The floor is free on
the axis phases 2 and 3 were scored on.

## 2. Floor pitch is not a lever, and the reason names the next experiment

| floor pitch | honeycomb theta-0 | blade theta-0 |
|---|---|---|
| 1.0 mm | 0.03549 % | 0.05623 % |
| 1.5 mm | **0.03355 %** | 0.05472 % |
| 2.0 mm | 0.03355 % | **0.05383 %** |
| 3.0 mm | 0.03378 % | 0.05478 % |

5.8 % across the whole range, and NOT monotonic -- the finest pitch is the
worst. The pre-registered prediction ("finer is better") was wrong.

`tip_flat` was held at 0.1 mm throughout, so a finer pitch packs the same flat
apex more densely: the viewer-facing flat fraction is (tip_flat/pitch)^2 =
1.00 / 0.44 / 0.25 / 0.11 %, which orders the first three points exactly.

## 3. The apex flat is the mechanism, and it is linear in area

Floor pitch 2.0 mm, depth 3 mm. Prediction written first: if the flat apex is
what a floor has to avoid, theta-0 should rise with flat AREA.

| tip_flat | flat area | honeycomb | blade |
|---|---|---|---|
| 0.02 mm | 0.010 % | 0.03309 % | 0.05346 % |
| 0.05 mm | 0.063 % | +0.4 % | +0.2 % |
| 0.10 mm | 0.250 % | +1.4 % | +0.7 % |
| 0.20 mm | 1.000 % | +4.7 % | +2.8 % |
| 0.40 mm | 4.000 % | **+18.4 %** | **+13.2 %** |

Slope on log-log is close to 1: **linear in flat area**, as predicted.

FOR THE QUOTATION. A 0.40 mm apex throws away 18 % of the benefit. 0.10 mm
costs 1.4 % and is effectively free. There is no reason to ask a die for
anything sharper than 0.10 mm, and good reason not to accept 0.20.

## 4. A cone does not need a floor -- which is the mechanism's own test

The sharpest available test of everything above: a cone array has no flat
floor. The space between cones is already a V. If "the ray meets a flat
surface" is the mechanism and it is complete, a cone should gain nothing.

Predicted before the render: **less than 1.3x**.

| cone 5.5 mm, 50 mm | theta-0 | gain | worst-theta |
|---|---|---|---|
| flat backing (control) | 0.17981 % | 1.00x | 0.2160 % |
| + 3 mm air gap | 0.18088 % | 0.99x | 0.2192 % |
| + 3 mm wave floor | 0.18080 % | 0.99x | 0.2192 % |
| + 3 mm pyramid floor | 0.18079 % | 0.99x | 0.2192 % |

**0.99x.** The three floors are indistinguishable from each other and from
doing nothing -- exactly as the air gap behaves under a honeycomb. Against
4.89x for the honeycomb and 3.82x for the blade, this is as clean a
confirmation as the study has produced: the floor helps precisely those
structures that end in a flat plate, and the cone does not.

It also costs: shortening the cone from 50 to 47 mm moved worst-theta from
0.2160 to 0.2192 %. A floor on a cone is 1.5 % worse for no gain.

## 5. Blade tilt is the only real trade-off in the whole study

Every other floor parameter moved one axis and left the rest alone. Tilt does
not. Blade 0.05 mm, pitch 5.5, slotted grid, 47 mm, over a 3 mm pyramid floor:

| tilt | worst-theta | theta-0 | smear | head-on |
|---|---|---|---|---|
| 0 deg | **0.1727 %** | **0.01668 %** | **1.13x** | 0.119 |
| 2 deg | 0.1861 % | 0.05383 % | 3.96x | 0.092 |
| 5 deg | 0.2103 % | 0.06256 % | **4.00x** | 0.053 |
| 10 deg | 0.2519 % | 0.10438 % | 3.58x | **0.039** |

    total reflectance   best at 0 deg,  46 % worse by 10
    form destruction    best at 5 deg,  COLLAPSES at 0
    head-on brightness  best at 10 deg, 3x worse at 0

Upright blades make a set of parallel slots. Light rattles up and down between
them and leaves the way it came: dark, and moved sideways not at all. 1.13x is
the honeycomb's failure mode (0.98x), reached from the other direction.

**This corrects a claim made one turn earlier in this project.** Seeing 0 deg
lead worst-theta by 7 %, it was written up as the new best design. It is not;
it was scored on one axis. The incumbent stands:

| design | worst-theta | smear | head-on |
|---|---|---|---|
| **blade tilt 2 + pyramid** | **0.1861 %** | 3.96x | 0.092 |
| blade tilt 5 + pyramid | 0.2103 % | 4.00x | 0.053 |
| cone 5.5 + pyramid floor | 0.2192 % | 4.02x | 0.054 |
| cone 5.5 alone | 0.2160 % | **4.11x** | 0.068 |

If head-on brightness is what the client judges, tilt 5 is the better buy:
1.7x dimmer to the eye and slightly better on form, for 13 % on total.

### The other two arms, and what they confirm

| pitch (tilt 2, grid) | worst-theta | aspect | exposed |
|---|---|---|---|
| 4.0 mm | 0.2046 % | 12.5 | 1.66 % |
| 4.75 mm | 0.2005 % | 10.5 | 1.40 % |
| **5.5 mm** | **0.1861 %** | 9.1 | 1.21 % |
| 7.0 mm | 0.1909 % | 7.1 | 0.95 % |

An interior optimum, as predicted -- but at 5.5, not below it. The prediction
said the aspect-ratio term would beat the exposed-edge term. It does not.

| azimuth | worst-theta | vs grid |
|---|---|---|
| slotted grid | 0.1861 % | - |
| random | 0.1998 % | +7.3 % |
| all parallel | 0.2737 % | **+47 %** |

Predicted grid ~= random > parallel, and the phase 2 gap of 33 % widens to 47 %
at 50 mm with a floor.

**The floor's 3.82x holds across the whole neighbourhood.** Floor and tube can
be specified separately and quoted separately.

## What this does NOT settle

**theta-0 total reflectance is not head-on brightness.** The cone reads
0.17981 % at normal incidence -- close to the flat-floored honeycomb's
0.16401 % -- while its head-on PEAK is 0.068 against the honeycomb's 1.634, a
factor of 24. Total counts every photon returned; peak counts only the ones
aimed at an eye. The floor experiments above are scored on total, and the
phase 4 report's gallery 2 heading calls that "darkest head-on", which
conflates the two. That heading needs correcting.

Measured since: cone + pyramid floor reads 0.054 head-on against the bare
cone's 0.068 -- **1.27x**, just inside the predicted "less than 1.3x", and the
lowest head-on figure anywhere in the study. So the floor does buy the cone a
little on the viewer axis while buying it nothing at all on total (0.99x). Both
are consistent with the mechanism; neither justifies the 1.5 % it costs on
worst-theta.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_floor.py
    Blender --background --factory-startup --python scripts/sweep_floorpitch.py
    Blender --background --factory-startup --python scripts/sweep_tipflat.py
    Blender --background --factory-startup --python scripts/sweep_conefloor.py
    python3 scripts/gate_sweep.py
