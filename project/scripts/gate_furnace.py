"""GATE 13 (rebuilt): the white furnace test on the REAL panel geometry.

The first attempt was wrong and its own numbers said so: rho = 0.99 at 128
bounces returned 0.989993 where truncation predicts ~0.72, and rho = 1.0
returned exactly 1.0. Too clean. The cube was 100 mm across and the camera sat
at 60 mm -- outside it -- so it was reading the OUTSIDE of a flat wall, which
of course returns its own rho. It measured the BSDF, not the cavity.

The test that matters, and the one already on record as failing:
FINDINGS_renderer_disagreement.md notes a rho = 1 comb returning 0.673 in
Cycles and 0.561 in Mitsuba, explained as "rho = 1 never decays, so 128 bounces
cannot finish the sum". Correct, and not a pass. So run it where the claim can
be tested: the real pyramid field, Lambertian rho = 1, bounces swept.

Under a uniform environment of radiance 1, a rho = 1 surface is
indistinguishable from the environment -- whatever the geometry, however many
times light bounces. The reading MUST climb toward 1.000 as bounces rise. If it
plateaus below 1, the renderer is losing energy, and every published number
needs a systematic correction.

Two controls, both necessary:
  FLAT rho=1   must read 1.000 at ANY bounce count (one bounce is enough on a
               plane, so this separates "loses energy" from "needs bounces")
  FLAT rho=0.5 must read 0.500 -- the BSDF check the broken version accidentally
               ran, kept because it is still worth having

PRE-REGISTERED:
  W1  flat rho=1 reads 1.000 +- 0.002 at every bounce count
  W2  the pyramid field at rho=1 climbs monotonically with bounces
  W3  by 2048 bounces it is within 2 % of 1.000. The mean free path in a
      pitch-4 / depth-20 valley is ~9 bounces (the project's own figure), so
      2048 is ~200 traversals and any real cavity should be saturated.
  W4  if W3 fails, report the plateau value -- that IS the renderer's energy
      leak, and it is the single most important number for the paper.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import bpy, blender_render as BR, rig_v2 as R2  # noqa: E402

OUT="/tmp/simsrv/furnace"; os.makedirs(OUT,exist_ok=True)

def read(bounces, spp=512, params=None, rho=1.0):
    """Uniform world of radiance 1; read the panel window. No control plate is
    needed -- the expected answer is rho itself, from first principles."""
    prm=dict(params); prm.update(face_w=prm.pop("face",100.0))
    prm["face_h"]=prm["face_w"]; prm.update(margin_depths=2.0,backing=2.0)
    sc=R2.build(prm,samples=spp,lambert_rho=rho)
    p,ctrl_x0=sc["p"],sc["ctrl_x0"]; total_w=sc["total_w"]; ortho=total_w*1.02
    res_x,res_y,mmpx,_=R2.resolution_for(ortho, p.face_h)
    wp,_=R2.full_face_windows(p,ctrl_x0,inset_mm=R2.sky_inset_mm(mmpx))
    BR.configure_cycles(spp,True)
    scn=bpy.context.scene
    for k in ("max_bounces","diffuse_bounces","glossy_bounces",
              "transmission_bounces","transparent_max_bounces"):
        try: setattr(scn.cycles,k,bounces)
        except Exception: pass
    for o in list(bpy.data.objects):
        if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
    BR.setup_camera(total_w/2.0,0.0,ortho,res_x,res_y,elev_deg=0.0)
    BR.set_world(1.0)
    f=os.path.join(OUT,"w.exr"); BR.render_to(f,f.replace(".exr",".png"))
    arr=BR.read_exr(f,res_x,res_y)
    v=BR.window_stats(arr,BR.to_pixel_window(wp))["mean"]
    try: os.remove(f)
    except OSError: pass
    return v

FLAT=dict(kind="pyramid",pitch=4.0,depth=0.001,tip_flat=0.0,face=100.0)
PYR =dict(kind="pyramid",pitch=4.0,depth=20.0,tip_flat=0.1,face=100.0)
rows=[]
print("=== W1: FLAT rho=1 (must read 1.000 at any bounce count) ===",flush=True)
for b in (1,8,128):
    v=read(b,params=FLAT,rho=1.0); rows.append({"g":"W1","b":b,"v":v})
    print("   bounces %5d -> %.6f   %s"
          % (b,v,"PASS" if abs(v-1)<=0.002 else "**FAIL**"),flush=True)
print("\n=== W1b: FLAT rho=0.5 ===",flush=True)
v=read(128,params=FLAT,rho=0.5); rows.append({"g":"W1b","v":v})
print("   -> %.6f   %s" % (v,"PASS" if abs(v-0.5)<=0.002 else "**FAIL**"),flush=True)
print("\n=== W2/W3: PYRAMID field rho=1, bounces swept ===",flush=True)
prev=None
for b in (8,32,128,512,2048):
    v=read(b,params=PYR,rho=1.0); rows.append({"g":"W2","b":b,"v":v})
    d="" if prev is None else " (%+.2f %%)"%(100*(v-prev)/max(prev,1e-9))
    print("   bounces %5d -> %.6f%s   deficit %.4f" % (b,v,d,1.0-v),flush=True)
    prev=v
    json.dump(rows,open(os.path.join(OUT,"furnace.json"),"w"),indent=1)
print("\n   W3 (within 2 %% of 1.000 at 2048): %s"
      % ("PASS" if abs(prev-1)<=0.02 else "**FAIL — plateau %.6f, leak %.2f %%**"
         % (prev,100*(1-prev))),flush=True)
print("@@DONE@@",flush=True)
