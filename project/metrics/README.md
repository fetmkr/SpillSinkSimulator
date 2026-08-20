# Metrics — what this project measures, and what each number can and cannot say

Every number that reaches a report or a client comes from one of the metrics
defined here. This folder exists so that a new session, or a different person,
starts from the same definitions instead of re-deriving them from script
comments — and so that a metric's known defects travel with it.

**Numbered like `profiles/`, so the evolution is visible.** A metric is never
silently edited into a different meaning: if the definition changes, the old
file is marked SUPERSEDED and a new number is issued.

## Live

| # | metric | what it answers | computed by | guarded by |
|---|---|---|---|---|
| [01](01_rho_dh.md) | ρ_dh — directional-hemispherical reflectance | how much of an arriving beam leaves again | `blender_render.py` mode `hemi_view` | `lock.py` |
| [02](02_smear_rms.md) | smear, rms | how far the returned line is spread | `form_mtf.py` `rms_width` | — |
| [04](04_peak_radiance.md) | **peak radiance ratio** | **how bright the brightest point of the wall copy is, vs a plain black wall** | `form_mtf.py` `peak` + `metrics.py` | — |
| [07](07_mtf.md) | MTF at a spatial period | how much contrast survives at a given feature size | `form_mtf.py` `mtf_at` | — |
| [09](09_audience_reflectance.md) | **reflectance at the audience** | **how bright the ceiling looks to a person under it — radiance factor β, 1.000 = perfect white** | `audience.py` / `measure_audience.py` | the two Lambertian references |
| [08](08_brdf_slice.md) | **in-plane BRDF slice** | **where the light goes — incidence against observation, in 1/sr** | `bidir.py` / `sweep_bidir.py` | `gate_bidir.py` |

## Planned

| # | metric | why |
|---|---|---|
| [05](05_tis.md) | total integrated scatter | published definition, makes our panel comparable to measured real materials. **Blocked only on an azimuth axis now that [08](08_brdf_slice.md) exists — 08 is the directional readout 05 said it needed** |
| [06](06_effective_albedo.md) | effective albedo | one cosine-weighted number when the rig's angle distribution is unknown |

## Retired

| # | metric | why it was retired |
|---|---|---|
| [03](03_core_frac.md) | core fraction | breaks at large smear — energy leaving the measurement window leaves the denominator too, so a *more* smeared design can score *better* |

## Which number goes to a client

**[09](09_audience_reflectance.md).** [01](01_rho_dh.md) is a hemispherical total and has already integrated away the direction the audience stands in; on the recommended panel the two disagree by 2.4x about what the structure is worth. Rank absorbers with 01; quote 09.

## Rules

1. **Absolute before relative.** The headline is always the absolute quantity;
   ratios against a flat plate or a plain wall are secondary and must name what
   they are against. A ratio column once said "against a flat plate of the same
   coating" while dividing by the 5% diffuse control — a 10x mislabel, in a line
   a client reads.
2. **Every metric names its baseline in its own file.** If a number has no
   stated baseline it is not reportable.
3. **Every metric lists what it does NOT capture.** That section is not
   optional; it is the part that prevents the number being over-read.
4. **A metric that cannot rank the designs in front of it is not doing its job.**
   Say so in the file rather than quoting it anyway. See 03.
