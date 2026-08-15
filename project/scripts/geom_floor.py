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
    for cx, cz in _lattice(p):
        b = len(verts)
        verts += [(cx - a, -p.depth, cz - a), (cx + a, -p.depth, cz - a),
                  (cx + a, -p.depth, cz + a), (cx - a, -p.depth, cz + a)]
        if t > 0:
            verts += [(cx - t, 0.0, cz - t), (cx + t, 0.0, cz - t),
                      (cx + t, 0.0, cz + t), (cx - t, 0.0, cz + t)]
            faces.append((b + 4, b + 5, b + 6, b + 7))
            for i in range(4):
                j = (i + 1) % 4
                faces.append((b + i, b + j, b + 4 + j, b + 4 + i))
        else:
            verts.append((cx, 0.0, cz))
            for i in range(4):
                faces.append((b + i, b + (i + 1) % 4, b + 4))
        faces.append((b + 3, b + 2, b + 1, b))
    _slab(verts, faces, p, -p.depth)
    return verts, faces


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
    return verts, faces


_BUILDERS = {"pyramid": _build_pyramid, "wave": _build_wave, "gap": _build_gap}


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
    return v, f


def describe(p: FloorParams) -> dict:
    return {"family": "floor", "topology": p.kind, "depth_mm": p.depth,
            "pitch_mm": p.pitch, "margin_depths": p.margin_depths}
