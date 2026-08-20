"""GATES 11-12: is the answer independent of how the mesh is built?

GATE 2 proved scale invariance with the CELL COUNT held at 25 x 25 -- triangle
count was exactly 7512 on every rung. So it controlled for mesh density rather
than testing it. Two things it therefore never asked:

GATE 11  CELL-COUNT SUFFICIENCY. Fixed pitch and depth, panel swept, so the
         sample holds 5, 10, 25, 50 cells a side. A periodic surface should
         not care once the sample is "enough" cells. Where is enough?
         This is the one that decides whether a 100 mm coupon can stand in for
         a wall, and whether the d500 report's 10x10 cells was a sample at all.

GATE 12  TESSELLATION. A pyramid face is exactly planar, so its triangulation
         is exact and there is nothing to converge. A CONE is not: geom_floor
         builds it from radial_seg = 24 flat facets, a FIXED count, so every
         published cone number is really a 24-gonal pyramid. Sweep radial_seg
         and see whether the cone's rho_dh has converged at 24.
         The project ranks cone against pyramid on differences of a few
         percent, so a tessellation bias of that size would decide it.

PRE-REGISTERED:
  M1  rho_dh is flat from 10 cells upward, within the 1-2 % floor; 5 cells may
      be off (edge cells are a large fraction of a small sample).
  M2  the cone's rho_dh still moves between radial_seg 24 and 48. A 24-gon has
      15 deg facets and the family's whole claim is rotational symmetry --
      "no azimuth has a flat to catch the beam" -- which a 24-gon only
      approximates.
  M3  if M2 holds, the published cone-vs-pyramid comparison is contaminated by
      a tessellation choice and must be re-run at converged segments.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import bpy, blender_render as BR, rig_v2 as R2  # noqa: E402

OUT="/tmp/simsrv/mesh"; os.makedirs(OUT,exist_ok=True)
THETAS=[0.0,-40.0]; SPP=384

def rho(params, face, spp=SPP):
    prm=dict(params); prm.update(face_w=face,face_h=face,
                                 margin_depths=2.0,backing=2.0)
    sc=R2.build(prm,samples=spp); p,ctrl_x0=sc["p"],sc["ctrl_x0"]
    R2.assert_clear(sc); total_w=sc["total_w"]; ortho=total_w*1.02
    res_x,res_y,mmpx,capped=R2.resolution_for(ortho, p.face_h)
    wp,wc=R2.full_face_windows(p,ctrl_x0,inset_mm=R2.sky_inset_mm(mmpx))
    cx,cz=total_w/2.0,0.0; BR.configure_cycles(spp,True)
    ntri=sum(len(o.data.loop_triangles) if o.data.loop_triangles else 0
             for o in bpy.data.objects if o.type=="MESH")
    if not ntri:
        for o in bpy.data.objects:
            if o.type=="MESH": o.data.calc_loop_triangles()
        ntri=sum(len(o.data.loop_triangles) for o in bpy.data.objects
                 if o.type=="MESH")
    out={}
    for th in THETAS:
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
        BR.setup_camera(cx,cz,ortho,res_x,res_y,elev_deg=th)
        BR.set_world(1.0)
        f=os.path.join(OUT,"m.exr"); BR.render_to(f,f.replace(".exr",".png"))
        arr=BR.read_exr(f,res_x,res_y)
        out["%+.0f"%th]=BR.window_stats(arr,BR.to_pixel_window(wp))["mean"]
        c=BR.window_stats(arr,BR.to_pixel_window(wc))["mean"]
        out["ctrl%+.0f"%th]=c
        try: os.remove(f)
        except OSError: pass
    return out,res_x,mmpx,capped,ntri

rows=[]
print("=== GATE 11: cells a side (pitch 4, depth 20 fixed) ===",flush=True)
vals={0.0:[],-40.0:[]}
for cells in (5,10,25,50):
    face=4.0*cells
    o,rx,mm,cap,nt=rho(dict(kind="pyramid",pitch=4.0,depth=20.0,tip_flat=0.1),face)
    rows.append({"g":11,"cells":cells,"face":face,"tris":nt,**o})
    for th in THETAS: vals[th].append(o["%+.0f"%th])
    print("  %2d x %2d cells  face %6.0f  tris %7d  %5d px | th0 %.6f  th-40 %.6f"
          " | ctrl %.6f" % (cells,cells,face,nt,rx,o["+0"],o["-40"],o["ctrl+0"]),flush=True)
    json.dump(rows,open(os.path.join(OUT,"mesh.json"),"w"),indent=1)
for th in THETAS:
    v=vals[th][1:]      # from 10 cells up
    m=sum(v)/len(v); sp=(max(v)-min(v))/m
    print("  th %+.0f  10-cells-and-up mean %.6f  spread %.2f %%  -> %s"
          % (th,m,100*sp,"PASS" if sp<=0.02 else "**FAIL**"),flush=True)

print("\n=== GATE 12: cone tessellation (pitch 5.5, depth 30) ===",flush=True)
prev=None
for seg in (8,12,24,48,96):
    o,rx,mm,cap,nt=rho(dict(kind="cone",pitch=5.5,depth=30.0,tip_radius=0.2,
                            jitter=0.0,radial_seg=seg,height_seg=12),150.0)
    d="" if prev is None else "  (%+.2f %%)"%(100*(o["+0"]-prev)/prev)
    rows.append({"g":12,"radial_seg":seg,"tris":nt,**o})
    print("  radial_seg %3d  tris %7d | th0 %.6f%s  th-40 %.6f | ctrl %.6f"
          % (seg,nt,o["+0"],d,o["-40"],o["ctrl+0"]),flush=True)
    prev=o["+0"]
    json.dump(rows,open(os.path.join(OUT,"mesh.json"),"w"),indent=1)
print("\n@@DONE@@")
