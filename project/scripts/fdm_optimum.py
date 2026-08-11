"""
Optimum pitch for a printable 0.4 mm ridge tip.

    Blender --background --factory-startup --python scripts/fdm_optimum.py

A 0.4 mm nozzle cannot lay down a feature narrower than the extrusion width,
so the ridge tip is pinned at ~0.4 mm instead of the 0.04 mm the design wanted.
That is not a small change: the tip is the head-on exposed area and the return
goes as roughly 0.5 * tip / pitch.

With the tip fixed, pitch stops being free and acquires an optimum:

    narrow pitch   more bounces (90 / 2*atan(pitch/2*depth)) but the tip takes
                   a larger fraction of the face
    wide pitch     smaller tip fraction but the groove opens up and the bounce
                   count collapses -- at depth 30 and pitch 40 it is down to
                   1.3, which is barely a groove at all

Both terms are swept here at each of three depths, so the answer is measured
rather than argued.
"""

import sys
import os
import csv
import math
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile_ridge import RidgeParams, describe                   # noqa: E402
from ridge_sweep import flatten                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "fdm")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in range(-80, 81, 10)]
FINE = [{"mode": "angle", "theta": float(t), "sun_angle_deg": 0.5}
        for t in range(-60, 61, 5)]

TIP = 0.4          # 0.4 mm nozzle: one extrusion width is the smallest feature


def case(tag, params):
    return {"tag": tag, "family": "ridge", "out_dir": RENDERS,
            "results_dir": os.path.join(RESULTS, "fdm"),
            "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
            "params": {"tip_width": TIP, "arc_segments": 24,
                       "valley_round": 0.3, **params},
            # total return only: the gloss sweep already established that
            # roughness 0.30 does not glint, so the fine angle scan is not
            # buying anything here and it doubles the run time
            "renders": VIEW,
            "rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
            "rho_chamber": 0.005, "rho_control": 0.05}


CASES = []
for depth in (30.0, 50.0, 80.0):
    for pitch in (3.0, 5.0, 8.0, 13.0, 20.0):
        CASES.append(case("P_d%03d_p%02d" % (depth, pitch),
                          dict(depth=depth, pitch_mean=pitch)))
# and the unprintable reference, to price what the nozzle costs
CASES.append({**case("P_d030_p04_SHARP",
                     dict(depth=30.0, pitch_mean=4.0)),
              "params": {"tip_width": 0.04, "arc_segments": 24,
                         "valley_round": 0.12, "depth": 30.0,
                         "pitch_mean": 4.0}})


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        d = describe(RidgeParams(**cfg["params"]))
        print("[CASE] (%d/%d) %-20s depth %4.0f pitch %5.1f  tip %.2f "
              "(%.1f%% of face)  half-angle %5.2f  bounces %5.1f  t+%.0fs"
              % (i, len(CASES), cfg["tag"], d["depth_mm"], d["pitch_mean_mm"],
                 d["tip_width_mm"], d["tip_fraction"] * 100,
                 d["half_angle_deg"], d["est_bounces"], time.time() - t0),
              flush=True)
        rows.extend(flatten(BR.run(cfg)))

    path = os.path.join(RESULTS, "sweep_fdm.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[DONE] {path}  ({len(rows)} rows, {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
