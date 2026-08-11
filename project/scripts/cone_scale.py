"""
How shallow can the cone array go?

    Blender --background --factory-startup --python scripts/cone_scale.py

Depth 80 mm is a lot of wall. But for cones the tip does not matter -- shrinking
it 16x moved head-on 16% -- so unlike the 1D ridge there is no fixed absolute
dimension pinning the design. If nothing is pinned, the optics should depend
only on the aspect ratio A = depth / pitch and not on the absolute size, and
depth 20 with pitch 5 should equal depth 80 with pitch 20.

That is the whole question here, and it is testable: two aspect ratios, four
sizes each. If the rows at equal A agree, depth is free and can be traded
against pitch one for one.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR
from cone3d_sweep import VIEW, COAT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "cone_scale")


def case(depth, pitch):
    cfg = {"tag": "S_d%03d_p%04.1f" % (depth, pitch), "family": "cone3d",
           "out_dir": RENDERS, "results_dir": os.path.join(ROOT, "results", "cone_scale"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           # lighter cones: the fine-pitch cases would otherwise run to
           # millions of vertices, and the tip is known not to matter
           "params": {"face_w": 100.0, "face_h": 100.0, "depth": float(depth),
                      "pitch": float(pitch), "tip_radius": 0.4, "jitter": 0.30,
                      "radial_seg": 20, "height_seg": 2},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


CASES = ([case(d, d / 4.0) for d in (20, 30, 50, 80)] +
         [case(d, d / 8.0) for d in (20, 30, 50, 80)])


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        pr = cfg["params"]
        print("[CASE] (%d/%d) %-14s A=%.1f  t+%.0fs"
              % (i, len(CASES), cfg["tag"], pr["depth"] / pr["pitch"],
                 time.time() - t0), flush=True)
        res = BR.run(cfg)
        d = res["derived"]
        for name, rec in res["modes"].items():
            rows.append({"tag": cfg["tag"], "depth": d["depth_mm"],
                         "pitch": d["pitch_mm"], "aspect": d["aspect"],
                         "theta": rec["theta"],
                         "rho": rec["panel"]["mean"]})
    path = os.path.join(ROOT, "results", "sweep_cone_scale.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("[DONE] %s (%d rows, %.0fs)" % (path, len(rows), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
