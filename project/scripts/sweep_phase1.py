"""
Phase 1 re-measured on the current ruler, so all four phases compare.

    Blender --background --factory-startup --python scripts/sweep_phase1.py

WHY. Phase 1 (extruded 2D cross-sections: slats, troughs, V-grooves) was
measured with ONE coating model and an older form metric. Phases 2-4 score the
worst case over THREE coating models. So the phase 1 numbers still quoted in the
phase 2 report -- "best result 0.027 % head-on" -- cannot be placed next to a
phase 4 number, and that line was removed from the report rather than compared.
This sweep puts the phase 1 families back on today's footing: same five angles,
same three coatings, same three seeds, same 50 mm envelope, same margin.

ANCHOR. `B_CONE_p0550` is re-measured here with byte-identical parameters to its
row in `sweep_buildable.csv`, so gate check 8 has a design in common and will
fail loudly if this sweep's scoring drifts from the rest of the study.

PREDICTION, before the render. The V-groove should be competitive on total
reflectance -- a deep groove is a good trap -- and should lose form destruction
outright, because an extruded profile has no structure along its own axis and a
line parallel to the grooves comes back a line. That was phase 1's conclusion
and this sweep either confirms it on the new ruler or overturns it.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from sweep_floor import open_append, done_tags                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "phase1")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_phase1.csv"))

FACE, SAMPLES, RES = 60.0, 64, (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH, MARGIN = 50.0, 2.0
SEEDS = (23, 101, 102)

FIELDS = ["tag", "family", "topology", "process", "feature", "seed",
          "diffuse_frac", "pitch", "depth", "theta", "rho", "control",
          "params_json"]


def designs():
    out = []
    for seed in SEEDS:
        def ridge(name, pitch, tip, **kw):
            out.append(("P1_%s_s%02d" % (name, seed), "ridge", "vgroove",
                        "print", tip, pitch,
                        dict(face_w=FACE, face_h=FACE, depth=DEPTH,
                             backing=2.0, pitch_mean=pitch, pitch_jitter=0.25,
                             pitch_seed=seed, tip_width=tip, tip_round=True,
                             valley_round=0.4, arc_segments=24,
                             margin_depths=MARGIN, **kw)))
        # family 3: the best extruded design phase 1 produced
        ridge("groove_p13_t04", 13.0, 0.4)
        ridge("groove_p075_t04", 7.5, 0.4)
        ridge("groove_p13_t08", 13.0, 0.8)
        # the serrated flank that was supposed to copy butterfly hierarchy
        ridge("groove_serr_p20", 20.0, 0.4, micro_pitch=1.0, micro_depth=0.3)
        # family 2: open troughs, the design aimed straight at form
        out.append(("P1_trough_u_s%02d" % seed, "scatter", "trough",
                    "print", 1.0, 20.0,
                    dict(face_w=FACE, face_h=FACE, depth=DEPTH,
                         width_mean=20.0, width_jitter=0.25, width_seed=seed,
                         depth_ratio=1.5, shape="u", thickness=1.0,
                         margin_depths=MARGIN)))
        out.append(("P1_trough_vee_s%02d" % seed, "scatter", "trough",
                    "print", 1.0, 20.0,
                    dict(face_w=FACE, face_h=FACE, depth=DEPTH,
                         width_mean=20.0, width_jitter=0.25, width_seed=seed,
                         depth_ratio=1.5, shape="vee", thickness=1.0,
                         margin_depths=MARGIN)))
        # family 1: angled slats over a hidden chamber
        out.append(("P1_slat_s%02d" % seed, "slat", "slat",
                    "print", 1.0, 20.0,
                    dict(face_w=FACE, face_h=FACE, depth=DEPTH, slat_deg=45.0,
                         slat_len=28.0, pitch_mean=14.0, pitch_jitter=0.25,
                         pitch_seed=seed, thickness=1.0,
                         margin_depths=MARGIN)))
        # THE ANCHOR: identical params to sweep_buildable.csv's B_CONE_p0550
        out.append(("B_CONE_p0550_s%02d" % seed, "cone3d", "cone",
                    "mould", 0.4, 5.5,
                    dict(backing=2.0, depth=50.0, depth_jitter=0.0,
                         face_h=60.0, face_w=60.0, height_seg=12, jitter=0.3,
                         margin_depths=2.0, pitch=5.5, profile_power=1.0,
                         radial_seg=24, seed=seed, tip_radius=0.2)))
    return out


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[PHASE1] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)
    t0, n = time.time(), 0
    for tag, fam, topo, proc, feat, pitch, prm in grid:
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
                w.writerow({"tag": tag, "family": fam, "topology": topo,
                            "process": proc, "feature": feat,
                            "seed": prm.get("seed", prm.get("pitch_seed",
                                                            prm.get("width_seed"))),
                            "diffuse_frac": mname, "pitch": pitch,
                            "depth": DEPTH, "theta": rec["theta"],
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
