"""
Phase 6: is the RANKING robust to the coating nobody measured?

THE CLAIM UNDER TEST, made repeatedly in this project and never checked:

    "Ratios between designs are robust -- every design on the page shares one
     coating, so a wrong coating moves them all together -- but the absolute
     percentages are not."

Every report carries a version of that sentence. It is the reason the study is
presented as usable despite two surface parameters being chosen rather than
measured. If it is false, the conclusions are contingent on a guess.

Diffuse fraction is already swept (0 / 0.76 / 1.0, worst case taken). Specular
roughness is NOT: every number in phases 2-5 was taken at 0.30, and phase 2
measured head-on brightness moving 332x across roughness 0.1 - 0.5. So the one
parameter with the largest known leverage has been held at a single value
throughout.

THE PRE-REGISTERED PREDICTION, before any render.

1. THE TOTAL-REFLECTANCE RANKING SURVIVES. Worst-theta rho_dh is set by how
   many times a ray bounces before it escapes, which is cavity geometry --
   aspect ratio, exposed area, whether the cell closes. Roughness changes where
   each bounce sends the ray, not how many there are. Predicted Spearman
   correlation against the roughness-0.30 order: > 0.9 at every roughness, and
   no change at all among the top three.

2. THE HEAD-ON RANKING MAY NOT. Head-on brightness is exactly a question about
   the angular distribution of a bounce, which is what roughness controls. This
   sweep measures total only, so it cannot settle that -- and saying so is part
   of the result.

3. ABSOLUTE VALUES MOVE A LOT. A smoother coating (0.10) concentrates the
   specular lobe; at grazing incidence more of it survives the cavity. Expect
   the whole field to shift by more than 2x between roughness 0.10 and 0.50,
   which is precisely why the percentages are not quotable.

If prediction 1 fails -- if designs reorder as roughness changes -- then the
comparisons in phases 2, 3 and 4 hold only at roughness 0.30, and every report
needs that caveat promoted from a footnote to the headline.

ANCHOR. Roughness 0.30 for each design is the value already in
`sweep_floor.csv` / `sweep_conefloor.csv`, so gate check 8 compares per seed.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
import geom_stack as ST                                            # noqa: E402
import geom3d as G3                                                # noqa: E402
import geom_topo as GT                                             # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from sweep_floor import open_append, done_tags                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "coatrobust")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_coatrobust.csv"))

FACE, SAMPLES, RES = 60.0, 64, (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
ROUGHS = (0.10, 0.20, 0.30, 0.40, 0.50)
ENVELOPE, MARGIN = 50.0, 2.0
SEEDS = (23, 101, 102)

COMB = dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0)
BLADE = dict(pitch=5.5, plate_t_top=0.05, plate_t_bot=0.05, tilt_deg=2.0,
             tilt_jitter=0.0, azimuth_mode="grid", jitter=0.30,
             plate_over=1.15)
CONE = dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=24,
            height_seg=12, depth_jitter=0.0, profile_power=1.0)
PYR = dict(pitch=2.0, tip_flat=0.1)


def designs():
    """The six the reports actually argue about, one per claim."""
    out = []
    for seed in SEEDS:
        common = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                      backing=2.0, seed=seed)

        def stack(name, top, tp, bot, bp, fd):
            out.append((name, "stack",
                        dict(common, top=top, top_depth=ENVELOPE - fd,
                             top_params=dict(tp), bot=bot, bot_depth=fd,
                             # margin_depth_ref exists only on FloorParams.
                             # Passing it to a comb bottom layer killed every
                             # cone/comb run -- 45 silent [FAIL] lines that the
                             # summary then showed as a missing row.
                             bot_params=(dict(bp, margin_depth_ref=ENVELOPE)
                                         if bot in ("pyramid", "wave", "gap")
                                         else dict(bp))),
                        seed))

        def single(name, fam, prm):
            out.append((name, fam, dict(common, depth=ENVELOPE, **prm), seed))

        single("CR_blade_flat", "topo", dict(topology="shingle", **BLADE))
        single("CR_cone_flat", "cone3d", CONE)
        single("CR_comb_flat", "topo", dict(topology="comb", **COMB))
        stack("CR_blade_pyr", "shingle", BLADE, "pyramid", PYR, 3.0)
        stack("CR_comb_pyr", "comb", COMB, "pyramid", PYR, 3.0)
        stack("CR_cone_comb", "cone", CONE, "comb", COMB, 25.0)
    return out


FIELDS = ["tag", "family", "topology", "process", "feature", "seed",
          "diffuse_frac", "roughness", "pitch", "depth", "theta", "rho",
          "control", "params_json"]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)
    grid = [(n, fam, prm, rg, seed)
            for n, fam, prm, seed in designs() for rg in ROUGHS]
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[COATROBUST] %d designs x %d roughness x %d seeds x %d materials "
          "= %d runs, %d done" % (6, len(ROUGHS), len(SEEDS),
                                  len(DIFFUSE_FRACS), total, len(seen)),
          flush=True)

    t0, n = time.time(), 0
    for name, fam, prm, rough, seed in grid:
        tag = "%s_r%02d_s%02d" % (name, rough * 100, seed)
        pitch = (prm.get("pitch")
                 or (prm.get("top_params") or {}).get("pitch") or 0.0)
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
                   "gpu": True, "spec_roughness": rough,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": rough},
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
                w.writerow({"tag": tag, "family": fam, "topology": name,
                            "process": "n/a", "feature": "", "seed": seed,
                            "diffuse_frac": mname, "roughness": rough,
                            "pitch": pitch, "depth": ENVELOPE,
                            "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            if n % 15 == 0:
                print("[%3d/%3d] %-24s eta %4.0fs"
                      % (n, total, tag,
                         (time.time() - t0) / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
