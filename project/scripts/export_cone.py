"""
STL export for the 3D cone family.

    Blender --background --factory-startup --python scripts/export_cone.py -- <depth> <pitch> [face]

Unlike the 1D ridge, nothing here is pinned to an absolute dimension: the tip
was measured not to matter (shrinking it 16x moved head-on by 16%), so the
design is set by the aspect ratio depth/pitch alone. That is what makes a
shallow version possible at all.

The measurement builds carry a large margin of extra cones so a tilted camera
never runs off the tile; for an export that margin is dropped to one pitch, so
the part is flush with the panel edge and neighbouring modules butt together.
"""
import sys, os, math, time
import bpy, bmesh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR
import geom3d as G3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "export")


def trim_to_face(ob, face, depth, backing):
    """
    Boolean-intersect with an exact face x face box, so the coupon has no cone
    hanging over the edge and butts flush against the next module.

    Cones are still generated across the whole face and cut at the boundary,
    rather than being kept clear of it -- pulling them inside would leave a
    flat border one base-radius wide, and a flat border is the brightest thing
    on the part.
    """
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    box.scale = (face, depth + backing + 4.0, face)
    box.location = (face / 2.0, -(depth + backing + 4.0) / 2.0 + 1.0, 0.0)
    bpy.context.view_layer.update()

    m = ob.modifiers.new("trim", "BOOLEAN")
    m.operation = "INTERSECT"
    m.solver = "EXACT"
    m.object = box
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(box, do_unlink=True)
    return ob


def trim_to_face(ob, face, depth, backing):
    """
    Boolean-intersect with an exact face x face box.

    Safe to cut only because the centre field is periodic over the module: the
    half-cone removed at the right edge is the same half-cone entering at the
    left, so butting two modules rebuilds whole cones. No flat border anywhere,
    which matters because a flat border would be the brightest feature on the
    panel.
    """
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    box = bpy.context.active_object
    thick = depth + backing + 6.0
    box.scale = (face, thick, face)
    box.location = (face / 2.0, 1.0 - thick / 2.0, 0.0)
    bpy.context.view_layer.update()

    m = ob.modifiers.new("trim", "BOOLEAN")
    m.operation = "INTERSECT"
    m.solver = "EXACT"
    m.object = box
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(box, do_unlink=True)
    return ob


def union(ob):
    """
    Boolean-union the interpenetrating cones into a single shell.

    The raw build is a few hundred separate closed solids that overlap. That is
    watertight, and every mainstream slicer unions overlapping shells so it
    would in practice print -- but a slicer using an even-odd fill rule would
    turn every overlap into a hole instead. Unioning removes the question.
    """
    t0 = time.time()
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(ob.data)
    for f in bm.faces:
        f.select = True
    bpy.ops.mesh.intersect_boolean(operation="UNION", solver="EXACT",
                                   use_self=True)
    bpy.ops.object.mode_set(mode="OBJECT")

    bm = bmesh.new(); bm.from_mesh(ob.data); bm.edges.ensure_lookup_table()
    opened = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    seen, shells = set(), 0
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        shells += 1
        stack = [f0]
        while stack:
            g = stack.pop()
            if g.index in seen:
                continue
            seen.add(g.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        stack.append(h)
    bm.free()
    print("[UNION] %.1fs  open=%d  nonmanifold=%d  shells=%d  %s"
          % (time.time() - t0, opened, nonman, shells,
             "OK" if (opened == 0 and nonman == 0 and shells == 1)
             else "CHECK"), flush=True)
    return ob


def export(ob, path):
    for o in bpy.data.objects:
        o.select_set(o is ob)
    bpy.context.view_layer.objects.active = ob
    try:
        bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)
    except AttributeError:
        bpy.ops.export_mesh.stl(filepath=path, use_selection=True)
    bb = ob.dimensions
    print("[STL] %-36s %6.1f MB  bbox %.0f x %.0f x %.0f mm  faces=%d"
          % (os.path.basename(path), os.path.getsize(path) / 1e6,
             bb.x, bb.y, bb.z, len(ob.data.polygons)), flush=True)


def build(depth, pitch, face, segs=24):
    BR.clear_scene()
    # tip radius fixed at 0.2 mm (0.4 mm across) -- one nozzle width, and
    # measured to be worth 1.8x against 0.4 mm at this depth
    p = G3.Cone3DParams(face_w=face, face_h=face, depth=depth, pitch=pitch,
                        tip_radius=0.2, jitter=0.30, radial_seg=segs,
                        height_seg=3, margin_depths=0.0,
                        centre_margin_pitches=1.0, backing=3.0, tileable=True,
                        # height jitter off for the export: with it on the
                        # shallowest cone sets where the slab has to sit, which
                        # would truncate the deepest valleys. Position jitter
                        # alone already breaks the periodicity.
                        depth_jitter=0.0)
    v, f = G3.build_mesh(p)
    ob = BR.mesh_to_object(v, f, "cones", BR.make_diffuse("m", 0.5))
    return p, ob


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    depth = float(argv[0]) if argv else 30.0
    pitch = float(argv[1]) if len(argv) > 1 else 7.5
    os.makedirs(EXPORT, exist_ok=True)

    d = G3.describe(G3.Cone3DParams(depth=depth, pitch=pitch, tip_radius=0.2))
    print("[GEOM] depth %.0f  pitch %.1f  A=%.1f  half-angle %.1f deg  "
          "tip frac %.5f (a 1D ridge would expose %.5f)"
          % (depth, pitch, d["aspect"], d["half_angle_deg"],
             d["tip_fraction"], d["equivalent_1d_fraction"]), flush=True)

    tag = "d%02d_p%04.1f" % (depth, pitch)
    # 100 x 100 only. A full 500 mm module is 450k faces and 36 MB, and the
    # cross-section is identical -- nothing is learned by exporting it.
    for face, label, segs in ((100.0, "coupon100", 24),):
        _, ob = build(depth, pitch, face, segs)
        union(ob)
        trim_to_face(ob, face, depth, 3.0)
        union(ob)
        export(ob, os.path.join(EXPORT, "CONE_%s_%s.stl" % (label, tag)))


if __name__ == "__main__":
    main()
