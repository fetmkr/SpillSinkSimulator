# NEXT — what to do when the overnight queue lands

Written 2026-08-13 ~00:15. Delete this file once the report is out.

**Promised deliverable:** two rankings (darkness, form) + 3D images of each +
comparison report, in **`report/2026-08-13/`**. The user asked for it explicitly
and asked twice not to let it drop.

## Wait for these to be true

| file | condition |
|---|---|
| `results/sweep_buildable.csv` | ~11,700 rows (180 designs x 12 seeds x 5 thetas x 3 materials) |
| `results/form_buildable.json` | 11 cases — **already done** |
| `results/form_roughness.json` | 20 records (5 roughness x [1 flat + 3 designs]) |

`logs/queue.log` shows START/END per job. `logs/keepalive.log` shows restarts
and any STALL.

## Then, in order

1. **Darkness ranking, WITH ERROR BARS.** Group `sweep_buildable.csv` by tag
   ignoring seed; report mean +/- SEM over the 12 seeds. **The single-seed
   ranking put the top 13 designs inside 1.09x against a realisation spread of
   ~3.5%, so most of that order was noise.** Collapse everything inside the
   error into one equivalence class and say so, rather than printing an order
   that cannot be defended.

2. **Re-normalise the form numbers** against the flat plate of the same
   coating, from `form_roughness.json` at roughness 0.30. `metrics/04` uses the
   0.05 matte wall, which is not the baseline `metrics/01` mandates, and against
   the right one the theta=0 result inverts from "worse than plain black paint"
   (1.34) to "better than its own coating" (0.81). See
   `results/FINDINGS_form_baseline.md`.

3. **Form ranking** from `form_buildable.json`. Use rms smear (metric 02, no
   known defect) as the headline and peak ratio (metric 04) beside it. MTF
   (metric 07) is supporting only — it discards phase and under-reports
   azimuthal spreading, which is the 3D families' whole mechanism.
   **theta = 0 only after step 2.**

4. **Roughness sensitivity** from `form_roughness.json` — this is probably the
   report's most important figure. 332x across 0.10-0.50 against 1.6x for the
   entire nine-topology search.

5. **3D renders**: `scripts/report_top10.py` pattern, but driven from
   `results/form_candidates.json` so the same 11 designs appear in both
   rankings. Remember `margin_depths` 0.2 for pictures, and say in the caption
   that no optical number comes from those renders.

6. **Report** to `report/2026-08-13/`, then publish as an Artifact.

## The report is already built and dry-run. Two commands.

    Blender --background --factory-startup --python scripts/report_buildable.py
    python3 scripts/build_report_2rank.py 2026-08-13

Machinery, all three stages exercised on partial data 2026-08-13 00:5x:

| script | does | verified |
|---|---|---|
| `analyze_buildable.py` | both rankings, mean +/- SEM over seeds, **process floor check** | yes |
| `report_buildable.py` | 11 renders + `report/<date>/data.json` | yes, 11/11 |
| `build_report_2rank.py` + `report_2rank_template.html` | self-contained HTML | yes, 1.9 MB, no unresolved fields |

The 11 renders are already in `report/2026-08-13/shots/` and are reused, so a
rebuild is fast. `webify()` makes the web JPEGs once.

**Ordering trap, already handled but know about it:** `data.json` snapshots the
roughness records that existed when `report_buildable.py` ran. If that is before
`form_roughness` finishes, the 332x figure vanishes from the page. The builder
now re-reads `results/form_roughness.json` directly and **prints a WARN if there
are none** — do not ignore that line.

Dry run on partial data (6 seeds) gave, darkness rank -> form rank:

     1 -> 6   CELLNEST        cannot be made (0.1 mm wall, print)
     2 -> 1   SHIN_t02_az180  sheet, lanced   <- only design high on BOTH
     3 -> 9   CELLSQUA        cannot be made
     4 -> 11  HONE_p5.2       bought foil     <- darkest bought, WORST on form
     6 -> 2   CONE_p5.5       moulded
    11 -> 4   SLNT_ln30       bought foil

Six of eleven cross by four places or more. That crossing is the report's
subject, not a footnote.

## Numbers that must appear, and must not be misstated

- **structure vs flat, same coating, same footing: 6.1218% -> 0.2028%, i.e.
  ~30x.** Geometry is decisive. An earlier framing of mine said "coating beats
  geometry" and conflated this with the next line; the user caught it.
- **between the nine topologies at their own realistic process: 1.6x.** Which
  topology you pick is nearly irrelevant.
- **coating diffuse fraction: measured directly 2026-08-21, sweeping 0.50-1.00
  with the geometry held fixed.** Order spec pyramid p4/d22 moves **11.7 % at
  theta 0 and 34.4 % at theta -40**, and the two move in OPPOSITE directions
  (head-on falls as the fraction rises, -40 climbs). A flat plate under the same
  sweep moves 0.2 % and 6.9 %, so **the lever is the geometry, not the coating**.
  No rank inversion between flat and pyramid anywhere in the range — the
  earlier "41x, with rank inversion" was withdrawn in CONTEXT.md and should not
  have survived here. `scripts/gate_diffuse_fraction.py`.
- **coating specular roughness: 332x on the theta=0 form peak.**
- Honeycomb is 5th on darkness and LAST on form (smear 0.96x — narrower than a
  flat wall). Vertical-walled cells trap light but do not move it sideways.
- Shingle is the only design in the top 3 of both, and it is sheet metal
  (laser-cut, lanced, bent, spot-welded), not printed.

## Carry the caveats into the report, do not bury them

- `results/PEER_REVIEW.md` — verdict is reject-as-is, and the fatal objection
  was a feature-size confound that inverted the headline. That is why
  `sweep_buildable` exists.
- `results/FINDINGS_control_overlap.md` — the flat control sits inside the panel
  field; absolute rho_dh is unaffected (measured), ratios against the control
  are not.
- Kaster 2025 (JAP 138 174904, Carl Zeiss AG) is direct prior art, simulation-
  only, and reports 0.65x average where we report ~0.03x. That gap needs
  explaining before any comparison is published.
- US 11,209,577 B2 (Ocean Insight) claims slanted mm-scale macro structures,
  periodic and irregular, hexagonal/triangular/square/conical. The geometry
  space is not open.
