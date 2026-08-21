"""Does any shipped design carry COINCIDENT surfaces the way the flat control did?

The depth-0 flat plate stacked 3.86 layers of geometry on one plane -- pyramid
tips and the backing's top face landing together. At rho = 1 that costs nothing
and still converges to 1.000, which is exactly why the energy check passed and
hid it; at a real 1 % coating every spurious bounce throws away 99 % of what
hits it. A honeycomb is the obvious place to look next, because adjacent cells
share walls and a field built by unioning cell solids gets each shared wall
twice.

Counting faces is not the test. Two coplanar faces only cost a bounce if a ray
that leaves one immediately lands on the other, so this shoots rays and
measures the GAP to the next surface along the same direction:

    hit the surface -> leave it along a direction in the OUTWARD hemisphere
    -> measure how far that outgoing ray travels before it hits something

FIRST VERSION OF THIS TEST WAS WRONG and said so: it continued along the
INCOMING ray past the hit, and the known-bad flat plate scored 0.00 %. Of course
it did -- a downward ray that has crossed y = 0 leaves every coincident face at
y = 0 behind it. Coincident geometry costs nothing on the way IN. It costs on
the way OUT: the reflected ray leaves the surface and lands instantly on the
face sitting on top of it, and that bounce is thrown away. The test has to
follow the light that is trying to leave.

Two controls, so the number has a scale:
  flat depth 0      known bad -- 3.86 layers on y = 0, measured
  pyramid depth 20  known clean -- 22.09 mm2 on y = 0, all of it tip flats

PRE-REGISTERED:
  C1  flat depth 0 shows a large coincident fraction. If it does not, the test
      cannot see the defect it was written for and nothing below means anything.
  C2  pyramid depth 20 shows ~0.
  C3  honeycomb shows ~0 too. The cell walls are built as a single field, not
      as unioned per-cell solids -- but that is a belief about the builder, and
      the walls are the one place a union would show, so it is worth a number.
  C4  the stack (comb over a pyramid floor) is the highest risk of the three:
      two modules meet at the layer boundary, and the comb's cell floor sits
      exactly at y = -top_depth, which is where the floor module puts its top.
      That plane already caused one bug -- the floor-coating split missed faces
      lying exactly on it.
"""
import os, sys, json, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy                      # noqa: E402
import rig_v2 as R2             # noqa: E402
from mathutils import Vector    # noqa: E402

STEP = 1e-4      # mm to step past a hit before casting again
TOL = 1e-3       # mm: closer than this and the two surfaces are coincident
NRAY = 4000

CASES = [
    ("평판 깊이0 (아는 불량)", dict(kind="pyramid", pitch=4.0, depth=0.0,
                                  tip_flat=0.0), 100.0),
    ("피라미드 깊이20 (아는 정상)", dict(kind="pyramid", pitch=4.0, depth=20.0,
                                      tip_flat=0.1), 100.0),
    ("벌집 간격6 깊이50", dict(topology="honeycomb", pitch=6.0, depth=50.0,
                             wall_top=0.08, wall_bot=0.08, jitter=0.0), 60.0),
    ("벌집 간격6 깊이10", dict(topology="honeycomb", pitch=6.0, depth=10.0,
                             wall_top=0.08, wall_bot=0.08, jitter=0.0), 60.0),
    ("벌집 간격3 깊이30", dict(topology="honeycomb", pitch=3.0, depth=30.0,
                             wall_top=0.08, wall_bot=0.08, jitter=0.0), 60.0),
]
STACKS = [
    ("벌집6/깊이50 위, 피라미드 바닥4", dict(top="honeycomb", top_depth=46.0,
        top_params={"pitch": 6.0}, bot="pyramid", bot_depth=4.0,
        bot_params={"pitch": 2.0}, seed=23), 60.0),
]


def probe(ob, lo, hi, face_w):
    """Hit the surface, then follow a ray trying to LEAVE it."""
    rng = random.Random(4)
    mw = ob.matrix_world
    inv = mw.inverted()
    hits = 0
    coincident = 0
    gaps = []
    tries = 0
    while hits < NRAY and tries < NRAY * 40:
        tries += 1
        # a point above the field, aimed down at a random tilt, so walls get
        # hit as well as floors -- a straight-down ray never sees a cell wall
        x = rng.uniform(0.0, face_w)
        z = rng.uniform(-face_w / 2.0, face_w / 2.0)
        th = math.radians(rng.uniform(0.0, 55.0))
        ph = rng.uniform(0.0, 2 * math.pi)
        d = Vector((math.sin(th) * math.cos(ph), -math.cos(th),
                    math.sin(th) * math.sin(ph))).normalized()
        o = Vector((x, hi + 5.0, z)) - d * 5.0
        ok, loc, nor, idx = ob.ray_cast(inv @ o, inv.to_3x3() @ d)
        if not ok:
            continue
        hits += 1
        # leave the surface the way scattered light does: a cosine-ish
        # direction in the hemisphere about the face normal, nudged off the
        # face first so the cast does not re-hit the face it started on
        n = nor.normalized()
        if n.dot(d) > 0:
            n = -n
        while True:
            u = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
            if u.length > 1e-6:
                break
        u.normalize()
        if u.dot(n) < 0:
            u = -u
        out = (u + n * 0.35).normalized()
        ok2, loc2, _, _ = ob.ray_cast(loc + n * STEP, out)
        if ok2:
            g = (loc2 - loc).length
            gaps.append(g)
            if g < TOL:
                coincident += 1
        else:
            gaps.append(float("inf"))
    gaps.sort()
    fin = [g for g in gaps if g != float("inf")]
    return {"rays": hits, "coincident": coincident,
            "frac": coincident / max(hits, 1),
            "escaped": sum(1 for g in gaps if g == float("inf")) / max(hits, 1),
            "median_gap": gaps[len(gaps) // 2] if gaps else None,
            "min_gap": fin[0] if fin else None}


def build_and_probe(params, face, label):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    prm = dict(params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    R2.build(prm, samples=16, lambert_rho=1.0)
    ob = bpy.data.objects["panel_mesh"]
    ys = [v.co.y for v in ob.data.vertices]
    r = probe(ob, min(ys), max(ys), face)
    r.update(label=label, faces=len(ob.data.polygons),
             verts=len(ob.data.vertices))
    return r


rows = []
print("면 위에서 1e-4 mm 나아간 뒤 다시 쏜다. 다음 면까지 1e-3 mm 미만이면 겹친 것.",
      flush=True)
print("\n%-30s %7s %8s %10s %10s %12s"
      % ("설계", "면수", "광선", "겹친비율", "빠져나감", "가운데간격mm"), flush=True)
for label, prm, face in CASES:
    try:
        r = build_and_probe(prm, face, label)
    except Exception as exc:
        print("%-30s 실패: %r" % (label, exc), flush=True)
        continue
    rows.append(r)
    print("%-30s %7d %8d %9.2f%% %9.1f%% %12s"
          % (label, r["faces"], r["rays"], 100 * r["frac"],
             100 * r["escaped"],
             ("%.5f" % r["median_gap"]) if r["median_gap"] not in (None, float("inf"))
             else "빠져나감"), flush=True)
for label, prm, face in STACKS:
    try:
        r = build_and_probe(prm, face, label)
    except Exception as exc:
        print("%-30s 실패: %r" % (label, exc), flush=True)
        continue
    rows.append(r)
    print("%-30s %7d %8d %9.2f%% %9.1f%% %12s"
          % (label, r["faces"], r["rays"], 100 * r["frac"],
             100 * r["escaped"],
             ("%.5f" % r["median_gap"]) if r["median_gap"] not in (None, float("inf"))
             else "빠져나감"), flush=True)

os.makedirs("/tmp/simsrv/coincident", exist_ok=True)
json.dump(rows, open("/tmp/simsrv/coincident/coincident.json", "w"), indent=1)
ctrl = [r for r in rows if "아는 불량" in r["label"]]
if ctrl and ctrl[0]["frac"] < 0.05:
    print("\n**기준 불량품이 겹침을 안 보인다 -- 이 시험은 아무 말도 못 한다**",
          flush=True)
print("\n@@DONE@@", flush=True)
