"""
Render the report set and assemble everything the HTML needs into one JSON.

    Blender --background --factory-startup --python scripts/report_buildable.py

Renders the designs that appear in BOTH rankings -- the form candidates -- so a
reader can compare the same eleven pictures across the two orderings rather than
two disjoint galleries.

`margin_depths` is overridden to 0.2 for the pictures. A measurement build needs
geometry running well past the window or a tilted camera reads world background;
a portrait wants the tile and nothing else. **No optical number in the report
comes from these renders** -- they come from the sweeps, at margin 2.0.
"""

import sys
import os
import json
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shot3d                                                      # noqa: E402
import analyze_buildable as AB                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def main():
    date = os.environ.get("REPORT_DATE") or \
        datetime.datetime.now().strftime("%Y-%m-%d")
    rdir = os.path.join(ROOT, "report", date)
    shots = os.path.join(rdir, "shots")
    os.makedirs(shots, exist_ok=True)

    cands = json.load(open(os.path.join(RESULTS, "form_candidates.json")))
    dark = {r["design"]: r for r in AB.darkness()}
    form = {r["design"]: r for r in AB.form()}

    entries = []
    for e in cands:
        base = e["tag"].rsplit("_s", 1)[0]
        prm = dict(e["params"])
        prm["margin_depths"] = 0.2
        fam = {"cone": "cone3d"}.get(e["topology"], e["family"])
        png = os.path.join(shots, "%s.png" % base)
        ok = True
        if not os.path.exists(png):
            try:
                shot3d.shoot(base, fam, prm, prm.get("face_w", 60.0), png)
            except Exception as exc:
                print("[FAIL] render %s: %s" % (base, exc), flush=True)
                ok = False
        d = dark.get(base)
        f = form.get(base)
        build_ok, build_note = (AB.buildable(d["process"], d["feature"])
                                if d else (None, "not scored"))
        entries.append({
            "design": base, "topology": e["topology"],
            # the full geometry, so a card can say what the design IS. Without
            # it two shingles differing in depth, tilt and assembly render as
            # visually identical cards with different ranks, and a first-time
            # reader has no way to tell them apart -- which is what happened.
            "params": e["params"],
            "process": d["process"] if d else e["process"],
            "feature": d["feature"] if d else None,
            "pitch": e["pitch"],
            "png": os.path.relpath(png, ROOT) if ok else None,
            "buildable": build_ok, "build_note": build_note,
            "dark_mean": d["mean"] if d else None,
            "dark_sem": d["sem"] if d else None,
            "dark_n": d["n"] if d else 0,
            "vs_flat": (AB.FLAT_COATING_WORST / d["mean"]) if d else None,
            "smear": f["smear"] if f else None,
            "peak0": f.get("peak0") if f else None,
            "peak_m40": f["peak_m40"] if f else None,
            "peak_p40": f["peak_p40"] if f else None,
            "mtf20": f["mtf20"] if f else None,
        })
        print("[%-28s] dark %s  form %s  build %s"
              % (base,
                 "%.4f%%" % (100 * d["mean"]) if d else "-",
                 "%.2fx" % f["smear"] if f else "-",
                 build_ok), flush=True)

    # ranks, computed here so the HTML never has to sort anything
    for key, field, rev in (("rank_dark", "dark_mean", False),
                            ("rank_form", "smear", True),
                            ("rank_peak", "peak0", False)):
        have = [e for e in entries if e[field] is not None]
        for i, e in enumerate(sorted(have, key=lambda r: r[field],
                                     reverse=rev), 1):
            e[key] = i

    rough = []
    rp = os.path.join(RESULTS, "form_roughness.json")
    if os.path.exists(rp):
        rough = json.load(open(rp))

    out = {"date": date,
           "flat_coating_worst": AB.FLAT_COATING_WORST,
           "wall": AB.WALL,
           "seeds": max((e["dark_n"] for e in entries), default=0),
           "process_floor": {k: v[0] for k, v in AB.PROCESS_FLOOR.items()},
           "entries": entries,
           "roughness": rough,
           "n_scored": len(AB.darkness()),
           "n_unbuildable": sum(1 for r in AB.darkness()
                                if AB.buildable(r["process"],
                                                r["feature"])[0] is False)}
    path = os.path.join(rdir, "data.json")
    json.dump(out, open(path, "w"), indent=1)
    print("[DONE] %s  (%d entries, %d roughness records)"
          % (path, len(entries), len(rough)))


if __name__ == "__main__":
    main()
