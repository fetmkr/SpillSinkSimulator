"""
Rank sweep_topo.csv, render the top N designs, and dump everything a report
needs into one JSON.

    Blender --background --factory-startup --python scripts/report_top10.py
    TOPN=10 Blender --background --factory-startup --python scripts/report_top10.py

Each design is rebuilt from the `params_json` column, which is why that column
exists: the CSV row IS the design, so a ranking can be turned back into
geometry without a lookup table that can drift out of step with the results.

Two deliberate choices, both stated in the report so a reader is not misled:

* **`margin_depths` is overridden to 0.2 for the pictures.** A measurement build
  needs 6.5 depths of geometry past the window or a tilted camera runs off the
  tile and reads world background. A portrait wants the tile and nothing else.
  The optical numbers come from the sweep, never from these renders.
* **One design per topology family is forced into the set** even if it does not
  make the top N, so the sheet compares FAMILIES and not just the head of one
  family's parameter sweep. A page of ten near-identical shingles would be a
  worse report than eight shingles and two of everything else.

Scoring is the project's: worst rho_dh over theta 0/+-20/+-40, then worst over
the three coating diffuse fractions. See results/analysis_shapes.md for why the
worst-of-three rule is in practice closer to a specular-only rule.
"""

import sys
import os
import csv
import json
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import shot3d                                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_topo.csv")

FLAT_COATING_RHO0 = 0.00998        # blender_render.MUSOU_RHO0
MATS = ("d00", "d76", "d100")
THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)


def load():
    rows = list(csv.DictReader(open(CSV)))
    per = collections.defaultdict(dict)
    meta = {}
    for r in rows:
        per[(r["tag"], r["diffuse_frac"])][float(r["theta"])] = float(r["rho"])
        meta[r["tag"]] = r
    worst = collections.defaultdict(dict)
    for (tag, mat), d in per.items():
        if len(d) == len(THETAS):
            worst[tag][mat] = max(d.values())
    complete = {t: v for t, v in worst.items() if len(v) == len(MATS)}
    return per, meta, complete


def main():
    topn = int(os.environ.get("TOPN", "10"))
    per, meta, complete = load()
    if not complete:
        sys.exit("no fully scored designs in %s" % CSV)

    ranked = sorted(complete.items(), key=lambda kv: max(kv[1].values()))

    # top N, then top up with the best of any family that missed out, so the
    # sheet is a comparison of topologies rather than of one family's tail
    chosen = [t for t, _ in ranked[:topn]]
    seen_fam = {meta[t]["topology"] for t in chosen}
    for tag, _ in ranked:
        fam = meta[tag]["topology"]
        if fam not in seen_fam:
            chosen.append(tag)
            seen_fam.add(fam)

    date = os.environ.get("REPORT_DATE") or __import__("datetime") \
        .datetime.now().strftime("%Y-%m-%d")
    outdir = os.path.join(ROOT, "report", date, "top")
    os.makedirs(outdir, exist_ok=True)

    entries = []
    for i, tag in enumerate(chosen, 1):
        r = meta[tag]
        prm = json.loads(r["params_json"])
        fam = {"cone": "cone3d"}.get(r["topology"], r["family"])
        shot = dict(prm)
        shot["margin_depths"] = 0.2          # picture, not measurement
        png = os.path.join(outdir, "%02d_%s.png" % (i, tag))
        try:
            shot3d.shoot(tag, fam, shot, shot.get("face_w", 60.0), png)
            ok = True
        except Exception as e:                # a bad render must not lose the report
            print("[FAIL] render %s: %s" % (tag, e), flush=True)
            ok = False
        v = complete[tag]
        comb = max(v.values())
        entries.append({
            "rank": i,
            "tag": tag,
            "topology": r["topology"],
            "family": fam,
            "params": prm,
            "png": os.path.relpath(png, ROOT) if ok else None,
            "d00": v["d00"], "d76": v["d76"], "d100": v["d100"],
            "combined": comb,
            "set_by": max(v, key=lambda m: v[m]),
            "vs_flat_coating": FLAT_COATING_RHO0 / comb,
            "exposed_est": float(r["exposed_est"]),
            "pitch": float(r["pitch"]), "depth": float(r["depth"]),
            "aspect": float(r["aspect"]),
            "by_theta": {m: {str(t): per[(tag, m)][t] for t in THETAS}
                         for m in MATS},
        })
        print("[%2d] %-34s %-10s combined %.5f  %s"
              % (i, tag, r["topology"], comb, "ok" if ok else "NO RENDER"),
              flush=True)

    out = {
        "date": date,
        "csv": os.path.relpath(CSV, ROOT),
        "designs_scored": len(complete),
        "baseline_flat_coating_rho0": FLAT_COATING_RHO0,
        "thetas": list(THETAS),
        "materials": list(MATS),
        "note_margin": "renders use margin_depths 0.2 for framing; every "
                       "optical number comes from the sweep at 6.5",
        "entries": entries,
    }
    path = os.path.join(ROOT, "report", date, "top10.json")
    json.dump(out, open(path, "w"), indent=2)
    print("[DONE] %s  (%d entries)" % (path, len(entries)))


if __name__ == "__main__":
    main()
