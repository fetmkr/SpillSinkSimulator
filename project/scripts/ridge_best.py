"""
The combination the two earlier families each got half of.

    Blender --background --factory-startup --python scripts/ridge_best.py

Deep V-groove (beam-dump geometry: 5-13 bounces, so the coating requirement
collapses) PLUS the ultra-black low-gloss coating that the slat family found
was the only thing that ever mattered there.

Each family failed in a different way and the failures were complementary:

  slat family   specular gave the lowest total return but a 271x glint at one
                incidence; roughness 0.30 was the interior optimum that killed
                the glint without turning the surface into a diffuser
  ridge family  deep grooves made ordinary 5% paint behave like Musou Black on
                slats, but the specular version glinted 66.7x at theta -30

So: keep the groove depth, keep the black coating, and sweep gloss to find
where the glint dies without the total return climbing back. Both metrics are
recorded for every case, because they move in opposite directions and only
looking at one is how the earlier rounds went wrong.
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
RENDERS = os.path.join(ROOT, "renders", "ridge_best")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in range(-80, 81, 10)]
FINE = [{"mode": "angle", "theta": float(t), "sun_angle_deg": 0.5}
        for t in range(-60, 61, 5)]


def case(tag, params, **extra):
    cfg = {"tag": tag, "family": "ridge",
           "out_dir": RENDERS, "results_dir": os.path.join(RESULTS, "ridge_best"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": params, "renders": VIEW + FINE,
           "rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
           "rho_chamber": 0.005, "rho_control": 0.05}
    cfg.update(extra)
    return cfg


def cases():
    out = []
    for depth in (100.0, 150.0):
        for rg in (0.05, 0.15, 0.30, 0.45):
            out.append(case(
                f"B_d{int(depth)}_g{int(rg*100):02d}",
                {"depth": depth, "pitch_mean": 20.0, "tip_width": 0.2},
                spec_roughness=rg))
    # the same geometry with ordinary black paint, so the coating upgrade can
    # be priced rather than assumed
    out.append(case("B_d100_g30_rho050",
                    {"depth": 100.0, "pitch_mean": 20.0, "tip_width": 0.2},
                    rho_slat=0.05, rho_specular=0.05, spec_roughness=0.30))
    # sharper tip, at the best expected gloss
    out.append(case("B_d100_g30_tip005",
                    {"depth": 100.0, "pitch_mean": 20.0, "tip_width": 0.05}))
    return out


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    cs = cases()
    for i, cfg in enumerate(cs, 1):
        d = describe(RidgeParams(**cfg["params"]))
        print("[CASE] (%d/%d) %-22s depth %5.0f  bounces %4.1f  rho %.3f  "
              "gloss %.2f  t+%.0fs"
              % (i, len(cs), cfg["tag"], d["depth_mm"], d["est_bounces"],
                 cfg["rho_slat"], cfg["spec_roughness"], time.time() - t0),
              flush=True)
        rows.extend(flatten(BR.run(cfg)))

    path = os.path.join(RESULTS, "sweep_ridge_best.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[DONE] {path}  ({len(rows)} rows, {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
