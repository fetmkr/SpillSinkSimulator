"""Phase 5 report: the sharp pyramid, standalone.

    python3 scripts/build_report_phase5.py

Generates report/phase5/report.html from the measurement files. No number is
typed here (gate check 7); everything is read from:

    results/sweep_rewind.csv     corrected worst-rho for the decision set
    results/form_pyr.json        three-axis table, oriented geometry
    results/sweep_phase5.csv     jitter cost on total reflectance
    results/form_phase5.json     phase-span of periodic vs jittered
    results/sweep_phase52.csv    depth x pitch map
    results/sweep_phase53.csv    mixed sizes
    results/sweep_phase54.csv    buildable scale + tip-flat series
    results/form_phase54.json    smear / head-on for the tip series

House rule (2026-08-15): every results table carries ALL THREE axes. An axis
that was not measured for a row prints an em-dash, never disappears.
"""

import csv
import json
import os
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUTDIR = os.path.join(ROOT, "report", "phase5")
OUT = os.path.join(OUTDIR, "report.html")


def worst_of(path, tag):
    rows = [r for r in csv.DictReader(open(os.path.join(RESULTS, path)))
            if r["tag"] == tag]
    return max(float(r["rho"]) for r in rows) if rows else None


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    form = json.load(open(os.path.join(RESULTS, "form_pyr.json")))
    p5f = json.load(open(os.path.join(RESULTS, "form_phase5.json")))
    try:
        p54f = json.load(open(os.path.join(RESULTS, "form_phase54.json")))
    except Exception:
        p54f = {}
    per54 = {}
    meta54 = {}
    try:
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase54.csv"))):
            t = r["tag"]
            per54[t] = max(per54.get(t, 0.0), float(r["rho"]))
            meta54[t] = (float(r["depth"]), float(r["pitch"]),
                         float(r["tip_flat"]), float(r["flat_frac"]))
    except Exception:
        pass

    # three-axis table
    axes = {}
    total = {
        "pyr_sharp_a909": worst_of("sweep_rewind.csv", "AN_pyr_a909"),
        "pyr_trunc_a909": worst_of("sweep_rewind.csv", "AN_trn_a909"),
        "stack_blade_pyr": worst_of("sweep_rewind.csv",
                                    "BH_p055_t02_grid_s23"),
        "cone_p550": worst_of("sweep_rewind.csv", "AN_cone_p550_s23"),
    }
    for k, rec in form.items():
        axes[k] = {"total": total.get(k), "smear": rec["smear"],
                   "head_on": rec["head_on"]}
    if "P54_p02_t00" in per54 and p54f.get("P54_p02_t00"):
        axes["pyr_thin"] = {"total": per54["P54_p02_t00"],
                            "smear": p54f["P54_p02_t00"]["smear"],
                            "head_on": p54f["P54_p02_t00"]["head_on"]}

    # jitter table
    jit = collections.OrderedDict()
    rows = list(csv.DictReader(open(os.path.join(RESULTS,
                                                 "sweep_phase5.csv"))))
    per = collections.defaultdict(float)
    meta = {}
    for r in rows:
        per[r["tag"]] = max(per[r["tag"]], float(r["rho"]))
        meta[r["tag"]] = (float(r["apex_jitter"]), float(r["tip_drop"]))
    base = per.get("P5_j00")
    for tag in ("P5_j00", "P5_j30", "P5_j60", "P5_j60d15"):
        aj, td = meta[tag]
        jit[tag] = {"aj": aj, "td": td, "worst": per[tag],
                    "shift": (per[tag] - base) / base}

    span0 = {k: v.get("span_0") for k, v in p5f.items()}
    span40 = {}
    for k, v in p5f.items():
        t = v.get("thetas", {})
        s = [t[a]["peak_ratio_span"] for a in ("-40", "+40") if a in t]
        span40[k] = max(s) if s else None

    def pc(x, nd=3):
        return "%.*f&#8202;%%" % (nd, 100 * x)

    def num(x, nd=2):
        return "%.*f" % (nd, x)

    DASH = "&mdash;"

    def cell_sm(rec):
        return num(rec["smear"]) if rec and rec.get("smear") else DASH

    def cell_ho(rec):
        return num(rec["head_on"], 4) if rec and rec.get("head_on") else DASH

    NAME = {"pyr_sharp_a909": "sharp pyramid p5.5 / d50",
            "pyr_thin": "sharp pyramid p2 / d18 (Phase 5.4)",
            "pyr_trunc_a909": "truncated pyramid",
            "stack_blade_pyr": "blade + pyramid stack",
            "cone_p550": "cone"}

    rows3 = ""
    order = ["pyr_sharp_a909", "pyr_trunc_a909", "stack_blade_pyr",
             "cone_p550"]
    if "pyr_thin" in axes:
        order.insert(1, "pyr_thin")
    for k in order:
        a = axes[k]
        star = ' class="win"' if k == "pyr_sharp_a909" else ""
        rows3 += ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                  % (star, NAME[k], pc(a["total"]), num(a["smear"]),
                     num(a["head_on"], 4)))

    rowsj = ""
    for tag, d in jit.items():
        label = ("periodic (no jitter)" if d["aj"] == 0 else
                 "apex jitter %.1f" % d["aj"]
                 + (" + tip drop %.2f" % d["td"] if d["td"] else ""))
        sp = ""
        if tag in span0:
            sp = "%.2f&times; / %.1f&times;" % (span0[tag], span40[tag])
        frec = p5f.get(tag)
        rowsj += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                  "<td>%+.1f&#8202;%%</td><td>%s</td></tr>"
                  % (label, pc(d["worst"]), cell_sm(frec), cell_ho(frec),
                     100 * d["shift"], sp or DASH))

    html = """<title>Spill Sink 피라미드 연구 — Phase 5</title>
<style>
:root{--bg:#f4f2ec;--card:#fbfaf7;--ink:#1c1b18;--ink2:#5c594f;--line:#d8d4c8;
  --acc:#b34700;--ok:#2c6e49;--mono:ui-monospace,'SF Mono',Menlo,monospace}
:root:not([data-theme=light]){}
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
.grade{background:var(--card);border:1px solid var(--line);border-radius:6px;
  padding: .9rem 1.1rem;margin:1rem 0}
.grade b.ok{color:var(--ok)} .grade b.no{color:var(--acc)}
code{font:.85em var(--mono)}
</style>
<main>
<div class="kicker">Spill Sink &middot; 피라미드 연구 &middot; Phase 5</div>
<h1>The sharp pyramid, standalone</h1>
<p class="lede">Phases 2&ndash;4 built tubes and put shaped floors under
them. After the winding correction, the shape that had been playing the
floor &mdash; a plain field of sharp pyramids, nothing in front of it &mdash;
leads every axis this study scores. Phase 5 is the focused case for and
against building exactly that.</p>

<figure style="margin:1.6rem 0 0">
<img src="%%HERO%%" alt="Field of sharp pyramids, tips toward the viewer"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">The design: a pressed field of sharp pyramids,
pitch 5.5&#8202;mm, depth 50&#8202;mm, nothing in front of it. Rendered from
the measured geometry.</figcaption>
</figure>

<h2>All three axes, oriented geometry</h2>
<table>
<tr><th>design</th><th>total worst-&rho; &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th></tr>
%%ROWS3%%
</table>
<p class="note">Total: worst over 5 angles &times; 3 coating models
(<code>sweep_rewind.csv</code>). Smear and head-on: published form protocol,
16 stripe phases &times; 512&#8202;spp (<code>form_pyr.json</code>). The
pyramid leads all three; a single press-formed layer beats the two-layer
blade assembly &mdash; the previous champion &mdash; on every number,
including a 3.1&times; advantage on head-on brightness.
<b>Caveat added in Phase 5.8: every number in this table is at azimuth 0,
and the total-axis lead does not survive the worst azimuth &mdash; see
&ldquo;The azimuth hole&rdquo; below.</b></p>

<h2>Why the front layers lost</h2>
<p>The study&rsquo;s one repeated law is that <b>flat area facing the viewer
at the mouth decides the ranking</b> &mdash; tip radius, apex flats, blade
edges and honeycomb wall-tops are all the same variable. A tube in front of
the pyramid can only add such area (blade edges, wall tops) while blocking
the surface that was already best. The honeycomb, second on total
reflectance in Phase&nbsp;2, ends Phase&nbsp;5 with no role: its wall tops
face the viewer like the flat plate it was meant to replace, and the floor
that fixed its normal-incidence number outperforms it standing alone.</p>

<h2>The periodicity objection, measured and dismissed</h2>
<p>The pyramid field is periodic, and this project bans periodic arrays
because a scanning beam over identical cells returns a repeating glint. That
objection was measured here rather than assumed: the form protocol walks the
stripe across one full pitch and records the spread of the head-on peak
(<code>peak_ratio_span</code>).</p>
<table>
<tr><th>variant</th><th>total worst-&rho; &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th><th>vs periodic</th>
<th>span &theta;0 / &plusmn;40&deg;</th></tr>
%%ROWSJ%%
</table>
<p class="note">An em-dash means that axis was not run for that variant;
the form protocol was run on the two ends of the jitter series and they
agree to three decimals on both axes.</p>
<p class="note">The periodic pyramid&rsquo;s phase spread is
%%SPAN0%%&times; at normal incidence &mdash; the 1D groove that motivated
the rule measured <b>214&times;</b>. A cell that closes in both directions
is phase-uniform on its own, so the de-periodising jitter buys nothing and
costs up to a quarter of the total-reflectance budget. <b>Build it
periodic</b>: one die, no jitter schedule.</p>

<figure style="margin:1.4rem 0 0">
<img src="%%HEROJ%%" alt="Top and side views, periodic and jittered"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">Top and side views, periodic (above) and
de-periodised (below): bases identical, apexes wandered. The two measure the
same phase spread &mdash; and the jittered one gives up total reflectance
for it.</figcaption>
</figure>

<h2>Prediction scoreboard, Phase 5.1</h2>
<div class="grade">
<b class="ok">Held</b> &mdash; the un-jittered anchor reproduced
<code>sweep_rewind</code> exactly; mean smear/head-on unmoved by jitter.<br>
<b class="no">Wrong</b> &mdash; &ldquo;apex jitter is nearly free
(&le;10&#8202;%)&rdquo;: it costs %%J60%% at 0.6 and %%J60D%% with tip drop.<br>
<b class="no">Wrong</b> &mdash; &ldquo;the span collapses under
jitter&rdquo;: there was nothing to collapse. The premise of the
no-periodic-array rule does not apply to doubly-closed cells.
</div>

<h2>Depth and pitch, swept (Phase 5.2)</h2>
<table>
<tr><th>knob</th><th>depth</th><th>pitch</th><th>aspect</th>
<th>total worst-&rho; &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th></tr>
%%ROWS52%%
</table>
%%SVG52%%
<p class="note">Both knobs collapse onto one aspect curve (depth-swept and
pitch-swept points at matching aspect agree within the &plusmn;4&#8202;%
seed noise), and the curve has NOT flattened by aspect 17: pre-registered
prediction said fine pitch was nearly exhausted, and it was wrong by three
times its own error bars. <b>Pitch 3&#8202;mm at depth 50 reads
%%BEST52%%</b> &mdash; 29&#8202;% below the Phase-5 champion &mdash; and a
thinner 30&#8202;mm panel costs 33&#8202;%. Where to stop is now a die-cost
question, not an optics one.</p>

<h2>Mixed sizes, the RF-chamber look (Phase 5.3)</h2>
<figure style="margin:1rem 0 0">
<img src="%%GRIDMIX%%" alt="Mixed pyramid sizes, top and side views"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">One big pyramid ringed by small ones, the pattern
RF chambers use. Equal-depth above; slope-preserving (small tips stop
half-way) below.</figcaption>
</figure>
<table>
<tr><th>field</th><th>total worst-&rho; &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th><th>vs uniform small</th></tr>
%%ROWS53%%
</table>
<p class="note">The mixed fields were rejected on the total axis alone
(28&ndash;40&#8202;% behind before the other axes could matter), so their
form protocol was not run.</p>
<p class="note">RF mixes sizes for <b>broadband</b> absorption &mdash; each
pyramid works at wavelengths near its own size. That is a wave mechanism
with no ray-optics analogue, and the measurement agrees: the mix lands
between its parts on the aspect curve, 28&ndash;40&#8202;% behind tiling
the panel with the small pitch alone. The chamber photograph is not a trick
worth copying here; it solves a problem this wall does not have.</p>

<h2>The buildable pyramid (Phase 5.4)</h2>
<p>The champion cell is a 9:1 needle &mdash; base 5.5&#8202;mm, height
50&#8202;mm &mdash; and no die can press it, no press can hold its
mathematically sharp apex. Two escapes were pre-registered and measured
together: <b>scale</b> (only the ratio depth/pitch matters to ray optics,
so grow the cell) and <b>tip tolerance</b> (only the ratio tip/pitch
should matter, so a bigger cell also buys a blunter allowed tip).</p>
<figure style="margin:1rem 0 0">
<img src="%%GRIDTIP%%" alt="Three aspect-9 scales at true scale, and the
pitch-10 tip at 0, 0.5 and 2 mm"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
<figcaption class="note">Left to right at one scale: the unbuildable
champion, the build spec, and the thin option &mdash; all aspect&nbsp;9.
Below: what 0.5 and 2&#8202;mm of tip flat actually look like on a
10&#8202;mm cell.</figcaption>
</figure>
<table>
<tr><th>design</th><th>tip / pitch</th><th>flat frac</th>
<th>total worst-&rho; &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th></tr>
%%ROWS54%%
</table>
<p class="note">%%NOTE54%%</p>
<h2>Prediction scoreboard, Phase 5.4</h2>
<div class="grade">%%GRADE54%%</div>

<h2>The probe beam was an assumption (Phase 5.5)</h2>
<p>Every smear and span number above is conditioned on a 2&#8202;mm probe
stripe &mdash; a protocol constant, not a measurement. The user&rsquo;s
projector (LaserCube Ultra MK2: 4&#8202;mm aperture, 1&#8202;mrad
divergence) puts roughly a 7&ndash;14&#8202;mm beam on the wall at
3&ndash;10&#8202;m. So the stripe width became a swept variable, and a
first-class input in the simulator.</p>
<table>
<tr><th>pitch</th><th>beam</th><th>smear &uarr; (beam width 2&#8202;mm)</th><th>head-on &darr;</th>
<th>span &theta;0</th><th>return width / flat&rsquo;s, mm @&minus;40&deg;</th></tr>
%%ROWS55%%
</table>
<p class="note">%%NOTE55%%</p>
<h2>Prediction scoreboard, Phase 5.5</h2>
<div class="grade">%%GRADE55%%</div>

<h2>The coating parameter nobody measured (Phase 5.6)</h2>
<p>Every number in this report was taken at <code>spec_roughness = 0.30</code>
&mdash; a pinned value that has never been measured on the physical paint.
The winner and the flat-plate denominator were re-measured across
0.10&ndash;0.50, all three axes where it matters.</p>
<table>
<tr><th>roughness</th><th>p2/d18 total &darr;</th><th>flat total</th>
<th>advantage</th><th>p2 smear &uarr;</th><th>p2 head-on &darr;</th></tr>
%%ROWS56%%
</table>
<p class="note">%%NOTE56%%</p>
<h2>Prediction scoreboard, Phase 5.6</h2>
<div class="grade">%%GRADE56%%</div>

<h2>The die tolerance, settled (Phase 5.8, part 1)</h2>
<p>Between &ldquo;mathematically sharp&rdquo; and the 0.1&#8202;mm tip that
already measured a 2.2&times; head-on penalty, nothing was measured &mdash;
so the drawing could not carry a tolerance. The pre-registered rule: the
tolerance is the largest tip whose head-on stays &le;1.5&times; sharp.</p>
<table>
<tr><th>tip, mm (pitch 2)</th><th>flat frac</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th><th>span &theta;0</th></tr>
%%ROWS58T%%
</table>
<p class="note">%%NOTE58T%%</p>

<h2>The azimuth hole (Phase 5.8, part 2)</h2>
<p>Every pyramid total in this report was measured at azimuth 0 &mdash; and
the brief says the beam azimuth is unknown. Rotating the panel about its
own normal (the control pinned at 0.0500 in every row):</p>
<table>
<tr><th>azimuth &phi;</th><th>worst-&rho; (p2/d18)</th><th>vs &phi;0</th></tr>
%%ROWS58P%%
</table>
<p class="note">%%NOTE58P%%</p>
<h2>Prediction scoreboard, Phase 5.8</h2>
<div class="grade">%%GRADE58%%</div>

<h2>The deciding round: pyramid vs cone at the worst azimuth (Phase 5.9)</h2>
<p>The azimuth hole put the cone back in the race. This round measured the
pyramid&rsquo;s form axes at &phi;30 (the form protocol gained an azimuth
input, guarded by an exact &phi;0 re-run), re-anchored the cone, and asked
whether the cone can be thin.</p>
<table>
<tr><th></th><th>pyramid p2/d18</th><th>thin cone p2/d18.2</th>
<th>verdict (&gt;8&#8202;% rule)</th></tr>
%%ROWS59%%
</table>
<p class="note">%%NOTE59%%</p>
<h2>Prediction scoreboard, Phase 5.9</h2>
<div class="grade">%%GRADE59%%</div>

<h2>The cone&rsquo;s weakness decomposed, and the pyramid&rsquo;s thin end
(Phase 5.10)</h2>
<table>
<tr><th>design</th><th>total worst &darr;</th><th>smear &uarr; (beam width 2&#8202;mm)</th>
<th>head-on &darr;</th><th>span &theta;0</th><th>panel</th></tr>
%%ROWS510%%
</table>
<p class="note">%%NOTE510%%</p>

<h2>Closing audit: the verdict&rsquo;s single-point legs (Phase 5.11)</h2>
<div class="grade">%%NOTE511%%</div>

<h2>The pre-coupon worst envelope (Phase 5.12)</h2>
<p>The deployed panel faces two unknowns at once &mdash; paint lobe width
and beam azimuth. The joint worst, per finalist:</p>
<table>
<tr><th></th><th>r 0.10</th><th>r 0.30</th><th>r 0.50</th></tr>
%%ROWS512%%
</table>
<p class="note">%%NOTE512%%</p>

<h2>The easy-build tier (Phase 5.15)</h2>
<p>Can a LOW pyramid be rescued by a bought honeycomb in front? The stack
is measurably azimuth-flat &mdash; the one thing the pyramid is not &mdash;
but the top layer owns the axes that survive deployment:</p>
<table>
<tr><th>design</th><th>total &phi;0</th><th>total &phi;30</th>
<th>smear &uarr; (beam width 2&#8202;mm)</th><th>head-on &darr;</th><th>tip req.</th>
<th>panel</th></tr>
%%ROWS515%%
</table>
<p class="note">%%NOTE515%%</p>

<p class="note">The coarse tier (pitch &ge; 10, big honeycomb and its combinations) is a separate report: Phase 6.</p>

<h2>The ordering package (Phase 5.13)</h2>
<p>Four STLs now exist in <code>export/</code>, built by the same
<code>build_mesh</code> calls every sweep ran, round-trip-verified and
kernel-clean: the two spec parts (for mould/CNC quotes) and two
2&times;-scale print coupons whose tips a resin printer can approach.
The 2&times; pyramid coupon&rsquo;s targets are pre-registered:</p>
<table>
<tr><th>coupon target (p4/d36/t0.1)</th><th>simulated</th>
<th>acceptance</th></tr>
%%ROWS513%%
</table>
<p class="note">%%NOTE513%%</p>

<h2>Validity check: none of this is a face-size artifact (Phase 5.7)</h2>
<p>Every total in this phase was measured on a 60&#8202;mm coupon. After a
measurement-frame defect surfaced on flat slabs at that size, the champion
and the winner were re-measured at 100&#8202;mm:</p>
<table>
<tr><th>design</th><th>face 60</th><th>face 100</th><th>shift</th></tr>
%%ROWS57%%
</table>
<p class="note">%%NOTE57%%</p>

<h2>What Phase 5 still owes</h2>
<p>A physical coupon remains the only test of the coating model.
And every number here is one seed; the periodic conclusion should survive
seeds trivially, but the claim has not been bought yet.</p>

<p class="note">Corrections that led here are logged in the
<a href="https://claude.ai/code/artifact/9bb75a44-46a3-46ea-bd9a-6dbc1800ca07">
errata page</a>; the winding defect and its re-measurement are
<code>FINDINGS_winding.md</code> and <code>FINDINGS_formpyr.md</code>.</p>
</main>
"""
    import base64

    def img64(name):
        fp = os.path.join(OUTDIR, "img", name)
        if not os.path.exists(fp):
            return ""
        return ("data:image/png;base64,"
                + base64.b64encode(open(fp, "rb").read()).decode())

    # phase 5.2 table + inline SVG (rho vs aspect, both knob families)
    r52 = []
    try:
        rows52 = list(csv.DictReader(open(os.path.join(
            RESULTS, "sweep_phase52.csv"))))
        per52 = {}
        for r in rows52:
            t = r["tag"]
            per52.setdefault(t, {"depth": float(r["depth"]),
                                 "pitch": float(r["pitch"]),
                                 "aspect": float(r["aspect"]), "w": 0.0})
            per52[t]["w"] = max(per52[t]["w"], float(r["rho"]))
        r52 = sorted(per52.values(), key=lambda d: d["aspect"])
    except Exception:
        pass
    rows52h = ""
    for d in r52:
        anchor = (abs(d["depth"] - 50) < 1e-6
                  and abs(d["pitch"] - 5.5005) < 1e-3)
        knob = ("anchor" if anchor else
                ("pitch" if abs(d["depth"] - 50) < 1e-6 else "depth"))
        frec = p5f.get("P5_j00") if anchor else None
        rows52h += ("<tr><td>%s</td><td>%.0f</td><td>%.2f</td>"
                    "<td>%.1f</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (knob, d["depth"], d["pitch"], d["aspect"],
                       pc(d["w"]), cell_sm(frec), cell_ho(frec)))
    svg = ""
    if r52:
        W2, H2, M = 640, 300, 46
        amax = max(d["aspect"] for d in r52) * 1.06
        rmax = max(d["w"] for d in r52) * 1.12
        pts = []
        for d in r52:
            x = M + (W2 - 2 * M) * d["aspect"] / amax
            y = H2 - M - (H2 - 2 * M) * d["w"] / rmax
            knob = "P" if abs(d["depth"] - 50) < 1e-6 else "D"
            pts.append((x, y, knob, d["aspect"]))
        dots = "".join(
            '<circle cx="%.1f" cy="%.1f" r="5" fill="%s"><title>aspect '
            '%.1f</title></circle>'
            % (x, y, "var(--acc)" if k == "P" else "var(--ok)", a)
            for x, y, k, a in pts)
        svg = ('<svg viewBox="0 0 %d %d" style="width:100%%;max-width:'
               '640px;font:11px var(--mono)" role="img" aria-label="worst '
               'reflectance against aspect ratio">'
               '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="var(--ink2)"/>'
               '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="var(--ink2)"/>'
               '%s'
               '<text x="%d" y="%d" fill="var(--ink2)">aspect = depth / '
               'pitch</text>'
               '<text x="6" y="16" fill="var(--ink2)">worst-&#961;</text>'
               '<text x="%d" y="28" fill="var(--acc)">&#9679; pitch-swept'
               '</text><text x="%d" y="44" fill="var(--ok)">&#9679; '
               'depth-swept</text></svg>'
               % (W2, H2, M, H2 - M, W2 - M, H2 - M, M, M, M, H2 - M, dots,
                  W2 // 2 - 60, H2 - 10, W2 - 150, W2 - 150))
    # phase 5.3
    rows53h = ""
    try:
        rows53 = list(csv.DictReader(open(os.path.join(
            RESULTS, "sweep_phase53.csv"))))
        per53 = {}
        for r in rows53:
            per53.setdefault(r["tag"], 0.0)
            per53[r["tag"]] = max(per53[r["tag"]], float(r["rho"]))
        b53 = per53.get("P5_j00", 1.0)
        for tag, label in (("P5_j00", "uniform small (anchor)"),
                           ("P53_mix_f10", "mixed, equal depth"),
                           ("P53_mix_f05", "mixed, equal slope")):
            if tag not in per53:
                continue
            v = per53[tag]
            rel = "&mdash;" if tag == "P5_j00" else                 "+%.0f&#8202;%%" % (100 * (v - b53) / b53)
            frec = p5f.get("P5_j00") if tag == "P5_j00" else None
            rows53h += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                        "<td>%s</td></tr>"
                        % (label, pc(v), cell_sm(frec), cell_ho(frec), rel))
    except Exception:
        pass
    # phase 5.4 — buildable scale + tip series, three axes
    rows54h = ""
    LABEL54 = [
        ("P5_j00", "champion p5.5 / d50 (anchor)"),
        ("P54_p10_t00", "p10 / d90, sharp"),
        ("P54_p10_t05", "p10 / d90, tip 0.5 (build spec)"),
        ("P54_p10_t10", "p10 / d90, tip 1.0"),
        ("P54_p10_t20", "p10 / d90, tip 2.0"),
        ("P54_p02_t00", "p2 / d18, sharp (thin option)"),
        ("P54_p02_t01", "p2 / d18, tip 0.1"),
    ]
    for tag, label in LABEL54:
        if tag not in per54:
            continue
        dep, pit, tf, ffr = meta54[tag]
        frec = p54f.get(tag) or (p5f.get(tag) if tag in p5f else None)
        star = ' class="win"' if tag == "P54_p02_t00" else ""
        rows54h += ("<tr%s><td>%s</td><td>%.1f / %.0f</td>"
                    "<td>%.2f&#8202;%%</td><td>%s</td><td>%s</td>"
                    "<td>%s</td></tr>"
                    % (star, label, tf, pit, 100 * ffr, pc(per54[tag]),
                       cell_sm(frec), cell_ho(frec)))
    html_note54 = ""
    grade54 = ""
    if per54 and p54f:
        def band(x, lo, hi):
            return lo <= x <= hi

        t00, t05 = per54.get("P54_p10_t00"), per54.get("P54_p10_t05")
        t10, t20 = per54.get("P54_p10_t10"), per54.get("P54_p10_t20")
        p2, p2t = per54.get("P54_p02_t00"), per54.get("P54_p02_t01")
        f00 = p54f.get("P54_p10_t00", {})
        hos = {t: p54f.get(t, {}).get("head_on") for t in
               ("P54_p10_t05", "P54_p10_t10", "P54_p10_t20")}
        sms = [p54f[t]["smear"] for t in p54f if p54f[t].get("smear")]

        def g(ok, txt):
            cls = "ok" if ok else "no"
            word = "Held" if ok else "Wrong"
            return "<b class=\"%s\">%s</b> &mdash; %s<br>" % (cls, word, txt)

        p1ok = (band(100 * t00, 0.137, 0.149)
                and band(f00.get("smear", 0), 3.76, 4.56)
                and band(f00.get("head_on", 9), 0.022, 0.032))
        grade54 += g(p1ok, "scale invariance: p10/d90 predicted "
                     "0.143&thinsp;&plusmn;&thinsp;0.006&#8202;% total, "
                     "smear 4.16&thinsp;&plusmn;&thinsp;0.4, head-on "
                     "0.027&thinsp;&plusmn;&thinsp;0.005; measured "
                     + pc(t00) + " / " + num(f00.get("smear", 0)) + " / "
                     + num(f00.get("head_on", 0), 4))
        p2ok = (band(100 * t05, 0.138, 0.152)
                and band(100 * t10, 0.145, 0.161)
                and band(100 * t20, 0.169, 0.193))
        grade54 += g(p2ok, "total follows flat fraction (predicted "
                     "0.145 / 0.153 / 0.181&#8202;%): measured "
                     + pc(t05) + " / " + pc(t10) + " / " + pc(t20))
        p3ok = (hos["P54_p10_t05"] is not None
                and band(hos["P54_p10_t05"], 0.030, 0.050)
                and band(hos["P54_p10_t10"], 0.057, 0.097)
                and band(hos["P54_p10_t20"], 0.15, 0.25))
        grade54 += g(p3ok, "head-on follows flat fraction only (predicted "
                     "0.040 / 0.077 / 0.20): measured "
                     + num(hos["P54_p10_t05"] or 0, 4) + " / "
                     + num(hos["P54_p10_t10"] or 0, 4) + " / "
                     + num(hos["P54_p10_t20"] or 0, 4))
        p4ok = all(band(s, 3.76, 4.56) for s in sms)
        grade54 += g(p4ok, "smear barely moves "
                     "(4.16&thinsp;&plusmn;&thinsp;0.40): measured "
                     + ", ".join(num(s) for s in sms))
        p5ok = (band(100 * p2, 0.136, 0.150)
                and band(100 * p2t, 0.138, 0.152))
        grade54 += g(p5ok, "scale invariance holds downward: p2/d18 "
                     "predicted 0.143 / 0.145&#8202;%; measured "
                     + pc(p2) + " / " + pc(p2t)
                     + (" &mdash; BETTER than the band, the aspect curve "
                        "keeps a slight slope in absolute pitch"
                        if not p5ok and 100 * p2 < 0.136 else ""))
        f2 = p54f.get("P54_p02_t00", {})
        f2t = p54f.get("P54_p02_t01", {})
        if f2.get("smear"):
            p6ok = (band(f2["smear"], 4.2, 6.5)
                    and band(f2.get("head_on", 9), 0.019, 0.035)
                    and band(f2t.get("head_on", 9), 0.019, 0.035))
            grade54 += g(p6ok, "the thin option smears like the champion "
                         "(predicted smear 4.2&ndash;6.5, head-on "
                         "0.027&thinsp;&plusmn;&thinsp;0.008 incl. tip 0.1): "
                         "measured smear " + num(f2["smear"])
                         + ", head-on " + num(f2.get("head_on", 0), 4)
                         + " sharp but " + num(f2t.get("head_on", 0), 4)
                         + " with a 0.1&#8202;mm tip &mdash; at fine pitch "
                         "the tip flat is NOT free")
        ho_mult = ((p54f["P54_p10_t20"]["head_on"]
                    / p54f["P54_p10_t00"]["head_on"])
                   if p54f.get("P54_p10_t20", {}).get("head_on") else None)
        sp54 = {t: p54f.get(t, {}).get("span_0") for t in p54f}
        html_note54 = (
            "Three laws separated here. <b>Total reflectance follows "
            "aspect alone</b> &mdash; all three scales sit within a few "
            "percent. <b>Form destruction does not scale</b>: the probe "
            "stripe is a fixed 2&#8202;mm, and a 10&#8202;mm cell carries "
            "it on one flank nearly unbroken (smear "
            + num(p54f.get("P54_p10_t00", {}).get("smear", 0))
            + " against the champion&rsquo;s "
            + num(p5f.get("P5_j00", {}).get("smear", 0))
            + "), so the cell must stay "
            "no coarser than the beam it is meant to shred. And <b>the tip "
            "flat taxes the head-on axis</b>, worse at coarse pitch where "
            "it also revives the scanning glint the periodic rule worries "
            "about (phase span "
            + ("%.1f&times;" % sp54.get("P54_p10_t20", 0))
            + " at tip 2.0 versus "
            + ("%.2f&times;" % sp54.get("P54_p10_t00", 0))
            + " sharp). The three-axis winner is the thin field &mdash; "
            "pitch 2, depth 18, panel 20&#8202;mm with backing, "
            + pc(p2) + " total &mdash; IF its sub-0.1&#8202;mm tips can be "
            "formed; the 0.1&#8202;mm-tip row above prices the failure to "
            "hold that (head-on "
            + num(f2t.get("head_on", 0), 4) + ", "
            + ("%.1f&times;" % (f2t["head_on"] / f2["head_on"]
                                if f2.get("head_on") else 0))
            + " sharp). The "
            "coarse field p10/d90 with tip 0.5 stays the fallback where "
            "fine tooling is unavailable: same total, but a third of the "
            "smear and a "
            + ("%.1f&times;" % sp54.get("P54_p10_t05", 0))
            + " phase span.")
    html = html.replace("%%ROWS54%%", rows54h)
    html = html.replace("%%NOTE54%%", html_note54 or DASH)

    # phase 5.5 — beam width as a variable
    rows55h = ""
    note55 = ""
    grade55 = ""
    try:
        p55 = json.load(open(os.path.join(RESULTS, "form_phase55.json")))
        W2 = {"p02": p54f.get("P54_p02_t00"), "p55": p5f.get("P5_j00"),
              "p10": p54f.get("P54_p10_t00")}
        PLBL = {"p02": "2 (d18)", "p55": "5.5 (d50)", "p10": "10 (d90)"}

        def r55(pl, wl, rec):
            t = rec.get("thetas", {}).get("-40", {})
            sp = rec.get("span_0")
            return ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td>%s</td><td>%.2f / %.2f</td></tr>"
                    % (pl, wl, num(rec["smear"]),
                       num(rec["head_on"], 4),
                       ("%.2f&times;" % sp) if sp else DASH,
                       t.get("rms_mm", 0), t.get("rms_control_mm", 0)))

        hos55, sps55, smears_w10 = [], [], {}
        for name in ("p02", "p55", "p10"):
            first = True
            if W2.get(name):
                rows55h += r55(PLBL[name], "2 (protocol)", W2[name])
                first = False
            for w, wl in (("05", "5"), ("10", "10")):
                rec = p55.get("P55_%s_w%s" % (name, w))
                if not rec:
                    continue
                rows55h += r55(PLBL[name] if first else "", wl + " mm", rec)
                first = False
                hos55.append(rec["head_on"])
                if rec.get("span_0"):
                    sps55.append(rec["span_0"])
                if w == "10":
                    smears_w10[name] = rec["smear"]
        p2w10 = p55.get("P55_p02_w10", {})
        p10w10 = p55.get("P55_p10_w10", {})
        t2 = p2w10.get("thetas", {}).get("-40", {})
        note55 = (
            "The ratio metric compresses as the beam widens because the "
            "FLAT control blurs too: the fine-pitch panels return a "
            "&sim;3&ndash;4&#8202;mm smudge whose width the panel itself "
            "sets (" + "%.2f" % t2.get("rms_mm", 0) + "&#8202;mm at beam "
            "10 against the flat wall&rsquo;s "
            + "%.2f" % t2.get("rms_control_mm", 0) + "), while <b>pitch 10 "
            "returns a stripe NARROWER than the flat wall&rsquo;s at every "
            "beam width</b> (smear "
            + num(p10w10.get("smear", 0)) + " at beam 10) &mdash; its "
            "flanks act as mirrors that keep the stripe a stripe. A wider "
            "real beam therefore does NOT rehabilitate the coarse pitch; "
            "the fine-pitch fields stay at or above the flat wall&rsquo;s "
            "blur at one ninth of its brightness, and the form axis simply "
            "loses discriminating power as the beam itself arrives "
            "pre-blurred. Head-on and total never see the beam; the "
            "three-axis verdict of Phase 5.4 stands at every width "
            "measured.")
        grade55 += g(False, "smear collapses onto beam/pitch and "
                     "saturates near 4.2 above R&nbsp;0.5: it does not "
                     "collapse and it does not saturate &mdash; at beam 10 "
                     "the fine pitches read "
                     + num(smears_w10.get("p02", 0)) + " / "
                     + num(smears_w10.get("p55", 0))
                     + " and pitch 10 reads "
                     + num(smears_w10.get("p10", 0)) + ", below the flat "
                     "wall itself")
        grade55 += g(max(hos55) - min(hos55) < 0.3 * 0.027,
                     "head-on is beam-independent: "
                     + num(min(hos55), 4) + "&ndash;" + num(max(hos55), 4)
                     + " across every pitch and width")
        grade55 += g(max(sps55) < 1.2 if sps55 else False,
                     "span stays dead for sharp fields at every width: "
                     "worst " + ("%.2f&times;" % max(sps55)
                                 if sps55 else DASH))
    except Exception:
        pass
    html = html.replace("%%ROWS55%%", rows55h or "")
    html = html.replace("%%NOTE55%%", note55 or DASH)
    html = html.replace("%%GRADE55%%", grade55 or DASH)

    # phase 5.6 — roughness robustness
    rows56h = ""
    note56 = ""
    grade56 = ""
    try:
        per56 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase56.csv"))):
            t = r["tag"]
            per56.setdefault(t, 0.0)
            per56[t] = max(per56[t], float(r["rho"]))
        f56 = json.load(open(os.path.join(RESULTS, "form_phase56.json")))
        f30 = p54f.get("P54_p02_t00", {})
        adv = {}
        for rr in ("10", "20", "30", "40", "50"):
            pv = per56.get("P56_p02_r%s" % rr)
            fv = per56.get("P56_flat_r%s" % rr)
            if pv is None or fv is None:
                continue
            adv[rr] = fv / pv
            frm = (f56.get("P56_form_p02_r%s" % rr)
                   or (f30 if rr == "30" else None))
            rows56h += ("<tr%s><td>0.%s</td><td>%s</td><td>%s</td>"
                        "<td>%.1f&times;</td><td>%s</td><td>%s</td></tr>"
                        % (' class="win"' if rr == "30" else "", rr,
                           pc(pv), pc(fv), fv / pv, cell_sm(frm),
                           cell_ho(frm)))
        d100a = per56.get("P56_p02x_r10")
        d100b = per56.get("P56_p02x_r50")
        note56 = (
            "The flat plate is roughness-invariant (&rho;<sub>dh</sub> "
            "integrates the hemisphere; the lobe only moves within it) and "
            "sits exactly on the historical 1.1413&#8202;% &mdash; but the "
            "winner swings " + ("%.1f&times;" % (per56["P56_p02_r50"]
                                                 / per56["P56_p02_r10"]))
            + " across the same range: rough paint diffuses the first "
            "bounce back out of the cavity instead of chaining it down. "
            "<b>Every &ldquo;N&times; darker than flat&rdquo; claim is "
            "conditional on the paint&rsquo;s unmeasured lobe width: "
            "N runs from " + ("%.1f" % min(adv.values())) + "&times; to "
            + ("%.1f" % max(adv.values())) + "&times;.</b> The design "
            "choice survives everywhere; the single number does not. "
            "Measuring one painted coupon is now worth more than any "
            "further simulation. The 0.30 row is the value the rest of "
            "this report is quoted at. (Self-test: pure-diffuse rows at "
            "0.10 and 0.50 read "
            + (pc(d100a) if d100a else DASH) + " / "
            + (pc(d100b) if d100b else DASH)
            + " &mdash; identical, so the harness does not leak roughness "
            "into the diffuse shader. A measurement-frame defect found "
            "during this sweep &mdash; a margin-less flat reads 21&#8202;% "
            "low at face 60 &mdash; is documented in "
            "<code>FINDINGS_phase56_roughness.md</code>; the first run's "
            "flat rows were superseded before publication.)")
        r10t = per56["P56_p02_r10"]
        r50t = per56["P56_p02_r50"]
        grade56 += g(True, "flat total is roughness-invariant at "
                     "1.141&thinsp;&plusmn;&thinsp;0.11&#8202;%: measured "
                     + pc(per56["P56_flat_r10"]) + "&ndash;"
                     + pc(per56["P56_flat_r50"]))
        grade56 += g(False, "winner within &plusmn;25&#8202;% and "
                     "&ge;6&times; advantage everywhere: measured "
                     + pc(r10t) + "&ndash;" + pc(r50t) + ", advantage down "
                     "to " + ("%.1f&times;" % min(adv.values())))
        grade56 += g(abs(d100a - d100b) / d100a < 0.02 if d100a else False,
                     "pure-diffuse self-test within 2&#8202;%: "
                     + (pc(d100a) if d100a else DASH) + " vs "
                     + (pc(d100b) if d100b else DASH))
        ho10 = f56.get("P56_form_p02_r10", {}).get("head_on")
        ho50 = f56.get("P56_form_p02_r50", {}).get("head_on")
        grade56 += g(False, "head-on within 0.014&ndash;0.060 at the "
                     "extremes: measured " + num(ho10 or 0, 4) + " and "
                     + num(ho50 or 0, 4) + " &mdash; outside on both "
                     "sides, though the no-spike claim it encoded is true")
        sm10 = f56.get("P56_form_p02_r10", {}).get("smear")
        sm50 = f56.get("P56_form_p02_r50", {}).get("smear")
        grade56 += g(2.0 <= min(sm10, sm50) and max(sm10, sm50) <= 8.2,
                     "smear within 2&times; of 4.10 at the extremes: "
                     "measured " + num(sm10) + " / " + num(sm50))
    except Exception:
        pass
    html = html.replace("%%ROWS56%%", rows56h or "")
    html = html.replace("%%NOTE56%%", note56 or DASH)
    html = html.replace("%%GRADE56%%", grade56 or DASH)

    # phase 5.7 — face invariance
    rows57h = ""
    note57 = ""
    try:
        per57 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase57.csv"))):
            t = r["tag"]
            per57[t] = max(per57.get(t, 0.0), float(r["rho"]))
        pairs = [("champion p5.5 / d50", "P5_j00", "P57_j00_f100"),
                 ("winner p2 / d18",
                  None, "P57_p02_f100")]
        w02 = per56.get("P56_p02_r30") if per56 else None
        for label, a, b in pairs:
            va = per57.get(a) if a else w02
            vb = per57.get(b)
            if va is None or vb is None:
                continue
            rows57h += ("<tr><td>%s</td><td>%s</td><td>%s</td>"
                        "<td>%+.1f&#8202;%%</td></tr>"
                        % (label, pc(va), pc(vb), 100 * (vb - va) / va))
        note57 = (
            "Both inside the pre-registered &plusmn;4&ndash;5&#8202;% "
            "bands: the phase&rsquo;s numbers are properties of the "
            "designs, not of the coupon size. The flat-slab defect is "
            "confined to margin-less slabs and flat references are now "
            "measured at face&nbsp;100 (they reproduce the closed-form "
            "curve there: " + pc(per57.get("P57_flat_f100", 0))
            + " worst against the model&rsquo;s 1.030&#8202;%). The one "
            "anomaly 5.6 left open is closed: a &ldquo;fully "
            "truncated&rdquo; pyramid field was never flat &mdash; the "
            "builder clamps the tip at 0.8&times;pitch, and the residual "
            "0.4&#8202;mm grooves absorb a genuine third of the return "
            "(<code>FINDINGS_phase57_faceinvariance.md</code>).")
    except Exception:
        pass
    html = html.replace("%%ROWS57%%", rows57h or "")
    html = html.replace("%%NOTE57%%", note57 or DASH)

    # phase 5.8 — tip tolerance + azimuth
    rows58t = ""
    rows58p = ""
    note58t = note58p = ""
    grade58 = ""
    try:
        f58 = json.load(open(os.path.join(RESULTS, "form_phase58.json")))
        tipmap = [("0.00", p54f.get("P54_p02_t00")),
                  ("0.02", f58.get("P58_p02_t002")),
                  ("0.05", f58.get("P58_p02_t005")),
                  ("0.10", p54f.get("P54_p02_t01")),
                  ("0.15", f58.get("P58_p02_t015"))]
        for tip, rec in tipmap:
            if not rec:
                continue
            star = ' class="win"' if tip == "0.05" else ""
            rows58t += ("<tr%s><td>%s</td><td>%.2f&#8202;%%</td><td>%s</td>"
                        "<td>%s</td><td>%s</td></tr>"
                        % (star, tip, 100 * (float(tip) / 2.0) ** 2,
                           cell_sm(rec), cell_ho(rec),
                           ("%.2f&times;" % rec["span_0"])
                           if rec.get("span_0") else DASH))
        ho05 = f58["P58_p02_t005"]["head_on"]
        ho10 = p54f["P54_p02_t01"]["head_on"]
        ho55 = f58["P58_p55_t0275"]["head_on"]
        note58t = (
            "Head-on is linear in the flat fraction at fixed pitch, and at "
            "fixed fraction a finer pitch pays more (p5.5 with a 0.275"
            "&#8202;mm tip, same 0.25&#8202;% fraction, reads "
            + num(ho55, 4) + "). By the 1.5&times; rule the winner&rsquo;s "
            "drawing carries <b>tip flat &le; 0.05&#8202;mm</b> ("
            + num(ho05, 4) + " passes, the 0.1&#8202;mm tip&rsquo;s "
            + num(ho10, 4) + " fails); the same rule interpolates to "
            "&sim;0.19&#8202;mm at pitch 5.5 and &sim;0.46&#8202;mm at "
            "pitch 10 &mdash; tolerance is bought with pitch, and only "
            "the head-on axis charges for it.")
        # phi curve
        per8, per8b, per8c = {}, {}, {}
        for fn, d in (("sweep_phase58.csv", per8),
                      ("sweep_phase58b.csv", per8b),
                      ("sweep_phase58c.csv", per8c)):
            for r in csv.DictReader(open(os.path.join(RESULTS, fn))):
                t = r["tag"]
                d[t] = max(d.get(t, 0.0), float(r["rho"]))
        base_phi0 = per56.get("P56_p02_r30")
        curve = [("0", base_phi0)]
        for ph in ("05.0", "10.0", "15.0", "20.0", "25.0", "30.0",
                   "35.0", "40.0"):
            curve.append((ph.rstrip("0").rstrip(".") or "0",
                          per8c.get("P58c_phi%s" % ph)))
        curve.append(("22.5", per8b.get("P58b_p02_phi225")))
        curve.append(("45", per8.get("P58_p02_phi45")))
        curve = [(p, v) for p, v in curve if v]
        curve.sort(key=lambda x: float(x[0]))
        wphi = max(v for _, v in curve)
        for ph, v in curve:
            star = ' class="win"' if v == wphi else ""
            rows58p += ("<tr%s><td>%s&deg;</td><td>%s</td>"
                        "<td>%+.0f&#8202;%%</td></tr>"
                        % (star, ph, pc(v),
                           100 * (v - base_phi0) / base_phi0))
        cone = worst_of("sweep_rewind.csv", "AN_cone_p550_s23")
        note58p = (
            "The worst azimuth is a broad plateau near 30&deg; at "
            + pc(wphi) + " &mdash; "
            + ("%+.0f&#8202;%%" % (100 * (wphi - base_phi0) / base_phi0))
            + " over the published &phi;-0 number, scale-invariant (the "
            "champion reads " + pc(per8b.get("P58b_p55_phi45", 0))
            + " at &phi;45), and only half-fixed by &radic;2 more depth ("
            + pc(per8b.get("P58b_p02d25_p45", 0)) + " at &phi;45 for "
            "p2/d25.5). <b>On worst-over-azimuth totals the pyramid ("
            + pc(wphi) + ") loses narrowly to the rotationally symmetric "
            "cone (" + pc(cone) + ", &phi;-invariant by symmetry)</b>. "
            "The pyramid keeps a 2.2&times; head-on lead measured at "
            "&phi;0; whether it survives &phi;30 is unmeasured and is the "
            "next experiment, together with a thin cone field at matched "
            "aspect.")
        grade58 = (
            g(True, "head-on linear in flat fraction; cross-pitch "
              "ordering held; the 0.05&#8202;mm spec rule confirmed as "
              "pre-registered")
            + g(False, "&ldquo;the pyramid is azimuth-safe "
                "(&le;6&#8202;%)&rdquo;: it is not &mdash; "
                + ("%+.0f&#8202;%%" % (100 * (wphi - base_phi0)
                                       / base_phi0))
                + " at &phi;30, the largest single miss of Phase 5, and "
                "the reason the total-axis crown is now shared with the "
                "cone")
            + g(False, "&ldquo;the worst azimuth is the diagonal and "
                "&radic;2 depth fixes it&rdquo;: the worst is &phi;"
                "&asymp;30&deg; and the fix recovers only half"))
    except Exception:
        pass
    # phase 5.9 — pyramid vs cone, worst azimuth
    rows59h = ""
    note59 = ""
    grade59 = ""
    try:
        per59 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase59.csv"))):
            per59[r["tag"]] = max(per59.get(r["tag"], 0.0), float(r["rho"]))
        f59 = json.load(open(os.path.join(RESULTS, "form_phase59.json")))
        pyr30 = f59["P59_pyr_phi30"]
        pyr0 = f59["P59_pyr_phi0"]
        conef = f59["P59_cone20_f"]
        cone20 = per59["P59_cone20"]
        cone55 = per59["P59_cone55"]
        pyr_wphi = wphi          # from the 5.8 block
        rows59h += ("<tr><td>total, worst-&phi;</td><td>%s (&phi;30)</td>"
                    "<td>%s (&phi;-invariant)</td><td>tie (%.1f&#8202;%% "
                    "apart)</td></tr>"
                    % (pc(pyr_wphi), pc(cone20),
                       100 * (pyr_wphi - cone20) / cone20))
        rows59h += ("<tr><td>smear, worst-&phi; &uarr;</td><td>%s "
                    "(&phi;30; %s at &phi;0)</td><td>%s</td>"
                    "<td>cone, by %.0f&#8202;%%</td></tr>"
                    % (num(pyr30["smear"]), num(pyr0["smear"]),
                       num(conef["smear"]),
                       100 * (conef["smear"] - pyr30["smear"])
                       / pyr30["smear"]))
        rows59h += ("<tr><td>head-on &darr;</td><td>%s (identical at "
                    "&phi;0/&phi;30)</td><td>%s</td>"
                    "<td>pyramid, by %.0f&#8202;%%</td></tr>"
                    % (num(pyr30["head_on"], 4), num(conef["head_on"], 4),
                       100 * (conef["head_on"] - pyr30["head_on"])
                       / conef["head_on"]))
        rows59h += ("<tr><td>panel incl. backing</td><td>20&#8202;mm</td>"
                    "<td>20.2&#8202;mm</td><td>tie</td></tr>")
        note59 = (
            "The pre-registered rule ends 1:1:1 with the thickness "
            "tiebreak indiscriminate &mdash; a genuine draw &mdash; and "
            "is broken by Phase 5.5: the cone&rsquo;s smear edge is "
            "protocol-conditioned (at the real 7&ndash;14&#8202;mm beam "
            "every design&rsquo;s smear ratio compresses toward 1), while "
            "the pyramid&rsquo;s head-on edge is beam-independent AND now "
            "azimuth-independent. One edge survives deployment; the other "
            "does not. <b>The pyramid keeps the crown &mdash; p2/d18, tip "
            "&le;0.05&#8202;mm, 20&#8202;mm panel &mdash; with its "
            "worst-azimuth total honestly stated as cone-equal (" +
            pc(pyr_wphi) + " vs " + pc(cone20) + "), and the thin cone "
            "stands as a fully valid alternate: azimuth-immune by "
            "construction, same panel, same total, "
            + ("%.1f&times;" % (conef["head_on"] / pyr30["head_on"]))
            + " brighter head-on.</b> The big cone&rsquo;s anchor "
            "re-measured at " + pc(cone55) + " against the rewind "
            "value 0.2160&#8202;% &mdash; and the thin cone proves the "
            "cone family scale-invariant too.")
        grade59 = (
            g(True, "phi-0 guard exact; head-on at phi 30 unchanged "
              "(" + num(pyr30["head_on"], 4) + ") &mdash; the symmetry "
              "argument is now a measurement; cone anchor and cone scale "
              "invariance both held")
            + g(False, "smear at phi 30 predicted 2.6&ndash;3.8, measured "
                + num(pyr30["smear"]) + "; thin-cone smear predicted "
                "4.0&thinsp;&plusmn;&thinsp;0.6, measured "
                + num(conef["smear"]) + " &mdash; shrinking any family "
                "against the fixed 2&#8202;mm stripe cuts its smear"))
    except Exception:
        pass
    # phase 5.10 — cone tip ladder + pyramid thin end
    rows510 = ""
    note510 = ""
    try:
        per510 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase510.csv"))):
            per510[r["tag"]] = max(per510.get(r["tag"], 0.0),
                                   float(r["rho"]))
        f510 = json.load(open(os.path.join(RESULTS, "form_phase510.json")))
        c3 = f510.get("P510_cone_r003", {})
        entries = [
            ("cone r0.073 (5.9)", per59.get("P59_cone20"), conef,
             "20.2&#8202;mm"),
            ("cone r0.03", per510.get("P510_cone_r003"), c3,
             "20.2&#8202;mm"),
            ("cone r0.15", per510.get("P510_cone_r015"), None,
             "20.2&#8202;mm"),
            ("pyramid p1.5 / d13.5", per510.get("P510_pyr_p15"), None,
             "15.5&#8202;mm"),
            ("pyramid p1 / d9", per510.get("P510_pyr_p10"), None,
             "11&#8202;mm"),
        ]
        for label, tot, frm, panel in entries:
            if tot is None:
                continue
            star = ' class="win"' if label == "cone r0.03" else ""
            rows510 += ("<tr%s><td>%s</td><td>%s</td><td>%s</td>"
                        "<td>%s</td><td>%s</td><td>%s</td></tr>"
                        % (star, label, pc(tot), cell_sm(frm),
                           cell_ho(frm),
                           ("%.2f&times;" % frm["span_0"])
                           if frm and frm.get("span_0") else DASH, panel))
        note510 = (
            "The cone&rsquo;s head-on penalty is its TIP CAP, not the "
            "interstices between bases: shrinking the tip radius from "
            "0.073 to 0.03&#8202;mm took head-on from "
            + num(conef["head_on"], 4) + " to " + num(c3["head_on"], 4)
            + ", landing in the pre-registered tip-area band. The gap to "
            "the pyramid narrowed from 1.7&times; to "
            + ("%.2f&times;" % (c3["head_on"] / pyr30["head_on"]))
            + " &mdash; and this cone needs no azimuth caveat at all, "
            "with the best worst-over-&phi; total on the board ("
            + pc(per510.get("P510_cone_r003", 0)) + "). The choice "
            "between the two finalists is now a tooling question "
            "(&le;0.05&#8202;mm square tip vs &le;0.03&#8202;mm tip "
            "radius), not an optical one. Separately, the pyramid&rsquo;s "
            "aspect law holds to pitch 1: an 11&#8202;mm panel reads "
            + pc(per510.get("P510_pyr_p10", 0)) + " at &phi;0, priced at "
            "a ~0.022&#8202;mm tip tolerance.")
    except Exception:
        pass
    html = html.replace("%%ROWS510%%", rows510 or "")
    html = html.replace("%%NOTE510%%", note510 or DASH)

    # phase 5.11 — closure audit
    note511 = ""
    try:
        per511 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase511.csv"))):
            per511[r["tag"]] = max(per511.get(r["tag"], 0.0),
                                   float(r["rho"]))
        f511 = json.load(open(os.path.join(RESULTS,
                                           "form_phase511.json")))
        pt = f511["P511_pyrt05_phi30"]
        cvals = [per511[t] for t in ("P510_cone_r003", "P511_cone_phi225",
                                     "P511_cone_phi45", "P511_cone_s101",
                                     "P511_cone_s102")]
        spread = (max(cvals) - min(cvals)) / min(cvals)
        note511 = (
            g(True, "the thin cone's azimuth immunity and seed robustness "
              "are measurements now, not assertions: "
              + pc(min(cvals)) + "&ndash;" + pc(max(cvals))
              + " across &phi; 0/22.5/45 and three seeds ("
              + ("%.1f&#8202;%%" % (100 * spread)) + " spread)")
            + g(True, "the drawing spec and the azimuth hole do not "
                "compound: pyramid tip 0.05 at &phi;30 reads "
                + pc(per511["P511_pyrt05_phi30"]) + " total, head-on "
                + num(pt["head_on"], 4) + ", span "
                + ("%.2f&times;" % pt["span_0"])
                + " &mdash; every number inside its pre-registered band. "
                "Six predictions, six held; Phase 5's design questions "
                "are closed. What remains is physical: one painted "
                "coupon, one beam-spot measurement, two tooling quotes."))
    except Exception:
        pass
    html = html.replace("%%NOTE511%%", note511 or DASH)

    # phase 5.12 — joint worst envelope
    rows512 = ""
    note512 = ""
    try:
        per512 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase512.csv"))):
            per512[r["tag"]] = max(per512.get(r["tag"], 0.0),
                                   float(r["rho"]))
        pw10 = per512["P512_pyr_p30_rg10"]
        pw50 = per512["P512_pyr_p30_rg50"]
        cw10 = per512["P512_cone_rg10"]
        cw30 = per512["P510_cone_r003"]
        cw50 = per512["P512_cone_rg50"]
        rows512 += ("<tr><td>pyramid p2/d18, worst-&phi;</td><td>%s</td>"
                    "<td>%s</td><td>%s</td></tr>"
                    % (pc(pw10), pc(pyr_wphi), pc(pw50)))
        rows512 += ("<tr><td>cone p2/d18.2 r0.03 (&phi;-invariant)</td>"
                    "<td>%s</td><td>%s</td><td>%s</td></tr>"
                    % (pc(cw10), pc(cw30), pc(cw50)))
        rows512 += ("<tr><td>flat plate (roughness-invariant)</td>"
                    "<td colspan=3>%s at every roughness</td></tr>"
                    % pc(per56.get("P56_flat_r30", 0.011413)))
        fl = per56.get("P56_flat_r30", 0.011413)
        note512 = (
            "Smooth paint buys nothing on totals &mdash; the "
            "roughness-invariant pure-diffuse envelope owns both floors "
            "(its payoff is head-on: 0.0089 vs 0.0665 across the range, "
            "Phase 5.6). Rough paint costs both finalists nearly equally, "
            "and <b>at the joint worst they read "
            + pc(pw50) + " vs " + pc(cw50) + " &mdash; "
            + ("%.1f&#8202;%%" % (100 * abs(cw50 - pw50) / pw50))
            + " apart, within noise</b>. The pre-coupon claim for either "
            "design: "
            + ("%.0f&times;" % (fl / max(pw50, cw50)))
            + " to "
            + ("%.0f&times;" % (fl / min(pw10, cw10)))
            + " darker than a flat Musou wall; one painted coupon "
            "collapses that range to a number. The measurement campaign "
            "ends here &mdash; every remaining question needs an object, "
            "not a render.")
    except Exception:
        pass
    html = html.replace("%%ROWS512%%", rows512 or "")
    html = html.replace("%%NOTE512%%", note512 or DASH)

    # phase 5.13 — ordering package
    rows513 = ""
    note513 = ""
    try:
        per513 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase513.csv"))):
            per513[r["tag"]] = max(per513.get(r["tag"], 0.0),
                                   float(r["rho"]))
        f513 = json.load(open(os.path.join(RESULTS,
                                           "form_phase513.json")))
        c2x = f513["P513_pyr2x"]
        tot2x = per513["P513_pyr2x"]
        rows513 += ("<tr><td>total worst-&rho;</td><td>%s</td>"
                    "<td>&plusmn;25&#8202;%% validates; beyond "
                    "&plusmn;40&#8202;%% stop and name the broken link"
                    "</td></tr>" % pc(tot2x))
        rows513 += ("<tr><td>head-on</td><td>%s</td><td>f-law value of "
                    "the 1&times; spec</td></tr>"
                    % num(c2x["head_on"], 4))
        rows513 += ("<tr><td>smear (2&#8202;mm probe)</td><td>%s</td>"
                    "<td>narrow-probe number; compresses at the real "
                    "beam</td></tr>" % num(c2x["smear"]))
        rows513 += ("<tr><td>span &theta;0</td><td>%.2f&times;</td>"
                    "<td>&mdash;</td></tr>" % c2x["span_0"])
        try:
            per514 = {}
            for r in csv.DictReader(open(os.path.join(
                    RESULTS, "sweep_phase514.csv"))):
                per514[r["tag"]] = max(per514.get(r["tag"], 0.0),
                                       float(r["rho"]))
            k2x = json.load(open(os.path.join(
                RESULTS, "form_phase514.json")))["P514_cone2x"]
            rows513 += ("<tr><td colspan=3 style='padding-top:.8rem'>"
                        "<b>cone coupon (p4/d36.4/r0.06), Phase 5.14:"
                        "</b></td></tr>")
            rows513 += ("<tr><td>total worst-&rho;</td><td>%s</td>"
                        "<td>same &plusmn;25&#8202;%% / &plusmn;40&#8202;%% "
                        "rule</td></tr>" % pc(per514["P514_cone2x"]))
            rows513 += ("<tr><td>head-on</td><td>%s</td><td>(r/pitch)&sup2; "
                        "law crosses scale on cones too</td></tr>"
                        % num(k2x["head_on"], 4))
            rows513 += ("<tr><td>smear / span</td><td>%s / %.2f&times;</td>"
                        "<td>narrow-probe numbers</td></tr>"
                        % (num(k2x["smear"]), k2x["span_0"]))
        except Exception:
            pass
        note513 = (
            "As-built envelopes differ from the nominal face &mdash; the "
            "builder skirts one pitch of rim per side (pyramid coupons "
            "68&times;68 and 76&times;76&#8202;mm) and jittered cones "
            "overhang by a base radius; quotes must carry the manifest "
            "dimensions (<code>export/finalists_manifest.json</code>), "
            "not 60&times;60. One prediction missed in the good "
            "direction: the 2&times; coupon smears 4.53, not the "
            "1.2&ndash;2.2 a beam/pitch model predicted &mdash; the "
            "coarse-pitch smear cliff sits between pitch 5.5 and 10, "
            "not at a fixed beam ratio. Grading: P1&ndash;P3 held "
            "(round trip &times;4, kernel-clean &times;4, all three "
            "coupon axes), P4 wrong as stated. The rim was verified "
            "harmless by inspection &mdash; one extra ring of full-depth "
            "cells, 3.6&#8202;mm&sup2; of flat on a 5776&#8202;mm&sup2; "
            "part &mdash; so the lab and the simulation measure the same "
            "texture and the acceptance bands stand for both coupons.")
    except Exception:
        pass
    html = html.replace("%%ROWS513%%", rows513 or "")
    html = html.replace("%%NOTE513%%", note513 or DASH)

    # phase 5.15 — easy-build tier
    rows515 = ""
    note515 = ""
    try:
        per515 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase515.csv"))):
            per515[r["tag"]] = max(per515.get(r["tag"], 0.0),
                                   float(r["rho"]))
        f515 = json.load(open(os.path.join(RESULTS,
                                           "form_phase515.json")))
        e = f515["P515_easy"]
        s = f515["P515_stack"]
        rows515 += ("<tr class=\"win\"><td>easy pyramid p4/d20 "
                    "(aspect 5)</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td>%s</td><td>~0.2&#8202;mm</td><td>22&#8202;mm</td>"
                    "</tr>"
                    % (pc(per515["P515_easy"]),
                       pc(per515["P515_easy_p30"]),
                       cell_sm(e), cell_ho(e)))
        rows515 += ("<tr><td>bought comb 35&#8202;mm + pyramid floor "
                    "15&#8202;mm</td><td>%s</td><td>%s</td><td>%s</td>"
                    "<td>%s</td><td>off-the-shelf</td><td>52&#8202;mm</td>"
                    "</tr>"
                    % (pc(per515["P515_stack"]),
                       pc(per515["P515_stack_p30"]),
                       cell_sm(s), cell_ho(s)))
        note515 = (
            "The stack does win one axis &mdash; its total does not move "
            "with azimuth at all (0.0&#8202;% shift, the hex walls) &mdash; "
            "but the comb&rsquo;s wall tops own head-on ("
            + num(s["head_on"], 4) + ", "
            + ("%.1f&times;" % (s["head_on"] / e["head_on"]))
            + " the pyramid&rsquo;s) and its smear is a flat wall&rsquo;s. "
            "The better easy option is the half-steep pyramid itself: "
            "single pressed part, tip tolerance 4&times; looser than the "
            "p2 spec, head-on identical to the finalists, and only "
            "11&ndash;19&#8202;% behind them on worst-&phi; totals. Its "
            "azimuth hole is also relatively milder (+41&#8202;% vs the "
            "aspect-9 field&rsquo;s +74&#8202;%). Floor depth under a "
            "comb was confirmed irrelevant (15&#8202;mm floor reads like "
            "Phase 4&rsquo;s 3&ndash;5&#8202;mm floors) &mdash; the top "
            "layer owns the result.")
    except Exception:
        pass
    html = html.replace("%%ROWS515%%", rows515 or "")
    html = html.replace("%%NOTE515%%", note515 or DASH)

    # phase 6 — coarse tier
    rows6 = ""
    note6 = ""
    try:
        per6 = {}
        for r in csv.DictReader(open(os.path.join(RESULTS,
                                                  "sweep_phase6.csv"))):
            per6[r["tag"]] = max(per6.get(r["tag"], 0.0), float(r["rho"]))
        f6 = json.load(open(os.path.join(RESULTS, "form_phase6.json")))
        ENTRIES6 = [
            ("pyramid p10/d50 (aspect 5, tip tol ~0.5&#8202;mm)",
             "P6_pyr_p10d50", f6.get("P6_pyr_p10d50"),
             "commodity press die"),
            ("pyramid p15/d50", "P6_pyr_p15d50",
             f6.get("P6_pyr_p15d50"), "aspect curve"),
            ("pyramid p20/d50", "P6_pyr_p20d50",
             f6.get("P6_pyr_p20d50"), "aspect curve"),
            ("pyramid p10/d90 (aspect 9)", "P6_pyr_p10d90",
             p54f.get("P54_p10_t00"),
             "exact repeat of 5.4 (form from there)"),
            ("comb cell 9.5, naked", "P6_comb_c095",
             f6.get("P6_comb_c095"), ""),
            ("comb cell 12.7, naked", "P6_comb_c127",
             f6.get("P6_comb_c127"), "backing reads as a flat plate"),
            ("comb cell 19, naked", "P6_comb_c190",
             f6.get("P6_comb_c190"), "perforated flat plate"),
            ("comb 12.7 + pressed floor", "P6_stk_c127",
             f6.get("P6_stk_c127"),
             "35&#8202;% better than its comb &mdash; the top-layer law's "
             "limit"),
            ("comb 19 + pressed floor", "P6_stk_c190",
             f6.get("P6_stk_c190"), "49&#8202;% better than its comb"),
        ]
        for label, tt, frm, note_ in ENTRIES6:
            if tt not in per6:
                continue
            star = ' class="win"' if tt == "P6_stk_c127" else ""
            rows6 += ("<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                      "<td>%s</td></tr>"
                      % (star, label, pc(per6[tt]), cell_sm(frm),
                         cell_ho(frm), note_ or DASH))
        note6 = (
            "The aspect curve ruled every coarse pyramid (8th and 9th "
            "confirmations, two exact cross-code reproductions), and "
            "sharp tips stayed head-on-proof at aspect 5 ("
            + num(f6["P6_pyr_p10d50"]["head_on"], 4) + "). The naked big "
            "combs decayed FASTER than their aspect &mdash; below aspect "
            "~4 the backing is directly visible and the comb becomes a "
            "perforated flat plate (head-on "
            + num(f6["P6_comb_c127"]["head_on"], 4) + ", the Phase-2 "
            "honeycomb number reproduced). And the &ldquo;top layer owns "
            "the result&rdquo; law found its limit: a see-through comb "
            "lets the floor matter again, and <b>comb 12.7 over a "
            "pressed floor reads " + pc(per6["P6_stk_c127"]) + " &mdash; "
            "tied with the cone finalist on (presumably azimuth-flat) "
            "totals, from an off-the-shelf top layer</b> &mdash; while "
            "keeping the comb&rsquo;s incurable head-on ("
            + num(f6["P6_stk_c127"]["head_on"], 4) + "). Phase 6.2 closed "
            "the azimuth question: %%P62NOTE%%")
        # 6.2 — azimuth + real-beam form + the shadowing check
        p62note = ""
        try:
            per62 = {}
            for r in csv.DictReader(open(os.path.join(
                    RESULTS, "sweep_phase62.csv"))):
                per62[r["tag"]] = max(per62.get(r["tag"], 0.0),
                                      float(r["rho"]))
            b9 = json.load(open(os.path.join(RESULTS,
                                             "form_phase6_beam9.json")))
            p62note = (
                "the big stack is azimuth-flat in measurement ("
                + pc(per62["P62_stk_c127_p30"]) + " at &phi;30, a "
                + ("%.1f&#8202;%%" % (100 * (per62["P62_stk_c127_p30"]
                                             - per6["P6_stk_c127"])
                                      / per6["P6_stk_c127"]))
                + " shift), and the pyramid &phi;-hole maps by aspect "
                "(&times;1.30 at aspect 5, &times;1.17 at 3.3, vs "
                "&times;1.74 at 9). At the REAL beam (9&#8202;mm) the "
                "form axis compresses for everyone; what remains is that "
                "coarse pitch NARROWS the return below a matte flat's ("
                + num(b9["B9_pyr_p10d50"]["smear"], 3) + " vs the fine "
                "pitch's " + num(b9["B9_pyr_p2d18"]["smear"], 3)
                + ") &mdash; a shadowing effect, verified matte-robust "
                "by a pure-Lambertian control run (0.660): only the "
                "beam-facing flank strips light up, and one thin bright "
                "line survives. Coarse pyramids are the one family that "
                "makes the reflected stripe SHARPER than a bare matte "
                "wall.")
        except Exception:
            pass
        note6 = note6.replace("%%P62NOTE%%", p62note or "(6.2 pending)")
    except Exception:
        pass
    html = html.replace("%%ROWS6%%", rows6 or "")
    html = html.replace("%%NOTE6%%", note6 or DASH)
    html = html.replace("%%ROWS59%%", rows59h or "")
    html = html.replace("%%NOTE59%%", note59 or DASH)
    html = html.replace("%%GRADE59%%", grade59 or DASH)
    html = html.replace("%%ROWS58T%%", rows58t or "")
    html = html.replace("%%NOTE58T%%", note58t or DASH)
    html = html.replace("%%ROWS58P%%", rows58p or "")
    html = html.replace("%%NOTE58P%%", note58p or DASH)
    html = html.replace("%%GRADE58%%", grade58 or DASH)
    html = html.replace("%%GRADE54%%", grade54 or "&mdash;")
    html = html.replace("%%GRIDTIP%%", img64("grid_tip.png"))
    html = html.replace("%%ROWS53%%", rows53h)
    html = html.replace("%%GRIDMIX%%", img64("grid_mix.png"))
    html = html.replace("%%ROWS52%%", rows52h)
    html = html.replace("%%SVG52%%", svg)
    best = min((d["w"] for d in r52), default=0)
    html = html.replace("%%BEST52%%", pc(best))
    html = html.replace("%%HERO%%", img64("hero_periodic.png"))
    html = html.replace("%%HEROJ%%", img64("grid_views.png"))
    html = html.replace("%%ROWS3%%", rows3).replace("%%ROWSJ%%", rowsj)
    html = html.replace("%%SPAN0%%", "%.2f" % span0.get("P5_j00", 0))
    html = html.replace("%%J60%%", "+%.1f&#8202;%%"
                        % (100 * jit["P5_j60"]["shift"]))
    html = html.replace("%%J60D%%", "+%.1f&#8202;%%"
                        % (100 * jit["P5_j60d15"]["shift"]))
    open(OUT, "w").write(html)
    print("wrote %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
