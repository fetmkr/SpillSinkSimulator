"""How bright is the ceiling to a person standing under it?

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/measure_audience.py

THE TOP-LINE NUMBER OF THE WHOLE STUDY, and it is not rho_dh. rho_dh is a
hemispherical total: the fraction of an arriving beam that leaves in ANY
direction. It ranks absorbers and it says nothing about how visible the spill
copy is. What a client asks is how bright the ceiling looks, and that is
directional.

THREE ANGLES, NOT TWO. The first version of this script measured
(theta_in, theta_out) with both positive, which in this rig's convention is the
RETRO side of the map for every cell -- the side a honeycomb is brightest on --
while only 24.5 % of the light an eye receives arrives there. It published
beta = 0.0037 and the wrong conclusion. Corrected 2026-08-21:
`results/FINDINGS_audience_azimuth_2026_08_21.md`.

Measures the BRDF over the (incidence, observation, azimuth) cells the room
actually uses -- `audience.cells()` says which -- then reports, for every
surface:

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
from collections import defaultdict

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

FIELDS = ["surface", "kind", "theta_in", "theta_out", "delta_phi", "brdf",
          "beta", "weight", "samples", "params_json"]

# Cells below this share of the room's light are not rendered. Whatever is
# dropped is REPORTED, because a mean over 90 % of the light is not a mean.
WEIGHT_FLOOR = 0.0015


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
    w = AUD.cells()
    todo = sorted((k for k, v in w.items() if v >= WEIGHT_FLOOR),
                  key=lambda k: -w[k])
    kept = sum(w[k] for k in todo)
    sun = 10.0
    print("  %d of %d cells carry >= %.2f %% each; together %.1f %% of the "
          "light. The remaining %.1f %% is not rendered."
          % (len(todo), len(w), 100 * WEIGHT_FLOOR, 100 * kept,
             100 * (1 - kept)), flush=True)
    # The Lambertian references need no renderer: for a Lambertian beta = rho
    # exactly, at every angle and every azimuth, and gate az proved this rig
    # returns that to 0.000 %. They are measured anyway, because a reference
    # that goes through a different path is not a reference.
    jobs = [("panel", "honeycomb 6.4/64/0.03, Musou to 15 %", panel_scene),
            ("flat_musou", "flat plate, its own Musou coating",
             lambda: flat_scene("musou_fit")),
            ("black_velour", "black velour (Lambertian model, rho 0.002)",
             lambda: flat_scene("black_velour")),
            ("white_paper", "white paper (Lambertian model, rho 0.80)",
             lambda: flat_scene("white_paper"))]

    # RESUMABLE, AND WRITTEN AS IT GOES. The first attempt held every row in
    # memory and wrote at the end; the process was killed after the panel's ten
    # minutes and all of it was lost. A surface already complete in the CSV is
    # skipped.
    done = defaultdict(dict)
    if os.path.exists(CSV) and os.path.getsize(CSV) > 0:
        for r in csv.DictReader(open(CSV)):
            if r.get("brdf") and r.get("delta_phi"):
                done[r["surface"]][(float(r["theta_in"]),
                                    float(r["theta_out"]),
                                    float(r["delta_phi"]))] = float(r["brdf"])
    fresh = not os.path.exists(CSV) or os.path.getsize(CSV) == 0 or not done
    fh = open(CSV, "a" if not fresh else "w", newline="")
    wr = csv.DictWriter(fh, fieldnames=FIELDS)
    if fresh:
        wr.writeheader()

    rows, res = [], {}
    for tag, kind, make in jobs:
        if len(done.get(tag, {})) >= len(todo):
            brdf = done[tag]
            mean, peak, cov = AUD.score(brdf)
            res[tag] = (mean, peak, cov, kind)
            print("  %-13s already measured: beta mean %.6f  peak %.6f"
                  % (tag, mean, peak), flush=True)
            continue
        t0 = time.time()
        sc, params = make()
        pj = json.dumps(params, sort_keys=True, default=str)
        brdf = dict(done.get(tag, {}))
        for (a, b, ph) in todo:
            if (a, b, ph) in brdf:
                continue
            r = BD.cell(sc, a, b, sun, out_dir=OUT, phi_deg=ph)
            brdf[(a, b, ph)] = r["brdf"]
            wr.writerow({"surface": tag, "kind": kind, "theta_in": a,
                         "theta_out": b, "delta_phi": ph, "brdf": r["brdf"],
                         "beta": math.pi * r["brdf"], "weight": w[(a, b, ph)],
                         "samples": SPP, "params_json": pj})
            fh.flush()
        mean, peak, cov = AUD.score(brdf)
        res[tag] = (mean, peak, cov, kind)
        print("  %-13s beta mean %.6f  peak %.6f  (%.0f %% of the light, "
              "%.0f s)" % (tag, mean, peak, 100 * cov, time.time() - t0),
              flush=True)

    fh.close()

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
