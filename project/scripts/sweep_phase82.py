"""Phase 8.2: the tilted AR window, measured. First simulation of Phase 8.

    Blender --background --factory-startup --python scripts/sweep_phase82.py

THE OBJECT. A 2 mm glass plate, AR-coated both sides (residual R per
surface, CONSTANT over angle by declared model -- the real angle curve is
the physical coupon's job), hinged at its TOP edge in the wall plane and
swung back 25 degrees at the bottom -- a hopper, glass facing DOWN --
over a void 90 deep whose interior is idealised black (rho 0). A beam
from elevation +theta reflects to -(theta + 2*tilt): every beam from the
projector above goes DOWN (beam 0 -> 50 down into a trough at the wall
base; beam +40 -> straight down, dies inside the box). The only beam a
level observer could catch mirrored must rise from 2*tilt BELOW the
horizon, where the floor is (report 8.1's "tilt >= 25" rule).

ORIENTATION WAS PINNED BY RENDER, NOT INTUITION: the sign was chased
twice on paper and both drafts disagreed; a 32-spp preview measured the
leaning-mirror orientation throwing 2R back near-horizontal (ratio 0.40
at +40) and settled it. The hopper is the correct build.

WHAT THE 32-SPP GEOMETRY PREVIEW ALREADY SHOWED (so these three rows
are POSTDICTIONS, marked): hemi_view of this assembly is NOT flat-2R.
The observer's mirrored sightline (elev -(theta+50)) either exits the
aperture into the world (reads ~2R) or ends on the black box interior
(reads ~0). Preview at R 1 %: theta 0 -> 1.84 %, theta +40 -> 0.001 %,
theta -40 -> 1.99 %. This IS the deployment physics: an observer above
the window sees the box floor mirrored; only observers at or below
window level see the mirrored room -- and in a real install that
mirrored scene is the dark trough, not a white world, so the uniform-
world hemi_view numbers are the WORST CASE for level observers.

    PREDICTIONS, numeric, before the measurement sweep. The aperture-
    clip model behind P1/P2: a window point at height z sees its mirror
    ray exit only if z - tan(theta+50)*|y(z)| > -61.

    P1  R-SCALING AT THETA 0 (true predictions at R 0.5/2 %; the R 1 %
        row is the preview's postdiction): panel mean = 0.92 x 2R
        +- 10 % -> R 0.5 %: 0.92 +- 0.09 %; R 2 %: 3.67 +- 0.37 %.

    P2  THE MIRROR-SHADOW LAW (true predictions, R 1 %):
        theta +20: clip model gives upper 43 % of window lit ->
        0.86 +- 0.30 %. theta +50/+70: mirror ray points down-back,
        never exits -> < 0.05 %. theta -20: 1.9 +- 0.3 %.
        theta -50/-70: back-face mirror path keeps the world visible ->
        1.6-2.0 %. (theta +-40 are the preview's postdictions.)

    P3  THE DANGER DIRECTION IS SINGLE AND PREDICTED (angle mode, front
        camera, R 1 %): the mirrored-sun ratio vs the 5 % control spikes
        ONLY at theta = -(2*tilt) = -50: ratio > 100 there; at every
        scanned theta with |theta + 50| >= 10 the ratio stays < 0.5.
        Shoulders at -45/-55 are unpredicted; reported as measured.

    P4  SYSTEM (glass + void + final-sample pyramid trap at the back,
        R 1 %): theta 0 = plate + T^2-seen trap = 1.84 + 0.17
        = 2.0 +- 0.5 %; theta +40 = the trap SEEN THROUGH the glass with
        the mirror term dead = 0.17 +- 0.08 % -- the system's above-
        window return matches the bare pyramid wall's own class.
        theta +20 = 0.86 + 0.17 = 1.0 +- 0.4 %.

    P5  FORM (beam width 7.5 mm, theta 0/+-40): head-on peak ratio
        < 0.005 -- the specular residual leaves the camera axis entirely
        (vs 0.040 for the pyramid wall, ~8x better). Smear is NOT
        gradeable on a near-zero return (rms of noise); reported, not
        banded, with the reason in the row.

WHY TOTALS MISLEAD HERE, ON PURPOSE: P1 says the window returns ~2R
(1-4 %), far WORSE than the pyramid wall's 0.177 % on the same
non-directional axis -- yet P3 says no front observer ever sees it.
The pair is the argument for 8.3's direction-resolved audience metric.

Anchor: P5_j00 reproduced alongside (the standing cross-code anchor).
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase82.csv")
FORMJSON = os.path.join(RESULTS, "form_phase82.json")
OUT = "/tmp/phase82"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
# envelope doubles as the system run's trap field: the final sample at 100
ENV = {"kind": "pyramid", "face_w": 100.0, "face_h": 100.0, "depth": 20.0,
       "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 2.0, "backing": 2.0}
AR_BASE = {"tilt_deg": 25.0, "thickness": 2.0, "ar_roughness": 0.02,
           "void_rho": 0.0, "void_depth": 90.0}

COLS = ["tag", "family", "topology", "mode", "r_surface", "theta",
        "rho", "control", "ratio", "params_json"]


def hemi_job(tag, prm, ar, th):
    return {"tag": tag, "family": "arplate", "out_dir": OUT,
            "results_dir": OUT, "samples": 64, "res_x": 480, "res_y": 220,
            "gpu": True, "params": prm, "ar": ar,
            "material_mode": "ar_glass",
            "renders": [{"mode": "hemi_view", "theta": th}]}


def angle_job(tag, prm, ar, th):
    j = hemi_job(tag, prm, ar, th)
    j["samples"] = 128
    j["renders"] = [{"mode": "angle", "theta": th}]
    return j


def main():
    import blender_render as BR
    import form_buildable as FB
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def record(tag, mode, r_surf, th, rec, ar_used=None):
        rows.append({"tag": tag, "family": "arplate", "topology": "arplate",
                     "mode": mode, "r_surface": r_surf, "theta": th,
                     "rho": rec["panel"]["mean"],
                     "control": rec["control"]["mean"],
                     "ratio": rec["ratio_mean"],
                     "params_json": json.dumps(ar_used or AR_BASE,
                                               sort_keys=True)})

    print("=" * 74)
    print("PHASE 8.2 — the tilted AR window")
    print("=" * 74)

    # anchor
    cfg = {"tag": "P5_j00_a82", "family": "floor", "out_dir": OUT,
           "results_dir": OUT, "samples": 64, "res_x": 480, "res_y": 220,
           "gpu": True, "spec_roughness": 0.30, "params": ANCHOR,
           "renders": [{"mode": "hemi_view", "theta": -40.0}],
           "material_mode": "coating"}
    body, spec = BR.coating_split(1.0)
    cfg["coating"] = {"body": body, "spec_scale": spec, "roughness": 0.30}
    cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
    res = BR.run(cfg)
    rec = list(res["modes"].values())[0]
    print("  anchor P5_j00 d100@-40: %.5f %% (book: 0.13392 at 64spp band)"
          % (100 * rec["panel"]["mean"]), flush=True)

    # P1/P2: the 2R law + grazing
    for r_surf, thetas in (
            (0.005, (0.0, 20.0, 40.0)),
            (0.01,  (0.0, 20.0, 40.0, -20.0, -40.0, 50.0, 70.0,
                    -50.0, -70.0)),
            (0.02,  (0.0, 20.0, 40.0))):
        ar = dict(AR_BASE, r_surface=r_surf)
        w = 0.0
        per = {}
        for th in thetas:
            tag = "P82_plate_R%03d_%+03.0f" % (r_surf * 1000, th)
            res = BR.run(hemi_job(tag, ENV, ar, th))
            rec = list(res["modes"].values())[0]
            record("P82_plate_R%03d" % (r_surf * 1000), "hemi_view",
                   r_surf, th, rec)
            if th in (0.0, 20.0, 40.0):
                w = max(w, rec["panel"]["mean"])
            per[th] = rec["panel"]["mean"]
        detail = "  ".join("%g:%.3f%%" % (t, 100 * v)
                           for t, v in sorted(per.items()))
        print("  R=%.1f%%  worst(0..-40) %.4f %%   [%s]"
              % (100 * r_surf, 100 * w, detail), flush=True)

    # P3: the danger scan, front camera
    ar = dict(AR_BASE, r_surface=0.01)
    print("  --- danger scan (angle mode, front camera, R 1%) ---")
    for th in (-60.0, -55.0, -50.0, -45.0, -40.0, -20.0, 0.0,
               20.0, 40.0, 50.0, 70.0):
        tag = "P82_scan_%+03.0f" % th
        res = BR.run(angle_job(tag, ENV, ar, th))
        rec = list(res["modes"].values())[0]
        record("P82_scan", "angle", 0.01, th, rec)
        print("    scan th %+5.1f  panel %.3e  ratio vs control %8.3f"
              % (th, rec["panel"]["mean"], rec["ratio_mean"]), flush=True)

    # P4: system with the pyramid trap at the back of the void
    ar = dict(AR_BASE, r_surface=0.01, backing="pyramid")
    w = 0.0
    for th in (0.0, 20.0, 40.0):
        tag = "P82_system_%+03.0f" % th
        res = BR.run(hemi_job(tag, ENV, ar, th))
        rec = list(res["modes"].values())[0]
        record("P82_system", "hemi_view", 0.01, th, rec, ar_used=ar)
        w = max(w, rec["panel"]["mean"])
    print("  system worst(0..+40) %.4f %%" % (100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))

    # P5: form at the deployment beam
    fout = {}
    print("\n=== form: P82_form_R10 (beam %.1f) ===" % FB.STRIPE_W,
          flush=True)
    entry = {"tag": "P82_form_R10", "family": "arplate",
             "topology": "arplate", "process": "glass",
             "params": ENV, "pitch": 4.0,
             "ar": dict(AR_BASE, r_surface=0.01)}
    rec = FB.run_case(entry)
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    rec["head_on"] = z["peak_ratio_mean"] if z else None
    rec["span_0"] = z["peak_ratio_span"] if z else None
    rec["stripe_w"] = FB.STRIPE_W
    fout["P82_form_R10"] = rec
    print("  smear(+-40) %s  head-on %s"
          % (rec["smear"], rec["head_on"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s" % FORMJSON)
    return 0


if __name__ == "__main__":
    sys.exit(main())
