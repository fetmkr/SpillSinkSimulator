"""Phase 5.14: the cone coupon's target numbers (closing the last gap in
the ordering package), plus the rim verification that motivated it.

    Blender --background --factory-startup --python scripts/sweep_phase514.py

WHY. 5.13 pre-registered acceptance targets for the 2x PYRAMID coupon but
not for the 2x CONE coupon that ships beside it — if the cone coupon is
printed first, it has no pass/fail. Also, checking the coupon rim exposed a
potential protocol breaker (a flat rim would inflate every lab reading);
numeric inspection refuted it before any render: the rim is one extra ring
of full-depth cells (flat area at y=0 is 3.6 mm² of tip flats on a
5776 mm² part), so lab and simulation see the same texture.

    PREDICTIONS, numeric, before any render.

    P1  CONE SCALE INVARIANCE, SECOND CONFIRMATION AT 2x: cone p4/d36.4/
        r0.06 totals 0.212 ± 8 % (worst over 3 mats x 5 theta).

    P2  CONE HEAD-ON FOLLOWS THE FLAT FRACTION ACROSS SCALE: r0.06/p4 has
        the same (r/pitch)^2 as r0.03/p2, so head-on = 0.0317 ± 0.006.
        This is the cross-scale test of 5.10's tip-area law on cones.

    P3  SPAN STAYS LOW: <= 1.3x (jitter de-registers the lattice).

    P4  SMEAR (2 mm probe): weak prior — pyramid p4 read 4.53, cone p2
        read 2.77; call cone p4 3.5 ± 1.0 and let the measurement place
        it. Whatever lands is the lab target, compressing at the real
        beam as always.

Anchor: P5_j00 + the cone coupon params are identical (minus margins) to
export/cone_p4_d36_r006.stl's manifest entry.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase514.csv")
FORMJSON = os.path.join(RESULTS, "form_phase514.json")
OUT = "/tmp/phase514"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
S = 2.0 / 5.5
CONE2X = {"face_w": 60.0, "face_h": 60.0, "depth": 100.0 * S, "pitch": 4.0,
          "tip_radius": 0.06, "jitter": 0.3, "depth_jitter": 0.0,
          "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
          "seed": 23, "margin_depths": 2.0, "backing": 2.0}

ALL = ("d00", "d76", "d100")
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
    print("PHASE 5.14 — the cone coupon's targets")
    print("=" * 74)
    for tag, family, prm in (("P5_j00", "floor", ANCHOR),
                             ("P514_cone2x", "cone3d", CONE2X)):
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
                             "topology": prm.get("kind", "cone"),
                             "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-12s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P514_cone2x ===", flush=True)
    entry = {"tag": "P514_cone2x", "family": "cone3d", "topology": "cone",
             "process": "print", "params": CONE2X, "pitch": 4.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["winding"] = "out"
    fout["P514_cone2x"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
