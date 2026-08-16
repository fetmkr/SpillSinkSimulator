# Phase 9.v — the double-floor artifact never touched a published number

2026-08-17. Data: `sweep_phase9v.csv` (31 rows). Predictions
pre-registered in `scripts/sweep_phase9v.py`. Gate passed.

Trigger: the print-file audit found every floor-family mesh is composed
of overlapping solids with a coincident double face plane at y = −20
(field base + slab top) and T-vertex rims. Every published floor number
was rendered on such meshes. This run proves the artifact is optically
inert instead of assuming it.

| claim | prediction | measured | grade |
|---|---|---|---|
| P3 composed rerun reproduces the book | 0.17668 % exact (seed determinism) | 0.17668 % | HELD |
| P1 cleaned manifold solid, worst mats × 5θ | 0.17668 ± 2.5 % rel | 0.17667 % | HELD |
| P2 per-cell agreement, 15 cells | within ±3 % rel each | worst cell 0.01 % rel | HELD |
| anchor | 0.13392 % | 0.13392 % | exact |

Verdict: **the book stands.** The coincident interior plane is
unreachable by transport, exactly as geometry says; unlike the winding
defect of 2026-08-14 (49 % swing), this artifact has no optical
signature. The cleaned-solid builder (strip interior faces, 4 mm slab
grid, edge-propagated coherent winding) lives in `sweep_phase9v.py`
`clean_solid()` and is what the four repaired export STLs already use.

Scope: verified on the final sample (pyramid 4/20/0.1) over 3 mats ×
5 θ at 64 spp. Other floor kinds share the same composition scheme and
the same interior-plane argument; no re-sweep scheduled.
