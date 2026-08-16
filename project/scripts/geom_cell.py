"""
Seventh geometry family: cell lattices -- wall networks that enclose a cavity,
built as unions of closed wall solids.

Why this family exists, and it is not the reason geom_topo gave
---------------------------------------------------------------
`geom_topo.py`'s docstring argues that any wall/honeycomb topology "LOSES this
axis by construction", because a pillar array exposes pi r^2 per cell against a
wall network's t * perimeter -- 0.26% against 10.7% at pitch 7.5, a factor of
40. The honeycomb went into `sweep_topo.py` as the negative control for exactly
that argument.

It did not lose by 40x. `results/FINDINGS_topo_smoke.md` measures it at 1.51x
head-on and **1.30x worst-over-theta**, against a cone re-measured in the same
frame under the same fitted coating. Two geometries 41.3x apart in exposed area
landed within 30% of each other. The estimator was checked and reproduces to 4
decimals; the render was checked against the flat-plate and 0.05 controls and
violates neither. So the conclusion stands:

    Under the corrected Fresnel coating, head-on reflectance is NOT governed by
    exposed area.  (FINDINGS_topo_smoke.md, "What it means")

That removes the only argument against wall networks, and leaves them with an
advantage no pillar family can have: **cells with vertical (or undercut) walls
never seal.** `geom3d.seal_fraction` puts a plain cone at pitch 7.5 at 0.722 of
its nominal depth, so a "depth 30" cone is 21.7 mm of cavity. A cell wall runs
the full 30. And `results/analysis_shapes.md` section 5 found

    usable aspect = seal_frac x depth / pitch

to be the single best predictor of the worst-theta score it has
(Spearman -0.876; log(combined) ~ log(usable_aspect) slope -1.147, R^2 = 0.729
over 192 designs), beating nominal aspect (-0.734) and seal_frac alone (-0.499).
A cell lattice starts on that axis at seal_frac = 1.0 by construction, i.e. 1.39x
ahead of the cone at the same nominal depth and pitch before any tuning.

Five variants, and what each one is a test OF
---------------------------------------------
    square      Did the hex tiling matter at all? Same wall length per unit
                area as hex (2/pitch for both -- see exposed_fraction_est), so
                any difference between square and the measured honeycomb is a
                cell-SHAPE effect with the area held fixed. That is the cheapest
                available control on the new finding.

    triangle    2*sqrt(3)/pitch of wall per unit area, 1.73x the hex/square
                figure, and cells of sqrt(3)/4 * pitch^2 instead of pitch^2 --
                so at one wall pitch it is simultaneously more exposed area and
                a higher usable aspect per cell. Under the old area law this is
                strictly worse by 1.73x. Under FINDINGS it is a direct test of
                whether area still costs anything at all.

    mixed       A Voronoi lattice on jittered, randomly thinned seeds: a real
                cell-SIZE distribution with no periodic pitch anywhere. The
                project's hard rule (geom3d.py docstring) is that a scanning
                beam crossing a periodic cell array makes periodic bright spots,
                and every other variant here is periodic in its nominal lattice
                even when the vertices are jittered.

    reentrant   Cells wider at the floor than at the mouth. See _build_reentrant
                for why a tiling cannot do this without sacrificing half its
                cells, and what that costs.

    nested      A coarse cell whose floor carries a finer cell lattice --
                ridges-plus-trabeculae at a scale where ray optics still
                applies. A bimodal CONE array already died this way; see
                _build_nested for how this differs and why the difference is
                stated before the render rather than after it.

Conventions, matched to geom_topo.py and geom3d.py exactly
----------------------------------------------------------
X across the face (0 .. face_w), Y depth with the entrance plane at Y = 0 and
deeper NEGATIVE, Z vertical (-face_h/2 .. +face_h/2). Solids interpenetrate and
the union is the geometry -- for an opaque surface no boolean is needed. A
backing slab closes the bottom. Geometry runs margin_depths * depth past the
window on every side, because a camera tilted to theta travels D/tan(90-theta)
in Z before it reaches the floor, and without that margin the tilted view runs
off the tile and reads world background (metrics/01, "Known defects, fixed" --
every |theta| >= 50 number taken before margin_depths = 6.5 is void).

NOTHING RISES ABOVE Y = 0. The truss in geom_topo had a node sitting exactly on
Y = 0 which put the top half of its strut above the entrance plane; it was
caught by checking max(y) and is now sunk by one strut radius. The __main__
block here asserts max(y) <= 0 for every variant, every time.

How the wall network is built, and why it is not one hexagon per centre
----------------------------------------------------------------------
A polygon drawn around each JITTERED CENTRE only tiles the plane on an exact
lattice. Jitter the centres and the polygons stop sharing edges: every cell
raises its own full set of walls, neighbours overlap into doubled walls, and
gaps open between them. geom_topo's `voronoi_cells` docstring records finding
exactly this in its own honeycomb, and CONTEXT.md round 1 records the earlier
version of the same mistake -- "regular arrays are 8x darker than jittered ones"
turned out to be gaps, not regularity.

Two constructions avoid it, and this module uses both, per variant:

  * `square`, `triangle`, `reentrant`, `nested` jitter the shared VERTICES of a
    named lattice in one deterministic keyed pass, so both cells touching an
    edge read the same two endpoints. Cheap, and it keeps the lattice TYPE as
    the variable under test, which is the whole point of square-vs-triangle.
  * `mixed` computes a real Voronoi tessellation, because there the cell size
    distribution IS the variable and no lattice survives.

Either way each wall exists once, corners close, and `exposed_fraction_est()`
is a statement about the mesh rather than about an idealisation of it. That is
checkable without a render and it is checked: at jitter 0 the mesh-measured
top area equals the analytic estimate times exactly (1 + wall_top/pitch) --
1.0533 at pitch 7.5 and 1.1067 at 3.75, to four decimals, that factor being the
corner extension and nothing else. __main__ prints both columns every run,
because this project's rule is that a prediction made before the measurement is
worth far more than an explanation offered after it.

(geom_topo.py was rewritten onto a Voronoi honeycomb while this file was being
written. The two are siblings, not duplicates: its Voronoi is a jittered field
at CONSTANT site density, this module's `mixed` thins the field so cell AREA
varies by about 3x.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from profile2d import _lcg


# --- small vector helpers ---------------------------------------------------
# Duplicated from geom_topo.py rather than imported on purpose: this module has
# to stay a standalone drop-in sibling, and geom_topo is under active edit by
# other work. Only the ones actually used are here -- every wall in this family
# is defined by two IN-PLANE points plus two heights, so the 3-vector algebra
# geom_topo needs for its tilted plates and struts never comes up.

def _norm2(vx, vz):
    """Normalise an in-plane (x, z) vector. Returns (0, 0) on a degenerate one."""
    L = math.hypot(vx, vz)
    return (vx / L, vz / L) if L > 1e-12 else (0.0, 0.0)


# --- primitive solid --------------------------------------------------------

def _hexa(verts, faces, top4, bot4):
    """One closed hexahedron from 4 top corners and 4 bottom corners.

    Corners must be given in the same rotational order for both rings, or the
    side quads come out twisted. Cycles renders both sides of a face, so an
    inverted normal costs nothing; a twisted quad is a real self-intersection
    and would. (geom_topo._hexa, same reasoning.)
    """
    b = len(verts)
    verts.extend(top4)
    verts.extend(bot4)
    faces.append((b, b + 1, b + 2, b + 3))                  # top
    faces.append((b + 7, b + 6, b + 5, b + 4))              # bottom
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b + i, b + 4 + i, b + 4 + j, b + j))  # sides


# --- parameters -------------------------------------------------------------

@dataclass
class CellParams:
    variant: str = "square"     # square | triangle | mixed | reentrant | nested

    # --- envelope (mm), same meaning as TopoParams / Cone3DParams ---
    face_w: float = 60.0
    face_h: float = 60.0
    depth: float = 30.0
    backing: float = 2.0

    # --- lattice ---
    # 3.75, not geom_topo's 7.5. FINDINGS_topo_smoke.md "Immediate next step"
    # asks for pitch down to 2.5-3.75 on the honeycomb arm, and
    # analysis_shapes.md section 3 rules 7.50-11.00 out entirely: those pitches
    # win only under the d00 (pure-specular) material, and the project's
    # both-extremes rule then makes 3.75-5.50 "the only defensible choice".
    pitch: float = 3.75
    jitter: float = 0.30        # vertex jitter, fraction of pitch. Must stay
                                # below 0.5: two adjacent vertices can close by
                                # 2*jitter*pitch and at 0.5 they would cross,
                                # which turns a cell inside out.
    seed: int = 23
    margin_depths: float = 6.5
    centre_margin_pitches: float = 1.0

    # --- walls ---
    # 0.4 is one FDM nozzle and it is the ONLY wall value ever measured
    # (FINDINGS_topo_smoke.md point 3: "The wall thickness has not been
    # optimised, at all"). It is a floor, not an optimum.
    wall_top: float = 0.4
    wall_bot: float = 1.2

    # --- mixed: Voronoi on thinned, jittered seeds ---
    # Dropping seeds is what produces a cell SIZE distribution; jitter alone
    # only moves cells around at constant area. keep 0.65 gives roughly a
    # factor-3 spread in cell area.
    mixed_keep: float = 0.65
    mixed_jitter: float = 0.45  # seeds may sit anywhere, they are not a tiling
    mixed_ring: int = 3         # lattice blocks searched for bisector neighbours

    # --- reentrant: undercut cells ---
    # Lean of the wall from vertical. Positive leans the wall foot AWAY from its
    # cell centre, so the mouth overhangs the floor.
    #
    # 6.0, not 10.0. 10.0 was the first default and it RE-SEALS the cavity at
    # y = -28.5 of a 30 mm depth -- measured, not derived: a slice-and-flood-fill
    # of the built mesh read the dark cavity at 12.5 mm2 at the mouth, 302 mm2 at
    # y = -4 (the undercut, working), and 0.5 mm2 at y = -29.5. See
    # lean_max_deg(); the ceiling at pitch 3.75 / depth 30 / wall_bot 1.2 is
    # 9.51 deg. A default that quietly seals would have made seal_frac() -- and
    # therefore usable_aspect(), the top predictor in analysis_shapes.md 5 --
    # report 1.0 for a structure that is 95% closed.
    lean_deg: float = 6.0

    # --- nested: coarse cells carrying a finer lattice on their floor ---
    nest_ratio: float = 0.30        # secondary pitch / primary pitch
    nest_depth_frac: float = 0.35   # secondary height / primary depth
    nest_wall_top: float = 0.25
    nest_wall_bot: float = 0.6

    # ---- derived ----------------------------------------------------------

    def margin(self) -> float:
        return max(self.margin_depths * self.depth,
                   self.centre_margin_pitches * self.pitch)

    def cell_area(self) -> float:
        """Mean plan area served by one cell, at the mouth."""
        if self.variant == "triangle":
            return math.sqrt(3.0) / 4.0 * self.pitch ** 2
        if self.variant == "mixed":
            return self.pitch ** 2 / max(self.mixed_keep, 1e-6)
        return self.pitch ** 2

    def wall_length_density(self) -> float:
        """Millimetres of wall centreline per square millimetre of face.

        This is the whole geometry of the exposed-area question: every variant's
        head-on exposed fraction is just this times wall_top.

            square      2 / pitch          2 edges of length pitch per cell
            hex         2 / pitch          3 half-edges of pitch/sqrt(3) per cell
                                           -- IDENTICAL to square, which is why
                                           square is the clean control on the
                                           honeycomb measurement
            triangle    2*sqrt(3) / pitch  1.5 edges of length pitch per cell of
                                           area sqrt(3)/4 pitch^2
            mixed       2 * sqrt(lambda)   Poisson-Voronoi edge-length identity,
                                           with lambda = mixed_keep / pitch^2
        """
        if self.variant == "triangle":
            return 2.0 * math.sqrt(3.0) / self.pitch
        if self.variant == "mixed":
            return 2.0 * math.sqrt(max(self.mixed_keep, 1e-6)) / self.pitch
        return 2.0 / self.pitch

    def secondary_pitch(self) -> float:
        return self.pitch * self.nest_ratio

    def secondary_depth(self) -> float:
        return self.depth * self.nest_depth_frac

    def secondary_sink(self) -> float:
        """How far the fine lattice's tops sit BELOW the entrance plane."""
        return self.depth - self.secondary_depth()

    def secondary_shadow_deg(self) -> float:
        """Beyond this |theta| the fine lattice is behind a primary wall.

        A secondary wall top sunk by `s` inside a shaft of width `w` stops being
        visible once s * tan(theta) > w. This is the number that the bimodal
        cone did not have: its secondary tips sat in an OPEN funnel between
        cones of the same height and were never occluded at any angle
        (CONTEXT.md, "Bimodal cones -- DEAD").
        """
        s = self.secondary_sink()
        if s <= 1e-9:
            return 90.0
        return math.degrees(math.atan(self.pitch / s))

    def undercut_depth(self) -> float:
        """Depth at which the reentrant PALE cells pinch shut (mm, positive).

        Below this the surviving cavity spans what were two cells, so this is
        where the undercut starts, not where anything is lost. Walls travel
        depth*tan(lean) outward; two facing walls of neighbouring dark cells meet
        when each has covered (pitch - wall_top)/2.
        """
        t = math.tan(math.radians(max(self.lean_deg, 1e-6)))
        return (self.pitch - self.wall_top) / (2.0 * t)

    def reseal_depth(self) -> float:
        """Depth at which the reentrant cavity closes altogether (mm, positive).

        Past `undercut_depth` the converged walls keep growing into a solid post
        at each pale centre, of width 2L - pitch + wall_bot with
        L = depth*tan(lean). Posts sit 2*pitch apart, so the cavity between them
        is 3*pitch - 2L - wall_bot and vanishes at L = (3*pitch - wall_bot)/2.

        Derived, then CHECKED against the mesh: at lean 10 the formula puts the
        close at 28.5 mm and a flood fill of the sliced mesh read the dark
        cavity at 46.3 mm2 at y = -20 and 0.5 mm2 at y = -29.5.
        """
        t = math.tan(math.radians(max(self.lean_deg, 1e-6)))
        return (3.0 * self.pitch - self.wall_bot) / (2.0 * t)

    def lean_max_deg(self) -> float:
        """Largest lean whose cavity still reaches the floor. 9.51 deg at the
        defaults (pitch 3.75, depth 30, wall_bot 1.2)."""
        return math.degrees(math.atan(
            (3.0 * self.pitch - self.wall_bot) / (2.0 * self.depth)))

    def seal_frac(self) -> float:
        """Fraction of nominal depth that is actually cavity.

        1.0 for square / triangle / mixed / nested, and that is the point of the
        family: their walls are parallel, so neighbours never meet and close the
        cell off. `reentrant` is the exception -- its walls DIVERGE, which means
        they eventually run into the neighbouring cell's walls, and past
        lean_max_deg() it seals like a pillar array does. Reported honestly
        because usable_aspect() feeds on it.
        `geom3d.seal_fraction` puts a plain cone at 0.722 at ANY pitch
        (analysis_shapes.md 6.7: the criterion is pitch-independent), so a
        depth-30 cone is 21.7 mm of cavity against 30 mm here.

        NOT a design objective on its own -- analysis_shapes.md section 5 finds
        seal_frac's residual correlation FLIPS SIGN to +0.251 once usable aspect
        is held. It is the correction factor that turns a nominal depth into a
        real one, and nothing more.
        """
        if self.variant == "reentrant":
            return min(1.0, self.reseal_depth() / self.depth)
        return 1.0

    def aspect(self) -> float:
        return self.depth / self.pitch

    def usable_aspect(self) -> float:
        """seal_frac * depth / pitch -- the best predictor in the sweep so far.

        Spearman -0.876 against worst-theta score, log-log slope -1.147,
        R^2 = 0.729 over 192 designs (analysis_shapes.md section 5). For the
        nested variant the primary pitch is the one that sets the shaft, so this
        is deliberately the primary number.
        """
        return self.seal_frac() * self.depth / self.pitch

    def exposed_fraction_est(self) -> float:
        """Predicted head-on exposed fraction, BEFORE rendering.

        A prediction to be checked against the render, not a result. Under the
        old flat-rho material this number WAS the answer; FINDINGS_topo_smoke.md
        shows it is not any more (41.3x in area bought 1.30x in worst-theta
        reflectance). It is kept, and kept honest, because a wrong prediction
        recorded in advance is how that finding was obtained in the first place.

        Corner overlap is NOT subtracted: where walls meet, their end extensions
        overlap, so the true exposed area is slightly below this. The mesh sums
        those overlaps twice, so it is slightly above. The bracket is measured,
        not guessed -- mesh / estimate, from top_area_by_level():

            variant   pitch  jitter 0   jitter 0.30   (1 + wall_top/pitch)
            square     7.50    1.0533      1.0675           1.0533
            square     3.75    1.1067      1.1293           1.1067
            triangle   7.50    1.0434      1.0575           1.0533
            triangle   3.75    1.1192      1.1370           1.1067
            mixed      7.50    1.0555      1.0771           1.0533
            mixed      3.75    1.0618      1.0475           1.0467 *

        Square at jitter 0 reproduces (1 + wall_top/pitch) to four decimals in
        both columns, which is the whole corner-extension term and confirms the
        estimator is exact on the wall network itself. Jitter adds 1-2% because
        a jittered edge is longer than the nominal pitch. Triangle sits slightly
        under the factor at 7.50 because six walls meet at a vertex and overlap
        more than four do. (*) mixed's own factor uses its mean Voronoi edge,
        not pitch; the Poisson identity over-predicts wall length for a
        non-Poisson field -- for a perfect hex lattice it gives 2.149/pitch
        against the true 2/pitch, +7.4% -- and here that over-prediction largely
        cancels the corner over-count.

        So: every variant's estimate is within -1% to +14% of its own mesh, with
        the residual fully attributed. Nothing here is a fudge factor; the
        estimate is deliberately left as the clean analytic form so it stays
        comparable to geom_topo's honeycomb figure row for row.
        """
        v = self.variant
        if v in ("square", "triangle", "mixed", "reentrant"):
            # The lean does not change the reentrant mouth: only the wall FOOT
            # moves, and the top edge stays on the shared cell boundary. So
            # reentrant costs exactly what square costs head-on, and buys its
            # undercut for free on this axis.
            return self.wall_length_density() * self.wall_top
        if v == "nested":
            prim = 2.0 / self.pitch * self.wall_top
            # The fine lattice is seen through whatever the primary leaves open,
            # and it is seen HEAD-ON -- sinking it does not hide it from an
            # observer collinear with the beam. This term is the entire reason
            # the bimodal cone died, and it is written down here BEFORE the
            # render instead of being discovered by one.
            sec = 2.0 / self.secondary_pitch() * self.nest_wall_top
            return prim + (1.0 - prim) * sec
        return float("nan")


# --- shared lattice ---------------------------------------------------------

def _grid_extent(p: CellParams, dx: float, dz: float):
    """Index range of a lattice covering face + margin.

    Same arithmetic as geom_topo._centres / geom3d.centres: the field has to run
    margin_depths * depth past the window on every side or a tilted camera reads
    world background off the edge of the tile.
    """
    m = p.margin()
    nx = int((p.face_w + 2 * m) / dx) + 2
    nz = int((p.face_h + 2 * m) / dz) + 2
    ix0 = -int(m / dx) - 1
    iz0 = -int((p.face_h / 2 + m) / dz) - 1
    return ix0, nx, iz0, nz


def _vertex_field(p: CellParams, dx: float, dz: float, seed: int,
                  jitter: float, lat_pitch: float, row_offset=None):
    """Jittered lattice of shared cell CORNERS, keyed by index.

    Keyed and generated in one deterministic pass so that both cells touching an
    edge read the SAME two endpoints. That is what makes the wall network a
    tiling instead of a pile of overlapping rings, and it is what makes
    exposed_fraction_est() a claim about the mesh (see module docstring).

    `lat_pitch` is THIS lattice's spacing and jitter scales with it, not with
    p.pitch. The first version used p.pitch for every field, which for the
    nested variant's secondary lattice (pitch 0.30 * primary) meant a jitter of
    one full secondary cell: vertices crossed, cells inverted, and the secondary
    level measured 33.0% of the window against a 22.2% prediction -- a 48%
    excess that was mesh corruption, not a modelling error. Caught by printing
    predicted next to mesh-measured per level, which is why that column exists.

    `row_offset(j)` supplies the half-cell stagger of a triangular lattice.
    """
    ix0, nx, iz0, nz = _grid_extent(p, dx, dz)
    rng = _lcg(seed)
    V = {}
    for j in range(iz0, iz0 + nz + 1):
        off = 0.0 if row_offset is None else row_offset(j)
        for i in range(ix0, ix0 + nx + 1):
            x = i * dx + off + (2.0 * next(rng) - 1.0) * jitter * lat_pitch
            z = j * dz + (2.0 * next(rng) - 1.0) * jitter * lat_pitch
            V[(i, j)] = (x, z)
    return V, (ix0, nx, iz0, nz)


def _backing(verts, faces, p: CellParams, y0):
    """Slab under everything, so nothing sees daylight through the tile.

    y0 is the TOP of the slab and must sit at or above the lowest point of the
    structure, or the structure floats free -- that defect (a 0.5 mm clearance
    that left the slab touching nothing, cone mass y -34.45..0 against slab
    y -38..-35) cost an export debugging session and is recorded in CONTEXT.md.
    Here every wall foot is exactly at -depth, so the slab top is -depth.
    """
    m = p.margin()
    h = p.face_h / 2.0 + m
    b = len(verts)
    for y in (y0, y0 - p.backing):
        verts += [(-m, y, -h), (p.face_w + m, y, -h),
                  (p.face_w + m, y, h), (-m, y, h)]
    faces += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b + i, b + 4 + i, b + 4 + j, b + j))


def _wall(verts, faces, A, B, y_top, y_bot, t_top, t_bot, shift=(0.0, 0.0)):
    """One closed wall panel from in-plane point A to B.

    Thin at the mouth and thick at the floor, for the same reason geom_topo's
    shingle tapers: the top face is the ONLY thing a head-on observer sees, so
    it is the design variable, while the foot has to carry the print. `shift`
    displaces the FOOT in-plane and is how the reentrant variant leans.

    Ends are extended by half the LOCAL thickness -- t_top/2 at the mouth and
    t_bot/2 at the foot -- so corners close at both levels without the mouth
    inheriting the foot's overhang. Extending both rings by t_bot/2 (the obvious
    version, and the first one written here) made the top face pitch + t_bot
    long instead of pitch + t_top: at pitch 7.5 / wall 0.4 / foot 1.2 that read
    12.475% exposed against a 10.667% prediction, a 17% gap that was pure
    bookkeeping and would have been charged to the render. The end quad stays
    planar under the split extension -- its four corners span n and
    ((e_top - e_bot) d - depth y), which is two vectors, not three.
    """
    dx, dz = _norm2(B[0] - A[0], B[1] - A[1])
    if dx == 0.0 and dz == 0.0:
        return
    nx, nz = -dz, dx                       # in-plane wall normal
    ht, hb = 0.5 * t_top, 0.5 * t_bot
    sx, sz = shift
    atx, atz = A[0] - dx * ht, A[1] - dz * ht
    btx, btz = B[0] + dx * ht, B[1] + dz * ht
    abx, abz = A[0] - dx * hb + sx, A[1] - dz * hb + sz
    bbx, bbz = B[0] + dx * hb + sx, B[1] + dz * hb + sz
    _hexa(verts, faces,
          [(atx + nx * ht, y_top, atz + nz * ht),
           (btx + nx * ht, y_top, btz + nz * ht),
           (btx - nx * ht, y_top, btz - nz * ht),
           (atx - nx * ht, y_top, atz - nz * ht)],
          [(abx + nx * hb, y_bot, abz + nz * hb),
           (bbx + nx * hb, y_bot, bbz + nz * hb),
           (bbx - nx * hb, y_bot, bbz - nz * hb),
           (abx - nx * hb, y_bot, abz - nz * hb)])


# --- variant: square --------------------------------------------------------

def _build_square(p: CellParams):
    """Square cells. The control on whether the hex tiling mattered at all.

    Square and hex have the SAME wall length per unit area (2/pitch), so this
    holds the exposed-area term of the measured honeycomb fixed and varies only
    the cell shape -- a square cell has four walls at 90 degrees where a hex has
    three at 120, which changes the corner-reflector content of the cavity and
    nothing else. If square and honeycomb read the same, cell shape is inert and
    the family collapses to two knobs (pitch, depth), which is what
    FINDINGS_topo_smoke.md's next-step section wants to sweep anyway.
    """
    verts, faces = [], []
    V, (ix0, nx, iz0, nz) = _vertex_field(p, p.pitch, p.pitch, p.seed, p.jitter, p.pitch)
    for j in range(iz0, iz0 + nz + 1):
        for i in range(ix0, ix0 + nx + 1):
            a = V.get((i, j))
            if a is None:
                continue
            for b in (V.get((i + 1, j)), V.get((i, j + 1))):
                if b is not None:
                    _wall(verts, faces, a, b, 0.0, -p.depth,
                          p.wall_top, p.wall_bot)
    _backing(verts, faces, p, -p.depth)
    return verts, faces


# --- variant: triangle ------------------------------------------------------

def _build_triangle(p: CellParams):
    """Triangular cells: 1.73x the wall per unit area, 0.43x the cell area.

    Three edge families per vertex on a staggered lattice, so every triangle is
    closed by walls its neighbours share. At one wall pitch this is the most
    exposed variant in the family and simultaneously the one with the smallest
    cavity mouth, which under the OLD area law makes it strictly 1.73x worse
    than square. FINDINGS_topo_smoke.md says the area law does not hold, so this
    is the variant that says by how much it does not hold.
    """
    verts, faces = [], []
    dz = p.pitch * math.sqrt(3.0) / 2.0
    V, (ix0, nx, iz0, nz) = _vertex_field(
        p, p.pitch, dz, p.seed, p.jitter, p.pitch,
        row_offset=lambda j: (p.pitch * 0.5 if j % 2 else 0.0))
    for j in range(iz0, iz0 + nz + 1):
        odd = j % 2
        # The two up-going neighbours of a staggered row sit at i + {0, -1} on
        # an even row and i + {1, 0} on an odd one. Getting this wrong does not
        # crash -- it silently builds a sheared lattice with the right face
        # count, so it is checked by the exp%pred vs exp%mesh column in
        # __main__ rather than by inspection.
        for i in range(ix0, ix0 + nx + 1):
            a = V.get((i, j))
            if a is None:
                continue
            for key in ((i + 1, j),
                        (i + (1 if odd else 0), j + 1),
                        (i + (0 if odd else -1), j + 1)):
                b = V.get(key)
                if b is not None:
                    _wall(verts, faces, a, b, 0.0, -p.depth,
                          p.wall_top, p.wall_bot)
    _backing(verts, faces, p, -p.depth)
    return verts, faces


# --- variant: mixed ---------------------------------------------------------

def _clip_halfplane(poly, a, b, c):
    """Sutherland-Hodgman clip of a convex polygon to a*x + b*z <= c."""
    out = []
    n = len(poly)
    for k in range(n):
        P = poly[k]
        Q = poly[(k + 1) % n]
        dp = a * P[0] + b * P[1] - c
        dq = a * Q[0] + b * Q[1] - c
        ip, iq = dp <= 0.0, dq <= 0.0
        if ip:
            out.append(P)
        if ip != iq:
            t = dp / (dp - dq)
            out.append((P[0] + t * (Q[0] - P[0]), P[1] + t * (Q[1] - P[1])))
    return out


def _voronoi_polys(p: CellParams):
    """Voronoi cells of a jittered, randomly thinned seed field.

    Seeds are thinned, not just jittered, because jitter alone moves cells
    without changing their AREA -- and the point of this variant is a cell size
    distribution, so that there is no single cell pitch for a scanning beam to
    beat against. geom3d.py's docstring states the rule: "a scanning beam
    crossing a periodic cell array produces periodic bright spots, which is the
    one thing the whole project must avoid."

    Each cell is clipped from a 3*pitch box by the perpendicular bisectors of
    its neighbours, nearest first, stopping once the box is smaller than half
    the distance to the next neighbour. Shared edges come out of both sides as
    the same bisector segment, so a rounded-midpoint key de-duplicates them
    exactly -- unlike the jittered-centre construction, where the two sides
    disagree by up to jitter*pitch and the key can never fire.
    """
    ix0, nx, iz0, nz = _grid_extent(p, p.pitch, p.pitch)
    rng = _lcg(p.seed * 7919 + 13)
    seeds = []                       # (x, z)
    bucket = {}                      # (i, j) -> [seed index]
    for j in range(iz0, iz0 + nz + 1):
        for i in range(ix0, ix0 + nx + 1):
            u, v, w = next(rng), next(rng), next(rng)
            if w > p.mixed_keep:
                continue
            x = i * p.pitch + (2.0 * u - 1.0) * p.mixed_jitter * p.pitch
            z = j * p.pitch + (2.0 * v - 1.0) * p.mixed_jitter * p.pitch
            bucket.setdefault((i, j), []).append(len(seeds))
            seeds.append((x, z, i, j))

    R = max(1, p.mixed_ring)
    half = 3.0 * p.pitch
    polys = []
    for sx, sz, si, sj in seeds:
        cand = []
        for jj in range(sj - R, sj + R + 1):
            for ii in range(si - R, si + R + 1):
                for k in bucket.get((ii, jj), ()):
                    nx_, nz_ = seeds[k][0], seeds[k][1]
                    d2 = (nx_ - sx) ** 2 + (nz_ - sz) ** 2
                    if d2 > 1e-12:
                        cand.append((d2, nx_, nz_))
        cand.sort(key=lambda t: t[0])
        poly = [(sx - half, sz - half), (sx + half, sz - half),
                (sx + half, sz + half), (sx - half, sz + half)]
        for d2, nx_, nz_ in cand:
            # once the cell fits inside the circle of radius d/2 no further
            # bisector can touch it
            rmax2 = max((q[0] - sx) ** 2 + (q[1] - sz) ** 2 for q in poly)
            if d2 * 0.25 > rmax2:
                break
            ux, uz = nx_ - sx, nz_ - sz
            mx, mz = 0.5 * (sx + nx_), 0.5 * (sz + nz_)
            poly = _clip_halfplane(poly, ux, uz, ux * mx + uz * mz)
            if len(poly) < 3:
                break
        if len(poly) >= 3:
            polys.append(poly)
    return polys, len(seeds)


def _build_mixed(p: CellParams):
    """Irregular Voronoi cell walls -- no periodic cell pitch anywhere."""
    verts, faces = [], []
    polys, _ = _voronoi_polys(p)
    seen = set()
    minlen = 0.75 * p.wall_bot      # shorter than its own corner extensions:
                                    # the wall would be pure overlap
    for poly in polys:
        n = len(poly)
        for k in range(n):
            A, B = poly[k], poly[(k + 1) % n]
            if math.hypot(B[0] - A[0], B[1] - A[1]) < minlen:
                continue
            key = (round((A[0] + B[0]) * 100), round((A[1] + B[1]) * 100))
            if key in seen:          # every Voronoi edge is shared by two cells
                continue
            seen.add(key)
            _wall(verts, faces, A, B, 0.0, -p.depth, p.wall_top, p.wall_bot)
    _backing(verts, faces, p, -p.depth)
    return verts, faces


# --- variant: reentrant -----------------------------------------------------

def _build_reentrant(p: CellParams):
    """Undercut cells: wider at the floor than at the mouth.

    A ray that enters through a mouth of area A and finds itself in a cavity of
    cross-section > A has to come back through the smaller opening to leave.

    WHY HALF THE CELLS ARE SACRIFICED -- this is a constraint, not a choice.
    In any shared-wall tiling the plan area is (sum of cell areas) + (wall
    length x wall thickness). Wall length is fixed by the lattice, so if EVERY
    cell grows with depth the walls must get thinner with depth, and the total
    available undercut is bounded by (wall_top - wall_bot)/2 -- about 0.4 mm,
    which at depth 30 is a lean of 0.8 degrees. Useless.

    So the cells are 2-coloured on a square lattice (its dual is bipartite; a
    hex tiling's dual is triangular and is NOT 2-colourable, which is why this
    variant is square and not hex). Every wall borders exactly one dark cell and
    one pale one, and every wall leans away from its dark cell's centre. The
    dark cells open out with depth; the pale ones close, their four walls
    converging into a solid post at `undercut_depth()`. Below that the cavity is
    a connected undercut chamber spanning what were two cells.

    AND THE LEAN IS BOUNDED, which was not obvious and was not assumed. Those
    posts keep growing, and at `reseal_depth()` they fill the chamber and the
    cavity closes -- a reentrant cell seals exactly the way a pillar array does,
    just later. `lean_max_deg()` is 9.51 degrees at pitch 3.75 / depth 30 /
    wall_bot 1.2. Measured on the built mesh by slicing every hexahedron at a
    height and flood-filling the open raster, dark-cell cavity area in mm2:

        lean       y=0    y=-4    y=-8   y=-12   y=-20  y=-29.5
        0 (square) 12.5    11.7    11.0    10.2     8.8      7.4
        10         12.5   302.6   331.5   317.2    46.3      0.5
        20         12.5   358.5   272.0   188.6    73.5      0.0

    Lean 10 is a 24x undercut by y = -4 and then a SEALED cell by y = -29.5,
    against a formula that put the reseal at -28.5. So the default is 6.0, and
    the same slice at 6.0 confirms it holds all the way down:

        lean 6     y=0    y=-4   y=-10   y=-16   y=-24  y=-29.9
                   12.5    16.3   300.4   287.2   146.2     10.0

    -- a 24x undercut mid-cavity and still 10.0 mm2 open at the floor, against
    the plain square cell's 7.3.

    Head-on this costs NOTHING relative to plain square: the wall TOP edges are
    still on the shared cell boundary and only the feet move, so
    exposed_fraction_est is identical (2 * wall_top / pitch). Note also from the
    table that a plain square cell LOSES cross-section with depth (12.5 -> 7.4),
    because wall_bot > wall_top; the reentrant is the only variant here whose
    cavity grows.

    PRINTABILITY: this is the non-self-supporting direction for FDM printed face
    up -- the wall overhangs the cavity by `lean` from vertical, and at 6
    degrees each 0.2 mm layer steps 21 microns outward over air. geom3d's
    `profile_lip` has the same problem and its docstring makes the same call:
    exploration is not manufacturing. Note also that lip 0.35 measured
    STRICTLY harmful for cones -- worse at every one of 96 matched pairs
    (analysis_shapes.md section 4). That result is about an overhang on a
    PILLAR flank, whose cavity seals anyway; whether it transfers to a
    non-sealing cell is exactly what this variant asks. [추측] that it does not.
    """
    verts, faces = [], []
    V, (ix0, nx, iz0, nz) = _vertex_field(p, p.pitch, p.pitch, p.seed, p.jitter, p.pitch)
    lean = p.depth * math.tan(math.radians(p.lean_deg))
    for j in range(iz0, iz0 + nz):
        for i in range(ix0, ix0 + nx):
            if (i + j) % 2:                       # only the dark cells own walls
                continue
            c = [V.get((i, j)), V.get((i + 1, j)),
                 V.get((i + 1, j + 1)), V.get((i, j + 1))]
            if any(q is None for q in c):
                continue
            cx = sum(q[0] for q in c) * 0.25
            cz = sum(q[1] for q in c) * 0.25
            for k in range(4):
                A, B = c[k], c[(k + 1) % 4]
                mx, mz = 0.5 * (A[0] + B[0]), 0.5 * (A[1] + B[1])
                ox, oz = _norm2(mx - cx, mz - cz)   # outward from this cell
                _wall(verts, faces, A, B, 0.0, -p.depth,
                      p.wall_top, p.wall_bot,
                      shift=(ox * lean, oz * lean))
    _backing(verts, faces, p, -p.depth)
    return verts, faces


# --- variant: nested --------------------------------------------------------

def _build_nested(p: CellParams):
    """A coarse cell lattice whose floor carries a finer one.

    HOW THIS DIFFERS FROM THE BIMODAL CONE, WHICH IS DEAD
    CONTEXT.md records it: a finer, shorter cone array dropped into the valleys
    between the primary cones. The all-angle figure was identical to four
    decimals (0.2132%) in every variant, so the secondary contributed nothing at
    grazing, while its tips were fully exposed and cost 2x head-on
    (0.0083 -> 0.0164). Shrinking just the secondary tips to 0.1 mm returned the
    head-on figure to baseline, "proving the entire effect was added tip area
    and nothing else."

    Three differences, all stated before any render of this module exists:

    1. OCCLUSION EXISTS HERE AND DID NOT EXIST THERE. The bimodal secondary sat
       in an open funnel between primary cones that sloped away from it, so no
       primary feature was ever between it and the camera at any theta. Here the
       fine lattice sits `secondary_sink()` mm down a shaft whose walls are
       vertical and full height, so it is occluded for all
       |theta| > secondary_shadow_deg() -- 10.9 degrees at the defaults, 21.0 at
       pitch 7.5, 29.4 at pitch 11. What it
       cannot escape is theta = 0, where observer and beam are collinear and the
       shaft is looked straight down; geom_topo's docstring is explicit that a
       single bounce cannot displace a photon at normal incidence.

    2. THE COST IS PREDICTED, NOT DISCOVERED. exposed_fraction_est() carries the
       secondary term explicitly, weighted by the primary's open fraction. The
       bimodal design had no such term and found the 2x by rendering.

    3. THE SECONDARY IS A WALL EDGE, NOT A TIP. It is thinner than the primary
       wall (nest_wall_top < wall_top) for the same reason the bimodal fix was
       to shrink the tip, and the knob is exposed rather than fixed.

    Honest arithmetic at the defaults (primary pitch 3.75, ratio 0.30): the
    secondary term alone is 2 * 0.25 / 1.125 = 44%, which swamps the primary's
    21%. This variant is only sane with a COARSE primary -- at pitch 11 the
    primary is 7.3% and the secondary 15.2%, for 21.3% total, the same as plain
    square at 3.75 but with a hierarchy inside it. The estimator says so before
    anything is rendered; that is what it is for.
    """
    verts, faces = [], []
    V, (ix0, nx, iz0, nz) = _vertex_field(p, p.pitch, p.pitch, p.seed, p.jitter, p.pitch)
    for j in range(iz0, iz0 + nz + 1):
        for i in range(ix0, ix0 + nx + 1):
            a = V.get((i, j))
            if a is None:
                continue
            for b in (V.get((i + 1, j)), V.get((i, j + 1))):
                if b is not None:
                    _wall(verts, faces, a, b, 0.0, -p.depth,
                          p.wall_top, p.wall_bot)

    sp = p.secondary_pitch()
    y_top = -p.secondary_sink()
    # different seed, so the fine lattice is not in phase with the coarse one --
    # an in-phase secondary would stack its walls under the primary walls, where
    # they are already shadowed and buy nothing
    V2, (jx0, mx_, jz0, mz_) = _vertex_field(p, sp, sp, p.seed * 101 + 7,
                                             p.jitter, sp)
    for j in range(jz0, jz0 + mz_ + 1):
        for i in range(jx0, jx0 + mx_ + 1):
            a = V2.get((i, j))
            if a is None:
                continue
            for b in (V2.get((i + 1, j)), V2.get((i, j + 1))):
                if b is not None:
                    _wall(verts, faces, a, b, y_top, -p.depth,
                          p.nest_wall_top, p.nest_wall_bot)
    _backing(verts, faces, p, -p.depth)
    import geom_kit as _GK
    verts, faces = _GK.orient_outward(verts, faces)
    return verts, faces


# --- entry point ------------------------------------------------------------

_BUILDERS = {"square": _build_square,
             "triangle": _build_triangle,
             "mixed": _build_mixed,
             "reentrant": _build_reentrant,
             "nested": _build_nested}


def build_mesh(p: CellParams):
    """Return (verts, faces) for the whole tile: closed wall solids plus slab.

    Walls interpenetrate at corners; for an opaque surface the union is the
    geometry, so no boolean is required (geom3d.build_mesh, same contract).
    """
    try:
        fn = _BUILDERS[p.variant]
    except KeyError:
        raise ValueError("unknown variant %r; have %s"
                         % (p.variant, sorted(_BUILDERS)))
    verts, faces = fn(p)
    # every variant through one oriented exit; see geom_kit.orient_outward
    import geom_kit as _GK
    return _GK.orient_outward(verts, faces)


def cell_count(p: CellParams) -> int:
    """Number of cells in the whole field, margin included."""
    if p.variant == "triangle":
        dz = p.pitch * math.sqrt(3.0) / 2.0
        _, nx, _, nz = _grid_extent(p, p.pitch, dz)
        return 2 * nx * nz
    if p.variant == "mixed":
        return _voronoi_polys(p)[1]
    _, nx, _, nz = _grid_extent(p, p.pitch, p.pitch)
    if p.variant == "reentrant":
        return (nx * nz + 1) // 2       # only the dark half is a cavity cell
    return nx * nz


def top_area_by_level(p: CellParams, verts, faces) -> list[tuple[float, float]]:
    """Upward-facing horizontal area per Y level, as a fraction of the window.

    Returns [(y, fraction), ...] deepest last. Every horizontal quad above the
    floor plane, projected into X-Z, over face_w * face_h, keyed by its Y.

    Per LEVEL, not summed, because summing is wrong the moment there are two
    levels: the nested variant's fine lattice runs under the coarse walls as
    well as between them, so a naive sum double-counts and read 113.9% of the
    window on the first run of this file. A number over 100% is not a
    measurement, it is a missing occlusion term.

    Within one level this counts corner overlaps twice, so it is an upper bound
    on that level's exposed area; exposed_fraction_est() ignores corners, so it
    is a lower bound. The two bracket the truth, and the gap is predictable:
    every wall's top face is pitch + wall_top long instead of pitch, so the
    bracket is (1 + wall_top/pitch) wide before jitter, a bit more after it.

    Quads are CLIPPED to the window, not selected by centroid. Selecting by
    centroid counted the walls lying on x = 0 and x = face_w whole, which at
    pitch 7.5 into a 60 mm face is 9 wall lines charged where 8 belong: it
    inflated the unjittered square from the correct 1.053 ratio to 1.185, and
    jitter hid it by smearing the boundary. An artifact that only shows up when
    the lattice is regular is exactly the kind this project keeps finding late.
    """
    y_floor = -p.depth + 1e-6
    W0, W1 = 0.0, p.face_w
    H0, H1 = -p.face_h / 2.0, p.face_h / 2.0
    lev: dict[int, float] = {}
    for f in faces:
        ys = [verts[k][1] for k in f]
        if max(ys) - min(ys) > 1e-9 or ys[0] <= y_floor:
            continue
        pts = [(verts[k][0], verts[k][2]) for k in f]
        xs = [q[0] for q in pts]
        zs = [q[1] for q in pts]
        if max(xs) <= W0 or min(xs) >= W1 or max(zs) <= H0 or min(zs) >= H1:
            continue
        if not (min(xs) >= W0 and max(xs) <= W1
                and min(zs) >= H0 and max(zs) <= H1):
            for a, b, c in ((-1.0, 0.0, -W0), (1.0, 0.0, W1),
                            (0.0, -1.0, -H0), (0.0, 1.0, H1)):
                pts = _clip_halfplane(pts, a, b, c)
                if len(pts) < 3:
                    break
            if len(pts) < 3:
                continue
        a = 0.0
        for k in range(len(pts)):
            m = (k + 1) % len(pts)
            a += pts[k][0] * pts[m][1] - pts[m][0] * pts[k][1]
        lev[round(ys[0] * 1e4)] = lev.get(round(ys[0] * 1e4), 0.0) \
            + abs(a) * 0.5
    A = p.face_w * p.face_h
    return sorted(((k * 1e-4, v / A) for k, v in lev.items()),
                  key=lambda t: -t[0])


def measured_exposed_fraction(p: CellParams, verts, faces) -> float:
    """Head-on exposed fraction read off the mesh, levels combined top-down.

    Each level below the first is seen only through what the levels above leave
    open, which is the same independence assumption exposed_fraction_est() makes
    for `nested`. Stated so that the two numbers are comparable term for term;
    for every single-level variant it reduces to that level's raw fraction.
    """
    open_f = 1.0
    tot = 0.0
    for _, frac in top_area_by_level(p, verts, faces):
        f = min(1.0, frac)
        tot += open_f * f
        open_f *= (1.0 - f)
    return tot


def open_edge_count(verts, faces) -> tuple[int, int]:
    """(open edges, non-manifold edges) for the whole mesh.

    Every solid here is a closed hexahedron, so every undirected edge must be
    used by exactly two faces, and every DIRECTED edge exactly once -- that is
    the same watertightness test the cone export was held to (CONTEXT.md: "0
    open edges, 0 non-manifold", in several shells). Interpenetration between
    separate solids does not affect it; a twisted or dropped quad does.

    Memory-hungry (one dict entry per directed edge), so __main__ runs it on a
    small coupon rather than on the 450 x 450 measurement field.
    """
    use: dict[tuple[int, int], int] = {}
    for f in faces:
        n = len(f)
        for k in range(n):
            a, b = f[k], f[(k + 1) % n]
            key = (a, b) if a < b else (b, a)
            use[key] = use.get(key, 0) + 1
    open_e = sum(1 for c in use.values() if c == 1)
    nonman = sum(1 for c in use.values() if c > 2)
    return open_e, nonman


def describe(p: CellParams) -> dict:
    return {"family": "cell",
            "variant": p.variant,
            "depth_mm": p.depth,
            "pitch_mm": p.pitch,
            "pitch_mean_mm": p.pitch,
            "aspect": p.aspect(),
            "seal_frac": p.seal_frac(),
            "usable_aspect": p.usable_aspect(),
            "jitter": p.jitter,
            "cell_area_mm2": p.cell_area(),
            "wall_length_density_per_mm": p.wall_length_density(),
            "exposed_fraction_est": p.exposed_fraction_est(),
            "margin_depths": p.margin_depths,
            "wall_top_mm": p.wall_top,
            "wall_bot_mm": p.wall_bot,
            "lean_deg": p.lean_deg if p.variant == "reentrant" else 0.0,
            "lean_max_deg": p.lean_max_deg(),
            "undercut_depth_mm": p.undercut_depth(),
            "reseal_depth_mm": p.reseal_depth(),
            "mixed_keep": p.mixed_keep,
            "mixed_jitter": p.mixed_jitter,
            "nest_ratio": p.nest_ratio,
            "nest_depth_frac": p.nest_depth_frac,
            "nest_wall_top_mm": p.nest_wall_top,
            "nest_wall_bot_mm": p.nest_wall_bot,
            "secondary_pitch_mm": p.secondary_pitch(),
            "secondary_sink_mm": p.secondary_sink(),
            "secondary_shadow_deg": p.secondary_shadow_deg()}


if __name__ == "__main__":
    import time

    VARIANTS = ("square", "triangle", "mixed", "reentrant", "nested")

    print("field at margin_depths 6.5, depth 30, face 60 -> %.0f x %.0f mm"
          % (60.0 + 2 * 6.5 * 30.0, 60.0 + 2 * 6.5 * 30.0))
    print()
    # geom_topo's truss reached 2.15 M faces and had to be CUT (strut_seg 4 not
    # 6, links 2 not 3), so 2.15 M is a known-unaffordable number, not a target.
    # Flag at half of it and refuse at 1 M.
    HEAVY = 1_000_000
    WARN = 350_000

    print("%-10s %6s %9s %9s %8s %8s %8s %7s %6s %6s %5s  %s"
          % ("variant", "pitch", "verts", "faces", "cells",
             "exp%pred", "exp%mesh", "uaspect", "ymin", "ymax", "s", "weight"))
    for pitch in (7.5, 3.75):
        for var in VARIANTS:
            prm = CellParams(variant=var, pitch=pitch, depth=30.0,
                             face_w=60.0, face_h=60.0)
            t0 = time.time()
            v, f = build_mesh(prm)
            dt = time.time() - t0
            ys = [q[1] for q in v]
            # Nothing may rise above the entrance plane. A geom_topo truss bug
            # of exactly this kind (a node on Y = 0 putting half a strut above
            # it) was caught by checking max(y).
            assert max(ys) <= 1e-9, "%s: max(Y) = %r > 0" % (var, max(ys))
            tag = ("TOO HEAVY" if len(f) >= HEAVY
                   else "heavy" if len(f) >= WARN else "ok")
            print("%-10s %6.2f %9d %9d %8d %8.3f %8.3f %7.2f %6.1f %6.1f %5.1f  %s"
                  % (var, pitch, len(v), len(f), cell_count(prm),
                     100.0 * prm.exposed_fraction_est(),
                     100.0 * measured_exposed_fraction(prm, v, f),
                     prm.usable_aspect(), min(ys), max(ys), dt, tag))
        print()

    print("all variants: max(Y) <= 0 asserted OK")
    print()

    # Watertightness of the primitive, on a small coupon so the edge dictionary
    # fits: the measurement field is 450 x 450 mm and would need ~8.5 M entries.
    print("closure check, coupon face 20 mm / margin_depths 0.5:")
    for var in VARIANTS:
        pc = CellParams(variant=var, pitch=3.75, depth=30.0,
                        face_w=20.0, face_h=20.0, margin_depths=0.5)
        vc, fc = build_mesh(pc)
        oe, nm = open_edge_count(vc, fc)
        assert oe == 0 and nm == 0, "%s: %d open, %d non-manifold" % (var, oe, nm)
        print("  %-10s faces %7d   open edges %d   non-manifold edges %d"
              % (var, len(fc), oe, nm))
    print()

    # nested is the only two-level variant, so it is the only one whose
    # prediction has two terms. Check them separately.
    for pitch in (7.5, 3.75, 11.0):
        pn = CellParams(variant="nested", pitch=pitch, depth=30.0)
        vn, fn = build_mesh(pn)
        levels = top_area_by_level(pn, vn, fn)
        prim = 2.0 / pn.pitch * pn.wall_top
        sec = 2.0 / pn.secondary_pitch() * pn.nest_wall_top
        print("nested p%.2f  levels(mesh) %s   pred primary %.3f%% "
              "secondary %.3f%%"
              % (pitch, "  ".join("y=%.1f %.3f%%" % (y, 100.0 * fr)
                                  for y, fr in levels),
                 100.0 * prim, 100.0 * sec))
    print()
    p11 = CellParams(variant="nested", pitch=11.0, depth=30.0)
    print("nested with a COARSE primary (pitch 11): exposed est %.3f%%, "
          "secondary pitch %.2f mm, sunk %.1f mm, shadowed beyond %.1f deg"
          % (100.0 * p11.exposed_fraction_est(), p11.secondary_pitch(),
             p11.secondary_sink(), p11.secondary_shadow_deg()))
    print()
    print("reentrant lean sweep at pitch 3.75 / depth 30 (max lean %.2f deg):"
          % CellParams(variant="reentrant", pitch=3.75, depth=30.0
                       ).lean_max_deg())
    for lean in (4.0, 6.0, 8.0, 9.5, 10.0, 20.0):
        pr = CellParams(variant="reentrant", pitch=3.75, depth=30.0,
                        lean_deg=lean)
        print("  lean %4.1f  foot +%5.2f mm  undercut from %5.1f mm  "
              "reseals at %6.1f mm  seal_frac %.3f  usable_aspect %.2f%s"
              % (lean, pr.depth * math.tan(math.radians(lean)),
                 pr.undercut_depth(), pr.reseal_depth(), pr.seal_frac(),
                 pr.usable_aspect(),
                 "   <-- SEALS INSIDE THE DEPTH" if pr.seal_frac() < 1.0
                 else ""))
