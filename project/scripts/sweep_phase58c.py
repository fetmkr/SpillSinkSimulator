"""Phase 5.8c: find the worst azimuth of the pyramid winner.

    Blender --background --factory-startup --python scripts/sweep_phase58c.py

5.8/5.8b measured phi 0 / 22.5 / 45 on p2/d18: 0.130 / 0.2165 / 0.196.
The worst azimuth is strictly inside (0, 45); the curve's shape is unknown.

    PREDICTIONS, before any render (d76+d100, theta 0/+-40 envelope —
    d00's phi-45 worst was 6x below the others, it cannot own the
    envelope; anchor row keeps all three mats).

    P1  ONE SMOOTH MAXIMUM between phi 10 and 35, no second peak;
        worst-over-phi lands at 0.215-0.235 %.

    P2  SYMMETRY SELF-TEST: phi 40 reads within 3 % of phi 5 mirrored
        about 22.5 only if the maximum is at exactly 22.5 — NOT asserted.
        What IS asserted by the cell's 4-fold symmetry: the curve on
        (0,45) need not be symmetric, but phi and 90-phi are identical,
        so measuring 0-45 covers everything.

    P3  THE VERDICT LINE: worst-over-phi pyramid vs the cone's
        azimuth-invariant 0.2160 % — within 10 % of each other. The
        total-axis crown is shared; the pyramid keeps its lead only on
        head-on (0.0271 vs 0.0595 at phi 0) and its azimuth dependence
        on THAT axis is unmeasured (flagged, not bought, this turn).

Anchor: P5_j00 phi 0, all three mats.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase58c.csv")
OUT = "/tmp/phase58c"

P0 = 5.500550055005501
PYR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 18.0,
       "pitch": 2.0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
PHIS = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0)
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac", "theta",
        "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.8c — the worst azimuth")
    print("=" * 74)

    def run_one(tag, prm, phi, mats, thetas):
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        for mat in mats:
            body, spec = BR.coating_split(DF[mat])
            for th in thetas:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": "floor", "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
                       "spec_roughness": 0.30, "params": prm,
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
                rows.append({"tag": tag, "family": "floor",
                             "topology": "pyramid", "phi": phi, "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-16s phi %4.1f  worst %.5f %%" % (tag, phi, 100 * w),
              flush=True)
        return w

    run_one("P5_j00", ANCHOR, 0.0, ("d00", "d76", "d100"),
            (0.0, -20.0, 20.0, -40.0, 40.0))
    for phi in PHIS:
        run_one("P58c_phi%04.1f" % phi, PYR, phi, ("d76", "d100"),
                (0.0, -40.0, 40.0))

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
