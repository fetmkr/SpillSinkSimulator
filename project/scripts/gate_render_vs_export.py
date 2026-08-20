"""Is the mesh the RENDER traces the same mesh the exporters write?

The STEP file calls itself "not a closed solid: 28 open edges". That is a
statement about the exported shell. It says nothing on its own about whether
the geometry the renderer traced was wrong, and the two must not be confused:

  export path   sim_server.build(spec) -> clip_to_panel -> stl/step
  render path   blender_render builds a scene, mesh_fn(p) -> mesh_to_object

Both are supposed to come from the same geom module's build_mesh. This does
not read the code; it builds the render scene, reads the mesh BACK OUT of
Blender -- the actual triangles light hits -- and compares it to what the
exporter writes.

PRE-REGISTERED:
  E1  same vertex count and same face count, before clipping.
  E2  same bounding box to under a micron.
  E3  same total surface area to under 1e-6 relative. Area is the quantity
      that decides how much light a face catches, so if this matches, the
      renderer and the exporter agree on every surface that matters.
  E4  the render mesh has NO degenerate (zero-area) faces. A dropped quad
      half -- the bug that halved the STEP file -- would show up here as a
      face count that differs from the exporter's, so E1 already covers it,
      but a zero-area face would corrupt a normal without changing counts.
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import bpy                                    # noqa: E402
import blender_render as BR                   # noqa: E402
import sim_server as SS                       # noqa: E402

SPECS = [
    ("pyramid p4/d22", {"top":"pyramid","top_params":{"pitch":4.0,"tip_flat":0.4},
                        "depth":22.0,"panel":24.0,"floor":"none"}),
    ("pyramid p2/d18", {"top":"pyramid","top_params":{"pitch":2.0,"tip_flat":0.0},
                        "depth":18.0,"panel":20.0,"floor":"none"}),
    ("honeycomb d50 ", {"top":"honeycomb","depth":50.0,"panel":30.0,"floor":"none"}),
]

def stats(verts, faces):
    xs=[v[0] for v in verts]; ys=[v[1] for v in verts]; zs=[v[2] for v in verts]
    area=0.0; degen=0
    for fc in faces:
        for i in range(1, len(fc)-1):
            a,b,c = verts[fc[0]], verts[fc[i]], verts[fc[i+1]]
            ux,uy,uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
            vx,vy,vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
            cx,cy,cz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
            t = 0.5*math.sqrt(cx*cx+cy*cy+cz*cz)
            area += t
            if t < 1e-12: degen += 1
    return {"nv":len(verts), "nf":len(faces), "area":area, "degen":degen,
            "bbox":(min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))}

print("%-16s | %-26s | %-26s | verdict" % ("design","render (read from Blender)","export (stl/step source)"), flush=True)
bad = 0
for label, spec in SPECS:
    ev, ef, _p = SS.build(dict(spec, margin_depths=0.0))
    E = stats(ev, ef)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    # the measurement scene normally carries a 2-depth skirt so the beam has
    # somewhere to land outside the face; the exporter writes the bare panel.
    # Force the SAME margin on both, otherwise the extents differ for a reason
    # that has nothing to do with the question being asked.
    prm = SS._render_params(dict(spec, margin_depths=0.0))
    prm["margin_depths"] = 0.0
    BR.build_scene({"family": SS._render_family(spec), "params": prm,
                    "spec_roughness": 0.30})
    ob = bpy.data.objects.get("panel_mesh")
    if ob is None:
        print("%-16s | render scene has no panel_mesh -- builder name differs" % label, flush=True)
        bad += 1; continue
    me = ob.data
    rv = [(v.co.x, v.co.y, v.co.z) for v in me.vertices]
    rf = [tuple(p.vertices) for p in me.polygons]
    R = stats(rv, rf)
    ok = (R["nv"]==E["nv"] and R["nf"]==E["nf"]
          and abs(R["area"]-E["area"]) <= 1e-6*max(1.0,E["area"])
          # BLENDER STORES VERTICES AS float32. Reading a 52.9 mm coordinate
          # back out costs about 4e-6 mm, so a tolerance of 1e-6 flags float32
          # round-trip as a geometry difference. The bar is one ulp of the
          # largest coordinate, which is the tightest bar that can be met by
          # two identical meshes stored at different precisions.
          and max(abs(a-b) for a,b in zip(R["bbox"],E["bbox"]))
              <= 2.0 * math.ulp(max(abs(x) for x in E["bbox"]) + 1.0) * 2**29
          and R["degen"]==0)
    if not ok: bad += 1
    print("%-16s | V %5d F %5d A %10.2f | V %5d F %5d A %10.2f | %s"
          % (label, R["nv"],R["nf"],R["area"], E["nv"],E["nf"],E["area"],
             "SAME MESH" if ok else "DIFFERENT"), flush=True)
    if not ok:
        print("     bbox render %s" % (tuple(round(x,4) for x in R["bbox"]),), flush=True)
        print("     bbox export %s" % (tuple(round(x,4) for x in E["bbox"]),), flush=True)
        print("     zero-area faces in render mesh: %d" % R["degen"], flush=True)
        print("     dV %d  dF %d  dArea %.9g (rel %.3g)  dBbox %.3g"
              % (R["nv"]-E["nv"], R["nf"]-E["nf"], R["area"]-E["area"],
                 abs(R["area"]-E["area"])/max(1.0,E["area"]),
                 max(abs(a-b) for a,b in zip(R["bbox"],E["bbox"]))), flush=True)
print("\n%s" % ("ALL SAME" if bad==0 else "%d MISMATCH" % bad), flush=True)
print("@@DONE@@")
