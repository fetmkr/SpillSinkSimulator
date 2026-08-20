# The coating model reproduces itself exactly; the residuals were never ours

2026-08-20. Code: `scripts/materials.py` (`Material.rho_dh`, `fresnel`),
`scripts/blender_render.py` (the fit block above `MUSOU_THR`). Locked by
`python3 scripts/materials.py`.

## What was believed

`blender_render.py` carries the fit of the Musou coating to Filip & Vávra 2026
and a table of residuals against it:

    theta      0      15     30     45     60     75     80
    target   1.000  1.000  1.030  1.130  1.430  2.330  3.180  %
    Cycles   0.998  0.999  1.007  1.060  1.294  2.278  3.085  %
    residual -0.2   -0.1   -2.2   -6.2   -9.5   -2.2   -3.0   %

The text around it reads that row as how well the implementation performs, and
describes the θ = 0 row as **exact by construction** — 1.000 % chosen so the
angle every headline number is quoted at would be exactly right.

## What is true

Evaluate the model this file actually builds — a diffuse body mixed with a
Fresnel-weighted glossy lobe — in pure Python, and it reproduces the **Cycles**
row to better than 0.04 % at every angle:

    theta        0      15      30      45      60      75      80
    Cycles    .00998  .00999  .01007  .01060  .01294  .02278  .03085
    model     .00998  .00999  .01007  .01060  .01293  .02277  .03086
    error     +.02%   -.03%   +.03%   -.03%   -.04%   -.03%   +.03%

So the residual row is **the model disagreeing with the paper**, not the
implementation disagreeing with the model. Those are different claims, and only
the second one would have been a defect. The implementation was never in
question; nothing about it needed fixing.

And θ = 0 is **not** exact by construction. It is short by 0.2 %, every time,
for a reason.

## The two things that had to be right

Both found by the session working on the ray tracer, which needed the curve the
renderer actually evaluates rather than an approximation to it.

**1. The Fresnel term is the exact dielectric curve, not Schlick.** They agree
at normal incidence and diverge hard in the middle:

    theta      0      30      45      60      75      80      85
    schlick  .0400   .0400   .0421   .0700   .2547   .4099   .6485
    exact    .0400   .0415   .0502   .0892   .2531   .3877   .6128
    error     0 %   -3.6 %  -16.3 % -21.5 %  +0.7 %  +5.7 %  +5.8 %

`ShaderNodeFresnel` is exact. `materials.fresnel()` is now exact too, and
Schlick survives as `fresnel_schlick()` for bookkeeping written against it.
This mattered directly: the closed form deriving a diffuse fraction from a
grazing rise divides by `F(80) − F0`, so Schlick put a 6 % error in the
denominator.

**2. The Mix Shader carries a cross-term.** `mix(diffuse, glossy, fac)` is
`(1−fac)·body + fac·1`. The diffuse arm is attenuated by the same `fac` that
weights the specular arm, so the tree integrates to

    rho_dh(theta) = body·(1 − fac) + fac,        fac = spec_scale·F(theta)

which is `rho0 − fac·body`, **not** `rho0`. At the fitted split that is
0.99818 % against a nominal 0.998 % — and that difference *is* the −0.2 in the
residual row. The θ = 0 row is short by exactly the cross-term.

## What this changes

Nothing measured, and no published number. The fit constants are untouched, the
node tree is untouched, and `coating_split` is float64-identical to its previous
form over 909 cases. This is a correction to what the numbers **mean**, which
is the kind this project has had to make before — `principles/02` exists because
`FLAT_COATING_WORST = 0.061218` was a denominator nobody had measured.

What it adds is `Material.rho_dh(theta)`: flat-plate reflectance for any
material at any angle, in pure Python, no Blender, locked in the self-test
against the Cycles row above. A coating's own curve can now be drawn live in
the UI, and a material can be sanity-checked before an hour is spent measuring
it. **Flat plate only** — it says nothing about what a structure does with the
light, which is the entire subject of the study.

## Still open

The 45–60 ° band is optimistic against the paper by 6–9 %, and that is
unaffected by any of the above: it is a choice about which angle to favour, and
the paper is still what it was. `body = 0.0082` would spread the error to a
6.1 % worst case at the cost of +6 % at normal incidence. Exact-at-normal is
kept deliberately.

The paper's own absolute scale is uncertain to about ±20 % (its Vantablack
reads 0.0023 against a 3.5e-4 spec), so the **shape** is well supported and the
level is not. Unchanged by this finding, and still the largest term.
