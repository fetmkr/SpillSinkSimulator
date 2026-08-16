"""Phase 9.4b: tilted, overlapping fibers — closing the one door 9.4
left open.

    Blender --background --factory-startup --python scripts/sweep_phase94b.py

WHY. 9.4 rejected the vertical-pillar flock model (head-on 1.0004 = a
flat plate) but named one unmodeled rescue: real flock fibers TILT and
ENTANGLE, hiding the floor. `pillar_lean` now shears each fiber by
depth*tan(lean) in a seeded random azimuth; at aspect 10 even 9 degrees
of lean fully covers the floor in projection, and the render shows a
thatch with no floor visible. This sweep measures whether hiding the
floor rescues the deciding axis.

MODEL. fill 25 % (width 1.0, pitch 2), height 20, Lambertian rho 0.05,
lean 15 / 30 / 45 degrees. POSTDICTION marked: a 32-spp preview saw
lean 30 at theta 0 read 1.96 %.

    PREDICTIONS, numeric, before the sweep.

    P1  TOTALS GET WORSE WITH LEAN, not better: leaning sides face the
        sky and the camera more (cosine), and fibers shade each other
        less steeply. Worst over 5 theta: lean 15 -> 1.9 +- 0.3 %,
        lean 30 -> 2.1 +- 0.4 %, lean 45 -> 2.4 +- 0.5 %.
        (Vertical fill 25 measured 1.758 %.)

    P2  HIDING THE FLOOR DOES NOT RESCUE HEAD-ON, it only halves it:
        the floor's specular-free retro is replaced by tilted LAMBERTIAN
        faces that still radiate toward a head-on camera with only a
        cosine penalty. Form at beam 7.5 mm, lean 30:
        head-on 0.35 +- 0.15 — still 3x over the 0.11 rule.

    REGISTERED VERDICT: within any Lambertian model, flocking fails the
    replacement rule at every lean; tilt moves the failure from "flat
    floor stares back" to "tilted faces still glow". Only fiber-scale
    physics beyond Lambertian (specular fiber sides channeling light
    down, sub-beam self-shadowing) could revive it — and that is
    exactly what the physical coupon measures. After this sweep the
    door is closed on the simulation side.

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
CSV = os.path.join(RESULTS, "sweep_phase94b.csv")
FORMJSON = os.path.join(RESULTS, "form_phase94b.json")
OUT = "/tmp/phase94b"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}


def pillars(lean):
    return {"kind": "pillars", "face_w": 60.0, "face_h": 60.0,
            "depth": 20.0, "pitch": 2.0, "tip_flat": 1.0,
            "margin_depths": 2.0, "backing": 2.0, "pillar_lean": lean}


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
        rows.append({"tag": tag, "family": "floor", "topology": "pillars",
                     "phi": 0, "seed": 23, "diffuse_frac": mat,
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(prm, sort_keys=True)})
        return rec["panel"]["mean"]

    print("=" * 74)
    print("PHASE 9.4b — tilted fibers: does hiding the floor rescue flock?")
    print("=" * 74)

    v = run_one("P5_j00", ANCHOR, -40.0, coating=True)
    print("  anchor: %.5f %% (book 0.13392)" % (100 * v), flush=True)

    for lean in (15.0, 30.0, 45.0):
        tag = "P94b_lean%02.0f" % lean
        w = 0.0
        for th in TH5:
            w = max(w, run_one(tag, pillars(lean), th))
        print("  lean %2.0f deg  worst(5th) %.4f %%" % (lean, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    print("\n=== form: P94b_lean30 (beam %.1f) ===" % FB.STRIPE_W,
          flush=True)
    entry = {"tag": "P94b_lean30_form", "family": "floor",
             "topology": "pillars", "process": "flock",
             "params": pillars(30.0), "pitch": 2.0, "rho": RHO}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["stripe_w"] = FB.STRIPE_W
    fout["P94b_lean30_form"] = rec
    print("  smear(+-40) %s  head-on %s"
          % (rec["smear"], rec["head_on"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
