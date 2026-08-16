"""Is this mesh a surface a photon can be traced against without ambiguity?

    python3 scripts/mesh_check.py            # every family, at its normal params

WHY. In an optical experiment the reflecting surface IS the experiment. If two
faces occupy the same place, a ray hits one or the other according to
floating-point luck, and where their normals oppose, a specular material sends
some rays backwards. The answer then depends on the mesh rather than on the
design.

That is not hypothetical. `geom_perf` built a pyramid shell by stacking 24
slab-shaped tiles per face; at zero open area the tiles touch exactly, burying
hundreds of thousands of coincident faces (12 011 faces for the solid pyramid
against 1 382 982 for the "same" shell). Measured with a pure Lambertian at
normal incidence the two agreed to 0.3 %. Measured with a pure SPECULAR coating
they differed by 37 %, and at 40 degrees by 67 % -- and that difference was
written up as a property of hollow shells. It was a property of the mesh.

WHAT IS CHECKED, and why each one matters to a ray:

  * **duplicate faces** -- the same triangle twice. The intersection is a coin
    toss between two surfaces that may have opposite normals.
  * **coincident faces** -- different triangles occupying the same plane and
    place. Same problem, and the usual result of two solids that touch exactly
    rather than overlapping.
  * **degenerate faces** -- zero area. Some intersectors return hits on them,
    some do not.
  * **edge use** -- every edge of a closed surface belongs to exactly two
    faces. An edge used once is a hole; used four times means two solids share
    it, which is the exact-touching case again.

THIS PROJECT'S CONVENTION IS FINE, AND THIS DOES NOT CONTRADICT IT.
`geom_topo` builds a union of closed solids and says "overlap is free: the union
is the geometry". True: a face buried inside solid material is unreachable and
harmless. What is NOT free is solids that touch EXACTLY, because then the buried
face is not buried -- it is on the surface, in the same place as another one.
Overlap by a real amount, or do not touch at all.
"""

import sys
import os
import math
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EPS = 1e-6


def _tris(verts, faces):
    out = []
    for f in faces:
        idx = list(f)
        for a in range(1, len(idx) - 1):
            out.append((idx[0], idx[a], idx[a + 1]))
    return out


def _area_normal(v, t):
    p, q, r = v[t[0]], v[t[1]], v[t[2]]
    u = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
    w = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
    n = (u[1] * w[2] - u[2] * w[1],
         u[2] * w[0] - u[0] * w[2],
         u[0] * w[1] - u[1] * w[0])
    a = 0.5 * math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
    return a, n


def check(verts, faces, name="mesh", quant=1e4):
    """Report the four defects. `quant` sets the grid coincidence is judged on."""
    tris = _tris(verts, faces)
    dup = collections.Counter()
    coin = collections.Counter()
    degen = 0
    edges = collections.Counter()

    def key(x):
        return int(round(x * quant))

    for t in tris:
        a, n = _area_normal(verts, t)
        if a < 1e-12:
            degen += 1
            continue
        dup[tuple(sorted(t))] += 1
        c = tuple(key(sum(verts[i][k] for i in t) / 3.0) for k in range(3))
        nl = math.sqrt(sum(q * q for q in n)) or 1.0
        # unsigned normal, so a face and its flipped twin count as coincident
        un = tuple(key(abs(q / nl)) for q in n)
        coin[(c, un, key(a))] += 1
        for i in range(3):
            e = tuple(sorted((t[i], t[(i + 1) % 3])))
            edges[e] += 1

    n_dup = sum(v - 1 for v in dup.values() if v > 1)
    n_coin = sum(v - 1 for v in coin.values() if v > 1)
    use = collections.Counter(edges.values())
    open_edges = use.get(1, 0)
    over_edges = sum(c for u, c in use.items() if u > 2)

    # ORIENTATION: signed volume per connected component must be positive.
    # Winding is invisible to every other number here and moved a glossy
    # measurement by 49 %; see geom_kit.orient_outward and FINDINGS_winding.md.
    parent=list(range(len(verts)))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for f in faces:
        r0=find(f[0])
        for i in f[1:]:
            ri=find(i)
            if ri!=r0: parent[ri]=r0
    volc = {}
    for t in tris:
        c=find(t[0])
        p0,q,r=verts[t[0]],verts[t[1]],verts[t[2]]
        volc[c]=volc.get(c,0.0)+(p0[0]*(q[1]*r[2]-q[2]*r[1])
            -p0[1]*(q[0]*r[2]-q[2]*r[0])+p0[2]*(q[0]*r[1]-q[1]*r[0]))/6.0
    inverted=sum(1 for v2 in volc.values() if v2 < -1e-9)

    return {"name": name, "tris": len(tris), "degenerate": degen,
            "inverted_components": inverted,
            "duplicate": n_dup, "coincident": n_coin,
            "open_edges": open_edges, "over_used_edges": over_edges,
            "clean": (degen == 0 and n_dup == 0 and n_coin == 0
                      and open_edges == 0 and over_edges == 0
                      and inverted == 0)}


def report(r):
    flags = []
    if r["degenerate"]:
        flags.append("%d degenerate" % r["degenerate"])
    if r["duplicate"]:
        flags.append("%d duplicate" % r["duplicate"])
    if r["coincident"]:
        flags.append("%d coincident" % r["coincident"])
    if r["open_edges"]:
        flags.append("%d open edges" % r["open_edges"])
    if r["over_used_edges"]:
        flags.append("%d edges used >2x" % r["over_used_edges"])
    if r.get("inverted_components"):
        flags.append("%d component(s) wound inward" % r["inverted_components"])
    print("  %-5s %-26s %9d tri   %s"
          % ("ok" if r["clean"] else "FAIL", r["name"], r["tris"],
             "clean" if r["clean"] else ", ".join(flags)))
    return r["clean"]


CASES = [
    ("geom_floor pyramid", "geom_floor", "FloorParams",
     dict(kind="pyramid", face_w=22.0, face_h=22.0, depth=50.0, pitch=5.5,
          tip_flat=0.0, margin_depths=0.0, backing=2.0)),
    ("geom_floor wave", "geom_floor", "FloorParams",
     dict(kind="wave", face_w=22.0, face_h=22.0, depth=50.0, pitch=5.5,
          margin_depths=0.0, backing=2.0, grid=6)),
    ("geom3d cone", "geom3d", "Cone3DParams",
     dict(face_w=22.0, face_h=22.0, depth=50.0, pitch=5.5, tip_radius=0.2,
          jitter=0.30, radial_seg=24, height_seg=12, margin_depths=0.0,
          backing=2.0, seed=23)),
    ("geom_topo comb", "geom_topo", "TopoParams",
     dict(topology="comb", face_w=22.0, face_h=22.0, depth=50.0, pitch=6.5,
          wall_top=0.08, wall_bot=0.08, jitter=0.0, margin_depths=0.0,
          backing=2.0, seed=23)),
    ("geom_topo shingle", "geom_topo", "TopoParams",
     dict(topology="shingle", face_w=22.0, face_h=22.0, depth=50.0, pitch=5.5,
          plate_t_top=0.05, plate_t_bot=0.05, tilt_deg=2.0, azimuth_mode="grid",
          jitter=0.30, plate_over=1.15, margin_depths=0.0, backing=2.0,
          seed=23)),
    ("geom_cell square", "geom_cell", "CellParams",
     dict(variant="square", face_w=22.0, face_h=22.0, depth=50.0, pitch=6.5,
          wall_top=0.1, wall_bot=0.1, margin_depths=0.0, backing=2.0,
          seed=23)),
    ("geom_perf solid skin", "geom_perf", "PerfParams",
     dict(face_w=22.0, face_h=22.0, depth=50.0, pitch=5.5, wall=0.5,
          hole_block=0, hole_period=0, nu=12, nv=24, margin_depths=0.0,
          backing=2.0)),
    ("geom_perf open 44", "geom_perf", "PerfParams",
     dict(face_w=22.0, face_h=22.0, depth=50.0, pitch=5.5, wall=0.5,
          hole_block=2, hole_period=3, nu=12, nv=24, margin_depths=0.0,
          backing=2.0)),
]


def main():
    print("=" * 74)
    print("MESH INTEGRITY — can a ray be traced against this without ambiguity?")
    print("=" * 74)
    bad = 0
    for name, mod, cls, prm in CASES:
        try:
            m = __import__(mod)
            v, f = m.build_mesh(getattr(m, cls)(**prm))
        except Exception as exc:
            print("  %-5s %-26s %s" % ("FAIL", name, str(exc)[:60]))
            bad += 1
            continue
        if not report(check(v, f, name)):
            bad += 1
    print("-" * 74)
    print("  %d of %d families have an unambiguous reflecting surface"
          % (len(CASES) - bad, len(CASES)))
    return bad


if __name__ == "__main__":
    sys.exit(min(main(), 120))
