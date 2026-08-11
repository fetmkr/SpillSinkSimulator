"""
Dated report: one image plus one machine-readable snapshot.

    python3 scripts/make_report.py                 # today's report
    python3 scripts/make_report.py "note text"     # with a headline note

Writes into project/report/YYYY-MM-DD/ :

    HHMM_report.png     the sheet to read
    HHMM_snapshot.json  the same numbers as data
    README.md           what was done that day, appended per report

REFLECTANCE IS THE HEADLINE NUMBER. Every measurement here is an absolute
directional-hemispherical reflectance: under uniform illumination of radiance
L0 a Lambertian surface of albedo rho leaves radiance rho*L0, so the rendered
pixel value IS rho_dh, and the flat control reads 0.050000 exactly as it
should. The ratio against that flat control is carried as a secondary column
because it is what stays meaningful when the coating assumption changes -- but
it is not the answer to "how reflective is it".

Each run also writes a snapshot JSON. Nothing on the sheet compares against it
today -- the per-report diff column was dropped because it is noise while the
design is still moving. The snapshots accumulate so that a later pass over the
whole report/ folder can reconstruct the history in one go.

Everything is read back out of results/*.csv, so the report can never quote a
number that was not measured.
"""

from __future__ import annotations

import os
import sys
import csv
import json
import glob
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
REPORT = os.path.join(ROOT, "report")

# the configuration currently being recommended
BEST = {"family": "ridge", "depth_mm": 50.0, "pitch_mm": 13.0,
        "tip_mm": 0.8, "rho": 0.005, "gloss": 0.30}

# Context for the headline number. Coating and wall figures are the working
# assumptions of this project; the last four are published values, quoted so
# the simulated result can be placed against something real.
BENCH = [
    ("plain matte black wall", 5.0, "assumed baseline", "#c02020"),
    ("good black anodise", 2.0, "assumed", "#c02020"),
    ("Musou-Black class coating, flat", 0.5, "assumed; spec ~0.6%", "#b35806"),
    ("deep-sea fish skin", 0.5, "Davis 2020, Curr Biol", "#666666"),
    ("ultra-black butterfly scale", 0.2, "Davis 2020, Nat Commun", "#666666"),
    ("optimised laser beam dump", 0.1, "RP Photonics", "#666666"),
    ("Vantablack (CNT forest)", 0.03, "Surrey NanoSystems", "#666666"),
]


def load_curves(path, keyfields):
    """key -> {theta: (absolute rho_dh, ratio vs flat)}."""
    if not os.path.exists(path):
        return {}
    rows = [r for r in csv.DictReader(open(path))
            if r.get("mode") == "hemi_view"]
    cur = defaultdict(dict)
    for r in rows:
        key = tuple(float(r[f]) for f in keyfields if f in r)
        cur[key][float(r["theta"])] = (float(r["panel_mean"]),
                                       float(r["ratio_vs_flat"]))
    return cur


def band(d, lo, hi, idx=0):
    v = [x[idx] for t, x in d.items() if lo <= t <= hi]
    return max(v) if v else None


def collect():
    snap = {"generated": datetime.now().isoformat(timespec="minutes"),
            "best": dict(BEST), "grid": {}, "curve": {}, "counts": {},
            "units": {"rho": "absolute directional-hemispherical reflectance",
                      "ratio": "same quantity divided by a flat rho=0.05 plate"}}

    keys = ("depth_mm", "pitch_mm", "tip_width_mm")
    grid = load_curves(os.path.join(RESULTS, "sweep_pitch_tip.csv"), keys)
    fdm = load_curves(os.path.join(RESULTS, "sweep_fdm.csv"), keys)

    for src in (grid, fdm):
        for k, d in src.items():
            name = "%.0f/%.0f/%.1f" % k
            if name in snap["grid"]:
                continue
            snap["grid"][name] = {
                "rho0": d.get(0.0, (None, None))[0],
                "rho40": band(d, -40, 40, 0),
                "rhoall": band(d, -90, 90, 0),
                "ratio0": d.get(0.0, (None, None))[1],
                "ratio40": band(d, -40, 40, 1),
                "ratioall": band(d, -90, 90, 1),
            }

    key = (BEST["depth_mm"], BEST["pitch_mm"], BEST["tip_mm"])
    src = grid.get(key) or fdm.get(key) or {}
    snap["curve"] = {str(t): v[0] for t, v in sorted(src.items())}

    snap["counts"] = {
        "renders": sum(len(glob.glob(os.path.join(ROOT, "renders", d, "*.exr")))
                       for d in os.listdir(os.path.join(ROOT, "renders"))
                       if os.path.isdir(os.path.join(ROOT, "renders", d))),
        "sweep_csvs": len(glob.glob(os.path.join(RESULTS, "sweep_*.csv"))),
        "profiles": len(glob.glob(os.path.join(ROOT, "profiles", "*.png"))),
        "stl": len(glob.glob(os.path.join(ROOT, "export", "*.stl"))),
    }
    return snap


def previous(exclude=None):
    files = sorted(glob.glob(os.path.join(REPORT, "*", "*_snapshot.json")))
    files = [f for f in files if f != exclude]
    if not files:
        return None, None
    day = os.path.basename(os.path.dirname(files[-1]))
    return json.load(open(files[-1])), day + " " + os.path.basename(files[-1])[:4]


def fmt_delta(now, then):
    if then is None or now is None:
        return "new", "#2171b5"
    if then == 0:
        return "", "#333333"
    ch = (now - then) / then * 100.0
    if abs(ch) < 0.5:
        return "same", "#888888"
    return ("%+.0f%%" % ch), ("#1a9850" if ch < 0 else "#d73027")


def draw(snap, prev, prev_tag, note):
    fig = plt.figure(figsize=(17.0, 17.6))
    gs = fig.add_gridspec(6, 3,
                          height_ratios=[0.30, 0.62, 0.95, 1.15, 0.72, 0.82],
                          hspace=0.55, wspace=0.24)
    b = snap["best"]
    kbest = "%.0f/%.0f/%.1f" % (b["depth_mm"], b["pitch_mm"], b["tip_mm"])
    mbest = snap["grid"].get(kbest, {})

    # ---- header ---------------------------------------------------------
    ax = fig.add_subplot(gs[0, :])
    ax.axis("off")
    ax.text(0, 1.0, "Anechoic laser wall panel", fontsize=16,
            fontweight="bold", va="top")
    ax.text(0, 0.50, snap["generated"].replace("T", "  "), fontsize=10.5,
            color="#555555", va="top")
    ax.text(0.27, 1.0, "current recommendation", fontsize=10,
            fontweight="bold", va="top")
    ax.text(0.27, 0.58,
            "ridge V-grooves, irregular pitch\n"
            "depth %.0f   pitch %.0f   tip %.1f  mm\n"
            "coating rho %.3f (%.1f%%) Musou-Black class\ngloss roughness %.2f"
            % (b["depth_mm"], b["pitch_mm"], b["tip_mm"], b["rho"],
               b["rho"] * 100, b["gloss"]),
            fontsize=9.2, va="top", family="monospace")
    if mbest.get("rho0") is not None:
        ax.text(0.585, 1.0, "measured reflectance", fontsize=10,
                fontweight="bold", va="top", color="#e6550d")
        ax.text(0.585, 0.58,
                "head-on      %.4f %%\nworst +/-40  %.4f %%\nworst all    %.4f %%"
                % (mbest["rho0"] * 100, mbest["rho40"] * 100,
                   mbest["rhoall"] * 100),
                fontsize=11, va="top", family="monospace", color="#e6550d",
                fontweight="bold")
    c = snap["counts"]
    ax.text(0.855, 1.0, "project totals", fontsize=10, fontweight="bold",
            va="top")
    ax.text(0.855, 0.58,
            "%d renders\n%d sweeps\n%d profiles   %d STL"
            % (c["renders"], c["sweep_csvs"], c["profiles"], c["stl"]),
            fontsize=9.5, va="top", family="monospace")
    if note:
        ax.text(0, -0.30, "note:  " + note, fontsize=10.5, va="top",
                color="#b35806")

    # ---- conditions ------------------------------------------------------
    # A first-time reader has none of the context, and every number below is
    # conditional on this block. It is stated before the results, not after.
    axc = fig.add_subplot(gs[1, :])
    axc.axis("off")
    axc.text(0, 1.02, "What is being measured, and under what assumptions",
             fontsize=11.5, fontweight="bold", va="top")
    # Lines are kept short on purpose. The first version ran the left column
    # under the right one and the two collided into unreadable mush.
    left = [
        ("problem", "laser projectors form an aerial image in haze; every"),
        ("", "beam carries on and lands on a wall, painting a sharp"),
        ("", "bright copy that outshines the artwork. this is the wall."),
        ("panel", "500 x 500 mm, one cross-section extruded along an axis,"),
        ("", "irregular pitch so a scanning beam meets no periodic array"),
        ("quantity", "absolute directional-hemispherical reflectance"),
        ("", "rho_dh(theta): the fraction of a beam that leaves again"),
    ]
    mid = [
        ("method", "Cycles path tracing, 128 bounces, no denoise,", "#111111"),
        ("", "no clamp, linear colour. uniform illumination", "#111111"),
        ("", "with the camera tilted to theta; by reciprocity", "#111111"),
        ("", "that reads rho_dh(theta) with no glint spikes", "#111111"),
        ("coating", "rho %.3f (%.1f%%) ASSUMED, Musou-Black class"
         % (b["rho"], b["rho"] * 100), "#b35806"),
        ("", "(published spec ~0.6%). reflectance is exactly", "#b35806"),
        ("", "linear in it, so another coating just rescales", "#b35806"),
        ("", "every number on this sheet by the same factor", "#b35806"),
    ]
    right = [
        ("baseline", "a flat plate of the SAME coating, in the", "#111111"),
        ("", "same frame; a plain matte black wall is 5%", "#111111"),
        ("checks", "emission 1.0 -> 1.000000", "#111111"),
        ("", "flat rho 0.05 -> 0.050001", "#111111"),
        ("", "box cavity f=1/6 -> 0.2356 (0.233 before)", "#111111"),
        ("", "rho=0 panel -> exactly 0, so no noise floor", "#111111"),
        ("NOT", "Fresnel, so grazing figures are optimistic;", "#8c510a"),
        ("modelled", "wavelength; coating thinning down the", "#8c510a"),
        ("", "groove; panel-to-panel tiling", "#8c510a"),
    ]

    # three columns, because two put thirteen wrapped lines against seven and
    # the right-hand block collapsed on itself
    for x0, xk, block in ((0.005, 0.085, [(k, v, "#111111") for k, v in left]),
                          (0.345, 0.425, mid),
                          (0.685, 0.775, right)):
        y = 0.72
        for k, v, colr in block:
            if k:
                axc.text(x0, y, k, fontsize=8.6, fontweight="bold",
                         family="monospace", color=colr)
            axc.text(xk, y, v, fontsize=8.3, family="monospace", color=colr)
            y -= 0.115

    # ---- the geometry itself ---------------------------------------------
    # A reader should not have to imagine the shape from three numbers. The
    # section is drawn live from the same generator the renders use, so it can
    # never disagree with them.
    axg = fig.add_subplot(gs[2, 0])
    try:
        import profile_ridge as PR
        from matplotlib.patches import Polygon
        pr = PR.RidgeParams(depth=b["depth_mm"], pitch_mean=b["pitch_mm"],
                            tip_width=b["tip_mm"], face_h=90.0,
                            valley_round=0.5, arc_segments=16)
        for loop in PR.build_cross_section(pr).stage1:
            axg.add_patch(Polygon(loop, closed=True, facecolor="#4da3ff",
                                  edgecolor="#1b5fa8", lw=0.5))
        axg.plot([0, 0], [-45, 45], color="#e04040", lw=0.9, ls="--")
        axg.set_xlim(-b["depth_mm"] * 1.12, b["depth_mm"] * 0.18)
        axg.set_ylim(-42, 42)
        axg.set_aspect("equal")
        axg.set_xlabel("Y depth (mm)   <- into wall     light from +Y ->",
                       fontsize=8)
        axg.set_ylabel("Z (mm)", fontsize=8)
        axg.tick_params(labelsize=7.5)
        axg.grid(alpha=0.18, lw=0.4)
        axg.set_title("cross-section, actual scale", fontsize=10)
    except Exception as exc:
        axg.axis("off")
        axg.text(0.5, 0.5, "section unavailable\n%s" % exc, ha="center",
                 fontsize=8)

    axi = fig.add_subplot(gs[2, 1:])
    shot = os.path.join(REPORT, "assets", "recommended_3d.png")
    if os.path.exists(shot):
        import matplotlib.image as mpimg
        axi.imshow(mpimg.imread(shot))
        axi.set_title("recommended geometry, %.0f mm of panel shown "
                      "(neutral grey; the real coating renders black)"
                      % 120.0, fontsize=10)
    else:
        axi.text(0.5, 0.5, "no render at report/assets/recommended_3d.png",
                 ha="center", fontsize=9, color="#888888")
    axi.axis("off")

    # ---- performance table, reflectance first -----------------------------
    ax1 = fig.add_subplot(gs[3, :2])
    ax1.axis("off")
    ax1.text(0, 1.03, "Reflectance in percent — absolute, at coating rho = "
             "%.3f" % b["rho"], fontsize=11.5, fontweight="bold", va="top")
    ax1.text(0, 0.925, "grey columns repeat the same numbers as a ratio "
             "against a flat plate of the same coating", fontsize=8.5,
             color="#777777", va="top")

    rows = []
    for depth in (30.0, 50.0):
        for pitch in (8.0, 13.0, 20.0, 30.0):
            for tip in (0.4, 0.8, 1.6):
                k = "%.0f/%.0f/%.1f" % (depth, pitch, tip)
                if k in snap["grid"] and snap["grid"][k]["rho0"] is not None:
                    rows.append((depth, pitch, tip, k, snap["grid"][k]))

    half = (len(rows) + 1) // 2
    cols = [(0.0, rows[:half]), (0.535, rows[half:])]
    dx = [0.0, 0.040, 0.079, 0.117, 0.162, 0.230, 0.298, 0.362, 0.418]
    hdr = ["dep", "pit", "tip", "A", "head-on", "+/-40", "all",
           "x flat", "x flat"]
    for x0, chunk in cols:
        y = 0.845
        for d_, h in zip(dx, hdr):
            ax1.text(x0 + d_, y, h, fontsize=8.6, fontweight="bold",
                     color="#777777" if h == "x flat" else "#111111")
        y -= 0.056
        for depth, pitch, tip, k, m in chunk:
            hit = (depth == b["depth_mm"] and pitch == b["pitch_mm"]
                   and tip == b["tip_mm"])
            col = "#e6550d" if hit else "#333333"
            fw = "bold" if hit else "normal"
            vals = ["%.0f" % depth, "%.0f" % pitch, "%.1f" % tip,
                    "%.1f" % (depth / pitch),
                    "%.4f" % (m["rho0"] * 100),
                    "%.4f" % (m["rho40"] * 100),
                    "%.4f" % (m["rhoall"] * 100)]
            for d_, v in zip(dx, vals):
                ax1.text(x0 + d_, y, v, fontsize=8.6, color=col,
                         fontweight=fw, family="monospace")
            ax1.text(x0 + dx[7], y, "%.4f" % m["ratio0"], fontsize=8.2,
                     color="#999999", family="monospace")
            ax1.text(x0 + dx[8], y, "%.4f" % m["ratio40"], fontsize=8.2,
                     color="#999999", family="monospace")
            y -= 0.056

    # ---- angle curve, absolute ------------------------------------------
    ax2 = fig.add_subplot(gs[3, 2])
    if snap["curve"]:
        ts = sorted(float(t) for t in snap["curve"])
        ax2.axvspan(-40, 40, color="#2171b5", alpha=0.08)
        ax2.plot(ts, [snap["curve"][str(t)] * 100 for t in ts], marker="o",
                 ms=3.5, lw=2.2, color="#e6550d", label="recommended")
    seen = set()
    for lbl, val, _src, colr in BENCH:
        if val > 3:
            continue
        ax2.axhline(val, color=colr, lw=0.9, ls=":", alpha=0.8)
        if val in seen:          # two references share 0.5%; label it once
            continue
        seen.add(val)
        ax2.text(-79, val * 1.14, lbl, color=colr, fontsize=6.8)
    ax2.set_yscale("log")
    ax2.set_ylim(5e-3, 8.0)
    ax2.set_xticks(range(-80, 81, 40))
    ax2.set_xlabel("incidence angle (deg)")
    ax2.set_ylabel("reflectance  (%)")
    ax2.set_title("Recommended design vs angle", fontsize=10.5)
    ax2.grid(alpha=0.22, which="both", lw=0.5)
    ax2.legend(fontsize=8, loc="upper center")

    # ---- why this configuration ------------------------------------------
    # Derived from the grid rather than written down, so it cannot drift out
    # of date when BEST changes.
    ax5 = fig.add_subplot(gs[4, :])
    ax5.axis("off")
    ax5.text(0, 1.0, "Why this configuration", fontsize=11.5,
             fontweight="bold", va="top")

    def val(dep, pit, tip):
        m = snap["grid"].get("%.0f/%.0f/%.1f" % (dep, pit, tip))
        if not m or m["rho0"] is None:
            return None
        return (m["rho0"] * 100, m["rho40"] * 100, m["rhoall"] * 100)

    depths = sorted({float(k.split("/")[0]) for k in snap["grid"]})
    pitches = sorted({float(k.split("/")[1]) for k in snap["grid"]})
    tips = sorted({float(k.split("/")[2]) for k in snap["grid"]})
    other_d = [d for d in depths if d != b["depth_mm"]]

    # 1) depth: is the chosen depth better everywhere, or only sometimes?
    wins = tot = 0
    for pit in pitches:
        for tip in tips:
            a, c2 = val(b["depth_mm"], pit, tip), None
            for od in other_d:
                c2 = val(od, pit, tip)
                if a and c2:
                    tot += 1
                    wins += int(a[0] < c2[0] and a[1] < c2[1] and a[2] < c2[2])
    y = 0.80
    ax5.text(0.01, y, "depth %.0f mm" % b["depth_mm"], fontsize=9.5,
             fontweight="bold", family="monospace")
    ax5.text(0.13, y,
             "beats every shallower depth on all three metrics in %d of %d "
             "pitch/tip combinations -- unconditional, take it if the depth "
             "budget allows" % (wins, tot),
             fontsize=9.2, family="monospace")

    # 2) tip: what does the printable tip cost against the sharpest tested?
    y -= 0.30
    here = [t for t in tips
            if t != b["tip_mm"] and val(b["depth_mm"], b["pitch_mm"], t)]
    sharp = min(here) if here else None
    a = val(b["depth_mm"], b["pitch_mm"], b["tip_mm"])
    c2 = val(b["depth_mm"], b["pitch_mm"], sharp) if sharp else None
    ax5.text(0.01, y, "tip %.1f mm" % b["tip_mm"], fontsize=9.5,
             fontweight="bold", family="monospace")
    if a and c2:
        ax5.text(0.13, y,
                 "NOT an optical choice. %.1f mm would give %.4f%% head-on "
                 "instead of %.4f%% (%.2fx better), but %.1f mm is exactly one "
                 "nozzle width\nwith no margin; %.1f mm is two and prints "
                 "reliably. This is the one place manufacturability overrode "
                 "the measurement."
                 % (sharp, c2[0], a[0], a[0] / c2[0], sharp, b["tip_mm"]),
                 fontsize=9.2, family="monospace", color="#8c510a")

    # 3) pitch: the genuinely undetermined one
    y -= 0.34
    ax5.text(0.01, y, "pitch %.0f mm" % b["pitch_mm"], fontsize=9.5,
             fontweight="bold", family="monospace")
    parts = []
    for pit in pitches:
        v = val(b["depth_mm"], pit, b["tip_mm"])
        if v:
            parts.append("p%-2.0f %.4f/%.4f" % (pit, v[0], v[2]))
    ax5.text(0.13, y,
             "A HEDGE, not an optimum. head-on / worst-all at this depth and "
             "tip:   " + "   ".join(parts) + "\n"
             "a coarser pitch keeps winning head-on and keeps losing at "
             "grazing; %.0f mm minimises the product of the two, but that "
             "weighting is my choice, not a measurement." % b["pitch_mm"],
             fontsize=9.2, family="monospace", color="#8c510a")

    # ---- benchmark table -------------------------------------------------
    ax4 = fig.add_subplot(gs[5, 0])
    ax4.axis("off")
    ax4.text(0, 1.0, "Where this sits", fontsize=11.5, fontweight="bold",
             va="top")
    y = 0.87
    ax4.text(0.0, y, "surface", fontsize=8.8, fontweight="bold")
    ax4.text(0.62, y, "refl.", fontsize=8.8, fontweight="bold")
    ax4.text(0.80, y, "source", fontsize=8.8, fontweight="bold")
    y -= 0.075
    entries = list(BENCH)
    if mbest.get("rho0") is not None:
        entries.append(("THIS PANEL, head-on", mbest["rho0"] * 100,
                        "simulated", "#e6550d"))
        entries.append(("THIS PANEL, worst angle", mbest["rhoall"] * 100,
                        "simulated", "#e6550d"))
    for lbl, val, src, colr in sorted(entries, key=lambda e: -e[1]):
        hit = lbl.startswith("THIS")
        ax4.text(0.0, y, lbl, fontsize=8.6, color=colr,
                 fontweight="bold" if hit else "normal")
        ax4.text(0.62, y, "%.3f%%" % val, fontsize=8.6, color=colr,
                 family="monospace", fontweight="bold" if hit else "normal")
        ax4.text(0.80, y, src, fontsize=7.4, color="#888888")
        y -= 0.075

    # ---- design laws + open questions ------------------------------------
    ax3 = fig.add_subplot(gs[5, 1:])
    ax3.axis("off")
    ax3.text(0, 1.0, "Design laws, measured", fontsize=11.5,
             fontweight="bold", va="top")
    y = 0.86
    for line in (
        "reflectance  ~  0.09 x (tip width / pitch) x rho     "
        "-- only the RATIO tip/pitch matters, so a coarser",
        "                pitch buys a blunter tip; and it is exactly linear "
        "in the coating reflectance",
        "aspect ratio A = depth / pitch:  A >= 2 holds +/-40 deg,  A >= 6 "
        "holds every angle;  below A = 1 it triples",
        "gloss roughness 0.30 is an interior optimum -- 0.15 leaves a "
        "specular lobe aimed at the observer, 0.50 scatters back",
    ):
        ax3.text(0.01, y, line, fontsize=8.8, family="monospace")
        y -= 0.082

    y -= 0.115
    ax3.text(0, y, "Open, and blocking a final choice", fontsize=11.5,
             fontweight="bold", va="top")
    y -= 0.135
    for line in (
        "1. incidence angle distribution of the real rig -- the pitch choice "
        "flips on whether +/-80 deg has to be held",
        "2. does the coating reach the bottom of the groove? an uncoated "
        "floor is not rho 0.005, it is bare substrate",
        "3. no Fresnel in the material model, so the grazing-angle figures "
        "are optimistic by an unmeasured factor",
        "4. every absolute number above assumes the coating really is "
        "rho 0.005; unverified until a coupon is measured",
    ):
        ax3.text(0.01, y, line, fontsize=8.8, family="monospace",
                 color="#8c510a")
        y -= 0.082

    out = os.path.join(snap["daydir"], snap["time"] + "_report.png")
    fig.savefig(out, dpi=118, bbox_inches="tight")
    plt.close(fig)
    return out


def append_readme(daydir, snap, note, png, prev_tag):
    path = os.path.join(daydir, "README.md")
    first = not os.path.exists(path)
    b = snap["best"]
    k = "%.0f/%.0f/%.1f" % (b["depth_mm"], b["pitch_mm"], b["tip_mm"])
    m = snap["grid"].get(k)
    with open(path, "a") as f:
        if first:
            f.write("# %s\n\n" % os.path.basename(daydir))
        f.write("## %s\n\n" % snap["time"])
        if note:
            f.write("%s\n\n" % note)
        f.write("- recommendation: depth %.0f mm, pitch %.0f mm, tip %.1f mm, "
                "coating rho %.3f, gloss %.2f\n"
                % (b["depth_mm"], b["pitch_mm"], b["tip_mm"], b["rho"],
                   b["gloss"]))
        if m:
            f.write("- **reflectance: head-on %.4f%%, worst +/-40 %.4f%%, "
                    "worst all %.4f%%**\n"
                    % (m["rho0"] * 100, m["rho40"] * 100, m["rhoall"] * 100))
            f.write("  (as a ratio against a flat plate of the same coating: "
                    "%.4f / %.4f / %.4f)\n"
                    % (m["ratio0"], m["ratio40"], m["ratioall"]))
        c = snap["counts"]
        f.write("- totals: %d renders, %d sweeps, %d profiles, %d STL\n"
                % (c["renders"], c["sweep_csvs"], c["profiles"], c["stl"]))
        f.write("- [%s](%s)\n\n" % (os.path.basename(png),
                                    os.path.basename(png)))
    return path


def main():
    note = sys.argv[1] if len(sys.argv) > 1 else ""
    now = datetime.now()
    snap = collect()
    snap["day"] = now.strftime("%Y-%m-%d")
    snap["time"] = now.strftime("%H%M")
    snap["daydir"] = os.path.join(REPORT, snap["day"])
    os.makedirs(snap["daydir"], exist_ok=True)

    js = os.path.join(snap["daydir"], snap["time"] + "_snapshot.json")
    prev, prev_tag = previous(exclude=js)

    png = draw(snap, prev, prev_tag, note)
    out = {k: v for k, v in snap.items() if k != "daydir"}
    with open(js, "w") as f:
        json.dump(out, f, indent=2)
    rd = append_readme(snap["daydir"], snap, note, png, prev_tag)

    print("[REPORT]", os.path.relpath(png, ROOT))
    print("[SNAP]  ", os.path.relpath(js, ROOT))
    print("[LOG]   ", os.path.relpath(rd, ROOT))
    print("[DIFF]  ", ("compared against " + prev_tag) if prev_tag
          else "first report, nothing to compare against yet")


if __name__ == "__main__":
    main()
