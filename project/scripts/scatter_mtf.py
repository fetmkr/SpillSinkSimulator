"""
Form destruction for the scatter-trough family.

    Blender --background --factory-startup --python scripts/scatter_mtf.py

Same validated LSF/MTF harness as form_mtf.py, pointed at the second geometry
family. The prediction being tested comes from the 2D ray trace:

    slat family   1 bounce with 0 mm of Z shift, or 10 bounces with 2 mm --
                  never few-bounces-with-large-shift, so form always survives
    trough family 2-4 bounces with 19-45 mm of Z shift at EVERY incidence

and from the escape-budget argument: the position-scrambled component scales
as rho^bounces while the position-preserving lip scales as rho, so scrambling
only wins once rho^(n-1) > 0.63 * thickness / pitch. For a 3-bounce trough
that means an interior around rho 0.15-0.35 -- grey, not black. Black kills
the scrambled light before it kills the lip, which is precisely the trap the
slat family fell into.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import form_mtf as FM                                              # noqa: E402
from profile_scatter import ScatterParams, describe                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

FM.OUT = os.path.join(ROOT, "renders", "scatter")
FM.THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)


def run(tag, params, extra):
    cfg_extra = {"family": "scatter"}
    cfg_extra.update(extra)
    return FM.run_case(tag, params, cfg_extra)


# depth budget is 100 mm, so trough depth = width * depth_ratio must fit
GEOM = {
    "u60": dict(width_mean=60.0, depth_ratio=1.5, shape="u"),
    "v60": dict(width_mean=60.0, depth_ratio=1.5, shape="vee"),
    "a60": dict(width_mean=60.0, depth_ratio=1.5, shape="asym"),
    "u40": dict(width_mean=40.0, depth_ratio=2.2, shape="u"),
    "u90": dict(width_mean=90.0, depth_ratio=1.05, shape="u"),
}

CASES = []
# interior reflectance is the axis the escape-budget argument is about
for rho in (0.05, 0.15, 0.35):
    CASES.append((f"S_u60_rho{int(rho*100):02d}", dict(GEOM["u60"]),
                  {"material_mode": "all_diffuse", "rho_slat": 0.005,
                   "rho_chamber": rho}))
# shape and scale, at the reflectance that argument points to
for key in ("v60", "a60", "u40", "u90"):
    CASES.append((f"S_{key}_rho15", dict(GEOM[key]),
                  {"material_mode": "all_diffuse", "rho_slat": 0.005,
                   "rho_chamber": 0.15}))
# a black lip at the mouth, to see whether hiding the shallow (one-bounce)
# part of the trough is worth the aperture it costs
CASES.append(("S_u60_rho15_lip", dict(GEOM["u60"], lip_len=12.0),
              {"material_mode": "all_diffuse", "rho_slat": 0.005,
               "rho_chamber": 0.15}))


def main():
    os.makedirs(FM.OUT, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    res = []
    for tag, prm, extra in CASES:
        d = describe(ScatterParams(**prm))
        print("[GEOM] %-18s trough %5.1f mm  apex %5.1f deg  f=%.3f  "
              "~bounces %.1f" % (tag, d["trough_depth_mm"],
                                 d["apex_angle_deg"], d["aperture_fraction"],
                                 d["est_bounces"]), flush=True)
        res.append(run(tag, prm, extra))
    path = os.path.join(RESULTS, "scatter_mtf.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=2)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
