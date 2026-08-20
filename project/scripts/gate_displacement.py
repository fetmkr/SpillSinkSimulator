"""GATE 10: the returned line lands about half a depth away. Is that a law?

GATE 8 measured, at theta -40, the offset between the panel's returned-line
centroid and the flat control's, phase by phase:

    d18  8.92 mm   d20  9.37   d22  9.27   d50 24.71   d90 44.58
    ratio to depth 0.50 / 0.47 / 0.42 / 0.49 / 0.50, swing across phases <1 mm

Five designs on one ratio is suggestive, not a law: pitch and depth moved
together in all five. Hold pitch fixed and sweep depth alone.

A flat wall returns from its surface. A pyramid field returns from somewhere
inside the well, and an oblique view turns that depth into a lateral offset.
If the escape depth were a fixed fraction f of the well, the offset would be
f * depth * tan(theta) -- so the slope against depth should also scale with
tan(theta), which is the second half of this test.

PRE-REGISTERED:
  D1  at fixed pitch, offset is linear in depth through the origin, R^2 > 0.98
  D2  the slope at theta -40 is 0.45-0.55
  D3  slope(theta) / tan(theta) is constant across theta 20/40/60 within 15 %.
      If it holds, the escape depth is f = slope/tan(theta) of the well and the
      law is  offset = f * depth * tan(theta).
      If D3 fails, the offset is not a simple escape-depth effect and must be
      reported as measured rather than explained.
  D4  offset does NOT depend on pitch at fixed depth (checked at the end)
"""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import numpy as np, bpy  # noqa: E402
import blender_render as BR, form_buildable as FB, rig_v2 as R2  # noqa: E402
from form_metrics import z_profile  # noqa: E402

OUT="/tmp/simsrv/disp"; os.makedirs(OUT, exist_ok=True)

def centroid(p):
    i=np.arange(p.size,dtype=float); t=p.sum()
    return float((i*p).sum()/t) if t>1e-20 else p.size/2.0

def offset(pitch, depth, theta, face, beam=7.5, n_phase=6, spp=256):
    prm=dict(kind="pyramid",pitch=pitch,depth=depth,tip_flat=0.1,
             face_w=face,face_h=face,margin_depths=2.0,backing=2.0)
    sc=R2.build(prm,samples=spp); p,ctrl_x0=sc["p"],sc["ctrl_x0"]
    R2.assert_clear(sc); total_w=sc["total_w"]; ortho=total_w*1.02
    res_x,res_y,mmpx,capped=R2.resolution_for(ortho, p.face_h)
    wp=(0.0,p.face_w,-p.face_h/2,p.face_h/2)
    wc=(ctrl_x0,ctrl_x0+p.face_w,-p.face_h/2,p.face_h/2)
    cx,cz=total_w/2.0,0.0; BR.configure_cycles(spp,True)
    ds=[]
    for i in range(n_phase):
        dz=(-pitch/2.0)+pitch*i/n_phase
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
        BR.setup_camera(cx,cz,ortho,res_x,res_y,elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(theta,cx,cz,beam,total_w,strength=400.0,
                      spread_deg=FB.SPREAD_DEG,target_z=dz)
        f=os.path.join(OUT,"d.exr"); BR.render_to(f,f.replace(".exr",".png"))
        arr=BR.read_exr(f,res_x,res_y)
        pp=z_profile(arr,BR.to_pixel_window(wp)); pc=z_profile(arr,BR.to_pixel_window(wc))
        ds.append((centroid(pp)-centroid(pc))*mmpx)
        try: os.remove(f)
        except OSError: pass
    return float(np.mean(ds)), float(np.ptp(ds)), mmpx, capped

rows=[]
print("=== D1/D2: pitch 4 fixed, depth swept, theta -40 ===",flush=True)
xs=[];ys=[]
for depth in (10.0,20.0,30.0,50.0,80.0):
    m,s,mm,cap=offset(4.0,depth,-40.0,max(300.0,depth*6))
    xs.append(depth); ys.append(m); rows.append({"g":"D1","pitch":4.0,"depth":depth,
        "theta":-40.0,"offset":m,"swing":s})
    print("  depth %5.1f -> offset %8.3f mm  (swing %.2f)  ratio %.3f"
          % (depth,m,s,m/depth),flush=True)
    json.dump(rows,open(os.path.join(OUT,"disp.json"),"w"),indent=1)
X=np.array(xs);Y=np.array(ys)
slope=float((X*Y).sum()/(X*X).sum())     # through the origin
ss=float(1-((Y-slope*X)**2).sum()/((Y-Y.mean())**2).sum())
print("  slope through origin %.4f   R2 %.4f  -> D1 %s  D2 %s"
      % (slope,ss,"PASS" if ss>0.98 else "**FAIL**",
         "PASS" if 0.45<=slope<=0.55 else "**FAIL**"),flush=True)

print("\n=== D3: slope vs tan(theta), depth 50 ===",flush=True)
for th in (-20.0,-40.0,-60.0):
    m,s,mm,cap=offset(4.0,50.0,th,400.0)
    t=math.tan(math.radians(abs(th)))
    rows.append({"g":"D3","theta":th,"offset":m,"f":m/50.0/t})
    print("  theta %5.0f  offset %8.3f mm  offset/depth %.3f  /tan %.3f"
          % (th,m,m/50.0,m/50.0/t),flush=True)
    json.dump(rows,open(os.path.join(OUT,"disp.json"),"w"),indent=1)

print("\n=== D4: depth 50 fixed, pitch swept, theta -40 ===",flush=True)
for pitch in (2.0,4.0,10.0):
    m,s,mm,cap=offset(pitch,50.0,-40.0,400.0)
    rows.append({"g":"D4","pitch":pitch,"offset":m})
    print("  pitch %5.1f -> offset %8.3f mm  ratio %.3f" % (pitch,m,m/50.0),flush=True)
    json.dump(rows,open(os.path.join(OUT,"disp.json"),"w"),indent=1)
print("\n@@DONE@@")
