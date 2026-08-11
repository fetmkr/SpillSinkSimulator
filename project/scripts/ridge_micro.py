"""
Can hierarchy buy back the depth?

    Blender --background --factory-startup --python scripts/ridge_micro.py

Bounce count in a V-groove depends only on pitch/depth, so a 150 mm deep
groove can be traded for a 50 mm one at a third of the pitch -- except the tip
fraction (tip width / pitch) then triples, and the tip is the entire return.

Hierarchy is the alternative: serrating each flank makes one macro bounce cost
several micro bounces, so the flank behaves as though its reflectance were
rho^k and the macro groove needs far fewer of them. That is how moth-eye
gratings, carbon nanotube forests and ultra-black deep-sea fish skin all work.

The question is whether it survives contact with a real render, since the 2D
ray trace only tracks specular paths and the micro teeth are hit at very
different angles depending on where in the macro groove they sit.
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
RENDERS = os.path.join(ROOT, "renders", "ridge_micro")
RESULTS = os.path.join(ROOT, "results")

VIEW = [{"mode": "hemi_view", "theta": float(t)} for t in range(-80, 81, 10)]
FINE = [{"mode": "angle", "theta": float(t), "sun_angle_deg": 0.5}
        for t in range(-60, 61, 5)]


def case(tag, params):
    return {"tag": tag, "family": "ridge",
            "out_dir": RENDERS,
            "results_dir": os.path.join(RESULTS, "ridge_micro"),
            "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
            # defaults first, so a case can override pitch or tip width
            # arc_segments 24: the tessellation test showed 6 facets put fake
            # mirror normals at +/-15/45/75 deg and manufactured a 6.7x glint
            "params": {"pitch_mean": 20.0, "tip_width": 0.2,
                       "arc_segments": 24, **params},
            "renders": VIEW + FINE,
            "rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
            "rho_chamber": 0.005, "rho_control": 0.05}


# The first run of this sweep used teeth whose depth was tied to their pitch,
# which made 3 mm teeth inside a 20 mm groove; the drawing showed them meeting
# across the ridge tips and pinching the mouth shut. Tooth depth is now
# absolute and tapers to zero at both ends of each flank, and the tooth size is
# swept over two decades instead of being guessed once.
CASES = [
    case("N_d050_plain", dict(depth=50.0)),
    case("N_d150_plain", dict(depth=150.0)),
]
for _md in (0.05, 0.1, 0.3, 1.0):
    CASES.append(case("N_d050_t%03d" % int(_md * 100),
                      dict(depth=50.0, micro_pitch=1.0, micro_depth=_md)))
for _mp in (0.3, 3.0):
    CASES.append(case("N_d050_p%02d_t010" % int(_mp * 10),
                      dict(depth=50.0, micro_pitch=_mp, micro_depth=0.1)))
CASES.append(case("N_d030_t010",
                  dict(depth=30.0, micro_pitch=1.0, micro_depth=0.1)))
CASES.append(case("N_d030_p040", dict(depth=30.0, pitch_mean=4.0,
                                      tip_width=0.04)))


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        d = describe(RidgeParams(**cfg["params"]))
        print("[CASE] (%d/%d) %-18s depth %5.0f  pitch %5.1f  half-angle %5.2f  "
              "macro bounces %4.1f  tip frac %.4f  t+%.0fs"
              % (i, len(CASES), cfg["tag"], d["depth_mm"], d["pitch_mean_mm"],
                 d["half_angle_deg"], d["est_bounces"], d["tip_fraction"],
                 time.time() - t0), flush=True)
        rows.extend(flatten(BR.run(cfg)))

    path = os.path.join(RESULTS, "sweep_ridge_micro2.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[DONE] {path}  ({len(rows)} rows, {time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
