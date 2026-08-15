"""
Can this mesh be FDM-printed FACE UP with a 0.4 mm nozzle and no support?

Face up means tips toward +Y: the part is built from -Y (backing slab, on the
plate) up to +Y (cone apexes, printed last). Project convention, matching
geom3d.build_mesh: X across the face, Y depth with the apex plane at Y = 0 and
deeper NEGATIVE, Z vertical on the panel. On the printer, Y is the build axis
and X/Z are the plate.

    overhang_report     surface angle away from the build axis, per face
    min_feature_report  narrowest cross-section a layer has to lay down
    bridge_report       material appearing over nothing (islands)
    verdict             the three together, plus reasons

Two properties of geom3d meshes that this module had to discover, and that
every number below depends on:

1.  THE WINDING IS INVERTED. `sum (a x b).c` over build_mesh output is NEGATIVE
    (measured -51869 on a pitch-11 depth-20 coupon): cones, slab and caps are
    all wound with normals pointing INTO the solid -- consistent, but flipped.
    `outward_sign()` detects it and everything here flips accordingly. Read a
    geom3d normal literally and every upward cone flank reads as a 67 deg
    overhang.

2.  IT IS A UNION THAT WAS NEVER UNIONED. Cones interpenetrate on purpose and
    every base disc is buried 0.5 mm inside the backing slab. Those discs are
    flat downward faces; taken literally they are ~20% of the area and 90 deg
    "overhangs", all fiction. They are removed by a point-in-union test: nudge
    the centroid along its outward normal, slice exactly at that height, take
    the nonzero winding number of the 2D cross-section. Nonzero means the
    outward side is inside another shell, so the face is interior.

LIMITS, stated rather than half-implemented:
  - No boolean union. Everything comes from oriented cross-sections plus the
    nonzero fill rule, which IS the union for consistently wound closed shells
    -- but slice by slice, never as a solid.
  - Slicing is Y-only. `overhang_report` honours an arbitrary `up`, but its
    buried-face filter and the other two reports require up = +Y.
  - No warping, adhesion, cooling, retraction or travel: this answers "is the
    geometry printable", not "will the print succeed".
  - stdlib only, no numpy, no bpy, so it imports under Blender's python and
    plain python3 alike.
"""

from __future__ import annotations

import math
from collections import deque

UP = (0.0, 1.0, 0.0)


# --------------------------------------------------------------------------
# mesh basics
# --------------------------------------------------------------------------

def _fan(faces):
    """Triangulate n-gons as a fan; geom3d emits quads along the flanks."""
    for f in faces:
        for k in range(1, len(f) - 1):
            yield f[0], f[k], f[k + 1]


def outward_sign(verts, faces) -> float:
    """+1 if the winding gives outward normals, -1 if it is inverted.

    Divergence theorem: the sum is 6V, positive only for outward winding. Valid
    on interpenetrating shells because each contributes its own volume with the
    same sign.
    """
    s = 0.0
    for i, j, k in _fan(faces):
        a, b, c = verts[i], verts[j], verts[k]
        s += (a[0] * (b[1] * c[2] - b[2] * c[1])
              - a[1] * (b[0] * c[2] - b[2] * c[0])
              + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return -1.0 if s < 0.0 else 1.0


def _tris(verts, faces):
    """[(A, B, C, nx, ny, nz, area)] with OUTWARD unit normals."""
    sgn = outward_sign(verts, faces)
    out = []
    for i, j, k in _fan(faces):
        a, b, c = verts[i], verts[j], verts[k]
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx = (uy * vz - uz * vy) * sgn
        ny = (uz * vx - ux * vz) * sgn
        nz = (ux * vy - uy * vx) * sgn
        L = math.sqrt(nx * nx + ny * ny + nz * nz)
        if L > 1e-15:                       # skips the degenerate apex fan
            out.append((a, b, c, nx / L, ny / L, nz / L, 0.5 * L))
    return out


def _shells(verts, faces):
    """Connected-component id per triangle, from shared vertices (union-find).

    Recovers "which solid" -- each geom3d cone is its own closed shell and the
    slab is another -- without knowing anything about geom3d.
    """
    parent = list(range(len(verts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for f in faces:
        r = find(f[0])
        for v in f[1:]:
            s = find(v)
            if s != r:
                parent[s] = r
    return [find(i) for i, j, k in _fan(faces)]


# --------------------------------------------------------------------------
# oriented cross-sections: the union, without a boolean
# --------------------------------------------------------------------------

def _cut(t, y):
    """Directed cross-section of triangle `t` at Y = y, or None.

    Vertices are classified by the strict test (vy > y), which makes the slice
    watertight with no epsilon fudging. The segment is directed so the solid
    lies to its LEFT in (x, z): the outward normal projects to (nx, nz), and
    rotating that +90 degrees gives the travel direction (-nz, nx).
    """
    a, b, c, nx, ny, nz, _ = t
    pts = []
    for p, q in ((a, b), (b, c), (c, a)):
        if (p[1] > y) != (q[1] > y):
            s = (y - p[1]) / (q[1] - p[1])
            pts.append((p[0] + s * (q[0] - p[0]), p[2] + s * (q[2] - p[2])))
    if len(pts) != 2:
        return None
    (x0, z0), (x1, z1) = pts
    if (x1 - x0) * -nz + (z1 - z0) * nx < 0.0:
        return (x1, z1, x0, z0)
    return (x0, z0, x1, z1)


def _sweep(tris, ys, z0, dz, nrows, shell=None):
    """Yield (y, segs, sids, rows) for ascending `ys`, one plane live at a time.

    Triangles are swept in order of their minimum Y, so the cost is
    O(T log T + total segments) instead of O(planes * T), and only one plane's
    worth of segments is ever in memory.
    """
    ymin = [min(t[0][1], t[1][1], t[2][1]) for t in tris]
    ymax = [max(t[0][1], t[1][1], t[2][1]) for t in tris]
    order = sorted(range(len(tris)), key=lambda i: ymin[i])
    active, ptr = [], 0
    for y in ys:
        while ptr < len(order) and ymin[order[ptr]] <= y:
            active.append(order[ptr])
            ptr += 1
        active = [i for i in active if ymax[i] > y]
        segs, sids, rows = [], [], [[] for _ in range(nrows)]
        for i in active:
            s = _cut(tris[i], y)
            if s is None:
                continue
            k = len(segs)
            segs.append(s)
            sids.append(None if shell is None else shell[i])
            r0 = max(0, int((min(s[1], s[3]) - z0) / dz))
            r1 = min(nrows - 1, int((max(s[1], s[3]) - z0) / dz))
            for r in range(r0, r1 + 1):
                rows[r].append(k)
        yield y, segs, sids, rows


def _winding(segs, rows, z0, dz, nrows, x, z):
    """Nonzero winding number of the union at (x, z); != 0 means inside."""
    r = int((z - z0) / dz)
    if r < 0 or r >= nrows:
        return 0
    wn = 0
    for i in rows[r]:
        x0, z0s, x1, z1s = segs[i]
        if z0s <= z:
            if z1s > z and (x1 - x0) * (z - z0s) - (x - x0) * (z1s - z0s) > 0:
                wn += 1
        elif z1s <= z and (x1 - x0) * (z - z0s) - (x - x0) * (z1s - z0s) < 0:
            wn -= 1
    return wn


def _spans(segs, rows, r, z):
    """Inside intervals [xa, xb) along raster row `r`, nonzero fill rule."""
    xs = []
    for i in rows[r]:
        x0, z0s, x1, z1s = segs[i]
        if (z0s > z) != (z1s > z):
            s = (z - z0s) / (z1s - z0s)
            xs.append((x0 + s * (x1 - x0), 1 if z1s > z0s else -1))
    xs.sort()
    out, w, start = [], 0, 0.0
    for x, d in xs:
        if w == 0:
            start = x
        w += d
        if w == 0 and x > start:
            out.append((start, x))
    return out


def _grid(verts, cell_hint, max_cells):
    """(x0, z0, cell, ncols, nrows) over the mesh, coarsened to stay affordable."""
    xs = [v[0] for v in verts]
    zs = [v[2] for v in verts]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    cell = max(cell_hint, (x1 - x0) / max_cells, (z1 - z0) / max_cells)
    return (x0, z0, cell, max(1, int((x1 - x0) / cell) + 1),
            max(1, int((z1 - z0) / cell) + 1))


def _layer_ys(verts, layer_h, max_layers):
    """Layer mid-planes bottom-up, coarsened if there would be too many."""
    ys = [v[1] for v in verts]
    lo, hi = min(ys), max(ys)
    n = max(2, min(max_layers, int((hi - lo) / max(layer_h, 1e-9))))
    return [lo + (i + 0.5) * (hi - lo) / n for i in range(n)], (hi - lo) / n


# --------------------------------------------------------------------------
# 1. overhangs
# --------------------------------------------------------------------------

def overhang_report(verts, faces, up=UP, limit_deg=45.0, plate_tol=0.05,
                    exclude_buried=True, max_probe_planes=900):
    """Area-weighted census of unsupported overhangs.

    `angle` is the SURFACE's tilt away from the build axis: 0 for a vertical
    wall, 90 for a flat ceiling. For a downward face with outward unit normal n
    that is asin(-n.up). Unsupported means downward AND angle > limit_deg --
    the ordinary 45-degree FDM rule.

    (The brief phrased this as "normal more than limit_deg from straight-down",
    which is the inverse: a normal pointing straight down is a flat ceiling,
    the worst case, not the safest. The physical rule is implemented, and it is
    the one the brief's own "38.3 < 45, therefore fine" cross-check assumes.)

    Excluded, with reason:
      - faces within `plate_tol` of the lowest point: the build plate holds them;
      - buried faces (see module docstring). Requires up = +Y; pass
        exclude_buried=False to see the raw numbers.

    Burial is decided per triangle, at its centroid, so a large triangle that
    is only partly buried is kept or dropped whole. On a finely tessellated
    mesh that is noise; on a coarse one it is not.

    `total_area_mm2` counts every face, buried ones included, because the true
    exterior area of an un-unioned mesh is not computable here. So
    `unsupported_fraction` is a lower bound; `fraction_of_downward` is not.
    """
    L = math.sqrt(sum(c * c for c in up))
    ux, uy, uz = up[0] / L, up[1] / L, up[2] / L
    tris = _tris(verts, faces)
    total = sum(t[6] for t in tris)
    hmin = min(v[0] * ux + v[1] * uy + v[2] * uz for v in verts)
    buried_ok = exclude_buried and (ux, uy, uz) == (0.0, 1.0, 0.0)

    q, cands, worst_raw = 5e-4, [], 0.0
    for a, b, c, nx, ny, nz, area in tris:
        d = nx * ux + ny * uy + nz * uz
        if d >= -1e-9:
            continue
        ang = math.degrees(math.asin(min(1.0, -d)))
        worst_raw = max(worst_raw, ang)
        cx, cy, cz = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0,
                      (a[2] + b[2] + c[2]) / 3.0)
        if cx * ux + cy * uy + cz * uz - hmin <= plate_tol:
            continue
        # probe point: one small step along the outward normal, with the Y
        # snapped to a 0.5 um grid so that many faces share one exact plane
        cands.append((cx + nx * 3 * q, round((cy + ny * 3 * q) / q) * q,
                      cz + nz * 3 * q, ang, area))

    buried = 0
    if buried_ok and cands:
        x0, z0, cell, ncols, nrows = _grid(verts, 1.0, 64)
        by = sorted({c[1] for c in cands})
        exact = len(by) <= max_probe_planes
        if not exact:                       # pathological mesh: snap instead
            by, _ = _layer_ys(verts, 0.0, max_probe_planes)
        idx = {y: i for i, y in enumerate(by)}
        groups = [[] for _ in by]
        for i, cd in enumerate(cands):
            k = idx.get(cd[1])
            if k is None:                   # snapped mode: nearest plane
                k = min(range(len(by)), key=lambda j: abs(by[j] - cd[1]))
            groups[k].append(i)
        keep = [True] * len(cands)
        for k, (_y, segs, _s, rows) in enumerate(
                _sweep(tris, by, z0, cell, nrows)):
            for i in groups[k]:
                if _winding(segs, rows, z0, cell, nrows, cands[i][0],
                            cands[i][2]) != 0:
                    keep[i] = False
                    buried += 1
        cands = [cd for i, cd in enumerate(cands) if keep[i]]

    down = bad = worst = 0.0
    y_lo = y_hi = None
    for cx, cy, cz, ang, area in cands:
        down += area
        if ang > limit_deg:
            bad += area
            worst = max(worst, ang)
            y_lo = cy if y_lo is None else min(y_lo, cy)
            y_hi = cy if y_hi is None else max(y_hi, cy)
    return {
        "total_area_mm2": total,
        "exterior_downward_area_mm2": down,
        "unsupported_area_mm2": bad,
        "unsupported_fraction": bad / total if total else 0.0,
        "fraction_of_downward": bad / down if down else 0.0,
        "worst_deg": max((c[3] for c in cands), default=0.0),
        "worst_unsupported_deg": worst,
        "worst_deg_including_buried": worst_raw,
        "unsupported_y_range": (y_lo, y_hi),
        "limit_deg": limit_deg,
        "buried_faces_dropped": buried,
        "winding_was_inverted": outward_sign(verts, faces) < 0,
    }


# --------------------------------------------------------------------------
# 2. minimum feature
# --------------------------------------------------------------------------

def min_feature_report(verts, faces, layer_h=0.2, nozzle=0.4, n_slices=32,
                       directions=18):
    """Narrowest cross-section feature over a sample of real layer planes.

    DOES. Takes the true layer grid (`layer_h`) and subsamples it to `n_slices`
    planes, always keeping the top and bottom layer -- the tip layer is the one
    that matters and a uniform sample misses it. On each plane the cut points
    are grouped by mesh shell and each shell's section is measured with
    `directions` calipers; the smallest projected extent is its width.

    CATCHES. A pillar tapering to a spike, a tip disc under one extrusion, a
    shell that has all but vanished between two layers.

    DOES NOT CATCH. (a) A waist WITHIN one shell: a caliper width is a convex
    hull measure, so a dumbbell or C-shaped section reads as its full width.
    (b) Anything between the sampled planes. (c) The width of the UNION where
    shells overlap -- only each shell's own outline is measured. (d) Sub-facet
    geometry, which is already absent from the mesh.

    NOT REPORTED, DELIBERATELY: nearest approach between two different shells.
    It was implemented and measured (0.002 to 0.045 mm over the eight configs
    in __main__) and it is pure artifact -- geom3d cones are REQUIRED to
    interpenetrate, so every "gap" was a cone-cone intersection curve where two
    boundaries touch by construction. The quantity is not well posed on an
    un-unioned mesh and no threshold rescues it.
    """
    tris = _tris(verts, faces)
    shell = _shells(verts, faces)
    _x0, z0, cell, _nc, nrows = _grid(verts, max(1.0, 2 * nozzle), 64)
    all_ys, step = _layer_ys(verts, layer_h, 10 ** 7)
    n = min(n_slices, len(all_ys))
    ys = [all_ys[round(i * (len(all_ys) - 1) / (n - 1))] for i in range(n)]
    cosines = [(math.cos(math.pi * d / directions),
                math.sin(math.pi * d / directions)) for d in range(directions)]

    best, best_y = float("inf"), None
    for y, segs, sids, _rows in _sweep(tris, ys, z0, cell, nrows, shell):
        pts = {}
        for s, sid in zip(segs, sids):
            pts.setdefault(sid, []).append((s[0], s[1]))
            pts[sid].append((s[2], s[3]))
        for ps in pts.values():
            if len(ps) < 3:
                continue
            for ca, sa in cosines:
                lo = hi = ps[0][0] * ca + ps[0][1] * sa
                for px, pz in ps:
                    v = px * ca + pz * sa
                    lo = v if v < lo else lo
                    hi = v if v > hi else hi
                if hi - lo < best:
                    best, best_y = hi - lo, y
    return {
        "min_width_mm": None if best == float("inf") else best,
        "min_width_y": best_y,
        "nozzle_mm": nozzle,
        "slices": len(ys),
        "layer_step_mm": step,
    }


# --------------------------------------------------------------------------
# 3. bridges and islands
# --------------------------------------------------------------------------

def bridge_report(verts, faces, layer_h=0.2, nozzle=0.4, max_layers=200,
                  max_grid=120):
    """Islands: solid at layer N with nothing under it at layer N-1.

    Each layer is rasterised from its oriented cross-section with the nonzero
    fill rule, which is exactly the union of the interpenetrating shells. Cells
    occupied at N and also at N-1 seed a flood fill through layer N's occupied
    cells; everything reached is supported, directly or through its own layer.
    What is left is being extruded onto air, which no amount of tuning prints.
    This is the check a sparse strut lattice fails.

    Layer count and grid pitch are both capped, and the values actually used
    come back in the result. BOTH caps can lie in BOTH directions, so check
    them before believing an answer:
      - a coarsened layer step compares against a plane further below than the
        real N-1, which invents islands; and it can skip the one layer where a
        real island existed before it merged, which hides them;
      - a coarsened grid cell drops any island smaller than one cell.
    `layer_step_is_requested` tells you whether the step was honoured;
    `grid_cell_mm` is the smallest island this run could possibly see.
    """
    tris = _tris(verts, faces)
    gx0, gz0, cell, ncols, nrows = _grid(verts, nozzle, max_grid)
    ys, step = _layer_ys(verts, layer_h, max_layers)

    islands = cells = 0
    first_y = None
    prev = None
    for y, segs, _s, rows in _sweep(tris, ys, gz0, cell, nrows):
        occ = [bytearray(ncols) for _ in range(nrows)]
        for r in range(nrows):
            row = occ[r]
            for xa, xb in _spans(segs, rows, r, gz0 + (r + 0.5) * cell):
                c0 = max(0, int(math.ceil((xa - gx0) / cell - 0.5)))
                c1 = min(ncols - 1, int((xb - gx0) / cell - 0.5))
                for c in range(c0, c1 + 1):
                    row[c] = 1
        if prev is not None:
            seen = [bytearray(ncols) for _ in range(nrows)]
            q = deque()
            for r in range(nrows):
                o, p, s = occ[r], prev[r], seen[r]
                for c in range(ncols):
                    if o[c] and p[c]:
                        s[c] = 1
                        q.append((r, c))
            while q:
                r, c = q.popleft()
                for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if 0 <= rr < nrows and 0 <= cc < ncols \
                            and occ[rr][cc] and not seen[rr][cc]:
                        seen[rr][cc] = 1
                        q.append((rr, cc))
            for r in range(nrows):
                for c in range(ncols):
                    if occ[r][c] and not seen[r][c]:
                        islands += 1
                        first_y = y if first_y is None else first_y
                        seen[r][c] = 1
                        q.append((r, c))
                        while q:
                            rr, cc = q.popleft()
                            cells += 1
                            for r2, c2 in ((rr + 1, cc), (rr - 1, cc),
                                           (rr, cc + 1), (rr, cc - 1)):
                                if 0 <= r2 < nrows and 0 <= c2 < ncols \
                                        and occ[r2][c2] and not seen[r2][c2]:
                                    seen[r2][c2] = 1
                                    q.append((r2, c2))
        prev = occ
    return {
        "islands": islands,
        "island_area_mm2": cells * cell * cell,
        "first_island_y": first_y,
        "layers": len(ys),
        "layer_step_mm": step,
        "layer_step_is_requested": abs(step - layer_h) < 1e-9,
        "grid_cell_mm": cell,
        "grid": (ncols, nrows),
    }


# --------------------------------------------------------------------------
# 4. verdict
# --------------------------------------------------------------------------

def verdict(verts, faces, up=UP, limit_deg=45.0, layer_h=0.2, nozzle=0.4,
            n_slices=32, max_layers=200, max_grid=120,
            max_unsupported_fraction=0.001):
    """The three reports plus `printable` and human-readable `reasons`.

    `reasons` always explains the call, pass or fail; a bare False tells nobody
    what to change.
    """
    oh = overhang_report(verts, faces, up, limit_deg)
    mf = min_feature_report(verts, faces, layer_h, nozzle, n_slices)
    br = bridge_report(verts, faces, layer_h, nozzle, max_layers, max_grid)
    reasons, ok = [], True

    if oh["unsupported_fraction"] > max_unsupported_fraction:
        ok = False
        lo, hi = oh["unsupported_y_range"]
        reasons.append(
            "%.3f%% of surface area overhangs past %.0f deg (worst %.1f deg), "
            "y = %.2f..%.2f mm" % (100 * oh["unsupported_fraction"], limit_deg,
                                   oh["worst_unsupported_deg"], lo, hi))
    else:
        reasons.append("overhangs OK: steepest exterior downward face %.1f deg "
                       "from the build axis, limit %.0f"
                       % (oh["worst_deg"], limit_deg))

    w = mf["min_width_mm"]
    if w is None:
        reasons.append("no cross-section found -- empty or degenerate mesh")
        ok = False
    elif w < nozzle:
        ok = False
        reasons.append("thinnest cross-section %.3f mm at y = %.2f is under one "
                       "%.1f mm extrusion" % (w, mf["min_width_y"], nozzle))
    elif w < 2 * nozzle:
        reasons.append("thinnest cross-section %.3f mm at y = %.2f is a single "
                       "extrusion wide: printable, zero margin"
                       % (w, mf["min_width_y"]))
    else:
        reasons.append("thinnest cross-section %.3f mm at y = %.2f, over the "
                       "%.1f mm nozzle" % (w, mf["min_width_y"], nozzle))

    if br["islands"]:
        ok = False
        reasons.append("%d island(s), %.2f mm2, first at y = %.2f: material "
                       "extruded onto air"
                       % (br["islands"], br["island_area_mm2"],
                          br["first_island_y"]))
    else:
        reasons.append("no islands over %d layers at %.3f mm"
                       % (br["layers"], br["layer_step_mm"]))

    if oh["winding_was_inverted"]:
        reasons.append("note: mesh winding is inverted; flipped before analysis")
    if oh["buried_faces_dropped"]:
        reasons.append("note: %d buried interior faces dropped (un-unioned mesh)"
                       % oh["buried_faces_dropped"])
    if not br["layer_step_is_requested"]:
        reasons.append("note: layer step coarsened to %.3f mm (asked %.3f) to "
                       "cap the raster at %d layers"
                       % (br["layer_step_mm"], layer_h, br["layers"]))
    return {"printable": ok, "reasons": reasons,
            "overhang": oh, "min_feature": mf, "bridge": br}


# --------------------------------------------------------------------------

if __name__ == "__main__":
    import os
    import sys
    import time
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from geom3d import Cone3DParams, build_mesh, cavity_radius, _cone_verts

    HSEG = 32          # NOT geom3d's default of 3; see the cross-check below

    def coupon(pitch, depth, lip, hseg=HSEG):
        return Cone3DParams(face_w=2.5 * pitch, face_h=2.5 * pitch, depth=depth,
                            pitch=pitch, profile_lip=lip, height_seg=hseg,
                            margin_depths=0.0, centre_margin_pitches=0.5)

    def pillar(pitch, depth, lip, hseg=HSEG, nseg=32):
        """One isolated cone: the flank profile with nothing else in the way."""
        p = Cone3DParams(pitch=pitch, depth=depth, profile_lip=lip)
        v, f = [], []
        _cone_verts(v, f, 0.0, 0.0, depth,
                    p.effective_overlap() * pitch / 2.0, p.tip_radius, 0.0,
                    nseg, hseg, lip=lip, lip_at=p.profile_lip_at)
        return v, f

    print("FDM face-up printability: 0.4 mm nozzle, no support, 45 deg limit")
    print("coupons 2.5 x 2.5 pitches, height_seg = %d, layer 0.2 mm\n" % HSEG)
    hdr = ("  lip pitch depth |  faces  worstOH  unsup%  unsupported y   "
           "minWidth   isl | printable")
    print(hdr + "\n" + "-" * len(hdr))
    for lip in (0.0, 0.35):
        for pitch in (3.75, 11.0):
            for depth in (20.0, 50.0):
                v, f = build_mesh(coupon(pitch, depth, lip))
                t = time.time()
                r = verdict(v, f)
                oh, mf, br = r["overhang"], r["min_feature"], r["bridge"]
                lo, hi = oh["unsupported_y_range"]
                print("%5.2f %5.2f %5.1f | %6d %7.1f %7.3f %s %8.3f %5d | %s"
                      % (lip, pitch, depth, len(f), oh["worst_deg"],
                         100 * oh["unsupported_fraction"],
                         "%7.2f..%-6.2f" % (lo, hi) if lo is not None
                         else "      --       ",
                         mf["min_width_mm"], br["islands"], r["printable"]))
                print("      [%4.1fs] %s" % (time.time() - t,
                                             "; ".join(r["reasons"][:3])))

    # ---- the geometry that is actually exported and printed ---------------
    print("\nThe real thing: export_cone.py's shipped coupon "
          "(d30 p7.5, tip 0.2, radial 24, height_seg 3, tileable)")
    ep = Cone3DParams(face_w=100, face_h=100, depth=30.0, pitch=7.5,
                      tip_radius=0.2, jitter=0.30, radial_seg=24, height_seg=3,
                      margin_depths=0.0, centre_margin_pitches=1.0,
                      backing=3.0, tileable=True)
    v, f = build_mesh(ep)
    t = time.time()
    r = verdict(v, f)
    print("  %d faces, %.1fs -> printable = %s" % (len(f), time.time() - t,
                                                   r["printable"]))
    for s in r["reasons"]:
        print("    - " + s)

    # ---- what the unsupported band at y = -depth actually is --------------
    print("""
THAT OVERHANG IS REAL AND IT IS ALWAYS AT y = -depth: the base discs of the
cones on the OUTER EDGE of the field, hanging off the edge of the backing slab.
build_mesh admits a centre anywhere in [-mx, face_w+mx] and then builds the slab
over exactly [-mx, face_w+mx], mx = max(margin_depths*depth,
centre_margin_pitches*pitch) + R -- so a centre at the limit puts half its base
disc, radius R, past the slab edge. Measured on the pitch-11 depth-20 coupon: of
640 base triangles 554 sit fully on the slab, 86 poke off, 46 have their
centroid off and survive the buried filter = 347 mm2 of flat 90-degree ceiling
over air. It is in the shipped export too. The fix is one term: the slab wants
mx + R. Until then these coupons need support at the border or a border trim,
and any "printable" claim covers the interior only.""")

    # ---- cross-check: the profile slope, on one isolated pillar -----------
    print("\n" + "=" * 74)
    print("CROSS-CHECK. Brief: at lip 0.35, pitch 11, depth 20 the worst")
    print("profile slope is 38.3 deg from vertical. One isolated pillar, so")
    print("neither the slab nor the neighbours can mask the flank:")
    for hseg in (3, 8, 16, 32, 64, 128):
        v, f = pillar(11.0, 20.0, 0.35, hseg)
        oh = overhang_report(v, f, limit_deg=0.0, exclude_buried=False)
        print("   height_seg %3d -> worst downward flank %6.2f deg" %
              (hseg, oh["worst_deg"]))
    p = coupon(11.0, 20.0, 0.35)
    R = p.effective_overlap() * p.pitch / 2.0
    N, prev, worst = 200000, None, 0.0
    for i in range(N + 1):
        fr = i / N
        rr = p.tip_radius + (R - p.tip_radius) * cavity_radius(
            fr, p.profile_power, p.profile_bulge, p.profile_lip,
            p.profile_lip_at)
        yy = -p.depth * fr
        if prev and rr < prev[0]:
            worst = max(worst,
                        math.degrees(math.atan2(prev[0] - rr, prev[1] - yy)))
        prev = (rr, yy)
    print("   analytic continuum, R = %.2f mm (%.2f x pitch/2)  %6.2f deg"
          % (R, p.effective_overlap(), worst))
    print("""
   THIS DISAGREES, AND IT IS NOT THE CHECKER. The mesh converges to 32.0 deg
   and the continuous profile it samples is 32.24, so the checker reproduces
   the geometry to 0.2 deg. The brief's 38.3 is 6.1 deg steeper than what
   geom3d builds. Best reconstruction: 38.3 needs a base radius near 10.53 mm,
   where effective_overlap() gives 8.80 (overlap 1.15 raised to 1.60 by jitter
   0.30); assume instead a base radius of the full pitch (overlap 2.0,
   R = 11.0) and the same profile yields 38.5 deg. So the likely error is a
   base-radius assumption, not the lip. The CONCLUSION survives either way --
   32.2 and 38.3 are both under 45 -- but the number needs correcting before
   it is quoted again.

   SEPARATELY, AND WORSE. At geom3d's default height_seg = 3, which is what
   export_cone.py ships, the worst flank overhang is 0.00 deg: four rings at
   f = 0, 1/3, 2/3, 1 straddle the lip bump and never sample its far side, so
   the exported solid has NO undercut at all. It is not the profile that was
   designed. Any profile_lip claim, optical or printable, needs
   height_seg >= 16.""")
