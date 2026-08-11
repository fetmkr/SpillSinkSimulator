"""
Debug render: who is the camera actually looking at?

Emission-tags each role so the front view can be decoded directly, and prints
mesh statistics so a silently-dropped face cannot masquerade as a physics
result.

    Blender --background --factory-startup --python scripts/debug_id.py
"""

import sys
import os

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile2d import PanelParams, build_cross_section                # noqa: E402
from blender_render import (                                          # noqa: E402
    clear_scene, loops_to_object, make_flat_plate, setup_camera,
    configure_cycles, set_world, render_to, read_exr, GAP,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "_debug")

RES_X, RES_Y = 1100, 500


def emis(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1.0)
    e.inputs["Strength"].default_value = 1.0
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def loop_report(name, loops):
    """Count how many loops bmesh will actually accept as faces."""
    bad = sum(1 for L in loops if len(L) < 3)
    print("[MESH] %-9s loops=%4d  min_pts=%3d  max_pts=%3d  degenerate=%d"
          % (name, len(loops),
             min((len(L) for L in loops), default=0),
             max((len(L) for L in loops), default=0), bad))


def run():
    os.makedirs(OUT, exist_ok=True)
    p = PanelParams()
    cs = build_cross_section(p)

    loop_report("slats", cs.stage1)
    loop_report("baffles", cs.stage2)
    loop_report("shell", cs.shell)

    clear_scene()
    m1 = emis("id_slats", (1.0, 0.0, 0.0))      # red   = stage 1 slats
    m2 = emis("id_baffles", (0.0, 1.0, 0.0))    # green = stage 2 baffles
    m3 = emis("id_shell", (0.0, 0.0, 1.0))      # blue  = shell / back wall
    m4 = emis("id_ctrl", (1.0, 1.0, 0.0))       # yellow= flat control

    expected = {"slats": len(cs.stage1), "baffles": len(cs.stage2),
                "shell": len(cs.shell)}
    o1 = loops_to_object(cs.stage1, p.face_w, 0.0, "slats", m1)
    o2 = loops_to_object(cs.stage2, p.face_w, 0.0, "baffles", m2)
    o3 = loops_to_object(cs.shell, p.face_w, 0.0, "shell", m3)
    ctrl_x0 = p.face_w + GAP
    make_flat_plate(p, ctrl_x0, "control", m4)

    for o in (o1, o2, o3):
        print("[OBJ] %-9s verts=%6d  faces=%6d  expected_prisms=%d"
              % (o.name, len(o.data.vertices), len(o.data.polygons),
                 expected[o.name]))

    total_w = ctrl_x0 + p.face_w
    configure_cycles(16, use_gpu=True)
    # emission only: no bounces needed, and a black world so unseen = black
    bpy.context.scene.cycles.max_bounces = 0
    set_world(0.0)

    print("[SEEN] elev    slats  baffles    shell  nothing")
    for elev in (-80, -60, -30, 0, 30, 60, 80):
        for o in list(bpy.data.objects):
            if o.type == "CAMERA":
                bpy.data.objects.remove(o, do_unlink=True)
        setup_camera(total_w / 2.0, 0.0, total_w * 1.02, RES_X, RES_Y,
                     elev_deg=elev)

        name = f"id_elev{elev:+03d}"
        exr = os.path.join(OUT, name + ".exr")
        render_to(exr, os.path.join(OUT, name + ".png"))
        arr = read_exr(exr, RES_X, RES_Y)

        # panel occupies world X [0,500]; the front view mirrors X, so the
        # panel lands on the right half of the frame
        sub = arr[:, 600:1100, :]
        r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
        tot = sub.shape[0] * sub.shape[1]
        dark = float(((r + g + b) < 0.01).sum()) / tot
        print("[SEEN] %+4d  %6.1f%%  %6.1f%%  %6.1f%%  %6.1f%%"
              % (elev,
                 100.0 * float((r > 0.5).sum()) / tot,
                 100.0 * float((g > 0.5).sum()) / tot,
                 100.0 * float((b > 0.5).sum()) / tot,
                 100.0 * dark))
    print("[OUT]", OUT)


if __name__ == "__main__":
    run()
