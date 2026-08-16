"""Phase 5.6: is the winner robust to the coating parameters nobody measured?

    Blender --background --factory-startup --python scripts/sweep_phase56.py

WHY. QUESTIONS.md Q6: `spec_roughness = 0.30` is pinned everywhere, is
unmeasured on the physical paint, and on the form axis the FLAT baseline
swings 332x across 0.10-0.50. Phase 5 crowned p2/d18 at exactly one point of
that axis. A winner that flips with an unmeasured parameter is the kind of
wrong claim this project keeps having to retract — so the claim is bought
here, before anything is ordered.

WHAT RUNS. Total axis (hemi_view, worst over theta): the winner p2/d18 and
the flat slab (the denominator of every "Nx darker" claim), each at
roughness 0.10 / 0.20 / 0.30 / 0.40 / 0.50 under d00 and d76 (d100 has no
specular lobe: measured only at the extremes as a self-test). Form axis:
p2/d18 full protocol at 0.10 and 0.50 (protocol beam 2 mm). Anchor P5_j00
at 0.30 pairs with sweep_phase5.csv; the p2/d18 0.30 rows duplicate
P54_p02_t00 and must agree with it.

    PREDICTIONS, numeric, written before any render.

    P1  FLAT TOTAL IS ROUGHNESS-INVARIANT: rho_dh integrates the whole
        hemisphere, and roughness only redistributes within it. Worst
        stays 1.141 +/- 0.11 % across 0.10-0.50 (the 332x of Q6 is a
        PEAK-axis effect, not a total).

    P2  THE WINNER IS ROBUST ON TOTAL: p2/d18 worst-over-(d00,d76) stays
        within +/- 25 % of 0.130 % at every roughness, and its advantage
        over the flat slab stays >= 6x everywhere. Mechanism risk being
        tested: a NARROW lobe (0.10) makes facet-to-facet chains coherent
        — they could either walk deeper (darker) or find the exit faster
        (brighter). I cannot sign the direction; I can sign the bound.

    P3  d100 SELF-TEST: pure-diffuse rows at 0.10 and 0.50 agree within
        2 % (no specular lobe to roughen). If they differ, the harness is
        leaking roughness into the diffuse shader and every row here is
        suspect.

    P4  THE WINNER'S HEAD-ON DOES NOT SPIKE AT LOW ROUGHNESS: flat's
        theta=0 peak explodes 119.92 at 0.10 (form_roughness.json) because
        it has a mirror facing the viewer. The sharp pyramid presents no
        upward-facing area, so head_on stays in 0.014-0.060 at both 0.10
        and 0.50 (i.e. within ~2x of its 0.30 value 0.0272).

    P5  SMEAR STAYS WITHIN 2x of 4.10 at both extremes (band 2.0-8.2,
        protocol beam 2 mm): the smudge width is set by geometry fanning
        bounces over facets, not by the lobe width of one bounce.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase56.csv")
FORMJSON = os.path.join(RESULTS, "form_phase56.json")
OUT = "/tmp/phase56"

FACE = 60.0
P0 = 5.500550055005501
PYR = {"kind": "pyramid", "face_w": FACE, "face_h": FACE,
       "margin_depths": 2.0, "backing": 2.0}
P02 = dict(PYR, depth=18.0, pitch=2.0, tip_flat=0.0)
ANCHOR = dict(PYR, depth=50.0, pitch=P0, tip_flat=0.0)
# FACE 100 AND NOT 60, MEASURED REASON (found mid-run, 2026-08-16): the
# degenerate slab has margin_depths x 0.001 mm ~= NO margin, and hemi_view's
# panel window then reads 21 % low at face 60 (0.794 % for a plate whose
# closed-form value is 0.998 %). At face 100 and 200 the same call reads
# 0.99832 / 0.99839 % -- converged and equal to fit_coating.py's validated
# construction, which always used FACE = 100. rho_dh is intensive, so the
# flat's face size does not affect comparability with the face-60 pyramids.
# The first run of this sweep used face 60 for the flat; those rows were 21 %
# flattering to the WINNER and are superseded by this file's output.
FLAT = dict(face_w=100.0, face_h=100.0, depth=0.001, pitch_mean=50.0,
            tip_width=50.0, tip_round=False, pitch_jitter=0.0,
            arc_segments=4, valley_round=0.0, margin_depths=6.5)

ROUGHS = (0.10, 0.20, 0.30, 0.40, 0.50)
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
COLS = ["tag", "family", "topology", "roughness", "seed", "diffuse_frac",
        "theta", "rho", "control", "params_json"]


def cases():
    # (tag, family, params, roughness, mats)
    yield ("P5_j00", "floor", ANCHOR, 0.30, ("d00", "d76", "d100"))
    for r in ROUGHS:
        mats = ["d00", "d76"]
        if r == 0.30:
            mats.append("d100")        # completes the P54_p02_t00 duplicate
        yield ("P56_p02_r%02.0f" % (100 * r), "floor", P02, r, tuple(mats))
    for r in ROUGHS:
        yield ("P56_flat_r%02.0f" % (100 * r), "ridge", FLAT, r,
               ("d00", "d76"))
    yield ("P56_p02x_r10", "floor", P02, 0.10, ("d100",))
    yield ("P56_p02x_r50", "floor", P02, 0.50, ("d100",))


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
    rows = []
    print("=" * 74)
    print("PHASE 5.6 — coating-parameter robustness of the winner")
    print("=" * 74)
    for tag, family, prm, rough, mats in cases():
        pj = json.dumps(dict(prm, winding="out"), sort_keys=True)
        w = 0.0
        for mat in mats:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
                       "spec_roughness": rough, "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": rough}}
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "flat"),
                             "roughness": rough, "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-16s rough %.2f  mats %-14s worst %.5f %%"
              % (tag, rough, ",".join(mats), 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # --- form axis at the roughness extremes -------------------------------
    fout = {}
    for r in (0.10, 0.50):
        tag = "P56_form_p02_r%02.0f" % (100 * r)
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                 "process": "press", "params": P02, "pitch": 2.0,
                 "roughness": r}
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["span_0"] = z["peak_ratio_span"] if z else None
        rec["roughness"] = r
        rec["winding"] = "out"
        fout[tag] = rec
        print("  smear %.3f  head-on %.5f  span@0 %.2fx"
              % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
