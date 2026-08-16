# Phase 9.d — from reflectance to visibility: will the scribbles actually disappear?

2026-08-17. ANALYSIS, not a render: every number here is arithmetic on
already-published measurements plus explicitly flagged assumptions.
The question the venue photo poses is not "what is ρ" but "does the
trace on the wall drop below what the eye notices against the
haze-lit room".

## The chain, stated

A scanned laser trace on a wall reads to the eye as a line whose
luminance is proportional to ρ_eff of the wall (everything else —
beam power, scan speed, dwell, wavelength — is IDENTICAL before and
after treatment, so it cancels in the ratio). Therefore treatment
buys exactly:

    trace dimming factor = ρ_current_wall / ρ_eff_new

with ρ taken at the geometry the trace actually meets (the book's
worst-over-angles values are the honest choice).

## The dimming ladder (book values)

| wall state | ρ_eff worst | dimming vs white wall (ρ 0.8) | vs gray wall (ρ 0.3) |
|---|---|---|---|
| white paint | 80 % | ×1 | — |
| dark gray paint | 30 % | ×2.7 | ×1 |
| flat Musou | 1.14 % | ×70 | ×26 |
| bare black pyramid (no paint) | 0.907 % | ×88 | ×33 |
| Musou pyramid (worst over everything) | 0.295 % | ×271 | ×102 |
| Musou pyramid (φ0 nominal) | 0.177 % | ×452 | ×169 |
| AR window unit, level viewer | 0.000–0.038 % | ×2,100 and beyond | ×790+ |

## The visibility criterion, and what decides it

A trace disappears when its luminance drops to roughly the ambient
luminance of the surface it sits on (contrast below a few tens of
percent is hard to notice on a textured dark wall; the exact threshold
depends on adaptation — flagged [추측], the spill-map photos measure
it directly). So the required factor is:

    required = (current trace luminance) / (ambient wall luminance)

measured from a single RAW photo of the current room: the ratio of
trace-pixel to nearby-wall-pixel linear values. The protocol's spill
map now doubles as this measurement (shoot one frame UNDERexposed so
the traces don't clip — added to the protocol).

## What the ladder already says, with the venue photo as a rough gauge

In the photo the traces are heavily overexposed against the haze-lit
walls — consistent with a trace-to-ambient ratio in the tens to
hundreds [추측 until a RAW frame is measured]. Against that range:

- **Musou pyramid zones (×170–450) put traces at or below ambient**:
  the scribbles sink into the wall's own haze glow. This is why the
  critical zones get the paint.
- **Bare zones (×33–88) leave faint traces plausibly visible** if the
  current ratio is above ~50. The two-tier plan is therefore not
  "critical zones look better" but "critical zones disappear,
  bare zones fade" — and whether fade is enough for the non-critical
  walls is exactly what one underexposed photo decides BEFORE any
  casting order.
- **The haze floor is the limit for everything**: no wall treatment
  can go below the volumetric glow of the beams in the air. Once
  traces sit under the haze luminance, further ρ buys nothing
  visible — which is why the window unit's extra ×10 over the Musou
  pyramid matters only for the beam-dump spot, где power concentrates.

## Action added to the physical protocol

Spill-map session: take one extra UNDERexposed frame (traces not
clipped) plus one ambient-only frame (laser off, haze on). Two pixel
ratios from those frames turn this entire ladder into a per-zone
verdict — including whether the bare tier suffices on side walls —
before any mold is ordered.
