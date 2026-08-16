"""Phase 6.3 (user-suggested): honeycomb cell 10 / depth 30 over a
cell-matched EASY pyramid floor (pitch 10 / depth 10, slope 45 deg).

    Blender --background --factory-startup --python scripts/sweep_phase63.py

THE IDEA. The comb's fatal flaw is its visible flat bottom; the user
proposes plugging it with a floor pyramid whose pitch MATCHES the cell —
one 45-degree pyramid per cell, shallow enough to vacuum-form. Total
depth 40 mm. Note: hex comb over a square pyramid grid does not register
1:1; the measurement averages over misalignment, which is what bought
parts would do anyway.

    PREDICTIONS, numeric, before any render.

    P1  TOTAL AT phi0: the cell-10 comb naked should sit near the cell-9.5
        naked value (0.246); a floor that fills the bottom with 45-deg
        slopes buys what the fine floor bought the 12.7 comb (~35 %):
        0.20 ± 0.03.

    P2  THE FINE floor STILL BEATS THE MATCHED COARSE floor: same comb
        over the p2/d15 floor reads BETTER than over the matched p10/d10
        floor by 5-20 % (a 45-deg face reflects normal rays sideways into
        walls — good — but its own aspect is only 1; the fine floor
        absorbs more before the walls are ever needed).

    P3  AZIMUTH-FLAT, like every comb stack: phi30 within 5 % of phi0.

    P4  FORM AXES: head-on 0.09 ± 0.03 (the comb tops own it — no floor
        can fix that); smear at the protocol probe 1.0-1.5.

Anchor: P5_j00; the c10 stacks pair with sweep_phase6.csv's comb entries
by construction.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase63.csv")
FORMJSON = os.path.join(RESULTS, "form_phase63.json")
OUT = "/tmp/phase63"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}


def stack(fpitch, fdepth, ftip):
    return {"face_w": 60.0, "face_h": 60.0, "margin_depths": 2.0,
            "backing": 2.0, "seed": 23,
            "top": "comb", "top_depth": 30.0,
            "top_params": {"jitter": 0.0, "pitch": 10.0, "wall_bot": 0.08,
                           "wall_top": 0.08},
            "bot": "pyramid", "bot_depth": fdepth,
            "bot_params": {"margin_depth_ref": 50.0, "pitch": fpitch,
                           "tip_flat": ftip}}


MATCHED = stack(10.0, 10.0, 0.0)     # the user's cell-matched 45-deg floor
FINE = stack(2.0, 15.0, 0.1)         # the reference fine floor

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",            "floor", ANCHOR,  0.0),
    ("P63_c10_pyr10",     "stack", MATCHED, 0.0),
    ("P63_c10_pyr10_p30", "stack", MATCHED, 30.0),
    ("P63_c10_pyr2",      "stack", FINE,    0.0),
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
    print("PHASE 6.3 — comb c10/d30 over the cell-matched easy floor")
    print("=" * 74)
    for tag, family, prm, phi in TOTALS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
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
                if phi:
                    cfg["phi_deg"] = phi
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": family,
                             "topology": "stack", "phi": phi,
                             "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-18s phi %4.1f  worst %.5f %%" % (tag, phi, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    for tag, prm in (("P63_c10_pyr10", MATCHED),):
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": "stack", "topology": "comb/pyr10",
                 "process": "assembly", "params": prm, "pitch": 10.0}
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
