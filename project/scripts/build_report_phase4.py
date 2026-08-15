"""
Phase 4 report: shaped cell floors, ranked on every axis, with a picture each.

    Blender --background --factory-startup --python scripts/build_report_phase4.py

Phase 3 found that a honeycomb's head-on brightness comes from the flat slab at
the BOTTOM of each cell, and fixed it by spending half the envelope on a cone.
Phase 4 asks how little of the envelope the floor actually needs, and answers
2-3 mm out of 50.

PICTURES ARE CUTAWAYS, AND SAY SO ON THE CARD. Every design here is a 45-48 mm
tube over a 2-5 mm floor. Photographed honestly, all fifty-two look like the
same black holes -- the floor is 15 tube-diameters down and invisible. So the
gallery renders each design with its tube shortened to 8 mm and its floor at
full size, which is the only view in which the thing being compared is visible.
The NUMBERS are all from the full-depth sweep; not one comes from these images.
Anything else would be a picture of one geometry captioned with another's
measurement, which is how phase 2 shipped a honeycomb with holes in it.
"""

import sys
import os
import csv
import json
import math
import html
import base64
import subprocess
import datetime
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
CUT_TUBE = 8.0                  # tube depth in the CUTAWAY renders only

TUBE_LABEL = {
    "p650f080": ("Honeycomb 6.5 / 0.08", "bought",
                 "Expanded aluminium foil, off the shelf."),
    "p520f050": ("Honeycomb 5.2 / 0.05", "bought",
                 "Finer bought foil, at the handling floor."),
    "bl050o115": ("Blade 0.05, overlap 1.15", "made",
                  "Laser-cut blades slotted together, phase 2 overlap."),
    "bl050o145": ("Blade 0.05, overlap 1.45", "made",
                  "The same blades 26% wider, so neighbours overlap more."),
    "bl100o115": ("Blade 0.10, overlap 1.15", "made",
                  "Thick enough to resist a thumb, phase 2 overlap."),
    "bl100o145": ("Blade 0.10, overlap 1.45", "made",
                  "Thick and wide."),
}
FLOOR_LABEL = {
    "flat": ("Flat slab", "The control. What a honeycomb sits on today."),
    "pyramid": ("Pressed pyramids", "Embossed sheet, square pyramids, "
                "0.1 mm apex flat. A die and a press."),
    "cone": ("Moulded cones", "What phase 3 used, made thin."),
    "wave": ("Pressed egg-carton", "Same press, no edges anywhere."),
    "gap": ("Air gap", "No floor at all — the slab simply set back. The "
            "control that separates shape from distance."),
}


def load():
    """(theta-0 rho, worst-theta rho) per design.

    SCORING, and the trap in it. The worst-theta column must be scored exactly
    as phases 2 and 3 scored everything, or a phase-4 number cannot be compared
    to a phase-2 one: for each (design, seed, coating) take the WORST rho over
    the five incidence angles, then the worst over the three coatings, then the
    MEAN over seeds. The first version of this function averaged over angles
    instead of taking the worst, which made every design here look ~40 % darker
    than it is -- the blade array read 0.1326 % where the identical geometry in
    `sweep_blade.csv` reads 0.2137 %. Caught by re-measuring one design against
    its phase-2 row and finding the theta-0 values matched to five decimals
    while the summary did not.

    The theta-0 column is a different question -- what a floor exists to move --
    and is scored mean over seeds, worst over coating, at normal incidence only.
    """
    rows = list(csv.DictReader(open(os.path.join(RESULTS,
                                                 "sweep_floor.csv"))))
    meta = {}
    per = collections.defaultdict(dict)      # (tag, coating) -> {theta: rho}
    zed = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        b = r["tag"].rsplit("_s", 1)[0]
        meta[b] = r
        per[(r["tag"], r["diffuse_frac"])][float(r["theta"])] = float(r["rho"])
        if abs(float(r["theta"])) < 1e-9:
            zed[b][r["diffuse_frac"]].append(float(r["rho"]))

    worst = {}                               # tag -> {coating: worst over theta}
    for (tag, mat), d in per.items():
        if len(d) == 5:
            worst.setdefault(tag, {})[mat] = max(d.values())
    byseed = collections.defaultdict(list)   # design -> [worst per seed]
    for tag, m in worst.items():
        if len(m) == 3:
            byseed[tag.rsplit("_s", 1)[0]].append(max(m.values()))

    W = {k: sum(v) / len(v) for k, v in byseed.items()}
    Z = {k: max(sum(v) / len(v) for v in m.values())
         for k, m in zed.items() if len(m) == 3}
    common = set(W) & set(Z)
    return ({k: Z[k] for k in common}, {k: W[k] for k in common}, meta)


def form_data():
    fp = os.path.join(RESULTS, "form_buildable.json")
    out = {}
    if not os.path.exists(fp):
        return out
    for e in json.load(open(fp)):
        if "thetas" not in e:
            continue
        t = e["thetas"]
        a, b = t.get("-40"), t.get("+40")
        smear = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                        + b["rms_mm"] / b["rms_control_mm"])
                 if a and b else None)
        out[e["tag"].rsplit("_s", 1)[0]] = (smear,
                                            t.get("+0", {}).get("peak_ratio_mean"))
    return out


def cutaway_params(meta_row):
    """The picture's geometry: real floor, tube cut to 8 mm so it is visible."""
    prm = json.loads(meta_row["params_json"])
    if "top" not in prm:                       # flat control: single layer
        return dict(prm, depth=CUT_TUBE, margin_depths=0.2,
                    face_w=40.0, face_h=40.0), "topo"
    bp = dict(prm["bot_params"])
    if "margin_depth_ref" in bp:
        bp["margin_depth_ref"] = CUT_TUBE + prm["bot_depth"]
    return dict(prm, top_depth=CUT_TUBE, bot_params=bp, margin_depths=0.2,
                face_w=40.0, face_h=40.0), "stack"


def shot_for(design, meta_row, shots):
    png = os.path.join(shots, "%s.png" % design)
    if os.path.exists(png):
        return png
    try:
        import shot3d
    except ImportError:
        return None
    prm, fam = cutaway_params(meta_row)
    print("[SHOT] %s" % design, flush=True)
    try:
        shot3d.shoot(design, fam, prm, prm["face_w"], png)
    except Exception as exc:
        print("[FAIL] %s: %s" % (design, exc), flush=True)
        return None
    return png if os.path.exists(png) else None


def webify(rdir, src, px=700, q=68):
    web = os.path.join(rdir, "web")
    os.makedirs(web, exist_ok=True)
    out = os.path.join(web, os.path.basename(src).replace(".png", ".jpg"))
    if not os.path.exists(out):
        subprocess.run(["sips", "-Z", str(px), "-s", "format", "jpeg",
                        "-s", "formatOptions", str(q), src, "--out", out],
                       capture_output=True)
    return out if os.path.exists(out) else None


def b64(p):
    return base64.b64encode(open(p, "rb").read()).decode("ascii")


def bar(v, lo, hi, invert=False):
    if v is None:
        return '<span class="bar"></span>'
    f = (math.log10(max(v, lo)) - math.log10(lo)) / \
        (math.log10(hi) - math.log10(lo))
    f = min(1.0, max(0.0, f))
    if invert:
        f = 1.0 - f
    return '<span class="bar"><i style="width:%.1f%%"></i></span>' % (100 * f)


def card(design, meta, Z, W, form, rank, metric, extra=""):
    e = meta[design]
    tl, track, tnote = TUBE_LABEL[e["tube"]]
    fl, fnote = FLOOR_LABEL[e["floor"]]
    fd = float(e["floor_depth"])
    sm, pk = form.get(design, (None, None))
    slug = design.lower().replace("_", "-")
    return """
<figure class="spec %s">
  <div class="shot i-%s"></div>
  <figcaption>
    <div class="hd"><span class="rk">%s</span><span class="fam">%s</span></div>
    <p class="sp">%s &middot; %s</p>
    <div class="big">%s</div>
    <dl class="kv">
      <div><dt>normal incidence</dt><dd>%.5f%%</dd></div>
      <div><dt>worst over &plusmn;40&deg;</dt><dd>%.4f%%</dd></div>
      <div><dt>form destruction</dt><dd>%s</dd></div>
      <div><dt>head-on brightness</dt><dd>%s</dd></div>
    </dl>%s
  </figcaption>
</figure>""" % (track, slug, rank, html.escape(fl),
                html.escape(tl),
                ("no floor" if fd == 0 else "floor %.0f mm" % fd),
                metric,
                100 * Z[design], 100 * W[design],
                ("%.2f&times;" % sm) if sm else "&mdash;",
                ("%.3f" % pk) if pk is not None else "&mdash;",
                extra)


def main():
    date = os.environ.get("REPORT_DATE") or \
        datetime.datetime.now().strftime("%Y-%m-%d")
    rdir = os.path.join(ROOT, "report", date)
    shots = os.path.join(rdir, "shots")
    os.makedirs(shots, exist_ok=True)

    Z, W, meta = load()
    form = form_data()
    designs = sorted(Z)
    print("[P4] %d designs, %d with form data" % (len(designs), len(form)))

    css = []
    for d in designs:
        png = shot_for(d, meta[d], shots)
        j = webify(rdir, png) if png else None
        if j:
            css.append(".i-%s{background-image:url(data:image/jpeg;base64,%s)}"
                       % (d.lower().replace("_", "-"), b64(j)))

    # --- gallery 1: the mechanism, five floors on the bought honeycomb ------
    mech = ["FL_p650f080_flat_d00", "FL_p650f080_pyramid_d30",
            "FL_p650f080_cone_d30", "FL_p650f080_wave_d30",
            "FL_p650f080_gap_d30"]
    ref = Z["FL_p650f080_flat_d00"]
    g1 = "\n".join(
        card(d, meta, Z, W, form, "&mdash;" if i == 0 else "%d" % i,
             "%.2f&times;" % (ref / Z[d]) if i else "baseline",
             '<p class="nt">%s</p>' % html.escape(FLOOR_LABEL[meta[d]["floor"]][1]))
        for i, d in enumerate(mech))

    # --- gallery 2: every design ranked at normal incidence -----------------
    g2 = "\n".join(card(d, meta, Z, W, form, str(i + 1), "%.5f%%" % (100 * Z[d]))
                   for i, d in enumerate(sorted(designs, key=lambda k: Z[k])))
    # --- gallery 3: every design ranked on worst-case total -----------------
    g3 = "\n".join(card(d, meta, Z, W, form, str(i + 1), "%.4f%%" % (100 * W[d]))
                   for i, d in enumerate(sorted(designs, key=lambda k: W[k])))
    # --- gallery 4: the twelve measured on all three ------------------------
    meas = [d for d in designs if form.get(d, (None, None))[0]]
    g4 = "\n".join(card(d, meta, Z, W, form, str(i + 1),
                        "%.2f&times;" % form[d][0])
                   for i, d in enumerate(sorted(meas, key=lambda k: -form[k][0])))
    g5 = "\n".join(card(d, meta, Z, W, form, str(i + 1), "%.3f" % form[d][1])
                   for i, d in enumerate(sorted(meas, key=lambda k: form[k][1]))
                   if form[d][1] is not None)

    def best(pred, key):
        c = [d for d in designs if pred(d)]
        return min(c, key=key) if c else None

    bz = min(designs, key=lambda k: Z[k])
    bw = min(designs, key=lambda k: W[k])
    bought = best(lambda d: meta[d]["tube_kind"] == "comb", lambda k: Z[k])
    made = best(lambda d: meta[d]["tube_kind"] == "shingle", lambda k: Z[k])

    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "report_phase4_template.html")).read()
    rep = {
        "{{DATE}}": date, "{{IMGCSS}}": "\n".join(css),
        "{{G_MECH}}": g1, "{{G_TH0}}": g2, "{{G_TOTAL}}": g3,
        "{{G_FORM}}": g4, "{{G_PEAK}}": g5,
        "{{NDESIGN}}": str(len(designs)),
        "{{NMEAS}}": str(len(meas)),
        "{{FLAT_TH0}}": "%.5f" % (100 * ref),
        "{{BEST_TH0}}": "%.5f" % (100 * Z[bz]),
        # the gain MUST be within one tube. Quoting the global best against a
        # different tube's flat control mixes two geometries into one ratio --
        # it read "6.20x" for a while, which is 6.5 mm foil's flat floor over
        # 5.2 mm foil's pyramid and describes no panel that exists.
        "{{BEST_TH0_GAIN}}": "%.2f" % (ref / Z["FL_p650f080_pyramid_d30"]),
        "{{SAMETUBE_PYR}}": "%.5f" % (100 * Z["FL_p650f080_pyramid_d30"]),
        "{{NTUBE}}": str(len({meta[d]["tube"] for d in designs})),
        "{{BEST_TH0_NAME}}": "%s + %s" % (TUBE_LABEL[meta[bz]["tube"]][0],
                                          FLOOR_LABEL[meta[bz]["floor"]][0].lower()),
        "{{BEST_TOTAL}}": "%.4f" % (100 * W[bw]),
        "{{BEST_TOTAL_NAME}}": "%s + %s" % (TUBE_LABEL[meta[bw]["tube"]][0],
                                            FLOOR_LABEL[meta[bw]["floor"]][0].lower()),
        "{{BOUGHT_TH0}}": "%.5f" % (100 * Z[bought]),
        "{{BOUGHT_NAME}}": "%s + %s" % (TUBE_LABEL[meta[bought]["tube"]][0],
                                        FLOOR_LABEL[meta[bought]["floor"]][0].lower()),
        "{{MADE_TH0}}": "%.5f" % (100 * Z[made]),
        "{{MADE_NAME}}": "%s + %s" % (TUBE_LABEL[meta[made]["tube"]][0],
                                      FLOOR_LABEL[meta[made]["floor"]][0].lower()),
        "{{GAP_TH0}}": "%.5f" % (100 * Z["FL_p650f080_gap_d30"]),
        "{{GAP_GAIN}}": "%.2f" % (ref / Z["FL_p650f080_gap_d30"]),
        "{{PYR2}}": "%.5f" % (100 * Z["FL_p650f080_pyramid_d20"]),
        "{{PYR3}}": "%.5f" % (100 * Z["FL_p650f080_pyramid_d30"]),
        "{{PYR5}}": "%.5f" % (100 * Z["FL_p650f080_pyramid_d50"]),
        "{{CUT}}": "%.0f" % CUT_TUBE,
    }
    for k in ("FL_p650f080_flat_d00", "FL_p650f080_pyramid_d30",
              "FL_bl050o115_flat_d00", "FL_bl050o115_pyramid_d30",
              "FL_bl050o145_flat_d00", "FL_bl050o145_pyramid_d30"):
        sm, pk = form.get(k, (None, None))
        short = k.replace("FL_", "").replace("_d00", "").replace("_d30", "")
        rep["{{SMEAR_%s}}" % short] = "%.2f" % sm if sm else "n/a"
        rep["{{PEAK_%s}}" % short] = "%.3f" % pk if pk is not None else "n/a"

    out = tpl
    for k, v in rep.items():
        out = out.replace(k, v)
    path = os.path.join(rdir, "report.html")
    open(path, "w").write(out)
    print("[DONE] %s (%.1f MB, %d designs, %d images)"
          % (path, os.path.getsize(path) / 1e6, len(designs), len(css)))


if __name__ == "__main__":
    main()
