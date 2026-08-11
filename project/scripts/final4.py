"""
The four designs the comparison report is built on, measured under one setup.

    Blender --background --factory-startup --python scripts/final4.py

Two extruded V-grooves and two cone arrays, all at the same coating, the same
sampling and the same corrected Z margin, so nothing in the comparison depends
on when a number happened to be measured.
"""
import sys, os, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR
from cone3d_sweep import VIEW, COAT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "final4")


def cfg(tag, family, params):
    c = {"tag": tag, "family": family, "out_dir": RENDERS,
         "results_dir": os.path.join(ROOT, "results", "final4"),
         "samples": 512, "res_x": 1100, "res_y": 500, "gpu": True,
         "params": params, "renders": VIEW}
    c.update(COAT)
    return c


CASES = [
    cfg("D1_groove_p13", "ridge",
        dict(depth=50.0, pitch_mean=13.0, tip_width=0.8, arc_segments=24,
             valley_round=0.4)),
    cfg("D1_groove_p08", "ridge",
        dict(depth=50.0, pitch_mean=8.0, tip_width=0.8, arc_segments=24,
             valley_round=0.4)),
    cfg("D3_cone_p7.5", "cone3d",
        dict(face_w=100.0, face_h=100.0, depth=30.0, pitch=7.5,
             tip_radius=0.2, jitter=0.30, radial_seg=24, height_seg=3, depth_jitter=0.0)),
    cfg("D3_cone_p3.75", "cone3d",
        dict(face_w=100.0, face_h=100.0, depth=30.0, pitch=3.75,
             tip_radius=0.2, jitter=0.30, radial_seg=24, height_seg=3, depth_jitter=0.0)),
]


def main():
    os.makedirs(RENDERS, exist_ok=True)
    rows, t0 = [], time.time()
    for i, c in enumerate(CASES, 1):
        print("[CASE] (%d/%d) %-16s t+%.0fs" % (i, len(CASES), c["tag"],
                                                time.time() - t0), flush=True)
        res = BR.run(c)
        d = res["derived"]
        for name, rec in res["modes"].items():
            rows.append({"tag": c["tag"], "family": c["family"],
                         "depth": d["depth_mm"],
                         "pitch": d.get("pitch_mm", d.get("pitch_mean_mm")),
                         "theta": rec["theta"], "rho": rec["panel"]["mean"]})
    path = os.path.join(ROOT, "results", "sweep_final4.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("[DONE] %s (%.0fs)" % (path, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
