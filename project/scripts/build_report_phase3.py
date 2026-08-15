"""
Phase 3 report: single layers against stacked pairs, on all three axes.

    Blender --background --factory-startup --python scripts/build_report_phase3.py

Phase 2 asked which topology. Phase 3 asks whether two of them in series beat
one, and the answer is no on total reflectance and interesting everywhere else:
the top layer decides how much the shape is destroyed, the bottom layer decides
how bright the panel looks to someone standing in front, and splitting a fixed
50 mm envelope between two layers costs both of them the aspect ratio that made
a cavity dark in the first place.

The three single layers reuse the phase 2 gallery renders; the three stacks are
rendered here through the same `shot3d.shoot`, so all six cards share a camera,
a lens and a light rig. A stack shot under a different camera would look
different for a reason that has nothing to do with the geometry.

Every number is read from a sweep row at build time; none is typed in.
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
FLAT = 0.011413                     # flat plate of the same coating, measured

PHASE2 = os.path.join(ROOT, "report", "2026-08-13", "shots")

# The stack layer presets, copied from sweep_stack.py so the picture is the
# geometry that was measured. Depth and margin are the only overrides: 0.2
# margin frames the tile for a portrait, where the sweep runs 2.0 so a tilted
# camera never reads world background.
_COMB = dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0)
_COMB_FINE = dict(pitch=3.17, wall_top=0.04, wall_bot=0.04, jitter=0.0)
_CONE = dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=24,
             height_seg=12, depth_jitter=0.0, profile_power=1.0)
_BLADE = dict(pitch=5.5, plate_t_top=0.1, plate_t_bot=0.1, tilt_deg=2.0,
              tilt_jitter=0.0, azimuth_mode="grid", jitter=0.30)


def _stack(top, tp, bot, bp):
    return dict(face_w=60.0, face_h=60.0, margin_depths=0.2, backing=2.0,
                seed=23, top=top, top_depth=25.0, top_params=dict(tp),
                bot=bot, bot_depth=25.0, bot_params=dict(bp))


# key -> (label, kind, what it is, render source | params to render)
DESIGNS = [
    ("CB_p0520_f040_x10", "Honeycomb 5.2 / 0.04", "single",
     "Commercial expanded foil, identical cells, bought by the sheet.",
     os.path.join(PHASE2, "CB_p0520_f040_x10.png")),
    ("ST_comb-comb_50", "Honeycomb over finer honeycomb", "stack",
     "Two scales of the same bought product: 6.5 mm cells over 3.17 mm cells. "
     "The only design in the study that beats every single layer on total "
     "reflectance — and the reason phase 3's first headline was withdrawn.",
     _stack("comb", _COMB, "comb", _COMB_FINE)),
    ("BL_FLAT_t100_p0550_a02_grid", "Blade array", "single",
     "0.1 mm laser-cut blades slotted together like an egg crate.",
     os.path.join(PHASE2, "BL_FLAT_t100_p0550_a02_grid.png")),
    ("B_CONE_p0550", "Cone array", "single",
     "Moulded cones, 0.4 mm tip, irregular placement.",
     os.path.join(PHASE2, "B_CONE_p0550.png")),
    ("ST_shin-comb_50", "Blades over honeycomb", "stack",
     "Sheet-metal blades in the top 25 mm, bought honeycomb beneath.",
     _stack("shingle", _BLADE, "comb", _COMB)),
    ("ST_comb-cone_50", "Honeycomb over cones", "stack",
     "Bought honeycomb in the top 25 mm, cone field beneath. The picture is "
     "the first card again — the cells hide the cones completely — and yet it "
     "reads 12× darker head-on. That gap is this phase's whole finding.",
     _stack("comb", _COMB, "cone", _CONE)),
    ("ST_cone-comb_50", "Cones over honeycomb", "stack",
     "Cone field in the top 25 mm, bought honeycomb beneath.",
     _stack("cone", _CONE, "comb", _COMB)),
]


def worst_by_design(paths):
    out = {}
    for p in paths:
        fp = os.path.join(RESULTS, p)
        if not os.path.exists(fp):
            continue
        per = collections.defaultdict(dict)
        for r in csv.DictReader(open(fp)):
            per[(r["tag"], r["diffuse_frac"])][float(r["theta"])] = \
                float(r["rho"])
        sc = {}
        for (tag, mat), d in per.items():
            if len(d) == 5:
                sc.setdefault(tag, {})[mat] = max(d.values())
        by = collections.defaultdict(list)
        for tag, v in sc.items():
            if len(v) == 3:
                by[tag.rsplit("_s", 1)[0]].append(max(v.values()))
        for k, v in by.items():
            out[k] = (sum(v) / len(v), len(v))
    return out


def form_by_design():
    fp = os.path.join(RESULTS, "form_buildable.json")
    out = {}
    if not os.path.exists(fp):
        return out
    for e in json.load(open(fp)):
        if "thetas" not in e:
            continue
        t = e["thetas"]
        a, b = t.get("-40"), t.get("+40")
        z = t.get("+0", {})
        smear = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                        + b["rms_mm"] / b["rms_control_mm"])
                 if a and b else None)
        out[e["tag"].rsplit("_s", 1)[0]] = (smear, z.get("peak_ratio_mean"))
    return out


def flat_head_on():
    """The flat plate's head-on peak, at the SAME specular roughness (0.30)
    the sweeps ran at. `form_roughness.json` holds five roughnesses and the
    flat plate moves from 119.9 to 0.36 across them, so quoting the wrong row
    would move the baseline by 300x."""
    for e in json.load(open(os.path.join(RESULTS, "form_roughness.json"))):
        if e.get("what") == "flat" and abs(e.get("roughness", 0) - 0.30) < 1e-9:
            return e["thetas"]["+0"]["peak_vs_wall"]
    sys.exit("no flat-plate row at roughness 0.30 in form_roughness.json")


def shot_for(key, src, shots):
    """Absolute path to this design's picture, rendering it if it is a stack.

    A string src is a phase 2 render that already exists under the same camera;
    a dict src is a stack that has never been shot at this camera, so it is
    built here rather than borrowed from profiles/ at a different angle.
    """
    if isinstance(src, str):
        return src if os.path.exists(src) else None
    png = os.path.join(shots, "%s.png" % key)
    if os.path.exists(png):
        return png
    try:
        import shot3d
    except ImportError:
        return None                    # --html-only, outside Blender
    print("[SHOT] %s" % key, flush=True)
    shot3d.shoot(key, "stack", src, src["face_w"], png)
    return png if os.path.exists(png) else None


def webify(rdir, src):
    web = os.path.join(rdir, "web")
    os.makedirs(web, exist_ok=True)
    out = os.path.join(web, os.path.basename(src).replace(".png", ".jpg"))
    if not os.path.exists(out):
        subprocess.run(["sips", "-Z", "820", "-s", "format", "jpeg",
                        "-s", "formatOptions", "70", src, "--out", out],
                       capture_output=True)
    return out if os.path.exists(out) else None


def b64(p):
    return base64.b64encode(open(p, "rb").read()).decode("ascii")


def bar(value, lo, hi, invert=False, w=118, h=8):
    """A tiny bar so three axes can be compared by eye, not by squinting."""
    if value is None:
        return ""
    f = (math.log10(max(value, lo)) - math.log10(lo)) / \
        (math.log10(hi) - math.log10(lo))
    f = min(1.0, max(0.0, f))
    if invert:
        f = 1.0 - f
    return ('<span class="bar"><i style="width:%.1f%%"></i></span>'
            % (100 * f))


def main():
    date = os.environ.get("REPORT_DATE") or \
        datetime.datetime.now().strftime("%Y-%m-%d")
    rdir = os.path.join(ROOT, "report", date)
    shots = os.path.join(rdir, "shots")
    os.makedirs(shots, exist_ok=True)

    dark = worst_by_design(["sweep_stack.csv", "sweep_comb.csv",
                            "sweep_blade.csv", "sweep_buildable.csv"])
    form = form_by_design()

    missing = [k for k, *_ in DESIGNS if k not in dark or k not in form]
    if missing:
        sys.exit("no measurement for: %s -- refusing to build a report with a "
                 "row that has no data behind it" % ", ".join(missing))

    # buildability comes from the same table the rankings use, so a card can
    # never quietly show a design the process floor rejects -- the featured
    # 0.04 mm honeycomb is below the user's 0.05 mm handling floor and the card
    # has to say so on its face
    import analyze_buildable as AB
    build = {r["design"]: (AB.buildable(r["process"], r["feature"]),
                           r["process"], r["feature"])
             for r in AB.darkness()}

    css, cards = [], []
    for key, label, kind, blurb, src in DESIGNS:
        d, n = dark[key]
        sm, pk = form[key]
        (ok, why), proc, feat = build[key]
        flag = ("" if ok else
                '<p class="nb">Below the process floor — %s, %s</p>'
                % (html.escape(str(why)), html.escape("%s mm" % feat)))
        slug = key.lower().replace("_", "-")
        png = shot_for(key, src, shots)
        j = webify(rdir, png) if png else None
        if j:
            css.append(".i-%s{background-image:url(data:image/jpeg;base64,%s)}"
                       % (slug, b64(j)))
        cards.append("""
<figure class="spec %s">
  <div class="shot i-%s"></div>
  <figcaption>
    <div class="hd"><span class="kind">%s</span><span class="fam">%s</span></div>
    <p class="nt">%s</p>%s
    <dl class="ax">
      <div><dt>total reflectance</dt><dd>%.4f%% <span class="s">%.1f× vs flat</span></dd>%s</div>
      <div><dt>form destruction</dt><dd>%.2f× <span class="s">smear vs flat wall</span></dd>%s</div>
      <div><dt>head-on brightness</dt><dd>%.3f <span class="s">vs plain black wall</span></dd>%s</div>
    </dl>
    <p class="seeds">%d geometry seeds</p>
  </figcaption>
</figure>""" % (kind, slug, kind.upper(), html.escape(label),
                html.escape(blurb), flag,
                100 * d, FLAT / d, bar(d, 0.002, 0.005, invert=True),
                sm, bar(sm, 0.9, 5.0),
                pk, bar(pk, 0.05, 2.0, invert=True), n))

    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "report_phase3_template.html")).read()
    # Study-wide, not just the six cards: the design that leads total
    # reflectance is a stack that was NOT in the original six, and quoting
    # "best single" from the card set only would have hidden that.
    rank = AB.darkness()
    singles = [r for r in rank if not r["design"].startswith("ST_")]
    stacks = [r for r in rank if r["design"].startswith("ST_")]
    ok_any = [r for r in rank if AB.buildable(r["process"], r["feature"])[0]]
    best_single, best_stack = singles[0], stacks[0]
    best_ok = ok_any[0]
    out = (tpl
           .replace("{{DATE}}", date)
           .replace("{{IMGCSS}}", "\n".join(css))
           .replace("{{CARDS}}", "\n".join(cards))
           .replace("{{FLATPCT}}", "%.4f" % (100 * FLAT))
           .replace("{{BEST_SINGLE}}", "%.4f" % (100 * best_single["mean"]))
           .replace("{{BEST_SINGLE_NAME}}", best_single["design"])
           .replace("{{BEST_STACK}}", "%.4f" % (100 * best_stack["mean"]))
           .replace("{{BEST_STACK_NAME}}", best_stack["design"])
           .replace("{{STACK_MARGIN}}",
                    "%.1f" % (100 * (1 - best_stack["mean"]
                                     / best_single["mean"])))
           .replace("{{BEST_OK}}", "%.4f" % (100 * best_ok["mean"]))
           .replace("{{BEST_OK_NAME}}", best_ok["design"])
           .replace("{{BEST_OK_PROC}}", best_ok["process"])
           # the range the comb-on-top splits actually span, read not typed
           .replace("{{COMBTOP_RANGE}}", "%.4f-%.4f" % (
               100 * min(dark["ST_comb-cone_%d" % k][0] for k in (25, 50, 75)),
               100 * max(dark["ST_comb-cone_%d" % k][0] for k in (25, 50, 75))))
           .replace("{{CC_TOTAL}}", "%.4f" % (100 * dark["ST_comb-comb_50"][0]))
           .replace("{{CC_SMEAR}}", "%.2f" % form["ST_comb-comb_50"][0])
           .replace("{{CC_PEAK}}", "%.3f" % form["ST_comb-comb_50"][1])
           .replace("{{HC_PEAK}}", "%.3f" % form["CB_p0520_f040_x10"][1])
           .replace("{{HCCONE_PEAK}}", "%.3f" % form["ST_comb-cone_50"][1])
           .replace("{{HC_SMEAR}}", "%.2f" % form["CB_p0520_f040_x10"][0])
           .replace("{{HCCONE_SMEAR}}", "%.2f" % form["ST_comb-cone_50"][0])
           .replace("{{CONECOMB_SMEAR}}", "%.2f" % form["ST_cone-comb_50"][0])
           .replace("{{CONECOMB_PEAK}}", "%.3f" % form["ST_cone-comb_50"][1])
           .replace("{{CONE_SMEAR}}", "%.2f" % form["B_CONE_p0550"][0])
           .replace("{{CONE_PEAK}}", "%.3f" % form["B_CONE_p0550"][1])
           .replace("{{FLATPEAK}}", "%.3f" % flat_head_on())
           .replace("{{HC_GAIN}}", "%.1f" % (form["CB_p0520_f040_x10"][1]
                                             / form["ST_comb-cone_50"][1]))
           # the recommendation is about cone-over-comb specifically, so its
           # OWN total belongs here -- {{BEST_STACK}} is a different design
           .replace("{{CONECOMB_TOTAL}}",
                    "%.4f" % (100 * dark["ST_cone-comb_50"][0]))
           .replace("{{CONE_TOTAL}}", "%.4f" % (100 * dark["B_CONE_p0550"][0]))
           .replace("{{CONECOMB_COST}}",
                    "%.0f" % (100 * (dark["ST_cone-comb_50"][0]
                                     / dark["B_CONE_p0550"][0] - 1))))
    path = os.path.join(rdir, "report.html")
    open(path, "w").write(out)
    print("[DONE] %s  (%.1f MB, %d designs)"
          % (path, os.path.getsize(path) / 1e6, len(DESIGNS)))


if __name__ == "__main__":
    main()
