"""
Phase 4: shaped floors for the bottom 2-5 mm of a honeycomb cell.

WHY. Phase 3 separated the two viewer-facing axes and found they belong to
different layers: form is set by the layer the light meets first, head-on
brightness by the layer it meets last. The control was decisive -- a honeycomb
over a FINER honeycomb reads 1.640 head-on, unchanged, because the tube still
ends in a flat slab; the same honeycomb over cones reads 0.121.

So the honeycomb's problem was never its walls or its cell shape. It is that
every cell is a tube pointing at the viewer with a flat mirror at the end.

Phase 3 fixed that by spending half the envelope on a cone field, which cost
total reflectance: a cone needs its depth in ONE continuous cavity and 25 mm of
cone is much worse than 50 mm of cone. This module asks the obvious next
question -- **how little of the depth does the floor actually need?** Give the
tube 47 mm and the floor 3 mm and you might keep the honeycomb's total
reflectance and the cone's head-on at the same time.

THE FOUR FLOORS, chosen because each is a different factory:

    cone      moulded shallow cones, tips up. What phase 3 used, made thin.
    pyramid   embossed sheet, square pyramids. A press and a die; the sheet is
              made flat and glued behind the honeycomb, so nothing has to be
              aligned cell-to-cell.
    wave      embossed sheet, egg-carton. Same factory as pyramid, no edges --
              worth separating because a pyramid's flat facets can retro-
              reflect where a curve cannot.
    gap       no floor at all: the backing slab simply set back, so the cells
              open onto air. Costs nothing to make. Included as the cheap
              control that tells you whether SHAPE is doing the work or merely
              DISTANCE.

HOW IT PLUGS IN. Every layer module in this project returns a union of closed
solids with its backing slab appended last as exactly 8 verts + 6 quads, and
`geom_stack._build_layer` strips that slab. This module follows the same
contract, so a shaped floor is just a very shallow bottom layer in an ordinary
stack and needs no new sweep machinery.

MARGIN, AND THE TRAP IN IT. `margin_depths` is a multiple of the LAYER's depth
everywhere else in the project, which is right when the layers are comparable.
Here they are not: a 47 mm tube wants 94 mm of margin and a 3 mm floor would
get 6 mm, leaving the floor absent under most of what a tilted camera sees --
the render would show honeycomb standing on nothing near the edges and the
number would be wrong in the direction that flatters the design. So this module
multiplies `margin_depths` by `margin_depth_ref` (the WHOLE stack's depth) when
it is given, and `geom_stack` merges `bot_params` before the shared keys, so
setting it from the sweep survives.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FloorParams:
    kind: str = "pyramid"            # cone | pyramid | wave | gap
    face_w: float = 60.0
    face_h: float = 60.0
    depth: float = 3.0               # how deep the shaping runs
    pitch: float = 2.0               # feature pitch of the floor itself
    backing: float = 2.0
    margin_depths: float = 2.0
    margin_depth_ref: float = 0.0    # 0 -> use `depth`, as elsewhere
    # AN ABSOLUTE FLOOR ON THE MARGIN, in mm, because the ratio above is not
    # enough. `margin_depth_ref` only ever reaches `margin()` multiplied by
    # `margin_depths`, so when that is ZERO -- which is exactly what the
    # preview and the STL export use, since they want the part and not the
    # overrun -- the product is zero however large the reference, and the floor
    # falls back to one pitch. A blade field spans x -15.8..110.7 for a 100 mm
    # panel; its floor came out -2.0..106.0, leaving 13.8 mm of blades standing
    # on nothing at the origin corner. Invisible in every measurement, because
    # those run at margin_depths = 2.0 where the ratio does work, and obvious
    # the moment anyone looked at the preview. `geom_stack` now passes the
    # tube's real overhang here as a length.
    margin_min: float = 0.0
    seed: int = 23
    # subdivisions per pitch for `wave`. 3 was the first value tried and the
    # render showed a field of facets, not a curve -- which would have answered
    # "do flat faces hurt?" with a surface that was ALL flat faces. 12 keeps the
    # facet angle under ~8 degrees at any depth used here.
    grid: int = 12
    tip_flat: float = 0.0            # flat spot on a pyramid apex, mm
    # Phase 5: de-periodising the pyramid WITHOUT breaking its tiling. The
    # base grid stays exact -- gaps between bases would expose the slab -- and
    # only the APEX moves: laterally by up to `apex_jitter` of the half-pitch,
    # and downward by up to `tip_drop` of the depth. Every cell then presents
    # four faces at its own angles, which is what removes the repeating
    # specular glint a scanning beam sees on identical cells.
    apex_jitter: float = 0.0         # lateral apex wander, fraction of pitch/2
    mix_depth_frac: float = 1.0      # pyrmix: small-pyramid depth / depth
    tip_drop: float = 0.0            # downward apex wander, fraction of depth
    # Phase 6.6, manufacturing reality of the pyramid field:
    # `valley_round` is the fillet radius (mm) an injection mould leaves at
    # the bottom of every valley (steel cannot hold a zero-radius ridge).
    # Modelled as a half-cylinder bead laid along every valley line, tangent
    # to both flanks, unioned with the cells by overlap -- the same
    # "overlap is free, the union is the geometry" convention geom_topo's
    # blades use. NOT kernel-clean by construction; measured, documented.
    valley_round: float = 0.0
    # Phase 9.4b: fiber LEAN for the flock stand-in ("pillars" kind
    # only). Each pillar is sheared so its top translates by
    # depth*tan(lean) in a per-pillar seeded random azimuth -- real flock
    # fibers tilt and overlap, hiding the floor from a head-on viewer.
    pillar_lean: float = 0.0         # degrees from vertical
    # `row_offset` is strip-assembly tolerance (mm): the field is built as
    # one-row strips (cut along valley planes) and glued; adjacent strips
    # sit at alternating +offset/2 / -offset/2 in y -- the deterministic
    # worst case of a +-offset/2 assembly jig.
    row_offset: float = 0.0

    def margin(self):
        ref = self.margin_depth_ref or self.depth
        return max(self.margin_depths * ref, self.pitch, self.margin_min)


def _slab(verts, faces, p: FloorParams, y0: float):
    """The backing slab, appended last: 8 verts, 6 quads. The contract."""
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


def _lattice(p: FloorParams):
    """Feature centres covering the face plus its margin."""
    m = p.margin()
    n_x = int((p.face_w + 2 * m) / p.pitch) + 2
    n_z = int((p.face_h + 2 * m) / p.pitch) + 2
    for iz in range(n_z):
        for ix in range(n_x):
            yield (-m + (ix + 0.5) * p.pitch,
                   -(p.face_h / 2.0 + m) + (iz + 0.5) * p.pitch)


def _build_pyramid(p: FloorParams):
    """Square pyramids, apex UP. Base sits on the slab; nothing overhangs.

    `tip_flat` truncates the apex. A press cannot make a mathematical point and
    a sharp one folds over in service, so the default is a real 0.05-0.2 mm
    flat -- the same honesty the cone family applies to its tip radius.
    """
    verts, faces = [], []
    a = p.pitch / 2.0
    t = max(0.0, min(p.tip_flat, p.pitch * 0.8)) / 2.0

    x = (p.seed * 1103515245 + 12345) & 0x7FFFFFFF
    def rng():
        nonlocal x
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        return x / 2147483648.0

    jmax = max(0.0, min(p.apex_jitter, 0.9)) * (a - t)
    dmax = max(0.0, min(p.tip_drop, 0.6)) * p.depth
    m = p.margin()
    z_base = -(p.face_h / 2.0 + m)
    for cx, cz in _lattice(p):
        jx = (2.0 * rng() - 1.0) * jmax
        jz = (2.0 * rng() - 1.0) * jmax
        dy = -rng() * dmax
        # strip-assembly tolerance: alternate strips (rows along x) sit a full
        # `row_offset` LOWER -- the same relative step as a +-off/2 jig, kept
        # entirely below y=0 so the floor-family contract (nothing pokes into
        # the layer above) holds. The WHOLE cell solid translates.
        if p.row_offset:
            iz = int(round((cz - z_base) / p.pitch - 0.5))
            ry = 0.0 if iz % 2 == 0 else -p.row_offset
        else:
            ry = 0.0
        b = len(verts)
        verts += [(cx - a, -p.depth + ry, cz - a),
                  (cx + a, -p.depth + ry, cz - a),
                  (cx + a, -p.depth + ry, cz + a),
                  (cx - a, -p.depth + ry, cz + a)]
        if t > 0:
            verts += [(cx + jx - t, dy + ry, cz + jz - t),
                      (cx + jx + t, dy + ry, cz + jz - t),
                      (cx + jx + t, dy + ry, cz + jz + t),
                      (cx + jx - t, dy + ry, cz + jz + t)]
            faces.append((b + 4, b + 5, b + 6, b + 7))
            for i in range(4):
                j = (i + 1) % 4
                faces.append((b + i, b + j, b + 4 + j, b + 4 + i))
        else:
            verts.append((cx + jx, dy + ry, cz + jz))
            for i in range(4):
                faces.append((b + i, b + (i + 1) % 4, b + 4))
        faces.append((b + 3, b + 2, b + 1, b))
    if p.valley_round > 0:
        _valley_beads(verts, faces, p)
    _slab(verts, faces, p, -p.depth - abs(p.row_offset))
    return verts, faces


def _build_pillars(p: FloorParams):
    """Phase 9.4: a fiber-forest stand-in (flocking, 식모). Square prisms
    standing on the slab top, tops at y = 0.

    Field semantics for this kind only: `pitch` is the fiber spacing,
    `depth` the fiber height, and `tip_flat` is the PILLAR WIDTH in mm
    (not an apex land) -- fill fraction = (tip_flat/pitch)^2. Real flock
    is round fibers at ~0.1 mm spacing; the aspect law is scale-
    invariant, so the sweep runs a scaled-up lattice and says so.
    The pillar bottoms coincide with the slab top; Phase 9.v measured
    coincident interior planes to be optically inert (0.01 % worst).

    `pillar_lean` (9.4b) shears each prism: the top translates by
    depth*tan(lean) in a per-pillar seeded azimuth. Side faces stay
    planar (parallelograms); tops stay at y = 0; overlap between leaning
    fibers is fine -- the union is the geometry, as everywhere.
    """
    import math as _m
    verts, faces = [], []
    t = max(0.05, min(p.tip_flat, p.pitch * 0.98)) / 2.0
    sh = p.depth * _m.tan(_m.radians(max(0.0, min(p.pillar_lean, 80.0))))
    x = (p.seed * 1103515245 + 12345) & 0x7FFFFFFF
    def rng():
        nonlocal x
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        return x / 2147483648.0
    for cx, cz in _lattice(p):
        ang = 2.0 * _m.pi * rng()
        dx, dz = sh * _m.cos(ang), sh * _m.sin(ang)
        b = len(verts)
        verts += [(cx - t, -p.depth, cz - t),
                  (cx + t, -p.depth, cz - t),
                  (cx + t, -p.depth, cz + t),
                  (cx - t, -p.depth, cz + t),
                  (cx - t + dx, 0.0, cz - t + dz),
                  (cx + t + dx, 0.0, cz - t + dz),
                  (cx + t + dx, 0.0, cz + t + dz),
                  (cx - t + dx, 0.0, cz + t + dz)]
        faces.append((b + 4, b + 5, b + 6, b + 7))          # top
        for i in range(4):
            j = (i + 1) % 4
            faces.append((b + i, b + j, b + 4 + j, b + 4 + i))
        faces.append((b + 3, b + 2, b + 1, b))              # bottom
    _slab(verts, faces, p, -p.depth)
    return verts, faces


def _valley_beads(verts, faces, p: FloorParams):
    """Half-cylinder fillet beads along every valley line.

    An injection mould cannot hold a zero-radius steel ridge, so the part's
    valleys carry a radius R. The bead is a closed solid: an arc of radius
    R (ARC_SEG segments spanning 180 deg) whose centre sits where a circle
    of radius R is tangent to both flanks, extruded the full field length,
    ends capped, bottom sunk into the slab. Overlap with the cells does the
    union, exactly as geom_topo's blades overlap their lattice.
    """
    import math as _m
    R = p.valley_round
    a = p.pitch / 2.0
    L = _m.hypot(a, p.depth)
    yc = -p.depth + R * L / a          # tangent-to-both-flanks centre height
    ARC_SEG = 8
    m = p.margin()
    x0, x1 = -m, p.face_w + m
    z0, z1 = -(p.face_h / 2.0 + m), p.face_h / 2.0 + m
    ybot = -p.depth - 0.5              # buried in the slab

    def bead(axis, c):
        """One bead along `axis` ('x' or 'z') at cross position c."""
        b = len(verts)
        prof = []                      # (u, y) cross-section, u across bead
        prof.append((-R, ybot))
        for i in range(ARC_SEG + 1):
            ang = _m.pi * i / ARC_SEG  # left rim, down through centre, right
            prof.append((-R * _m.cos(ang), yc - R * _m.sin(ang)))
        prof.append((R, ybot))
        n = len(prof)
        for end in (0, 1):
            w = (x0, x1)[end] if axis == "x" else (z0, z1)[end]
            for (u, y) in prof:
                if axis == "x":
                    verts.append((w, y, c + u))
                else:
                    verts.append((c + u, y, w))
        for i in range(n - 1):
            q = (b + i, b + i + 1, b + n + i + 1, b + n + i)
            faces.append(q if axis == "x" else (q[3], q[2], q[1], q[0]))
        # end caps + bottom
        cap0 = tuple(range(b, b + n))
        cap1 = tuple(range(b + 2 * n - 1, b + n - 1, -1))
        faces.append(cap0 if axis == "z" else cap0[::-1])
        faces.append(cap1 if axis == "z" else cap1[::-1])
        q = (b, b + n, b + 2 * n - 1, b + n - 1)
        faces.append(q if axis == "x" else (q[3], q[2], q[1], q[0]))

    nz = int((z1 - z0) / p.pitch) + 2
    for iz in range(nz + 1):
        c = z0 + iz * p.pitch
        if z0 <= c <= z1:
            bead("x", c)
    nx = int((x1 - x0) / p.pitch) + 2
    for ix in range(nx + 1):
        c = x0 + ix * p.pitch
        if x0 <= c <= x1:
            bead("z", c)


def _build_wave(p: FloorParams):
    """Egg-carton: y = -d/2 * (1 - cos(2pi x/L) cos(2pi z/L)).

    One continuous embossed sheet rather than a field of separate solids, so it
    is closed by dropping a skirt from its border down to the slab. Curvature
    everywhere and no facet anywhere is the point: it is the control that says
    whether the pyramid's flat faces help or hurt.
    """
    verts, faces = [], []
    m = p.margin()
    L = p.pitch
    x0, x1 = -m, p.face_w + m
    z0, z1 = -(p.face_h / 2.0 + m), p.face_h / 2.0 + m
    nx = max(2, int((x1 - x0) / L * p.grid))
    nz = max(2, int((z1 - z0) / L * p.grid))

    def y_of(x, z):
        return -0.5 * p.depth * (1.0 - math.cos(2 * math.pi * x / L)
                                 * math.cos(2 * math.pi * z / L))

    top = []
    for iz in range(nz + 1):
        z = z0 + (z1 - z0) * iz / nz
        row = []
        for ix in range(nx + 1):
            x = x0 + (x1 - x0) * ix / nx
            row.append(len(verts))
            verts.append((x, y_of(x, z), z))
        top.append(row)
    for iz in range(nz):
        for ix in range(nx):
            faces.append((top[iz][ix], top[iz][ix + 1],
                          top[iz + 1][ix + 1], top[iz + 1][ix]))
    # skirt: drop the four borders to the slab plane so the sheet is a solid
    yb = -p.depth - 1e-3
    for row, rev in ((top[0], False), (top[-1], True)):
        seq = row[::-1] if rev else row
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            n = len(verts)
            verts += [(verts[a][0], yb, verts[a][2]),
                      (verts[b][0], yb, verts[b][2])]
            faces.append((a, b, n + 1, n))
    for col, rev in ((0, True), (nx, False)):
        seq = [top[iz][col] for iz in range(nz + 1)]
        if rev:
            seq = seq[::-1]
        for i in range(len(seq) - 1):
            a, b = seq[i], seq[i + 1]
            n = len(verts)
            verts += [(verts[a][0], yb, verts[a][2]),
                      (verts[b][0], yb, verts[b][2])]
            faces.append((a, b, n + 1, n))
    _slab(verts, faces, p, -p.depth)
    return verts, faces


def _build_gap(p: FloorParams):
    """Nothing but air, then the slab. The zero-cost control.

    `geom_stack._build_layer` strips the slab and gets an empty layer back,
    which is exactly right: the cells open onto `depth` mm of nothing and the
    stack puts its own slab underneath. If this matches a shaped floor, the
    shaping was never doing the work and phase 4's answer is "move the wall
    back", which is free.
    """
    verts, faces = [], []
    _slab(verts, faces, p, -p.depth)
    import geom_kit as _GK
    verts, faces = _GK.orient_outward(verts, faces)
    return verts, faces


def _build_pyrmix(p: FloorParams):
    """Two pyramid sizes tiling one panel: RF chambers mix sizes for
    BROADBAND absorption -- big cells own long wavelengths, small cells short
    ones. That is a wave mechanism with no ray-optics analogue, so Phase 5.3
    measures whether anything survives the translation.

    The tiling is a 3x3 super-cell of the small pitch `s = pitch`: one big
    pyramid of base 2s covers a 2x2 corner block, five small pyramids fill the
    remaining L. Bases tile exactly; no slab shows. `mix_depth_frac` sets the
    SMALL pyramids' depth as a fraction of `depth` -- 1.0 gives every tip in
    the entrance plane (small cells steeper), 0.5 preserves the big pyramid's
    slope on the small ones (their tips stop half-way down).
    """
    verts, faces = [], []
    sp = p.pitch
    sup = 3.0 * sp
    m = p.margin()
    small_depth = max(1e-3, min(1.0, p.mix_depth_frac)) * p.depth

    def pyr(cx, cz, half, depth):
        b = len(verts)
        verts.extend([(cx - half, -p.depth, cz - half),
                      (cx + half, -p.depth, cz - half),
                      (cx + half, -p.depth, cz + half),
                      (cx - half, -p.depth, cz + half),
                      (cx, -p.depth + depth, cz)])
        for i in range(4):
            faces.append((b + i, b + (i + 1) % 4, b + 4))
        faces.append((b + 3, b + 2, b + 1, b))

    nx = int((p.face_w + 2 * m) / sup) + 2
    nz = int((p.face_h + 2 * m) / sup) + 2
    for iz in range(nz):
        for ix in range(nx):
            ox = ix * sup - m
            oz = iz * sup - (p.face_h / 2.0 + m)
            pyr(ox + sp, oz + sp, sp, p.depth)              # big, base 2s
            for (ux, uz) in ((2, 0), (2, 1), (0, 2), (1, 2), (2, 2)):
                pyr(ox + (ux + 0.5) * sp, oz + (uz + 0.5) * sp,
                    sp / 2.0, small_depth)
    _slab(verts, faces, p, -p.depth)
    return verts, faces




def _build_boxpanel(p: FloorParams):
    """Phase 7.4: a box assembled ENTIRELY from the universal panel
    (pitch 4 / depth 20 / tip 0.1 / backing 2, 22 mm thick). `pitch` is
    the cell size, `depth` the total box depth. Floor: panel face-up.
    Walls: panels stood upright on every border, tips into each cell
    (shared borders carry two back-to-back panels, 44 mm). Rim: the
    44 mm double-wall top is capped with a face-up panel strip -- the
    "clad every exposed face with the universal tile" architecture the
    user named. Solids overlap; the union is the geometry.
    """
    TP, TD, TT, TB = 4.0, 20.0, 0.1, 2.0
    WT = TD + TB
    cell = p.pitch
    D = p.depth
    m = p.margin()
    x0, x1 = -m, p.face_w + m
    z0, z1 = -(p.face_h / 2.0 + m), p.face_h / 2.0 + m

    verts, faces = [], []

    def emit(v2, f2, xform):
        b = len(verts)
        for (x, y, z) in v2:
            verts.append(xform(x, y, z))
        for f in f2:
            faces.append(tuple(b + i for i in f))

    def field(face_w, face_h):
        q = FloorParams(kind="pyramid", face_w=face_w, face_h=face_h,
                        depth=TD, pitch=TP, tip_flat=TT, backing=TB,
                        margin_depths=0.0, margin_min=0.0)
        return _build_pyramid(q)

    # floor: tips up at y = -D + WT
    fv, ff = field(x1 - x0, z1 - z0)
    emit(fv, ff, lambda x, y, z: (x0 + x, y - D + WT, z))

    # walls: local field has tips at y=0 (pointing +y), z centered.
    wall_h = D - 2 * WT          # from under the cap to the floor tips
    ymid = -WT - wall_h / 2.0
    wv, wf = field(x1 - x0, wall_h)
    nx = max(1, int(round((x1 - x0) / cell)))
    nz = max(1, int(round((z1 - z0) / cell)))
    for iz in range(nz + 1):
        zb = z0 + iz * cell
        emit(wv, wf, lambda x, y, z, zb=zb: (x0 + x, ymid + z, zb + y))
        emit(wv, wf, lambda x, y, z, zb=zb: (x0 + x, ymid + z, zb - y))
    wv2, wf2 = field(z1 - z0, wall_h)
    for ix in range(nx + 1):
        xb = x0 + ix * cell
        emit(wv2, wf2, lambda x, y, z, xb=xb: (xb + y, ymid + z, z0 + x))
        emit(wv2, wf2, lambda x, y, z, xb=xb: (xb - y, ymid + z, z0 + x))

    # rim caps: face-up panel strips, width 2*WT, tips at y = 0
    cv, cf = field(x1 - x0, 2 * WT)
    for iz in range(nz + 1):
        zb = z0 + iz * cell
        emit(cv, cf, lambda x, y, z, zb=zb: (x0 + x, y, zb + z))
    cv2, cf2 = field(z1 - z0, 2 * WT)
    for ix in range(nx + 1):
        xb = x0 + ix * cell
        emit(cv2, cf2, lambda x, y, z, xb=xb: (xb + z, y, z0 + x))

    _slab(verts, faces, p, -D + TB)
    return verts, faces


def _build_boxgrid(p: FloorParams):
    """Phase 7.3, v3. The box is 1 mm single-thickness sheet (user spec).
    Floor: the final sample's pyramid field (4/20/0.1). Walls: VERTICAL
    ACCORDION folds. Two wall textures failed by measurement first:
    symmetric zigzag (1.17 % total -- its 90-degree concave corners are
    retroreflectors) and louvers (0.905 % -- 45-degree down-faces mirror
    the +-40-degree incidence cone straight back). The surviving
    requirement is the pyramid's own lesson: faces near-vertical. The
    accordion keeps every face vertical, swinging azimuth +-45 degrees:
    zero up-facing area; its concave corners lie in the horizontal plane
    and cannot reverse the beam's downward travel. Solids overlap; the
    union is the geometry.
    """
    TP, TD, TT, TB = 4.0, 20.0, 0.1, 2.0
    SHEET = 1.0
    PER, AMP = 24.0, 8.0        # accordion period along the wall, swing
    cell = p.pitch
    D = p.depth
    m = p.margin()
    x0, x1 = -m, p.face_w + m
    z0, z1 = -(p.face_h / 2.0 + m), p.face_h / 2.0 + m

    verts, faces = [], []

    def emit(v2, f2, xform):
        b = len(verts)
        for (x, y, z) in v2:
            verts.append(xform(x, y, z))
        for f in f2:
            faces.append(tuple(b + i for i in f))

    q = FloorParams(kind="pyramid", face_w=x1 - x0, face_h=z1 - z0,
                    depth=TD, pitch=TP, tip_flat=TT, backing=TB,
                    margin_depths=0.0, margin_min=0.0)
    fv, ff = _build_pyramid(q)
    emit(fv, ff, lambda x, y, z: (x0 + x, y - D + TD + TB, z))

    ytop, ybot = 0.0, -(D - TD - TB)

    def wall(length, place):
        """Accordion: profile varies along the LENGTH, uniform in y."""
        b = len(verts)
        n_half = max(2, int(length / (PER / 2.0)))
        pts = [(length * i / n_half,
                (AMP if i % 2 == 0 else 0.0) - AMP / 2.0)
               for i in range(n_half + 1)]
        n = len(pts)
        for off in (-SHEET / 2.0, SHEET / 2.0):
            for (w, u) in pts:
                for y in (ytop, ybot):
                    verts.append(place(w, y, u + off))
        for side in (0, 1):
            base = b + side * 2 * n
            for i in range(n - 1):
                q4 = (base + 2 * i, base + 2 * i + 1,
                      base + 2 * i + 3, base + 2 * i + 2)
                faces.append(q4 if side == 1 else q4[::-1])
        for i in range(n - 1):
            for y_i in (0, 1):
                q4 = (b + 2 * i + y_i, b + 2 * (i + 1) + y_i,
                      b + 2 * n + 2 * (i + 1) + y_i,
                      b + 2 * n + 2 * i + y_i)
                faces.append(q4 if y_i == 0 else q4[::-1])
        for edge in (0, n - 1):
            q4 = (b + 2 * edge, b + 2 * edge + 1,
                  b + 2 * n + 2 * edge + 1, b + 2 * n + 2 * edge)
            faces.append(q4 if edge == n - 1 else q4[::-1])

    nx = max(1, int(round((x1 - x0) / cell)))
    nz = max(1, int(round((z1 - z0) / cell)))
    for iz in range(nz + 1):
        zb = z0 + iz * cell
        wall(x1 - x0, lambda w, y, u, zb=zb: (x0 + w, y, zb + u))
    for ix in range(nx + 1):
        xb = x0 + ix * cell
        wall(z1 - z0, lambda w, y, u, xb=xb: (xb + u, y, z0 + w))

    _slab(verts, faces, p, -D + TB)
    return verts, faces


_BUILDERS = {"boxpanel": _build_boxpanel, "boxgrid": _build_boxgrid, "pyramid": _build_pyramid, "pillars": _build_pillars, "wave": _build_wave, "gap": _build_gap,
             "pyrmix": _build_pyrmix}


def build_mesh(p: FloorParams):
    if p.kind not in _BUILDERS:
        raise ValueError("unknown floor kind %r (have %s)"
                         % (p.kind, ", ".join(sorted(_BUILDERS))))
    v, f = _BUILDERS[p.kind](p)
    assert len(f) >= 6 and all(len(x) == 4 for x in f[-6:]), \
        "floor %s: last 6 faces must be the slab" % p.kind
    assert len({round(q[1], 3) for q in v[-8:]}) == 2, \
        "floor %s: last 8 verts must be the slab" % p.kind
    assert max(q[1] for q in v) <= 1e-6, \
        "floor %s: geometry above y=0 would poke into the layer above" % p.kind
    import geom_kit as _GK
    v, f = _GK.orient_outward(v, f)
    return v, f


def describe(p: FloorParams) -> dict:
    return {"family": "floor", "topology": p.kind, "depth_mm": p.depth,
            "pitch_mm": p.pitch, "margin_depths": p.margin_depths}
