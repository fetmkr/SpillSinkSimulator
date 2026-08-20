"""
Every family at the feature size ITS OWN process delivers, depth fixed at 50 mm.

    Blender --background --factory-startup --python scripts/sweep_buildable.py
    STAGE=2 Blender ... scripts/sweep_buildable.py     # seed replicates

WHY THIS REPLACES sweep_feature.py. That sweep held minimum feature common at
0.2/0.3/0.4 mm across all nine families and the cone won everywhere. The axis
was wrong: a common feature size assumes a common process, and the cell families
are not printed. Aluminium honeycomb is a commodity with 0.03-0.1 mm foil, and
black-anodised honeycomb light traps are already sold for this exact purpose
(reference/HONEYCOMB_SPECS.md). Comparing a bought 0.04 mm foil wall against a
printed 0.4 mm cone tip on a "matched feature" axis penalises the honeycomb for
a constraint it does not have.

So each family sits at what it can really be made at:

    honeycomb / slant   0.03-0.1 mm foil, and ONLY the (cell, foil) pairs the
                        supplier actually lists -- the two are coupled, and a
                        0.1 mm wall forces a cell of 6.5 mm or coarser
    shingle             0.1 mm plate. Sheet metal in BOTH azimuth cases:
                        laser-cut, lanced, bent, spot-welded. Not printed.
    cone                0.4 mm tip DIAMETER, moulded or FDM
    printed cells       0.1 mm walls, optimistic for FDM, kept for comparison

CONE TIP IS FIXED AT 0.4 mm AND THAT IS A RESULT, NOT A CONCESSION. Measured in
sweep_feature.csv: tip diameter 0.4 -> 0.3 -> 0.2 mm gives 0.1983 -> 0.1937 ->
0.1851 %. Halving the tip buys 7%, against a geometry-realisation spread of
~3.5%. There is no optical reason to go sharper, and three practical reasons not
to: a 50 mm cone on a 5.5 mm pitch ending in a 0.2 mm point is fragile enough to
bend on contact, impossible to clean without damaging, and a sharp-bottomed
mould cavity traps air.

MARGIN IS 2.0, NOT 6.5, AND THAT IS MEASURED. `sweep_shapes.py` carried "margin
1.0 moves head-on by -15%, and the reason is not yet understood, so it stays".
test_margin.py swept 1.0/1.5/2.0/3.0/6.5 on both a wall network and a pillar
array: every value agrees within 3.5%, i.e. inside the realisation noise. The
-15% does not reproduce at theta <= 40. It was almost certainly measured with
grazing angles in the set, where a camera at 80 degrees needs 5.7 depths of
geometry and 1.0 genuinely is not enough. The objective narrowed to +/-40 and
the margin was never revisited. At +/-40 the geometric requirement is
depth/tan(50) + face_h/2 = 72 mm = margin_depths 1.44, so 2.0 carries margin.
This is what makes a 0.86 mm cell computable at all: at 6.5 it needs 14.2 M
faces, at 2.0 it needs 1.9 M.

Scoring unchanged: worst rho_dh over theta 0/+-20/+-40, then worst over diffuse
fraction 0.0/0.76/1.0.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import done_tags, shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
import geom_topo as GT                                             # noqa: E402
import geom_cell as GC                                             # noqa: E402
import geom3d as G3                                                # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "buildable")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_buildable.csv"))

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH = 50.0
MARGIN = 2.0
CONE_TIP_DIA = 0.4
SHEET = 0.1                     # folded / laser-cut sheet thickness

# (cell mm, foil mm) exactly as the supplier lists them. The two are coupled:
# micro-cell comes only in 0.03/0.04, regular cell only from 0.04 up.
# reference/HONEYCOMB_SPECS.md 1.
HONEY_MICRO = [(0.86, 0.03), (1.04, 0.03), (1.73, 0.04), (2.6, 0.04),
               (3.17, 0.04), (3.47, 0.04), (5.2, 0.04)]
HONEY_REG = [(6.5, 0.08), (6.5, 0.10), (8.47, 0.08), (8.47, 0.10),
             (9.53, 0.10), (12.7, 0.10)]
# commercial slant angles, not the 0/10/20/30 our own sweep happened to use
SLANT = (0.0, 30.0, 45.0, 60.0)
SLANT_ON = [(3.17, 0.04), (5.2, 0.04), (6.5, 0.10), (8.47, 0.08)]

FIELDS = ["tag", "family", "topology", "process", "feature", "seed",
          "diffuse_frac", "pitch", "depth", "aspect", "exposed_est",
          "theta", "rho", "control", "params_json"]


def designs(stage=1, seeds=(23,)):
    out = []
    for seed in seeds:
        base = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                    backing=2.0, seed=seed, depth=DEPTH)

        def topo(topology, process, feat, **kw):
            p = dict(base, topology=topology, jitter=0.30)
            p.update(kw)
            out.append(("topo", topology, process, feat, seed, p))

        def cell(variant, **kw):
            p = dict(base, variant=variant)
            p.update(kw)
            out.append(("cell", "c_" + variant, "print", SHEET, seed, p))

        # --- honeycomb, only buyable (cell, foil) pairs ---------------------
        for pitch, foil in HONEY_MICRO + HONEY_REG:
            topo("honeycomb", "expanded foil", foil,
                 pitch=pitch, wall_top=foil, wall_bot=foil)

        # --- slant honeycomb, at the commercial angles ----------------------
        for pitch, foil in SLANT_ON:
            for lean in SLANT:
                if lean == 0.0:
                    continue            # already covered above
                topo("slant", "expanded foil", foil,
                     topology_override=None, pitch=pitch, wall_top=foil,
                     wall_bot=foil, cell_lean_deg=lean, cell_lean_domain=16.0)

        # --- shingle: sheet metal, and the azimuth question -----------------
        # azimuth_jitter 180 was pinned in every shingle design ever run and
        # never compared against 0. Both are sheet-metal processes, so what
        # this decides is tooling complexity, not whether the part is printed.
        for pitch in (3.75, 5.5, 7.5):
            for tilt in (2.0, 6.0, 12.0):
                for az in (0.0, 180.0):
                    # BOTH are sheet metal, not printing. A randomly-oriented
                    # plate array is made by lancing tabs out of sheet and
                    # bending each one -- laser-cut, folded, spot-welded --
                    # which is how louvred ventilation and acoustic panels are
                    # already produced. The azimuth is set by the tooling, not
                    # by a printer. Labelling az=180 "print" was wrong and it
                    # would have pushed the answer toward the bought honeycomb
                    # for a reason that does not exist.
                    topo("shingle",
                         "sheet, parallel" if az == 0.0 else "sheet, lanced",
                         SHEET,
                         pitch=pitch, tilt_deg=tilt, plate_over=1.15,
                         plate_t_top=SHEET, plate_t_bot=0.9,
                         tilt_jitter=0.0, azimuth_jitter=az)

        # --- cone: tip diameter 0.4 mm, moulded ----------------------------
        for pitch in (3.75, 5.5, 7.5, 11.0):
            out.append(("cone3d", "cone", "mould", CONE_TIP_DIA, seed,
                        dict(face_w=FACE, face_h=FACE, depth=DEPTH,
                             pitch=pitch, tip_radius=CONE_TIP_DIA / 2.0,
                             jitter=0.30, radial_seg=24, height_seg=12,
                             margin_depths=MARGIN, backing=2.0,
                             depth_jitter=0.0, profile_power=1.0, seed=seed)))

        # --- printed cell variants, for comparison --------------------------
        for variant in ("square", "triangle", "mixed", "reentrant"):
            for pitch in (3.17, 5.2, 6.5):
                cell(variant, pitch=pitch, wall_top=SHEET, wall_bot=SHEET)
        cell("nested", pitch=11.0, wall_top=SHEET, wall_bot=SHEET)
    return out


def tag_for(family, topology, feat, seed, prm):
    if family == "cone3d":
        return "B_CONE_p%04d_s%02d" % (prm["pitch"] * 100, seed)
    if family == "cell":
        return "B_CELL%s_p%04d_s%02d" % (prm["variant"][:4].upper(),
                                         prm["pitch"] * 100, seed)
    if topology == "shingle":
        return "B_SHIN_p%04d_t%02d_az%03d_s%02d" % (
            prm["pitch"] * 100, prm["tilt_deg"], prm["azimuth_jitter"], seed)
    if topology == "slant":
        return "B_SLNT_p%04d_f%03d_ln%02d_s%02d" % (
            prm["pitch"] * 100, prm["wall_top"] * 1000,
            prm["cell_lean_deg"], seed)
    return "B_HONE_p%04d_f%03d_s%02d" % (prm["pitch"] * 100,
                                         prm["wall_top"] * 1000, seed)


def main():
    stage = int(os.environ.get("STAGE", "1"))
    seeds = (23,) if stage == 1 else tuple(range(101, 113))
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    new = not os.path.exists(OUTCSV)
    fh = open(OUTCSV, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()
        fh.flush()

    grid = designs(stage, seeds)
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[BUILD] stage %d: %d designs x %d materials = %d runs, %d done"
          % (stage, len(grid), len(DIFFUSE_FRACS), total, len(seen)),
          flush=True)

    t0, n = time.time(), 0
    for family, topology, process, feat, seed, prm in grid:
        # "slant" is a label for the report; geom_topo builds it as a honeycomb
        # with a lean, which is what the supplier's slant core physically is
        build_prm = {k: v for k, v in prm.items()
                     if k != "topology_override"}
        if topology == "slant":
            build_prm["topology"] = "honeycomb"
        tag = tag_for(family, topology, feat, seed, prm)
        if family == "topo":
            est = GT.TopoParams(**build_prm).exposed_fraction_est()
        elif family == "cell":
            est = GC.CellParams(**build_prm).exposed_fraction_est()
        else:
            est = G3.Cone3DParams(**build_prm).tip_fraction()
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
            cfg = {"tag": "%s_%s" % (tag, mname), "family": family,
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True, "spec_roughness": 0.30,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": 0.30},
                   "params": build_prm,
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
            pj = json.dumps(build_prm, sort_keys=True)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "family": family,
                            "topology": topology, "process": process,
                            "feature": feat, "seed": seed,
                            "diffuse_frac": mname, "pitch": prm["pitch"],
                            "depth": DEPTH, "aspect": DEPTH / prm["pitch"],
                            "exposed_est": est, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            el = time.time() - t0
            print("[%4d/%4d] %-30s %-5s %5.1fs  eta %5.0fs"
                  % (n, total, tag, mname, time.time() - t1,
                     el / max(n, 1) * (total - n)), flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
