> **CORRECTION (winding).** Three families in this table were built with
> inside-out normals, which inflates specular rows; see
> `FINDINGS_renderer_disagreement.md` and `FINDINGS_winding.md`. Re-measured
> with oriented geometry (`sweep_rewind.csv`): the **sharp pyramid's worst at
> aspect 9.09 is 0.13392 %** (was 0.18151), the **truncated pyramid 0.17202 %**
> (was 0.45988) — moving it from last place to second — and the cone, comb and
> wedge stand as published. The exposed-flat-area law below survives, but its
> magnitudes for pyramid and truncated rows are superseded by the corrected
> table in `FINDINGS_winding.md`.

# RF and audio anechoic shapes, coated black

Anechoic chambers solved a version of this problem in two other bands, and
their shapes are standardised. This measures all of them at this study's
envelope with this study's coating, to find out whether the shape carries or
whether it was the material all along.

Six shapes at four aspect ratios, 50 mm depth fixed, standard protocol
(5 angles × 3 coating models), worst case. Pitch = depth / aspect. **2.83 is a
real RF pyramidal absorber** — 425 mm tall on a 150 mm base; **9.09 is this
study's cone** at pitch 5.5.

## The measurement

| shape | aspect 2.83 | 4.00 | 6.00 | 9.09 |
|---|---|---|---|---|
| **pyramid, sharp** | 0.25261 % | 0.27401 % | 0.22886 % | **0.18151 %** |
| convoluted | 0.28434 % | 0.30407 % | 0.21559 % | 0.18255 % |
| wedge | 0.36722 % | 0.33553 % | 0.31736 % | 0.30406 % |
| hollow pyramid | 0.40022 % | 0.36436 % | 0.38150 % | 0.45366 % |
| truncated pyramid | 0.47100 % | 0.49725 % | 0.47330 % | 0.45988 % |
| *cone (this study)* | | | | *0.21548 %* |

The anchor is the cone at pitch 5.5 with the identical `params_json` the
published sweeps recorded. It reads **0.215484 %** here and 0.215484 % in
`sweep_buildable`, `sweep_conefloor`, `sweep_phase1`, `sweep_coatrobust` and
`sweep_azimuth` — six files, no difference at the last digit. The same cone
across 13 seeds spans 0.2029–0.2218 %, so **±4 % is the noise floor** for
comparing designs here and anything inside it is not a result.

## Three of five predictions were wrong

**P1, the sharpest one, WRONG.** I predicted the hollow/solid ranking would
invert: RF reports hollow as worse "due to lower material volume", we have no
material volume, and the review credits the cavity with "multiple reflections
within the cavity boundaries", which is our whole mechanism. Hollow is worse
here too, at every aspect, and it gets worse as aspect rises where every other
shape gets better.

The reason is the thing I did not model: a hollow pyramid formed from 0.5 mm
sheet has a **rim** all the way round its mouth, and the rim is flat and faces
the viewer. As pitch falls the rim keeps its width and the mouth shrinks:

| pitch | 17.67 | 12.50 | 8.33 | 5.50 mm |
|---|---|---|---|---|
| rim as fraction of the mouth | 11.0 % | 15.4 % | 22.6 % | **33.1 %** |

which tracks the hollow curve exactly. **The cavity idea was not tested** —
what was tested was a cavity behind a third of a flat plate. A hollow pyramid
with a knife edge at the mouth, or with the rim rolled under, is still an open
question and the argument for it stands.

**P2 WRONG, and this is the useful one.** I predicted RF's stubby aspect of
2.83 would be 3-10× worse than this study's designs, because reflectance goes
as rho^n and n follows aspect. It is 17 % worse than the cone, not 300 %. The
whole 2.83 → 9.09 range moves the sharp pyramid by only 39 %. **Aspect ratio is
a much weaker lever than this study has assumed**, and the RF chambers' choice
of a stubby absorber is not the compromise it looked like.

**P5 WRONG.** I predicted the pyramid would not beat the cone by more than a
few percent. **It beats it by 15.8 %** — 0.18151 % against 0.21548 %, four
times the ±4 % noise floor. The flat facets are worth something, and a
press-formed pyramid is a cheaper part than a moulded cone.

**P3 HELD.** pyramid ≈ convoluted > wedge at equal aspect: 0.1815, 0.1826,
0.3041 at aspect 9.09. The wedge is one-dimensional and a beam arriving along
the ridge leaves after two bounces, which is exactly why chambers put wedges on
the side walls and pyramids where incidence is normal. Our incidence is
±30-40° from an unknown azimuth, the case a wedge is worst at.

**P4 HELD, strongly.** RF reports the truncated pyramid as the best average
over 1-10 GHz. Optically it is the **worst shape at every aspect**, 2.5× the
sharp pyramid, and it barely responds to aspect at all — 0.471 at 2.83 against
0.460 at 9.09. A flat top is area facing the viewer one bounce away, and this
study already measured that reflectance rises linearly with flat apex area.

## What actually separates these shapes

Not aspect. Not the cross-section. **Exposed flat area at the mouth**, and it
orders the whole table:

| | flat area facing the viewer | worst ρ at aspect 9.09 |
|---|---|---|
| pyramid, sharp | a point | 0.18151 % |
| convoluted | a smooth crest | 0.18255 % |
| wedge | a 0.08 mm ridge line | 0.30406 % |
| hollow pyramid | a 33 % rim | 0.45366 % |
| truncated pyramid | a 20 %-of-pitch flat | 0.45988 % |

Everything this study has learned about tip radius, apex flat and blade edge
thickness is the same law, and it survives the change of family.

## What this is not

The RF figure of −33 dB (0.05 %) is better than anything here and it is not a
fair comparison. An RF pyramid is carbon-loaded foam: a **lossy bulk** that
attenuates the wave inside the taper, with the geometry acting as an impedance
match. Musou Black is a 1 % **surface** — nothing enters it. Borrowing the
shape does not borrow the mechanism, which is why the aspect ratio these
chambers settled on transfers so poorly in the direction I expected and so
easily in the direction I did not.

## What follows

The sharp pyramid is now the best single layer this study has measured on total
reflectance, by 16 % over the cone, and it is the simplest shape in the list.
It has **not** been measured on the other two axes — form destruction and
head-on brightness — which is what decides the design, and a periodic pyramid
array collides with this project's no-periodic-array rule the same way the
regular blade lattice did. Both are the next measurement, not a conclusion of
this one.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_anechoic.py
