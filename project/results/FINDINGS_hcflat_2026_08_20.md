# Honeycomb front, flat back: a global search, and what to build

2026-08-20. 509 designs, 1527 design-seed measurements, ~3 h of Cycles.
`scripts/sweep_hcflat.py` → `results/sweep_hcflat.csv`,
`scripts/rerank_hcflat.py` → `results/rerank_hcflat.csv`,
`scripts/plot_hcflat.py`, `scripts/report_hcflat.py`.

## The build being searched

Musou Black is the good coating and the expensive one. Anodised aluminium
honeycomb is what you buy. So pay for Musou only where it decides the answer —
the tips, and as far down the cell as a spray actually reaches — and take the
as-bought anodising for the rest of the wall. The floor is a separate pressed
sheet, painted flat before assembly, so it is Musou again.

```
y = 0            tips, and the painted band          musou_fit    ρ₀ 0.998 %
y = -paint       ------------------------------
                 the wall, as bought                 anodised_hi  ρ₀ 6.0 %
y = -deep_until  ------------------------------
                 the floor, painted flat             musou_fit
```

**That is one material, not three.** Per-slot materials cannot express it —
`mat_slots` says so in its own docstring, because a honeycomb wall is one quad
from mouth to floor and no labelling of faces can cut it. `make_depth_split`
switches `body` and `spec_scale` at a plane, and `deep_until` gives the
as-bought finish a *band* rather than a half-space, so the floor below it is
painted again. The two mechanisms are mutually exclusive in `build_scene`; the
depth split is the one that answers this question.

## What to build

**Cell 6.4 mm · foil 0.03 mm · depth 50–65 mm · Musou sprayed 8 mm down.**

ρ_dh = 0.00164, worst of θ = 0/±20/±40, mean over three geometry seeds.

6.4 mm is a standard commercial expanded-foil cell size, and 0.03 mm is about
1.2 mil — the thin end of stock foil, but stock. Nothing here needs a special
order.

**It is one of an equivalence class, and quoting it as "the winner" would be
false precision.** The top 20 designs span 0.001635–0.001678, a spread of
**2.6 %**, against a seed-to-seed SEM of 0.3–1.5 %. Re-measured at a constant
cell count (below) the top twelve span 3.4 %. Inside that band, choose on
manufacturability and price, not on optics:

| pitch | depth | wall | ρ_dh worst | cells in a 60 mm sample |
|---|---|---|---|---|
| 8.12 | 80 | 0.03 | 0.001631 | 7.4 |
| 8.00 | 80 | 0.03 | 0.001635 | 7.5 |
| **6.40** | **80** | **0.03** | **0.001643** | 9.4 |
| 6.50 | 80 | 0.03 | 0.001644 | 9.2 |
| 6.50 | 64 | 0.03 | 0.001646 | 9.2 |
| 5.20 | 80 | 0.03 | 0.001658 | 11.5 |
| 10.00 | 80 | 0.03 | 0.001664 | 6.0 |
| 4.16 | 80 | 0.03 | 0.001687 | 14.4 |

## Three design laws, measured

**1. The paint must reach about 1.25 cell widths down, and beyond that it buys
nothing.** This is the whole lever, and the natural variable is *pitch*, not
millimetres and not percent — binned in millimetres the same data is noise.

| paint reach (÷ pitch) | 0.25 | 0.50 | 0.75 | 1.00 | **1.25** | 1.50 | 2.00 | 3.00 |
|---|---|---|---|---|---|---|---|---|
| median ρ_dh | 0.00586 | 0.00370 | 0.00248 | 0.00200 | **0.00178** | 0.00183 | 0.00183 | 0.00199 |

For a 6.4 mm cell that is **8 mm of spray**. On the recommended design, 15 % of
depth reads 0.001635 and 10 % reads 0.001687 — 3 % worse for a third less
paint — while 5 % reads 0.002916 and no paint at all reads 0.009483.

**Painting nothing but the tips buys almost nothing: 0.00948 against 0.01065
for a bare anodised panel.** The tips are under 1 % of the area and the band is
what matters.

**2. Depth saturates near aspect 8–10.** Past depth ≈ 8 × pitch the wall is
already black before the light reaches the floor, and more depth is material
you are paying to ship. Between depth 50 and 80 at pitch 6.5 the answer moves
0.5 %.

**3. Thinner foil is monotonically better, and it is the strongest geometric
axis.** At pitch 6.5 / depth 80: wall 0.03 → 0.001635, 0.05 → 0.001687,
0.08 → 0.00179, 0.20 → 0.00243. Tip area is 2·wall/pitch and the tips are the
one surface a head-on observer strikes directly.

**Pitch has an interior optimum around 5–10 mm** — not the finest. A fine pitch
is a bigger tip fraction; a coarse one is a lower aspect at fixed depth. Those
pull against each other, which is why 2.0 mm and 16 mm both lose.

## The re-rank, which falsified its own predictions

`sweep_hcflat` measures every design on the same 60 mm panel, so cell count
falls as pitch rises — 30 cells at pitch 2, 3.8 at pitch 16. GATE 11 of the
2026-08-20 audit swept 5/10/25/50 cells and found ρ_dh falling monotonically and
*still* falling at 50, with a 10-cell sample reading ~5 % high. **The spread
across pitch here is 3 %. The bias was larger than the effect**, so the ranking
was not defensible and `rerank_hcflat.py` re-measured the top twelve at a
constant 25 cells a side (panel = 25 × pitch, up to 250 mm).

Pre-registered: R1 every design reads darker; R2 the coarse pitches gain most;
R3 the order changes.

**R1 failed. R2 failed.** The changes are −1.2 % to +1.2 %, mixed in sign, and
the order barely moved. **This family is far less cell-count sensitive than the
one GATE 11 swept**, so the 60 mm ranking was safe after all — which R3 said was
worth knowing, and is the only reason to have run it.

## Where the light goes (metric 08)

The six best designs and a flat plate of the same Musou, mapped over the scoring
band on one shared colour scale — `results/hcflat_maps_globalnorm.png`.
Excluding θ_in = 0, where retro, specular and audience all coincide:

| | audience (θ_out=0) | retro (θ_out=θ_in) | specular | retro ÷ audience |
|---|---|---|---|---|
| flat Musou plate | 0.004531 | 0.002764 | 0.069047 | 0.6× |
| best honeycomb | **0.000065** | 0.001457 | 0.000283 | **22×** |

**On the audience line the honeycomb is 69× darker than a flat plate of the
same coating**, and the flat plate's specular ridge is gone — suppressed 244×.

**But the honeycomb is a retroreflector, and the map says so plainly.** Its
brightest structure is the retro diagonal, 19–22× above its own audience line.
That is the corner-reflector geometry: a honeycomb wall and a flat floor are
mutually perpendicular mirrors, so a bounce off both reverses the ray. It is
excellent for the audience and it sends light back up the beam. **Whether that
matters depends on where the projectors sit relative to the people**, and
nothing in this repo knows that — it is README open item 1.

Head-on, cell (0, 0), the honeycomb is only 3.5× darker than flat: that is the
one direction where an observer looks straight down the cells and sees the tips.

## What would change these numbers

- **`anodised_hi` is an estimate in every shape parameter.** `materials.py`
  marks `diffuse_frac`, `roughness` *and* `ior` estimated, translated from
  Kaster 2025, and its own note says "Sweep it; do not trust it." ρ₀ = 6 % is
  the pessimistic end of a 3–6 % spread. The whole search is conditional on it.
  A goniometer measurement of the actual foil would settle it and could move
  every absolute number here.
- **The coating model is not reciprocal** (`FINDINGS_bidir_2026_08_20.md`), so
  the metric 08 cells carry that caveat. The *structure* of the maps is
  geometric and stands.
- **Zero physical measurements.** Still true, and still the largest open item.
- One azimuth plane; φ was not swept. `sweep_azimuth` exists for it.
