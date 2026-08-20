# Phase 5.5 — the probe beam width was an assumption; sweeping it changes the story's shape but not its verdict

> ## VERDICT WITHDRAWN 2026-08-20 — THE TABLE BELOW IS CLIPPED
>
> Every smear in this file was measured on a 60 mm panel, whose measurement
> window was 24 mm. `rms_width` normalises by the energy INSIDE the window, so
> light past the edge leaves numerator and denominator alike and the reading
> collapses onto the core instead of merely shrinking. Re-measured with the
> window opened until it converges, off the same designs and beams:
>
> | design | beam | published here | converged | ratio |
> |---|---|---|---|---|
> | p02/d18 | 2 | 4.104 | 5.226 | 1.27x |
> | p02/d18 | 10 | 1.040 | 1.463 | 1.41x |
> | p55/d50 | 2 | 4.159 | **14.220** | 3.42x |
> | p55/d50 | 10 | 1.075 | 3.123 | 2.91x |
> | p10/d90 | 2 | **1.272** | **24.766** | **19.5x** |
> | p10/d90 | 10 | 0.655 | 5.184 | 7.91x |
>
> **The order inverts.** This file concluded "coarse pitch is not rehabilitated
> by a big beam" and rejected pitch 10 on a smear of 1.272. With converged
> windows the order is p10 > p55 > p02 at EVERY beam width — the reverse — and
> pitch 10 leads by 3.5x at the deployment beam.
>
> Point 2 below ("Coarse pitch is not rehabilitated by a big beam") is
> withdrawn. Points 1 and 3 survive: the ratio still compresses as the beam
> widens, and head-on and span still do not see the beam.
>
> Reproduce: `Blender --background --factory-startup --python
> scripts/redo_phase55.py`. Full account in
> `results/FINDINGS_rig_audit_2026_08_20.md`.


2026-08-16. Data: `form_phase55.json` (6 runs, full-fidelity form protocol at
stripe widths 5 and 10 mm) + width-2 anchors from `form_pyr.json` /
`form_phase5.json` / `form_phase54.json`. Predictions pre-registered in
`scripts/sweep_phase55.py`.

## Why

Every published smear/span number was conditioned on STRIPE_W = 2.0 mm — a
protocol constant. The real projector is a LaserCube Ultra 7.5W MK2
(4 mm aperture, 1 mrad divergence — X-Laser product page), i.e. ~7 mm at 3 m,
~9 mm at 5 m, ~14 mm at 10 m on the wall. The user flagged it; the width is
now a swept variable AND a first-class simulator input (`beam_w` through
/api/form, cyc_worker, mts_worker, and the UI).

## Measurements (form protocol, 16 phases × 512 spp; rms at −40°)

| pitch | beam | smear | head-on | span@0 | panel / flat return, mm |
|-------|------|-------|---------|--------|--------------------------|
| 2     | 2    | 4.104 | 0.02723 | 1.01×  | 3.23 / 0.78 |
| 2     | 5    | 1.793 | 0.02730 | 1.00×  | 3.41 / 1.90 |
| 2     | 10   | 1.040 | 0.02732 | 1.00×  | 3.93 / 3.77 |
| 5.5   | 2    | 4.159 | 0.02710 | 1.01×  | 3.15 / 0.78 |
| 5.5   | 5    | 1.825 | 0.02727 | 1.01×  | 3.36 / 1.90 |
| 5.5   | 10   | 1.075 | 0.02732 | 1.00×  | 3.97 / 3.77 |
| 10    | 2    | 1.272 | 0.02701 | 1.02×  | 1.07 / 0.78 |
| 10    | 5    | 0.786 | 0.02722 | 1.01×  | 1.59 / 1.90 |
| 10    | 10   | 0.655 | 0.02738 | 1.01×  | 2.56 / 3.77 |

## What the numbers mean

1. **The smear RATIO compresses toward 1 as the beam widens** — not because
   the panel destroys less, but because the flat control blurs more: the
   control's return is the beam itself (0.78 → 1.90 → 3.77 mm), while a
   fine-pitch panel returns a smudge whose width the PANEL sets
   (~3.2–4.0 mm, nearly beam-independent).
2. **Coarse pitch is not rehabilitated by a big beam.** Pitch 10 returns a
   stripe NARROWER than the flat wall's at every width (smear 0.65–1.27):
   its 10 mm flanks act as mirrors and keep the stripe a stripe. My interim
   guess in chat ("a 9 mm beam revives p10") was wrong; the measurement
   killed it.
3. **Head-on (0.0270–0.0274) and span (≤1.02×) never see the beam** for
   sharp fields — and total ρ never did. So the three-axis verdict of
   Phase 5.4 stands at every beam width: **p2/d18 sharp wins; p10 stays a
   compromised fallback.**
4. At real beam widths the form axis loses discriminating power among
   fine-pitch designs — the beam arrives pre-blurred. What separates designs
   in deployment is total ρ and head-on, plus the p10 anti-feature above.

## Prediction grading

- P1 (smear collapses onto R = beam/pitch, saturating ~4.2 above R 0.5) —
  **WRONG decisively.** No collapse, no saturation; smear falls with beam
  width for every pitch.
- P2 (head-on beam-independent ±30%) — **HELD** (spread < 3%).
- P3 (span < 1.2× everywhere) — **HELD** (worst 1.01×).

## Caveats

- The stripe models a static beam footprint; the real display scans at
  35 kpps. Time-averaged the stripe model is reasonable, but a slow-scan
  line could look different. [추측]
- 1 mrad is the vendor's nominal divergence for a combined RGB beam; a
  1-minute tape-measure of a static spot on the wall would replace it with
  a measurement.
