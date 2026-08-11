"""
Does mixing two cone sizes buy anything?

    Blender --background --factory-startup --python scripts/cone_bimodal.py

Head-on reflectance comes from the exposed tips; grazing reflectance comes from
the smooth flanks of the big cones. Different surfaces, so in principle they
can be attacked separately: fill the valleys between the primary cones with a
finer, SHORTER array that traps the rays skimming those flanks, and sink it far
enough that its tips are shadowed at head-on and cost nothing there.

The render says that shadowing is not obvious: with a 7.1 degree half-angle the
primary cone is only 1.7 mm across at the depth where the secondary tips start,
against a 3.75 mm half-spacing, so the small tips are in plain view. The sweep
below settles whether that costs more than the trapping gains, and how far the
secondary has to be sunk before it stops costing anything.

Also finishes the tip-size question at depth 30, which the earlier run did not
get to: radii 0.4 / 0.2 / 0.1 mm, i.e. 0.8 / 0.4 / 0.2 mm across.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR
from cone3d_sweep import VIEW, COAT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "bimodal")


def case(tag, **params):
    cfg = {"tag": tag, "family": "cone3d", "out_dir": RENDERS,
           "results_dir": os.path.join(ROOT, "results", "bimodal"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"face_w": 100.0, "face_h": 100.0, "depth": 30.0,
                      "pitch": 7.5, "tip_radius": 0.4, "jitter": 0.30,
                      "radial_seg": 24, "height_seg": 3, **params},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


CASES = [
    case("B_none"),
    case("B_none_p3.75", pitch=3.75),
    # tip size on the plain array, the question left over from before
    case("B_tip020", tip_radius=0.2),
    case("B_tip010", tip_radius=0.1),
    # secondary array: two sizes, three sink depths
    case("B_s50_f40", second_ratio=0.5, second_depth_frac=0.40),
    case("B_s50_f55", second_ratio=0.5, second_depth_frac=0.55),
    case("B_s50_f70", second_ratio=0.5, second_depth_frac=0.70),
    case("B_s33_f55", second_ratio=0.33, second_depth_frac=0.55),
    # secondary with a fine tip, since its tips may be what costs
    case("B_s50_f55_t01", second_ratio=0.5, second_depth_frac=0.55,
         second_tip=0.1),
]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        print("[CASE] (%d/%d) %-16s t+%.0fs" % (i, len(CASES), cfg["tag"],
                                                time.time() - t0), flush=True)
        res = BR.run(cfg)
        d = res["derived"]
        for name, rec in res["modes"].items():
            rows.append({"tag": cfg["tag"], "pitch": d["pitch_mm"],
                         "tip_radius": cfg["params"]["tip_radius"],
                         "second_ratio": d.get("second_ratio", 0.0),
                         "second_depth_frac": d.get("second_depth_frac", 0.0),
                         "second_tip": d.get("second_tip_mm", 0.0),
                         "theta": rec["theta"], "rho": rec["panel"]["mean"]})
    path = os.path.join(ROOT, "results", "sweep_bimodal.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("[DONE] %s (%.0fs)" % (path, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
