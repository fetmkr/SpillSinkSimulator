# FINDINGS — Kaster reconciliation: his 0.65x is mostly his planar cap

2026-08-17 · `scripts/sweep_kaster.py` → `results/sweep_kaster.csv` (33 rows)
· figure `results/fig_kaster.png` · closes QUESTIONS.md **Q19-4**
· gate: PASSED (8 checks; the anchor pairs with `sweep_floor.csv` as a
documented epoch deviation — see §5, `results/anchor_deviations.json`)

## 1. What was done

QUESTIONS.md Q19-4: the closest prior art — Kaster 2025, *Macroscopic
structural light absorbers* (arXiv:2507.05152, J. Appl. Phys. 138 174904) —
had been cited from its abstract only, and `reference/SUMMARY.md` §4 flags
the 3x gap between his published "average intensity ratio < 0.65" and our
~0.19x same-coating claim as *"the single number a referee will attack
first."* The PDF (12 pp.) has now been read in full, and the decisive
difference was reproduced in our own harness.

What the paper actually says:

- **Material** [p.7]: reflectance 5 % (absorbance 95 %), split 85 %
  Lambertian + 15 % Gaussian lobe (FWHM 25°), one material for specimen and
  planar reference. An empirical stand-in for black anodised aluminium.
- **Geometry** [p.2, p.7]: Gyroid (period 5 mm), Schwarz D (6.25 mm), and a
  strut lattice (2.85 mm), all at volumetric density 30.6 %, min feature
  0.5 mm, 40 mm discs. And the sentence the abstract never mentions:
  *"To mitigate direct wide-angular backscatter from curved structures, we
  generate a planar cap layer"* — the specimen's top face is a plane cut
  through a 30.6 %-dense solid, so **~30.6 % of his frontal area is flat
  land** at the entrance plane.
- **Results** [p.3, Table 1]: avg intensity ratio specimen/planar
  0.544–0.701 over AOI {0, 37.5, 75} x {XZ, YZ}; peak ratio 0.259–0.613.
- **Method** [p.7–8]: ANSYS SpaceClaim geometry + ANSYS SPEOS non-sequential
  forward tracing [p.11, refs 27–28], 1e8 rays per scan, energy weighting,
  hemispherical far-field intensity receiver at 1° resolution; the ratio is
  a mean over receiver cells. Simulation only, no fabricated sample [p.6].

Our tip law says flat land at the entrance plane returns like a flat plate,
in proportion to its area. His cap **is** 30.6 % flat land. So the
hypothesis, pre-registered in the sweep docstring: the gap between his
0.65x and our 0.19x is his cap, not our physics.

## 2. The analog, in one harness

Three specimens, all rendered under HIS material — `coating_split(0.85,
rho0=0.05)`: body 0.0425 Lambertian + glossy scaled to make rho_dh(0) = 5 %
— at his AOI set {0, −37.5, −75}, glossy roughness bracketed {0.30, 0.15}
to stand in for his 25°-FWHM Gaussian:

| specimen | flat land at entrance | stands in for |
|---|---|---|
| flat plate (phase 6.7 rig) | 100 % | his planar reference |
| our pyramid p4/d20/tip 0.1 | (0.1/4)² = 0.06 % | the product |
| **cap analog** p4/d20/tip 2.2127 | (2.2127/4)² = **30.6 %** | his cap plane |

Pyramidal pits stand in for gyroid channels: both are deep absorbing
cavities behind the same flat entrance fraction. `[추측]` The channels'
tortuosity is NOT reproduced — see §4 for where that shows up.

## 3. Results against the pre-registered predictions

rho_dh in % (Cycles, 64 spp, seed 0), ratio = specimen/flat at the same
angle and roughness:

| θ | flat r.30 | ours r.30 (ratio) | cap31 r.30 (ratio) | ours r.15 (ratio) | cap31 r.15 (ratio) |
|---|---|---|---|---|---|
| 0 | 4.968 | 0.491 (**0.099**) | 1.711 (**0.344**) | 0.408 (0.082) | 1.657 (0.334) |
| −37.5 | 5.044 | 0.794 (**0.157**) | 2.004 (**0.397**) | 0.738 (0.146) | 1.970 (0.391) |
| −75 | 8.792 | 1.016 (**0.116**) | 3.381 (**0.385**) | 0.874 (0.099) | 3.319 (0.377) |

Kaster's published avg-intensity ratios at the same AOI: 0.54–0.58 (0°),
0.54–0.60 (37.5°), 0.60–0.70 (75°) [p.3, Table 1].

Prediction scorecard, honestly:

- **P1 HIT.** Flat plate reads the material: 4.968 % at 0° (model says
  5.000, −0.6 %), 5.044 at −37.5 (band 5.0–5.5), 8.79 at −75 (band 6.5–9;
  the rise is our Fresnel-weighted glossy — his material has no angle
  dependence, a recorded definitional difference).
- **P2 PARTIAL.** Predicted ours/flat 0.13–0.25 at 0°: measured 0.099/0.082
  — **better than predicted, outside the band low**. −37.5 (0.157/0.146)
  in band; −75 well under the 0.35 ceiling.
- **P3 PARTIAL — the direction confirmed, the magnitude under-shot.**
  Predicted cap31 0.40–0.50 at 0° and ≥0.50 at −75; measured 0.33–0.40
  at every angle. The cap lifts the ratio **3.4–4.1x above our pyramid at
  the same material and angles** — but stops 1.4–1.8x short of Kaster's
  published band.
- **P4 PARTIAL.** Flat and cap31 move ≤3 % relative between roughness 0.30
  and 0.15; our pyramid's 0° cell moves 19 % (band was ±15 %) — the
  smallest number is lobe-sensitive; every conclusion above survives both
  roughness settings.

## 4. What this settles, and what remains

**Settled.** At one material and one metric, walking the flat entrance
fraction from 0.06 % to his 30.6 % moves the specimen/flat ratio from
0.08–0.17 to 0.33–0.40 — i.e. **most of the log-distance from our claim
(0.19x worst-case) to his (0.65x) is his own planar cap**, exactly what the
tip law predicts (`results/fig_kaster.png`: at his land fraction, half the
drawn rays leave after ONE bounce off the cap; at ours, none do). His
design choice was deliberate — the cap suppresses wide-angle backscatter
from curved struts [p.2] and his Fig. 2 confirms enhanced backscatter is
where his structures pay — but it puts a hard floor under his ratios:
`ratio ≥ land + (1−land)·(pit return)`. The SUMMARY.md §4 sentence "we
claim ~3.7x more improvement than the published state of the art" can stop
being a discrepancy: the two results measure differently-capped structures,
and the uncapped one wins for a reason the harness reproduces.

**Remaining, recorded as open** `[추측]`: the residual 1.4–1.8x between our
cap analog (0.33–0.40) and his band (0.54–0.70) has three candidate
sources, none reproduced here: (a) his ratio is a mean over receiver CELLS
of an intensity map, not an energy ratio — his own Table 2 shows ~1 %
relative standard error on maxima, but the cell-mean statistic weights
directions, not energy; (b) gyroid channels are tortuous and re-convergent
where our pits are straight — a channel that turns returns more of what
enters it; (c) his material reflects 5 % at every angle while our glossy
share is Fresnel-weighted (visible in the flat row rising to 8.8 % at
−75). Naming which needs his raw receiver maps, which are available only
on request [p.9].

**Mechanism note.** The paper's stated mechanism is "increasing the number
of reflections" [abstract]. The figure shows what the harness measures:
the cap fraction returns in ONE bounce and dominates his floor; the number
of reflections only governs the pit fraction. This is the same
single-bounce-dominates accounting our `ray_census.py` measured
(CONTEXT.md 2026-08-11), now visible inside the closest prior art.

**Axes.** This sweep compares the 반사 총량 axis only: Kaster's paper has no
smear or head-on axis to compare against (his receiver maps are the nearest
thing to a smear statement, and only ratios were published). 모양 뭉개기 /
정면 반짝임: 측정 무효 — 비교 상대가 논문에 없음. Our product's own three
axes are unchanged in the book: 0.177 % / 1.42 / 0.040.

## 5. Defects found and handled on the way

- **Margin overrun, caught by the control (first run VOIDED →
  `results/__void__sweep_kaster_margin65.csv`).** margin_depths 6.5 at
  depth 20 runs the field to x = 198, under the control window starting at
  x = 172; cap31's 30.6 % flat tips are coplanar with the control plate at
  y = 0 and the coincident faces read −4.5 % control drift at 0/−37.5. Our
  pyramid has the same overrun but 0.06 % tip area — its drift hid at
  −0.01 %, which is why no earlier sweep ever tripped it. Re-ran at
  margin_depths 4.5 (90 mm still covers the −75° shadow, 20·tan 75° = 75 mm;
  field ends at x = 158): control back to 0.0500 exactly, panel values
  unchanged to 6 digits — the panel window was never contaminated.
- **The anchor that would not bit-match.** `KA_anchor_s23` re-measures
  `FL_p650f080_flat_d00_s23` (comb 6.5/0.08, depth 50) cell-for-cell, and
  came out 5.5e-4 relative away from `sweep_floor.csv`. Investigated to the
  end: NOT the orient_outward winding fix (replaying with the pre-fix
  `geom_topo` gives today's value, not the book's), NOT the harness diff
  (the full 80d8945 module set gives today's value), NOT the environment
  (Blender app and macOS unchanged since 05-19/08-10, no reboot since
  08-10, and the pyramid anchor P5_j00 d100@−40 still reproduces
  0.0013391865650191903 **bit-exact**). Remaining cause: sweep_floor.csv
  was measured 08-14/15 by a pre-commit harness state git does not
  preserve — geom_topo and friends were born inside that commit's work.
  Consequence: **no current sweep can bit-match any pre-80d8945 comb-family
  row**; the deviation is bounded at 5.5e-4 relative, 10x below the ±0.5 %
  seed noise (phase 9.s). Recorded in `results/anchor_deviations.json`;
  gate check 8 now passes a mismatching pair ONLY when it is named there
  and inside its recorded bound — silent drift still fails.
- **Figure sampling alias (drawn, then caught by looking).** The first
  fig_kaster aimed rays at span·(k+0.5)/9, which landed rays 1, 4, 7
  exactly on the three tip centres — a 0.06 % land drawn as a 33 % land.
  And its first trace had a sign error that let rays sail through the
  solid. Both fixed; the shipped figure's rays reflect off the same closed
  loop that is drawn, at true angles.

## 6. Cross-checks against existing measurements

- Flat plate at Musou coating (gate check 1's own rig) unaffected — this
  sweep's flat used the same phase 6.7 rig at a different material.
- K_ours worst over his angle set, d85/rho 5 %: 1.016 % ≈ 0.203 x rho —
  read against the bare-black law total = 0.18 x rho (measured at d100):
  same first digit, the +13 % being the d85 glossy share at −75 that the
  d100 law never sees. Consistent, not identical, for a recorded reason.
- Anchor: 15/15 cells against `sweep_floor.csv` within 5.5e-4 relative
  (documented epoch deviation, §5); pyramid book anchor bit-exact.
