# Phase 5.14 — the cone coupon's targets, and the rim verified harmless

2026-08-16. Data: `sweep_phase514.csv` (30 rows), `form_phase514.json`.
Predictions pre-registered in `scripts/sweep_phase514.py`.

## Rim verification (numeric, no render — refuted a protocol breaker)

The coupon rim discovered in 5.13 could have broken the acceptance
protocol if it were a flat skirt at the entrance plane (the lab measures
the whole part; the simulated target excludes the rim). Numeric
inspection of `pyr_p4_d36_t010`: flat area at y=0 is **3.6 mm² on a
5776 mm² part** — all of it tip flats — and rim vertices span the full
depth (0 / −36 / −38). **The rim is one extra ring of full-depth cells,
same texture as the field. Lab and simulation see the same thing;
the acceptance bands stand.**

## The 2× cone coupon target (export/cone_p4_d36_r006.stl)

| axis | simulated target | prediction | grade |
|---|---|---|---|
| total worst (3 mats × 5θ) | **0.21617 %** | 0.212 ± 8 % | P1 HELD — cone scale invariance, 2nd confirmation |
| head-on | **0.03491** | 0.0317 ± 0.006 | P2 HELD — the (r/pitch)² law crosses scale on cones |
| span@0 | 1.32× | ≤ 1.3× | P3 miss by 0.02 |
| smear (2 mm probe) | **3.681** | 3.5 ± 1.0 | P4 HELD |

Acceptance for the printed cone coupon (same rule as the pyramid's):
painted with the fitted Musou, θ 0/±20/±40 — within ±25 % of 0.216 %
validates; beyond ±40 % stop and name the broken link.

## Ordering package, now complete

Both coupons carry pre-registered targets; both spec parts carry verified
STLs and as-built dimensions. Nothing else in this project requires a
render. The queue is physical: paint coupon (roughness), beam spot
(footprint), print/quote both coupons, measure against the tables above.
