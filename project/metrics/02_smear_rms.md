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

## MEASUREMENT CONDITIONS (revised 2026-08-20, and they are not optional)

**The window must be opened until the answer stops changing.** It used to be a
fixed 40 % of the sample (`blender_render.MEAS_INSET_Z = 0.30`), which is a
LENGTH written as a fraction, so it scaled with the panel instead of with the
returned light. Worse, `rms_width` normalises by the energy INSIDE the window,
so light past the edge leaves the numerator AND the denominator and the reading
collapses onto the core rather than merely shrinking. Synthetic profile of true
rms 17.777 mm: 0.800 through a 24 mm window, 0.800 at 48, 17.777 at 96.
**A clipped design is indistinguishable from one that does not smear at all, so
a value near 1.0 is the most suspect, not a large one.**

Rule of thumb from two independent convergences: **the window must be about six
times the return's 90 %-energy half-width.** p10/d90 (z90 30 mm) converged at
192 mm; the order spec (z90 10 mm) at 48 mm.

**The profile array must follow the window.** `NWIN = 361` was a SAMPLE COUNT,
so its physical length shrank as sampling got finer -- 77.6 mm at 0.215 mm/px
but 9.0 mm at 0.025, which clipped a 10 mm return and took smear from 2.234 to
1.008. It is now derived from the face.

**Sampling density does not matter for this metric** (0.5 % over a 5.6x range,
0.16 % over a 3 x 3 grid of panel size and density) because it is a ratio of two
widths measured in the same frame: numerator and denominator blur together.
This is NOT true of metric 04, which is a peak. See that file.

**Panel size does not matter** once the window converges: 2.237 / 2.237 / 2.238
/ 2.238 / 2.238 over 50-500 mm. Before the fix the same sweep moved 4.1x.

**Record the beam.** Fifteen result files carry no beam width and were measured
at 2.09 mm, recoverable only by inverting the control's own rms = W/sqrt(12).
The deployment beam is 7.5 mm and the control floor differs 3.6x between them.

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
  **2026-08-20: this warning was live and unguarded for the whole project.**
  Phase 5.5 published 1.272 for a design that reads 24.77 with a converged
  window -- a 19x error that rejected a design. The window is now driven to
  convergence and every result carries a `converged` flag; a value that never
  settles must be quoted as a lower bound or not at all.
- DISPLACEMENT IS SUBTRACTED. `form_metrics.recentre` puts each profile on its
  OWN centroid, so a return that is MOVED rather than widened scores as if
  nothing happened. The code this replaced (`form_mtf.py:180-191`) put both on
  the CONTROL centroid and kept it, with the reason in its comment. Measured:
  the returned line lands 0.59 x depth x tan(theta) away from where a flat wall
  puts it -- 11 mm for the order spec at 40 deg, 45 mm for a 90 mm well. The two
  conventions change the design ORDER, so displacement belongs on its own axis.
  See `results/FINDINGS_rig_audit_2026_08_20.md` section 5.
