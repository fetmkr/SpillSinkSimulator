"""
Form measurement for the ridge family.

    Blender --background --factory-startup --python scripts/ridge_mtf.py

Same LSF/MTF harness as form_mtf.py. The open question this settles: the ridge
family attenuates far harder than anything before it (observer peak 0.0095 of a
bare wall at the worst incidence, against 0.069 for the best slat design), but
attenuation was never the stated priority. What comes back has bounced 5-13
times according to the 2D ray trace, so it SHOULD be position-scrambled -- but
that was also true of the slat family, where the surviving light turned out to
be a single lip bounce that remembered exactly where the beam landed.

So the test is whether the ridge tip does the same thing at a smaller scale.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import form_mtf as FM                                              # noqa: E402
from profile_ridge import RidgeParams, describe                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

FM.OUT = os.path.join(ROOT, "renders", "ridge_mtf")
FM.THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)

BLACK = {"rho_slat": 0.005, "rho_specular": 0.005, "rho_chamber": 0.005,
         "rho_control": 0.05, "material_mode": "mixed", "family": "ridge"}

CASES = [
    # the winner on brightness
    ("G_d150_g30", {"depth": 150.0, "pitch_mean": 20.0, "tip_width": 0.2},
     dict(BLACK, spec_roughness=0.30)),
    # sharper tip: does killing the lip also kill the surviving form?
    ("G_d150_g30_tip005",
     {"depth": 150.0, "pitch_mean": 20.0, "tip_width": 0.05},
     dict(BLACK, spec_roughness=0.30)),
    # the specular version, which won on total return but glints 6.7x
    ("G_d150_g05", {"depth": 150.0, "pitch_mean": 20.0, "tip_width": 0.2},
     dict(BLACK, spec_roughness=0.05)),
    # ordinary black paint, as the fallback if the coating cannot be had
    ("G_d150_g30_rho050",
     {"depth": 150.0, "pitch_mean": 20.0, "tip_width": 0.2},
     dict(BLACK, rho_slat=0.05, rho_specular=0.05, spec_roughness=0.30)),
    # coarser pitch: a wider groove smears further but traps less
    ("G_d150_g30_p40",
     {"depth": 150.0, "pitch_mean": 40.0, "tip_width": 0.2},
     dict(BLACK, spec_roughness=0.30)),
]


def main():
    os.makedirs(FM.OUT, exist_ok=True)
    res = []
    for tag, prm, extra in CASES:
        d = describe(RidgeParams(**prm))
        print("[GEOM] %-22s depth %5.0f  half-angle %5.2f  bounces %5.1f  "
              "tip frac %.4f" % (tag, d["depth_mm"], d["half_angle_deg"],
                                 d["est_bounces"], d["tip_fraction"]),
              flush=True)
        res.append(FM.run_case(tag, prm, extra))
    path = os.path.join(RESULTS, "ridge_mtf.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=2)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
