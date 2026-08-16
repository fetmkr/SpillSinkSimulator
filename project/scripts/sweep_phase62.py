"""Phase 6.2: the coarse tier at the worst azimuth.

    Blender --background --factory-startup --python scripts/sweep_phase62.py

WHY. Phase 6.1 left exactly two named holes: the big-cell stack's
worst-phi (the 5.15 cell-5.2 stack measured a 0.0 % shift; ASSUMED to
carry to 12.7, unmeasured) and the coarse pyramid's phi 30 (the aspect-5
p4/d20 field measured x1.407; same aspect at p10/d50 should scale the
same if the phi hole is an aspect property, not a pitch property).

    PREDICTIONS, numeric, before any render.

    P1  THE BIG STACK IS PHI-FLAT: P6_stk_c127 at phi 30 within 5 % of
        its phi-0 0.21184 (hex symmetry; the floor is fine-pitch and
        phi-mild).

    P2  THE PHI HOLE IS AN ASPECT PROPERTY, NOT A PITCH PROPERTY:
        p10/d50 at phi 30 = 0.194 x 1.41 = 0.274 ± 0.025 (the aspect-5
        ratio measured on p4/d20). If instead it lands near the
        aspect-9 ratio (x1.74 -> 0.336) the hole grows with absolute
        pitch and the p4/d20 easy tier was flattered.

    P3  SHALLOWER SLOPES, SMALLER HOLE (monotonic in aspect): p15/d50
        (aspect 3.3) at phi 30 shifts LESS than x1.41: band
        x1.15-1.40 -> 0.271-0.330.

Anchor: P5_j00 + P6_stk_c127 / P6_pyr_p10d50 / P6_pyr_p15d50 phi-0 rows
pair with sweep_phase6.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase62.csv")
OUT = "/tmp/phase62"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
def pyr(depth, pitch):
    return {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0,
            "depth": depth, "pitch": pitch, "tip_flat": 0.0,
            "margin_depths": 2.0, "backing": 2.0}
STACK = {"face_w": 60.0, "face_h": 60.0, "margin_depths": 2.0,
         "backing": 2.0, "seed": 23,
         "top": "comb", "top_depth": 35.0,
         "top_params": {"jitter": 0.0, "pitch": 12.7, "wall_bot": 0.08,
                        "wall_top": 0.08},
         "bot": "pyramid", "bot_depth": 15.0,
         "bot_params": {"margin_depth_ref": 50.0, "pitch": 2.0,
                        "tip_flat": 0.1}}

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",           "floor", ANCHOR,          0.0),
    ("P62_stk_c127_p30", "stack", STACK,           30.0),
    ("P62_p10d50_p30",   "floor", pyr(50.0, 10.0), 30.0),
    ("P62_p15d50_p30",   "floor", pyr(50.0, 15.0), 30.0),
]
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 6.2 — the coarse tier at the worst azimuth")
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
                             "topology": prm.get("kind", "stack"),
                             "phi": phi, "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-17s phi %4.1f  worst %.5f %%" % (tag, phi, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
