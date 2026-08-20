# 09 · reflectance at the audience — the radiance factor a person actually sees

**Status:** live · **The top-line number of the study**

## Definition

**Radiance factor**, β — the CIE reflectance factor. This surface's radiance
divided by that of a **perfect Lambertian white** under identical illumination:

    β(θ_in, θ_out) = π · f_r(θ_in, θ_out)          [dimensionless]

β = 1.000 is the white standard. It is dimensionless, it is what a goniometer
reports, and it is directly comparable with anyone else's measurement.

**Reflectance at the audience** is β weighted over the (θ_in, θ_out) cells the
installation actually uses:

    β_audience = Σ w(θ_in, θ_out) · β(θ_in, θ_out)  /  Σ w

where w is the irradiance the room delivers to that cell — every projector,
every part of the scan field, every place a person is allowed to stand. See
`scripts/audience.py` and `INSTALLATION.md`.

Two figures, because they answer different questions:

| | |
|---|---|
| **mean** | how bright the ceiling looks — the wash |
| **peak** | the brightest patch anyone can see — the glare |

## Why this and not ρ_dh

`metrics/01` is a **hemispherical total**: the fraction of an arriving beam that
leaves in *any* direction. It ranks absorbers. It cannot say how visible the
spill copy is, because it has already integrated away the direction the
audience is standing in.

**The two disagree, and by a lot.** On the recommended panel, ρ_dh says the
structure buys 5–30× over its own coating. At the audience it buys **2.1×**.
The difference is not error: a honeycomb is a retroreflector, so much of what
ρ_dh counts as "removed" is in fact *redirected up the beam* — real light,
going somewhere the audience is not. ρ_dh gets the credit; the audience does
not get the benefit.

**Quote metric 09 to a client. Quote metric 01 when ranking absorbers.**

## Saying it three ways

Each is the same measurement, and each should be labelled wherever it appears:

| name | what it means | panel reads |
|---|---|---|
| **radiance factor β** | 1.000 = perfect Lambertian white | **0.0037** |
| **× white paper** | paper is 75–85 %, near-Lambertian, β ≈ 0.80 | **1 / 216** |
| **× black velour** | theatrical blackout, the thing this replaces | **1.16 ×** |

## Baselines, all measured through the identical rig

- **perfect Lambertian white**, β = 1.000 — the definition
- **white paper**, β = 0.80 — an approximation of paper in general, not a
  measurement of anyone's sheet. It exists so a client can hold one up.
- **black velour**, β = 0.002 at normal incidence — the directional-hemispherical
  reflectance of black velvet measured by Filip & Vávra 2026 (Fig. 6). **Its
  angular behaviour here is a Lambertian assumption and the paper says that is
  wrong**: they measure it rising to 0.0122 at 85°, and report it with the
  *lowest* TIS of any sample, meaning its return is the most
  specular-concentrated. Modelled with that measured rise it reads β = 0.0032
  over this room's cells.
- **a flat plate of the panel's own coating** — what the structure is worth

## What it does NOT capture

- **It is conditional on the room.** Change the projector aim, the ceiling
  height or where people stand and the weighting changes. `INSTALLATION.md`
  states the geometry it assumes; that geometry is **stated by the client, not
  surveyed**.
- **One azimuth plane.** φ was never swept.
- **No beam divergence or spot size.** The rays are lines.
- **The coating model is not reciprocal** (`FINDINGS_bidir_2026_08_20.md`), and
  `anodised_hi` is an estimate in every shape parameter. Both sit under every
  absolute β here.
- **Adaptation and glare are not modelled.** β is a physical ratio, not a
  perceived brightness; a dark room changes what 0.0037 looks like.

## Validation

The two Lambertian references are the check, and they are exact: measured
through the same 48-cell grid the panel goes through, white paper returns
β = 0.800001 and black velour β = 0.002000 — the rig gives back precisely what
it is handed, in every cell. Anything the panel reads is therefore the panel.
