"""Phase 6.7: the final sample beyond the brief — grazing angles 50-70.

    Blender --background --factory-startup --python scripts/sweep_phase67.py

WHY. Every number so far stops at ±40° (the brief's cone). A real
installation grazes the wall's far edges harder — a projector 3 m from a
wide wall reaches 60°+ at the corners. If the pyramid collapses out
there, the wall's edges need different treatment or placement rules;
if it degrades gracefully, one panel covers the room. The flat plate is
measured alongside at the same angles as the honest denominator (its
model curve rises to 3.18 % at 80°).

    PREDICTIONS, numeric, before any render (medium confidence — the
    aspect curve was never probed past 40°).

    P1  THE PYRAMID DEGRADES SMOOTHLY, NO CLIFF: worst-over-mats at
        theta 50 = 0.30 ± 0.10 %, theta 60 = 0.45 ± 0.15 %,
        theta 70 = 0.75 ± 0.30 %. Faces are 5.7° from vertical, so no
        mirror alignment happens until ~84°; the loss is cavity escape,
        not glint.

    P2  THE ADVANTAGE OVER FLAT SURVIVES GRAZING: flat reads ~1.06 /
        1.29 / 1.9 % at 50/60/70 (model extrapolation), so the ratio
        stays >= 2.5x at every angle measured.

    P3  AZIMUTH AT GRAZING: theta 50 at phi 30 within x1.5 of theta 50
        at phi 0 (the phi hole shrank with effective aspect; at grazing
        the cell is already leaking, so phi has less left to spoil).

    P4  FORM AT ±50 (beam 7.5): smear within ± 30 % of the ±40 value
        1.42 — the return stays a wide smudge, no re-sharpening.

Anchor: P5_j00 + the flat face-100 ridge pairs with sweep_phase57.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase67.csv")
FORMJSON = os.path.join(RESULTS, "form_phase67.json")
OUT = "/tmp/phase67"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
FLAT = dict(face_w=100.0, face_h=100.0, depth=0.001, pitch_mean=50.0,
            tip_width=50.0, tip_round=False, pitch_jitter=0.0,
            arc_segments=4, valley_round=0.0, margin_depths=6.5)

DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
GRAZE = (-50.0, -60.0, -70.0)
# (tag, family, params, thetas, phi)
JOBS = [
    ("P5_j00",         "floor", ANCHOR, (0.0, -20.0, 20.0, -40.0, 40.0), 0),
    ("P67_final_graze", "floor", FINAL, GRAZE, 0),
    ("P67_final_g50p30", "floor", FINAL, (-50.0,), 30.0),
    ("P67_flat_graze", "ridge", FLAT, GRAZE, 0),
]
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 6.7 — grazing angles, 50 to 70 degrees")
    print("=" * 74)
    for tag, family, prm, thetas, phi in JOBS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        per_th = {}
        for mat in ("d00", "d76", "d100"):
            body, spec = BR.coating_split(DF[mat])
            for th in thetas:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT,
                       "results_dir": OUT, "samples": 64, "res_x": 480,
                       "res_y": 220, "gpu": True, "spec_roughness": 0.30,
                       "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30}}
                if phi:
                    cfg["phi_deg"] = phi
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                per_th[th] = max(per_th.get(th, 0.0),
                                 rec["panel"]["mean"])
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "flat"),
                             "phi": phi, "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        detail = "  ".join("%g:%.4f%%" % (t, 100 * v)
                           for t, v in sorted(per_th.items()))
        print("  %-17s worst %.5f %%   [%s]" % (tag, 100 * w, detail),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # form at +-50 (beam default 7.5)
    fout = {}
    old = FB.THETAS
    FB.THETAS = (-50.0, 50.0, 0.0)
    try:
        print("\n=== form: P67_final_pm50 (beam %.1f) ===" % FB.STRIPE_W,
              flush=True)
        entry = {"tag": "P67_final_pm50", "family": "floor",
                 "topology": "pyramid", "process": "press",
                 "params": FINAL, "pitch": 4.0}
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-50"), t.get("+50"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["span_0"] = z["peak_ratio_span"] if z else None
        rec["stripe_w"] = FB.STRIPE_W
        rec["thetas_used"] = [-50.0, 50.0, 0.0]
        rec["winding"] = "out"
        fout["P67_final_pm50"] = rec
        print("  smear(+-50) %.3f  head-on %.5f"
              % (rec["smear"], rec["head_on"]), flush=True)
    finally:
        FB.THETAS = old
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
