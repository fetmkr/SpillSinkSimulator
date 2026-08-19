"""Phase 10.3 — how much tilt does the wedge plate need?

10.2 found every plate geometry returning the SAME audience value in one
cell (sun -20, obs -10): the audience-facing branch is the FLAT FRONT FACE's
specular reflection, which no back-face groove pattern can change. Only the
TILT moves it.

So sweep the tilt. Sun -40..+40 (negative = a beam arriving from BELOW the
horizon, e.g. bounced off the floor first), observer at and below eye level.

PRE-REGISTERED:
  T1  tilt 15: mirror cell at (sun -20, obs -10) stays hot; every positive
      sun stays dark.
  T2  tilt 25: the hot cell moves to a steeper observer (or leaves).
  T3  tilt 35 (the phase-8 hopper): no audience cell above 1e-6 at any sun.
  T4  the hot cell always satisfies obs ~= sun + 2*tilt (mirror arithmetic).
"""
import os, sys, math, json
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import bpy, blender_render as BR                                # noqa: E402
from geom_floor import FloorParams                              # noqa: E402
from probe_fresnel import black_surroundings                    # noqa: E402
import probe_fresnel2d as F2                                    # noqa: E402

OUT = "/tmp/simsrv/tiltsweep"; os.makedirs(OUT, exist_ok=True)
PWIN = FloorParams(kind="pyramid", face_w=60.0, face_h=60.0, depth=22.0,
                   pitch=4.0, margin_depths=2.0)
SUNS = [-40.0, -20.0, 0.0, 20.0, 40.0]
OBS = [0.0, -10.0, -20.0, -30.0]
TILTS = [15.0, 25.0, 35.0]

res = {}
for tilt in TILTS:
    F2.TILT = tilt
    BR.clear_scene()
    F2.plate_2d(hip=True)
    black_surroundings()
    BR.configure_cycles(192, True)
    w, _ = BR.measurement_windows(PWIN, 60.0 + BR.GAP, None)
    for sun in SUNS:
        for oe in OBS:
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(30.0, 0.0, 84.0, 480, 220, elev_deg=oe)
            BR.set_world(0.0)
            BR.add_sun(sun, strength=1.0, angular_size_deg=0.5)
            nm = "t%02.0f_s%+03.0f_o%+03.0f" % (tilt, sun, oe)
            exr = os.path.join(OUT, nm + ".exr")
            BR.render_to(exr, os.path.join(OUT, nm + ".png"))
            arr = BR.read_exr(exr, 480, 220)
            v = BR.window_stats(arr, BR.to_pixel_window(w))["mean"]
            res["t%.0f_s%+.0f_o%+.0f" % (tilt, sun, oe)] = v
            if v > 1e-6:
                print("[t%2.0f] sun %+3.0f obs %+3.0f  %.4f  <<" % (tilt, sun, oe, v), flush=True)
    hot = [k for k, x in res.items() if k.startswith("t%.0f_" % tilt) and x > 1e-6]
    print("[t%2.0f] hot cells: %d/%d %s" % (tilt, len(hot), len(SUNS)*len(OBS), hot), flush=True)
json.dump(res, open(os.path.join(OUT, "tilt_results.json"), "w"), indent=1)
print("@@DONE@@")
