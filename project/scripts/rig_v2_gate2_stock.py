"""GATE 2 run on the STOCK rig — the 'before' the repair has to earn.

rig_v2 passed scale invariance at 1.70 % (theta 0) and 0.99 % (theta -40) over
a 25x size span. A repair is only justified if the thing it replaced fails the
same test, so run the identical ladder through the stock protocol: constant
res_x = 1400, GAP = 100, windows inset 20 % in x and 30 % in z.

Identical geometry, identical angles, identical statistic. The only difference
is the instrument.

PRE-REGISTERED:
  S1  the stock ladder's spread is far outside the repaired rig's 1.7 % -- I
      expect tens of percent, because mm-per-pixel runs from 0.08 to 1.9 mm
      across these rungs and the window is a fraction of a growing face.
  S2  the failure grows with size: the small rungs (pitch 2, 4) agree with the
      repaired rig, the large ones diverge.
  S3  the stock control still reads 0.050000 throughout (pyramids expose almost
      nothing at y = 0, as GATE 1 established), so this is NOT a control-plate
      failure -- it is sampling and windowing alone.
"""

import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
import form_buildable as FB  # noqa: E402

OUT = "/tmp/simsrv/rigv2"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -40.0]
SPP = 256


def rho_stock(params, face):
    prm = dict(params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    cfg = {"tag": "stock", "out_dir": OUT, "results_dir": OUT, "samples": SPP,
           "res_x": 1400, "res_y": 620, "gpu": True, "spec_roughness": 0.30,
           "params": prm, "renders": [], "material_mode": "coating",
           "family": "floor"}
    b, s = BR.coating_split(0.76)
    cfg["coating"] = {"body": b, "spec_scale": s, "roughness": 0.30}
    cfg.update({k: v for k, v in FB.COAT.items() if k != "spec_roughness"})
    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    ortho = total_w * 1.02
    res_x, res_y = 1400, 620
    mmpx = ortho / res_x
    w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)
    cx, cz = total_w / 2.0, 0.0
    BR.configure_cycles(SPP, True)
    out = {}
    for th in THETAS:
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=th)
        BR.set_world(1.0)
        f = os.path.join(OUT, "s2.exr")
        BR.render_to(f, f.replace(".exr", ".png"))
        arr = BR.read_exr(f, res_x, res_y)
        out["%+.0f" % th] = {
            "panel": BR.window_stats(arr, BR.to_pixel_window(w_panel))["mean"],
            "ctrl": BR.window_stats(arr, BR.to_pixel_window(w_ctrl))["mean"]}
        try:
            os.remove(f)
        except OSError:
            pass
    return {"rho": out, "res_x": res_x, "mm_per_px": mmpx,
            "window_mm": w_panel[3] - w_panel[2],
            "gate1": max(abs(v["ctrl"] - 0.05) for v in out.values()) <= 1e-4}


def main():
    rows = []
    print("\n===== GATE 2 on the STOCK rig =====", flush=True)
    for pitch in [2.0, 4.0, 10.0, 25.0, 50.0]:
        prm = dict(kind="pyramid", pitch=pitch, depth=pitch * 5.0,
                   tip_flat=pitch * 0.025)
        face = pitch * 25.0
        r = rho_stock(prm, face)
        rows.append({"pitch": pitch, "face": face, **r})
        print("  pitch %5.1f  face %6.0f | 1400 px  %6.3f mm/px  window "
              "%7.1f mm | th0 %.6f  th-40 %.6f | control %s"
              % (pitch, face, r["mm_per_px"], r["window_mm"],
                 r["rho"]["+0"]["panel"], r["rho"]["-40"]["panel"],
                 "OK" if r["gate1"] else "FAIL"), flush=True)
    for th in ("+0", "-40"):
        vals = [r["rho"][th]["panel"] for r in rows]
        m = sum(vals) / len(vals)
        spread = (max(vals) - min(vals)) / m
        print("  th %-4s mean %.6f  spread %.2f %%  -> %s"
              % (th, m, 100 * spread,
                 "PASS" if spread <= 0.03 else "**FAIL**"), flush=True)
    with open(os.path.join(OUT, "gate2_stock.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("\n@@DONE@@")


if __name__ == "__main__":
    main()
