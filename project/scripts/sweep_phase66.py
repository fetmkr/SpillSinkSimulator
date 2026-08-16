"""Phase 6.6: what manufacturing does to the final sample — injection valley
radius, and strip-assembly row offset.

    Blender --background --factory-startup --python scripts/sweep_phase66.py

WHY. Injection rules demand a valley radius (steel cannot hold a
zero-radius ridge; standard internal-fillet floor ~R0.3-0.5). The user's
alternative is to mould ONE-ROW strips and glue them (seams hide in the
valleys, tiny moulds, trivial venting) at the price of a row-to-row height
step. Both are now builder parameters (`valley_round`, `row_offset`),
verified numerically (fillet bottom matches the closed form to 1e-3) and
by preview.

MECHANISM TO TEST. A fillet in a NARROW V does not add much up-facing
area — it FILLS THE VALLEY BOTTOM: at pitch 4 / depth 20, R0.3 wedges
2.7 mm up, R0.5 wedges 4.6 mm up. The cost should therefore look like
LOST DEPTH (effective aspect 4.33 / 3.85 instead of 5).

    PREDICTIONS, numeric, before any render. Final sample base (t0.1):
    total 0.17668 / smear 4.258 (beam 2) / head-on 0.03243 / span 1.47x.

    P1  VALLEY R0.3: total 0.190 ± 0.015 (effective-aspect law),
        head-on 0.036 ± 0.008 (concave recessed bottom adds little),
        smear 4.3 ± 0.5, span <= 2x.
    P2  VALLEY R0.5: total 0.205 ± 0.020, head-on 0.042 ± 0.010.
    P3  ROW OFFSET 0.1 mm: total within +1 ± 2 % of base, head-on
        0.032 ± 0.006 — but SPAN rises to 1.5-3x (alternating rows are a
        new 8 mm periodicity the scanning stripe can see).
    P4  ROW OFFSET 0.2 mm: total +2 ± 2 %, span 2-4x.

    DECISION RULES, fixed now. Injection drawing is COMPLETE if R0.3
    keeps total <= 0.205 and head-on <= 0.041 (the 1.5x rule on the p4
    sharp value). Strip assembly is VIABLE if row 0.1 obeys the same
    limits with span <= 2.5x. If both pass, pick by tooling quotes; if
    only one passes, the geometry has decided.

Anchor: P5_j00 + the t0.1 base pairs with sweep_phase515.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase66.csv")
FORMJSON = os.path.join(RESULTS, "form_phase66.json")
OUT = "/tmp/phase66"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}


def final(**kw):
    d = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0,
         "backing": 2.0}
    d.update(kw)
    return d


DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",        ANCHOR),
    ("P66_vr03",      final(valley_round=0.3)),
    ("P66_vr05",      final(valley_round=0.5)),
    ("P66_row01",     final(row_offset=0.1)),
    ("P66_row02",     final(row_offset=0.2)),
]
FORMS = ("P66_vr03", "P66_vr05", "P66_row01", "P66_row02")
COLS = ["tag", "family", "topology", "valley_round", "row_offset", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    prms = dict(TOTALS)
    print("=" * 74)
    print("PHASE 6.6 — valley radius and row offset on the final sample")
    print("=" * 74)
    for tag, prm in TOTALS:
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
                             "topology": "pyramid",
                             "valley_round": prm.get("valley_round", 0.0),
                             "row_offset": prm.get("row_offset", 0.0),
                             "seed": 23, "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-12s vr %.1f row %.1f  worst %.5f %%"
              % (tag, prm.get("valley_round", 0), prm.get("row_offset", 0),
                 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    for tag in FORMS:
        prm = prms[tag]
        print("\n=== form: %s (beam width 2) ===" % tag, flush=True)
        entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                 "process": "press", "params": prm, "pitch": 4.0}
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["span_0"] = z["peak_ratio_span"] if z else None
        rec["winding"] = "out"
        fout[tag] = rec
        print("  smear %.3f  head-on %.5f  span@0 %.2fx"
              % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
