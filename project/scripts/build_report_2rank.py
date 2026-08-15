"""
Build the two-ranking comparison report from report/<date>/data.json.

    python3 scripts/build_report_2rank.py [YYYY-MM-DD]

Self-contained HTML: images inlined as data URIs so the file survives being
opened from disk, mailed, or published where no external host is reachable.

Every number is read from the JSON at build time. This project has already
shipped one report that hard-coded withdrawn claims (`make_report.py`, since
disarmed) and one whose headline was an artifact of a feature-size mismatch
(`report/2026-08-12`). A report that cannot drift from its data is the cheapest
guard against a third.
"""

import sys
import os
import json
import base64
import html
import math
import subprocess
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

# The name a reader will look for. `honeycomb` was labelled "Voronoi cell" --
# accurate about the construction, useless to anyone looking for the honeycomb,
# and it is the one design in the set you can buy off the shelf.
LABEL = {"shingle": "Blade array", "honeycomb": "Honeycomb (bought)",
         "cone": "Cone", "slant": "Slanted honeycomb", "truss": "Strut lattice",
         "c_square": "Square cell", "c_triangle": "Triangle cell",
         "c_mixed": "Mixed-size cell", "c_reentrant": "Re-entrant cell",
         "c_nested": "Nested cell"}
NOTE = {
    "shingle": "Thin blades standing almost normal to the panel, each turned "
               "to its own azimuth. Laser-cut sheet, slotted together.",
    "honeycomb": "Vertical cell walls at full depth, on an irregular (Voronoi) "
                 "tessellation so there is no periodic array. Bought as "
                 "expanded aluminium foil — the only design here you do not "
                 "have to make.",
    "cone": "The incumbent. Irregular cone array, moulded, 0.4 mm tip.",
    "slant": "The same cells leaned over — a stock product at 30/45/60°.",
    "c_square": "Square cells. Tests whether the hex tiling mattered.",
    "c_triangle": "Triangular cells: more wall per unit area.",
    "c_mixed": "Voronoi on thinned seeds, so cell area varies ~3×.",
    "c_reentrant": "Walls diverging with depth — wider at the floor than the "
                   "mouth.",
    "c_nested": "A coarse cell whose floor carries a finer lattice, sunk below "
                "the wall tops so it is shadowed head-on.",
}


def spec_line(topology, prm):
    """The geometry in one line, in the units a supplier would use.

    Every card must say what the design IS, not just where it ranked. Two
    blade arrays differing only in assembly were rendering as identical cards
    with a 33% gap between them and nothing to attribute it to.
    """
    b = []
    g = prm.get
    if g("pitch") is not None:
        b.append("pitch %.2f mm" % g("pitch"))
    if g("depth") is not None:
        b.append("depth %.0f mm" % g("depth"))
    if topology == "shingle":
        t0, t1 = g("plate_t_top"), g("plate_t_bot")
        if t0 is not None:
            b.append("blade %.2f mm" % t0 if t1 in (None, t0)
                     else "blade %.2f\u2192%.2f mm (wedge)" % (t0, t1))
        if g("tilt_deg") is not None:
            b.append("tilt %.0f\u00b0" % g("tilt_deg"))
        b.append({"grid": "slotted grid", "parallel": "all parallel",
                  "random": "random azimuth"}.get(g("azimuth_mode"),
                                                  "random azimuth"))
    elif topology in ("honeycomb", "slant", "comb"):
        w0, w1 = g("wall_top"), g("wall_bot")
        if w0 is not None:
            b.append("wall %.2f mm" % w0 if w1 in (None, w0)
                     else "wall %.2f\u2192%.2f mm" % (w0, w1))
        if topology == "comb":
            b.append("identical cells, bonded walls doubled")
        if g("cell_lean_deg"):
            b.append("cell lean %.0f\u00b0" % g("cell_lean_deg"))
    elif topology == "cone":
        if g("tip_radius") is not None:
            b.append("tip \u00f8%.2f mm" % (2 * g("tip_radius")))
    elif topology.startswith("c_"):
        if g("wall_top") is not None:
            b.append("wall %.2f mm" % g("wall_top"))
        if g("lean_deg"):
            b.append("wall lean %.0f\u00b0" % g("lean_deg"))
    if g("jitter"):
        b.append("placement jitter %.0f%%" % (100 * g("jitter")))
    elif topology == "comb":
        b.append("periodic")
    return " \u00b7 ".join(b)


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def webify(rdir, png):
    """Downscale to a web-sized JPEG once; 18 full renders is 350 MB."""
    web = os.path.join(rdir, "web")
    os.makedirs(web, exist_ok=True)
    out = os.path.join(web, os.path.basename(png).replace(".png", ".jpg"))
    if not os.path.exists(out):
        subprocess.run(["sips", "-Z", "900", "-s", "format", "jpeg",
                        "-s", "formatOptions", "72",
                        os.path.join(ROOT, png), "--out", out],
                       capture_output=True)
    return out if os.path.exists(out) else None


# --- the slope chart: the whole point of the report --------------------------

def slope_svg(entries, w=880, h=440):
    """Rank on darkness, joined to rank on form.

    A design's two ranks are the report's finding: they disagree, and a reader
    who is shown only one ordering will pick the wrong panel. Lines crossing is
    the honest picture of that; two sorted tables side by side is not.
    """
    have = [e for e in entries if e.get("rank_dark") and e.get("rank_form")
            and e.get("rank_peak")]
    if not have:
        return ""
    n = len(have)
    pad_t, pad_b, xl, xr = 44, 26, 176, 176
    cols = ("rank_dark", "rank_form", "rank_peak")
    xs = (xl, (xl + w - xr) / 2.0, w - xr)
    heads = ("LESS LIGHT TOTAL \u2192", "SHAPE DESTROYED \u2192",
             "DIMMER HEAD-ON \u2192")

    def y(rank):
        return pad_t + (rank - 1) / max(n - 1, 1) * (h - pad_t - pad_b)

    p = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Rank on total '
         'reflectance, form destruction and head-on brightness">' % (w, h)]
    for i, (x, hd) in enumerate(zip(xs, heads)):
        anc = "end" if i == 0 else ("middle" if i == 1 else "start")
        p.append('<text class="colhead" x="%.0f" y="20" text-anchor="%s">%s'
                 '</text>' % (x + (-12 if i == 0 else (0 if i == 1 else 12)),
                              anc, hd))
    for e in sorted(have, key=lambda r: r["rank_dark"]):
        r = [e[c] for c in cols]
        span = max(r) - min(r)
        cls = "ln" + (" ln-x" if span >= 4 else "")
        cls += "" if e.get("buildable") is not False else " ln-no"
        for a in range(2):
            y1, y2 = y(r[a]), y(r[a + 1])
            x1, x2 = xs[a], xs[a + 1]
            p.append('<path class="%s" d="M%.0f %.1f C%.0f %.1f, %.0f %.1f, '
                     '%.0f %.1f"/>' % (cls, x1, y1, x1 + 70, y1, x2 - 70, y2,
                                       x2, y2))
        for a in range(3):
            p.append('<circle class="dot" cx="%.0f" cy="%.1f" r="3.5"/>'
                     % (xs[a], y(r[a])))
        nm = html.escape(LABEL.get(e["topology"], e["topology"]))
        bad = "" if e.get("buildable") is not False else " \u2715"
        p.append('<text class="lb" x="%.0f" y="%.1f" text-anchor="end" '
                 'dy="0.32em">%d. %s%s</text>' % (xl - 12, y(r[0]), r[0], nm,
                                                  bad))
        p.append('<text class="lb" x="%.0f" y="%.1f" dy="0.32em">%d. %s%s'
                 '</text>' % (w - xr + 12, y(r[2]), r[2], nm, bad))
    p.append("</svg>")
    return "\n".join(p)


def roughness_svg(rough, w=760, h=320):
    """theta=0 peak against coating roughness, per design and for a flat plate."""
    if not rough:
        return ""
    series = {}
    for r in rough:
        t = r["thetas"].get("+0")
        if not t:
            continue
        series.setdefault(r["what"], []).append(
            (r["roughness"], t["peak_vs_wall"]))
    for k in series:
        series[k].sort()
    xs = sorted({x for v in series.values() for x, _ in v})
    ys = [y for v in series.values() for _, y in v]
    if not xs or not ys:
        return ""
    lo, hi = max(min(ys), 1e-3), max(ys)
    pad_l, pad_r, pad_t, pad_b = 62, 150, 18, 40

    def px(x):
        return pad_l + (x - xs[0]) / max(xs[-1] - xs[0], 1e-9) * \
            (w - pad_l - pad_r)

    def py(v):                       # log scale: the span is 300x
        return h - pad_b - (math.log10(max(v, lo)) - math.log10(lo)) / \
            max(math.log10(hi) - math.log10(lo), 1e-9) * (h - pad_t - pad_b)

    p = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Head-on peak against '
         'coating roughness">' % (w, h)]
    dec = math.floor(math.log10(lo))
    while 10 ** dec <= hi:
        v = 10 ** dec
        if v >= lo:
            p.append('<line class="grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>'
                     % (pad_l, py(v), w - pad_r, py(v)))
            p.append('<text class="ax" x="%d" y="%.1f" text-anchor="end" '
                     'dy="0.32em">%g×</text>' % (pad_l - 8, py(v), v))
        dec += 1
    p.append('<line class="unit" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>'
             % (pad_l, py(1.0), w - pad_r, py(1.0)))
    for x in xs:
        p.append('<text class="ax" x="%.1f" y="%d" text-anchor="middle">%.2f'
                 '</text>' % (px(x), h - pad_b + 16, x))
    order = ["flat"] + [k for k in series if k != "flat"]
    for i, k in enumerate(order):
        if k not in series:
            continue
        d = " ".join(("M" if j == 0 else "L") + "%.1f %.1f" % (px(a), py(b))
                     for j, (a, b) in enumerate(series[k]))
        cls = "rflat" if k == "flat" else "r%d" % (i % 3)
        p.append('<path class="rl %s" d="%s"/>' % (cls, d))
        lab = "flat plate, same coating" if k == "flat" else \
            html.escape(k[2:].split("_")[0])
        p.append('<text class="lb %s" x="%d" y="%.1f" dy="0.32em">%s</text>'
                 % (cls, w - pad_r + 8, py(series[k][-1][1]), lab))
    p.append('<text class="ax" x="%.1f" y="%d" text-anchor="middle">coating '
             'specular roughness</text>'
             % ((pad_l + w - pad_r) / 2, h - 6))
    p.append("</svg>")
    return "\n".join(p)


def flat_head_on():
    """The flat plate's head-on peak at the roughness the sweeps ran at (0.30).

    `form_roughness.json` holds five roughnesses and the flat plate runs from
    119.9 to 0.36 across them, so the wrong row moves this baseline 300x. It
    was a typed 1.644 in two places until 2026-08-14.
    """
    for e in json.load(open(os.path.join(ROOT, "results",
                                         "form_roughness.json"))):
        if e.get("what") == "flat" and abs(e.get("roughness", 0) - 0.30) < 1e-9:
            return e["thetas"]["+0"]["peak_vs_wall"]
    sys.exit("no flat-plate row at roughness 0.30 in form_roughness.json")


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else \
        __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    rdir = os.path.join(ROOT, "report", date)
    data = json.load(open(os.path.join(rdir, "data.json")))
    ent = data["entries"]

    # `data.json` carries whatever roughness records existed when
    # report_buildable.py ran. If that was before form_roughness finished, the
    # field is empty and the chart silently disappears from the page -- caught
    # in a dry run, and exactly the kind of ordering trap that produces a report
    # missing its most important figure at 2 a.m. Re-read the source of truth.
    rp = os.path.join(ROOT, "results", "form_roughness.json")
    if os.path.exists(rp):
        live = json.load(open(rp))
        if len(live) > len(data.get("roughness") or []):
            data["roughness"] = live
            print("[note] roughness re-read from results/: %d records"
                  % len(live))
    if not data.get("roughness"):
        print("[WARN] no roughness records — the 332x figure will be MISSING "
              "from the report. Run scripts/form_roughness.py first.")

    by = {e["design"]: e for e in ent}
    best_build = min((e for e in ent if e.get("buildable")
                      and e["dark_mean"]), key=lambda r: r["dark_mean"])
    best_form = max((e for e in ent if e.get("smear")),
                    key=lambda r: r["smear"])

    # each image embedded ONCE as a CSS rule; three galleries reuse it by
    # class. Repeating the data URI per gallery would triple a 1.9 MB file.
    css, slug = [], {}
    for e in ent:
        k = re.sub(r"[^a-z0-9]+", "-", e["design"].lower()).strip("-")
        slug[e["design"]] = k
        if e["png"]:
            j = webify(rdir, e["png"])
            if j:
                css.append(".i-%s{background-image:url(data:image/jpeg;base64,%s)}"
                           % (k, b64(j)))

    AXES = [
        ("darkness", "rank_dark", False,
         "Total reflectance", "How much light comes back in total, summed over "
         "every outgoing direction. This is what an integrating sphere reads. "
         "Worst case over incidence 0\u00b0, \u00b120\u00b0, \u00b140\u00b0 and over three "
         "coating models, averaged across geometry seeds.",
         lambda e: "%.4f%%" % (100 * e["dark_mean"]) if e["dark_mean"] else "\u2014",
         lambda e: "%.1f\u00d7 vs flat plate" % e["vs_flat"] if e.get("vs_flat") else ""),
        ("form", "rank_form", True,
         "Form destruction", "Whether the returned light keeps its shape. A "
         "2 mm line is walked across one full pitch in 16 steps; the number is "
         "how much wider it comes back than on a flat wall. 1.0\u00d7 means the "
         "artwork returns intact and legible.",
         lambda e: "%.2f\u00d7" % e["smear"] if e["smear"] else "\u2014",
         lambda e: "wider than a flat wall"),
        ("headon", "rank_peak", False,
         "Head-on brightness", "What a person standing in front actually "
         "receives, against a plain matte black wall. Total reflectance cannot "
         "predict this: the same energy spread wide is dim and concentrated "
         "forward is dazzling. A bare flat plate of the same coating reads "
         "<b>%.3f</b>." % flat_head_on(),
         lambda e: "%.3f" % e["peak0"] if e.get("peak0") else "\u2014",
         lambda e: "vs plain black wall"),
    ]

    def card(e, rank_key, big, sub):
        bad = e.get("buildable") is False
        k = slug[e["design"]]
        return """
<figure class="spec%s">
  <div class="shot i-%s"></div>
  <figcaption>
    <div class="hd"><span class="rk">%s</span><span class="fam">%s</span>%s</div>
    <div class="big">%s<span class="sub">%s</span></div>
    <p class="sp">%s</p>
    <dl class="kv">
      <div><dt>process</dt><dd>%s</dd></div>
      <div><dt>min feature</dt><dd>%s mm</dd></div>
      <div><dt>other ranks</dt><dd>%s</dd></div>
    </dl>
  </figcaption>
</figure>""" % (" no" if bad else "", k, e.get(rank_key, "\u2014"),
                html.escape(LABEL.get(e["topology"], e["topology"])),
                '<span class="tag-no">cannot be made</span>' if bad else "",
                big(e), sub(e),
                html.escape(spec_line(e["topology"], e.get("params", {}))),
                html.escape(e["process"]), e["feature"],
                " \u00b7 ".join("%s #%s" % (n, e.get(kk, "\u2014"))
                            for n, kk in (("total", "rank_dark"),
                                          ("form", "rank_form"),
                                          ("head-on", "rank_peak"))
                            if kk != rank_key))

    galleries = []
    for aid, rk, rev, title, blurb, big, sub in AXES:
        have = [e for e in ent if e.get(rk)]
        have.sort(key=lambda r: r[rk])
        galleries.append(
            '<section id="%s">\n<span class="eyebrow">Ranking %d of 3</span>\n'
            '<h2>%s</h2>\n<p class="lede col">%s</p>\n'
            '<div class="grid-cards">%s</div>\n</section>'
            % (aid, len(galleries) + 1, title, blurb,
               "\n".join(card(e, rk, big, sub) for e in have)))

    tpl = open(os.path.join(HERE, "report_2rank_template.html")).read()
    out = (tpl
           .replace("{{DATE}}", date)
           .replace("{{SEEDS}}", str(data["seeds"]))
           .replace("{{NSCORED}}", str(data["n_scored"]))
           .replace("{{NBAD}}", str(data["n_unbuildable"]))
           .replace("{{FLATPCT}}", "%.4f" % (100 * data["flat_coating_worst"]))
           .replace("{{BEST_NAME}}", html.escape(
               LABEL.get(best_build["topology"], best_build["topology"])))
           .replace("{{BEST_DESIGN}}", html.escape(best_build["design"]))
           .replace("{{BEST_PCT}}", "%.4f" % (100 * best_build["dark_mean"]))
           .replace("{{BEST_SEM}}", "%.4f" % (100 * best_build["dark_sem"]))
           .replace("{{BEST_VSFLAT}}", "%.1f" % best_build["vs_flat"])
           .replace("{{VSFLAT}}", "%.1f" % best_build["vs_flat"])
           .replace("{{BEST_PROCESS}}", html.escape(best_build["process"]))
           .replace("{{BEST_SMEAR}}", "%.1f" % (best_build["smear"] or 0))
           .replace("{{BEST_FORM_RANK}}", str(best_build.get("rank_form", "—")))
           # Read, never typed. Every one of these was a hand-written constant
           # until the comb lattice was fixed, at which point the prose kept
           # quoting 0.2092% and 0.140 -- numbers measured on geometry with
           # 30% of its face missing -- while the tables beside it showed the
           # re-measured values. A typed measurement in prose is a measurement
           # that will not be updated.
           .replace("{{COMB_RANK}}",
                    {1:"First",2:"Second",3:"Third"}.get(
                        by["CB_p0520_f040_x10"].get("rank_dark"),
                        "%dth" % (by["CB_p0520_f040_x10"].get("rank_dark") or 0)))
           .replace("{{NCAND}}", str(len(ent)))
           .replace("{{COMB_PCT}}", "%.4f" % (100 * by["CB_p0520_f040_x10"]["dark_mean"]))
           .replace("{{COMB_PEAK}}", "%.3f" % by["CB_p0520_f040_x10"]["peak0"])
           .replace("{{COMB_SMEAR}}", "%.2f" % by["CB_p0520_f040_x10"]["smear"])
           .replace("{{COMBCONE_PEAK}}", "%.3f" % by["ST_comb-cone_50"]["peak0"])
           .replace("{{FLATPEAK}}", "%.3f" % flat_head_on())
           .replace("{{SLOPE}}", slope_svg(ent))
           .replace("{{ROUGH}}", roughness_svg(data.get("roughness")))
           .replace("{{IMGCSS}}", "\n".join(css))
           .replace("{{GALLERIES}}", "\n".join(galleries)))
    path = os.path.join(rdir, "report.html")
    open(path, "w").write(out)
    print("[DONE] %s  (%.1f MB)" % (path, os.path.getsize(path) / 1e6))


if __name__ == "__main__":
    main()
