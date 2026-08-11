# 2026-08-11

## 1527

ridge V-groove family established; pitch x tip trade fully mapped; tessellation artifact found and withdrawn

- recommendation: depth 50 mm, pitch 13 mm, tip 0.8 mm, coating rho 0.005, gloss 0.30
- **reflectance: head-on 0.0264%, worst +/-40 0.0293%, worst all 0.2660%**
  (ratio column, mislabelled at the time: it is against the **5% diffuse control plate**,
  not a flat plate of the same coating — 0.0053 / 0.0059 / 0.0532. Against the coating on a
  flat plate, which measures 0.4953%, the head-on ratio is 0.053, i.e. 19x darker, not 190x.)
- totals: 5569 renders, 12 sweeps, 67 profiles, 12 STL
- [1527_report.png](1527_report.png)

## 1702

3D cone array supersedes the extruded V-groove: 5x lower reflectance and the first real form destruction

- recommendation: 3D cone array, depth 80 mm, pitch 13 mm, tip 0.8 mm, coating rho 0.005, gloss 0.30
- **reflectance: head-on 0.0044%, worst +/-40 0.0049%, worst all 0.1276%**
- form at -40 deg: core 0.112, MTF@20mm 0.0626 (1D groove: 0.993 / 0.984)
- totals: 6054 renders, 14 sweeps, 67 profiles, 12 STL
- [1702_report.png](1702_report.png)


## 1900 — v2 comparison, after adversarial review

**Supersedes every entry above.** A standing reviewer audited the live claims and found three
wrong, all of them flattering the cone. Anyone shown an earlier version needs these corrections.

- **tip convention.** `profile_ridge.tip_width` is a full WIDTH; `geom3d.tip_radius` is a RADIUS.
  The "tip 0.2 mm, both" comparison therefore gave the groove a tip half the size — and 0.2 mm
  is half an FDM nozzle, so it was not a buildable design either. Everything is now quoted at
  one nozzle, **0.4 mm across, for both families**.
- **measured vs exported.** The cones were measured with `tileable=False` while the STL and the
  renders used `tileable=True`, which re-snaps the lattice up to 5% denser. Measured and pictured
  were 7.5% apart. All cone numbers are now measured on the geometry that is actually exported.
- **form.** "core 0.11 vs 0.99" came from two designs that were not on the page and did not match
  each other. `core_frac` is also unusable at large smear — energy leaving the window leaves the
  denominator too — so smear is now reported as **rms**.

Also fixed: the regression lock's own "flat plate" self-check was a washboard of 25 mm
half-cylinders (`tip_round` defaults True) reading 0.353%. A real flat plate of the coating reads
**0.4953%**. The lock now asserts on the 0.05 diffuse control that every render already carries.

| design | head-on | ±40 | all | smear @-40 | MTF@20mm |
|---|---|---|---|---|---|
| 1D V-groove d50 / p13 | 0.0159% | 0.0178% | 0.2491% | 2.41 mm | 0.76 |
| 1D V-groove d30 / p7.5 | 0.0237% | 0.0261% | 0.2613% | 1.02 mm | 0.96 |
| **3D cone d30 / p7.5** | **0.0047%** | **0.0055%** | 0.2013% | **4.33 mm** | **0.35** |
| 3D cone d30 / p3.75 | 0.0080% | 0.0080% | **0.0796%** | 3.86 mm | 0.43 |
| flat plate, same coating | 0.4953% | 0.4953% | 0.4953% | 0.87 mm | — |

Matched on depth, pitch and printable tip, the cone is **5.0x** darker head-on and smears the
line **4.3x** wider. Both axes, one design.

Conditions: coating rho 0.005 (Musou-Black class, gloss 0.30, measured 0.4953% flat); absolute
directional-hemispherical reflectance; Cycles 128 bounces, no denoise or clamp, linear colour;
reciprocity measurement (uniform illumination, camera tilted).

Open: the "105x darker than the flat coating" figure is **head-on only** — by -80 deg it is 2.4x.
Fresnel is not modelled, and grazing is where that bites. The pitch choice cannot be settled until
we know the incidence angles the real rig puts on the wall; that is a measurement on the
installation, not a simulation.

- [1900_compare.png](1900_compare.png)
