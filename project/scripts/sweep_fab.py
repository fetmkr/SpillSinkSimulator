"""
The two questions that decide how the blade array is actually built.

    Blender --background --factory-startup --python scripts/sweep_fab.py

Both are fabrication questions, not optimisation. The design is already chosen
(pitch 5.5, blade 0.1 mm, depth 50, tilt 2 deg, random azimuth, 0.2147%). What
is not known is whether it survives being made.

**1. Tilt tolerance.** Tilt 2 deg is the optimum and the curve around it is not
flat: at 0.05 mm blades the same design reads 0.2300% at tilt 0, 0.2141% at 1,
0.2056% at 2, 0.2064% at 3. That is a 12% swing across three degrees. A blade
slotted into a base plate and spot-welded will not land at exactly 2 deg, and
nobody has asked what +/-1 or +/-2 degrees of assembly scatter costs. Swept two
ways, because they are different things:

    tilt_deg        the whole array leaning wrong -- a systematic setup error
    tilt_jitter     each blade landing somewhere else -- assembly scatter

**2. Egg-crate.** Random azimuth beats all-parallel by 31% (0.2147 vs 0.2840),
and random costs nothing extra because the slot angles are just a drawing. But
if the blades are restricted to 0 and 90 degrees only, the array can be
**slotted together like an egg crate with no base plate and no welding** --
notches cut halfway through two sets of strips, pushed together. That is a
different order of manufacturing cost.

So: does "grid" recover the random gain, or does it sit with parallel? Nobody
has measured it. `geom_topo.azimuth_mode` was added for this and does nothing
else.

Scoring identical to sweep_buildable.py: worst rho_dh over theta 0/+-20/+-40,
then worst over diffuse fraction 0.0/0.76/1.0. Three seeds, because the
realisation spread is ~3.5% and several of these differences will be smaller
than that -- a single seed could not tell them apart.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import geom_topo as GT                                             # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "fab")
OUTCSV = os.path.join(RESULTS, "sweep_fab.csv")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH = 50.0
MARGIN = 2.0
BLADE = 0.1                    # the thickness actually specified in SAMPLES.md
SEEDS = (23, 101, 102)

FIELDS = ["tag", "question", "pitch", "tilt_deg", "tilt_jitter",
          "azimuth_mode", "seed", "diffuse_frac", "theta", "rho", "control",
          "params_json"]


def designs():
    out = []
    for seed in SEEDS:
        base = dict(topology="shingle", face_w=FACE, face_h=FACE, depth=DEPTH,
                    margin_depths=MARGIN, backing=2.0, jitter=0.30, seed=seed,
                    plate_over=1.15, plate_t_top=BLADE, plate_t_bot=0.9)

        # 1a. systematic tilt error -- the whole array leaning wrong
        for tilt in (0.0, 1.0, 2.0, 3.0, 4.0, 6.0):
            out.append(("tilt", dict(base, pitch=5.5, tilt_deg=tilt,
                                     tilt_jitter=0.0,
                                     azimuth_mode="random",
                                     azimuth_jitter=180.0)))
        # 1b. assembly scatter -- each blade landing somewhere else
        for tj in (0.0, 1.0, 2.0, 4.0):
            out.append(("scatter", dict(base, pitch=5.5, tilt_deg=2.0,
                                        tilt_jitter=tj,
                                        azimuth_mode="random",
                                        azimuth_jitter=180.0)))
        # 2. how the blades are oriented in plan, which is the assembly method
        for pitch in (5.5, 7.5):
            for mode in ("random", "grid", "parallel"):
                out.append(("azimuth", dict(base, pitch=pitch, tilt_deg=2.0,
                                            tilt_jitter=0.0,
                                            azimuth_mode=mode,
                                            azimuth_jitter=180.0)))
    return out


def tag_for(q, p):
    return "FAB_%s_p%04d_t%02d_j%02d_%s_s%02d" % (
        q[:4].upper(), p["pitch"] * 100, p["tilt_deg"], p["tilt_jitter"],
        p["azimuth_mode"][:4], p["seed"])


def done_tags(path):
    if not os.path.exists(path):
        return set()
    return {(r["tag"], r["diffuse_frac"]) for r in csv.DictReader(open(path))}


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    new = not os.path.exists(OUTCSV)
    fh = open(OUTCSV, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()
        fh.flush()

    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[FAB] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for q, prm in grid:
        tag = tag_for(q, prm)
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": "topo",
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
            try:
                res = BR.run(cfg)
            except Exception as e:
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            pj = json.dumps(prm, sort_keys=True)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "question": q, "pitch": prm["pitch"],
                            "tilt_deg": prm["tilt_deg"],
                            "tilt_jitter": prm["tilt_jitter"],
                            "azimuth_mode": prm["azimuth_mode"],
                            "seed": prm["seed"], "diffuse_frac": mname,
                            "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            el = time.time() - t0
            print("[%3d/%3d] %-34s %-5s eta %4.0fs"
                  % (n, total, tag, mname, el / max(n, 1) * (total - n)),
                  flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
