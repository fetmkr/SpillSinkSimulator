# Peer review — "Nine ways to stop a wall from repeating the artwork"

Reviewer: hostile external referee, Optics Express / Applied Optics / Optica level.
Date: 2026-08-12. Material reviewed: `CONTEXT.md`, `metrics/*`, `reference/SUMMARY.md`,
`results/analysis_shapes.md`, `results/FINDINGS_*.md`, `report/2026-08-12/report.html`,
`scripts/blender_render.py`, `scripts/geom_topo.py`, `scripts/sweep_topo.py`,
`scripts/build_report_html.py`, and `results/sweep_topo.csv` (7110 rows, re-analysed
independently for this review).

Tags: `[확인]` verified in a named file at a named line · `[추측]` my inference ·
`[모름]` unknown to me.

---

## VERDICT — **reject as-is**

**Reject as submitted.** Not because the work is bad — the internal methodological
discipline here is better than most submissions I see, and four of the defects the
authors found themselves would have survived review at many journals — but because the
central result of the paper as presented is **an artifact of an uncontrolled variable
the authors already knew about and had already been burned by once.** The reported
winner (shingle, 0.1825 %, "29 % better than the best cone") is compared against a cone
whose minimum feature is **8× larger**: 0.05 mm plate edge against a 0.4 mm cone tip
`[확인 sweep_topo.csv params_json; report/2026-08-12/report.html rank 1 and rank 12]`.
Hold both to the same 0.4 mm manufacturable feature and **the incumbent cone wins**:
0.2580 % (rank 87) against the best printable shingle's 0.2690 % (rank 96) — the
reported conclusion inverts `[확인 re-analysis of sweep_topo.csv, below]`. This is
precisely the error `CONTEXT.md:503–522` records the project catching in the
2026-08-11 "fair fight" and resolving by tip-matching; it has been repeated one level
down. Beyond that, the paper's one mechanism figure asserts a crossing that does not
occur in the data it plots, the top four entries are separated by 0.18–0.76 % against
a family self-consistency of 3.5 %, there is not a single independent replicate
anywhere in the dataset, the paper's own stated first priority (form) is not measured
by the reported figure of merit at all, and there is no experiment. A shorter,
much weaker, and genuinely publishable paper is buried in this material; see the last
section. Getting to it means abandoning the "we found the best panel" frame entirely.

---

# Objections, ordered by how fatal

## 1. FATAL — The headline ranking is a ranking of minimum feature size, not of topology

The report's answer is `SHIN_p0750_d80_t06_o114_k050`, 0.1825 %, "29 % better than the
best cone, re-measured in the same frame at 0.2580 %"
`[확인 report/2026-08-12/report.html, extracted text lines 29–36]`.

I extracted the minimum feature of every design in `results/sweep_topo.csv` from its
`params_json` and re-ranked `[확인 my analysis]`:

| rank | design | score | min. feature |
|---|---|---|---|
| 1–6 | `SHIN_p*_d80/d100_*_k050` | 0.1825–0.1917 % | **0.05 mm** plate edge |
| 7 | `SHIN_p0550_d50_t02_o114_k020` | 0.1999 % | **0.02 mm** |
| 8–20 | shingles / `HONE_*_wt005` | 0.2025–0.2102 % | **0.05 mm** |
| **87** | **`CONE_p0375_d30`** | **0.2580 %** | **0.40 mm** tip dia. |
| 95 | `CELL_NEST_p1100_d50_ln00` | 0.2669 % | 0.40 mm |
| **96** | **`SHIN_p0550_d50_t02_o114_k400`** | **0.2690 %** | **0.40 mm** |
| 117 | `HONE_p0750_d50_wt040_wb040_ln00` | 0.2863 % | 0.40 mm |

**Every one of the top 86 designs is unmanufacturable by the project's own stated
process floor** (0.4 mm nozzle, `results/FINDINGS_printability.md:106–110`: "tip_radius
= 0.2 is exactly one nozzle width, so 0.437 mm is a single extrusion with essentially
zero margin ... tip radius cannot go lower on FDM"). The report knows this and says so
in a footnote — "These are optics probes, not buildable parts; the printable edge is
0.4 mm" `[확인 report.html extracted line 453–456]` — and then ranks on them anyway,
puts one on the cover, and quotes its margin over a design that *was* held to the
floor.

The size of the confound is measured inside the authors' own sweep. Same shingle
design, same pitch, depth and tilt, edge thickness only:

    SHIN_p0550_d50_t02_o114_k020   edge 0.02 mm  ->  0.1999 %   (rank 7)
    SHIN_p0550_d50_t02_o114_k400   edge 0.40 mm  ->  0.2690 %   (rank 96)

**1.35× from the edge thickness alone** `[확인 sweep_topo.csv]` — larger than the entire
1.41× the report claims over the cone.

Feature-matched at 0.4 mm, the nine families collapse into a band:

    cone (incumbent)      0.2580 %
    nested cell           0.2669 %
    shingle (the winner)  0.2690 %
    square cell           0.2736 %
    mixed cell            0.2796 %
    re-entrant cell       0.2815 %
    honeycomb             0.2863 %
    triangle cell         0.3286 %
    strut lattice         0.4729 %

Seven of nine families inside 1.11×, and the shingle 4.3 % *behind* the cone — which
is inside the noise (objection 3). **The correct conclusion from this sweep is that at
manufacturable feature size, no topology beats the incumbent by more than the
measurement error.** That is a real and interesting result. It is the opposite of what
was written.

Note this cuts both ways and the authors must say so: the cone was never measured at a
0.05 mm tip either, so I cannot claim the cone wins — only that **the comparison as
performed cannot support any ordering** `[추측, but the k020/k400 series makes the
direction certain]`.

**Fix.** Re-run the ranking on a grid where minimum feature is an explicit, matched
axis: every family at {0.05, 0.1, 0.2, 0.4, 0.8} mm minimum feature, and report
ρ_dh *versus* minimum feature per family. If the families separate at 0.05 mm and
converge at 0.4 mm, that is publishable and says something about the physics. If they
stay converged, say so. Either way the cover claim goes.

---

## 2. FATAL — The paper's one mechanism figure plots two curves that do not cross, and its caption says the answer is set by where they cross

`scripts/build_report_html.py:91–97` states the chart's purpose: *"the two coating
models want opposite tilts, so the design that survives both is set by where the curves
cross, not by either one's own optimum."* Line 160 selects the series:
`series = tilt_series(best, "0750", "80")` — pitch 7.5, depth 80, i.e. the winning
cell `[확인]`.

That series, read out of `results/sweep_topo.csv` `[확인 my analysis]`:

| tilt° | 2 | 4 | 6 | 7 | 8 | 12 |
|---|---|---|---|---|---|---|
| d00 (specular) | 0.1510 | 0.1272 | 0.1061 | 0.0917 | 0.0780 | 0.0472 |
| d100 (diffuse) | 0.1838 | 0.1828 | **0.1825** | 0.1829 | 0.1891 | 0.2157 |

**d00 is below d100 at every tilt measured. The curves never cross.** The
worst-of-both score equals d100 throughout, and the "best worst-case · 6°" marker is
simply the minimum of the d100 curve. I checked all nine (pitch, depth) tilt series:
a crossing exists at (5.5, 30), (7.5, 30) and (7.5, 50) — none of which is the
winner — and does not exist at any depth-80 or depth-100 cell `[확인]`.

The same thing shows in the ranking as a whole: **d100 sets the combined score for
10 of the top 10, 20 of the top 20, and 48 of the top 50** `[확인]`. d100 is
`coating_split(1.0)` — a pure Lambertian body of albedo 0.998 % with no Fresnel term
and no angular structure whatsoever `[확인 blender_render.py:228–231, 224–225]`. So the
entire head of the ranking is decided by a diffuse-cavity view-factor problem in which
plate tilt between 2° and 8° changes the answer by 0.71 %, and the paper's narrative
about specular redirection — which is real, and is what d00 shows — **does not touch
the score at all.**

A referee reading the figure against the CSV finds this in ten minutes. It reads as
a story imposed on data that does not support it, which is far more damaging than the
error itself.

**Fix.** Either (a) plot a cell where the crossing genuinely occurs and say plainly
that the reported winner is *not* in that regime, or (b) drop the crossing narrative
and report the true structure: under the diffuse extreme the score is a cavity
view-factor problem that is nearly flat in tilt; under the specular extreme tilt is
strongly beneficial; the two arms are not reconciled by any design in this grid, only
by the arbitrary choice to score on the worse of them.

---

## 3. FATAL — Zero replicates; the top of the ranking is a tie by a factor of ~6600 in N

The project's own stated floor is ~1.3 % `[확인 results/analysis_shapes.md:204–206;
FINDINGS_control_overlap.md:54–56]`. That floor is too generous for this sweep, and
the ranking is far inside even the generous version.

**(a) There are no independent replicates anywhere.** `blender_render.py:97` pins
`SEED = 0` and `sweep_topo.py` never passes `cycles_seed`; `geom_topo.TopoParams.seed`
is `23` for every design `[확인 geom_topo.py:157]`. I found two accidental duplicate
rows in the CSV where a design was written twice with byte-identical parameters
(`CELL_REEN_p0550_d30_ln06`, `SHIN_p0550_d30_t02_o114_k050`): **all 30 repeated cells
agree to 0.00 %** `[확인]`. The pipeline is fully deterministic. **N = 1 for every
number in the paper, on both the Monte Carlo and the geometry-realisation axes.**

**(b) The realisation error is ~20× the Monte Carlo error, and only the second one is
under control.** In-frame control σ/μ over shingle rows is 0.181 % `[확인]` — that is
the Cycles noise at 64 spp `[확인 sweep_topo.py:68]`. But the shingle is specified
*statistically* (`azimuth_jitter = 180.0`, `jitter = 0.30`
`[확인 geom_topo.py:156,168]`), so ±θ pairs must agree up to realisation noise. They do
not: over the 140 round-5 shingle designs, median |ρ(+40)/ρ(−40) − 1| = **3.49 %**,
mean 7.66 %, max 59.8 % `[확인]`. Per-topology, the shingle is the worst offender
(median 3.57 %, p90 17.3 %) against honeycomb 0.36 % `[확인]`. Converting: σ per single
measurement ≈ **3.7 % relative** `[추측, from median|dev| = 0.674σ and √2 for the pair]`.

The proximate cause is visible in the harness: the measurement window is
`MEAS_INSET_X = 0.20`, `MEAS_INSET_Z = 0.30` of a 60 mm face
`[확인 blender_render.py:99–100; sweep_topo.py:67]`, i.e. **36 × 24 mm = 864 mm²**. At
pitch 7.5 mm that is **~18 cells** `[확인 arithmetic]`, each with an independent random
azimuth. Eighteen draws is not an ensemble.

**(c) What that does to the ranking.** Minimum detectable difference at α = 0.05,
power 0.8, with N independent realisations per design is 2.8·σ·√(2/N). At σ = 3.7 %:

| separation to establish | pair | required N per design |
|---|---|---|
| 0.18 % | #1 vs #2 | **≈ 6600** |
| 0.26 % | #1 vs #3 | ≈ 3200 |
| 0.76 % | #1 vs #4 | ≈ 370 |
| 3.61 % | #1 vs #5 | ≈ 17 |
| 9.54 % | #1 vs #7 | ≈ 3 |

**Of the nine separations inside the reported top ten, six exceed the 3.49 % family
floor and three do not** `[확인]`. Ranks 1–4 are one equivalence class; ranks 1–5 are
arguably one. The report presents them as an ordered list with four significant
figures and puts rank 1 on the cover with a named tilt of 6°.

Independent corroboration that 6° is noise: at pitch 5.5 / depth 80 the minimum is at
tilt **2**; at pitch 3.75 / depth 80 it is at tilt **4**; at pitch 7.5 / depth 80 it is
at tilt **6** `[확인]`. A physical optimum does not wander across neighbouring pitches
by the full width of the sampled range.

**Fix, concretely.** (i) More samples per frame buys nothing — the Monte Carlo error
is already 20× below the realisation error. Spend the budget on **≥ 12 independent
geometry seeds** per design and report mean ± SEM; that resolves ~4 % differences,
which is honest. (ii) Enlarge the face and the window so the window holds ≥ 200 cells,
not 18 — this is the cheaper fix and attacks the cause rather than averaging over it.
(iii) State a resolution limit in the abstract and collapse everything inside it into
a single reported equivalence class ("all shingles with depth ≥ 50 mm and pitch
3.75–7.5 mm: 0.18–0.21 %"). (iv) Report the ±θ asymmetry as the error bar, per family,
in the figure.

**Also a data-integrity defect found while doing this.** `sweep_topo.tag_for()`
(lines 380–384) omits `tilt_jitter` from the shingle tag. Eight tags in
`results/sweep_topo.csv` therefore carry 2–4 physically different designs
`[확인]` — e.g. `SHIN_p0550_d50_t06_o114_k050` holds four geometries whose θ=0 d100
values span 16.7 %. Both `done_tags()` (:395–399) and the report's `load_scores()` key
on tag, so a resumed run would have silently skipped designs, and the report conflates
these four into one ranked entry (rank 25). Not in the top 20, so it does not change
the headline — but it must be fixed and disclosed.

---

## 4. FATAL for the claim size — There is no experiment, and the physics that decides the answer is exactly what is unmeasured

### 4a. What the material model is fit to, and why that is not enough

`make_coating()` is a two-parameter fit — an angle-independent Lambertian body plus a
scaled dielectric Fresnel lobe — to **one published curve**: Filip & Vávra's THR of a
brush-applied Musou Black *flat plate* versus incidence angle
`[확인 blender_render.py:137–202; reference/SUMMARY.md §1]`. The authors state the
limitation themselves and correctly:

> "the fit constrains only ρ_dh(θ) of a *flat plate*. Nothing in it constrains BRDF
> shape or multi-bounce behaviour — and multi-bounce is what every cavity number
> depends on. Neither material model is validated where it matters."
> `[확인 metrics/01_rho_dh.md:85–89]`

**Quantify how bad.** The undetermined direction is the diffuse fraction *d* at fixed
ρ_dh(0), and the authors have measured its leverage: designs move by **2× to 41×** and
**the ranking inverts** `[확인 metrics/01_rho_dh.md:63–75]`. In the present sweep, d00
and d100 differ by **44.2× and 4.67× in dynamic range respectively**
`[확인 analysis_shapes.md:56–59]`, d00's grazing ceiling is 24.95 % against d100's
0.998 % `[확인 analysis_shapes.md:50–53]`, and 39 rows read *above* the 5 % matte
control `[확인 analysis_shapes.md:207–215]`. **The single unmeasured parameter moves
the answer by up to 41×; the entire geometry search moves it by 1.5× at matched
feature size (objection 1).** The paper is optimising a variable 27× less important
than one it has not measured. A referee will phrase it exactly that way.

Worse: the split is not merely uncertain, it is **chosen**. `coating_split(d)` pins
both arms at the one angle where they agree — ρ_dh(0) — and lets them diverge 25×
everywhere else `[확인 blender_render.py:228–231; analysis_shapes.md:216–221]`. So the
"worst of three materials" rule is not a robustness envelope; it is a specular-only
rule for 170/196 designs in `sweep_shapes` and a **diffuse-only rule for 48/50 of the
top 50 here** `[확인]`. Two different sweeps, two opposite effective rules, same stated
methodology. That must be disclosed and explained, not presented as "holds up under
either assumption".

### 4b. Is there published data that would constrain it? Yes, and it is not cited

`[확인 reference/ contains exactly three PDFs: 2601.05094v1, 2404.18169v1,
s41467-020-15033-1]` — a preprint on black-material reflectance and two bio-inspired
reviews/papers. Nothing else.

What would constrain multi-bounce behaviour is the **BRDF itself, not its hemispherical
integral**. Filip & Vávra measured the full BRDF on a gonioreflectometer — 24 488
samples per material, θ_v 0–85° in 1° steps, azimuth 0–360° in 10° steps
`[확인 reference/SUMMARY.md §"Measurement setup"]`. **That dataset, not the THR curve
derived from it, is what the model should be fit to.** The paper's own §3.3 reports
R_s and R_d separately and a TIS with a 5° specular exclusion cone
`[확인 reference/SUMMARY.md, eq. 3, p.4]` — TIS = R_d/(R_s+R_d) *is* the diffuse
fraction, measured, for six real materials including Musou paint. The authors read that
definition, filed it under "worth adopting" `[확인 SUMMARY.md:164–178]`, flagged that
the paper's TIS text contradicts its own figure, and then **did not use the figure to
pin the split.** That is the single cheapest, highest-value fix available and it needs
no laboratory: read the TIS panel of Fig. 6 at 400 dpi the way the rest of that file
was read, and set *d* from it with a stated uncertainty band. `[추측 that it is
readable — the authors report reading other panels of the same figure]`

The other published constraint the paper ignores entirely: **classical diffuse-cavity
theory**. The d100 arm is a pure Lambertian problem with a closed-form answer
(Gouffé / integrating-sphere, ρ_eff = ρf/(1−ρ(1−f)), f = A_aperture/A_total). I ran it
for the printable honeycomb `HONE_p0750_d50_wt040_wb040_ln00`, pitch 7.5, depth 50,
wall 0.4, ρ = 0.00998 `[확인 my calculation]`:

    A_cell 48.71 mm²   A_inner 43.66   A_total 1273.4   f = 0.0343
    cavity  ρ_eff = 0.0345 %   +   exposed wall tops 10.38 % × ρ = 0.1037 %
    predicted total  0.1346 %      rendered (d100, θ=0)  0.1122 %      ratio 0.83

**The renderer agrees with closed-form cavity theory to 17 % on a first-order estimate
that neglects the tube's aspect ratio.** This is the best validation result in the
project and it is not in the paper, because it was never run. Put it in. It is the
figure that lets a simulation-only paper survive review.

### 4c. What is missing as physics, beyond the coating

- **No polarisation** `[확인 metrics/01_rho_dh.md:47]`. The application is laser
  projectors; projector output is typically strongly polarised, and Fresnel at the
  grazing angles that dominate a deep cavity is strongly polarisation-dependent. A
  reviewer will not accept "unpolarised" for a laser paper without a bound on the
  error.
- **No wavelength** — one broadband grey channel against an RGB-weighted 380–700 nm
  measurement `[확인 metrics/01:46; SUMMARY.md caveat 2]`. Lasers are narrow-line.
- **No coherence, therefore no speckle.** This is the one I would press hardest.
  The paper's stated priority is destroying the *form* of a coherent laser image
  returned from a mm-scale random structure. Cycles is an incoherent path tracer; it
  cannot represent speckle, and speckle from a random mm-scale surface under coherent
  illumination is a first-order determinant of what the wall copy actually looks like.
  Nothing in `metrics/` acknowledges this. `[확인 by absence across metrics/*.md]`
- **Angular range truncated at ±40°.** `THETAS = (0, ±20, ±40)`
  `[확인 sweep_topo.py:70]`. The project's own earlier data shows the worst-over-all-
  angles figure is **9× the ±40° figure** (0.2660 % vs 0.0293 %,
  `[확인 CONTEXT.md:149–152]`) and the fitted coating rises **3.2× from 0° to 80°**
  `[확인 reference/SUMMARY.md, Filip Fig. 6 table]`. The report's headline
  "0.1825 %" is therefore a best-case band, presented without that qualifier
  `[확인 report.html line 22–24: "Ranked on the worst reflectance across incidence
  angles 0°, ±20° and ±40°"]` — it is stated, but the abstract-equivalent and the
  cover number are not qualified. The rig's actual incidence distribution is never
  given, so ±40° is unjustified. Extend to ±80° or justify the truncation with the
  rig geometry.
- **The coating is assumed to reach the root of a 50–80 mm deep, 5 mm wide cell.**
  `[확인 metrics/01:48–49, "Unverified until a coupon is printed and measured"]`. The
  source paper explicitly warns about this: acryl paint's anomaly is attributed to
  *substrate showing through a thin/uneven film* `[확인 SUMMARY.md, Filip p.7]`. At
  aspect 10–20 a brushed or sprayed coating will not be uniform. If the root reads
  5 % instead of 1 %, every cavity number is wrong by more than the entire geometry
  search.

### 4d. What experiment settles it, and what the minimum is for publication

For a claim of this size (a recommended panel design with quoted absolute
reflectances), an optics journal will demand **fabricate and measure**. The minimum
that would satisfy me:

1. **One 100 × 100 mm printed coupon** of the recommended design plus **a flat plate of
   the same coating from the same batch**, both measured on the same instrument. The
   exporter already produces exactly this `[확인 CONTEXT.md:464 export_cone.py, "STL:
   union, trim to face, tileable, 100 x 100 only"]` — with the caveat that
   `FINDINGS_printability.md:40–52` shows the shipped exporter runs `height_seg = 3`,
   at which "the exported solid is not the profile that was designed."
2. **ρ_dh(θ) at θ = 0, 20, 40, 60, 75, 80°** on an integrating sphere with a rotating
   sample holder, or a goniometer. This is the *identical* quantity `hemi_view`
   computes, so it is a direct one-to-one test with no conversion
   `[확인 metrics/01:12–14]`. Predicted vs measured, one figure, no fitting.
3. **Flat-plate BRDF of the actual coating** at ≥3 incidence angles, integrated to give
   the diffuse fraction *d*. This kills objection 4a outright and costs one afternoon
   on any goniometer.
4. **Coating-reach verification**: section the coupon and measure ρ at the cell root
   versus at the rim.

Items 2–3 are a week of instrument time and turn this from a rejected manuscript into
a strong Applied Optics paper.

**Is a simulation-only version publishable?** Yes — in Applied Optics or OSA Continuum,
*not* in Optica — but only if (a) the analytic cavity cross-check of §4b is included as
a validation figure, (b) the claim is reduced to a *sensitivity* result rather than a
design recommendation, and (c) no absolute reflectance is quoted as a property of a
real panel. See the last section for the exact claim that survives.

---

## 5. SERIOUS — The reported figure of merit does not measure the paper's stated first priority

`CONTEXT.md:18–23` states the priority order: **(1) destroy the FORM of what returns;
(2) reduce total reflected light.** The reported ranking measures only (2)
`[확인 report.html: "This run ranks on total reflectance only"]`.

The state of the form metrics:

| metric | status | defect |
|---|---|---|
| 02 smear rms | live | "At θ=0 ... rms is near the control floor for everything and **cannot rank designs. This is the unsolved axis.**" `[확인 metrics/02:48–51]` |
| 03 core fraction | **RETIRED** | denominator shrinks with the thing it measures; a *more* smeared design scores *better*; cost two reports `[확인 metrics/03:14–31]` |
| 04 peak radiance | live, "**proposed as the primary figure of merit**" | "first results are striking and **not yet trusted**"; groove numbers may be a stripe-phase artifact; needs N ≥ 12 phases `[확인 metrics/04:3–4, 65–84; CONTEXT.md:614–616]` |
| 07 MTF | live, known defect | `\|F\|` discards phase, so a smear that is *shifted* is not penalised; FWHM helper collapses to one pixel `[확인 metrics/07:31–36]`; and it "**under-reports**" azimuthal spreading, which is the 3D families' whole mechanism `[확인 metrics/07:45–47]` |

So: the metric declared primary is untrusted, the metric that replaced the retired one
is untrusted, the one that works cannot rank at the critical angle, and the reported
ranking uses none of them.

**Would a referee accept ρ_dh as the figure of merit?** For a paper claiming "we reduced
total reflectance", yes — it is a standard, well-defined, directly measurable quantity
and the authors handle it carefully. For a paper claiming "we stopped the wall
repeating the artwork", **no**. Those are different papers and only the first one is
supported.

The demonstration of why this matters is in the authors' own data: re-scored at θ = 0
alone — the collinear, form-critical angle where "one bounce cannot displace a photon"
`[확인 metrics/02:48–51]` — **the ranking moves substantially**: the reported winner
falls from rank 1 to rank 27, and `HONE_p0550_d100_wt015` rises from rank 77 to rank 7
`[확인 my analysis]`. A figure of merit whose ranking is unstable against restriction to
the physically decisive angle needs justification the paper does not give.

**Fix.** Either (a) build the response matrix H(z_out; z_in) at ≥ 40 input positions
and the synthesised bar-contrast-vs-period-and-phase that `CONTEXT.md:357–360` already
specifies, and report a two-axis Pareto front (ρ_dh, contrast at the artwork's stroke
width) — this would be the paper's most novel content; or (b) delete every claim about
form, retitle, and say in the introduction that form destruction is out of scope. (b)
is acceptable. Silence is not.

---

## 6. SERIOUS — Novelty is close to zero as framed, and the prior-art search has a hole the size of the field

`reference/` contains three PDFs `[확인]`: Filip & Vávra 2026 (black material
reflectance), Mouchet 2024 (bio-inspired IR absorbers, a review), Davis 2020 (butterfly
scales). All three are materials/biology. **There is not one stray-light engineering
reference in the folder** — no Breault vane-baffle design, no Gouffé cavity theory,
no Sparrow & Lin or Hollands V-groove analysis, no honeycomb light-trap literature,
no commercial black-surface data (Acktar, Vantablack, Metal Velvet), no ASTM/SPIE
stray-light standard. `[확인 by inspection of reference/ and by grep over all .md for
"baffle|vane|louver|stray light|Gouffé|Sparrow|Hollands|integrating sphere" — the only
hits are two informal mentions of "beam dump" from an RP Photonics encyclopedia page,
CONTEXT.md:116 and :366]`

This matters because **the reported winner is a vane baffle.** "Overlapping inclined
plates, tilted off the panel normal, knife-edged at the mouth" is the standard vane /
louvre baffle of every telescope baffle tube, in the literature since the 1970s, with
established design rules for exactly the quantities measured here (edge exposure,
tilt angle, overlap, and the knife-edge requirement). The honeycomb family is the
commercial honeycomb light trap. The cone in a ribbed canister is the textbook beam
dump, which the authors do cite informally. The V-groove is classical cavity theory.
The strut lattice is open-cell foam.

Asked directly: **is "irregular inclined plates at mm scale, evaluated in ray optics" a
contribution?** As stated, no — it is a competent engineering exercise re-deriving a
known baffle geometry, with the added liability that the derivation currently gets the
sign of the comparison wrong (objection 1). A referee who knows the baffle literature
will reject on novelty alone even if every number were sound.

**What here could be a contribution — three candidates, in order of strength:**

1. **The material-model sensitivity result.** "The diffuse fraction of a nominally
   1 %-reflectance black coating, at fixed hemispherical reflectance, changes cavity
   ρ_dh by up to 41× and inverts the design ranking." `[확인 metrics/01:63–83]` This is
   a genuine, quantitative, general and slightly alarming statement about how
   stray-light structures are simulated. It says that everyone fitting a black coating
   to a hemispherical curve and then simulating a cavity with it is doing something
   underdetermined. **I have not seen this stated quantitatively anywhere.** `[모름 —
   I did not search external literature for this review; the authors must.]` This is
   the paper.
2. **The falsification of the exposed-area law for pillar arrays.** But see objection 7:
   as stated it is over-claimed.
3. **The negative result that nine topologically distinct families converge within
   1.11× at matched minimum feature size.** Modest, but honest and useful, and it is
   what the data actually shows.

Candidate 1 is publishable. Candidates 2 and 3 are supporting sections of it.

---

## 7. The "exposed area no longer predicts anything" claim is over-generalised

The report's second-largest section says: "Across these nine families the exposed area
spans 24× while the score spans only 2.6×, and they do not even rank in the same
order" `[확인 report.html lines 329–339]`, concluding that "Shrink the tip is no longer
the primary design move".

The comparison is made on the *combined worst-θ-over-three-materials score*. The law it
falsifies was established on **head-on** reflectance `[확인 CONTEXT.md:73–79]`. I tested
the law on the quantity it was actually about — θ = 0 under d100 — using the best
member of each family `[확인 my analysis]`:

| family | exposed % | predicted = exp × ρ | measured ρ_dh(0) | meas/pred |
|---|---|---|---|---|
| honeycomb | 1.33 | 0.0133 % | 0.0197 % | 1.48 |
| shingle | 1.77 | 0.0177 % | 0.0301 % | 1.70 |
| mixed cell | 8.60 | 0.0858 % | 0.0956 % | 1.11 |
| square cell | 10.67 | 0.1065 % | 0.1164 % | 1.09 |
| re-entrant cell | 10.67 | 0.1065 % | 0.1572 % | 1.48 |
| triangle cell | 18.48 | 0.1844 % | 0.1828 % | **0.99** |
| nested cell | 21.32 | 0.2128 % | 0.0977 % | 0.46 |
| truss | 8.63 | 0.0862 % | 0.2168 % | 2.52 |
| **cone** | **1.03** | **0.0103 %** | **0.1000 %** | **9.71** |

The law holds to within 1.0–1.7× for every wall-network topology across a 14× span in
exposed area, and fails by **9.7× for exactly one family: the cone.** That is not "area
predicts nothing"; that is "**the pillar array's return is not its tip disc**" — which
is the conclusion the project already reached independently and correctly in the fair
fight: "Scales like r, not r² -> the return is the flank near the tip, not the tip
disc" `[확인 CONTEXT.md:518–519]`.

Same correction applies to the honeycomb smoke test. `FINDINGS_topo_smoke.md` reports
the prediction "off by a factor of 27" — but the prediction's error there is
overwhelmingly in the *cone* reference (9.7×), not the honeycomb (1.5×) `[확인]`.

**Fix.** Restate as: the exposed-area law is a good first-order predictor
(within ~1.5×) for wall-network topologies and fails by an order of magnitude for
pillar arrays, because a rounded pillar's return comes from the flank near the tip
rather than the tip disc. That is a sharper, defensible, and more useful statement than
the one in the report, and it costs nothing.

---

## 8. Reproducibility and disclosure

What is currently **not** reproducible by a third party `[확인 by inspection]`:

- **Blender version, Cycles build, GPU/CPU device and OS are recorded nowhere in the
  CSV or the report.** `configure_cycles()` selects GPU by default
  (`blender_render.py:688`). Cycles results are not bit-identical across devices or
  versions, and with `SEED = 0` fixed and N = 1, device-dependence is
  indistinguishable from signal. Must be pinned and stated.
- **`renders/` is gitignored (5.7 GB)** `[확인 CONTEXT.md:477]`, so the EXRs behind
  every number are unavailable. That is defensible; the CSVs are the artifact. But then
  the CSV must carry seed, spp, resolution, Blender version, and margin per row — it
  currently carries none of them (`FIELDS`, `sweep_topo.py:75–77`).
- **The report is not gated.** `CONTEXT.md:618–621` records `lock.py` + `gate.py` as the
  precondition machinery and that `make_report.py` is **DISARMED** because it
  hard-coded two withdrawn claims. `build_report_html.py` mentions the gate only in a
  string of prose it emits (line 376) — I found no call into `gate.py` or `lock.py`
  `[확인 grep]`. And `lock.py`'s control assertion is known to be invalid
  `[확인 FINDINGS_control_overlap.md:56–58]`. So the report that carries the claims is
  ungated, by a mechanism the project built specifically to prevent this.
- **`results/sweep_topo.csv` has 8 tag collisions** conflating distinct designs
  (objection 3). A third party rebuilding "the rank-25 design" from its tag gets one of
  four different geometries.
- **The exporter does not build the geometry that was measured.** The sweep uses
  `height_seg = 12`; `export_cone.py` ships `height_seg = 3`, at which "the exported
  solid is not the profile that was designed" `[확인 FINDINGS_printability.md:40–52]`,
  and the shipped export carries a known 0.649 % unsupported-area defect at the slab
  edge, deliberately not fixed `[확인 FINDINGS_printability.md:56–77, 100–104]`.

**Minimum release for publication:** the three sweep CSVs with per-row seed/spp/version
columns; `blender_render.py`, `geom3d.py`, `geom_topo.py`, `geom_cell.py`, the sweep
drivers, `validate.py`, `test_floor.py`, `test_tessellation.py`,
`test_control_gap.py`, `fit_coating.py`, `printability.py`; the coating node graph as
a standalone Blender file; the STL of every design in the reported table; the exact
Blender version and device; and a `README` reproducing one row end-to-end. Deposit in
Zenodo with a DOI. `[추측 on journal policy specifics; Optica-family journals require
data availability statements and increasingly enforce them for simulation-only papers]`

---

## 9. The four defects found are reassuring; here is what has NOT been checked

Found and documented, to the authors' credit `[확인 report.html lines 402–437 and the
FINDINGS files]`: the hexagon-not-honeycomb tessellation defect, the control plate
embedded in the panel field, the 5° tilt clamp, the leaning-cell wall dropout. Plus,
earlier: the tessellation glint, the margin/background defect, the base-gap defect, the
slab-clearance defect, the hseg-3 void, the stripe-phase artifact.

**Ten defects, every one of which first presented as an interesting result.** A referee
reads that list and asks the obvious question: what is the base rate, and what is still
in there? These are the checks I would require before I believe any number:

1. **Seed sensitivity of the geometry.** The single most important missing check. Every
   design in the paper is one draw of `seed = 23`. Re-run the top 20 at 12 seeds. If
   the ranking reshuffles — and objection 3 says it will — that is the result.
2. **Cycles device/version cross-check.** Same design, CPU vs GPU, two Blender
   versions. Must agree to better than the claimed resolution.
3. **Spp convergence at 64 on *these* geometries.** `CONTEXT.md:60–61` records the
   convergence check ("samples 384 / 1536 / 6144 — already converged at 384") but the
   production sweeps run at **64** `[확인 sweep_topo.py:68; sweep_shapes.py:49]`, on a
   different geometry class, and no convergence test at 64 exists for the topo
   families. Re-run the top 10 at 64/256/1024 spp.
4. **The unexplained −15 % margin sensitivity.** `sweep_topo.py:73` and
   `FINDINGS_control_overlap.md:79–83`: "margin 1.0 moved head-on by −15 % and the
   reason is not yet understood, so it stays." **An unexplained 15 % sensitivity to a
   parameter of the measurement setup, in a paper whose top separations are 0.18 %, is
   disqualifying on its own.** Sweep margin_depths at 3, 6.5, 10, 15 and explain the
   curve. If it is still moving at 6.5, every number is margin-dependent.
5. **The systematic −0.85 % ±θ asymmetry at zero tilt.** Documented as open, cause
   suspected (lattice sampling at pitch 11), **untested**
   `[확인 analysis_shapes.md:222–232, 269]`. My re-analysis of `sweep_topo.csv` shows
   the mean +40/−40 ratio is 1.0126 with all three materials biased the same way
   (d00 1.0147, d76 1.0120, d100 1.0111) `[확인]` — same signature, opposite sign,
   larger. Two seeds settles it.
6. **The energy check at 85°.** No design has been measured past 40° in this sweep;
   `analysis_shapes.md:207` reports 39 rows already exceeding the 5 % matte control
   at ±40 under d00, with a ceiling of 24.95 %. Extend to 80° and verify no design
   exceeds the flat plate of its own coating anywhere.
7. **Window-size sensitivity.** `MEAS_INSET_X/Z` are 0.20/0.30 with no stated
   justification for the asymmetry beyond a code comment ("fins run past the panel
   there", `blender_render.py:100`). Sweep the inset and show ρ_dh is flat in it.
8. **A second, independent renderer.** `raytrace2d.py` exists as an independent 2D
   specular tracer `[확인 CONTEXT.md:467]` but there is no 3D independent check. The
   analytic cavity calculation of §4b is the cheap substitute and should be run across
   the whole d100 honeycomb sub-grid, not just the one case I did.
9. **Control-overlap re-baseline.** `FINDINGS_control_overlap.md` proves the control
   plate sits inside the panel field for every 3D family ever measured, states
   "**fix NOT yet applied**", and recommends GAP 500 with matched `res_x`. The report
   still quotes "27× darker than a plain black wall" `[확인 report.html line 16–19]` —
   a ratio against a control the project has proven invalid. Either apply the fix or
   delete every control-relative ratio.
10. **Coating roughness.** `spec_roughness = 0.30` is pinned with the note that it
    "moves cavity ρ_dh by 32 %" `[확인 sweep_topo.py:71; CONTEXT.md:604–605]`. A 32 %
    lever pinned at one value, in a ranking whose top is separated by 0.18 %, must be
    swept per family — the authors themselves say so `[확인 blender_render.py:194–196]`
    and then did not.

---

# What the strongest honest paper from this material would be

Not a design paper. The design result does not survive objection 1, and even if it did,
objection 6 says a vane baffle is not new. The strongest paper is the *methodological*
one, and the material for it already exists.

### Title

**"The diffuse fraction of a black coating, not the surface topography, determines
the reflectance of millimetre-scale light traps: a ray-optical study across nine
topologies"**

### Claim

For structured black surfaces at millimetre scale (pitch 3.75–11 mm, depth 20–100 mm,
coating ρ_dh(0) = 1.0 %), evaluated in ray optics against a coating model fitted to
published goniometric data:

1. **The design-to-design spread across nine topologically distinct families —
   pillar arrays, tilted-vane louvres, Voronoi wall networks, re-entrant and nested
   cells, strut lattices — is 1.11× at matched minimum manufacturable feature size
   (0.4 mm), and 1.5× at matched aspect ratio.**
2. **The same designs move by up to 41×, with rank inversion, when the coating's
   diffuse/specular split is varied at fixed hemispherical reflectance ρ_dh(0).**
3. **Therefore the split — which a flat-plate directional-hemispherical reflectance
   curve does not constrain, and which is the quantity most commonly published for
   black coatings — is a 27×-larger lever than the entire topology search, and any
   cavity simulation fitted only to ρ_dh(θ) is underdetermined at the level that
   decides the answer.**
4. Secondary: the exposed-area law ρ_dh(0) ≈ f_exposed × ρ predicts wall-network
   topologies to within 1.5× across a 14× span in exposed area, and fails by 9.7× for
   rounded pillar arrays, whose return scales as tip radius r rather than r² — i.e.
   it comes from the flank adjacent to the tip, not the tip disc.

This is defensible, quantitative, general, useful, and — critically — **it is a claim
about simulation methodology, so a simulation-only paper is the natural vehicle** and
the absence of a fabricated sample is a stated scope boundary rather than a hole.
It also inverts the liability of the whole project: the unmeasured parameter stops
being the weakness and becomes the finding.

### Figures it would need

| # | figure | status |
|---|---|---|
| **1** | Geometry atlas: the nine families, 3D render + section, annotated with pitch, depth, aspect, minimum feature | renders exist in `profiles/` and `report/2026-08-12/top/`; needs the minimum-feature annotation |
| **2** | **Validation, three panels**: (a) flat Lambertian ρ=0.05 → 0.0500; (b) fitted coating vs Filip Fig. 6 THR, 0–80°, with residuals (worst 9.5 %); (c) **rendered ρ_dh vs closed-form Gouffé cavity theory for the Lambertian arm, over the depth × pitch × wall grid** | (a) and (b) exist `[확인 metrics/01:53–57; blender_render.py:165–177]`. **(c) does not exist and is the single highest-value missing figure** — my one-point check lands at 0.83× |
| **3** | **The headline**: ρ_dh vs minimum feature size, one curve per family, error bars = SEM over ≥12 geometry seeds. The figure where the ranking visibly collapses | **does not exist**; requires the feature-matched re-run of objection 1 and the seed replication of objection 3 |
| **4** | **The result**: ρ_dh vs diffuse fraction d ∈ [0,1] at fixed ρ_dh(0), one curve per family, showing the 41× span and the rank crossings | data partly exists at d ∈ {0, 0.76, 1.0}; needs ≥7 values of d to show the crossings |
| **5** | ρ_dh(θ), 0–85°, best member of each family under both material extremes — showing what the ±40° truncation hides | **does not exist**; sweep stops at 40° |
| **6** | Exposed-area law: predicted vs measured ρ_dh(0), log-log, marked by topology class, with the pillar family as the visible outlier | computable today from `sweep_topo.csv` (my table in objection 7) |

**Optional 7 (only if built):** the response matrix H(z_out; z_in) at ≥40 input
positions and synthesised bar contrast vs period *and phase*, for three families at
θ = 0 and 40° — the fix `CONTEXT.md:357–360` already specifies. If it is not built,
**delete every form claim from the paper** and say in the introduction that form
destruction is out of scope. That is an acceptable paper. A paper that claims form
destruction as priority 1 and measures total reflectance is not.

### What it must NOT claim

- No recommended design. No "the answer is shingles". No cover number.
- No absolute reflectance presented as a property of a real panel — the coating model
  is ±20 % on absolute level by the source paper's own internal inconsistencies
  `[확인 reference/SUMMARY.md §1, caveat 3]`.
- No ratio against the control plate until `FINDINGS_control_overlap.md`'s fix is
  applied.
- No claim outside ±40° until the sweep is extended.

### And if the authors want the design paper instead

Then it needs the coupon, the goniometer, and the measured diffuse fraction — items
1–4 of §4d. With those, "A 3D-printed vane-baffle panel with measured ρ_dh below
0.3 % over ±60°, validated against ray-optical simulation" is a solid Applied Optics
paper, and the simulation methodology above becomes its second half. Without them,
the design claim is not reviewable, because the reviewer has no way to distinguish a
result from a fit to an assumption.

---

*A closing note, because it should be said: the practice in this repository — numbered
metrics that carry their own defect list, retired metrics kept with the reason,
withdrawn conclusions stated plainly, `[확인]/[추측]/[모름]` on literature claims, and
negative controls put in specifically to fail — is better than the field's norm, and
it is the reason this review could be written at all. Every fatal objection above was
found using the authors' own instrumentation. The failure here is not of rigour; it is
that a report was written on top of a rigorous process without re-running the process
against the report's specific claims.*
