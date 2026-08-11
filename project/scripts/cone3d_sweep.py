"""
First sweep of the 3D cone family, against a re-measured 1D V-groove.

    Blender --background --factory-startup --python scripts/cone3d_sweep.py

Two things are being asked.

1. Does going 2D buy what the arithmetic says? The head-on return has been the
   exposed tip in every 1D family, and a cone's tip is a point rather than a
   line, so its exposed fraction is pi*r^2/cell instead of 2r/pitch -- 18x
   smaller at 13 mm pitch and a 0.8 mm tip. The smoke test says NO: it read
   0.0344% head-on where the tip-only estimate predicts 0.0017%, so something
   other than the tip dominates. The tip series here settles which.

2. Is it more isotropic? The 1D groove runs 0.026 / 0.029 / 0.266% across
   head-on, +/-40 and grazing. The smoke test put the cone at 0.034 / 0.005 /
   0.157 -- far flatter, and flat is what the Gaboon viper's black scales are.

The 1D reference cases are re-run here, not quoted from the earlier sweeps,
because both families were extended in Z after a margin defect was found: a
tilted camera was running off the end of the tile and reading world background,
which inflated everything above |theta| = 50. Old grazing numbers are void.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "cone3d")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in range(-80, 81, 10)]
COAT = {"rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
        "rho_chamber": 0.005, "rho_control": 0.05}


def cone(tag, **params):
    cfg = {"tag": tag, "family": "cone3d", "out_dir": RENDERS,
           "results_dir": os.path.join(RESULTS, "cone3d"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"depth": 50.0, "pitch": 13.0, "tip_radius": 0.4,
                      **params},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


def ridge(tag, **params):
    cfg = {"tag": tag, "family": "ridge", "out_dir": RENDERS,
           "results_dir": os.path.join(RESULTS, "cone3d"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"depth": 50.0, "pitch_mean": 13.0, "tip_width": 0.8,
                      "arc_segments": 24, "valley_round": 0.4, **params},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


CASES = [
    # the 1D reference, re-measured with the corrected Z extent
    ridge("R_ref_d50_p13"),
    ridge("R_ref_d50_p08", pitch_mean=8.0),

    # tip series: if head-on is tip-dominated it must fall with r^2
    cone("C_tip005", tip_radius=0.05),
    cone("C_tip020", tip_radius=0.2),
    cone("C_tip040"),
    cone("C_tip080", tip_radius=0.8),

    # aspect ratio: cones let a ray walk azimuthally and escape, so they may
    # simply need more depth per pitch than a groove does
    cone("C_d30", depth=30.0),
    cone("C_d80", depth=80.0),
    cone("C_d120", depth=120.0),

    # pitch
    cone("C_p08", pitch=8.0),
    cone("C_p20", pitch=20.0),

    # arrangement
    cone("C_square", lattice="square"),
    cone("C_nojitter", jitter=0.0),
    # bird of paradise: barbules tilted ~30 deg, darkest from one direction
    cone("C_tilt20", tilt_deg=20.0),
    cone("C_tilt30", tilt_deg=30.0),
    cone("C_tiltjit", tilt_deg=0.0, tilt_jitter=25.0),
]


def flat(res):
    d = res["derived"]
    rows = []
    for name, rec in res["modes"].items():
        rows.append({
            "tag": res["tag"], "family": d.get("family", "ridge"),
            "theta": rec["theta"],
            "rho": rec["panel"]["mean"], "ratio": rec["ratio_mean"],
            "control": rec["control"]["mean"],
            "depth_mm": d["depth_mm"],
            "pitch_mm": d.get("pitch_mm", d.get("pitch_mean_mm")),
            "tip_mm": d.get("tip_width_mm"),
            "tip_fraction": d.get("tip_fraction"),
            "aspect": d.get("aspect", d["depth_mm"] / d.get("pitch_mean_mm", 1)),
            "lattice": d.get("lattice", "-"),
            "tilt_deg": d.get("tilt_deg", 0.0),
        })
    return rows


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        print("[CASE] (%d/%d) %-16s t+%.0fs" % (i, len(CASES), cfg["tag"],
                                                time.time() - t0), flush=True)
        rows.extend(flat(BR.run(cfg)))
    path = os.path.join(RESULTS, "sweep_cone3d.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[DONE] %s  (%d rows, %.0fs)" % (path, len(rows), time.time() - t0),
          flush=True)


if __name__ == "__main__":
    main()
