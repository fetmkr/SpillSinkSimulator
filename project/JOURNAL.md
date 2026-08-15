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
