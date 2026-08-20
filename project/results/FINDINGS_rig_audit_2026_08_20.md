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

**The common cause of the first eight: stating a hypothesis as a conclusion
before testing it.** The pre-registered predictions at the top of each gate
script are what caught them; they are the reason the record can be audited.

---

## 9. Reproduce

    Blender --background --factory-startup --python scripts/rig_v2_gates.py
    Blender --background --factory-startup --python scripts/rig_v2_gates2.py
    Blender --background --factory-startup --python scripts/gate_furnace.py
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
