"""Phase 5.5: how the form axes depend on the probe beam width.

    Blender --background --factory-startup --python scripts/sweep_phase55.py

WHY. Phase 5.4's law "the cell must be no coarser than the beam" hangs on
STRIPE_W = 2.0 mm, which is a protocol assumption, not a measurement of the
real laser footprint at the wall. The user flagged it: the real beam may be
bigger. Total reflectance never sees the beam (hemispherical, by
reciprocity); smear / head-on / span are all conditioned on it. This sweep
turns the single 2 mm column into a map: stripe width 2 / 5 / 10 mm x pitch
2 / 5.5 / 10, so when the real beam IS measured, the allowed pitch can be
read off a curve instead of re-simulated.

Existing width-2 anchors (form_pyr.json, form_phase54.json):
    p5.5/d50 smear 4.159   p10/d90 smear 1.272   p2/d18 smear 4.104

    PREDICTIONS, numeric, before any render. The organising variable is
    R = stripe_width / pitch. Anchors: R 0.20 -> 1.27, R 0.36 -> 4.16,
    R 1.00 -> 4.10. The jump between 0.20 and 0.36 says the transition is
    steep and lives near R ~ 0.3.

    P1  SMEAR COLLAPSES ONTO R: at equal R, different pitches read the
        same smear within 15 %.
        p10  w5   (R 0.50)  smear 4.2 ± 0.8
        p10  w10  (R 1.00)  smear 4.1 ± 0.8   (matches p2/w2's 4.10)
        p5.5 w5   (R 0.91)  smear 4.2 ± 0.8
        p5.5 w10  (R 1.82)  smear 4.2 ± 1.0
        p2   w5   (R 2.50)  smear 4.4 ± 1.0
        p2   w10  (R 5.00)  smear 4.4 ± 1.0
        i.e. above R ~ 0.5 the curve is FLAT near 4.2; only the p10/w2
        point (R 0.20) sits in the cliff.

    P2  HEAD-ON MEAN IS BEAM-INDEPENDENT for sharp fields: every design
        stays at its width-2 value ± 30 % at all widths (the peak ratio is
        normalised by the control's own peak, which widens identically).

    P3  SPAN STAYS DEAD (< 1.2x) for all sharp fields at every width —
        phase uniformity is a property of the doubly-closed cell, not of
        the beam.

    CONSEQUENCE IF P1 HOLDS: the build rule becomes pitch <= 2x the real
    beam width (R >= 0.5). A 5 mm beam admits pitch 10; a 10 mm beam
    admits pitch 20. The fine-pitch tip problem then evaporates with the
    coarse pitch it forced.

Runs: 6 (three width-2 columns already measured; they are the anchors and
gate-8-style overlap for this JSON).
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
FORMJSON = os.path.join(RESULTS, "form_phase55.json")

FACE = 60.0
P0 = 5.500550055005501
DESIGNS = {
    "p02": dict(depth=18.0, pitch=2.0, tip_flat=0.0),
    "p55": dict(depth=50.0, pitch=P0, tip_flat=0.0),
    "p10": dict(depth=90.0, pitch=10.0, tip_flat=0.0),
}
BASE = {"kind": "pyramid", "face_w": FACE, "face_h": FACE,
        "margin_depths": 2.0, "backing": 2.0}
WIDTHS = (5.0, 10.0)


def main():
    import form_buildable as FB
    fout = json.load(open(FORMJSON)) if os.path.exists(FORMJSON) else {}
    for w in WIDTHS:
        FB.STRIPE_W = w
        for name, extra in DESIGNS.items():
            tag = "P55_%s_w%02.0f" % (name, w)
            prm = dict(BASE, **extra)
            print("\n=== form: %s (stripe %.0f mm) ===" % (tag, w),
                  flush=True)
            entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                     "process": "press", "params": prm,
                     "pitch": extra["pitch"]}
            rec = FB.run_case(entry)
            t = rec.get("thetas", {})
            a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
            rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                                   + b["rms_mm"] / b["rms_control_mm"])
                            if a and b else None)
            rec["head_on"] = z["peak_ratio_mean"] if z else None
            rec["span_0"] = z["peak_ratio_span"] if z else None
            rec["stripe_w"] = w
            rec["winding"] = "out"
            fout[tag] = rec
            print("  smear %.3f  head-on %.5f  span@0 %.2fx"
                  % (rec["smear"], rec["head_on"], rec["span_0"]),
                  flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s (%d entries)" % (FORMJSON, len(fout)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
