"""
The standard metric table, from a form measurement.

    python3 scripts/metrics.py results/form_v2.json

Definitions and their known defects live in metrics/. This script only reads
what form_mtf already computed and puts it in one place, so that a report never
has to reach into the JSON and pick a field by hand -- which is how "core 0.11
vs 0.99" ended up quoting two designs that were not the ones being compared.

The headline it adds is the PEAK RADIANCE RATIO (metrics/04). Total return and
smear have been reported separately all along, but neither on its own answers
the actual question: is the copy of the artwork on the wall visible? That
depends on how bright its brightest point is, which folds both together --
spread the same energy over 4x the width and the peak drops 4x.

Panel and control are lit by the same stripe in the same frame (add_stripe is
given the full width, control included), so the ratio is in consistent units
and needs no calibration.
"""

from __future__ import annotations

import sys
import os
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FIELDS = [("peak_ratio", "peak vs flat wall", "%9.4f"),
          ("rms_mm", "smear rms (mm)", "%9.2f"),
          ("mtf_20mm", "MTF @20mm", "%9.2f"),
          ("energy_ratio", "total vs flat wall", "%9.4f")]


def rows(path):
    out = []
    for rec in json.load(open(path)):
        for th, d in rec["thetas"].items():
            p, c = d["panel"], d["control"]
            peak_ratio = (p["peak"] / c["peak"]) if c["peak"] > 0 else float("nan")
            out.append({
                "tag": rec["tag"], "theta": float(th),
                "peak_ratio": peak_ratio,
                "rms_mm": p["rms_mm"],
                "ctrl_rms_mm": c["rms_mm"],
                "mtf_20mm": p.get("mtf_20mm", float("nan")),
                "energy_ratio": d.get("energy_ratio", float("nan")),
            })
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "results", "form_v2.json")
    r = rows(path)
    thetas = sorted({x["theta"] for x in r})
    tags = []
    for x in r:
        if x["tag"] not in tags:
            tags.append(x["tag"])

    print("\nBaseline for every ratio: the 0.05 diffuse control plate in the "
          "same frame -- a plain matte black wall.\n")
    for th in thetas:
        print("theta %+.0f deg" % th)
        print("  %-22s %10s %9s %9s %9s"
              % ("design", "peak/flat", "rms mm", "MTF@20", "energy"))
        ctrl = None
        for tag in tags:
            x = next((y for y in r if y["tag"] == tag and y["theta"] == th),
                     None)
            if not x:
                continue
            ctrl = x["ctrl_rms_mm"]
            print("  %-22s %10.4f %9.2f %9.2f %9.4f"
                  % (tag, x["peak_ratio"], x["rms_mm"], x["mtf_20mm"],
                     x["energy_ratio"]))
        if ctrl:
            print("  %-22s %10.4f %9.2f %9s %9s"
                  % ("(flat wall, control)", 1.0, ctrl, "~1.0", "1.0"))
        print()

    out = os.path.join(ROOT, "results", "metrics_" +
                       os.path.basename(path).replace(".json", "") + ".json")
    json.dump(r, open(out, "w"), indent=2)
    print("wrote", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
