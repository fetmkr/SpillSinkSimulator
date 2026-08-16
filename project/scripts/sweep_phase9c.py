"""Phase 9.c: the wall-floor inside corner — does it need special
treatment, or does the pyramid texture already close it?

    Blender --background --factory-startup --python scripts/sweep_phase9c.py

WHY. The venue photo shows spill brightest along wall-floor junctions,
and design law 1 (Phase 7) says concave ~90-degree corners facing the
beam are retroreflectors — measured on SMOOTH folds. Whether two
PYRAMID panels meeting at 90 degrees revive that retro, and whether a
smooth-Musou corner is even dangerous on totals, was never measured.
The `corner` scene builds a vertical wall field and a floor field
running toward the camera; observers sit at +20/+40 (above the corner,
as audience eyes are), and the window reads the corner-zone assembly.

POSTDICTIONS, marked: 32-spp previews at d00/theta+20 read 0.058 %
(pyramid corner) and 0.122 % (smooth corner). The preview also
identified the two-bounce specular retro path (floor at grazing ->
wall -> sky) and showed its Musou product F1*F2 is SMALL — the retro
is a high-reflectance disease.

    PREDICTIONS, numeric, before the sweep. Control drifts ~3 % here
    (the floor field shades a slice of the control's sky, as in 8.3);
    absolute panel means are the record, drift noted.

    P1  SMOOTH-MUSOU CORNER, worst over {d00,d100} x {+20,+40}:
        1.0-1.6 % — each face alone is a ~1.14 % flat; the specular
        pair path adds little under Musou; grazing-floor Fresnel may
        push the top of the band.

    P2  PYRAMID CORNER stays panel-class: worst over the same cells
        within 0.8-1.5x of the SAME-SWEEP pyramid wall reference at the
        same angles. The texture eats both legs of any pair path.

    P3  THE CORNER PENALTY IS A SMOOTH-SURFACE DISEASE: penalty ratio
        (corner / its own wall) at matched cells is at least 3x larger
        for smooth than for pyramid.

    DECISION RULE, registered: corners need NO special treatment
    (no cove strips, no fillets, panels simply butt at 90 degrees)
    iff the pyramid corner reads <= 1.5x the pyramid wall at both
    angles. Otherwise the junction gets a rule in the build sheet.

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
CSV = os.path.join(RESULTS, "sweep_phase9c.csv")
OUT = "/tmp/phase9c"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 100.0, "face_h": 100.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
DF = {"d00": 0.0, "d100": 1.0}
THS = (20.0, 40.0)
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def run_one(tag, family, mat, th, corner=None, prm=None):
        prm = prm or FINAL
        body, spec = BR.coating_split(DF[mat])
        cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
               "family": family, "out_dir": OUT, "results_dir": OUT,
               "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
               "spec_roughness": 0.30, "params": prm,
               "renders": [{"mode": "hemi_view", "theta": th}],
               "material_mode": "coating",
               "coating": {"body": body, "spec_scale": spec,
                           "roughness": 0.30}}
        if corner is not None:
            cfg["corner"] = corner
        cfg.update({k: v for k, v in COAT.items()
                    if k != "spec_roughness"})
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": family,
                     "topology": "corner" if corner else "pyramid",
                     "phi": 0, "seed": 23, "diffuse_frac": mat,
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(
                         dict(prm, **({"corner": corner} if corner
                                      else {})), sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 9.c — the wall-floor inside corner")
    print("=" * 74)

    v = run_one("P5_j00", "floor", "d100", -40.0, prm=ANCHOR)
    print("  anchor: %.5f %% (book 0.13392)" % (100 * v), flush=True)

    for tag, family, corner in (
            ("P9c_wall", "floor", None),
            ("P9c_pyr", "corner", {"floor_len": 300.0}),
            ("P9c_smooth", "corner", {"floor_len": 300.0,
                                      "smooth": True})):
        w = 0.0
        per = {}
        for mat in ("d00", "d100"):
            for th in THS:
                r = run_one(tag, family, mat, th, corner)
                w = max(w, r)
                per[(mat, th)] = r
        detail = "  ".join("%s@%g:%.3f%%" % (m, t, 100 * v2)
                           for (m, t), v2 in sorted(per.items()))
        print("  %-10s worst %.4f %%   [%s]" % (tag, 100 * w, detail),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
