# Cross-validation — is the renderer telling the truth?

Every optical number in phases 1-5 came from one path tracer driven by one
harness. Gate check 8 compares sweeps against other sweeps: it catches drift
and cannot catch a mistake both sides share. Stray-light practice cross-traces
identical rays between independent codes for exactly that reason.

Three independent checks now exist, in increasing cost.

## 1. The harness itself  `scripts/validate_physics.py`

| check | result |
|---|---|
| convergence: 64 spp vs 1024 spp | **0.69 %** |
| energy conservation, rho = 1 cavity, 2048 bounces | **0.99974** |
| Lambertian control at every theta and phi | **0.0500 exactly** |

The rho = 1 cavity reads 0.675 at the sweeps' 128-bounce limit and 0.99974 at
2048, so the limit is real but it binds only where a ray never dies. At every
reflectance this project uses it does not bind at all:

    rho     0.90     0.50     0.05     0.01
    b=128 / b=512 / b=2048 identical to 5 decimals

**0.69 % is the floor on any claim.** Designs separated by less than that are
not separated.

## 2. A closed-form model  `scripts/crosscheck_analytic.py`

Shares no code with the renderer. Predicts normal-incidence return from
geometry and one flat-plate number:

    rho_dh(0)  ~=  f_exposed * rho_flat(0)

916 designs compared.

| family | ratio measured/predicted |
|---|---|
| honeycomb, cell lattices | **0.92 - 1.07x** |
| **anything with a pyramid floor** | **1.02 - 1.05x** |
| blade arrays | ~2 - 5x |
| **cone, truss** | **100 - 800x** |

Where the exposed area is a few percent the model is exact to within 10 %:

    FL_p650f080_pyramid_d30   predicted 0.03275 %   rendered 0.03355 %   1.02x
    HONE_p0250_d50_wt040      predicted 0.31936 %   rendered 0.31640 %   0.99x

Where it is a fraction of a percent the model collapses, because its whole
premise -- that the return is one bounce off the exposed solid -- stops being
true. A cone exposes 0.12 % and returns 300x what that would give. **The
interior is doing the work, and that is why the cone's normal-incidence total
(0.18 %) sits near a flat-floored honeycomb's while its head-on PEAK is 24x
lower: it returns as much and spreads it.**

**The phase 4 recommendation sits inside the range where the analytic model
agrees.** The cone does not, which is what made a second renderer necessary.

## 3. A second renderer  `scripts/crosscheck_mitsuba.py`

Mitsuba 3.9.1, installed alongside rather than replacing Cycles. Same mesh,
same pure Lambertian rho = 0.01 -- deliberately NOT the fitted Musou coating,
which Cycles builds from a Fresnel-driven mix that Mitsuba has no identical
construction for. A disagreement there would be about materials; this isolates
geometry, the uniform-illumination measurement, and transport.

Setup validated first: a flat Lambertian must read its own reflectance.

    rho 0.010 -> 0.01000   rho 0.050 -> 0.05000    err 0.01 %

| design | Cycles | Mitsuba 3 | difference |
|---|---|---|---|
| cone 5.5 / tip r0.2 | 0.000861 | 0.000894 | **+3.8 %** |
| honeycomb 6.5 / 0.08 | 0.000360 | 0.000344 | **-4.4 %** |

The prediction written before the run was "within a few percent, and more than
~10 % means one of the two codes is wrong about deep-cavity transport and this
study has a problem larger than any design question in it." **+3.8 / -4.4 %.**
The residual is the size of the Monte Carlo floor measured in check 1 plus a
difference in window trimming.

Two codes sharing no sampler, no BVH, no ray generation and no language agree
on a 1.7-million-triangle cone to 4 %.

### The convention that nearly produced a false disagreement

Mitsuba read the flat plate as exactly 0.00000 at first. **Mitsuba 3 BSDFs are
one-sided** -- a back face is black -- and Cycles has no such rule, so this
project's meshes have never had their winding audited. Wrapping in `twosided`
fixed it. Without that the headline would have been "the two renderers
disagree", and it would have been about a convention, not about optics.

## What this settles, and what it does not

SETTLED. Cycles agrees with a closed-form model where that model applies, and
with an independent renderer where it does not. The measurement floor is
0.69 %. Energy is conserved to 0.03 % once bounces are not truncated.

**WITHDRAWN: "Energy is conserved to 0.03 % once bounces are not truncated."**
That was this project's own measurement, not a literature value, and it does not
hold for the geometry it was quoted about. A comb cavity of rho = 1.0 must
return 1.000 at every angle; re-measured at 512 spp it returns 0.673 in Cycles
and 0.561 in Mitsuba at normal incidence. Neither is a renderer fault -- at
rho = 1 nothing decays, so no finite bounce limit can finish the sum -- but the
sentence as written is wrong. What IS established, against the Labsphere closed
form rather than against the other renderer, is in
`FINDINGS_renderer_disagreement.md`: an integrating sphere at rho up to 0.98
(40 mean bounces) is reproduced to 0.27 % by Cycles and 1.22 % by Mitsuba.

NOT SETTLED, and not settleable by more simulation:

- **the coating.** Both renderers were fed the same Lambertian on purpose. The
  fitted two-parameter Musou mix has never been checked against a measured
  BSDF, which is what stray-light practice actually uses.
- **polarization.** Every number here assumes unpolarised light. The numbers
  live at +-40 degrees, which is where polarization matters most. Mitsuba has
  `metal_ad_spectral_polarized` available on this machine; Cycles cannot do it
  at all.
- **wavelength.** One broadband grey channel. Musou Black is 0.6 % at 550 nm
  and **10.7 % at 1500 nm** -- the panel is not black in the near infrared.

## The simulator disagreed by 23 % for a reason that was not optics

The numbers above come from `crosscheck_mitsuba.py`, which builds the cone at
`radial_seg 24 / height_seg 12` because that is what every published sweep row
used. The browser simulator disagreed by **+22.7 %** on what looked like the
same design, and that gap sat in the open-questions list as a possible
transport disagreement at coarse tessellation.

It was neither. `sim_server.NORMAL` listed only each family's headline
parameters and let the rest fall through to the geometry dataclass's own
defaults, which for the cone are `radial_seg 32 / height_seg 3`. A cone wall at
three height bands is a three-facet approximation of a curve; Cycles and
Mitsuba tessellate and shade that differently, and the difference is 23 %. Set
to the published 24 / 12, the same comparison reads **+3.9 %** -- the figure the
script always reported.

The audit that found it (`scripts/audit_normal.py`) compares every value the
simulator would use against the value pinned in `params_json`, and found seven
mismatches across four families:

| family | parameter | simulator showed | reports measured |
|---|---|---|---|
| cone | `radial_seg` / `height_seg` | 32 / 3 | 24 / 12 |
| comb | `jitter` | 0.30 | 0.0 |
| honeycomb | `cell_lean_domain` | 8.0 | 16.0 |
| vgroove | `arc_segments` | 6 | 24 |
| vgroove | `micro_depth` / `micro_pitch` | 0.0 / 0.0 | 0.3 / 1.0 |

The `comb` one contradicted its own module: a commercial expanded honeycomb is
periodic by construction and cannot be jittered, which `_build_comb`'s
docstring states outright. **No published number was affected** -- the sweeps
never read `NORMAL` -- but for as long as it stood, the panel on screen and the
panel in the reports were different parts, and the simulator's whole purpose is
that they are the same one. The audit now runs as a check.

## All three axes, and what the cross-check had been hiding

Until now the cross-check covered ONE of the project's three axes. Smear and
head-on peak -- the two the study calls its first priority -- had never been run
in a second code. Both now are (`scripts/mts_form.py`), through the SAME
statistics module (`form_metrics.py`) so a disagreement cannot be in the
arithmetic, and with the stripe reproduced as a perfectly collimated source
through a 2 mm slit rather than an area lamp.

On comb 6.5/0.08, Lambertian 0.01, 6 phases:

| axis | Cycles | Mitsuba 3.9.1 | difference |
|---|---|---|---|
| smear | 0.95781 | 0.94517 | **-1.3 %** |
| head-on peak | 0.20025 | 0.19997 | **-0.1 %** |

The pre-registered expectation held: the emitter models differ (Blender's lamp
has a 0.05 degree spread and a finite source; the Mitsuba stripe is a perfect
slit), so the absolute rms differs at +-40 degrees -- 0.750 against 0.549 -- but
it acts on the CONTROL as well and divides out of the ratio.

## Two defects the single-axis cross-check could not see

**The two codes were averaging over different windows.** `crosscheck_mitsuba`
trimmed 12 % off both axes; `blender_render` trims 20 % in x and 30 % in z,
harder in z because fins run past the panel there. Every cross-check number
published before this line was measured through mismatched windows. The error
grows with how anisotropic the structure is: a comb read -4.3 % at a 60 mm face
and -8.2 % at 100 mm. Matched, the comb reads **-6.0 %**.

**The winning design sits exactly where the two codes disagree most.** Sweeping
the blade thickness at 1024 spp, matched windows, Lambertian 0.01:

| plate_t | 0.05 mm | 0.2 mm | 0.5 mm | 1.0 mm | 2.0 mm |
|---|---|---|---|---|---|
| Mitsuba vs Cycles | **+26.9 %** | +8.7 % | -1.3 % | -6.1 % | -9.1 % |

Two effects superimposed. At thick blades the offset settles near -6 to -9 %,
the same figure the comb shows, so that part is a systematic common to the
geometry. On top of it sits a thin-sheet term that grows as the sheet thins and
flips the sign: at the 0.05 mm blade this study's three-axis winner is built
from, the two codes differ by **27 %**.

This was invisible because the cross-check only ever ran a comb and a cone --
both made of walls two orders of magnitude thicker than a blade. It is not yet
known which code is right. A 0.05 mm sheet in a 100 mm panel is a 2000:1 aspect
where ray-offset epsilons and thin-geometry handling differ between codes, which
is the first thing to test, and until that is settled **every blade number in
this study carries an unquantified 27 % systematic** that no amount of sampling
removes: the disagreement is flat from 256 to 4096 spp.

## Reproduce

    Blender --background --factory-startup --python scripts/validate_physics.py
    python3 scripts/crosscheck_analytic.py
    <venv>/bin/python scripts/crosscheck_mitsuba.py
    python3 scripts/audit_normal.py
    python3 scripts/audit_geometry.py
