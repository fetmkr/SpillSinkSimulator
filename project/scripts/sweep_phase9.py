"""Phase 9.1: the two physics questions that price 100 panels of 1 m^2.

    Blender --background --factory-startup --python scripts/sweep_phase9.py

WHY NOW. The user needs ~100 units of 1 m^2. At that quantity the panel
price is set by two simulation-answerable questions:

  (a) EXTRUSION: an extruded groove profile (same 4/20/0.1 cross-section
      as the pyramid) can be made in endless 1 m-wide lengths in soft
      PVC/TPU. The unknown is the azimuth hole: a groove has a mirror
      plane along its axis. If the worst azimuth stays inside x1.6 of
      phi 0 -- the pyramid's own azimuth factor class -- extrusion
      unlocks and mold-casting dies to a niche.
  (b) BARE MATERIAL: if a plain black urethane (rho ~4-8 %, no Musou)
      pyramid field already lands near the flat-Musou class (~1.1 %),
      the walls far from the audience can skip the paint entirely.
      Paint area for 100 m^2 of texture is ~500 m^2 of slant face --
      the coating is a first-order cost term.

    ASSUMPTION, stated: bare cast urethane/TPU blacks sit at
    rho 0.04-0.08 Lambertian. The sweep brackets that range; a vendor
    datasheet or coupon pins the point inside it later.

    PREDICTIONS, numeric, before any render.

    P1  GROOVES AT PHI 0 MATCH THE PYRAMID CLASS: worst over
        3 mats x 5 theta = 0.19 +- 0.05 % (pyramid book: 0.17668 %).
        Same aspect, same coating; the 2D cavity loses the corner
        leaks of the 3D cell and gains a continuous valley.

    P2  THE GROOVE AZIMUTH HOLE IS BOUNDED (the extrusion decision):
        worst over phi in {15,30,45,60,75} x 3 mats at theta -40, and
        phi 90 over 3 mats x 5 theta, all <= 0.30 % absolute
        (= x1.6 of the P1 center). Medium confidence: at phi 90 the
        transverse projection still descends the V steeply, so the
        ladder survives; the risk is a specular along-axis channel at
        d00. If any phi row breaks 0.30 %, extrusion needs an
        orientation rule (grooves vertical) or dies.

    P3  BARE BLACK SCALES LINEARLY AND LANDS NEAR FLAT-MUSOU:
        pyramid 4/20/0.1, pure Lambertian, worst over 5 theta:
        rho 0.05 -> 0.90 +- 0.30 %; rho 0.04 -> 0.72 and
        rho 0.08 -> 1.44, each +- 35 %. Mechanism: a diffuse aspect-5
        cavity lets ~1/5 of first-bounce flux escape, so rho_eff is
        ~0.18 x rho, linear in rho.

    P4  BARE FORM (beam width 7.5 mm): head-on < 0.5 (wide band, low
        confidence -- no specular lobe exists, so the peak is diffuse
        spill); smear >= 1.2. Both recorded against the same-material
        flat control.

    P5  GROOVE FORM AT PHI 0 (beam width 7.5 mm) MATCHES THE PYRAMID:
        head-on 0.040 +- 0.020, smear 1.42 +- 0.40. PHI 90 form is
        UNPREDICTED (no analog exists in the book) and is recorded as
        measured.

    DECISION RULES, registered with the predictions:
    - Extrusion path unlocks iff P2 holds AND groove phi-90 head-on
      <= 0.08 at beam 7.5.
    - Skip-Musou zones become a design option iff bare rho<=0.05 worst
      <= 1.2 % (the flat-Musou wall class).

Anchor: P5_j00, 3 mats x 5 theta, cross-checked against the book value
0.13392 % (d100 at -40, 64 spp) before anything is announced.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase9.csv")
FORMJSON = os.path.join(RESULTS, "form_phase9.json")
OUT = "/tmp/phase9"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
FINAL = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
GROOVE = {"face_w": 60.0, "face_h": 60.0, "depth": 20.0, "backing": 2.0,
          "pitch_mean": 4.0, "pitch_jitter": 0.0, "tip_width": 0.1,
          "tip_round": False, "valley_round": 0.0, "micro_pitch": 0.0,
          "micro_depth": 0.0, "margin_depths": 2.0}

DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
TH5 = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "phi", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 9.1 — extrusion azimuth + bare-material, pricing 100 m^2")
    print("=" * 74)

    def run_one(tag, family, prm, mat, th, phi, mode_cfg):
        cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
               "family": family, "out_dir": OUT, "results_dir": OUT,
               "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
               "spec_roughness": 0.30, "params": prm,
               "renders": [{"mode": "hemi_view", "theta": th}]}
        cfg.update(mode_cfg)
        if phi:
            cfg["phi_deg"] = phi
            cfg["tag"] += "_f%02.0f" % phi
        res = BR.run(cfg)
        rec = list(res["modes"].values())[0]
        rows.append({"tag": tag, "family": family,
                     "topology": prm.get("kind", "groove"),
                     "phi": phi, "seed": 23, "diffuse_frac": mat,
                     "theta": th, "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "params_json": json.dumps(
                         dict(prm, **({"phi": phi} if phi else {})),
                         sort_keys=True)})
        return rec["panel"]["mean"]

    def coat_cfg(mat):
        body, spec = BR.coating_split(DF[mat])
        c = {"material_mode": "coating",
             "coating": {"body": body, "spec_scale": spec,
                         "roughness": 0.30}}
        c.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
        return c

    # anchor + grooves phi 0 / phi 90 (3 mats x 5 theta each)
    for tag, family, prm, phi in (
            ("P5_j00", "floor", ANCHOR, 0),
            ("P91_groove_p00", "ridge", GROOVE, 0),
            ("P91_groove_p90", "ridge", GROOVE, 90.0)):
        w = 0.0
        for mat in ("d00", "d76", "d100"):
            for th in TH5:
                w = max(w, run_one(tag, family, prm, mat, th, phi,
                                   coat_cfg(mat)))
        print("  %-16s worst(mats x 5th) %.5f %%" % (tag, 100 * w),
              flush=True)

    # groove azimuth scan at theta -40, all mats
    w = 0.0
    per = {}
    for phi in (15.0, 30.0, 45.0, 60.0, 75.0):
        for mat in ("d00", "d76", "d100"):
            v = run_one("P91_groove_scan", "ridge", GROOVE, mat, -40.0,
                        phi, coat_cfg(mat))
            w = max(w, v)
            per[phi] = max(per.get(phi, 0.0), v)
    print("  groove phi-scan worst(th-40) %.5f %%   [%s]"
          % (100 * w, "  ".join("%g:%.3f%%" % (f, 100 * v)
                                for f, v in sorted(per.items()))),
          flush=True)

    # bare black pyramid, Lambertian bracket
    for r in (0.04, 0.05, 0.08):
        w = 0.0
        mode = {"material_mode": "all_diffuse", "rho_slat": r,
                "rho_chamber": r, "rho_specular": r, "rho_diffuse": r}
        for th in TH5:
            w = max(w, run_one("P91_bare_r%03.0f" % (r * 100), "floor",
                               FINAL, "bare%03.0f" % (r * 100), th, 0,
                               mode))
        print("  bare rho=%.2f  worst(5th) %.5f %%" % (r, 100 * w),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for row in rows:
            wcsv.writerow(row)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # form: groove phi0, groove phi90, bare 0.05 (beam 7.5 throughout)
    fout = {}
    for tag, family, prm, phi, rho in (
            ("P91_groove_form_p00", "ridge", GROOVE, 0, None),
            ("P91_groove_form_p90", "ridge", GROOVE, 90.0, None),
            ("P91_bare_form_r05", "floor", FINAL, 0, 0.05)):
        print("\n=== form: %s (beam %.1f) ===" % (tag, FB.STRIPE_W),
              flush=True)
        entry = {"tag": tag, "family": family, "topology": "groove",
                 "process": "extrude" if family == "ridge" else "cast",
                 "params": prm, "pitch": 4.0}
        if phi:
            entry["phi"] = phi
        if rho is not None:
            entry["rho"] = rho
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["span_0"] = z["peak_ratio_span"] if z else None
        rec["stripe_w"] = FB.STRIPE_W
        fout[tag] = rec
        print("  smear(+-40) %s  head-on %s"
              % (rec["smear"], rec["head_on"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
