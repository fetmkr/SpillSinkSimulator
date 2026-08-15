"""
Does the fitted coating actually reproduce the measured curve?

    Blender --background --factory-startup --python scripts/fit_coating.py
    Blender --background --factory-startup --python scripts/fit_coating.py -- sweep

blender_render.make_coating is a FIT to Filip & Vavra 2026 Fig. 6 (Musou Black
paint on a goniometer, 24488 samples; reference/SUMMARY.md has the table). The
fit was done analytically, on paper, against a Fresnel curve. Whether Cycles'
own BSDFs reproduce it is a separate question and must be measured rather than
assumed -- the old make_glossy already taught us that lesson: set to rho=0.005
it reads 0.4953%, not 0.5000%.

So: build a genuinely flat plate of the coating, read rho_dh at the seven
angles the paper reports, and print the residual against each. Nothing
downstream uses this material until the residuals are small.

`sweep` then walks body / spec_scale / ior around the paper fit, because the
analytic fit was made against an ideal Fresnel term and Cycles' mix is not
exactly that. The best cell is printed as a drop-in for the constants in
blender_render.
"""

import sys
import os
import json
import itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "renders", "fit_coating")

TARGET = BR.MUSOU_THR
FACE = 100.0

# a genuinely flat plate: tip_round OFF and no pitch jitter. With tip_round on
# (the default) each ridge is capped by a half-cylinder of radius tip_width/2,
# which is how a 25 mm washboard once got into the regression lock calling
# itself a flat plate and reading 0.353%.
PLATE = dict(face_w=FACE, face_h=FACE, depth=0.001, pitch_mean=50.0,
             tip_width=50.0, tip_round=False, pitch_jitter=0.0,
             arc_segments=4, valley_round=0.0, margin_depths=6.5)


def measure(body, spec_scale, ior, roughness=0.30, samples=768, tag="fit"):
    cfg = {"tag": tag, "family": "ridge", "out_dir": OUT,
           "results_dir": os.path.join(RESULTS, "fit_coating"),
           "samples": samples, "res_x": 900, "res_y": 420, "gpu": True,
           "material_mode": "coating", "rho_control": 0.05,
           "coating": {"body": body, "spec_scale": spec_scale, "ior": ior,
                       "roughness": roughness},
           "params": dict(PLATE),
           "renders": [{"mode": "hemi_view", "theta": -float(t)}
                       for t in sorted(TARGET)]}
    res = BR.run(cfg)
    return {int(round(-rec["theta"])): rec["panel"]["mean"]
            for rec in res["modes"].values()}, res


def score(got):
    """Worst relative residual across the seven measured angles."""
    return max(abs(got[t] - TARGET[t]) / TARGET[t] for t in TARGET)


def report(got):
    print("\n%-8s %10s %10s %9s" % ("theta", "target", "measured", "resid"))
    for t in sorted(TARGET):
        r = (got[t] - TARGET[t]) / TARGET[t]
        print("%-8d %9.4f%% %9.4f%% %+8.1f%%"
              % (t, TARGET[t] * 100, got[t] * 100, r * 100))
    w = score(got)
    print("\nworst residual: %.1f%%" % (w * 100))
    return w


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    os.makedirs(OUT, exist_ok=True)

    got, res = measure(BR.MUSOU_BODY, BR.MUSOU_SPEC_SCALE, BR.MUSOU_IOR,
                       tag="fit_paper")
    print("\n=== the analytic fit, as written in blender_render ===")
    worst = report(got)
    ctrl = [rec["control"]["mean"] for rec in res["modes"].values()]
    print("control plate: %.6f .. %.6f (nominal 0.05)" % (min(ctrl), max(ctrl)))
    best = (worst, BR.MUSOU_BODY, BR.MUSOU_SPEC_SCALE, BR.MUSOU_IOR, got)

    if argv and argv[0] == "sweep":
        print("\n=== sweeping around it ===", flush=True)
        for body, spec, ior in itertools.product(
                (0.0068, 0.00758, 0.0082),
                (0.050, 0.0605, 0.072, 0.085),
                (1.4, 1.5, 1.6)):
            g, _ = measure(body, spec, ior, samples=512,
                           tag="s_%d_%d_%d" % (body * 1e5, spec * 1e4,
                                               ior * 10))
            w = score(g)
            mark = ""
            if w < best[0]:
                best = (w, body, spec, ior, g)
                mark = "  <-- best"
            print("body %.5f  spec %.4f  ior %.1f  worst %5.1f%%%s"
                  % (body, spec, ior, w * 100, mark), flush=True)

    print("\n=== best ===")
    w, body, spec, ior, g = best
    report(g)
    print("\nMUSOU_BODY = %.5f\nMUSOU_SPEC_SCALE = %.4f\nMUSOU_IOR = %.1f"
          % (body, spec, ior))
    if w > 0.15:
        print("\nFIT NOT GOOD ENOUGH (%.0f%%) -- do not use downstream yet"
              % (w * 100))
    json.dump({"worst": w, "body": body, "spec_scale": spec, "ior": ior,
               "target": {str(k): v for k, v in TARGET.items()},
               "measured": {str(k): v for k, v in g.items()}},
              open(os.path.join(RESULTS, "fit_coating.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
