# 09 · reflectance at the audience — the radiance factor a person actually sees

**Status:** live · **The top-line number of the study**

## Definition

**Radiance factor**, β — the CIE reflectance factor. This surface's radiance
divided by that of a **perfect Lambertian white** under identical illumination:

    β(θ_in, θ_out) = π · f_r(θ_in, θ_out)          [dimensionless]

β = 1.000 is the white standard. It is dimensionless, it is what a goniometer
reports, and it is directly comparable with anyone else's measurement.

**Reflectance at the audience** is β weighted over the **three-angle** cells
the installation actually uses:

    β_audience = Σ w(θ_in, θ_out, Δφ) · β(θ_in, θ_out, Δφ)  /  Σ w

where Δφ is the azimuth between the direction back to the projector and the
direction to the eye, and w is the irradiance the room delivers to that cell —
every projector, every part of the scan field, every place a person is allowed
to stand. See `scripts/audience.py` and `INSTALLATION.md`.

**Δφ IS NOT OPTIONAL, AND LEAVING IT OUT PUBLISHED A WRONG NUMBER.** A room
lights a point from every azimuth at once: 24.5 % of the light an eye receives
arrives near retro, 64.5 % near specular, and the mode is at 150°. An in-plane
rig reaches only 0° and 180° and therefore cannot sample 76 % of it. The
2026-08-20 version of this metric keyed on two angles, sampled the retro side of
every cell, and was wrong by 3.5×. See
`results/FINDINGS_audience_azimuth_2026_08_21.md`.

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
structure buys 5–30× over its own coating. At the audience it buys **27.5×**
on the mean and **54×** on the peak — the two disagree in *both* directions
depending on the design, which is exactly why both must be quoted.
The difference is not error: a honeycomb is a retroreflector, so much of what
ρ_dh counts as "removed" is in fact *redirected up the beam* — real light,
going somewhere the audience is not. ρ_dh gets the credit; the audience does
not get the benefit.

**Quote metric 09 to a client. Quote metric 01 when ranking absorbers.**

## Saying it three ways

Each is the same measurement, and each should be labelled wherever it appears:

| name | what it means | panel reads |
|---|---|---|
| **radiance factor β** | 1.000 = perfect Lambertian white | **0.00105** |
| **× white paper** | paper is 75–85 %, near-Lambertian, β ≈ 0.80 | **1 / 764** |
| **× black velour** | theatrical blackout, the thing this replaces | **0.09–0.52 ×** |

## Baselines, all measured through the identical rig

All are quoted as **brackets between two measured points**, never as a fitted
curve. An earlier draft interpolated velour with an exponent that was invented,
and the answer swung 2× with it. For a Lambertian **β = ρ exactly**, at every
angle and every azimuth, so none of these needs rendering.

- **perfect Lambertian white**, β = 1.000 — the definition
- **white paper**, β = 0.80 — an approximation of paper in general, not a
  measurement of anyone's sheet. It exists so a client can hold one up.
- **black velour**, **β = 0.0020 to 0.0122** over 0–85° — Filip & Vávra 2026
  Fig. 6. The paper reports velour with the *lowest* TIS of any sample it
  measured, so it is **not** Lambertian and this model flatters it: the
  comparison is conservative.
- **Musou fabric**, **β = 0.0012 to 0.0055** — same table. *This* is the
  material behind "surely Musou beats velour": the fabric does, the paint
  (β 0.0100 at normal) does not.
- **a plain matte black wall**, β = 0.05 — the control plate in every frame,
  and what happens if nobody does anything.
- **a flat plate of the panel's own coating** — what the structure is worth

## What it does NOT capture

- **It is conditional on the room.** Change the projector aim, the ceiling
  height or where people stand and the weighting changes. `INSTALLATION.md`
  states the geometry it assumes; that geometry is **stated by the client, not
  surveyed**.
- **No beam divergence or spot size.** The rays are lines.
- **The coating model is not reciprocal** (`FINDINGS_bidir_2026_08_20.md`), and
  `anodised_hi` is an estimate in every shape parameter. Both sit under every
  absolute β here.
- **Adaptation and glare are not modelled.** β is a physical ratio, not a
  perceived brightness; a dark room changes what 0.0037 looks like.

## Validation

The two Lambertian references are the check, and they are exact: measured
through the same 72-cell grid the panel goes through, white paper returns
β = 0.800001 and black velour β = 0.002000 — the rig gives back precisely what
it is handed, in every cell. Anything the panel reads is therefore the panel.

**And the check that catches the azimuth class of error:** a Lambertian is
isotropic, so its β must be identical at every Δφ. Measured 0.20000 at
φ = 0/45/90/135/180 — worst departure 0.000 %. Five renders, and it is the whole
defence.
