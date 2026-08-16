"""Render a geometry and LOOK at it, before any number is measured.

    Blender --background --factory-startup --python scripts/preview_geom.py \
        -- <family> '<params json>' [out.png]

WHY THIS EXISTS. A perforated pyramid was built with its apex at -depth and its
base in the entrance plane -- a FUNNEL -- and measured against a solid pyramid,
which is a spike. Two different shapes under one name. The sweep ran, the gate
passed, the numbers were consistent, a findings file explained the 1.9x
difference by a mechanism that was not there, and the error surfaced only when
someone asked why a shell with no holes did not measure the same as a solid.

Nothing in the pipeline could have caught it. Every check this project has is
numerical: the gate compares sweeps, `audit_geometry` measures extents and
coverage, `audit_normal` compares defaults. None of them knows which way up a
pyramid is, because "which way up" is not a quantity any of them reads.

So: render it, put the picture in front of a person or a model, and look. This
takes two seconds and is the only check that would have caught a funnel called
a pyramid.

THE VIEW. Three panels in one image so orientation is unambiguous:

    front elevation   the silhouette -- a spike points up, a funnel opens up
    top view          what the measurement camera sees at theta = 0
    three-quarter     for reading the whole cell

The panel is lit from a fixed key so the shape reads; this is not a
measurement and the lighting is chosen to show form, not to be physical.
"""

import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build(family, params):
    """Same dispatch `blender_render.build_scene` uses, mesh only."""
    if family == "perf":
        import geom_perf as M
        return M.build_mesh(M.PerfParams(**params))
    if family == "floor":
        import geom_floor as M
        return M.build_mesh(M.FloorParams(**params))
    if family == "topo":
        import geom_topo as M
        return M.build_mesh(M.TopoParams(**params))
    if family == "cone3d":
        import geom3d as M
        return M.build_mesh(M.Cone3DParams(**params))
    if family == "cell":
        import geom_cell as M
        return M.build_mesh(M.CellParams(**params))
    if family == "stack":
        import geom_stack as M
        return M.build_mesh(M.StackParams(**params))
    raise ValueError("no such family: %s" % family)


def render(family, params, out_png, cells=3.0):
    import bpy
    import blender_render as BR

    verts, faces = build(family, params)
    pitch = float(params.get("pitch", params.get("pitch_mean", 6.0)))
    depth = float(params.get("depth", 50.0))
    face_h = float(params.get("face_h", 60.0))

    BR.clear_scene()
    mesh = bpy.data.meshes.new("preview")
    mesh.from_pydata([tuple(q) for q in verts], [],
                     [tuple(q) for q in faces])
    mesh.update()
    ob = bpy.data.objects.new("preview", mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(BR.make_diffuse("preview", 0.45))

    cy = BR.configure_cycles(64, True)
    cy.max_bounces = 4
    BR.set_world(0.25)

    # A POST THAT STICKS UP OUT OF THE PANEL, so every view says which way is
    # out. A flat reference lying IN the plane y = 0 was the first attempt and
    # it is invisible edge-on -- a surface seen along itself is a line. A solid
    # post rising from y = 0 to y = +depth/3, placed beside the field, reads in
    # all three views: material on the post's side of the entrance plane is
    # OUTSIDE the panel, material on the other side is inside it. Without this
    # an edge-on render of a pyramid field is equally consistent with spikes
    # and with funnels, which is exactly the mix-up this script exists to stop.
    def _box(x0, x1, y0, y1, z0, z1, name, rho):
        m2 = bpy.data.meshes.new(name)
        vs = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
              (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
        fs = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2),
              (2, 6, 7, 3), (3, 7, 4, 0)]
        m2.from_pydata(vs, [], fs)
        m2.update()
        o2 = bpy.data.objects.new(name, m2)
        bpy.context.collection.objects.link(o2)
        o2.data.materials.append(BR.make_diffuse(name, rho))

    # PREVIEW_NO_MARKER=1 drops the reference post for report-grade images.
    # For orientation CHECKS the marker stays on by default; a picture used
    # to verify up-ness must keep the thing that encodes up-ness.
    import os as _os
    if not _os.environ.get("PREVIEW_NO_MARKER"):
        post = 0.35 * pitch
        _box(-1.6 * pitch, -1.6 * pitch + post, 0.0, depth / 3.0,
             -post / 2.0, post / 2.0, "up_post", 0.95)
        # and a dark sill lying at y = 0 beside it
        _box(-1.6 * pitch, 0.0, -0.12 * pitch, 0.0,
             -post / 2.0, post / 2.0, "sill", 0.25)

    # a key light, so the silhouette reads. NOT a measurement setup.
    d = bpy.data.lights.new("key", type="SUN")
    d.energy = 3.0
    o = bpy.data.objects.new("key", d)
    o.rotation_euler = (math.radians(55), 0.0, math.radians(35))
    bpy.context.collection.objects.link(o)

    span = cells * pitch
    cx, cz = span / 2.0, 0.0
    res = 520
    # elev is measured FROM THE PANEL NORMAL, so 0 is the top-down view the
    # measurement takes and 90 is edge-on. Named for what they show, because
    # calling the top-down one "front" is how the last mix-up started.
    shots = [("topdown", 0.0), ("edge", 90.0), ("threequarter", 35.0)]
    paths = []
    for name, elev in shots:
        for ob2 in list(bpy.data.objects):
            if ob2.type == "CAMERA":
                bpy.data.objects.remove(ob2, do_unlink=True)
        ortho = max(span, depth) * 1.35
        cam = BR.setup_camera(cx, cz, ortho, res, res, elev_deg=elev,
                              dist=max(span, depth) * 8.0)
        # `setup_camera` rolls the camera 180 degrees about its view axis,
        # which is right for the measurement framing and upside down for a
        # human looking at an edge-on view: the panel's outside came out at the
        # BOTTOM of the frame. Undo the roll here so +y -- out of the panel --
        # is up on screen, which is the only orientation anyone reads without
        # having to think about it.
        if abs(elev - 90.0) < 1e-6:
            cam.rotation_euler[2] = 0.0
        p = out_png.replace(".png", "_%s.png" % name)
        BR.render_to(p.replace(".png", ".exr"), p)
        try:
            os.remove(p.replace(".png", ".exr"))
        except OSError:
            pass
        paths.append(p)

    # stitch the three side by side so one image answers the question
    try:
        from PIL import Image
        ims = [Image.open(p).convert("RGB") for p in paths]
        w = sum(i.width for i in ims)
        h = max(i.height for i in ims)
        sheet = Image.new("RGB", (w, h), (20, 22, 25))
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0))
            x += i.width
        sheet.save(out_png)
        for p in paths:
            os.remove(p)
    except Exception:
        pass
    return out_png


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    fam = argv[0]
    prm = json.loads(argv[1])
    out = argv[2] if len(argv) > 2 else "/tmp/preview_%s.png" % fam
    print(render(fam, prm, out))
