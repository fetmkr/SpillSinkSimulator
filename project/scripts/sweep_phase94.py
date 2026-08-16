"""Phase 9.4: the fiber forest (flocking stand-in) — does floor exposure
kill it, as the 9.2 law predicts?

    Blender --background --factory-startup --python scripts/sweep_phase94.py

WHY. Flocking paper (식모지) is the only commodity that IS the
"shrink the pyramids to a fiber forest" limit, sold in 1 m rolls with
zero molding. If it lands anywhere near the bare-black pyramid tier
(0.907 % / head-on 0.107), it replaces the ENTIRE non-critical casting
tier and most of the 100-panel mold bill. The 9.2 law says it should
NOT: head-on is area-weighted, and a pillar field's area is mostly
exposed FLAT floor staring at the camera.

MODEL. Square pillars on a slab (`pillars` kind), Lambertian rho 0.05
throughout — black nylon fiber class [assumption registered; a real
coupon pins it]. Spacing 2 mm scaled up from real flock (~0.1 mm);
the aspect law is scale-invariant. fill = (width/pitch)^2.

    POSTDICTIONS, marked: the 32-spp geometry preview already saw
    fill 25 % / aspect 10 at theta 0 (1.398 %) and -40 (1.759 %).

    PREDICTIONS, numeric, before the sweep.

    P1  EXPOSURE OWNS THE TOTAL (worst over 5 theta, aspect 10):
        fill 4 %  -> 2.6 +- 0.8 %
        fill 10 % -> 2.2 +- 0.7 %
        fill 25 % -> 1.85 +- 0.4 % (anchored by the preview pair)
        All FAR above the bare pyramid's 0.907 %: the flat floor
        between fibers returns what the pyramid's closed base cannot.

    P2  ASPECT BUYS LITTLE AT LOW FILL: fill 25 % at aspect 5 reads
        within x1.35 of aspect 10 (2.0-2.6 %) — depth cannot shade a
        floor the camera sees directly at normal incidence.

    P3  HEAD-ON FAILS BY THE AREA LAW (form, beam 7.5 mm,
        fill 25 / aspect 10): peak ratio >= 0.4 vs the same-rho flat
        control — 4x the bare pyramid tier. Mechanism: 75 % of the
        camera-facing area IS a flat floor.

    DECISION RULE, registered: flocking replaces the bare cast tier
    iff total <= 0.9 % AND head-on <= 0.11 at any tested fill.
    Predicted verdict: FAILS both — flocking stays a candidate only
    for zones the pyramid tiers already treat as non-critical AND
    where a real coupon measures better than this Lambertian model
    (real fibers are tilted and entangled, which HIDES the floor;
    that geometry is not in this model and is the one mechanism that
    could save it — named, unmodeled, coupon's job).

Anchor: P5_j00 d100@-40 must equal 0.13392 %.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase94.csv")
FORMJSON = os.path.join(RESULTS, "form_phase94.json")
OUT = "/tmp/phase94"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}


def pillars(width, depth):
    return {"kind": "pillars", "face_w": 60.0, "face_h": 60.0,
            "depth": depth, "pitch": 2.0, "tip_flat": width,
            "margin_depths": 2.0, "backing": 2.0}


DESIGNS = [
    ("P94_f04_a10", pillars(0.4, 20.0)),
    ("P94_f10_a10", pillars(0.632, 20.0)),
    ("P94_f25_a10", pillars(1.0, 20.0)),
    ("P94_f25_a05", pillars(1.0, 10.0)),
]
TH5 = (0.0, -20.0, 20.0, -40.0, 40.0)
RHO = 0.05
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def run_one(tag, prm, th, coating=False):
        cfg = {"tag": "%s_%+03.0f" % (tag, th), "family": "floor",
               "out_dir": OUT, "results_dir": OUT, "samples": 64,
               "res_x": 480, "res_y": 220, "gpu": True,
               "spec_roughness": 0.30, "params": prm,
               "renders": [{"mode": "hemi_view", "theta": th}]}
        if coating:
            body, spec = BR.coating_split(1.0)
            cfg["material_mode"] = "coating"
            cfg["coating"] = {"body": body, "spec_scale": spec,
                              "roughness": 0.30}
            cfg.update({k: v for k, v in COAT.items()
                        if k != "spec_roughness"})
            mat = "d100"
        else:
            cfg["material_mode"] = "all_diffuse"
            cfg.update(rho_slat=RHO, rho_chamber=RHO, rho_specular=RHO,
                       rho_diffuse=RHO)
            mat = "bare005"
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": "floor",
                     "topology": prm["kind"], "phi": 0, "seed": 23,
                     "diffuse_frac": mat, "theta": th,
                     "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(prm, sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 9.4 — the fiber forest, measured against the area law")
    print("=" * 74)

    v = run_one("P5_j00", ANCHOR, -40.0, coating=True)
    print("  anchor: %.5f %% (book 0.13392)" % (100 * v), flush=True)

    for tag, prm in DESIGNS:
        w = 0.0
        for th in TH5:
            w = max(w, run_one(tag, prm, th))
        print("  %-12s fill=(%.3g/2)^2  worst(5th) %.4f %%"
              % (tag, prm["tip_flat"], 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P94_f25_a10 (beam %.1f) ===" % FB.STRIPE_W,
          flush=True)
    entry = {"tag": "P94_f25_a10_form", "family": "floor",
             "topology": "pillars", "process": "flock",
             "params": pillars(1.0, 20.0), "pitch": 2.0, "rho": RHO}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["stripe_w"] = FB.STRIPE_W
    fout["P94_f25_a10_form"] = rec
    print("  smear(+-40) %s  head-on %s"
          % (rec["smear"], rec["head_on"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
