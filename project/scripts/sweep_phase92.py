"""Phase 9.2: paint the TOPS only — the front-spray hypothesis.

    Blender --background --factory-startup --python scripts/sweep_phase92.py

WHY. Phase 9.1 priced full Musou coverage at 50-100M KRW (1,000 m^2 of
slant face). The user asks: paint only the tip region from the front.
Two measured facts argue it works: (1) bare-black totals are LINEAR in
rho (0.18 x rho) -- escaping light bounces effectively once; (2) escape
requires sky view, which only the upper face has, and the head-on term
(the tip flat) is at the very top. The face is a triangle narrowing
toward the tip, so the top 5 mm of a 20 mm face is only (5/20)^2 = 6 %
of the paint area.

MACHINERY. `paint_depth` (make_depth_split): Musou-fit coating above
the plane, rho 0.05 Lambertian below it (the bare urethane of 9.1).
paint_fade 0 (sharp boundary) -- the front-spray gradient is softer;
sharp is the conservative model of "적당히".

    PREDICTIONS, numeric, before any render. Bounds: unpainted
    0.90685 % / painted 0.17668 % (both book). Model: escape-weighted
    bounce location is top-heavy but not entirely top (theta 40 light
    enters low on the shadowed flank), so recovery is sublinear in
    depth but far above area fraction.

    P1  TOP 2 mm  (1 % of paint area): total 0.55 +- 0.20 %
        (recovers ~half the gap for 1 % of the paint).
    P2  TOP 5 mm  (6 % of paint area): total 0.35 +- 0.15 %.
    P3  TOP 10 mm (25 % of paint area): total 0.22 +- 0.05 %.
    P4  HEAD-ON IS A TOP PHENOMENON: at paint_depth 5, head-on
        (beam 7.5 mm) 0.05 +- 0.02 -- close to the fully painted 0.040,
        far from the bare 0.107. Smear recorded, no band.

    DECISION RULE, registered: the front-spray tier ships iff
    paint_depth 5 gives total <= 0.35 % AND head-on <= 0.06. Then the
    paint bill for non-critical zones drops ~16x instead of to zero,
    at ~2.5x better total than bare.

Anchor: P5_j00 d100@-40 single render, must match 0.13392 %.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase92.csv")
FORMJSON = os.path.join(RESULTS, "form_phase92.json")
OUT = "/tmp/phase92"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
TH5 = (0.0, -20.0, 20.0, -40.0, 40.0)
DEEP_RHO = 0.05
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 9.2 — paint the tops only (front-spray hypothesis)")
    print("=" * 74)

    def run_one(tag, prm, mat, th, pd):
        body, spec = BR.coating_split(DF[mat])
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
        if pd is not None:
            cfg["paint_depth"] = pd
            cfg["deep_coating"] = {"body": DEEP_RHO,
                                   "spec_scale": DEEP_RHO}
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": "floor", "topology": "pyramid",
                     "phi": 0, "seed": 23, "diffuse_frac": mat,
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(
                         dict(prm, **({"paint_depth": pd} if pd else {})),
                         sort_keys=True)})
        return rec["panel"]["mean"]

    v = run_one("P5_j00", ANCHOR, "d100", -40.0, None)
    print("  anchor P5_j00 d100@-40: %.5f %% (book 0.13392)" % (100 * v),
          flush=True)

    for pd in (2.0, 5.0, 10.0):
        w = 0.0
        for mat in ("d00", "d76", "d100"):
            for th in TH5:
                w = max(w, run_one("P92_pd%02.0f" % pd, FINAL, mat, th,
                                   pd))
        print("  paint top %4.1f mm  worst(mats x 5th) %.5f %%"
              % (pd, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # form at paint_depth 5 (beam 7.5)
    fout = {}
    print("\n=== form: P92_pd05 (beam %.1f) ===" % FB.STRIPE_W, flush=True)
    entry = {"tag": "P92_pd05_form", "family": "floor",
             "topology": "pyramid", "process": "cast+frontspray",
             "params": FINAL, "pitch": 4.0,
             "paint_depth": 5.0,
             "deep_coating": {"body": DEEP_RHO, "spec_scale": DEEP_RHO}}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["stripe_w"] = FB.STRIPE_W
    fout["P92_pd05_form"] = rec
    print("  smear(+-40) %s  head-on %s"
          % (rec["smear"], rec["head_on"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
