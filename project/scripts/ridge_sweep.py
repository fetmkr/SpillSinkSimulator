"""
Sweep the beam-dump ridge family.

    Blender --background --factory-startup --python scripts/ridge_sweep.py

Two axes measured together, because for this family they should stop being
separate problems:

  hemi_view  total reflected fraction for a beam arriving at theta
             (reciprocity; the flat rho=0.05 control must read 0.05 at every
             theta, which is the built-in check)
  angle      what a front observer actually sees, sampled finely enough to
             catch a specular glint

Prediction under test, from beam-dump practice and the lip law:
    return ~ 0.63 * (tip width / pitch) * (rho / 0.05)
with the multi-bounce floor pushed to nothing because a pitch-20 depth-100
groove takes 5-13 bounces (2D ray trace) instead of the slat family's 1-2.
If that holds, tip sharpness is the only manufacturing spec that matters and
the coating requirement collapses.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile_ridge import RidgeParams, describe                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "ridge")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in range(-80, 81, 10)]
FINE = [{"mode": "angle", "theta": float(t), "sun_angle_deg": 0.5}
        for t in range(-60, 61, 5)]


def case(tag, params, renders, **extra):
    cfg = {"tag": tag, "family": "ridge",
           "out_dir": RENDERS, "results_dir": os.path.join(RESULTS, "ridge"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": params, "renders": renders,
           "rho_slat": 0.05, "rho_specular": 0.05, "spec_roughness": 0.05,
           "rho_chamber": 0.05, "rho_control": 0.05}
    cfg.update(extra)
    return cfg


def cases():
    out = []
    # 1) tip width -- the lip, and the prediction's only free variable
    for tw in (0.05, 0.2, 0.5, 1.0, 2.0):
        out.append(case(f"R_tip{int(tw*100):03d}",
                        {"depth": 100.0, "pitch_mean": 20.0, "tip_width": tw},
                        VIEW))
    # 2) groove depth -- sets the bounce count, hence how black the coating
    #    actually needs to be
    for d in (25.0, 50.0, 100.0, 150.0):
        out.append(case(f"R_depth{int(d):03d}",
                        {"depth": d, "pitch_mean": 20.0, "tip_width": 0.2},
                        VIEW))
    # 3) coating: does a deep groove really let ordinary black paint work?
    for rho, rg in ((0.005, 0.05), (0.02, 0.05), (0.05, 0.05),
                    (0.05, 0.30), (0.05, 0.60)):
        out.append(case(f"R_rho{int(rho*1000):03d}_g{int(rg*100):02d}",
                        {"depth": 100.0, "pitch_mean": 20.0, "tip_width": 0.2},
                        VIEW, rho_slat=rho, rho_specular=rho,
                        spec_roughness=rg))
    # 4) glint check on the leading candidate, finely sampled
    out.append(case("R_glint_best",
                    {"depth": 100.0, "pitch_mean": 20.0, "tip_width": 0.2},
                    FINE))
    out.append(case("R_glint_rho05_g30",
                    {"depth": 100.0, "pitch_mean": 20.0, "tip_width": 0.2},
                    FINE, spec_roughness=0.30))
    return out


def flatten(res):
    rows = []
    d = res["derived"]
    for name, rec in res["modes"].items():
        rows.append({
            "tag": res["tag"],
            "mode": name.split("__")[1].rsplit("_th", 1)[0],
            "theta": rec["theta"],
            "ratio_vs_flat": rec["ratio_mean"],
            "panel_mean": rec["panel"]["mean"],
            "control_mean": rec["control"]["mean"],
            "panel_p99": rec["panel"]["p99"],
            "panel_max": rec["panel"]["max"],
            "rho_slat": res["rho_slat"],
            "spec_roughness": res["spec_roughness"],
            "depth_mm": d["depth_mm"],
            "pitch_mm": d["pitch_mean_mm"],
            "tip_width_mm": d["tip_width_mm"],
            "tip_fraction": d["tip_fraction"],
            "half_angle_deg": d["half_angle_deg"],
            "est_bounces": d["est_bounces"],
            "predicted_return": d["predicted_return_rho05"],
            "png": rec["png"],
        })
    return rows


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    cs = cases()
    for i, cfg in enumerate(cs, 1):
        d = describe(RidgeParams(**cfg["params"]))
        print("[CASE] (%d/%d) %-22s half-angle %5.2f deg  bounces %4.1f  "
              "tip frac %.4f  t+%.0fs"
              % (i, len(cs), cfg["tag"], d["half_angle_deg"], d["est_bounces"],
                 d["tip_fraction"], time.time() - t0), flush=True)
        rows.extend(flatten(BR.run(cfg)))

    path = os.path.join(RESULTS, "sweep_ridge.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[DONE] {path}  ({len(rows)} rows, {time.time()-t0:.0f}s)",
          flush=True)


if __name__ == "__main__":
    main()
