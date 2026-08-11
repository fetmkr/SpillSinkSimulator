"""
Form measurement for the 3D cone family — priority 1, never yet measured in 3D.

    Blender --background --factory-startup --python scripts/cone3d_mtf.py

Every family so far attenuates and none destroys form: the line comes back as a
line. The reason has been the same each time — at retro-incidence the observer
and the beam are collinear, so whatever the beam hits first is visible, and a
single bounce cannot displace a photon.

A cone might break that. In a 2D groove a ray is confined to the cross-section
plane, so wherever it ends up it is still at the same X. On a cone it is free
to walk azimuthally, which is a displacement mechanism the extruded families
structurally do not have. That is worth measuring rather than assuming: the
same azimuthal freedom is why cones trap worse per bounce.

The panel is built at 300 mm rather than the 100 mm used for the reflectance
sweeps, so the measurement window is +/-90 mm and a smear of tens of mm is not
clipped. The 1D groove is re-measured alongside under identical conditions.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import form_mtf as FM                                              # noqa: E402
import blender_render as BR                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

FM.OUT = os.path.join(ROOT, "renders", "cone3d_mtf")
FM.THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)
FM.LINE_Z = (-52.0, -7.0, 38.0)

COAT = {"rho_slat": 0.005, "rho_specular": 0.005, "spec_roughness": 0.30,
        "rho_chamber": 0.005, "rho_control": 0.05}

FACE = 300.0

CASES = [
    ("K_cone_d50_p13",
     {"face_w": FACE, "face_h": FACE, "depth": 50.0, "pitch": 13.0,
      "tip_radius": 0.4, "jitter": 0.30, "margin_depths": 2.0},
     dict(COAT, family="cone3d")),
    ("K_cone_d120_p13",
     {"face_w": FACE, "face_h": FACE, "depth": 120.0, "pitch": 13.0,
      "tip_radius": 0.4, "jitter": 0.30, "margin_depths": 2.0},
     dict(COAT, family="cone3d")),
    ("K_cone_d80_p08",
     {"face_w": FACE, "face_h": FACE, "depth": 80.0, "pitch": 8.0,
      "tip_radius": 0.4, "jitter": 0.30, "margin_depths": 2.0},
     dict(COAT, family="cone3d")),
    # same coating and depth, one dimension of freedom fewer
    ("K_ridge_d50_p13",
     {"face_w": FACE, "face_h": FACE, "depth": 50.0, "pitch_mean": 13.0,
      "tip_width": 0.8, "arc_segments": 24, "valley_round": 0.4,
      "margin_depths": 2.0},
     dict(COAT, family="ridge")),
]


def main():
    os.makedirs(FM.OUT, exist_ok=True)
    res = []
    for tag, prm, extra in CASES:
        print("[CASE]", tag, flush=True)
        res.append(FM.run_case(tag, prm, extra))
    path = os.path.join(RESULTS, "cone3d_mtf.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=2)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
