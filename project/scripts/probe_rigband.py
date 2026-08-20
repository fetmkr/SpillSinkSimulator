"""Does the recommended panel hold at the angles the ROOM delivers?

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/probe_rigband.py

`principles/00` section C scores darkness at theta = 0 / +-20 / +-40, and the
whole honeycomb search was run and ranked in that band. The stated installation
-- a ring aimed up at 45 deg with a +-25 deg scan field -- puts light on the
panel between 20 and 70 deg instead, so most of what it throws arrives outside
the band the design was chosen in. README open item 1 is exactly this gap; the
geometry is now stated, so it can be closed.

Writes `results/rigband_hcflat.csv`, one row per angle, so the report quotes a
file rather than a transcript.

PRE-REGISTERED: rho_dh rises monotonically with incidence, because the coating
is Fresnel and metrics/01 quotes its flat plate rising 3.07x from 0 to 80 deg.
The question is whether the STRUCTURE holds that rise down -- if the panel
tracks the coating it is doing nothing at angle, and if it beats it the cells
are still trapping at 70 deg.
"""

from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import materials as MAT                                          # noqa: E402
import sim_server as S                                           # noqa: E402
import sweep_hcflat as SW                                        # noqa: E402
import report_geometry as G                                      # noqa: E402

ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "rigband_hcflat.csv")

PITCH, DEPTH, WALL, FRAC = 6.4, 64.0, 0.03, 0.15
THETAS = [0.0, 10.0, 20.0, 30.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0]
FIELDS = ["tag", "pitch", "depth", "wall", "paint_frac", "seed", "theta",
          "rho", "in_scored_band", "in_rig_band", "flat_coating_rho",
          "samples", "margin_depths", "params_json"]


def main():
    g = G.facts()
    coat = MAT.resolve(SW.SHALLOW)
    rows = []
    for seed in SW.SEEDS:
        spec = SW.spec_of(PITCH, DEPTH, WALL, seed)
        # > 50 deg needs the lock-grade skirt: gate 17's G5 measured margin 2.0
        # against 6.5 as agreeing to 0.08 % inside +-40 and diverging 5.05 %
        # beyond it, and this probe exists to look beyond it.
        spec["margin_depths"] = 6.5
        r = S.measure(spec, THETAS, 0.76, 0.30, SW.SPP, SW.SHALLOW,
                      deep_coating=SW.DEEP, paint_depth=FRAC * DEPTH,
                      deep_until=DEPTH - 1.0, paint_fade=0.0)
        rho = {float(k): float(v) for k, v in list(r.values())[0].items()}
        pj = json.dumps(spec, sort_keys=True)
        for th in THETAS:
            rows.append({
                "tag": "RIGBAND_p%04.1f_d%04.1f_w%04.2f_s%d"
                       % (PITCH, DEPTH, WALL, seed),
                "pitch": PITCH, "depth": DEPTH, "wall": WALL,
                "paint_frac": FRAC, "seed": seed, "theta": th,
                "rho": rho.get(th),
                "in_scored_band": int(abs(th) <= max(G.SCORED)),
                "in_rig_band": int(g["inc_lo"] <= th <= g["inc_hi"]),
                "flat_coating_rho": coat.rho_dh(th),
                "samples": SW.SPP, "margin_depths": 6.5, "params_json": pj})
        print("  seed %d done" % seed, flush=True)

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("\n  %-7s %-11s %-11s %s" % ("theta", "panel", "flat coating",
                                       "panel / flat"), flush=True)
    for th in THETAS:
        vs = [r["rho"] for r in rows if r["theta"] == th]
        m = sum(vs) / len(vs)
        fc = coat.rho_dh(th)
        print("  %-7.0f %-11.6f %-11.6f %.4f" % (th, m, fc, m / fc), flush=True)
    sc = max(sum(r["rho"] for r in rows if r["theta"] == t) / len(SW.SEEDS)
             for t in G.SCORED)
    rg = max(sum(r["rho"] for r in rows if r["theta"] == t) / len(SW.SEEDS)
             for t in THETAS if g["inc_lo"] <= t <= g["inc_hi"])
    print("\n  scored worst (0/20/40) %.6f" % sc, flush=True)
    print("  rig worst    (%.0f-%.0f)   %.6f   = %.2fx the scored figure"
          % (g["inc_lo"], g["inc_hi"], rg, rg / sc), flush=True)
    print("\nwrote %s" % CSV, flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
