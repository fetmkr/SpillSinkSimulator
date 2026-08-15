# 06 · effective albedo — PLANNED

**Status:** planned, not yet implemented

## Definition

From Filip & Vávra 2026 eq. 2 (`reference/SUMMARY.md` §1):

    A = ∫  ρ(ω_i) · cos θ_i  dω_i

a single cosine-weighted number per surface, integrating ρ_dh over incidence.

## Why it is worth adding

Our current single-number summary is "worst ρ_dh over all angles", which is a
minimax. That is the right choice only if the rig genuinely puts beams at every
angle. It also **guarantees that a directionally-biased design loses**, which is
how the tilted-cone result was scored — and the bird-of-paradise cavities that
inspired it are *designed* to be directionally biased, darkest from the distal
direction (`reference/SUMMARY.md` §3.1). The metric, not the design, may have
been what failed.

A cosine-weighted integral is the honest summary when the incidence
distribution is unknown, and a **measured** incidence distribution from the real
installation would be better than either.

## Caution

The source paper's own albedo figures do not appear to be normalised by
∫cos θ dω = π, and their Fig. 4 albedo bars do not line up with their Fig. 6
THR curves. **Do not quote their albedo numbers** until that is resolved; define
ours explicitly and state the normalisation.
