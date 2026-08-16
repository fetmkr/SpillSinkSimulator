"""Phase 5.4: the buildable pyramid — scale-up to pitch 10 and the price of a
blunt tip, measured on ALL THREE AXES at once.

    Blender --background --factory-startup --python scripts/sweep_phase54.py

WHY. A pressed or moulded die cannot hold a mathematically sharp apex, and the
champion cell (pitch 5.5, depth 50) is a 9:1 needle nobody can demould. The
aspect law says pitch 10 / depth 90 is the same aspect 9 at twice the feature
size — checked ad-hoc on 08-15 (0.14322 %) but never recorded in a sweep CSV,
never form-tested, and the tip series was never run. Existing anchors:

    sharp  a909 (t0.0/p5.5)   total 0.13392   smear 4.159   head-on 0.02710
    trunc  a909 (t1.1/p5.5)   total 0.17202   smear 4.512   head-on 0.20100

The truncated anchor shows the REAL casualty of a flat tip is the head-on
axis: +28 % total but 7.4x head-on. Flat fraction f = (tip/pitch)^2 = 4 %.

    PREDICTIONS, numeric, written before any render. Grading is against
    these exact numbers.

    P1  SCALE INVARIANCE HOLDS IN A RECORDED SWEEP: p10/d90/t0 re-reads the
        ad-hoc 0.143 within seed noise -> total 0.143 ± 0.006 %.
        Its form numbers match the p5.5 champion within 10 %:
        smear 4.16 ± 0.4, head-on 0.027 ± 0.005 (aspect and shape identical,
        only scale differs; ray optics has no scale).

    P2  TOTAL FOLLOWS FLAT FRACTION, calibrated on the truncated anchor
        (+0.038 abs at f=4 % -> 0.95 abs per unit f):
        t0.5/p10 (f 0.25 %)  0.145 ± 0.007   (invisible)
        t1.0/p10 (f 1 %)     0.153 ± 0.008
        t2.0/p10 (f 4 %)     0.181 ± 0.012   (the a909-trunc ratio, rescaled)

    P3  HEAD-ON FOLLOWS FLAT FRACTION ONLY — NOT absolute tip size. The
        anchor gives head_on ≈ 0.027 + 5.0 × f:
        t0.5  0.040 ± 0.010
        t1.0  0.077 ± 0.020
        t2.0  0.20  ± 0.05    (same f as trunc a909 -> same head-on, even
                               though the tip is 2 mm instead of 1.1 mm)
        If t2.0 lands near 0.20 the law is fraction-based and the build rule
        is simple: TIP/PITCH is the spec, not tip in mm.

    P4  SMEAR BARELY MOVES: 4.16 ± 0.40 for every design in the series.

    P5  SCALE INVARIANCE HOLDS DOWNWARD TOO (user asked: pitch 2 -> is
        depth 18 enough?): p2/d18/t0 is aspect 9 -> total 0.143 ± 0.007 %.
        With tip 0.1 mm (same f 0.25 % as t0.5/p10) the cost stays
        invisible: 0.145 ± 0.007 %. If P5 holds, an 18 mm panel is on the
        table and the whole spec is one ratio pair: depth/pitch 9,
        tip/pitch <= 1/20.

Anchor: P5_j00 (identical params to sweep_phase5.csv) pairs for gate check 8.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase54.csv")
FORMJSON = os.path.join(RESULTS, "form_phase54.json")
OUT = "/tmp/phase54"

FACE = 60.0
P0 = 5.500550055005501
BASE = {"kind": "pyramid", "face_w": FACE, "face_h": FACE,
        "margin_depths": 2.0, "backing": 2.0}

DESIGNS = [
    ("P5_j00",      dict(depth=50.0, pitch=P0,   tip_flat=0.0)),   # anchor
    ("P54_p10_t00", dict(depth=90.0, pitch=10.0, tip_flat=0.0)),
    ("P54_p10_t05", dict(depth=90.0, pitch=10.0, tip_flat=0.5)),
    ("P54_p10_t10", dict(depth=90.0, pitch=10.0, tip_flat=1.0)),
    ("P54_p10_t20", dict(depth=90.0, pitch=10.0, tip_flat=2.0)),
    ("P54_p02_t00", dict(depth=18.0, pitch=2.0,  tip_flat=0.0)),
    ("P54_p02_t01", dict(depth=18.0, pitch=2.0,  tip_flat=0.1)),
]
FORM_DESIGNS = ("P54_p10_t00", "P54_p10_t05", "P54_p10_t10", "P54_p10_t20")

MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "depth", "pitch", "tip_flat",
        "flat_frac", "seed", "diffuse_frac", "theta", "rho", "control",
        "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    worst = {}
    print("=" * 74)
    print("PHASE 5.4 — buildable scale and the blunt tip, three axes")
    print("=" * 74)
    for tag, extra in DESIGNS:
        prm = dict(BASE, **extra)
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        ff = (extra["tip_flat"] / extra["pitch"]) ** 2
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
                             "topology": "pyramid", "depth": extra["depth"],
                             "pitch": extra["pitch"],
                             "tip_flat": extra["tip_flat"],
                             "flat_frac": round(ff, 6), "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        worst[tag] = w
        print("  %-13s tip %.1f/p%.0f (f %.2f %%)   worst %.5f %%"
              % (tag, extra["tip_flat"], extra["pitch"], 100 * ff, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # --- the other two axes, full-fidelity form protocol -------------------
    fout = {}
    for tag, extra in DESIGNS:
        if tag not in FORM_DESIGNS:
            continue
        prm = dict(BASE, **extra)
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                 "process": "press", "params": prm, "pitch": extra["pitch"]}
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

    print("\n  summary (three axes):")
    for tag, extra in DESIGNS:
        f = fout.get(tag, {})
        print("   %-13s total %.5f %%   smear %s   head-on %s"
              % (tag, 100 * worst[tag],
                 "%.3f" % f["smear"] if f.get("smear") else "--",
                 "%.5f" % f["head_on"] if f.get("head_on") else "--"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
