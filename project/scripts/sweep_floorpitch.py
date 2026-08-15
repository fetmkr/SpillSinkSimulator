"""
Phase 4b: floor feature pitch. Queued for the watchdog, run without Claude.

Phase 4 measured one floor pitch, 2.0 mm, and found a pressed pyramid sheet
takes a bought honeycomb from 0.164 % to 0.034 % at normal incidence. Nobody
asked whether 2.0 was the right pitch -- it was picked because it puts roughly
3x3 features in a 6.5 mm cell.

PREDICTION, written before the render. Finer is better down to the point where
the pyramid facet stops being large compared to the ray bundle, so 1.0 and 1.5
should beat 2.0, and 3.0 should be worse. If instead pitch barely matters, the
mechanism is "any non-normal facet will do" and the floor should be specified
at whatever pitch is cheapest to press, not the finest.

Anchored: FL_p650f080_pyramid_d30 at pitch 2.0 is re-measured here so gate
check 8 has a design in common with sweep_floor.csv.
"""
import sys, os, csv, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR
import geom_stack as ST
from cone3d_sweep import COAT
from sweep_floor import (FACE, SAMPLES, RES, THETAS, DIFFUSE_FRACS, ENVELOPE,
                         MARGIN, SEEDS, TUBES, FIELDS, open_append, done_tags,
                         tube_feature, FLOOR_PROC)

RESULTS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "results")
RENDERS = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "renders", "floorpitch")
OUTCSV = os.path.join(RESULTS, "sweep_floorpitch.csv")
PITCHES = (1.0, 1.5, 2.0, 3.0)
TUBE_SET = ("p650f080", "bl050o115")


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = []
    for seed in SEEDS:
        for tname in TUBE_SET:
            tk, tp = TUBES[tname]
            for fp in PITCHES:
                grid.append(("FP_%s_pyr_p%02d_s%02d" % (tname, fp * 10, seed),
                             tname, tk, tp, fp, seed))
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[FLOORPITCH] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)
    t0, n = time.time(), 0
    for tag, tname, tk, tp, fp, seed in grid:
        prm = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                   backing=2.0, seed=seed, top=tk, top_depth=ENVELOPE - 3.0,
                   top_params=dict(tp), bot="pyramid", bot_depth=3.0,
                   bot_params=dict(pitch=fp, margin_depth_ref=ENVELOPE,
                                   tip_flat=0.1))
        sp = ST.StackParams(**prm)
        tproc, tfeat = tube_feature(tk, tp)
        proc, feat = (FLOOR_PROC["pyramid"] if FLOOR_PROC["pyramid"][1] < tfeat
                      else (tproc, tfeat))
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
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
                            "topology": "%s/pyramid" % tk, "process": proc,
                            "feature": feat, "seed": seed,
                            "diffuse_frac": mname, "tube": tname,
                            "tube_kind": tk, "tube_pitch": tp["pitch"],
                            "tube_wall": tfeat, "tube_depth": ENVELOPE - 3.0,
                            "floor": "pyramid", "floor_depth": 3.0,
                            "floor_pitch": fp, "depth": ENVELOPE,
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
