"""Phase 9.f: the walkable floor — a coarse grate over a pyramid pit,
measured at the angles a floor actually faces.

    Blender --background --factory-startup --python scripts/sweep_phase9f.py

WHY. The venue photo shows the floor band as bright as the walls, and a
floor must be WALKED ON — pyramid tiles cannot be laid where feet go.
The proposed build (RF-anechoic precedent) is a load-bearing grate over
a pyramid pit: light passes the grid and dies below, shoes ride the
bars. That object was never measured. The stack family measures it
directly: comb top (the grate), pyramid floor below.

AXES, honestly scoped: a floor's deployment axes are TOTALS at
standing-viewer angles (a person 1.6 m tall looking at floor 2-5 m
away sees it at 50-70 deg from its normal) and at beam angles
(40-70 deg). The form/head-on protocol looks straight DOWN at the
panel — a view no audience has of a floor — so it is NOT run;
scoped out with reason, not skipped silently. The 9.2 area law
already warns what it would say: 3 mm bar tops at 40 mm pitch are
15 % flat land, so this grate must never be used on a WALL.

    PREDICTIONS, numeric, before any render.

    P1  THE IN-SWEEP FLOOR REFERENCE REPRODUCES THE BOOK: pyramid
        4/20/0.1 alone reads worst(5th) = 0.17668 % and graze
        -50/-60/-70 = 0.18413 / 0.19210 / 0.19805 % (seed
        determinism: all digits).
    P2  GRATE 40/wall 3/depth 40 over the pyramid pit, worst over
        3 mats x 5 theta: 0.30 +- 0.08 % — the pit owns normal
        incidence, the bars add wall-grazing glint.
    P3  GRAZE BAND (-50/-60/-70), the axis that matters: worst
        0.30 +- 0.15 %, and >= 2.5x better than a flat Musou floor
        at the same angles (book: 1.44 / 2.23 / 4.27 %).
    P4  FINER GRATE 25/3/40 is WORSE, not better (more bar land,
        more wall area): +10-40 % over the 40 grate on both bands.

    DECISION RULE, registered: the walkable grate floor ships iff
    graze-band worst <= 0.45 % AND 5-theta worst <= 0.40 %.
    Otherwise the floor stays content-clipping + dark covering.

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
CSV = os.path.join(RESULTS, "sweep_phase9f.csv")
OUT = "/tmp/phase9f"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}


def grate(cpitch, wall, cdepth, fdepth=20.0):
    return {"face_w": 60.0, "face_h": 60.0, "margin_depths": 2.0,
            "backing": 2.0, "seed": 23,
            "top": "comb", "top_depth": cdepth,
            "top_params": {"jitter": 0.0, "pitch": cpitch,
                           "wall_bot": wall, "wall_top": wall},
            "bot": "pyramid", "bot_depth": fdepth,
            "bot_params": {"margin_depth_ref": 60.0, "pitch": 4.0,
                           "tip_flat": 0.1}}


ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
TH5 = (0.0, -20.0, 20.0, -40.0, 40.0)
GRAZE = (-50.0, -60.0, -70.0)
DESIGNS = [
    ("P9f_floor_ref", "floor", FINAL),
    ("P9f_grate40", "stack", grate(40.0, 3.0, 40.0)),
    ("P9f_grate25", "stack", grate(25.0, 3.0, 40.0)),
]
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def run_one(tag, family, prm, mat, th):
        body, spec = BR.coating_split(DF[mat])
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
        rows.append({"tag": tag, "family": family,
                     "topology": prm.get("kind", prm.get("top", "?")),
                     "phi": 0, "seed": 23, "diffuse_frac": mat,
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(prm, sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 9.f — the walkable grate floor")
    print("=" * 74)

    v = run_one("P5_j00", "floor", ANCHOR, "d100", -40.0)
    print("  anchor: %.5f %% (book 0.13392)" % (100 * v), flush=True)

    for tag, family, prm in DESIGNS:
        w5 = 0.0
        wg = 0.0
        for mat in ALL:
            for th in TH5:
                w5 = max(w5, run_one(tag, family, prm, mat, th))
            for th in GRAZE:
                wg = max(wg, run_one(tag, family, prm, mat, th))
        print("  %-14s worst(5th) %.4f %%   worst(graze) %.4f %%"
              % (tag, 100 * w5, 100 * wg), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
