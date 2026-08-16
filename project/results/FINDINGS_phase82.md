# Phase 8.2 — the tilted AR window, first measurement

2026-08-16. Data: `sweep_phase82.csv` (29 rows), `form_phase82.json`.
Predictions pre-registered in `scripts/sweep_phase82.py`; the three rows
the 32-spp geometry preview had already seen (R 1 %, θ 0/±40) are marked
POSTDICTION there and here.

## The object

2 mm glass, R per surface CONSTANT (declared model; the real AR angle
curve is the physical coupon's job), hinged at its TOP edge in the wall
plane, bottom swung 25° back over a 90-deep void with idealised black
interior (ρ 0). Glass faces DOWN: beam from elevation +θ reflects to
−(θ+50°).

**Orientation was pinned by render, not intuition.** The hinge sign was
derived by hand twice with opposite answers; a 32-spp preview settled
it: the leaning-mirror orientation (bottom-back) throws 2R back into
the room near eye level (measured ratio 0.40 at +40°), the hopper
(top-hinged) sends every above-horizon beam downward. The hopper is the
build. Bonus: the exposed face points down, shedding dust; the
up-facing side is sealed inside the void.

## Grades

| claim | prediction | measured | grade |
|---|---|---|---|
| P1 R-scaling, θ0, R 0.5 % | 0.92 ± 0.09 % | 0.923 % | HELD |
| P1 R-scaling, θ0, R 2 % | 3.67 ± 0.37 % | 3.602 % | HELD |
| (θ0, R 1 %) | postdiction 1.84 | 1.850 % | consistent |
| P2 θ +20 | 0.86 ± 0.30 % | 0.143 % | MISS, good direction ×6 |
| P2 θ +50 / +70 | < 0.05 % | 0.002 % / 0.000 % | HELD |
| P2 θ −20 | 1.9 ± 0.3 % | 2.006 % | HELD |
| P2 θ −50 / −70 | 1.6–2.0 % | 1.986 / 1.973 % | HELD (measured in the follow-up run, same day) |
| P3 danger spike at −50 | ratio > 100 | **34,176** | HELD |
| P3 off-spike (\|θ+50\| ≥ 10°) | ratio < 0.5 | ≤ 0.0004 | HELD |
| P3 shoulders −45/−55 | unpredicted | ratio 0.0069 / 0.0067 | recorded |
| P4 system θ0 | 2.0 ± 0.5 % | 1.892 % | HELD |
| P4 system θ +20 | 1.0 ± 0.4 % | 0.195 % | MISS, good direction ×5 |
| P4 system θ +40 | 0.17 ± 0.08 % | 0.031 % | MISS, good direction ×5 |
| P5 head-on (beam 7.5 mm) | < 0.005 | **0.0000023** | HELD ×2000 |
| P5 smear (beam 7.5 mm) | not gradeable, pre-registered | NaN (zero return at ±40) | as registered |

Anchor: P5_j00 d100@−40 = 0.13390 % vs book 0.13392 % — agree.

## The two lessons the misses bought

1. **The +20 clip model was too coarse** (P2): the aperture-clip
   estimate lit 43 % of the window; the render says 7 %. More of the
   mirror path dies inside the box than the single-edge model allows.
   Every miss is in the safe direction.
2. **The void SHADES its own trap** (P4 +20/+40): the pyramid trap at
   the back of the box reads 0.031 % at +40 — 5.7× darker than the same
   pyramid field as an open wall (0.177 %) — because the box mouth
   restricts its illumination exactly as it restricts a deployed beam.

## Three axes against the standing champion (beam width labeled)

| design | 반사 총량 worst-ρ | 모양 뭉개기 smear | 정면 반짝임 head-on |
|---|---|---|---|
| pyramid wall p4/d20/t0.1 | 0.177 % (φ0, mats×5θ) | 1.42 (beam 7 mm) | 0.0400 (beam 7/10 mm) |
| AR window assembly | 2.006 % worst over measured θ (−20); but 0.001–0.14 % for every θ ≥ +20 | 측정 무효 — ±40° return is zero, rms undefined (beam 7.5 mm) | **0.0000023** (beam 7.5 mm) |
| AR window + pyramid trap (system) | 1.892 % (θ0) / 0.195 (θ+20) / 0.031 (θ+40) | — same invalidity | — inherits the window's |

The window LOSES the classic total axis 11× and WINS head-on 17,000×.
Neither number alone decides anything: the total is direction-blind and
this object is all direction. hemi_view with a uniform white world is
the WORST CASE for the level observer — in a deployed room the mirrored
scene at −50° is the absorbing trough (≈ 0.18 % scene), so a level
viewer's actual return is ≈ 2R × 0.0018 ≈ 0.004 % [derived, not
rendered — 8.3's direction-resolved metric renders exactly this].

## Where the residual physically lands (traced figure, raypaths.png)

- beam 0° → down 50° → absorbing trough at the wall base (pyramid
  tile laid flat) — a REAL part the install now owes. Width rule,
  corrected by the audit: reach = (window-top height above floor)
  / tan 50° ≈ **1.2 × window height** (the first draft said 0.85×,
  measured from the wrong edge).
- beam +40° → straight down → dies inside the box.
- a level viewer's mirror direction needs a beam from 50° below the
  horizon: the floor. Single, predicted, razor-thin danger cone
  (±5° shoulders are already at 0.7 % of a gray wall).

## Audit (independent agent, same day)

An audit agent recomputed the rotation, the reflection table, the
winding, and the figure. Outcomes:

- Geometry and reflection math confirmed independently (hopper normal
  (0, cos25°, −sin25°); reflection law −(θ+50°) exact).
- **Winding**: the slab's six faces mixed 3 inward / 3 outward. Fixed
  to uniform outward and re-rendered A/B: values identical to every
  digit (0.0184957 / 1.0177e-05 / 0.019957 at θ 0/+40/−40) — the
  Transparent+Glossy mix is two-sided symmetric, so no published
  number moves. Fix kept for hygiene (the 49 % winding swing in the
  project's history was a one-sided coating, not this material).
- **P2 −50/−70 gap**: predictions existed with no measurement; closed
  the same day (1.986 / 1.973 %, HELD) and the thetas are now in the
  sweep script.
- **Figure**: the beam-0 residual had been drawn from a point whose
  exit is blocked by the sill (one of the ~8 % that die inside); redrawn
  from a clearing point, and the trough width label corrected to 1.2×.
- Unpredicted-but-measured rows (R 0.5/2 % at θ +20/+40) stay in the
  CSV unbanded; they follow the same mirror-shadow pattern as R 1 %.

## Harness-audit note (2026-08-17, core-harness audit)

The measurement window sits on the wall plane; at POSITIVE theta the
receding plate covers a shrinking fraction of it (tilt 25: full to
+29 deg, 0.65 at +40, none past +54). The +40/+50 "trap seen through
the glass" rows are therefore DILUTED by the black void behind the
uncovered strip — the true per-aperture through-glass signal is up to
~3x the printed row. The direction is favorable (the printed numbers
overstate nothing a viewer would see; the window samples what a viewer
of the wall aperture samples), and every negative-theta and danger-scan
claim has full coverage. Recorded, not re-run.

## Model limits (named, not hidden)

- R constant over angle: real AR rises toward grazing → coupon.
- Void interior ρ 0: idealised; real interior needs Musou or tile.
- Uniform-world hemi_view overstates the level-observer return vs a
  real dark trough (factor ~500 by the derivation above).
- Glass-surface dust scatter: NOT simulatable, still the deciding term.

## Next

8.3: direction-resolved audience-zone metric (render the room, not the
hemisphere). Physical queue += AR-coated coupon: R(θ) curve + a week of
floor dust.
