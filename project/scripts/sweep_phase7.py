"""Phase 7.1: the recessed box — a cavity in front of the final sample.

    Blender --background --factory-startup --python scripts/sweep_phase7.py

WHY (user-directed). Space behind the wall is available. The strongest
absorber is not a surface but a HOLE into a dark volume; the question is
whether the box modules' front frames (the flat rims where adjacent boxes
meet) give the advantage back. Model: a deep cell array (cell 110 mm,
220 mm deep, Musou walls) over the final-sample pyramid floor (p4/d20/
t0.1), measured at face 240 so two-plus cells fit.

    VARIANTS.
    A  flat frames: wall 3 mm straight (the user's worry, as-is)
    B  drafted frames: wall 3 mm at the root tapering to 0.5 mm at the
       front (the knife-edge treatment that the 6.4 study priced)

    PREDICTIONS, numeric, before any render. Final sample base: total
    0.17668 / head-on 0.03243. Frame area fraction ~2w/pitch: A 5.5 %,
    B 0.9 %.

    P1  VARIANT A IS FRAME-DOMINATED: head-on 0.117 ± 0.035 (frame
        fraction x the flat plate's 1.64 plus the pyramid base), total
        0.12 ± 0.04 (cavity gain on the floor + frame's flat-plate
        contribution). The user's worry is quantitatively right.

    P2  VARIANT B KEEPS THE CAVITY GAIN: total 0.05-0.12 % — BETTER than
        the flat final-sample panel (0.177) by 1.5-3.5x, because floor
        re-emission mostly hits cavity walls before the aperture lets it
        out. Head-on 0.042 ± 0.012.

    P3  FORM IMPROVES MARKEDLY IN THE BOX: smear (beam 2) >= 4.5 for
        both variants — the image dies inside; span <= 1.5x (cell 110 is
        far coarser than any stripe walk, phases sample within one cell).

    DECISION RULE, fixed now: the box replaces the flat panel as the
    Phase 7 recommendation only if variant B beats the final sample on
    total AND head-on stays <= 0.05. Otherwise the box is an optional
    upgrade, not the baseline.

Anchor: P5_j00.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase7.csv")
FORMJSON = os.path.join(RESULTS, "form_phase7.json")
OUT = "/tmp/phase7"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}


def box(wall_top):
    return {"face_w": 240.0, "face_h": 240.0, "margin_depths": 0.5,
            "backing": 2.0, "seed": 23,
            "top": "comb", "top_depth": 220.0,
            "top_params": {"jitter": 0.0, "pitch": 110.0,
                           "wall_bot": 3.0, "wall_top": wall_top},
            "bot": "pyramid", "bot_depth": 20.0,
            "bot_params": {"margin_depth_ref": 240.0, "pitch": 4.0,
                           "tip_flat": 0.1}}


DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
TOTALS = [
    ("P5_j00",       "floor", ANCHOR),
    ("P7_box_flat",  "stack", box(3.0)),
    ("P7_box_taper", "stack", box(0.5)),
]
COLS = ["tag", "family", "topology", "wall_top", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    prms = {t: p for t, _, p in TOTALS}
    print("=" * 74)
    print("PHASE 7.1 — the recessed box over the final sample")
    print("=" * 74)
    for tag, family, prm in TOTALS:
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in ("d00", "d76", "d100"):
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT,
                       "results_dir": OUT, "samples": 64, "res_x": 480,
                       "res_y": 220, "gpu": True, "spec_roughness": 0.30,
                       "params": prm,
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
                             "topology": "box" if family == "stack"
                             else "pyramid",
                             "wall_top": prm.get("top_params",
                                                 {}).get("wall_top", ""),
                             "seed": 23, "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-13s worst %.5f %%" % (tag, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    for tag in ("P7_box_flat", "P7_box_taper"):
        prm = prms[tag]
        print("\n=== form: %s (beam width 2) ===" % tag, flush=True)
        entry = {"tag": tag, "family": "stack", "topology": "box",
                 "process": "assembly", "params": prm, "pitch": 110.0}
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
