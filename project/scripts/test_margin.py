"""
Settle the unexplained margin sensitivity before it blocks the fine-cell sweep.

    Blender --background --factory-startup --python scripts/test_margin.py

THE PROBLEM. `sweep_shapes.py` records, as a budget note, that "margin 6.5 NOT
reducible: margin 1.0 moves head-on by -15%, and the reason is not yet
understood, so it stays". That was never chased. It is now blocking, because
commercial honeycomb runs down to a 0.86 mm cell and at margin_depths 6.5 a
0.86 mm cell needs 14.2 M faces -- 7x past the point where geom_topo's truss had
to be cut. At margin 1.5 the same geometry is 1.24 M faces and buildable.

WHAT THE GEOMETRY SAYS IT NEEDS. A camera tilted to theta sees the valley floor
at depth D after travelling D/tan(90-theta) in Z. At the sweep's widest angle,
theta = 40 and D = 50, that is 42 mm, plus half the face height, so 72 mm --
which is margin_depths 1.44. Anything beyond that is geometrically unnecessary
FOR THIS ANGLE RANGE. The 6.5 figure was sized for theta = 80, where the same
formula gives 5.7 D, and it was never revisited when the objective narrowed to
+/-40.

So either the -15% is a real effect with a cause worth knowing, or it was
measured at theta values this project no longer uses. Both outcomes are useful;
guessing between them is not.

METHOD. Two geometries -- one wall network, one pillar array -- at five margins,
under all three coating models, at every theta the sweep uses. If the answer is
flat from some margin upward, that margin is the answer and the fine-cell sweep
can use it. If it is not flat, the whole measurement chain has a problem that
matters far beyond this sweep.
"""

import sys
import os
import csv
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "margin")
OUTCSV = os.path.join(RESULTS, "test_margin.csv")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
MARGINS = (1.0, 1.5, 2.0, 3.0, 6.5)

CASES = [
    ("HONE_p0650_wt010", "topo",
     dict(topology="honeycomb", face_w=FACE, face_h=FACE, depth=50.0,
          pitch=6.5, wall_top=0.1, wall_bot=0.1, jitter=0.30, backing=2.0)),
    ("CONE_p0550_r020", "cone3d",
     dict(face_w=FACE, face_h=FACE, depth=50.0, pitch=5.5, tip_radius=0.2,
          jitter=0.30, radial_seg=24, height_seg=12, backing=2.0,
          depth_jitter=0.0, profile_power=1.0)),
]

FIELDS = ["tag", "case", "margin_depths", "diffuse_frac", "theta",
          "rho", "control"]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    fh = open(OUTCSV, "w", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    t0 = 0
    for name, family, base in CASES:
        for md in MARGINS:
            prm = dict(base, margin_depths=md)
            for dfrac in DIFFUSE_FRACS:
                mname = "d%02d" % (dfrac * 100)
                body, spec = BR.coating_split(dfrac)
                tag = "%s_m%03d" % (name, md * 10)
                cfg = {"tag": "%s_%s" % (tag, mname), "family": family,
                       "out_dir": RENDERS, "results_dir": RENDERS,
                       "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                       "gpu": True, "spec_roughness": 0.30,
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30},
                       "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": t}
                                   for t in THETAS]}
                cfg.update({k: v for k, v in COAT.items()
                            if k not in ("spec_roughness",)})
                cfg["material_mode"] = "coating"
                t1 = time.time()
                res = BR.run(cfg)
                for rec in res["modes"].values():
                    w.writerow({"tag": tag, "case": name, "margin_depths": md,
                                "diffuse_frac": mname, "theta": rec["theta"],
                                "rho": rec["panel"]["mean"],
                                "control": rec["control"]["mean"]})
                fh.flush()
                print("[MARGIN] %-20s m=%.1f %-5s %5.1fs"
                      % (name, md, mname, time.time() - t1), flush=True)
    fh.close()
    print("[DONE] %s" % OUTCSV, flush=True)


if __name__ == "__main__":
    main()
