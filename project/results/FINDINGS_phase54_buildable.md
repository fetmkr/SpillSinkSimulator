# Phase 5.4 — the buildable pyramid: scale-up, tip truncation, and where scale invariance breaks

2026-08-15. Data: `sweep_phase54.csv` (105 rows), `form_phase54.json` (6 designs).
Predictions pre-registered in `scripts/sweep_phase54.py` (P1–P5) and
`scripts/sweep_phase54b.py` (P6) before any render.

## The question

The champion (pitch 5.5, depth 50, sharp) is a 9:1 needle no die can press and
no press can tip sharply. User asked: does pitch 10 / depth 90 work (aspect 9,
coarser tooling)? Does pitch 2 / depth 18 (thin panel)? How blunt may the tip
be? All three axes, always together (user rule, same day).

## Measurements (worst-ρ over d00/d76/d100 × 5θ; form protocol 16×512spp)

| design                | total %  | smear | head-on | span@0 |
|-----------------------|----------|-------|---------|--------|
| champion p5.5/d50     | 0.13392  | 4.159 | 0.02710 | 1.01×  |
| p10/d90 sharp         | 0.14322  | 1.272 | 0.02701 | 1.02×  |
| p10/d90 tip 0.5       | 0.14264  | 3.228 | 0.04323 | 4.25×  |
| p10/d90 tip 1.0       | 0.14829  | 3.266 | 0.07401 | 7.32×  |
| p10/d90 tip 2.0       | 0.17638  | 2.653 | 0.14846 | 12.94× |
| **p2/d18 sharp**      | **0.13015** | **4.104** | **0.02723** | **1.01×** |
| p2/d18 tip 0.1        | 0.12967  | 4.484 | 0.05900 | 2.20×  |

Anchor P5_j00 reproduced to six decimals in all four phase-5 CSVs.

## Three laws, now separated

1. **Total reflectance follows aspect (depth/pitch) alone.** All three
   aspect-9 scales sit within 10% (0.130–0.143%). Confirmed up (p10/d90)
   and down (p2/d18); the down direction came in slightly BELOW the
   prediction band — fine pitch keeps a small absolute-size edge.

2. **Form destruction does NOT scale.** The probe stripe is a fixed 2 mm
   (`form_buildable.STRIPE_W`). A 10 mm cell carries a 2 mm stripe on one
   flank nearly coherently: smear 1.272 vs champion 4.159. A 2 mm cell sits
   fully inside the stripe: smear 4.104. **The cell must be no coarser than
   the beam it is meant to shred.** Scale invariance is a total-axis law
   only — this is why the three axes must be read together; total alone
   would have called p10/d90 equivalent to the champion.

3. **The tip flat taxes the head-on axis, and revives the scanning glint.**
   Sharp fields are phase-uniform (span 1.01–1.02×). Any flat brings phase
   dependence back: span 4.25× at tip 0.5/p10, 12.94× at tip 2.0/p10.
   Head-on cost is NOT purely fraction-based across pitches: the same flat
   fraction 0.25% costs 0.0432 at p10 (tip 0.5) but 0.0590 at p2 (tip 0.1).

## Verdict

- **Winner: p2/d18 sharp** — equal-or-better than the champion on every
  axis with an 18 mm panel (20 mm with backing) — IF sub-0.1 mm tips can be
  formed at 2 mm pitch. The tip-0.1 row prices failure: head-on 2.2×.
- **Fallback: p10/d90 tip 0.5** — same total, easy tooling, but one third
  of the smear and a 4.25× phase span. Choose only if fine tooling is
  unavailable and form destruction can be compromised.
- p10/d90 sharp is strictly dominated (loses smear, gains nothing).

## Prediction grading (self-graded, honest)

- P1 scale invariance p10/d90 — **WRONG** (total ✓ 0.14322, head-on ✓
  0.02701, but smear 1.272 vs predicted 4.16±0.4).
- P2 total follows flat fraction — **HELD** (0.14264 / 0.14829 / 0.17638
  vs bands 0.145±0.007 / 0.153±0.008 / 0.181±0.012).
- P3 head-on follows flat fraction only — **WRONG twice**: t2.0 measured
  0.14846, 1% below the 0.15–0.25 band; and cross-pitch the same fraction
  costs differently (0.0432 vs 0.0590).
- P4 smear barely moves — **WRONG decisively** (1.27–3.27, none in band).
- P5 downward scale invariance (totals) — **WRONG in the good direction**
  (0.13015/0.12967 below the 0.143±0.007 band).
- P6 thin option smears like champion — **borderline/mixed**: smear 4.104
  (band said ≥4.2), head-on sharp ✓ 0.02723, head-on tip-0.1 ✗ 0.0590.

## Caveats

- The 2 mm stripe width is the protocol's model of the beam. If the real
  beam at the wall is much wider than 2 mm, law 2's threshold moves with
  it (pitch ≤ beam width, not pitch ≤ 2 mm). Worth one measurement of the
  actual beam footprint before committing to pitch 2.
- One seed, as everywhere in Phase 5.
- p2/d18 at 480×220 render puts ~7 px per cell in hemi_view; the mean is
  well-sampled but sub-cell detail is not. Form renders are higher-res.
