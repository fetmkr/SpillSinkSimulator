"""Feasibility probe: MIRROR-WALLED funnel pyramid with a Musou dump floor.

The idea under test (phase 8 extension, 2026-08-19): instead of painting the
whole pyramid field with Musou, make the walls SHINY (cheap aluminium-class
specular) so they merely GUIDE the beam down into the valley, and paint only
a thin bottom band ("the dump") with Musou. Paint area collapses; geometry
does the routing.

PRE-REGISTERED PREDICTIONS (written before any render):
  P1  all-mirror p4/d22/t0.4, rho_spec 0.90, roughness 0.02, no dump:
      worst-theta rho_dh 30-50 % (the ~9-bounce ladder alone cannot absorb).
  P2  mirror walls + musou_fit bottom 3 mm: worst-theta 0.3-0.8 %.
      Jackpot rule: <= 0.5 % beats the bare-urethane tier (0.907 %) with a
      fraction of its paint.
  P3  walls at rho 0.95: P2 roughly halves.

Measured with the SAME instrument as every number in the book: uniform
hemisphere, tilted ortho camera, control plate must read 0.0500.
"""
import os
import sys

HERE = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts"
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import json  # noqa: E402
import blender_render as BR  # noqa: E402
from geom_floor import FloorParams, build_mesh  # noqa: E402

OUT = "/tmp/simsrv/funnel"
os.makedirs(OUT, exist_ok=True)

FACE = 60.0
P = FloorParams(kind="pyramid", face_w=FACE, face_h=FACE, depth=22.0,
                pitch=4.0, tip_flat=0.4, backing=2.0, margin_depths=2.0)
THETAS = [0.0, -20.0, -40.0, 20.0, 40.0]


def build_panel(dump_h, rho_walls, rough):
    """One pyramid field object; if dump_h > 0 the mesh is bisected at
    y = -depth + dump_h and the lower band gets the fitted Musou coating."""
    v, f = build_mesh(P)
    mesh = bpy.data.meshes.new("panel")
    mesh.from_pydata([tuple(x) for x in v], [], [tuple(x) for x in f])
    mesh.update()
    ob = bpy.data.objects.new("panel", mesh)
    bpy.context.collection.objects.link(ob)

    m_wall = BR.make_glossy("walls", rho_walls, rough)
    ob.data.materials.append(m_wall)
    if dump_h > 0:
        m_dump = BR.make_coating("dump", roughness=0.30,
                                 body=BR.MUSOU_BODY,
                                 spec_scale=BR.MUSOU_SPEC_SCALE,
                                 ior=BR.MUSOU_IOR)
        ob.data.materials.append(m_dump)
        y_split = -P.depth + dump_h
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges)
                               + list(bm.faces),
                               plane_co=(0.0, y_split, 0.0),
                               plane_no=(0.0, 1.0, 0.0))
        for face in bm.faces:
            c = face.calc_center_median()
            face.material_index = 1 if c.y < y_split else 0
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
    return ob


def measure(tag, dump_h, rho_walls, rough=0.02):
    BR.clear_scene()
    ob = build_panel(dump_h, rho_walls, rough)
    ctrl_x0 = P.face_w + BR.GAP
    m_ctrl = BR.make_diffuse("ctrl", 0.05)
    BR.make_flat_plate(P, ctrl_x0, "control", m_ctrl)

    total_w = ctrl_x0 + P.face_w
    cx, cz = total_w / 2.0, 0.0
    BR.configure_cycles(256, True)
    w_panel, w_ctrl = BR.measurement_windows(P, ctrl_x0, None)

    out = {}
    for th in THETAS:
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, cz, total_w * 1.02, 480, 220, elev_deg=th)
        BR.set_world(1.0)
        px_p = BR.to_pixel_window(w_panel)
        px_c = BR.to_pixel_window(w_ctrl)
        name = "%s_th%+05.1f" % (tag, th)
        exr = os.path.join(OUT, name + ".exr")
        BR.render_to(exr, os.path.join(OUT, name + ".png"))
        arr = BR.read_exr(exr, 480, 220)
        panel = BR.window_stats(arr, px_p)["mean"]
        ctrl = BR.window_stats(arr, px_c)["mean"]
        out["%+.0f" % th] = {"panel": panel, "ctrl": ctrl}
        print("[%s] th %+5.1f  panel %.6f  ctrl %.6f" % (tag, th, panel, ctrl),
              flush=True)
    return out


def main():
    res = {}
    res["P1_all_mirror_r90"] = measure("m90", 0.0, 0.90)
    res["P2_dump3_r90"] = measure("d3r90", 3.0, 0.90)
    res["P3_dump3_r95"] = measure("d3r95", 3.0, 0.95)
    with open(os.path.join(OUT, "funnel_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("@@DONE@@")


if __name__ == "__main__":
    main()
