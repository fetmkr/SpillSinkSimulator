# Phase 9.f — the walkable grate floor: better than every walkable alternative, but it misses its own bar

2026-08-17. Data: `sweep_phase9f.csv` (97 rows incl. the chained
grate40b). Predictions pre-registered in `scripts/sweep_phase9f.py`
and the chained script. Gate passed. Anchor 0.13392 % — book exact.

The venue photo's floor band needs a WALKABLE absorber. The candidate
(RF-anechoic precedent): a load-bearing grate over a pyramid pit.
Form/head-on was scoped OUT with reason: no audience sightline looks
straight down at a floor; the deployment axes are totals at standing-
viewer and beam angles (40–70°). The 9.2 area law already rules this
grate off WALLS (15 % flat bar land).

## Measured (worst over 3 mats; graze = −50/−60/−70)

| design | 5-angle worst | graze worst | vs flat Musou floor @70° (4.27 %) |
|---|---|---|---|
| pyramid floor alone (ref) | 0.1767 % | 0.1980 % | 21.6× better |
| grate 40 / wall 3 / deep 40 | 0.3761 % | 0.8017 % | 5.3× better |
| grate 25 / wall 3 / deep 40 | 0.5034 % | 1.4949 % | 2.9× better |
| grate 40 / wall 1.5 / deep 60 (chained) | 0.3181 % | 0.4891 % | 8.7× better |

## Grades

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 in-sweep floor ref = book (5θ + graze) | exact digits | 0.1767 / 0.1980 | HELD |
| P2 grate40 5θ | 0.30 ± 0.08 % | 0.3761 % | HELD at band edge |
| P3 grate40 graze | 0.30 ± 0.15 %, ≥2.5× vs flat | **0.8017 %** / 5.3× | MISS ×1.8 on the band; the ≥2.5× clause held |
| P4 finer grate worse | +10–40 % | +34 % (5θ) / +86 % (graze) | HELD on 5θ, over on graze |
| chained grate40b graze | 0.45 ± 0.15 % | 0.4891 % | HELD |

Ship rule (graze ≤ 0.45 AND 5θ ≤ 0.40): grate40 FAILS on graze;
grate40b passes 5θ (0.318) and misses graze by 9 % (0.489).
**Registered verdict: not shipped as specced.**

## What the miss taught, and the honest close

At grazing floor angles the beam hits the grate's VERTICAL bars nearly
face-on — the bars do to the floor what the louver did to the box
wall, softened by Musou. Thinner/deeper helps on a clean trend
(0.80 → 0.49 for wall 3→1.5, depth 40→60); extrapolating, wall ~1 mm
at depth ~80 would pass, but that is no longer a load-bearing grate
anyone stocks. The object stays the best WALKABLE floor measured —
2.9–8.7× better than an (unwalkable) flat Musou floor at 70° and ~10×
better than dark carpet (ρ 5 %) — so it remains available as a
CONDITIONAL option where the floor band must be treated and ~0.5 %
grazing is acceptable. The primary floor plan stays: clip the scan
content's lower bound, dark covering where feet go, pyramid tiles
where they don't.

## Rig note

The chained grate40b rows carry a drifted control (0.046 vs 0.05):
its taller stack's margin (2 × 60 top depth) overruns x = 180, into
the control zone at 160+. Panel absolute values are unaffected (the
panel window is far from the overrun); ratios from those rows must
not be used. Recorded here; the base sweep's margins stay clean.
