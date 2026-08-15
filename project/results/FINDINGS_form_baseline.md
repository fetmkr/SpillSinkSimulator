# 2026-08-12 late — the form metric's baseline was wrong, and roughness is a 332x lever

**Status: measured, reproduced two ways, not yet in any report.**

## How this surfaced

`form_buildable.py` returned `peak_ratio` **greater than 1** at theta = 0 for
the first two designs — 1.45 and 1.64 — meaning the panel's brightest point is
*brighter* than a plain matte black wall, on designs that are 25x darker
hemispherically (rho_dh 0.20% against the control's 5%).

`metrics/01_rho_dh.md` warns about exactly this configuration: shooting a
collimated beam and photographing the return "puts a delta-function glint in the
frame", and an early version of this project reported a ratio of 46,000 for that
reason. So it was treated as a suspected artifact and chased before being
reported.

## What it was NOT

**Not the stripe lamp being imaged.** Rendering the same frame with the lamp's
`visible_camera` on and off gives results identical to six decimal places.

**Not `recentre()` truncating or misaligning the profile.** Computing the peak
ratio from the raw z-profiles and from the recentred ones gives the *same*
number to four decimals (1.3360 both ways), and the profile is 149 rows against
a 361-sample window, so nothing is clipped:

    theta  +0   RAW      panel 0.016109 @row 71   ctrl 0.012058 @row 77   1.3360
                RECENTRE panel 0.016109           ctrl 0.012058           1.3360
    theta -40   RAW      panel 0.000043           ctrl 0.009237           0.0046

**Not a first spot-check that said 0.89.** That check averaged over raw x-ranges
instead of the inset measurement windows and took a 5-row band mean rather than
the profile peak. It was measuring a different quantity and it was wrong.

## What it is

A flat plate of the SAME COATING, no structure at all, in the same frame:

| theta = 0, peak vs the 0.05 matte black wall | ratio |
|---|---|
| **flat plate of the coating** | **1.644** |
| structured panel (nested cell, pitch 11, depth 50) | 1.336 |
| 0.05 matte black wall | 1.000 |

**The flat plate is brighter than the structured panel.** The panel improves on
its own coating by 1.23x; both are brighter than plain black paint at normal
incidence. At theta = 0 the stripe and the camera are collinear, so the
coating's specular lobe returns straight to the observer — and that is a
property of the coating, not something the geometry created.

### Consequence 1 — the baseline was wrong

`metrics/01` states the rule: a ratio must name its baseline, and the meaningful
one is **a flat plate of the same coating**. `metrics/04` uses the 0.05 diffuse
wall instead. Against the correct baseline the panel reads **0.81** at theta = 0
(1.336 / 1.644), not 1.34 — an improvement, not a failure. The same numbers,
read against the baseline the project already mandates elsewhere, invert the
conclusion. **Metric 04 needs the flat-coating reference added before any of its
numbers are quoted.**

### Consequence 2 — `spec_roughness` is a 332x lever on form, and it is pinned

Same experiment, coating roughness varied, nothing else changed:

| `spec_roughness` | theta = 0 peak vs the 0.05 wall |
|---|---|
| 0.10 | **119.92** |
| **0.30 (used everywhere in this project)** | **1.644** |
| 0.50 | 0.361 |

**332x between 0.10 and 0.50.** The value 0.30 is pinned in every config file in
the project on the strength of one statement — that it is an interior optimum
for *rho_dh* (CONTEXT.md: 0.15 leaves a lobe narrow enough to aim at the
observer, 0.50 approaches a diffuser). **That justification is about total
reflectance. It has never been examined against the form metric**, which is the
project's stated first priority and which this measurement shows is far more
sensitive to it.

## Where this leaves the project

Each stated priority is now dominated by a different unmeasured coating
parameter, and neither is constrained by the flat-plate rho_dh(theta) curve the
material model is fitted to:

| priority | dominant unmeasured parameter | measured swing |
|---|---|---|
| 2 — reduce total reflected light | coating **diffuse fraction** | **41x**, with rank inversion (metrics/01) |
| 1 — destroy the form | coating **specular roughness** | **332x** on theta = 0 peak |

Against that, the entire nine-topology geometry search spans **1.6x** at matched
process (results/sweep_buildable.csv). The geometry is not what decides this
panel; the coating is, twice over, along two different axes.

## What to do

1. **Add a flat plate of the same coating to `form_buildable.py`** as a second
   reference, and report peak against both. One extra render per case.
2. **Sweep `spec_roughness`** on the form metric the way the diffuse fraction is
   swept on rho_dh — at minimum 0.10 / 0.20 / 0.30 / 0.40 / 0.50, on two or
   three designs. It is a bigger lever than any geometry choice made so far.
3. Do not quote any theta = 0 peak figure until 1 is done.
4. `results/PEER_REVIEW.md` objection 5 — "the figure of merit does not measure
   the stated first priority" — is now sharper than the reviewer put it: the
   form metric exists, and its baseline was wrong.

## Reproduce

    /tmp/peakchk.py   raw vs recentred peak, one design, theta 0 and -40
    /tmp/flatchk.py   flat coating plate at roughness 0.10 / 0.30 / 0.50

Both are throwaway scripts; the checks they perform should move into
`scripts/` before this is written up.
