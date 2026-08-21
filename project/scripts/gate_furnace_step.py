"""ONE furnace reading per Blender process. Prints one JSON line.

Why one process per point: sweeping bounce counts inside a single Blender
aborts partway through with

    ccl::MetalKernelPipeline::compile()
    ccl::path_cache_get(...)
    BUG_IN_CLIENT_OF_LIBMALLOC: POINTER BEING FREED WAS NOT ALLOCATED

[confirmed: ~/Library/Logs/DiagnosticReports/Blender-2026-08-20-161521.ips]
That is Cycles' Metal shader-cache thread double-freeing when it recompiles,
not anything about the geometry -- and it exits 0, so the sweep looked like it
had simply stopped. A fresh process compiles once and never recompiles.

Cases:
  bare   a SINGLE quad, no rig, no control, no backing: nothing can occlude
         it, so a Lambertian of albedo r under a uniform sky of radiance 1
         must read exactly r at ONE bounce. This is the BSDF check, and it is
         the check the old W1b was trying to make -- but W1b read the rig's
         plate, which sits in a tray and sees its own dark surround, so it
         read 0.354 for r = 0.5 and called the renderer wrong.
  flat   the rig's plate: converges to r only for r = 1 (a perfect furnace);
         for r < 1 the surround is darker than the sky and it reads LESS.
  pyr    the real pitch-4 / depth-20 field. This is the number for the paper.

usage: blender -b -P gate_furnace_step.py -- <case> <bounces> <rho> [spp]
"""
import os, sys, json, math
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import bpy, blender_render as BR, rig_v2 as R2  # noqa: E402
import numpy as np  # noqa: E402

a=sys.argv[sys.argv.index("--")+1:]
CASE=a[0]; B=int(a[1]); RHO=float(a[2]); SPP=int(a[3]) if len(a)>3 else 512
OUT="/tmp/simsrv/furnace"; os.makedirs(OUT,exist_ok=True)

def set_bounces(b):
    c=bpy.context.scene.cycles
    for k in ("max_bounces","diffuse_bounces","glossy_bounces",
              "transmission_bounces","transparent_max_bounces"):
        try: setattr(c,k,b)
        except Exception: pass

if CASE=="bare":
    BR.configure_cycles(SPP,True); set_bounces(B)
    for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
    S=200.0
    v=[(-S,0.0,-S),(S,0.0,-S),(S,0.0,S),(-S,0.0,S)]
    BR.mesh_to_object(v,[(0,1,2,3)],"bare",BR.make_diffuse("bare_m",RHO))
    res=600; ortho=100.0
    BR.setup_camera(0.0,0.0,ortho,res,res,elev_deg=0.0)
    BR.set_world(1.0)
    f=os.path.join(OUT,"bare.exr"); BR.render_to(f,f.replace(".exr",".png"))
    arr=BR.read_exr(f,res,res)
    # dead centre only: nothing else is in the scene, but stay off the rim
    c=arr[res//4:3*res//4, res//4:3*res//4]
    val=float(c.mean()); spread=float(c.max()-c.min())
    print("@@JSON@@"+json.dumps({"case":CASE,"b":B,"rho":RHO,"v":val,
                                 "spread":spread}))
    sys.exit(0)

PRM={"flat":dict(kind="pyramid",pitch=4.0,depth=0.0,tip_flat=0.0),
     "pyr" :dict(kind="pyramid",pitch=4.0,depth=20.0,tip_flat=0.1),
     # the honeycomb, because a geometry check said its walls were stacked and
     # then turned out to be reading its own broken plane key. The furnace is
     # already validated, so ask IT: a cavity that wastes bounces cannot reach
     # 1.000 however many it is given.
     "comb":dict(topology="honeycomb",pitch=6.0,depth=50.0,wall_top=0.08,
                 wall_bot=0.08,jitter=0.0)}[CASE]
F = 60.0 if CASE=="comb" else 100.0
prm=dict(PRM); prm.update(face_w=F,face_h=F,margin_depths=2.0,backing=2.0)
sc=R2.build(prm,samples=SPP,lambert_rho=RHO)
p,cx0=sc["p"],sc["ctrl_x0"]; tw=sc["total_w"]; ortho=tw*1.02
rx,ry,mmpx,_=R2.resolution_for(ortho,p.face_h)
wp,_=R2.full_face_windows(p,cx0,inset_mm=R2.sky_inset_mm(mmpx))
BR.configure_cycles(SPP,True); set_bounces(B)
for o in list(bpy.data.objects):
    if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
BR.setup_camera(tw/2.0,0.0,ortho,rx,ry,elev_deg=0.0)
BR.set_world(1.0)
f=os.path.join(OUT,"%s_%d.exr"%(CASE,B)); BR.render_to(f,f.replace(".exr",".png"))
arr=BR.read_exr(f,rx,ry)
val=float(BR.window_stats(arr,BR.to_pixel_window(wp))["mean"])
try: os.remove(f)
except OSError: pass
print("@@JSON@@"+json.dumps({"case":CASE,"b":B,"rho":RHO,"v":val,
                             "res_x":rx,"mm_per_px":mmpx}))
