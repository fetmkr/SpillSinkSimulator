"""
Does the panel geometry overlapping the flat control change the PANEL number?

    Blender --background --factory-startup --python scripts/test_control_gap.py

The defect, found in results/sweep_topo.csv: the 0.05 flat control plate reads
0.0423 mean for honeycomb designs and as low as 0.0253, where it must read
0.0500. Contribution tracks exposed area exactly --

    truss     1.6% exposed -> control 0.05000
    shingle   1.1%         -> 0.04999
    cone      0.26%        -> 0.04987   ( 0.05 x 0.9974 = 0.04987 )
    honeycomb 13.2%        -> 0.04234   ( 0.05 x 0.868  = 0.04340 )

Cause: `blender_render.GAP = 100` mm puts the control at x = 160..220, while the
panel field runs to `face_w + margin_depths * depth` = 255 mm at depth 30. The
control plate is EMBEDDED IN THE PANEL, with cell walls growing through it.

**This has always been true.** It was invisible while every family was a pillar
array exposing well under 1% of its area. It is not new, and every control
figure ever recorded is low by the panel's own exposed fraction.

THE QUESTION THIS TEST ANSWERS. The headline metric is absolute rho_dh, which
does not divide by the control, so it may be untouched -- or the extra geometry
around the control may be changing the light field enough to move the panel too.
Reasoning cannot settle that; the project rule is to measure it.

Method: the same design, rendered at the default GAP and at a GAP wide enough
that the control sits entirely clear of the panel field. If the panel numbers
agree, the defect is confined to the control column and the absolute results
stand. If they do not, every 3D number in the project is affected.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "gaptest")
RESULTS = os.path.join(ROOT, "results")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -40.0)
MARGIN = 6.5

CASES = [
    ("honeycomb_p7.5_d30", "topo",
     dict(topology="honeycomb", face_w=FACE, face_h=FACE, depth=30.0,
          pitch=7.5, wall_top=0.4, wall_bot=1.2, margin_depths=MARGIN,
          backing=2.0, jitter=0.30)),
    ("cone_p7.5_d30", "cone3d",
     dict(face_w=FACE, face_h=FACE, depth=30.0, pitch=7.5, tip_radius=0.2,
          jitter=0.30, radial_seg=24, height_seg=12, margin_depths=MARGIN,
          backing=2.0, depth_jitter=0.0, profile_power=1.0)),
]

# default, and wide enough to clear face_w + margin_depths * depth = 255
GAPS = (100.0, 500.0)


def run_case(name, family, prm, gap, dfrac=0.0):
    BR.GAP = gap
    body, spec = BR.coating_split(dfrac)
    # `run()` sets ortho_scale from the TOTAL scene width, so widening the gap
    # at a fixed res_x silently samples the panel at fewer pixels per mm. The
    # first version of this test did exactly that and reported a 7.07% shift in
    # the cone's theta=0 figure -- 620/220 = 2.8x coarser sampling, not a
    # physical effect. Scale the resolution with the width so pixels per mm is
    # the one thing held constant.
    scale = (FACE + gap + FACE) / (FACE + 100.0 + FACE)
    res_x = int(round(RES[0] * scale))
    cfg = {"tag": "%s_gap%04d" % (name, gap), "family": family,
           "out_dir": OUT, "results_dir": OUT,
           "samples": SAMPLES, "res_x": res_x, "res_y": RES[1], "gpu": True,
           "spec_roughness": 0.30,
           "coating": {"body": body, "spec_scale": spec, "roughness": 0.30},
           "params": prm,
           "renders": [{"mode": "hemi_view", "theta": t} for t in THETAS]}
    cfg.update({k: v for k, v in COAT.items() if k not in ("spec_roughness",)})
    cfg["material_mode"] = "coating"
    res = BR.run(cfg)
    return {rec["theta"]: (rec["panel"]["mean"], rec["control"]["mean"])
            for rec in res["modes"].values()}


def main():
    os.makedirs(OUT, exist_ok=True)
    default_gap = BR.GAP
    print("[GAPTEST] default GAP = %.0f mm; panel field reaches x = %.0f mm"
          % (default_gap, FACE + MARGIN * 30.0))
    out = {}
    for name, family, prm in CASES:
        out[name] = {}
        for gap in GAPS:
            out[name]["gap%d" % gap] = run_case(name, family, prm, gap)
        print()
        print("%s" % name)
        print("  %-8s %-10s %-10s %-10s %-10s"
              % ("theta", "panel@100", "panel@500", "ctrl@100", "ctrl@500"))
        for t in THETAS:
            p1, c1 = out[name]["gap100"][t]
            p2, c2 = out[name]["gap500"][t]
            print("  %-8.0f %-10.6f %-10.6f %-10.6f %-10.6f   panel %+.2f%%"
                  % (t, p1, p2, c1, c2, 100.0 * (p1 / p2 - 1.0)))
    BR.GAP = default_gap
    path = os.path.join(RESULTS, "test_control_gap.json")
    json.dump(out, open(path, "w"), indent=2, default=str)
    print()
    print("[DONE] %s" % path)


if __name__ == "__main__":
    main()
