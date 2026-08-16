"""Phase 5.11: buy the single-point assertions under the final verdict.

    Blender --background --factory-startup --python scripts/sweep_phase511.py

WHY. The 5.10 verdict rests on three claims that are each one measurement
(or zero) deep:
  (a) the thin cone's azimuth immunity — asserted from symmetry plus the
      OLD pitch-5.5 cone's 1.05x spread; the pitch-2 / r0.03 cone itself
      was never rotated;
  (b) the thin cone's seed robustness — jitter 0.3, ONE seed (23);
  (c) the pyramid drawing spec (tip <= 0.05 mm) and the azimuth hole were
      measured separately; whether they COMPOUND at phi 30 is unmeasured.

    PREDICTIONS, numeric, before any render.

    P1  CONE PHI SPREAD <= 5 %: r0.03 cone at phi 22.5 and 45 reads
        0.2122 ± 5 % (jitter already randomises azimuth within the cell;
        the lattice is the only phi-bearing structure left).

    P2  CONE SEED SPREAD <= 5 %: seeds 101 and 102 read 0.2122 ± 5 %
        (historical cone seed spread 4.5 % at pitch 5.5).

    P3  TIP AND AZIMUTH DO NOT COMPOUND ON TOTALS: pyramid t0.05 at
        phi 30 reads the t0 phi-30 value plus at most the phi-0 tip cost:
        0.2260 + (0.1145 - 0.1139) ~ 0.226, band 0.226 ± 0.010.

    P4  ...NOR ON THE FORM AXES: pyramid t0.05 at phi 30 —
        head-on 0.034 ± 0.008 (the phi-0 t0.05 value; head-on proved
        phi-proof at t0), smear 2.4 ± 0.5 (the phi-30 t0 value; the tip
        helped smear at phi 0, grazing hurts it, call it a wash),
        span <= 2.0x (phi breaks the stripe/lattice registration that
        gave t0.05 its 1.35x at phi 0 — it should not grow).

    IF ALL HOLD the recommendation stands as written and Phase 5 closes.
    Any failure names its own next experiment.

Anchor: P5_j00 + P510_cone_r003 params (identical to sweep_phase510.csv).
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase511.csv")
FORMJSON = os.path.join(RESULTS, "form_phase511.json")
OUT = "/tmp/phase511"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
PYR_T05 = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 18.0,
           "pitch": 2.0, "tip_flat": 0.05, "margin_depths": 2.0,
           "backing": 2.0}
S = 2.0 / 5.5
def cone(seed):
    return {"face_w": 60.0, "face_h": 60.0, "depth": 50.0 * S, "pitch": 2.0,
            "tip_radius": 0.03, "jitter": 0.3, "depth_jitter": 0.0,
            "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
            "seed": seed, "margin_depths": 2.0, "backing": 2.0}

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
# (tag, family, params, phi)
TOTALS = [
    ("P5_j00",           "floor",  ANCHOR,    0.0),
    ("P510_cone_r003",   "cone3d", cone(23),  0.0),    # anchor re-run
    ("P511_cone_phi225", "cone3d", cone(23),  22.5),
    ("P511_cone_phi45",  "cone3d", cone(23),  45.0),
    ("P511_cone_s101",   "cone3d", cone(101), 0.0),
    ("P511_cone_s102",   "cone3d", cone(102), 0.0),
    ("P511_pyrt05_phi30", "floor", PYR_T05,   30.0),
]
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac", "theta",
        "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.11 — buying the verdict's single-point assertions")
    print("=" * 74)
    for tag, family, prm, phi in TOTALS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        for mat in ALL:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT, "results_dir": OUT,
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
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "cone"),
                             "phi": phi, "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-18s phi %4.1f seed %3d  worst %.5f %%"
              % (tag, phi, prm.get("seed", 23), 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # form: pyramid t0.05 at phi 30 (the drawing spec at the worst azimuth)
    fout = {}
    print("\n=== form: P511_pyrt05_phi30 ===", flush=True)
    entry = {"tag": "P511_pyrt05_phi30", "family": "floor",
             "topology": "pyramid", "process": "press", "params": PYR_T05,
             "pitch": 2.0, "phi": 30.0}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["phi"] = 30.0
    rec["winding"] = "out"
    fout["P511_pyrt05_phi30"] = rec
    print("  smear %.3f  head-on %.5f  span@0 %.2fx"
          % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
