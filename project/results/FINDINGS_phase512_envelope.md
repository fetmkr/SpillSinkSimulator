# Phase 5.12 — the pre-coupon worst envelope: the finalists are 1.4 % apart where it matters

2026-08-16. Data: `sweep_phase512.csv` (90 rows). Predictions pre-registered
in `scripts/sweep_phase512.py`. Anchors re-read exactly (P5_j00 0.13392,
cone r0.03 0.21222).

## The joint-unknown envelope (worst over 3 mats × 5θ)

The deployed panel faces two unknowns at once: paint lobe width (no coupon
yet) and beam azimuth (never controlled). Worst-over-(φ × roughness):

| | r 0.10 | r 0.30 | r 0.50 |
|---|---|---|---|
| pyramid p2/d18, worst-φ (φ30) | 0.22597 % | 0.22597 % | **0.38496 %** |
| cone p2/d18.2 r0.03 (φ-invariant) | 0.21222 % | 0.21222 % | **0.39029 %** |
| flat plate (roughness-invariant, 5.6) | 1.141 % | 1.141 % | 1.141 % |

- **Low roughness buys nothing on totals**: the roughness-invariant d100
  envelope owns both designs' floors (P1, P3 — both held to the digit).
- **High roughness costs both, nearly equally**: pyramid ×1.70 over its
  worst-φ floor, cone ×1.84 over its floor (P2 held; P4 missed low by
  0.015 — the φ30 d76 channel scales slightly less than φ0's did).
- **At the joint worst the finalists read 0.385 vs 0.390 — 1.4 % apart**
  (P5's 15 %-parity clause held; its "~2.3×" advantage guess was wrong —
  measured 2.9–3.0×).

## What this settles

1. The pre-coupon honest claim for EITHER finalist, worst-over-φ:
   **"3× to 5× darker than a flat Musou wall; which end depends on the
   paint's lobe width, which one 도장 쿠폰 measurement fixes."**
   (1.141/0.390 = 2.9× at r0.50; 1.141/0.212 = 5.4× at r≤0.30. The
   5.6 figure of up to 11.6× survives only if the azimuth happens to be
   aligned — it is a φ0 number, not a claimable one.)
2. The finalist choice cannot be made on optics — 1.4 % at the joint
   worst, within noise. It is a tooling decision (0.05 mm square tip vs
   0.03 mm tip radius), exactly as 5.10 concluded, now robust to both
   unknowns.
3. Smooth paint's real payoff is not totals (d100 floor) but **head-on**
   (0.0089 at r0.10 vs 0.0665 at r0.50, from 5.6) — the axis that
   survives beam width and azimuth. If the paint can be chosen, choose
   smooth; the reason is the glint, not the integral.

## Grading

P1 HELD (exact) · P2 HELD · P3 HELD (exact) · P4 MISS by 0.015 under the
band · P5 half (parity clause held, advantage figure wrong).

Phase 5 measurement campaign ends here. Every remaining question needs an
object, not a render: painted coupon, beam spot, tooling quotes.
