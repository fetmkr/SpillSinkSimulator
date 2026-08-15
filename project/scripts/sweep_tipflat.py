"""
Phase 4c: the flat spot on a pressed pyramid's apex. Does it explain everything?

THE OBSERVATION THAT PROMPTED THIS. `sweep_floorpitch.csv` swept floor pitch
1.0 / 1.5 / 2.0 / 3.0 mm and found it is not a lever -- 5.8 % across the whole
range -- but it is NOT monotonic, and the finest pitch was the WORST:

    honeycomb 6.5/0.08, theta-0:  1.0mm 0.03549   1.5mm 0.03355
                                  2.0mm 0.03355   3.0mm 0.03378 %

`tip_flat` was held at 0.1 mm throughout, so a finer pitch packs the same flat
spot more densely: the flat, viewer-facing fraction of the floor is
(tip_flat/pitch)^2, which is 1.00 / 0.44 / 0.25 / 0.11 % across those four.
That ordering matches the first three points exactly.

THE PRE-REGISTERED PREDICTION, quantitative, written before the render.
Phase 3 and 4 both say the same thing: what makes a floor work is that a
normal-incidence ray stops meeting a surface square-on. A flat apex is exactly
such a surface. So if the apex flat is the mechanism, then at fixed pitch 2.0:

    tip_flat   0.05    0.10    0.20  mm
    flat area  0.0625  0.25    1.00  %      = (tip_flat/pitch)^2
    predicted  theta-0 rises with flat area, roughly linearly, and the
    0.20 mm case should be clearly worst.

If instead the three are within a couple of percent, the apex flat is NOT the
mechanism, the pitch non-monotonicity has some other cause, and a press can be
given whatever apex it finds easy.

WHY IT MATTERS FOR MANUFACTURE. A sharper apex is a harder die and a shorter
die life. If 0.20 mm costs nothing optically, the floor gets cheaper; if it
costs a third of the benefit, the die has to hold 0.05 and that is a different
quotation.

ANCHOR. `tip_flat = 0.1` at pitch 2.0 is re-measured for both tubes, which is
the design `sweep_floor.csv` and `sweep_floorpitch.csv` already carry, so gate
check 8 has two shared designs and will fail if the scoring drifts.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import geom_stack as ST                                            # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from sweep_floor import (FACE, SAMPLES, RES, THETAS, DIFFUSE_FRACS,
                         ENVELOPE, MARGIN, SEEDS, TUBES, FIELDS,
                         open_append, done_tags, tube_feature, FLOOR_PROC)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "tipflat")
OUTCSV = os.path.join(RESULTS, "sweep_tipflat.csv")

FLOOR_PITCH = 2.0
FLOOR_DEPTH = 3.0
TIP_FLATS = (0.02, 0.05, 0.10, 0.20, 0.40)
TUBE_SET = ("p650f080", "bl050o115")


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = [("TF_%s_p20_t%03d_s%02d" % (t, tf * 100, s), t, tf, s)
            for s in SEEDS for t in TUBE_SET for tf in TIP_FLATS]
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[TIPFLAT] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for tag, tname, tflat, seed in grid:
        tk, tp = TUBES[tname]
        prm = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                   backing=2.0, seed=seed, top=tk,
                   top_depth=ENVELOPE - FLOOR_DEPTH, top_params=dict(tp),
                   bot="pyramid", bot_depth=FLOOR_DEPTH,
                   bot_params=dict(pitch=FLOOR_PITCH,
                                   margin_depth_ref=ENVELOPE,
                                   tip_flat=tflat))
        sp = ST.StackParams(**prm)
        tproc, tfeat = tube_feature(tk, tp)
        # the apex flat IS the pressed sheet's minimum feature once it is the
        # smaller of the two, which is the whole manufacturing question here
        fproc, _ = FLOOR_PROC["pyramid"]
        proc, feat = ((fproc, tflat) if tflat < tfeat else (tproc, tfeat))
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
                            "tube_wall": tfeat,
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
