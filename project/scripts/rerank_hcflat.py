"""Re-rank the honeycomb search at a CONSTANT CELL COUNT, because the search
itself could not.

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/rerank_hcflat.py -- [--top 12] [--cells 25]

WHY THIS EXISTS. `sweep_hcflat` measures every design on the same 60 mm panel,
so the number of cells in the sample falls as the pitch rises:

    pitch  2.0  3.2  4.0  5.2  6.5  8.0 10.0 13.0 16.0
    cells 30.0 18.8 15.0 11.5  9.2  7.5  6.0  4.6  3.8

and GATE 11 of the 2026-08-20 audit measured what that does. Sweeping 5 / 10 /
25 / 50 cells, rho_dh fell monotonically -- 0.001096 / 0.001033 / 0.000995 /
0.000984 -- and was STILL falling at 50. A 10-cell sample reads about 5 % high
against a 25-cell one, and a 5-cell sample about 10 %.

THE SPREAD ACROSS PITCH IN THE SEARCH IS ABOUT 3 %. The bias is larger than the
effect. So the pitch ranking from a fixed 60 mm panel is not defensible, however
tight its seed-to-seed SEM looks, and a tight SEM on a biased measurement is
exactly the trap `NEXT.md` describes -- "the single-seed ranking put the top 13
designs inside 1.09x against a realisation spread of ~3.5%".

The bias runs AGAINST the coarse pitches, which is worth stating: they are
penalised more and still won, so the search's direction is probably right even
though its ORDER is not. This re-measures at a fixed cell count so the order can
be quoted.

    panel = cells x pitch,  so every design is sampled over the same number of
    cells and the only thing that differs is the design.

The cost is that the panel, and therefore the frame, grows with pitch. At 25
cells a pitch-8 design is a 200 mm panel. That is why this runs on the top few
rather than on the whole grid.

PRE-REGISTERED:
  R1  every design reads DARKER here than it did at 60 mm, because every one of
      them had fewer than 25 cells there.
  R2  the coarse pitches gain most, because they were the most under-celled.
  R3  the order changes. If it does not, the fixed-panel ranking was safe after
      all and that is worth knowing too.
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

import sim_server as S                                           # noqa: E402
import sweep_hcflat as SW                                        # noqa: E402

ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "rerank_hcflat.csv")

FIELDS = ["tag", "cells", "panel", "seed", "pitch", "depth", "wall",
          "paint_frac", "paint_mm", "shallow", "deep", "aspect", "tip_frac",
          "samples", "theta", "rho", "rho_at60", "params_json"]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    n_top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 12
    cells = float(argv[argv.index("--cells") + 1]) if "--cells" in argv else 25.0

    agg = SW.worst_by_design()
    if not agg:
        raise SystemExit("no rows in %s" % SW.CSV)
    picks = sorted(agg, key=lambda k: agg[k][0])[:n_top]

    done = set()
    if os.path.exists(CSV) and os.path.getsize(CSV) > 0:
        for r in csv.DictReader(open(CSV)):
            done.add(r["tag"])
    new = not os.path.exists(CSV) or os.path.getsize(CSV) == 0
    fh = open(CSV, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()

    print("rerank_hcflat: top %d designs at %.0f cells a side" % (len(picks),
                                                                  cells),
          flush=True)
    t0 = time.time()
    for (pitch, depth, wall, frac) in picks:
        panel = round(cells * pitch, 1)
        for seed in SW.SEEDS:
            tag = "RR_p%04.1f_d%04.1f_w%04.2f_f%03.0f_s%d" % (
                pitch, depth, wall, 100 * frac, seed)
            if tag in done:
                continue
            spec = SW.spec_of(pitch, depth, wall, seed)
            spec["panel"] = panel
            pd = float(frac) * float(depth)
            try:
                r = S.measure(spec, SW.THETAS, 0.76, 0.30, SW.SPP, SW.SHALLOW,
                              deep_coating=SW.DEEP, paint_depth=pd,
                              deep_until=float(depth) - 1.0, paint_fade=0.0)
            except Exception as exc:
                print("  [FAIL] %s  %s: %s" % (tag, type(exc).__name__, exc),
                      flush=True)
                continue
            inner = list(r.values())[0]
            rho = {float(k): float(v) for k, v in inner.items()}
            pj = json.dumps(spec, sort_keys=True)
            for th in SW.THETAS:
                w.writerow({"tag": tag, "cells": cells, "panel": panel,
                            "seed": seed, "pitch": pitch, "depth": depth,
                            "wall": wall, "paint_frac": frac, "paint_mm": pd,
                            "shallow": SW.SHALLOW, "deep": SW.DEEP,
                            "aspect": depth / pitch,
                            "tip_frac": 2 * wall / pitch, "samples": SW.SPP,
                            "theta": th, "rho": rho.get(th),
                            "rho_at60": agg[(pitch, depth, wall, frac)][0],
                            "params_json": pj})
            fh.flush()
            done.add(tag)
        el = time.time() - t0
        print("  p%.1f d%.0f w%.2f  panel %.0f mm  (%.0f s elapsed)"
              % (pitch, depth, wall, panel, el), flush=True)
    fh.close()

    # --- score and compare
    per = {}
    for r in csv.DictReader(open(CSV)):
        if not r.get("rho"):
            continue
        k = (float(r["pitch"]), float(r["depth"]), float(r["wall"]),
             float(r["paint_frac"]), int(r["seed"]))
        per[k] = max(per.get(k, 0.0), float(r["rho"]))
    out = {}
    for (p, d, wl, f, s), v in per.items():
        out.setdefault((p, d, wl, f), []).append(v)

    print("\n=== ranking at %.0f cells, against the 60 mm ranking ===" % cells,
          flush=True)
    print("  %-6s %-6s %-6s %-6s %-7s %-11s %-11s %-8s %s"
          % ("pitch", "depth", "wall", "paint", "panel", "rho@25cells",
             "rho@60mm", "change", "cells@60"), flush=True)
    rows = []
    for k, vs in out.items():
        m = sum(vs) / len(vs)
        rows.append((m, k, agg.get(k, (float("nan"),))[0]))
    for m, (p, d, wl, f), old in sorted(rows):
        print("  %-6.2f %-6.1f %-6.2f %-6.0f %-7.0f %-11.6f %-11.6f %+7.1f %% %.1f"
              % (p, d, wl, 100 * f, cells * p, m, old, 100 * (m - old) / old,
                 SW.FACE / p), flush=True)
    print("\nwrote %s" % CSV, flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
