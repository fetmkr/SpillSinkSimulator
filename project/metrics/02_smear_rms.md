# 02 · smear, rms

**Status:** live

## Definition

The root-mean-square width, in millimetres, of the returned light distribution
along Z, for a thin line incident on the panel.

    rms = sqrt( Σ w(z)·(z − z̄)²  )      with w(z) = profile(z) / Σ profile

Light transport is linear, so the response to one thin line is the line-spread
function, and the response to any artwork is that artwork convolved with it. A
big rms means the wall copy is blurred; the flat-wall control sets the floor.

## How it is measured

A 2 mm collimated stripe (`spread_deg = 0.05`, deliberately small — an early
run used 1.0° at 900 mm, which blurred the "2 mm" line before it ever reached
the panel and made every design look good). The Z profile of the returned
radiance is taken over the panel window; the same stripe illuminates the
control plate in the same frame, so the control's rms is a same-units floor.

## Baseline

The **0.05 diffuse control plate in the same frame** — a plain matte black wall.
It reads about 0.87 mm at −40°, which is the stripe's own footprint. Any panel
value must be quoted against that number, not in isolation.

## Measured, at −40°, coating ρ 0.005, tip 0.4 mm across

| design | rms |
|---|---|
| flat wall (control) | 0.87 mm |
| 1D V-groove d30 / p7.5 | 1.02 mm |
| 1D V-groove d50 / p13 | 2.41 mm |
| 3D cone d30 / p3.75 | 3.86 mm |
| 3D cone d30 / p7.5 | **4.33 mm** |

## What it does NOT capture

- **Brightness.** A design can smear beautifully and still be too bright to
  hide. rms must always be read next to [01](01_rho_dh.md) or, better, folded
  into [04](04_peak_radiance.md).
- **The shape of the smear.** rms is a second moment; a wide flat halo and a
  narrow core plus two distant spikes can share an rms. Use [07](07_mtf.md) when
  the distribution shape matters.
- **Head-on.** At θ=0 every geometry tried returns an essentially unsmeared
  line, because observer and beam are collinear, the first hit is visible, and
  one bounce cannot displace a photon. rms at θ=0 is near the control floor for
  everything and cannot rank designs. **This is the unsolved axis.**
- Truncation: if the smear approaches the window width the second moment is
  underestimated. Keep the panel wide enough that the tails are inside it.
