"""Phase 8.3: the audience metric — where does the window turn ON, and
what does a real floor make of it?

    Blender --background --factory-startup --python scripts/sweep_phase83.py

WHY. The lip-closed 35-degree unit measured 0.000 % for a level observer
and ~2 % for observers at -20/-40 (below the horizon). Two questions
remain before a mounting rule can be written, and both are one scan
each:

  (a) TURN-ON ANGLE: somewhere between 0 and -20 degrees the return
      switches on. That angle IS the mounting rule (how far above the
      lowest audience eye the unit must sit).
  (b) THE WHITE-WORLD DISCOUNT: the 2 % below-horizon figure mirrors a
      uniform WHITE world. A real below-horizon sightline mirrors the
      ROOM FLOOR. With a Lambertian floor plane at the sill level the
      same scan states the deployed number instead of the worst case.

Geometry: tilt 35, plate 155, void 130, lip to +22, R 1 %/surface.
Floor plane rho 0.05 (an ordinary dark floor; a trough tile would be
0.0018 — 0.05 is the conservative room).

    PREDICTIONS, numeric, before any render.

    P1  TURN-ON IS SHARP AND SITS NEAR -8: white-world scan over
        theta {-2, -5, -8, -12, -16, -20}: readings < 0.05 % at -2 and
        -5; > 1.5 % at -16 and -20; the crossing between -5 and -12.
        Medium confidence on the exact edge, high on sharpness (the
        under-edge path either clears the plate bottom or does not).

    P2  THE FLOOR DISCOUNT IS ~x20 OR BETTER: with the rho 0.05 floor,
        every theta in the same scan reads <= 0.13 % (the mirrored
        scene's own radiance bounds the return: 2R x rho_floor class,
        plus geometry). If P2 holds, even a floor-level viewer of the
        unit sees less than the pyramid wall's own 0.177 %.

    MOUNTING RULE, registered as the deliverable: if the turn-on edge
    is at -E degrees, a unit whose center sits H meters above the
    lowest audience eye is safe at every distance d > H / tan(E).
    The FINDINGS will state it with the measured E.

Anchor: P5_j00 d100@-40 must equal 0.13392 %.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase83.csv")
OUT = "/tmp/phase83"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
ENV = {"kind": "pyramid", "face_w": 100.0, "face_h": 100.0, "depth": 20.0,
       "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
BASE = {"tilt_deg": 35.0, "thickness": 2.0, "ar_roughness": 0.02,
        "void_rho": 0.0, "void_depth": 130.0, "plate_h": 155.0,
        "r_surface": 0.01, "lip_to": 22.0}
THS = (-2.0, -5.0, -8.0, -12.0, -16.0, -20.0)
COLS = ["tag", "family", "topology", "mode", "r_surface", "theta",
        "rho", "control", "ratio", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def hemi(tag, ar, th):
        cfg = {"tag": "%s_%+04.0f" % (tag, th), "family": "arplate",
               "out_dir": OUT, "results_dir": OUT, "samples": 64,
               "res_x": 480, "res_y": 220, "gpu": True, "params": ENV,
               "ar": ar, "material_mode": "ar_glass",
               "renders": [{"mode": "hemi_view", "theta": th}]}
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": "arplate",
                     "topology": "arplate", "mode": "hemi_view",
                     "r_surface": 0.01, "theta": th,
                     "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "ratio": rec["ratio_mean"],
                     "params_json": json.dumps(ar, sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 8.3 — turn-on angle and the real-floor discount")
    print("=" * 74)

    cfg = {"tag": "P5_j00_a83", "family": "floor", "out_dir": OUT,
           "results_dir": OUT, "samples": 64, "res_x": 480, "res_y": 220,
           "gpu": True, "spec_roughness": 0.30, "params": ANCHOR,
           "renders": [{"mode": "hemi_view", "theta": -40.0}],
           "material_mode": "coating"}
    body, spec = BR.coating_split(1.0)
    cfg["coating"] = {"body": body, "spec_scale": spec, "roughness": 0.30}
    cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
    res = BR.run(cfg)
    rec = list(res["modes"].values())[0]
    print("  anchor: %.5f %% (book 0.13392)" % (100 * rec["panel"]["mean"]),
          flush=True)

    # AMENDED REGISTRATION (recorded, first floor attempt VOID): the
    # sill-level infinite floor occluded the below-horizon camera and
    # drifted the control; the floor is now a 300 mm strip in the
    # panel's x-range, and the floor scan stops at -14 because beyond
    # ~-15 the strip itself occludes the 3 m camera. P2 band unchanged
    # (<= 0.13 %) over {-2..-14}; the -16/-20 white rows bound the
    # voided angles by the mirrored-scene argument.
    # v3 REGISTRATION (v2 void beyond -8: the 300 strip let the mirror
    # see white world past its edge). Floor now 220 below the sill,
    # 1000 long -- a wall-mounted unit. Prediction, before render:
    # every theta in {-2..-20} reads <= 0.15 % (mirrored scene is dark
    # floor everywhere in the scan: 2R x rho_floor class).
    for label, ar, ths in (
            ("P83_white", dict(BASE), THS),
            ("P83_floor3", dict(BASE, room_floor=0.05), THS)):
        per = {}
        for th in ths:
            per[th] = hemi(label, ar, th)
        print("  %-10s " % label + "  ".join(
            "%g:%.3f%%" % (t, 100 * v) for t, v in sorted(per.items())),
            flush=True)

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
