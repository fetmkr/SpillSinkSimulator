"""
Perspective 3D view: a hazy room, a laser beam, half flat wall and half panel.

    Blender --background --factory-startup --python scripts/render3d.py

The measurement renders are deliberately flat and orthographic so the numbers
mean something. This one is the opposite: it shows the situation the numbers
are about -- a beam crossing haze and terminating on a wall, with the treated
and untreated halves side by side under identical light.

Nothing here should be read as a measurement. The exposure is chosen so the
beam is visible, which necessarily crushes the difference between 1e-3 and
1e-4 on the wall.
"""

import sys
import os
import math

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile_ridge import RidgeParams, build_cross_section        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "3d")

RES_X, RES_Y = 1600, 900
SAMPLES = 512
PANEL_W = 500.0


def haze(size, density):
    """A scattering volume, so the beams are visible in flight."""
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    v = nt.nodes.new("ShaderNodeVolumeScatter")
    v.inputs["Density"].default_value = density
    v.inputs["Anisotropy"].default_value = 0.4
    nt.links.new(v.outputs[0], out.inputs["Volume"])

    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = "haze"
    ob.scale = size
    ob.location = (0.0, size[1] * 0.5, 0.0)
    ob.data.materials.append(m)
    return ob


def beam(origin, target, energy, spot_deg=0.35, color=(0.55, 0.75, 1.0)):
    d = bpy.data.lights.new("beam", type="SPOT")
    d.energy = energy
    d.spot_size = math.radians(spot_deg)
    d.spot_blend = 0.02
    d.shadow_soft_size = 0.0
    d.color = color
    o = bpy.data.objects.new("beam", d)
    bpy.context.collection.objects.link(o)
    o.location = origin
    dz = (target[0] - origin[0], target[1] - origin[1], target[2] - origin[2])
    o.rotation_euler = _aim(dz)
    return o


def _aim(d):
    from mathutils import Vector
    v = Vector(d)
    return v.to_track_quat("-Z", "Y").to_euler()


def main():
    os.makedirs(OUT, exist_ok=True)
    BR.clear_scene()

    p = RidgeParams(depth=150.0, pitch_mean=20.0, tip_width=0.2,
                    face_w=PANEL_W, face_h=PANEL_W)
    cs = build_cross_section(p)

    m_panel = BR.make_glossy("coat", 0.005, 0.30)
    m_flat = BR.make_diffuse("flat", 0.05)

    # panel on the right, plain coated wall on the left, same plane
    BR.loops_to_object(cs.stage1, PANEL_W, 0.0, "panel", m_panel)
    BR.make_flat_plate(p, -PANEL_W - 20.0, "flatwall", m_flat)

    # a floor, so the scene reads as a room rather than as floating geometry
    mesh = bpy.data.meshes.new("floor")
    import bmesh
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in
          [(-1400, 0, -260), (900, 0, -260),
           (900, 2600, -260), (-1400, 2600, -260)]]
    bm.faces.new(vs)
    bm.to_mesh(mesh)
    bm.free()
    fl = bpy.data.objects.new("floor", mesh)
    fl.data.materials.append(BR.make_diffuse("floormat", 0.03))
    bpy.context.collection.objects.link(fl)

    haze((3000.0, 2600.0, 1400.0), 0.00035)

    # three beams from projector positions, converging past the camera and
    # terminating: two on the panel, one on the plain wall
    beam((900.0, 2300.0, 700.0), (250.0, 0.0, 40.0), 9.0e7)
    beam((-1200.0, 2300.0, 500.0), (380.0, 0.0, -90.0), 9.0e7,
         color=(1.0, 0.55, 0.8))
    beam((700.0, 2300.0, 600.0), (-300.0, 0.0, 20.0), 9.0e7,
         color=(0.6, 1.0, 0.7))

    cam_data = bpy.data.cameras.new("cam")
    cam_data.lens = 34.0
    cam_data.clip_start = 10.0
    cam_data.clip_end = 20000.0
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (-250.0, 1500.0, 190.0)
    cam.rotation_euler = _aim((-250.0 - -250.0, 0.0 - 1500.0, -20.0 - 190.0))
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    sc = bpy.context.scene
    sc.render.resolution_x = RES_X
    sc.render.resolution_y = RES_Y
    BR.configure_cycles(SAMPLES, True)
    sc.cycles.volume_bounces = 2
    sc.cycles.max_bounces = 32
    BR.set_world(0.0)
    # a beauty frame, not a measurement: Filmic-style rolloff is wanted here
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 1.5

    exr = os.path.join(OUT, "room_view.exr")
    png = os.path.join(OUT, "room_view.png")
    BR.render_to(exr, png)
    print("[3D]", png, flush=True)


if __name__ == "__main__":
    main()
