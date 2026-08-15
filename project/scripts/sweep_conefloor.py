"""
Phase 4d: does a shaped floor help a CONE? The mechanism says no.

WHY THIS IS THE SHARPEST TEST LEFT. Phases 3 and 4 converged on one claim:
a panel is bright head-on because a normal-incidence ray meets a surface
square-on at the bottom of the cavity, and shaping that surface fixes it.

    honeycomb 6.5/0.08 + pyramid 3 mm   0.16401 -> 0.03355 %   4.89x
    blade 0.05/o1.15   + pyramid 3 mm   0.20566 -> 0.05383 %   3.82x
    honeycomb + 3 mm AIR GAP            0.16401 -> 0.17040 %   0.96x  (nothing)

A cone array has no flat floor. The space between cones is already a V, and
`geom3d` closes it onto the backing slab at the valley, so a normal ray landing
between two cones meets sloped material, not a plate. If the mechanism above is
correct and complete, **the cone should gain little or nothing from a floor** --
it already has the thing the floor provides.

THE PRE-REGISTERED PREDICTION, quantitative, before any render:

    cone 5.5 mm, 50 mm, flat backing   -> baseline
    cone 47 mm + pyramid 3 mm          -> better by LESS THAN 1.3x
    cone 47 mm + 3 mm gap              -> no change, as for the honeycomb

If instead the cone gains 3-5x like the honeycomb did, then the mechanism is
NOT "the ray meets a flat surface" -- it is something else that happens to
correlate, and both phase 3's conclusion and phase 4's recommendation need
re-reading. That is the outcome worth having.

A SECOND THING THIS SETTLES. Shortening the cone from 50 to 47 mm costs total
reflectance: phase 3 measured the cone losing ground fast as its depth shrinks
(0.2170 % at 50, 0.2380 % at 37.5). So even a small head-on gain may be paid
for on the other axis, and the worst-theta column here says by how much.

ANCHOR. `B_CONE_p0550` at the full 50 mm with a flat backing is re-measured
here with parameters byte-identical to its row in `sweep_buildable.csv` and
`sweep_phase1.csv`, so gate check 8 has a design shared with two other sweeps.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import geom_stack as ST                                            # noqa: E402
import geom3d as G3                                                # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from sweep_floor import (FACE, SAMPLES, RES, THETAS, DIFFUSE_FRACS,
                         ENVELOPE, MARGIN, SEEDS, FIELDS, open_append,
                         done_tags, FLOOR_PROC)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "conefloor")
OUTCSV = os.path.join(RESULTS, "sweep_conefloor.csv")

# byte-identical to B_CONE_p0550 in sweep_buildable.csv
CONE = dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=24,
            height_seg=12, depth_jitter=0.0, profile_power=1.0)
FLOOR_DEPTH = 3.0
FLOOR_PITCH = 2.0


def designs():
    out = []
    for seed in SEEDS:
        out.append(("B_CONE_p0550_s%02d" % seed, "flat", 0.0, seed))
        for kind in ("pyramid", "gap", "wave"):
            out.append(("CF_cone_%s_d30_s%02d" % (kind, seed),
                        kind, FLOOR_DEPTH, seed))
    return out


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[CONEFLOOR] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for tag, floor, fd, seed in grid:
        if floor == "flat":
            prm = dict(CONE, face_w=FACE, face_h=FACE, depth=ENVELOPE,
                       margin_depths=MARGIN, backing=2.0, seed=seed)
            family, aspect = "cone3d", ENVELOPE / CONE["pitch"]
            est = G3.Cone3DParams(**prm).tip_fraction()
            proc, feat = "mould", 2 * CONE["tip_radius"]
        else:
            bp = dict(margin_depth_ref=ENVELOPE)
            if floor != "gap":
                bp.update(pitch=FLOOR_PITCH, tip_flat=0.1)
            prm = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                       backing=2.0, seed=seed, top="cone",
                       top_depth=ENVELOPE - fd, top_params=dict(CONE),
                       bot=floor, bot_depth=fd, bot_params=bp)
            sp = ST.StackParams(**prm)
            family, aspect, est = "stack", sp.aspect(), sp.exposed_fraction_est()
            fproc, ffeat = FLOOR_PROC[floor]
            # the cone tip is 0.4 mm across; a pressed apex flat of 0.1 mm is
            # finer, so the press becomes the binding process
            proc, feat = ((fproc, ffeat) if ffeat < 2 * CONE["tip_radius"]
                          else ("mould", 2 * CONE["tip_radius"]))
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
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
            try:
                res = BR.run(cfg)
            except Exception as e:
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            pj = json.dumps(prm, sort_keys=True, default=str)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "family": "floor",
                            "topology": "cone/%s" % floor, "process": proc,
                            "feature": feat, "seed": seed,
                            "diffuse_frac": mname, "tube": "cone_p550",
                            "tube_kind": "cone", "tube_pitch": CONE["pitch"],
                            "tube_wall": 2 * CONE["tip_radius"],
                            "tube_depth": ENVELOPE - fd, "floor": floor,
                            "floor_depth": fd,
                            "floor_pitch": (0.0 if floor in ("flat", "gap")
                                            else FLOOR_PITCH),
                            "depth": ENVELOPE, "aspect": aspect,
                            "exposed_est": est, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            if n % 9 == 0:
                print("[%3d/%3d] %-26s eta %4.0fs"
                      % (n, total, tag,
                         (time.time() - t0) / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
