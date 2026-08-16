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
    # Measurement builds need cones far past the window; an export wants the
    # pattern to stop at the panel edge. 0 places centres only inside the face.
    centre_margin_pitches: float = 1.0
    # Tileable placement: the centre field is made exactly periodic over
    # face_w x face_h, so a cone crossing the right edge has its other half
    # entering at the left edge of the neighbouring module. Cutting the tile at
    # the boundary then reassembles whole cones when modules are butted, with
    # no flat border anywhere -- a flat border would be the brightest thing on
    # the panel.
    tileable: bool = False

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

    # --- secondary (interstitial) cones ---
    # Head-on reflectance comes from the exposed tips; grazing reflectance
    # comes from the smooth flanks of the big cones. Different surfaces, so
    # they can be attacked separately: drop a finer array into the valleys
    # between the primary cones, but SHORTER, so its tips sit below the
    # primary tips and are shadowed at head-on while still trapping the rays
    # that skim the primary flanks.
    #
    # This is the butterfly's ridges-plus-trabeculae hierarchy at a scale
    # where geometric optics still applies. It is not the flank serration
    # that failed earlier: a sawtooth only deflects a grazing ray, a cone
    # still traps it.
    second_ratio: float = 0.0      # secondary pitch / primary pitch; 0 = off
    second_depth_frac: float = 0.55  # secondary height / primary height
    second_tip: float = 0.4        # secondary tip radius

    # --- variation ---
    # Height jitter is OFF by default. With it on, the shallowest cone sets
    # where the backing slab has to sit for every cone to reach it, and that
    # slab then fills the deepest valleys: at depth 30 and jitter 0.15 the slab
    # rises to -25 mm and 5 mm of valley disappears, which measured 4x worse
    # (0.0046 -> 0.0183%). Position jitter alone already breaks periodicity,
    # and this keeps the measured geometry identical to the exported one.
    depth_jitter: float = 0.0
    # cavity cross-section, see cavity_radius(). 1.0 / 0.0 is the plain cone
    # every result before 2026-08-11 used.
    profile_power: float = 1.0
    profile_bulge: float = 0.0
    profile_lip: float = 0.0
    profile_lip_at: float = 0.25
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

    if p.tileable:
        # snap the lattice so a whole number of cells spans the module, and an
        # even number of rows so the hex row offset returns to phase 0
        nx = max(1, round(p.face_w / dx))
        nz = max(2, round(p.face_h / dz))
        if p.lattice == "hex" and nz % 2:
            nz += 1
        dx, dz = p.face_w / nx, p.face_h / nz
        base = []
        for iz in range(nz):
            for ix in range(nx):
                x = ix * dx + (dx * 0.5 if (p.lattice == "hex" and iz % 2)
                               else 0.0)
                z = iz * dz - p.face_h / 2.0
                x += (2.0 * next(rng) - 1.0) * p.jitter * p.pitch
                z += (2.0 * next(rng) - 1.0) * p.jitter * p.pitch
                base.append((x, z))
        for gx in (-1, 0, 1):
            for gz in (-1, 0, 1):
                out += [(x + gx * p.face_w, z + gz * p.face_h)
                        for x, z in base]
        return out
    # generous margin: cones must run past the measurement window on all sides
    mz = p.margin_depths * p.depth
    mx = max(p.margin_depths * p.depth, p.centre_margin_pitches * p.pitch)
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


# --- the cavity profile ------------------------------------------------------
#
# The pillars interpenetrate and their union is the solid, so the CAVITY is the
# space between them. Which means the pillar's radius-versus-depth curve is the
# only thing that distinguishes a cone from a paraboloid, a tube, a needle or an
# undercut cell -- everything else (layout, jitter, tiling, backing slab,
# manifoldness) is already handled and shape-independent.
#
#     r(f) = f ** power,  then bulged:  r += bulge * sin(pi f) * (1 - r)
#
# with f = 0 at the tip and 1 at the base. Two knobs cover the whole library:
#
#     power 1.0            straight cone (what every result so far used)
#     power 0.5            paraboloid -- blunt near the tip, the profile the
#                          moth-eye survey found lowest of cone/parab/Gaussian
#                          (sub-wavelength there, so this is worth TESTING at mm
#                          scale, not assuming)
#     power 2.0            needle -- slim near the tip, fat only at the base
#     power 0.15           near-cylindrical tube: an axial ray misses the walls
#                          and strikes the floor near NORMAL incidence, which is
#                          the cheapest angle under Fresnel. Opposite profile to
#                          the V/cone family.
#     bulge > 0            barrel: the pillar overhangs just below the tip, so a
#                          ray striking near the tip is deflected INWARD instead
#                          of back out. Not printable face-up without support --
#                          deliberately not a constraint during exploration.
#
# Both are continuous, so a sweep can walk between shapes instead of choosing
# from a menu of hand-written mesh scripts.

def cavity_radius(f, power=1.0, bulge=0.0, lip=0.0, lip_at=0.25,
                  lip_width=0.12):
    """Pillar radius fraction at depth fraction f. 0 at the tip, 1 at the base.

    `bulge` widens the pillar smoothly and is MONOTONE -- verified over the
    whole (power, bulge) grid, min dr = 0.000000. It therefore cannot make an
    undercut, and the comment that once claimed it did was wrong.

    `lip` is what actually makes one: a localised Gaussian bump at `lip_at`
    that the profile then falls back from, so dr < 0 just below it. That is a
    real overhang -- the pillar is wider near the tip than beneath it, and a
    ray striking the lip is deflected INWARD rather than back out. Not
    printable face-up without support; deliberately not fenced off, because
    exploration is not manufacturing.
    """
    r = f ** max(1e-3, power)
    if bulge:
        r = r + bulge * math.sin(math.pi * f) * (1.0 - r)
    if lip:
        r = r + lip * math.exp(-((f - lip_at) / max(1e-3, lip_width)) ** 2)
    return min(1.0, max(0.0, r))


def seal_fraction(power, bulge, lip, pitch, overlap=1.6, n=4000):
    """Depth fraction at which neighbouring pillars close the cell off.

    Once the pillar radius reaches the hex circumradius pitch/sqrt(3), the
    three neighbours meet and everything below is not an optical cavity at all.
    A plain cone at pitch 7.5 seals at 72% of its nominal depth -- so "depth 30"
    has never meant 30 mm of usable cavity.
    """
    R = overlap * pitch / 2.0
    rc = pitch / math.sqrt(3.0)
    for k in range(1, n + 1):
        f = k / n
        if cavity_radius(f, power, bulge, lip) * R >= rc:
            return f
    return 1.0


def _cone_verts(verts, faces, cx, cz, H, R, r_tip, shift, n, m, y_top=0.0,
                power=1.0, bulge=0.0, lip=0.0, lip_at=0.25):
    """One closed pillar, appended in place. `y_top` sinks the apex."""
    base0 = len(verts)
    for k in range(m + 1):
        f = k / m
        r = r_tip + (R - r_tip) * cavity_radius(f, power, bulge, lip, lip_at)
        y = y_top - H * f
        for i in range(n):
            a = 2.0 * math.pi * i / n
            verts.append((cx + r * math.cos(a), y,
                          cz + r * math.sin(a) - shift * f))
    apex = len(verts); verts.append((cx, y_top, cz))
    floor = len(verts); verts.append((cx, y_top - H, cz - shift))
    for i in range(n):
        j = (i + 1) % n
        faces.append((apex, base0 + i, base0 + j))
        for k in range(m):
            a0 = base0 + k * n
            a1 = base0 + (k + 1) * n
            faces.append((a0 + i, a1 + i, a1 + j, a0 + j))
        b = base0 + m * n
        faces.append((floor, b + j, b + i))


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

    # slab extent, computed here so cones can be filtered against it: any cone
    # whose centre falls outside it is not attached and would survive a boolean
    # union as its own shell, which is what makes a print non-manifold
    sx0 = -(max(p.margin_depths * p.depth,
                p.centre_margin_pitches * p.pitch) + R)
    sx1 = p.face_w - sx0
    sz1 = p.face_h / 2.0 + max(p.margin_depths * p.depth,
                               p.centre_margin_pitches * p.pitch) + R

    for cx, cz in centres(p):
        if not (sx0 <= cx <= sx1 and -sz1 <= cz <= sz1):
            continue
        H = p.depth * (1.0 + (2.0 * next(rng) - 1.0) * p.depth_jitter)
        tilt = math.radians(p.tilt_deg
                            + (2.0 * next(rng) - 1.0) * p.tilt_jitter)
        # a tilted cone leans its axis; the apex stays on the face plane and
        # the base slides, which is what the bird-of-paradise barbule does
        shift = H * math.tan(tilt)

        _cone_verts(verts, faces, cx, cz, H, R, p.tip_radius, shift, n, m,
                    power=p.profile_power, bulge=p.profile_bulge,
                    lip=p.profile_lip, lip_at=p.profile_lip_at)

    # secondary array, dropped into the valleys and deliberately shorter so
    # its tips sit in the shadow of the primary ones
    if p.second_ratio > 0.0:
        sp = Cone3DParams(**{**p.__dict__, "pitch": p.pitch * p.second_ratio,
                             "second_ratio": 0.0, "seed": p.seed + 101})
        R2 = sp.effective_overlap() * sp.pitch / 2.0
        rng2 = _lcg(p.seed * 17 + 3)
        H2 = p.depth * p.second_depth_frac
        for cx, cz in centres(sp):
            h = H2 * (1.0 + (2.0 * next(rng2) - 1.0) * p.depth_jitter)
            # sunk so the tip starts below the primary apex plane
            # apex sunk so it starts below the primary apex plane and its
            # base lands on the same valley floor
            _cone_verts(verts, faces, cx, cz, h, R2, p.second_tip, 0.0,
                        max(6, n // 2), max(1, m - 1),
                        y_top=-(p.depth - h))

    # backing slab, so nothing sees daylight through the tile
    # The slab top must sit ABOVE the shallowest cone base, or no cone reaches
    # it. The previous "-0.5 clearance" put it 0.5 mm below the DEEPEST base,
    # so every cone floated and a boolean union left the slab as its own shell
    # -- measured directly: the cone mass spanned y -34.45..0 and the slab
    # y -38..-35.
    y0 = -p.depth * (1.0 - p.depth_jitter) + 0.5
    y1 = y0 - p.backing
    # kept inside the panel's own X lane: the flat control sits at
    # face_w + GAP and must not have this slab reaching under it
    # the slab follows the same margin as the cone field, so an export with a
    # small margin comes out flush with the panel edge instead of oversize
    # one extra pitch beyond the cone field, so every cone lands ON the slab.
    # Without it the outermost cones float free and a boolean union leaves
    # them as separate shells, which is what makes a print non-manifold.
    # the slab has to reach the outermost cone BASE, or edge cones float free
    # and the boolean union leaves them as separate shells
    R = p.effective_overlap() * p.pitch / 2.0
    mx = max(p.margin_depths * p.depth,
             p.centre_margin_pitches * p.pitch) + R
    h = p.face_h / 2.0 + max(p.margin_depths * p.depth,
                             p.centre_margin_pitches * p.pitch) + R
    m0 = len(verts)
    for y in (y0, y1):
        verts += [(-mx, y, -h), (p.face_w + mx, y, -h),
                  (p.face_w + mx, y, h), (-mx, y, h)]
    faces += [(m0, m0 + 1, m0 + 2, m0 + 3),
              (m0 + 7, m0 + 6, m0 + 5, m0 + 4)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((m0 + i, m0 + 4 + i, m0 + 4 + j, m0 + j))

    import geom_kit as _GK
    verts, faces = _GK.orient_outward(verts, faces)
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
        "second_ratio": p.second_ratio,
        "second_depth_frac": p.second_depth_frac,
        "second_tip_mm": p.second_tip,
        "tileable": p.tileable,
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
