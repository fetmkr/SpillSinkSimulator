# Phase 6.2 — the coarse tier at the worst azimuth, and form at the real beam

2026-08-16. Data: `sweep_phase62.csv` (60 rows), `form_phase6_beam9.json`
(3 runs at stripe 9 mm), `form_phase6.json` (now 8 entries — every Phase 6
design carries all three axes, per the user's standing rule).

## Worst-azimuth totals (φ30, worst over 3 mats × 5θ)

| design | φ0 | φ30 | ratio | prediction | grade |
|---|---|---|---|---|---|
| comb 12.7 + pressed floor | 0.21184 % | 0.21689 % | ×1.024 | ≤ 5 % shift | P1 HELD — the big stack is azimuth-flat |
| pyramid p10/d50 (aspect 5) | 0.19420 % | 0.25198 % | ×1.298 | 0.274 ± 0.025 | P2 HELD (band edge) — the φ hole is mostly an aspect property |
| pyramid p15/d50 (aspect 3.3) | 0.23574 % | 0.27641 % | ×1.172 | ×1.15–1.40 | P3 HELD — shallower slopes, smaller hole |

The φ-hole ratio now maps cleanly by aspect: 9 → ×1.74, 5 → ×1.30–1.41,
3.3 → ×1.17. Hex stacks and cones sit at ×1.0.

## Form destruction at the real beam (stripe 9 mm ≈ LaserCube at 5 m)

| design | smear (beam 9) | return width vs flat | head-on |
|---|---|---|---|
| pyramid p2/d18 | 1.119 | 12 % wider | 0.02731 |
| pyramid p10/d50 | **0.675** | **30 % NARROWER — form-preserving, the one real hazard** | 0.02735 |
| comb 12.7 + floor | 0.981 | equal | 0.10414 |

At the real beam nobody meaningfully widens the return; the axis's job in
deployment is avoiding designs that NARROW it (pitch ≥ 10 pyramids act as
mirror flanks). Head-on remains the discriminating axis at every beam
width and azimuth measured: pyramid class 0.027, comb-topped class 0.10.

## Coarse-tier verdict (three axes, worst-φ, real beam)

| design | 반사 총량 (worst-φ) | 모양 뭉개기 (beam 9) | 정면 반짝임 |
|---|---|---|---|
| comb 12.7 + floor | 0.217 % | 0.98 | 0.104 |
| pyramid p10/d50 | 0.252 % | 0.68 | 0.027 |
| pyramid p15/d50 | 0.276 % | — (not run at 9 mm) | 0.030 |
| (fine-tier reference: pyramid p2/d18) | 0.226 % | 1.12 | 0.027 |

The coarse tier offers no all-axis winner: the big stack ties the fine
tier on totals and azimuth but glints 3.8× head-on; the coarse pyramids
keep the pyramid head-on but preserve beam form and pay the φ hole.
The fine-tier finalists and the p4/d20 easy pyramid remain the
recommendations; the big stack is the "buy it this week" fallback when
head-on can be tolerated.

Grading: P1, P2, P3 all HELD (P2 at its band edge — the hole has a mild
pitch dependence the aspect-only model underestimates by ~8 %).

## Addendum — why the coarse pyramid narrows the return (user challenged it; first explanation refuted by measurement)

The user objected: a pyramid beating a FLAT at form preservation seems
wrong. First hypothesis (specular flank mirrors) was killed by its own
test: a PURE MATTE big pyramid still reads smear 0.660 (2.34 mm return vs
the flat's 3.40) — no specular component needed.

The real mechanism is SHADOWING: a matte flat glows across the whole
oblique footprint (~12 mm at 40°), but a 10 mm-pitch field puts the beam
into one or two grooves where only the beam-facing flank strips light up —
and those lit strips are narrower than the footprint. Fine pitch has
dozens of strips per beam width, which merge into a wide smudge; coarse
pitch leaves one thin bright line. The effect is real, matte-robust, and
bad for this project's threat model (the observer sees a sharper stripe
than a bare matte wall would give). Verified 2026-08-16, run
`B9L_pyr_p10d50`.
