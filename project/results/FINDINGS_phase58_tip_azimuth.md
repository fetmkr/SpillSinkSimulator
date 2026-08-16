# Phase 5.8 — the die tolerance is settled, and the pyramid's crown is azimuth-conditioned

2026-08-16. Data: `sweep_phase58.csv` (70 rows) + `form_phase58.json` (4 full
form runs) + `sweep_phase58b.csv` (75) + `sweep_phase58c.csv` (63).
Predictions pre-registered in the three sweep scripts.

## Part 1 — tip tolerance: the number the toolmaker must hold

Full form protocol, p2/d18 unless noted (t0 and t0.1 from earlier phases):

| tip (mm) | flat frac | total (d00/d76) | smear | head-on | span@0 |
|---|---|---|---|---|---|
| 0.00 | 0 | 0.11387* | 4.104 | 0.02723 | 1.01× |
| 0.02 | 0.01 % | 0.11387 | 4.161 | 0.02823 | 1.06× |
| 0.05 | 0.06 % | 0.11447 | 4.269 | **0.03441** | 1.35× |
| 0.10 | 0.25 % | — | 4.484 | 0.05900 | 2.20× |
| 0.15 | 0.56 % | 0.11788 | 4.712 | 0.09627 | 2.20× |
| p5.5 t0.275 | 0.25 % | 0.11841 | 5.022 | 0.05525 | 4.09× |

\* t0.00 total shown is t0.02's (t0's d00/d76-only worst not re-run; its
3-mat worst is 0.13015 with d100@40 owning the envelope).

- **Spec rule (pre-registered): largest tip with head-on ≤ 1.5× sharp
  (≤ 0.041) → tip 0.05 mm passes (0.0344), 0.1 mm fails (0.0590).
  The p2 drawing carries: tip flat ≤ 0.05 mm.** (P5 HELD)
- Head-on is linear in flat fraction at fixed pitch (P2 HELD: three
  predictions inside bands). At fixed fraction, finer pitch pays more
  (P3 HELD: p5.5/f0.25 % = 0.0553, between p10's 0.0432 and p2's 0.0590).
- Interpolated 1.5× tolerances per pitch [추측, two-point linear]:
  p2 → 0.066 mm, p5.5 → 0.19 mm, p10 → 0.46 mm.
- Totals barely move (+3.5 % to t0.15); numeric bands of P1 were
  mis-anchored (predicted vs 3-mat envelope, swept 2 mats) — graded WRONG
  on my own terms, the physics claim held.
- Span/smear: span grows with tip but t0.15 undershot its band (2.20 vs
  2.5–4.5, P4 partial); smear IMPROVES with tip (4.10 → 4.71) — flats
  break up the coherent flank return; not predicted.

## Part 2 — the azimuth hole (found by P6 failing by 10× its band)

All pyramid numbers in Phases 4–5 are φ = 0. The brief says azimuth is
unknown. Measured, p2/d18 sharp, worst over mats × θ (control pinned at
0.05000 in every row; worst axis is pure-diffuse d100@±40 — geometry, not
shader):

| φ | 0° | 5° | 10° | 15° | 20° | 25° | 30° | 35° | 40° | 45° |
|---|---|---|---|---|---|---|---|---|---|---|
| worst % | 0.134 | 0.142 | 0.184 | 0.206 | 0.217 | 0.216 | **0.226** | 0.225 | 0.199 | 0.196 |

- **Worst-over-φ = 0.226 % at φ ≈ 30°, +74 % over the published φ-0
  number (0.22597/0.13015).** Broad plateau 20–35°. (5.8c P1 HELD: 0.215–0.235 band.)
- Scale-invariant: champion p5.5/d50 at φ45 = 0.19335 vs winner's 0.196
  (5.8b P1 HELD).
- The √2-depth fix is only half a fix: p2/d25.5 reads 0.109 at φ0 (aspect
  curve ✓) but 0.174 at φ45, not the predicted 0.134 (5.8b P2 WRONG) —
  the diagonal cut crosses saddle flats that aspect alone cannot remove.
- The worst azimuth is NOT the diagonal (5.8b P3 WRONG: φ22.5 > φ45).

## The verdict revision this forces

On the honest metric for an unknown-azimuth brief — worst over φ —
**the pyramid's total-axis lead evaporates: pyramid 0.226 % vs the
rotationally-symmetric cone's 0.2160 % (azimuth-invariant by symmetry,
measured spread 1.05×). The cone narrowly wins the total axis.**
(5.8c P3 HELD: within 10 %.)

What the pyramid still holds, φ-0-conditioned: head-on 0.0271 vs cone
0.0595 (2.2×), smear 4.10 vs 4.06 (tie). **Neither pyramid form axis has
been measured at φ30** — the form protocol runs at one azimuth. Buying or
refuting "pyramid keeps head-on at the worst azimuth" is the next
highest-value measurement, together with the cone's own three axes on the
modern (post-winding) harness at matched aspect.

Panel-thickness note: at equal worst-over-φ ≈ 0.22 %, the pyramid needs
18 mm and the cone family was measured at 50 mm depth — if the cone's
aspect law scales the same way, a thin cone field is the natural next
candidate (unmeasured).

## Prediction scorecard (9 graded)

5.8: P1 wrong-by-setup · P2 HELD · P3 HELD · P4 partial · P5 HELD ·
P6 WRONG (the finding). 5.8b: P1 HELD · P2 half · P3 WRONG.
5.8c: P1 HELD · P3 HELD.
