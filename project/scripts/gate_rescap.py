"""GATE 14: does the pixel cap bias the answer, or is it only slow?

RES_CAP = 6000 is a render-time budget I chose, with no physical basis. Above
it, mm-per-pixel drifts again -- exactly the defect the fixed-density change was
made to remove. Warning about it is not the same as knowing whether it matters.

So measure the same scene at the capped resolution and at the resolution the
fixed density actually asks for, and compare all three axes.

  panel 1000, pitch 4: the protocol wants ~9980 px; the old 6000 budget gave
                       0.357 mm/px instead of 0.215
  panel  500, pitch 4: wants ~5240 px, under the old budget -- a control that
                       should show no difference at all

RES_CAP has since been raised to 20000 and reclassified as a MEMORY ceiling,
not a quality knob, so the "capped" arm below is history rather than current
behaviour. It is still worth measuring: it tells us how much the study's older
large-panel numbers were biased by coarse sampling.

PRE-REGISTERED:
  R1  rho_dh is unmoved (< 1 %). It is an area average and GATE 2 already showed
      it survives a 13x change in pixel size.
  R2  smear moves little (< 2 %). It is a ratio of two widths measured in the
      same frame, so a coarser grid blurs numerator and denominator together.
  R3  head-on DOES move, and downward at coarse pixels. It is a PEAK, and a
      peak is the one statistic a bigger pixel must dilute. Today's ladder
      already hints at it: head-on rose 0.1776 -> 0.1850 as the sample grew.
  R4  the 500 mm control shows no change on any axis, because neither run is
      capped -- if it does, the difference is not the cap.

If R3 holds, the cap is not a slowdown, it is a bias on one axis, and either it
goes or head-on is not quotable on a capped scene.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import numpy as np, bpy  # noqa: E402
import blender_render as BR, form_buildable as FB, rig_v2 as R2  # noqa: E402
from form_metrics import z_profile, recentre, rms_width  # noqa: E402

OUT="/tmp/simsrv/rescap"; os.makedirs(OUT,exist_ok=True)

def run(face, cap, pitch=4.0, depth=22.0, tip=0.4, beam=7.5, nph=8, spp=256):
    old=R2.RES_CAP; R2.RES_CAP=cap
    try:
        prm=dict(kind="pyramid",pitch=pitch,depth=depth,tip_flat=tip,
                 face_w=face,face_h=face,margin_depths=2.0,backing=2.0)
        sc=R2.build(prm,samples=spp); p,ctrl_x0=sc["p"],sc["ctrl_x0"]
        total_w=sc["total_w"]; ortho=total_w*1.02
        rx,ry,mm,capped=R2.resolution_for(ortho, p.face_h)
        wp,wc=R2.full_face_windows(p,ctrl_x0)
        cx,cz=total_w/2.0,0.0; BR.configure_cycles(spp,True)
        # --- totals, same frame convention as the gates
        wpt,wct=R2.full_face_windows(p,ctrl_x0,inset_mm=R2.sky_inset_mm(mm))
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
        BR.setup_camera(cx,cz,ortho,rx,ry,elev_deg=-40.0)
        BR.set_world(1.0)
        f=os.path.join(OUT,"t.exr"); BR.render_to(f,f.replace(".exr",".png"))
        a=BR.read_exr(f,rx,ry)
        rho=BR.window_stats(a,BR.to_pixel_window(wpt))["mean"]
        ctl=BR.window_stats(a,BR.to_pixel_window(wct))["mean"]
        os.remove(f)
        # --- smear + head-on
        accp=np.zeros(FB.NWIN); accc=np.zeros(FB.NWIN); pk=[]
        for i in range(nph):
            dz=(-pitch/2.0)+pitch*i/nph
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT","CAMERA"): bpy.data.objects.remove(o,do_unlink=True)
            BR.setup_camera(cx,cz,ortho,rx,ry,elev_deg=0.0)
            BR.set_world(0.0)
            BR.add_stripe(0.0,cx,cz,beam,total_w,strength=400.0,
                          spread_deg=FB.SPREAD_DEG,target_z=dz)
            f=os.path.join(OUT,"s.exr"); BR.render_to(f,f.replace(".exr",".png"))
            arr=BR.read_exr(f,rx,ry)
            pp=recentre(z_profile(arr,BR.to_pixel_window(wp)),FB.NWIN)
            pc=recentre(z_profile(arr,BR.to_pixel_window(wc)),FB.NWIN)
            accp+=pp; accc+=pc
            pk.append(float(pp.max())/float(pc.max()) if pc.max()>0 else float("nan"))
            os.remove(f)
        return {"res_x":rx,"mm_per_px":mm,"capped":capped,"rho":rho,"ctrl":ctl,
                "smear":rms_width(accp,mm)/rms_width(accc,mm),
                "head_on":float(np.nanmean(pk))}
    finally:
        R2.RES_CAP=old

rows=[]
for face,label in ((1000.0,"판 1000 (상한에 걸림)"),(500.0,"판 500 (대조, 안 걸림)")):
    print("\n=== %s ===" % label,flush=True)
    a=run(face,6000)          # the OLD budget, kept as the "before"
    b=run(face,25000)         # unconstrained: what the protocol density asks
    rows.append({"face":face,"capped":a,"full":b})
    print("  %-10s %6d px  %.3f mm/px | rho %.6f | smear %8.4f | head-on %.5f"
          % ("capped",a["res_x"],a["mm_per_px"],a["rho"],a["smear"],a["head_on"]),flush=True)
    print("  %-10s %6d px  %.3f mm/px | rho %.6f | smear %8.4f | head-on %.5f"
          % ("full",b["res_x"],b["mm_per_px"],b["rho"],b["smear"],b["head_on"]),flush=True)
    for k,lim in (("rho",0.01),("smear",0.02),("head_on",0.02)):
        d=(a[k]-b[k])/b[k]
        print("     %-9s %+7.2f %%   %s" % (k,100*d,
              "ok" if abs(d)<=lim else "**BIASED**"),flush=True)
    json.dump(rows,open(os.path.join(OUT,"rescap.json"),"w"),indent=1,default=str)
print("\n@@DONE@@",flush=True)
