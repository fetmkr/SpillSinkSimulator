"""Phase 6.5: the final sample's own envelope — no more borrowed numbers.

    Blender --background --factory-startup --python scripts/sweep_phase65.py

WHY. The chosen build (pyramid pitch 4 / depth 20 / tip 0.1) carries two
numbers inherited from OTHER designs: its worst-azimuth total is the sharp
p4's phi-ratio applied to the t0.1 phi-0 value, and its paint-roughness
sensitivity is assumed equal to the p2 field's. Before anything is printed,
the design should own its own worst cases.

    PREDICTIONS, numeric, before any render.

    P1  WORST-AZIMUTH TOTAL, measured directly: t0.1 at phi 30 =
        0.2486 ± 0.010 % (sharp p4 ratio x1.407 on 0.17668; tip and
        azimuth proved non-compounding at p2, 5.11).

    P2  ROUGHNESS BOUNDS (d00+d76, 5 theta):
        r 0.10 -> 0.177 ± 0.010 % (the roughness-invariant d100 floor
        owns the low end, as at p2)
        r 0.50 -> 0.48 ± 0.12 %  (the p2 field's x2.95 blow-up carries;
        aspect 5 has fewer bounces so the top of the band is likelier)

    P3  FORM AT THE WORST AZIMUTH (beam width 2 mm): head-on stays
        0.032 ± 0.006 (phi-proof at theta 0, measured twice elsewhere);
        smear drops to 2.6 ± 0.6 (grazing transport, as p2 showed).

Anchor: P5_j00 + P515_easy_t01 phi-0 rows pair with sweep_phase515.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase65.csv")
FORMJSON = os.path.join(RESULTS, "form_phase65.json")
OUT = "/tmp/phase65"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}

DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
# (tag, params, phi, roughness, mats)
JOBS = [
    ("P5_j00",          ANCHOR, 0.0,  0.30, ("d00", "d76", "d100")),
    ("P65_final_p30",   FINAL,  30.0, 0.30, ("d00", "d76", "d100")),
    ("P65_final_rg10",  FINAL,  0.0,  0.10, ("d00", "d76")),
    ("P65_final_rg50",  FINAL,  0.0,  0.50, ("d00", "d76")),
]
COLS = ["tag", "family", "topology", "phi", "roughness", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 6.5 — the final sample's own envelope")
    print("=" * 74)
    for tag, prm, phi, rough, mats in JOBS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        for mat in mats:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": "floor", "out_dir": OUT,
                       "results_dir": OUT, "samples": 64, "res_x": 480,
                       "res_y": 220, "gpu": True, "spec_roughness": rough,
                       "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": rough}}
                if phi:
                    cfg["phi_deg"] = phi
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": "floor",
                             "topology": "pyramid", "phi": phi,
                             "roughness": rough, "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-15s phi %4.1f rough %.2f  worst %.5f %%"
              % (tag, phi, rough, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P65_final_p30 (beam width 2) ===", flush=True)
    entry = {"tag": "P65_final_p30", "family": "floor",
             "topology": "pyramid", "process": "press", "params": FINAL,
             "pitch": 4.0, "phi": 30.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["phi"] = 30.0
    rec["winding"] = "out"
    fout["P65_final_p30"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
