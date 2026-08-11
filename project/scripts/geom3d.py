"""
Fifth geometry family, and the first that is not an extruded cross-section:
an irregular array of cones.

Why leave the extrusion behind
------------------------------
Every family so far is a Y-Z profile swept along X, which makes all of them
anisotropic by construction -- they behave differently along the grooves than
across them, and the measurements show it (the V-groove holds 0.029% inside
+/-40 degrees but degrades to 0.266% at grazing). The Gaboon viper's black
scales, by contrast, show no specular peak at all and a smooth falloff with
emerging angle, which the literature attributes to an isotropic arrangement of
scale structure rather than to any single trapping feature.

The arithmetic that makes this worth doing
------------------------------------------
The head-on return is the exposed tip and essentially nothing else -- measured
across 24 combinations, reflectance divided by (tip area / cell area) stays
between 0.75 and 1.5 of the naive estimate. So the exposed fraction IS the
design variable, and it scales differently in one and two dimensions:

    1D ridge   exposed fraction = tip_width / pitch            (linear)
    2D cone    exposed fraction = pi r^2 / cell_area           (quadratic)

At a 0.8 mm tip and 13 mm pitch that is 6.15% against 0.30% -- twenty times
smaller for the same feature size and the same depth. If the tip law holds, the
same 0.5% coating should read about 0.0015% instead of 0.0264%.

Construction
------------
Cones are built as separate closed solids and allowed to interpenetrate. For
opaque rendering the union is what matters, so no Voronoi partition or height
field is needed: overlapping solids give exactly the intended surface, with the
valleys forming naturally where neighbours intersect, and the apex radius stays
under exact control instead of being set by a sampling grid.

A jittered lattice, not a regular one: a scanning beam crossing a periodic cell
array produces periodic bright spots, which is the one thing the whole project
must avoid.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from profile2d import _lcg


@dataclass
class Cone3DParams:
    # --- envelope (mm) ---
    face_w: float = 100.0          # smaller than the 500 mm module on purpose:
    face_h: float = 100.0          # a 3D tile is measured as a coupon
    depth: float = 50.0            # cone height, apex plane to valley floor
    backing: float = 4.0

    # --- cells ---
    pitch: float = 13.0            # mean centre-to-centre spacing
    jitter: float = 0.30           # lattice jitter as a fraction of pitch
    lattice: str = "hex"           # hex | square
    seed: int = 23
    # A tilted camera looking at depth D through the window travels
    # D / tan(90 - theta) in Z before it reaches the floor -- 5.7 D at
    # theta = 80. Without a field that wide the view runs off the tile and
    # reads world background instead of panel, which is exactly what produced
    # an impossible 27% "reflectance" on the first run.
    margin_depths: float = 6.5

    # --- cone ---
    tip_radius: float = 0.4        # THE exposed feature. 0.4 = a 0.8 mm tip,
                                   # matching the 1D design it is compared to
    # Base radius as a multiple of pitch/2. It has to cover the jitter, not
    # just the nominal spacing: two neighbours can drift 2*jitter*pitch apart,
    # and if their bases do not still meet the backing slab shows through as a
    # flat patch. The first sweep had overlap 1.15 against jitter 0.30 and the
    # no-jitter case came out 8x darker -- that was gaps, not regularity being
    # better. `effective_overlap()` enforces the floor.
    overlap: float = 1.15
    radial_seg: int = 32           # facets around the cone
    height_seg: int = 3            # rings down the flank

    # --- variation ---
    depth_jitter: float = 0.15     # per-cone height variation
    tilt_deg: float = 0.0          # lean the cones, bird-of-paradise style
    tilt_jitter: float = 0.0

    # ---- derived ----------------------------------------------------------

    def effective_overlap(self) -> float:
        """Base radius multiple, raised if needed to cover the jitter."""
        return max(self.overlap, 1.0 + 2.0 * self.jitter)

    def gap_risk(self) -> bool:
        return self.overlap < 1.0 + 2.0 * self.jitter

    def cell_area(self) -> float:
        """Mean area served by one cone."""
        if self.lattice == "hex":
            return math.sqrt(3.0) / 2.0 * self.pitch ** 2
        return self.pitch ** 2

    def tip_fraction(self) -> float:
        """Head-on exposed fraction: the whole ball game, now quadratic."""
        return math.pi * self.tip_radius ** 2 / self.cell_area()

    def equivalent_1d_fraction(self) -> float:
        """What the same tip and pitch would expose as a 1D ridge."""
        return 2.0 * self.tip_radius / self.pitch

    def aspect(self) -> float:
        return self.depth / self.pitch

    def half_angle_deg(self) -> float:
        return math.degrees(math.atan(0.5 * self.pitch / max(self.depth, 1e-9)))


# --------------------------------------------------------------------------

def centres(p: Cone3DParams) -> list[tuple[float, float]]:
    """Jittered lattice of cone centres, in (x, z) on the face plane."""
    rng = _lcg(p.seed)
    out = []
    if p.lattice == "hex":
        dx = p.pitch
        dz = p.pitch * math.sqrt(3.0) / 2.0
    else:
        dx = dz = p.pitch
    # generous margin: cones must run past the measurement window on all sides
    mz = p.margin_depths * p.depth
    mx = 0.35 * p.face_w
    nx = int((p.face_w + 2 * mx) / dx) + 2
    nz = int((p.face_h + 2 * mz) / dz) + 2
    ix0 = -int(mx / dx) - 1
    iz0 = -int((p.face_h / 2 + mz) / dz) - 1
    for iz in range(iz0, iz0 + nz):
        for ix in range(ix0, ix0 + nx):
            x = ix * dx + (dx * 0.5 if (p.lattice == "hex" and iz % 2) else 0.0)
            z = iz * dz
            x += (2.0 * next(rng) - 1.0) * p.jitter * p.pitch
            z += (2.0 * next(rng) - 1.0) * p.jitter * p.pitch
            out.append((x, z))
    return out


def build_mesh(p: Cone3DParams):
    """
    Return (verts, faces) for the whole tile: one closed cone per centre, plus
    a backing slab. Cones interpenetrate; for an opaque surface the union is
    the geometry, so no boolean is required.

    Coordinates match the rest of the project: X across the face, Y depth with
    the apex plane at Y = 0 and deeper being negative, Z vertical.
    """
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    rng = _lcg(p.seed * 31 + 7)

    R = p.effective_overlap() * p.pitch / 2.0
    n = max(6, p.radial_seg)
    m = max(1, p.height_seg)

    for cx, cz in centres(p):
        H = p.depth * (1.0 + (2.0 * next(rng) - 1.0) * p.depth_jitter)
        tilt = math.radians(p.tilt_deg
                            + (2.0 * next(rng) - 1.0) * p.tilt_jitter)
        # a tilted cone leans its axis; the apex stays on the face plane and
        # the base slides, which is what the bird-of-paradise barbule does
        shift = H * math.tan(tilt)

        base0 = len(verts)
        # apex cap ring, then rings down the flank to the base
        for k in range(m + 1):
            f = k / m
            r = p.tip_radius + (R - p.tip_radius) * f
            y = -H * f
            for i in range(n):
                a = 2.0 * math.pi * i / n
                verts.append((cx + r * math.cos(a),
                              y,
                              cz + r * math.sin(a) - shift * f))
        apex = len(verts)
        verts.append((cx, 0.0, cz))          # single point closing the cap
        floor = len(verts)
        verts.append((cx, -H, cz - shift))   # single point closing the base

        for i in range(n):
            j = (i + 1) % n
            faces.append((apex, base0 + i, base0 + j))
            for k in range(m):
                a0 = base0 + k * n
                a1 = base0 + (k + 1) * n
                faces.append((a0 + i, a1 + i, a1 + j, a0 + j))
            b = base0 + m * n
            faces.append((floor, b + j, b + i))

    # backing slab, so nothing sees daylight through the tile
    y0 = -p.depth * (1.0 + p.depth_jitter) - 0.5
    y1 = y0 - p.backing
    # kept inside the panel's own X lane: the flat control sits at
    # face_w + GAP and must not have this slab reaching under it
    w = p.face_w
    h = p.face_h / 2.0 + p.margin_depths * p.depth + 2 * p.pitch
    m0 = len(verts)
    for y in (y0, y1):
        verts += [(-0.35 * w, y, -h), (1.35 * w, y, -h),
                  (1.35 * w, y, h), (-0.35 * w, y, h)]
    faces += [(m0, m0 + 1, m0 + 2, m0 + 3),
              (m0 + 7, m0 + 6, m0 + 5, m0 + 4)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((m0 + i, m0 + 4 + i, m0 + 4 + j, m0 + j))

    return verts, faces


def describe(p: Cone3DParams) -> dict:
    return {
        "family": "cone3d",
        "depth_mm": p.depth,
        "pitch_mm": p.pitch,
        "pitch_mean_mm": p.pitch,
        "lattice": p.lattice,
        "jitter": p.jitter,
        "tip_radius_mm": p.tip_radius,
        "tip_width_mm": 2.0 * p.tip_radius,
        "cell_area_mm2": p.cell_area(),
        "tip_fraction": p.tip_fraction(),
        "equivalent_1d_fraction": p.equivalent_1d_fraction(),
        "fraction_gain_vs_1d": p.equivalent_1d_fraction() / max(p.tip_fraction(), 1e-12),
        "aspect": p.aspect(),
        "est_bounces": 90.0 / max(2.0 * p.half_angle_deg(), 1e-9),
        "half_angle_deg": p.half_angle_deg(),
        "depth_jitter": p.depth_jitter,
        "margin_depths": p.margin_depths,
        "overlap": p.overlap,
        "effective_overlap": p.effective_overlap(),
        "overlap_was_raised": p.gap_risk(),
        "tilt_deg": p.tilt_deg,
    }


if __name__ == "__main__":
    for pitch in (8.0, 13.0, 20.0):
        prm = Cone3DParams(pitch=pitch)
        v, f = build_mesh(prm)
        d = describe(prm)
        print("pitch %4.1f  tip frac %.5f  (1D would be %.5f, %.1fx worse)  "
              "A=%.1f  bounces %.1f  verts=%d faces=%d"
              % (pitch, d["tip_fraction"], d["equivalent_1d_fraction"],
                 d["fraction_gain_vs_1d"], d["aspect"], d["est_bounces"],
                 len(v), len(f)))
