"""
Is the cone's win actually about being 3D, or just about having a smaller tip?

    Blender --background --factory-startup --python scripts/fairfight.py

The four-design comparison put the 1D V-groove at 0.0268% head-on and the 3D
cone at 0.0051%, and called that 5.2x. But the two were not tip-matched: the
groove exposes a 0.8 mm LINE every 13 mm (6.2% of the surface), the cone a
0.2 mm-radius POINT per 48.7 mm^2 cell (0.26%). A 24x difference in exposed
tip, sitting inside a family whose reflectance was already measured to be
proportional to tip/pitch. So most or all of that 5.2x could be the tip.

This re-runs the groove with the tip the cone actually gets -- 0.2 mm, which
an FDM nozzle can hold as well in a ridge as in a cone -- and at the cone's
depth and pitch as well, so depth and pitch stop being confounds too. Same
coating, same sampling, same corrected Z margin as sweep_final4.csv, so the
numbers drop straight into that table.

What survives this is the real 3D effect. What does not was the tip.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import VIEW, COAT                                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "fairfight")
RESULTS = os.path.join(ROOT, "results")


def ridge(tag, **params):
    cfg = {"tag": tag, "family": "ridge", "out_dir": RENDERS,
           "results_dir": os.path.join(RESULTS, "fairfight"),
           "samples": 512, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"depth": 50.0, "pitch_mean": 13.0, "tip_width": 0.8,
                      "arc_segments": 24, "valley_round": 0.4,
                      "margin_depths": 6.5, **params},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


def cone(tag, **params):
    cfg = {"tag": tag, "family": "cone3d", "out_dir": RENDERS,
           "results_dir": os.path.join(RESULTS, "fairfight"),
           "samples": 512, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"depth": 30.0, "pitch": 7.5, "tip_radius": 0.2,
                      "jitter": 0.30, "margin_depths": 6.5, **params},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


CASES = [
    # the groove exactly as reported, but with the tip the cone gets
    ridge("F_gr_d50_p13_t02", tip_width=0.2),
    # ...and now matched on depth and pitch too: every dimension the same as
    # the cone except the one being tested, extrusion vs revolution
    ridge("F_gr_d30_p75_t02", depth=30.0, pitch_mean=7.5, tip_width=0.2),
    ridge("F_gr_d30_p375_t02", depth=30.0, pitch_mean=3.75, tip_width=0.2),
    # and the reverse control: the cone given the groove's fat tip
    cone("F_co_d30_p75_t04", tip_radius=0.4),
    cone("F_co_d30_p75_t08", tip_radius=0.8),
]


def flat(res):
    d = res["derived"]
    rows = []
    for _, rec in res["modes"].items():
        rows.append({
            "tag": res["tag"], "family": d.get("family", "ridge"),
            "theta": rec["theta"], "rho": rec["panel"]["mean"],
            "ratio": rec["ratio_mean"], "control": rec["control"]["mean"],
            "depth_mm": d["depth_mm"],
            "pitch_mm": d.get("pitch_mm", d.get("pitch_mean_mm")),
            "tip_mm": d.get("tip_width_mm"),
            "tip_fraction": d.get("tip_fraction"),
            "aspect": d.get("aspect",
                            d["depth_mm"] / d.get("pitch_mean_mm", 1.0)),
        })
    return rows


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        print("[CASE] (%d/%d) %-18s t+%.0fs"
              % (i, len(CASES), cfg["tag"], time.time() - t0), flush=True)
        rows.extend(flat(BR.run(cfg)))
    path = os.path.join(RESULTS, "sweep_fairfight.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[DONE] %s (%d rows, %.0fs)" % (path, len(rows), time.time() - t0),
          flush=True)


if __name__ == "__main__":
    main()
