"""
Build the self-contained HTML comparison report from top10.json + the renders.

    python3 scripts/build_report_html.py [YYYY-MM-DD]

Everything is inlined as data URIs: the report has to survive being opened from
a file:// path, mailed, or published where no external host is reachable.

Regenerating is the point. Every number below is read from the CSV and the
JSON at build time, so the report cannot drift away from the measurements the
way a hand-written one does -- and this project has already shipped a report
that hard-coded two withdrawn claims (scripts/make_report.py, now disarmed).
"""

import sys
import os
import csv
import json
import base64
import collections
import re
import datetime
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLAT = 0.00998            # flat plate of the same coating, rho_dh(0)
CONTROL = 0.05            # plain matte black wall
MATS = ("d00", "d76", "d100")
THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)

FAMILY_LABEL = {
    "shingle": "Shingle",
    "honeycomb": "Voronoi cell",
    "cone": "Cone (reference)",
    "truss": "Strut lattice",
    "c_square": "Square cell",
    "c_triangle": "Triangle cell",
    "c_mixed": "Mixed-size cell",
    "c_reentrant": "Re-entrant cell",
    "c_nested": "Nested cell",
}
FAMILY_NOTE = {
    "shingle": "Inclined plates, knife-edged at the mouth, each leaning in its "
               "own azimuth. Overlapping neighbours turn the gap into a slot.",
    "honeycomb": "Voronoi cell walls, vertical, full depth. Cells never seal — "
                 "unlike a pillar array, which stops being a cavity at 72% of "
                 "its nominal depth.",
    "cone": "The incumbent. Irregular cone array, tip radius 0.2 mm.",
    "truss": "Sparse strut lattice between jittered node layers. High surface "
             "area, no preferred direction.",
    "c_square": "Square cells — tests whether the hex tiling ever mattered.",
    "c_triangle": "Triangular cells: more wall per unit area.",
    "c_mixed": "Voronoi on thinned seeds, so cell area varies ~3×.",
    "c_reentrant": "Walls that diverge with depth, so the cell is wider at the "
                   "floor than at its mouth.",
    "c_nested": "A coarse cell whose floor carries a finer lattice, sunk below "
                "the primary wall tops so it is shadowed head-on.",
}


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def load_scores(csv_path):
    rows = list(csv.DictReader(open(csv_path)))
    per, meta = collections.defaultdict(dict), {}
    for r in rows:
        per[(r["tag"], r["diffuse_frac"])][float(r["theta"])] = float(r["rho"])
        meta[r["tag"]] = r
    worst = collections.defaultdict(dict)
    for (tag, mat), d in per.items():
        if len(d) == len(THETAS):
            worst[tag][mat] = max(d.values())
    return per, meta, {t: v for t, v in worst.items() if len(v) == len(MATS)}


def tilt_series(best, pitch_tag, depth_tag):
    pat = re.compile(r"SHIN_p%s_d%s_t(\d+)_o114_k050$" % (pitch_tag, depth_tag))
    out = []
    for tag, v in best.items():
        m = pat.match(tag)
        if m and len(v) == 3:
            out.append((int(m.group(1)), v["d00"], v["d100"]))
    return sorted(out)


# --- the tilt-crossing chart -------------------------------------------------

def crossing_svg(series, w=760, h=330):
    """Two curves and the point where the worse of them is least.

    This is the report's one real chart, and it earns the space because it is
    the mechanism: the two coating models want opposite tilts, so the design
    that survives both is set by where the curves cross, not by either one's
    own optimum.
    """
    pad_l, pad_r, pad_t, pad_b = 58, 18, 22, 40
    xs = [s[0] for s in series]
    ys = [v for s in series for v in (s[1], s[2])]
    x0, x1 = 0, max(xs)
    y0, y1 = 0.0, max(ys) * 1.08

    def px(x):
        return pad_l + (x - x0) / (x1 - x0) * (w - pad_l - pad_r)

    def py(y):
        return h - pad_b - (y - y0) / (y1 - y0) * (h - pad_t - pad_b)

    def path(idx):
        return " ".join(("M" if i == 0 else "L")
                        + "%.1f %.1f" % (px(s[0]), py(s[idx]))
                        for i, s in enumerate(series))

    best = min(series, key=lambda s: max(s[1], s[2]))
    parts = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Reflectance '
             'versus plate tilt for the two coating models">' % (w, h)]
    # y grid
    for k in range(5):
        y = y0 + (y1 - y0) * k / 4
        parts.append('<line class="grid" x1="%.1f" y1="%.1f" x2="%.1f" '
                     'y2="%.1f"/>' % (pad_l, py(y), w - pad_r, py(y)))
        parts.append('<text class="ax" x="%.1f" y="%.1f" text-anchor="end" '
                     'dy="0.32em">%.3f%%</text>' % (pad_l - 8, py(y), y * 100))
    for x in xs:
        parts.append('<text class="ax" x="%.1f" y="%.1f" text-anchor="middle">'
                     '%d</text>' % (px(x), h - pad_b + 16, x))
    parts.append('<line class="axis" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (pad_l, py(y0), w - pad_r, py(y0)))
    # the crossing marker, drawn under the curves
    parts.append('<line class="mark" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
                 % (px(best[0]), pad_t, px(best[0]), py(y0)))
    parts.append('<path class="spec" d="%s"/>' % path(1))
    parts.append('<path class="diff" d="%s"/>' % path(2))
    for s in series:
        parts.append('<circle class="spec-d" cx="%.1f" cy="%.1f" r="3"/>'
                     % (px(s[0]), py(s[1])))
        parts.append('<circle class="diff-d" cx="%.1f" cy="%.1f" r="3"/>'
                     % (px(s[0]), py(s[2])))
    parts.append('<text class="mark-t" x="%.1f" y="%.1f" text-anchor="middle">'
                 'best worst-case · %d°</text>' % (px(best[0]), pad_t - 6,
                                                   best[0]))
    parts.append('<text class="ax" x="%.1f" y="%.1f" text-anchor="middle">'
                 'plate tilt from panel normal (degrees)</text>'
                 % ((pad_l + w - pad_r) / 2, h - 4))
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else \
        datetime.datetime.now().strftime("%Y-%m-%d")
    rdir = os.path.join(ROOT, "report", date)
    data = json.load(open(os.path.join(rdir, "top10.json")))
    per, meta, best = load_scores(os.path.join(ROOT, data["csv"]))

    ent = data["entries"]
    win = ent[0]
    series = tilt_series(best, "0750", "80") or tilt_series(best, "0550", "30")

    # family bests, for the exposed-area table
    fam = {}
    for tag, v in best.items():
        f = meta[tag]["topology"]
        c = max(v.values())
        if f not in fam or c < fam[f][0]:
            fam[f] = (c, tag, 100 * float(meta[tag]["exposed_est"]))

    def esc(s):
        return html.escape(str(s))

    cards = []
    for e in ent:
        img = os.path.join(rdir, "web", os.path.basename(e["png"])
                           .replace(".png", ".jpg"))
        src = ("data:image/jpeg;base64," + b64(img)) if os.path.exists(img) \
            else ""
        p = e["params"]
        bits = []
        for k, lab in (("tilt_deg", "tilt"), ("plate_over", "overlap"),
                       ("plate_t_top", "edge"), ("wall_top", "wall"),
                       ("wall_bot", "wall base"), ("lean_deg", "lean"),
                       ("cell_lean_deg", "cell lean"), ("strut_r", "strut r"),
                       ("layers", "layers"), ("tip_radius", "tip r")):
            if k in p and p[k] not in (None, ""):
                bits.append("%s&nbsp;%s" % (lab, p[k]))
        rel = e["combined"] / ent[0]["combined"]
        cards.append("""
<figure class="spec">
  <div class="shot"><img src="%s" alt="3D render of %s" loading="lazy"></div>
  <figcaption>
    <div class="spec-head">
      <span class="rk">%s</span>
      <span class="fam">%s</span>
    </div>
    <div class="score"><b>%.4f%%</b><span class="rel">%s</span></div>
    <dl class="kv">
      <div><dt>pitch</dt><dd>%.2f mm</dd></div>
      <div><dt>depth</dt><dd>%.0f mm</dd></div>
      <div><dt>aspect</dt><dd>%.1f</dd></div>
      <div><dt>exposed</dt><dd>%.2f%%</dd></div>
    </dl>
    <p class="prm">%s</p>
    <p class="tag">%s</p>
  </figcaption>
</figure>""" % (src, esc(e["tag"]), e["rank"],
                esc(FAMILY_LABEL.get(e["topology"], e["topology"])),
                100 * e["combined"],
                "winner" if e["rank"] == 1 else "%.2f× #1" % rel,
                e["pitch"], e["depth"], e["aspect"], 100 * e["exposed_est"],
                " · ".join(bits) or "&mdash;", esc(e["tag"])))

    famrows = []
    for f, (c, tag, ex) in sorted(fam.items(), key=lambda kv: kv[1][0]):
        famrows.append(
            "<tr><td class=\"nm\">%s</td><td class=\"num\">%.4f%%</td>"
            "<td class=\"num\">%.2f×</td><td class=\"num\">%.2f%%</td>"
            "<td class=\"nt\">%s</td></tr>"
            % (esc(FAMILY_LABEL.get(f, f)), 100 * c, FLAT / c, ex,
               esc(FAMILY_NOTE.get(f, ""))))

    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "report_template.html")).read()
    out = (tpl
           .replace("{{DATE}}", date)
           .replace("{{SCORED}}", str(data["designs_scored"]))
           .replace("{{WIN_TAG}}", esc(win["tag"]))
           .replace("{{WIN_PCT}}", "%.4f" % (100 * win["combined"]))
           .replace("{{WIN_VS_FLAT}}", "%.1f" % (FLAT / win["combined"]))
           .replace("{{WIN_VS_WALL}}", "%.0f" % (CONTROL / win["combined"]))
           .replace("{{WIN_VS_CONE}}",
                    "%.0f" % (100 * (1 - win["combined"] / fam["cone"][0])))
           .replace("{{CONE_PCT}}", "%.4f" % (100 * fam["cone"][0]))
           .replace("{{CARDS}}", "\n".join(cards))
           .replace("{{FAMROWS}}", "\n".join(famrows))
           .replace("{{CHART}}", crossing_svg(series))
           .replace("{{AREA_SPAN}}",
                    "%.0f" % (max(v[2] for v in fam.values())
                              / min(v[2] for v in fam.values())))
           .replace("{{SCORE_SPAN}}",
                    "%.1f" % (max(v[0] for v in fam.values())
                              / min(v[0] for v in fam.values()))))
    path = os.path.join(rdir, "report.html")
    open(path, "w").write(out)
    print("[DONE] %s  (%.1f MB)" % (path, os.path.getsize(path) / 1e6))


if __name__ == "__main__":
    main()
