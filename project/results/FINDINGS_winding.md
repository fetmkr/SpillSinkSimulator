# Winding: three families were built inside-out, and specular rows knew

This session's baseline discipline — *a shell with no holes must measure the
same as the solid it replaces, under every coating, before any perforated
number is quotable* — refused to pass for three sessions. It was right to
refuse. The chain it pulled ends at a project-wide defect: **the cone, the
shingle and the solid pyramid were wound inside-out**, and a glossy coating
reads inward-wound geometry ~50 % apart from outward-wound geometry of the
identical shape.

## The isolation chain, kept because each step killed a wrong explanation

The shell read −34 to −37 % against the solid under d00 (specular) while
matching under d100 (diffuse). In order, measured and rejected:

1. coincident faces from tile-stacking → rebuilt on `geom_kit`, clean: no change
2. funnel orientation → fixed (tip up), verified by cross-section: no change
3. hip bore micro-slits → single wrapped solid per pyramid, no hip bores: no change
4. thin double wall at the tip → solid tip, no wall thinner than 0.5 mm: no change
5. µm-scale joints leaking in float32 → joints at 50 µm: no change
6. MetalRT → CPU render: same −34 %
7. rays reaching the interior → inner skin painted pure white: **no change at
   all**, so nothing ever reaches it; a float64 tracer confirmed the two
   meshes are ray-identical (mirror bounces, same seeds: 0.1060 vs 0.1057)

What remained: with the interior proven irrelevant, the outer skin ALONE read
0.00112 wound outward and 0.00167 wound inward — same planes, same positions.
**The winding was the entire effect**, and the "solid" reference was the
inside-out one.

## The audit

Signed volume per family, before the fix:

| family | orientation |
|---|---|
| **geom3d cone** (the flagship) | **inward** |
| **geom_topo shingle** (the three-axis winner) | **inward** |
| **geom_floor pyramid** | **inward** |
| geom_topo comb / geom_floor wave / geom_cell square / geom_perf | outward |

Cross-family comparisons under any specular-weighted number had been comparing
two different renderer behaviours.

## The fix is construction, not inspection

`geom_kit.orient_outward(verts, faces)`: connected components by shared
vertices, signed volume per component, inverted components reversed. Wired
into the exit of every builder (`geom_floor`, `geom3d`, `geom_topo`,
`geom_cell`, `geom_perf`), so a builder cannot ship an inside-out solid no
matter how it assembles one. `mesh_check` also asserts zero inverted
components, as the backstop.

After the fix the zero-hole baseline **passes**: worst gap 5.0 % across
3 coatings × 2 angles, inside the ±4 % seed noise.

## Blast radius, measured not guessed

The winding does not touch diffuse rows (d100 re-measured bit-identical:
+0.00 %). It collapses specular rows on the inward families:

    cone p5.5, d00 theta 0:   0.00183 -> 0.00100   (−45 %)
    cone p5.5, d00 theta 40:  0.00210 -> 0.00022   (−89 %)
    cone p5.5, d76 rows:                            (−16 %)

**The flagship headline survives**: the cone's published worst-ρ is set by its
d100 rows, which did not move — 0.215479 % after the fix against 0.215484 %
published.

But the argmax is not always diffuse. Scanning every live sweep: of 2 531
designs, **773 (30 %) have their worst-ρ set by a d00 row**. Those values are
inflated wherever the family was inward-wound — cone, shingle/blades,
honeycomb (69 designs in `sweep_topo` alone), and the anechoic pyramid rows.
Every one needs re-measurement before its worst-ρ is quoted again. Rows whose
worst comes from d100 (1 758 designs) stand.

Also affected in kind: the form/head-on measurements run the fitted coating
(specular-weighted), so the smear and peak numbers for inward-wound families
carry a bias of the d76 order (~15 %) until re-measured.

## The re-measurement, and what actually moved

`sweep_rewind.csv`: the eleven decision-carrying designs, re-measured with the
oriented builders, identical `params_json` (plus `"winding": "out"` recorded).
Predictions were written in `sweep_rewind.py` before the render; graded here.

| design | published worst | re-measured | shift |
|---|---|---|---|
| cone B_CONE_p0550_s23 | 0.21548 % | 0.21548 % | −0.0 % |
| blade+pyramid stack BH_p055_t02 | 0.18419 % | 0.18419 % | +0.0 % |
| comb AZ_comb_p00_s23 (control) | 0.22275 % | 0.22274 % | −0.0 % |
| honeycomb B_HONE_p0086_f030 | 0.25590 % | 0.25591 % | +0.0 % |
| blade standalone BL_FLAT_t050 | 0.20794 % | 0.20768 % | −0.1 % |
| pyramid AN_pyr_a283 | 0.25261 % | 0.25261 % | +0.0 % |
| **pyramid AN_pyr_a909** | 0.18151 % | **0.13392 %** | **−26.2 %** |
| **truncated AN_trn_a283** | 0.47100 % | **0.25548 %** | **−45.8 %** |
| **truncated AN_trn_a909** | 0.45988 % | **0.17202 %** | **−62.6 %** |
| cone anchor AN_cone_p550_s23 | 0.21548 % | 0.21548 % | −0.0 % |

(The wedge is a 1D extruded family outside the oriented builders; its worst is
d100-set and stands as published.)

Predictions: 1, 2, 4 and 5 held. **Prediction 3 was wrong in the best way**:
the truncated pyramid was never the disaster the table said -- its last place
was almost entirely the winding artifact, and at aspect 9 it moves from worst
to SECOND. The blade standalone's d00 row barely moved (−0.1 %), which says
the artifact's size depends on the geometry: real grazing reflection off thin
plates is genuinely specular, while the pyramid's d00 rows were mostly
artifact.

## The anechoic table, corrected (worst-ρ, aspect 9.09, depth 50 mm)

| rank | design | worst ρ |
|---|---|---|
| 1 | **sharp pyramid** | **0.13392 %** |
| 2 | truncated pyramid | 0.17202 % |
| 3 | blade + pyramid stack | 0.18419 % |
| 4 | cone | 0.21548 % |
| 5 | comb | 0.22275 % |
| 6 | wedge | 0.30406 % |

Two headlines change. **The sharp pyramid's lead over the cone grows from 16 %
to 38 %**, and it now beats the three-axis stack winner on total reflectance —
a single pressed layer outperforming the two-layer assembly on this axis. And
**the truncated pyramid is rehabilitated**: a flat-topped, press-friendly part
sits second, which matters because a perfectly sharp pressed tip is the hard
part to make. Neither result touches the form or head-on axes, which for these
shapes are still unmeasured (and were themselves biased for inward-wound
families; the same re-measurement is owed there).

## What did NOT cause this, for the record

The renderer. Cycles agreed with itself (CPU/GPU), with the closed forms
(sphere, canyon) and with the independent tracer whenever the geometry it was
given was wound correctly. The defect was ours: builders that assembled solids
with whatever winding fell out of their loop order, and no check that looked.

## Reproduce

    python3 scripts/mesh_check.py          # orientation is now a named failure
    Blender --background --factory-startup --python /tmp/base2.py   # baseline
