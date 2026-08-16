"""Phase 5.9: pyramid vs cone at the worst azimuth — the deciding round.

    Blender --background --factory-startup --python scripts/sweep_phase59.py

WHERE 5.8 LEFT IT. Worst-over-azimuth totals: pyramid 0.226 % (phi 30) vs
cone 0.2160 % (phi-invariant by symmetry) — cone narrowly ahead on the one
axis where the pyramid had claimed the crown. The pyramid's remaining leads
(head-on 0.0272 vs 0.0595, 2.2x; smear 4.10 vs 4.06) are PHI-0 numbers.
This round measures the pyramid's form axes at phi 30, and asks whether the
cone can also be thin (its only measured configuration is 50 mm deep).

`form_buildable.run_case` gained `entry["phi"]` for this (panel rotates,
stripe/control/windows fixed). A phi-0 re-run guards the code change.

    PREDICTIONS, numeric, before any render.

    P1  GUARD: pyramid p2/d18 form at phi 0 through the edited code path
        reproduces smear 4.104 ± 0.25 and head-on 0.0272 ± 0.003.

    P2  HEAD-ON SURVIVES THE WORST AZIMUTH: at theta 0 the beam runs along
        the panel normal, and rotating the panel about that same axis
        cannot change what returns toward the source except through
        stripe-vs-valley alignment, which the 16-phase average integrates
        out. Pyramid head-on at phi 30 = 0.027 ± 0.008 — the 2.2x lead
        over the cone stands.

    P3  SMEAR DEGRADES AT PHI 30 BUT STAYS COMPETITIVE: the +-40 grazing
        transport that blew up the totals also carries the smear metric,
        so smear drops from 4.10 to 2.6-3.8. The cone's 4.06 then leads
        the smear axis.

    P4  CONE ANCHOR: re-measured through this script, AN_cone_p550
        params reproduce 0.2160 ± 4 % total (worst over 3 mats x 5 theta).

    P5  THE CONE IS SCALE-INVARIANT TOO: the same cone scaled x0.364
        (pitch 2.0, depth 18.2, tip 0.073, same jitter/seed) reads
        0.216 ± 0.015 %. If it holds, the cone matches the pyramid's
        20 mm panel and keeps its azimuth immunity.

    P6  THIN-CONE FORM: smear 4.0 ± 0.6, head-on 0.060 ± 0.015 (the
        cone's own phi-0 values carry over, as the pyramid's did at
        matched beam/pitch class).

    VERDICT RULE, fixed in advance: score worst-over-phi on all three
    axes. A design wins an axis if better by more than 8 % (2x seed
    noise); otherwise tied. The build recommendation goes to whichever
    wins more axes; a tie on axes goes to the THINNER panel.

Anchor: P5_j00 (phi 0, face 60) + AN_cone_p550 params pair with
sweep_rewind.csv for gate check 8.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase59.csv")
FORMJSON = os.path.join(RESULTS, "form_phase59.json")
OUT = "/tmp/phase59"

P0 = 5.500550055005501
PYR2 = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 18.0,
        "pitch": 2.0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
CONE55 = {"face_w": 60.0, "face_h": 60.0, "depth": 50.0, "pitch": 5.5,
          "tip_radius": 0.2, "jitter": 0.3, "depth_jitter": 0.0,
          "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
          "seed": 23, "margin_depths": 2.0, "backing": 2.0}
S = 2.0 / 5.5
CONE20 = dict(CONE55, pitch=2.0, depth=50.0 * S, tip_radius=0.2 * S)

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
# (tag, family, params, phi)
TOTALS = [
    ("P5_j00",        "floor",  ANCHOR, 0.0),
    ("P59_cone55",    "cone3d", CONE55, 0.0),
    ("P59_cone20",    "cone3d", CONE20, 0.0),
]
FORMS = [
    ("P59_pyr_phi0",  "floor",  PYR2,   2.0, 0.0),
    ("P59_pyr_phi30", "floor",  PYR2,   2.0, 30.0),
    ("P59_cone20_f",  "cone3d", CONE20, 2.0, 0.0),
]
COLS = ["tag", "family", "topology", "depth", "pitch", "phi", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.9 — pyramid vs cone at the worst azimuth")
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
                             "depth": prm["depth"], "pitch": prm["pitch"],
                             "phi": phi, "seed": prm.get("seed", 23),
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-14s depth %5.1f pitch %4.2f  worst %.5f %%"
              % (tag, prm["depth"], prm["pitch"], 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    fout = {}
    for tag, family, prm, pitch, phi in FORMS:
        print("\n=== form: %s (phi %.0f) ===" % (tag, phi), flush=True)
        entry = {"tag": tag, "family": family,
                 "topology": prm.get("kind", "cone"),
                 "process": "press" if family == "floor" else "mould",
                 "params": prm, "pitch": pitch}
        if phi:
            entry["phi"] = phi
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["span_0"] = z["peak_ratio_span"] if z else None
        rec["phi"] = phi
        rec["winding"] = "out"
        fout[tag] = rec
        print("  smear %.3f  head-on %.5f  span@0 %.2fx"
              % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
