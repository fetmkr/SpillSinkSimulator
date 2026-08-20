# The installation, and what the audience actually sees

**The geometry here is stated by the client, not surveyed.** Everything derived
from it is arithmetic, computed by `scripts/report_geometry.py` and
`scripts/audience.py` so it cannot drift from the report that quotes it.
Recorded 2026-08-21.

## The headline: reflectance at the audience

**Radiance factor β** — this surface's radiance divided by that of a **perfect
Lambertian white** under the same light. β = 1.000 is the white standard.

| surface | β, mean | β, peak | × white paper | × black velour |
|---|---|---|---|---|
| **the panel** — honeycomb 6.4 / 64 / 0.03, Musou to 15 % | **0.0037** | 0.0166 | **1 / 216** | **1.16 ×** |
| a flat plate of the panel's own Musou coating | 0.0078 | 0.0114 | 1 / 103 | 2.44 × |
| black velour, with its measured grazing rise | 0.0032 | — | 1 / 251 | 1.00 |
| black velour, at its normal-incidence value only | 0.0020 | 0.0020 | 1 / 400 | 0.63 |
| white paper (Lambertian model, ρ = 0.80) | 0.8000 | 0.8005 | 1 / 1 | 251 × |

**Read that as: the ceiling reads about one two-hundredth of a sheet of white
paper held in the same place, and it is level with black velour — not better
than it.**

### Two things this changes

**1. The structure is worth about 2×, not 5–30×.** `metrics/01` ρ_dh — the
hemispherical total — credits the honeycomb with 5–30× over its own coating. At
the audience it buys **2.1×** (0.0078 → 0.0037). The difference is not error: a
honeycomb is a retroreflector, so much of what ρ_dh scores as *removed* is
actually *redirected back up the beam*. Real light, going somewhere the audience
is not. ρ_dh takes the credit; the audience does not get the benefit.

**2. It does not beat black velour.** Modelled with the grazing rise Filip &
Vávra 2026 measured (β 0.002 at normal → 0.0122 at 85°), velour reads β = 0.0032
over this room's angles against the panel's 0.0037 — **the panel is 16 %
brighter.** Against velour's normal-incidence value alone it is 1.85× brighter.
The velour model is Lambertian and the same paper says velour is not Lambertian
(it has the *lowest* TIS of anything they measured), so this comparison is
already tilted in the panel's favour.

The case for the panel is therefore **not** that it out-darkens velour. It is
that it is a rigid ceiling panel with a buyable process, at velour's brightness.

## The room

| | |
|---|---|
| projectors | a ring on a **6 m circle**, at eye height **1.6 m** |
| aim | **inward and up at 45°** |
| scan field | **±25° square**, both axes |
| panel | **ceiling at 4.5 m**, facing down, treated as infinite |
| audience | standing, inside **half the ring radius — 1.5 m** |

Eye height is an assumption; the angles barely move with it, because incidence
is set by the aim, not the heights.

## What the room delivers

**Incidence on the panel = 90° minus the ray's elevation.** A 45° aim with a
±25° scan therefore lands between **20° and 70°, and never near normal** — the
corner rays of a square field reach 71.9°.

**68 % of the light arrives outside |θ| ≤ 40°**, the band `principles/00` §C
scores in and the band the whole honeycomb search was ranked in. Normal
incidence — where the panel is far and away at its best — never happens.

Measured across the delivered band (`scripts/probe_rigband.py` →
`results/rigband_hcflat.csv`, three seeds, margin 6.5):

| ρ_dh, directional-hemispherical reflectance | |
|---|---|
| worst of the **scored** band, 0/±20/±40 | 0.001645 |
| worst of the **delivered** band, 20–70° | **0.002905** — 1.77× |

## Where the light lands, and where it comes back

A 45° beam from r = 3 m rises 2.9 m and runs 2.9 m, so **the centre ray
converges within 0.1 m of the axis**. The scan field spreads either side: the
steepest ray lands at r = 1.9 m, the shallowest 5.0 m past the axis on the far
side. **The lit ceiling is everything inside about r = 5 m.**

**The retro return goes back up the beam, to r = 2.9 m — the projector ring
itself.** Holding the audience inside 1.5 m keeps them out of it: looking
straight up, a listener is **45° off the retro ridge**, the darkest part of the
map.

**But overhead is not the worst case.** Over every lit ceiling point, every
projector that can light it and every place a person may stand
(`report_geometry.closest_to_retro`), the closest approach is **4.2° off the
retro direction** — at the far rim of the lit ceiling, incidence 70°, a listener
at r = 1.5 m looking outward at 66°. **The exposure is a grazing look across the
room, not a look overhead.** The panel's hottest cells sit there: β = 0.0111 at
incidence 70 / observation 60, carrying 1.1 % of the light.

If that matters, the lever is **aim control** — trimming the low edge of the
scan field shrinks the lit radius and removes those cells entirely.

## What is still unknown

- **Stated geometry, not a survey.** No dimension here was measured on site.
- **One azimuth plane.** φ was never swept, so how neighbouring scan fields
  overlap on the ceiling is unmodelled.
- **No beam divergence or spot size.** The rays are lines.
- **The velour baseline is a Lambertian model** from two measured points, and
  the source says velour is not Lambertian.
- **`anodised_hi` is an estimate in every shape parameter**, and the coating
  model is not reciprocal. Both sit under every absolute number here.
- **Zero physical measurements**, still, of anything.

## Where this lives in code

| | |
|---|---|
| the room, and everything derived from it | `scripts/report_geometry.py` |
| the audience weighting and the β metric | `scripts/audience.py`, `metrics/09_audience_reflectance.md` |
| the measurement | `scripts/measure_audience.py` → `results/audience.csv` |
| ρ_dh across the delivered band | `scripts/probe_rigband.py` → `results/rigband_hcflat.csv` |
| the report | `scripts/build_report_hcflat.py` → `report/2026-08-20/hcflat.html` |

Change a dimension in `report_geometry.py` and the report redraws itself. **Do
not retype these angles anywhere else.**
