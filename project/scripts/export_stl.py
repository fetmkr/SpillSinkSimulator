"""
Export the current best geometry to STL, and render a 3D view of it.

    Blender --background --factory-startup --python scripts/export_stl.py

Geometry: ridge family, depth 30 mm, mean pitch 4 mm, irregular pitch.

Why this one: bounce count in a V-groove depends only on depth/pitch, so the
150 mm design and this one are optically equivalent -- measured 0.00178 vs
0.00139 at normal incidence and 0.0253 vs 0.0247 at the worst angle -- while
this is a fifth of the depth.

Three files are written:

    panel_full   500 x 500 mm, the real module
    coupon       100 x 100 mm, for a first print and a coating trial
    coupon_flat  100 x 100 mm flat plate, the A/B control. Every number in this
                 project is a ratio against a flat plate of the same coating,
                 so the physical test needs the same control or it measures
                 nothing.

The ridge tip is 0.04 mm in the design. That is below what a filament printer
resolves, so a print will round it off to whatever the nozzle does -- and the
tip is exactly what sets the return (return ~ 0.5 x tip width / pitch). A
second coupon with a 0.15 mm tip is written so the two can be measured against
each other and the tip law checked on real parts.
"""

import sys
import os

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile_ridge import RidgeParams, build_cross_section, describe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")
RENDERS = os.path.join(ROOT, "renders", "3d")

BEST = dict(depth=30.0, pitch_mean=4.0, tip_width=0.04, pitch_jitter=0.25,
            valley_round=0.12, arc_segments=16, backing=4.0)


def build(params, width, name):
    BR.clear_scene()
    p = RidgeParams(**params)
    cs = build_cross_section(p)
    mat = BR.make_glossy("coat", 0.005, 0.30)
    ob = BR.loops_to_object(cs.stage1, width, 0.0, name, mat)
    return p, cs, ob


def export(ob, path):
    for o in bpy.data.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True,
                              global_scale=1.0)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True)
    mb = os.path.getsize(path) / 1e6
    print("[STL] %-28s %7.2f MB  verts=%d faces=%d"
          % (os.path.basename(path), mb, len(ob.data.vertices),
             len(ob.data.polygons)), flush=True)


def flat_coupon(size, thick, path):
    BR.clear_scene()
    import bmesh
    me = bpy.data.meshes.new("flat")
    bm = bmesh.new()
    for v in [(0, 0, 0), (size, 0, 0), (size, 0, size), (0, 0, size),
              (0, -thick, 0), (size, -thick, 0), (size, -thick, size),
              (0, -thick, size)]:
        bm.verts.new(v)
    bm.verts.ensure_lookup_table()
    for f in [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
              (2, 6, 7, 3), (3, 7, 4, 0)]:
        bm.faces.new([bm.verts[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("coupon_flat", me)
    bpy.context.collection.objects.link(ob)
    export(ob, path)


def render_3d(params, width, path_png, shading="grey"):
    """
    Raking-light perspective view.

    Two versions are wanted for different reasons. With the real coating the
    frame comes out essentially black -- which is the correct answer and the
    whole point of the panel, but it shows nothing about the shape. So the
    shape view uses a neutral grey; only the "black" version represents what
    the surface actually looks like.
    """
    BR.clear_scene()
    p = RidgeParams(**params)
    cs = build_cross_section(p)
    if shading == "grey":
        mat = BR.make_diffuse("shape", 0.45)
    else:
        mat = BR.make_glossy("coat", 0.005, 0.30)
    ob = BR.loops_to_object(cs.stage1, width, 0.0, "panel", mat)

    key = bpy.data.lights.new("key", type="AREA")
    key.energy = 4.0e6
    key.size = 400.0
    ko = bpy.data.objects.new("key", key)
    ko.location = (width * 0.1, 900.0, 700.0)
    from mathutils import Vector
    ko.rotation_euler = (Vector((width * 0.4, -900.0, -700.0))
                         .to_track_quat("-Z", "Y").to_euler())
    bpy.context.collection.objects.link(ko)

    rim = bpy.data.lights.new("rim", type="AREA")
    rim.energy = 1.2e6
    rim.size = 300.0
    rim.color = (0.6, 0.75, 1.0)
    ro = bpy.data.objects.new("rim", rim)
    ro.location = (width * 1.1, 600.0, -500.0)
    ro.rotation_euler = (Vector((-width * 0.5, -600.0, 500.0))
                         .to_track_quat("-Z", "Y").to_euler())
    bpy.context.collection.objects.link(ro)

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 55.0
    cam_data.clip_start = 1.0
    cam_data.clip_end = 20000.0
    cam = bpy.data.objects.new("cam", cam_data)
    # pull back and look down the ridges at a shallow angle: the relief only
    # reads when the line of sight is close to along the grooves
    tgt = Vector((width * 0.45, -12.0, 0.0))
    cam.location = (width * 1.15, 300.0, 150.0)
    cam.rotation_euler = ((tgt - Vector(cam.location))
                          .to_track_quat("-Z", "Y").to_euler())
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    sc = bpy.context.scene
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 1000
    BR.configure_cycles(256, True)
    sc.cycles.max_bounces = 24
    BR.set_world(0.25 if shading == "grey" else 0.02)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.0 if shading == "grey" else 2.2

    BR.render_to(path_png.replace(".png", ".exr"), path_png)
    print("[3D]", path_png, flush=True)


def main():
    os.makedirs(EXPORT, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)

    d = describe(RidgeParams(**BEST))
    print("[GEOM] depth %.0f  pitch %.1f  half-angle %.2f deg  ~%.1f bounces  "
          "tip %.3f mm = %.3f%% of the face"
          % (d["depth_mm"], d["pitch_mean_mm"], d["half_angle_deg"],
             d["est_bounces"], d["tip_width_mm"], d["tip_fraction"] * 100),
          flush=True)

    _, _, ob = build(BEST, 500.0, "panel_full")
    export(ob, os.path.join(EXPORT, "panel_d30_p4_500x500.stl"))

    _, _, ob = build(dict(BEST, face_h=100.0), 100.0, "coupon")
    export(ob, os.path.join(EXPORT, "coupon_d30_p4_100x100.stl"))

    _, _, ob = build(dict(BEST, face_h=100.0, tip_width=0.15), 100.0,
                     "coupon_blunt")
    export(ob, os.path.join(EXPORT, "coupon_d30_p4_tip015_100x100.stl"))

    flat_coupon(100.0, 6.0, os.path.join(EXPORT, "coupon_FLAT_control_100x100.stl"))

    render_3d(dict(BEST, face_h=120.0), 120.0,
              os.path.join(RENDERS, "ridge_d30_p4_shape.png"), shading="grey")
    render_3d(dict(BEST, face_h=120.0), 120.0,
              os.path.join(RENDERS, "ridge_d30_p4_black.png"), shading="black")


if __name__ == "__main__":
    main()
