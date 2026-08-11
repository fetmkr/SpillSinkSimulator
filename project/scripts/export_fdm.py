"""
STL export tuned for a 0.4 mm nozzle.

    Blender --background --factory-startup --python scripts/export_fdm.py -- <pitch_mm> [depth_mm]

Differences from export_stl.py, all forced by the nozzle:

  tip 0.42 mm      one extrusion width, slightly over 0.4 so the slicer emits a
                   real perimeter instead of dropping the feature. The design
                   wanted 0.04 mm; the tip is the head-on exposed area and sets
                   the return, so this is the single biggest compromise in the
                   print and the reason pitch has to be re-optimised.
  valley 0.45 mm   the groove floor also cannot be sharper than the nozzle
  arc_segments 12  no point tessellating finer than the printer resolves

PRINT ORIENTATION MATTERS MORE THAN ANY SLICER SETTING HERE. The cross-section
is constant along the extrusion axis, so standing the part up on that axis
makes every layer identical and the overhang exactly zero -- no supports, and
the layer lines end up running ALONG the grooves where they barely touch the
ray paths. The STL is written already oriented that way: the extrusion axis is
+Z, so it prints standing up as-is.

Laying it down the other way puts the flanks at ~86 degrees of overhang.
"""

import sys
import os
import math

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile_ridge import RidgeParams, build_cross_section, describe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")

NOZZLE = 0.4
TIP = 0.42


def build_oriented(params, extrude_len, name):
    """
    Build and rotate so the extrusion axis points +Z, i.e. the part arrives in
    the slicer already standing on the orientation that needs no support.
    """
    BR.clear_scene()
    p = RidgeParams(**params)
    cs = build_cross_section(p)
    mat = BR.make_diffuse("m", 0.5)
    ob = BR.loops_to_object(cs.stage1, extrude_len, 0.0, name, mat)
    ob.rotation_euler = (0.0, math.radians(90.0), 0.0)   # X (extrusion) -> Z
    bpy.context.view_layer.update()
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(rotation=True)
    return p, ob


def export(ob, path):
    for o in bpy.data.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True)
    bb = ob.dimensions
    print("[STL] %-34s %6.2f MB  bbox %.0f x %.0f x %.0f mm  faces=%d"
          % (os.path.basename(path), os.path.getsize(path) / 1e6,
             bb.x, bb.y, bb.z, len(ob.data.polygons)), flush=True)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    pitch = float(argv[0]) if argv else 8.0
    depth = float(argv[1]) if len(argv) > 1 else 30.0

    os.makedirs(EXPORT, exist_ok=True)
    base = dict(depth=depth, pitch_mean=pitch, tip_width=TIP,
                pitch_jitter=0.25, valley_round=NOZZLE * 1.125,
                arc_segments=12, backing=3.0)

    d = describe(RidgeParams(**base))
    print("[GEOM] depth %.0f  pitch %.1f  tip %.2f (%.2f%% of face)  "
          "half-angle %.2f deg  ~%.1f bounces"
          % (d["depth_mm"], d["pitch_mean_mm"], d["tip_width_mm"],
             d["tip_fraction"] * 100, d["half_angle_deg"], d["est_bounces"]),
          flush=True)

    tag = "d%02d_p%04.1f" % (depth, pitch)
    for size, label in ((100.0, "coupon100"), (500.0, "panel500")):
        _, ob = build_oriented(dict(base, face_h=size), size,
                               f"{label}_{tag}")
        export(ob, os.path.join(EXPORT, f"FDM_{label}_{tag}.stl"))


if __name__ == "__main__":
    main()
