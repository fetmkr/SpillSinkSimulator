"""
Sixth geometry family: topologies that are neither an extruded V-groove nor a
pillar/cone array.

Why a new family at all
-----------------------
Within +/-40 degrees the cone array is already very good -- peak radiance ratio
0.0002 at -40 (metrics/04). What it cannot do is theta = 0, where it reads
0.0103 to 0.0451 and every family ever tried reads core 1.000. metrics/02 calls
that "the unsolved axis" and the reason is not a defect: at normal incidence the
observer and the beam are collinear, so whatever the beam strikes FIRST is
visible, and a single bounce cannot displace a photon.

Two levers exist at theta = 0, and only two:

    (a) shrink the exposed area              -- already at its limit
    (b) aim the first bounce somewhere else  -- untouched

(a) is exhausted. A point array exposes pi r^2 per cell against a wall network's
t * perimeter; at pitch 7.5 with a 0.4 mm nozzle feature that is 0.26% against
10.7%, a factor of 40 in the pillar's favour. Nothing beats points on area, so
any "more clever" wall/honeycomb topology LOSES this axis by construction. That
is worth measuring once as a negative control and then not revisiting.

(b) is where this module lives. What the observer receives at theta = 0 is set
by the exposed surface's NORMAL distribution, not its area. A rounded cone tip
has a locally horizontal cap whose normal points straight back at the observer.
A structure whose topmost visible surfaces are all steeply inclined, or which
hides its first-hit surface inside a cavity mouth, has no such normal.

Three topologies, in decreasing order of how much is riding on them
-------------------------------------------------------------------
    shingle    inclined plates that overlap like roof tiles, each leaning in a
               jittered azimuth so the array is isotropic. At normal incidence
               the observer looks past the leading edge INTO the pocket behind
               it; the only surfaces facing out are the plate edges. This is
               Rosalia alpina's "tent-shaped scales, inclined, touching
               neighbours at the tips" (reference/SUMMARY.md 3.5), flagged there
               as "a distinct topology from anything we have built".

    truss      a sparse 3D lattice of struts between jittered node layers. High
               surface area, low volume fraction, and no preferred direction --
               the "sparse material with high surface area" principle that Davis
               2020 states, and the only hierarchical idea in the folder whose
               mechanism is ray-optical rather than sub-wavelength.

    honeycomb  deep cell walls. Included as the NEGATIVE CONTROL for the area
               argument above: it should lose head-on by roughly the predicted
               40x, and if it does not then the exposed-area law is wrong and
               that matters more than any design.

Conventions, matched to geom3d.py exactly
-----------------------------------------
X across the face (0 .. face_w), Y depth with the entrance plane at Y = 0 and
deeper NEGATIVE, Z vertical (-face_h/2 .. +face_h/2). Solids interpenetrate and
the union is the geometry -- for an opaque surface no boolean is needed. A
backing slab closes the bottom. Geometry runs margin_depths * depth past the
window on every side, because a camera tilted to theta travels D/tan(90-theta)
in Z before it reaches the floor and without that margin the view runs off the
tile and reads world background (this produced an impossible 27% "reflectance"
once; see CONTEXT.md 5b).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from profile2d import _lcg


# --- small vector helpers ---------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(v):
    L = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / L, v[1] / L, v[2] / L) if L > 1e-12 else (0.0, 0.0, 0.0)


# --- primitive solids -------------------------------------------------------

def _hexa(verts, faces, top4, bot4):
    """One closed hexahedron from 4 top corners and 4 bottom corners.

    Corners must be given in the same rotational order for both rings, or the
    side quads come out twisted. Winding is consistent within the solid; Cycles
    renders both sides of a face, so an inverted normal costs nothing here, but
    a twisted quad is a real self-intersection and would.
    """
    b = len(verts)
    verts.extend(top4)
    verts.extend(bot4)
    faces.append((b, b + 1, b + 2, b + 3))                  # top
    faces.append((b + 7, b + 6, b + 5, b + 4))              # bottom
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b + i, b + 4 + i, b + 4 + j, b + j))  # sides


def _strut(verts, faces, p0, p1, r, n=6):
    """One closed n-gon prism from p0 to p1, radius r. Capped at both ends."""
    ax = _sub(p1, p0)
    L = math.sqrt(ax[0] ** 2 + ax[1] ** 2 + ax[2] ** 2)
    if L < 1e-9:
        return
    ax = _mul(ax, 1.0 / L)
    ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm(_cross(ax, ref))
    v = _norm(_cross(ax, u))
    b = len(verts)
    for P in (p0, p1):
        for i in range(n):
            a = 2.0 * math.pi * i / n
            verts.append(_add(P, _add(_mul(u, r * math.cos(a)),
                                      _mul(v, r * math.sin(a)))))
    c0 = len(verts); verts.append(p0)
    c1 = len(verts); verts.append(p1)
    for i in range(n):
        j = (i + 1) % n
        faces.append((b + i, b + n + i, b + n + j, b + j))
        faces.append((c0, b + j, b + i))
        faces.append((c1, b + n + i, b + n + j))


# --- parameters -------------------------------------------------------------

@dataclass
class TopoParams:
    topology: str = "shingle"      # shingle | truss | honeycomb

    # --- envelope (mm), same meaning as Cone3DParams ---
    face_w: float = 60.0
    face_h: float = 60.0
    depth: float = 30.0
    backing: float = 2.0

    # --- lattice ---
    pitch: float = 7.5
    jitter: float = 0.30
    seed: int = 23
    margin_depths: float = 6.5
    centre_margin_pitches: float = 1.0

    # --- shingle: inclined overlapping plates ---
    # tilt is measured from the panel NORMAL. 0 would lay the plate flat across
    # the mouth (and block everything); 90 would stand it straight down the hole
    # (and expose only its edge, but form no pocket). The interesting range is
    # 45-75, where the plate both covers its neighbour's mouth and leaves a slot.
    tilt_deg: float = 60.0
    tilt_jitter: float = 10.0
    azimuth_jitter: float = 180.0  # full randomisation kills array anisotropy
    # random | grid | parallel. See _build_shingle -- this is a FABRICATION
    # choice, not a tuning knob: only "grid" can be slotted together without a
    # base plate.
    azimuth_mode: str = "random"
    # The plate is a KNIFE EDGE at the entrance plane and thickens toward the
    # floor. The first version made it a constant-thickness slab hanging from a
    # top edge that lay in the entrance plane, which put a horizontal rectangle
    # of plate_t x width per cell facing straight at a head-on observer -- 15.2%
    # exposed against the cone's 0.26%, i.e. it handed back the entire area
    # advantage before measuring anything. Tapering also happens to be the
    # self-supporting direction for FDM, but that is a side effect, not why.
    plate_t_top: float = 0.05      # ~0: the exposed edge at theta = 0
    plate_t_bot: float = 0.9       # structural thickness at the floor
    plate_over: float = 1.45       # plate width / pitch. >1 makes tiles overlap
    plate_len: float = 1.0         # plate length as a fraction of depth/cos(tilt)

    # --- truss: sparse strut lattice ---
    # strut_seg 4 and links 2, not 6 and 3: at margin_depths 6.5 and depth 30
    # the field is 450 x 450 mm, which is 4402 cells at pitch 7.5, and a 6-gon
    # strut with 3 links per node came to 2.15 M faces. A square strut with 2
    # links is 1/4 of that for the same volume fraction and surface area.
    layers: int = 5                # node layers between entrance and floor
    strut_r: float = 0.35
    strut_seg: int = 4
    links: int = 2                 # struts down from each node
    layer_jitter: float = 0.40     # in-plane jitter per layer, x pitch
    link_reach: float = 1.6        # max horizontal reach, x pitch

    # --- honeycomb: deep cell walls on a Voronoi tessellation ---
    wall_top: float = 0.4
    wall_bot: float = 1.2
    # Cell lean and twist. Both leave the cell's cross-section unchanged at
    # every depth, so the cavity stays full-depth and narrow -- which is what
    # holds up under a DIFFUSE coating -- while making every wall inclined,
    # which is what redirects a bounce under a SPECULAR one. The two material
    # extremes want different things and these two knobs are an attempt to
    # serve both in one structure:
    #
    #   shingle   inclined plates. Beats the cone 4.8x at theta=0 under d00
    #             (0.00040 vs 0.00193) and LOSES under d100, where there is no
    #             redirection to be had and it simply leaks.
    #   honeycomb narrow full-depth cells. Never seals, unlike a pillar array
    #             that stops being a cavity at 72% of nominal depth.
    #
    # lean tilts the whole cell like a leaning prism; twist rotates the floor
    # polygon about the cell centre so no wall is planar and no straight path
    # runs from mouth to floor. Jittered per cell, or the array is periodic.
    cell_lean_deg: float = 0.0
    cell_lean_jitter: float = 0.0    # +/- fraction of the lean AMPLITUDE
    # How many pitches the lean-direction field takes to turn over. Small
    # values rearrange the cell adjacency between mouth and floor and walls get
    # dropped; the builder prints the count, and a run that drops walls is not
    # a design, it is a broken mesh.
    cell_lean_domain: float = 8.0
    # --- comb: the commercial expanded product ---
    # expanded pitch across the ribbon / bonded pitch along it. 1.0 = regular
    comb_expand: float = 1.0

    # ---- derived ----------------------------------------------------------

    def cell_area(self) -> float:
        return math.sqrt(3.0) / 2.0 * self.pitch ** 2

    def aspect(self) -> float:
        return self.depth / self.pitch

    def margin(self) -> float:
        return max(self.margin_depths * self.depth,
                   self.centre_margin_pitches * self.pitch)

    def exposed_fraction_est(self) -> float:
        """Predicted head-on exposed fraction, BEFORE rendering.

        This is a prediction to be checked against the measurement, not a
        result. The whole point of the honeycomb control is that this number
        says it should lose by ~40x; if the render disagrees, the law is wrong.
        """
        if self.topology == "comb":
            # four single walls and two double ones per cell, shared
            return (3.0 * (self.pitch / math.sqrt(3.0)) * self.wall_top
                    * (4.0 / 6.0 + 2.0 * 2.0 / 6.0)) / self.cell_area()
        if self.topology == "honeycomb":
            # three shared hex edges per cell, each of length pitch/sqrt(3)
            return 3.0 * (self.pitch / math.sqrt(3.0)) * self.wall_top \
                / self.cell_area()
        if self.topology == "shingle":
            # one plate KNIFE EDGE per cell: width x top thickness
            return self.plate_over * self.pitch * self.plate_t_top \
                / self.cell_area()
        if self.topology == "truss":
            # the top layer's strut ends, seen end-on
            return math.pi * self.strut_r ** 2 * self.links / self.cell_area()
        return float("nan")


# --- shared lattice ---------------------------------------------------------

def _centres(p: TopoParams, pitch=None, seed=None):
    """Jittered hex lattice of cell centres in (x, z), covering face + margin."""
    pitch = p.pitch if pitch is None else pitch
    rng = _lcg(p.seed if seed is None else seed)
    dx = pitch
    dz = pitch * math.sqrt(3.0) / 2.0
    m = p.margin()
    nx = int((p.face_w + 2 * m) / dx) + 2
    nz = int((p.face_h + 2 * m) / dz) + 2
    ix0 = -int(m / dx) - 1
    iz0 = -int((p.face_h / 2 + m) / dz) - 1
    out = []
    for iz in range(iz0, iz0 + nz):
        for ix in range(ix0, ix0 + nx):
            x = ix * dx + (dx * 0.5 if iz % 2 else 0.0)
            z = iz * dz
            x += (2.0 * next(rng) - 1.0) * p.jitter * pitch
            z += (2.0 * next(rng) - 1.0) * p.jitter * pitch
            out.append((x, z))
    return out


def _backing(verts, faces, p: TopoParams, y0):
    """Slab under everything, so nothing sees daylight through the tile.

    y0 is the TOP of the slab and must sit at or above the lowest point of the
    structure, or the structure floats free -- that defect (a 0.5 mm clearance
    that left the slab touching nothing) cost a whole export debugging session
    and is recorded in CONTEXT.md.
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


# --- topology: shingle ------------------------------------------------------

def _build_shingle(p: TopoParams):
    """Overlapping inclined plates, each leaning in its own azimuth.

    Each plate hangs from a top edge lying in the entrance plane and leans away
    from vertical by `tilt` toward its own azimuth. Neighbours overlap
    (plate_over > 1), so a plate's body covers the mouth its neighbour left
    open, and the pocket between them is reachable only through a slot. At
    theta = 0 the only outward-facing surface is the top edge -- an area
    plate_t x width, which is why plate_t is the head-on design variable here
    the way tip radius was for the cone.
    """
    verts, faces = [], []
    rng = _lcg(p.seed * 31 + 7)
    half = 0.5 * p.plate_over * p.pitch
    for cx, cz in _centres(p):
        # azimuth_mode decides how a blade is oriented in plan, and it decides
        # the FABRICATION. Random orientations are set by the slot angles in the
        # base plate -- a drawing change, no extra cost. "grid" restricts every
        # blade to 0 or 90 degrees, which is the only case that can be built by
        # slotting two sets of strips together (egg-crate) with no separate base
        # plate and no welding. Measured: random beats all-parallel by 31%, and
        # whether grid recovers that is the question this parameter exists for.
        if p.azimuth_mode == "grid":
            az = (math.pi / 2.0) if next(rng) < 0.5 else 0.0
        elif p.azimuth_mode == "parallel":
            az = 0.0
        else:
            az = math.radians((2.0 * next(rng) - 1.0) * p.azimuth_jitter)
        # Floor was 5 degrees and it silently ate an entire experiment: tilt
        # 1, 2 and 3 all clamped to 5 and returned results identical to five
        # decimal places, which read as "the optimum is a plateau below 5" when
        # it was three copies of the same geometry. Tilt 0 is a vertical fin
        # and is perfectly well defined here -- axis becomes (0,-1,0) and the
        # plate length is exactly `depth` -- so the floor is 0.
        tl = math.radians(max(0.0, min(85.0,
                              p.tilt_deg + (2.0 * next(rng) - 1.0)
                              * p.tilt_jitter)))
        # top edge direction, in the entrance plane
        e = (math.cos(az), 0.0, math.sin(az))
        # lean direction: perpendicular to the edge, in-plane component only
        lean = (-math.sin(az), 0.0, math.cos(az))
        # plate runs down by L*cos(tilt) and sideways by L*sin(tilt); tilt is
        # measured from the panel normal, so 0 is a vertical fin and 85 is
        # almost flat across the mouth. Length is capped so the plate reaches
        # the floor and no further -- a plate hanging past the backing slab
        # would poke through it.
        L = p.plate_len * p.depth / max(math.cos(tl), 0.15)
        L = min(L, p.depth / max(math.cos(tl), 0.15))
        axis = _norm(_add(_mul(lean, math.sin(tl)), (0.0, -math.cos(tl), 0.0)))
        nrm = _norm(_cross(axis, e))
        A = (cx - half * e[0], 0.0, cz - half * e[2])
        B = (cx + half * e[0], 0.0, cz + half * e[2])
        A2 = _add(A, _mul(axis, L))
        B2 = _add(B, _mul(axis, L))
        tt = _mul(nrm, 0.5 * p.plate_t_top)
        tb = _mul(nrm, 0.5 * p.plate_t_bot)
        # sink by the top half-thickness's Y component so nothing rises above
        # the entrance plane: the camera, the measurement windows and the
        # "apex plane at Y = 0" convention all assume Y <= 0 everywhere.
        dy = (0.0, -abs(tt[1]), 0.0)
        A, B = _add(A, dy), _add(B, dy)
        A2, B2 = _add(A2, dy), _add(B2, dy)
        _hexa(verts, faces,
              [_add(A, tt), _add(B, tt), _sub(B, tt), _sub(A, tt)],
              [_add(A2, tb), _add(B2, tb), _sub(B2, tb), _sub(A2, tb)])
    _backing(verts, faces, p, -p.depth)
    return verts, faces


# --- topology: truss --------------------------------------------------------

def _build_truss(p: TopoParams):
    """Sparse strut lattice between jittered node layers.

    Every strut is a closed prism; the union is a connected tangle with a low
    volume fraction and a large surface area, and -- unlike every other family
    here -- no preferred direction at all. The head-on exposed area is the top
    layer's strut ends seen end-on, which is a point array again, so this does
    not give up the area argument to buy isotropy.
    """
    verts, faces = [], []
    reach = p.link_reach * p.pitch
    nodes = []
    for k in range(p.layers + 1):
        f = k / p.layers
        pts = _centres(p, seed=p.seed + 977 * k)
        rng = _lcg(p.seed * 13 + 5 + k)
        # sunk by one strut radius: a node sitting exactly on Y = 0 puts the
        # top half of its strut above the entrance plane, and everything
        # downstream (camera, measurement windows, the flat control's Y) assumes
        # the structure lives at Y <= 0.
        y = -p.strut_r - (p.depth - p.strut_r) * f
        layer = []
        for (x, z) in pts:
            x += (2.0 * next(rng) - 1.0) * p.layer_jitter * p.pitch
            z += (2.0 * next(rng) - 1.0) * p.layer_jitter * p.pitch
            layer.append((x, y, z))
        nodes.append(layer)

    for k in range(p.layers):
        upper, lower = nodes[k], nodes[k + 1]
        for a in upper:
            cand = []
            for b in lower:
                dx, dz = b[0] - a[0], b[2] - a[2]
                d2 = dx * dx + dz * dz
                if d2 <= reach * reach:
                    cand.append((d2, b))
            cand.sort(key=lambda t: t[0])
            for _, b in cand[:max(1, p.links)]:
                _strut(verts, faces, a, b, p.strut_r, max(3, p.strut_seg))
    _backing(verts, faces, p, -p.depth)
    return verts, faces


# --- topology: honeycomb (negative control) ---------------------------------

def _smooth_dir_field(seed, cell):
    """A C1-continuous unit direction field on the (x, z) plane.

    Random unit vectors on a grid of spacing `cell`, bilinearly interpolated
    with a smoothstep weight. Interpolating the VECTOR rather than the angle
    avoids the wraparound that makes angle interpolation discontinuous, and
    picking random vectors rather than summing sines keeps it isotropic — a sum
    of two sine waves has preferred axes, which is the one thing this project
    must not build in.

    Not normalised after interpolation, deliberately: the magnitude sags
    between grid nodes, so the lean angle varies a little across the panel as
    well as the direction. That is extra irregularity for free.
    """
    grid = {}

    def at(gx, gz):
        k = (gx, gz)
        if k not in grid:
            r = _lcg(seed * 1000003 + gx * 7919 + gz * 104729)
            a = 2.0 * math.pi * next(r)
            grid[k] = (math.cos(a), math.sin(a))
        return grid[k]

    def sample(x, z):
        fx, fz = x / cell, z / cell
        gx, gz = int(math.floor(fx)), int(math.floor(fz))
        tx, tz = fx - gx, fz - gz
        sx = tx * tx * (3.0 - 2.0 * tx)
        sz = tz * tz * (3.0 - 2.0 * tz)
        v00, v10 = at(gx, gz), at(gx + 1, gz)
        v01, v11 = at(gx, gz + 1), at(gx + 1, gz + 1)
        a0 = (v00[0] + (v10[0] - v00[0]) * sx, v00[1] + (v10[1] - v00[1]) * sx)
        a1 = (v01[0] + (v11[0] - v01[0]) * sx, v01[1] + (v11[1] - v01[1]) * sx)
        return (a0[0] + (a1[0] - a0[0]) * sz, a0[1] + (a1[1] - a0[1]) * sz)

    return sample


def _clip_halfplane(poly, p, q, tag=None):
    """Clip convex polygon `poly` to the half-plane nearer to p than to q.

    `poly` is a list of `(point, edge_tag)`, where edge_tag labels the edge
    running from that point to the next one and holds the index of the SITE
    whose bisector created it. Carrying that tag is what makes leaning cells
    possible: to build the wall between two cells at two different depths, the
    same neighbour pair has to be identified in both tessellations, and the
    geometry alone cannot say which edge is which once the sites have moved.
    """
    mx, mz = 0.5 * (p[0] + q[0]), 0.5 * (p[1] + q[1])
    dx, dz = q[0] - p[0], q[1] - p[1]
    out = []
    n = len(poly)
    for i in range(n):
        (a, ta), (b, _) = poly[i], poly[(i + 1) % n]
        sa = (a[0] - mx) * dx + (a[1] - mz) * dz
        sb = (b[0] - mx) * dx + (b[1] - mz) * dz
        if sa <= 0.0:
            out.append((a, ta))
        if (sa <= 0.0) != (sb <= 0.0):
            t = sa / (sa - sb)
            ip = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
            # leaving the half-plane: this point starts the clipped edge, which
            # belongs to the clipping site. entering: it continues the edge we
            # were already on, so it keeps that edge's tag.
            out.append((ip, tag if sa <= 0.0 else ta))
    return out


def voronoi_cells(sites, pitch):
    """Voronoi cell polygon for each site, by half-plane clipping.

    WHY THIS EXISTS, and it is not a refinement -- the first version was wrong.
    The honeycomb was built by drawing a hexagon around each jittered centre.
    A hexagon only tiles the plane on an EXACT lattice: the moment the centres
    are jittered by 0.30 x pitch the hexagons stop sharing edges, so every cell
    raises its own six walls, neighbours overlap into doubled walls, and gaps
    open between them. The 3D render (profiles/087) showed it immediately --
    hex tubes at staggered depths with daylight between them -- and it would
    have been invisible in the CSV. This project has already been bitten by
    exactly this once: "regular arrays are 8x darker than jittered ones" turned
    out to be gaps, not regularity (CONTEXT.md, round 1).

    A Voronoi tessellation of the same jittered points covers the plane exactly:
    every edge is shared by exactly two cells, there are no gaps and no
    overlaps, and the cells stay irregular, which the no-periodic-array rule
    requires.

    Sites are bucketed on a pitch-sized grid and each cell is clipped only
    against the 5x5 neighbourhood, because an O(n^2) pass over the ~4400 sites
    a 6.5-depth margin generates is 19 M distance tests per mesh build, and the
    mesh is rebuilt for every render.

    Returns one list per site of `(point, neighbour_index)` pairs, where
    neighbour_index identifies the site across that edge (None for an edge of
    the initial bounding box, which only happens at the far margin).
    """
    grid = {}
    for i, (x, z) in enumerate(sites):
        grid.setdefault((int(math.floor(x / pitch)),
                         int(math.floor(z / pitch))), []).append(i)
    R = pitch * 2.5
    cells = []
    for i, (x, z) in enumerate(sites):
        poly = [((x - R, z - R), None), ((x + R, z - R), None),
                ((x + R, z + R), None), ((x - R, z + R), None)]
        gx, gz = int(math.floor(x / pitch)), int(math.floor(z / pitch))
        for ax in range(gx - 2, gx + 3):
            for az in range(gz - 2, gz + 3):
                for j in grid.get((ax, az), ()):
                    if j != i:
                        poly = _clip_halfplane(poly, (x, z), sites[j], j)
                        if len(poly) < 3:
                            break
        cells.append(poly if len(poly) >= 3 else [])
    return cells


def _build_honeycomb(p: TopoParams):
    """Deep cell walls on a Voronoi tessellation, tapered thicker toward the
    floor.

    Present to FALSIFY, not to win: the exposed-area law predicts it loses
    head-on to a pillar array by about 41x at pitch 7.5 with a 0.4 mm wall. It
    lost by 1.30x (results/FINDINGS_topo_smoke.md) -- but that measurement was
    taken on the broken jittered-hexagon geometry described in
    `voronoi_cells`, so it is PROVISIONAL until re-run on this construction.
    The direction should survive: the broken version had doubled walls, i.e.
    MORE exposed area than the clean tessellation, so a correct honeycomb can
    only be darker.

    Unlike a pillar array, a cell wall never seals: `geom3d.seal_fraction` puts
    a plain cone at pitch 7.5 at 72.2% of nominal depth, so its "depth 30" is
    21.7 mm of cavity, while these walls are vertical and give the full 30 mm.
    """
    verts, faces = [], []
    sites0 = _centres(p)

    # Leaning cells are made by DISPLACING THE SITES with depth, not by tilting
    # the walls. Tilting each cell's walls independently would break the
    # tessellation the same way jittered hexagons did -- two neighbours cannot
    # each lean their shared wall their own way. Displacing the sites keeps a
    # valid Voronoi diagram at every depth, so the wall between two cells is
    # whatever the bisector says it is, at the top and at the floor alike.
    # The lean DIRECTION comes from a smooth field, not from a per-cell random
    # draw. An independent azimuth per cell was tried first and destroyed the
    # tessellation: at pitch 5.5 / depth 30 a 15 degree lean displaces a site by
    # 8.0 mm, which is 1.5 pitches, so the adjacency is completely rearranged
    # and 36270 of ~47000 walls had no counterpart at the floor -- 77% of the
    # structure gone. That is not an implementation problem, it is geometry:
    # two neighbours cannot lean their SHARED wall in two different directions.
    #
    # A field that varies over `cell_lean_domain` pitches makes neighbours lean
    # almost identically, so adjacency survives, while the panel as a whole
    # still contains every lean direction and stays isotropic at panel scale.
    # Locally coherent, globally isotropic -- which is also what the bird-of-
    # paradise barbules do (reference/SUMMARY.md 3.1).
    lean = p.cell_lean_deg > 0.0
    if lean:
        field = _smooth_dir_field(p.seed * 7 + 19,
                                  max(2.0, p.cell_lean_domain) * p.pitch)
        rng = _lcg(p.seed * 13 + 5)
        amp = p.depth * math.tan(math.radians(min(p.cell_lean_deg, 60.0)))
        sites1 = []
        for (x, z) in sites0:
            ux, uz = field(x, z)
            s = 1.0 + (2.0 * next(rng) - 1.0) * p.cell_lean_jitter
            sites1.append((x + amp * s * ux, z + amp * s * uz))
        cells1 = voronoi_cells(sites1, p.pitch)
    else:
        sites1, cells1 = sites0, None
    cells0 = voronoi_cells(sites0, p.pitch)
    if cells1 is None:
        cells1 = cells0

    def edges_by_neighbour(poly):
        out = {}
        n = len(poly)
        for k in range(n):
            A, tag = poly[k]
            B, _ = poly[(k + 1) % n]
            if tag is not None:
                out[tag] = (A, B)
        return out

    done = set()
    dropped = 0
    for i, poly0 in enumerate(cells0):
        e0 = edges_by_neighbour(poly0)
        e1 = edges_by_neighbour(cells1[i])
        for j, (A, B) in e0.items():
            key = (i, j) if i < j else (j, i)
            if key in done:
                continue
            done.add(key)
            if j in e1:
                C, D = e1[j]
            else:
                # A pair adjacent at the mouth need not still be Voronoi-
                # adjacent at the floor once the sites have moved, and no
                # amount of smoothing drives that to zero -- adjacency flips on
                # near-cocircular quadruples. Skipping those walls was tried
                # first and left 4.7% to 38% of the structure as HOLES.
                #
                # So the wall is built anyway, with its floor edge translated by
                # the mean displacement of the two cells that own it. Where the
                # true bisector has moved elsewhere this overlaps a neighbouring
                # wall, and overlap is free: the union is the geometry, so two
                # walls in the same place are one wall. A gap is not free. That
                # asymmetry is the same lesson the cone base-overlap bug taught
                # -- it presented as "regular arrays are 8x darker", and it was
                # daylight through the backing slab.
                mx = 0.5 * ((sites1[i][0] - sites0[i][0])
                            + (sites1[j][0] - sites0[j][0]))
                mz = 0.5 * ((sites1[i][1] - sites0[i][1])
                            + (sites1[j][1] - sites0[j][1]))
                C = (A[0] + mx, A[1] + mz)
                D = (B[0] + mx, B[1] + mz)
                dropped += 1
            L0 = math.hypot(B[0] - A[0], B[1] - A[1])
            L1 = math.hypot(D[0] - C[0], D[1] - C[1])
            if L0 < 1e-6 or L1 < 1e-6:
                continue
            wmax = 0.5 * max(p.wall_top, p.wall_bot)
            d0 = ((B[0] - A[0]) / L0, 0.0, (B[1] - A[1]) / L0)
            d1 = ((D[0] - C[0]) / L1, 0.0, (D[1] - C[1]) / L1)
            n0, n1 = (-d0[2], 0.0, d0[0]), (-d1[2], 0.0, d1[0])
            # extend each end so the corners where three walls meet fill solid
            # instead of leaving a pinhole
            A3 = _sub((A[0], 0.0, A[1]), _mul(d0, wmax))
            B3 = _add((B[0], 0.0, B[1]), _mul(d0, wmax))
            C3 = _sub((C[0], -p.depth, C[1]), _mul(d1, wmax))
            D3 = _add((D[0], -p.depth, D[1]), _mul(d1, wmax))
            tt, tb = _mul(n0, 0.5 * p.wall_top), _mul(n1, 0.5 * p.wall_bot)
            _hexa(verts, faces,
                  [_add(A3, tt), _add(B3, tt), _sub(B3, tt), _sub(A3, tt)],
                  [_add(C3, tb), _add(D3, tb), _sub(D3, tb), _sub(C3, tb)])
    _backing(verts, faces, p, -p.depth)
    if dropped:
        print("[geom_topo] honeycomb lean %.0f domain %.0f: %d of %d walls "
              "(%.1f%%) had no floor bisector and were translated instead"
              % (p.cell_lean_deg, p.cell_lean_domain, dropped, len(done),
                 100.0 * dropped / max(len(done), 1)))
    return verts, faces


def honeycomb_exposed_measured(p: TopoParams):
    """Actual wall-top area fraction, from the built tessellation.

    The analytic estimate in `exposed_fraction_est` assumes a REGULAR hex
    tiling (3 shared edges of length pitch/sqrt(3) per cell). A jittered
    Voronoi has a different total edge length, so the estimate is a guide and
    this is the number. Reported by __main__ next to the estimate; if the two
    disagree by a lot, quote this one.
    """
    sites = _centres(p)
    cells = voronoi_cells(sites, p.pitch)
    seen, total = set(), 0.0
    for i, poly in enumerate(cells):
        n = len(poly)
        for k in range(n):
            A, tag = poly[k]
            B, _ = poly[(k + 1) % n]
            if tag is None:
                continue
            key = (i, tag) if i < tag else (tag, i)
            if key in seen:
                continue
            seen.add(key)
            total += math.hypot(B[0] - A[0], B[1] - A[1]) * p.wall_top
    m = p.margin()
    field = (p.face_w + 2 * m) * (p.face_h + 2 * m)
    return total / field


def _assert_tessellates(cell, tol=1e-6):
    """Fail the build unless the cell lattice actually tiles the plane.

    A cell array that does not tile is not a honeycomb, it is a honeycomb
    pattern with holes in it, and the holes look through to the flat backing
    slab. This project has now shipped that defect twice -- once with jittered
    hexagons (fixed by going to Voronoi) and once with a swapped lattice in
    `_build_comb` -- and neither time did anything crash, neither time did the
    CSV look wrong, and both times the render still read as "a honeycomb" to a
    quick glance. So it is checked arithmetically instead of by eye.

    The test is edge sharing: in a tiling every one of a cell's six edges is
    also an edge of exactly one neighbour. Six shared edges, no more, no less.
    """
    def key(a, b):
        return tuple(sorted((tuple(round(c, 6) for c in a),
                             tuple(round(c, 6) for c in b))))

    h = cell(0, 0)
    mine = {key(h[k], h[(k + 1) % 6]) for k in range(6)}
    shared = 0
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if (i, j) == (0, 0):
                continue
            n = cell(i, j)
            shared += len(mine & {key(n[k], n[(k + 1) % 6]) for k in range(6)})
    if shared != 6:
        raise ValueError(
            "cell lattice does not tessellate: a cell shares %d of its 6 edges "
            "with its neighbours. Gaps in a cell array open straight onto the "
            "backing slab and every optical number measured on it is void."
            % shared)


def _build_comb(p: TopoParams):
    """COMMERCIAL expanded honeycomb — every cell identical, as it is sold.

    This exists because `honeycomb` above is NOT a product. It tessellates
    JITTERED points, so every cell is a different shape. Aluminium honeycomb is
    made by bonding foil ribbons at regular intervals and pulling the stack
    open, which can only produce identical cells -- and the numbers quoted for
    "the honeycomb you can buy" were measured on the irregular one for a full
    day. `[확인: alcomb.com 제조 설명, and the L/W ribbon literature]`

    Three things the real product has that a regular hexagon grid does not:

    1. **The walls along the ribbon direction are DOUBLE thickness.** That is
       where two foils are bonded. Four walls of each cell are one foil, two
       are two foils. Optically this matters: those walls present twice the
       exposed area at the mouth.
    2. **The cell is stretched, not regular.** Expansion pulls the bonded stack
       open, so the hexagon is elongated across the ribbon direction. Fully
       expanded is close to regular; under- and over-expanded are not.
    3. **It is PERIODIC.** There is no jitter and there cannot be. This
       collides head-on with the project's own no-periodic-array rule -- a
       scanning beam over a periodic cell array produces periodic bright spots
       -- and that collision is a real finding about the bought option, not
       something to design away.

    `comb_expand` is the ratio of the expanded pitch across the ribbon to the
    bonded pitch along it. 1.0 is a regular hexagon.
    """
    verts, faces = [], []
    t1 = p.wall_top                     # single foil
    t2 = 2.0 * p.wall_top               # bonded node: two foils
    b1, b2 = p.wall_bot, 2.0 * p.wall_bot
    S = p.pitch                         # cell size across flats
    ex = max(0.3, p.comb_expand)
    rad = S / math.sqrt(3.0)            # circumradius; vertices lie along z
    # THE LATTICE. Vertices sit at 30+60k degrees, so the cell has FLATS facing
    # +-x (flat-to-flat = S) and VERTICES along +-z (vertex-to-vertex = 2*rad).
    # A cell therefore meets its x-neighbour along a whole flat wall, and the
    # rows in z interlock at 1.5*rad with alternate rows shifted half a cell
    # across.
    #
    # The first version had these two axes swapped -- x stepped by
    # S*sqrt(3)/2 and z by 1.5*S -- which is the lattice for a hexagon turned
    # 30 degrees from this one. Nothing crashed and the render still looked
    # like a honeycomb, but NO cell shared an edge with ANY neighbour and
    # 30.1 % of the face belonged to no cell at all: open channels straight
    # down to the backing slab, i.e. 30 % flat plate wearing a honeycomb
    # costume. `_assert_tessellates` below now makes that a build error, and
    # `sweep_comb` / every stack containing `comb` had to be re-measured.
    dx = S * ex                         # across the ribbon (expansion dir)
    dz = 1.5 * rad                      # along the ribbon: row pitch
    row_off = 0.5 * S * ex              # alternate rows shift across
    m = p.margin()
    nx = int((p.face_w + 2 * m) / dx) + 3
    nz = int((p.face_h + 2 * m) / dz) + 3
    dy = (0.0, -p.depth, 0.0)

    def wall(A, B, tt, tb):
        L = math.hypot(B[0] - A[0], B[1] - A[1])
        if L < 1e-9:
            return
        d = ((B[0] - A[0]) / L, 0.0, (B[1] - A[1]) / L)
        n = (-d[2], 0.0, d[0])
        ext = _mul(d, 0.5 * max(tt, tb))
        A3 = _sub((A[0], 0.0, A[1]), ext)
        B3 = _add((B[0], 0.0, B[1]), ext)
        a, b = _mul(n, 0.5 * tt), _mul(n, 0.5 * tb)
        _hexa(verts, faces,
              [_add(A3, a), _add(B3, a), _sub(B3, a), _sub(A3, a)],
              [_add(_add(A3, dy), b), _add(_add(B3, dy), b),
               _sub(_add(B3, dy), b), _sub(_add(A3, dy), b)])

    def cell(ix, iz):
        """The six corners of one cell, stretched across the ribbon."""
        cx = ix * dx + (row_off if iz % 2 else 0.0) - m
        cz = iz * dz - (p.face_h / 2.0 + m)
        return [(cx + rad * ex * math.cos(math.radians(30 + 60 * k)),
                 cz + rad * math.sin(math.radians(30 + 60 * k)))
                for k in range(6)]

    _assert_tessellates(cell)

    # The field must reach face + margin on all four sides, or the measurement
    # window sees world background past the edge of the panel.
    _c0, _c1 = cell(0, 0), cell(nx - 1, nz - 1)
    _lo_x, _lo_z = min(q[0] for q in _c0), min(q[1] for q in _c0)
    _hi_x, _hi_z = max(q[0] for q in _c1), max(q[1] for q in _c1)
    assert _lo_x <= -m + 1e-6 and _hi_x >= p.face_w + m - 1e-6, \
        "comb field x %.2f..%.2f does not cover %.2f..%.2f" % (
            _lo_x, _hi_x, -m, p.face_w + m)
    assert _lo_z <= -(p.face_h / 2.0 + m) + 1e-6 \
        and _hi_z >= p.face_h / 2.0 + m - 1e-6, \
        "comb field z %.2f..%.2f does not cover +-%.2f" % (
            _lo_z, _hi_z, p.face_h / 2.0 + m)

    # cell(0, 0) already sits at the -m corner, so the loop starts at 0. It
    # used to run range(-nx, nx), which laid down FOUR TIMES the cells -- half
    # of them at negative coordinates, entirely outside the panel and its
    # margin. A 100 mm panel built a 276 mm field: 74 736 triangles of which
    # 9 976 survive the clip. Invisible in a measurement, because the window
    # only ever sees the face, and plainly wrong in a preview and in the time
    # every render took. The coverage assert below is what makes shrinking the
    # loop safe: it fails if the field ever stops reaching face + margin.
    seen = set()
    for iz in range(0, nz):
        for ix in range(0, nx):
            hexv = cell(ix, iz)
            for k in range(6):
                A, B = hexv[k], hexv[(k + 1) % 6]
                key = (round((A[0] + B[0]) * 100), round((A[1] + B[1]) * 100))
                if key in seen:
                    continue
                seen.add(key)
                # the two walls whose normal points along the ribbon (z) are
                # the bonded ones -- they carry two foils
                horiz = abs(B[0] - A[0]) < abs(B[1] - A[1])
                wall(A, B, (t2 if horiz else t1), (b2 if horiz else b1))
    _backing(verts, faces, p, -p.depth)
    import geom_kit as _GK
    verts, faces = _GK.orient_outward(verts, faces)
    return verts, faces


# --- entry point ------------------------------------------------------------

_BUILDERS = {"shingle": _build_shingle,
             "truss": _build_truss,
             "honeycomb": _build_honeycomb,
             # the product, as opposed to the idealisation above
             "comb": _build_comb}


def build_mesh(p: TopoParams):
    try:
        fn = _BUILDERS[p.topology]
    except KeyError:
        raise ValueError("unknown topology %r; have %s"
                         % (p.topology, sorted(_BUILDERS)))
    verts, faces = fn(p)
    # EVERY topology through one exit, oriented. The shingle came out wound
    # inward while the comb came out outward, and a glossy coating reads the
    # two windings ~50 % apart; see geom_kit.orient_outward.
    import geom_kit as _GK
    return _GK.orient_outward(verts, faces)


def describe(p: TopoParams) -> dict:
    return {"family": "topo",
            "topology": p.topology,
            "depth_mm": p.depth,
            "pitch_mm": p.pitch,
            "pitch_mean_mm": p.pitch,
            "aspect": p.aspect(),
            "jitter": p.jitter,
            "cell_area_mm2": p.cell_area(),
            "exposed_fraction_est": p.exposed_fraction_est(),
            "margin_depths": p.margin_depths,
            "tilt_deg": p.tilt_deg,
            "plate_t_top_mm": p.plate_t_top,
            "plate_t_bot_mm": p.plate_t_bot,
            "plate_over": p.plate_over,
            "layers": p.layers,
            "links": p.links,
            "strut_r_mm": p.strut_r,
            "wall_top_mm": p.wall_top,
            "wall_bot_mm": p.wall_bot}


if __name__ == "__main__":
    print("%-10s %8s %8s %10s %9s %9s"
          % ("topology", "verts", "faces", "exposed%", "aspect", "cells"))
    for topo in ("shingle", "truss", "honeycomb"):
        for pitch in (5.5, 7.5):
            prm = TopoParams(topology=topo, pitch=pitch, depth=30.0,
                             face_w=60.0, face_h=60.0)
            v, f = build_mesh(prm)
            ys = [q[1] for q in v]
            print("%-10s %8d %8d %10.4f %9.1f %9d   y %.1f..%.1f"
                  % (topo, len(v), len(f),
                     100.0 * prm.exposed_fraction_est(), prm.aspect(),
                     len(_centres(prm)), min(ys), max(ys)))
