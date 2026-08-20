"""How bright is the ceiling to a person standing under it?

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/measure_audience.py

THE TOP-LINE NUMBER OF THE WHOLE STUDY, and it is not rho_dh. rho_dh is a
hemispherical total: the fraction of an arriving beam that leaves in ANY
direction. It ranks absorbers and it says nothing about how visible the spill
copy is. What a client asks is how bright the ceiling looks, and that is
directional.

Measures the BRDF over the (incidence, observation) cells the room actually
uses -- `audience.cells()` says which, and they are theta_in 20-70 against
theta_out 0-70 -- then reports, for every surface:

    RADIANCE FACTOR beta = pi * f_r      1.0 = a perfect Lambertian white
    x WHITE PAPER   beta / 0.80          paper is 75-85 % and near-Lambertian
    x BLACK VELOUR  beta / 0.002         theatrical blackout, the thing this
                                         replaces

Four surfaces, all through the identical rig so the ratios are like-for-like:
the recommended panel, a flat plate of its own Musou coating, black velour and
white paper. The last two are LAMBERTIAN MODELS -- for a Lambertian, beta =
rho exactly at every angle -- so they double as a check that the rig returns
the answer it is given.

Writes `results/audience.csv`, one row per surface per cell.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import audience as AUD                                           # noqa: E402
import bidir as BD                                               # noqa: E402
import materials as MAT                                          # noqa: E402
import sweep_hcflat as SW                                        # noqa: E402

ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "audience.csv")
OUT = "/tmp/simsrv/audience"
SPP = 128
PITCH, DEPTH, WALL, FRAC = 6.4, 64.0, 0.03, 0.15

FIELDS = ["surface", "kind", "theta_in", "theta_out", "brdf", "beta",
          "weight", "samples", "params_json"]


def panel_scene():
    params = {"topology": "honeycomb", "pitch": PITCH, "wall_top": WALL,
              "wall_bot": WALL, "jitter": 0.3, "cell_lean_domain": 16.0,
              "depth": DEPTH, "face_w": SW.FACE, "face_h": SW.FACE,
              "backing": 2.0, "seed": 23, "margin_depths": 6.5}
    deep = MAT.resolve(SW.DEEP)
    body, ss = deep.split()
    extra = {"paint_depth": FRAC * DEPTH,
             "deep_coating": {"body": body, "spec_scale": ss},
             "deep_until": DEPTH - 1.0, "paint_fade": 0.0}
    return BD.build(params, material=SW.SHALLOW, samples=SPP, family="topo",
                    extra=extra), params


def flat_scene(mat):
    params, extra = BD.flat_plate(100.0)
    return BD.build(params, material=mat, samples=SPP, family="stack",
                    extra=extra), params


def main():
    ins, outs = AUD.axes()
    w = AUD.cells()
    sun = 10.0
    jobs = [("panel", "honeycomb 6.4/64/0.03, Musou to 15 %", panel_scene),
            ("flat_musou", "flat plate, its own Musou coating",
             lambda: flat_scene("musou_fit")),
            ("black_velour", "black velour (Lambertian model, rho 0.002)",
             lambda: flat_scene("black_velour")),
            ("white_paper", "white paper (Lambertian model, rho 0.80)",
             lambda: flat_scene("white_paper"))]

    rows, res = [], {}
    for tag, kind, make in jobs:
        t0 = time.time()
        sc, params = make()
        pj = json.dumps(params, sort_keys=True, default=str)
        brdf = {}
        for a in ins:
            for b in outs:
                if w.get((a, b), 0.0) <= 0.0:
                    continue                 # the room never uses this cell
                r = BD.cell(sc, a, b, sun, out_dir=OUT)
                brdf[(a, b)] = r["brdf"]
                rows.append({"surface": tag, "kind": kind, "theta_in": a,
                             "theta_out": b, "brdf": r["brdf"],
                             "beta": math.pi * r["brdf"], "weight": w[(a, b)],
                             "samples": SPP, "params_json": pj})
        mean, peak, cov = AUD.score(brdf)
        res[tag] = (mean, peak, cov, kind)
        print("  %-13s beta mean %.6f  peak %.6f  (%.0f %% of the light, "
              "%.0f s)" % (tag, mean, peak, 100 * cov, time.time() - t0),
              flush=True)

    with open(CSV, "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=FIELDS)
        wr.writeheader()
        for r in rows:
            wr.writerow(r)

    print("\n=== REFLECTANCE AT THE AUDIENCE ===", flush=True)
    print("radiance factor beta: 1.000 = a perfect Lambertian white\n",
          flush=True)
    print("  %-13s %-11s %-11s %-14s %s"
          % ("surface", "beta mean", "beta peak", "x white paper",
             "x black velour"), flush=True)
    vel = res["black_velour"][0]
    for tag, _kind, in ((t, k) for t, (_m, _p, _c, k) in res.items()):
        m, pk, _c, _k = res[tag]
        print("  %-13s %-11.6f %-11.6f 1/%-12.0f %.3f"
              % (tag, m, pk, 1.0 / AUD.as_paper(m) if m > 0 else 0, m / vel),
              flush=True)
    pm = res["panel"][0]
    print("\n  the panel is %.2fx black velour and 1/%.0f of white paper "
          "at the audience" % (pm / vel, 1.0 / AUD.as_paper(pm)), flush=True)
    print("wrote %s" % CSV, flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
