"""Phase 5, experiment 1: does de-periodising the pyramid cost anything?

    Blender --background --factory-startup --python scripts/sweep_phase5.py

WHERE PHASE 5 STANDS. With oriented geometry the sharp pyramid leads all three
axes (total 0.134 %, smear 4.16, head-on 0.0271 — `FINDINGS_formpyr.md`). One
objection stands between it and a build: it is a PERIODIC array, and the
project's rule against those exists because a beam scanning across identical
cells returns a repeating glint. The form protocol phase-averages, so the mean
numbers cannot see this; what CAN see it is `peak_ratio_span` — the max/min of
the head-on peak across the 16 stripe positions, already recorded by the
protocol. A periodic array has a large span (the stripe lands on tip, face,
valley, tip...); a de-periodised one should flatten it.

THE DE-PERIODISATION. The base grid must stay exact (gaps would expose slab),
so only the APEX moves: laterally by `apex_jitter` × half-pitch, downward by
`tip_drop` × depth. Every cell keeps a sharp tip and a perfect base; no two
cells present the same facet angles.

    PREDICTION, written before any render.

    1. ANCHOR: the un-jittered pyramid re-reads its `sweep_rewind` value
       (0.13392 %) within seed noise.

    2. TOTAL REFLECTANCE IS NEARLY FREE: apex jitter <= 10 % rise at 0.6.
       The tip stays a point, the base stays sealed; faces steepen on one side
       and shallow on the other, roughly cancelling. If it costs more than
       20 % the whole idea dies here.

    3. THE SPAN COLLAPSES: periodic pyramid peak_ratio_span is large (I
       expect > 3x) and apex_jitter 0.6 + tip_drop 0.15 cuts it by at least
       half. This is the number the periodicity rule is about.

    4. MEAN smear/head-on move little (< 15 %): jitter buys uniformity across
       phase, not better averages.

Rows carry `"winding": "out"` so gate check 8 pairs the anchor with
`sweep_rewind.csv` and not with the pre-fix `sweep_anechoic.csv`.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase5.csv")
FORMJSON = os.path.join(RESULTS, "form_phase5.json")
OUT = "/tmp/phase5"

FACE, DEPTH = 60.0, 50.0
PITCH = 5.500550055005501          # identical to AN_pyr_a909 / sweep_rewind
BASE = {"kind": "pyramid", "face_w": FACE, "face_h": FACE, "depth": DEPTH,
        "pitch": PITCH, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}

DESIGNS = [
    ("P5_j00", {}),                                     # anchor
    ("P5_j30", {"apex_jitter": 0.3, "seed": 23}),
    ("P5_j60", {"apex_jitter": 0.6, "seed": 23}),
    ("P5_j60d15", {"apex_jitter": 0.6, "tip_drop": 0.15, "seed": 23}),
]
FORM_DESIGNS = ("P5_j00", "P5_j60d15")

MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)

COLS = ["tag", "family", "topology", "apex_jitter", "tip_drop", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    worst = {}
    print("=" * 74)
    print("PHASE 5.1 — de-periodising the sharp pyramid")
    print("=" * 74)
    for tag, extra in DESIGNS:
        prm = dict(BASE, **extra)
        rec_pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
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
                             "topology": "pyramid",
                             "apex_jitter": extra.get("apex_jitter", 0.0),
                             "tip_drop": extra.get("tip_drop", 0.0),
                             "seed": extra.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": rec_pj})
        worst[tag] = w
        print("  %-10s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # --- form protocol on periodic vs de-periodised ------------------------
    fout = {}
    for tag, extra in DESIGNS:
        if tag not in FORM_DESIGNS:
            continue
        prm = dict(BASE, **extra)
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                 "process": "press", "params": prm, "pitch": PITCH}
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

    print("\n  summary:")
    for tag, _ in DESIGNS:
        extra = "  span@0 %.2fx" % fout[tag]["span_0"] if tag in fout else ""
        print("   %-10s worst %.5f %%%s" % (tag, 100 * worst[tag], extra))
    return 0


if __name__ == "__main__":
    sys.exit(main())
