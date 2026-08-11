"""
Comparison report, v2: the extruded V-groove against the 3D cone array.

    python3 scripts/report_compare.py ["note"]

Rewritten after an adversarial review found three wrong claims in v1. What
changed, and why, is on the page itself -- a client who was shown v1 has to be
able to see exactly which numbers moved.

    tip convention   profile_ridge.tip_width is a full WIDTH, geom3d.tip_radius
                     is a RADIUS, so v1's "tip 0.2 both" was still a factor of
                     two apart, in the direction that flattered the cone. And
                     0.2 mm is half an FDM nozzle: not a buildable design.
                     Everything here is one nozzle, 0.4 mm across, for both.
    exported geom     v1 measured the cones with tileable=False while the STL
                     and the render used tileable=True, which re-snaps the
                     lattice. Measured and pictured were 7.5% apart. All cone
                     numbers here are measured on the exported geometry.
    form              v1 quoted "core 0.11 vs 0.99" from two designs that are
                     not on the page and do not match each other. Measured on
                     the actual pair, and reported as rms rather than core_frac,
                     which breaks when the smear runs off the window.

Reads results/sweep_v2.csv and results/form_v2.json. Gated on scripts/lock.py.
"""
from __future__ import annotations
import os, sys, csv, json
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate import require_lock                                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
REPORT = os.path.join(ROOT, "report")
PROF = os.path.join(ROOT, "profiles")

FLAT = "V2_flat_coating"
CASES = [
    ("1D V-groove", "d50 / p13", "V2_groove_d50_p13", "W_groove_d50_p13",
     "085_3d_fair_groove_d50_p13.png", "#c02020"),
    ("1D V-groove", "d30 / p7.5", "V2_groove_d30_p75", "W_groove_d30_p75",
     "086_3d_fair_groove_d30_p75.png", "#e6845c"),
    ("3D cone, as exported", "d30 / p7.5", "V2_cone_d30_p75", "W_cone_d30_p75",
     "083_3d_stl_cone_d30_p75.png", "#e6550d"),
    ("3D cone, as exported", "d30 / p3.75", "V2_cone_d30_p375",
     "W_cone_d30_p375", "084_3d_stl_cone_d30_p375.png", "#2171b5"),
]


def load():
    cur = defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(RESULTS, "sweep_v2.csv"))):
        cur[r["tag"]][float(r["theta"])] = float(r["rho"]) * 100.0
    form = {}
    fp = os.path.join(RESULTS, "form_v2.json")
    if os.path.exists(fp):
        for rec in json.load(open(fp)):
            form[rec["tag"]] = rec
    return cur, form


def band(d, lo, hi):
    return max(v for t, v in d.items() if lo <= t <= hi)


def img(fname):
    p = os.path.join(PROF, fname)
    return p if os.path.exists(p) else None


def main():
    note = sys.argv[1] if len(sys.argv) > 1 else ""
    lock_status = require_lock()
    cur, form = load()
    now = datetime.now()
    daydir = os.path.join(REPORT, now.strftime("%Y-%m-%d"))
    os.makedirs(daydir, exist_ok=True)
    flat = cur[FLAT]

    fig = plt.figure(figsize=(18.2, 19.0))
    gs = fig.add_gridspec(5, 4, height_ratios=[0.78, 1.00, 1.00, 0.82, 1.15],
                          hspace=0.66, wspace=0.24)

    # ---------------- header -------------------------------------------
    ax = fig.add_subplot(gs[0, :]); ax.axis("off")
    ax.text(0, 1.04, "V-groove vs 3D cone", fontsize=16,
            fontweight="bold", va="top")
    ax.text(0, 0.68, now.strftime("%Y-%m-%d  %H:%M") + "     v2, after review",
            fontsize=10.5, color="#555555", va="top")
    ax.text(0, 0.40, lock_status, fontsize=9.5, va="top", family="monospace",
            color="#2166ac" if lock_status.startswith("LOCK PASS") else "#b35806")
    if note:
        ax.text(0, 0.10, "note:  " + note, fontsize=10, va="top",
                color="#b35806")

    ax.text(0.26, 1.04, "the situation", fontsize=10, fontweight="bold",
            va="top")
    ax.text(0.26, 0.80,
            "hundreds of laser projectors converge in mid-air to form the\n"
            "artwork, visible only because haze scatters a few percent of\n"
            "each beam. every beam then carries on and lands on a wall,\n"
            "which gets essentially the full beam power and paints a sharp\n"
            "bright copy of the artwork around it. this panel is that wall.\n"
            "priority 1 is destroying the FORM of what returns, priority 2\n"
            "is reducing how much returns. the beams cannot be blanked --\n"
            "the beam in flight IS the artwork.",
            fontsize=9.0, va="top", family="monospace")
    ax.text(0.63, 1.04, "the conditions every number below assumes",
            fontsize=10, fontweight="bold", va="top")
    ax.text(0.63, 0.80,
            "coating   rho 0.005 (0.5%), Musou-Black class, gloss 0.30.\n"
            "          measured on a flat plate here: 0.4953%. published\n"
            "          spec is ~0.6%, so this is slightly optimistic.\n"
            "          reflectance is linear in it (checked over 8x), so a\n"
            "          different coating rescales every number equally.\n"
            "tip       one FDM nozzle, 0.4 mm ACROSS, for both families.\n"
            "quantity  absolute directional-hemispherical reflectance: the\n"
            "          fraction of an arriving beam that leaves again.\n"
            "method    Cycles, 128 bounces, no denoise/clamp, linear colour;\n"
            "          uniform illumination with the camera tilted, which by\n"
            "          reciprocity reads that fraction directly.\n"
            "NOT modelled  Fresnel (so grazing is optimistic), wavelength,\n"
            "          whether the coating reaches the root of a deep cell.",
            fontsize=9.0, va="top", family="monospace")

    # ---------------- the four designs ----------------------------------
    for i, (fam, spec, tag, ftag, im, colr) in enumerate(CASES):
        axi = fig.add_subplot(gs[1, i])
        p = img(im)
        if p:
            axi.imshow(mpimg.imread(p))
        axi.axis("off")
        axi.set_title("%s\n%s / tip 0.4 across" % (fam.replace(", as exported", "\n(as exported)"), spec), fontsize=9.2,
                      color=colr, fontweight="bold")
        d = cur[tag]
        rms = form.get(ftag, {}).get("thetas", {}).get("-40", {}) \
                  .get("panel", {}).get("rms_mm")
        axi.text(0.5, -0.08,
                 "head-on %.4f %%\n+/-40   %.4f %%\nall     %.4f %%%s"
                 % (d[0.0], band(d, -40, 40), band(d, -90, 90),
                    ("\nsmear   %.2f mm" % rms) if rms else ""),
                 transform=axi.transAxes, ha="center", va="top",
                 fontsize=9.5, family="monospace", color=colr)

    # ---------------- curves --------------------------------------------
    ax2 = fig.add_subplot(gs[2, :2])
    for fam, spec, tag, ftag, im, colr in CASES:
        d = cur[tag]
        ts = sorted(d)
        lw = 2.6 if "cone" in tag else 1.8
        ax2.plot(ts, [d[t] for t in ts], marker="o", ms=3.5, lw=lw,
                 color=colr, label="%s  %s" % (fam.split(",")[0], spec))
    ts = sorted(flat)
    ax2.plot(ts, [flat[t] for t in ts], lw=1.6, ls="--", color="#b35806",
             label="the same coating on a FLAT plate")
    ax2.axvspan(-40, 40, color="#2171b5", alpha=0.07)
    for lbl, val in (("plain matte black wall", 5.0), ("black anodise", 2.0),
                     ("ultra-black butterfly", 0.2),
                     ("optimised beam dump", 0.1)):
        if val > 3:
            continue
        ax2.axhline(val, color="#999999", lw=0.8, ls=":")
        ax2.text(-79, val * 1.14, lbl, color="#777777", fontsize=7)
    ax2.set_yscale("log"); ax2.set_ylim(3e-3, 3.0)
    ax2.set_xticks(range(-80, 81, 20))
    ax2.set_xlabel("incidence angle from the panel normal (deg)")
    ax2.set_ylabel("reflectance  (%)")
    ax2.set_title("All four, same coating, same measurement", fontsize=11.5)
    ax2.grid(alpha=0.25, which="both", lw=0.5)
    ax2.legend(fontsize=8.3, loc="upper center")

    ax3 = fig.add_subplot(gs[2, 2])
    for lbl, tag, colr in (("1D V-groove", "V2_groove_d30_p75", "#c02020"),
                           ("3D cone", "V2_cone_d30_p75", "#e6550d")):
        d = cur[tag]
        ts = sorted(d)
        ax3.plot(ts, [d[t] for t in ts], marker="o", ms=3.5, lw=2.4,
                 color=colr, label=lbl)
    ax3.set_yscale("log"); ax3.set_ylim(3e-3, 0.4)
    ax3.set_xticks(range(-80, 81, 40))
    ax3.set_xlabel("incidence (deg)"); ax3.set_ylabel("reflectance (%)")
    ax3.set_title("Fair fight\nd30 / p7.5 / 0.4 across, both", fontsize=10)
    ax3.grid(alpha=0.25, which="both", lw=0.5); ax3.legend(fontsize=8)

    # what the STRUCTURE buys, angle by angle -- the honest form of "100x"
    ax4 = fig.add_subplot(gs[2, 3])
    for fam, spec, tag, ftag, im, colr in CASES:
        d = cur[tag]
        ts = sorted(d)
        ax4.plot(ts, [flat[t] / d[t] for t in ts], lw=2.0, color=colr)
    ax4.axhline(1.0, color="#999999", lw=0.8, ls=":")
    ax4.set_yscale("log")
    ax4.set_xticks(range(-80, 81, 40))
    ax4.set_xlabel("incidence (deg)")
    ax4.set_ylabel("x darker than the flat coating")
    ax4.set_title("The '100x' is a HEAD-ON figure", fontsize=10)
    ax4.grid(alpha=0.25, which="both", lw=0.5)

    # ---------------- form ------------------------------------------------
    ax5 = fig.add_subplot(gs[3, :2])
    labels, vals, cols = [], [], []
    for fam, spec, tag, ftag, im, colr in CASES:
        rec = form.get(ftag)
        if not rec:
            continue
        labels.append("%s\n%s" % (fam.split(",")[0], spec))
        vals.append(rec["thetas"]["-40"]["panel"]["rms_mm"])
        cols.append(colr)
    ctrl = (form.get("W_cone_d30_p75", {}).get("thetas", {}).get("-40", {})
            .get("control", {}).get("rms_mm"))
    ax5.bar(range(len(vals)), vals, color=cols, width=0.62)
    if ctrl:
        ax5.axhline(ctrl, color="#333333", lw=1.2, ls="--")
        ax5.text(len(vals) - 0.4, ctrl * 1.06,
                 "flat wall, %.2f mm" % ctrl, fontsize=8, ha="right")
    ax5.set_xticks(range(len(labels)))
    ax5.set_xticklabels(labels, fontsize=8.5)
    ax5.set_ylabel("smear of a 2 mm line, rms (mm)")
    ax5.set_title("PRIORITY 1: how badly the line is destroyed, at -40 deg",
                  fontsize=11.5)
    ax5.grid(alpha=0.25, axis="y", lw=0.5)
    for i, v in enumerate(vals):
        ax5.text(i, v * 1.02, "%.2f" % v, ha="center", fontsize=9,
                 fontweight="bold")

    # ---------------- table ------------------------------------------------
    ax6 = fig.add_subplot(gs[3, 2:]); ax6.axis("off")
    ax6.text(0, 1.06, "Reflectance %, absolute, and smear at -40 deg",
             fontsize=11.5, fontweight="bold", va="top")
    xs = [0.0, 0.30, 0.44, 0.58, 0.72, 0.87]
    for x, h in zip(xs, ["design", "head-on", "+/-40", "all", "smear",
                         "MTF@20mm"]):
        ax6.text(x, 0.92, h, fontsize=8.8, fontweight="bold")
    y = 0.80
    for fam, spec, tag, ftag, im, colr in CASES:
        d = cur[tag]
        rec = form.get(ftag, {}).get("thetas", {}).get("-40", {}).get("panel", {})
        vals = ["%s %s" % ("1D" if "groove" in tag else "3D", spec),
                "%.4f" % d[0.0], "%.4f" % band(d, -40, 40),
                "%.4f" % band(d, -90, 90),
                ("%.2f mm" % rec["rms_mm"]) if rec else "-",
                ("%.2f" % rec["mtf_20mm"]) if rec else "-"]
        for x, v in zip(xs, vals):
            ax6.text(x, y, v, fontsize=8.8, color=colr, family="monospace")
        y -= 0.095
    ax6.text(0, y - 0.02, "%-14s %s" % ("flat plate", "%.4f  (the coating on "
             "its own)" % flat[0.0]), fontsize=8.8, family="monospace",
             color="#b35806")
    y -= 0.14
    gr, co = cur["V2_groove_d30_p75"][0.0], cur["V2_cone_d30_p75"][0.0]
    for line in (
        "matched on depth, pitch and printable tip, the",
        "cone is %.1fx darker head-on and smears the line" % (gr / co),
        "%.1fx wider. both axes, one design." % (
            form["W_cone_d30_p75"]["thetas"]["-40"]["panel"]["rms_mm"] /
            form["W_groove_d30_p75"]["thetas"]["-40"]["panel"]["rms_mm"]),
        "",
        "head-on nothing destroys form: observer and beam",
        "collinear, first hit visible, one bounce.",
    ):
        ax6.text(0.0, y, line, fontsize=8.6, family="monospace",
                 color="#333333")
        y -= 0.075

    # ---------------- what changed since v1 --------------------------------
    ax7 = fig.add_subplot(gs[4, :]); ax7.axis("off")
    ax7.text(0, 1.04, "What changed since the first version of this "
             "comparison, and what is still open", fontsize=11.5,
             fontweight="bold", va="top")
    y = 0.90
    for line, colr in (
        ("An adversarial review of v1 found three claims wrong. All three "
         "flattered the cone, so anyone shown v1 needs these:", "#8c510a"),
        ("", "#333333"),
        ("  TIP     v1 said \"tip 0.2 mm, both\". It was not: ridge tip_width "
         "is a full width, cone tip_radius is a radius, so the groove had a "
         "tip half the", "#8c510a"),
        ("          size -- and 0.2 mm is half an FDM nozzle and cannot be "
         "printed. At one nozzle, 0.4 mm across for both, the gain is %.1fx, "
         "not 2.9x." % (gr / co), "#8c510a"),
        ("  GEOMETRY v1 measured the cones with tileable off while the STL and "
         "the picture had it on, which re-snaps the lattice up to 5% denser. "
         "Measured", "#8c510a"),
        ("          and pictured were 7.5% apart. Every cone number here is "
         "measured on the geometry that is actually exported.", "#8c510a"),
        ("  FORM    v1's \"core 0.11 vs 0.99\" came from two designs that are "
         "not on this page and do not match each other. The real pair is in "
         "the bar", "#8c510a"),
        ("          chart. core_frac is also unusable at large smear -- energy "
         "that leaves the window leaves the denominator too -- so smear is "
         "reported as rms.", "#8c510a"),
        ("", "#333333"),
        ("Still open. The \"%.0fx darker than the flat coating\" figure is "
         "HEAD-ON: by -80 deg it is only %.1fx, as the third panel shows. "
         "Fresnel is not"
         % (flat[0.0] / co, flat[-80.0] / cur["V2_cone_d30_p75"][-80.0]),
         "#333333"),
        ("modelled, and grazing is exactly where that bites. And the pitch "
         "choice -- coarse wins head-on, fine wins at grazing -- cannot be "
         "settled until", "#333333"),
        ("we know the incidence angles the real rig puts on the wall. That is "
         "the one missing input, and it is a measurement on the installation, "
         "not a simulation.", "#333333"),
    ):
        ax7.text(0.005, y, line, fontsize=8.8, family="monospace", color=colr)
        y -= 0.078

    out = os.path.join(daydir, now.strftime("%H%M") + "_compare.png")
    fig.savefig(out, dpi=112, bbox_inches="tight")
    plt.close(fig)
    print("[REPORT]", os.path.relpath(out, ROOT))


if __name__ == "__main__":
    main()
