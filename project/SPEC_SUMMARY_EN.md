# Spill Sink — Research Purpose and Final Specification

One-page summary. As of 2026-08-19, drawn from the measurements of Phases 1–10.

**Where the numbers come from** — every figure below is a simulation measurement.
No physical measurement has been made yet. One instrument produces all of them
(uniform hemisphere illumination, tilted orthographic camera), and every run is
checked against a control plate that must read 0.0500. The renderer itself was
cross-validated against an independent research renderer (Mitsuba) and against
geometries with closed-form answers.

---

## 1. What this research is for

Hundreds of laser projectors meet in mid-air and draw a picture there.
The beams pass through the picture and continue to the wall, where they paint a
**sharp copy of that same picture**. The audience sees the copy on the wall,
not the image in the air.

So we rebuild the wall — so that a beam landing on it disappears.

The deliverables are **one panel type** for the walls, and **one window unit**
for the spots where beams strike hardest.

## 2. There are three judging axes

Measure only one and you will choose wrong. Honeycomb proved it: it cut total
reflectance fivefold while leaving the other two axes identical to a flat plate.

| Axis | What it measures | Why it matters |
|---|---|---|
| **Total reflectance** | Sum of all returned light | How bright the wall is overall |
| **Smear** | How much the returned light loses the original line shape | **First priority.** If text is legible, we have failed |
| **Head-on peak** | How much of that light enters the viewer's eye | Equal totals still dazzle if the light is concentrated |

The baseline is a flat plate wearing the same coating. Flat Musou Black returns
**1.1413 %**.

---

## 3. What gets built — at a glance

| Item | Specification | Quantity |
|---|---|---|
| Pyramid absorber panel | 1000×1000 mm, pitch 4 · depth 22 · tip 0.4 · backing 2 | ~100 panels |
| Silicone mould | 1000×1000, life 30–50 casts | 3–4 |
| Master pattern | SLA print (can be supplied) | 1 |
| Window unit | AR glass 733×620 + pyramid trap behind | Set by the spill map |
| Dark floor strip | 1 m in front of the unit, reflectance ≤ 5 % | — |

---

## 4. Pyramid absorber panel (the main product)

### 4.1 Geometry

| Item | Value | Tolerance |
|---|---|---|
| Pyramid pitch | 4.0 mm | Square grid |
| Pyramid depth | 22.0 mm | (research optimum is 20.0) |
| Tip flat | 0.4 mm | For mould life. 0.1 is the optical optimum |
| Valley | **Sharp** | Fillet radius under R0.1 |
| Backing | 2.0 mm | 24 mm total thickness |
| Edges | Terminate on a valley line | No border; cut at any valley |
| Panel-to-panel joint | Valley to valley | Misalignment up to ±0.2 mm costs nothing |
| Corners | Plain 90° butt | No moulding, no fillet |

### 4.2 Performance

| | Order spec (d22 / t0.4) | Research optimum (d20 / t0.1) | Flat Musou |
|---|---|---|---|
| Total reflectance | 0.185 % | 0.17668 % | 1.1413 % |
| Smear | 1.53× | 1.42× | 1.00 |
| Head-on peak | 0.173 | 0.0400 | 1.00 |

Going to depth 22 and relaxing the tip to 0.4 costs **roughly 4× on head-on
peak**. That is still a sixth of a flat matte panel. Total reflectance rises
only 4 %, and smear actually improves slightly.

**It performs better at grazing angles.** At 70° a flat Musou surface brightens
to 4.27 %; this panel stays at 0.198 %. A gap of 21.6×. That means the corners
where projectors graze the wall can be covered with the same single panel type.

### 4.3 Why it wins

A flat plate takes one hit and returns everything. Inside a pyramid valley a beam
bounces about nine times. Each bounce leaves 1 % alive, so by the time light finds
its way out there is essentially nothing left.

### 4.4 Material and process

- Soft to semi-rigid urethane, **foamed preferred**. Colour: carbon-black pigmented.
- Target bulk material reflectance ≤ 5 % (to be confirmed by coupon measurement).
- Panel weight roughly 0.6–1 kg.
- Process: **3D-printed master → platinum silicone mould → foamed urethane casting.**
- Surfaces destined for paint must accept primer then Musou Black (silicone bodies will not).

**Standard injection moulding is optically rejected.** It cannot hold a sharp
valley. A fillet of just 0.1 mm radius in the valley pushes head-on peak to twice
the allowance, because the concave trough concentrates light back toward the source.

**Extrusion is rejected for the base panel too.** Extrusion produces grooves. A
pyramid tip is a *point* — 0.06 % of the area; a groove tip is a *line* — 2.5 %.
At the same tip width the groove is 40× brighter head-on (measured 0.040 vs 0.894).

### 4.5 Acceptance test (first article, measured by the buyer)

| Item | Criterion |
|---|---|
| Total reflectance (unpainted) | 0.18 × material reflectance, ±25 % |
| Total reflectance (after Musou) | 0.177 %, ±25 %. Outside ±40 %, halt production until the cause is found |
| Tip and valley macro photos | Confirm §4.1 tolerances |

No optical measurement is asked of the supplier. The buyer performs it with a
flicker-accumulation method (procedure supplied).

---

## 5. Coating

### 5.1 The 0.18 rule

Cast the panel in bare material and, whatever that material's reflectance is,
**the panel returns 0.18 × that value**. Three materials at 4 %, 5 % and 8 % land
exactly on one line, and the measured 0.177 % for 1 % Musou is explained by the
same coefficient. Paint budgeting is now arithmetic.

### 5.2 Painted area is 10× the panel area

Because of the slopes. A 100 m² wall carries 1,000 m² of paintable surface.
This must be stated explicitly in any quotation.

### 5.3 Two-tier painting

- Painting everything with Musou costs 50–100 M KRW in paint alone.
- **Paint only the 10–20 % that the audience actually sees; leave the rest as bare
  black urethane.** That drops to 5–20 M KRW.
- Even the bare zones are 33–88× darker than a flat white wall.

### 5.4 Basis of the coating model

Pinned to a published goniometric measurement of Musou Black (Filip & Vávra 2026):
1.00 % at 0°, 1.13 % at 45°.

---

## 6. Window unit (where beams strike head-on)

Do not absorb. **Transmit.**

### 6.1 Assembly

- Picture-framing AR glass (museum glass), ≤ 1 % reflectance per surface, **733×620 mm**.
- Hung on a top hinge and **tilted. Minimum 25°, 35° recommended.**
- A cover lip conceals the top quarter of the glass.
- Behind it, an MDF box: 600×600 aperture, 500 deep, lined with pyramid panel.
- The glass rests on a top ledge with side rails. No adhesive; gravity holds it,
  and it lifts out for cleaning.
- Keep 1 m of dark floor (reflectance ≤ 5 %) in front of the unit.

99 % of incoming light passes through the glass and falls into the pyramid trap
below. The 1 % that reflects is always folded downward.

### 6.2 The mirror law

Where the reflected branch lands is set by tilt alone.

> **observer angle = −(beam angle + 2 × tilt)**

At 15° tilt a level beam reflects to −30°, which is a seated viewer's line of
sight. At 25° it moves to −50°, outside the audience band. **Hence the 25°
minimum.** 35° adds margin for light bouncing up off the floor.

Dropping from 35° to 25° reduces the projection depth of a 733 mm pane from
420 mm to 310 mm — a 26 % saving.

### 6.3 Splitting the pane — the cut edges must be blacked

One large sheet is awkward to move and to hang. It can be split. **With one condition.**

| Build | Worst value |
|---|---|
| One pane, edges concealed | 0.000000 |
| 4 panes, **raw cut edges** | **116** |
| 4 panes, bright frames | 0.10 |
| 4 panes, blacked edges | **0.009** |

Light leaks out of the cut edges. A steeply incident beam is trapped inside the
pane by total internal reflection, runs along it, and exits at the cut end — the
pane acts as a light pipe. A single pane hides both edges (top under the lip,
bottom in the trough). Four panes add six edges with nowhere to hide.

**Blacking the cut faces drops it 12,000×.**

Three supporting rules:
1. Black every cut edge.
2. Frames must be black and recessed. A bright frame lights every viewing angle
   evenly, which is worse than an edge that flares at particular angles.
3. Prefer left–right splits. Vertical joints hide behind the frame.

### 6.4 Audience curve

With the dark floor in place, lowering your line of sight never makes the window
brighter than the wall.

| Viewer elevation | Brightness |
|---|---|
| At eye level and above | 0.000–0.001 % |
| −5° | 0.018 % |
| −12° | 0.062 % |
| −16° | 0.091 % |

The pyramid wall itself reads 0.177 %, so **down to −16° the window is darker
than the wall it replaces.**

Only one thing wakes it up: **a bright object standing inside the dark strip in
front of it.** No white props, no white flooring, no lit costume in that strip.

### 6.5 Where projectors may be placed (at 25° tilt)

- **Up to +29°** above: the pane intercepts the whole beam.
- **+29° to +54°**: partial interception.
- **Below −30°**: hazard zone. The reflected branch reaches the audience.

A window that receives a low-mounted projector is built upside down.

---

## 7. Measured and rejected (do not re-propose)

Each of these was actually built and measured.

| Idea | Result |
|---|---|
| Recessed boxes (plain / zigzag / louver / accordion / panel-clad) | Built five, lost five to the flat panel. The zigzag was brighter than bare flat stock |
| Honeycomb | Good on totals, but does nothing to shape (0.97×) |
| Spraying only the tips | 1/16 the paint cost, but does not move head-on peak at all |
| Flocked paper | At any fibre angle, head-on peak is 6–9× the allowance |
| Mirror funnel (shiny walls, painted valley only) | Oblique light exits after 1–2 bounces. Shinier walls make it worse |
| Vertical Fresnel plate | The front face is simply a vertical mirror — 25,000× flat Musou |
| Walkable grating floor | Fails the grazing-angle rule. Survives only as a conditional option |

**Three design laws bought with those failures:**
1. A concave right-angle corner facing the beam is a retroreflector.
2. No face normal may point into the incoming cone (±40°).
3. An absorbing texture needs fine-pitch, near-vertical faces. Sheet metal 1 mm
   thick cannot be folded that way.

**The best use of space behind the wall is distance, not a box. Move the panel back.**

---

## 8. Not yet measured physically (pending before ordering)

| # | Item | Why it is needed |
|---|---|---|
| 1 | Spill-map photographs (low-exposure frame + haze-only frame) | Decides which walls become Musou zones |
| 2 | Black urethane coupon reflectance | The material value that feeds the 0.18 rule |
| 3 | Musou Black coverage per litre | Whether the paint budget is millions or tens of millions of KRW |
| 4 | Museum glass R at 35°, plus one week of dust | The window unit's real performance |
| 5 | Printed coupon acceptance test | Reconciles the simulation prediction against a physical part |

**The coating's surface roughness is still unmeasured.** Depending on it, "N times
darker than a flat plate" ranges from 3 to 11.6. The design ranking does not move,
but until a coupon is measured the honest claim is **"3–5×"** and nothing sharper.

---

## 9. Documents supplied

- Manufacturing file: `pyr_universal_p4_d20_t010_200x200.stl` (with 1 m scale-up drawing)
- Drawing: `blueprint_p4d22t04.png` (dimensions and machining cautions marked)
- Measurement procedure and acceptance criteria
- The simulator exports STL at the press of a button

---

## 10. References

1. J. Filip, R. Vávra, *"How dark is dark? A reflectance and scattering analysis of black materials"*,
   J. Opt. Soc. Am. A 43(7), 1037–1045 (2026). DOI 10.1364/JOSAA.589935 · arXiv:2601.05094
   — Goniometric measurement of Musou Black. **The root of every absolute value here.**
2. Kaster, *"Macroscopic structural light absorbers"*, J. Appl. Phys. 138, 174904 (2025).
   Carl Zeiss AG. arXiv:2507.05152 — The closest prior art.
3. A. Davis, H. F. Nijhout, S. Johnsen, *"Diverse nanostructures underlie thin ultra-black scales in butterflies"*,
   Nature Communications 11:1294 (2020).
4. S. Mouchet, *"Infrared absorbers inspired by nature"* (2024). arXiv:2404.18169
5. US Patent 11,209,577 B2, *"Macro-scale features for optically black surfaces"*, Ocean Insight Inc. (2021).
   — Broad claims over mm-scale black surface structures. **Clear rights before ordering.**
6. Commercial products — Musou Black (KoPro) · LaserCube Ultra 7.5W MK2 (X-Laser; beam 7–14 mm at the wall) ·
   museum glass (≤ 1 % reflectance per surface) · aluminium honeycomb core (Huarui Honeycomb)
