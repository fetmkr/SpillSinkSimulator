# 05 · total integrated scatter (TIS) — PLANNED

**Status:** planned, not yet implemented

## Definition

From Filip & Vávra 2026 eq. 3 (`reference/SUMMARY.md` §1):

    TIS = R_d / R_t = R_d / (R_s + R_d)

the fraction of reflected energy scattered *away* from the specular direction,
with a specular exclusion cone of half-angle 5°.

## Why it is worth adding

1. **It is what our panel is for.** A structure that converts specular return
   into diffuse return has TIS → 1. That is form destruction, stated as a
   published quantity.
2. **It makes us comparable to real materials.** The same paper reports TIS for
   six measured black materials, so our panel stops being comparable only to
   itself. Lowest TIS among theirs was black velvet, then Vantablack and Musou
   fabric.

## Implementation note

**The directional readout now exists** — `metrics/08_brdf_slice.md`, beam and
camera rather than reciprocity, absolute in 1/sr. What 05 still needs from it
is an AZIMUTH axis: TIS is a ratio of two hemisphere integrals, and 08 measures
one plane. At normal incidence, where the BRDF is azimuthally symmetric, 08
already closes the integral (`gate_bidir` G6) and TIS is computable today.

Needs a directional readout, not the reciprocity trick — TIS is defined on the
outgoing distribution for a fixed incidence, so it wants the beam-and-camera
geometry with the specular cone masked out. The 5° exclusion cone is the
authors' choice for real black materials and should be matched exactly if the
numbers are to be compared.
