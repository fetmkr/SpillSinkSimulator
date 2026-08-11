"""
How shallow can it go, and what is the measurement floor?

    Blender --background --factory-startup --python scripts/test_floor.py

Three things at once, all of which the audit said were missing:

1. THE FLOOR OF THE CHAIN. A panel with rho = 0.0 must read exactly 0. Whatever
   it actually reads is the floor of the whole measurement, and two "structural
   floors" of 0.0030 and 0.0029 were previously quoted for geometries that
   share nothing -- which is what a measurement floor looks like.

2. NOISE. cy.seed was hard-coded to 0 and never varied, and every number in the
   project is a single point estimate. Same case at five seeds, and at four
   sample counts.

3. HOW SHALLOW. Bounce count is set by depth/pitch alone, so the two scale
   together. With a mathematically sharp tip there is no lip term left, and the
   only question is how few bounces the coating can afford. This walks
   depth/pitch = 2.5 (about 4 bounces) down from 50 mm to 5 mm, and separately
   sharpens the tip at fixed depth.
"""

import sys
import os
import csv

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "floor")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in (-60, -30, 0, 30, 60)]


def case(tag, params, **extra):
    cfg = {"tag": tag, "family": "ridge", "out_dir": RENDERS,
           "results_dir": os.path.join(RESULTS, "floor"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"pitch_mean": 20.0, "tip_width": 0.2,
                      "arc_segments": 24, **params},
           "renders": VIEW,
           "rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
           "rho_chamber": 0.005, "rho_control": 0.05}
    cfg.update(extra)
    return cfg


def cases():
    out = []
    # 1) the floor: a perfectly black panel must read 0
    out.append(case("F_rho000", {"depth": 50.0},
                    rho_slat=0.0, rho_specular=0.0, rho_chamber=0.0))
    out.append(case("F_rho000_sharp", {"depth": 50.0, "tip_width": 0.001},
                    rho_slat=0.0, rho_specular=0.0, rho_chamber=0.0))

    # 2) tip sharpness with no manufacturing limit
    for tw in (0.001, 0.01, 0.05, 0.2):
        out.append(case(f"F_tip{tw:g}".replace(".", "p"),
                        {"depth": 50.0, "tip_width": tw}))

    # 3) shrink everything at constant depth/pitch = 2.5, sharp tip
    for d in (50.0, 25.0, 12.5, 5.0):
        out.append(case(f"F_scale_d{d:g}".replace(".", "p"),
                        {"depth": d, "pitch_mean": d / 2.5,
                         "tip_width": d / 2.5 * 0.0005}))
    # and at a deeper aspect, which buys bounces instead of depth
    for d in (25.0, 12.5):
        out.append(case(f"F_deep_d{d:g}".replace(".", "p"),
                        {"depth": d, "pitch_mean": d / 7.5,
                         "tip_width": d / 7.5 * 0.0005}))
    return out


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows = []
    for cfg in cases():
        print("[CASE]", cfg["tag"], cfg["params"], flush=True)
        res = BR.run(cfg)
        for name, rec in res["modes"].items():
            rows.append({"tag": cfg["tag"], "rho": cfg["rho_slat"],
                         "depth": cfg["params"]["depth"],
                         "pitch": cfg["params"]["pitch_mean"],
                         "tip": cfg["params"]["tip_width"],
                         "seed": 0, "samples": 384,
                         "theta": rec["theta"], "ratio": rec["ratio_mean"],
                         "panel_mean": rec["panel"]["mean"],
                         "control_mean": rec["control"]["mean"]})

    # 2) noise: same case, five seeds, then four sample counts
    base = case("F_noise", {"depth": 50.0})
    base["renders"] = [{"mode": "hemi_view", "theta": 0.0}]
    for seed in range(5):
        pass
        res = BR.run(dict(base, tag=f"F_seed{seed}", cycles_seed=seed))
        rec = list(res["modes"].values())[0]
        rows.append({"tag": "F_seed", "rho": 0.005, "depth": 50.0,
                     "pitch": 20.0, "tip": 0.2, "seed": seed, "samples": 384,
                     "theta": 0.0, "ratio": rec["ratio_mean"],
                     "panel_mean": rec["panel"]["mean"],
                     "control_mean": rec["control"]["mean"]})
    for s in (384, 1536, 6144):
        res = BR.run(dict(base, tag=f"F_samp{s}", samples=s))
        rec = list(res["modes"].values())[0]
        rows.append({"tag": "F_samples", "rho": 0.005, "depth": 50.0,
                     "pitch": 20.0, "tip": 0.2, "seed": 0, "samples": s,
                     "theta": 0.0, "ratio": rec["ratio_mean"],
                     "panel_mean": rec["panel"]["mean"],
                     "control_mean": rec["control"]["mean"]})

    path = os.path.join(RESULTS, "floor_test.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
