# Commercial aluminium honeycomb — what can actually be bought

Read 2026-08-12 from Huarui Honeycomb Technology Co., Ltd (alcomb.com), Foshan,
Guangdong. Same tagging rules as `SUMMARY.md`: `[확인]` read it on the page ·
`[추측]` plausible, unverified · `[모름]` unknown.

**Why this file exists.** The 2026-08-12 geometry search compared every topology
at a common "minimum feature size", which silently assumed every topology is
made the same way — FDM, 0.4 mm nozzle. That assumption is wrong for the cell
families. Aluminium honeycomb is a commodity with foil an **order of magnitude
thinner than one FDM nozzle**, and black-anodised honeycomb light traps are
already sold for exactly our application. Any fair comparison has to put each
family at the feature size *its own best process* delivers, and for the cell
families that process is not printing.

**None of these pages give core thickness (= our depth).** That is the one
parameter we most need and it is `[모름]` throughout. It has to come from a
quote. See the open questions at the end.

---

## 1. Aluminium honeycomb core — the standard grid

`https://www.alcomb.com/product/aluminum-honeycomb-core` `[확인]`

**The cell size and foil thickness are COUPLED into two product families.** This
is the constraint that matters most for us and it is not obvious from the
category page:

| family | cell size (mm) | foil thickness (mm) |
|---|---|---|
| **Micro-cell** | 0.86 · 1.04 · 1.73 · 2.6 · 3.17 · 3.47 · 5.2 | **0.03 · 0.04** |
| **Regular cell** | 6.5 · 8.47 · 9.53 · 12.7 · 19.05 · 25.9 (+ custom) | **0.04 · 0.05 · 0.06 · 0.07 · 0.08 · 0.1** |

- alloy 3003, or 3003/5052 `[확인]`
- density tolerance ±10% `[확인]`
- service range −55 °C to 175 °C `[확인]`
- max sheet: micro-cell 300×300 to 2000×1700 mm (varies with thickness);
  regular cell up to 8000×1700 mm `[확인]` — **these are panel dimensions, not
  core depth**
- micro-cell stated applications include *"lighting, purification, ventilator
  filter, photography, **laser bed**"* `[확인]`

**So a 0.1 mm wall forces a cell of 6.5 mm or coarser, and a 2.6 mm cell forces
a 0.03–0.04 mm wall.** You cannot order a thick wall on a fine cell in this
product line.

## 2. Light louver / black grid mesh — the coupling relaxes

`https://www.alcomb.com/product/round-aluminum-honeycomb-light-louver` `[확인]`
`https://www.alcomb.com/product/black-honeycomb-grid-mesh-for-lighting` `[확인]`

These are the products sold *for our purpose* — "shield for illuminators, reduce
glare", used in traffic lights, light fixtures, photography.

| | light louver | black grid mesh |
|---|---|---|
| cell size | **1 – 30 mm** | **1 – 30 mm** |
| foil thickness | **0.04 · 0.05 · 0.06 · 0.07 · 0.08 · 0.1 · 0.2 mm** | **0.04 – 0.1 mm** |
| alloy | AA3003H18, AA5052H18 | aluminium alloy `[모름]` which |
| finish | **anodized** or mill finished | **black anodized** |
| shape | round | square or round |
| frame | optional | available |
| overall | "customized" | — |

**Two things here contradict §1 and are better for us:**

1. **Cell size is quoted as a continuous 1–30 mm range**, not the discrete
   micro/regular ladder, and **foil goes to 0.2 mm**. `[추측]` The louver line is
   a made-to-order cut of the same cores, so the ladder in §1 is probably still
   the real constraint underneath and "1–30 mm" is a marketing range. **Do not
   design against a combination outside §1 without confirming it in a quote.**
2. **The black is ANODISED, not painted.** That matters more than it looks:
   anodising is an electrolytic bath, so it reaches the full depth of a 50 mm
   cell uniformly. `metrics/01_rho_dh.md` carries "coating reach into a deep
   cell is unverified" as an open item, and Filip & Vávra warn specifically
   about substrate showing through a thin sprayed film. **Anodised honeycomb
   removes that open item; a spray-painted 3D print does not.**

## 3. Slant honeycomb — our "leaning cell" is a stock item

`https://www.alcomb.com/product/slant-aluminum-honeycomb-core-with-black-color`
`[확인]`

- **slant angles 30°, 45°, 60°** `[확인]`
- foil thickness **0.04 – 0.1 mm** `[확인]`
- **"painted black before cutting into size"** `[확인]` — painted, NOT anodised,
  unlike the grid mesh above. Surface treatment options listed generally as
  "powder coating, anodized, etc." `[확인]`
- cell size, depth, panel size, alloy, density: **not stated** `[모름]`
- production: multilayer foil laminated, then stretched and expanded `[확인]`
- stated uses: structural support, energy absorption, light diffusion, flow
  straightener `[확인]` — **no optical performance data of any kind**

`scripts/geom_topo.py`'s `cell_lean_deg` was built on 2026-08-11 as a novel
combination of the shingle's inclined walls with the honeycomb's full-depth
cells. **It is a stock product.** The commercial angles 30/45/60 are exactly the
lean values worth measuring, and our sweep used 0/10/20/30 — only one of which
overlaps.

---

## 4. The buildable design space, with our derived quantities

Hex network: exposed area fraction = `2t/p`, cavity aspect = `depth/p`.
Computed here at **depth 50 mm**, which is `[모름]` as an availability at the
fine end (see open questions).

| cell p (mm) | foil t (mm) | family | exposed 2t/p | aspect @ d50 |
|---|---|---|---|---|
| 0.86 | 0.03 | micro | 6.98 % | **58.1** |
| 1.04 | 0.03 | micro | 5.77 % | 48.1 |
| 1.73 | 0.04 | micro | 4.62 % | 28.9 |
| 2.6 | 0.04 | micro | 3.08 % | 19.2 |
| 3.17 | 0.04 | micro | **2.52 %** | **15.8** |
| 3.47 | 0.04 | micro | 2.31 % | 14.4 |
| 5.2 | 0.04 | micro | **1.54 %** | 9.6 |
| 6.5 | 0.08 | regular | 2.46 % | 7.7 |
| 6.5 | 0.10 | regular | 3.08 % | 7.7 |
| 8.47 | 0.08 | regular | 1.89 % | 5.9 |
| 8.47 | 0.10 | regular | 2.36 % | 5.9 |
| 9.53 | 0.10 | regular | 2.10 % | 5.2 |
| 12.7 | 0.10 | regular | **1.57 %** | 3.9 |

For scale: a cone at pitch 5.5 with a 0.4 mm tip exposes **0.48 %**, still
3–5× less than any of these. But the 2026-08-12 result is that exposed area
stopped predicting the ranking once the material model gained Fresnel, so the
aspect column is at least as interesting — and **micro-cell at 1.73–3.17 mm
reaches aspect 16–29, which is inside the 7–80 range the bird-of-paradise
literature reports and which nothing this project has built has ever entered**
(`SUMMARY.md` §3.1, and its own note that our best was aspect 4).

---

## 5. Open questions — these need a quote, not a search

1. **Core depth availability, per cell size.** Everything above is silent on it.
   We want **50 mm**. Expanding a 0.86 mm cell to 50 mm deep is an aspect of 58
   in manufacture and `[추측]` unlikely; 3–6 mm cells at 50 mm are probably
   routine. **This single answer decides whether the interesting half of the
   table above exists.**
2. **Is the 1–30 mm louver cell range real, or a cut of the §1 ladder?** i.e.
   can a 3 mm cell be had with a 0.1 mm foil.
3. **Slant honeycomb: cell size and depth range**, and whether it can be had
   **anodised** rather than painted, given the coating-reach argument in §2.
4. **Anodised black — what is its actual reflectance?** Everything in this
   project is modelled on Musou Black paint (ρ_dh(0) = 0.998 %, Filip & Vávra).
   Black anodised aluminium is a different and generally *worse* absorber;
   Kaster models it at **5 % reflectance, 85 % Lambertian / 15 % Gaussian
   FWHM 25°** (`2507.05152v1.pdf` p.7). **If the panel is anodised aluminium
   rather than painted, every absolute number in this project is off by roughly
   5×** and the diffuse fraction is near the Lambertian end where our own sweep
   says designs behave differently. This is not a detail; it is a different
   material.
5. Minimum order quantity and whether a 100×100 mm coupon can be sampled — the
   whole project is blocked on one measured coupon.

---

## 6. What this does to the comparison

The 2026-08-12 feature-matched sweep put every family at 0.2/0.3/0.4 mm and the
cone won at all three. That comparison is now known to be the wrong axis:

| family | realistic process | realistic minimum feature |
|---|---|---|
| honeycomb / cell | expanded aluminium foil, **bought** | **0.03 – 0.1 mm** |
| slant honeycomb | same, stock item at 30/45/60° | 0.04 – 0.1 mm |
| shingle, parallel | folded / laser-cut sheet | `[추측]` 0.05 – 0.2 mm |
| shingle, random azimuth | 3D print only | 0.4 mm |
| cone | mould or FDM | **`[모름]` — the open question** |
| truss, cells | 3D print only | 0.4 mm |

A cone pulled from a mould is not limited by an FDM nozzle, and the tip is that
family's dominant variable, so **the cone's realistic tip diameter decides the
whole comparison** and it is the one number nobody has yet.
