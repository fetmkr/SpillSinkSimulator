"""Phase 5.7: is the face-60 measurement biased? The anomaly from 5.6, hunted.

    Blender --background --factory-startup --python scripts/sweep_phase57.py

WHY. Phase 5.6 found two things it could not explain, only contain:
  (a) a margin-less ridge flat reads 21 % low at face 60 (fixed by face 100,
      cause not isolated), and
  (b) a "flat" built as a fully truncated pyramid field (floor family,
      tip_flat = pitch, real margins) reads 0.647 % against a closed-form
      1.0 % — 35 % low, worse than (a), UNEXPLAINED.
Every Phase 5 total was measured on the floor family at face 60. If (b) is a
face-60 window artifact rather than a property of that degenerate geometry,
the entire phase's numbers carry an unknown bias. That possibility outranks
every remaining design question.

    PREDICTIONS, numeric, written before any render. Grading against these.

    P1  THE CHAMPION IS FACE-INVARIANT: P5_j00 re-measured at face 100
        reads 0.13392 % ± 4 % (worst over 3 mats x 5 theta). rho_dh is
        intensive; a periodic field's edge cells are the only face effect
        and 20 %-inset windows exclude them. If this FAILS, Phase 5 is
        systemically biased and everything pauses for re-measurement.

    P2  THE WINNER IS FACE-INVARIANT TOO: p2/d18 at face 100 reads
        0.13015 % ± 5 %.

    P3  THE (b) ANOMALY IS A FACE/WINDOW ARTIFACT, NOT GEOMETRY: the
        truncated-flat field at face 100 recovers to 0.99 % ± 0.06 %
        (d76, worst over theta). Sub-prediction: one step before
        degeneracy, tip_flat 1.9 at face 60 reads 0.93 % ± 0.07 % (the
        0.1 mm-deep V-groove barely traps) — i.e. the ladder is smooth
        and only the measurement, not the shape, breaks at face 60.

    P4  THE RIDGE FLAT ROWS REPRODUCE THE 5.6 PROBES in CSV form:
        face 60 -> 0.78 % ± 0.03, face 100 -> 0.998 % ± 0.02 (d76,
        theta 0 worst-of-5 close behind at 40 deg).

WHAT IS AT STAKE. P1/P2 hold + P3 holds = Phase 5 verdicts stand, the
anomaly is closed as "degenerate flat-field measurements need face >= 100",
and the rule becomes: any near-flat design must be measured at face 100.
P1 or P2 fail = stop, void, re-measure the phase.

Anchor: P5_j00 at face 60, identical params to sweep_phase5.csv.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase57.csv")
OUT = "/tmp/phase57"

P0 = 5.500550055005501
def pyr(face, depth, pitch, tip):
    return {"kind": "pyramid", "face_w": face, "face_h": face,
            "depth": depth, "pitch": pitch, "tip_flat": tip,
            "margin_depths": 2.0, "backing": 2.0}
def flat_ridge(face):
    return dict(face_w=face, face_h=face, depth=0.001, pitch_mean=50.0,
                tip_width=50.0, tip_round=False, pitch_jitter=0.0,
                arc_segments=4, valley_round=0.0, margin_depths=6.5)

# (tag, family, params, mats)
ALL = ("d00", "d76", "d100")
D76 = ("d76",)
DESIGNS = [
    ("P5_j00",        "floor", pyr(60.0, 50.0, P0, 0.0),  ALL),   # anchor
    ("P57_j00_f100",  "floor", pyr(100.0, 50.0, P0, 0.0), ALL),
    ("P57_p02_f100",  "floor", pyr(100.0, 18.0, 2.0, 0.0), ALL),
    ("P57_e19_f60",   "floor", pyr(60.0, 18.0, 2.0, 1.9), D76),
    ("P57_e20_f60",   "floor", pyr(60.0, 18.0, 2.0, 2.0), D76),
    ("P57_e20_f100",  "floor", pyr(100.0, 18.0, 2.0, 2.0), D76),
    ("P57_flat_f60",  "ridge", flat_ridge(60.0), D76),
    ("P57_flat_f100", "ridge", flat_ridge(100.0), D76),
]
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "face_w", "tip_flat", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.7 — face invariance and the truncated-flat anomaly")
    print("=" * 74)
    for tag, family, prm, mats in DESIGNS:
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in mats:
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
                             "topology": prm.get("kind", "flat"),
                             "face_w": prm["face_w"],
                             "tip_flat": prm.get("tip_flat", ""),
                             "seed": 23, "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-15s face %5.0f  mats %-12s worst %.5f %%"
              % (tag, prm["face_w"], ",".join(mats), 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
