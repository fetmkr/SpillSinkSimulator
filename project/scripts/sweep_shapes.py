"""
Overnight shape search: sweep the cavity profile under BOTH material models.

    Blender --background --factory-startup --python scripts/sweep_shapes.py

Why both materials. The old flat-rho glossy and the new Fresnel coating
disagree by up to 41x on the same cone, and neither is validated where it
matters -- the coating fit constrains only a flat plate, while every cavity
number depends on multi-bounce behaviour that nothing constrains. Until a
printed coupon settles it, optimising hard against either one is a bet on which
is right. So every design is scored under both, and the ones worth building are
the ones that are good under BOTH. A design that only wins under one model is a
gamble; a design that wins under both is robust to the thing we do not know.

Budget, measured not guessed (scratchpad/speedtest.py):

    face 60 mm    within 1.2% of face 100 mm, and smaller tiles do NOT run
                  faster -- render time is samples x pixels, not triangles
    64 spp        within 1% of 512 spp, 3.4x faster
    480x220       within 0.5% of 900x420
    margin 6.5    NOT reducible: margin 1.0 moves head-on by -15%, and the
                  reason is not yet understood, so it stays

Geometry knobs are the two continuous profile parameters added to geom3d:
power (0.15 tube ... 1.0 cone ... 2.0 needle) and bulge (barrel/undercut),
crossed with pitch and depth. Depth is capped at 50 mm and the base at 2 mm.

Writes results/sweep_shapes.csv incrementally, one row per design per material,
so the run can be stopped and resumed without losing work.
"""

import sys
import os
import csv
import time
import itertools

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import geom3d as G3                                                # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "shapes")
OUTCSV = os.path.join(RESULTS, "sweep_shapes.csv")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)

# height_seg 12, not 3. At hseg=3 cavity_radius is sampled at four rings and
# linearly interpolated, and the answer at power 0.15 moved 50.6x between
# hseg 3 and 12 -- the first version of this sweep was measuring tessellation,
# not geometry. Powers below 0.5 are fenced off for the same reason: at 0.25
# the result is still not converged at hseg 48, and not even monotone.
HEIGHT_SEG = 12
SPEC_ROUGHNESS = 0.30           # pinned: it moves cavity rho_dh by 32%

POWERS = (0.50, 0.75, 1.00, 1.50, 2.00)
BULGES = (0.00, 0.35)           # monotone widening
LIPS = (0.00, 0.35)             # localised overhang -- a real undercut
PITCHES = (3.75, 5.50, 7.50, 11.00)
DEPTHS = (20.0, 30.0, 40.0, 50.0)

# The material axis is the DIFFUSE FRACTION, at fixed measured flat-plate
# rho_dh(0). It is the dominant unmeasured parameter: holding rho fixed and
# swinging diffuse-vs-specular reproduces the whole 2x-41x spread between
# designs, while the Fresnel term alone contributes only 1.2-1.5x. Scoring
# every design at both extremes and at the nominal fit means the answer does
# not depend on a split that nothing has measured.
DIFFUSE_FRACS = (0.0, 0.76, 1.0)

FIELDS = ["tag", "diffuse_frac", "power", "bulge", "lip", "pitch", "depth",
          "aspect", "seal_frac", "theta", "rho", "control"]


def done_tags(path):
    if not os.path.exists(path):
        return set()
    seen = set()
    for r in csv.DictReader(open(path)):
        seen.add((r["tag"], r["diffuse_frac"]))
    return seen


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    new = not os.path.exists(OUTCSV)
    fh = open(OUTCSV, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()
        fh.flush()

    grid = list(itertools.product(POWERS, BULGES, LIPS, PITCHES, DEPTHS))
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[SWEEP] %d designs x %d diffuse fractions = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for power, bulge, lip, pitch, depth in grid:
        tag = "P%03d_B%02d_L%02d_p%04d_d%02d" % (power * 100, bulge * 100,
                                                 lip * 100, pitch * 100, depth)
        seal = G3.seal_fraction(power, bulge, lip, pitch)
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": "cone3d",
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True,
                   "material_mode": "coating",
                   "spec_roughness": SPEC_ROUGHNESS,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": SPEC_ROUGHNESS},
                   "params": dict(face_w=FACE, face_h=FACE, depth=depth,
                                  pitch=pitch, tip_radius=0.2, jitter=0.30,
                                  radial_seg=24, height_seg=HEIGHT_SEG,
                                  margin_depths=6.5, backing=2.0,
                                  depth_jitter=0.0, profile_power=power,
                                  profile_bulge=bulge, profile_lip=lip),
                   "renders": [{"mode": "hemi_view", "theta": t}
                               for t in THETAS]}
            cfg.update({k: v for k, v in COAT.items()
                        if k not in ("spec_roughness",)})
            cfg["material_mode"] = "coating"
            try:
                res = BR.run(cfg)
            except Exception as e:                        # keep the run alive
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "diffuse_frac": mname, "power": power,
                            "bulge": bulge, "lip": lip, "pitch": pitch,
                            "depth": depth, "aspect": depth / pitch,
                            "seal_frac": seal, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"]})
            fh.flush()
            el = time.time() - t0
            if n % 20 == 0:
                print("[%4d/%4d] %s %-7s  t+%5.0fs  eta %5.0fs"
                      % (n, total, tag, mname, el, el / n * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
