"""The winners of the honeycomb search, as angle-in / angle-out maps.

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/report_hcflat.py -- [--top 6] [--step 20]

`sweep_hcflat` ranks on one scalar -- worst rho_dh -- and metric 01 says in its
own file what that scalar cannot see: WHERE the light goes. These are the same
designs read with metric 08, so the ranking and the redistribution sit beside
each other.

THE MATERIAL IS THE SEARCH'S MATERIAL, not the study default. Musou above the
paint line, anodised_hi below it, Musou again at the floor, driven through the
same `paint_depth` / `deep_coating` / `deep_until` keys `sweep_hcflat` uses --
`bidir.build` passes them straight to `build_scene` through `extra`. A map drawn
with a different finish from the search that selected the design would not be a
picture of that design.

EVERY PANEL SHARES ONE COLOUR SCALE. One LogNorm over every cell of every
design, so a colour means the same BRDF wherever it appears and the panels can
be compared to each other and to the flat plate. A per-panel normalisation makes
the darkest design look exactly like the brightest.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bidir as BD                                               # noqa: E402
import materials as MAT                                          # noqa: E402
import sweep_hcflat as SW                                        # noqa: E402

ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUT = "/tmp/simsrv/hcmap"
SPP = 128

# THE MAP COVERS THE SCORING BAND, NOT GRAZING, and that is a cost decision
# stated rather than hidden. Gate 17's G5 measured margin_depths 2.0 against
# 6.5 on the order-spec pyramid: they agree to 0.08 % inside +-40 deg and
# diverge 5.05 % beyond it. Staying inside +-40 therefore keeps margin 2.0
# honest, and margin 6.5 on a depth-80 cell is a 520 mm skirt -- a frame five
# times wider than the sample, for angles outside the band the study scores on.
LIMIT = 40.0


def top_designs(n):
    agg = SW.worst_by_design()
    if not agg:
        raise SystemExit("no rows in %s -- run sweep_hcflat first" % SW.CSV)
    best = sorted(agg, key=lambda k: agg[k][0])[:n]
    return [(k, agg[k]) for k in best]


def build_for(pitch, depth, wall, frac, seed=23):
    """The search's geometry AND the search's three-band finish."""
    params = {"topology": "honeycomb", "pitch": float(pitch),
              "wall_top": float(wall), "wall_bot": float(wall),
              "jitter": 0.3, "cell_lean_domain": 16.0,
              "depth": float(depth), "face_w": SW.FACE, "face_h": SW.FACE,
              "backing": 2.0, "seed": int(seed),
              "margin_depths": BD.margin_for([-LIMIT, LIMIT], [-LIMIT, LIMIT])}
    deep = MAT.resolve(SW.DEEP)
    body, spec_scale = deep.split()
    extra = {"paint_depth": float(frac) * float(depth),
             "deep_coating": {"body": body, "spec_scale": spec_scale},
             "deep_until": float(depth) - 1.0,
             "paint_fade": 0.0}
    return BD.build(params, material=SW.SHALLOW, samples=SPP, family="topo",
                    extra=extra), params


def sweep_one(tag, pitch, depth, wall, frac, ins, outs, sun):
    path = os.path.join(RESULTS, "sweep_bidir_%s.csv" % tag)
    done = set()
    if os.path.exists(path) and os.path.getsize(path) > 0:
        for r in csv.DictReader(open(path)):
            done.add((round(float(r["theta_in"]), 3),
                      round(float(r["theta_out"]), 3)))
    todo = [(a, b) for a in ins for b in outs
            if (round(a, 3), round(b, 3)) not in done]
    if not todo:
        print("    %s already complete" % tag, flush=True)
        return path
    sc, params = build_for(pitch, depth, wall, frac)
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    fh = open(path, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=SW_FIELDS)
    if new:
        w.writeheader()
    pj = json.dumps(params, sort_keys=True)
    want = set(todo)
    t0, n = time.time(), 0
    for rec in BD.sweep(sc, ins, outs, sun_angle_deg=sun,
                        skip=lambda a, b: (a, b) not in want, out_dir=OUT):
        row = {k: rec.get(k) for k in SW_FIELDS if k in rec}
        row.update(tag=tag, family="topo", topology="honeycomb", phi=0.0,
                   seed=23, margin_depths=params["margin_depths"],
                   params_json=pj)
        w.writerow(row)
        fh.flush()
        n += 1
    fh.close()
    print("    %s  %d cells  %.1f s/cell" % (tag, n, (time.time() - t0) / n),
          flush=True)
    return path


import sweep_bidir as SB                                         # noqa: E402
SW_FIELDS = SB.FIELDS


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    n_top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 6
    step = float(argv[argv.index("--step") + 1]) if "--step" in argv else 10.0
    global LIMIT
    LIMIT = float(argv[argv.index("--limit") + 1]) if "--limit" in argv else 40.0

    ins, outs = BD.grid(step, in_limit=LIMIT, out_limit=LIMIT)
    sun = BD.default_sun_angle(ins)
    picks = top_designs(n_top)

    print("report_hcflat: %d designs x %d x %d cells, sun %.0f deg"
          % (len(picks), len(ins), len(outs), sun), flush=True)
    print("  %s above the paint line, %s below, %s at the floor"
          % (SW.SHALLOW, SW.DEEP, SW.SHALLOW), flush=True)

    made = []
    for (pitch, depth, wall, frac), (rho, sem, nseed) in picks:
        tag = "hc_p%04.1f_d%04.1f_w%04.2f_f%03.0f" % (pitch, depth, wall,
                                                      100 * frac)
        print("\n  %s   rho_worst %.6f +- %.6f" % (tag, rho, sem), flush=True)
        made.append(sweep_one(tag, pitch, depth, wall, frac, ins, outs, sun))

    with open(os.path.join(RESULTS, "hcflat_map_set.json"), "w") as fh:
        json.dump({"csvs": made,
                   "designs": [{"pitch": k[0], "depth": k[1], "wall": k[2],
                                "paint_frac": k[3], "rho_worst": v[0],
                                "sem": v[1], "seeds": v[2]}
                               for k, v in picks],
                   "shallow": SW.SHALLOW, "deep": SW.DEEP,
                   "step": step, "samples": SPP}, fh, indent=1)
    print("\nwrote results/hcflat_map_set.json", flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
