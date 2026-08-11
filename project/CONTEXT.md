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

## 6. Audit findings — one fixed, three still open

An adversarial methodology audit (`Agent`, general-purpose) found:

- **FIXED:** a "66.7x glint at θ = −30" was tessellation, not physics. Six
  facets on the rounded tip put mirror normals at exactly ±15/45/75°;
  `scripts/test_tessellation.py` confirmed the peak tracks 180/n. All
  `arc_segments` are now 24. The conclusion was withdrawn.
- **OPEN:** no Fresnel in the material model, so grazing figures are optimistic
  by an unmeasured factor.
- **OPEN:** the panel is modelled in isolation with free top/bottom edges; it
  will be installed tiled, which changes the |θ| ≥ 50 arm.
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
