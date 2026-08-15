# Reference papers — detailed reading notes

Read 2026-08-11, page by page, from the PDFs in this folder.

**Rules used, because the failure mode here is remembering the story and forgetting
the numbers:**

- read the PDF page by page. No abstracts, no search summaries, no memory.
- **every factual claim carries a page or figure number.** No citation → `[추측]`,
  and it must not be used as a design input.
- figures whose numbers matter are re-rendered at 400 dpi with `pdftoppm` and read
  enlarged. Never eyeballed from a page thumbnail. (This caught a real error: the
  Musou-paint THR curve reads 0.0100 at normal incidence, which is not what the
  page-sized figure suggested.)
- a separate section per paper records **what the authors say does NOT work**, and
  **what is only cited from elsewhere**, because those are the parts that evaporate.
- `[확인]` read it on the page · `[추측]` plausible, unverified · `[모름]` unknown

**Correction to earlier work in this project:** `2404.18169` was referred to
throughout the 2026-08-10/11 sessions as "the bird of paradise paper". It is not.
It is a **review** of bioinspired infrared absorbers (Mouchet 2024); birds of
paradise are §2.3, two paragraphs, citing McCoy et al. as the primary source. Any
bird-of-paradise number quoted in this project traces to a review's summary of
someone else's measurement, not to a measurement in the folder. Numbers below are
tagged accordingly.

---

# 1. Filip & Vávra (2026) — *How Dark is Dark? A Reflectance and Scattering Analysis of Black Materials*

`2601.05094v1.pdf` · arXiv 2601.05094v1, 8 Jan 2026 · Czech Academy of Sciences (UTIA)

**CITATION UPDATED 2026-08-12 — this is no longer a preprint.** Published as
Jiří Filip and Radomír Vávra, *"How dark is dark? A reflectance and scattering
analysis of black materials"*, **J. Opt. Soc. Am. A 43(7), 1037–1045 (10 June
2026)**, DOI 10.1364/JOSAA.589935.
`[확인: opg.optica.org/josaa/abstract.cfm?uri=josaa-43-7-1037]`

Everything below was read from the **arXiv v1 PDF in this folder**, not from the
JOSA A version of record. The two may differ — peer review is exactly the
process that would have addressed the internal inconsistencies flagged below
(the TIS ranking that contradicts its own figure, the Fig. 4 albedo bars that
cannot be reconciled with the Fig. 6 THR curves). **Before any number from this
paper is quoted in a publication, re-read the JOSA A version and re-check those
three items.** The `make_coating()` fit, and therefore every absolute number in
this project, rests on the Fig. 6 Musou-paint THR curve.

The peer-reviewed status also changes how the caveats below should be weighed:
"it is a preprint" was doing real work as a reason to treat the absolute scale
as ±20%. That reason is now weaker. The other two reasons — BRDF reported "in
relative units", and their own Vantablack reading 6.6× above spec — are not,
and they still stand on the v1 text.

## Why this is the most important paper in the folder

It measures **the exact quantity we simulate**, on **the exact coating we assumed**.
Everything else here is about structure; this is about whether our material input is
right. It is not.

Their THR — total hemispherical reflectance `[확인 eq. 1, p.4]`:

    ρ(ω_i) = ∫_Ωo  f_r(ω_i, ω_o) · cos θ_v  dω_v

That is directional-hemispherical reflectance: the fraction of a beam arriving from
ω_i that leaves again. **It is the same number our `hemi_view` reciprocity
measurement produces.** Same definition, no conversion, no π factor.

**Three caveats on comparability, added after 原文 verification:**

1. **The integral is truncated.** θ_v is sampled 0–85°, so the 85–90° band is
   missing — about 2.4% of the projected hemisphere, and disproportionately
   important for the grazing-lobe materials `[확인 §3.3, p.4]`.
2. **It is a visible-band, RGB-weighted average** (380–700 nm, channel peaks
   480/520/615) `[확인 p.3]`. Our `hemi_view` is one broadband grey channel. Say so
   when quoting the comparison.
3. **The absolute scale is undocumented.** p.3: BRDF values are "reported in
   **relative units**", and the paper never states how THR is placed on an absolute
   scale. Two internal checks suggest the floor is not tight: their own p.2 quotes
   Vantablack at "over 99.965%" absorption (ρ = 3.5e-4) against a measured THR of
   0.0023 — **6.6× higher**; Musou's 99.4% spec (ρ = 6e-3) against 0.0100 — 1.7×
   higher. **An absolute uncertainty of order 0.002 is 20% of the 1.00% headline.**
   So: trust the *shape* of the curve and the *ratios between materials*, and treat
   the absolute level as ±20%. Quoting 1.00 / 1.43 / 3.18% to three significant
   figures is over-precise.

## Measurement setup `[확인 §3.2–3.3, p.3–4]`

| | |
|---|---|
| instrument | UTIA gonioreflectometer, angular repeatability 0.03° |
| illumination | Cree XML LED, 280 lm @ 3.0 A, 1 m from sample, unpolarised |
| camera | AVT Pike 1600C, 14-bit CCD, 4872×3248, 2 m away, 180 mm lens (~650 dpi at sample) |
| spectral | 380–700 nm; RGB channel peaks 480 / 520 / 615 nm |
| exposure | up to 2.6 s — the samples are very dark |
| θ_i | 0, 15, 30, 45, 60, 75, 80, 85° |
| θ_v | 0–85° in 1° steps; azimuth 0–360° in 10° steps |
| samples | 24 488 per material, **96 h acquisition each** |
| specimen | 40×40 mm; BRDF averaged over the central 4×4 mm |

## THE NUMBER THAT CHANGES OUR ABSOLUTE RESULTS `[확인 Fig. 6, p.7, read at 400 dpi]`

Legend verified by enlarging the legend box: acryl ○ blue · chalkboard + red ·
**Musou paint × yellow** · black velvet ✻ purple · Musou fabric □ green ·
Vantablack △ cyan.

**Musou Black paint — measured THR vs illumination polar angle:**

| θ_i | 0° | 15° | 30° | 45° | 60° | 75° | 80° | 85° |
|---|---|---|---|---|---|---|---|---|
| THR | **0.0100** | 0.0100 | 0.0103 | 0.0113 | 0.0143 | 0.0233 | 0.0318 | off-scale (>0.04) |

**Our simulation assumes ρ = 0.005; our flat plate measures 0.4953% at 0° and
0.4521% at −80°.**

1. **Head-on we are 2× optimistic.** 0.50% assumed vs **1.00%** measured.
2. **At grazing we are ~7× optimistic, and the shape is wrong in sign.** Our model
   has reflectance falling slightly toward grazing; the measurement has it rising
   **3.2× from 0° to 80°**. This is the missing Fresnel appearing exactly where it
   was predicted to bite.
3. The manufacturer figure we had been quoting — "absorbs up to 99.4%", i.e. 0.6%
   `[확인 p.3; their ref 16 is musoublack.com]` — is a best case that a goniometric
   measurement of a brush-applied film does not reproduce.

### Effect on our reported numbers

Reflectance is **exactly linear in ρ** (our own check, 8× sweep), so this rescales
cleanly:

| | as reported (ρ=0.005) | rescaled to measured Musou paint |
|---|---|---|
| 3D cone d30/p7.5, head-on | 0.0047% | **~0.0094%** |
| 1D V-groove d30/p7.5, head-on | 0.0237% | ~0.0474% |
| flat plate of the coating | 0.4953% | **1.00%** |

**Ratios between designs are untouched** — same coating everywhere, linearity
verified. The 5.0× cone-vs-groove result stands **at the stated tip convention: one
FDM nozzle, 0.4 mm across, for both families** (`sweep_v2.csv`). The convention has
to be named every time that ratio is quoted — the same comparison read 5.2× and then
2.9× before tip-matching was done properly, and both were wrong. What moves is every absolute
claim, and "105× darker than the flat coating" must be re-derived, because the
coating itself now gets *worse* toward grazing rather than better.

## Second headline: fabric beats paint by ~8× `[확인 Fig. 4 p.6, Fig. 6 p.7]`

| material | THR @ θ_i=0 | THR @ θ_i=85 | toward grazing |
|---|---|---|---|
| Vantablack (VACNT) | ~0.002 | ~0.003 | essentially flat |
| Musou **fabric** | ~0.0012 | ~0.0055 | rises gently |
| black velvet | ~0.002 | ~0.0122 | rises |
| **Musou paint** | **0.0100** | >0.04 | **rises steeply** |
| chalkboard paint | **0.0351** | off-scale | rises steeply |
| acryl paint | **off-scale (>0.05)** | off-scale | worst at normal, dips to 0.030 at 45° |

*(corrected: I originally put acryl at ~0.035 at normal and called it "worst
throughout". It is off the top of the 0.05 axis at 0° and 15°, re-enters at ~21°,
and at 45° reads 0.0299 — below chalkboard's 0.0336. Chalkboard is the ~0.035
material at normal. The paper's own p.7 says as much: "the increase in THR for
acrylic paint at low and moderate illumination polar angles".)*

Mechanism given: fibrous / VACNT microstructure keeps the **specular** component R_s
low at all angles through multiple scattering, whereas coatings show "significantly
higher R_s values that increase rapidly toward grazing illumination" `[확인 p.7]`.

**This is the same mechanism our panel geometry uses — multiple scattering in a
structure — but operating at fibre scale inside the material. The fabric is already
doing at ~10 µm what we are doing at 7.5 mm.**

## Perception at *our* light level `[확인 §4.4, Fig. 8, p.9]`

36 participants rated perceived darkness 0–100 on renderings at nominal, 10×, and
100× intensity. **Our application is the 100× regime** — the beam lands on the wall
with essentially full power.

At intensity 100, read from Fig. 8: Vantablack ~66±22, Musou fabric ~64±20, black
velvet ~27.5±17, **Musou paint ~24±16**, acryl ~14.5, chalkboard ~7.5.

**The error bars are enormous and I originally omitted them.** Musou paint and black
velvet are **not separated at all** at this intensity. What the figure supports is
"the two fabrics/VACNT stay dark, the coatings do not" — not a ranking within either
group. (Also: "at intensity 1 every coating looks fine" is not true of acryl, ≈53.)

**The materials only separate when you turn the light up** — precisely our problem.

## Other definitions worth adopting

- **TIS** = R_d / (R_s + R_d), with a 5° specular exclusion cone `[확인 eq. 3, p.4]`.
  A structure that converts specular into diffuse has TIS → 1, which is what we want
  for form destruction. The definition is worth adopting.
  **But do not adopt the paper's ranking with it.** p.7 says "the lowest TIS values
  are consistently observed for black velvet, followed closely by Vantablack and
  Musou fabric" — and an independent 400 dpi read of their own TIS panel does not
  show that: the lowest curve by a wide margin is **acryl paint** (~0.90 at 15–30°,
  0.85 at 45°, off-scale below 0.8 elsewhere), with every other material at
  0.93–0.995 through 60°, and black velvet the **highest** (~0.957) at 85°.
  `[확인 Fig. 6 TIS panel, p.7, re-read at 400 dpi]` The quoted sentence is accurate;
  the finding it states is contradicted by the figure beside it. I originally copied
  the sentence as fact and built a recommendation on it — and inconsistently, since
  TIS→1 is the goal and the sentence names the *lowest*-TIS materials as exemplary.
- **Effective albedo** A = ∫ ρ(ω_i) cos θ_i dω_i `[확인 eq. 2, p.4]` — one number per
  material, cosine-weighted over incidence. Better than our "worst over all angles"
  when the rig's angle distribution is unknown.
- "very dark materials typically exhibit ρ(ω_i) < 0.02 over most illumination
  directions" `[확인 p.4]` — a sanity band.

## What the authors say does NOT work / limitations `[확인 §5, p.10]`

- visible range only (380–700 nm); NIR may differ
- rendering used **one point light and a simple 4-sphere scene**, chosen to emphasise
  angular scattering; richer illumination may give different perceptual results
- psychophysics ran on **LDR screens showing renderings**, not physical samples — no
  wear, contamination, or large-scale spatial context
- only *perceived darkness* was rated; gloss and texture were not
- acryl paint's non-circular highlights are suspected to be partly **substrate
  showing through** a thin/uneven film, not the paint `[확인 p.7]` — a direct warning
  about coating the root of a deep 3D-printed cell
- Vantablack is "not available for consumer use" `[확인 p.2]`

## Open questions `[모름]`

- Is 1.00% specific to *brush-applied* Musou paint on their substrate? p.3 says
  "brush-on"; there is no thickness or application-method study.
- ~~Their Fig. 4 albedo bar for Musou paint reads far below 0.010…~~ **WRONG in both
  halves, corrected after verification.** Measured at 400 dpi, the Fig. 4 albedo bars
  are: acryl 0.215, chalkboard 0.046, **Musou paint 0.0240**, black velvet 0.0059,
  Musou fabric 0.0025, Vantablack 0.0025. Musou paint reads *above* 0.010, not below;
  and dropping a 1/π normalisation would make A *larger* than mean ρ, not smaller, so
  the inference was backwards too. The correct statement: **Fig. 4 cannot be
  reconciled with Fig. 6 by any single factor** — Vantablack matches ρ 1:1, acryl
  matches πρ, the rest fall between — and the Fig. 4 axis is labelled "relative
  luminance Y", not albedo. **The recommendation stands (use Fig. 6, do not quote
  their albedo); the reason I gave for it did not.** This was also a figure I claimed
  to have re-rendered at 400 dpi and had not.
- Whether Musou fabric can be laminated into a folded or printed cavity at our scale,
  and what it costs.

---

# 2. Davis, Nijhout & Johnsen (2020) — *Diverse nanostructures underlie thin ultra-black scales in butterflies*

`s41467-020-15033-1.pdf` · Nature Communications 11:1294 · Duke University
· received 6 Jun 2019, accepted 21 Jan 2020

## Numbers `[확인 p.2]`

- 10 ultra-black species across 4 subfamilies; 4 control species.
- Ultra-black wings: **0.06–0.4% reflectance at 500 nm, normal incidence.**
  Controls: **1–3%.**
- Papilionids reach 0.2% via a poly-disperse honeycomb `[확인 abstract]`.
- **Important comparability caveat** `[확인 Methods, p.5]`: measured with a
  fibre-optic **back-reflectance probe at 90° to the wing**, deliberately "to capture
  the maximum specular reflectance and thus provide a conservative estimate". This is
  **near-retro specular reflectance, NOT hemispherical.** It is *not* directly
  comparable to our ρ_dh or to Filip's THR. Calibrated against a **2%** Spectralon
  standard, not a 99% white one.

## The structure `[확인 p.2–3, Fig. 2]`

Upper lamina perforated by quasi-periodic holes; hole shape and size vary widely
between species:

| species | hole geometry |
|---|---|
| *Eunica chlorocroa* | chevron-shaped |
| *Catonephele antinoe*, *C. numilia*, *Heliconius doris* | 500 × 330 nm rectangles |
| *Euploea dufresne*, *E. klugi* | 750 × 500 nm rectangles |
| *Trogonoptera brookiana* (papilionid) | honeycomb |

**Two features are present in every ultra-black species and absent or reduced in
controls** `[확인 p.3]`:
1. **steep longitudinal ridges**
2. **robust trabeculae** — pillars connecting the upper and lower laminae

## FDTD results — the key quantitative claims `[확인 p.3–4, Figs. 3–4]`

- Full scale model: 0.4–1.0% reflectance across the visible.
- That is **14–40× lower** than two flat overlapping slabs made of *the same volume*
  of the same absorbing material.
- **Removing the ridges OR the trabeculae → 3–16× increase in reflectance.
  Removing both → 7–28×.** Removing the basal lamina: marginal.
- **Removing the same volume of material from a flat block increases reflectance by
  at most 2×** `[확인 Supplementary Fig. 5, cited p.3]`. So it is the *arrangement*,
  not the amount of absorber.
- **Decoupling structure from absorption** `[확인 Fig. 4, p.4]`: making the trabeculae
  *non-absorbing* still leaves them reducing reflectance by **5–70%**; non-absorbing
  ridges reduce it by **14–58%**. "These structural features alone significantly
  reduce reflectance, even though they do not directly contribute to absorption."
- Refractive index sweep, 99 combinations at 550 nm `[확인 Fig. 5, p.5]`: reflectance
  is driven mainly by the **imaginary** part k. With k=0 reflectance approaches 100%;
  at k=0.06 it is 1%. Conclusion: "melanin's particular optical properties are not
  necessary… only a strongly absorbing material — ideally one with a real part of the
  refractive index **lower** than that of melanin (n=1.8)."

## The design principle they state `[확인 abstract and p.5]`

> "butterflies produce ultra-black by creating a **sparse material with high surface
> area** to increase absorption and minimize surface reflection"

and, p.5:

> "consistent with a growing body of literature supporting **sparse packing, high
> surface area, and strong absorption** as the general design principles of natural
> ultra-black materials"

## What the authors say does NOT work / is uncertain `[확인 p.5]`

- **The resonance criterion is weaker than previously thought.** "the diversity of
  hole shapes (chevrons, rectangles, quasi-honeycombs) and sizes (350–750 nm) suggest
  that enhanced absorption from resonance effects when hole radius r ≈ λ may be
  **either less important or a more flexible criterion** than previously hypothesised".
- The role of the periodic ridges is **contested in the literature**: one model gives
  them an important channelling role, another finds an insignificant effect on
  broadband absorption in the visible `[확인 p.2]`. This paper supports a substantial
  role, contra prior work.
- Ridge spacing differs by family: papilionids >1 µm (two rows of holes between
  ridges), nymphalids within the visible wavelength range. So ridge behaviour is not
  one mechanism.
- Only one specimen per species — chosen deliberately for minimal wear, so **no
  within-species variation is characterised**.

## Honest transfer assessment to our mm scale

- The hole sizes are **350–750 nm**, ridge spacing ~1 µm, at λ ≈ 500 nm. These are
  wavelength-scale: the mechanisms are diffractive / effective-index, **not ray
  optics**. Our failed mm-scale flank serration is consistent with this and should
  not be retried on this paper's authority.
- **What does transfer is scale-free**: *sparse packing + high surface area + strong
  absorption*, and the finding that **structure works even when it does not absorb**
  (Fig. 4) — that is pure geometry redirecting light, and geometry redirecting light
  is exactly what ray optics does.
- The 14–40× structural gain over a flat slab of equal material is the right order to
  compare against our own measured **105× at head-on** — reassuring, not identical
  (different quantity, different scale).

---

# 3. Mouchet (2024) — *Infrared absorbers inspired by nature*

`2404.18169v1.pdf` · arXiv 2404.18169v1, 28 Apr 2024 · Univ. Namur / Univ. Exeter

**This is a review, not a primary measurement paper.** Everything below is the
review's summary of other people's work; the reference numbers are given so the
primary source can be pulled if a number is going to be load-bearing.

## 3.1 Birds of paradise — §2.3, p.7, Fig. 7 · primary source: McCoy et al. [ref 36]

- absorption up to **99.95%**; directional reflectance **0.05–0.31%**
- **barbules curved up and tilted ~30° from the normal, toward the feather's distal
  tip** `[확인 p.7]`
- **cavities 5–30 µm wide, 200–400 µm deep** `[확인 p.7]`
  → aspect ratio depth/width spans **~7 to ~80**. (This project has been quoting
  "aspect 10–40"; the review's own figures give a wider range. Corrected.)
- **"the super-black effect is most pronounced when looked from the distal
  direction… The cavities present a directional reflectance bias, making the feathers
  even darker when viewed from the distal direction."** `[확인 p.7]`

**`[추측]` This may explain our failed tilt experiment — but note a step I took
silently: Mouchet's bias sentences are about VIEWING direction, and I converted them
into a claim about ILLUMINATION direction. Reciprocity relates the two; the paper does
not assert it.** We tested tilted cones and
scored them on *worst reflectance over all angles*, symmetric in ±θ. A structure whose
whole point is a **directional bias** is guaranteed to lose on that metric: it buys
darkness from one side by giving it up on the other. The tilt result was not
necessarily wrong — **the metric was wrong for it.** If the real rig has a known
dominant beam direction, tilt becomes a legitimate lever again.

## 3.2 Gaboon viper *Bitis rhinoceros* — §2.5, p.8, Fig. 9 · primary: [ref 87]

- hierarchical: **densely packed leaf-like microstructures covered with nanoridges**
- **The V-cavity model is for the PALE scales, not the black ones.** I dropped the
  clause that inverts this. Full sentence, p.8: "Modelling of diffuse reflection
  using Lambertian symmetric V-shaped cavities validated the proposed light-trapping
  mechanism and elucidated the angular dependence of reflectance spectra **in pale
  scales** [87]. **However, the black scales exhibit a distinct angular
  characteristic**, lacking a specular reflection peak and displaying a gradual
  decrease in reflectance intensity with increasing emerging angle." So the earlier
  claim that "the V-groove family we built is literally the published model for this
  animal['s black]" was **wrong, and backwards**: the black is explicitly contrasted
  with the V-cavity fit.
- black scales **lack a specular peak** and show a *gradual* decrease in reflectance
  with emerging angle — "attributed to the more isotropic arrangement of scale
  structure" `[확인 p.8]`
- **Coating the black scales with Au-Pd preserves the black and *further diminishes*
  reflectance** `[확인 p.8]`, because the metal "further enhances light trapping via
  light reflections on the metal-coated surfaces".

**That last point is the most counter-intuitive result in the folder and it matters
to us.** Making the surface *more* specular made the structure *darker*. Mechanism:
in a deep cavity, a diffuse first hit scatters light back out of the mouth, while a
specular first hit sends it deeper. Our own measured "gloss roughness 0.30 is an
interior optimum" is the same effect. It also means **the coating choice and the
geometry are not separable** — a darker but more diffuse coating can make a deep
structure worse.

## 3.3 Scarab *Euprotaetia inexpectata* — p.7, Fig. 6 · primary: [ref 84]

- **arrays of ellipsoidal and randomly located micropillars** `[확인 p.7]`
- absorption up to **99.5%**, reflectance **0.1% at 400 nm**
- mechanism given: **Mie scattering + optical focusing**, delivering light to melanin
  inside the elytra

Random placement of rounded pillars, stated as the mechanism. Closest natural
analogue to our jittered cone array.

## 3.4 Jumping spiders *Maratus* — §2.4, p.8, Fig. 8 · primary: McCoy et al. [ref 86]

- *M. speciosus* **0.44%**, *M. karrie* **0.35%**; ordinary black spider *Cylistella*
  **4.61%**; bird of paradise *Drepanornis bruijnii* **0.17%** `[확인 Fig. 8b]`
- structures: **microlens arrays** over striated cuticle + a melanin layer, plus
  **brush-like scales**
- four mechanisms listed `[확인 Fig. 8g]`: (1) multiple scattering off spiny
  projections, (2) multiple scattering between bump surfaces, (3) extended path
  length within the melanin layer, (4) diffraction from the periodic microlens array

## 3.5 Longhorn beetle *Rosalia alpina* — §2.2, p.6–7, Fig. 5 · primary: [refs 81,82]

- **"tent-shaped" scales: inclined, touching neighbours at the tips**, 1 µm period,
  with 100 nm grating on them `[확인 p.7]`
- light trapping attributed to **"several reflections on opposite inclined patterned
  scales"** `[확인 p.7]`

Opposed inclined surfaces meeting at the tips — a tent, not a cone. A distinct
topology from anything we have built.

## 3.6 Moth-eye / nipple arrays — §2.1, p.5–6, Fig. 4

- antireflection by **gradual refractive-index matching**; requires protuberance
  spacing **below the incident wavelength, typically <200 nm**, so that non-zero
  diffraction orders are evanescent `[확인 p.5]`
- **explicitly sub-wavelength. This does NOT transfer to mm scale.** Recorded so this
  project stops reaching for it.

Two findings from this section are nonetheless scale-free and directly useful:

- ~~**Disorder helps.**~~ **RETRACTED 2026-08-11 by原文 verification.** The quote is
  verbatim on p.6 but I attributed it wrongly. Full sentence: "disorder in the
  protuberance height, width, and position was found to increase the transparency
  properties, **in the case of *G. oto* glasswing butterfly [59]**" — ref [59] is
  Siddique, Gomard & Hölscher, *Nat. Commun.* 6:6909 (2015). Not *C. ossa*, and not
  Fig. 4, which models *C. ossa* as truncated cones (ref [57]) and contains **no
  disorder study**. It is also about **transparency** — antireflection of a
  transparent membrane — not blackness, and it sits inside the section this very
  document declares "explicitly sub-wavelength, does NOT transfer to mm scale".
  **This source does not support turning `depth_jitter` back on.** Our own jitter
  result stands on our own measurement; it has no literature backing here.
- **Paraboloid beats cone — in butterfly COMPOUND EYES, at ~200 nm.** Quote verbatim
  on p.6: "the paraboloid profile with protuberances almost touching each other was
  found to exhibit the lowest reflectance, with the effective refractive index
  varying quasi-linearly with depth" `[확인 p.6, ref 21]`. **Qualifier I originally
  dropped:** ref [21] is Stavenga et al., *"Light on the moth-eye **corneal nipple
  array** of butterflies"*, Proc. R. Soc. B 273:661 (2006) — the 19-species survey is
  of **corneal nipples on compound eyes**, not wing scales and not black patches.
  Sub-wavelength, same as the rest of this section.

The stated mechanism is effective-index, which is sub-wavelength. **But the shape
ranking is worth testing in ray optics anyway**, because a paraboloid has a
continuously varying flank angle — steep at the tip, shallow at the base — and our own
measurement says the return scales like the tip **radius** (exponent 1.11), i.e. it
comes from the **flank near the tip**, not the tip disc. A paraboloid changes exactly
that flank.

## 3.7 Magellan birdwing *Troides magellanus* — p.4–5 · primary: [ref 27]

- 98% absorption of visible light; IR peaks at 3 µm and 6 µm from C=O in chitin
- five structural elements: a **roof-like structure** carrying ridges, holes in the
  separating structures, and **pillars joining upper and lower membranes**
- **the structural gain here is modest**: vs a non-structured flat slab of *equal
  volume*, only **+10% absorption and +17% emissivity at 40°C** `[확인 p.5]`

Recorded because it cuts against the butterfly paper's 14–40×. Different quantity
(absorption vs reflectance) and different species, but it is a reminder that
"structure beats flat" is not a fixed factor.

## 3.8 *Papilio ulysses* — p.3–4, Fig. 2 · primary: [ref 28]

The cleanest experimental proof that the effect is structural:
**matt black scales absorb 95%, which drops to 55% when wetted with bromoform**, an
index-matching fluid; lustrous black scales drop 90% → 70% `[확인 p.3, Fig. 2b]`.
Fill the structure and it stops working.

Also `[확인 p.3]`: **coating ultra-black butterfly structures with gold does not
increase reflectance**, unlike ordinary black wings — the same surprising result as the
viper's Au-Pd coating, from a different animal.

---

# 4. Kaster (2025) — *Macroscopic structural light absorbers*

**THE CLOSEST PRIOR ART IN THE FOLDER, AND IT WAS NOT KNOWN TO THIS PROJECT
UNTIL 2026-08-12.** Found while checking whether our result is publishable.

J. Appl. Phys. **138**(17), 174904, 7 Nov 2025 · preprint arXiv:2507.05152,
7 Jul 2025 · Special Topic on Mechanical Metamaterials
`[확인: arxiv.org/abs/2507.05152, pubs.aip.org]`

**PDF NOT YET IN THIS FOLDER AND NOT YET READ PAGE BY PAGE.** Everything here is
from the abstract, the AIP SciLights piece, and listing metadata. By this file's
own rules that makes all of it weaker than `[확인 p.N]`, and none of it may be
used as a design input until the PDF is read. It is recorded now because the
novelty question cannot wait for that.

## What it is

- **Same problem class as ours**: stray light from illuminated peripheral
  surfaces, mitigated by geometry rather than by coating.
- **Structures**: "periodic minimal surface approximations and quasi-stochastic
  lattices" — TPMS/gyroid-like foams and sponge-like lattices. The SciLights
  piece says three absorber designs. `[확인 abstract]`
- **Scale**: "minimal structural dimensions of approximately **100 µm**"
  `[확인 abstract]`. Ours run 0.05–0.4 mm features on a 3.75–11 mm pitch, so we
  are the coarser of the two by roughly an order of magnitude — but both are
  ray-optics regime and both call themselves macroscopic.
- **Quantity**: peak and average intensity at a **hemispherical receiver**
  `[확인 abstract]`. That is our `hemi_view` and our metrics 01 and 04, arrived
  at independently.
- **Method**: `[모름]` — neither the abstract nor SciLights names the ray tracer,
  the ray count, or the BSDF used for the absorbing surface. **This is the first
  thing to read in the PDF**, because it decides whether their numbers and ours
  are comparable at all.
- **No fabricated sample.** "No prototypes were fabricated or experimentally
  validated in this work. Simulations only." `[확인 AIP SciLights]` The author
  states he plans to fabricate and validate later.

## The headline numbers, and how ours compare

> "reductions in received **peak** intensities by factors of less than **0.39**
> and **average** intensities by factors of less than **0.65**, without altering
> the surface properties" `[확인 abstract]`

So 2.6× on peak, **1.5× on average**. Our best shingle reads 0.00182 against a
flat plate of the same coating at 0.00998 — a factor of **0.18, i.e. 5.5×**.

**We are claiming ~3.7× more improvement than the published state of the art in
the same problem, at a coarser scale, with the same absence of experiment.** That
is the single number a referee will attack first. `[추측]` The likely
explanations, in the order they should be checked: their baseline may not be a
flat plate of the same material; their receiver may be truncated differently;
and our multi-bounce behaviour rests on a BRDF split nothing has measured.
Until the PDF is read, **do not present the comparison as a win.**

## The direct contradiction, and it may be our contribution

Kaster's stated mechanism is **"by increasing the number of reflections before
residual reflected light reaches a hemispherical receiver"** `[확인 abstract]`,
and SciLights repeats it. The Ocean Insight patent below says the same thing in
different words.

**Our own measurement says the opposite.** Doubling ρ under a specular material
multiplies the return by 2.000 ± 0.008 for every design tested, cones included
— the return is **single-bounce in every geometry**, and bounce statistics
describe rays carrying 0.002% of the escaping energy (CONTEXT.md, 2026-08-11;
`scripts/ray_census.py`). CONTEXT.md states plainly: *do not use bounce counts
as a search objective.*

Either this is a real and publishable correction to how this class of structure
is understood, or our material model is wrong in a way that suppresses
multi-bounce. **Both papers are simulation-only, so the disagreement cannot be
settled by either of them — only by a measured coupon.** That framing is
probably the most defensible contribution available from this work.

---

# 5. US 11,209,577 B2 — the geometry space is already claimed

*"Macro-scale features for optically black surfaces and straylight
suppression"* · Ocean Insight Inc. (orig. Ocean Optics) · inventor James A.
Carter · filed 30 May 2019, priority 30 May 2018, granted 28 Dec 2021
`[확인: patents.google.com/patent/US11209577B2/en]`

Claim 1: *"a cluster of macro structures located on the supporting surface each
including **macro-scale surfaces at different surface orientations that are
slanted with respect to the supporting surface**"* — slanted so as to redirect
light **into neighbouring structures** so it bounces between them.

- **Scale claimed: "under 1 mm (e.g., around 0.5 mm)" and "greater than 1 mm".**
  Millimetre scale — the same regime as this project, and coarser than Kaster.
- **Both periodic and irregular arrangements are claimed**, with identical or
  non-identical macro structures.
- Dependent claims cover **hexagonal, triangular, rectangular and square
  polygonal bases**, **conical tops**, hybrid tapered-polygon-plus-cone
  sections, and **non-identical heights and dimensions**.

**Read against our families: shingle (slanted surfaces redirecting into
neighbours), honeycomb, square cell, triangle cell, cone, and lattice jitter all
fall inside those claims.** Whatever else this work is, the geometry space is
not open.

**But the patent reports no reflectance numbers at all** `[확인]`. Neither does
it compare families. That is the gap: the structures are claimed, the physics is
not published.

---

# Consolidated implementation points

Ordered by how much they change what we do next.

## A. Material model — do this before any new geometry

1. **Re-baseline every absolute number at ρ = 0.010, not 0.005.** Linearity is
   verified, so it is a rescale, not a re-run — but the report must say which ρ it
   quotes and why. Keep 0.005 as a labelled optimistic bound.
   `[Filip Fig. 6]`
2. **Fresnel is now mandatory.** The measured coating gets **3.2× worse** from 0° to
   80°; our model gets slightly better. Every grazing claim we have made is wrong in
   sign as well as magnitude.
3. **We now have a validation target we never had.** A flat plate in our harness must
   read **1.00% at 0°, 1.43% at 60°, 3.18% at 80°**. Fit the material model to that
   curve and put it in `lock.py` as the material-model check — the same way
   `flat_coating` already guards the geometry.
4. **`[추측]` Coating and geometry may not be separable.** Weaker than I first wrote.
   The viper result is verbatim and does say *"preserves the black colour and further
   diminishes reflectance"* `[확인 Mouchet p.8]` — but Mouchet frames it as "supports
   the idea that", and it is a review's paraphrase of ref [87]. The butterfly result
   says only that gold *"does not lead to an **increase** in light reflectance"*
   `[확인 Mouchet p.3]` — which is not "reduced", and whose primary source (Davis p.3)
   is a qualitative SEM-prep observation, that the scales "retained their black color
   when coated with gold", **not a reflectance measurement**. So this rests on one
   review paraphrase, not two results. Still worth acting on cheaply — sweep gloss
   against each new geometry rather than inheriting 0.30 — but do not present it to a
   client as an established finding.
5. **Consider flocked fabric for the large faces.** 8× darker than paint and nearly
   flat with angle `[Filip Fig. 6]`. It cannot line a 0.4 mm cone tip, but it can line
   a large cavity — and with a fabric liner the geometry has far less work to do.

## B. Metrics — our current ones cannot rank these structures

6. **Adopt TIS and effective albedo** `[Filip eqs. 2–3]`. Published definitions with
   measured values for six real materials, so our panel becomes comparable to
   something other than itself.
7. **Stop scoring directional designs on a symmetric metric.** The bird-of-paradise
   tilt is *designed* to be a directional bias `[Mouchet p.7]`; "worst over all
   angles" guarantees it loses. Either score it directionally, or settle the rig's
   real beam distribution first. **Our earlier "tilt is worse" conclusion should be
   marked as metric-dependent, not as a property of tilt.**
8. **Peak returned radiance remains the real objective** (from the Phase-1 plan), and
   Filip's Fig. 8 supports it: material ranking changes with light intensity, and our
   regime is their 100×.

## C. Geometry candidates, now with sources

**Every row whose source is Mouchet is a REVIEW's paraphrase of someone else's
measurement.** That flag has to travel to the point of use, not just sit in the
section header — two of the most counter-intuitive claims in this folder are review
paraphrases, and one of them demonstrably drifted in transmission.

| candidate | what the literature actually says | source |
|---|---|---|
| **Paraboloid instead of cone** | lowest reflectance of conical / paraboloidal / Gaussian — but of **compound-eye corneal nipples at ~200 nm**, sub-wavelength | review → Stavenga 2006 [21] |
| ~~Height disorder~~ | **RETRACTED** — the quote is about *G. oto* glasswing **transparency**, sub-wavelength, not blackness and not *C. ossa* | review → Siddique 2015 [59] |
| **Randomly placed rounded pillars** | ellipsoidal, randomly located micropillars; 99.5% absorptance | Mouchet p.7, Fig. 6 |
| **Tent / opposed inclined faces** | inclined scales touching at the tips; "several reflections on opposite inclined patterned scales" | Mouchet p.7, Fig. 5 |
| **Tilted deep cavities** | barbules tilted ~30°, cavities 5–30 µm × 200–400 µm, aspect ~7–80, **directional bias** | Mouchet p.7, McCoy ref 36 |
| **Sparse high-surface-area volume** | "sparse material with high surface area"; structure works even when non-absorbing | Davis abstract, Fig. 4 |
| **V-cavity (what we already built)** | **the V-cavity model fits the viper's PALE scales**; its black scales are explicitly contrasted with it | review → ref [87] |

**Do NOT retry:** flank serration, moth-eye grading, or any sub-wavelength mechanism.
Moth-eye is explicitly sub-200 nm `[Mouchet p.5]`, and mm-scale hierarchy has now
failed twice in this project. The one hierarchical idea that is *not* a third variant
of the same thing is the sparse-volume candidate, because its mechanism is ray-optical
multiple scattering rather than index grading.

## D. Aspect ratio reality check

Bird-of-paradise cavities run aspect **7–80** `[Mouchet p.7]`. Our best design is
depth 30 / pitch 7.5 = **4**. Our own measurement says A≥6 is needed to hold at all
angles. **Nature is operating far deeper than we are, in relative terms** — which
says the 30 mm depth constraint, not the shape, may be the binding limit. Worth
quantifying what aspect 8–12 would cost in printability at a 0.4 mm nozzle.
