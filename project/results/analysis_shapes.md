# sweep_shapes.csv — analysis of a live snapshot

Produced by an adversarial analysis agent on a frozen copy taken while
`sweep_shapes.py` was still appending. `rho` is absolute ρ_dh (metrics/01).

Baselines used throughout, named:

- **flat plate of the same coating**, ρ_dh(0) = **0.00998** (`MUSOU_RHO0`,
  `blender_render.py:216`) — identical for all three materials by construction,
  because `coating_split` splits at fixed ρ_dh(0).
- **0.05 matte black control**, in every frame; measured mean 0.049868.

---

## 1. Snapshot coverage

| quantity | value |
|---|---|
| data rows | 2950 |
| distinct tags | 197 |
| (tag, material) runs | 590, every one with all 5 thetas |
| **designs complete on all 3 materials** | **196 / 320 (61.3%)** |
| designs not started | 123 |

The grid is `product(POWERS, BULGES, LIPS, PITCHES, DEPTHS)` with power slowest,
so the hole is one clean slab of the power axis:

| power | complete | missing |
|---|---|---|
| 0.50 / 0.75 / 1.00 | 64 each | 0 |
| **1.50** | **4** | 59 |
| **2.00** | **0** | 64 |

**What the analysis cannot yet see.** The four power-1.50 designs that exist are
all bulge 0, lip 0, pitch 3.75 — and three land in the top 5. The head of the
ranking is set by a corner sampled at 4 points of 64, on the single most
favourable pitch. Everything about power ≥ 1.5 is provisional. Main effects
below are computed on the balanced 192-design block (power ≤ 1.00) so the hole
cannot distort them.

---

## 2. Ranking

Score = max ρ over the 5 thetas; combined = max over d00 / d76 / d100.

### Which material sets the score

d00 is worst for **170 of 196** designs, d100 for 26, d76 for none. Cause, from
`blender_render.py:215-222`: `coating_split(0.0)` gives `spec_scale = 0.2495`, so
the pure-specular arm's grazing ceiling is **24.95%**, while `coating_split(1.0)`
is a Lambertian body of **0.998%** with no angular rise. Fixing both arms at
equal ρ_dh(0) fixes them at the weakest point of the d00 curve.

| material | min | max | spread |
|---|---|---|---|
| d00 | 0.00214 | 0.09435 | **44.2×** |
| d76 | 0.00182 | 0.02486 | 13.6× |
| d100 | 0.00187 | 0.00871 | **4.67×** |

### Top 10 by combined score

| # | tag | pow | bulge | lip | pitch | depth | seal | **combined** |
|---|---|---|---|---|---|---|---|---|
| 1 | P150_B00_L00_p0375_d40 | 1.50 | 0 | 0 | 3.75 | 40 | 0.805 | **0.00214** |
| 2 | P100_B00_L00_p0550_d50 | 1.00 | 0 | 0 | 5.50 | 50 | 0.722 | **0.00215** |
| 3 | P150_B00_L00_p0375_d50 | 1.50 | 0 | 0 | 3.75 | 50 | 0.805 | 0.00217 |
| 4 | P150_B00_L00_p0375_d30 | 1.50 | 0 | 0 | 3.75 | 30 | 0.805 | 0.00229 |
| 5 | P100_B00_L00_p0375_d50 | 1.00 | 0 | 0 | 3.75 | 50 | 0.722 | 0.00230 |
| 6 | P100_B00_L00_p0550_d40 | 1.00 | 0 | 0 | 5.50 | 40 | 0.722 | 0.00231 |
| 7 | P100_B00_L00_p0750_d50 | 1.00 | 0 | 0 | 7.50 | 50 | 0.722 | 0.00236 |
| 8 | P100_B00_L00_p0375_d40 | 1.00 | 0 | 0 | 3.75 | 40 | 0.722 | 0.00236 |
| 9 | P075_B00_L00_p0550_d50 | 0.75 | 0 | 0 | 5.50 | 50 | 0.648 | 0.00240 |
| 10 | P100_B00_L00_p0750_d40 | 1.00 | 0 | 0 | 7.50 | 40 | 0.722 | 0.00249 |

**14 of the top 15 have lip = 0 and 14 of 15 have bulge = 0.** No lip-0.35
design reaches the top 14.

**Best fully-explored design: `P100_B00_L00_p0550_d50`, combined 0.00215** —
4.6× darker than a flat plate of the same coating at normal incidence, 23×
darker than the 0.05 matte control, holding under both material extremes.

---

## 3. Do the two material extremes agree? — the headline is misleading

| subset | n | Spearman(d00, d100) |
|---|---|---|
| all designs | 196 | **+0.982** |
| top 50 | 50 | +0.695 |
| **top 30** | 30 | **+0.633** |
| top 15 | 15 | +0.764 |

Top-N overlap: 3/5, **7/10**, 11/15, 15/20, 21/30.

**The materials agree completely on what to throw away and substantially
disagree on what to build.** The +0.982 is carried by ~150 designs both agree
are bad.

### The disagreement has exactly one axis: pitch

Within the top 50, rank shift correlates with pitch at **Spearman −0.877
(p = 6.3e-17)** and with nothing else (bulge −0.009, power −0.042, depth −0.178).

| pitch | mean rank shift | reading |
|---|---|---|
| 3.75 | **+8.73** | d100 (diffuse) likes it more |
| 5.50 | −6.57 | |
| 7.50 | −14.86 | |
| 11.00 | **−17.00** | d00 (specular) likes it more |

Named: `P100_B00_L00_p1100_d50` is rank **9** under d00 and rank **29** under
d100. `P100_B35_L00_p0375_d40` is rank 34 under d00 and rank **15** under d100.

**Under the project's both-extremes rule this makes pitch 3.75–5.50 the only
defensible choice**, because 7.50–11.00 wins only under the specular assumption.

---

## 4. Main effects

Marginal medians over the balanced 192-design block:

| knob | level | median combined | vs best |
|---|---|---|---|
| **depth** | 20 / 30 / 40 / **50** | 0.01511 / 0.00616 / 0.00399 / **0.00323** | **4.68×** |
| **pitch** | **3.75** / 5.50 / 7.50 / 11.00 | **0.00317** / 0.00408 / 0.00688 / 0.01597 | **5.05×** |
| **lip** | **0.00** / 0.35 | **0.00343** / 0.01023 | **2.98×** |
| **power** | 0.50 / 0.75 / **1.00** | 0.00975 / 0.00439 / **0.00348** | **2.80×** |
| **bulge** | **0.00** / 0.35 | **0.00411** / 0.00775 | 1.88× |

But **at the optimum every knob is worth only 1.2–1.4×** — the design surface is
flat near the top, and the large numbers above are the cost of getting *away*
from it.

| knob | verdict |
|---|---|
| depth | biggest; monotone in 140/144 adjacent pairs |
| pitch | second, **and the axis the materials disagree on** |
| lip | **strictly harmful** — worse at every one of 96 matched pairs |
| power | matters below 0.75; 0.75→1.00 is only 1.26× |
| bulge | mildly harmful; worse in 93 of 96 pairs. Small but not noise |

**Nothing in this grid is noise.** The smallest real effect is ~18× the
measurement floor.

---

## 5. seal_frac — a confound, and worse than suspected

### It carries zero independent information

`geom3d.seal_fraction` compares `cavity_radius(f)·overlap·pitch/2` against
`pitch/√3`. **Both sides scale with pitch, so pitch cancels exactly** — the
criterion is `cavity_radius(f) ≥ 2/(1.6√3) = 0.7217`, pitch-independent.
Confirmed in the data: seal_frac is identical across all 4 pitches for every
(power, bulge, lip) triple.

**seal_frac is a deterministic function of three knobs and varies not at all
with the other two. It cannot be tested as an independent variable in this
design.** Any "seal_frac effect" is a relabelling of the power/bulge/lip effect.

Note also: lip 0.35 does **nothing** to seal_frac at power 0.75 and 1.00 (the
Gaussian peaks at 0.60–0.70, below the 0.7217 threshold) but **collapses it to
0.19–0.22 at power 0.50**. A genuine discontinuity in the meaning of the lip
knob across the power axis, documented nowhere.

### The real predictor

| predictor of combined score | Spearman |
|---|---|
| seal_frac | −0.499 |
| nominal depth | −0.488 |
| usable depth = seal_frac × depth | −0.689 |
| nominal aspect = depth / pitch | −0.734 |
| **usable aspect = seal_frac × depth / pitch** | **−0.876** |

`log(combined) ~ log(usable_aspect)`: **slope −1.147, R² = 0.729** over 192
designs. Worst-θ ρ falls as roughly the inverse first power of *usable* aspect.

### "depth 50" is never 50 mm of cavity

| nominal | usable at seal 0.7218 | usable at seal 0.1653 |
|---|---|---|
| 20 | 14.4 mm | **3.3 mm** |
| 50 | **36.1 mm** | **8.3 mm** |

**A depth-50 design at bulge 0.35 + lip 0.35 has 8.3 mm of cavity — less than a
depth-20 design at bulge 0 + lip 0.** Any plot of ρ against `depth` is a plot
against a mislabelled axis.

### After controlling for usable aspect, seal_frac's sign flips

Residual correlation: seal_frac **+0.251 (p = 4.5e-4)** — higher seal is
slightly *worse* once usable aspect is held. **seal_frac is not a design
objective. Build for usable aspect; treat seal_frac as the correction factor
that turns a nominal depth into a real one.**

---

## 6. Things that look wrong

Measurement floor used throughout: ±θ pairs should be identical; their median
disagreement is 1.28% (±40) / 1.51% (±20); the control has σ/μ = 0.228%.
**Anything under ~2% is not a result.**

### 6.1 — 39 rows read ABOVE the matte-black control [explained, but load-bearing]

Worst: `P075_B35_L35_p0750_d20` d00 θ=0, **ρ = 0.09435 vs control 0.04995**. All
39 are d00. 367 rows exceed the flat coating plate; **d100 has zero**.

Not a render defect. `coating_split(0.0)` gives spec_scale 0.2495, so the d00
material's **grazing ceiling is 24.95%**; the observed max is 37.8% of it. The
d100 arm is pure Lambertian at albedo 0.00998 and its observed max is
0.00871 = 87.3% of ceiling, **never over, in 980 rows**.

**What is wrong is the framing, not the render.** Splitting the two materials at
fixed ρ_dh(0) pins them at the one angle where they agree and lets them diverge
25× everywhere else. So the **"worst of three materials" rule is in practice a
specular-only rule**, and the bulge+lip family is not a failed trap but a
*grazing-angle amplifier*.

### 6.2 — Systematic +θ/−θ asymmetry of −0.85%, with zero tilt

Mean +40/−40 ratio **0.9915**; per material d00 0.9871, d76 0.9941, d100 0.9932 —
**all three biased the same way**, where noise would centre on 1.000. The sweep
sets `depth_jitter=0` and never sets `tilt_deg`. Worst cases are all pitch 11 /
depth 30 (ratio 0.859).

[추측] Lateral position jitter with one seed does not average out at face 60 mm /
pitch 11 — only ~30 cells across the face. **Untested. Worth one run at a second
jitter seed before any 1–5% difference in this file is quoted.**

### 6.3 — The control does not read exactly 0.050000

metrics/01 asserts it does. Measured over 2940 rows: mean **0.049868 (−0.264%)**,
min 0.049616, σ = 0.000114. True to ~0.8%, not exact. That is the empirical
noise floor of a 64-spp frame.

### 6.4 — Non-monotone depth, in the sealed families only

4 of 144 adjacent pairs go the wrong way by >2%, worst ×1.26. **All four are
pitch 11.00**, three of four are bulge+lip with seal ≈ 0.17–0.22. Same family as
6.1, same pitch as 6.2.

### 6.5 — Non-monotone pitch at the top, and it is material-dependent

**d00 has an interior optimum at pitch 5.50; d100 is monotone and wants 3.75.**
Reproducible across two powers and two depths. Effects are 2–7%, i.e. 2–5× the
floor — probably real but not comfortably so, and it is what decides #1 vs #5.

### 6.6 — The top of the ranking is a statistical tie

#1 (0.00214) and #3 (0.00217) differ by **1.4%**, below the ±θ floor of 1.28%.
#1 and #2 differ by 0.5%. And #1/#3/#4 are all power 1.50, a level with 4 of 64
measured. **Do not quote power 1.50 as the winner until the other 59 land.**

### 6.7 — Checked and clean

Duplicate rows: 0. Duplicate (tag, material, theta) keys: 0. Truncated runs: 0.
No inert knob. No energy-conservation violation under any material.
`seal_fraction`'s docstring reads as pitch-specific; it is not — 0.72175 is the
value at every pitch. Function correct, docstring misleading.

---

## Three things to chase before anything here is reported

1. the **−0.85% systematic ±θ asymmetry** in a zero-tilt configuration
2. the fact that the **"worst of three materials" rule is in practice
   specular-only**, because d00's grazing ceiling is 25% against d100's 1%
3. the **1.4% gap at the top of the ranking**, which is smaller than the
   measurement floor
