# Continuation brief

Everything needed to pick this up without re-deriving it. Written at the point
where the extruded-cross-section families are exhausted and the next step is
full 3D geometry.

---

## 2026-08-20 — 측정 장비 감사: 결함 9개, 그리고 축마다 다른 측정 조건

전체 기록: `results/FINDINGS_rig_audit_2026_08_20.md`

계기는 사용자가 돌린 간격 100 / 깊이 500 보고서가 모양 뭉개기 15.46 을 낸 것.
그 숫자가 진짜인지 쫓다가 설계가 아니라 장비가 드러났습니다.

**결함 9개, 8개 수정.** 여섯 개가 같은 실수입니다 — **길이를 개수로 적은 것**.
개수는 시료가 커져도 그대로라, 그것이 나타내는 실제 길이가 시료를 따라 변합니다.
측정 창(시료의 40%), 화면 픽셀(1400 고정), 화면 세로 비율(0.443 고정),
프로파일 배열(361칸), 제가 새로 넣은 픽셀 상한(6000), Mitsuba 쪽 상수 복사본.

**축마다 조건이 다릅니다.** 하나의 측정으로 셋을 발표하면 최소 하나가 틀린 조건입니다.

| 축 | 각도 | 밀도 | 시료 | 창 |
|---|---|---|---|---|
| 반사 총량 | 0/±40 | 0.215 mm/px | 판 전체, 칸 25개 이상 | 가장자리 4픽셀 |
| 모양 뭉개기 | ±40 | 0.215 (둔감) | 판 전체 | 수렴까지 |
| 정면 반짝임 | **0** | **최소피처÷4** | **칸 10개 조각** | 조각 전체 |

**바뀐 숫자.** 발주 사양 정면 반짝임 0.173 → 0.189. 연구 표준 0.040 → 0.0677.
팁을 0.1 에서 0.4 로 푼 대가가 4.3배가 아니라 **2.8배**. 발주 결정에 유리한 쪽.
Phase 5.5 의 굵은 간격 판정은 뒤집혔습니다 (1.272 → 24.77).

**새 축.** 되돌아온 줄이 `0.59 × 깊이 × tan(입사각)` 만큼 옆으로 밀립니다.
적합도 0.9982, 간격과 무관. 지금까지 아무도 안 잰 값입니다.

**흰 용광로 시험 통과.** 반사율 1 공동이 512번 튕김에서 0.999906. 렌더러는
에너지를 잃지 않습니다. 기록에 실패로 남아 있던 0.673 은 튕김 부족이었음이 증명됐습니다.

**도구.** Mitsuba 부활 (venv 가 /tmp 에 있어 macOS 청소에 지워졌음, 홈으로 이전).
Radiance 6.0.2 설치 (`~/.spillsink/radiance`) — 실물 고니오포토미터와 대조 검증된
유일한 도구. 아직 연결 안 함.

**미해결.** 칸 개수(50칸에서도 안 멈춤), Cycles 대 Mitsuba 피라미드 +27%,
순위표 전체 재측정, 벌집 재측정, **실측 여전히 0건**.


## 0. STATE AS OF 2026-08-17 — the simulation study is CLOSED. Read this first.

Phases 5-9 ran to completion after this brief was first written. Everything
below section 1 remains valid history; this section is the current truth.

**The product.** Pyramid field, pitch 4 / depth 20 / tip <= 0.15 mm, 22 mm
panel, valleys sharp (< R0.1). Universal cut-anywhere tile exported
(`export/pyr_universal_p4_d20_t010_200x200.stl`, manifold-verified). Its own
measured envelope: total 0.177 % (phi 0) / 0.295 % (worst over theta <= 70 x
phi x roughness 0.30); smear 1.42 at beam 7 mm; head-on 0.040 (beam 7/10 mm);
tip ladder 0.1/0.2/0.4 -> 0.032/0.052/0.107; azimuth hole x1.4 at phi 30;
grazing 50-70 deg barely degrades (0.184-0.198 vs flat 1.44-4.27).

**Manufacturing (phase 9).** Mold casting is the default: SLA positive master
-> platinum silicone mold (peeled off, a consumable) -> soft urethane; foamed
PU for the 100-panel run; row-strip assembly measured free to +-0.2 mm.
Injection rejected (valley radius + demolding). Extrusion rejected as default
(a tip LINE pays 40x the flat land of a tip POINT: head-on 0.894 vs 0.040).
Two-tier paint: Musou only on audience-critical zones (paint area is x10 the
wall area; full coverage would cost 50-100M KRW); bare black urethane
elsewhere obeys total = 0.18 x rho(material) (measured linear; the same 0.18
reproduces the Musou panel from its ~1 % coating). Tops-only paint fails
(totals are top-weighted, head-on is area/bottom-weighted -- the axes invert
depth). Flocking fails in any Lambertian model (vertical AND tilted fibers);
one physical coupon could still surprise. Corners need nothing: two panels
butting at 90 deg read 0.84x of the open wall (mutual shading).

**The window (phase 8).** Museum-glass hopper, tilt 35, rim lip over the top
quarter, pyramid trap behind: level observer 0.000 %, danger scan empty
-75..+70, system 0.005-0.038 % at every deployment angle, head-on 1.5e-6 at
beam 7.5 mm. Mounting rule became a floor rule: ~1 m of dark floor in front,
no bright props in the strip. Remaining gates are physical: vendor R(35 deg)
curve and the one-week dust coupon.

**Verification state.** Every sweep pre-registered predictions and passed the
8-check gate; anchors reproduce to all digits everywhere (P5_j00 d100@-40 =
0.13392 %); seed noise measured under +-0.5 % relative (phase 9.s); the
composed-mesh double-floor artifact proven optically inert (9.v, 0.01 %
worst); two independent audit agents re-derived the harness math and traced
every FINDINGS number to its CSV (no blockers; small fixes applied and
logged). Exports repaired to single manifold solids; universal tile volume
reproduces 353,500 mm^3 exactly. The live sim_server was restarted onto
the audited code (2026-08-17) and validated against the book over the
API: final sample reads 0.17668 % at -40 AND 0.19805 % at -70 to all
digits -- the steep-angle margin fix is confirmed live (the old 2.0
margin would have leaked background at -70).

**Prior art reconciled (2026-08-17).** Kaster 2025 (arXiv:2507.05152) read
in full and reproduced: his "average intensity ratio < 0.65" vs our ~0.19x
same-coating claim is mostly his own 30.6 % planar cap layer -- at his
material (rho 5 %, d85) and AOI set, a 30.6 %-land pyramid analog reads
0.33-0.40x flat while our 0.06 %-land product reads 0.08-0.17x
(FINDINGS_kaster.md, sweep_kaster.csv, fig_kaster.png; QUESTIONS.md Q19-4
answered). Side discoveries, both handled: margin_depths 6.5 at depth 20
overruns the control zone (voided first run kept as
__void__sweep_kaster_margin65.csv; use 4.5 at depth 20); and NO current
sweep can bit-match pre-80d8945 comb-family rows -- those CSVs were
measured by pre-commit harness bytes git never kept (bounded 5.5e-4
relative, 10x under seed noise; results/anchor_deviations.json + gate
check 8's documented-deviation path record it, silent drift still fails).

**Machinery added since phase 4** (all in scripts/): floor-family kinds
`pillars` (+lean), arplate (AR glass + void + lip + room floor), `corner`
scene; make_ar_glass; paint_depth split rides form_buildable; gate check 8
robust to non-coating sweeps; clean_solid()/orient repair in sweep_phase9v;
stack_frames.py (modulated-beam coupon protocol, verified on synthetic data).

**Reports.** English: report/phase{5..9}/report.html. Korean editions:
report/ko/phase{1-4,5..9}.html + report/ko/protocol.html (the physical
measurement protocol). All published as claude.ai artifacts; URLs in the
session log. FINDINGS_phase{5x,6x,7x,82*,83,9,92,94,94b,9c,9d,9s,9v}.md hold
every grading.

**What is left is physical, in order:** (1) spill-map photos incl. one
underexposed + one haze-only frame (decides zone allocation AND whether the
bare tier suffices -- FINDINGS_phase9d.md), (2) black-urethane rho coupon,
(3) Musou coverage per liter, (4) museum-glass R(theta) + dust week,
(5) optional flocking coupon. The pipeline check: cast one tile, magnify
tips/valleys, bend-test the paint film.

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

## 11a. THE RULE THAT WAS BROKEN FOUR TIMES IN TWO DAYS — read before sweeping

**Validate BEFORE you measure, not after. A sweep you have not earned the right
to run is worse than no sweep, because it produces a ranking someone will act
on.**

On 2026-08-12/13 four separate conclusions were published and then withdrawn.
Not one was overturned by new physics. All four were setup errors that a check
costing minutes would have caught before the sweep that cost hours:

| withdrawn claim | what was actually wrong |
|---|---|
| "shingle beats the cone by 29%" | compared a 0.05 mm edge against a 0.4 mm tip — 8x mismatch, in families whose return is dominated by the exposed feature |
| "a structure buys 28-30x" | the flat-plate denominator was a constant somebody typed. No measurement was ever taken at that value. The true figure is 5.3x |
| "the blade array smears 4.5x" | the spec sheet said 0.1 mm sheet; the measured part was a wedge 0.1 mm at the mouth and **0.9 mm at the root**. Real value 3.44x |
| "the coating's diffuse fraction moves designs 41x" | misread a table whose title says it compares the OLD material model to the new one. The real lever is 6.3x worst case, 1.06-1.39x for the designs actually proposed |

Each was found by someone else — an adversarial reviewer, a questioning agent,
or the user asking "is that really Musou Black?" — after the number had already
been reported.

**The gate, to be passed before any sweep whose output will be ranked:**

1. **Does a control reproduce a known answer?** A flat plate of the coating must
   reproduce the published curve. A rho=0 panel must read exactly 0. The 0.05
   control must read 0.05000. `scripts/fit_coating.py` does the first.
2. **Is every baseline a measurement?** A number used as a denominator must
   trace to a render, with the config that produced it. Never a constant.
3. **Are the things being compared matched on feature size AND process?** Both,
   not either. Matching feature alone assumes a common process and penalises
   whichever family does not need it.
4. **Is the geometry being measured the geometry in the document?** Diff the
   `params_json` against the spec sheet, field by field. `plate_t_bot` was 0.9
   in every blade measurement while the spec said 0.1, for two days.
5. **Does every quoted ratio name its baseline in the same sentence?**

`scripts/gate.py` and `scripts/lock.py` exist for exactly this and were not used
once during those two days.

**Agents are cheap; use them BEFORE, not after.** A questioning agent found
three of the four errors above in fifteen minutes, run after the fact. A
watchdog agent that only checks whether processes are alive finds none of them —
process health and result correctness are different jobs and need different
agents.

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

---

# 2026-08-11 late — READ THIS FIRST. Most of what is above is superseded.

Three things were overturned today. A new session that skips this will repeat
the errors, because the superseded claims are stated confidently above.

## 1. The material model was wrong, and the FIX is only half-constrained

`make_glossy(rho, roughness)` has no Fresnel: its rho_dh is flat with angle
(0.4953% head-on, 0.4521% at 80 deg for rho=0.005). Real black coatings do the
opposite. Filip & Vavra 2026 (reference/2601.05094v1.pdf, Fig. 6; full notes in
reference/SUMMARY.md) measured Musou Black on a goniometer and report THR --
the same quantity hemi_view reads:

    theta   0     15    30    45    60    75    80
    THR   1.00  1.00  1.03  1.13  1.43  2.33  3.18  %

So we were 2x optimistic head-on and ~7x at 80 deg, with the angular trend
running the WRONG WAY. `make_coating()` is a fit to that curve, validated by
scripts/fit_coating.py and guarded by lock.py's material_check.

**But the fit constrains only rho_dh(theta) of a FLAT PLATE, and that curve
cannot distinguish diffuse from specular.** The 76%-Lambertian split in the fit
was CHOSEN, not measured -- and it turns out to drive everything (see 2). Treat
the paper as ±20% on absolute level: it is a preprint, reports BRDF "in
relative units", its own Vantablack reads 6.6x above spec, and its text
contradicts its own TIS figure. Trust the SHAPE, not the digits.

## 2. The mechanism: it is ONE bounce, and diffuse-vs-specular is everything

Switching to the Fresnel coating made designs worse by 2.0x (flat plate), 6.5x
and 8.8x (grooves), 14.5x and 41x (cones). **Three wrong explanations were
offered before the right one; do not add a fourth without measuring.**

Measured decomposition (doubling rho under a specular material):

    D/A = 2.000 +/- 0.008 for EVERY design, cones included.

The return is **one-bounce in every geometry**. There is no multi-bounce
population. Bounce statistics from scripts/ray_census.py describe rays carrying
0.002% of the escaping energy -- 99.9%+ of what returns is the n=1 tip hit.
**Do not use bounce counts as a search objective.**

The whole 2x-to-41x spread is diffuse-vs-specular at fixed rho. Under a
specular BSDF a flank bounce sends light deeper; under a Lambertian one every
mm^2 of wall has a direct view of the sky and simply leaks. Cone p3.75 is hurt
less than p7.5 because it is a NARROWER cavity (aspect 8 vs 4) and traps
diffuse light better -- classic cavity behaviour, not bounce count.

**Consequence: the diffuse fraction of the coating is the single most
consequential unmeasured parameter in the project.** `BR.coating_split(d)`
sweeps it at fixed measured rho_dh(0). Only a printed coupon settles it.

## 3. Reflectance is NOT invariant to the coating change

metrics/01 used to say "linear in rho, so a change of coating rescales every
design equally". True for the old flat-rho material, FALSE for the Fresnel one.
Design-to-design spread collapses from 5.0x to 1.65x at theta=0 and **the
ranking inverts** -- the recommended cone d30/p7.5 goes from best to worst.
**Every past comparison must be RE-RUN, not rescaled.**

## Geometry facts learned today

- `geom3d` now takes a cavity profile: `cavity_radius(f, power, bulge, lip)`.
  power 0.5 paraboloid / 1.0 cone / 2.0 needle; `bulge` widens monotonically
  and CANNOT make an undercut (verified, min dr = 0 over the whole grid);
  `lip` adds a Gaussian overhang that can.
- **`height_seg=3` does not resolve the profile.** At power 0.15 the answer
  moves 50.6x between hseg 3 and 12. Use hseg >= 12 and power >= 0.5. A whole
  sweep (1031 rows) was voided over this -- results/__void__sweep_shapes_hseg3.csv.
- **Cells seal.** Once the pillar radius reaches the hex circumradius
  pitch/sqrt(3), neighbours meet and everything below is not a cavity. A plain
  cone at pitch 7.5 seals at 72% of nominal depth: "depth 30" was never 30 mm
  of cavity. `geom3d.seal_fraction()` records it.
- `spec_roughness` moves CAVITY rho_dh by 32% (0.05 vs 0.30) even though it is
  irrelevant on a flat plate. Pin it explicitly in every config.

## Metrics now live in metrics/ — read metrics/README.md

Numbered like profiles/. 03 core_frac is RETIRED (its denominator shrinks with
the thing it measures). 04 peak_radiance is defined but its first results were
a stripe-phase artifact: a 1D groove's peak spans 214x depending on whether the
stripe lands on a ridge or in a valley, and form_mtf samples only 3 phases.
Needs N>=12 phases and mm_per_px <= tip/4 before it is quotable.

## Machinery that now exists

- `scripts/lock.py` freezes the reported designs AND the material model, 20s.
  `scripts/gate.py` makes report generation a precondition on it passing.
- `.claude/agents/optics-reviewer.md` + `scripts/review_needed.py`.
- `scripts/make_report.py` is DISARMED -- it hard-coded two withdrawn claims.
  Use `scripts/report_compare.py`, which is gated.

---

# 2026-08-11 23:xx — the exposed-area law is DEAD, and the search left the
# cone/V-groove families for the first time

## 1. The law that drove every design decision does not survive the coating fix

Full write-up and method: `results/FINDINGS_topo_smoke.md`.

    reflectance(head-on)  ~=  exposed_fraction x rho

was established on the 1D ridge family across 24 combinations, and it is the
entire argument for going 3D: a point exposes pi r^2 / cell where a line
exposes 2r / pitch, which at pitch 7.5 is 0.258% against 10.667% -- **41x**.

A hex-wall honeycomb was built as a NEGATIVE CONTROL, expected to lose by that
41x. Measured, same frame, re-measured cone reference, fitted coating:

| topology | exposed area | worst rho | rho at theta=0 |
|---|---|---|---|
| cone p7.5 d30 r0.2 | 0.258 % | 0.00286 | 0.00233 |
| **honeycomb p7.5 d30 w0.4** | **10.667 %** | **0.00373** | **0.00352** |
| shingle p7.5 d30 tilt60 | 1.116 % | 0.00725 | 0.00606 |
| truss p7.5 d30 L5 r0.35 | 1.580 % | 0.01832 | 0.00957 |

**1.51x head-on, not 41x. The prediction is off by a factor of 27.**

Not a render defect: the cone was re-measured in the same frame, both use the
same mesh path / margin / slab / coating instance, and neither exceeds the flat
plate of its own coating at any theta.

**Consequence: "shrink the tip" is no longer the primary design move**, and the
1D->3D argument in `geom3d.py`'s module docstring is an argument about area,
which has just been shown not to be the lever. Cavity-lattice topologies are
back on the table -- and they have an advantage no pillar array can have:
**they never seal.** A cone at pitch 7.5 stops being a cavity at 72.2% of its
nominal depth; a hex cell with vertical walls is 30 mm of cavity at depth 30.

## 2. From the sweep_shapes analysis (`results/analysis_shapes.md`)

Three findings that change how results are read, all with numbers in that file:

- **`seal_frac` is not an independent variable at all.** Pitch cancels exactly
  from `seal_fraction`'s criterion, so it is a deterministic function of
  (power, bulge, lip) and identical across all four pitches. Any "seal_frac
  effect" is a relabelling of those three knobs.
- **The real predictor is `usable aspect = seal_frac x depth / pitch`**:
  Spearman -0.876, log-log slope -1.15, **R^2 = 0.73** over 192 designs. Nominal
  depth only reaches -0.488. **A depth-50 design at bulge 0.35 + lip 0.35 has
  8.3 mm of cavity -- less than a depth-20 design at bulge 0 + lip 0.** Any plot
  against `depth` is a plot against a mislabelled axis.
- **The "worst of three materials" rule is in practice a SPECULAR-ONLY rule.**
  `coating_split(0.0)` has a grazing ceiling of 24.95%; `coating_split(1.0)` is
  Lambertian at 0.998%. Splitting at fixed rho_dh(0) pins them where they agree
  and lets them diverge 25x elsewhere, so d00 sets the combined score for
  170 of 196 designs. Quote the ceilings whenever that rule is quoted.

Also open, and worth one run each before any small difference is quoted: a
**systematic -0.85% +theta/-theta asymmetry in a zero-tilt configuration** (all
three materials biased the same way, so not noise -- suspected lattice-sampling
at pitch 11 / face 60), and the fact that the **top of the ranking is a 1.4%
statistical tie** against a 1.28% measurement floor.

## 3. New machinery

| file | does |
|---|---|
| `geom_topo.py` | family 6: `shingle` / `truss` / `honeycomb`. First non-pillar, non-extruded topologies |
| `sweep_topo.py` | their sweep. Scoring IDENTICAL to `sweep_shapes.py` on purpose; every row carries `params_json` so one row rebuilds its design exactly |
| `results/FINDINGS_topo_smoke.md` | the falsification above |
| `results/analysis_shapes.md` | full adversarial analysis of `sweep_shapes.csv` |

`blender_render.build_scene` now dispatches families through a `mesh_fn`
variable rather than hard-coding `geom3d`. **`describe()`'s fallthrough to
`profile2d.describe` is silent** -- an unregistered family fails later with a
confusing `no attribute 'slat_len'`. Register any new family in BOTH places.
