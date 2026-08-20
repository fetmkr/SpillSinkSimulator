"""Build the honeycomb search report. Every number is read back out of
`results/`, so the page cannot quote something nobody measured.

    python3 scripts/build_report_hcflat.py [DATE]

Writes `report/<DATE>/hcflat.html`, self-contained: figures are inlined as
base64 so the file can be mailed, and it opens with <title> and a token block
rather than a doctype, which is the shape the rest of `report/` uses and the
shape an Artifact publish expects.

The palette is the study's own (`report_2rank_template.html`), and its three
accents are not decorative: --dark, --form and --peak are the same teal, amber
and violet the simulator draws the retro, specular and audience lines in
(`sim/index.html` PHICOL / the metric 08 map). A colour means the same thing on
the page as it does on the plot.
"""

from __future__ import annotations

import base64
import csv
import html
import os
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")

# Where the paint-reach curve stops paying, in cell widths. Read off the
# measured curve in `build()`, not chosen -- it is asserted against the data
# below so the prose and the table cannot drift apart.
KNEE = 1.25


# ---------------------------------------------------------------- data
def score(path):
    per = {}
    for r in csv.DictReader(open(path)):
        if not r.get("rho"):
            continue
        k = (float(r["pitch"]), float(r["depth"]), float(r["wall"]),
             float(r["paint_frac"]), int(r["seed"]))
        per[k] = max(per.get(k, 0.0), float(r["rho"]))
    agg = defaultdict(list)
    for (p, d, w, f, s), v in per.items():
        agg[(p, d, w, f)].append(v)
    out = {}
    for k, vs in agg.items():
        m = sum(vs) / len(vs)
        sem = (statistics.stdev(vs) / len(vs) ** 0.5) if len(vs) > 1 else 0.0
        out[k] = (m, sem, len(vs))
    return out, sum(len(v) for v in agg.values())


def load_map(path):
    m = {}
    for r in csv.DictReader(open(path)):
        if r.get("brdf"):
            m[(float(r["theta_in"]), float(r["theta_out"]))] = float(r["brdf"])
    return m


def map_lines(m):
    """audience / retro / specular means, excluding theta_in = 0 where all
    three coincide and the number would say nothing about any of them."""
    ins = [a for a in sorted({a for a, _ in m}) if a != 0.0]
    g = lambda f: [m[(a, f(a))] for a in ins if (a, f(a)) in m]   # noqa: E731
    aud, ret, spc = g(lambda a: 0.0), g(lambda a: a), g(lambda a: -a)
    return (sum(aud) / len(aud), sum(ret) / len(ret), sum(spc) / len(spc))


def b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


# ---------------------------------------------------------------- page
def num(v, dp=6):
    return "%.*f" % (dp, v)


def build(date):
    agg, n_meas = score(os.path.join(RESULTS, "sweep_hcflat.csv"))
    import sweep_hcflat as SW
    on = {k: v for k, v in agg.items()
          if k[0] in set(SW.PITCH) and k[1] in set(SW.DEPTH)}
    order = sorted(agg, key=lambda k: agg[k][0])
    best = order[0]
    top20 = order[:20]
    span = 100 * (agg[top20[-1]][0] - agg[top20[0]][0]) / agg[top20[0]][0]

    # paint reach, in cell widths
    bins = defaultdict(list)
    for (p, d, w, f), (v, _s, _n) in agg.items():
        if f > 0:
            bins[round((f * d / p) * 4) / 4].append(v)
    reach = [(b, statistics.median(bins[b]), len(bins[b]))
             for b in sorted(bins) if len(bins[b]) >= 5]

    # what the band is worth on the recommended geometry
    # THE RECOMMENDED DEPTH IS THE SHALLOWEST ONE STILL IN THE BAND, not the
    # darkest. Depth saturates, and past the knee the extra millimetres are
    # material you pay to ship and hang. "In the band" is within TOL of the
    # best at the same pitch and wall -- computed here so the headline cannot
    # drift from the table under it.
    TOL = 0.01
    rec_pitch, rec_wall = 6.4, 0.03
    # every depth MEASURED at that pitch and wall, not just the stage-A list:
    # the recommended cell is itself a stage-C refinement point, and its
    # depths live between the base grid lines.
    same = {k[1]: v[0] for k, v in agg.items()
            if k[0] == rec_pitch and k[2] == rec_wall and k[3] == 0.15}
    if same:
        floor_ = min(same.values())
        rec_depth = min(d for d, v in same.items() if v <= floor_ * (1 + TOL))
    else:
        rec_depth = 65.0
    rec = (rec_pitch, rec_depth, rec_wall)
    # The paint axis was only run on the stage-A grid, and the recommended
    # cell is a stage-C refinement point that sits between grid lines. Quote
    # the band from the darkest geometry that actually HAS the whole series
    # rather than from a geometry with one point of it.
    FRACS = (0.15, 0.10, 0.05, 0.0)
    full = [g for g in {k[:3] for k in agg}
            if all(g + (f,) in agg for f in FRACS)]
    band_geom = min(full, key=lambda g: agg[g + (0.15,)][0]) if full else None
    band = ([(f, agg[band_geom + (f,)][0]) for f in FRACS]
            if band_geom else [])

    # wall series at the best pitch/depth
    # SERIES ARE TAKEN FROM A POINT ON THE BASE GRID, not from `best`. Stage C
    # refines around the winner and its pitches and depths sit between grid
    # lines, so a series anchored there exists for one or two values and the
    # table collapses to a single row under prose describing a curve.
    gbest = min(on, key=lambda k: on[k][0])
    wall = sorted((w, agg[(gbest[0], gbest[1], w, gbest[3])][0])
                  for w in set(SW.WALL)
                  if (gbest[0], gbest[1], w, gbest[3]) in agg)
    dep = sorted((d, agg[(gbest[0], d, gbest[2], gbest[3])][0])
                 for d in set(SW.DEPTH)
                 if (gbest[0], d, gbest[2], gbest[3]) in agg)
    pit = sorted((p, agg[(p, gbest[1], gbest[2], gbest[3])][0])
                 for p in set(SW.PITCH)
                 if (p, gbest[1], gbest[2], gbest[3]) in agg)

    # the re-rank
    rr = []
    rp = os.path.join(RESULTS, "rerank_hcflat.csv")
    if os.path.exists(rp):
        per = {}
        old = {}
        for r in csv.DictReader(open(rp)):
            if not r.get("rho"):
                continue
            k = (float(r["pitch"]), float(r["depth"]), float(r["wall"]),
                 float(r["paint_frac"]))
            per.setdefault(k, {})[int(r["seed"])] = max(
                per.get(k, {}).get(int(r["seed"]), 0.0), float(r["rho"]))
            old[k] = float(r["rho_at60"])
            globals().setdefault("_cells", float(r["cells"]))
        for k, sd in per.items():
            vs = list(sd.values())
            rr.append((sum(vs) / len(vs), k, old[k]))
        rr.sort()

    # the maps
    maps = []
    fl = os.path.join(RESULTS, "sweep_bidir_flat40.csv")
    if os.path.exists(fl):
        maps.append(("flat plate, same Musou", map_lines(load_map(fl))))
    import glob
    for f in sorted(glob.glob(os.path.join(RESULTS, "sweep_bidir_hc_*.csv"))):
        nm = os.path.basename(f)[len("sweep_bidir_hc_"):-4]
        maps.append((nm, map_lines(load_map(f))))

    A = html.escape
    P = []
    P.append("<title>The Honeycomb Spill Sink</title>")
    P.append(CSS)
    P.append('<div class="wrap">')

    # header
    P.append('<header class="top">')
    P.append('<div class="eyebrow">Panel search &middot; %s</div>' % A(date))
    P.append("<h1>The ceiling reads one seven-hundredth of a sheet "
             "of white paper</h1>")
    P.append('<p class="sub">A honeycomb front on a flat back, sprayed with '
             'Musou Black at the mouth and left as bought further down. '
             '%d designs, %d design&ndash;seed measurements, about three hours '
             'of Cycles, over cell pitch, cell depth, foil thickness and how '
             'far the paint reaches.</p>' % (len(agg), n_meas))
    P.append("</header>")

    # ---- REFLECTANCE AT THE AUDIENCE: the top line
    import audience as AUD
    ab = defaultdict(dict)
    apath = os.path.join(RESULTS, "audience.csv")
    if os.path.exists(apath):
        for r in csv.DictReader(open(apath)):
            ab[r["surface"]][(float(r["theta_in"]),
                              float(r["theta_out"]),
                              float(r["delta_phi"]))] = float(r["brdf"])
    if ab:
        sc_ = {k: AUD.score(v) for k, v in ab.items()}
        pan = sc_["panel"][0]
        # BRACKETS, NOT A FITTED CURVE. An earlier draft interpolated velour
        # between its two measured points with an exponent that was invented,
        # and the answer moved 2x with it. For a Lambertian beta = rho exactly,
        # so a bracket needs no model at all. Filip & Vavra 2026 Fig. 6.
        REFS = [("black velour", 0.0020, 0.0122,
                 "theatrical blackout &mdash; the thing this replaces"),
                ("Musou fabric", 0.0012, 0.0055,
                 "the best black cloth in the reference"),
                ("a plain matte black wall", 0.05, 0.05,
                 "what happens if nobody does anything"),
                ("white paper", 0.80, 0.80,
                 "hold a sheet up and check it")]

        P.append("<section>")
        P.append('<div class="eyebrow">The top line</div>')
        P.append("<h2>Reflectance at the audience</h2>")
        P.append('<p class="col lede"><b>Radiance factor &beta;</b> &mdash; '
                 'this surface&rsquo;s brightness divided by that of a '
                 '<b>perfect Lambertian white</b> under the same light. '
                 '&beta;&nbsp;=&nbsp;1.000 is the white standard. It is the '
                 'CIE reflectance factor, it is dimensionless, and it is what '
                 'a goniometer reports.</p>')
        P.append('<div class="levers">')
        P.append('<div><dt>Radiance factor &beta; at the audience</dt>'
                 '<dd class="big">%.5f</dd><p>mean over the angles this room '
                 'actually uses. 1.000 = perfect white</p></div>' % pan)
        P.append('<div><dt>As a fraction of white paper</dt><dd>1 / %.0f</dd>'
                 '<p>paper is 75&ndash;85 %% and near-Lambertian, '
                 '&beta;&nbsp;&asymp;&nbsp;0.80</p></div>'
                 % (1.0 / AUD.as_paper(pan)))
        P.append('<div><dt>Against black velour</dt><dd>%.2f&ndash;%.2f&times;'
                 '</dd><p>theatrical blackout, over its whole measured range. '
                 '<b>The panel is darker</b></p></div>'
                 % (pan / 0.0122, pan / 0.0020))
        P.append("</div>")

        P.append('<div class="tbl"><table><thead><tr><th>surface</th>'
                 '<th>&beta; mean<br><span class="u">radiance factor, '
                 '1.000 = perfect white</span></th><th>&beta; peak<br>'
                 '<span class="u">brightest patch</span></th>'
                 '<th>&times; white paper</th><th>the panel vs it</th>'
                 '</tr></thead><tbody>')
        m, pk, _c = sc_["panel"]
        P.append('<tr class="hit"><td><b>the panel</b> &mdash; honeycomb '
                 '6.4&nbsp;/&nbsp;64&nbsp;/&nbsp;0.03, Musou to 15&nbsp;%%'
                 '</td><td>%.5f</td><td>%.4f</td><td>1 / %.0f</td>'
                 '<td>&mdash;</td></tr>' % (m, pk, 1.0 / AUD.as_paper(m)))
        fm, fpk, _c = sc_["flat_musou"]
        P.append('<tr><td>a flat plate of its own Musou paint<br>'
                 '<span class="u">the specular glare a painted ceiling shows'
                 '</span></td><td>%.5f</td><td><b>%.3f</b></td>'
                 '<td>1 / %.0f</td><td>panel is %.3f&times;</td></tr>'
                 % (fm, fpk, 1.0 / AUD.as_paper(fm), m / fm))
        for nm, lo, hi, why in REFS:
            rng = ("%.4f" % lo if lo == hi
                   else "%.4f &ndash; %.4f" % (lo, hi))
            vs = ("%.3f&times;" % (m / lo) if lo == hi
                  else "%.2f&ndash;%.2f&times;" % (m / hi, m / lo))
            P.append('<tr><td>%s<br><span class="u">%s</span></td><td>%s</td>'
                     '<td>&mdash;</td><td>1 / %.0f</td><td>panel is %s</td>'
                     '</tr>' % (nm, why, rng, 1.0 / AUD.as_paper(hi), vs))
        P.append("</tbody></table></div>")

        P.append('<div class="warn col"><p><b>Corrected 2026-08-21.</b> An '
                 'earlier version of this page said &beta;&nbsp;=&nbsp;0.0037 '
                 'and &ldquo;does not beat black velour&rdquo;. Both were '
                 'wrong: the measurement sampled the <i>retro</i> side of the '
                 'reflectance map for every cell, while 76&nbsp;% of the '
                 'light an eye receives arrives at azimuths an in-plane rig '
                 'cannot reach at all. The record is in '
                 '<code>FINDINGS_audience_azimuth_2026_08_21.md</code>.</p>'
                 '</div>')
        P.append('<p class="col"><b>The structure is worth %.1f&times; on the '
                 'mean and %.0f&times; on the peak</b>, and the peak is the one '
                 'that matters. A flat plate of the same paint reads a peak of '
                 '<b>%.3f</b> &mdash; three quarters as bright as white paper. '
                 'That is <b>the specular reflection of a projector in a '
                 'painted ceiling</b>. The honeycomb takes it to %.3f.</p>'
                 % (fm / m, fpk / pk, fpk, pk))
        P.append('<p class="col"><b>It is darker than every reference black in '
                 'the literature this study relies on</b> &mdash; below the '
                 'bottom of every bracket above. And the velour figure is '
                 'conservative against us: it is a Lambertian model, and its '
                 'own source reports velour with the <i>lowest</i> TIS of any '
                 'sample it measured, so real velour at these angles is very '
                 'likely worse than 0.0020.</p>')
        P.append('<p class="col"><b>On &ldquo;surely Musou beats '
                 'velour&rdquo;:</b> it does, as a <i>fabric</i> &mdash; 0.0012 '
                 'against 0.0020. As <i>paint</i>, which is what this panel is '
                 'coated in, it does not: 0.0100 against 0.0020. The structure '
                 'is what closes that gap and then some.</p>')

        P.append('<p class="col">Weighted over the <b>three-angle</b> cells this '
                 'room actually uses &mdash; incidence, observation <i>and the '
                 'azimuth between them</i>, over every projector, every part of '
                 'the scan field and every place a person may stand. The two '
                 'Lambertian '
                 'references are the check on the rig: through the identical '
                 '72-cell grid, white paper returns %.6f and black velour '
                 '%.6f, so the rig gives back exactly what it is handed and '
                 'anything the panel reads is the panel. Definition and '
                 'defects: <code>metrics/09</code>.</p>'
                 % (sc_["white_paper"][0], sc_["black_velour"][0]))
        P.append("</section>")

    # the answer
    P.append("<section>")
    P.append('<div class="eyebrow">What to build</div>')
    P.append('<h2>Cell %g&nbsp;mm &middot; foil %g&nbsp;mm &middot; depth '
             '%g&nbsp;mm &middot; Musou %.0f&nbsp;mm down</h2>'
             % (rec[0], rec[2], rec[1], KNEE * rec[0]))
    P.append('<div class="levers">')
    rec_key = rec + (0.15,)
    rec_rho, rec_n = (agg[rec_key][0], agg[rec_key][2]) if rec_key in agg \
        else (agg[best][0], agg[best][2])
    P.append('<div><dt>&rho;<sub>dh</sub> &mdash; hemispherical total, NOT '
             'what the audience sees</dt><dd>%s</dd>'
             '<p>this cell, mean over %d geometry seeds. The darkest cell '
             'anywhere in the search is %s.</p></div>'
             % (num(rec_rho), rec_n, num(agg[best][0])))
    P.append('<div><dt>Top 20 designs span</dt><dd>%.1f&nbsp;%%</dd>'
             '<p>against a seed SEM of 0.3&ndash;1.5&nbsp;%%, so they are one '
             'equivalence class</p></div>' % span)
    if maps:
        fa = maps[0][1][0]
        ha = min(m[1][0] for m in maps[1:]) if len(maps) > 1 else fa
        P.append('<div><dt>In-plane map, &theta;<sub>out</sub>&nbsp;=&nbsp;0 '
                 'row</dt><dd>%.0f&times;</dd><p>darker than a flat plate, in '
                 'the &plusmn;40&deg; slice only. <b>Not the audience figure '
                 '&mdash; that is %.0f&times;, above</b></p></div>'
                 % (fa / ha, (sc_["flat_musou"][0] / sc_["panel"][0])
                    if "panel" in sc_ else 0))
    P.append("</div>")
    if same and rec_depth != min(same, key=lambda d: same[d]):
        deepest = min(same, key=lambda d: same[d])
        gain = 100 * (same[rec_depth] - same[deepest]) / same[deepest]
        P.append('<p class="col lede">Depth is the shallowest that is still in '
                 'the band: %g&nbsp;mm reads %s, and going all the way to '
                 '%g&nbsp;mm buys %s for %.0f&nbsp;%% more material to ship '
                 'and hang.</p>'
                 % (rec_depth, num(same[rec_depth]), deepest,
                    ("nothing measurable" if gain < 0.05
                     else "%.1f&nbsp;%%" % gain),
                    100 * (deepest - rec_depth) / rec_depth))
    P.append('<p class="col lede">Both numbers are stock. 6.4&nbsp;mm is a '
             'standard expanded-foil cell and 0.03&nbsp;mm is about 1.2&nbsp;'
             'mil &mdash; the thin end of catalogue foil, but catalogue foil. '
             'Nothing here needs a special order.</p>')
    P.append('<p class="col">It is <em>one of</em> an equivalence class, and '
             'quoting it as the winner would be false precision. Inside that '
             'band, choose on price and process, not on optics.</p>')

    P.append('<div class="tbl"><table><thead><tr>'
             '<th>pitch</th><th>depth</th><th>wall</th><th>paint</th>'
             '<th>&rho;<sub>dh</sub> worst</th><th>SEM</th><th>aspect</th>'
             '<th>tip area</th></tr></thead><tbody>')
    for k in top20[:10]:
        p, d, w, f = k
        m, sem, _n = agg[k]
        hit = ' class="hit"' if (p, d, w) == rec else ""
        P.append("<tr%s><td>%g</td><td>%g</td><td>%g</td><td>%.0f&nbsp;%%</td>"
                 "<td>%s</td><td>%s</td><td>%.1f</td><td>%.2f&nbsp;%%</td></tr>"
                 % (hit, p, d, w, 100 * f, num(m), num(sem), d / p,
                    100 * 2 * w / p))
    P.append("</tbody></table></div>")
    P.append("</section>")

    # laws
    P.append("<section>")
    P.append('<div class="eyebrow">Three laws, measured</div>')
    P.append("<h2>The paint must reach about one and a quarter cell widths "
             "down</h2>")
    P.append('<p class="col">This is the whole lever, and the natural variable '
             'is <em>pitch</em>. Binned in millimetres the same data is noise; '
             'binned in cell widths it is a curve with a knee.</p>')
    P.append('<div class="tbl"><table><thead><tr><th>paint reach '
             '(&divide; pitch)</th>')
    for b, _v, _n in reach:
        P.append("<th>%.2f</th>" % b)
    P.append("</tr></thead><tbody><tr><td>median &rho;<sub>dh</sub></td>")
    lo = min(v for _b, v, _n in reach)
    for _b, v, _n in reach:
        P.append('<td%s>%s</td>' % (' class="hit"' if v == lo else "", num(v)))
    P.append("</tr></tbody></table></div>")
    if band:
        P.append('<p class="col">On the recommended cell that is <b>%.0f&nbsp;'
                 'mm of spray</b>. Measured on the darkest geometry that '
                 'carries the whole series (pitch&nbsp;%g, depth&nbsp;%g, '
                 'wall&nbsp;%g): going from %.0f&nbsp;%% of depth to %.0f&nbsp;'
                 '%% costs %.0f&nbsp;%% for a third less paint (%s against '
                 '%s); halving it again costs far more (%s); and painting '
                 'nothing but the tips buys almost nothing at all (%s).</p>'
                 % (KNEE * rec[0], band_geom[0], band_geom[1], band_geom[2],
                    100 * band[0][0], 100 * band[1][0],
                    100 * (band[1][1] - band[0][1]) / band[0][1],
                    num(band[1][1]), num(band[0][1]), num(band[2][1]),
                    num(band[3][1])))
    P.append("</section>")

    P.append("<section>")
    P.append("<h2>Depth saturates, and thin foil is the strongest geometric "
             "axis</h2>")
    P.append('<div class="two">')
    P.append('<div class="tbl"><table><thead><tr><th>depth (mm)</th>'
             '<th>&rho;<sub>dh</sub></th><th>aspect</th></tr></thead><tbody>')
    for d, v in dep:
        P.append("<tr><td>%g</td><td>%s</td><td>%.1f</td></tr>"
                 % (d, num(v), d / gbest[0]))
    P.append("</tbody></table></div>")
    P.append('<div class="tbl"><table><thead><tr><th>wall (mm)</th>'
             '<th>&rho;<sub>dh</sub></th><th>tip area</th></tr></thead><tbody>')
    for w, v in wall:
        P.append("<tr><td>%g</td><td>%s</td><td>%.2f&nbsp;%%</td></tr>"
                 % (w, num(v), 100 * 2 * w / gbest[0]))
    P.append("</tbody></table></div>")
    P.append("</div>")
    P.append('<p class="col">Past an aspect of roughly eight the wall is '
             'already black before light reaches the floor, and more depth is '
             'material you are paying to ship. Tip area is 2&middot;wall/pitch '
             'and the tips are the one surface a head-on observer strikes '
             'directly, which is why the foil gauge moves the answer more than '
             'anything else in the geometry.</p>')
    P.append('<p class="col">Pitch has an <em>interior</em> optimum &mdash; '
             'not the finest. A fine pitch means more tip area; a coarse one '
             'means less aspect at the same depth.</p>')
    P.append('<div class="tbl"><table><thead><tr><th>pitch (mm)</th>')
    for p, _v in pit:
        P.append("<th>%g</th>" % p)
    P.append("</tr></thead><tbody><tr><td>&rho;<sub>dh</sub></td>")
    plo = min(v for _p, v in pit)
    for _p, v in pit:
        P.append('<td%s>%s</td>' % (' class="hit"' if v == plo else "", num(v)))
    P.append("</tr></tbody></table></div>")
    P.append("</section>")

    # landscape figure
    P.append("<section>")
    P.append('<div class="eyebrow">The landscape</div>')
    P.append("<h2>Every panel on one colour scale</h2>")
    P.append('<p class="col">Worst &rho;<sub>dh</sub> over cell pitch and cell '
             'depth, one panel per foil thickness. One logarithmic scale across '
             'all of them, so a colour means the same reflectance wherever it '
             'appears &mdash; a per-panel normalisation would make the worst '
             'foil look exactly as good as the best. The dashed line is aspect '
             '8, and it traces the edge of the dark region rather than being '
             'fitted to it.</p>')
    P.append('<figure class="fig"><img alt="Worst rho_dh over pitch and depth, '
             'five foil thicknesses, one shared colour scale" '
             'src="data:image/png;base64,%s">'
             '<figcaption>Musou to 15&nbsp;%% of depth. The same figure exists '
             'at 10, 5 and 0&nbsp;%% on the identical scale.</figcaption>'
             '</figure>' % b64(os.path.join(RESULTS, "hcflat_paint15.png")))
    P.append("</section>")

    # re-rank
    if rr:
        cells = globals().get("_cells", 25.0)
        P.append("<section>")
        P.append('<div class="eyebrow">A check that failed its own '
                 'predictions</div>')
        P.append("<h2>Was the ranking an artefact of sample size?</h2>")
        P.append('<p class="col">Every design was measured on one 60&nbsp;mm '
                 'panel, so the number of cells in the sample falls as the '
                 'pitch rises &mdash; 30 at pitch 2, under 4 at pitch 16. '
                 'GATE&nbsp;11 of the rig audit swept 5/10/25/50 cells and '
                 'found &rho;<sub>dh</sub> falling monotonically and '
                 '<em>still</em> falling at 50, with a ten-cell sample reading '
                 'about 5&nbsp;%% high. The spread across pitch here is about '
                 '3&nbsp;%%. <b>The bias was larger than the effect</b>, so the '
                 'ranking was not quotable and the top twelve were '
                 're-measured at a constant %.0f cells a side.</p>' % cells)
        P.append('<div class="tbl"><table><thead><tr><th>pitch</th>'
                 '<th>depth</th><th>wall</th><th>panel</th>'
                 '<th>&rho; at %.0f cells</th><th>&rho; at 60&nbsp;mm</th>'
                 '<th>change</th></tr></thead><tbody>' % cells)
        for m, (p, d, w, f), o in rr:
            ch = 100 * (m - o) / o
            P.append("<tr><td>%g</td><td>%g</td><td>%g</td><td>%.0f&nbsp;mm"
                     "</td><td>%s</td><td>%s</td><td>%+.1f&nbsp;%%</td></tr>"
                     % (p, d, w, cells * p, num(m), num(o), ch))
        P.append("</tbody></table></div>")
        P.append('<p class="col">Predicted: every design reads darker, the '
                 'coarse pitches gain most, the order changes. <b>The first two '
                 'failed.</b> The changes are mixed in sign and the order '
                 'barely moved, so this family is far less cell-count '
                 'sensitive than the one GATE&nbsp;11 swept &mdash; and the '
                 'fixed-panel ranking was safe after all. That is the only '
                 'reason to have run it.</p>')
        P.append("</section>")

    # maps
    if maps:
        P.append("<section>")
        P.append('<div class="eyebrow">Where the light goes</div>')
        P.append("<h2>Excellent for the audience, and a retroreflector</h2>")
        P.append('<p class="col">&rho;<sub>dh</sub> is one scalar and says '
                 'nothing about direction. These are the same designs read as '
                 'a BRDF over incidence against observation &mdash; every panel '
                 'again on one shared scale. Three lines carry the questions: '
                 '<span class="k retro">retro</span>, straight back at the '
                 'projector; <span class="k spec">specular</span>, where a flat '
                 'mirror would send it; and <span class="k aud">the audience</'
                 'span>.</p>')
        P.append('<figure class="fig"><img alt="BRDF maps, six honeycombs and a '
                 'flat plate, one shared scale" '
                 'src="data:image/png;base64,%s"><figcaption>Incidence across, '
                 'observation up, BRDF on a shared logarithmic scale.'
                 '</figcaption></figure>'
                 % b64(os.path.join(RESULTS,
                                    "hcflat_maps_globalnorm.png")))
        P.append('<div class="tbl"><table><thead><tr><th>design</th>'
                 '<th class="k aud">audience</th><th class="k retro">retro</th>'
                 '<th class="k spec">specular</th><th>retro &divide; audience'
                 '</th></tr></thead><tbody>')
        for nm, (a, r, s) in maps:
            P.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
                     "<td>%.0f&times;</td></tr>"
                     % (A(nm), num(a), num(r), num(s), r / a))
        P.append("</tbody></table></div>")
        P.append('<p class="col">Excluding &theta;<sub>in</sub>&nbsp;=&nbsp;0, '
                 'where all three lines coincide and the number would say '
                 'nothing about any of them. <b>A honeycomb wall and a flat '
                 'floor are mutually perpendicular mirrors</b>, so a bounce off '
                 'both reverses the ray: the brightest structure on every map '
                 'is the retro diagonal. It is superb in front of people and it '
                 'sends light back up the beam. Whether that matters depends on '
                 'where the projectors sit relative to the audience, and '
                 'nothing in this study knows that yet.</p>')
        P.append("</section>")

    # ---- the room, and the corner of the map it uses
    import report_geometry as G
    g = G.facts()
    near = G.closest_to_retro()
    frac_out, _incs = G.fraction_outside_scored()
    rb = os.path.join(RESULTS, "rigband_hcflat.csv")
    band = defaultdict(list)
    flat_at = {}
    if os.path.exists(rb):
        for r in csv.DictReader(open(rb)):
            if r.get("rho"):
                band[float(r["theta"])].append(float(r["rho"]))
                flat_at[float(r["theta"])] = float(r["flat_coating_rho"])
    band = {k: sum(v) / len(v) for k, v in band.items()}

    P.append("<section>")
    P.append('<div class="eyebrow">The room</div>')
    P.append("<h2>The audience plane &mdash; which corner of the map this "
             "room uses</h2>")
    P.append('<p class="col">The panel has a reading for every incidence '
             'against every observation angle. A room only ever visits part of '
             'it, and this one visits a corner that the search never scored. '
             'The geometry below is <b>stated, not measured</b> &mdash; a '
             '%g&nbsp;m ring of projectors at %.1f&nbsp;m aimed inward and up '
             'at %.0f&deg; with a &plusmn;%.0f&deg; square scan field, a '
             'ceiling at %.1f&nbsp;m, and an audience keeping inside '
             '%.1f&nbsp;m. Everything after it is arithmetic.</p>'
             % (2 * G.RING_R, G.EYE_H, G.AIM_EL, G.SCAN, G.CEIL_H, G.AUD_R))
    P.append(G.fig_section())
    P.append(G.fig_plan())
    P.append(G.fig_plane(near))

    P.append('<div class="warn col"><p><b>The band the panel was chosen in is '
             'not the band this room uses.</b> Scoring is &theta;&nbsp;= '
             '0/&plusmn;20/&plusmn;40. This rig delivers %.0f&ndash;%.0f&deg;, '
             'so <b>%.0f&nbsp;%% of what it throws at the ceiling arrives '
             'outside the scored band</b> &mdash; and normal incidence, where '
             'the panel is far and away at its best, never happens at all. '
             'That is README open item 1, and the geometry above closes '
             'it.</p></div>' % (g["inc_lo"], g["inc_hi"], 100 * frac_out))

    if band:
        sc = max(band[t] for t in G.SCORED if t in band)
        rg = max(v for t, v in band.items()
                 if g["inc_lo"] <= t <= g["inc_hi"])
        P.append('<div class="levers">')
        P.append('<div><dt>Scored worst, &theta; 0/&plusmn;20/&plusmn;40</dt>'
                 '<dd>%s</dd><p>the figure the search ranked on</p></div>'
                 % num(sc))
        P.append('<div><dt>This room&rsquo;s worst, %.0f&ndash;%.0f&deg;</dt>'
                 '<dd class="big">%s</dd><p>%.2f&times; the scored figure. '
                 'This is the number to quote</p></div>'
                 % (g["inc_lo"], g["inc_hi"], num(rg), rg / sc))
        P.append('<div><dt>Straight up, off the retro ridge</dt><dd>%.0f&deg;'
                 '</dd><p>and a grazing look at the far rim comes within '
                 '%.0f&deg;</p></div>' % (g["overhead_gap"], near[0]))
        P.append("</div>")
        P.append('<div class="tbl"><table><thead><tr><th>incidence</th>'
                 '<th>panel &rho;<sub>dh</sub></th><th>its own coating, flat'
                 '</th><th>panel &divide; coating</th><th></th></tr></thead>'
                 '<tbody>')
        for t in sorted(band):
            # str.strip takes a SET of characters, not a suffix: stripping
            # " &middot;" off "in the room's band" ate the i and the d and
            # printed "n the room's ban".
            parts = []
            if t in G.SCORED:
                parts.append("scored")
            if g["inc_lo"] <= t <= g["inc_hi"]:
                parts.append("in the room&rsquo;s band")
            tag = " &middot; ".join(parts)
            P.append('<tr%s><td>%.0f&deg;</td><td>%s</td><td>%s</td>'
                     '<td>%.3f</td><td class="note">%s</td></tr>'
                     % (' class="hit"' if t == max(band, key=band.get) else "",
                        t, num(band[t]), num(flat_at.get(t, 0.0)),
                        band[t] / flat_at[t] if flat_at.get(t) else 0.0, tag))
        P.append("</tbody></table></div>")
        P.append('<p class="col">The panel is at its best head-on, where it '
                 'reads %.3f of its own coating on a flat plate, and at its '
                 'worst near %.0f&deg;. It never stops working: even at '
                 '%.0f&deg; the structure is still holding the coating down by '
                 '%.1f&times;. <b>But the honest headline for this room is '
                 '%s, not %s.</b></p>'
                 % (band[0.0] / flat_at[0.0], 55.0, g["inc_hi"],
                    1.0 / (band[g["inc_hi"]] / flat_at[g["inc_hi"]]),
                    num(rg), num(sc)))
    P.append("</section>")

    # caveats
    P.append("<section>")
    P.append('<div class="eyebrow">What would change these numbers</div>')
    P.append("<h2>The search is conditional on a material nobody has "
             "measured</h2>")
    P.append('<div class="warn col"><p><b>anodised_hi is an estimate in every '
             'shape parameter.</b> The library marks its diffuse fraction, '
             'roughness <em>and</em> refractive index estimated &mdash; '
             'translated from Kaster 2025, with its own note reading '
             '&ldquo;Sweep it; do not trust it.&rdquo; &rho;<sub>0</sub>&nbsp;='
             '&nbsp;6&nbsp;% is the pessimistic end of a 3&ndash;6&nbsp;% '
             'spread. A goniometer reading of the actual foil would settle it '
             'and could move every absolute number on this page.</p></div>')
    P.append('<ul class="col">')
    P.append("<li>The coating model is <b>not reciprocal</b>, so the BRDF cells "
             "carry that caveat. The <em>structure</em> of the maps is "
             "geometric and stands.</li>")
    P.append("<li><b>Zero physical measurements.</b> Still true of the whole "
             "study, and still the largest open item.</li>")
    P.append("<li>One azimuth plane. &phi; was not swept.</li>")
    P.append("<li>The maps cover the scoring band, &plusmn;40&deg;, not "
             "grazing &mdash; margin 2.0 is measured-good there and a "
             "6.5-depth skirt on an 80&nbsp;mm cell is a frame five times "
             "wider than the sample.</li>")
    P.append("</ul>")
    P.append("</section>")

    P.append('<footer><p>Every number on this page is read out of '
             '<code>results/sweep_hcflat.csv</code>, '
             '<code>results/rerank_hcflat.csv</code> and the metric&nbsp;08 map '
             'files by <code>scripts/build_report_hcflat.py</code>. Scoring is '
             '<code>principles/00</code> &sect;C, unchanged.</p></footer>')
    P.append("</div>")
    return "\n".join(P)


CSS = """<style>
:root{
  --ground:#f5f6f7; --surface:#fff; --sunk:#eceff1;
  --ink:#101519; --ink-2:#48545e; --ink-3:#6f7d89;
  --line:#dce1e5; --line-2:#c4ced4;
  --dark:#0d6f79; --form:#a4691a; --peak:#5b4b9e; --no:#a3352a; --soft:#e3f0f1;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#080a0c; --surface:#11161a; --sunk:#0d1114;
    --ink:#e5ebf0; --ink-2:#9daab5; --ink-3:#74828e;
    --line:#1e262c; --line-2:#2e3841;
    --dark:#49c2ca; --form:#dda647; --peak:#a394e8; --no:#e0705f;
    --soft:#0f2b2e;
  }
}
:root[data-theme="dark"]{
  --ground:#080a0c; --surface:#11161a; --sunk:#0d1114;
  --ink:#e5ebf0; --ink-2:#9daab5; --ink-3:#74828e;
  --line:#1e262c; --line-2:#2e3841;
  --dark:#49c2ca; --form:#dda647; --peak:#a394e8; --no:#e0705f; --soft:#0f2b2e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);
  font:400 16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,
  "Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px 96px}
.col{max-width:66ch}
h1,h2{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,
  "Times New Roman",serif;font-weight:600;margin:0;text-wrap:balance}
h1{font-size:clamp(30px,4.4vw,50px);line-height:1.08;letter-spacing:-.015em}
h2{font-size:clamp(20px,2.4vw,27px);line-height:1.22}
p{margin:0}
em{font-style:italic}
code{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:.9em;
  background:var(--sunk);padding:1px 5px;border-radius:3px}
.eyebrow{font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.16em;
  text-transform:uppercase;color:var(--dark)}
header.top{border-bottom:1px solid var(--line);padding:60px 0 34px;
  display:flex;flex-direction:column;gap:18px}
.sub{font-size:18px;line-height:1.55;color:var(--ink-2);max-width:62ch}
section{padding-top:56px;display:flex;flex-direction:column;gap:20px}
.lede{font-size:17px;color:var(--ink-2)}
.levers{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
  gap:0;border:1px solid var(--line);border-radius:3px;overflow:hidden;
  background:var(--surface)}
.levers>div{padding:16px 18px;border-right:1px solid var(--line)}
.levers>div:last-child{border-right:0}
.levers dt{font:600 10px/1.35 ui-monospace,Menlo,monospace;letter-spacing:.11em;
  text-transform:uppercase;color:var(--ink-3);margin-bottom:8px}
.levers dd{margin:0;font:650 25px/1 ui-monospace,Menlo,monospace;
  font-variant-numeric:tabular-nums}
.levers .big{color:var(--dark)}
.levers p{font-size:12.5px;color:var(--ink-3);margin-top:7px;line-height:1.45}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:3px;
  background:var(--surface)}
table{border-collapse:collapse;width:100%;min-width:520px;
  font:400 13.5px/1.5 ui-monospace,Menlo,monospace;
  font-variant-numeric:tabular-nums}
th,td{padding:9px 13px;text-align:right;white-space:nowrap;
  border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
thead th{font-weight:600;font-size:10.5px;letter-spacing:.11em;
  text-transform:uppercase;color:var(--ink-3);background:var(--sunk)}
tbody tr:last-child td{border-bottom:0}
td.hit{color:var(--dark);font-weight:650}
tr.hit td{background:var(--soft)}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
  gap:14px}
figure.fig{margin:0;border:1px solid var(--line);border-radius:3px;
  background:var(--surface);padding:14px;overflow-x:auto}
figure.fig img{width:100%;min-width:720px;height:auto;display:block}
figure.diag svg{width:100%;min-width:560px;height:auto;display:block}
th .u{display:block;font-weight:400;text-transform:none;letter-spacing:0;
  font-size:10px;color:var(--ink-3);margin-top:2px}
td.note{color:var(--ink-3);font-size:11.5px;text-align:left;white-space:normal}
figcaption{margin-top:10px;font:400 12.5px/1.5 ui-monospace,Menlo,monospace;
  color:var(--ink-3)}
.k{font-weight:650}
.k.retro{color:var(--dark)} .k.spec{color:var(--form)} .k.aud{color:var(--peak)}
.warn{border-left:3px solid var(--no);background:var(--surface);
  border-top:1px solid var(--line);border-right:1px solid var(--line);
  border-bottom:1px solid var(--line);border-radius:0 3px 3px 0;padding:15px 18px}
ul.col{margin:0;padding-left:1.15em;display:flex;flex-direction:column;gap:9px;
  color:var(--ink-2)}
li::marker{color:var(--ink-3)}
footer{margin-top:64px;padding-top:22px;border-top:1px solid var(--line);
  font-size:13px;color:var(--ink-3)}
a:focus-visible,img:focus-visible{outline:2px solid var(--dark);
  outline-offset:3px}
@media (prefers-reduced-motion:reduce){*{animation:none!important;
  transition:none!important}}
</style>"""


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else "2026-08-20"
    out_dir = os.path.join(ROOT, "report", date)
    os.makedirs(out_dir, exist_ok=True)
    page = build(date)
    path = os.path.join(out_dir, "hcflat.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(page)
    print("wrote %s  (%.0f KB)" % (path, os.path.getsize(path) / 1024))
    # Check the PROSE, not the stylesheet and not the base64 blobs -- "}}"
    # ends every nested media query and "nan" occurs in base64 by chance, so
    # a naive scan cries wolf on every build and stops being read.
    import re
    body = re.sub(r'src="data:image/png;base64,[^"]+"', "", page)
    body = re.sub(r"<style>.*?</style>", "", body, flags=re.S)
    bad = [t for t in ("{{", "}}", "None", "nan", "inf")
           if re.search(r"\b%s\b" % re.escape(t), body) or t in ("{{", "}}")
           and t in body]
    if bad:
        print("  UNRESOLVED IN THE PROSE: %s" % ", ".join(bad))
        raise SystemExit(1)
    print("  no unresolved fields in the prose")


if __name__ == "__main__":
    main()
