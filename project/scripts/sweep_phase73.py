"""Phase 7.3: the REAL box — 1 mm folded-sheet walls, measured.

    Blender --background --factory-startup --python scripts/sweep_phase73.py

WHY. The surrogate (walls carrying the panel's albedo) read 0.045 % but
ignored construction. The user pinned the constraint: single 1 mm sheet.
The buildable answer is a press-brake FOLDED wall — 45-degree zigzag
(period 32, swing ±8), texture from bending, not thickness — over the
final-sample pyramid floor. Cell 220, depth 240, front edge = the sheet's
own 1 mm top. Geometry verified numerically (fold swing ±8.5, ~45°) and
by preview before this run.

    PREDICTIONS, numeric, before any render.

    P1  TOTAL: 0.08 ± 0.04 %. The 45° folds deflect near-normal light
        across the cell into further absorbing hits; obliques see fold
        faces instead of a flat wall. Should land between the surrogate
        (0.045) and the plain-wall box (0.216).

    P2  HEAD-ON: 0.035 ± 0.015 (beam 7.5). Up-facing 45° bands reflect
        normal light sideways, not back; the 1 mm top edges are
        0.45&#8202;% of the face.

    P3  SMEAR (beam 7.5): >= 1.2 — the image dies in the box, and the
        fine floor plus folds should at least match the flat panel's
        1.4 class.

    ADOPTION RULE (fixed in advance): total <= 0.12 AND head-on <= 0.05
    -> the folded-sheet box becomes the recommendation wherever ~25 cm
    of depth exists; otherwise the flat final sample stands everywhere.

Anchor: P5_j00.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase73.csv")
FORMJSON = os.path.join(RESULTS, "form_phase73.json")
OUT = "/tmp/phase73"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
BOX = {"kind": "boxgrid", "face_w": 440.0, "face_h": 440.0, "pitch": 220.0,
       "depth": 240.0, "margin_depths": 0.5, "margin_min": 0.0,
       "backing": 2.0}

DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "seed", "diffuse_frac", "theta",
        "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 7.3 — the folded-sheet box, real geometry")
    print("=" * 74)
    for tag, prm in (("P5_j00", ANCHOR), ("P73_boxfold", BOX)):
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in ("d00", "d76", "d100"):
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": "floor", "out_dir": OUT,
                       "results_dir": OUT, "samples": 64, "res_x": 480,
                       "res_y": 220, "gpu": True, "spec_roughness": 0.30,
                       "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30}}
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": "floor",
                             "topology": prm["kind"], "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-13s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P73_boxfold (beam %.1f) ===" % FB.STRIPE_W,
          flush=True)
    entry = {"tag": "P73_boxfold", "family": "floor",
             "topology": "boxgrid", "process": "fold+assembly",
             "params": BOX, "pitch": 220.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["stripe_w"] = FB.STRIPE_W
    rec["winding"] = "out"
    fout["P73_boxfold"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
