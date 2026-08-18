"""Beauty render of the FINAL ORDER SPEC pyramid field (p4 / d22 / t0.4).

Replaces the journey-report cover, which showed a mid-study cone field while
its caption claimed pyramids (user 2026-08-18). Clay grey like the old cover;
the real coating renders featureless black.
"""
import os
import sys

HERE = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project/scripts"
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from geom_floor import FloorParams, build_mesh  # noqa: E402

OUT = os.environ.get("HERO_OUT", "/tmp/hero_final.png")
SPP = int(os.environ.get("HERO_SPP", "128"))

p = FloorParams(kind="pyramid", face_w=240.0, face_h=240.0, depth=22.0,
                pitch=4.0, tip_flat=0.4, backing=2.0, margin_depths=0.0)
v, f = build_mesh(p)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

mesh = bpy.data.meshes.new("panel")
mesh.from_pydata([tuple(x) for x in v], [], [tuple(x) for x in f])
mesh.update()
ob = bpy.data.objects.new("panel", mesh)
bpy.context.collection.objects.link(ob)

mat = bpy.data.materials.new("clay")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.52, 0.53, 0.55, 1.0)
bsdf.inputs["Roughness"].default_value = 0.55
ob.data.materials.append(mat)

# world: soft grey dome
w = bpy.context.scene.world or bpy.data.worlds.new("w")
bpy.context.scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.56, 0.58, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.9

# low sun raking across the tips for flank contrast
sun_d = bpy.data.lights.new("sun", type="SUN")
sun_d.energy = 3.0
sun_d.angle = 0.2
sun = bpy.data.objects.new("sun", sun_d)
sun.rotation_euler = (1.05, 0.0, 2.4)
bpy.context.collection.objects.link(sun)

# camera: low three-quarter close-up so spikes fill the frame.
# panel spans x 0..160, z -80..80 (face centred in z), tips at y=0 plane?
# geom_floor: shaping occupies y in [-depth, 0], tips at y=0, slab below.
cam_d = bpy.data.cameras.new("cam")
cam_d.lens = 52
cam = bpy.data.objects.new("cam", cam_d)
cam.location = (190.0, 58.0, -82.0)
# aim at a point inside the field, slightly below tip plane
import mathutils  # noqa: E402
target = mathutils.Vector((112.0, -10.0, 6.0))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = SPP
sc.render.resolution_x = 1500
sc.render.resolution_y = 1050
sc.render.film_transparent = False
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
