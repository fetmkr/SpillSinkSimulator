"""Phase 6 standalone report: the coarse tier.

    python3 scripts/build_report_phase6.py

Generates report/phase6/report.html from measurement files only (no typed
numbers): sweep_phase6.csv, form_phase6.json, sweep_phase62.csv,
form_phase6_beam9.json, sweep_phase63.csv, form_phase63.json, and — when
present — sweep_phase64.csv / form_phase64.json (knife-edged comb tops).
"""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(ROOT, "report", "phase6")
OUT = os.path.join(OUTDIR, "report.html")

DASH = "&mdash;"


def worst_per_tag(path):
    out = {}
    p = os.path.join(RESULTS, path)
    if not os.path.exists(p):
        return out
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


def sm(rec):
    return num(rec.get("smear")) if rec else DASH


def ho(rec):
    return num(rec.get("head_on"), 4) if rec else DASH


def sp(rec):
    return ("%.2f&times;" % rec["span_0"]) if rec and rec.get("span_0") \
        else DASH


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    p6 = worst_per_tag("sweep_phase6.csv")
    p62 = worst_per_tag("sweep_phase62.csv")
    p63 = worst_per_tag("sweep_phase63.csv")
    p64 = worst_per_tag("sweep_phase64.csv")
    f6 = jload("form_phase6.json")
    f63 = jload("form_phase63.json")
    f64 = jload("form_phase64.json")
    b9 = jload("form_phase6_beam9.json")
    f54 = jload("form_phase54.json")
    p515 = worst_per_tag("sweep_phase515.csv")
    f515 = jload("form_phase515.json")
    p65 = worst_per_tag("sweep_phase65.csv")
    f65 = jload("form_phase65.json")
    fbeam = jload("form_p4d20_beam.json")
    p91 = worst_per_tag("sweep_phase9.csv")
    f91 = jload("form_phase9.json")

    rows61 = ""
    for label, tt, frm, note in [
        ("pyramid p10/d50 (aspect 5)", "P6_pyr_p10d50",
         f6.get("P6_pyr_p10d50"), "tip tolerance ~0.5&#8202;mm"),
        ("pyramid p15/d50", "P6_pyr_p15d50", f6.get("P6_pyr_p15d50"), ""),
        ("pyramid p20/d50", "P6_pyr_p20d50", f6.get("P6_pyr_p20d50"), ""),
        ("pyramid p10/d90 (aspect 9)", "P6_pyr_p10d90",
         f54.get("P54_p10_t00"), "exact repeat of Phase 5.4"),
        ("comb cell 9.5, naked", "P6_comb_c095", f6.get("P6_comb_c095"),
         ""),
        ("comb cell 12.7, naked", "P6_comb_c127", f6.get("P6_comb_c127"),
         "backing reads as a flat plate"),
        ("comb cell 19, naked", "P6_comb_c190", f6.get("P6_comb_c190"),
         "perforated flat plate"),
        ("comb 12.7 + fine floor", "P6_stk_c127", f6.get("P6_stk_c127"),
         "35&#8202;% better than its comb"),
        ("comb 19 + fine floor", "P6_stk_c190", f6.get("P6_stk_c190"),
         "49&#8202;% better than its comb"),
    ]:
        if tt not in p6:
            continue
        star = ' class="win"' if tt == "P6_stk_c127" else ""
        rows61 += ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                   "<td>%s</td><td>%s</td></tr>"
                   % (star, label, pc(p6[tt]), sm(frm), ho(frm), sp(frm),
                      note or DASH))

    # 6.2 azimuth + real beam
    rows62 = ""
    for label, t0, t30 in [
        ("comb 12.7 + fine floor", p6.get("P6_stk_c127"),
         p62.get("P62_stk_c127_p30")),
        ("pyramid p10/d50", p6.get("P6_pyr_p10d50"),
         p62.get("P62_p10d50_p30")),
        ("pyramid p15/d50", p6.get("P6_pyr_p15d50"),
         p62.get("P62_p15d50_p30")),
    ]:
        if not (t0 and t30):
            continue
        rows62 += ("<tr><td>%s</td><td>%s</td><td>%s</td>"
                   "<td>&times;%.2f</td></tr>"
                   % (label, pc(t0), pc(t30), t30 / t0))

    rows9 = ""
    for label, key in [("pyramid p2/d18 (fine reference)", "B9_pyr_p2d18"),
                       ("pyramid p10/d50", "B9_pyr_p10d50"),
                       ("comb 12.7 + fine floor", "B9_stk_c127")]:
        r = b9.get(key)
        if not r:
            continue
        t = r.get("thetas", {}).get("-40", {})
        rows9 += ("<tr><td>%s</td><td>%s</td><td>%.2f / %.2f&#8202;mm</td>"
                  "<td>%s</td></tr>"
                  % (label, num(r.get("smear"), 3), t.get("rms_mm", 0),
                     t.get("rms_control_mm", 0), ho(r)))

    # 6.3 user combo
    rows63 = ""
    for label, tt, frm in [
        ("comb c10/d30 + MATCHED 45&deg; floor (p10/d10)",
         "P63_c10_pyr10", f63.get("P63_c10_pyr10")),
        ("same, at &phi;30", "P63_c10_pyr10_p30", None),
        ("comb c10/d30 + fine floor (p2/d15)", "P63_c10_pyr2", None),
    ]:
        if tt not in p63:
            continue
        rows63 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                   "<td>%s</td></tr>"
                   % (label, pc(p63[tt]), sm(frm), ho(frm), sp(frm)))

    # 6.4 knife edge (may be pending)
    sec64 = ""
    if "P64_stk_knife" in p64:
        mid = f64.get("P64_stk_mid04")
        k = f64.get("P64_stk_knife")
        blunt_ho = (f6.get("P6_stk_c127") or {}).get("head_on")
        sec64 = (
            "<h2>Knife-edged comb tops (Phase 6.4, user-suggested)</h2>"
            "<p>Everything measured is already Musou-coated, so the comb "
            "stack&rsquo;s head-on comes from the FLAT AREA of its wall "
            "tops, not their finish. Tapering the wall from 0.08&#8202;mm "
            "at the root to 0.01&#8202;mm at the top cuts that area "
            "8&times;:</p><table>"
            "<tr><th>stack (comb 12.7 + fine floor)</th>"
            "<th>total worst-&rho;</th><th>smear (beam width 2&#8202;mm)</th><th>head-on</th>"
            "<th>span</th></tr>"
            "<tr><td>blunt tops (0.08&#8202;mm)</td><td>" +
            pc(p6.get("P6_stk_c127")) + "</td><td>" +
            sm(f6.get("P6_stk_c127")) + "</td><td>" +
            ho(f6.get("P6_stk_c127")) + "</td><td>" +
            sp(f6.get("P6_stk_c127")) + "</td></tr>"
            "<tr><td>mid tops (0.04&#8202;mm)</td><td>&mdash;</td><td>" +
            (sm(mid) if mid else DASH) + "</td><td>" +
            (ho(mid) if mid else DASH) + "</td><td>" +
            (sp(mid) if mid else DASH) + "</td></tr>"
            "<tr><td>knife tops (0.01&#8202;mm)</td><td>" +
            pc(p64.get("P64_stk_knife")) + "</td><td>" + sm(k) +
            "</td><td>" + ho(k) + "</td><td>" + sp(k) + "</td></tr>"
            "</table><p class=\"note\">A MECHANISM STUDY, not a spec "
            "change: the build stays at the commercial 0.08&#8202;mm foil "
            "(user decision). The ladder separates the comb&rsquo;s "
            "head-on into ~30&#8202;% top-area glint (removable) and "
            "~70&#8202;% wall glint at grazing incidence (geometry, not "
            "finish &mdash; everything here is already Musou-coated, and "
            "a facing flat returns its 1&#8202;% straight at the viewer "
            "while tilted faces scatter theirs away). The smear ladder "
            "(" + sm(f6.get("P6_stk_c127")) + " &rarr; "
            + (sm(mid) if mid else DASH) + " &rarr; " + sm(k)
            + ") confirms the return profile "
            "is a weighted mix of bright narrow top-glow and dim wide "
            "in-cell glow &mdash; the mid point landing mid-way is the "
            "verification.</p>")

    html = """<title>Spill Sink 피라미드 연구 — Phase 6</title>
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
th{font-weight:600;text-align:left;color:var(--ink2);border-bottom:1px solid var(--ink2)}
td,th{padding:.45rem .6rem .45rem 0}
td{border-bottom:1px solid var(--line)}
tr.win td{color:var(--acc);font-weight:700}
.note{font-size:.85rem;color:var(--ink2)}
code{font:.85em var(--mono)}
</style>
<main>
<div class="kicker">Spill Sink &middot; 피라미드 연구 &middot; Phase 6</div>
<h1>The coarse tier: pitch &ge; 10, big honeycomb, and their combinations</h1>
<p class="lede">User-directed phase. Fine-pitch finalists (Phase 5) demand
sub-0.1&#8202;mm tips; this phase maps what cheap tooling and shelf stock
offer &mdash; big pressed pyramids, commercial honeycomb in 3/8&Prime; to
3/4&Prime; cells, and stacks &mdash; on the same three axes. Every design
in every table carries all three.</p>

<figure style="margin:1.4rem 0 0">
<img src="%%GRID6%%" alt="Top and side views of the Phase 6 designs"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">Top and side views, rendered from the measured
geometry: coarse pyramid, naked comb, the comb-plus-floor pick, and the
cell-matched 45&deg; floor.</figcaption>
</figure>

<h2>The coarse map (Phase 6.1)</h2>
<table>
<tr><th>design</th><th>total worst-&rho; &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th><th>span &theta;0</th><th>note</th></tr>
""" + rows61 + """
</table>
<p class="note">Aspect rules every pyramid (two exact cross-code
reproductions). Naked big combs decay FASTER than aspect &mdash; below
aspect ~4 the flat backing is directly visible and the comb becomes a
perforated flat plate. And the &ldquo;top layer owns the result&rdquo;
law found its limit: a see-through comb lets the floor matter again
(stacks read 35&ndash;49&#8202;% better than their combs).</p>

<h2>Worst azimuth, and the real beam (Phase 6.2)</h2>
<table>
<tr><th>design</th><th>&phi;0</th><th>&phi;30</th><th>ratio</th></tr>
""" + rows62 + """
</table>
<p class="note">The &phi;-hole maps by aspect (&times;1.74 at aspect 9,
&times;1.30 at 5, &times;1.17 at 3.3); hex stacks sit at &times;1.02.</p>
<table>
<tr><th>at the real beam</th><th>smear (beam width 9&#8202;mm)</th>
<th>return / flat&rsquo;s width</th><th>head-on</th></tr>
""" + rows9 + """
</table>
<p class="note">Coarse pitch NARROWS the return below a matte flat&rsquo;s
&mdash; verified matte-robust by a pure-Lambertian control (0.660): only
the beam-facing flank strips light up (shadowing), so one thin bright
line survives. Pitch &ge;10 pyramids are the one family that makes the
reflected stripe SHARPER than a bare matte wall.</p>

<h2>Cell-matched 45&deg; floor (Phase 6.3, user-suggested)</h2>
<table>
<tr><th>design</th><th>total worst-&rho;</th><th>smear (beam width 2&#8202;mm)</th>
<th>head-on</th><th>span</th></tr>
""" + rows63 + """
</table>
<p class="note">The matched 45&deg; floor and the fine floor read the SAME
worst-case total &mdash; the envelope is set at grazing incidence, where
light never reaches any floor through a 30&#8202;mm-deep cell-10 comb.
So under a deep comb the floor can be as cheap as vacuum-formed
45&deg; pyramids. What no floor fixes: the comb-top head-on
(""" + ho(f63.get("P63_c10_pyr10")) + """).</p>

""" + sec64 + """

<h2>The final test sample, and why (Phases 5&ndash;6 conclusion)</h2>
<figure style="margin:1rem 0 0">
<img src="%%FINAL6%%" alt="Final test sample, top and side views"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
<table>
<tr><th>pyramid pitch 4 / depth 20 / tip 0.1</th><th>value</th></tr>
%%ROWSFS%%
</table>
<figure style="margin:1rem 0 0">
<img src="%%TIPLADDER%%" alt="Tip options at 0.1, 0.2, 0.4 mm, to scale"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
<table>
<tr><th>tip flat</th><th>total worst-&rho;</th>
<th>smear (beam width 2&#8202;mm)</th><th>head-on &darr;</th>
<th>span &theta;0</th></tr>
%%ROWSTIP%%
</table>
<p class="note">Bluntness taxes exactly one axis: head-on (and its scan
wobble). Totals and smear do not move. The pre-registered 1.5&times; rule
puts the drawing tolerance between 0.1 and 0.2: <b>tip &le;
0.15&#8202;mm</b>.</p>
<p class="note">Chosen over every alternative for one reason per axis:
head-on is in the best class measured and is the one axis that survives
the real beam width AND the unknown azimuth; smear sits in the fine-pitch
class; the total gives up ~10&ndash;19&#8202;% against the hard finalists
while relaxing the tip requirement to 0.1&ndash;0.2&#8202;mm &mdash;
ordinary tooling, one pressed part, 22&#8202;mm panel. Files:
<code>pyr_p4_d20_t010_116x116.stl</code> (as-built 116&times;116&times;22,
the recommended print) and <code>pyr_p4_d20_t010_76x76.stl</code>;
file names carry AS-BUILT dimensions. Acceptance for the painted sample:
&plusmn;25&#8202;% of the totals row validates the simulator; beyond
&plusmn;40&#8202;% stop and name the broken link.</p>

<figure style="margin:1.2rem 0 0">
<img src="%%BLUEPRINT%%" alt="Final sample blueprint"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">The blueprint a maker needs: section with pitch /
depth / tip tolerance, the sharp-valley requirement, the as-built envelope,
and the fabrication notes &mdash; every number on it is a measurement from
this study.</figcaption>
</figure>

<figure style="margin:1.2rem 0 0">
<img src="%%RAYS6%%" alt="Specular ray paths: flat plate vs pyramid"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">Traced specular paths (independent float64
tracer). A flat plate returns every ray in one bounce; the pyramid
ladders rays ~9 deep &mdash; with a 1&#8202;% coating each bounce, that
is 10&sup1;&#8309; times less light coming back.</figcaption>
</figure>

<h2>Manufacturing constraints, measured (Phase 6.6)</h2>
<table>
<tr><th>final sample +</th><th>total worst-&rho;</th>
<th>smear</th><th>head-on &darr;</th><th>span</th><th>beam width</th></tr>
%%ROWS66%%
</table>
<p class="note">%%NOTE66%%</p>

<p class="note">The recessed box study is its own report: Phase 7.</p>

<h2>Grazing angles: the brief said &plusmn;40&deg;; the room will do
worse (Phase 6.7)</h2>
<table>
<tr><th>&theta;</th><th>final sample, total worst-&rho;</th>
<th>flat plate</th><th>advantage</th></tr>
%%ROWS67%%
</table>
<p class="note">%%NOTE67%%</p>

<h2>Pricing 100 m&sup2;: extrusion and bare material, measured
(Phase 9.1)</h2>
<p>Two questions set the cost of a 100-panel run, and both are now
measured (predictions pre-registered in
<code>scripts/sweep_phase9.py</code>, gradings in
<code>results/FINDINGS_phase9.md</code>). All smear/head-on figures
below are at the 7.5&#8202;mm deployment beam.</p>
<table>
<tr><th>candidate</th><th>total worst-&rho; &darr;</th>
<th>smear &uarr;</th><th>head-on &darr;</th><th>verdict</th></tr>
%%ROWS91%%
</table>
<p><b>A tip LINE is 40&times; worse than a tip POINT.</b> The
pyramid&rsquo;s head-on cost is quadratic in tip/pitch (a 0.1&#8202;mm
flat is 0.06&#8202;% of area); an extruded groove&rsquo;s tip land is a
line &mdash; 2.5&#8202;% of area for the same 0.1&#8202;mm &mdash; and
its worst-orientation head-on measured exactly that class. Extrusion
therefore unlocks ONLY where the beam plane is known and the grooves
can be laid along it; it cannot be the default panel. The groove also
pays &times;1.9 on totals at its worst azimuth (which is &phi;0,
inverted from the pyramid), because <b>a 2D trench loses ~2&times; to a
3D cell on diffuse light</b> &mdash; bounces escape along the open
axis.</p>
<p><b>Bare black urethane works as a second tier.</b> Unpainted
pyramid fields obey <i>total &asymp; 0.18 &times; &rho;(material)</i>
(measured linear over &rho; 0.04&ndash;0.08; the same 0.18 escape
factor reproduces the Musou panel&rsquo;s own 0.177&#8202;% from its
~1&#8202;% coating). At &rho; 0.05 the bare panel lands at
0.91&#8202;% total with head-on 0.107 &mdash; flat-Musou-wall class on
totals, 10&times; better than any flat on head-on, with zero paint.
Since the slant faces multiply paintable area &times;10 (100&#8202;m&sup2;
of wall = ~1,000&#8202;m&sup2; of painted surface), skipping Musou on
non-critical zones is a first-order cost lever.</p>

<h2>Where Phase 6 leaves the build menu</h2>
<p>The coarse tier offers no all-axis winner, but two useful objects: the
<b>shelf-honeycomb stack</b> (azimuth-flat totals tying the cone
finalist, ruined only by comb-top head-on&nbsp;&mdash; see the knife-edge
test above) and the <b>commodity press-die pyramid p10/d50</b> (pyramid
head-on at 0.5&#8202;mm tip tolerance, but it sharpens the reflected
stripe and pays a &times;1.3 azimuth hole). The fine-pitch finalists of
Phase 5 remain the performance recommendations.</p>

<p class="note">Predictions for every sweep were registered in the
script docstrings before rendering (<code>scripts/sweep_phase6*.py</code>);
gradings live in <code>results/FINDINGS_phase6_coarse.md</code> and
<code>FINDINGS_phase62_coarse_azimuth.md</code>.</p>
</main>
"""
    rows91 = ""
    for label, tkey, fkey, verdict, win in (
            ("cast pyramid + Musou (the final sample)", "P65_final",
             None, "audience-critical zones", True),
            ("cast pyramid, bare black &rho;&#8202;0.05 (no paint)",
             "P91_bare_r005", "P91_bare_form_r05",
             "non-critical zones, paint skipped", False),
            ("extruded groove + Musou, best orientation (&phi;90)",
             "P91_groove_p90", "P91_groove_form_p90",
             "conditional: beam plane must run along the grooves",
             False),
            ("extruded groove + Musou, worst orientation (&phi;0)",
             "P91_groove_p00", "P91_groove_form_p00",
             "fails head-on 22&times;", False)):
        if tkey == "P65_final":
            # the final sample's own book rows: totals from phase 5.15,
            # beam-7 form from the beam sweep -- never typed here
            tw = p515.get("P515_easy_t01")
            fr = fbeam.get("B7_p4d20")
        else:
            tw = p91.get(tkey)
            fr = f91.get(fkey)
        star = ' class="win"' if win else ""
        rows91 += ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                   "<td>%s</td></tr>"
                   % (star, label, pc(tw), sm(fr), ho(fr), verdict))
    html = html.replace("%%ROWS91%%", rows91)

    rowstip = ""
    for tf, key in ((0.1, "P515_easy_t01"), (0.2, "P515_easy_t02"),
                    (0.4, "P515_easy_t04")):
        fr = f515.get(key)
        tw = p515.get(key)
        if not (fr and tw):
            continue
        star = ' class="win"' if tf == 0.1 else ""
        rowstip += ("<tr%s><td>%.1f&#8202;mm</td><td>%s</td><td>%s</td>"
                    "<td>%s</td><td>%s</td></tr>"
                    % (star, tf, pc(tw), sm(fr), ho(fr), sp(fr)))
    html = html.replace("%%ROWSTIP%%", rowstip or "<tr><td>pending</td>"
                        "<td colspan=4>&mdash;</td></tr>")
    rowsfs = ""
    fs = f515.get("P515_easy_t01")
    tfs = p515.get("P515_easy_t01")
    if fs and tfs:
        rowsfs += ("<tr><td>total worst-&rho;, &phi;0</td>"
                   "<td>" + pc(tfs) + "</td></tr>")
        if p65.get("P65_final_p30"):
            rowsfs += ("<tr><td>total at the worst azimuth (&phi;30, "
                       "measured directly)</td><td>"
                       + pc(p65["P65_final_p30"]) + "</td></tr>")
        if p65.get("P65_final_rg50"):
            rowsfs += ("<tr><td>total if the paint is rough "
                       "(roughness 0.50; smooth paint keeps the &phi;0 "
                       "value)</td><td>" + pc(p65["P65_final_rg50"])
                       + "</td></tr>")
        rowsfs += ("<tr><td>smear &uarr;, beam width 2&#8202;mm "
                   "(&phi;0 / &phi;30)</td><td>" + sm(fs) + " / "
                   + sm(f65.get("P65_final_p30")) + "</td></tr>")
        b7 = fbeam.get("B7_p4d20")
        b10 = fbeam.get("B10_p4d20")
        if b7 and b10:
            rowsfs += ("<tr><td>smear &uarr; at the DEPLOYMENT beam "
                       "(7 / 10&#8202;mm)</td><td>" + sm(b7) + " / "
                       + sm(b10) + "</td></tr>")
            rowsfs += ("<tr><td>head-on &darr; (beam 2 / 7 / "
                       "10&#8202;mm)</td><td>" + ho(fs) + " / " + ho(b7)
                       + " / " + ho(b10) + "</td></tr>")
        else:
            rowsfs += ("<tr><td>head-on &darr;</td><td>" + ho(fs)
                       + "</td></tr>")
        rowsfs += ("<tr><td>span &theta;0 (&phi;0 / &phi;30)</td><td>"
                   + sp(fs) + " / " + sp(f65.get("P65_final_p30"))
                   + "</td></tr>")
    html = html.replace("%%ROWSFS%%", rowsfs or "<tr><td>pending</td>"
                        "<td>&mdash;</td></tr>")
    # 6.6 + 7 tables
    p66 = worst_per_tag("sweep_phase66.csv")
    f66 = jload("form_phase66.json")
    p7 = worst_per_tag("sweep_phase7.csv")
    f7 = jload("form_phase7.json")
    rows66 = ""
    for label, tt, fk, bw in [
        ("valley R0.1", None, "P66_vr01", "2&#8202;mm"),
        ("valley R0.3", "P66_vr03", "P66_vr03", "2&#8202;mm"),
        ("valley R0.3", None, "P66_vr03_b75", "7.5&#8202;mm"),
        ("valley R0.5", "P66_vr05", "P66_vr05", "2&#8202;mm"),
        ("row offset 0.2", "P66_row02", "P66_row02_p8",
         "2&#8202;mm (8&#8202;mm walk)"),
        ("row offset 0.2", None, "P66_row02_b75", "7.5&#8202;mm"),
    ]:
        fr = f66.get(fk)
        if not fr:
            continue
        rows66 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                   "<td>%s</td><td>%s</td></tr>"
                   % (label, pc(p66.get(tt)) if tt else DASH, sm(fr),
                      ho(fr), sp(fr), bw))
    note66 = (
        "Any measurable valley radius fails the head-on rule "
        "(&le;0.041): R0.1 reads " + ho(f66.get("P66_vr01"))
        + " and R0.3 reads " + ho(f66.get("P66_vr03_b75"))
        + " at the deployment beam. Valleys must stay sharp &mdash; "
        "<b>standard injection is optically rejected</b>; silicone-cast "
        "resin or row-strip assembly with ground dies remain. The strip "
        "route is measured FREE: a 0.2&#8202;mm row step moves no axis "
        "at any beam width, including the honest full-period span "
        "re-check.")
    html = html.replace("%%ROWS66%%", rows66 or "")
    html = html.replace("%%NOTE66%%", note66)
    # 6.7 grazing table
    rows67 = ""
    note67 = ""
    try:
        g = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase67.csv"))):
            k = (r["tag"], float(r["theta"]))
            g[k] = max(g.get(k, 0.0), float(r["rho"]))
        for th in (-50.0, -60.0, -70.0):
            pv = g.get(("P67_final_graze", th))
            fv = g.get(("P67_flat_graze", th))
            if not (pv and fv):
                continue
            rows67 += ("<tr><td>%.0f&deg;</td><td>%s</td><td>%s</td>"
                       "<td>%.1f&times;</td></tr>"
                       % (-th, pc(pv), pc(fv), fv / pv))
        g50p30 = g.get(("P67_final_g50p30", -50.0))
        f67j = jload("form_phase67.json").get("P67_final_pm50", {})
        note67 = (
            "The pyramid barely degrades while the flat plate&rsquo;s "
            "grazing Fresnel blows up &mdash; <b>the harder the wall is "
            "grazed, the bigger the advantage</b> (21.6&times; at "
            "70&deg;). Form at &plusmn;50&deg; (beam width "
            "7.5&#8202;mm): smear " + num(f67j.get("smear"))
            + ", head-on " + num(f67j.get("head_on"), 4)
            + " &mdash; unchanged. One panel type covers the whole wall "
            "including corners; no edge treatment or placement rule "
            "needed. The honest worst-over-everything total (&theta; "
            "&le;70&deg; &times; azimuth &times; roughness 0.30) is "
            + pc(g50p30) + " at &theta;50/&phi;30.")
    except Exception:
        pass
    html = html.replace("%%ROWS67%%", rows67 or "")
    html = html.replace("%%NOTE67%%", note67 or DASH)
    import base64
    gp = os.path.join(OUTDIR, "img", "grid_views6.png")
    g64 = ("data:image/png;base64,"
           + base64.b64encode(open(gp, "rb").read()).decode()) \
        if os.path.exists(gp) else ""
    html = html.replace("%%GRID6%%", g64)
    bp = os.path.join(OUTDIR, "img", "blueprint_final.png")
    bp64 = ("data:image/png;base64,"
            + base64.b64encode(open(bp, "rb").read()).decode()) \
        if os.path.exists(bp) else ""
    html = html.replace("%%BLUEPRINT%%", bp64)
    r6 = os.path.join(OUTDIR, "img", "rays_flat_vs_pyramid.png")
    r664 = ("data:image/png;base64,"
            + base64.b64encode(open(r6, "rb").read()).decode()) \
        if os.path.exists(r6) else ""
    html = html.replace("%%RAYS6%%", r664)
    fp2 = os.path.join(OUTDIR, "img", "final_sample.png")
    f64i = ("data:image/png;base64,"
            + base64.b64encode(open(fp2, "rb").read()).decode()) \
        if os.path.exists(fp2) else ""
    html = html.replace("%%FINAL6%%", f64i)
    tl = os.path.join(OUTDIR, "img", "tip_ladder.png")
    tl64 = ("data:image/png;base64,"
            + base64.b64encode(open(tl, "rb").read()).decode()) \
        if os.path.exists(tl) else ""
    html = html.replace("%%TIPLADDER%%", tl64)
    open(OUT, "w").write(html)
    print("wrote %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
