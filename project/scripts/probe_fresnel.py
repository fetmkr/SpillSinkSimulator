"""Feasibility probe: FRESNEL WEDGE PLATE — refract the beam downward.

A vertical (or slightly tilted) clear plate whose back face is a sawtooth of
prisms. Transmitted light bends downward into a floor trough; the device is
CENTIMETRES thick where the phase-8 window needs a deep hopper.

Metric: AUDIENCE-ANGLE brightness, phase-8 style. A collimated sun enters at
+theta; an observer camera sits at eye level or below; the panel window mean
is compared cell-by-cell against a flat Musou plate under the identical rig.

PRE-REGISTERED PREDICTIONS (before any render):
  P1  F0 (vertical plate, prism 40 deg, uncoated n=1.49): the front face is a
      vertical mirror at 4 percent -- the (sun +20, obs -20) and
      (sun +40, obs -40...) mirror cells read >= 10x the flat-Musou cell.
      FAILS as a wall.
  P2  F15 (same plate tilted 15 deg, top hinge): every observer cell at or
      below eye level reads <= 0.5x flat Musou -- the specular branch is
      folded below the observer band. If this holds, a 15-deg-tilt device
      replaces the 35-deg hopper at less than half the projection depth.
  P3  G35 (plain glass tilted 35, the phase-8 geometry, uncoated): dark at
      every observer cell -- sanity anchor for the rig.
  P4  visual: F0/F15 pngs show the transmitted beam landing DOWNWARD behind
      the plate (prism deviation ~33 deg for A=40, n=1.49).
"""
import os
import sys
import math
import json

HERE = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts"
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
from geom_floor import FloorParams  # noqa: E402

OUT = "/tmp/simsrv/fresnel"
os.makedirs(OUT, exist_ok=True)

FACE = 60.0
# windows only; no pyramid geometry is built from this
PWIN = FloorParams(kind="pyramid", face_w=FACE, face_h=FACE, depth=22.0,
                   pitch=4.0, margin_depths=2.0)
SUNS = [0.0, 20.0, 40.0]
OBS = [0.0, -5.0, -10.0, -20.0]


def make_glass(name, ior=1.49):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    g = nt.nodes.new("ShaderNodeBsdfGlass")
    g.inputs["IOR"].default_value = ior
    g.inputs["Roughness"].default_value = 0.0
    nt.links.new(g.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def prism_plate(prism_deg, tilt_deg, thick=3.0, pitch=2.0):
    """Closed solid: flat front face at y=0, sawtooth back. Teeth run along x;
    the working faces tilt so transmitted light bends toward -z (down).
    Then the whole plate is rotated about its TOP edge by tilt_deg
    (bottom swings back, phase-8 convention)."""
    h = pitch * math.tan(math.radians(prism_deg))
    nz = int(FACE / pitch)
    z0 = -FACE / 2.0
    verts, faces = [], []

    def vid(x, y, z):
        verts.append((x, y, z))
        return len(verts) - 1

    # profile points in (y, z) shared by both x-ends
    front_top = (0.0, FACE / 2.0)
    front_bot = (0.0, -FACE / 2.0)
    back_prof = []                      # sawtooth from bottom to top
    for k in range(nz):
        zb = z0 + k * pitch
        back_prof.append((-thick - h, zb))       # deep point (tooth root)
        back_prof.append((-thick, zb + pitch))   # shallow point (tooth tip)
    # build two x-end rings and bridge
    ring = [front_bot, front_top] + list(reversed(back_prof))
    ids0 = [vid(0.0, y, z) for (y, z) in ring]
    ids1 = [vid(FACE, y, z) for (y, z) in ring]
    n = len(ring)
    for i in range(n):
        a, b = ids0[i], ids0[(i + 1) % n]
        c, d = ids1[(i + 1) % n], ids1[i]
        faces.append((a, b, c, d))
    faces.append(tuple(ids0))
    faces.append(tuple(reversed(ids1)))

    # tilt about the top edge (z=+FACE/2, y=0), bottom swings to -y
    t = math.radians(tilt_deg)
    ct, st = math.cos(t), math.sin(t)
    zt = FACE / 2.0
    out_v = []
    for (x, y, z) in verts:
        dz = z - zt
        out_v.append((x, y * ct + dz * st, zt + (-y * st + dz * ct)))
    mesh = bpy.data.meshes.new("plate")
    mesh.from_pydata(out_v, [], faces)
    mesh.update()
    ob = bpy.data.objects.new("plate", mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(make_glass("gl"))
    return ob


def black_surroundings():
    """Ideal absorber behind the plate and on the floor in front: isolates
    the plate's own room-side return, as phase 8.2's idealised interior did."""
    m0 = BR.make_diffuse("void", 0.0)
    for name, verts in {
        "back": [(-40, -160, -160), (100, -160, -160), (100, -8, -160),
                 (-40, -8, -160)],
    }.items():
        pass
    import bmesh
    # box behind the plate: y in [-160, -6], generous in x/z
    me = bpy.data.meshes.new("void_box")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for vtx in bm.verts:
        vtx.co.x = vtx.co.x * 240 + FACE / 2.0
        vtx.co.y = vtx.co.y * 154 - 83.0     # y in [-160, -6]
        vtx.co.z = vtx.co.z * 320
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("void_box", me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(m0)
    # floor strip in front, below the plate (the dark-floor rule)
    me2 = bpy.data.meshes.new("floor")
    # 250 mm below the sill, as phase 8.3 learned: a floor AT sill height
    # blocks every below-horizon sightline to the panel
    fz = -FACE / 2 - 250.0
    f0 = [(-120, -6, fz), (240, -6, fz),
          (240, 400, fz), (-120, 400, fz)]
    me2.from_pydata(f0, [], [(0, 1, 2, 3)])
    me2.update()
    ob2 = bpy.data.objects.new("floor", me2)
    bpy.context.collection.objects.link(ob2)
    ob2.data.materials.append(m0)


def flat_musou():
    m = BR.make_coating("musou", roughness=0.30, body=BR.MUSOU_BODY,
                        spec_scale=BR.MUSOU_SPEC_SCALE, ior=BR.MUSOU_IOR)
    me = bpy.data.meshes.new("flat")
    me.from_pydata([(0, 0, -FACE / 2), (FACE, 0, -FACE / 2),
                    (FACE, 0, FACE / 2), (0, 0, FACE / 2)], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("flat", me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(m)
    return ob


def run_config(tag, builder):
    BR.clear_scene()
    builder()
    black_surroundings()
    BR.configure_cycles(256, True)
    w_panel, _ = BR.measurement_windows(PWIN, FACE + BR.GAP, None)
    cx = FACE / 2.0
    res = {}
    for sun in SUNS:
        for ob_e in OBS:
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(cx, 0.0, FACE * 1.4, 480, 220, elev_deg=ob_e)
            BR.set_world(0.0)
            BR.add_sun(sun, strength=1.0, angular_size_deg=0.5)
            name = "%s_s%+03.0f_o%+03.0f" % (tag, sun, ob_e)
            exr = os.path.join(OUT, name + ".exr")
            BR.render_to(exr, os.path.join(OUT, name + ".png"))
            arr = BR.read_exr(exr, 480, 220)
            v = BR.window_stats(arr, BR.to_pixel_window(w_panel))["mean"]
            res["s%+.0f_o%+.0f" % (sun, ob_e)] = v
            print("[%s] sun %+3.0f obs %+3.0f  %.6f" % (tag, sun, ob_e, v),
                  flush=True)
    return res


def main():
    res = {}
    res["FLAT_musou"] = run_config("flat", flat_musou)
    res["F0_vertical_A40"] = run_config("f0", lambda: prism_plate(40.0, 0.0))
    res["F15_tilt15_A40"] = run_config("f15", lambda: prism_plate(40.0, 15.0))
    res["G35_plain_glass"] = run_config(
        "g35", lambda: prism_plate(0.001, 35.0, thick=2.0, pitch=FACE))
    with open(os.path.join(OUT, "fresnel_results.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("@@DONE@@")


if __name__ == "__main__":
    main()
