"""
A 3D view of every geometry tried, numbered into the same record as the
cross-sections.

    Blender --background --factory-startup --python scripts/shot3d.py -- [name ...]
    Blender --background --factory-startup --python scripts/shot3d.py -- all

Writes profiles/NNN_3d_<name>.png and appends to profiles/INDEX.md, so the
folder reads as a chronological record of what was built — dead ends included.
A design that failed is still something to show and explain; the picture is
what makes "we tried this and here is why it did not work" a sentence anyone
can follow.

Two renders per design where it helps: neutral grey so the shape is legible,
and the real coating so the client can see that the working surface is simply
black.
"""

import sys
import os
import math

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "profiles")
INDEX = os.path.join(OUT, "INDEX.md")


# name -> (family, params, tile size, one-line note)
DESIGNS = {
    "slat_chamber": (
        "slat",
        dict(face_w=140.0, face_h=140.0, slat_deg=45.0, slat_len=79.2,
             pitch_mean=40.0, baffle_rows=2, baffle_deg=-45.0,
             baffle_len=48.8, baffle_pitch=60.0),
        140.0,
        "family 1, angled slats over a hidden chamber. DEAD: the slats blocked "
        "the chamber entirely, so its geometry could not matter"),
    "scatter_trough": (
        "scatter",
        dict(face_w=140.0, face_h=140.0, width_mean=60.0, depth_ratio=1.5,
             shape="u", depth=100.0),
        140.0,
        "family 2, open troughs, aimed at destroying form. DEAD: at "
        "retro-incidence the first hit is visible and one bounce cannot "
        "displace a photon"),
    "ridge_vgroove": (
        "ridge",
        dict(face_w=140.0, face_h=140.0, depth=50.0, pitch_mean=13.0,
             tip_width=0.8, arc_segments=24, valley_round=0.4,
             margin_depths=0.2),
        140.0,
        "family 3, deep V-grooves, the wall-scale form of a beam dump. Best "
        "extruded design: 0.027% head-on, but the line comes back as a line"),
    "ridge_serrated": (
        "ridge",
        dict(face_w=140.0, face_h=140.0, depth=50.0, pitch_mean=20.0,
             tip_width=0.8, arc_segments=24, micro_pitch=1.0,
             micro_depth=0.3, margin_depths=0.2),
        140.0,
        "V-grooves with serrated flanks, copying butterfly hierarchy. DEAD: "
        "sub-wavelength physics does not transfer to mm scale; a sawtooth only "
        "deflects a grazing ray where a pit would trap it"),
    "cone_d80": (
        "cone3d",
        dict(face_w=110.0, face_h=110.0, depth=80.0, pitch=13.0,
             tip_radius=0.4, jitter=0.30, margin_depths=0.2),
        110.0,
        "family 5, irregular cone array. 0.0044% head-on, 6x better than the "
        "groove, and the first design to destroy form as well"),
    "cone_d30": (
        "cone3d",
        dict(face_w=90.0, face_h=90.0, depth=30.0, pitch=7.5, tip_radius=0.4,
             jitter=0.30, margin_depths=0.2),
        90.0,
        "the same at 30 mm depth: 0.0084% head-on, 1.8x worse than 50 mm but "
        "a wall two fifths as thick"),
    "cmp_groove_p13": (
        "ridge",
        dict(face_w=120.0, face_h=120.0, depth=50.0, pitch_mean=13.0,
             tip_width=0.8, arc_segments=24, valley_round=0.4,
             margin_depths=0.15),
        120.0, "COMPARISON: 1D V-groove, depth 50, pitch 13, tip 0.8 mm"),
    "cmp_groove_p08": (
        "ridge",
        dict(face_w=120.0, face_h=120.0, depth=50.0, pitch_mean=8.0,
             tip_width=0.8, arc_segments=24, valley_round=0.4,
             margin_depths=0.15),
        120.0, "COMPARISON: 1D V-groove, depth 50, pitch 8, tip 0.8 mm"),
    "cmp_cone_p75": (
        "cone3d",
        dict(face_w=80.0, face_h=80.0, depth=30.0, pitch=7.5, tip_radius=0.2,
             jitter=0.30, margin_depths=0.0, centre_margin_pitches=1.0),
        80.0, "COMPARISON: 3D cone array, depth 30, pitch 7.5, tip r 0.2 mm"),
    "cmp_cone_p375": (
        "cone3d",
        dict(face_w=60.0, face_h=60.0, depth=30.0, pitch=3.75, tip_radius=0.2,
             jitter=0.30, margin_depths=0.0, centre_margin_pitches=1.0),
        60.0, "COMPARISON: 3D cone array, depth 30, pitch 3.75, tip r 0.2 mm"),
    # --- the four the comparison report actually argues about --------------
    # tip convention: ONE NOZZLE, 0.4 mm ACROSS, for both families. ridge
    # tip_width is a full width and cone tip_radius is a radius, so the
    # earlier "tip 0.2 both" pair was still a factor of two apart -- and a
    # 0.2 mm ridge is half a nozzle and cannot be printed at all.
    "fair_groove_d50_p13": (
        "ridge",
        dict(face_w=120.0, face_h=120.0, depth=50.0, pitch_mean=13.0,
             tip_width=0.4, arc_segments=24, valley_round=0.4,
             margin_depths=0.15),
        120.0, "1D V-groove d50 p13, tip 0.4 mm across -- best 1D head-on, "
        "0.0159%"),
    "fair_groove_d30_p75": (
        "ridge",
        dict(face_w=80.0, face_h=80.0, depth=30.0, pitch_mean=7.5,
             tip_width=0.4, arc_segments=24, valley_round=0.4,
             margin_depths=0.15),
        80.0, "1D V-groove d30 p7.5, tip 0.4 across -- matched to the cone on "
        "depth, pitch and printable tip, 0.0237%"),
    # exactly the geometry export_cone.py writes to STL: tileable, backing 3,
    # no height jitter, tip r0.2. what gets printed is what gets rendered
    "stl_cone_d30_p75": (
        "cone3d",
        dict(face_w=100.0, face_h=100.0, depth=30.0, pitch=7.5,
             tip_radius=0.2, jitter=0.30, radial_seg=24, height_seg=3,
             margin_depths=0.0, centre_margin_pitches=1.0, backing=3.0,
             tileable=True, depth_jitter=0.0),
        100.0, "AS EXPORTED: 3D cone d30 p7.5 r0.2, tileable 100x100 STL, "
        "0.0051% head-on"),
    "stl_cone_d30_p375": (
        "cone3d",
        dict(face_w=100.0, face_h=100.0, depth=30.0, pitch=3.75,
             tip_radius=0.2, jitter=0.30, radial_seg=24, height_seg=3,
             margin_depths=0.0, centre_margin_pitches=1.0, backing=3.0,
             tileable=True, depth_jitter=0.0),
        100.0, "AS EXPORTED: 3D cone d30 p3.75 r0.2, tileable 100x100 STL, "
        "0.0803% all-angle"),
    "cone_bimodal": (
        "cone3d",
        dict(face_w=70.0, face_h=70.0, depth=30.0, pitch=7.5, tip_radius=0.4,
             jitter=0.30, second_ratio=0.5, second_depth_frac=0.55,
             margin_depths=0.2),
        70.0,
        "two cone sizes: a finer, shorter array dropped into the valleys to "
        "catch the rays that skim the primary flanks"),
}


def next_revision():
    n = 0
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            head = f.split("_", 1)[0]
            if head.isdigit():
                n = max(n, int(head))
    return n + 1


def build(family, params, material):
    # the scene is cleared by the caller BEFORE the material is made; clearing
    # it here would delete the material that was just passed in
    if family == "cone3d":
        import geom3d as G3
        p = G3.Cone3DParams(**params)
        v, f = G3.build_mesh(p)
        BR.mesh_to_object(v, f, "geo", material)
        return p
    mod = {"slat": "profile2d", "scatter": "profile_scatter",
           "ridge": "profile_ridge"}[family]
    cls = {"slat": "PanelParams", "scatter": "ScatterParams",
           "ridge": "RidgeParams"}[family]
    m = __import__(mod)
    p = getattr(m, cls)(**params)
    cs = m.build_cross_section(p)
    for loops in (cs.stage1, cs.stage2, cs.shell):
        if loops:
            BR.loops_to_object(loops, p.face_w, 0.0, "geo%d" % id(loops),
                               material)
    return p


def shoot(name, family, params, size, path, black=False):
    from mathutils import Vector
    BR.clear_scene()
    mat = (BR.make_glossy("coat", 0.005, 0.30) if black
           else BR.make_diffuse("shape", 0.45))
    build(family, params, mat)

    for loc, en, sz, col in (((0.0, size * 6.0, size * 5.5), 3.0e5 * size,
                              size * 3.0, (1, 1, 1)),
                             ((size * 1.6, size * 4.5, -size * 3.5),
                              1.0e5 * size, size * 2.4, (0.6, 0.75, 1.0))):
        d = bpy.data.lights.new("L", type="AREA")
        d.energy = en
        d.size = sz
        d.color = col
        o = bpy.data.objects.new("L", d)
        o.location = loc
        o.rotation_euler = (Vector((size * 0.45, 0, 0)) - Vector(loc)) \
            .to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(o)

    cd = bpy.data.cameras.new("c")
    cd.lens = 52.0
    cd.clip_start = 1.0
    cd.clip_end = 20000.0
    cam = bpy.data.objects.new("c", cd)
    tgt = Vector((size * 0.5, -size * 0.20, 0.0))
    cam.location = (size * 1.05, size * 2.05, size * 0.95)
    cam.rotation_euler = (tgt - Vector(cam.location)) \
        .to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    sc = bpy.context.scene
    sc.render.resolution_x = 1400
    sc.render.resolution_y = 950
    BR.configure_cycles(160, True)
    sc.cycles.max_bounces = 10
    BR.set_world(0.05 if black else 0.30)
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 2.0 if black else 0.0
    BR.render_to(path.replace(".png", ".exr"), path)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    names = list(DESIGNS) if (not argv or argv[0] == "all") else argv

    os.makedirs(OUT, exist_ok=True)
    for name in names:
        if name not in DESIGNS:
            print("[SKIP] unknown design", name, flush=True)
            continue
        family, params, size, note = DESIGNS[name]
        rev = next_revision()
        path = os.path.join(OUT, "%03d_3d_%s.png" % (rev, name))
        shoot(name, family, params, size, path)
        with open(INDEX, "a") as f:
            f.write("| %03d | %s | [3d_%s](%03d_3d_%s.png) | %s | |\n"
                    % (rev, family, name, rev, name, note))
        print("[%03d] %s" % (rev, os.path.basename(path)), flush=True)


if __name__ == "__main__":
    main()
