# SpillSinkSimulator

Finding a wall panel geometry for a large indoor laser installation.

Hundreds of synchronised laser projectors converge in mid-air to form a
volumetric image, visible only because haze scatters a few percent of each
beam. Every beam then carries on and terminates on a wall, which receives
essentially the full beam power and paints a sharp, bright copy of the artwork
around it. Outdoors this does not happen — the beam never lands. Indoors it
buries the piece.

This repository is the simulation used to find a panel that kills that spill,
and the record of what was tried.

## Current answer

Deep V-grooves — the wall-scale version of a laser beam dump, where only the
ridge line is exposed head-on and everything else is at grazing incidence.

| | |
|---|---|
| geometry | V-grooves, depth 50 mm, mean pitch 13 mm (±25% irregular), ridge tip 0.8 mm |
| coating | ρ = 0.005 (0.5%), Musou-Black class, gloss roughness 0.30 |
| **reflectance, head-on** | **0.026 %** |
| reflectance, worst within ±40° | 0.029 % |
| reflectance, worst over all angles | 0.266 % |

Against a plain matte black wall at 5%, that is roughly 190× darker head-on.
The structure contributes about 19× of it; the coating the rest.

## Design laws, all measured rather than assumed

```
reflectance  ≈  0.09 × (ridge tip width / pitch) × ρ
```

Only the *ratio* tip/pitch matters, so a coarser pitch buys a blunter — and far
more makeable — tip. Reflectance is exactly linear in the coating reflectance
(measured 0.170 / 0.172 / 0.176 across a 10× range), so a different coating
rescales every number by the same factor.

```
aspect ratio A = depth / pitch     A ≥ 2 holds ±40°,  A ≥ 6 holds every angle
```

Below A = 1 the ±40° figure triples. And gloss roughness 0.30 is an interior
optimum: 0.15 leaves a specular lobe narrow enough to aim at the observer,
0.50 scatters straight back.

## What did not work, and why

Three geometry families were built and measured before this one. The dead ends
are kept because they are most of the information.

**Angled slats over a hidden chamber.** The slats blocked the view completely —
a material-ID render showed the front view was 97.8% slat and 0.0% chamber — so
the entire stage-1 : stage-2 depth-ratio sweep moved the result by under 2%.
Raising the hidden chamber's reflectance from 0.05 to 0.90 changed nothing to
four decimals: light that gets in never comes back out past the black slats.

**Open scatter troughs.** Meant to destroy the *shape* of the return rather
than just dim it. At retro-incidence the observer and the beam are collinear,
so whatever the beam hits first is visible, and a single bounce can never
displace a photon. Form survived at every trough width and interior
reflectance.

**Hierarchical serration** on the groove flanks, copying ultra-black butterfly
scales. Those work by graded refractive index at sub-wavelength scale; at
millimetre scale the teeth only spoil the grazing incidence the groove depends
on. Measured: no effect below 0.1 mm, actively worse above 0.3 mm.

## Method

Cycles path tracing at 128 bounces, denoising and clamping off, linear colour.
The primary measurement is uniform illumination with the camera tilted to θ,
which by Helmholtz reciprocity reads the directional-hemispherical reflectance
ρ_dh(θ) directly — the total fraction of an arriving beam that leaves again —
with none of the delta-function glint that destabilises a collimated-source
measurement.

Validation, in `scripts/validate.py` and `scripts/test_floor.py`:

| check | result |
|---|---|
| emission 1.0 / 0.5 plane | 1.000000 / 0.500000 |
| flat Lambertian ρ = 0.05 | 0.050001 |
| open box cavity, f = 1/6 | 0.2356 (0.233 recorded previously) |
| ρ = 0 panel | exactly 0 — the measurement has no floor |
| seeds 0–4, samples 384→6144 | spread 0.2%, already converged |

An adversarial audit of the methodology caught a real error partway through:
a 66.7× "glint" turned out to be tessellation, not physics — six facets on the
rounded ridge tip put mirror normals at exactly ±15/45/75°, and
`scripts/test_tessellation.py` confirmed the peak moves to 180/n as the segment
count changes. That result was withdrawn.

## Layout

```
project/
  scripts/     generators, the Cycles harness, sweeps, analysis, reporting
  results/     CSV per sweep, JSON per validation, summary plots
  profiles/    numbered cross-sections, oldest first — see INDEX.md
  report/      YYYY-MM-DD/HHMM_report.png + snapshot.json + README.md
  export/      STL, including printable coupons and a flat control
  renders/     EXR/PNG (not tracked; regenerable from the sweeps)
```

Run a report with `python3 scripts/make_report.py "note"`. Every number on the
sheet is read back out of `results/*.csv`, so it cannot quote something that
was not measured.

## What a person standing under it sees

**Radiance factor β = 0.00105** — about **one seven-hundredth of a sheet of
white paper** held in the same place, and **darker than every reference black in
the literature**: below black velour's 0.0020–0.0122 bracket, below Musou
fabric's 0.0012–0.0055, and 25× below a plain matte black wall
(`project/metrics/09_audience_reflectance.md`). That is the number to quote.

Against a flat plate of the same paint it is **27.5× on the mean and 54× on the
peak** — and the peak is the one that matters, because a painted ceiling shows
the projector's specular reflection at β = 0.603, three quarters as bright as
white paper. The structure takes that to 0.011.

## Open

1. ~~The incidence-angle distribution of the real rig.~~ **Stated, and it
   changes the answer** — see `project/INSTALLATION.md`. A ring of projectors
   aimed up at 45° with a ±25° scan field puts **20–70°** on the ceiling and
   never anything near normal, so **68 % of the light arrives outside the
   0/±20/±40 band every design here was scored in**. Still open: nobody has
   surveyed the room, and φ was never swept.
2. Whether the coating reaches the bottom of the groove. An uncoated floor is
   not ρ 0.005, it is bare substrate.
3. ~~No Fresnel in the material model.~~ **There is now** — `materials.py`
   fits one and `metrics/01` records that it inverted the ranking. What
   replaces this: the coating model is **not reciprocal**
   (`results/FINDINGS_bidir_2026_08_20.md`), which is the property
   `metrics/01`'s reciprocity measurement rests on.
4. Every absolute number assumes the coating really is ρ 0.005. Unverified
   until a physical coupon is measured — `export/` has the coupons and the
   flat control to do it with.
