# Phase 5.6 — the winner is hostage to an unmeasured coating parameter, by a factor of 3.9

2026-08-16. Data: `sweep_phase56.csv` (130 rows), `form_phase56.json`.
Predictions pre-registered in `scripts/sweep_phase56.py` (P1–P5).

## Why

QUESTIONS.md Q6: `spec_roughness = 0.30` is pinned in every configuration and
has never been measured on the physical paint. Phase 5 crowned p2/d18 at that
one point. This sweep buys (or refuses to buy) the claim across 0.10–0.50,
on the winner and on the flat-plate denominator, before anything is ordered.

## Measurements (worst over θ 0/±20/±40, d00+d76; form at protocol beam 2 mm)

| roughness | p2/d18 total | flat total | advantage | p2 head-on | p2 smear |
|-----------|--------------|------------|-----------|------------|----------|
| 0.10      | 0.09866 %    | 1.14105 %  | 11.6×     | 0.00892    | 4.157 |
| 0.20      | 0.10340 %    | 1.14135 %  | 11.0×     | —          | — |
| 0.30      | 0.13015 %    | 1.14119 %  | 8.8×      | 0.02723*   | 4.104* |
| 0.40      | 0.23080 %    | 1.14179 %  | 4.9×      | —          | — |
| 0.50      | 0.38433 %    | 1.14145 %  | 3.0×      | 0.06654    | 4.050 |

\* 0.30 row from `form_phase54.json` (identical design, same protocol).
d100 self-test: 0.13015 % at r 0.10 and r 0.50, identical to 5 decimals.

## Findings

1. **The flat plate's total is roughness-invariant** (1.14105–1.14179 %,
   spread 0.06 %) and sits exactly on the historical 1.1413 % — ρ_dh
   integrates the hemisphere; roughness only redistributes within it. Q6's
   332× is a peak-axis effect and never contaminated the total axis.
2. **The winner's total swings 3.9×** across the same range: rough paint
   diffuses the first bounce back out of the cavity instead of chaining it
   down. Smooth paint helps (0.099 % at 0.10); rough paint costs
   (0.384 % at 0.50). Direction: monotonic, knee above 0.30.
3. **Every "N× darker than flat" claim is therefore conditional on the
   paint's actual lobe width: N ∈ [3.0, 11.6].** The pyramid beats the flat
   wall at every roughness — the DESIGN choice is robust — but the marketing
   number is not. Measuring the real paint's roughness (or one coupon) is
   now the highest-value physical measurement, ahead of even the beam spot.
4. Form axes are calm: smear 4.05–4.16 at the extremes (geometry, not lobe
   width, fans the stripe); head-on falls to 0.0089 at 0.10 (specular chains
   dive deeper) and rises to 0.0665 at 0.50 — still 25× under what flat does
   at LOW roughness (119.92 peak, form_roughness.json), because the pyramid
   presents no upward-facing mirror.

## Prediction grading

- P1 flat invariant at 1.141 ± 0.11 — **HELD** (dead center, after the
  measurement-frame fix below).
- P2 winner within ±25 % and ≥6× advantage everywhere — **WRONG** (0.231
  and 0.384 far outside; advantage 3.0× at 0.50).
- P3 d100 self-test within 2 % — **HELD** (identical to 5 decimals).
- P4 head-on within 0.014–0.060 at extremes — **WRONG twice, both
  boundary** (0.0089 good side, 0.0665 high side); the "no spike" claim it
  encoded is nevertheless true.
- P5 smear within 2× of 4.10 — **HELD**.

## Measurement-infrastructure defect found and contained mid-run

The first run measured the flat slab at face 60 and read 0.958 % — 21 % low.
Isolation (probes A–K, /tmp/flat_probe*.py): the degenerate slab has
margin_depths × 0.001 mm ≈ NO margin, and hemi_view's panel window reads a
margin-less 60 mm panel 21 % low; at face 100 and 200 the same call reads
0.99832 / 0.99839 %, equal to `fit_coating.py`'s validated construction
(which always used FACE = 100). The sweep now measures the flat at face 100
(ρ_dh is intensive; comparability with face-60 pyramids is unaffected — the
structured designs all carry real margins of 2×depth). Blast radius: the
first run's flat rows only, superseded in place. Had it stood, it would have
flattered the winner by 21 %.

**Open anomaly — RESOLVED in Phase 5.7** (`FINDINGS_phase57_faceinvariance.md`):
the "fully truncated" field was never flat. `geom_floor` clamps tip_flat at
0.8 × pitch, so the mesh carries 0.4 mm-wide, 3.6 mm-deep grooves whose
absorption is real. Wrong premise, not wrong measurement; the flat reference
rule (ridge construction, face ≥ 100) stands.

## Consequence for the build

Unchanged winner, changed sales pitch: p2/d18 sharp, 20 mm panel. Quote
"3–12× darker than a flat Musou wall, pending paint measurement", not "9×".
If the paint can be CHOSEN, choose the smoothest black available: within
this model, roughness 0.10 nearly halves the winner's return AND its
head-on. [추측: real paints tie roughness to ρ0; the two knobs may not be
independent on a shelf.]
