"""Phase 6.4 (user-suggested): knife-edge the honeycomb wall tops.

    Blender --background --factory-startup --python scripts/sweep_phase64.py

THE QUESTION. The comb stack's one incurable axis is head-on (0.085-0.104)
— attributed to the Musou-coated but FLAT wall tops (top-area fraction
2*0.08/12.7 = 1.26 %). The user asks: sharpen the tops to an edge (the
comb param set supports tapered walls: wall_top < wall_bot). If the
exposed-flat-area law owns head-on, thinning the top to 0.01 mm
(fraction 0.157 %) should collapse it toward the pyramid class.

    PREDICTIONS, numeric, before any render.

    P1  HEAD-ON IS LINEAR IN TOP AREA: knife stack head-on
        = 0.027 + (0.085 - 0.027) x (0.157/1.26) = 0.034 ± 0.010.
        If instead it stays >= 0.07, the walls themselves glint and no
        edge treatment helps.

    P2  TOTALS BARELY MOVE: knife stack total within ± 5 % of the blunt
        stack's 0.21184 (top area is ~1 % of the face either way).

    P3  SMEAR/SPAN unchanged within noise (smear 1.0 ± 0.3,
        span <= 2.2x).

Anchor: P5_j00 + the blunt stack P6_stk_c127 params pair with
sweep_phase6.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase64.csv")
FORMJSON = os.path.join(RESULTS, "form_phase64.json")
OUT = "/tmp/phase64"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}


def stack(wtop):
    return {"face_w": 60.0, "face_h": 60.0, "margin_depths": 2.0,
            "backing": 2.0, "seed": 23,
            "top": "comb", "top_depth": 35.0,
            "top_params": {"jitter": 0.0, "pitch": 12.7, "wall_bot": 0.08,
                           "wall_top": wtop},
            "bot": "pyramid", "bot_depth": 15.0,
            "bot_params": {"margin_depth_ref": 50.0, "pitch": 2.0,
                           "tip_flat": 0.1}}


KNIFE = stack(0.01)

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",         "floor", ANCHOR),
    ("P64_stk_knife",  "stack", KNIFE),
]
COLS = ["tag", "family", "topology", "wall_top", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 6.4 — knife-edged comb tops")
    print("=" * 74)
    for tag, family, prm in TOTALS:
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in ALL:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220,
                       "gpu": True, "spec_roughness": 0.30, "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30}}
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": family,
                             "topology": "stack" if family == "stack"
                             else "pyramid",
                             "wall_top": prm.get("top_params",
                                                 {}).get("wall_top", ""),
                             "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-14s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P64_stk_knife ===", flush=True)
    entry = {"tag": "P64_stk_knife", "family": "stack",
             "topology": "comb/pyr", "process": "assembly+etch",
             "params": KNIFE, "pitch": 12.7}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["winding"] = "out"
    fout["P64_stk_knife"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
