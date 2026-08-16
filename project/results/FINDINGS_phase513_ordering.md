# Phase 5.13 — the ordering package: four verified STLs, and the numbers a printed coupon must hit

2026-08-16. Data: `export/*.stl` + `export/finalists_manifest.json`,
`sweep_phase513.csv` (30 rows), `form_phase513.json`. Predictions
pre-registered in `scripts/sweep_phase513.py`.

## The files (export/, binary STL, built by the SAME build_mesh the sweeps ran)

| file | tris | as-built envelope (x×z×y mm) | volume | roundtrip | mesh |
|---|---|---|---|---|---|
| pyr_p2_d18_t005.stl | 6,942 | 68 × 68 × 20 | 36,647 mm³ | OK | clean |
| pyr_p4_d36_t010.stl | 2,172 | 76 × 76 × 38 | 80,336 mm³ | OK | clean |
| cone_p2_d18_r003.stl | 406,566 | 70.3 × 67.2 × 19.7 | 68,452 mm³ | OK | clean |
| cone_p4_d36_r006.stl | 118,278 | 80.1 × 74.4 × 37.9 | 149,358 mm³ | OK | clean |

- P1 (roundtrip identity) HELD ×4. P2 (kernel cleanliness) HELD ×4.
- The kernel emits QUAD faces; the writer fan-triangulates (first run
  crashed on the assumption of triangles — fixed, re-run, verified).
- **As-built ≠ nominal face**: the builder skirts the 60×60 face with one
  pitch of rim per side (pyr 1×: 68×68; 2×: 76×76) and jittered cones
  overhang by up to a base radius. THESE are the dimensions for a quote,
  not 60×60. Q12's failure mode (documented part ≠ built part) is why
  this table exists.

## The 2× print coupon and its pre-registered target

No printer holds a 0.05 mm tip at pitch 2; the aspect law is
scale-invariant, so `pyr_p4_d36_t010` prints the SAME optics with a
0.1 mm tip an SLA machine can approach.

Measured now (the target the physical coupon must hit):

| axis | simulated | pre-registered band | grade |
|---|---|---|---|
| total worst (3 mats × 5θ) | **0.12923 %** | 0.130 ± 8 % | P3 HELD (6th aspect-law confirmation) |
| head-on | **0.03247** | 0.035 ± 0.007 | P3 HELD |
| span@0 | 1.47× | ≤ 1.6× | P3 HELD |
| smear (2 mm probe) | **4.530** | 1.2–2.2 | **P4 WRONG, good direction** |

P4's miss matters: I predicted p4 falls in the p10-style smear cliff
(beam/pitch 0.5) — it does not. The cliff sits between pitch 5.5 and 10,
not at a beam/pitch ratio (which 5.5 P1 had already refuted; I reused the
dead model anyway). Corrected map: p2 4.10 · p4 4.53 · p5.5 4.16 ·
p10 1.27 at the 2 mm probe.

## Acceptance protocol for the physical coupon (fixed before the part exists)

Paint `pyr_p4_d36_t010` with the fitted Musou, measure ρ_dh at
θ 0/±20/±40:
- within **±25 %** of 0.129 % → simulator validated end-to-end (the
  coating fit's own residual is 9.5 %);
- outside **±40 %** → name the broken link (paint lobe? print fidelity?
  model?) before ANY 1 m² order. The roughness axis alone spans 3.9×
  (5.6), so an out-of-band result most likely measures the paint, not
  the geometry.

## Grading

P1 HELD ×4 · P2 HELD ×4 · P3 HELD (all three axes) · P4 WRONG (favourable;
mechanism named).
