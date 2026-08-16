"""Phase 5.3: mixed pyramid sizes — does the RF-chamber trick translate?

    Blender --background --factory-startup --python scripts/sweep_phase53.py

WHY RF DOES IT, AND WHY IT SHOULD NOT CARRY. Chamber walls mix big and small
pyramids for BROADBAND absorption: a pyramid works where its size is
comparable to the wavelength, so two sizes cover two bands. That is a wave
mechanism. This study is ray optics — performance follows aspect
(depth/pitch) through bounce count, and a mixed field is just a mixture of
aspects. The law that has ordered every table so far says the mix lands at
the area-weighted average of its parts, i.e. strictly WORSE than tiling the
panel with the small pitch alone.

THE TILING. 3×3 super-cell of small pitch s: one big pyramid (base 2s,
aspect halved) on a 2×2 block, five small pyramids (base s) fill the L.
Bases tile exactly. `mix_depth_frac` = 1.0 puts every tip in the entrance
plane; 0.5 preserves the big pyramid's slope on the small ones (their tips
stop half-way down, the RF-photo look).

    PREDICTIONS, numeric, before any render. Uniform s=5.5 measured 0.13392;
    the aspect curve (Phase 5.2) gives ~0.19 at the big cell's aspect 4.55.

    P1  mix, same depth (frac 1.0):  area-weighted (4/9 big + 5/9 small)
        -> 0.159 ± 0.012 %   (15-25 % worse than uniform small)

    P2  mix, same slope (frac 0.5):  worse again — the top half of the
        panel is only big-pyramid flanks with open wells over the small
        cells -> 0.175 ± 0.020 %

    P3  THE MIX NEVER BEATS UNIFORM SMALL PITCH. If it does, a genuinely
        new mechanism exists in ray optics (mutual shadowing between scales)
        and the aspect law is incomplete — that would be worth more than the
        design result.

Anchor: P5_j00, identical params to sweep_phase5.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase53.csv")
OUT = "/tmp/phase53"

FACE = 60.0
P0 = 5.500550055005501
DESIGNS = [
    ("P5_j00", {"kind": "pyramid", "pitch": P0, "tip_flat": 0.0}),
    ("P53_mix_f10", {"kind": "pyrmix", "pitch": P0, "mix_depth_frac": 1.0}),
    ("P53_mix_f05", {"kind": "pyrmix", "pitch": P0, "mix_depth_frac": 0.5}),
]
MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "mix_depth_frac", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 70)
    print("PHASE 5.3 — mixed pyramid sizes")
    print("=" * 70)
    for tag, extra in DESIGNS:
        prm = dict(extra, face_w=FACE, face_h=FACE, depth=50.0,
                   margin_depths=2.0, backing=2.0)
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
                             "topology": prm["kind"],
                             "mix_depth_frac": prm.get("mix_depth_frac", ""),
                             "seed": 23, "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        w0 = w
        print("  %-14s worst %.5f %%" % (tag, 100 * w0), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
