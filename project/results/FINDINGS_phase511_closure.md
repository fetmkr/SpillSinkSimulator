# Phase 5.11 — the verdict's single-point assertions, bought; Phase 5 closes

2026-08-16. Data: `sweep_phase511.csv` (105 rows), `form_phase511.json`.
Predictions pre-registered in `scripts/sweep_phase511.py`. All six held.

## What was single-point, and what it measured

| assertion | prediction | measured | grade |
|---|---|---|---|
| thin cone (r0.03) azimuth immunity | 0.2122 ± 5 % at φ22.5/45 | 0.20715 / 0.21176 (spread 2.4 %; φ0 anchor re-read 0.21222 exactly) | HELD |
| thin cone seed robustness | ± 5 % at seeds 101/102 | 0.21656 / 0.21495 (≤ 2.0 %) | HELD |
| tip spec × azimuth, totals | t0.05 @ φ30 = 0.226 ± 0.010 | 0.22525 | HELD |
| tip spec × azimuth, head-on | 0.034 ± 0.008 | 0.02857 (below the φ0 t0.05 value — φ slightly de-registers the tip glint) | HELD |
| tip spec × azimuth, smear | 2.4 ± 0.5 | 2.498 | HELD |
| tip spec × azimuth, span | ≤ 2.0× | 1.01× (φ kills stripe/lattice registration, as predicted) | HELD |

## Phase 5 final state

**Recommendation stands, now with no single-point legs:**

- **Pyramid p2 / d18 / tip ≤ 0.05 mm, 20 mm panel.** Worst-over-azimuth
  total 0.226 % (tip included — no compounding), head-on ≤ 0.034 at every
  measured φ and beam width, span dead everywhere, aspect law valid
  p1–p10 (11 mm panel available at 0.022 mm tip tolerance).
- **Cone p2 / d18.2 / r0.03, 20.2 mm panel — equal-standing alternate.**
  0.207–0.217 % across azimuth AND seeds, head-on 0.0317, no azimuth
  caveat by construction. Choice between the two is tooling
  (≤0.05 mm square tip vs ≤0.03 mm tip radius) [모름 — toolmaker].

Conditional on (unchanged): coating roughness (3–12× multiplier vs flat,
one coupon fixes it), real beam width at the wall (form-axis verdicts),
one seed → n/a for the deterministic pyramid, 2.4 % φ/seed spread for the
cone. The remaining open items are physical, not simulated: coupon, beam
spot, tooling quotes.
