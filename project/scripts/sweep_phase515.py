"""Phase 5.15: the easy-to-make question — does anything beat a merely
half-steep pyramid?

    Blender --background --factory-startup --python scripts/sweep_phase515.py

WHY. User: aspect 9 tips are hard; can a LOWER pyramid be helped by a
structure in front (honeycomb over a shallow pyramid floor)? Existing data
says the measured stacks (comb 45-48 mm over 2-5 mm floors) sit at
0.2175-0.230 % — beaten by an aspect-5 pyramid alone (0.194 % on the
aspect curve). But two things are unmeasured: the low pyramid's AZIMUTH
hole (the aspect-9 hole was +74 %; shallower slopes may fare worse or
better), and whether a comb over a DEEPER floor (15 mm, aspect 7.5 —
never swept; old floors stopped at 5 mm) changes the stack's class, and
whether the hex comb's azimuth safety (1.06x measured) shields the stack
at worst-phi where the bare pyramid bleeds.

    PREDICTIONS, numeric, before any render.

    P1  EASY PYRAMID AT phi0: p4/d20 (aspect 5, tip half-angle 5.7 deg,
        tip tolerance ~0.2 mm by the 5.8 law) reads 0.194 ± 0.012 —
        the aspect-5 point, 7th scale-invariance check (p10/d50 read
        0.19420 via the simulator on 08-15).

    P2  ITS AZIMUTH HOLE IS PROPORTIONALLY SIMILAR OR WORSE: phi30
        reads 0.30 ± 0.05 (aspect-9 scaled x1.74; shallower slopes have
        more saddle flat per cell, so the top of the band is likelier).

    P3  COMB OVER A DEEP FLOOR IMPROVES THE STACK CLASS BUT NOT ENOUGH:
        comb(5.2/0.05) 35 mm over pyramid(p2, tip 0.1) 15 mm floor at
        phi0 reads 0.165 ± 0.025 (floor aspect 7.5 alone would read
        ~0.137; wall tops and blocked obliques cost the rest).

    P4  THE STACK IS PHI-SAFE WHERE THE BARE PYRAMID IS NOT: at phi30
        the stack moves <= 25 % (hex walls 1.06x, fine-pitch floor
        phi-mild), i.e. <= 0.21. IF P2 and P4 both hold, the stack WINS
        the worst-phi comparison against the easy pyramid (0.21 vs 0.30)
        and the user's instinct is right at equal ease-of-build — the
        verdict table then needs a third finalist.

    P5  EASY PYRAMID HEAD-ON STAYS SHARP-CLASS: 0.027-0.040 (sharp tip,
        no upward flat; aspect has never moved head-on for sharp fields).

Anchor: P5_j00; the stack pairs with sweep_floor.csv via identical
top/bot params except bot_depth.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase515.csv")
FORMJSON = os.path.join(RESULTS, "form_phase515.json")
OUT = "/tmp/phase515"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
EASY = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
        "pitch": 4.0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
STACK = {"face_w": 60.0, "face_h": 60.0, "margin_depths": 2.0,
         "backing": 2.0, "seed": 23,
         "top": "comb", "top_depth": 35.0,
         "top_params": {"jitter": 0.0, "pitch": 5.2, "wall_bot": 0.05,
                        "wall_top": 0.05},
         "bot": "pyramid", "bot_depth": 15.0,
         "bot_params": {"margin_depth_ref": 50.0, "pitch": 2.0,
                        "tip_flat": 0.1}}

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
# (tag, family, params, phi)
TOTALS = [
    ("P5_j00",          "floor", ANCHOR, 0.0),
    ("P515_easy",       "floor", EASY,   0.0),
    ("P515_easy_p30",   "floor", EASY,   30.0),
    ("P515_stack",      "stack", STACK,  0.0),
    ("P515_stack_p30",  "stack", STACK,  30.0),
]
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.15 — the easy pyramid, and the stack at worst azimuth")
    print("=" * 74)
    for tag, family, prm, phi in TOTALS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
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
                if phi:
                    cfg["phi_deg"] = phi
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "stack"),
                             "phi": phi, "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-15s phi %4.1f  worst %.5f %%" % (tag, phi, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P515_easy ===", flush=True)
    entry = {"tag": "P515_easy", "family": "floor", "topology": "pyramid",
             "process": "press", "params": EASY, "pitch": 4.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["winding"] = "out"
    fout["P515_easy"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
