"""Phase 5.8: the number a toolmaker must hold — tip tolerance per pitch,
plus the winner's missing azimuth check.

    Blender --background --factory-startup --python scripts/sweep_phase58.py

WHY. The build recommendation is p2/d18 sharp, with one measured cliff: a
0.1 mm tip flat costs 2.2x head-on (form_phase54). Between "mathematically
sharp" and 0.1 mm nothing is measured, so the drawing cannot carry a
tolerance. Also: every pyramid number is at azimuth 0, and the brief says
azimuth is unknown; the 4-fold cell's worst case should be phi 45. The
old azimuth study (FINDINGS_phase5_azimuth.md) predates the pyramid.

    PREDICTIONS, numeric, before any render. f = (tip/pitch)^2.

    P1  TOTALS BARELY MOVE (flat-fraction law, 0.95 abs per unit f):
        p2 t0.02  0.1302   t0.05  0.1306   t0.15  0.1355   (all ± 0.006)
        p5.5 t0.275 (f 0.25 %)  0.1345 ± 0.006

    P2  HEAD-ON IS LINEAR IN f AT FIXED PITCH (anchors: 0.0272 at f=0,
        0.0590 at f=0.25 %):
        t0.02 (f 0.01 %)   0.028 ± 0.004
        t0.05 (f 0.0625 %) 0.035 ± 0.006
        t0.15 (f 0.5625 %) 0.099 ± 0.020

    P3  AT FIXED f, FINER PITCH PAYS MORE (5.4 measured 0.0432 at
        p10/f0.25 %, 5.4b measured 0.0590 at p2/f0.25 %): p5.5 t0.275
        lands between them, 0.050 ± 0.008.

    P4  SPAN GROWS WITH THE TIP: t0.02 <= 1.2x, t0.05 in 1.2-2.0x,
        t0.15 in 2.5-4.5x. Smear stays 4.1 ± 0.4 throughout (protocol
        beam 2 mm).

    P5  THE SPEC RULE, decided before measuring: the drawing tolerance is
        the largest tip whose head-on stays <= 1.5x sharp (<= 0.041).
        Prediction: t0.05 passes, t0.1 (already measured, 0.0590) fails.
        So the p2 die must hold 0.05 mm; if a toolmaker cannot, the pitch
        must grow to buy tolerance (p5.5 -> ~0.14 mm, p10 -> ~0.5 mm by
        the same 1.5x rule and P3).

    P6  THE PYRAMID IS AZIMUTH-SAFE: p2/d18 sharp at phi 45 reads within
        6 % of phi 0 on worst-over-(3 mats x 5 theta) — same bound the
        honeycomb held. A doubly-closed cell has no continuous groove for
        phi to exploit.

Anchor: P5_j00 face-60 (identical params to sweep_phase5.csv).
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase58.csv")
FORMJSON = os.path.join(RESULTS, "form_phase58.json")
OUT = "/tmp/phase58"

P0 = 5.500550055005501
def pyr(depth, pitch, tip):
    return {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0,
            "depth": depth, "pitch": pitch, "tip_flat": tip,
            "margin_depths": 2.0, "backing": 2.0}

ALL = ("d00", "d76", "d100")
D2 = ("d00", "d76")
# (tag, params, mats, phi)
DESIGNS = [
    ("P5_j00",        pyr(50.0, P0, 0.0),   ALL, 0.0),   # anchor
    ("P58_p02_t002",  pyr(18.0, 2.0, 0.02), D2,  0.0),
    ("P58_p02_t005",  pyr(18.0, 2.0, 0.05), D2,  0.0),
    ("P58_p02_t015",  pyr(18.0, 2.0, 0.15), D2,  0.0),
    ("P58_p55_t0275", pyr(50.0, P0, 0.275), D2,  0.0),
    ("P58_p02_phi45", pyr(18.0, 2.0, 0.0),  ALL, 45.0),
]
FORM_DESIGNS = ("P58_p02_t002", "P58_p02_t005", "P58_p02_t015",
                "P58_p55_t0275")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "pitch", "tip_flat", "phi", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    worst = {}
    print("=" * 74)
    print("PHASE 5.8 — tip tolerance per pitch, and azimuth")
    print("=" * 74)
    for tag, prm, mats, phi in DESIGNS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        for mat in mats:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
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
                             "topology": "pyramid", "pitch": prm["pitch"],
                             "tip_flat": prm["tip_flat"], "phi": phi,
                             "seed": 23, "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        worst[tag] = w
        print("  %-15s pitch %5.2f tip %5.3f phi %2.0f  worst %.5f %%"
              % (tag, prm["pitch"], prm["tip_flat"], phi, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    for tag, prm, mats, phi in DESIGNS:
        if tag not in FORM_DESIGNS:
            continue
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                 "process": "press", "params": prm, "pitch": prm["pitch"]}
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
