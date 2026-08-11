# Continuation brief

Everything needed to pick this up without re-deriving it. Written at the point
where the extruded-cross-section families are exhausted and the next step is
full 3D geometry.

---

## 1. The problem, and the priority order

Hundreds of synchronised laser projectors converge in mid-air to form a
volumetric image, visible only because haze scatters a few percent of each
beam. Every beam then continues and terminates on a wall, which receives
essentially the full beam power and paints a sharp bright copy of the artwork
around it. The reference photo the user supplied shows the word "sup" formed in
air, dim, while the side walls carry razor-sharp legible copies of it.

The user's stated priority, in order:

1. **destroy the FORM** of what returns, so the wall reads as texture and not
   as a legible figure
2. reduce total reflected light

Beams cannot be blanked — the beam in flight *is* the artwork.

Panel envelope: 500 x 500 mm, depth 30–100 mm depending on variant.

---

## 2. Measurement chain — validated, do not rebuild

Cycles, `max_bounces = 128`, denoising off, clamping off, view transform
Standard, gamma 1.0. `scripts/blender_render.py` is the harness; everything
else calls into it.

**Primary metric — `hemi_view`.** Uniform world illumination (radiance 1.0)
with the CAMERA tilted to elevation θ. By Helmholtz reciprocity the radiance
leaving toward θ equals ρ_dh(θ), the total fraction reflected by a collimated
beam arriving from θ. This is an ABSOLUTE reflectance, not a ratio. It has no
delta-function glint, which is why it replaced the naive
collimated-source-plus-front-camera measurement (that gave ratios of 46,000 at
one angle and 1e-4 next door).

**Secondary — `angle`.** Sun at incidence θ, front camera: what an observer
straight ahead actually sees. Dominated by specular glints, so max/p99 matter
as much as the mean.

**Form — `scripts/form_mtf.py`.** A 2 mm collimated stripe (spread 0.05°), Z
profile of the return, averaged over 3 stripe positions; reports rms width,
core fraction (energy within the central 10 mm) and MTF at several periods.

Validation, in `scripts/validate.py` + `scripts/test_floor.py`:

| check | result |
|---|---|
| emission 1.0 / 0.5 plane | 1.000000 / 0.500000 |
| flat Lambertian ρ = 0.05 | 0.050001 |
| open box cavity f = 1/6 | 0.2356 vs 0.233 recorded previously |
| ρ = 0 panel | exactly 0 — **the measurement has no floor** |
| seeds 0–4 | spread 0.2% |
| samples 384 / 1536 / 6144 | already converged at 384 |

**Baseline discipline:** every result is a ratio against a flat plate of the
SAME coating rendered in the same frame, and the absolute value is that ratio
x 0.05. Report reflectance first, ratio second. A confound here produced a
wrong "4.5x brighter than a flat wall" claim once.

---

## 3. Design laws, measured

```
reflectance(head-on)  ≈  0.09 × (tip width / pitch) × ρ
```

Only the *ratio* tip/pitch matters, so a coarser pitch buys a blunter tip.
Verified across 24 combinations: (measured ÷ naive tip-area estimate) stays
between 0.75 and 1.5. **The head-on return is the exposed ridge tip and
essentially nothing else** — light that enters the groove does not come back.

```
reflectance ∝ ρ exactly
```

Coefficients 0.170 / 0.172 / 0.176 across a 10x reflectance range. Linear, not
ρ² or ρ³ — which is itself the proof that the visible return is a single
bounce.

```
aspect ratio A = depth / pitch:   A ≥ 2 holds ±40°,  A ≥ 6 holds every angle
```

Below A = 1 the ±40° figure triples. Bounce count ≈ 3.15 × A.

**Gloss roughness 0.30 is an interior optimum.** 0.15 leaves a specular lobe
narrow enough to aim at the observer (worst-angle return 6.2x a plain wall at
ρ=0.05); 0.50 approaches a diffuser and scatters straight back.

---

## 4. Three geometry families tried

**`profile2d.py` — angled slats over a hidden chamber.** Dead. A material-ID
render showed the front view was 97.8% slat and 0.0% chamber, so the entire
stage1:stage2 depth-ratio sweep moved results under 2%. Raising the hidden
chamber's reflectance 0.05 → 0.90 changed nothing to four decimals: diffuse
light inside cannot get back out past the black slats. Best: 0.0013 head-on but
0.069 at the worst angle, and the line came back as a line.

**`profile_scatter.py` — open deep troughs.** Dead for form. At retro-incidence
the observer and the beam are collinear, so whatever the beam hits first is
visible, and a single bounce can never displace a photon. core stayed 0.85–0.98
at normal incidence for every width and interior reflectance.

**`profile_ridge.py` — deep sharp V-grooves. CURRENT.** The wall-scale form of
a laser beam dump: only the ridge line is exposed head-on, everything else is
at grazing incidence. Grounded in beam-dump practice (cone in a ribbed
canister, back-reflection < 0.1%) and V-groove cavity theory.

**`geom3d.py` — irregular 3D cone array. IN PROGRESS, first non-extruded
family.** Cones built as interpenetrating closed solids on a backing slab; for
an opaque surface the union is the geometry, so no Voronoi or height field is
needed and the apex radius stays under exact control. Added
`blender_render.mesh_to_object` alongside `loops_to_object`; everything
downstream needed no change, as predicted.

**`profile_laby.py` — folded labyrinth channels.** Dead. Specular rays do not
follow a folded channel; they go straight and hit the outer wall of the fold.
Path length is only meaningful for rays already grazing along the channel.

**Hierarchical flank serration** (inside `profile_ridge.py`, `micro_pitch` /
`micro_depth`). Dead at this scale. Corrected measurement: no effect at ≤0.1 mm
teeth, actively worse at ≥0.3 mm. The mistake was making *serrations* when
nature makes *cavities* — at grazing incidence a sawtooth just deflects, a pit
still traps.

---

## 5. Current best

```
ridge V-grooves, depth 50 mm, mean pitch 13 mm (±25% irregular),
ridge tip 0.8 mm, coating ρ = 0.005 (0.5%, Musou-Black class),
gloss roughness 0.30
```

| | reflectance | ratio vs flat same-coating plate |
|---|---|---|
| head-on | 0.0264 % | 0.0053 |
| worst within ±40° | 0.0293 % | 0.0059 |
| worst over all angles | 0.2660 % | 0.0532 |

Why these three values: depth 50 beats every shallower depth on all three
metrics in 14 of 19 combinations (unconditional). Tip 0.8 is a
**manufacturability** choice, not optical — 0.4 gives 0.0149% but is exactly
one 0.4 mm nozzle width with no margin. Pitch 13 is a **hedge**, minimising the
product of head-on and worst-all, and that weighting is a choice, not a
measurement.

**Form is NOT destroyed by any of this.** The panel attenuates; the line comes
back as a line. Priority 1 remains unmet.

---

## 5b. What the 3D step has established so far

**A margin defect was found, and it voids every grazing number measured before
2026-08-11.** A camera tilted to θ looking at depth D travels D/tan(90−θ) in Z
before it reaches the valley floor — 5.7 D at θ = 80. Neither family generated
geometry that far past the measurement window, so the tilted view ran off the
tile and read world background instead of panel. It surfaced as an impossible
27% "reflectance" on the first 3D run (55× the coating's own reflectance).
Both `geom3d.py` and `profile_ridge.py` now take `margin_depths = 6.5`. This is
audit item A-4, and it is now fixed rather than open. **Any |θ| ≥ 50 figure in
a CSV written before this date is void; the head-on and ±40 figures are not
affected.**

**The tip law does NOT carry over to cones.** For a 1D ridge the head-on return
is the exposed tip and nothing else — verified across 24 combinations. A cone's
tip is a point, so its exposed fraction is πr²/cell = 0.343% against the
ridge's 2r/pitch = 6.15%, which predicts 0.0017% head-on. Measured: **0.0344%,
twenty times higher.** The flanks dominate, and the reason is geometric: a 2D
V-groove confines a ray to the cross-section plane where each bounce ratchets
it toward the apex, while on a 3D cone the ray can walk azimuthally around and
escape after fewer bounces. Cones trap worse per bounce than grooves.

**But cones are far more isotropic**, which was the point of going 3D:

| θ | 3D cone d50/p13/tip0.8 | 1D groove, same numbers |
|---|---|---|
| head-on | 0.0344% | 0.0264% |
| ±40° | **0.0054%** | 0.0293% |
| ±80° | 0.157% | 0.266% (old, void) |

Five times better off-axis, thirty percent worse head-on, and much flatter
overall — which is what the Gaboon viper's "no specular peak, gradual falloff"
looks like. The cone is worst head-on, because head-on is where the apex is
seen unforeshortened.

### Round 1, and the defect it hid

A second geometry defect turned up: the cone base radius was 1.15 x pitch/2
against a jitter of 0.30 x pitch, so two neighbours could drift far enough
apart that their bases no longer met and the backing slab showed through. It
presented as "regular arrays are 8x darker than jittered ones", which is not a
physical result -- it was gaps. `Cone3DParams.effective_overlap()` now enforces
`overlap >= 1 + 2 * jitter`.

**Everything measured in round 1 is inflated by that.** The same configuration
reads 0.0344% head-on with gaps and 0.0051% without -- a factor of 6.7. In
particular the round-1 conclusion that a 30 degree tilt buys a 5x directional
improvement is WITHDRAWN: it was measured against the broken baseline. Against
a gap-free one, tilt is worse head-on (0.0085 vs 0.0051) and 21x worse at
+/-40 (0.137 vs 0.0064). The bird-of-paradise directional bias does not
reproduce at this geometry and scale.

### Round 2, gaps closed — where the 3D family actually stands

| case | depth | pitch | jitter | head-on | ±40° | all |
|---|---|---|---|---|---|---|
| J_jit30 | 50 | 13 | 0.30 | 0.0051% | 0.0064% | 0.230% |
| J_d120_jit30 | 120 | 13 | 0.30 | **0.0045%** | **0.0048%** | 0.098% |
| **J_d80_p08** | 80 | 8 | 0.30 | 0.0068% | 0.0068% | **0.070%** |
| J_nojit | 50 | 13 | 0 | 0.0042% | 0.0050% | 0.101% |
| 1D groove, re-measured | 50 | 13 | — | 0.0268% | 0.0311% | 0.258% |

**The 3D cone array beats the 1D groove by four to six times on every metric.**
Aspect ratio is still the lever, and the tip is still not: shrinking the tip
16x moved head-on by 16%, against the 1D family where the tip was the entire
signal. That is the practical win — a cone can be blunt and deep instead of
sharp and shallow, which is the opposite of what a 0.4 mm nozzle struggles
with.

The cost of irregularity is now measured too: jitter 0 -> 0.30 costs 21% head-on
(0.0042 -> 0.0051) and 2.3x at grazing (0.101 -> 0.230). That is the price of
the no-periodic-array rule, and it is worth paying.

### Form — the first time both axes moved together

`scripts/cone3d_mtf.py`, same LSF harness, 300 mm panel so the window is
+/-90 mm and a wide smear is not clipped:

| θ | | 1D V-groove d50 | 3D cone d120 |
|---|---|---|---|
| −40° | core / MTF@20 / energy | 0.993 / 0.984 / 0.0327 | **0.112 / 0.063 / 0.00038** |
| 0° | core | 1.000 | 1.000 |
| +40° | core / MTF@20 / energy | 0.996 / 0.985 / 0.0313 | **0.172 / 0.116 / 0.00033** |

The groove keeps core at 0.99-1.00 at every angle — form completely intact.
The cone drops it to 0.11-0.17 off-normal AND is 86x dimmer at the same time.
Every earlier family traded one axis against the other; this is the first that
improves both. The mechanism is the azimuthal freedom that also makes cones
trap worse per bounce: a ray can walk around the cone, and where it exits is no
longer where it entered.

**θ = 0 is still core 1.000 for every geometry ever tried.** Observer and beam
collinear, first hit visible, one bounce, no displacement. That rule has not
been broken by any of the five families.

### What the cone family settled

**Depth is not the lever it looked like; the tip is, again — but only once it
is a large enough fraction of the cell.** The scale sweep held aspect ratio
fixed and shrank everything, expecting scale invariance since the tip had been
shown not to matter. It is not invariant, because the tip radius was pinned at
0.4 mm in every case: at pitch 20 that is 0.15% of the cell, at pitch 2.5 it is
9.3%. The measured 0.0484% at pitch 2.5 against a tip-area estimate of 0.047%
settles it. The full rule is

    reflectance  ~=  max( tip_area_fraction x rho ,  flank floor(A) )

so "the tip does not matter for cones" holds only while the first term is below
the second.

At depth 30, tip radius 0.4 -> 0.2 -> 0.1 mm gives 0.0083 -> 0.0046 -> 0.0037%.
**Tip radius is now fixed at 0.2 mm (0.4 mm across, one nozzle width)**, which
makes depth 30 equal to depth 50 with a 0.4 mm radius tip. A sharper tip buys
back 20 mm of wall.

Depth comparison at that tip, best pitch for each:

| depth | pitch | head-on | ±40° | all |
|---|---|---|---|---|
| 30 | 7.5 | 0.0046% | 0.0056% | 0.220% |
| 30 | 3.75 | — | — | 0.089% |
| 50 | 13 | 0.0047% | 0.0055% | 0.174% |
| 80 | 13 | 0.0044% | 0.0049% | 0.128% |

Pitch sets which end of the angle range wins: coarse is better head-on, fine is
better at grazing, and which to pick still depends on the rig's incidence
distribution.

**Bimodal cones — DEAD.** A finer, shorter array dropped into the valleys to
catch rays skimming the primary flanks. Measured: the all-angle figure is
*identical* to four decimals (0.2132%) in every variant, so the secondary array
contributes nothing at grazing — those rays never reach that deep. Meanwhile
its tips are fully exposed and cost 2x head-on (0.0083 -> 0.0164). Shrinking
just the secondary tips to 0.1 mm returns the head-on figure to baseline,
proving the entire effect was added tip area and nothing else.

**Tilt — WITHDRAWN**, see the round-1 note above.

### Printability, measured not assumed

The exported cone STL was a few hundred interpenetrating closed solids. It was
watertight (0 open edges, 0 non-manifold) but in several shells, and a slicer
using an even-odd fill rule would turn every overlap into a hole.

A boolean union got it to 4 shells, not 1. Rather than guess, the shells were
located: the cone mass spanned y −34.45..0 and the backing slab y −38..−35 —
**the slab was 0.5 mm clear of the deepest cone and touching nothing.** The
"−0.5 mm clearance" in the slab placement was itself the defect. The slab now
sits above the *shallowest* cone base, and height jitter is off for exports.

Exports are also **tileable with no border**. The centre field is made exactly
periodic over the module, so the tile can be cut at the boundary and the half
cone removed on the right is the half entering on the left; butting two modules
rebuilds whole cones. Verified on the exported mesh: the z faces match vertex
for vertex, and the x faces agree geometrically to a median of 5 nm and a worst
case of 0.9 µm — a two-hundredth of a printer layer. A flat border was rejected
outright: it would be the brightest feature on the panel.

Every export now prints `[UNION] open / nonmanifold / shells` and is only
shipped on `OK`.

### 3D images of everything

`scripts/shot3d.py` renders any family to `profiles/NNN_3d_<name>.png` and logs
a line to INDEX.md, so the numbered record now carries pictures of the dead ends
as well as the survivors. A failed design still has to be explained to someone,
and the picture is what makes that a sentence anyone can follow. Run it for
every new geometry, not only the good ones.

`scripts/cone3d_sweep.py` is the first real sweep: tip series (does head-on
fall as r²?), aspect ratio (do cones just need more depth per pitch?), pitch,
hex vs square, jitter on/off, and tilt 20/30° plus tilt jitter for the
bird-of-paradise directional bias. It re-measures the 1D reference rather than
quoting the old numbers, because of the margin fix above.

---

## 6. Audit findings — two fixed, two still open

An adversarial methodology audit (`Agent`, general-purpose) found:

- **FIXED:** a "66.7x glint at θ = −30" was tessellation, not physics. Six
  facets on the rounded tip put mirror normals at exactly ±15/45/75°;
  `scripts/test_tessellation.py` confirmed the peak tracks 180/n. All
  `arc_segments` are now 24. The conclusion was withdrawn.
- **OPEN:** no Fresnel in the material model, so grazing figures are optimistic
  by an unmeasured factor.
- **FIXED:** the panel was modelled with too little geometry past the
  measurement window, so tilted views ran off it and read background. See §5b.
  Genuine panel-to-panel tiling is still not modelled, but the window is now
  fully surrounded by geometry.
- **OPEN:** the LSF/MTF pipeline has real defects — |FFT| discards phase so MTF
  is translation-invariant by construction, and `fwhm_mm` collapses to one
  pixel on spiky profiles. The proposed fix is a full response matrix
  H(z_out; z_in) at ≥40 input positions, then synthesised bar-pattern contrast
  vs period and phase.

---

## 7. Literature already read

- **RP Photonics / beam dumps** — cone in a ribbed black canister; only the
  cone tip is head-on, everything else grazes; optimised traps < 0.1%.
- **V-groove cavity theory** (Frontiers in Physics 2022, ScienceDirect) —
  apparent absorptivity of a collapsing specular V approaches unity; strongly
  dependent on collimation angle; ~5 reflections reaches 1e-5.
- **Davis 2020, Current Biology** (deep-sea fish) — <0.5%; ellipsoidal
  melanosomes 400–800 nm, aspect 1.2–3, randomly packed in a *continuous* layer;
  scattering and absorption from the same particles.
- **Davis 2020, Nature Communications** (`reference/s41467-020-15033-1.pdf`) —
  butterfly scales 0.06–0.4% in a 2.5 µm layer; ridges + trabeculae + holes;
  removing either raises reflectance 3–16x; structure works even when
  non-absorbing; principle is "sparse material, high surface area, strong
  absorption"; irregular hole shape helps at non-normal incidence.
- **Mouchet 2024, arXiv 2404.18169** (`reference/2404.18169v1.pdf`), biology
  sections pp. 1–13 read in detail. Key items in §8 below. The rest (pp. 14–31)
  is fabrication for PV and radiative cooling.
- `reference/2601.05094v1.pdf` — **not yet read.**

---

## 8. What Mouchet 2024 adds, and why it points at 3D

**Bird of paradise feathers, §2.3.** Absorption to 99.95%, directional
reflectance 0.05–0.31%. Barbules curve up and tilt ~30° from the normal toward
the feather's distal tip, forming cavities **5–30 µm wide and 200–400 µm deep**
— aspect ratio **10–40**, against our 3.8. And: *"the super-black effect is most
pronounced when looked from the distal direction… the cavities present a
directional reflectance bias."* **The cavities are deliberately tilted toward
one observer.** We have an audience direction and a laser direction and have
been weighting all angles equally.

**Gaboon viper, §2.5.** Densely packed leaf-like microstructures with
nanoridges. An Au-Pd coating *preserves* the black and lowers reflectance
further — proof the mechanism is structural. They validated it with *Lambertian
symmetric V-shaped cavities*, the same model we use. Critically, the black
scales show **no specular peak at all** and a gradual falloff with emerging
angle, attributed to "a more isotropic arrangement of scale structure". Our
extruded 1D groove has inherent angular anisotropy; theirs does not.

**Maratus jumping spiders, §2.4.** 0.35–0.44%. Microlens arrays over striated
cuticle over a melanin layer — light is **focused into** the absorber rather
than only trapped. A mechanism we have never tried.

**Rosalia alpina, §2.2.** Inclined "tent-shaped" scales touching neighbours at
the tips — a nearly closed cell with a small entrance. Requires undercuts;
impossible extruded, fine printed.

**Euproctaetia scarab, §2.2.** Ellipsoidal, **randomly located** micropillars;
absorptance 99.5%, reflectance 0.1%.

Two of these (tilt, aspect ratio) are parameter changes on the existing family.
Two (isotropy, undercut cells) need geometry the current pipeline cannot build.

---

## 9. Next steps, in the order agreed

**A. Tilt sweep.** `RidgeParams.tilt_deg` and `tilt_jitter` already exist and
have never been swept. Bird-of-paradise says tilting biases the darkness toward
one direction, which is exactly what a fixed audience wants.

**B. Aspect ratio to 10+.** Parameter change only. A = 6.2 already measured
0.217 worst-all against 0.266 at A = 3.8.

**C. 3D geometry — the real extension.** Everything so far is a Y-Z
cross-section extruded along X, so every design is anisotropic by construction.
Going 3D opens irregular pyramid arrays, randomly placed pillars, 2D cavity
lattices, and undercut tent cells.

*Implementation sketch:* `blender_render.build_scene` currently dispatches on
`cfg["family"]` to a module returning a `CrossSection` of 2D loops, which
`loops_to_object` extrudes along X. Add a family that returns a mesh directly
(verts + faces) and a `mesh_to_object` alongside `loops_to_object`. Everything
downstream — camera, `hemi_view`, reciprocity, windows, LSF/MTF, sweeps,
reporting — is dimension-agnostic and needs no change. The measurement windows
already use Blender's own projection.

*Watch for:* mesh size (a 500 mm panel of 4 mm cells is 125x125 = 15,625 cells,
so build a smaller tile and instance it, or measure a 100 mm coupon and state
that); and the `arc_segments`-style tessellation trap — any rounded feature
needs enough facets that fake mirror normals do not manufacture a glint.

---

## 10. Tooling map

| file | does |
|---|---|
| `blender_render.py` | the harness: materials, mesh build, camera, modes, windows, `run()` |
| `profile2d.py` | family 1, slats (dead) |
| `profile_scatter.py` | family 2, troughs (dead) |
| `profile_ridge.py` | family 3, V-grooves (current) |
| `profile_laby.py` | family 4, folded channels (dead) |
| `geom3d.py` | family 5, 3D cone array (current work) |
| `cone3d_sweep.py` | first 3D sweep, with re-measured 1D references |
| `cone_scale.py` | aspect-ratio-fixed size sweep; found the tip pinning |
| `cone_bimodal.py` | two cone sizes (dead) plus the tip series at depth 30 |
| `cone3d_mtf.py` | form measurement for the 3D family |
| `export_cone.py` | STL: union, trim to face, tileable, 100 x 100 only |
| `shot3d.py` | numbered 3D render of any family, into profiles/ |
| `plot_cone_vs_ridge.py` | the cone-vs-groove comparison sheet |
| `raytrace2d.py` | independent 2D specular tracer; bounce count and Z displacement |
| `validate.py`, `test_floor.py`, `test_tessellation.py` | measurement-chain checks |
| `sweep.py`, `ridge_sweep.py`, `ridge_best.py`, `ridge_micro.py`, `fdm_optimum.py`, `pitch_tip_grid.py` | sweeps |
| `form_mtf.py`, `scatter_mtf.py`, `ridge_mtf.py` | form measurement |
| `plot_family.py`, `plot_profile.py`, `plot_candidate.py`, `plot_pitch_choice.py` | numbered profile drawings |
| `make_report.py` | dated report + snapshot; run on "보고서 써" |
| `export_stl.py`, `export_fdm.py` | STL, oriented for printing |
| `analyze.py`, `contact_sheet.py`, `shape_sheet.py`, `dump_crops.py` | analysis and comparison sheets |

Renders are gitignored (5.7 GB, regenerable). Every extracted number is in
`results/*.csv`.

---

## 11. Working conventions

- Draw the geometry (cross-section + 2D ray trace) before rendering it; both
  caught bugs the Cycles numbers hid.
- Never quote a number without naming its baseline.
- Reflectance is the headline; the vs-flat ratio is secondary.
- Verify with debug output — ID renders, ρ=0 controls, seed sweeps,
  tessellation sweeps — never with reasoning alone.
- Profile drawings are numbered `profiles/NNN_*.png` and never overwritten;
  dead ends stay next to survivors. `profiles/INDEX.md` is the log.
- Run an adversarial methodology audit periodically.
- Withdraw a broken conclusion plainly and move on.
- Search prior art before designing; do not let a guess be the starting point.
- Keep this file current as the work moves, not only at handoff.
- Render a 3D view of every geometry tried, successes and failures alike, and
  number it into profiles/ — the client sees pictures, not CSVs.
- STL is 100 x 100 mm only, single shell, tileable, no flat border. Verify
  open edges / non-manifold / shell count on the exported file before shipping.
- When a mesh check fails, locate the defect (component bounds, edge
  positions) before changing anything. The slab-clearance bug was found that
  way in one measurement after two wrong guesses.

## 2026-08-11 — the fair fight (IMPORTANT, supersedes the 5.2x claim)

`scripts/fairfight.py` -> `results/sweep_fairfight.csv`. The four-design
comparison was NOT tip-matched: groove tip 0.8 mm line at pitch 13 = 6.2%
exposed, cone tip r0.2 point per cell = 0.26%. 24x, inside families whose
reflectance is dominated by the tip. Matched on depth, pitch AND tip:

    1D V-groove d30/p7.5/tip0.2   0.0148 / 0.0153 / 0.2553 %
    3D cone     d30/p7.5/r0.2     0.0051 / 0.0056 / 0.2149 %   -> 2.9x, not 5.2x

The remaining 1.8x was tip and geometry the groove could have had too.
Best 1D at any depth: d50/p13/tip0.2 = 0.0104% head-on.

CORRECTION: "the tip does not matter for cones" (round 1, 16x tip -> 16%
change) came from the base-gap geometry and is WRONG. At d30/p7.5, cone tip
r0.2 -> r0.8 costs 4.6x (0.0051 -> 0.0237%). Scales like r, not r^2 -> the
return is the flank near the tip, not the tip disc.

The cone's remaining outright win is FORM (priority 1): core 0.11 vs 0.99 at
-40 deg. Nothing in the fair fight touches that.

Renders 081-084 are the geometry actually measured/exported (081/082 the
tip-0.2 grooves, 083/084 the cones exactly as export_cone.py writes the STL,
tileable, backing 3, depth_jitter 0). Report: report/2026-08-11/*_compare.png
via scripts/report_compare.py.
