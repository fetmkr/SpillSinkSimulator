"""Phase 5.10: can the cone's one weakness be repaired, and how thin can the
pyramid go?

    Blender --background --factory-startup --python scripts/sweep_phase510.py

WHY. 5.9 ended in a draw broken only by deployment robustness: the thin cone
matches the pyramid everywhere except head-on (0.0464 vs 0.0272, 1.7x). If
that 1.7x is the TIP CAP (a rounded tip_radius 0.073 mm facing the viewer),
it shrinks with the cap; if it is the three-cusp INTERSTICES between circle
bases, no tip polish fixes it. One ladder separates the two. Secondary: the
pyramid's aspect-9 scale invariance is confirmed at pitches 10/5.5/2 — the
stale question list asks about 1.0/1.5, which at aspect 9 are 9 and 13.5 mm
panels. Two cheap points extend the law to its thin end.

    PREDICTIONS, numeric, before any render.

    P1  CONE HEAD-ON FOLLOWS TIP AREA: model head_on = base + k*r^2
        calibrated on (r=0.073 -> 0.0464) with base = pyramid's 0.027:
        r 0.03  -> 0.030 ± 0.005
        r 0.15  -> 0.109 ± 0.025
        If instead head-on is FLAT across r, the interstices own it and
        the cone is stuck at 1.7x.

    P2  CONE TOTALS BARELY MOVE WITH TIP RADIUS: within ± 8 % of 0.2146
        at both radii (tip area is <=1 % of the cell even at r 0.15).

    P3  IF P1 HOLDS at r 0.03 the cone reaches head-on parity with the
        pyramid (within 15 %) while keeping azimuth immunity — an
        all-axis-robust design. Whether a mould can hold a 0.03 mm tip
        radius is a manufacturing question flagged, not answered, here.

    P4  THE PYRAMID ASPECT LAW EXTENDS TO ITS THIN END: p1.5/d13.5 and
        p1.0/d9 read 0.130 ± 8 % each (3rd and 4th scale confirmations).
        Panels 15.5 and 11 mm incl. backing. Tip tolerance shrinks with
        pitch (~0.033 and ~0.022 mm by the 5.8 interpolation) — recorded
        as the price of thinness, not measured here.

    P5  CONE r0.03 FORM: smear 2.77 ± 0.5 (tips do not govern smear),
        span <= 1.3x.

Anchor: P5_j00 + P59_cone20 params (identical to sweep_phase59.csv).
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase510.csv")
FORMJSON = os.path.join(RESULTS, "form_phase510.json")
OUT = "/tmp/phase510"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
def pyr(depth, pitch):
    return {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0,
            "depth": depth, "pitch": pitch, "tip_flat": 0.0,
            "margin_depths": 2.0, "backing": 2.0}
S = 2.0 / 5.5
def cone(r):
    return {"face_w": 60.0, "face_h": 60.0, "depth": 50.0 * S, "pitch": 2.0,
            "tip_radius": r, "jitter": 0.3, "depth_jitter": 0.0,
            "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
            "seed": 23, "margin_depths": 2.0, "backing": 2.0}

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",        "floor",  ANCHOR),
    ("P59_cone20",    "cone3d", cone(0.2 * S)),        # anchor, r 0.0727
    ("P510_cone_r003", "cone3d", cone(0.03)),
    ("P510_cone_r015", "cone3d", cone(0.15)),
    ("P510_pyr_p15",  "floor",  pyr(13.5, 1.5)),
    ("P510_pyr_p10",  "floor",  pyr(9.0, 1.0)),
]
COLS = ["tag", "family", "topology", "depth", "pitch", "tip_radius", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.10 — the cone's tip, and the pyramid's thin end")
    print("=" * 74)
    for tag, family, prm in TOTALS:
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in ALL:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT, "results_dir": OUT,
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
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "cone"),
                             "depth": prm["depth"], "pitch": prm["pitch"],
                             "tip_radius": prm.get("tip_radius", ""),
                             "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-15s depth %5.1f pitch %4.2f tip %s  worst %.5f %%"
              % (tag, prm["depth"], prm["pitch"],
                 prm.get("tip_radius", "-"), 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    prm = cone(0.03)
    print("\n=== form: P510_cone_r003 ===", flush=True)
    entry = {"tag": "P510_cone_r003", "family": "cone3d", "topology": "cone",
             "process": "mould", "params": prm, "pitch": 2.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["winding"] = "out"
    fout["P510_cone_r003"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
