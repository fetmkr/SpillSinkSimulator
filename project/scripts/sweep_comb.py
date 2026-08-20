"""
The honeycomb you can actually buy, swept over pitch, foil and expansion.

    Blender --background --factory-startup --python scripts/sweep_comb.py

WHY THIS EXISTS. `geom_topo._build_honeycomb` tessellates JITTERED points, so
every cell is a different shape. No supplier sells that. Aluminium honeycomb is
made by bonding foil ribbons at intervals and pulling the stack open, which can
only produce identical cells. Every number quoted for "the honeycomb you can
buy" has to come from `comb`, not from `honeycomb`.

WHY IT WAS REWRITTEN, 2026-08-14. The original script was lost, and the CSV it
produced turned out to be void anyway: `_build_comb` stepped the lattice along
the wrong two axes, so no cell shared an edge with any neighbour and 30.1 % of
the panel face belonged to no cell at all -- open channels straight down to the
flat backing slab. The render still looked like a honeycomb. The grid below is
reconstructed from the voided CSV's `params_json` so the new numbers are
directly comparable to the old ones, design for design.

ON "SEEDS". `comb` has jitter 0 because the product is periodic, so all three
seeds build the identical mesh. The spread across them is Cycles sampling
noise, NOT realisation spread, and must not be reported as the latter. It is
kept at three because every downstream analyser expects three and because a
noise floor is worth having.

Scoring identical to the rest of phase 2: worst rho_dh over theta 0/+-20/+-40,
then worst over the three coating models.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import done_tags, shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
import geom_topo as GT                                             # noqa: E402
from cone3d_sweep import COAT                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "comb")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_comb.csv"))

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH = 50.0
MARGIN = 2.0
SEEDS = (23, 101, 102)

# (pitch mm, foil mm). The foil floor the user set is 0.05-0.1 mm for a panel
# that survives being handled; 0.04 is below it and is carried as the
# thin-foil reference only -- `analyze_buildable.PROCESS_FLOOR` marks it.
GRID = [(3.17, 0.04), (5.20, 0.04), (6.50, 0.08),
        (6.50, 0.10), (8.47, 0.08), (9.53, 0.10)]
EXPANDS = (1.0, 1.3)        # fully expanded, and over-expanded

FIELDS = ["tag", "topology", "process", "feature", "seed", "diffuse_frac",
          "pitch", "depth", "aspect", "exposed_est", "theta", "rho",
          "control", "params_json"]


def designs():
    out = []
    for seed in SEEDS:
        for pitch, foil in GRID:
            for ex in EXPANDS:
                out.append((
                    "CB_p%04d_f%03d_x%02d_s%02d"
                    % (pitch * 100, foil * 1000, ex * 10, seed),
                    dict(topology="comb", face_w=FACE, face_h=FACE,
                         depth=DEPTH, pitch=pitch, wall_top=foil,
                         wall_bot=foil, jitter=0.0, comb_expand=ex,
                         margin_depths=MARGIN, backing=2.0, seed=seed),
                    foil))
    return out


def open_append(path, fields):
    """Append to `path`, but ONLY if its header is exactly `fields`.

    `csv.DictWriter` does not compare its fieldnames against the header already
    on disk. Adding one column to FIELDS and re-running a resumable sweep
    therefore appends 22-column rows under a 21-column header, and every later
    `DictReader` silently shifts each new row by one -- `rho` reads a `theta`,
    and nothing anywhere raises. That happened here on 2026-08-14 with
    `tube_kind`; the rows were recoverable only because the two widths were
    distinguishable by length.

    A schema change is a new file or a migration, never an append.
    """
    import csv as _csv
    if os.path.exists(path):
        with open(path) as fh:
            have = next(_csv.reader(fh), None)
        if have is not None and have != list(fields):
            raise SystemExit(
                "%s has header\n  %s\nbut this script writes\n  %s\n"
                "Appending would shift every new row. Migrate the file or "
                "write a new one." % (os.path.basename(path),
                                      ",".join(have), ",".join(fields)))
        new = False
    else:
        new = True
    fh = open(path, "a", newline="")
    w = _csv.DictWriter(fh, fieldnames=list(fields))
    if new:
        w.writeheader()
        fh.flush()
    return fh, w


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)

    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[COMB] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for tag, prm, foil in grid:
        p = GT.TopoParams(**prm)
        est = p.exposed_fraction_est()
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            # another shard is measuring this design; NSHARD unset makes
            # take() always true, so an unsharded run is unchanged
            if not take(tag):
                continue
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": "topo",
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True, "spec_roughness": 0.30,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": 0.30},
                   "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": t}
                               for t in THETAS]}
            cfg.update({k: v for k, v in COAT.items()
                        if k not in ("spec_roughness",)})
            cfg["material_mode"] = "coating"
            try:
                res = BR.run(cfg)
            except Exception as e:
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            pj = json.dumps(prm, sort_keys=True, default=str)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "topology": "comb",
                            "process": "expanded foil", "feature": foil,
                            "seed": prm["seed"], "diffuse_frac": mname,
                            "pitch": p.pitch, "depth": DEPTH,
                            "aspect": DEPTH / p.pitch, "exposed_est": est,
                            "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            if n % 9 == 0:
                el = time.time() - t0
                print("[%3d/%3d] %-26s eta %4.0fs"
                      % (n, total, tag, el / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
