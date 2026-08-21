"""Is the geometry we BUILD fit to trace light through?

We are not importing CAD. We generate every panel from our own code, which is
exactly why nothing checks it: an imported model at least passes through a
translator that reports errors, ours goes from `geom_*.build_mesh` straight
into Cycles. The one honest diagnostic in the project -- `weld_and_close`, with
its Euler count and open-edge count -- runs only when someone clicks Export
STEP, and writes its verdict into a file header nobody reads.

The industry rule for optical ray tracing is blunt: a valid watertight solid,
no internal faces, and solids that touch or overlap must be Booleaned into one
before use, because a non-watertight mesh sends rays through the holes and
those rays are counted as errors [Ansys Speos / TracePro CAD-import guidance].
ISO 10303-59 is the standard that names the defect classes; STEP's geometric
validation properties are the standard way to check a transferred model, at
CAx-IF thresholds of under 1 % deviation in volume and area to pass.

THE FIRST VERSION OF THIS CHECK WAS WRONG, and its own control said so twice.

  1. A ray probe followed the INCOMING ray past the hit. The known-bad plate
     scored 0.00 %. Of course: a downward ray that has crossed y = 0 leaves
     every coincident face at y = 0 behind it.
  2. The plane grouping keyed on abs(nx), abs(ny), abs(nz) and abs(offset).
     That merges four distinct orientations into one bucket and both sides of
     a symmetric panel into one plane. A honeycomb's walls sit at +-60 degrees,
     so they landed in one bucket and the panel scored "4.4 layers" -- an
     artifact of the key, not a property of the mesh.

  3. Even with a correct plane key, counting ALL stacked planes failed the
     clean control: a pyramid field at depth 20 reported 1.92 layers over
     14.5 % of its area. That stacking is real -- the field's base sits on the
     backing slab's top face -- and it is also irrelevant, because it is
     buried inside the material where no photon goes.

So the plane key here is CANONICAL: flip the normal so its first significant
component is positive, and keep the offset signed. And stacking is counted
only among faces LIGHT CAN REACH, found by tracing rays in from outside and
letting them bounce, because a defect a photon never meets is not a defect.
The whole thing is validated on two controls before any number is quoted.
"""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy                     # noqa: E402
import rig_v2 as R2            # noqa: E402
import numpy as np             # noqa: E402

TOL = 1e-3


def plane_key(n, v0):
    """Canonical (normal, signed offset). Two faces share a key only if they
    lie in the same plane with the same orientation up to a flip."""
    x, y, z = n
    for c in (x, y, z):
        if abs(c) > 1e-6:
            if c < 0:
                x, y, z = -x, -y, -z
            break
    d = x * v0[0] + y * v0[1] + z * v0[2]
    return (round(x, 4), round(y, 4), round(z, 4), round(d, 3))


def edge_report(me):
    """Open and non-manifold edges, and the Euler characteristic."""
    cnt = {}
    for pl in me.polygons:
        vs = list(pl.vertices)
        for i in range(len(vs)):
            e = (vs[i], vs[(i + 1) % len(vs)])
            cnt[(min(e), max(e))] = cnt.get((min(e), max(e)), 0) + 1
    openv = sum(1 for c in cnt.values() if c == 1)
    nonm = sum(1 for c in cnt.values() if c > 2)
    V, E, F = len(me.vertices), len(cnt), len(me.polygons)
    return openv, nonm, V - E + F


def duplicate_faces(me):
    """Faces whose vertex COORDINATES coincide -- the repairable overlap."""
    V = [(round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
         for v in me.vertices]
    seen, dup = {}, []
    for pl in me.polygons:
        k = tuple(sorted(V[i] for i in pl.vertices))
        if k in seen:
            dup.append(pl.index)
        else:
            seen[k] = pl.index
    return dup


def reachable_faces(ob, face_w, nray=6000, bounces=6, seed=7):
    """Which faces can light actually touch?

    Fire rays in from above at every tilt, then let each one scatter and carry
    on, so a face at the bottom of a cell is reached the way a photon reaches
    it. Faces never hit are interior -- the base of the field against the
    backing slab, the underside of a slab -- and a stack of geometry down there
    costs nothing.
    """
    import random
    from mathutils import Vector
    rng = random.Random(seed)
    ys = [v.co.y for v in ob.data.vertices]
    hi = max(ys)
    seen = set()
    for _ in range(nray):
        x = rng.uniform(0.0, face_w)
        z = rng.uniform(-face_w / 2.0, face_w / 2.0)
        th = math.radians(rng.uniform(0.0, 75.0))
        ph = rng.uniform(0.0, 2 * math.pi)
        d = Vector((math.sin(th) * math.cos(ph), -math.cos(th),
                    math.sin(th) * math.sin(ph))).normalized()
        o = Vector((x, hi + 5.0, z)) - d * 5.0
        for _b in range(bounces):
            ok, loc, nor, idx = ob.ray_cast(o, d)
            if not ok:
                break
            seen.add(idx)
            n = nor.normalized()
            if n.dot(d) > 0:
                n = -n
            u = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
            if u.length < 1e-6:
                break
            u.normalize()
            if u.dot(n) < 0:
                u = -u
            d = (u + n * 0.4).normalized()
            o = loc + n * 1e-4
    return seen


def stacked_planes(me, keep=None, cell=0.2, min_layers=1.5):
    """Per plane: summed face area over the footprint it covers. 1.0 = one
    layer. Anything above ~1 means two sheets of geometry in the same place."""
    V = [(v.co.x, v.co.y, v.co.z) for v in me.vertices]
    buckets = {}
    for pl in me.polygons:
        if keep is not None and pl.index not in keep:
            continue
        n = pl.normal
        if n.length < 1e-9:
            continue
        n = n.normalized()
        k = plane_key((n.x, n.y, n.z), V[pl.vertices[0]])
        buckets.setdefault(k, []).append(pl.index)
    worst = (0.0, None, 0, 0.0)
    total_stacked = 0.0
    for k, idx in buckets.items():
        area = sum(me.polygons[i].area for i in idx)
        if area < 1.0 or len(idx) < 2:
            continue
        nx, ny, nz, _ = k
        ax = [0, 1, 2]
        ax.remove(int(np.argmax([abs(nx), abs(ny), abs(nz)])))
        pts = np.array([[V[i][ax[0]], V[i][ax[1]]]
                        for j in idx for i in me.polygons[j].vertices])
        lo, hi = pts.min(0), pts.max(0)
        gx = max(2, int((hi[0] - lo[0]) / cell))
        gy = max(2, int((hi[1] - lo[1]) / cell))
        if gx * gy > 8_000_000:
            continue
        g = np.zeros((gx, gy), bool)
        for j in idx:
            q = np.array([[V[i][ax[0]], V[i][ax[1]]]
                          for i in me.polygons[j].vertices])
            a = np.clip(((q.min(0) - lo) / cell).astype(int), 0, [gx - 1, gy - 1])
            b = np.clip(((q.max(0) - lo) / cell).astype(int) + 1, 0, [gx, gy])
            g[a[0]:b[0], a[1]:b[1]] = True
        foot = g.sum() * cell * cell
        r = area / max(foot, 1e-9)
        if r >= min_layers:
            total_stacked += area
        if r > worst[0]:
            worst = (r, k, len(idx), area)
    return worst, total_stacked


def check(label, params, face):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    prm = dict(params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    R2.build(prm, samples=16, lambert_rho=1.0)
    ob = bpy.data.objects["panel_mesh"]
    me = ob.data
    openv, nonm, euler = edge_report(me)
    dup = duplicate_faces(me)
    reach = reachable_faces(ob, face)
    (r, k, nf, area), stacked = stacked_planes(me, keep=reach)
    tot = sum(me.polygons[i].area for i in reach) if reach else 1e-9
    return {"label": label, "faces": len(me.polygons), "verts": len(me.vertices),
            "open_edges": openv, "nonmanifold_edges": nonm, "euler": euler,
            "dup_faces": len(dup),
            "dup_area_pct": 100 * sum(me.polygons[i].area for i in dup) / max(tot, 1e-9),
            "reachable_faces": len(reach),
            "worst_layers": r, "worst_plane": list(k) if k else None,
            "stacked_area_pct": 100 * stacked / max(tot, 1e-9)}


CONTROLS = [
    ("평판 깊이0 (겹침 있는 것으로 확인됨)",
     dict(kind="pyramid", pitch=4.0, depth=0.0, tip_flat=0.0), 100.0, True),
    ("피라미드 깊이20 (깨끗한 것으로 확인됨)",
     dict(kind="pyramid", pitch=4.0, depth=20.0, tip_flat=0.1), 100.0, False),
]
DESIGNS = [
    ("피라미드 간격4 깊이22", dict(kind="pyramid", pitch=4.0, depth=22.0,
                                tip_flat=0.4), 100.0),
    ("벌집 간격6 깊이50", dict(topology="honeycomb", pitch=6.0, depth=50.0,
                            wall_top=0.08, wall_bot=0.08, jitter=0.0), 60.0),
    ("벌집 간격6 깊이10", dict(topology="honeycomb", pitch=6.0, depth=10.0,
                            wall_top=0.08, wall_bot=0.08, jitter=0.0), 60.0),
    ("벌집 간격3 깊이30", dict(topology="honeycomb", pitch=3.0, depth=30.0,
                            wall_top=0.08, wall_bot=0.08, jitter=0.0), 60.0),
]

HDR = ("%-34s %7s %8s %7s %8s %9s %9s"
       % ("설계", "면수", "빛닿는면", "열린모서리", "똑같은면", "가장겹침", "겹친면적%"))


def show(r):
    print("%-34s %7d %8d %7d %8d %9.2f %9.1f"
          % (r["label"], r["faces"], r["reachable_faces"], r["open_edges"],
             r["dup_faces"], r["worst_layers"], r["stacked_area_pct"]),
          flush=True)


print("먼저 아는 답 두 개로 검사기를 검증한다. 못 맞히면 나머지 숫자는 못 믿는다.\n",
      flush=True)
print(HDR, flush=True)
rows = []
ok = True
for label, prm, face, should_stack in CONTROLS:
    r = check(label, prm, face)
    rows.append(r)
    show(r)
    if should_stack and r["worst_layers"] < 1.5:
        print("   ** 겹침이 있는 판을 깨끗하다고 했다 -- 검사기 불합격 **", flush=True)
        ok = False
    if not should_stack and r["worst_layers"] >= 1.5:
        print("   ** 깨끗한 판을 겹쳤다고 했다 -- 검사기 불합격 **", flush=True)
        ok = False
if not ok:
    print("\n검사기가 기준을 못 맞혔다. 아래 숫자는 발표하지 않는다.", flush=True)
else:
    print("\n검사기 합격. 이제 실제 설계들:\n", flush=True)
    print(HDR, flush=True)
    for label, prm, face in DESIGNS:
        try:
            r = check(label, prm, face)
        except Exception as exc:
            print("%-34s 실패: %r" % (label, exc), flush=True)
            continue
        rows.append(r)
        show(r)
os.makedirs("/tmp/simsrv/fitness", exist_ok=True)
json.dump(rows, open("/tmp/simsrv/fitness/model_fitness.json", "w"), indent=1,
          ensure_ascii=False)
print("\n@@DONE@@", flush=True)
