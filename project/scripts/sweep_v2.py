"""
The comparison re-measured after review, with the two defects that made the
first version wrong removed.

    Blender --background --factory-startup --python scripts/sweep_v2.py

1. TIP CONVENTION. profile_ridge.tip_width is a full WIDTH; geom3d.tip_radius
   is a RADIUS. The previous "tip-matched, 0.2 both" comparison therefore gave
   the groove a 0.2 mm tip against the cone's 0.4 mm across -- still a factor
   of two, in the direction that flattered the cone. Worse, 0.2 mm is half an
   FDM nozzle and cannot be printed at all, so it was not a buildable design.
   The convention here is one nozzle width, 0.4 mm across, for both:
   tip_width = 0.4 and tip_radius = 0.2.

2. TILEABLE. The cone numbers were measured on tileable=False while the STL
   and the render used tileable=True, which re-snaps the lattice to an integer
   cell count and makes it 1.3-5% denser. Measured and exported were 7.5%
   apart -- outside the lock's own tolerance. Everything here is measured on
   the geometry that is actually exported.

radial_seg is pinned at 24 everywhere: fairfight.py left it at the geom3d
default of 32 while final4.py set 24, which is harmless (1.2%) but was one
more thing differing between cases that were being compared.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import VIEW, COAT                                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "v2")
RESULTS = os.path.join(ROOT, "results")

TIP_ACROSS = 0.4        # one FDM nozzle: the minimum printable feature


def base(tag, family, params):
    cfg = {"tag": tag, "family": family, "out_dir": RENDERS,
           "results_dir": os.path.join(RESULTS, "v2"), "samples": 512,
           "res_x": 1100, "res_y": 500, "gpu": True, "params": params,
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


def ridge(tag, depth, pitch):
    return base(tag, "ridge",
                dict(depth=depth, pitch_mean=pitch, tip_width=TIP_ACROSS,
                     arc_segments=24, valley_round=0.4, margin_depths=6.5))


def cone(tag, depth, pitch):
    # exactly export_cone.build, plus the Z margin the tilted views need
    return base(tag, "cone3d",
                dict(depth=depth, pitch=pitch, tip_radius=TIP_ACROSS / 2.0,
                     jitter=0.30, radial_seg=24, height_seg=3,
                     margin_depths=6.5, centre_margin_pitches=1.0,
                     backing=3.0, tileable=True, depth_jitter=0.0))


CASES = [
    ridge("V2_groove_d50_p13", 50.0, 13.0),
    ridge("V2_groove_d30_p75", 30.0, 7.5),
    cone("V2_cone_d30_p75", 30.0, 7.5),
    cone("V2_cone_d30_p375", 30.0, 3.75),
    # the reference the "100x" claim is against: a flat plate of the coating
    base("V2_flat_coating", "ridge",
         dict(depth=0.001, pitch_mean=50.0, tip_width=50.0, tip_round=False,
              pitch_jitter=0.0, arc_segments=4, valley_round=0.0,
              margin_depths=6.5)),
]


def flat(res):
    d = res["derived"]
    return [{"tag": res["tag"], "family": d.get("family", "ridge"),
             "theta": rec["theta"], "rho": rec["panel"]["mean"],
             "control": rec["control"]["mean"],
             "depth": d["depth_mm"],
             "pitch": d.get("pitch_mm", d.get("pitch_mean_mm")),
             "tip_across": TIP_ACROSS}
            for rec in res["modes"].values()]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        print("[CASE] (%d/%d) %-20s t+%.0fs"
              % (i, len(CASES), cfg["tag"], time.time() - t0), flush=True)
        rows.extend(flat(BR.run(cfg)))
    path = os.path.join(RESULTS, "sweep_v2.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[DONE] %s (%.0fs)" % (path, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
