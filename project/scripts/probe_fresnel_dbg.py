"""Routing check for the tilted Fresnel wedge: paint the back box grey and
look from the SIDE — the bright band on the box wall shows where the
transmitted beam actually lands (P4)."""
import os
import sys
import math

HERE = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts"
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import mathutils  # noqa: E402
import blender_render as BR  # noqa: E402
from probe_fresnel import prism_plate, FACE  # noqa: E402

OUT = "/tmp/simsrv/fresnel"
BR.clear_scene()
prism_plate(30.0, 15.0)

grey = BR.make_diffuse("grey", 0.4)
def plane(name, pts):
    me = bpy.data.meshes.new(name)
    me.from_pydata(pts, [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(grey)
# back wall 160 mm behind the plate, and a floor 200 mm below
plane("back", [(-40, -160, -260), (100, -160, -260),
               (100, -160, 60), (-40, -160, 60)])
plane("bottom", [(-40, -160, -200), (100, -160, -200),
                 (100, 10, -200), (-40, 10, -200)])

BR.set_world(0.0)
BR.add_sun(0.0, strength=1.0, angular_size_deg=0.5)

# front view: the back wall faces this camera, so the transmitted beam's
# landing stripe below the plate is directly visible
BR.setup_camera(30.0, -80.0, 340, 640, 640, elev_deg=0.0)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 256
sc.render.resolution_x = 640
sc.render.resolution_y = 640
sc.render.filepath = os.path.join(OUT, "f15_routing.png")
BR.configure_cycles(256, True)
sc.render.resolution_x = 640
sc.render.resolution_y = 640
sc.render.filepath = os.path.join(OUT, "f15_routing.png")
bpy.ops.render.render(write_still=True)
print("@@DONE@@", sc.render.filepath)
