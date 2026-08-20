"""Primitives that cannot produce an ambiguous reflecting surface.

In an optical experiment the surface IS the experiment. A mesh where two faces
occupy the same place has no defined answer: the ray hits one or the other by
floating-point luck, and where their normals oppose, a specular material sends
part of the light backwards. A shell built by stacking overlapping slabs did
exactly that -- it agreed with the equivalent solid to 0.3 % under a pure
Lambertian and disagreed by 37 % under a pure specular, and the difference was
written up as physics.

Checking for that afterwards is the wrong repair. This module is the repair:
build through these primitives and the defect is not reachable.

THE INVARIANTS, enforced here rather than tested for later.

  1. **Every face is emitted once.** A shell is generated from ONE
     parametrisation in a single pass -- outer skin, inner skin and bore walls
     together -- so there is no second pass that could lay a face on top of an
     existing one.

  2. **Winding is consistent and outward.** Outer-skin quads are wound so their
     normal points along +n of the mid-surface; inner-skin quads are the same
     quads reversed. A bore wall inherits its winding from the cell edge it
     closes. Nothing depends on a caller getting a vertex order right.

  3. **Closed: every edge belongs to exactly two faces.** A material cell
     contributes an outer and an inner quad; wherever it meets a hole or the
     patch boundary, the pair is closed by a bore. `shell()` asserts this before
     returning, so a construction error is a build failure and not a number.

  4. **Solids may overlap, never touch exactly.** The union of closed solids is
     a legitimate way to build these panels -- a face buried in material is
     unreachable and harmless. A face that exactly touches another is NOT
     buried; it is on the surface, in the same place as its neighbour.
     `assert_no_exact_touch` is here for builders that place solids on a
     lattice, and `NUDGE` is the amount to overlap by when the design says
     "touching".

WHAT THIS DOES NOT DO. It does not check for self-intersection of the
mid-surface, and it does not stop a caller passing a patch that folds over
itself. Those are geometry errors in the design, not in the meshing.
"""

from __future__ import annotations

import math

# mm to overlap by where a design says two solids touch. 0.05, NOT 1e-3: the
# renderer traverses its BVH in float32, and at panel coordinates of ~160 mm a
# micron is ~80 ulps -- close enough to the traversal epsilon that grazing
# rays leak between solids joined at that scale. Measured: a shell whose parts
# overlapped by 1 um read 37 % dark under a glossy coating while a float64
# tracer found it ray-identical to the solid it replaced; the same geometry
# joined at 50 um is the experiment below this constant.
NUDGE = 0.05


# --- vector helpers ---------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    n = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-15 else (0.0, 1.0, 0.0)


def _add(a, b, s=1.0):
    return (a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s)


# --- the sheet primitive ----------------------------------------------------

def shell(patch, nu, nv, thickness, keep=None, verts=None, faces=None,
          check=True, offsets=None, emit=("out", "in", "bore")):
    """A closed sheet of `thickness` following the mid-surface `patch`.

    `patch(u, v) -> (x, y, z)` for u, v in [0, 1]; `keep(i, j)` selects the
    material cells. Perforation is which cells were never emitted, so no face
    can lie on another.

    HOW THE OFFSET IS COMPUTED, and why it is not a finite difference. The two
    skins are the mid-surface offset by +-thickness/2 along a vertex normal.
    Numerically differentiating `patch` for that normal put 5.8 degrees of tilt
    into a PLANAR face (the apex node has no derivative and fell back to a made-
    up axis), and even after patching that, skins carried ~0.02 degrees of
    noise. The literature method is exact where the surface is flat: build the
    mid-surface faces first, take their TRUE face normals, and give each vertex
    the ANGLE-WEIGHTED average of its incident face normals -- the
    angle-weighted pseudo-normal of Thuermer & Wuethrich (CG&A 1998), the same
    normal Baerentzen & Aanaes use for signed distance, and what a solidify
    operation offsets along. On a planar region every incident face normal is
    the plane normal, so the average IS the plane normal and the skin is
    offset exactly.

    Even thickness at creases: the offset distance is scaled by the inverse
    cosine between the vertex normal and each incident face normal (averaged),
    clamped at 3, so a 90-degree fold keeps its wall thickness instead of
    thinning.
    """
    if verts is None:
        verts = []
    if faces is None:
        faces = []
    base = len(verts)

    P = [[patch(i / nu, j / nv) for j in range(nv + 1)] for i in range(nu + 1)]

    def solid(i, j):
        if i < 0 or j < 0 or i >= nu or j >= nv:
            return False
        return True if keep is None else bool(keep(i, j))

    # reject hole patterns that join material only at a cell corner
    for i in range(nu - 1):
        for j in range(nv - 1):
            aa = solid(i, j)
            bb = solid(i + 1, j)
            cc = solid(i, j + 1)
            dd = solid(i + 1, j + 1)
            if aa and dd and not bb and not cc or                     bb and cc and not aa and not dd:
                raise ValueError(
                    "perforation pattern joins material only at the corner of "
                    "cells (%d,%d)-(%d,%d): a sheet cannot hang from a point"
                    % (i, j, i + 1, j + 1))

    # ---- mid-surface first: welded nodes, then faces with collapse handling
    node = {}
    nid = [[0] * (nv + 1) for _ in range(nu + 1)]
    pos = []
    for i in range(nu + 1):
        for j in range(nv + 1):
            key = tuple(int(round(c * 1e7)) for c in P[i][j])
            if key not in node:
                node[key] = len(pos)
                pos.append(P[i][j])
            nid[i][j] = node[key]

    mid = []                      # faces as tuples of node ids, outward wound
    for i in range(nu):
        for j in range(nv):
            if not solid(i, j):
                continue
            loop = []
            for q in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                k = nid[q[0]][q[1]]
                if not loop or loop[-1] != k:
                    loop.append(k)
            if len(loop) > 2 and loop[-1] == loop[0]:
                loop.pop()
            if len(loop) >= 3:
                mid.append(tuple(loop))

    # ---- exact face normals (Newell), then angle-weighted vertex normals
    fn = []
    for f in mid:
        nx = ny = nz = 0.0
        for k in range(len(f)):
            p0 = pos[f[k]]
            p1 = pos[f[(k + 1) % len(f)]]
            nx += (p0[1] - p1[1]) * (p0[2] + p1[2])
            ny += (p0[2] - p1[2]) * (p0[0] + p1[0])
            nz += (p0[0] - p1[0]) * (p0[1] + p1[1])
        fn.append(_norm((nx, ny, nz)))

    vn = [(0.0, 0.0, 0.0)] * len(pos)
    for fi, f in enumerate(mid):
        n = len(f)
        for k in range(n):
            a2 = pos[f[(k - 1) % n]]
            b2 = pos[f[k]]
            c2 = pos[f[(k + 1) % n]]
            e1 = _norm(_sub(a2, b2))
            e2 = _norm(_sub(c2, b2))
            dot = max(-1.0, min(1.0, sum(x * y for x, y in zip(e1, e2))))
            ang = math.acos(dot)
            v0 = vn[f[k]]
            vn[f[k]] = (v0[0] + fn[fi][0] * ang, v0[1] + fn[fi][1] * ang,
                        v0[2] + fn[fi][2] * ang)
    vn = [_norm(v) for v in vn]

    # even-thickness scale: mean sec(angle to incident faces), clamped
    acc = [[0.0, 0] for _ in pos]
    for fi, f in enumerate(mid):
        for k in f:
            d = sum(x * y for x, y in zip(vn[k], fn[fi]))
            acc[k][0] += max(abs(d), 1e-3)
            acc[k][1] += 1
    scale = []
    for c, t in acc:
        mean_cos = c / t if t else 1.0
        scale.append(min(3.0, 1.0 / mean_cos))

    # WHERE THE TWO SKINS SIT relative to the mid-surface. The default is
    # symmetric, +-t/2. `offsets=(0.0, -t)` puts the OUTER skin exactly on the
    # parametrised surface, which matters whenever that surface is the design:
    # a shell whose skins straddled the mid-surface had its outer envelope
    # 0.25 mm proud of the solid pyramid it was standing in for, with sheet
    # crossings at the hips and apex forming crevices -- invisible under a
    # diffuse coating (+0.8 %) and a 37 % light trap under a specular one. With
    # the outer skin ON the surface, everything else is inside the envelope and
    # the exterior is exactly the solid it replaces.
    if offsets is None:
        offsets = (thickness / 2.0, -thickness / 2.0)
    out_id = [0] * len(pos)
    in_id = [0] * len(pos)
    for k, p0 in enumerate(pos):
        # `offsets` may be a callable of the mid-surface point, for sheets
        # whose thickness must taper -- a shell inside a converging solid has
        # less room than the sheet is thick near the convergence, and a fixed
        # inner offset pokes through the opposite face there. The caller knows
        # its own geometry; the kernel just asks it.
        off_out, off_in = offsets(p0) if callable(offsets) else offsets
        out_id[k] = len(verts)
        verts.append(_add(p0, vn[k], off_out * scale[k]))
        in_id[k] = len(verts)
        verts.append(_add(p0, vn[k], off_in * scale[k]))

    # ---- skins and bores
    edge_use = {}
    for f in mid:
        n = len(f)
        for k in range(n):
            e = (f[k], f[(k + 1) % n])
            edge_use[tuple(sorted(e))] = edge_use.get(tuple(sorted(e)), 0) + 1

    # `emit` exists for DIAGNOSIS, not for building panels: it renders the
    # outer skin, inner skin and bores separately so a measured difference can
    # be pinned to a part of the sheet. A mesh missing any of the three is not
    # closed, so the closure check only runs when all three are emitted.
    for fi, f in enumerate(mid):
        if "out" in emit:
            faces.append(tuple(out_id[k] for k in f))
        if "in" in emit:
            faces.append(tuple(in_id[k] for k in reversed(f)))
        n = len(f)
        for k in range(n):
            a3, b3 = f[k], f[(k + 1) % n]
            if edge_use[tuple(sorted((a3, b3)))] == 1 and "bore" in emit:
                faces.append((out_id[a3], in_id[a3], in_id[b3], out_id[b3]))

    if set(emit) != {"out", "in", "bore"}:
        check = False

    if check:
        assert_closed(verts, faces, first=base,
                      what="shell(%dx%d, %d faces)" % (nu, nv, len(mid)))
    return verts, faces


# --- invariants -------------------------------------------------------------

def assert_closed(verts, faces, first=0, what="mesh"):
    """Every edge of the faces added since `first` must be used exactly twice."""
    import collections
    use = collections.Counter()
    for f in faces:
        if min(f) < first:
            continue
        n = len(f)
        for k in range(n):
            e = tuple(sorted((f[k], f[(k + 1) % n])))
            use[e] += 1
    bad = collections.Counter(v for v in use.values() if v != 2)
    if bad:
        raise AssertionError(
            "%s is not closed: %s"
            % (what, ", ".join("%d edges used %dx" % (c, u)
                               for u, c in sorted(bad.items()))))
    return True


def assert_no_exact_touch(verts, faces, quant=1e4, what="mesh"):
    """No two faces may occupy the same place.

    Solids that overlap are fine; solids that touch exactly are not, because
    the shared face is on the surface twice. Call this from any builder that
    lays closed solids on a lattice.
    """
    import collections
    seen = collections.Counter()
    for f in faces:
        pts = [verts[i] for i in f]
        c = tuple(int(round(sum(p[k] for p in pts) / len(pts) * quant))
                  for k in range(3))
        seen[c] += 1
    dup = sum(v - 1 for v in seen.values() if v > 1)
    if dup:
        raise AssertionError(
            "%s has %d face(s) sharing a position with another -- solids are "
            "touching exactly; overlap them by NUDGE instead" % (what, dup))
    return True


def slab(verts, faces, corners_top, corners_bot):
    """A closed hexahedron from four top and four bottom corners, wound out.

    The one place a box is built, so the winding is written once. `corners_*`
    are in order around the face; the top loop is seen from outside.
    """
    b = len(verts)
    verts.extend(list(corners_top) + list(corners_bot))
    faces.append((b, b + 1, b + 2, b + 3))
    faces.append((b + 7, b + 6, b + 5, b + 4))
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b + i, b + 4 + i, b + 4 + j, b + j))
    return verts, faces


def orient_outward(verts, faces):
    """Make every closed component's normals point out of its own volume.

    WHY THIS IS LOAD-BEARING, measured before it existed: the same pyramid
    field, same planes, same coating, read 0.00179 with inward normals and
    0.00112 with outward ones under a glossy coating at normal incidence --
    a 49 % swing from winding alone. The project's families disagreed
    (cone, shingle and the solid pyramid were wound inward; comb, wave,
    square outward), so every cross-family comparison under a specular
    coating mixed two different renderer behaviours. A ray tracer is
    validated for outward-wound opaque solids; that is the orientation
    every builder must hand it.

    Components are found by shared vertices; each is flipped independently
    if its signed volume is negative, so a mesh that mixes a correct slab
    with inverted solids comes out uniformly correct.
    """
    parent = list(range(len(verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for f in faces:
        r0 = find(f[0])
        for i in f[1:]:
            ri = find(i)
            if ri != r0:
                parent[ri] = r0
    vol = {}
    for f in faces:
        c = find(f[0])
        idx = list(f)
        for a in range(1, len(idx) - 1):
            p0, q, r = verts[idx[0]], verts[idx[a]], verts[idx[a + 1]]
            vol[c] = vol.get(c, 0.0) + (
                p0[0] * (q[1] * r[2] - q[2] * r[1])
                - p0[1] * (q[0] * r[2] - q[2] * r[0])
                + p0[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
    out = []
    for f in faces:
        if vol.get(find(f[0]), 0.0) < 0.0:
            out.append(tuple(reversed(f)))
        else:
            out.append(tuple(f))
    return verts, out


# --- depth bands -------------------------------------------------------------

def split_at_depth(verts, faces, slots, planes, bands):
    """Cut every face at each y = plane so none straddles a band boundary.

    Returns (verts, faces, slots) with each slot suffixed "@<band>", shallow
    band first. `planes` are y values in DESCENDING order (0 is the mouth,
    deeper is more negative); `bands` has len(planes) + 1 names.

    WHY CUTTING AND NOT LABELLING. "The paint reaches 10 mm" is not a partition
    of the faces. A honeycomb wall is ONE quad from y = 0 to y = -50, and a
    pyramid flank is one quad spanning its whole depth, so classifying a face
    by (say) its lowest vertex puts the entire flank in the deep band and
    returns roughly the bare number. Phase 9.2 measured paint reaching 2 / 5 /
    10 mm into a pyramid field of depth 20 and got 0.829 / 0.561 / 0.290 %; a
    labelling scheme cannot reproduce any of that. The polygon has to be cut.

    FOUR PROPERTIES THIS RELIES ON:

    1. `planes == []` IS THE IDENTITY -- the same list objects come back, no
       new vertices, no reindexing. Stated as an early return rather than left
       to emerge from the loop, because it is what lets an unbanded job stay
       bit-identical.
    2. A face wholly inside one band passes through UNTOUCHED, original vertex
       indices and all. Only straddling faces are rebuilt, which for a
       honeycomb at paint_depth 5 is one ring of side quads per cell.
    3. THE SHARED-EDGE ULP TRAP. Two neighbouring wall quads share an edge and
       traverse it in opposite directions, so t = da/(da-db) differs between
       them and `a + t*(b-a)` can land a fraction of a micron away from
       `b + t'*(a-b)`. This module's own opening records a 1 um join reading
       37 % dark under a glossy coating. Fixed twice over: the endpoints are
       ordered canonically before cutting so both faces solve the SAME
       equation, and the cut point's y is forced EXACTLY onto the plane rather
       than interpolated.
    4. Winding is preserved, so `orient_outward` need not be re-run.

    A single plane gives a hard paint line. Several give a staircase
    approximating a real spray fading with depth; the error against a linear
    ramp is bounded by (deep - shallow) / 2N.
    """
    if not planes:
        return verts, faces, slots
    if len(bands) != len(planes) + 1:
        raise ValueError("split_at_depth: %d planes needs %d band names, got %d"
                         % (len(planes), len(planes) + 1, len(bands)))
    ys = [float(y) for y in planes]
    if any(ys[i] <= ys[i + 1] for i in range(len(ys) - 1)):
        raise ValueError("split_at_depth: planes must descend, got %r" % (ys,))

    out_v = list(verts)
    cut_cache = {}

    def cut(ia, ib, y):
        """Index of the point where edge (ia, ib) meets y, memoised.

        The key is the SORTED index pair, so the two faces sharing this edge
        get the same vertex back rather than two that merely agree to within a
        rounding error.
        """
        key = (ia, ib, y) if ia < ib else (ib, ia, y)
        hit = cut_cache.get(key)
        if hit is not None:
            return hit
        a, b = out_v[key[0]], out_v[key[1]]
        da, db = a[1] - y, b[1] - y
        t = 0.0 if da == db else da / (da - db)
        out_v.append((a[0] + t * (b[0] - a[0]), y,        # y EXACT, not lerped
                      a[2] + t * (b[2] - a[2])))
        cut_cache[key] = len(out_v) - 1
        return cut_cache[key]

    def clip(poly, y, keep_above):
        """Sutherland-Hodgman against the half-space y >= / <= plane."""
        if not poly:
            return []
        res = []
        n = len(poly)
        for i in range(n):
            ia, ib = poly[i], poly[(i + 1) % n]
            ya, yb = out_v[ia][1], out_v[ib][1]
            ina = (ya >= y) if keep_above else (ya <= y)
            inb = (yb >= y) if keep_above else (yb <= y)
            if ina:
                res.append(ia)
            if ina != inb:
                res.append(cut(ia, ib, y))
        return res

    out_f, out_s = [], []
    for fi, face in enumerate(faces):
        base = slots[fi] if slots is not None else ""
        lo_y = min(out_v[i][1] for i in face)
        hi_y = max(out_v[i][1] for i in face)
        # which bands this face actually spans -- most touch exactly one
        first = next((k for k, y in enumerate(ys) if hi_y > y), len(ys))
        last = next((k for k, y in enumerate(ys) if lo_y >= y), len(ys))
        if first == last:
            out_f.append(face)                      # untouched, indices intact
            out_s.append("%s@%s" % (base, bands[first]) if base
                         else bands[first])
            continue
        for k in range(len(bands)):
            piece = list(face)
            if k > 0:
                piece = clip(piece, ys[k - 1], False)   # below the upper plane
            if k < len(ys):
                piece = clip(piece, ys[k], True)        # above the lower plane
            if len(piece) < 3:
                continue
            out_f.append(tuple(piece))
            out_s.append("%s@%s" % (base, bands[k]) if base else bands[k])
    return out_v, out_f, out_s
