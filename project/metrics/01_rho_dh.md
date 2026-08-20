# 01 · ρ_dh — directional-hemispherical reflectance

**Status:** live · **Primary quantity of the project**

## Definition

The fraction of a beam arriving from direction θ that leaves the surface again,
in any direction.

    ρ_dh(θ) = ∫_hemisphere  f_r(θ, ω_o) · cos θ_o  dω_o

This is the same quantity as the THR defined in Filip & Vávra 2026 eq. 1
(`reference/SUMMARY.md` §1), which means our numbers are directly comparable to
their goniometer measurements of real black materials with no conversion.

## How it is measured

By **Helmholtz reciprocity**, not by shooting a beam. The scene is lit by a
uniform world of radiance 1.0 and the *camera* is tilted to elevation θ. What
the camera reads is then ρ_dh(θ) directly.

The reason for doing it this way: shooting a collimated beam and photographing
the return puts a delta-function glint in the frame, and a single specular spike
destroys any mean taken over the panel window. An early version of this project
reported a ratio of 46,000 at one angle for exactly that reason. Reciprocity has
no such spike — every pixel is already an integral over the hemisphere.

Cycles settings that matter: `max_bounces=128`, no denoising, no clamping,
`view_transform=Standard`, gamma 1.0. Any of these wrong silently changes the
number.

## Baseline

Absolute. No baseline needed to state it. When a ratio is quoted alongside it,
the baseline must be named explicitly and is one of:

- **plain matte black wall** — the 0.05 diffuse control plate present in every frame
- **the coating on a flat plate** — currently 1.00% at normal incidence for the
  fitted Musou Black model, and it is *not* flat with angle (3.18% at 80°)

## What it does NOT capture

- **How bright the surface looks.** This is a hemispherical TOTAL, so it has
  already integrated away the direction an observer stands in. For the
  recommended honeycomb it credits the structure with 5-30x over its own
  coating while a person under it sees 2.1x, because a honeycomb is a
  retroreflector and much of what this metric scores as *removed* is
  *redirected back up the beam*. Use `metrics/09` for what a client is asking.
- **Where the light goes.** ρ_dh is a single scalar; a design that returns the
  same energy as a sharp line and one that returns it as a wide smear score
  identically. Form destruction is metric 02/04/07, not this one.
- **Wavelength.** One broadband grey channel. Real lasers are narrow-line.
- **Polarisation.** Not modelled at all.
- **Coating reach.** The model assumes the coating covers the root of a deep
  cell as well as the tip. Unverified until a coupon is printed and measured.

## Validation

- A flat Lambertian plate of ρ=0.05 reads 0.050000. Checked in every frame as
  the control, and asserted by `lock.py`.
- A flat plate of the fitted coating reproduces the published goniometer curve
  to within 9.5% worst-case (`scripts/fit_coating.py`, table in
  `blender_render.py`). Asserted by `lock.py` `material_check`.
- ~~Reflectance is exactly linear in ρ, so a change of coating rescales every
  design equally.~~ **TRUE ONLY FOR THE OLD FLAT-ρ MATERIAL. FALSE for the
  Fresnel coating, and this is the most consequential correction in the
  project so far.**

  Measured, same four designs, old glossy ρ=0.005 vs the fitted coating:

  | design | old ρ_dh @0 | new ρ_dh @0 | factor |
  |---|---|---|---|
  | flat plate | 0.4953% | 0.9982% | **2.0×** |
  | 1D groove d50/p13 | 0.0160% | 0.1401% | 8.8× |
  | 1D groove d30/p7.5 | 0.0236% | 0.1546% | 6.5× |
  | 3D cone d30/p3.75 | 0.0080% | 0.1163% | 15× |
  | 3D cone d30/p7.5 | 0.0047% | 0.1923% | **41×** |

  The design-to-design spread collapses from 5.0× to 1.65× at θ=0, and **the
  ranking inverts: the recommended cone goes from best to worst head-on.**

  Mechanism, measured not assumed: a trap is dark because a ray takes many
  bounces, and most of those bounces are at grazing angles. Under a flat-ρ
  material a grazing bounce keeps 0.5%; under Fresnel it keeps about 5%. The
  deeper the trap, the more bounces, the more it loses — which is why the cone
  loses 41× and the shallow groove only 6.5×. **Fresnel eats the advantage of
  depth.**

  **Consequence: every past comparison must be RE-RUN, not rescaled.**

  **Second consequence, and the reason not to simply believe the new number
  either:** the coating fit constrains only ρ_dh(θ) of a *flat plate*. Nothing
  in it constrains BRDF shape or multi-bounce behaviour — and multi-bounce is
  what every cavity number depends on. Neither material model is validated
  where it matters. Only a measured printed coupon settles this.

## Known defects, fixed

- **Margin defect.** A camera tilted to θ travels D/tan(90−θ) in Z before it
  sees the valley floor — 5.7·D at 80°. Geometry that stopped short of that let
  the tilted view read world background. Every |θ|≥50 number taken before
  `margin_depths=6.5` is void.
- **Tessellation artifact.** `arc_segments=6` put facet normals at exactly
  ±15/45/75°, and a facet at φ retroreflects incidence 2φ. Reported once as a
  66.7× glint. It was the mesh. All arc counts are 24 or more now.
