# 07 · MTF at a spatial period

**Status:** live, with a known defect

## Definition

The modulation transfer at spatial period q, from the line-spread function:

    MTF(q) = |F(1/q)| / |F(0)|

where F is the Fourier transform of the Z profile. `mtf_20mm = 0.35` means a
feature 20 mm across comes back with 35% of its contrast.

This is the metric that speaks most directly to the actual problem — the wall
copy is legible if contrast survives at the size the artwork's strokes are.

## Baseline

The control plate in the same frame reads close to 1.0 at every period, because
a flat wall returns the line intact. Quote the panel value against it.

## Measured, at −40°, MTF at 20 mm

| design | MTF@20mm |
|---|---|
| 1D V-groove d30 / p7.5 | 0.96 |
| 1D V-groove d50 / p13 | 0.76 |
| 3D cone d30 / p3.75 | 0.43 |
| 3D cone d30 / p7.5 | **0.35** |

## Known defect — do not over-read

`|F|` discards phase. Two distributions with the same modulation but different
placement score identically, and a smear that is *shifted* rather than
*spread* is not penalised. The FWHM helper in the same module also collapses to
a single pixel on sharply peaked profiles and should not be quoted.

Until phase is handled, treat MTF as **supporting** evidence for
[02](02_smear_rms.md) and [04](04_peak_radiance.md), not as a headline.

## What it does NOT capture

- brightness — same caveat as 02
- the head-on case, for the same collinearity reason as 02
- 2D structure: the profile is taken along Z only, so azimuthal spreading is
  projected away. For a 3D cone array, which spreads azimuthally by design,
  this **under-reports** the effect.
