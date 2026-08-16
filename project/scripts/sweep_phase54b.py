"""Phase 5.4b: form protocol on the thin option (pitch 2 / depth 18).

    Blender --background --factory-startup --python scripts/sweep_phase54b.py

WHY THIS EXISTS AS A SECOND PASS. Phase 5.4's form runs surfaced that scale
invariance holds for TOTAL reflectance but NOT for form: the stripe is a
fixed 2 mm (form_buildable.STRIPE_W), so a 10 mm cell carries it on one flank
almost coherently (smear 1.27 vs the champion's 4.16). Form depends on pitch
RELATIVE TO THE BEAM, not on aspect. The p2/d18 field was swept for totals
only; its form numbers are now the deciding measurement for the build
recommendation.

    PREDICTIONS, numeric, before these renders.

    P6  p2/d18 SMEARS AT LEAST AS WELL AS THE CHAMPION: 2 mm cells sit fully
        inside the 2 mm stripe (5.5 mm cells only partly did) ->
        smear >= 4.2, band 4.2 - 6.5. Head-on stays pyramid-like:
        0.027 ± 0.008. Same for tip 0.1 (f 0.25 %, invisible).

    If P6 holds, the three-axis winner is p2/d18: best total measured at
    aspect 9 (0.130 %), champion-or-better smear, same head-on, 18 mm panel.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
FORMJSON = os.path.join(RESULTS, "form_phase54.json")

FACE = 60.0
BASE = {"kind": "pyramid", "face_w": FACE, "face_h": FACE,
        "margin_depths": 2.0, "backing": 2.0}
DESIGNS = [
    ("P54_p02_t00", dict(depth=18.0, pitch=2.0, tip_flat=0.0)),
    ("P54_p02_t01", dict(depth=18.0, pitch=2.0, tip_flat=0.1)),
]


def main():
    import form_buildable as FB
    fout = json.load(open(FORMJSON)) if os.path.exists(FORMJSON) else {}
    for tag, extra in DESIGNS:
        prm = dict(BASE, **extra)
        print("\n=== form: %s ===" % tag, flush=True)
        entry = {"tag": tag, "family": "floor", "topology": "pyramid",
                 "process": "press", "params": prm, "pitch": extra["pitch"]}
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["span_0"] = z["peak_ratio_span"] if z else None
        rec["winding"] = "out"
        fout[tag] = rec
        print("  smear %.3f  head-on %.5f  span@0 %.2fx"
              % (rec["smear"], rec["head_on"], rec["span_0"]), flush=True)
    json.dump(fout, open(FORMJSON, "w"), indent=1)
    print("wrote %s (%d designs)" % (FORMJSON, len(fout)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
