# Phase 9.1 — the two answers that price 100 m² of panel

2026-08-16. Data: `sweep_phase9.csv` (75 rows), `form_phase9.json`.
Predictions pre-registered in `scripts/sweep_phase9.py`. Trigger: the
user needs ~100 units of 1 m². Questions: (a) does an extruded groove
survive its azimuth hole (unlocks endless rolls), (b) does bare black
urethane (no Musou) land in a usable class (unlocks skip-paint zones).

Anchor: P5_j00 worst 0.13392 % — equals the book value to all digits.

## Grades

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 groove φ0 total | 0.19 ± 0.05 % | **0.33457 %** | **MISS ×1.8** |
| P2 groove azimuth bounded ≤ 0.30 % | ≤ 0.30 | φ15 0.330 / φ30 0.314 / φ45 0.284 / φ60 0.238 / φ75 0.170 / φ90 0.173 | marginal MISS (worst is φ0 itself) |
| P3 bare ρ0.04 / 0.05 / 0.08 total | 0.72 / 0.90±0.30 / 1.44, ±35 % | **0.721 / 0.907 / 1.478 %** | HELD, dead center |
| P4 bare form (beam 7.5 mm) | head-on < 0.5; smear ≥ 1.2 | head-on 0.107; smear 1.383 | HELD |
| P5 groove form φ0 (beam 7.5 mm) | head-on 0.040 ± 0.020 | **0.894** | **MISS ×22 — the finding** |
| P5 groove smear φ0 | 1.42 ± 0.40 | 1.081 | edge of band |
| (φ90 form, unpredicted) | — | smear 1.547, head-on 0.0696 | recorded |

## Two new design laws (each bought by a miss)

1. **A tip LINE is 40× worse than a tip POINT.** The pyramid's head-on
   law is quadratic in tip/pitch because its flat is a point:
   (0.1/4)² = 0.06 % of area. A groove's tip land is a LINE:
   0.1/4 = 2.5 % of area — the same 0.1 mm tip costs 40× more flat
   land, and head-on measured exactly that class: 0.894 vs 0.040.
   Extrusion dies also wear tips round first. **Any extruded profile
   pays head-on linearly in tip/pitch; molded pyramids pay
   quadratically.** This is the deep reason the pyramid wins.
2. **A 2D trench loses ~2× to a 3D cell on diffuse light.** Groove φ0
   total 0.335 % vs pyramid 0.177 %, dominated by d100 (Lambertian):
   diffuse bounces escape along the trench's open axis, which the
   pyramid's fourth pair of walls closes. The grooves' azimuth
   behaviour inverts the pyramid's: grooves are WORST at φ0
   (0.335 %) and best at φ90 (0.173 %), monotonic between.

## Bare black pyramid: the 0.18 rule, confirmed and cross-checked

ρ_eff / ρ_material = 0.180–0.185 across ρ 0.04–0.08 (linear, as
predicted). Cross-check against the book: the Musou coating's own
normal-incidence return is ~1 %, and 0.18 × 1 % = 0.18 % ≈ the
measured Musou pyramid total 0.177 % — the same escape factor
explains both. One number now predicts any coating on this geometry:
**total ≈ 0.18 × ρ_coating; head-on ≈ 0.107 at ρ 0.05 (beam 7.5 mm).**

## Decision table (all three axes, beam widths labeled)

| candidate | 반사 총량 worst | 모양 뭉개기 smear (beam 7.5 mm) | 정면 반짝임 head-on (beam 7.5 mm) | verdict for 100 m² |
|---|---|---|---|---|
| cast pyramid + Musou | 0.177 % (φ0) / 0.295 % (all-worst) | 1.42 | 0.040 | audience-critical zones |
| cast pyramid, bare black ρ0.05 | 0.907 % | 1.383 | 0.107 | non-critical zones, paint skipped |
| extruded groove + Musou, best orientation (φ90) | 0.173 % | 1.547 | 0.0696 | conditional only |
| extruded groove + Musou, worst orientation (φ0) | 0.335 % | 1.081 | **0.894** | fails head-on 22× |

Registered decision rules, applied: extrusion needed P2 AND φ90
head-on ≤ 0.08 — P2 broke marginally and the orientation spread is
×13 on head-on, so **extrusion unlocks only for zones where the beam
plane is known and the grooves can be laid along it; it cannot be the
default panel.** Bare-black needed ≤ 1.2 % — held with margin, so
**skip-Musou zones are now a design option**: same mold, no paint,
5× the total of the painted panel but still 10× below any flat wall
on head-on.

## Scale math for 100 × 1 m² (computed, not quoted)

- Solid cast urethane at 4/20/0.1 + 2 mm backing: 8.67 L/m² →
  ~870 L ≈ ~0.9 t total; 9.1 kg per panel. Foamed PU (anechoic-
  industry style, density 0.06–0.10) cuts both ~10×: ~0.6–1 kg/panel.
- Paint area: slant faces multiply surface ×10.05 → 100 m² of wall is
  ~1,000 m² of painted surface. Priced (user 2026-08-17: Musou Black
  30,000 KRW / 100 ml): at assumed 3–6 m²/L effective coverage
  [coverage assumed — coupon pins it], full coverage costs
  **50M–100M KRW in paint alone**; painting only the critical
  10–20 % cuts it to 5–20M. On bare zones a cheap matte black
  (ρ 4–5 %) adds nothing over the bare urethane (0.18 × ρ), so the
  rational choice there is no paint at all.
- Mold count: silicone molds live ~30–50 casts → 3–4 molds for 100
  panels; master (the asset) is one metal or SLA positive per size.

## Scope notes

- Groove φ-scan ran at θ −40 only (registered scope); the full-θ
  azimuth surface is bounded by the φ0/φ90 5θ runs on either end.
- Bare-material bracket assumes Lambertian ρ 0.04–0.08 for black
  urethane/TPU [assumption registered; a coupon pins the point].
- Form control for the bare rows is the same-ρ flat plate (the
  cross-check convention), so its ratios are material-matched.
