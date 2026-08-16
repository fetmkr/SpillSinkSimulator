# Phases 6.6–7.2 — manufacturing constraints measured, and the box reborn with textured walls

2026-08-16. Data: `sweep_phase66.csv`, `form_phase66.json` (incl. b75
re-checks), `sweep_phase7.csv` (incl. the textured surrogate), 
`form_phase7.json` (incl. wide-window b75 re-runs). Predictions
pre-registered in `scripts/sweep_phase66.py`, `sweep_phase7.py` and the
chained run scripts. NOTE: default probe beam changed to 7.5 mm this day
(user directive); every number below carries its beam width.

## 6.6 — the valley verdict (beam width labeled per row)

| final sample + | total | smear | head-on | span | beam |
|---|---|---|---|---|---|
| (base t0.1) | 0.17668 % | 4.258 / 1.42 / 1.09 | 0.0324 / 0.0400 | 1.47× | 2 / 7 / 10 mm |
| valley R0.1 | — | 4.259 | 0.0873 | 3.12× | 2 mm |
| valley R0.2 | — | 4.264 | 0.1088 | 3.52× | 2 mm |
| valley R0.3 | 0.18891 % | 4.369 | 0.1176 | 3.33× | 2 mm |
| valley R0.3 | — | 1.352 | **0.1866** | 1.00× | **7.5 mm** |
| valley R0.5 | 0.20054 % | 4.429 | 0.1259 | 2.65× | 2 mm |
| row offset 0.1 | 0.17661 % | 4.249 | 0.0324 | 1.47× | 2 mm |
| row offset 0.2 | 0.17645 % | 4.240 / 4.428* | 0.0324 / 0.0319* | 1.47 / 1.50×* | 2 mm (*true 8 mm period walk) |
| row offset 0.2 | — | 1.342 | 0.0401 | 1.02× | **7.5 mm** |

- **ANY measurable valley radius fails the head-on rule (≤0.041): even
  R0.1 reads 0.087 at beam 2 and R0.3 reads 0.187 at the deployment
  beam.** Valleys must be essentially sharp. Mechanism hypothesis
  [추측]: the concave trough acts as a cylindrical retro-concentrator;
  magnitude and span pattern support it, not yet isolated.
- **Row-strip assembly is free**: 0.2 mm steps move nothing on any axis
  at any beam width, including the honest full-period span re-check.

**Process verdict: standard injection is optically rejected (it cannot
hold sharp valleys). Viable paths: silicone-cast resin from a printed
master (sharp everything), or row-strip assembly with ground dies.**
[공정 일반론 부분은 추측 표시]

## 7.1–7.2 — the recessed box

| box (cell 110 / depth 220 over the final-sample floor) | total | smear | head-on | span | beam |
|---|---|---|---|---|---|
| plain Musou walls, flat 3 mm frames | 0.26745 % | 1.028 | 0.1678 | 3.41× | 7.5 mm |
| plain Musou walls, tapered frames | 0.21624 % | 4.608 | 0.0587 | 2.13× | 7.5 mm |
| **pyramid-textured walls (SURROGATE), tapered frames** | **0.04530 %** | not yet run | not yet run | — | (totals only) |
| reference: flat final sample | 0.17668 % | 1.42 / 1.09 | 0.0400 | — | 7 / 10 mm |

- Plain-wall boxes LOSE to the flat panel on totals (P1/P2 of 7.1 both
  wrong): at aspect 2 the box is just a big honeycomb, and its flat
  Musou walls hand back the oblique light. The measurement-window fix
  ("측정창 키워", adaptive z-inset in form_buildable) made the form
  numbers valid: flat frames glint 0.168; tapered frames smear well
  (4.61, the image dies in the box) with head-on 0.059.
- **The user's textured-wall idea flips the verdict: 0.0453 % —
  3.9× better than the flat panel, ~25× darker than a flat Musou wall.**
  SURROGATE caveat: walls modelled as flat surfaces with the panel's
  albedo (pure diffuse 0.21 %), not real pyramid geometry; redirection
  effects are not captured (real texture likely a bit better downward,
  possibly worse at grazing). Pre-registered rule (≤0.12 % earns real
  modelling) passed with margin.

## Next (named)

1. Real wall-pyramid geometry for the box (builder work) → confirm
   0.045 % and produce its smear/head-on at 7.5–10 mm beam.
2. Box form axes for the surrogate require paint-split support in
   `form_buildable.run_case` (totals path has it; form path does not).
3. The physical queue unchanged: coupon print, Musou coupon, beam spot.

## Phase 7.3 — the real 1 mm-sheet box: three wall textures, three failures, three laws

User constraint: box walls are single 1 mm sheet. Three fold textures were
built as real geometry (verified numerically + by preview) and measured.
All beam-width-7.5 numbers; cell 220, depth 240, final-sample floor.

| wall texture | total | smear | head-on | span | verdict |
|---|---|---|---|---|---|
| plain flat sheet (7.1, tapered rims) | 0.21624 % | 4.608 | 0.0587 | 2.13× | loses to panel |
| symmetric 45° zigzag folds | **1.17110 %** | 2.122 | 0.0473 | 2.84× | WORSE THAN A BARE FLAT PLATE |
| louver folds (45° down-faces) | **0.90503 %** | 1.432 | 0.1068 | 28.4× | rejected |
| vertical accordion folds | 0.17569 % | 3.014 | 0.0502 | 6.58× | ties the panel; worse span; rejected by the ≤0.12 rule |
| (reference: flat final sample) | 0.17668 % | 1.42/1.09 (beam 7/10) | 0.0400 | ~1.5× | the standing recommendation |

Predictions: 7.3 P1 wrong by 10× (0.08±0.04 → 1.171); 7.3b wrong
(0.10±0.06 → 0.905, head-on 2× over); 7.3c total at the top edge of a
wide low-confidence band, head-on 0.0002 over the rule.

**Three design laws, each bought by a measured failure:**
1. **Concave ~90° corners facing the beam are retroreflectors.** The
   zigzag's fold pairs sent light straight back (1.17 %); the same physics
   produced the valley-fillet head-on blow-up in 6.6.
2. **No face normal may point into the ±40° incidence cone.** The
   louver's 45° down-faces mirrored oblique beams back (0.905 %,
   span 28×).
3. **Absorbing texture needs near-vertical faces at fine pitch** — the
   pyramid's 5.7° flanks are the point. A 1 mm sheet cannot be folded
   into that (the accordion, the best legal fold, only TIES the flat
   panel while adding 24 cm of depth and a 6.6× scanning span).

**BOX PROGRAM CLOSED.** The only box that won (surrogate, 0.045 %)
required panel-grade wall texture, i.e. 22 mm-thick textured walls — 
excluded by the 1 mm constraint. With space behind the wall, the best
use of that space is DISTANCE (move the panel back), not boxes.
The flat final sample (pitch 4 / depth 20 / tip 0.1) stands as the
recommendation everywhere.

## Phase 7.4 — the box assembled from universal panels: the last box, rejected

The user's cladding architecture (every exposed face covered with the
pitch-4 universal tile) was built as real geometry: floor tile face-up,
walls of back-to-back tiles (tips into each cell), the 44 mm double-wall
rims capped with face-up tile strips. Cell 220, depth 240. Verified
numerically and by preview; measured at beam width 7.5 mm.

| | predicted | measured | grade |
|---|---|---|---|
| total worst-ρ | 0.10 ± 0.03 % | **0.19681 %** | WRONG, ~2× high |
| head-on | ≤ 0.045 | **0.09636** | WRONG, ~2× high |
| smear (beam 7.5) | ≥ 1.2 | 1.550 | held |
| span | — | 5.50× | periodic cell glint |

Worse than the flat panel (0.17668 / 0.0400) on BOTH deciding axes; the
adoption rule fails outright. The cavity gain the surrogate promised
(0.045 %) did not materialize in any real construction: five box
variants measured (plain, zigzag, louver, accordion, panel-clad), five
losses. Head-on mechanism unresolved [추측: the wall tiles' 5.7°
up-tilted faces plus cap/wall junction pockets; span 5.5× shows the
220 mm cell registration glinting] — but the measurement is decisive
and the box program is now closed with real geometry, not just with the
1 mm-sheet constraint.

**Standing verdict, final: the flat universal panel IS the product.**
Depth behind the wall buys more as plain distance than as any box.
