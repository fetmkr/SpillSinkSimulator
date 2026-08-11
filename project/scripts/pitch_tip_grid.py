"""
How coarse can the pitch go, and how blunt can the tip be?

    Blender --background --factory-startup --python scripts/pitch_tip_grid.py

A print showed what the sweeps had implied: the ridge tip has to be thin, and a
thin tip is the hard part to make. The way out is that only the RATIO tip/pitch
matters for the head-on return, so a coarser pitch buys tolerance on the tip --
a 0.8 mm tip at 13 mm pitch is a smaller fraction of the face (6.2%) than a
0.4 mm tip at 4 mm pitch (10%), and 13 mm pitch is far easier to make.

What stops the pitch growing is the other end of the angle range. Bounce count
goes as depth/pitch, so a coarse pitch at fixed depth empties the groove out
and grazing incidence gets worse. The existing sweep already shows the two
pulling opposite ways; this maps the full grid so the trade can be read off
instead of guessed.

Grid: pitch 8 / 13 / 20 / 30 mm  x  tip 0.4 / 0.8 / 1.6 mm  x  depth 30 / 50.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile_ridge import RidgeParams, describe                   # noqa: E402
from ridge_sweep import flatten                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "grid")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in range(-80, 81, 10)]


def case(depth, pitch, tip):
    return {"tag": "G_d%02d_p%02d_t%02d" % (depth, pitch, tip * 10),
            "family": "ridge", "out_dir": RENDERS,
            "results_dir": os.path.join(RESULTS, "grid"),
            "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
            "params": {"depth": depth, "pitch_mean": pitch, "tip_width": tip,
                       "arc_segments": 24, "valley_round": max(0.3, tip * 0.8)},
            "renders": VIEW,
            "rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
            "rho_chamber": 0.005, "rho_control": 0.05}


CASES = [case(d, p, t)
         for d in (30.0, 50.0)
         for p in (8.0, 13.0, 20.0, 30.0)
         for t in (0.4, 0.8, 1.6)]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        d = describe(RidgeParams(**cfg["params"]))
        print("[CASE] (%d/%d) %-18s depth %3.0f pitch %4.1f tip %.1f "
              "(%.2f%%)  A=%.1f  bounces %4.1f  t+%.0fs"
              % (i, len(CASES), cfg["tag"], d["depth_mm"], d["pitch_mean_mm"],
                 d["tip_width_mm"], d["tip_fraction"] * 100,
                 d["depth_mm"] / d["pitch_mean_mm"], d["est_bounces"],
                 time.time() - t0), flush=True)
        rows.extend(flatten(BR.run(cfg)))

    path = os.path.join(RESULTS, "sweep_pitch_tip.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[DONE] {path}  ({len(rows)} rows, {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
