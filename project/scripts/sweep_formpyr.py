"""Form and head-on for the corrected top designs, with oriented geometry.

    Blender --background --factory-startup --python scripts/sweep_formpyr.py

WHY NOW. The winding fix rewrote the total-reflectance ranking: sharp pyramid
0.134 %, truncated 0.172 %, blade+pyramid stack 0.184 %, cone 0.215 %. But the
design is decided on three axes, and the other two -- form destruction and
head-on brightness -- have never been measured for the pyramids at all, and
were measured for the cone and the stack on inside-out geometry with a
specular-weighted coating (a bias of the d76 order, ~15 %). This runs the
published protocol (`form_buildable.run_case`, 16 phases x 512 spp, theta
0/+-40) on the four designs the decision now rests on.

ANCHORS. The cone and the stack have published form numbers in
`form_buildable.json`; re-measuring them with fixed winding both anchors this
file and quantifies the winding bias on the form axes -- predicted direction
and rough size below, before the render.

    PREDICTION, written before any render.

    1. WINDING BIAS ON THE ANCHORS: head-on peak DROPS for the cone and the
       stack, by 5-25 %. The inward winding inflated specular return, and the
       head-on peak at theta 0 is the most specular quantity in the protocol.
       Smear moves less -- it is a ratio of widths, both measured on the same
       frame, so the bias largely divides out. If smear moves more than ~10 %
       something other than winding is at work and this file cannot be an
       anchor.

    2. THE SHARP PYRAMID IS COMPETITIVE HEAD-ON: a point presents no area to
       the viewer. Predict head-on peak within 2x of the cone's re-measured
       value, and BELOW the stack's.

    3. THE SHARP PYRAMID IS *WORSE* ON SMEAR THAN THE STACK. Its facets are
       flat mirrors at fixed angles: a stripe at +-40 reflects into a defined
       direction rather than being scattered by jittered blades. Predict the
       pyramid's smear ratio at least 25 % worse (closer to 1 = worse
       destruction) than the stack's. This is the axis the periodic pyramid
       should lose, and if it does not, the two-layer stack has no remaining
       advantage and the whole design conversation changes.

    4. THE TRUNCATED PYRAMID IS CLEARLY WORSE HEAD-ON than the sharp one --
       its flat top faces the viewer at one bounce. Predict at least 2x the
       sharp pyramid's head-on peak. If truncation is cheap here too, the
       press-friendly part wins the manufacturability argument outright.

Output is `results/form_pyr.json` (form protocol, not a rho sweep, so gate
check 8 does not parse it; the anchor comparison against
`form_buildable.json` is printed and recorded instead).
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUTJSON = os.path.join(RESULTS, "form_pyr.json")

FACE, DEPTH = 60.0, 50.0

DESIGNS = [
    ("cone_p550", "cone3d", 5.5,
     {"face_w": FACE, "face_h": FACE, "depth": DEPTH, "pitch": 5.5,
      "tip_radius": 0.2, "jitter": 0.30, "radial_seg": 24, "height_seg": 12,
      "depth_jitter": 0.0, "profile_power": 1.0, "margin_depths": 2.0,
      "backing": 2.0, "seed": 23}),
    ("stack_blade_pyr", "stack", 5.5,
     {"backing": 2.0, "bot": "pyramid", "bot_depth": 3.0,
      "bot_params": {"margin_depth_ref": 50.0, "pitch": 2.0, "tip_flat": 0.1},
      "face_h": FACE, "face_w": FACE, "margin_depths": 2.0, "seed": 23,
      "top": "shingle", "top_depth": 47.0,
      "top_params": {"azimuth_mode": "grid", "jitter": 0.3, "pitch": 5.5,
                     "plate_over": 1.15, "plate_t_bot": 0.05,
                     "plate_t_top": 0.05, "tilt_deg": 2.0,
                     "tilt_jitter": 0.0}}),
    ("pyr_sharp_a909", "floor", 5.5006,
     {"kind": "pyramid", "face_w": FACE, "face_h": FACE, "depth": DEPTH,
      "pitch": 5.500550055005501, "tip_flat": 0.0, "margin_depths": 2.0,
      "backing": 2.0}),
    ("pyr_trunc_a909", "floor", 5.5006,
     {"kind": "pyramid", "face_w": FACE, "face_h": FACE, "depth": DEPTH,
      "pitch": 5.500550055005501, "tip_flat": 1.1001100110011002,
      "margin_depths": 2.0, "backing": 2.0}),
]


def main():
    import form_buildable as FB
    out = {}
    pub = {}
    try:
        pub = json.load(open(os.path.join(RESULTS, "form_buildable.json")))
    except Exception:
        pass

    for tag, family, pitch, prm in DESIGNS:
        print("\n=== %s (%s) ===" % (tag, family), flush=True)
        entry = {"tag": tag, "family": family, "topology": tag,
                 "process": "n/a", "params": prm, "pitch": pitch}
        rec = FB.run_case(entry)
        t = rec.get("thetas", {})
        a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
        rec["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                               + b["rms_mm"] / b["rms_control_mm"])
                        if a and b else None)
        rec["head_on"] = z["peak_ratio_mean"] if z else None
        rec["winding"] = "out"
        out[tag] = rec
        print("  smear %.4f   head-on %.5f"
              % (rec["smear"], rec["head_on"]), flush=True)

    json.dump(out, open(OUTJSON, "w"), indent=1)
    print("\nwrote %s" % OUTJSON)

    # anchor comparison against the published (inside-out) form numbers
    print("\n  anchors vs published form_buildable.json:")
    for tag, pubtag in (("cone_p550", None), ("stack_blade_pyr", None)):
        # find the published record whose params match closest by name
        cand = [k for k in pub if "CONE" in k.upper()] if "cone" in tag else \
               [k for k in pub if "SHIN" in k.upper() or "ST_" in k]
        for k in cand[:3]:
            t = pub[k].get("thetas", {})
            a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
            if not (a and b and z):
                continue
            sm = 0.5 * (a["rms_mm"] / a["rms_control_mm"]
                        + b["rms_mm"] / b["rms_control_mm"])
            print("   pub %-26s smear %.4f  head-on %.5f"
                  % (k, sm, z["peak_ratio_mean"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
