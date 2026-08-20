# Working journal — 2026-08-12 → 13

Kept because the session can die and the reasoning is worth more than the
numbers. Newest at the bottom. `results/*.md` hold the finished findings; this
holds how they were arrived at, including the wrong turns.

---

## The through-line of the last two days

**The same error class has now appeared three times, and each time it put an
unmanufacturable feature at the top of a ranking.**

1. **The 8x tip mismatch.** The 2026-08-12 report claimed shingle beat cone by
   29%. The shingle used a 0.05 mm plate edge, the cone a 0.4 mm tip. Matched at
   0.4 mm the cone wins and seven of nine families sit inside 1.11x. The report
   was published before this was checked. `results/PEER_REVIEW.md` found it.
   **CONTEXT.md:503 records the project catching the identical error once
   before, in the "fair fight", and I had read and summarised that section
   earlier the same session.**

2. **The feature axis was still wrong.** Fixing (1) by holding minimum feature
   common assumed a common process. Aluminium honeycomb is a bought commodity
   with 0.03-0.1 mm foil; a cone is moulded or printed at 0.4 mm. Comparing them
   at a "matched" 0.4 mm penalises the honeycomb for a constraint it does not
   have. Hence `sweep_buildable.py`, where each family sits at what its own
   process delivers.

3. **CELLNEST, 2026-08-13.** The current darkness leader is a nested cell at
   **wall 0.1 mm, 50 mm deep, 11 mm cell** — the wall is 1:500 thickness to
   height. It is labelled `process = print` and **cannot be FDM printed**
   (0.4 mm nozzle floor), is not expanded foil (that is a regular hexagon, not
   an irregular Voronoi with a floor lattice), and has no demonstrated sheet
   route. `sweep_buildable.py`'s docstring says "0.1 mm walls, optimistic for
   FDM, kept for comparison" — but the ranking output does not carry that
   caveat, so it reads as the winner. **Seen by rendering it
   (profiles/097) and looking, not from the numbers.**

**The pattern:** an optimiser will always walk to the edge of whatever box it is
given, and the box is set by parameters chosen for convenience. Every ranking in
this project has to state the process and the minimum feature next to the
number, or it ranks the box rather than the design.

---

## What was settled, with the measurement that settled it

| claim | number | how |
|---|---|---|
| structure vs flat, same coating, same footing | **~30x** (6.1218% -> 0.2041%) | flat plate measured over the same 5 thetas and 3 materials |
| between the nine topologies, each at its own process | **1.6x** | `sweep_buildable.csv` |
| coating diffuse fraction | **41x**, rank inversion | metrics/01 |
| coating specular roughness, on theta=0 form peak | **332x** (0.10 -> 0.50) | `FINDINGS_form_baseline.md` |

An earlier framing of mine — "coating beats geometry" — conflated the first two
rows. The user caught it. **Correct statement: having a structure is decisive
(30x); which structure is nearly irrelevant (1.6x); and two unmeasured coating
parameters sit above both.**

## Things that turned out to be non-problems

- **margin_depths 6.5.** Carried a note "margin 1.0 moves head-on by -15%,
  reason not understood". `test_margin.py` swept 1.0-6.5 on a wall network and a
  pillar array: flat within 3.5%, i.e. inside the realisation noise. The -15%
  does not reproduce at theta <= 40 and was almost certainly measured with
  grazing angles in the set. Margin is now 2.0, which is what made 0.86 mm cells
  computable (14.2 M faces -> 1.9 M).
- **The theta=0 form peak > 1.** Not the lamp (visible_camera on/off identical
  to six decimals), not `recentre` (raw and recentred agree to four decimals).
  It is the coating: a flat plate of the same coating reads 1.64 where the
  structured panel reads 1.34. The baseline was wrong, not the measurement.

## Things that are still wrong or unfinished

- `form_roughness` was added to `run_queue.sh` while the queue was RUNNING, and
  zsh had already parsed the loop body, so it silently did not run. A restart is
  armed for when `sweep_seeds` finishes. **Edit the queue only when it is idle.**
- The flat control plate sits inside the panel field (`GAP` 100 mm vs a field
  reaching 160 mm at margin 2.0). Absolute rho_dh is unaffected — measured — but
  every ratio against the control is. Not yet fixed.
- Honeycomb is 4th on darkness and LAST on form: smear 0.96x, i.e. **narrower
  than a flat wall**, MTF 0.970. Vertical-walled cells trap light but do not
  move it sideways, so the line comes back where it went in. Shingle is the only
  design in the top 3 of both.
- No experiment. Nothing here has been built or measured. Kaster 2025 (JAP 138
  174904, Carl Zeiss AG) is the same: simulation only, and it reports 0.65x
  average reduction where we report ~0.03x. **That gap has to be explained
  before any comparison is published.**

## Supervision, and why it is on disk

Two failures drove this:
- sweep_topo finished at 00:34 and nothing started the next job for **eight
  hours**, because the only thing that ever started a job was a chat turn.
- A watchdog *agent* was tried and terminated after four minutes while
  reporting it was "standing by". An agent lives inside a session.

So: `run_queue.sh` (job loop, survives a crashing job) + `keepalive.sh`
(restarts the queue, flags a 45-minute output stall). Both on disk, both
stoppable with `touch logs/STOP`.

---

## 2026-08-20 — the renderer was never the bottleneck

Asked whether results are being rendered with full acceleration. Measured
rather than assumed, on the M1 Pro under Blender 4.3.2 at 480x220:

| variant | 5 angles x 512 spp |
|---|---|
| **Metal GPU, MetalRT AUTO — what we already do** | **10.06 s** |
| MetalRT forced ON | 10.86 s |
| Metal GPU + CPU together | 21.83 s |
| CPU only | 28.21 s |
| Blender 5.1.2 (installed, unused) | 10.20 s |

So Cycles is fine. Four things worth writing down:

- **MetalRT AUTO is correct here.** An M1 Pro has no ray-tracing cores, so AUTO
  resolves to off. Forcing it on costs 8% and a 51 s one-time kernel compile.
- **The CPU+GPU comment in `configure_cycles` was right.** It said hybrid
  "costs more than it adds" without a number; it is 2.2x slower, and the number
  is now in the comment.
- **128 bounces is free.** At 32 bounces rho is identical to seven digits and no
  faster: at rho 0.005 the rays die long before the cap. The correctness setting
  costs nothing, which is worth knowing before anyone is tempted to lower it.
- **Blender 5.1.2 is not an upgrade.** Same speed, and it moves rho by ~0.12%.
  Staying on 4.3.2 costs nothing and avoids a lock re-freeze.

**The defect this turned up.** `configure_cycles` set `cy.device = "GPU"`
whether or not the device loop had enabled anything. Cycles does not refuse
that — it falls back to the CPU silently, and `report_cycles_settings` went on
printing `device=GPU`. Reproduced: 6.09 s against 2.0 s for the same frame,
with nothing in the log to say why. A sweep could have run 3x slow for hours
while its own log said GPU. It now raises unless `ALLOW_CPU=1`, and the results
JSON carries a `renderer` block naming the device that actually rendered it.

**What was actually slow was the pipeline around the render.** An interactive
Measure at the 64-spp default is 1.30 s wall of which 0.56 s is the render; the
rest is Blender starting and exiting, paid per click. And sweeps ran one process
at a time, so the single-threaded Python geometry build — 2.6 s for the
1.1 M-vertex cone — always had the GPU idle beside it.

Hence `sweep_shard.py`: the same sweep split over two Blender processes, each
building while the other renders, merged back into the canonical CSV afterwards
so nothing downstream learns that sharding exists. Measured end-to-end on
`sweep_fab`, 720 rows regenerated from nothing: **557 s serial, 411 s sharded,
1.36x**. Sharded and serial re-runs agree to 0.0018%, which is the GPU's own
run-to-run spread. With `NSHARD` unset every function in the module is a no-op
and an unsharded run is byte-identical — verified against the committed CSV.

The persistent-worker half landed too, once `sim_server.py` went quiet:
`cyc_worker.py --serve` reads one JSON request per line, `sim_server` keeps one
warm and serialises on `RENDER_LOCK`, which had been defined and unused. An
interactive Measure at the 64-sample default went **1.30 s to 0.6-0.75 s**.
One-shot mode is kept and both modes agree to 0.0015%, inside the GPU's own
spread, so the process boundary moved and nothing else did.

Two things measured rather than assumed while building it. A malformed request
returns an error and the worker survives -- verified, because the whole value
of the mode is the startup it has already paid. And the idle worker costs
**33 MB**, not the ~1.4 GB this journal nearly claimed: the "Mem:1345M" Cycles
prints is the DEVICE allocation during a render and it is released afterwards.
RSS sawtooths 110-250 MB across 30 consecutive 3-angle measurements with
persistent data on, with no monotonic growth.

**Two things found on the way that are not mine to fix:**

- `lock.py -- check` is red before any of this, and has been: `flat_coating`
  reads control 0.041786 against a 0.05 nominal at all three angles, tripping
  `CONTROL_TOL`. Confirmed identical on pristine a0cb21a. Another session traced
  it to `CASES["flat_coating"]` using a degenerate ridge (pitch_mean 50, depth
  0.001) whose two periods do not cover the measurement window, so the plate
  reads dark by exactly its coverage shortfall — 0.8357 here, 0.7485 in their
  case. It is the window, not the coating.
- **The committed sweep CSVs no longer reproduce.** Re-measuring all 720 rows of
  `sweep_fab.csv` against today's code gives a median drift of 1.20% and a worst
  of 8.75% on `d00` (pure specular), against 0.28% median on `d100` (pure
  Lambertian). The gradient with diffuse fraction points at the material-model
  work, not at geometry. The original file was restored untouched; nobody has
  re-frozen anything.
