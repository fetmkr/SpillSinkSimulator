"""
Minimum feature size as an EXPLICIT matched axis, across every topology.

    Blender --background --factory-startup --python scripts/sweep_feature.py

WHY THIS EXISTS. The 2026-08-12 ranking was wrong, and wrong in a way this
project had already documented catching once. Every design in the top 86 used a
0.05 mm plate edge while the cone reference used a 0.4 mm tip -- an 8x
difference in minimum feature, inside families whose reflectance is dominated by
the exposed feature. Held to a common 0.4 mm floor the conclusion INVERTS:

    cone      0.2580 %      <- the incumbent wins
    nested    0.2669 %
    shingle   0.2690 %      <- the reported "winner", 4.3% behind
    square    0.2736 %   mixed 0.2796   reentrant 0.2815
    honeycomb 0.2863 %   triangle 0.3286   truss 0.4729

Seven of nine families inside 1.11x. And the same shingle moved 1.35x on edge
thickness alone (0.02 mm -> 0.1999 %, 0.40 mm -> 0.2690 %), which is more than
the 1.41x the report claimed over the cone. **The ranking was ranking feature
size.** CONTEXT.md:503 records the identical error being caught in the "fair
fight" and fixed by tip-matching; this is that error one level down.

So feature size stops being an incidental parameter and becomes the abscissa.

WHAT "MINIMUM FEATURE" MEANS PER FAMILY. It is the narrowest solid the printer
must lay down, which is a different parameter in each family and is exactly why
the confound was invisible:

    shingle     plate_t_top      the knife edge at the mouth
    honeycomb   wall_top         cell wall thickness at the mouth
    cell        wall_top         same
    cone        2 x tip_radius   tip diameter
    truss       2 x strut_r      strut diameter

FEATURES: 0.2 / 0.3 / 0.4 mm -- the range the user states is actually
manufacturable. 0.4 mm is one standard nozzle; 0.2-0.3 needs a fine nozzle and
is the honest lower bound. Values below 0.2 are deliberately NOT swept here:
they produced the wrong headline once already, and a number that cannot be built
does not belong on the axis a recommendation is read off.

Each family is re-optimised AT EACH FEATURE SIZE over its own geometry knobs,
rather than being handed one configuration and rescaled. A family whose optimum
pitch or depth moves with feature size would otherwise be penalised for it.

Scoring is unchanged and deliberately identical to sweep_topo.py: worst rho_dh
over theta 0/+-20/+-40, then worst over diffuse fractions 0.0/0.76/1.0.

Stage 2 -- repeat seeds for error bars on the per-family optima -- is a separate
run; see SEEDS below. The single-seed stage 1 grid CANNOT support a ranking
claim on its own, because the measured geometry-realisation spread is ~3.5%,
which is larger than most of the gaps this grid will produce. That is the point
of running it: to show the collapse, not to pick a winner.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import geom_topo as GT                                             # noqa: E402
import geom_cell as GC                                             # noqa: E402
import geom3d as G3                                                # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "feature")
OUTCSV = os.path.join(RESULTS, "sweep_feature.csv")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
SPEC_ROUGHNESS = 0.30
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
MARGIN_DEPTHS = 6.5

FEATURES = (0.2, 0.3, 0.4)
SEEDS = (23,)          # stage 1. Stage 2 re-runs the winners over many seeds.

FIELDS = ["tag", "family", "topology", "feature", "seed", "diffuse_frac",
          "pitch", "depth", "aspect", "exposed_est", "theta", "rho", "control",
          "params_json"]


def designs():
    out = []
    for f in FEATURES:
        for seed in SEEDS:
            base = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN_DEPTHS,
                        backing=2.0, seed=seed)

            def topo(topology, **kw):
                p = dict(base, topology=topology, jitter=0.30)
                p.update(kw)
                out.append(("topo", topology, f, seed, p))

            def cell(variant, **kw):
                p = dict(base, variant=variant)
                p.update(kw)
                out.append(("cell", "c_" + variant, f, seed, p))

            # --- shingle: knife edge = f -------------------------------------
            # tilt spans both sides of every crossing seen so far (2 / 6 / 12)
            for pitch in (3.75, 5.5, 7.5):
                for depth in (30.0, 50.0, 80.0):
                    for tilt in (2.0, 6.0, 12.0):
                        topo("shingle", pitch=pitch, depth=depth,
                             tilt_deg=tilt, plate_over=1.15,
                             plate_t_top=f, plate_t_bot=max(0.9, 2.0 * f),
                             tilt_jitter=0.0, azimuth_jitter=180.0)

            # --- honeycomb: straight wall, thickness = f ---------------------
            # straight (wall_bot = wall_top) beat tapered at every thickness
            for pitch in (3.75, 5.5, 7.5, 11.0):
                for depth in (30.0, 50.0, 80.0):
                    topo("honeycomb", pitch=pitch, depth=depth,
                         wall_top=f, wall_bot=f)

            # --- cone: tip DIAMETER = f, so tip_radius = f/2 -----------------
            # this is the parameter the fair fight already showed is decisive
            for pitch in (3.75, 5.5, 7.5):
                for depth in (30.0, 50.0, 80.0):
                    out.append(("cone3d", "cone", f, seed,
                                dict(face_w=FACE, face_h=FACE, depth=depth,
                                     pitch=pitch, tip_radius=f / 2.0,
                                     jitter=0.30, radial_seg=24, height_seg=12,
                                     margin_depths=MARGIN_DEPTHS, backing=2.0,
                                     depth_jitter=0.0, profile_power=1.0,
                                     seed=seed)))

            # --- geom_cell variants ------------------------------------------
            for variant in ("square", "triangle", "mixed", "reentrant"):
                for pitch in (5.5, 7.5):
                    for depth in (30.0, 50.0):
                        cell(variant, pitch=pitch, depth=depth,
                             wall_top=f, wall_bot=f)
            for depth in (30.0, 50.0):
                cell("nested", pitch=11.0, depth=depth,
                     wall_top=f, wall_bot=f)

            # --- truss: strut DIAMETER = f -----------------------------------
            # included for completeness only. It is 1.8x behind and its failure
            # is structural: struts stand at near-grazing incidence and it
            # swings 4.6x between the two material extremes.
            for pitch in (5.5, 7.5):
                topo("truss", pitch=pitch, depth=30.0, layers=3,
                     strut_r=f / 2.0, links=2, strut_seg=4)
    return out


def tag_for(family, topology, feat, seed, prm):
    if family == "cone3d":
        return "F%03d_CONE_p%04d_d%03d_s%02d" % (
            feat * 1000, prm["pitch"] * 100, prm["depth"], seed)
    if family == "cell":
        return "F%03d_CELL%s_p%04d_d%03d_s%02d" % (
            feat * 1000, prm["variant"][:4].upper(), prm["pitch"] * 100,
            prm["depth"], seed)
    if topology == "shingle":
        return "F%03d_SHIN_p%04d_d%03d_t%02d_s%02d" % (
            feat * 1000, prm["pitch"] * 100, prm["depth"],
            prm["tilt_deg"], seed)
    if topology == "truss":
        return "F%03d_TRUS_p%04d_d%03d_s%02d" % (
            feat * 1000, prm["pitch"] * 100, prm["depth"], seed)
    return "F%03d_HONE_p%04d_d%03d_s%02d" % (
        feat * 1000, prm["pitch"] * 100, prm["depth"], seed)


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
    print("[FEATURE] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for family, topology, feat, seed, prm in grid:
        tag = tag_for(family, topology, feat, seed, prm)
        if family == "topo":
            est = GT.TopoParams(**prm).exposed_fraction_est()
        elif family == "cell":
            est = GC.CellParams(**prm).exposed_fraction_est()
        else:
            est = G3.Cone3DParams(**prm).tip_fraction()
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": family,
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True, "spec_roughness": SPEC_ROUGHNESS,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": SPEC_ROUGHNESS},
                   "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": t}
                               for t in THETAS]}
            cfg.update({k: v for k, v in COAT.items()
                        if k not in ("spec_roughness",)})
            cfg["material_mode"] = "coating"
            t1 = time.time()
            try:
                res = BR.run(cfg)
            except Exception as e:
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            pj = json.dumps(prm, sort_keys=True)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "family": family,
                            "topology": topology, "feature": feat,
                            "seed": seed, "diffuse_frac": mname,
                            "pitch": prm["pitch"], "depth": prm["depth"],
                            "aspect": prm["depth"] / prm["pitch"],
                            "exposed_est": est, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            el = time.time() - t0
            print("[%4d/%4d] %-32s %-5s %5.1fs  eta %5.0fs"
                  % (n, total, tag, mname, time.time() - t1,
                     el / max(n, 1) * (total - n)), flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
