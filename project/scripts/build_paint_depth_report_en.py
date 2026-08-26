# -*- coding: utf-8 -*-
"""How far down does the black have to go -- English edition of the same report.

PAIRED WITH `build_paint_depth_report.py`. Same data, same numbers, same
sections; only the prose is English. The project already keeps its documents
this way (`SPEC_SUMMARY.md` / `SPEC_SUMMARY_EN.md`, `journey_ko.html` /
`journey_en.html`), and the alternative -- threading a language key through
five hundred lines of the Korean builder -- would have put the one report the
vendor discussion actually runs on at risk for no gain.

**Change one, change the other.** Both read the same JSON, so a corrected
material value reaches both by re-running them; what does NOT travel by itself
is a rewritten sentence.

reads
    results/paint_depth/paint_depth_9p53_40.json    the twelve paint depths
    results/comb_depth/comb_depth_pick.json         depth and cell size
    results/comb_depth/comb_foil.json               foil gauge
    figures/comb_headon_vs_oblique_en.svg           the ray drawing, English
    material/*.json                                 values and colours
    report/comb/comb_musou_2026-08-22.html          stylesheet, reused
writes
    report/comb/paint_depth_2026-08-24_en.html
"""
import os
import re
import io
import json
import glob
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "results/paint_depth/paint_depth_9p53_40.json")
DEPTHF = os.path.join(ROOT, "results/comb_depth/comb_depth_pick.json")
FOILF = os.path.join(ROOT, "results/comb_depth/comb_foil.json")
FIG = os.path.join(ROOT, "figures/comb_headon_vs_oblique_en.svg")
STYLE_FROM = os.path.join(ROOT, "report/comb/comb_musou_2026-08-22.html")
OUT = os.path.join(ROOT, "report/comb/paint_depth_2026-08-24_en.html")

rows = json.load(open(SRC))
by_d = {r["paint_depth"]: r for r in rows}
r0 = rows[0]
P, D, T = r0["pitch"], r0["depth"], r0["foil"]


def materials():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "material", "*.json"))):
        b = os.path.basename(f)[:-5]
        if b.startswith("_"):
            continue
        d = json.load(open(f))
        bsdf = d.get("bsdf", {}) or {}
        out[b] = {"color": d.get("color", "#3a3f47"),
                  "label": d.get("label_en") or d.get("label") or b,
                  "rho": (d.get("scattering", {}).get("reflectance", {})
                          .get("value")),
                  "df": bsdf.get("diffuse_fraction"),
                  "alpha": (bsdf.get("lobe", {}) or {}).get("alpha_ggx")}
    return out


MAT = materials()
RHO_BASE = (MAT.get(r0["base"], {}) or {}).get("rho")
RHO_TOP = (MAT.get(r0["top"], {}) or {}).get("rho")

# Closed form, worked on paper with no Blender in it. An expanded honeycomb
# doubles half of its walls at the bond lines, so the rim area is 3t/p.
F_RIM = 3.0 * T / P
F_OPEN = 1.0 - F_RIM
HALF0 = math.degrees(math.atan((P / 2.0) / D))
ESC0 = math.sin(math.radians(HALF0)) ** 2
D40 = (P / 2.0) / math.tan(math.radians(40.0))
HALF40 = math.degrees(math.atan((P / 2.0) / D40))
ESC40 = math.sin(math.radians(HALF40)) ** 2

t_none = by_d[0.0]["total"]["0"]
t_rim = by_d[1.0]["total"]["0"]
t_wall = by_d[20.0]["total"]["0"]
t_all = by_d[40.0]["total"]["0"]
span = t_none - t_all
PARTS = [("foil rim", t_none - t_rim, "the panel's own front face; spray reaches it"),
         ("cell wall, 1-20 mm", t_rim - t_wall, "painting it changes nothing head-on"),
         ("backing plate", t_wall - t_all, "a flat plate; paint it before bonding")]
FLASH_FLOOR = by_d[10.0]["head_on"] / by_d[40.0]["head_on"]

DR = json.load(open(DEPTHF))
FR = json.load(open(FOILF))
dby = {(r["pitch"], r["depth"], r["arm"]): r for r in DR}
fby = {(r["foil"], r["arm"]): r for r in FR}
DEPTHS = sorted({r["depth"] for r in DR})
FOILS = sorted({r["foil"] for r in FR})
PICK_D, PICK_F, NOW_F = 40.0, 0.04, 0.08


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


style = re.search(r"<style>(.*?)</style>",
                  io.open(STYLE_FROM, encoding="utf-8").read(), re.S).group(1)
fig = io.open(FIG, encoding="utf-8").read()
fig = re.sub(r'^<\?xml[^>]*\?>\s*', '', fig)
fig = fig.replace('width="1080" height="640"',
                  'width="100%" style="max-width:1080px;height:auto"', 1)

o = io.StringIO()
o.write('<!doctype html><html lang="en"><head><meta charset="utf-8">\n')
o.write('<meta name="viewport" content="width=device-width,initial-scale=1">\n')
o.write('<title>How far down does the black have to go</title>\n')
o.write('<style>%s\n.fig{background:#f4f1eb;border:1px solid var(--line);'
        'border-radius:3px;padding:10px;overflow-x:auto}\n'
        '.big{font-size:30px;font-weight:800;font-family:var(--mono);'
        'font-variant-numeric:tabular-nums}\n'
        '.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));'
        'gap:12px}\n.tag{font-family:var(--mono);font-size:11px;color:var(--muted);'
        'letter-spacing:.06em}\nul{margin:0;padding-left:20px;max-width:64ch}\n'
        'li{margin:4px 0}\na{color:var(--cy)}\n</style></head><body>\n'
        % style)
o.write('<div class="wrap">\n')

o.write('<header><div class="eyebrow">2026-08-24 &middot; coating depth</div>\n')
o.write('<h1>How far down does the black have to go</h1>\n')
o.write('<p class="sub">%.2f mm cell &middot; %.0f mm deep &middot; %.2f mm foil. '
        'The honeycomb a supplier said could not be painted black on the inside, '
        'and could not be anodised either. Both are true of their line. Neither '
        'turns out to matter much.</p>\n' % (P, D, T))
o.write('<p class="tag">Korean edition: <code>paint_depth_2026-08-24.html</code> '
        '&mdash; same data, same numbers.</p></header>\n')

# ---------------- verdict ----------------
o.write('<section><div class="card verdict ok">\n<h2 style="margin:0">Verdict</h2>\n')
o.write('<p class="lead"><b>The deep wall never needed painting.</b> For light '
        'arriving head-on, the <b>foil rim</b> and the <b>backing plate</b> '
        'decide almost all of it, and both are flat exposed faces. Only oblique '
        'light uses the wall, and it stops mattering 15 mm down.</p>\n')
o.write('<div class="grid3">\n')
for name, val, note in PARTS:
    # One decimal. The wall is 0.35 %, and rounding it to "0 %" would state
    # something we did not measure.
    o.write('<div><div class="tag">%s</div><div class="big">%.1f %%</div>'
            '<div style="font-size:13px;color:var(--muted)">%s</div></div>\n'
            % (esc(name), 100.0 * val / span, esc(note)))
o.write('</div>\n')
o.write('<p style="font-size:14px;color:var(--muted)">The three shares of the '
        'drop from %.3f %% to %.3f %% head-on.</p>\n' % (100 * t_none, 100 * t_all))
o.write('</div></section>\n')

# ---------------- why head-on is dark ----------------
o.write('<section><h2>A honeycomb cell is a trap that opens one way</h2>\n')
o.write('<p>The strangest number in the table is that <b>head-on is five times '
        'darker than oblique</b>. The reason is on the way out, not the way '
        'in.</p>\n')
o.write('<figure><div class="fig">%s</div>\n' % fig)
o.write('<figcaption class="tag">Angles are drawn true. The foil is %.2f mm; '
        'it is drawn thick to be visible. Built by '
        '<code>scripts/build_ray_figure.py</code>, which emits both '
        'languages.</figcaption></figure>\n' % T)
o.write('<p>Light arriving straight down never touches a wall and reaches the '
        'floor. Getting out is the problem. From the bottom of a %.0f mm well '
        'the exit subtends a half-angle of only %.1f degrees, and of the light '
        'scattered there just <b>%.1f %%</b> leaves in one go. The rest hits a '
        'wall, and loses most of itself each time.</p>\n'
        % (D, HALF0, 100 * ESC0))
o.write('<p>Oblique light at 40 degrees meets a wall <b>%.1f mm</b> down. It '
        'never reaches the floor. From that shallow point the exit is open to '
        '%.0f degrees and <b>%.0f %%</b> simply leaves &mdash; %.0f times the '
        'head-on share.</p>\n' % (D40, HALF40, 100 * ESC40, ESC40 / ESC0))
o.write('</section>\n')

# ---------------- closed form ----------------
o.write('<section><h3>Worked on paper as well, with no renderer in it</h3>\n')
o.write('<p>Head-on return = foil rim (%.2f %% of the area) + what escapes from '
        'the floor.</p>\n' % (100 * F_RIM))
o.write('<div class="scroll"><table><thead><tr><th>coating inside the cell</th>'
        '<th>rim</th><th>floor escape</th><th>closed form</th><th>render</th>'
        '<th>difference</th></tr></thead><tbody>\n')
for label, rho, meas in (("matte black, 5 %", RHO_BASE, t_none),
                         ("Musou, 1 %", RHO_TOP, t_all)):
    a, b = F_RIM * rho, F_OPEN * rho * ESC0
    s = a + b
    o.write('<tr><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.1f %%</td></tr>\n'
            % (label, 100 * a, 100 * b, 100 * s, 100 * meas,
               100 * abs(meas - s) / meas))
o.write('</tbody></table></div>\n')
o.write('<p>Within 2 % and 6 %. That is the render checking out, and it is also '
        'what turns the paragraph above from a story into a calculation.</p>'
        '</section>\n')

# ---------------- the twelve depths ----------------
o.write('<section><h2>Good black, N mm down from the tip</h2>\n')
o.write('<p>The base is 5 % matte black throughout. Musou (1 %) is laid over it '
        'from the tip down to N mm. All three axes are given &mdash; reporting '
        'one hides what the other two are doing.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>N mm</th>'
        '<th>total, head-on</th><th>total, 20&deg;</th><th>total, 40&deg;</th>'
        '<th>smear</th><th>head-on flash</th></tr></thead><tbody>\n')
for r in rows:
    d = r["paint_depth"]
    pick = ' class="pick"' if d == 15.0 else ""
    o.write('<tr%s><td>%.0f</td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td class="n">%s</td><td class="n">%s</td></tr>\n'
            % (pick, d, 100 * r["total"]["0"], 100 * r["total"]["20"],
               100 * r["total"]["40"],
               ("%.4f" % r["smear"]) if r["smear"] is not None else "&middot;",
               ("%.4f" % r["head_on"]) if r["head_on"] is not None else "&middot;"))
o.write('</tbody></table></div>\n')
o.write('<p class="tag">The green row is where the 40&deg; total stops moving. '
        'N = %.0f is the whole panel in Musou, backing plate included.</p>\n' % D)
o.write('<ul>\n')
o.write('<li><b>Head-on total</b> falls to %.5f %% at 1 mm and is still %.5f %% '
        'at 20 mm. It does not move.</li>\n' % (100 * t_rim, 100 * t_wall))
o.write('<li><b>The 40&deg; total</b> reads %.5f %% at 15 mm, %.5f %% at 20 mm, '
        '%.5f %% at 40 mm. <b>It is finished at 15 mm</b>, which is where '
        'pitch/tan(40&deg;) = 11.4 mm says it should be.</li>\n'
        % (100 * by_d[15.0]["total"]["40"], 100 * by_d[20.0]["total"]["40"],
           100 * by_d[40.0]["total"]["40"]))
o.write('<li><b>Smear</b> stays between %.4f and %.4f. Paint depth does not '
        'touch it; smear is set by shape.</li>\n'
        % (min(r["smear"] for r in rows if r["smear"]),
           max(r["smear"] for r in rows if r["smear"])))
o.write('<li><b>Head-on flash</b> drops to %.4f by 2 mm, holds there through '
        '10 mm, and then falls to <b>%.4f</b> once the backing plate is Musou '
        'too &mdash; a factor of %.1f.</li>\n'
        % (by_d[2.0]["head_on"], by_d[40.0]["head_on"], FLASH_FLOOR))
o.write('</ul>\n')
o.write('<p>That last drop is not gloss. The two coatings have the same diffuse '
        'fraction (%.3f against %.2f) and the same roughness. It is Musou being '
        'five times darker, showing through.</p>\n'
        % (MAT[r0["top"]]["df"], MAT[r0["base"]]["df"]))
o.write('</section>\n')

# ---------------- depth, cell, foil ----------------
o.write('<section><h2>So what depth</h2>\n')
o.write('<p>Cell 9.53 mm, depth varied. <b>A</b> is a backing plate we could not '
        'paint (Musou only 15 mm from the tip); <b>B</b> is a backing plate we '
        'could.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>depth</th>'
        '<th>head-on A</th><th>head-on B</th><th>20&deg; B</th><th>40&deg; B</th>'
        '<th>smear B</th><th>flash B</th></tr></thead><tbody>\n')
for d in DEPTHS:
    a, b = dby[(9.53, d, "A")], dby[(9.53, d, "B")]
    pick = ' class="pick"' if d == PICK_D else ""
    o.write('<tr%s><td>%.0f mm</td><td class="n">%.5f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%s</td>'
            '<td class="n">%.4f</td></tr>\n'
            % (pick, d, 100 * a["total"]["0"], 100 * b["total"]["0"],
               100 * b["total"]["20"], 100 * b["total"]["40"],
               ("%.4f" % b["smear"]) if b["smear"] is not None else "&middot;",
               b["head_on"]))
o.write('</tbody></table></div>\n')
d20, d40, d60 = (dby[(9.53, x, "B")] for x in (20.0, 40.0, 60.0))
gain = (100 * (d20["total"]["0"] - d40["total"]["0"])
        / (d20["total"]["0"] - d60["total"]["0"]))
o.write('<ul>\n')
o.write('<li><b>The 40&deg; total does not care about depth</b>: %.5f %% at '
        '20 mm, %.5f %% at 60 mm. And it is five times the head-on number, so '
        'depth is not what makes the panel dark.</li>\n'
        % (100 * d20["total"]["40"], 100 * d60["total"]["40"]))
o.write('<li><b>Only head-on buys anything from depth</b>, and <b>%.0f %% of '
        'what 60 mm gives is already there at 40 mm.</b> Past that the panel '
        'only gets thicker.</li>\n' % gain)
o.write('<li><b>Flash is untouched</b> &mdash; %.4f at every depth.</li>\n'
        % d40["head_on"])
o.write('<li><b>Smear is untouched too</b>, %.4f to %.4f with no ordering. '
        'That is measurement scatter, not a trend.</li>\n'
        % (min(dby[(9.53, d, "B")]["smear"] for d in DEPTHS
               if dby[(9.53, d, "B")]["smear"]),
           max(dby[(9.53, d, "B")]["smear"] for d in DEPTHS
               if dby[(9.53, d, "B")]["smear"])))
o.write('</ul>\n')

o.write('<h3>Cell size &mdash; the ranking inverts</h3>\n')
o.write('<p>Once the backing is painted, what is left is mostly the foil rim, '
        'and the rim area is <span style="font-family:var(--mono)">3 &times; '
        'foil &divide; pitch</span> &mdash; smaller for a larger cell. So the '
        'answer before and after painting the backing is not the same.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>at 40 mm deep</th>'
        '<th>6.35 mm cell</th><th>9.53 mm cell</th><th>winner</th>'
        '</tr></thead><tbody>\n')
for arm, name in (("A", "backing unpainted &mdash; head-on"),
                  ("B", "backing painted &mdash; head-on")):
    x, y = dby[(6.35, 40.0, arm)], dby[(9.53, 40.0, arm)]
    win = "6.35" if x["total"]["0"] < y["total"]["0"] else "9.53"
    o.write('<tr><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td><b>%s</b></td></tr>\n'
            % (name, 100 * x["total"]["0"], 100 * y["total"]["0"], win))
for k, name in (("40", "backing painted &mdash; 40&deg;"),
                ("20", "backing painted &mdash; 20&deg;")):
    x, y = dby[(6.35, 40.0, "B")], dby[(9.53, 40.0, "B")]
    win = "6.35" if x["total"][k] < y["total"][k] else "9.53"
    o.write('<tr><td>%s</td><td class="n">%.5f %%</td><td class="n">%.5f %%</td>'
            '<td><b>%s</b></td></tr>\n'
            % (name, 100 * x["total"][k], 100 * y["total"][k], win))
o.write('</tbody></table></div>\n')
o.write('<p>With the backing painted, <b>9.53 wins at all three angles.</b> '
        '6.35 led in the 32-case study because the base there was 5 % '
        'paint.</p>\n')

o.write('<h3>Foil gauge is a bigger lever than depth</h3>\n')
o.write('<p>The rim is what is left, so thinning the foil beats deepening the '
        'panel. Cell 9.53, depth 40, backing painted.</p>\n')
o.write('<div class="scroll"><table><thead><tr><th>foil</th><th>rim area</th>'
        '<th>head-on</th><th>20&deg;</th><th>40&deg;</th><th>flash</th>'
        '</tr></thead><tbody>\n')
for f in FOILS:
    r = fby[(f, "B")]
    pick = ' class="pick"' if f == PICK_F else ""
    o.write('<tr%s><td>%.2f mm</td><td class="n">%.2f %%</td>'
            '<td class="n"><b>%.5f %%</b></td><td class="n">%.5f %%</td>'
            '<td class="n">%.5f %%</td><td class="n">%.4f</td></tr>\n'
            % (pick, f, 100 * r["rim_fraction"], 100 * r["total"]["0"],
               100 * r["total"]["20"], 100 * r["total"]["40"], r["head_on"]))
o.write('</tbody></table></div>\n')
fa, fb = fby[(NOW_F, "B")], fby[(PICK_F, "B")]


def times(x):
    # Below 1 is worse, not better. Left in the same colour it reads as
    # "0.96x improvement", which is how it was first read.
    return ('<td class="n%s">%.2f&times;%s</td>'
            % ("" if x >= 1.0 else " bad", x, "" if x >= 1.0 else " (worse)"))


o.write('<div class="scroll"><table><thead><tr><th>on the same panel</th>'
        '<th>head-on</th><th>20&deg;</th><th>40&deg;</th><th>thickness</th>'
        '</tr></thead><tbody>\n')
o.write('<tr><td>depth 40 &rarr; 60 (foil 0.08)</td>%s%s%s'
        '<td class="n bad">1.5&times; thicker</td></tr>\n'
        % (times(d40["total"]["0"] / d60["total"]["0"]),
           times(d40["total"]["20"] / d60["total"]["20"]),
           times(d40["total"]["40"] / d60["total"]["40"])))
o.write('<tr class="pick"><td>foil 0.08 &rarr; 0.04 (depth 40)</td>%s%s%s'
        '<td class="n">unchanged</td></tr>\n'
        % (times(fa["total"]["0"] / fb["total"]["0"]),
           times(fa["total"]["20"] / fb["total"]["20"]),
           times(fa["total"]["40"] / fb["total"]["40"])))
o.write('</tbody></table></div>\n')
o.write('<p>Going 1.5 times deeper makes 40&deg; slightly worse. Halving the '
        'foil improves all three angles and leaves the panel the same '
        'thickness.</p>\n')
o.write('<p>Thin foil is not a special order. Hexcel grades its core as '
        '"cell size &ndash; alloy &ndash; foil gauge", and <b>3/8-5052-.001</b> '
        'is a catalogue part: 3/8 inch (9.53 mm) cell, 0.001 inch (0.0254 mm) '
        'foil. The 0.08 mm we had been assuming is on the heavy side for this '
        'cell.</p>\n')
o.write('<p class="tag">[verified] <a href="https://www.hexcel.com/wp-content/'
        'uploads/2025/12/HexWeb_CRIII_DataSheet.pdf">HexWeb CR III datasheet</a>'
        ', read directly &middot; local copy in '
        '<code>reference/datasheets/</code></p>\n')

pick = fby[(PICK_F, "B")]
now = fby[(NOW_F, "B")]
o.write('<div class="card verdict ok"><h3 style="margin:0">Recommendation</h3>\n')
o.write('<p class="lead"><b>9.53 mm</b> cell &middot; <b>40 mm</b> deep &middot; '
        '<b>0.03&ndash;0.04 mm</b> foil &middot; '
        '<b>paint the backing plate separately and bond the core onto it</b></p>\n')
o.write('<div class="scroll"><table><thead><tr><th>three axes</th>'
        '<th>as quoted (foil 0.08)</th><th>recommended (foil 0.04)</th>'
        '</tr></thead><tbody>\n')


def ax(r):
    return (100 * r["total"]["0"], 100 * r["total"]["20"],
            100 * r["total"]["40"], r["smear"], r["head_on"])


for nm, i, fmt in (("total reflectance, head-on", 0, "%.5f %%"),
                   ("total reflectance, 20&deg;", 1, "%.5f %%"),
                   ("total reflectance, 40&deg;", 2, "%.5f %%"),
                   ("smear", 3, "%.4f"),
                   ("head-on flash", 4, "%.4f")):
    a, b = ax(now)[i], ax(pick)[i]
    o.write('<tr><td>%s</td><td class="n">%s</td><td class="n"><b>%s</b></td>'
            '</tr>\n' % (nm, fmt % a if a is not None else "&middot;",
                         fmt % b if b is not None else "&middot;"))
o.write('</tbody></table></div>\n')
o.write('<p><b>There is one axis a tube cannot buy.</b> The smear target is '
        '1.42 and a honeycomb sits near 0.96 at every depth, cell size and foil '
        'gauge. A flat plate is 1.0 by definition, so <b>the honeycomb does not '
        'blur the shape at all.</b> If that axis matters, a tube is not the '
        'answer.</p>\n')
o.write('</div></section>\n')

# ---------------- how to make it ----------------
o.write('<section><h2>How it can be made</h2>\n')
WAYS = [
    ("Paint the backing plate separately and bond afterwards",
     "Half the head-on return and a factor of six on flash live on that plate, "
     "and it is flat. Paint it before the core goes on and the depth problem "
     "never arises.", None),
    ("Spray only 15 mm from the top",
     "40 mm does not have to be coated. The aspect ratio to reach is 1.6 to 1, "
     "not 4.2 to 1. That sprays.", None),
    ("Dip it",
     "An automotive catalyst substrate is a 1 mm channel 100 mm long &mdash; "
     "100 to 1 &mdash; and it is dip-coated to a uniform 30 &micro;m with no "
     "cracking at the corners. Ours is 4.2 to 1, twenty-four times easier. If "
     "pooling is the worry, dip-spin throws the excess off centrifugally.",
     [("cordierite honeycomb dip coating",
       "https://www.sciencedirect.com/science/article/abs/pii/S0272884216308343"),
      ("Chem-Plate dip-spin",
       "https://www.chemplateindustries.com/dip-spin")]),
    ("Electrocoat (ED, e-coat)",
     "Dipping with a field behind it. As the outside coats it insulates, and "
     "the current moves to whatever is still bare, so blind holes and internal "
     "cavities come out even. The Faraday cage that stops powder coating does "
     "not apply. 25&ndash;50 &micro;m. <b>But the finish comes out smooth</b>, "
     "and smooth means gloss, and gloss raises the flash. Any face that shows "
     "has to be finished matte separately.",
     [("Valence: e-coat vs powder coat",
       "https://www.valencesurfacetech.com/the-news/e-coat-vs-powder-coat/")]),
    ("Coat the foil before expanding it",
     "Honeycomb is made by printing adhesive lines on flat foil, stacking and "
     "pressing it into a block, slicing, and expanding. Treating the surface "
     "before the block is standard. Done this way there is no depth at all.",
     [("Corex honeycomb manufacturing",
       "https://corex-honeycomb.com/products-and-services/aluminium-honeycomb-manufacturing/")]),
    ("A slotted grid instead of a honeycomb",
     "Notched strips pushed together. Every blade is flat before assembly, so "
     "paint it flat and then build. Depth is just blade height. The cells come "
     "out square, so our measurements would have to be repeated.",
     [("Edee eggcrate louvers", "https://www.edee.com/fbseries.htm")]),
]
for i, (title, body, links) in enumerate(WAYS, 1):
    o.write('<div class="card"><h3 style="margin:0">%d. %s</h3>\n<p>%s</p>\n'
            % (i, esc(title), body))
    if links:
        o.write('<p class="tag">[verified] %s</p>\n'
                % " &middot; ".join('<a href="%s">%s</a>' % (u, esc(t))
                                    for t, u in links))
    o.write('</div>\n')
o.write('</section>\n')

# ---------------- anodising ----------------
o.write('<section><h2>Losing anodising costs nothing</h2>\n')
o.write('<div class="scroll"><table><thead><tr><th>material</th>'
        '<th>reflectance</th><th>diffuse fraction</th></tr></thead><tbody>\n')
for k in (r0["top"], "anodised", r0["base"]):
    m = MAT.get(k)
    if not m:
        continue
    o.write('<tr><td><span style="display:inline-block;width:10px;height:10px;'
            'background:%s;border:1px solid var(--line);margin-right:6px"></span>'
            '%s</td><td class="n">%.3f %%</td><td class="n">%.4f</td></tr>\n'
            % (m["color"], esc(m["label"]), 100 * m["rho"], m["df"]))
o.write('</tbody></table></div>\n')
o.write('<p><b>Black anodised aluminium and ordinary matte black paint are the '
        'same to within half a percentage point.</b> Anodising was never the '
        'good answer.</p>\n')
o.write('<p>And the supplier is right on the physics. Black anodising runs '
        '10&ndash;25 &micro;m and about half of it grows inward, eating the '
        'metal. On %.0f &micro;m foil, 25 &micro;m a side leaves %.0f &micro;m '
        'of metal and the rest is brittle oxide. The fold lines would not '
        'survive expansion.</p>\n' % (1000 * T, 1000 * T - 25))
o.write('<p class="tag">[verified] <a href="https://www.xometry.com/resources/'
        'machining/black-anodizing/">Xometry, black anodising thickness</a></p>\n')
o.write('</section>\n')

# ---------------- questions for the supplier ----------------
o.write('<section><h2>Questions for the supplier</h2><div class="card"><ul>\n')
for q in ("Can you supply the backing plate separately? We will paint it and "
          "bond the core on afterwards.",
          "We need black only 15 mm down from the top, not through the full "
          "40 mm.",
          "Do you have a partner who dips or electrocoats?",
          "Can the foil be coated black before it is expanded?",
          "Does 0.04 mm foil stand up at 40 mm depth? Hexcel lists "
          "3/8-5052-.001 at 0.0254 mm as a catalogue part, but we have not "
          "confirmed it at this depth.",
          "Anodising is not needed. Matte black paint is equivalent, provided "
          "the gloss is low."):
    o.write('<li>%s</li>\n' % esc(q))
o.write('</ul></div></section>\n')

# ---------------- not measured ----------------
o.write('<section><h2>Not measured</h2><ul>\n')
for x in ("The case where <b>nothing</b> reaches the inside. Bare aluminium is "
          "not in our material table, and we do not publish numbers for "
          "materials we have not sourced a value for.",
          "The three axes for a square grid. Our measurements are hexagonal.",
          "The actual roughness of an electrocoated surface. \"Smooth\" is the "
          "supplier's word, not our measurement.",
          "Smear and flash were run at 6 phases rather than 16, so they are "
          "estimates of the published statistic rather than the statistic. "
          "Flash was measured by the same method as the 32-case study "
          "(ten-cell patch, head-on, 7.5 mm beam) and returned the same values, "
          "2.635 and 2.599."):
    o.write('<li>%s</li>\n' % x)
o.write('</ul></section>\n')

o.write('<section><p class="tag">measured: %s &middot; %d points &middot; '
        '%d samples &middot; roughness slider %.4f (alpha %.3f) &middot; '
        'brightest of the 0/45/90&deg; planes. Built by '
        '<code>scripts/sweep_paint_depth.py</code>, '
        '<code>scripts/sweep_paint_depth_flash.py</code>. This document: '
        '<code>scripts/build_paint_depth_report_en.py</code>, paired with '
        '<code>build_paint_depth_report.py</code>.</p></section>\n'
        % (os.path.basename(SRC), len(rows), r0["samples"], r0["slider"],
           r0["alpha"]))
o.write('</div></body></html>\n')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
io.open(OUT, "w", encoding="utf-8").write(o.getvalue())
print("%s  (%d bytes)" % (OUT, len(o.getvalue())))
