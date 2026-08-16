"""Phase 5.8b: the azimuth hole has a mechanism and a fix — test both.

    Blender --background --factory-startup --python scripts/sweep_phase58b.py

WHAT 5.8 FOUND. The pyramid at phi 45 reads 0.19629 % worst (d100@40),
+51 % over its phi-0 value. Control pinned at 0.05000 at every row, worst
axis is PURE DIFFUSE — geometry, not a shader or winding artifact.

MECHANISM HYPOTHESIS, registered before these renders: along the cell
diagonal the surface profile is stretched by sqrt(2) while depth is
unchanged, so the EFFECTIVE aspect at phi 45 is aspect/sqrt(2) = 6.4, and
the aspect curve (phase 5.2) at 6.4 predicts ~0.17-0.19 — which is where
the phi-45 measurement landed. If that is the mechanism, two things follow:

    P1  SCALE INVARIANCE OF THE HOLE: the champion (p5.5/d50, same aspect)
        at phi 45 reads the same as the winner's phi-45 value:
        0.196 ± 0.012 % (worst over 3 mats x 5 theta).

    P2  THE FIX IS sqrt(2) MORE DEPTH: p2 / depth 25.5 (aspect 12.75,
        effective 9.0 at phi 45):
        phi 45 -> 0.134 ± 0.012 %   (back to the aspect-9 value)
        phi 0  -> 0.107 ± 0.008 %   (the aspect-12.75 point of the curve,
                                     interpolated between 11.8 -> 0.1075
                                     and 12.5 -> 0.1102... i.e. ~0.108)

    P3  INTERMEDIATE AZIMUTH IS INTERMEDIATE: p2/d18 at phi 22.5 lands
        between the phi-0 and phi-45 values: 0.150-0.180 %. If instead it
        exceeds the phi-45 value, the worst azimuth is not the diagonal
        and the mechanism story is wrong.

CONSEQUENCE IF P1-P2 HOLD: every pyramid total in this report is a
phi-0 number; the honest worst-over-azimuth spec is either (a) the same
pitch with sqrt(2) deeper cells (p2/d25.5, ~28 mm panel), or (b) a
rotationally symmetric cell (cone) re-entering the race. The three-axis
comparison must be redone on worst-over-phi.

Anchor: P5_j00 phi 0 (identical params to sweep_phase5.csv).
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase58b.csv")
OUT = "/tmp/phase58b"

P0 = 5.500550055005501
def pyr(depth, pitch):
    return {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0,
            "depth": depth, "pitch": pitch, "tip_flat": 0.0,
            "margin_depths": 2.0, "backing": 2.0}

ALL = ("d00", "d76", "d100")
DESIGNS = [
    ("P5_j00",         pyr(50.0, P0),  ALL, 0.0),    # anchor
    ("P58b_p55_phi45", pyr(50.0, P0),  ALL, 45.0),
    ("P58b_p02d25_p0", pyr(25.456, 2.0), ALL, 0.0),
    ("P58b_p02d25_p45", pyr(25.456, 2.0), ALL, 45.0),
    ("P58b_p02_phi225", pyr(18.0, 2.0), ALL, 22.5),
]
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "depth", "pitch", "phi", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.8b — the azimuth mechanism and the sqrt(2) fix")
    print("=" * 74)
    for tag, prm, mats, phi in DESIGNS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        for mat in mats:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": "floor", "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
                       "spec_roughness": 0.30, "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30}}
                if phi:
                    cfg["phi_deg"] = phi
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": "floor",
                             "topology": "pyramid", "depth": prm["depth"],
                             "pitch": prm["pitch"], "phi": phi, "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-16s depth %6.2f phi %4.1f  worst %.5f %%"
              % (tag, prm["depth"], phi, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
