# Phase 5.7 — Phase 5 is not face-biased, and the 0.647 % "flat" was never flat

2026-08-16. Data: `sweep_phase57.csv` (70 rows). Predictions pre-registered in
`scripts/sweep_phase57.py`.

## Why this outranked every design question

5.6 left an unexplained anomaly: a floor-family "flat" (tip_flat = pitch)
read 0.647 % against a closed-form 1.0 %. Every Phase 5 total was measured on
the floor family at face 60; if that deficit was a face-60 window artifact,
the whole phase carried an unknown bias.

## Measurements (worst over mats × 5θ unless noted)

| design | face 60 | face 100 | shift |
|---|---|---|---|
| champion p5.5/d50 | 0.13392 % | 0.13032 % | −2.7 % |
| winner p2/d18     | 0.13015 % | 0.12998 % | −0.1 % |
| truncated field tip 1.9 (d76) | 0.69960 % | — | |
| truncated field tip 2.0 (d76) | 0.69960 % | 0.69956 % | −0.0 % |
| ridge flat (d76)  | 0.83275 % | 1.03046 % | the known face-60 defect |

## Findings

1. **Phase 5 stands.** The champion and the winner are face-invariant
   (−2.7 % and −0.1 %, both inside the pre-registered bands). The face-60
   defect is confined to margin-less flat slabs; structured floor-family
   designs with real margins do not share it. (P1, P2 — HELD.)
2. **The anomaly was a wrong premise, not a wrong measurement.**
   `geom_floor.py:135` clamps the tip flat: `min(tip_flat, pitch * 0.8)`.
   "tip_flat = pitch" and 1.9 both build the SAME mesh — flats 1.6 mm wide
   separated by 0.4 mm-wide, 3.6 mm-deep V-grooves (aspect 9 at
   micro-scale). That field reading 0.70 % where a true flat reads 1.03 %
   is physics, not artifact: grooves occupying 20 % of the surface remove
   32 % of the return. The identical values at tip 1.9 / 2.0 / face 100
   were the clamp's fingerprint. (P3 — WRONG as stated: "the anomaly is a
   face artifact" was refuted; the resolution is better than the
   prediction.)
3. Ridge-flat rows reproduce the 5.6 probes in CSV form: θ0 0.79277 % at
   face 60, 0.99637 % at face 100. (P4 — HELD.) Rule confirmed: **flat or
   near-flat references are measured at face ≥ 100**; the face-60 flat
   deficit remains un-isolated (documented, contained, not explained).
4. Incidental but real: a groove field that is 80 % flat area still cuts
   the d76 total by a third. Consistent with the exposed-flat-area law
   operating on the remaining 80 %, plus aspect-9 grooves absorbing what
   falls in.

## Status of QUESTIONS/threats after this turn

- Phase 5 verdicts: intact, now face-validated.
- 5.6's "open anomaly": CLOSED (clamp + real groove absorption).
- Still open: why a margin-less 60 mm slab reads low in the panel window
  (contained by the face-100 rule); the physical coupon; the beam spot.
