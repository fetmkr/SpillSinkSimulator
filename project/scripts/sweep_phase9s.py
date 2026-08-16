"""Phase 9.s: buying the seed-robustness claim Phase 5 still owed.

    Blender --background --factory-startup --python scripts/sweep_phase9s.py

WHY. Phase 5 closed with an honest debt: "every number here is one
seed; the claim has not been bought yet." Every published anchor and
final-sample cell runs at the fixed Cycles seed 0 (blender_render.SEED),
which makes runs reproducible and HIDES the Monte-Carlo spread. The
cone measured a 4.5 % spread over three seeds in 5.11; the pyramid
never did. This sweep buys the claim for the two cells everything else
hangs from.

    PREDICTIONS, numeric, before any render.

    P1  ANCHOR CELL (aspect-9 pyramid, d100 at -40, 64 spp): three
        seeds {0, 7, 23} agree within +-3 % relative of their own mean,
        and seed 0 reproduces the book 0.13392 % exactly.
    P2  FINAL-SAMPLE CELL (p4/d20/t0.1, d100 at -40, 64 spp): same
        +-3 % band across the three seeds; seed 0 equals the value
        recorded in sweep_phase515.csv for that cell.
    P3  The worst-over-theta ORDERING is seed-stable: at every seed the
        -40 cell stays the worst of {0, -40} for both designs (no
        rank flip from noise).

    If any cell spreads beyond +-5 % the noise-band caveat must be
    added to every FINDINGS that quotes a single-seed number.

Anchor: the seed-0 rows ARE the anchors here, cross-checked against the
book values by exact reproduction.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase9s.csv")
OUT = "/tmp/phase9s"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
SEEDS = (0, 7, 23)
THS = (0.0, -40.0)
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    body, spec = BR.coating_split(1.0)

    def run_one(tag, prm, th, seed):
        cfg = {"tag": "%s_s%d_%+03.0f" % (tag, seed, th),
               "family": "floor", "out_dir": OUT, "results_dir": OUT,
               "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
               "spec_roughness": 0.30, "params": prm,
               "cycles_seed": seed,
               "renders": [{"mode": "hemi_view", "theta": th}],
               "material_mode": "coating",
               "coating": {"body": body, "spec_scale": spec,
                           "roughness": 0.30}}
        cfg.update({k: v for k, v in COAT.items()
                    if k != "spec_roughness"})
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": "floor", "topology": "pyramid",
                     "phi": 0, "seed": seed, "diffuse_frac": "d100",
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(prm, sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 9.s — the seed debt, paid")
    print("=" * 74)
    for tag, prm in (("P9s_anchor", ANCHOR), ("P9s_final", FINAL)):
        for seed in SEEDS:
            per = {}
            for th in THS:
                per[th] = run_one(tag, prm, th, seed)
            print("  %-10s seed %2d   0deg %.5f %%   -40deg %.5f %%"
                  % (tag, seed, 100 * per[0.0], 100 * per[-40.0]),
                  flush=True)

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
