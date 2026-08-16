# Phase 6.5 — the final sample owns its own worst cases

2026-08-16. Data: `sweep_phase65.csv` (50 rows), `form_phase65.json`,
`form_p4d20_beam.json`, plus the tip ladder in `sweep_phase515.csv` /
`form_phase515.json`. Predictions pre-registered in `scripts/sweep_phase65.py`
and the two chained run scripts.

## The design: pyramid pitch 4 / depth 20 / tip 0.1 (files: pyr_p4_d20_t010_*)

### Totals (worst over stated mats × 5θ)

| condition | measured | prediction | grade |
|---|---|---|---|
| φ0, roughness 0.30, 3 mats | 0.17668 % (d100@40-owned) | — | base |
| **φ30 (worst azimuth), measured directly** | **0.25109 %** | 0.2486 ± 0.010 | P1 HELD |
| roughness 0.10 (d00+d76) | 0.13519 % → 3-mat envelope stays 0.17668 (d100 floor) | 0.177 ± 0.010 | P2a HELD |
| roughness 0.50 (d00+d76) | **0.44356 %** (×2.51 over base) | 0.48 ± 0.12 | P2b HELD |

### Form (all beam widths labeled)

| condition | smear | head-on | span | grade |
|---|---|---|---|---|
| beam 2 mm, φ0 | 4.258 | 0.03243 | 1.47× | base |
| beam 2 mm, φ30 | 3.241 | 0.02961 | 1.03× | P3: head-on HELD, smear 0.04 above band |
| **beam 7 mm** (deployment low) | 1.417 | 0.04000 | — | in band |
| **beam 10 mm** (deployment high) | 1.094 | 0.04038 | — | in band |

### Tip ladder (beam 2 mm; drawing rule)

| tip | total | smear | head-on | span |
|---|---|---|---|---|
| 0.1 | 0.17668 % | 4.258 | 0.03243 | 1.47× |
| 0.2 | 0.17635 % | 4.471 | 0.05158 | 2.89× |
| 0.4 | 0.17821 % | 4.868 | 0.10664 | 6.72× |

Drawing tolerance by the pre-registered 1.5× rule: **tip ≤ 0.15 mm**
(0.1 good / 0.2 borderline / 0.4 rejected — and 0.4 revives the scanning
wobble at 6.7×).

## What this closes

Every number the recommendation stands on is now the design's own
measurement: worst azimuth 0.251 %, paint-roughness envelope 0.177–0.444 %
(one coupon collapses it), deployment-beam form 1.1–1.4 with head-on
≈ 0.040, tip tolerance 0.15 mm. Nothing is borrowed from p2 or from sharp
tips anymore.

## Open (named, not hidden)

- **Valley radius**: injection rules demand ~R0.3–0.5 valleys; the pyramid
  builder has no valley-round parameter yet. Next simulator task: add it,
  measure R0.3/R0.5. If the cost is small the injection drawing is
  complete; if large, the build leans hot-press/casting.
- Physical: coupon print (files ready, incl. the t0.4 comparison pair),
  Musou coupon, beam spot confirmation.

## Phase 6.7 addendum — grazing angles 50-70° (beam widths labeled)

| θ | final sample (worst mats) | flat plate | advantage |
|---|---|---|---|
| 50° | 0.18413 % | 1.43894 % | 7.8× |
| 60° | 0.19210 % | 2.22578 % | 11.6× |
| 70° | 0.19805 % | 4.26796 % | 21.6× |

- P1 (smooth degradation, 0.30/0.45/0.75 bands): the pyramid did BETTER
  than every band — it barely degrades at all (0.184→0.198). The miss is
  in the good direction by 2-4×; the cells keep trapping at grazing while
  the flat plate's Fresnel blows up.
- P2 (advantage ≥2.5× everywhere): held with huge margin — **the harder
  the wall is grazed, the bigger the pyramid's advantage** (22× at 70°).
- P3 (φ30 at θ50 within ×1.5): 0.29523 = ×1.60, just over the band. The
  azimuth hole persists at grazing. **0.295 % is the honest
  worst-over-everything total** (θ≤70 × φ × roughness 0.30).
- P4 (smear ±50 within ±30 % of ±40): held — 1.214 vs 1.417 at beam
  7.5 mm; head-on 0.04009 unchanged.

Consequence: no edge treatment, no placement rule — ONE panel type covers
the entire wall including corners the projector grazes at 70°.
