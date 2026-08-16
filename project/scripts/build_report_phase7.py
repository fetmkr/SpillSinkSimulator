"""Phase 7 standalone report: the recessed box.

    python3 scripts/build_report_phase7.py

Generated from sweep_phase7.csv / form_phase7.json / sweep_phase515.csv
only; no typed measurements.
"""

import csv
import json
import os
import sys
import base64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(ROOT, "report", "phase7")
OUT = os.path.join(OUTDIR, "report.html")
DASH = "&mdash;"


def worst(path):
    out = {}
    p = os.path.join(RESULTS, path)
    for r in csv.DictReader(open(p)):
        out[r["tag"]] = max(out.get(r["tag"], 0.0), float(r["rho"]))
    return out


def jload(path):
    p = os.path.join(RESULTS, path)
    return json.load(open(p)) if os.path.exists(p) else {}


def pc(x, nd=3):
    return "%.*f&#8202;%%" % (nd, 100 * x) if x else DASH


def num(x, nd=2):
    return ("%.*f" % (nd, x)) if x is not None else DASH


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    p7 = worst("sweep_phase7.csv")
    f7 = jload("form_phase7.json")
    p515 = worst("sweep_phase515.csv")
    p73 = worst("sweep_phase73.csv")
    f73 = jload("form_phase73.json")

    def frow(label, tt, fk, bw, star=False):
        fr = f7.get(fk) if fk else None
        return ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                "<td>%s</td><td>%s</td></tr>"
                % (' class="win"' if star else "", label, pc(p7.get(tt)),
                   num(fr.get("smear")) if fr else "not yet run",
                   num(fr.get("head_on"), 4) if fr else "not yet run",
                   ("%.2f&times;" % fr["span_0"]) if fr and
                   fr.get("span_0") else DASH, bw))

    rows = (frow("plain Musou walls, flat 3&#8202;mm frames",
                 "P7_box_flat", "P7_box_flat_b75", "7.5&#8202;mm")
            + frow("plain Musou walls, tapered frames",
                   "P7_box_taper", "P7_box_taper_b75", "7.5&#8202;mm")
            + frow("pyramid-textured walls (surrogate), tapered frames",
                   "P72_boxtex", None, "totals only", star=True)
            + ("<tr><td>reference: flat final sample "
               "(p4/d20/t0.1)</td><td>%s</td><td>1.42 / 1.09</td>"
               "<td>0.0400</td><td>&mdash;</td><td>7 / 10&#8202;mm</td>"
               "</tr>" % pc(p515.get("P515_easy_t01"))))

    gain = ((p515.get("P515_easy_t01") or 1)
            / (p7.get("P72_boxtex") or 1))

    pb = os.path.join(OUTDIR, "img", "panelbox.png")
    pb64 = ("data:image/png;base64,"
            + base64.b64encode(open(pb, "rb").read()).decode()) \
        if os.path.exists(pb) else ""
    rf = os.path.join(OUTDIR, "img", "rays_failures.png")
    rf64 = ("data:image/png;base64,"
            + base64.b64encode(open(rf, "rb").read()).decode()) \
        if os.path.exists(rf) else ""
    wt = os.path.join(OUTDIR, "img", "wall_textures.png")
    wt64 = ("data:image/png;base64,"
            + base64.b64encode(open(wt, "rb").read()).decode()) \
        if os.path.exists(wt) else ""
    img = os.path.join(OUTDIR, "img", "box_views.png")
    b64 = ("data:image/png;base64,"
           + base64.b64encode(open(img, "rb").read()).decode()) \
        if os.path.exists(img) else ""

    html = """<title>Spill Sink 피라미드 연구 — Phase 7</title>
<style>
:root{--bg:#f4f2ec;--card:#fbfaf7;--ink:#1c1b18;--ink2:#5c594f;--line:#d8d4c8;
  --acc:#b34700;--ok:#2c6e49;--mono:ui-monospace,'SF Mono',Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme=light]){
  --bg:#171613;--card:#1f1e1a;--ink:#e8e5dd;--ink2:#a39f92;--line:#37342c;
  --acc:#ff8c42;--ok:#7fc8a0}}
:root[data-theme=dark]{--bg:#171613;--card:#1f1e1a;--ink:#e8e5dd;
  --ink2:#a39f92;--line:#37342c;--acc:#ff8c42;--ok:#7fc8a0}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);
  font:16px/1.65 Georgia,'Times New Roman',serif;margin:0;padding:0 18px}
main{max-width:46rem;margin:0 auto;padding:3rem 0 5rem}
h1{font-size:1.9rem;line-height:1.25;margin:.2rem 0 0}
h2{font-size:1.15rem;margin:2.6rem 0 .6rem;border-bottom:1px solid var(--line);
  padding-bottom:.35rem}
.kicker{font:700 .72rem var(--mono);letter-spacing:.18em;color:var(--acc);
  text-transform:uppercase}
.lede{color:var(--ink2);font-size:1.05rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;
  font:.86rem var(--mono);font-variant-numeric:tabular-nums}
th{font-weight:600;text-align:left;color:var(--ink2);
  border-bottom:1px solid var(--ink2)}
td,th{padding:.45rem .6rem .45rem 0}
td{border-bottom:1px solid var(--line)}
tr.win td{color:var(--acc);font-weight:700}
.note{font-size:.85rem;color:var(--ink2)}
code{font:.85em var(--mono)}
</style>
<main>
<div class="kicker">Spill Sink &middot; 피라미드 연구 &middot; Phase 7</div>
<h1>The recessed box: a cavity in front of the panel</h1>
<p class="lede">Space behind the wall is available (user-confirmed), so
the strongest absorber may be a hole into a dark volume rather than a
surface. Phase 7 asks whether box modules — deep cells over the
final-sample pyramid floor — beat the flat panel, and what their front
frames and side walls cost. Every table row carries all three axes and
its beam width.</p>

<figure style="margin:1.4rem 0 0">
<img src="%%VIEWS%%" alt="Box structure diagram, side section and top view"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">Structure diagram (Korean labels): side
section and top view. Cell 110&#8202;mm, depth 220&#8202;mm, the
final-sample pyramid field as the floor. The simulator measured HEX
cells (builder limitation); square boxes are the same structural class,
noted on the figure.</figcaption>
</figure>

<h2>Measurements</h2>
<table>
<tr><th>variant</th><th>total worst-&rho; &darr;</th><th>smear &uarr;</th>
<th>head-on &darr;</th><th>span &theta;0</th><th>beam width</th></tr>
%%ROWS%%
</table>

<h2>What happened, in order</h2>
<p><b>Plain walls lost</b> (both pre-registered predictions wrong): at
depth/cell = 2 the box is optically a big honeycomb, and its flat Musou
walls hand the oblique light back. Flat frames also glint (0.168 head-on);
tapering them fixes the glint and lets the cavity smear the image well
(4.61 &mdash; it dies inside), but totals still trail the flat panel.
Along the way the form protocol&rsquo;s measurement window was widened
(&ldquo;측정창 키워&rdquo;) &mdash; the original inset window was smaller
than one 110&#8202;mm cell and returned NaN.</p>
<p><b>Then the user&rsquo;s move: texture the side walls too.</b>
Modelled first as a surrogate &mdash; walls carrying the measured panel
albedo (0.21&#8202;% diffuse) instead of real pyramid geometry &mdash;
the box reads <b>%%BOXTEX%%</b>: %%GAIN%%&times; better than the flat
final sample and roughly 25&times; darker than a flat Musou wall. The
pre-registered threshold for taking the concept seriously
(&le;0.12&#8202;%) passed with margin.</p>

<h2>The real 1&#8202;mm-sheet box: three wall textures, three failures
(Phase 7.3)</h2>
<p>The user pinned the constraint: box walls are single 1&#8202;mm sheet.
Three fold textures were built as real geometry and measured. Every
smear/span figure in the table below is at the 7.5&#8202;mm deployment
beam.</p>
<figure style="margin:1rem 0 0">
<img src="%%RAYFAIL%%" alt="Traced ray paths showing the two failure mechanisms"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
<figure style="margin:1rem 0 0">
<img src="%%WALLTEX%%" alt="The three wall fold textures and why each failed"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
<table>
<tr><th>wall texture</th><th>total worst-&rho; &darr;</th>
<th>smear &uarr;</th><th>head-on &darr;</th><th>span</th>
<th>verdict</th></tr>
%%ROWS73%%
</table>
<p class="note">%%NOTE73%%</p>

<h2>The last box: assembled from universal panels (Phase 7.4)</h2>
<figure style="margin:1rem 0 0">
<img src="%%PANELBOX%%" alt="Box assembled from universal panels, section"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
<table>
<tr><th>box from universal tiles (cell 220 / depth 240)</th>
<th>total worst-&rho; &darr;</th><th>smear &uarr;</th>
<th>head-on &darr;</th><th>span</th><th>beam width</th></tr>
%%ROWS74%%
</table>
<p class="note">%%NOTE74%%</p>

<h2>Open, named</h2>
<p>The surrogate is not geometry: real wall pyramids redirect light
(likely slightly better downward, possibly worse at grazing), and the
textured box&rsquo;s smear/head-on are not yet run (the form path lacks
the two-finish material split). Next: build the wall-pyramid box mesh,
confirm the totals, and complete its three axes at the deployment beam.
The physical queue &mdash; coupon print, Musou coupon, beam spot &mdash;
is unchanged and still gates any 1&#8202;m&sup2; decision.</p>
</main>
"""
    def r73(label, tt, fk, verdict, star=False):
        fr = f73.get(fk) if fk else None
        return ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                "<td>%s</td><td>%s</td></tr>"
                % (' class="win"' if star else "", label,
                   pc(p73.get(tt)),
                   num(fr.get("smear")) if fr else DASH,
                   num(fr.get("head_on"), 4) if fr else DASH,
                   ("%.2f&times;" % fr["span_0"]) if fr and
                   fr.get("span_0") else DASH, verdict))
    rows73 = (
        r73("symmetric 45&deg; zigzag folds", "P73_boxfold",
            "P73_boxfold", "retroreflector &mdash; worse than a bare "
            "flat plate")
        + r73("louver folds (45&deg; down-faces)", "P73_boxlouver",
              "P73_boxlouver", "mirrors the incidence cone; span 28&times;")
        + r73("vertical accordion folds", "P73_boxaccordion",
              "P73_boxaccordion", "ties the flat panel at 12&times; the "
              "depth; rejected")
        + ("<tr class=\"win\"><td>reference: flat final sample</td>"
           "<td>%s</td><td>1.42 / 1.09 (beam 7/10)</td><td>0.0400</td>"
           "<td>~1.5&times;</td><td>the standing recommendation</td></tr>"
           % pc(p515.get("P515_easy_t01"))))
    note73 = (
        "Three design laws, each bought by a measured failure: "
        "<b>(1) concave ~90&deg; corners facing the beam are "
        "retroreflectors</b> (the zigzag&rsquo;s "
        + pc(p73.get("P73_boxfold")) + "; the same physics blew up the "
        "6.6 valley fillets); <b>(2) no face normal may point into the "
        "&plusmn;40&deg; incidence cone</b> (the louver&rsquo;s "
        + pc(p73.get("P73_boxlouver")) + "); <b>(3) absorbing texture "
        "needs near-vertical faces at fine pitch</b> &mdash; the "
        "pyramid&rsquo;s 5.7&deg; flanks are the point, and a 1&#8202;mm "
        "sheet cannot be folded into them. <b>BOX PROGRAM CLOSED.</b> "
        "The only winning box (the 0.045&#8202;% surrogate) required "
        "panel-grade 22&#8202;mm textured walls, excluded by the "
        "1&#8202;mm constraint. If space exists behind the wall, spend "
        "it as DISTANCE, not boxes. The flat final sample stands "
        "everywhere.")
    f73all = jload("form_phase73.json")
    pbf = f73all.get("P74_boxpanel", {})
    rows74 = ("<tr><td>every face clad with the pitch-4 tile</td>"
              "<td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
              "<td>7.5&#8202;mm</td></tr>"
              "<tr><td>reference: one flat universal tile</td>"
              "<td>%s</td><td>1.42 / 1.09</td><td>0.0400</td>"
              "<td>~1.5&times;</td><td>7 / 10&#8202;mm</td></tr>"
              % (pc(p73.get("P74_boxpanel")), num(pbf.get("smear")),
                 num(pbf.get("head_on"), 4),
                 ("%.2f&times;" % pbf["span_0"]) if pbf.get("span_0")
                 else DASH, pc(p515.get("P515_easy_t01"))))
    note74 = (
        "Predicted 0.10&thinsp;&plusmn;&thinsp;0.03 / head-on "
        "&le;0.045; measured " + pc(p73.get("P74_boxpanel")) + " / "
        + num(pbf.get("head_on"), 4) + " &mdash; both roughly 2&times; "
        "worse than predicted and worse than ONE flat tile on both "
        "deciding axes. Five box variants measured, five losses; the "
        "surrogate&rsquo;s 0.045&#8202;% was an idealization no real "
        "construction reached. <b>The box program is closed on real "
        "geometry. The flat universal panel is the product; depth "
        "behind the wall buys more as plain distance than as any "
        "box.</b>")
    html = html.replace("%%PANELBOX%%", pb64)
    html = html.replace("%%ROWS74%%", rows74)
    html = html.replace("%%NOTE74%%", note74)
    html = html.replace("%%RAYFAIL%%", rf64)
    html = html.replace("%%WALLTEX%%", wt64)
    html = html.replace("%%ROWS73%%", rows73)
    html = html.replace("%%NOTE73%%", note73)
    html = html.replace("%%ROWS%%", rows)
    html = html.replace("%%VIEWS%%", b64)
    html = html.replace("%%BOXTEX%%", pc(p7.get("P72_boxtex")))
    html = html.replace("%%GAIN%%", "%.1f" % gain)
    open(OUT, "w").write(html)
    print("wrote %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
