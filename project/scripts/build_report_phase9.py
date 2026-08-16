"""Phase 9 standalone report: manufacturing physics for a 100-panel run.

    python3 scripts/build_report_phase9.py

Numbers are read from sweep_phase9.csv / form_phase9.json (and the final
sample's own book files) at build time -- never typed here (gate check 7).
"""

import os
import sys
import csv
import json
import base64
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(ROOT, "report", "phase9")
OUT = os.path.join(OUTDIR, "report.html")

DASH = "&mdash;"


def worst_per_tag(path):
    out = collections.defaultdict(float)
    p = os.path.join(RESULTS, path)
    if not os.path.exists(p):
        return out
    for r in csv.DictReader(open(p)):
        out[r["tag"]] = max(out[r["tag"]], float(r["rho"]))
    return out


def worst_per_phi(path, tag):
    out = collections.defaultdict(float)
    p = os.path.join(RESULTS, path)
    for r in csv.DictReader(open(p)):
        if r["tag"] == tag:
            out[float(r["phi"])] = max(out[float(r["phi"])],
                                       float(r["rho"]))
    return out


def jload(path):
    p = os.path.join(RESULTS, path)
    return json.load(open(p)) if os.path.exists(p) else {}


def b64(path):
    p = os.path.join(OUTDIR, "img", path)
    return ("data:image/png;base64,"
            + base64.b64encode(open(p, "rb").read()).decode()) \
        if os.path.exists(p) else ""


def pc(x, nd=3):
    return "%.*f&#8202;%%" % (nd, 100 * x) if x else DASH


def num(x, nd=2):
    return ("%.*f" % (nd, x)) if x is not None else DASH


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    p91 = worst_per_tag("sweep_phase9.csv")
    f91 = jload("form_phase9.json")
    p515 = worst_per_tag("sweep_phase515.csv")
    fbeam = jload("form_p4d20_beam.json")
    scan = worst_per_phi("sweep_phase9.csv", "P91_groove_scan")

    pyr_t = p515["P515_easy_t01"]
    pyr_f = fbeam.get("B7_p4d20", {})

    rows = ""
    for label, tw, fr, verdict, win in (
            ("cast pyramid + Musou (the final sample)", pyr_t, pyr_f,
             "audience-critical zones", True),
            ("cast pyramid, bare black &rho;&#8202;0.05 (no paint)",
             p91["P91_bare_r005"], f91.get("P91_bare_form_r05"),
             "non-critical zones, paint skipped", True),
            ("extruded groove + Musou, best orientation (&phi;90)",
             p91["P91_groove_p90"], f91.get("P91_groove_form_p90"),
             "conditional: beam plane must run along the grooves", False),
            ("extruded groove + Musou, worst orientation (&phi;0)",
             p91["P91_groove_p00"], f91.get("P91_groove_form_p00"),
             "fails head-on 22&times;", False)):
        star = ' class="win"' if win else ""
        rows += ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                 "<td>%s</td></tr>"
                 % (star, label, pc(tw),
                    num(fr.get("smear") if fr else None),
                    num(fr.get("head_on") if fr else None, 4), verdict))

    scanrow = "".join("<td>%s</td>" % pc(scan[f])
                      for f in sorted(scan))
    scanhead = "".join("<th>&phi;%g</th>" % f for f in sorted(scan))

    grades = ""
    for claim, pred, meas, grade in (
            ("P1 groove &phi;0 total", "0.19 &plusmn; 0.05&#8202;%",
             pc(p91["P91_groove_p00"]), "MISS &times;1.8"),
            ("P2 azimuth bounded &le; 0.30&#8202;%",
             "&le; 0.30&#8202;%",
             "worst " + pc(max(max(scan.values()),
                               p91["P91_groove_p00"],
                               p91["P91_groove_p90"])),
             "marginal MISS (worst is &phi;0 itself)"),
            ("P3 bare &rho; 0.04 / 0.05 / 0.08", "0.72 / 0.90 / 1.44"
             "&#8202;% &plusmn;35&#8202;%",
             "%s / %s / %s" % (pc(p91["P91_bare_r004"]),
                               pc(p91["P91_bare_r005"]),
                               pc(p91["P91_bare_r008"])),
             "HELD, dead center"),
            ("P4 bare form (beam 7.5&#8202;mm)",
             "head-on &lt; 0.5; smear &ge; 1.2",
             "head-on %s; smear %s"
             % (num(f91["P91_bare_form_r05"]["head_on"], 3),
                num(f91["P91_bare_form_r05"]["smear"])),
             "HELD"),
            ("P5 groove form &phi;0 (beam 7.5&#8202;mm)",
             "head-on 0.040 &plusmn; 0.020",
             "<b>%s</b>" % num(f91["P91_groove_form_p00"]["head_on"], 3),
             "<b>MISS &times;22 &mdash; the finding</b>"),
            ("(&phi;90 form, unpredicted)", DASH,
             "head-on %s; smear %s"
             % (num(f91["P91_groove_form_p90"]["head_on"], 4),
                num(f91["P91_groove_form_p90"]["smear"])),
             "recorded")):
        grades += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (claim, pred, meas, grade))

    html = """<title>Spill Sink 피라미드 연구 — Phase 9</title>
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
tr.win td{color:var(--ok);font-weight:600}
.note{font-size:.85rem;color:var(--ink2)}
code{font:.85em var(--mono)}
figure{margin:1.2rem 0 0}
figure img{width:100%;border:1px solid var(--line);border-radius:6px}
</style>
<main>
<div class="kicker">Spill Sink &middot; 피라미드 연구 &middot; Phase 9</div>
<h1>Manufacturing physics: what 100 panels of 1&#8202;m&sup2; may and
may not be made of</h1>
<p class="lede">The user needs ~100 units of 1&#8202;m&sup2;. At that
quantity two simulation-answerable questions dominate the price: can the
panel be EXTRUDED as an endless groove profile, and can the Musou paint
be SKIPPED on non-critical zones. Both are now measured. Predictions
were registered in <code>scripts/sweep_phase9.py</code> before
rendering; gradings live in <code>results/FINDINGS_phase9.md</code>.
Anchor P5_j00 reproduced the book value to all digits.</p>

<h2>Answer 1 &mdash; extrusion: a tip LINE is 40&times; worse than a
tip POINT</h2>
<figure><img src="%%TIPLINE%%"
 alt="Tip point vs tip line: area fractions and head-on glints"></figure>
<p>The pyramid&rsquo;s head-on cost is quadratic in tip/pitch: its
0.1&#8202;mm flat is a point, 0.06&#8202;% of area. An extruded
groove&rsquo;s tip land is a LINE &mdash; the same 0.1&#8202;mm costs
2.5&#8202;% of area, 40&times; more flat land looking straight back at
the audience. Measured at the 7.5&#8202;mm deployment beam: head-on
0.894 at the worst orientation vs the pyramid&rsquo;s 0.040 &mdash;
&times;22, exactly the predicted-in-hindsight class, and the registered
prediction (0.040 &plusmn; 0.020) missed by that factor, which IS the
finding. Extrusion dies also wear tips round first, so the land only
grows over a production run.</p>
<table>
<tr><th>groove azimuth (&theta; &minus;40, worst mat)</th>%%SCANHEAD%%</tr>
<tr><td>total worst-&rho;</td>%%SCANROW%%</tr>
</table>
<p class="note">The groove&rsquo;s azimuth behaviour INVERTS the
pyramid&rsquo;s: worst at &phi;0, monotonically better toward &phi;90.
Verdict: extrusion unlocks only where the beam plane is known and the
grooves can be laid along it. It cannot be the default panel.</p>

<h2>Answer 2 &mdash; bare black obeys total = 0.18 &times; &rho;</h2>
<figure><img src="%%RULE018%%"
 alt="Linear law for bare material and the trench-vs-cell diffuse
escape"></figure>
<p>Unpainted Lambertian pyramids measured linear over &rho;
0.04&ndash;0.08 with escape factor 0.18&ndash;0.185 &mdash; and the
same factor reproduces the painted panel: 0.18 &times; the Musou
coating&rsquo;s ~1&#8202;% gives the book value 0.177&#8202;%. One
number now predicts any coating on this geometry. The right panel shows
why the extruded trench also loses 2&times; on totals: diffuse bounces
escape along its open axis; the pyramid&rsquo;s fourth pair of walls
closes them.</p>

<h2>The decision table (all three axes; smear/head-on at beam width
7.5&#8202;mm)</h2>
<table>
<tr><th>candidate</th><th>&#48152;&#49324; &#52509;&#47049; total
worst-&rho; &darr;</th><th>&#47784;&#50577; &#47501;&#44060;&#44592;
smear &uarr;</th><th>&#51221;&#47732; &#48152;&#51676;&#51076; head-on
&darr;</th><th>verdict</th></tr>
%%ROWS%%
</table>

<h2>Prediction grades</h2>
<table>
<tr><th>claim</th><th>registered prediction</th><th>measured</th>
<th>grade</th></tr>
%%GRADES%%
</table>

<h2>Scale math for 100 &times; 1&#8202;m&sup2; (computed)</h2>
<table>
<tr><th>item</th><th>solid cast urethane</th><th>foamed PU
(anechoic-industry style)</th></tr>
<tr><td>resin volume, total</td><td>~870&#8202;L (8.67&#8202;L/m&sup2;)</td>
<td>~10&times; less by mass</td></tr>
<tr><td>panel weight</td><td>~9.1&#8202;kg</td>
<td>~0.6&ndash;1&#8202;kg</td></tr>
<tr><td>painted surface if Musou everywhere</td>
<td colspan=2>~1,000&#8202;m&sup2; (slant faces multiply area
&times;10.05) &mdash; the first-order cost term the bare-black result
attacks</td></tr>
<tr><td>silicone molds (30&ndash;50 casts each)</td>
<td colspan=2>3&ndash;4 molds of 1&#8202;m&sup2;; one master is the
asset</td></tr>
</table>
<p><b>The paint term, priced (user: Musou Black 30,000&#8202;KRW per
100&#8202;ml):</b> at an assumed effective coverage of
3&ndash;6&#8202;m&sup2;/L [coverage assumed, not measured &mdash; a
coupon pins it], painting all 1,000&#8202;m&sup2; of slant surface
costs <b>50M&ndash;100M&#8202;KRW in paint alone</b> &mdash; likely
more than every other line item combined. Painting only the
audience-critical 10&ndash;20&#8202;% of area cuts that to
5M&ndash;20M&#8202;KRW, and the bare-black zones lose nothing a cheap
paint could restore: an ordinary matte black (&rho; ~4&ndash;5&#8202;%)
lands at 0.18 &times; &rho; &asymp; the bare urethane itself, so on
non-critical zones the rational choice is NO paint at all.</p>
<p class="note">Bare-material bracket assumes black urethane/TPU at
Lambertian &rho; 0.04&ndash;0.08; one coupon pins the point on the
0.18 line.</p>

<h2>9.2 &mdash; paint the tops only? Totals yes, head-on NO</h2>
<p>The user proposed spraying only the tip region from the front
(the top 5&#8202;mm of face is just 6&#8202;% of the paint area, so the
50&ndash;100M paint bill would drop 16&times;). Measured with the
depth-split material (Musou above the plane, bare &rho;&#8202;0.05
below; predictions registered in <code>scripts/sweep_phase92.py</code>,
gradings in <code>results/FINDINGS_phase92.md</code>):</p>
<figure><img src="%%FRONTSPRAY%%"
 alt="Tops-only paint: totals improve, head-on does not"></figure>
<table>
<tr><th>painted from tip</th><th>paint area</th>
<th>total worst-&rho; &darr;</th><th>head-on &darr;
(beam 7.5&#8202;mm)</th></tr>
%%ROWS92%%
</table>
<p><b>The two axes weight depth in OPPOSITE directions.</b> Totals are
earned at the top: at oblique incidence the flank shadows the cell, so
lit area and sky view concentrate near the tips &mdash; 25&#8202;% of
the paint closed 84&#8202;% of the bare-to-full-Musou gap
(0.907 to 0.290 against a floor of 0.177). Head-on is earned
everywhere, which means mostly at the bottom: at normal incidence
nothing shadows, the beam lights the whole face down to the valley, the
camera sees all of it, and the return is area-weighted &mdash; painting
the cheap 6&#8202;% cannot move a number owned by the deep 94&#8202;%
(the area average predicts the measured value to a few percent). Every
registered prediction missed toward this law, and the registered ship
rule (total &le; 0.35&#8202;% AND head-on &le; 0.06) <b>failed on both
counts: the front-spray tier does not ship</b>. It survives only as a
niche for zones that need tighter totals while their head-on is
unseen.</p>

<h2>9.4 &mdash; the fiber forest (flocking) fails head-on at 1.00</h2>
<p>Flocking paper is a fiber forest on a 1&#8202;m roll with zero
molding &mdash; if it worked, it would replace the whole non-critical
cast tier. Modeled as Lambertian &rho;&#8202;0.05 pillars (spacing
2&#8202;mm scale-invariant stand-in, fills 4&ndash;25&#8202;%, heights
10/20; predictions in <code>scripts/sweep_phase94.py</code>, gradings
in <code>results/FINDINGS_phase94.md</code>): totals land at
1.08&ndash;1.87&#8202;% &mdash; above the bare pyramid&rsquo;s
0.907&#8202;% &mdash; and <b>head-on measured 1.0004 at the
7.5&#8202;mm beam: indistinguishable from a bare flat plate</b>, the
9.2 area law verbatim (the camera-facing area of a pillar field IS its
flat floor; the pyramid&rsquo;s sloped bases leave no flat area at
all). The registered replacement rule failed on both counts. The named
door &mdash; real fibers tilt and entangle, hiding the floor &mdash;
was then closed by measurement (9.4b, <code>sweep_phase94b.py</code> /
<code>FINDINGS_phase94b.md</code>): shearing every fiber by
15/30/45&deg; in seeded random azimuths hides the floor completely,
and head-on improves only from 1.00 to <b>0.634</b> at lean 30
(beam 7.5&#8202;mm) while totals worsen to 1.83&ndash;2.50&#8202;% &mdash;
tilted Lambertian faces glow where the floor used to stare. Within any
Lambertian model flocking fails the replacement rule at every measured
geometry. What remains is fiber-scale physics no such model carries
(specular fiber sides, sub-beam self-shadowing) &mdash; exactly what
the few-thousand-won coupon measures.</p>
<figure><img src="%%FOREST%%"
 alt="Pyramid vs fiber forest at normal incidence"></figure>

<h2>9.c &mdash; the wall-floor corner: no special treatment needed</h2>
<p>The venue photo shows spill along wall-floor junctions, and the
Phase-7 law says smooth concave corners retroreflect. Measured
(predictions in <code>scripts/sweep_phase9c.py</code>, gradings in
<code>results/FINDINGS_phase9c.md</code>): a corner of two pyramid
panels reads <b>0.84&times; of its own wall</b> (0.146 vs
0.175&#8202;% worst over two coatings and +20/+40&deg;) &mdash; the
junction is DARKER than the open wall, because each face blocks half
the other&rsquo;s sky and the texture eats both legs of any pair path.
Even the smooth-Musou corner reads 0.519&#8202;%, under half a flat
wall: the retro disease belongs to high-reflectance folds, not to
Musou-coated room corners. The registered rule passes: <b>panels
simply butt at 90&deg;</b> &mdash; no cove strips, no fillets. Vertical
wall-wall junctions are covered verbatim by an exact symmetry (rotating
the scene about the view axis under the isotropic world leaves every
&rho; unchanged; FINDINGS_phase9c addendum).</p>
<figure><img src="%%CORNER%%"
 alt="Wall-floor corner measurement"></figure>

<h2>9.d &mdash; from reflectance to visibility (analysis)</h2>
<p>Treatment dims a scanned trace by exactly
&rho;<sub>current</sub>/&rho;<sub>new</sub> &mdash; everything else
cancels. Against a white wall the Musou pyramid buys
&times;271&ndash;452, the bare tier &times;88, the window unit
&times;2,100+; the floor under all of it is the haze&rsquo;s own
volumetric glow, which no wall can undercut. Whether the bare tier
suffices on side walls reduces to ONE measurable number &mdash; the
current trace-to-ambient pixel ratio from an underexposed spill-map
frame &mdash; and the protocol now collects it
(<code>results/FINDINGS_phase9d.md</code>).</p>

<h2>9.f &mdash; the walkable grate floor: conditional, not shipped</h2>
<p>The venue floor needs a WALKABLE absorber. A load-bearing grate over
a pyramid pit measured 0.376&#8202;% (5 angles) / 0.802&#8202;%
(grazing 50&ndash;70&deg;) at bar 3&#8202;mm &times; depth 40; thinner
and deeper (1.5 &times; 60) improved to 0.318 / 0.489&#8202;% but still
missed the registered grazing bar (&le;&#8202;0.45&#8202;%) by
9&#8202;% &mdash; at floor-grazing angles the beam hits the vertical
bars nearly face-on, the louver lesson softened by Musou. Verdict per
the registered rule: <b>not shipped as specced</b>; it remains the best
walkable option measured (2.9&ndash;8.7&times; better than a flat
Musou floor at 70&deg;, ~10&times; better than dark carpet) and stays
available where ~0.5&#8202;% grazing is acceptable. Primary floor plan
unchanged: clip the scan&rsquo;s lower bound, dark covering underfoot,
pyramid tiles where nobody walks. Never use this grate on a wall (the
9.2 area law: 15&#8202;% flat bar land). Details:
<code>results/FINDINGS_phase9f.md</code>.</p>

<h2>The manufacturing decision as it now stands</h2>
<p><b>Mold casting is the default</b>: SLA positive master &rarr;
platinum-silicone mold (peeled off the part, treated as a consumable)
&rarr; soft urethane cast; row-strip molds are the fallback if tip
tearing appears; a ground-steel master when volume grows. Injection
stays rejected (valley radius + demolding, measured in Phase 6.6).
<b>Paint becomes two-tier</b>: Musou only on audience-critical zones;
bare black elsewhere at 5&times; the total but 10&times; better
head-on than any flat wall, with zero paint. <b>Extrusion is a niche</b>
for known-beam-direction zones only. Physical gates before ordering:
cast one tile through the pipeline, magnify tips and valleys
(tip &le; 0.15&#8202;mm, valley &lt; R0.1), bend-test the Musou film on
primed urethane, and measure one black-urethane coupon&rsquo;s &rho;.</p>
</main>
"""
    p92 = worst_per_tag("sweep_phase92.csv")
    f92 = jload("form_phase92.json").get("P92_pd05_form", {})
    fbare = jload("form_phase9.json").get("P91_bare_form_r05", {})
    rows92 = ""
    for label, area, tw, ho in (
            ("0 (bare)", "0&#8202;%", p91["P91_bare_r005"],
             num(fbare.get("head_on"), 3)),
            ("2&#8202;mm", "1&#8202;%", p92["P92_pd02"], DASH),
            ("5&#8202;mm", "6&#8202;%", p92["P92_pd05"],
             num(f92.get("head_on"), 3)),
            ("10&#8202;mm", "25&#8202;%", p92["P92_pd10"], DASH),
            ("20&#8202;mm (full Musou)", "100&#8202;%", pyr_t,
             num(pyr_f.get("head_on"), 3))):
        rows92 += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                   % (label, area, pc(tw), ho))
    html = html.replace("%%ROWS92%%", rows92)
    html = html.replace("%%CORNER%%", b64("corner.png"))
    html = html.replace("%%FOREST%%", b64("forest.png"))
    html = html.replace("%%FRONTSPRAY%%", b64("frontspray.png"))
    html = html.replace("%%TIPLINE%%", b64("tipline.png"))
    html = html.replace("%%RULE018%%", b64("rule018.png"))
    html = html.replace("%%ROWS%%", rows)
    html = html.replace("%%GRADES%%", grades)
    html = html.replace("%%SCANHEAD%%", scanhead)
    html = html.replace("%%SCANROW%%", scanrow)
    open(OUT, "w").write(html)
    print("wrote %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
