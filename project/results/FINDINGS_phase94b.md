# Phase 9.4b — tilting the fibers does not rescue flock; the door is closed

2026-08-17. Data: `sweep_phase94b.csv` (16 rows), `form_phase94b.json`.
Predictions pre-registered in `scripts/sweep_phase94b.py` (the lean-30
θ0 cell was a marked postdiction from a 32-spp preview). Gate passed.
Anchor P5_j00 d100@−40 = 0.13392 % — equals the book.

9.4 rejected vertical-pillar flock (head-on 1.0004 = a flat plate) but
named one unmodeled rescue: real fibers tilt and entangle, hiding the
floor. `pillar_lean` now shears each fiber in a seeded random azimuth;
the render shows a genuine thatch with no floor visible. Measured:

## Grades

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 totals worsen with lean: 15° → 1.9±0.3 / 30° → 2.1±0.4 / 45° → 2.4±0.5 % | as stated | **1.827 / 2.129 / 2.499 %** | HELD, all three |
| (lean-30 θ0 postdiction 1.96 %) | — | 1.969 % | consistent |
| P2 head-on at lean 30 (beam 7.5 mm) | 0.35 ± 0.15 | **0.634** | MISS HIGH — tilt helps even less than the cosine model allowed |
| (smear, beam 7.5 mm) | recorded | 1.096 | — |

## The verdict, now measured from both sides

Hiding the floor traded "a flat floor stares back" (1.0004) for
"tilted Lambertian faces glow at the camera" (0.634) — a factor 1.6,
where the replacement rule needs a factor 9 (≤ 0.11). Totals moved the
wrong way at every lean (leaning sides catch more sky and face the
camera more), exactly as registered. **Within any Lambertian model,
flocking fails the bare-cast-tier replacement rule at every measured
geometry: vertical, and tilted 15/30/45°.** The simulation side of
this question is closed.

What could still revive the material is physics a Lambertian model
cannot carry: specular fiber sides channeling light downward, and
sub-beam self-shadowing at real 0.1 mm fiber scale. Both are exactly
what the few-thousand-won flocking-paper coupon measures with the
modulated-beam protocol. Until that coupon reports, the two-tier cast
plan stands with no flock tier.

## Cross-checks

- Vertical fill-25 baseline (9.4): 1.758 % / head-on 1.0004 — the lean
  series brackets it from above on totals, below on head-on, both
  monotonic in lean. No inversion anywhere.
- The pyramid tiers stand untouched: bare 0.907 / 0.107, Musou
  0.177 / 0.040 (its form row at beam 7 mm).
