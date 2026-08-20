"""
The blade array as it would actually be cut from sheet: CONSTANT thickness.

    Blender --background --factory-startup --python scripts/sweep_blade.py

WHY THIS RE-RUN EXISTS. `SAMPLES.md` told a supplier to laser-cut blades from
0.1 mm sheet. Every number backing that came from a design whose params are:

    plate_t_top 0.1     plate_t_bot 0.9

-- a WEDGE, 0.1 mm at the mouth thickening to 0.9 mm at the root, nine times
thicker. That is not sheet metal. It is what a printed or moulded part looks
like, and `geom_topo`'s shingle builder defaults to it because the taper is the
self-supporting direction for FDM. Nobody noticed the default was still there
after the family was reclassified as a sheet-metal part.

So every figure quoted for the blade array is for a part nobody can cut, and
the re-run has to answer three things at once:

    1. what a genuinely constant-thickness blade reads
    2. what the taper was buying, by keeping the wedge in as a reference
    3. whether the fabrication answers from sweep_fab still hold -- they were
       all measured on the wedge too

**azimuth_mode is the one that decides cost.** Random orientation beats
all-parallel by 31% and costs nothing extra, because the slot angles are just a
drawing. But restricting blades to 0 and 90 degrees lets two sets of notched
strips be pushed together like an egg crate -- no base plate, no welding. If
"grid" keeps most of the random gain, the part gets much cheaper.

Three seeds, because the geometry-realisation spread is ~3.5% and several of
these differences will be smaller than that.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import done_tags, shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "blade")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_blade.csv"))

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH = 50.0
MARGIN = 2.0
SEEDS = (23, 101, 102)

FIELDS = ["tag", "profile", "thickness", "pitch", "tilt_deg", "azimuth_mode",
          "seed", "diffuse_frac", "theta", "rho", "control", "params_json"]


def designs():
    out = []
    for seed in SEEDS:
        base = dict(topology="shingle", face_w=FACE, face_h=FACE, depth=DEPTH,
                    margin_depths=MARGIN, backing=2.0, jitter=0.30, seed=seed,
                    plate_over=1.15, tilt_jitter=0.0, azimuth_jitter=180.0)

        # constant thickness -- what sheet metal actually gives
        for t in (0.05, 0.1, 0.2):
            for pitch in (5.5, 7.5):
                for tilt in (2.0, 6.0):
                    for mode in ("random", "grid"):
                        out.append(("flat", dict(
                            base, pitch=pitch, tilt_deg=tilt,
                            plate_t_top=t, plate_t_bot=t,
                            azimuth_mode=mode)))
        # the wedge that every previous blade number was measured on, kept as
        # the reference so the difference is attributable rather than inferred
        for pitch in (5.5, 7.5):
            for tilt in (2.0, 6.0):
                out.append(("wedge", dict(
                    base, pitch=pitch, tilt_deg=tilt,
                    plate_t_top=0.1, plate_t_bot=0.9,
                    azimuth_mode="random")))
        # all-parallel, constant thickness -- the cheap louvre, for the gap
        for pitch in (5.5,):
            out.append(("flat", dict(base, pitch=pitch, tilt_deg=2.0,
                                     plate_t_top=0.1, plate_t_bot=0.1,
                                     azimuth_mode="parallel")))
    return out


def tag_for(prof, p):
    return "BL_%s_t%03d_p%04d_a%02d_%s_s%02d" % (
        prof[:4].upper(), p["plate_t_top"] * 1000, p["pitch"] * 100,
        p["tilt_deg"], p["azimuth_mode"][:4], p["seed"])


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
    print("[BLADE] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for prof, prm in grid:
        tag = tag_for(prof, prm)
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            # another shard is measuring this design; NSHARD unset makes
            # take() always true, so an unsharded run is unchanged
            if not take(tag):
                continue
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
                w.writerow({"tag": tag, "profile": prof,
                            "thickness": prm["plate_t_top"],
                            "pitch": prm["pitch"], "tilt_deg": prm["tilt_deg"],
                            "azimuth_mode": prm["azimuth_mode"],
                            "seed": prm["seed"], "diffuse_frac": mname,
                            "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            el = time.time() - t0
            if n % 15 == 0:
                print("[%3d/%3d] %-36s eta %4.0fs"
                      % (n, total, tag, el / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
