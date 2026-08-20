# A room lights a point from every azimuth. An in-plane rig cannot answer it.

2026-08-21. **A published claim is withdrawn here**, and the reason it was wrong
is more useful than the number was.

## The claim, and its retraction

`report/2026-08-20/hcflat.html` said the panel reads **radiance factor
β = 0.0037** at the audience and therefore **"does not beat black velour"**.

**Both halves were wrong.** Corrected:

| | published 2026-08-20 | corrected 2026-08-21 |
|---|---|---|
| panel, β mean | 0.0037 | **0.00105** |
| flat plate of its own coating, β mean | 0.0078 | **0.0288** |
| what the structure is worth | 2.1× | **27.5×** on the mean, 54× on the peak |
| against black velour | "1.16×, the panel is brighter" | **0.09–0.52×, the panel is darker** |

The withdrawal was prompted by Elliot pushing back — *"surely Musou black is
better than velour"* — on a result that felt wrong. It was.

## The bug

`measure_audience.py` called `bidir.cell(sc, θ_in, θ_out)` with **both angles
positive**. In this rig's convention that is the **retro side** of the BRDF, and
a honeycomb is a retroreflector, so every one of the 48 cells was sampled where
the panel is brightest.

It is worse than a sign error, because the fix is not a sign. Measured share of
the light that actually reaches an eye, by the azimuth Δφ between the direction
back to the projector and the direction to the eye:

| Δφ | 0° retro | 30° | 60° | 90° | 120° | 150° | 180° specular |
|---|---|---|---|---|---|---|---|
| share | 6.2 % | 9.7 % | 8.6 % | 11.0 % | 19.1 % | 27.8 % | 17.7 % |

**24.5 % near retro, 64.5 % near specular, and the mode at 150°.** An in-plane
rig can only produce Δφ = 0 and Δφ = 180. **It cannot sample 76 % of the light
at all.** The old measurement did not merely pick the wrong one of two — it
represented a continuum by one endpoint.

## The general lesson

**A BRDF slice in one plane cannot answer a question about a room.** A goniometer
scan in the incidence plane is the right instrument for characterising a
surface, and `metrics/08` is honest about being one. But a room lights every
point from every azimuth at once, and an audience stands somewhere unrelated to
that plane. Any metric that integrates over a real space needs the azimuth axis.

`metrics/08` scoped that axis out, and `metrics/05` (TIS) has been blocked on it
since it was written. The room forced it.

## What was added

`blender_render.add_sun()` gained a `phi_deg` that rotates the source about the
panel normal — the rig could previously only place a source in the Y–Z plane.
The direction becomes `(−sin θ sin φ, −cos θ, −sin θ cos φ)`, which is the
convention `raytrace_viz.trace()` already used, so the two tracers now agree by
construction rather than by luck.

It **subsumes** the old signed convention rather than replacing it: measured,
φ = 0 reproduces the old `+θ_out` and φ = 180 the old `−θ_out`, both to a ratio
of 1.0000.

## The check that would have caught it, and now runs

**A Lambertian is isotropic, so its radiance factor must be identical at every
azimuth.** Measured on a flat Lambertian ρ₀ = 0.20 at θ_in 30 and 60, θ_out 40:

    φ =    0     45     90    135    180
    β = 0.20000 0.20000 0.20000 0.20000 0.20000     worst departure 0.000 %

Any azimuth dependence there would be the rig, not the surface. It costs five
renders and it is the whole defence against this class of error.

## Why the flat plate moved so much more than the panel

The flat Musou plate went 0.0078 → 0.0288 on the mean and shows a **peak of
0.603** — three quarters as bright as white paper. That is the **specular
reflection of a projector in a painted ceiling**, and the old in-plane retro-side
measurement could not see it at all. It is also the strongest argument for the
structure that this study has produced: the honeycomb takes that 0.603 glare
down to 0.011.

## Still true, and still open

- The velour and Musou-fabric baselines are **brackets between two points read
  off someone else's plot** (Filip & Vávra 2026 Fig. 6), quoted as ranges
  because the curve between them is not known. An earlier draft interpolated
  with an exponent I invented; the answer swung by 2× with it, and that is not
  a baseline.
- Velour's own source reports it with the **lowest TIS** of any sample measured,
  so a Lambertian model of it flatters it, and the comparison stays conservative.
- 3.1 % of the light sits in cells too small to render and is excluded from the
  mean; the coverage figure is reported with every number.
- Zero physical measurements, of anything, still.
