"""GATE 1 for rig_v2: the control plate must read 0.050000.

The study's standing rule is that a measurement counts only if the 0.05 diffuse
control in the same frame reads its own rho back. FINDINGS_control_overlap.md
showed 1440 of 2875 recorded rows failing it, worst 0.04234, because the panel
field swallowed the control. rig_v2 moves the control clear; this asserts it.

Run over designs spanning the margin range that caused the failure:

    p4/d20    margin  40 mm   (stock gap 100 was enough -- should pass either way)
    p4/d22    margin  44 mm   the ORDER SPEC
    p10/d90   margin 180 mm   (stock gap 100 fails -- field reaches x=300,
                               control starts at x=200)
    p4/d500   margin 1000 mm  the d500 report's geometry, worst case

PASS is |control - 0.05| <= 1e-4 at every angle. Anything else and the design
numbers built on that frame are not quotable.

Also reported, because it is the number the whole study rests on: the panel's
own rho_dh under the repaired rig beside the value the stock rig gives. If the
headline totals move, that is the most important result of the day.
"""

import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
import rig_v2 as R2  # noqa: E402

OUT = "/tmp/simsrv/rigv2"
os.makedirs(OUT, exist_ok=True)

THETAS = [0.0, -40.0, 40.0]
SPP = 256

CASES = [
    ("p4/d20  study std", dict(kind="pyramid", pitch=4.0, depth=20.0,
                               tip_flat=0.1)),
    ("p4/d22  ORDER SPEC", dict(kind="pyramid", pitch=4.0, depth=22.0,
                                tip_flat=0.4)),
    ("p10/d90 coarse    ", dict(kind="pyramid", pitch=10.0, depth=90.0,
                                tip_flat=0.0)),
    ("p100/d500 the d500", dict(kind="pyramid", pitch=100.0, depth=500.0,
                                tip_flat=0.1)),
]


def measure_totals(params, face, repaired):
    """rho_dh via the standard uniform-hemisphere read, either rig."""
    prm = dict(params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)

    if repaired:
        sc = R2.build(prm, samples=SPP)
        p, ctrl_x0 = sc["p"], sc["ctrl_x0"]
        field_hi, ctrl_lo = R2.assert_clear(sc)
        total_w = sc["total_w"]
        ortho = total_w * 1.02
        res_x, res_y, mmpx, capped = R2.resolution_for(ortho, p.face_h)
        # totals path: the world is radiance 1.0, so keep a few pixels of sky
        # shield. GATE 1's first run ran this at inset 0 and read the control
        # 6 % high off a 1-2 pixel background leak.
        w_panel, w_ctrl = R2.full_face_windows(
            p, ctrl_x0, inset_mm=R2.sky_inset_mm(mmpx))
        gap = sc["gap"]
    else:
        cfg = R2.build.__wrapped__ if False else None
        import form_buildable as FB
        cfg = {"tag": "old", "out_dir": OUT, "results_dir": OUT,
               "samples": SPP, "res_x": 1400, "res_y": 620, "gpu": True,
               "spec_roughness": 0.30, "params": prm, "renders": [],
               "material_mode": "coating", "family": "floor"}
        b, s = BR.coating_split(0.76)
        cfg["coating"] = {"body": b, "spec_scale": s, "roughness": 0.30}
        cfg.update({k: v for k, v in FB.COAT.items() if k != "spec_roughness"})
        BR.clear_scene()
        p, cs, ctrl_x0 = BR.build_scene(cfg)
        total_w = ctrl_x0 + p.face_w
        ortho = total_w * 1.02
        res_x, res_y, mmpx, capped = 1400, 620, ortho / 1400.0, False
        w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)
        xs = [(o.matrix_world @ v.co).x for o in bpy.data.objects
              if o.type == "MESH" and "control" not in o.name
              for v in o.data.vertices]
        field_hi, ctrl_lo, gap = (max(xs) if xs else 0.0), ctrl_x0, BR.GAP

    cx, cz = total_w / 2.0, 0.0
    BR.configure_cycles(SPP, True)
    out = {}
    for th in THETAS:
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=th)
        BR.set_world(1.0)
        f = os.path.join(OUT, "g_%s_%+03.0f.exr" % ("new" if repaired
                                                    else "old", th))
        BR.render_to(f, f.replace(".exr", ".png"))
        arr = BR.read_exr(f, res_x, res_y)
        panel = BR.window_stats(arr, BR.to_pixel_window(w_panel))["mean"]
        ctrl = BR.window_stats(arr, BR.to_pixel_window(w_ctrl))["mean"]
        out["%+.0f" % th] = {"panel": panel, "ctrl": ctrl}
        try:
            os.remove(f)
        except OSError:
            pass
    return {"rho": out, "res_x": res_x, "mm_per_px": mmpx, "capped": capped,
            "gap": gap, "field_hi": field_hi, "ctrl_x0": ctrl_lo,
            "overlap": field_hi >= ctrl_lo}


def main():
    rows = []
    for label, params in CASES:
        face = 100.0
        print("\n=== %s ===" % label, flush=True)
        for repaired in (False, True):
            tag = "REPAIRED" if repaired else "stock   "
            try:
                r = measure_totals(params, face, repaired)
            except AssertionError as e:
                print("   %s  GATE FAILED TO BUILD: %s" % (tag, e), flush=True)
                continue
            worst = max(abs(v["ctrl"] - 0.05) for v in r["rho"].values())
            ok = "PASS" if worst <= 1e-4 else "**FAIL**"
            print("   %s gap %6.0f  field ends x=%7.1f  control x=%7.1f  %s"
                  % (tag, r["gap"], r["field_hi"], r["ctrl_x0"],
                     "OVERLAP" if r["overlap"] else "clear"), flush=True)
            print("        %5d px  %5.3f mm/px%s   control worst |err| "
                  "%.6f  %s"
                  % (r["res_x"], r["mm_per_px"],
                     "  (CAPPED)" if r["capped"] else "", worst, ok),
                  flush=True)
            for th, v in r["rho"].items():
                print("        th %-4s  panel %.6f  control %.6f"
                      % (th, v["panel"], v["ctrl"]), flush=True)
            rows.append({"design": label, "repaired": repaired, **r})
    with open(os.path.join(OUT, "gate1.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("\n@@DONE@@")


if __name__ == "__main__":
    main()
