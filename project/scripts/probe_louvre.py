"""Phase 10.4 — split the one big pane into several small ones.

User's question (2026-08-19): one 733 mm plate is awkward to carry and to
mount. Can it be several small panes?

The mirror law found in 10.3 (obs = -(beam + 2*tilt)) depends ONLY on tilt,
so N panes at the same tilt should send their specular branch exactly where
one pane does. If that holds, splitting is optically free -- and a LOUVRE
stack (panes staggered like a venetian blind) also collapses the projection
depth from H*sin(tilt) to (H/N)*sin(tilt): 310 mm becomes ~80 mm at N = 4.

Three builds, all AR glass n=1.49, tilt 25, same total aperture 733 x 60:
  S1  one pane, 733 long                     (the incumbent)
  L4  four louvre panes of 183, staggered, 8 mm gaps
  L4F same louvres but with a BRIGHT frame bar (rho 0.5 diffuse) at each
      joint -- the failure mode to look for: mullions are flat surfaces
      facing the room, the same disease as the hollow pyramid's rim

PRE-REGISTERED:
  P1  S1 and L4 agree cell-by-cell within noise: splitting is free.
  P2  L4 gaps do NOT leak to the audience (light through a gap continues
      into the trap).
  P3  L4F lights up: >= one audience cell above the flat-Musou level. If so,
      the build rule is "frames must be black and recessed behind the glass".
"""
import os, sys, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, blender_render as BR                                # noqa: E402
from geom_floor import FloorParams                              # noqa: E402
from probe_fresnel import make_glass, black_surroundings        # noqa: E402

OUT = "/tmp/simsrv/louvre"; os.makedirs(OUT, exist_ok=True)
FACE, TILT, THICK = 60.0, 25.0, 3.0
PWIN = FloorParams(kind="pyramid", face_w=FACE, face_h=FACE, depth=22.0,
                   pitch=4.0, margin_depths=2.0)
SUNS = [0.0, 20.0, 40.0, -20.0]
OBS = [0.0, -10.0, -20.0]
t = math.radians(TILT)


def pane(z_top, length, name, black_edges=False):
    """One flat pane hinged at its top edge, tilted back by TILT."""
    v, f = [], []
    for (yy, zz) in ((0.0, 0.0), (-THICK, 0.0), (-THICK, -length), (0.0, -length)):
        # local (y, z) with z measured DOWN the slope from the hinge
        y = yy * math.cos(t) + zz * math.sin(t)
        z = z_top + (-yy * math.sin(t) + zz * math.cos(t))
        v += [(0.0, y, z), (FACE, y, z)]
    idx = [(0, 2, 4, 6), (1, 7, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4),
           (4, 5, 7, 6), (6, 7, 1, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], idx)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(make_glass("g_" + name))
    if black_edges:
        # the cut faces only: verts 0/1=front-top, 2/3=back-top,
        # 4/5=back-bottom, 6/7=front-bottom, so faces 0,1 are the x-ends and
        # faces 2,4 the top/bottom cut edges. Faces 3 (back) and 5 (front)
        # stay glass.
        ob.data.materials.append(BR.make_coating(
            "edge_" + name, roughness=0.30, body=BR.MUSOU_BODY,
            spec_scale=BR.MUSOU_SPEC_SCALE, ior=BR.MUSOU_IOR))
        for i in (0, 1, 2, 4):
            ob.data.polygons[i].material_index = 1
        ob.data.update()
    return ob


def bar(z_at, name, rho):
    """A frame bar at a joint: 10 mm square, facing the room."""
    m = BR.make_diffuse(name + "_m", rho)
    v = []
    for (yy, zz) in ((2.0, 5.0), (-8.0, 5.0), (-8.0, -5.0), (2.0, -5.0)):
        v += [(0.0, yy, z_at + zz), (FACE, yy, z_at + zz)]
    idx = [(0, 2, 4, 6), (1, 7, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4),
           (4, 5, 7, 6), (6, 7, 1, 0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], idx)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(m)


def build_single():
    pane(FACE / 2.0, FACE, "s1")


def build_louvre(frame_rho=None, black_edges=False):
    n, gap = 4, 1.0
    seg = (FACE - gap * (n - 1)) / n
    for i in range(n):
        z_top = FACE / 2.0 - i * (seg + gap)
        pane(z_top, seg, "l%d" % i, black_edges=black_edges)
        if frame_rho is not None and i:
            bar(z_top + gap / 2.0, "bar%d" % i, frame_rho)


def run(tag, builder):
    BR.clear_scene(); builder(); black_surroundings()
    BR.configure_cycles(192, True)
    w, _ = BR.measurement_windows(PWIN, FACE + BR.GAP, None)
    res = {}
    for sun in SUNS:
        for oe in OBS:
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(FACE / 2.0, 0.0, FACE * 1.4, 480, 220, elev_deg=oe)
            BR.set_world(0.0)
            BR.add_sun(sun, strength=1.0, angular_size_deg=0.5)
            nm = "%s_s%+03.0f_o%+03.0f" % (tag, sun, oe)
            exr = os.path.join(OUT, nm + ".exr")
            BR.render_to(exr, os.path.join(OUT, nm + ".png"))
            arr = BR.read_exr(exr, 480, 220)
            v = BR.window_stats(arr, BR.to_pixel_window(w))["mean"]
            res["s%+.0f_o%+.0f" % (sun, oe)] = v
            if v > 1e-6:
                print("[%s] sun %+3.0f obs %+3.0f  %.6f  <<" % (tag, sun, oe, v), flush=True)
    print("[%s] worst %.6f, hot %d/%d" % (tag, max(res.values()),
          sum(1 for x in res.values() if x > 1e-6), len(res)), flush=True)
    return res

r = {}
r["S1_one_pane"] = run("s1", build_single)
r["L4_louvre"] = run("l4", lambda: build_louvre(None))
r["L4F_bright_frames"] = run("l4f", lambda: build_louvre(0.5))
r["L4B_black_edges"] = run("l4b", lambda: build_louvre(None, black_edges=True))
r["S1_black_edges"] = run("s1b", lambda: pane(FACE / 2.0, FACE, "s1b",
                                              black_edges=True))
json.dump(r, open(os.path.join(OUT, "louvre_results.json"), "w"), indent=1)
print("@@DONE@@")
