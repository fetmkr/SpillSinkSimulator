"""
Phase 4e: the neighbourhood of the design that currently wins all three axes.

WHERE IT STANDS. `FL_bl050o115_pyramid_d30` -- 0.05 mm blades on a 5.5 mm
slotted grid, 47 mm deep, over a 3 mm pressed pyramid floor -- leads the study:

    total (worst over +-40)   0.1861 %     best of anything buildable
    form destruction          3.96x        second only to the cone's 4.11x
    head-on brightness        0.092        third, behind cone 0.068 / 0.054

Its three free parameters were never searched at this depth WITH a floor. The
pitch came from phase 2 at 30 mm, the 2 deg tilt from a phase 2 sweep whose
clamp bug voided 450 rows, and the grid azimuth beat "parallel" by 33 % but was
only ever compared against two alternatives.

THE PRE-REGISTERED PREDICTION, before any render.

1. PITCH DOMINATES, AND 5.5 IS PROBABLY NOT THE OPTIMUM. Two effects pull
   opposite ways. Aspect ratio 50/pitch says finer is darker: 12.5 at 4.0 mm,
   9.1 at 5.5, 7.1 at 7.0. Exposed blade edge ~ t/pitch says finer is brighter:
   1.25 % at 4.0 mm, 0.91 % at 5.5, 0.71 % at 7.0. So worst-theta should have
   an interior optimum. I expect it BELOW 5.5 -- nearer 4.5 -- because the
   aspect term has been the stronger one in every family so far.

2. TILT IS A MINOR AXIS, worth under 5 %. Phase 2's tilt result was voided by a
   clamp bug and never redone; this re-tests it at 0 / 2 / 5 / 10 deg. If tilt
   turns out to be worth more than 10 % the phase 2 conclusion was wrong for a
   second reason and that matters more than the ranking.

3. GRID ~= RANDOM > PARALLEL. Phase 2 measured 0.2065 / 0.2067 / 0.2819. The
   gap should survive at 50 mm with a floor, because it is about whether
   neighbouring blades shadow each other, which the floor does not touch.

4. THE FLOOR'S BENEFIT SHOULD BE INDEPENDENT OF ALL THREE. Phase 4 says the
   floor works on whatever the tube leaves flat at the bottom, so its ~3.8x on
   normal-incidence reflectance should hold across the whole neighbourhood. If
   it varies with pitch, the floor and the tube are coupled and the two cannot
   be specified separately.

ANCHOR. pitch 5.5, tilt 2, grid is `FL_bl050o115_pyramid_d30`, already in
`sweep_floor.csv`; gate check 8 compares it per seed.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
import geom_stack as ST                                            # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from sweep_floor import (FACE, SAMPLES, RES, THETAS, DIFFUSE_FRACS,
                         ENVELOPE, MARGIN, SEEDS, FIELDS, open_append,
                         done_tags, FLOOR_PROC)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "bladehood")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_bladehood.csv"))

THICK = 0.05
FLOOR_DEPTH = 3.0
FLOOR_PITCH = 2.0
PITCHES = (4.0, 4.75, 5.5, 7.0)
TILTS = (0.0, 2.0, 5.0, 10.0)
AZIMUTHS = ("grid", "random", "parallel")


def blade(pitch, tilt, az):
    return dict(pitch=pitch, plate_t_top=THICK, plate_t_bot=THICK,
                tilt_deg=tilt, tilt_jitter=0.0, azimuth_mode=az,
                jitter=0.30, plate_over=1.15)


def designs():
    """One axis at a time around the incumbent, not a full grid: a 4x4x3 cube
    is 144 designs and most of its corners answer nothing. Each arm holds the
    other two at the incumbent's value, so every point is comparable to it."""
    out = []
    for seed in SEEDS:
        for p in PITCHES:
            out.append(("BH_p%03d_t02_grid_s%02d" % (p * 10, seed),
                        p, 2.0, "grid", seed))
        for t in TILTS:
            if t == 2.0:
                continue
            out.append(("BH_p055_t%02d_grid_s%02d" % (t, seed),
                        5.5, t, "grid", seed))
        for a in AZIMUTHS:
            if a == "grid":
                continue
            out.append(("BH_p055_t02_%s_s%02d" % (a, seed),
                        5.5, 2.0, a, seed))
    return out


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[BLADEHOOD] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for tag, pitch, tilt, az, seed in grid:
        tp = blade(pitch, tilt, az)
        prm = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                   backing=2.0, seed=seed, top="shingle",
                   top_depth=ENVELOPE - FLOOR_DEPTH, top_params=dict(tp),
                   bot="pyramid", bot_depth=FLOOR_DEPTH,
                   bot_params=dict(pitch=FLOOR_PITCH,
                                   margin_depth_ref=ENVELOPE, tip_flat=0.1))
        sp = ST.StackParams(**prm)
        fproc, ffeat = FLOOR_PROC["pyramid"]
        proc, feat = ((fproc, ffeat) if ffeat < THICK
                      else ("sheet, grid", THICK))
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
            cfg = {"tag": "%s_%s" % (tag, mname), "family": "stack",
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
            pj = json.dumps(prm, sort_keys=True, default=str)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "family": "floor",
                            "topology": "shingle/pyramid", "process": proc,
                            "feature": feat, "seed": seed,
                            "diffuse_frac": mname,
                            "tube": "bl050_p%03d_t%02d_%s" % (pitch * 10,
                                                              tilt, az),
                            "tube_kind": "shingle", "tube_pitch": pitch,
                            "tube_wall": THICK,
                            "tube_depth": ENVELOPE - FLOOR_DEPTH,
                            "floor": "pyramid", "floor_depth": FLOOR_DEPTH,
                            "floor_pitch": FLOOR_PITCH, "depth": ENVELOPE,
                            "aspect": sp.aspect(),
                            "exposed_est": sp.exposed_fraction_est(),
                            "theta": rec["theta"], "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            if n % 12 == 0:
                print("[%3d/%3d] %-28s eta %4.0fs"
                      % (n, total, tag,
                         (time.time() - t0) / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
