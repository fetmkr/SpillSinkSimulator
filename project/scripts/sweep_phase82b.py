"""Phase 8.2b: the 35-degree build, measured (the report must not rest
on arithmetic alone).

    Blender --background --factory-startup --python scripts/sweep_phase82b.py

WHY. 8.3 (the buildable unit) grew the tilt from the measured 25 to 35
degrees on mirror arithmetic. Directions ARE arithmetic; the measured
quantities are not: aperture vignetting moves every hemi number, the
danger spike must relocate to -(2*35) = -70, and the deeper swing eats
more of the window's own view. The unit is one render session away from
being measured at its as-built angle; publishing it unmeasured is how
this project got burned before.

GEOMETRY. Tilt 35 needs a longer plate to keep covering the window:
z_bottom = Hp*(0.5 - cos35) <= -47.5 -> Hp >= 149; plate_h = 155
(bottom swings 88.9 deep), void_depth 130 keeps 17 mm of clearance to
the trap tips. R = 1 % per surface throughout.

    PREDICTIONS, numeric, before any render. Aperture-clip model: a
    window point at height z sees its mirror ray (elev -(theta+70))
    exit only if z - tan(theta+70)*0.700*(75-z) > -61.

    P1  LEVEL OBSERVER COLLAPSES ~4x VS TILT 25: at theta 0 the mirror
        elev is -70 and only the top ~20 % of the window clears the
        sill: hemi total 0.40 +- 0.15 % (tilt 25 measured 1.85).
    P2  BELOW-HORIZON OBSERVERS: theta -20 -> upper half clears ->
        1.0 +- 0.3 %. theta -40 -> clip model says 73 % BUT the
        under-edge back-face path (seen at tilt 25) adds an unmodeled
        term: wide band 1.2-2.0 %.
    P3  ABOVE-HORIZON STAYS DEAD: theta +20/+40/+50/+70 all < 0.05 %
        (mirror elev -90 and steeper: no exit path exists).
    P4  THE DANGER SPIKE RELOCATES EXACTLY TO -70: front-camera ratio
        vs the 5 % control > 100 at theta -70; every scanned theta with
        |theta + 70| >= 10 stays < 0.5. Shoulders -75/-65 unpredicted,
        recorded. (At tilt 25 the spike sat at -50 with ratio 34,176.)
    P5  FORM (beam 7.5 mm): head-on < 0.001 (the theta-0 residual
        leaves at -70, further off-axis than tilt 25's -50, which
        measured 0.0000023). Smear not gradeable on a zero return,
        as before; recorded with reason.
    P6  SYSTEM (pyramid trap at the back): theta 0 = clipped mirror +
        through-trap = 0.55 +- 0.25 %; theta +20 = 0.15 +- 0.08;
        theta +40 = 0.05 +- 0.04.

Anchor: P5_j00 d100@-40 single render, must equal 0.13392 %.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase82b.csv")
FORMJSON = os.path.join(RESULTS, "form_phase82b.json")
OUT = "/tmp/phase82b"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
ENV = {"kind": "pyramid", "face_w": 100.0, "face_h": 100.0, "depth": 20.0,
       "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
AR35 = {"tilt_deg": 35.0, "thickness": 2.0, "ar_roughness": 0.02,
        "void_rho": 0.0, "void_depth": 130.0, "plate_h": 155.0,
        "r_surface": 0.01}
COLS = ["tag", "family", "topology", "mode", "r_surface", "theta",
        "rho", "control", "ratio", "params_json"]


def hemi_job(tag, ar, th):
    return {"tag": tag, "family": "arplate", "out_dir": OUT,
            "results_dir": OUT, "samples": 64, "res_x": 480, "res_y": 220,
            "gpu": True, "params": ENV, "ar": ar,
            "material_mode": "ar_glass",
            "renders": [{"mode": "hemi_view", "theta": th}]}


def angle_job(tag, ar, th):
    j = hemi_job(tag, ar, th)
    j["samples"] = 128
    j["renders"] = [{"mode": "angle", "theta": th}]
    return j


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def record(tag, mode, th, rec):
        rows.append({"tag": tag, "family": "arplate", "topology": "arplate",
                     "mode": mode, "r_surface": 0.01, "theta": th,
                     "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "ratio": rec["ratio_mean"],
                     "params_json": json.dumps(AR35, sort_keys=True)})

    print("=" * 74)
    print("PHASE 8.2b — the 35-degree build, measured")
    print("=" * 74)

    cfg = {"tag": "P5_j00_a82b", "family": "floor", "out_dir": OUT,
           "results_dir": OUT, "samples": 64, "res_x": 480, "res_y": 220,
           "gpu": True, "spec_roughness": 0.30, "params": ANCHOR,
           "renders": [{"mode": "hemi_view", "theta": -40.0}],
           "material_mode": "coating"}
    body, spec = BR.coating_split(1.0)
    cfg["coating"] = {"body": body, "spec_scale": spec, "roughness": 0.30}
    cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
    res = BR.run(cfg)
    rec = list(res["modes"].values())[0]
    print("  anchor P5_j00 d100@-40: %.5f %% (book 0.13392)"
          % (100 * rec["panel"]["mean"]), flush=True)

    per = {}
    for th in (0.0, 20.0, 40.0, 50.0, 70.0, -20.0, -40.0):
        tag = "P82b_t35_%+03.0f" % th
        res = BR.run(hemi_job(tag, AR35, th))
        rec = list(res["modes"].values())[0]
        record("P82b_t35", "hemi_view", th, rec)
        per[th] = rec["panel"]["mean"]
    print("  hemi: " + "  ".join("%g:%.3f%%" % (t, 100 * v)
                                 for t, v in sorted(per.items())),
          flush=True)

    print("  --- danger scan (angle mode, front camera) ---")
    for th in (-75.0, -70.0, -65.0, -60.0, -50.0, -40.0, -20.0, 0.0,
               40.0, 70.0):
        tag = "P82b_scan_%+03.0f" % th
        res = BR.run(angle_job(tag, AR35, th))
        rec = list(res["modes"].values())[0]
        record("P82b_scan", "angle", th, rec)
        print("    scan th %+5.1f  panel %.3e  ratio %10.3f"
              % (th, rec["panel"]["mean"], rec["ratio_mean"]), flush=True)

    ar = dict(AR35, backing="pyramid")
    for th in (0.0, 20.0, 40.0):
        tag = "P82b_sys_%+03.0f" % th
        res = BR.run(hemi_job(tag, ar, th))
        rec = list(res["modes"].values())[0]
        record("P82b_sys", "hemi_view", th, rec)
        print("  system th %+3.0f: %.4f %%"
              % (th, 100 * rec["panel"]["mean"]), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P82b_t35 (beam %.1f) ===" % FB.STRIPE_W, flush=True)
    entry = {"tag": "P82b_t35_form", "family": "arplate",
             "topology": "arplate", "process": "glass",
             "params": ENV, "pitch": 4.0, "ar": AR35}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["stripe_w"] = FB.STRIPE_W
    fout["P82b_t35_form"] = rec
    print("  smear(+-40) %s  head-on %s"
          % (rec["smear"], rec["head_on"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
