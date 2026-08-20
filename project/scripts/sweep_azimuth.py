"""
Phase 5: the axis this project never measured -- azimuth of incidence.

WHAT IS WRONG WITH EVERY NUMBER PUBLISHED SO FAR. `hemi_view` tilts the camera
in one plane, so theta was swept 0/+-20/+-40 and phi was silently held at zero.
The brief says the beam direction is unknown and effectively omnidirectional.
For a design with no preferred direction that does not matter. For an extruded
V-groove, or blades all laid the same way, it matters completely: the published
figure is not a property of the design, it is a property of which way the
sample happened to be turned.

A probe before writing this file, on all-parallel blades at theta 40:

    phi   0 deg   rho 0.002113
    phi  45 deg   rho 0.001752
    phi  90 deg   rho 0.003076      -- 1.76x across one design

That range is larger than most of the gaps this study has used to rank designs
against each other.

THE PRE-REGISTERED PREDICTION, by symmetry, before the render.

    cone 5.5, jittered      isotropic by construction   < 3 % across phi
    comb honeycomb          6-fold, period 60 deg        < 10 %
    blade, slotted grid     4-fold, period 90 deg        10-30 %
    blade, all parallel     2-fold                       ~1.8x, per the probe
    V-groove, extruded      2-fold, the extreme case     LARGEST of the five

And the consequence, which is the point of the sweep: the study scores designs
on the WORST case over theta. If phi moves a design by 1.8x, the honest score
is the worst over theta AND phi, and every directional design is currently
reported better than it is. The isotropic ones -- cone, and the honeycomb --
should be unaffected, which would mean the ranking's top is safe and its
middle is not.

IF THE PREDICTION FAILS in the direction of "the cone moves too", then the
sweep has found something wrong with the rotation itself rather than with the
designs, and nothing here is reportable until that is understood.

ANCHOR. phi = 0 for each design is the geometry already measured elsewhere:
the blade grid is `FL_bl050o115_flat_d00` minus its floor, the cone is
`B_CONE_p0550`. The cone at phi 0 must reproduce `sweep_conefloor.csv` exactly.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from sweep_floor import open_append, done_tags                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "azimuth")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_azimuth.csv"))

FACE, SAMPLES, RES = 60.0, 64, (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
PHIS = (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH, MARGIN = 50.0, 2.0
SEEDS = (23, 101, 102)

BLADE = dict(pitch=5.5, plate_t_top=0.05, plate_t_bot=0.05, tilt_deg=2.0,
             tilt_jitter=0.0, jitter=0.30, plate_over=1.15)
DESIGNS = [
    ("cone", "cone3d", dict(pitch=5.5, tip_radius=0.2, jitter=0.30,
                            radial_seg=24, height_seg=12, depth_jitter=0.0,
                            profile_power=1.0)),
    ("comb", "topo", dict(topology="comb", pitch=6.5, wall_top=0.08,
                          wall_bot=0.08, jitter=0.0)),
    ("blgrid", "topo", dict(topology="shingle", azimuth_mode="grid", **BLADE)),
    ("blpara", "topo", dict(topology="shingle", azimuth_mode="parallel",
                            **BLADE)),
    ("vgroove", "ridge", dict(pitch_mean=13.0, pitch_jitter=0.25,
                              tip_width=0.4, tip_round=True,
                              valley_round=0.4, arc_segments=24)),
]

FIELDS = ["tag", "family", "topology", "process", "feature", "seed",
          "diffuse_frac", "phi", "pitch", "depth", "theta", "rho", "control",
          "params_json"]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = [(n, fam, prm, phi, seed)
            for seed in SEEDS for n, fam, prm in DESIGNS for phi in PHIS]
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[AZIMUTH] %d designs x %d phi x %d seeds x %d materials = %d runs, "
          "%d done" % (len(DESIGNS), len(PHIS), len(SEEDS),
                       len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for name, fam, base, phi, seed in grid:
        tag = "AZ_%s_p%02d_s%02d" % (name, phi, seed)
        prm = dict(base, face_w=FACE, face_h=FACE, depth=DEPTH,
                   margin_depths=MARGIN, backing=2.0)
        prm["pitch_seed" if fam == "ridge" else "seed"] = seed
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
            cfg = {"tag": "%s_%s" % (tag, mname), "family": fam,
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True, "spec_roughness": 0.30, "phi_deg": phi,
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
                w.writerow({"tag": tag, "family": fam,
                            "topology": name, "process": "n/a",
                            "feature": "", "seed": seed,
                            "diffuse_frac": mname, "phi": phi,
                            "pitch": base.get("pitch",
                                              base.get("pitch_mean")),
                            "depth": DEPTH, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            if n % 15 == 0:
                print("[%3d/%3d] %-22s eta %4.0fs"
                      % (n, total, tag,
                         (time.time() - t0) / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
