# Phase 6.1 — the coarse tier: aspect rules the pyramids, backing exposure breaks the combs, and the top-layer law has a limit

2026-08-16. Data: `sweep_phase6.csv` (150 rows), `form_phase6.json` (3 form
runs). Predictions pre-registered in `scripts/sweep_phase6.py`.
User-directed phase: pitch ≥ 10 pyramids, large-cell honeycombs, stacks.

## Totals (worst over 3 mats × 5θ, φ0)

| design | aspect | measured | prediction | grade |
|---|---|---|---|---|
| pyramid p10/d50 | 5.0 | 0.19420 % | 0.194 ± 0.012 | HELD — **exact repeat of the 08-15 API value** |
| pyramid p15/d50 | 3.3 | 0.23574 % | 0.240 ± 0.015 | HELD |
| pyramid p20/d50 | 2.5 | 0.24605 % | 0.260 ± 0.020 | HELD (low edge) |
| pyramid p10/d90 | 9.0 | 0.14322 % | 0.143 ± 0.006 | HELD — exact repeat of P54 |
| comb cell 9.5 / d50 | 5.3 | 0.24649 % | 0.24 ± 0.03 | HELD |
| comb cell 12.7 / d50 | 3.9 | 0.32713 % | 0.27 ± 0.04 | **WRONG, worse** |
| comb cell 19 / d50 | 2.6 | 0.44377 % | 0.32 ± 0.06 | **WRONG, much worse** |
| stack: comb 12.7 (35) + pyr floor (15) | — | **0.21184 %** | comb-alone ± 10 % | **WRONG — 35 % BETTER than comb alone** |
| stack: comb 19 (35) + pyr floor (15) | — | 0.22452 % | comb-alone ± 10 % | WRONG — 49 % better |

## Form (2 mm probe)

| design | smear | head-on | span | grade |
|---|---|---|---|---|
| pyramid p10/d50 sharp | 1.293 | **0.02698** | 1.03× | P4 HELD — sharp tips head-on-proof at aspect 5 too |
| comb 12.7 alone | 1.293 | **1.63312** | 1.01× | P4 HELD dead-centre — the naked comb's backing reads like a flat plate (Phase 2's 1.637, reproduced) |
| comb 12.7 + pyramid floor | 1.033 | 0.08526 | 1.75× | P4 HELD (wall-top scaling: predicted 0.075 ± 0.025) |

## Three findings

1. **The aspect curve owns pyramids at every scale** — 8th and 9th
   confirmations, two of them exact reproductions of values measured by
   different code paths (API, sweep_phase54).
2. **Big honeycomb decays FASTER than its aspect** (P2 wrong in the bad
   direction). Mechanism: below aspect ~4 the flat backing becomes
   directly visible through the cells at working angles — the comb stops
   being a wall of traps and becomes a perforated flat plate. Naked big
   honeycomb is not a usable design.
3. **The "top layer owns the result" law has a limit, and Phase 6 found
   it** (P3 wrong in the good direction). At cell 12.7/19 the floor is
   visible through the comb, so the floor matters again: the stack reads
   35–49 % better than its comb alone. **comb 12.7 + pressed floor =
   0.21184 % — statistically tied with the cone finalist (0.212) on
   azimuth-flat totals, from an off-the-shelf top layer.** Its ceiling
   is unchanged though: head-on 0.085 (3.1× the pyramid class) is the
   comb's wall tops, and no floor removes those.

## Standings after Phase 6.1

The coarse tier adds one interesting design (big-cell stack, azimuth-flat
0.212, bad head-on) and one clean commodity option (pyramid p10/d50:
0.194 φ0 / head-on 0.027 / tip tolerance ~0.5 mm). The finalists are
unthreatened on head-on; the stack matches them on totals only.
Open in Phase 6: stack worst-φ verification (hex should be flat — 5.15
measured 0.0 % at cell 5.2; assumed to carry, unmeasured at 12.7),
coarse-pyramid φ30, and whether a cheap floor under the STOCK big comb
the user can buy today beats ordering custom tooling at all.

## Phase 6.3 — the cell-matched 45° floor (user-suggested)

comb c10/d30 over a MATCHED p10/d10 floor: 0.22291 % (φ30: 0.21925, flat),
form smear 1.080 / head-on 0.10527 / span 1.41×. The fine p2 floor under
the same comb reads the identical worst (0.22291 %) — per-row values
differ, but the worst-case envelope is set at grazing incidence where
light never reaches ANY floor through a 30 mm-deep cell-10 comb. Verdict:
under a deep comb the floor can be as cheap as vacuum-formed 45°
pyramids (P1 held at band edge; P2 "fine floor wins by 5–20 %" WRONG at
the envelope — instructive); comb-top head-on unchanged (P4 held).

## Phase 6.4 — knife-edged comb tops (user-suggested)

Tapering the stack's walls 0.08 → 0.01 mm at the top (all Musou-coated
as always):

| stack comb12.7 + fine floor | total | smear | head-on | span |
|---|---|---|---|---|
| blunt tops (0.08) | 0.21184 % | 1.033 | 0.08526 | 1.75× |
| knife tops (0.01) | 0.20050 % | 4.031 | 0.06186 | 1.49× |

- ALL three axes improved — smear 4× (the top glints had been narrowing
  the return; with them gone the floor's wide smudge shows), total −5 %,
  head-on −27 %.
- But P1 (head-on linear in top area → 0.034±0.010) is WRONG: measured
  0.0619. Only ~40 % of the comb's head-on is top area; the rest is WALL
  GLINT — near-normal light grazing the near-vertical cell walls, where
  Fresnel reflectance rises regardless of coating. No edge treatment
  removes that; it is the geometry of vertical walls.
- Net: a sharpened bought comb + floor reads 0.201 % / 4.03 / 0.0619 —
  a genuinely decent all-rounder, still 2.3× the pyramid class on
  head-on. P2 borderline (−5.4 % vs ±5 % band), P3 wrong in the good
  direction on smear.
