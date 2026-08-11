"""
Tip size at depth 30, the two candidate pitches.

    Blender --background --factory-startup --python scripts/cone_tip30.py

The tip was shown not to matter when it is a small fraction of the cell, and to
dominate completely once it is not -- the scale sweep read 0.048% at pitch 2.5
against a naive tip-area estimate of 0.047%. At depth 30 the pitches on the
table are 7.5 and 3.75 mm, where a 0.4 mm radius tip is 1.0% and 4.1% of the
cell, so this is exactly the regime where it starts to bite.

Radii 0.4 / 0.2 / 0.1 mm, i.e. tip diameters 0.8 / 0.4 / 0.2 mm, so the answer
is there whichever convention was meant. Nothing else is swept: FDM will not
hold a tip tighter than this, so the point is to pick a value and move on.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR
from cone3d_sweep import VIEW, COAT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "cone_tip30")


def case(pitch, r):
    cfg = {"tag": "T_p%04.1f_r%03d" % (pitch, r * 100), "family": "cone3d",
           "out_dir": RENDERS,
           "results_dir": os.path.join(ROOT, "results", "cone_tip30"),
           "samples": 384, "res_x": 1100, "res_y": 500, "gpu": True,
           "params": {"face_w": 100.0, "face_h": 100.0, "depth": 30.0,
                      "pitch": pitch, "tip_radius": r, "jitter": 0.30,
                      "radial_seg": 24, "height_seg": 3},
           "renders": VIEW}
    cfg.update(COAT)
    return cfg


CASES = [case(p, r) for p in (7.5, 3.75) for r in (0.4, 0.2, 0.1)]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, cfg in enumerate(CASES, 1):
        print("[CASE] (%d/%d) %s  t+%.0fs" % (i, len(CASES), cfg["tag"],
                                              time.time() - t0), flush=True)
        res = BR.run(cfg)
        d = res["derived"]
        for name, rec in res["modes"].items():
            rows.append({"tag": cfg["tag"], "pitch": d["pitch_mm"],
                         "tip_radius": cfg["params"]["tip_radius"],
                         "tip_dia": 2 * cfg["params"]["tip_radius"],
                         "tip_fraction": d["tip_fraction"],
                         "theta": rec["theta"], "rho": rec["panel"]["mean"]})
    path = os.path.join(ROOT, "results", "sweep_cone_tip30.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("[DONE] %s (%.0fs)" % (path, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
