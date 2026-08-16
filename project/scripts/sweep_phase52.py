"""Phase 5.2: the pyramid's depth and pitch, swept independently.

    Blender --background --factory-startup --python scripts/sweep_phase52.py

WHY. The champion was measured at exactly one point: depth 50, pitch 5.5. The
wall build cares about both knobs separately -- depth is panel thickness
(cost, weight, room) and pitch is die size. The anechoic sweep varied aspect
at fixed depth but its pyramid rows predate the winding fix except two; this
is the clean map.

    PREDICTIONS, numeric, written before any render. Grading is against these
    exact numbers, not against their spirit.

    P1  PITCH AT FIXED DEPTH 50 IS A WEAK LEVER, and flat-to-falling toward
        fine pitch: from the corrected pair already measured (aspect 2.83 ->
        0.2526 %, aspect 9.09 -> 0.1339 %) I extrapolate gently:
        pitch 4.0 (aspect 12.5)   0.125 +- 0.010 %
        pitch 3.0 (aspect 16.7)   0.120 +- 0.012 %
        i.e. finer pitch keeps helping but with visibly diminishing returns;
        under 10 % gain from 5.5 to 3.0.

    P2  DEPTH AT FIXED PITCH 5.5 IS THE SAME CURVE IN DISGUISE (aspect is
        what matters, not which knob moved):
        depth 30 (aspect 5.45)    0.175 +- 0.015 %   (near the aspect-6
                                                      anechoic point ~0.17)
        depth 40 (aspect 7.27)    0.150 +- 0.012 %
        depth 65 (aspect 11.8)    0.125 +- 0.010 %
        Concretely: the depth-30 panel gives up ~30 % against depth-50. If
        depth 30 lands under 0.15 % the wall could be 20 mm thinner than
        planned, which is a real manufacturing win worth knowing.

    P3  ASPECT COLLAPSE: plotting all points against aspect = depth/pitch,
        the two families (pitch-swept and depth-swept) fall on ONE curve
        within seed noise (+-4 %). If they do NOT collapse, depth and pitch
        act separately and the whole "aspect" framing this study inherited
        from the RF literature is wrong for surface coatings.

The anchor is P5_j00 (depth 50, pitch 5.5006, identical params_json inc.
winding:"out"), pairing with sweep_phase5.csv and sweep_rewind.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase52.csv")
OUT = "/tmp/phase52"

FACE = 60.0
P0 = 5.500550055005501
BASE = {"kind": "pyramid", "face_w": FACE, "face_h": FACE,
        "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}

DESIGNS = [
    ("P5_j00", 50.0, P0),                    # anchor
    ("P52_d50_p1767", 50.0, 17.67),
    ("P52_d50_p0833", 50.0, 8.33),
    ("P52_d50_p0400", 50.0, 4.0),
    ("P52_d50_p0300", 50.0, 3.0),
    ("P52_d30_p0550", 30.0, P0),
    ("P52_d40_p0550", 40.0, P0),
    ("P52_d65_p0550", 65.0, P0),
]

MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "depth", "pitch", "aspect", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 70)
    print("PHASE 5.2 — depth x pitch for the sharp pyramid")
    print("=" * 70)
    for tag, depth, pitch in DESIGNS:
        prm = dict(BASE, depth=depth, pitch=pitch)
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat, df in MATS:
            body, spec = BR.coating_split(df)
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": "floor", "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
                       "spec_roughness": 0.30, "params": prm,
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
                             "topology": "pyramid", "depth": depth,
                             "pitch": pitch,
                             "aspect": round(depth / pitch, 3), "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-16s depth %5.1f pitch %6.2f aspect %5.2f   worst %.5f %%"
              % (tag, depth, pitch, depth / pitch, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
