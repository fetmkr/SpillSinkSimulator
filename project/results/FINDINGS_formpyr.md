# The corrected top designs on all three axes — and the pyramid takes them all

After the winding fix rewrote the total-reflectance ranking, the other two axes
had to follow: form destruction and head-on brightness had never been measured
for the pyramids, and were measured for the cone and the stack on inside-out
geometry. This runs the published form protocol (16 stripe phases × 512 spp,
θ 0/±40) on the four designs the decision rests on, plus the Phase-4 floor
headline set at θ0, all with oriented geometry.

## Reference designs first (the re-measured baselines)

| design | published | re-measured | shift |
|---|---|---|---|
| cone: smear | 4.113 | 4.055 | −1.4 % |
| cone: head-on | 0.06826 | 0.05951 | **−12.8 %** |
| FL comb flat floor θ0 | 0.16401 % | 0.16402 % | +0.0 % |
| FL comb + pyramid floor θ0 | 0.03355 % | 0.03291 % | −1.9 % |
| FL comb + cone floor θ0 | 0.03539 % | 0.03368 % | −4.8 % |
| FL comb + wave floor θ0 | 0.03868 % | 0.03640 % | −5.9 % |
| FL blade flat θ0 | 0.20794 % | 0.20768 % | −0.1 % |
| FL blade + pyramid θ0 | 0.05088 % | 0.04879 % | −4.1 % |

Prediction 1 held: head-on (the most specular quantity) dropped 12.8 % on the
cone, inside the predicted 5–25 %; smear moved 1.4 %, inside the predicted
10 % — the ratio construction absorbs most of the bias, as expected.

**Phase 4 survives.** The floor effect was measured on d00-set rows and was
therefore at risk in full; re-measured, the numbers move only 2–6 % and the
ratios strengthen slightly: flat-vs-pyramid goes 4.89× → **4.98×** on the comb
tube and 4.09× → 4.26× on the blade tube, and the floor ranking
(pyramid < cone < wave) is unchanged. The phase-4 report needs an errata line,
not a re-issue.

(The stack anchor has no exact published form pair — `form_buildable.json`
holds the tilt-0/5/10 variants but not tilt-2 — so the stack row below is a
new measurement, not a comparison.)

## The three axes, oriented geometry, one table

| design | total worst-ρ | smear (higher = better) | head-on (lower = better) |
|---|---|---|---|
| **sharp pyramid a909** | **0.134 %** | **4.16** | **0.0271** |
| truncated pyramid a909 | 0.172 % | **4.51** | 0.201 |
| blade + pyramid stack | 0.184 % | 3.96 | 0.0851 |
| cone p5.5 | 0.215 % | 4.06 | 0.0595 |

**The sharp pyramid leads every axis it was measured on.** Total reflectance
by 27 % over the next design, head-on by 2.2× over the cone (the previous
head-on champion) and 3.1× over the stack, and smear ahead of both. A single
press-formed layer beats the two-layer blade assembly on all three numbers.

Prediction grades: P1 ✓, P2 ✓ (head-on within 2× of the cone — in fact 0.46×),
P4 ✓ (truncated head-on 7.4× the sharp tip's; the flat top pays exactly where
the exposed-area law says it must). **P3 ✗** — I predicted the pyramid's flat
mirror facets would smear at least 25 % worse than the jittered blades; it
smears 5 % better. Phase-averaged over 16 stripe positions, a facet that
redirects the whole stripe far away destroys the line as effectively as
scattering it.

The truncated pyramid is its own story: **best smear in the study (4.51)** and
worst head-on (0.201). A shape for form-first placements, and a hint that a
small truncation might trade a little head-on for form — unmeasured.

## What stands between the pyramid and "build it"

* **It is periodic.** The no-periodic-array rule exists because a scanning
  beam over identical cells makes repeating bright spots; the form protocol
  phase-averages that away, so this table cannot see the objection. A jittered
  pyramid field (geom_floor has no jitter parameter today) is the missing
  measurement.
* Phase 2/3 form tables carry the ~13 % head-on bias on their inward-wound
  rows; rankings there had 10×-class gaps and survive, but the numbers need
  an errata mark until re-generated.

## Reproduce

    Blender --background --factory-startup --python scripts/sweep_formpyr.py
    results/form_pyr.json          # the four designs, full protocol
