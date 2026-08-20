# The installation, and what the audience actually sees

**The geometry here is stated by the client, not surveyed.** Everything derived
from it is arithmetic, computed by `scripts/report_geometry.py` and
`scripts/audience.py` so it cannot drift from the report that quotes it.
Recorded 2026-08-21.

## The headline: reflectance at the audience

**Radiance factor β** — this surface's radiance divided by that of a **perfect
Lambertian white** under the same light. β = 1.000 is the white standard.

| surface | β, mean | β, peak | × white paper | vs this |
|---|---|---|---|---|
| **the panel** — honeycomb 6.4 / 64 / 0.03, Musou to 15 % | **0.00105** | **0.0111** | **1 / 764** | — |
| a flat plate of the panel's own Musou paint | 0.0288 | **0.603** | 1 / 28 | panel is **0.036×** |
| black velour (Lambertian model, bracket 0–85°) | 0.0020 – 0.0122 | — | 1 / 400 – 1 / 66 | panel is **0.09–0.52×** |
| Musou fabric (Lambertian model, bracket 0–85°) | 0.0012 – 0.0055 | — | 1 / 667 – 1 / 145 | panel is **0.19–0.87×** |
| a plain matte black wall | 0.0500 | — | 1 / 16 | panel is **0.02×** |
| white paper (Lambertian model, ρ = 0.80) | 0.8000 | 0.8000 | 1 / 1 | panel is **0.0013×** |

**Read that as: the ceiling reads about one seven-hundredth of a sheet of white
paper held in the same place, and it is darker than every reference black in the
literature this study relies on — below the bottom of every bracket.**

> **Corrected 2026-08-21.** An earlier version of this table said β = 0.0037 and
> "does not beat black velour". Both were wrong: the measurement sampled the
> retro side of the BRDF for every cell while 76 % of the light an eye receives
> arrives at azimuths an in-plane rig cannot reach.
> `results/FINDINGS_audience_azimuth_2026_08_21.md`.

### Two things this changes

**1. The structure is worth 27.5× on the mean and 54× on the peak.** A flat
plate of the same Musou paint reads β = 0.0288 with a **peak of 0.603** — three
quarters as bright as white paper. That peak is **the specular reflection of a
projector in a painted ceiling**, and it is the strongest argument for the
structure this study has produced: the honeycomb takes it to 0.011.

**2. It is darker than every black in the reference literature.** Below black
velour's whole bracket (0.0020–0.0122), below Musou fabric's (0.0012–0.0055),
25× below a plain matte black wall. And the velour figure is conservative
against us: it is a Lambertian model, and its own source reports velour with the
*lowest* TIS of any sample measured, so real velour at these angles is very
likely worse than the bracket's floor.

**On "surely Musou beats velour":** it does — as a *fabric*, 0.0012 against
0.0020. As *paint*, which is what this panel is coated in, it does not: 0.0100
against 0.0020. The structure is what closes that gap and then some.

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
