"""Phase 6.1: the coarse tier — pitch >= 10 pyramids, large-cell honeycombs,
and their stacks.

    Blender --background --factory-startup --python scripts/sweep_phase6.py

WHY (user-directed). Coarse features are what cheap tooling and off-the-shelf
stock actually offer: big pressed pyramids, commercial honeycomb in 3/8",
1/2", 3/4" cells. Phase 5 mapped the fine end; this maps the coarse end on
the same three axes so the price of "easy" is a number, not a feeling.

    PREDICTIONS, numeric, before any render.

    P1  COARSE PYRAMIDS FOLLOW THE ASPECT CURVE (8th, 9th checks):
        p10/d50 (aspect 5)    0.194 ± 0.012   (the API measured 0.19420
                                               on 08-15; CSV-grade now)
        p15/d50 (aspect 3.3)  0.240 ± 0.015
        p20/d50 (aspect 2.5)  0.260 ± 0.020
        p10/d90 (aspect 9)    0.143 ± 0.006   (pairs with P54_p10_t00)

    P2  BIG HONEYCOMB DECAYS WITH ITS OWN ASPECT (depth/cell): the
        p5.2-6.5 combs (aspect ~8-10) sat at ~0.22; at depth 50
        cell 9.5  (aspect 5.3)  0.24 ± 0.03
        cell 12.7 (aspect 3.9)  0.27 ± 0.04
        cell 19   (aspect 2.6)  0.32 ± 0.06

    P3  STACKS READ AS THEIR TOP LAYER, floors notwithstanding (Phase
        3/5.15 law, third test): comb-over-pyramid-floor lands within
        10 % of the same comb over its default backing.

    P4  FORM AXES, three runs:
        - sharp p10/d50 pyramid: head-on 0.027 ± 0.008 (sharp tips are
          head-on-proof at every aspect so far), smear ~1.3 (coarse cell
          at the 2 mm probe), span <= 1.1x
        - comb 12.7 alone: head-on 1.0-1.7 (the viewer sees the flat
          backing straight down the cells — Phase 2's honeycomb failure
          at its worst)
        - comb 12.7 over pyramid floor: head-on 0.075 ± 0.025 (backing
          flash gone, wall tops remain: wall fraction 1.26 % scaled from
          the 5.15 comb-5.2 stack's 0.098 at 1.92 %)

Anchor: P5_j00 + P6_pyr_p10d90 pairs with sweep_phase54.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase6.csv")
FORMJSON = os.path.join(RESULTS, "form_phase6.json")
OUT = "/tmp/phase6"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
def pyr(depth, pitch):
    return {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0,
            "depth": depth, "pitch": pitch, "tip_flat": 0.0,
            "margin_depths": 2.0, "backing": 2.0}
def comb(pitch, wall, depth=50.0, face=60.0):
    return {"topology": "comb", "face_w": face, "face_h": face,
            "depth": depth, "pitch": pitch, "wall_top": wall,
            "wall_bot": wall, "jitter": 0.0, "seed": 23,
            "margin_depths": 2.0, "backing": 2.0}
def stack(cpitch, wall, cdepth, fdepth):
    return {"face_w": 60.0, "face_h": 60.0, "margin_depths": 2.0,
            "backing": 2.0, "seed": 23,
            "top": "comb", "top_depth": cdepth,
            "top_params": {"jitter": 0.0, "pitch": cpitch,
                           "wall_bot": wall, "wall_top": wall},
            "bot": "pyramid", "bot_depth": fdepth,
            "bot_params": {"margin_depth_ref": 50.0, "pitch": 2.0,
                           "tip_flat": 0.1}}

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",          "floor", ANCHOR),
    ("P6_pyr_p10d50",   "floor", pyr(50.0, 10.0)),
    ("P6_pyr_p15d50",   "floor", pyr(50.0, 15.0)),
    ("P6_pyr_p20d50",   "floor", pyr(50.0, 20.0)),
    ("P6_pyr_p10d90",   "floor", pyr(90.0, 10.0)),
    ("P6_comb_c095",    "topo",  comb(9.5, 0.08)),
    ("P6_comb_c127",    "topo",  comb(12.7, 0.08)),
    ("P6_comb_c190",    "topo",  comb(19.0, 0.10)),
    ("P6_stk_c127",     "stack", stack(12.7, 0.08, 35.0, 15.0)),
    ("P6_stk_c190",     "stack", stack(19.0, 0.10, 35.0, 15.0)),
]
COLS = ["tag", "family", "topology", "pitch", "depth", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 6.1 — the coarse tier")
    print("=" * 74)
    for tag, family, prm in TOTALS:
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
                             "topology": prm.get("kind",
                                                 prm.get("topology",
                                                         "stack")),
                             "pitch": prm.get("pitch",
                                              prm.get("top_params",
                                                      {}).get("pitch", "")),
                             "depth": prm.get("depth",
                                              prm.get("top_depth", "")),
                             "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-15s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # --- form: coarse pyramid, big comb alone, big comb stack --------------
    fout = {}
    FORMS = [
        ("P6_pyr_p10d50", "floor", pyr(50.0, 10.0), 10.0),
        ("P6_comb_c127", "topo", comb(12.7, 0.08), 12.7),
        ("P6_stk_c127", "stack", stack(12.7, 0.08, 35.0, 15.0), 12.7),
    ]
    for tag, family, prm, pitch in FORMS:
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": family,
                 "topology": prm.get("kind", prm.get("topology", "stack")),
                 "process": "press", "params": prm, "pitch": pitch}
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
