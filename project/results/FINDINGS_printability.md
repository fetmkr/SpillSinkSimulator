# 2026-08-11 — printability audit of geom3d, and a correction to my own number

Produced by `scripts/printability.py` (new, pure stdlib, imports without
Blender). Target: FDM, face up, 0.4 mm nozzle, **no support material**.

---

## 0. CORRECTION — the 38.3 degree overhang figure was wrong

Earlier tonight I computed, by hand from `cavity_radius`, that the worst
overhang across the `sweep_shapes` grid at `profile_lip = 0.35` was **38.3
degrees** (pitch 11, depth 20), and concluded that the lip designs are
self-supporting because 38.3 < 45.

**The correct figure is 32.2 degrees.** Convergence on an isolated pillar:

| height_seg | worst flank overhang |
|---|---|
| 3 | **0.00 deg** |
| 8 | 19.64 |
| 16 | 29.93 |
| 32 | 31.32 |
| 64 | 31.99 |
| 128 | 32.04 |
| analytic continuum | **32.24** |

The mesh-based checker reproduces the continuous profile to 0.2 deg, so the
checker is not what was wrong. **My hand calculation used a base radius of the
full pitch (R = 11.0 at pitch 11); `effective_overlap()` actually gives 8.80**
(overlap 1.15, raised to 1.60 by jitter 0.30). Feeding R = 11.0 into the same
profile reproduces 38.5, which is where my number came from.

**The conclusion survives — 32.2 is still well under the 45 degree
self-support rule, and lip designs print face-up without support.** The number
does not. Note also that 45 deg is a rule of thumb, not a measurement of the
printer that will actually be used.

---

## 1. NEW: at the shipped `height_seg`, the lip's undercut does not exist

Read the table above again at `height_seg = 3` — the geom3d **default**, and the
value `export_cone.py` ships with. Worst overhang **0.00 degrees**, because the
four rings at f = 0, 1/3, 2/3, 1 straddle the Gaussian lip bump and never sample
its far side.

**The exported solid is not the profile that was designed.** This is the same
class of defect as the voided `__void__sweep_shapes_hseg3.csv` run, where the
answer moved 50.6x between hseg 3 and 12 — but that fix was applied to the
*sweep* and never to the *exporter*.

**Any `profile_lip` claim, optical or printable, requires `height_seg >= 16`.**

---

## 2. NEW: the backing slab does not reach the outer cone bases

`geom3d.build_mesh` admits a cone centre anywhere in `[-mx, face_w + mx]` and
then builds the slab over *exactly* that same span. A centre sitting at the
limit puts half its base disc — radius R — past the slab edge, with nothing
under it.

Measured on the pitch-11 / depth-20 coupon: of 640 base triangles, 554 sit fully
on the slab, **86 poke off**, and 46 survive the buried-face filter =
**347 mm² of flat 90-degree ceiling over air**. Every configuration tested
reports 0.3–1.4% unsupported area at exactly `y = -depth`, and **it is present
in the shipped export.**

One-term fix: the slab wants `mx + R`, or the centre filter wants `mx - R`.

**NOT APPLIED YET — deliberately.** `sweep_topo.py` is running right now with a
cone reference built by this same function, and changing the geometry mid-sweep
would make rows before and after the change incomparable. The optical effect is
negligible anyway (a few base discs at the far margin, far outside the
measurement window); this is an *export* defect, not a measurement one. Apply it
once the sweeps land, then re-export.

---

## 3. Two conventions in geom3d that had to be measured, not assumed

- **The winding is inverted.** `sum (a x b).c` over `build_mesh` output is
  **-51869** on a pitch-11 depth-20 coupon: cones, slab and caps all point their
  normals *into* the solid. Consistent, but flipped — taken literally, every
  upward cone flank reads as a 67 degree overhang. Cycles renders both sides of
  a face so this has never cost a measurement, but any tool that reasons about
  normals must detect it. `printability.outward_sign()` does.
- **It is a union that was never unioned.** Every cone base disc sits 0.5 mm
  inside the backing slab, and those buried flat downward faces are ~20% of the
  total area and read as 90 degree overhangs. All fiction. Removed by a
  point-in-union test (7756 faces dropped on the shipped export).

---

## 4. The shipped export, measured

`export_cone.py` d30 / p7.5 / tip 0.2 / radial 24 / height_seg 3 / tileable,
40686 faces, 4.6 s:

| check | result |
|---|---|
| unsupported area | 0.649% at y = -30 — the slab-edge defect in §2 |
| **thinnest cross-section** | **0.437 mm at y = -0.10** |
| islands (needing support from below) | **0** over 162 layers at 0.201 mm |

**The tip is at the floor of what the printer can lay down.** `tip_radius = 0.2`
is exactly one nozzle width, so 0.437 mm is a single extrusion with essentially
zero margin. That is a deliberate choice recorded in CONTEXT.md — but it is now
measured rather than assumed, and it means tip radius cannot go lower on FDM.

Zero islands across all 8 configurations tested. Expected, since cones only
narrow going up — but previously unverified.

---

## 5. What the checker deliberately does NOT do

Recorded so it is not mistaken for coverage:

- **Inter-shell nearest approach is not reported.** It was built and measured
  (0.002–0.045 mm across 8 configs) and is pure artifact: geom3d cones are
  *required* to interpenetrate, so every "gap" was a cone-cone intersection
  curve where boundaries touch by construction. Not well-posed on an un-unioned
  mesh.
- `min_feature_report` uses a per-shell caliper width, so it cannot see a waist
  *within* a single shell.
- Coarsening the layer step can both invent **and** hide islands, and a coarse
  grid drops islands smaller than one cell. Both caps are returned in the result
  dict rather than hidden.

## 6. Validation against known answers

Cube → printable, 0 overhang. 30 deg wedge → 30.00, 0 unsupported. 60 deg wedge
→ 60.00, 200 mm² (exact). Slab + floating cube → 1 island, 64.0 mm² (exact).
T-cap → 90 deg, 400 mm².
