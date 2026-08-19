# Phase 10 probes — reroute-not-absorb: first two ideas measured (2026-08-19)

Question: can the beam be ROUTED to a dump instead of absorbed at the wall?
Two candidates probed end-to-end in one session; predictions were registered
in each script's docstring before rendering.

## Probe A — mirror-walled funnel pyramid (`probe_funnel.py`)

p4/d22/t0.4 field, specular walls, musou dump band in the valley bottom.
Instrument: the standard hemi_view rig; control read 0.0500 in all 15 rows.

| config                          | th0     | ±20     | ±40 (worst) |
|---------------------------------|---------|---------|---------|
| all-mirror rho 0.90             | 14.0 %  | 17.6 %  | 23.8 %  |
| mirror walls + 3 mm musou dump  | 0.90 %  | 9.6 %   | 16.7 %  |
| walls at rho 0.95               | 0.95 %  | 20.5 %  | 29.3 %  |

P2 predicted 0.3-0.8 % worst-theta and missed by 20-50x at oblique angles:
a funnel only funnels light that arrives along its axis; oblique light
mirror-exits after 1-2 wall bounces (the one-bounce law again). Shinier
walls make it WORSE. **VERDICT: dead as a wall.** Recorded alive for
normal-incidence-only zones: th0 = 0.90 % with paint on ~25 % of the area.

## Probe B — Fresnel wedge plate (`probe_fresnel.py`)

Clear plate, back-face prism sawtooth, transmitted beam bends downward.
Instrument: phase-8-style audience matrix (sun {0,20,40} x observer
{0,-5,-10,-20}), panel-window mean vs flat Musou in the identical rig.
Surroundings idealised black (plate-only paths), floor 250 mm below sill
(a floor AT sill height occludes every below-horizon sightline -- refound
phase 8.3's lesson the hard way; first run voided).

- FLAT musou baseline: 0.0006-0.029 across cells (rig sane).
- F0 vertical plate: mirror cells blaze -- (sun0,obs0) 678, (sun20,obs-20)
  652 = ~25,000x flat musou. As predicted: **vertical fails.**
- F15, same plate tilted only 15 deg: **all 12 audience cells 0.000000.**
  Every specular branch folds below -20 deg. The 35-deg hopper's audience
  performance at less than half the projection.
- G35 plain glass (phase-8 geometry) anchor: all zero. Rig confirmed.

Prism-angle law found on the way: acrylic's TIR limit is 42.2 deg; A=40
prisms sit at the cliff and splatter half the light internally (seen as
saturated forward glare in the grey-walled routing render). A=30 (net
downward deviation ~16 deg at tilt 15) behaves. **Spec prisms at <= 30 deg.**

## Open before F15 can be trusted as a device

1. SYSTEM audience numbers with a real musou trough interior (not the
   idealised black). Caveat discovered: Cycles undersamples light that
   reaches a diffuse interior THROUGH a refracting plate (classic missing
   caustics), so the naive render is non-conservative. Needs a two-step
   instrument: measure interior irradiance with the plate replaced by its
   analytic transmission, then propagate.
2. Transmission efficiency / dump load budget.
3. phi behaviour (prism grooves are 1D -- expect azimuth structure).

## Probe C — 2D wedges and the azimuth question (`probe_fresnel2d.py`)

User's question (2026-08-19): the 35 deg window chopped into prisms IS a
Fresnel plate -- so make the grooves 2D and serve every azimuth. Four plates
(1D horizontal, 1D vertical, 2D pyramid wedges, 2D hip cells), all acrylic
n=1.49, prism 30 deg, tilt 15 deg, measured over the audience matrix at
phi 0/45/90 x theta {0,+-20,+-40} x observer {0,-10,-20} = 45 cells each.

**All four returned the SAME audience number, to six digits, in the same
cell.** That is the finding, not a bug: the audience-facing branch is the
specular reflection of the FLAT FRONT FACE, which is identical in all four
plates. No back-face groove pattern can move it. Predictions P1/P2/P3
(grooves control azimuth leakage) are all WRONG; P4 holds but for the wrong
reason. The grooves steer only the TRANSMITTED light inside the trap.

Corollary: the plate is azimuth-blind on the audience axis. 1D grooves are
therefore acceptable there, and the 2D question is really about where the
transmitted beam lands inside the trap (dump placement), not about safety.

## Probe D — the tilt law (`probe_tiltsweep.py`)

Sweeping tilt with the hip plate, 20 audience cells each:

| tilt | hot cells (> 1e-6) | which |
|------|--------------------|-------|
| 15 deg | 2/20 | (sun -20, obs -10), (sun 0, obs -30) |
| 25 deg | 0/20 | -- |
| 35 deg | 0/20 | -- |

T4 held exactly: the mirror branch lands at **obs = -(sun + 2 x tilt)**.
15 deg puts it at -30 for a level beam, i.e. inside a seated audience's
sightline; 25 deg pushes it to -50, outside. **Minimum tilt 25 deg**, and
phase 8's 35 deg keeps margin for beams arriving from below the horizon
(floor bounces).

So the thin-plate dream survives, at 25 deg rather than 15: projection depth
for a 733 mm window drops from 420 mm (35 deg) to 310 mm (25 deg), a 26 %
saving, with the whole audience matrix still exactly zero.

### Still open (unchanged from probes A-B)
Interior dump load and trap-mouth escape need the two-step instrument;
Cycles undersamples diffuse light reached through a refracting plate.

## Probe E — splitting the window pane (`probe_louvre.py`)

User's question (2026-08-19): one 733 mm sheet is awkward; can it be several
small panes? The 10.3 mirror law depends on tilt alone, so N panes at one
tilt should be optically identical. Audience matrix, 12 cells each
(sun {0,+20,+40,-20} x observer {0,-10,-20}), tilt 25, acrylic n=1.49.

| build | worst | hot cells |
|-------|-------|-----------|
| one pane, edges hidden | **0.000000** | 0/12 |
| one pane + blacked edges | 0.000000 | 0/12 |
| 4 louvres, blacked cut edges | **0.009** | 12/12 (all faint) |
| 4 louvres, bright frame bars (rho 0.5) | 0.10 | 12/12 |
| 4 louvres, RAW cut edges | **116** | 2/12 |

P1 (splitting is free) REFUTED; P2 (gaps do not leak) REFUTED; P3 (bright
frames light up) HELD.

**Mechanism, seen in the render, not deduced:** the leak appears as bright
horizontal LINES exactly at the pane cut edges. Light entering at a steep
angle is trapped inside the pane by TIR, runs along it and exits the cut
end -- the pane is a light pipe. One big pane hides both its edges (top
under the lip, bottom in the trough); four panes add six edges with nowhere
to hide. Blacking the cut faces drops the worst value 12 000x, to 0.009.

**Build rules bought here:** (1) every cut edge must be blacked; (2) frames
must be black and recessed -- a bright frame lights every audience cell
evenly, which is worse than an edge that flares at particular angles;
(3) prefer left-right splits (vertical joints hide behind the frame);
the stacked-louvre form saves the most depth (310 mm -> 77 mm) but exposes
the most edges. 0.009 assumes an ideal black edge; real paint will read
somewhat brighter.

Figure: `results/fig_split_panes.png` (`scripts/fig_split_panes.py`).
Written into both phase 8 reports as section 8.6.
