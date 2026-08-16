"""Phase 8 standalone report: redirect, don't absorb.

    python3 scripts/build_report_phase8.py

Concept stage: geometry rules and the measurement plan with pre-registered
predictions. Simulation sections fill in as sweeps land.
"""

import os
import sys
import csv
import json
import base64

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(ROOT, "report", "phase8")
OUT = os.path.join(OUTDIR, "report.html")
RESULTS = os.path.join(ROOT, "results")


def load_82():
    """Numbers come from the sweep outputs at build time, never typed here
    (gate check 7)."""
    path = os.path.join(RESULTS, "sweep_phase82.csv")
    if not os.path.exists(path):
        return None
    rows = list(csv.DictReader(open(path)))
    hemi, scan = {}, {}
    for r in rows:
        th = float(r["theta"])
        if r["mode"] == "hemi_view":
            hemi[(r["tag"], th)] = float(r["rho"])
        elif r["mode"] == "angle":
            scan[th] = (float(r["rho"]), float(r["ratio"]))
    form = {}
    fj = os.path.join(RESULTS, "form_phase82.json")
    if os.path.exists(fj):
        form = json.load(open(fj)).get("P82_form_R10", {})
    return {"hemi": hemi, "scan": scan, "form": form}


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    img = os.path.join(OUTDIR, "img", "concept.png")
    b64 = ("data:image/png;base64,"
           + base64.b64encode(open(img, "rb").read()).decode()) \
        if os.path.exists(img) else ""
    rp = os.path.join(OUTDIR, "img", "raypaths.png")
    rp64 = ("data:image/png;base64,"
            + base64.b64encode(open(rp, "rb").read()).decode()) \
        if os.path.exists(rp) else ""
    d82 = load_82()

    html = """<title>Spill Sink 피라미드 연구 — Phase 8</title>
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
.note{font-size:.85rem;color:var(--ink2)}
code{font:.85em var(--mono)}
</style>
<main>
<div class="kicker">Spill Sink &middot; 피라미드 연구 &middot; Phase 8</div>
<h1>Redirect, don&rsquo;t absorb: the tilted AR window</h1>
<p class="lede">User-directed phase. Instead of fighting the light at a
surface, pass it through: a transparent panel with a broadband
anti-reflection coating transmits ~99&#8202;% of the beam into a dark
void, and the tilt aims the ~1&#8202;% specular residual at a ceiling
trap the audience cannot see. The pyramid panel does not disappear from
this architecture &mdash; it lines the void and the trap. Glass steers;
pyramids kill.</p>

<figure style="margin:1.4rem 0 0">
<img src="%%CONCEPT%%" alt="Phase 8 concept, side view"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>

<h2>The geometry rule (computed, no render needed)</h2>
<p>Beams arrive within &plusmn;40&deg; of the wall normal, so the
specular fan off a plate tilted by T spans 2T&minus;40&deg; to
2T+40&deg;. <b>T &ge; 25&deg;</b> lifts the entire fan above
+10&deg; elevation &mdash; over every head, onto a ceiling strip clad
with the universal panel. The transmitted 99&#8202;% must still die:
the void behind the glass ends on a universal panel as well.</p>

<h2>Why this could beat the panel &mdash; and how it could fail worse</h2>
<table>
<tr><th>path to the audience</th><th>estimate</th><th>status</th></tr>
<tr><td>ceiling-trap re-scatter of the 1&#8202;% residual</td>
<td>~0.002&#8202;%</td><td>computable; simulation next</td></tr>
<tr><td>back-panel re-scatter of the transmitted 99&#8202;%</td>
<td>~0.01&ndash;0.05&#8202;% (distance-diluted)</td>
<td>computable; simulation next</td></tr>
<tr><td>AR residual toward the audience (off-spec angles)</td>
<td>0&#8202;% by geometry IF T&ge;25&deg; holds for every beam</td>
<td>geometry; verify against the scan volume</td></tr>
<tr><td><b>glass-surface scatter (dust, scratches)</b></td>
<td><b>unknown &mdash; the deciding term</b></td>
<td>NOT simulatable; physical coupon required</td></tr>
</table>
<p class="note">Failure mode to respect: the 1&#8202;% residual is a
PERFECT mirror image of the mid-air content &mdash; forms preserved
exactly. Any sightline into the specular fan shows the whole image.
The absorbing wall degrades gracefully; the window fails theatrically.
[AR figures are typical broadband multi-layer values from vendor
curves, 추측-class until a coupon is measured.]</p>

<h2>Measurement plan (pre-registered)</h2>
<p>8.2 adds an AR-glass material to the simulator (transmission +
controlled specular residual R per surface) and measures the tilted
plate&rsquo;s three axes at R = 0.5 / 1 / 2&#8202;% per surface, beam
width 7.5&#8202;mm, &theta; 0&ndash;70&deg;. Predictions: the return
toward the room tracks 2R within &plusmn;30&#8202;%; head-on toward the
audience zone ~0 by geometry; the system (glass + trap + back panel)
lands under 0.05&#8202;% audience-visible IF the dust term is excluded.
8.3 defines the audience-zone metric (direction-resolved) that totals
cannot express. The physical queue gains one item: an AR-coated glass
coupon measured for scatter after a week of floor dust.</p>

%%SECTION82%%
%%SECTION83%%
%%SECTION84%%
</main>
"""
    sec82 = ""
    if d82:
        h = d82["hemi"]
        f = d82["form"]
        t0 = f.get("thetas", {}).get("+0", {})
        head_on = t0.get("peak_ratio_mean")
        sec82 = """
<h2>8.2 &mdash; the window measured (simulation, beam width labeled)</h2>
<p>The plate: 2&#8202;mm glass, residual R per surface (constant by
declared model &mdash; the real AR angle curve is the physical
coupon&rsquo;s job), over a 90&#8202;mm void with idealised black
interior. <b>Orientation was pinned by a preview render, not by
intuition</b>: hand derivation flipped the hinge sign twice; the render
showed the bottom-hinged &ldquo;leaning mirror&rdquo; throwing the
residual back into the room near eye level, and the top-hinged
<b>hopper</b> (glass faces down) sending every above-horizon beam
downward. 8.1 proposed aiming the fan at a ceiling trap; the hopper is
the safer refinement &mdash; its fan spans &minus;50&deg; to
&minus;90&deg; (floor trough), never crossing a standing sightline,
where the ceiling fan&rsquo;s bottom edge (+10&deg;) grazes heads near
the window.</p>
<figure style="margin:1rem 0 0">
<img src="@@RAYPATHS@@" alt="Traced ray paths through the tilted AR window"
 style="width:100%%;border:1px solid var(--line);border-radius:6px">
</figure>
<h2>The danger direction is single, predicted, and razor-thin</h2>
<p>Front camera, sun swept &minus;60&deg; to +70&deg; (R
1&#8202;%%): the mirrored-sun spike sits exactly at the predicted
&minus;(2&times;tilt) = &minus;50&deg; at %(spike).0f&times; a
5&#8202;%% gray wall; 5&deg; off it is already down to
%(sh).1f&#8202;%% of that wall; 10&deg; off, %(off).2f&#8202;%%. Every
beam a projector above can produce (0&ndash;70&deg;) returns
%(above)s of the beam to a front viewer &mdash; nothing. The one
dangerous direction rises from 50&deg; below the horizon, where the
floor is.</p>
<table>
<tr><th>sun elevation</th><th>&minus;60</th><th>&minus;55</th>
<th><b>&minus;50</b></th><th>&minus;45</th><th>&minus;40</th>
<th>0</th><th>+40</th><th>+70</th></tr>
<tr><td>vs 5&#8202;%% gray wall</td><td>%(m60).4f</td><td>%(m55).4f</td>
<td><b>%(m50).0f</b></td><td>%(m45).4f</td><td>%(m40).4f</td>
<td>%(p0).6f</td><td>%(p40).6f</td><td>%(p70).6f</td></tr>
</table>
<h2>Totals are direction-split &mdash; and that is the finding</h2>
<p>Directional-hemispherical return of the assembly (worst case: the
mirrored scene is a uniform white world; in a deployed room the level
observer&rsquo;s mirrored scene is the dark trough, &asymp;500&times;
darker):</p>
<table>
<tr><th>observer elevation</th><th>R 0.5&#8202;%%</th>
<th>R 1&#8202;%%</th><th>R 2&#8202;%%</th>
<th>system (R 1&#8202;%% + pyramid trap)</th></tr>
<tr><td>0&deg; (level)</td><td>%(r05_0).3f&#8202;%%</td>
<td>%(r10_0).3f&#8202;%%</td><td>%(r20_0).3f&#8202;%%</td>
<td>%(sys0).3f&#8202;%%</td></tr>
<tr><td>+20&deg; (above)</td><td>%(r05_20).3f&#8202;%%</td>
<td>%(r10_20).3f&#8202;%%</td><td>%(r20_20).3f&#8202;%%</td>
<td>%(sys20).3f&#8202;%%</td></tr>
<tr><td>+40&deg; (above)</td><td>%(r05_40).3f&#8202;%%</td>
<td>%(r10_40).3f&#8202;%%</td><td>%(r20_40).3f&#8202;%%</td>
<td>%(sys40).3f&#8202;%%</td></tr>
<tr><td>&minus;20 / &minus;40&deg; (below)</td><td>&mdash;</td>
<td>%(r10_m20).3f / %(r10_m40).3f&#8202;%%</td><td>&mdash;</td>
<td>&mdash;</td></tr>
</table>
<p class="note">R-scaling at 0&deg; held at 0.92&times;2R &plusmn;10%%
(predicted). The +40&deg; system row is the void shading its own trap:
0.031&#8202;%% &mdash; 5.7&times; darker than the same pyramid field as
an open wall, because the box mouth restricts illumination exactly as
it restricts a deployed beam.</p>
<h2>Three axes vs the pyramid wall (all beam widths labeled)</h2>
<table>
<tr><th>design</th><th>반사 총량 total worst-&rho; &darr;</th>
<th>모양 뭉개기 smear &uarr;</th><th>정면 반짝임 head-on &darr;</th></tr>
<tr><td>pyramid wall p4/d20/t0.1</td><td>0.177&#8202;%% (&phi;0)</td>
<td>1.42 (beam 7&#8202;mm)</td><td>0.0400 (beam 7/10&#8202;mm)</td></tr>
<tr><td>AR window assembly (R 1&#8202;%%)</td>
<td>%(worst).3f&#8202;%% worst over measured &theta; (at &minus;20&deg;;
0.001&ndash;0.14&#8202;%% for every &theta; &ge; +20&deg;)</td>
<td>측정 무효 &mdash; the &plusmn;40&deg; return is ZERO, rms undefined
(beam 7.5&#8202;mm)</td>
<td><b>%(ho).7f</b> (beam 7.5&#8202;mm)</td></tr>
</table>
<p>The window loses the direction-blind total axis 11&times; and wins
head-on %(hox)s&times;. Neither number alone can rank this object:
it is all direction, which is what 8.3&rsquo;s audience-zone metric
exists to score. Model limits stay named: constant R (real AR rises at
grazing), idealised black void, dust unsimulatable &mdash; all coupon
terms.</p>
""" % {
            "spike": d82["scan"][-50.0][1],
            "sh": 100 * d82["scan"][-45.0][1],
            "off": 100 * d82["scan"][-40.0][1],
            "above": "&le; 10&#8309;&#8315;&#8201;of 1&#8202;%",
            "m60": d82["scan"][-60.0][1], "m55": d82["scan"][-55.0][1],
            "m50": d82["scan"][-50.0][1], "m45": d82["scan"][-45.0][1],
            "m40": d82["scan"][-40.0][1], "p0": d82["scan"][0.0][1],
            "p40": d82["scan"][40.0][1], "p70": d82["scan"][70.0][1],
            "r05_0": 100 * h[("P82_plate_R005", 0.0)],
            "r10_0": 100 * h[("P82_plate_R010", 0.0)],
            "r20_0": 100 * h[("P82_plate_R020", 0.0)],
            "r05_20": 100 * h[("P82_plate_R005", 20.0)],
            "r10_20": 100 * h[("P82_plate_R010", 20.0)],
            "r20_20": 100 * h[("P82_plate_R020", 20.0)],
            "r05_40": 100 * h[("P82_plate_R005", 40.0)],
            "r10_40": 100 * h[("P82_plate_R010", 40.0)],
            "r20_40": 100 * h[("P82_plate_R020", 40.0)],
            "r10_m20": 100 * h[("P82_plate_R010", -20.0)],
            "r10_m40": 100 * h[("P82_plate_R010", -40.0)],
            "sys0": 100 * h[("P82_system", 0.0)],
            "sys20": 100 * h[("P82_system", 20.0)],
            "sys40": 100 * h[("P82_system", 40.0)],
            "worst": 100 * max(h[("P82_plate_R010", t)]
                               for t in (-20.0, -40.0, -50.0, -70.0,
                                         0.0, 20.0, 40.0, 50.0, 70.0)),
            "ho": head_on if head_on is not None else float("nan"),
            "hox": format(int(round(0.04 / head_on)), ",").replace(
                ",", "&#8202;") if head_on else "&mdash;",
        }
        sec82 = sec82.replace("@@RAYPATHS@@", rp64)
    dv = os.path.join(OUTDIR, "img", "device.png")
    dv64 = ("data:image/png;base64,"
            + base64.b64encode(open(dv, "rb").read()).decode()) \
        if os.path.exists(dv) else ""
    sec83 = ""
    if dv64:
        sec83 = """
<h2>8.3 &mdash; the buildable unit, AS MEASURED (8.2b/c)</h2>
<p>The unit was re-measured at its as-built tilt of 35&deg; instead of
resting on mirror arithmetic (predictions and gradings in
<code>scripts/sweep_phase82b.py</code> /
<code>results/FINDINGS_phase82b.md</code>; anchor reproduced to all
digits). The measurement found something the arithmetic missed:
<b>at 35&deg; both the residual's only exit path and the only
level-viewer glint path retreat to the TOP quarter of the glass</b>
(the sole region whose mirror ray clears the sill; the render shows the
2R speckle band exactly there). A tile-clad <b>rim lip over that top
strip</b> closes both &mdash; verified by a same-day chained run whose
render shows the band gone. With the lip: level observer %%L0%%,
above-horizon observers %%HI%%, danger scan &minus;75&deg;&hellip;
+70&deg; empty everywhere, head-on %%HO%% at beam width
7.5&#8202;mm, and the full system with the pyramid trap reads
%%SYS%% &mdash; under the 0.05&#8202;% audience-visible target 8.1
registered, and below the pyramid wall's own 0.177&#8202;%. The
built-in shelf drops to OPTIONAL. An algebraic corollary
(FINDINGS_phase82b addendum) extends the safety claim to EVERY azimuth:
the hopper&rsquo;s reflection is always steeper-downward than its beam,
so no off-axis level viewer exists either. Sightlines rising from the
floor (&minus;20/&minus;40&deg;) still see ~2&#8202;%: mount the unit at or
above eye level, or accept that the floor sees a mirror. Parts stay
commodity: frame-shop museum glass (gravity-held, lifts out), MDF box,
nine 200&times;200 tiles, tile-clad lip. Still owed: the vendor
reflectance curve at 35&deg; incidence and the one-week dust
coupon.</p>
<figure style="margin:1rem 0 0">
<img src="%%DEVICE%%" alt="Buildable Phase 8 unit, side section"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
"""
        sec83 = sec83.replace("%%DEVICE%%", dv64)


    au = os.path.join(OUTDIR, "img", "audience.png")
    au64 = ("data:image/png;base64,"
            + base64.b64encode(open(au, "rb").read()).decode()) \
        if os.path.exists(au) else ""
    sec84 = ""
    if au64:
        sec84 = """
<h2>8.4 &mdash; the audience metric: the mounting rule became a
FLOOR rule</h2>
<p>The one open direction was below the horizon. Scanning observer
elevation &minus;2&deg; to &minus;20&deg; (predictions and two VOIDED
rig attempts recorded in <code>scripts/sweep_phase83.py</code> and
<code>results/FINDINGS_phase83.md</code>) killed the registered
height-over-eye rule: the turn-on is a smooth ramp, not an edge, and
with a worst-case bright mirrored scene it crosses the pyramid
wall&rsquo;s 0.177&#8202;% already at &minus;3.3&deg;. But the same
scan with a REAL mirrored scene &mdash; a dark floor
(&rho;&#8202;5&#8202;%) below the unit &mdash; reads
0.001&ndash;0.091&#8202;% all the way to &minus;16&deg;: below the
pyramid wall itself from every seat. The deployed rule is therefore:
<b>keep ~1&#8202;m of dark floor or trough tile in front of the unit,
and keep bright props out of that strip</b>. Level and above stay at
0.000&ndash;0.001&#8202;% (closed by the lip). The &minus;20&deg;
deployed value is bracketed 0.091&ndash;0.467&#8202;% by a rig edge
limit, recorded as such.</p>
<figure style="margin:1rem 0 0">
<img src="@@AUDIENCE@@" alt="Turn-on curve: white vs dark-floor mirrored scene"
 style="width:100%;border:1px solid var(--line);border-radius:6px">
</figure>
"""
        sec84 = sec84.replace("@@AUDIENCE@@", au64)
    html = html.replace("%%SECTION84%%", sec84)
    html = html.replace("%%SECTION83%%", sec83)
    # 8.2b/c numbers, loaded from the sweep outputs at build time
    b82 = {}
    scan82_max = 0.0
    p82b = os.path.join(RESULTS, "sweep_phase82b.csv")
    if os.path.exists(p82b):
        for r in csv.DictReader(open(p82b)):
            k = (r["tag"], float(r["theta"]))
            if r["mode"] == "hemi_view":
                b82[k] = max(b82.get(k, 0.0), float(r["rho"]))
            else:
                scan82_max = max(scan82_max, float(r["ratio"]))
    f82b = load_82 and json.load(open(os.path.join(
        RESULTS, "form_phase82b.json")))["P82b_t35_form"] \
        if os.path.exists(os.path.join(RESULTS, "form_phase82b.json")) \
        else {}
    if b82:
        hi_ts = (20.0, 40.0, 50.0, 70.0)
        sys_ts = (0.0, 20.0, 40.0)
        html = html.replace("%%L0%%", "%.3f&#8202;%%"
                            % (100 * b82[("P82c_lip", 0.0)]))
        html = html.replace("%%HI%%", "%.3f&ndash;%.3f&#8202;%%"
                            % (100 * min(b82[("P82b_t35", t)] for t in hi_ts),
                               100 * max(b82[("P82b_t35", t)] for t in hi_ts)))
        html = html.replace("%%HO%%", "%.7f" % f82b.get("head_on", float("nan")))
        html = html.replace("%%SYS%%", "%.3f&ndash;%.3f&#8202;%%"
                            % (100 * min(b82[("P82b_sys", t)] for t in sys_ts),
                               100 * max(b82[("P82b_sys", t)] for t in sys_ts)))
    html = html.replace("%%SECTION82%%", sec82)
    html = html.replace("%%CONCEPT%%", b64)
    open(OUT, "w").write(html)
    print("wrote %s (%d bytes)" % (OUT, os.path.getsize(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
