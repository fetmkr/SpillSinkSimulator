"""Q8, part 2: what the two buildable blade arrays cost optically.

    Blender --background --factory-startup --python scripts/sweep_blade_fit2.py

Part 1 (`sweep_blade_fit.py`) counted the interference and found the published
design cannot be assembled from sheet: at `plate_over = 1.15`, `jitter = 0.30`,
grid azimuth, **89 of 193 blades (46.1 %) are involved in at least one
collision**, and no `plate_over` down to 0.70 makes it zero. Two settings do
make it zero, and each gives up something the study asked for:

    parallel azimuth      0 collisions at every width up to 1.45, because
                          parallel blades cannot cross. It is a slat array --
                          one axis only -- and azimuthal scattering is the
                          reason the blade family beat the V-groove.

    jitter 0, over <= 1.0 0 collisions on a regular lattice with blades that
                          just touch. It is PERIODIC, which this project bans
                          outright: a scanning beam over a periodic array
                          produces periodic bright spots.

This measures all three under the standard protocol so the cost of each escape
is a number rather than an argument.

    PREDICTION, written before the render.

    1. PARALLEL WILL BE WORSE ON TOTAL REFLECTANCE, by 10-30 %. With every
       blade facing the same way there is a clear channel along the blade
       direction, and a ray entering along it meets fewer surfaces before it
       leaves. `sweep_blade.csv` already has grid against parallel WITHOUT a
       floor and the direction there is the guide.

    2. THE PERIODIC ARRAY (jitter 0, over 1.0) WILL BE THE WORST OF THE THREE
       on total reflectance, by 20-50 %. Two effects push the same way: at
       over = 1.0 the blades no longer overlap, so each cell mouth has a clear
       line to the floor, and with no jitter every mouth is identical, so
       whatever leaks does so from every cell at once.

    3. NEITHER will be catastrophic -- I expect all three within a factor of
       two, because the pyramid floor and the 47 mm depth do most of the work
       and the blade layout is a second-order term on TOTAL reflectance. The
       cost of a periodic array is not in this number at all; it is in the form
       axis, which this sweep does not measure.

    If prediction 3 fails and a buildable variant is within a few percent of
    the published one, then Q8 is answered cheaply: build that one instead.

The anchor `BH_p055_t02_grid_s23` is measured again here, identical
`params_json` to `sweep_bladehood.csv` and to part 1, so gate check 8 ties all
three files together.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sweep_blade_fit as BF                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "sweep_bladefit2.csv")
OUT = "/tmp/bladefit2"

CASES = [
    # (plate_over, azimuth_mode, jitter, tag)
    (1.15, "grid", 0.30, "BH_p055_t02_grid_s23"),        # published, anchor
    (1.15, "parallel", 0.30, "BF_par115_s23"),           # buildable, 1D
    (1.00, "grid", 0.00, "BF_grid100_j0_s23"),           # buildable, periodic
    (1.00, "grid", 0.30, "BF_grid100_j30_s23"),          # over=1 but jittered
]

COLS = ["tag", "family", "topology", "process", "feature", "seed",
        "diffuse_frac", "plate_over", "azimuth_mode", "jitter", "blades",
        "collisions", "blades_hit", "hit_frac", "theta", "rho", "control",
        "params_json"]


def measure(over, mode, jitter, tag):
    import blender_render as BR
    from cone3d_sweep import COAT
    tp = {"azimuth_mode": mode, "jitter": jitter, "pitch": BF.PITCH,
          "plate_over": over, "plate_t_bot": 0.05, "plate_t_top": 0.05,
          "tilt_deg": 2.0, "tilt_jitter": 0.0}
    # RECORD THE PARAMETER THAT CHANGED THE GEOMETRY. `geom_floor.margin_min`
    # was added this session so a shaped floor reaches the tube standing on it;
    # for a blade field at face 60 the tube overhangs by 103.42 mm against the
    # 100.00 mm the old rule gave, so the floor grew by 3.42 mm and every
    # blade-stack measurement moved by up to 0.76 %. Leaving it out of
    # `params_json` would let gate check 8 compare these rows against
    # `sweep_bladehood.csv` as if they were the same geometry -- the exact
    # failure `plate_over` caused. Recorded, the gate reports them as measuring
    # different things, which is true.
    prm = {"backing": 2.0, "bot": "pyramid", "bot_depth": BF.FDEPTH,
           "bot_params": {"margin_depth_ref": BF.DEPTH, "pitch": 2.0,
                          "tip_flat": 0.1},
           "face_h": BF.FACE, "face_w": BF.FACE, "margin_depths": 2.0,
           "seed": 23, "top": "shingle", "top_depth": BF.DEPTH - BF.FDEPTH,
           "top_params": tp}
    rows = []
    for mat, df in (("d00", 0.0), ("d76", 0.76), ("d100", 1.0)):
        body, spec = BR.coating_split(df)
        for th in (0.0, -20.0, 20.0, -40.0, 40.0):
            cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th), "family": "stack",
                   "out_dir": OUT, "results_dir": OUT, "samples": 64,
                   "res_x": 480, "res_y": 220, "gpu": True,
                   "spec_roughness": 0.30, "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": th}],
                   "material_mode": "coating",
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": 0.30}}
            cfg.update({k: v for k, v in COAT.items()
                        if k != "spec_roughness"})
            res = BR.run(cfg)
            rec = list(res["modes"].values())[0]
            rows.append((mat, th, rec["panel"]["mean"], rec["control"]["mean"],
                         json.dumps(prm, sort_keys=True)))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 74)
    print("Q8 part 2: the optical cost of a buildable blade array")
    print("=" * 74)
    rows = []
    for over, mode, jitter, tag in CASES:
        b, _p = BF.blade_segments(over, mode, jitter=jitter)
        g = BF.count_interference(b)
        print("\n  %-22s over %.2f %-8s jitter %.2f -> %d collisions, "
              "%.1f%% of blades"
              % (tag, over, mode, jitter, g["collisions"],
                 100 * g["hit_frac"]), flush=True)
        for mat, th, rho, ctrl, pj in measure(over, mode, jitter, tag):
            rows.append({"tag": tag, "family": "stack",
                         "topology": "shingle/pyramid", "process": "sheet",
                         "feature": 0.05, "seed": 23, "diffuse_frac": mat,
                         "plate_over": over, "azimuth_mode": mode,
                         "jitter": jitter, "blades": g["blades"],
                         "collisions": g["collisions"],
                         "blades_hit": g["blades_hit"],
                         "hit_frac": round(g["hit_frac"], 5),
                         "theta": th, "rho": rho, "control": ctrl,
                         "params_json": pj})

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nwrote %s (%d rows)" % (CSV, len(rows)))

    worst, zero = {}, {}
    for r in rows:
        worst[r["tag"]] = max(worst.get(r["tag"], 0.0), r["rho"])
        if abs(r["theta"]) < 1e-9:
            zero[r["tag"]] = max(zero.get(r["tag"], 0.0), r["rho"])
    base = worst["BH_p055_t02_grid_s23"]
    basez = zero["BH_p055_t02_grid_s23"]
    print("\n  %-22s %11s %11s %11s %9s"
          % ("design", "worst rho", "theta-0 rho", "vs published", "buildable"))
    for over, mode, jitter, tag in CASES:
        b, _p = BF.blade_segments(over, mode, jitter=jitter)
        g = BF.count_interference(b)
        print("  %-22s %10.5f%% %10.5f%% %10s %9s"
              % (tag, 100 * worst[tag], 100 * zero[tag],
                 "-" if tag.startswith("BH_")
                 else "%+.1f%%" % (100 * (worst[tag] - base) / base),
                 "yes" if g["collisions"] == 0 else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
