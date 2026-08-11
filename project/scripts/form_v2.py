"""
Form measurement on the four designs the report actually shows.

    Blender --background --factory-startup --python scripts/form_v2.py

The report's "core 0.11 vs 0.99" was quoted from two designs that are not on
the page and do not match each other: 0.11 was a cone at depth 120 / pitch 13
/ r0.4, 0.99 a groove at depth 50 / pitch 13 / tip 0.8. The design being sold
is depth 30 / pitch 7.5. So the pair was never measured.

Two further defects were found in how form was being reported:

- core_frac is unusable at large smear. It is the energy inside a fixed
  central band divided by the energy in the measurement window, and once the
  smear runs off the window the lost light leaves the DENOMINATOR too, so a
  more smeared design can score BETTER. A cone at depth 120 has twice the rms
  of one at depth 50 and a higher core_frac. rms_mm has no such failure and
  ranks the designs monotonically, so rms_mm is the number to quote.
- results/cone3d_mtf.json is stale: written before geom3d.py last changed, and
  re-running its own cases today gives different answers.

The panel is built at 400 mm and the window widened to match, so that a smear
of tens of mm is inside it and core_frac is at least meaningful for the two
designs that matter. Same coating and tip convention as sweep_v2.py.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import form_mtf as FM                                              # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

FM.OUT = os.path.join(ROOT, "renders", "form_v2")
FM.THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)
FM.LINE_Z = (-70.0, -9.0, 52.0)

FACE = 400.0
TIP_ACROSS = 0.4

CASES = [
    ("W_groove_d50_p13",
     dict(face_w=FACE, face_h=FACE, depth=50.0, pitch_mean=13.0,
          tip_width=TIP_ACROSS, arc_segments=24, valley_round=0.4,
          margin_depths=2.0), dict(COAT, family="ridge")),
    ("W_groove_d30_p75",
     dict(face_w=FACE, face_h=FACE, depth=30.0, pitch_mean=7.5,
          tip_width=TIP_ACROSS, arc_segments=24, valley_round=0.4,
          margin_depths=2.0), dict(COAT, family="ridge")),
    ("W_cone_d30_p75",
     dict(face_w=FACE, face_h=FACE, depth=30.0, pitch=7.5,
          tip_radius=TIP_ACROSS / 2.0, jitter=0.30, radial_seg=24,
          height_seg=3, margin_depths=2.0, centre_margin_pitches=1.0,
          backing=3.0, tileable=True, depth_jitter=0.0),
     dict(COAT, family="cone3d")),
    ("W_cone_d30_p375",
     dict(face_w=FACE, face_h=FACE, depth=30.0, pitch=3.75,
          tip_radius=TIP_ACROSS / 2.0, jitter=0.30, radial_seg=24,
          height_seg=3, margin_depths=2.0, centre_margin_pitches=1.0,
          backing=3.0, tileable=True, depth_jitter=0.0),
     dict(COAT, family="cone3d")),
]


def main():
    os.makedirs(FM.OUT, exist_ok=True)
    res = []
    for tag, prm, extra in CASES:
        print("[CASE]", tag, flush=True)
        res.append(FM.run_case(tag, prm, extra))
    path = os.path.join(RESULTS, "form_v2.json")
    json.dump(res, open(path, "w"), indent=2)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
