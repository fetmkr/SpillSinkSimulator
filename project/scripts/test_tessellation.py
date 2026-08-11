"""
Is the ridge glint physics, or is it the mesh?

    Blender --background --factory-startup --python scripts/test_tessellation.py

The ridge tip is rounded with `_arc(..., pi/2, -pi/2, arc_segments)`. With 6
segments the facet normals land on exactly +/-15, +/-45, +/-75 degrees, and a
mirror facet whose normal is phi degrees off the panel normal throws incidence
theta = 2*phi straight at a front observer. phi = 15 predicts a glint at
theta = 30 -- which is exactly where the 66.7x peak was measured.

The discriminator: change ONLY arc_segments.

    tessellation  the innermost glint moves to theta = 180/n as n rises
                  (30, 15, 7.5, 3.75 deg) at roughly constant height
    physics       it stays at 30 deg

A second, independent check comes free: the same 66.7x peak was reported for
grooves of half-angle 5.71 and 3.81 degrees with panel_mean agreeing to ten
significant figures, which no depth-dependent path could do.

Sampled at 1 degree so the peaks cannot slip between samples -- the 5 degree
grid used before steps from 1.3e-3 to 66.7 and back between adjacent points.
"""

import sys
import os
import csv
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "tess")
RESULTS = os.path.join(ROOT, "results")

FINE = [{"mode": "angle", "theta": float(t) * 1.0, "sun_angle_deg": 0.5}
        for t in range(-45, 46, 1)]


def case(tag, segs, rough):
    return {"tag": tag, "family": "ridge",
            "out_dir": RENDERS, "results_dir": os.path.join(RESULTS, "tess"),
            "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
            "params": {"depth": 150.0, "pitch_mean": 20.0, "tip_width": 0.2,
                       "arc_segments": segs},
            "renders": FINE,
            "rho_slat": 0.005, "rho_specular": 0.005,
            "spec_roughness": rough, "rho_chamber": 0.005,
            "rho_control": 0.05}


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows = []
    for segs in (6, 12, 24, 48):
        for rough in (0.05, 0.30):
            tag = f"T_seg{segs:02d}_g{int(rough*100):02d}"
            print("[TESS] %s  predicted facet glints at theta = %s"
                  % (tag, ", ".join("%.2f" % (180.0 / segs * (k + 0.5))
                                    for k in range(min(3, segs // 2)))),
                  flush=True)
            res = BR.run(case(tag, segs, rough))
            for name, rec in res["modes"].items():
                rows.append({"tag": tag, "arc_segments": segs,
                             "roughness": rough, "theta": rec["theta"],
                             "ratio": rec["ratio_mean"],
                             "panel_mean": rec["panel"]["mean"],
                             "panel_max": rec["panel"]["max"]})

    path = os.path.join(RESULTS, "tessellation_test.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
