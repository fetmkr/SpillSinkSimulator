# 2026-08-20 — the measurement rig audited: nine defects, and a protocol that names its own conditions

**Supersedes the first version of this file, written when three defects were
known and containing three claims I later withdrew. Withdrawals are listed in
§8 rather than deleted.**

Trigger: a user-run report for a pitch-100 / depth-500 pyramid returned a smear
of 15.46x against the study standard's 1.42x. Chasing whether that number was
real exposed the instrument, not the design.

---

## 1. The nine defects

Six of the nine are the same mistake: **a length written as a count.** A count
stays fixed while the sample changes size, so the physical quantity it stands
for silently scales with the sample.

| # | what | how it was written | what it must be | status |
|---|---|---|---|---|
| 1 | measurement window | 40 % of the sample (`MEAS_INSET_Z = 0.30`) | ~6x the return's 90 % width, driven to convergence | fixed |
| 2 | frame pixels | `RES_X = 1400` constant | mm-per-pixel fixed, count follows | fixed |
| 3 | beam width | not recorded at all | written into every result | fixed |
| 4 | beam default, two renderers | 7.5 in Cycles, 2.0 in Mitsuba | one constant, one place | fixed |
| 5 | pixel ceiling | `RES_CAP = 6000` (**mine**, added while fixing #2) | a memory ceiling that refuses, never degrades | fixed |
| 6 | frame height | `res_y/res_x = 0.443` fixed | 1.06 x the face | fixed |
| 7 | density control | wired to the UI, dropped in the dispatch lambda | reaches `form()` | fixed |
| 8 | Mitsuba's rig constants | stale copies, comment claimed they could not drift | passed in the request | fixed |
| 9 | profile array | `NWIN = 361` samples | derived from the window | fixed |

**Not fixed:** the Cycles-vs-Mitsuba +27 % on the pyramid at theta 0 (§7).

### The one that cost the most: #1, and why clipping does not merely shrink

`rms_width` normalises by the energy INSIDE the window, so light that spreads
past the window leaves the numerator AND the denominator. The reading does not
sag, it **collapses onto the core**. Synthetic check, true rms 17.777 mm:

| window | reads | energy kept |
|---|---|---|
| 24 mm | **0.800** | 72.7 % |
| 48 mm | **0.800** | 72.7 % |
| 96 mm | 17.777 | 100 % |

A design throwing 23 % of its light to ±34 mm reads the same as one that
throws none. **So a value near 1.0 is the most dangerous, not a large one** —
the opposite of what I assumed for most of the day.

Measured on identical renders (p10/d90, beam 2, theta -40): 1.35x through a
24 mm window, 23.03x through a converged one, converging at 192 mm.

### The one that changes a decision: #2 and #6 on head-on

The three axes behave differently under pixel size, and the reason is what kind
of statistic each is:

| axis | statistic | pixel size | why |
|---|---|---|---|
| total | area average | indifferent (0.9 % over 13x) | averaging is what a bigger pixel already does |
| smear | ratio of two widths in one frame | indifferent (0.5 % over 5.6x) | numerator and denominator blur together |
| head-on | **peak** | **decisive (55 % over 5.6x)** | a peak has nothing to cancel against |

Measured, order spec, panel 100:

| density | smear | head-on |
|---|---|---|
| 0.215 mm/px (protocol) | 2.238 | 0.1835 |
| 0.600 | 2.232 | 0.1064 |
| 1.200 | 2.227 | 0.0821 |

The bias is always **downward**, on the one axis that says whether the audience
is dazzled. Every published head-on read a design as safer than it is.

---

## 2. The protocol, and where each number in it came from

Nothing here is chosen; each condition is the result of a convergence sweep run
today.

| axis | angle | density | sample | window |
|---|---|---|---|---|
| total | 0, ±40 | 0.215 mm/px | full panel, **>= 25 cells** | face minus 4 px sky shield |
| smear | ±40 | 0.215 mm/px | full panel | **opened until two readings agree** |
| head-on | **0** | **min feature / 4** | **10-cell patch** | the patch |

- **min feature / 4**: head-on was swept at 1, 2, 4, 8, 16 pixels across the
  0.4 mm tip and settled at 4 — 0.15024 / 0.16979 / 0.18898 / 0.18907 / 0.18874.
- **10-cell patch**: a peak is local. The patch (40 mm) returns 0.18919 against
  0.18881 and 0.18895 from full 100 and 200 mm panels at fine density — 0.2 %,
  and **25x faster**. Resolving a honeycomb's 0.08 mm wall across a 400 mm panel
  is 15 000 px and hours; ten cells of it is minutes.
- **>= 25 cells**: GATE 11 swept 5/10/25/50 cells and rho_dh fell monotonically
  (0.001096 / 0.001033 / 0.000995 / 0.000984), still moving at 50. 25 cells
  reads ~1 % high. Recorded as a residual, not solved.
- **window to convergence**: two independent convergences landed on ~6x the
  return's 90 % half-width (p10/d90: z90 30 mm, converged at 192; order spec:
  z90 10 mm, at 48).
- **4-px sky shield**: the totals path fills the world with radiance 1.0, so a
  window at the exact face edge caught background 20x brighter than the control
  — 0.0530 against 0.0500 from a 0.3 % sliver. The inset is a sky shield, not
  only an edge shield, and must stay on that path.

### Density each family actually needs

| design | min feature | needed | the 0.215 protocol is |
|---|---|---|---|
| pyramid p4 / tip 0.4 (order spec) | 0.40 mm | 0.100 | 2.1x too coarse |
| pyramid p4 / tip 0.1 (study std) | 0.10 mm | 0.025 | 8.6x too coarse |
| honeycomb 6.5 / wall 0.08 | 0.08 mm | 0.020 | 10.8x too coarse |
| blade 0.1 | 0.10 mm | 0.025 | 8.6x too coarse |

---

## 3. What the instrument now passes

| gate | question | result |
|---|---|---|
| 1 control | does the 0.05 plate read 0.050000? | PASS, every design and angle |
| 2 scale | same shape over a 25x size span | PASS 0.55 % (stock) / 1.70 % (repaired) |
| 3 pixels | halve mm-per-pixel | PASS 0.87 % |
| 4 rays | 4x the samples | PASS 0.31 % |
| 5 window | does smear converge? | PASS, both fine and coarse pitch |
| 6 scale (form) | same shape 5x bigger, beam scaled | PASS 0.8 % |
| 11 cells | how many cells is enough? | **FAIL — still moving at 50** |
| 13 furnace | rho=1 cavity must return 1.000 | **PASS 0.999906** at 512 bounces |
| 16 feature px | pixels across the tip | converges at 4 |

**The measurement floor is 1-2 %.** Smaller differences are not differences.

### The furnace test, which had been failing on the record

`FINDINGS_renderer_disagreement.md` recorded a rho = 1 comb returning 0.673 and
explained it as bounce truncation. Correct, and not a pass. Run on the real
pyramid field with bounces swept:

| bounces | reads | deficit |
|---|---|---|
| 8 | 0.467010 | 0.5330 |
| 32 | 0.806371 | 0.1936 |
| 128 | 0.989164 | 0.0108 |
| 512 | 0.999905 | 0.0001 |
| 2048 | 0.999906 | 0.0001 |

**The renderer loses no energy.** The old 0.673 was truncation, now proven
rather than argued. Note that **128 bounces is not enough at high reflectance**
— the shipped default — though the real 1 % coating is dead in three.

Re-run 2026-08-20 evening, one Blender process per point, reproduces the row
above to five decimals: 0.467013 / 0.806381 / 0.989174 / 0.999904 / 0.999904.
The plateau is identical at 512 and 2048, so the residual 96 ppm is the floor,
not a climb that has not finished.

### But the flat CONTROL was broken, twice, and both were mine

The furnace sweep only means something next to a control that separates *the
renderer loses energy* from *this cavity needs bounces*. That control failed
every run, and each time the fault was in the control, not the renderer.

**First: the "flat" plate was not flat.** It was a pyramid field 0.001 mm deep.
It read 0.662 at 1, 4, 32 and 256 bounces — frozen to six figures, which is the
signature of rays being *killed* rather than absorbed; an unfinished sum climbs.
One micrometre of relief is below Cycles' ray offset, so a bounce departs
already inside the neighbouring facet and self-terminates.

**Second: depth = 0 stacks the geometry on one plane.** The pyramid tips and
the backing's top face both land on y = 0. Measured on the built mesh:

| plate | area lying exactly on y = 0 | layers over the 100 x 100 face | facing down or sideways |
|---|---|---|---|
| depth 0 (the "flat" control) | 38576 mm2 | **2.87** | 13456 mm2 |
| depth 20 (the real field) | 22.09 mm2 | 0.00 | 0 |

**CORRECTED 2026-08-21.** This first said 3.86 layers, from dividing the stacked
area by the 100 x 100 face. The plane it stacks on is the whole panel INCLUDING
its margin skirt, 13456 mm2, so the figure is 2.87. Same defect, smaller number,
and the denominator was never checked before it was published here.

At rho = 1 a stack costs nothing — the sum still converges to 1.000000 — which
is why the energy check passed anyway and hid the defect. At rho = 0.5 the plate
read **0.354 where 0.5 was predicted**. That failure was pre-registered as
evidence the renderer's BSDF was wrong. It was not.

The sentence that stood here said "every spurious bounce halves the light". I
wrote that as an explanation before testing it, and it is not what the evidence
shows — an outgoing ray leaving a plane never meets that plane again, and a ray
probe built to find the wasted bounce scored the known-bad plate at 0.00 %.
What IS measured settles it: **move the coincident sheet 0.01 mm and the plate
reads exactly 0.500000**, up from 0.343224. Coincidence is the cause; the
mechanism sentence was mine and is withdrawn. Deleting duplicate faces changes
nothing, because there are none — the two sheets are different polygons
occupying one plane.

**The BSDF control has to be a bare quad.** One face, no rig, no control plate,
no backing, nothing that can occlude it; under a uniform sky of radiance 1 a
Lambertian of albedo r must read exactly r at one bounce:

| albedo | reads | spread across the face |
|---|---|---|
| 1.0 | 1.000000 | 0 |
| 0.5 | 0.500000 | 0 |
| 0.05 | 0.050000 | 0 |
| 0.01 | 0.010000 | 0 |

Exact at every level, with zero variation across the face. **The real geometry
at depth 20 carries no coincident surface at all**, so neither defect ever
touched a published measurement — but the instrument that was supposed to prove
that had been reading its own damage for as long as it existed.

### The sweep kept dying with exit code 0

Three runs stopped partway through the bounce sweep with no traceback and a
zero exit status, which reads as "finished". The crash report names it:

    ccl::MetalKernelPipeline::compile()
    ccl::path_cache_get(...)
    BUG_IN_CLIENT_OF_LIBMALLOC: POINTER BEING FREED WAS NOT ALLOCATED

[confirmed: ~/Library/Logs/DiagnosticReports/Blender-2026-08-20-161521.ips]

Cycles' Metal shader-cache thread double-frees when it recompiles a kernel, and
sweeping bounce counts inside one process forces exactly that. Nothing to do
with the geometry. `gate_furnace_step.py` takes ONE reading per process, so the
kernel compiles once; the driver retries a point that produces no reading,
because the same crash also hits the first launches against a cold cache.

**Any batch that varies a render setting in a loop inside one Blender is
exposed to this, and it fails silently.** A run that stops early looks like a
run that finished.

### The render's mesh IS the exporters' mesh

The STEP file declares itself "not a closed solid: 28 open edges", which raises
the obvious question of whether the geometry the renderer traced was also
wrong. It was not, and this is measured rather than argued: build the render
scene, read the mesh BACK OUT of Blender — the actual triangles light hits —
and compare it to what the exporter writes.

| design | render (read from Blender) | exporter |
|---|---|---|
| pyramid p4/d22 | V 808  F 606  A 23344.69 | V 808  F 606  A 23344.69 |
| pyramid p2/d18 | V 988  F 986  A 16261.76 | V 988  F 986  A 16261.76 |
| honeycomb d50 | V 1560  F 1170  A 113445.55 | V 1560  F 1170  A 113445.55 |

Identical, with no zero-area faces. Surface **area** is the quantity that
decides how much light a face catches, so agreement there is the agreement that
matters. The one initial mismatch was 1.05e-06 mm of bounding box, which is
float32 round-trip on a 53 mm coordinate — the tolerance was tighter than
Blender's own vertex storage, so the gate now sets its bar at one ulp.

The open edges are a property of the *shell*, not the surfaces: the panel is
modelled as overlapping solids, so faces meet inside the material where no
light reaches. That blocks booleans in CAD. It does not move a photon.

---

## 4. Numbers that change

| quantity | published | verified | direction |
|---|---|---|---|
| order spec head-on | 0.173 | **0.189** | +9.2 %, worse |
| study std head-on | 0.040 | **0.0677** | +69 %, worse |
| **tip 0.1 -> 0.4 head-on penalty** | **4.3x** | **2.8x** | smaller than published |
| p10/d90 smear (phase 5.5) | 1.272 | **24.77** | 19x |
| p5.5/d50 smear (phase 5.5) | 4.159 | **14.22** | 3.4x |
| p2/d18 smear (phase 5.5) | 4.104 | **5.226** | 1.27x |

**Phase 5.5's verdict inverts.** It concluded "coarse pitch is not
rehabilitated by a big beam"; with converged windows the order is
p10 > p5.5 > p2 at every beam width, the reverse of what was published, and
p10 was rejected on the strength of the wrong number.

The order spec's own decision improves: relaxing the tip from 0.1 to 0.4 costs
2.8x on head-on, not the 4.3x on record, because the finer tip was 8.6x
under-resolved against the coarser one's 2.1x.

### Re-verification across panel size (order spec, corrected rig)

| panel | cells | total % | smear | head-on | control |
|---|---|---|---|---|---|
| 100 | 25 | 0.1512 | 2.2391 | 0.18919 | OK |
| 200 | 50 | 0.1501 | 2.2394 | 0.18919 | OK |
| 400 | 100 | 0.1495 | 2.2387 | 0.18919 | OK |

Total within 1.1 %, smear within 0.03 %. The same sweep this morning moved 4.1x.

---

## 5. A new axis: the returned line is displaced

Not previously measured, and it is what the audience actually sees — where the
copy lands, not only how wide it is.

> **displacement = 0.59 x depth x tan(incidence)**

| depth | offset at -40 deg | ratio |
|---|---|---|
| 10 mm | 4.687 | 0.469 |
| 20 | 9.377 | 0.469 |
| 30 | 14.395 | 0.480 |
| 50 | 24.824 | 0.496 |
| 80 | 40.793 | 0.510 |

Slope through the origin 0.502, R2 0.9982. Independent of pitch (0.501 / 0.496
/ 0.475 at pitch 2 / 4 / 10) and the coefficient holds across angle (0.587 /
0.591 / 0.595 at 20 / 40 / 60 deg). Light leaves from about 60 % of the way
down the well. The order spec displaces 11 mm at 40 deg; a 90 mm well, 45 mm.

The measurement convention matters here and must be stated: `recentre` puts
each profile on its OWN centroid, which subtracts the displacement. The code it
replaced put both on the CONTROL centroid and kept it. The two conventions
change the design ORDER (p10 vs p5.5 swap), so **displacement should be
reported as its own axis, not folded into a width**.

---

## 6. The tools

- **Mitsuba** was dead: its venv lived under `/private/tmp`, macOS pruned it by
  access time and removed `pyvenv.cfg` and the package `__init__.py` files while
  leaving the directory standing, so the existence check passed and every
  cross-check died on `ModuleNotFoundError`. Rebuilt at `~/.spillsink/mts_env`;
  the interpreter is now resolved from a candidate list.
- **The third tracer** (`raytrace_viz.py`) is the only code with **no
  scale-dependent constant**, because it has no pixels — and six of the nine
  defects were pixels. Verified scale-invariant to 0.4 % over a 1000x size
  range, its error falls as 1/sqrt(N) (0.585 / 0.564 / 0.563 against the ideal
  0.548), and its converged rho sits **0.07 sigma** from Cycles.
- **Radiance 6.0.2** installed at `~/.spillsink/radiance`, with `genBSDF`. Not
  yet wired in. It is the only tool in reach that has been **validated against a
  physical goniophotometer**, which is the connection this project lacks
  entirely.

---

---

## 5b. 2026-08-21 — what the audit found once it was pointed at the batches

### The geometry family was chosen by a default, and two jobs died of it

`rig_v2.build` took `family="floor"` as its default, so any caller that did not
name its family got the floor module whatever it had asked for:

    rig_v2_gates_mesh.py  kind="cone", tip_radius=0.2
      -> FloorParams.__init__() got an unexpected keyword argument 'tip_radius'
    sweep_standalone.py   wall_top=...
      -> FloorParams.__init__() got an unexpected keyword argument 'wall_top'

**No wrong shape was ever measured** — a dataclass rejects an unknown keyword and
`geom_floor.build_mesh` raises on an unknown `kind`, so the mis-routing is loud.
But the job dies, and a dead batch's log ends on a plausible data row. Both had
been dead for a day. `build` now infers the family from the parameter NAMES,
tries `floor` first so every working call keeps the family it had, and reports
what each family rejected instead of letting one TypeError stand for the whole
answer. `kind` is also read as a family selector when no floor builder claims
it, and dropped from the parameters in that case — inference and the call have
to agree on one set, which the first version of the fix did not.

### Batches were dying silently, and the log looked finished

Three classes, all of which read as success:

| how it died | what the log shows |
|---|---|
| Cycles Metal shader cache double-free | last line is a data row, exit code 0, no `Blender quit` |
| loud TypeError | traceback, but the table above it looks complete |
| sim server restarted or 500'd under the job | HTTP error at the end of a partial table |

`scripts/run_batch.sh` refuses to call a job finished without its own marker.
No error and no marker means the Metal abort, which it retries once against a
warm cache. Blender prints `Blender quit` on a clean exit and does not when it
aborts, so that line separates the first class from the second — and it is the
only check available for the ~98 older sweep scripts that print no marker.

Recovered by this: `mesh_gate` (83 s), `gates_form` (3542 s, a TypeError nobody
had ever looked at), `famsize` (66309 s), `featpx`.

### Measurement scripts must not call the app

`gate_feature_px.py` posted to the sim server and died twice on HTTP 500: once
because the server restarted under it, once because it and the user's Render
button were queued behind one worker. `form` is a plain function. It is called
in-process now, and so are the two coating gates.

### My own two new gates printed DONE with every cell empty

`gate_diffuse_fraction` and `gate_floor_coat_totals` read `out["rho_dh"]`;
`measure()` returns `{phi: {theta: value}}`. Every cell came back None and both
scripts printed their marker — the exact silent success they were written to
stop. They now refuse to finish with a hole in the table.

### The density rule serves BOTH axes, and the doubt is retracted

An old server-killed log of the feature-pixel sweep showed smear falling
2.2377 -> 1.0082 across the densities where head-on was flat, which would have
meant `mm_per_px = min_feature / 4` was fixed by watching one axis and silently
wrong for another. Re-run on the repaired rig:

| px per tip | mm/px | head-on | smear |
|---|---|---|---|
| 1 | 0.4000 | 0.15024 | 2.2377 |
| 2 | 0.2000 | 0.16979 | 2.2388 |
| **4** | **0.1000** | **0.18898** | **2.2396** |
| 8 | 0.0500 | 0.18907 | 2.2397 |
| 16 | 0.0250 | 0.18874 | 2.2398 |

Smear never moves. The collapse was the old window defect, not density, and the
rule stands. The sweep then stopped at 32 px/tip on a REFUSAL, not a crash —
"needs 24480 px and the budget is 200" — which is the resolution cap doing the
job it was rewritten for, where the old code would have quietly coarsened and
answered anyway.

### Panel size does not touch head-on

    panel  400 mm -> 1.64311
    panel  700 mm -> 1.64309
    panel 1000 mm -> 1.64311

Five decimals across a 2.5x change in panel size.

### The honeycomb is clean, and my claim that it was not is withdrawn

A geometry check reported the honeycomb's cell walls stacked 4.4 deep over
85.9 % of the panel. **That was an artifact of my own detector**, which keyed
planes on `abs(nx), abs(ny), abs(nz)` and `abs(offset)`: honeycomb walls sit at
+-60 degrees, so four distinct orientations and both sides of a symmetric panel
landed in one bucket. With a canonical signed key, and counting only faces
light can actually reach (found by tracing rays in and letting them bounce):

| design | worst stacking | stacked area |
|---|---|---|
| flat depth 0 (known bad) | 2.22 layers | 100 % |
| pyramid depth 20 (known clean) | 0.51 | 0 % |
| pyramid p4/d22 | 0.55 | 0 % |
| honeycomb p6/d50 | 1.14 | 0 % |
| honeycomb p6/d10 | 1.14 | 0 % |
| honeycomb p3/d30 | 1.21 | 0 % |

The `+8.85 %` I reported from nudging the honeycomb's "coincident" sheets apart
is withdrawn with it: those faces were not coincident, so the nudge opened
0.01 mm slits and the light leaked through them.

Confirmed with the instrument that was already validated rather than a third
new detector — the white furnace on the honeycomb itself:

| bounces | reads |
|---|---|
| 32 | 0.133623 |
| 128 | 0.612317 |
| 512 | 0.986594 |
| 2048 | 0.999776 |
| 8192 | 0.999776 |

Deficit 224 ppm at plateau, against the pyramid's 96 ppm. **The honeycomb loses
no energy.** And the builder was never at fault: `_build_honeycomb` keys every
wall on `(i, j)` and raises each shared wall once, and `voronoi_cells` exists
precisely because an earlier jittered-hexagon version DID double its walls.

### Resolving the feature: W3 confirmed, W4 refuted, and the honeycomb stands

`sweep_standalone` gave every family a density of min_feature / 4 and read
head-on off a 10-cell patch. Panel 100 to 400 mm, three families:

| design | min feature | at the 0.215 protocol | resolved at feature/4 | change |
|---|---|---|---|---|
| pyramid p4/d22/t0.4 (order spec) | 0.40 mm | 0.18234—0.18471 | **0.18919** | +9 % vs the published 0.173 |
| pyramid p4/d20/t0.1 (study std) | 0.10 mm | 0.040 published | **0.06771** | **+69 %** |
| honeycomb 6.5/w0.08 | 0.08 mm | 1.639 published | **1.64314** | +0.3 %, i.e. nothing |

**W3 holds: the finer the feature, the larger the correction** — except that
the honeycomb, whose wall is the finest feature of the three at 0.37 px, does
not move at all. **W4 is refuted.** I had predicted the honeycomb's 1.639 was
an under-resolution artifact and that resolving the wall would raise it
materially. It reads 1.64314 with the wall at 4 px, five figures identical.
**The rejection of the honeycomb was made on a sound number and stands.**

Why the honeycomb is the exception is [추측]: a cell wall seen from head-on is a
LINE with a flat top, so the fraction of a pixel it covers does not change when
the pixel shrinks; a pyramid tip is a POINT, and subdividing the pixel uncovers
the peak that was averaged away. Not tested — it needs a sweep of wall-top
width at fixed density.

Two things this settles beyond the honeycomb:

  - The corrected figures already written into `SPEC_SUMMARY.md` and
    `metrics/04_peak_radiance.md` (0.189 and 0.0677) are **independently
    reproduced** here by a different script on its own rig: 0.18919 and
    0.06771.
  - Panel size does not touch head-on once the feature is resolved: 100, 200
    and 400 mm agree to five figures in all three families, which matches
    `sweep_family_size` over 50—1000 mm.

Still carrying an old-density number: the extrusion comparison in both spec
summaries, "40x brighter head-on, measured 0.040 vs 0.894". Both halves were
read at the old density, so the RATIO may survive but the absolute values do
not. Flagged in place; the groove has not been re-measured at the matching
density.

### `sweep_family_size`: what it can and cannot see, and two predictions wrong

Same three families, panel 50 to 1000 mm, at the PROTOCOL density:

| design | total | smear | head-on |
|---|---|---|---|
| pyramid p4/d22/t0.4 | 0.37 % | 0.12 % | 1.65 % PASS |
| pyramid p4/d20/t0.1 | 0.40 % | 0.25 % | **2.47 % FAIL** |
| honeycomb 6.5/w0.08 | 1.55 % | 0.49 % | 0.01 % PASS |

S3 predicted head-on would FALL as the panel grew, because mm-per-pixel is
fixed while the feature is not; S4 predicted the honeycomb would be worst hit.
**Both wrong.** The honeycomb is the steadiest of the three (0.01 %), and the
most unstable is the pyramid with the 0.1 mm tip.

The lesson is that this sweep measures the wrong quantity for the question I
asked of it. Under-resolution produces a BIAS, not a scatter: changing panel
size does not change the density, so the same bias enters every row and cancels
in the spread. **Scatter with size and bias from density are different
measurements**, and only `sweep_standalone` above measures the second.

### The coating's diffuse fraction, measured instead of quoted

The fitted coating is 76 % Lambertian plus a 24 % Fresnel lobe. That split is a
FIT, so whatever it drags along is a systematic on every published total. Swept
0.50 to 1.00 with the geometry held fixed, against a flat plate that has no
geometry to contribute:

| design | spread at theta 0 | spread at theta -40 |
|---|---|---|
| flat plate | 0.2 % | 6.9 % |
| pyramid p4/d22 | 11.7 % | **34.4 %** |

Predictions D1, D2 and D3 hold. D4 holds too: the pyramid stays far below the
flat plate at every fraction, so **no ranking in the study is decided by the
coating fit.**

Two things are larger than the record said. The systematic at -40 was noted as
15 %; it is **34.4 %**, so every published total at the deployment angle carries
that much uncertainty from a number nobody has measured. And the two angles move
in OPPOSITE directions — raising the diffuse fraction darkens head-on
(0.00102 -> 0.00092) and brightens -40 (0.00126 -> 0.00170) — so a single
"the coating makes it x % worse" correction cannot exist.

Because the flat plate barely moves, **the lever is the geometry, not the
coating**: what the fraction changes is how a valley treats a specular lobe
versus a diffuse one. `NEXT.md` and `JOURNAL.md` still carried "41x, with rank
inversion", withdrawn in CONTEXT.md long ago; both now carry the measurement.

### The floor's finish: worth 26 % on a shallow cell, worth nothing on a deep one

Comb geometry fixed, only the floor's coating swept. Cell pitch 6 mm, so the
40-degree beam stops reaching the floor above 6/tan40 = 7.15 mm of cell depth:

| stack | spread at theta 0 | spread at theta -40 |
|---|---|---|
| shallow, cell depth 10, floor 4 | **34.5 %** | 1.9 % |
| deep, cell depth 50, floor 4 | 1.7 % | **0.0 %** |

F1 and F2 confirmed, and the reach law with them: the deep cell's total does not
move by a single digit at -40 however black the floor is painted. Even head-on a
50 mm cell barely sees its own floor (1.7 %).

F3 fails, and that is the useful part. On the shallow stack the floor finish is
**as large a lever as the geometry**: leaving it anodised reads 0.00283 head-on,
painting it Musou reads 0.00210 — **26 % better for a coat of paint**. A
shallow-cell design has to specify its floor finish; a deep-cell design need not
bother.

### There is a standard for this, and we were doing half of it

Two separate questions, two separate bodies of practice.

**Is the software right?** CIE 171:2006, test cases to assess the accuracy of
lighting computer programs, with analytical and experimental reference data per
aspect of light propagation — not updated since 2006. Plus the white furnace
test, which is not a standard but is the accepted way to catch a renderer
losing energy. We do this.

**Is the MODEL fit to trace?** The optical-simulation rule is blunt: a valid
watertight solid, no internal faces, and solids that touch or overlap must be
Booleaned into one before use, because a non-watertight mesh sends rays through
the holes and those rays are counted as errors [Ansys Speos / TracePro CAD
import guidance]. ISO 10303-59 names the defect classes. STEP geometric
validation properties are the standard check on a transferred model — volume,
surface area and centroid written into the file and recomputed by the receiver
— at CAx-IF thresholds of under 1 % deviation to pass, 1-10 % marginal, over
10 % failed; centroid under 1 mm, 1-5 mm, over 5 mm. **We did not do this.** The
one honest diagnostic we had, `weld_and_close`, ran only on Export STEP and
wrote its verdict into a file header.

`scripts/gate_model_fitness.py` is that check: open and non-manifold edges, the
Euler characteristic, duplicate faces, and stacking among light-reachable faces
only. **It validates itself on a known-bad and a known-clean panel first and
refuses to print the rest if it fails either.** It failed twice while being
written and stopped both times, which is the whole point.

Sources: Ansys Speos meshing and CAD-import guidance (optics.ansys.com);
ISO 10303-59:2022; MBx-IF Recommended Practices for Geometric and Assembly
Validation Properties v4.5 section 4.13; CIE 171:2006.

---

---

## 5c. 2026-08-21 evening — the honeycomb study, and four defects in the tracer

### The ray tracer was wrong in four ways, and every one of them flattered the panel

**It ignored the base coating and the coverage.** `rho` came from
`CO[$('#coat').value].rho0`, the TOP paint, whatever the rest of the panel wore.
A panel with anodised base and 0 % coverage — no Musou on it anywhere — still
traced at Musou's 1 % and printed "musou_fit 1.00%" under the result. It now
takes the area-weighted mix and says so.

**Its bounce limit was 24, and deep cells hit it.** At cell 6.35 / depth 50,
head-on, the MEAN bounce count was 23.7 — sitting on the limit. A path cut
short is counted as absorbed:

| bounce limit | reads | mean bounces |
|---|---|---|
| 24 | 0.122 % | 23.7 |
| 200 | 0.186 % | 101.3 |

**The deeper the design, the more it flattered it**, which is exactly backwards
for a study whose whole question is how deep to go. Raised to 200.

**Its default mode was `specular` — a mirror.** Anodised aluminium and black
paint are not mirrors. In mirror mode a head-on ray hits the floor, reflects
straight back, and leaves after ONE bounce, so the trace reported 4.36 % at
theta 0 while the Render reported 0.19 %. Both were right for their own
material. Default is now the fitted mix.

**It never read the diffuse-fraction or roughness sliders at all.** The panel
described on the left as "these three describe the whole panel" was two
sliders the trace did not see. A `fitted` mode now mixes per bounce with the
panel's own diffuse fraction and blurs the mirror leg by its roughness.
Validated on a flat plate: trace 4.500 % against Render 4.464 %. On a
honeycomb the two still differ by 20-30 % in magnitude while agreeing in
shape; **not explained.**

### rho_dh IS the beam answer, and my "re-measure with a beam" was wrong

I built `gate_beam_total.py` to re-measure everything under an actual beam,
believing the sky-illuminated `rho_dh` did not describe a laser. It does:
rho_dh(theta) is by definition the fraction of light arriving at theta that
leaves again, and reciprocity is only how it is read.

Worse, the gate itself was invalid. It summed pixels in the camera's view,
which is radiance toward one direction, not flux over the hemisphere. The
control test says so plainly: put the CONTROL'S OWN material in the panel slot
and it reads 1.0019 — correct — but add the paint's gloss and the same flat
panel reads 8.2448, which cannot be a returned fraction. I had already put a
warning on the published report telling the reader not to use its numbers. The
numbers were right; the warning was mine and is withdrawn.

### Why a honeycomb of 5 % material returns 0.3 %, checked two independent ways

The question came up four times and deserves the arithmetic. Light enters a
vertical tube at 0 degrees and reaches the floor without touching a wall — the
way in is free. The way OUT is not: the floor scatters into the whole
hemisphere, and from the bottom of a 60 mm tube 6.35 mm wide the opening
subtends a half-angle of **3.0 degrees**, so only **0.28 %** of the scattered
light leaves directly. The rest hits walls, and each hit keeps 5 %.

An independent Monte Carlo — 200k photons bounced by hand, no Blender —
against the render, pure diffuse 5 %, normal incidence, flat panel = 1:

| depth | hand: tube | hand: rim | hand: total | render | gap |
|---|---|---|---|---|---|
| 30 | 0.0137 | 0.0369 | 0.0505 | 0.0454 | -10 % |
| 40 | 0.0079 | 0.0369 | 0.0448 | 0.0398 | -11 % |
| 50 | 0.0048 | 0.0369 | 0.0417 | 0.0352 | -16 % |
| 60 | 0.0035 | 0.0369 | 0.0403 | 0.0350 | -13 % |

Two methods sharing no code, agreeing within 16 %.

**Most of what comes back is not from the tube at all.** The foil rim — the
0.08 mm top edge, measured at 3.69 % of the face — is not in a cavity and
behaves like a flat wall. At depth 60 it is **nine tenths** of the return.

### Where the paint has to be, per angle

Cell 6.35 / depth 30, base anodised 4.5 %, Musou from the mouth down:

| Musou depth | head-on | 40 deg |
|---|---|---|
| 0 | 0.4662 % | 0.8489 % |
| 1 mm | 0.3448 % | 0.5432 % |
| 5 mm | 0.3386 % | 0.2266 % |
| 10 mm | 0.3314 % | 0.1864 % |
| 20 mm | 0.3205 % | 0.1863 % |
| 29 mm | 0.3140 % | 0.1863 % |
| **30 mm** | **0.0963 %** | 0.1863 % |

Three surfaces, three jobs:

  - **the rim** — 1 mm catches it, and that is a third of the head-on change
  - **the walls** — 5-10 mm is everything at 40 degrees, because a 40-degree
    beam never goes below pitch/tan(40) = 7.6 mm. 20 and 29 mm read identically.
  - **the floor** — nothing until the paint reaches the full depth, then it
    supplies the remaining 61 % of the head-on change

**A dipped honeycomb cannot reach its own floor**, so under the user's process
the head-on total stops at ~0.31 % however deep the dip.

### The head-on FLASH is the paint, not the structure

The peak ratio is unchanged by the honeycomb, and it is not the gloss lobe
retracing the tube — that was my explanation and it is wrong. Measured with
the gloss removed entirely:

| | with gloss | gloss-free |
|---|---|---|
| flat wall | 8.2293 | 1.0000 |
| comb depth 30 | 8.2256 | 0.9999 |
| comb depth 60 | 7.1531 | 0.9992 |

**Gloss-free, the comb reads the same as a flat wall to four figures.** The
reason is that a peak is a RADIANCE and a tube does not dim what you see
straight down it — it only narrows the angles you can see it from. Looking
head-on into a cell is optically the same as looking at a flat panel of the
same paint.

What the flash actually measures is the coating's gloss:

| diffuse / specular | peak |
|---|---|
| 100 / 0 | 1.00 |
| 90 / 10 | 4.01 |
| **76 / 24 (the fit)** | **8.23** |
| 60 / 40 | 13.05 |
| 40 / 60 | 19.08 |

**Every head-on number in this project rests on the 76 % diffuse fraction,
which is a fit and has never been measured.** At 60 % it would be 13.05.

### Renderer checks that PASSED, so the above is not a renderer fault

Pure diffuse, flat plate, reads the coating exactly and is flat in angle:
5.0000 % at 0, 20, 40 and 60 degrees. With the fitted gloss it rises with
angle — 4.955 / 4.963 / 5.121 / 6.377 — which is Fresnel and is expected.
The split does under-deliver at normal incidence by 0.2 % (Musou) to 1.1 %
(anodised_hi); small, and recorded rather than fixed.

### The labels were the real defect in the report

"정면" meant the VIEWING angle for the total and the INCIDENCE angle for the
flash, and the report said "the angle light comes in at" for both. A reader
asked four times why head-on was the darkest column when head-on is the
brightest thing you can look at, and the answer each time was that the label
was wrong, not the number. **Every measured column now has to name its
illumination, its direction, and whether it is an average or a peak** — and
the Render readout in the simulator now prints the material under the result
for the same reason.

---

---

## 5d. 2026-08-22 — the coating was the biggest error in the study

### The diffuse fraction was never measured, and it is not 0.76

Every published number in phases 2—5 used a diffuse fraction of 0.76 with a
specular roughness of 0.30. Both were ASSUMPTIONS. `principles/00_how_to_run.md`
says so in the open: the protocol takes the worst of three coating guesses,
d = 0.0 / 0.76 / 1.00. Nobody measured a real one.

Two papers do measure it, and 0.76 contradicts both.

**DePoy et al., SPIE 9147, 91474Q (2014), arXiv:1407.8265** measure the
specular fraction directly: a HeNe laser at 10, 22 and 44 degrees, a photodiode
in the specular direction, and diffuse = 1 — specular. **That is our
definition of the diffuse fraction.** Their Figure 6:

| surface | specular | diffuse fraction |
|---|---|---|
| black anodised aluminium, bead-blasted | 0.02 | **0.98** |
| black anodised aluminium, raw | 0.03 | **0.97** |
| matte black spraypaint | 0.03 | **0.97** |
| black anodised aluminium, machined | 0.05 | 0.95 |
| black anodised aluminium, POLISHED | 0.70 | **0.30** |

**Black paint is very nearly a perfect diffuser.** Only the polished surface
behaves like a mirror.

**Filip & Vavra, JOSA A 43, 1037 (2026)** rank specular strength across black
coatings: acrylic matte spray is the strongest, Musou paint markedly weaker.
So Musou must sit ABOVE the 0.97 measured for matte spray, not at 0.76 — at
0.76 the model says Musou is glossier than ordinary black paint, which both
papers contradict. Musou is now 0.99, and that number is an ordering argument,
not a measurement.

### What the correction does to the numbers

Same geometry, same rho0, only the diffuse fraction changed:

| | at d = 0.76 | at the measured d |
|---|---|---|
| comb 6.35 / depth 40 / no Musou, head-on | 0.403 % | 0.216 % |
| the same at 40 deg | 0.906 % | 1.097 % |
| its head-on FLASH | 8.22 | **1.90** |
| best of the 32, head-on | 0.156 % | 0.058 % |

**Head-on halves, off-axis rises about 20 %, and the flash drops to a
quarter.** More diffuse means less comes straight back and more spreads
sideways, which is exactly what moves.

**"The flash is 8x" was an artifact of the wrong coating.** At the measured
0.97 it is 1.90.

### The published ranking flips, and the designs are actually tied

Measured directly across four diffuse fractions, worst of five thetas and
three azimuth planes, Musou throughout:

| design | d=0 | d=0.76 | d=0.97 | d=1.00 |
|---|---|---|---|---|
| pyramid p4/d22/t0.4 | 0.1177 | 0.1842 | 0.2290 | 0.2355 |
| pyramid p4/d20/t0.1 | 0.1045 | 0.1835 | 0.2310 | 0.2378 |
| comb 6.35/d40 | 0.2079 | 0.1876 | 0.2262 | 0.2317 |
| flat plate | 1.1414 | 1.0305 | 1.0020 | 0.9980 |

    d = 0.76   pyramid t0.1  <  pyramid t0.4  <  comb  <  flat
    d = 0.97   comb  <  pyramid t0.4  <  pyramid t0.1  <  flat

The order reverses among the three structures. **But read it properly: the
three sit within 2 % of each other at the measured coating.** The honest
statement is not "the comb wins", it is **"at the real coating these three
cannot be told apart"** — and the published claim that the pyramid beats the
honeycomb rests on a coating value nobody measured.

### The 66 000 published rows do NOT have to be re-rendered

The sweeps already carry d = 0.00 / 0.76 / 1.00 (16 360 / 16 403 / 16 338
rows), and 3 900 design-angle combinations have all three. Interpolating d76
and d100 to 0.97 was checked against direct measurement on four designs:
**error 0.0 to 0.1 %.** So the corrected numbers can be produced from the
existing data.

One caveat that changes how the protocol should read: **the worst of the three
guesses is a different guess at different angles.** Head-on, d = 0 is worst;
at 40 degrees, d = 1 is worst. A protocol that takes the worst of three is not
taking a coating, it is taking an envelope — and now that the coating is
measured, the envelope is the wrong instrument.

### Materials are now a table with provenance, in a file

`material/materials.json` is the single source; the simulator reads it, so
editing the file changes the tool. Each material carries rho0, df, rough, a
one-line source, and a provenance grade per value:

    measured   somebody put it on an instrument
    fitted     chosen so this project reproduces a measured total
    guessed    ordered against a measurement, magnitude unknown

Eleven materials. **Not one has a measured roughness** — DePoy et al. sample
three angles and cannot give a lobe width, Filip & Vavra show lobe shapes only
as plots. 0.30 is the original assumption and every head-on flash number still
rests on it.

### Four defects in the simulator, all of them coating

  - the ray tracer read only the top paint, ignoring the base and the coverage
  - its bounce limit of 24 truncated deep cells (mean 23.7 at depth 50)
  - its default mode was `specular`, a mirror, for materials that are 97 %
    diffuse
  - it never read the diffuse-fraction or roughness sliders at all
  - and `/api/form` — the smear + head-on button — dropped the coating in
    three separate places, so it reported Musou numbers whatever was picked

**Every one of them flattered the panel, and every one was material, not
geometry.** The geometry side passed every check it was given today.

---

## 5e. 2026-08-22 late — the roughness, and the flash is not reportable

### "Roughness has no effect" was wrong, and the sweep that said so was blind

`scripts/sweep_coatrobust.py` and the note in §5d concluded the specular
roughness barely moves anything. **That conclusion is withdrawn.** `form()` had
no `roughness` parameter at all, so the sweep set a value that was never
delivered to the renderer; every row measured the same 0.30. The claim is in
commit `409873e` and in the `coating-diffuse-fraction` memory, and both are
wrong.

After wiring `roughness` through `form()` and `/api/form`, a 5 % painted flat
plate at a fixed diffuse fraction of 0.97:

| roughness | head-on flash |
|---|---|
| 0.05 | 1200.97 |
| 0.10 | 75.98 |
| 0.20 | 5.66 |
| 0.30 | 1.90 |
| 0.45 | 1.16 |
| 0.60 | 1.04 |

**1160x across the range.** It is the single most powerful knob in the model,
and its value was never measured.

### Nobody publishes "roughness", but two groups publish something that pins it

The instruction was explicit: do not fit our own model to a foreign sample,
find what other people actually do. What they do is publish TIS.

**Filip & Vavra 2026 (arXiv 2601.05094), Fig. 6** report total integrated
scatter per material with a **5 degree half-angle specular exclusion cone**
(their §3.4). TIS is the share of reflected energy landing OUTSIDE that cone,
so `1 - TIS` is the share landing INSIDE it — and that is a direct measurement
of how tight the lobe is. Read off Fig. 6 at normal incidence:

| material | TIS at theta = 0 | share inside the 5 deg cone |
|---|---|---|
| acrylic matte black spray on aluminium | ~0.87-0.90 | 10-13 % |
| chalkboard paint | ~0.96-0.98 | 2-4 % |
| Musou paint | ~0.985-0.995 | 0.5-1.5 % |
| Vantablack | ~0.97-0.99 | 1-3 % |

`scripts/gate_roughness_from_tis.py` inverts this through our own BSDF
(`blender_render.coating_split`: at normal incidence the diffuse leg carries
`df * rho0` and the glossy leg `(1 - df) * rho0`). A Lambertian puts
`sin^2(5 deg) = 0.0076` inside the cone; a GGX lobe puts
`tan^2(2.5 deg) / (alpha^2 + tan^2(2.5 deg))`.

**For the acrylic matte spray — the closest published match to our 5 % paint —
a diffuse fraction of 0.97 has NO solution at all.** If only 3 % of the energy
is specular, no roughness can put 10 % inside a 5 degree cone. The measurement
rules out the pair we have been using.

| diffuse fraction | roughness that reproduces the measured TIS |
|---|---|
| 0.97 | impossible |
| 0.90 | 0.012 |
| 0.80 | 0.034 - 0.046 |
| 0.70 | 0.052 - 0.064 |
| 0.50 | 0.075 - 0.089 |

**Every solution is 0.01-0.11. Our 0.30 is outside the range for any diffuse
fraction.**

A second, independent read agrees. **Shirsekar 2019 (Virginia Tech MS thesis,
Fig. 4.2, Aeroglaze Z302 at 532 nm)** measures a full BRDF by goniometer. At 10
degrees incidence the specular maximum is ~2e-2 sr^-1 against a floor of
~4.5e-5 sr^-1 — a ratio near 440 — with a half-width of roughly 8 degrees. That
is alpha ~ 0.06. Z302 is a *gloss* black polyurethane, so it is an upper bound
on glossiness, and 0.06 lands inside the same window. The thesis is now in
`reference/papers/`.

### The two papers were never in conflict

DePoy et al. 2014 measure black spray paint at a diffuse fraction of 0.97;
Filip & Vavra's 5 degree cone says at most 0.90. That looked like a
contradiction. It is not — it is the detector.

DePoy put a **Gentec PH100-SiUV about 1 m from the sample**. A 10 mm detector
at 1 m subtends about **0.57 degrees** [추측: the aperture is not stated in the
paper; PH100 is a 10 x 10 mm head]. A lobe of alpha = 0.046 puts only ~1.3 % of
its energy inside 0.57 degrees but ~47 % inside 5 degrees. So DePoy's
"specular" catches the spike and misses the shoulder, and the diffuse fraction
they report is an **upper bound**, exactly as `material/_sources.json` already
warned. **Both papers are satisfied by roughly df = 0.8 and alpha = 0.04.**

### What this does to the three axes

`scripts/gate_paper_pairs.py`, 5 % painted flat plate, only the pairs the
measurement allows:

| pair (df / roughness) | total, brightest angle | smear rms | head-on flash |
|---|---|---|---|
| what we have been using, 0.97 / 0.30 | 5.014 % | 2.17 mm | **1.90** |
| 0.90 / 0.012 | 5.046 % | 2.18 mm | **1 143 834** |
| 0.80 / 0.034 | 5.098 % | 2.17 mm | 37 416 |
| 0.80 / 0.046 | 5.098 % | 2.17 mm | 11 168 |
| 0.70 / 0.052 | 5.155 % | 2.17 mm | 10 258 |
| 0.70 / 0.064 | 5.155 % | 2.17 mm | 4 471 |
| 0.50 / 0.089 | 5.287 % | 2.17 mm | 1 993 |

Pre-registered R1 and R2 both hold, and the consequence is sharp:

  - **Total reflectance survives.** 5.4 % across the whole allowed range. Every
    darkness ranking in the project stands.
  - **Smear survives.** 2.17 mm everywhere, unmoved to three figures.
  - **The head-on flash does not survive.** 574x of spread *inside* the allowed
    range alone, and up to 600 963x against the value we published. **No flash
    number in this project is reportable until a real coupon is measured.**

The user said this in plain words on 2026-08-21 — "정면이면 거울처럼 되돌아
와야 하는데 무슨 저런게 나와?" — and was told the tube explains it. The tube
does not explain it. A roughness of 0.30 was flattening the specular return of
a painted wall, and the intuition was right.

### What still cannot be answered

The allowed window (df 0.5-0.9, alpha 0.01-0.11) is **574x wide on the flash**.
Reading TIS off a published plot cannot close it. Closing it needs one
goniometer scan of one flat painted coupon — the same measurement
`material/_sources.json` has been asking for since 2026-08-22 morning.

---

## 7. Still open

1. **Cell count.** rho_dh was still falling at 50 cells a side. The study
   standard is 25 and reads ~1 % high.
2. **Cycles vs Mitsuba, +27 % on the pyramid at theta 0.** Solid families are
   supposed to agree (the cone does, at +3.6 %). Unexplained. The third tracer
   backs Cycles.
3. **Every smear and head-on ranking in the project** is provisional until
   re-measured under §2.
4. **The honeycomb**, whose published head-on of 1.639 rejected it as "no better
   than a flat plate", was measured with its wall spanning 0.37 of a pixel.
   Re-measurement in progress.
5. **Physical measurement: still zero.** CIE 171:2006 takes half its reference
   data from experiment for exactly this reason — simulation checked only
   against simulation cannot catch a shared error.

---

## 8. Withdrawn today, and by what

Kept because a reader needs to know which claims were tested and lost.

| claim I made | withdrawn by |
|---|---|
| "the smear is displacement, not spread" | `recentre` already removes displacement — though §5 shows the displacement is real and large |
| "I reproduced phase 5.5" | it used a 60 mm panel, I used 100 |
| "a faint wide halo drives the runaway rms" | the pedestal is 0.01 % |
| "163 % vs 3 % proves the repair" | it compared a 1-cell sample against a 25-cell one, not two rigs |
| "the control-plate overlap is the cause" | pyramids expose ~0 % at y=0; the stock rig reads 0.050000 even overlapped |
| "head-on is a peak so the window cannot touch it" | it moved 23 % |
| "small smear values are safe" | inverted: values near 1.0 are the most dangerous |
| "n_phase is a dead knob" | my test could not tell converged from dead; at beam < pitch it moves |
| my cone-binned head-on estimator | it is a radiance, the project's head-on is a profile peak — different quantities, and the standard method is Westin/Arvo/Torrance 1992 or Radiance's genBSDF, not something to invent |
| "the flat control stacks 3.86 layers" | wrong denominator — the plane spans the panel plus its margin, so 2.87 |
| "every spurious bounce halves the light" | written before testing; a ray probe built to show it scored the known-bad plate at 0.00 % |
| "the honeycomb's walls stack 4.4 deep over 85.9 % of the panel" | my plane key used abs() on the normal, merging four orientations; a canonical key gives 1.14, and the furnace gives 0.999776 |
| "nudging the honeycomb's sheets apart gains 8.85 %" | those faces were not coincident, so the nudge opened 0.01 mm slits and light leaked out |
| "the furnace re-run stopped partway" | it had finished; I read a log that was still being written |
| "the shallow-floor gate died" | same — it had its marker, and I spent 2 h 17 m re-running a job that was never dead |
| "the coating's diffuse fraction moves designs 41x, with rank inversion" (still live in NEXT.md and JOURNAL.md) | measured: 11.7 % at theta 0 and 34.4 % at -40 on the order spec, no inversion; CONTEXT.md had already withdrawn it and the other two were never updated |
| "the diffuse-fraction systematic is 15 % at 40 degrees" | 34.4 % |
| "resolving the honeycomb's wall will raise its 1.639 materially" (W4) | it reads 1.64314 at 4 px across the wall; the rejection was sound |
| "head-on falls as the panel grows at fixed density" (S3) | flat to 0.01-2.5 %; under-resolution is a bias, and a bias does not show up in a spread |
| "the honeycomb is worst hit by under-resolution" (S4) | it is the steadiest of the three; the 0.1 mm pyramid tip is the unstable one |
| "the sky-lit rho_dh does not describe a laser beam; re-measure with a beam" | rho_dh(theta) IS that fraction by definition, and the beam gate I wrote summed camera-direction radiance, not flux: the control's own material read 1.0019 but the same flat panel with gloss read 8.2448 |
| "the honeycomb flashes more than a plain wall because it adds cell walls" | the paints differed; gloss-free the comb reads 0.9999 against a flat wall's 1.0000 |
| "the gloss lobe retraces the tube, which is why the flash survives" | removing the gloss entirely leaves the flash unchanged; a peak is a radiance and a tube does not dim it |
| "the coating's diffuse fraction is 0.76" (phases 2-5, every published number) | never measured; DePoy et al. 2014 measure black paint at 0.97 and Filip & Vavra 2026 put Musou above ordinary matte, so 0.76 says Musou is glossier than black paint |
| "the head-on flash is 8x a plain wall" | that was the 0.76 coating. At the measured 0.97 it is 1.90 |
| "the pyramid beats the honeycomb" | at d=0.76 yes, at the measured d=0.97 the order reverses -- and all three sit within 2 %, so they are tied, not ranked |
| "there is no model check at all" | `weld_and_close` computes Euler and open edges, but only on Export STEP, so it never sees the measurement path |
| **"the specular roughness barely moves anything"** (in commit `409873e` and the `coating-diffuse-fraction` memory) | `form()` had no `roughness` parameter, so the sweep never varied it and every row rendered at 0.30. Wired through, the head-on flash moves **1160x** across 0.05-0.60 — the strongest knob in the model |
| "roughness 0.30 for black paint on aluminium" (every published flash number) | Filip & Vavra 2026 Fig. 6 measures 10-13 % of the acrylic paint's energy inside a 5 deg cone. No roughness reproduces that at df 0.97, and every (df, alpha) pair that does reproduce it has alpha in 0.01-0.11. Shirsekar 2019's Z302 BRDF agrees at ~0.06 |
| "DePoy 0.97 and Filip & Vavra disagree about black paint" | they do not — DePoy's photodiode subtends ~0.6 deg and catches the spike but not the shoulder, so their diffuse fraction is an upper bound. Both are satisfied near df 0.8, alpha 0.04 |
| every **head-on flash** number published in this project | 574x of spread inside the range the measurements allow, up to 600 963x against what we printed. The total and the smear are unaffected |

**The common cause of most of these: stating a hypothesis as a conclusion
before testing it.** The 2026-08-21 additions have a second cause worth naming
on its own: **reading an instrument before checking the instrument.** Three are
a detector that had never been run against a known answer, and two are a log
file read while it was still being written.

**The common cause of the first eight: stating a hypothesis as a conclusion
before testing it.** The pre-registered predictions at the top of each gate
script are what caught them; they are the reason the record can be audited.

---

## 9. Reproduce

    Blender --background --factory-startup --python scripts/rig_v2_gates.py
    Blender --background --factory-startup --python scripts/rig_v2_gates2.py
    Blender --background --factory-startup --python scripts/gate_render_vs_export.py

    # the furnace sweep must NOT be run as one process -- Cycles' Metal
    # shader cache double-frees on recompile and exits 0 mid-sweep. One
    # reading per process, retrying a point that produces no reading:
    for c in "bare 1 1.0" "bare 1 0.5" "bare 1 0.05" "flat 512 1.0" \
             "pyr 8 1.0" "pyr 32 1.0" "pyr 128 1.0" "pyr 512 1.0" "pyr 2048 1.0"; do
      Blender --background --factory-startup \
        --python scripts/gate_furnace_step.py -- ${=c}
    done
    Blender --background --factory-startup --python scripts/gate_displacement.py
    Blender --background --factory-startup --python scripts/gate_feature_px.py
    Blender --background --factory-startup --python scripts/sweep_standalone.py
    Blender --background --factory-startup --python scripts/redo_phase55.py
    python3 scripts/headon_raytrace.py

Every script carries its predictions in the docstring, written before the run.
Grade them against the output; where I was wrong the prediction is still there.

**Batch scripts must not call the simulator server.** Blender renders one frame
at a time, so a user pressing Render sits behind the batch and the button looks
dead. `sweep_standalone.py` shows the pattern: build through `rig_v2` in its own
Blender.
