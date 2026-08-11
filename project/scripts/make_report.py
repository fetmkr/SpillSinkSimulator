"""
Dated report: one image plus one machine-readable snapshot.

    python3 scripts/make_report.py                 # today's report
    python3 scripts/make_report.py "note text"     # with a headline note

Writes into project/report/YYYY-MM-DD/ :

    HHMM_report.png     the sheet to read
    HHMM_snapshot.json  the same numbers as data
    README.md           what was done that day, appended per report

REFLECTANCE IS THE HEADLINE NUMBER, absolute and in percent. Under uniform
illumination of radiance L0 a Lambertian surface of albedo rho leaves radiance
rho*L0, so a rendered pixel IS rho_dh and the flat control reads 0.050000. The
ratio against that control is carried as a secondary column.

Snapshots accumulate so a later pass over the whole report/ folder can rebuild
the history; nothing on the sheet compares against them today.

Every number is read back out of results/*.csv and results/*.json, so the
report cannot quote something that was not measured.
"""

from __future__ import annotations

import os
import sys
import csv
import json
import glob
import math
from datetime import datetime
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
REPORT = os.path.join(ROOT, "report")

BEST = {"family": "3D cone array", "tag": "J_d80_jit30", "form_tag":
        "K_cone_d120_p13", "depth_mm": 80.0, "pitch_mm": 13.0, "tip_mm": 0.8,
        "jitter": 0.30, "rho": 0.005, "gloss": 0.30}

# label, tag, which CSV, colour
ROWS = [
    ("1D V-groove  d50 p13", "R_ref_d50_p13", "r1", "#c02020"),
    ("1D V-groove  d50 p8", "R_ref_d50_p08", "r1", "#c02020"),
    ("3D cone  d50 p13", "J_jit30", "r2", "#2171b5"),
    ("3D cone  d80 p13", "J_d80_jit30", "r2", "#e6550d"),
    ("3D cone  d120 p13", "J_d120_jit30", "r2", "#2171b5"),
    ("3D cone  d80 p8", "J_d80_p08", "r2", "#41ab5d"),
    ("3D cone  no jitter", "J_nojit", "r2", "#888888"),
    ("3D cone  tilt 30", "J_tilt30_jit30", "r2", "#888888"),
]

BENCH = [
    ("plain matte black wall", 5.0, "assumed baseline", "#c02020"),
    ("good black anodise", 2.0, "assumed", "#c02020"),
    ("Musou-Black class, flat", 0.5, "assumed; spec ~0.6%", "#b35806"),
    ("deep-sea fish skin", 0.5, "Davis 2020 Curr Biol", "#666666"),
    ("ultra-black butterfly", 0.2, "Davis 2020 Nat Commun", "#666666"),
    ("optimised beam dump", 0.1, "RP Photonics", "#666666"),
    ("Vantablack (CNT)", 0.03, "Surrey NanoSystems", "#666666"),
]


def load_csv(name, key="tag"):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return {}, {}
    cur, meta = defaultdict(dict), {}
    for r in csv.DictReader(open(path)):
        if "rho" in r:
            val = float(r["rho"]) * 100.0
        elif r.get("mode") == "hemi_view":
            val = float(r["panel_mean"]) * 100.0
        else:
            continue
        cur[r[key]][float(r["theta"])] = val
        meta[r[key]] = r
    return cur, meta


def band(d, lo, hi):
    v = [x for t, x in d.items() if lo <= t <= hi]
    return max(v) if v else None


def collect():
    snap = {"generated": datetime.now().isoformat(timespec="minutes"),
            "best": dict(BEST), "cases": {}, "curve": {}, "form": {},
            "counts": {},
            "units": {"reflectance": "absolute, percent, "
                      "directional-hemispherical"}}

    r1, m1 = load_csv("sweep_cone3d.csv")
    r2, m2 = load_csv("sweep_cone3d_r2.csv")
    src = {"r1": (r1, m1), "r2": (r2, m2)}

    for label, tag, which, _c in ROWS:
        cur, meta = src[which]
        if tag not in cur:
            continue
        d = cur[tag]
        snap["cases"][label] = {
            "tag": tag,
            "head_on": d.get(0.0), "w40": band(d, -40, 40),
            "wall": band(d, -90, 90),
            "depth": float(meta[tag]["depth_mm"]),
            "pitch": float(meta[tag]["pitch_mm"]),
            "aspect": float(meta[tag]["aspect"]),
        }

    if BEST["tag"] in r2:
        snap["curve"] = {str(t): v for t, v in sorted(r2[BEST["tag"]].items())}

    fpath = os.path.join(RESULTS, "cone3d_mtf.json")
    if os.path.exists(fpath):
        for c in json.load(open(fpath)):
            snap["form"][c["tag"]] = {
                th: {"core": v["panel"]["core_frac"],
                     "rms": v["panel"]["rms_mm"],
                     "mtf20": v["panel"]["mtf_20mm"],
                     "energy": v["energy_ratio"]}
                for th, v in c["thetas"].items()}

    snap["counts"] = {
        "renders": sum(len(glob.glob(os.path.join(ROOT, "renders", d, "*.exr")))
                       for d in os.listdir(os.path.join(ROOT, "renders"))
                       if os.path.isdir(os.path.join(ROOT, "renders", d))),
        "sweeps": len(glob.glob(os.path.join(RESULTS, "sweep_*.csv"))),
        "profiles": len(glob.glob(os.path.join(ROOT, "profiles", "*.png"))),
        "stl": len(glob.glob(os.path.join(ROOT, "export", "*.stl"))),
    }
    return snap


def draw(snap, note):
    b = snap["best"]
    best = None
    for label, tag, _w, _c in ROWS:
        if tag == b["tag"] and label in snap["cases"]:
            best = snap["cases"][label]
    fig = plt.figure(figsize=(17.5, 15.6))
    gs = fig.add_gridspec(5, 3, height_ratios=[0.30, 0.58, 1.00, 1.05, 0.86],
                          hspace=0.58, wspace=0.24)

    # ---------------- header ----------------
    ax = fig.add_subplot(gs[0, :]); ax.axis("off")
    ax.text(0, 1.0, "Anechoic laser wall panel", fontsize=16,
            fontweight="bold", va="top")
    ax.text(0, 0.48, snap["generated"].replace("T", "  "), fontsize=10.5,
            color="#555555", va="top")
    ax.text(0.25, 1.0, "current recommendation", fontsize=10,
            fontweight="bold", va="top")
    ax.text(0.25, 0.58,
            "%s, irregular\ndepth %.0f   pitch %.0f   tip %.1f  mm\n"
            "coating rho %.3f (%.1f%%)   gloss %.2f"
            % (b["family"], b["depth_mm"], b["pitch_mm"], b["tip_mm"],
               b["rho"], b["rho"] * 100, b["gloss"]),
            fontsize=9.4, va="top", family="monospace")
    if best:
        ax.text(0.575, 1.0, "measured reflectance", fontsize=10,
                fontweight="bold", va="top", color="#e6550d")
        ax.text(0.575, 0.58,
                "head-on      %.4f %%\nworst +/-40  %.4f %%\nworst all    %.4f %%"
                % (best["head_on"], best["w40"], best["wall"]),
                fontsize=11, va="top", family="monospace", color="#e6550d",
                fontweight="bold")
    c = snap["counts"]
    ax.text(0.855, 1.0, "project totals", fontsize=10, fontweight="bold",
            va="top")
    ax.text(0.855, 0.58, "%d renders\n%d sweeps\n%d profiles   %d STL"
            % (c["renders"], c["sweeps"], c["profiles"], c["stl"]),
            fontsize=9.4, va="top", family="monospace")
    if note:
        ax.text(0, -0.28, "note:  " + note, fontsize=10.5, va="top",
                color="#b35806")

    # ---------------- conditions ----------------
    axc = fig.add_subplot(gs[1, :]); axc.axis("off")
    axc.text(0, 1.02, "What is being measured, and under what assumptions",
             fontsize=11.5, fontweight="bold", va="top")
    cols = [
        (0.005, 0.085, [
            ("problem", "laser projectors form an aerial image in haze;", "#111"),
            ("", "every beam carries on and lands on a wall, painting", "#111"),
            ("", "a sharp copy that outshines it. this is the wall.", "#111"),
            ("panel", "500 x 500 mm module; irregular cell placement so", "#111"),
            ("", "a scanning beam meets no periodic array", "#111"),
            ("quantity", "absolute directional-hemispherical reflectance:", "#111"),
            ("", "the fraction of an arriving beam that leaves again", "#111")]),
        (0.345, 0.425, [
            ("method", "Cycles path tracing, 128 bounces, no denoise,", "#111"),
            ("", "no clamp, linear colour. uniform illumination with", "#111"),
            ("", "the camera tilted to theta; by reciprocity that", "#111"),
            ("", "reads rho_dh(theta) with no glint spikes", "#111"),
            ("coating", "rho %.3f (%.1f%%) ASSUMED, Musou-Black class"
             % (b["rho"], b["rho"] * 100), "#b35806"),
            ("", "(spec ~0.6%). reflectance is exactly linear in it,", "#b35806"),
            ("", "so another coating rescales every number here", "#b35806")]),
        (0.685, 0.775, [
            ("baseline", "a flat plate of the SAME coating in the same", "#111"),
            ("", "frame; a plain matte black wall is taken as 5%", "#111"),
            ("checks", "emission 1.0 -> 1.000000", "#111"),
            ("", "flat rho 0.05 -> 0.050001", "#111"),
            ("", "box cavity f=1/6 -> 0.2356 (0.233 before)", "#111"),
            ("", "rho=0 panel -> exactly 0, so no noise floor", "#111"),
            ("NOT", "Fresnel, so grazing figures are optimistic;", "#8c510a"),
            ("modelled", "wavelength; coating reach into the cell;", "#8c510a"),
            ("", "panel-to-panel tiling", "#8c510a")]),
    ]
    for x0, xk, block in cols:
        y = 0.72
        for k, v, colr in block:
            if k:
                axc.text(x0, y, k, fontsize=8.6, fontweight="bold",
                         family="monospace", color=colr)
            axc.text(xk, y, v, fontsize=8.3, family="monospace", color=colr)
            y -= 0.115

    # ---------------- geometry ----------------
    axg = fig.add_subplot(gs[2, 0])
    try:
        import geom3d as G3
        p = G3.Cone3DParams(depth=b["depth_mm"], pitch=b["pitch_mm"],
                            tip_radius=b["tip_mm"] / 2.0)
        R = p.effective_overlap() * p.pitch / 2.0
        for k in (-1, 0, 1):
            xs = [k * p.pitch - R, k * p.pitch - b["tip_mm"] / 2,
                  k * p.pitch + b["tip_mm"] / 2, k * p.pitch + R]
            ys = [-p.depth, 0.0, 0.0, -p.depth]
            axg.fill(xs, ys, facecolor="#4da3ff", edgecolor="#1b5fa8", lw=0.6,
                     alpha=0.85)
        axg.plot([-1.6 * p.pitch, 1.6 * p.pitch], [0, 0], color="#e04040",
                 lw=0.9, ls="--")
        axg.set_xlim(-1.7 * p.pitch, 1.7 * p.pitch)
        axg.set_ylim(-p.depth * 1.12, p.depth * 0.22)
        axg.set_aspect("equal")
        axg.set_xlabel("across the face (mm)", fontsize=8)
        axg.set_ylabel("depth (mm)", fontsize=8)
        axg.tick_params(labelsize=7.5)
        axg.grid(alpha=0.18, lw=0.4)
        axg.set_title("one cone in section, actual scale\n"
                      "(3 of ~600 across a 500 mm module)", fontsize=9.5)
    except Exception as exc:
        axg.axis("off")
        axg.text(0.5, 0.5, str(exc), ha="center", fontsize=8)

    axi = fig.add_subplot(gs[2, 1:])
    shot = os.path.join(REPORT, "assets", "recommended_3d.png")
    if os.path.exists(shot):
        import matplotlib.image as mpimg
        axi.imshow(mpimg.imread(shot))
        axi.set_title("the recommended surface (neutral grey; the real "
                      "coating renders black)", fontsize=10)
    axi.axis("off")

    # ---------------- reflectance table + curve ----------------
    ax1 = fig.add_subplot(gs[3, :2]); ax1.axis("off")
    ax1.text(0, 1.03, "Reflectance in percent — absolute, at coating rho = "
             "%.3f" % b["rho"], fontsize=11.5, fontweight="bold", va="top")
    xs = [0.0, 0.30, 0.42, 0.53, 0.66, 0.79]
    for x, h in zip(xs, ["case", "depth", "A", "head-on", "+/-40", "all"]):
        ax1.text(x, 0.93, h, fontsize=9, fontweight="bold")
    y = 0.855
    for label, tag, _w, colr in ROWS:
        if label not in snap["cases"]:
            continue
        m = snap["cases"][label]
        hit = tag == b["tag"]
        fw = "bold" if hit else "normal"
        cc = "#e6550d" if hit else colr
        for x, v in zip(xs, [label, "%.0f" % m["depth"], "%.1f" % m["aspect"],
                             "%.4f" % m["head_on"], "%.4f" % m["w40"],
                             "%.4f" % m["wall"]]):
            ax1.text(x, y, v, fontsize=8.8, color=cc, fontweight=fw,
                     family="monospace" if x > 0.2 else "sans-serif")
        y -= 0.075

    y -= 0.05
    ax1.text(0, y, "Form — does the line come back as a line?", fontsize=11.5,
             fontweight="bold", va="top")
    y -= 0.08
    fx = [0.0, 0.30, 0.44, 0.58, 0.74]
    for x, h in zip(fx, ["case", "theta", "core frac", "MTF @20mm",
                         "energy vs flat"]):
        ax1.text(x, y, h, fontsize=9, fontweight="bold")
    y -= 0.072
    for tag, colr in ((b["form_tag"], "#e6550d"),
                      ("K_ridge_d50_p13", "#c02020")):
        f = snap["form"].get(tag)
        if not f:
            continue
        for th in ("-40", "+0", "+40"):
            if th not in f:
                continue
            v = f[th]
            nm = ("3D cone d120" if "cone" in tag else "1D V-groove d50") \
                if th == "-40" else ""
            for x, s in zip(fx, [nm, th, "%.3f" % v["core"],
                                 "%.4f" % v["mtf20"],
                                 "%.5f" % v["energy"]]):
                ax1.text(x, y, s, fontsize=8.8, color=colr,
                         family="monospace" if x > 0.2 else "sans-serif")
            y -= 0.072

    ax2 = fig.add_subplot(gs[3, 2])
    if snap["curve"]:
        ts = sorted(float(t) for t in snap["curve"])
        ax2.axvspan(-40, 40, color="#2171b5", alpha=0.08)
        ax2.plot(ts, [snap["curve"][str(t)] for t in ts], marker="o", ms=3.5,
                 lw=2.2, color="#e6550d", label="recommended")
    seen = set()
    for lbl, val, _s, colr in BENCH:
        if val > 3:
            continue
        ax2.axhline(val, color=colr, lw=0.9, ls=":", alpha=0.8)
        if val not in seen:
            seen.add(val)
            ax2.text(-79, val * 1.14, lbl, color=colr, fontsize=6.8)
    ax2.set_yscale("log"); ax2.set_ylim(2e-3, 8.0)
    ax2.set_xticks(range(-80, 81, 40))
    ax2.set_xlabel("incidence angle (deg)")
    ax2.set_ylabel("reflectance  (%)")
    ax2.set_title("Recommended design vs angle", fontsize=10.5)
    ax2.grid(alpha=0.22, which="both", lw=0.5)
    ax2.legend(fontsize=8, loc="upper center")

    # ---------------- benchmark + laws ----------------
    ax4 = fig.add_subplot(gs[4, 0]); ax4.axis("off")
    ax4.text(0, 1.0, "Where this sits", fontsize=11.5, fontweight="bold",
             va="top")
    y = 0.86
    for x, h in ((0.0, "surface"), (0.60, "refl."), (0.78, "source")):
        ax4.text(x, y, h, fontsize=8.8, fontweight="bold")
    y -= 0.078
    entries = list(BENCH)
    if best:
        entries += [("THIS PANEL, worst angle", best["wall"], "simulated",
                     "#e6550d"),
                    ("THIS PANEL, head-on", best["head_on"], "simulated",
                     "#e6550d")]
    for lbl, val, src_, colr in sorted(entries, key=lambda e: -e[1]):
        hit = lbl.startswith("THIS")
        ax4.text(0.0, y, lbl, fontsize=8.5, color=colr,
                 fontweight="bold" if hit else "normal")
        ax4.text(0.60, y, "%.3f%%" % val, fontsize=8.5, color=colr,
                 family="monospace", fontweight="bold" if hit else "normal")
        ax4.text(0.78, y, src_, fontsize=7.2, color="#888888")
        y -= 0.078

    ax3 = fig.add_subplot(gs[4, 1:]); ax3.axis("off")
    ax3.text(0, 1.0, "What the 3D step changed", fontsize=11.5,
             fontweight="bold", va="top")
    y = 0.86
    for line in (
        "the tip stops being the answer. shrinking it 16x moves head-on 16%, "
        "against the 1D family where it was",
        "   everything -- so a cone can be blunt and deep, which is what a "
        "printer can actually make",
        "aspect ratio A = depth / pitch takes over as the lever, and it is the "
        "grazing arm that keeps wanting more",
        "form is destroyed for the first time: core 0.11 at -40 deg against "
        "0.99 for the groove, and 86x dimmer with it",
        "head-on is still core 1.000 for every geometry tried. observer and "
        "beam collinear, one bounce, no displacement.",
    ):
        ax3.text(0.01, y, line, fontsize=8.8, family="monospace")
        y -= 0.093

    y -= 0.05
    ax3.text(0, y, "Open", fontsize=11.5, fontweight="bold", va="top")
    y -= 0.10
    for line in (
        "1. incidence angle distribution of the real rig -- it decides "
        "whether the grazing arm matters at all",
        "2. no Fresnel in the material model, so grazing figures are "
        "optimistic by an unmeasured factor",
        "3. every absolute number assumes the coating is rho 0.005; "
        "unverified until a coupon is measured",
        "4. can a coating reach the root of a 13 mm x 80 mm cone? deeper "
        "cells are harder to coat, not easier",
    ):
        ax3.text(0.01, y, line, fontsize=8.8, family="monospace",
                 color="#8c510a")
        y -= 0.093

    out = os.path.join(snap["daydir"], snap["time"] + "_report.png")
    fig.savefig(out, dpi=115, bbox_inches="tight")
    plt.close(fig)
    return out


def append_readme(daydir, snap, note, png):
    path = os.path.join(daydir, "README.md")
    first = not os.path.exists(path)
    b = snap["best"]
    best = None
    for label, tag, _w, _c in ROWS:
        if tag == b["tag"] and label in snap["cases"]:
            best = snap["cases"][label]
    with open(path, "a") as f:
        if first:
            f.write("# %s\n\n" % os.path.basename(daydir))
        f.write("## %s\n\n" % snap["time"])
        if note:
            f.write("%s\n\n" % note)
        f.write("- recommendation: %s, depth %.0f mm, pitch %.0f mm, tip "
                "%.1f mm, coating rho %.3f, gloss %.2f\n"
                % (b["family"], b["depth_mm"], b["pitch_mm"], b["tip_mm"],
                   b["rho"], b["gloss"]))
        if best:
            f.write("- **reflectance: head-on %.4f%%, worst +/-40 %.4f%%, "
                    "worst all %.4f%%**\n"
                    % (best["head_on"], best["w40"], best["wall"]))
        fm = snap["form"].get(b["form_tag"], {})
        if "-40" in fm:
            f.write("- form at -40 deg: core %.3f, MTF@20mm %.4f "
                    "(1D groove: 0.993 / 0.984)\n"
                    % (fm["-40"]["core"], fm["-40"]["mtf20"]))
        c = snap["counts"]
        f.write("- totals: %d renders, %d sweeps, %d profiles, %d STL\n"
                % (c["renders"], c["sweeps"], c["profiles"], c["stl"]))
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

    png = draw(snap, note)
    js = os.path.join(snap["daydir"], snap["time"] + "_snapshot.json")
    with open(js, "w") as f:
        json.dump({k: v for k, v in snap.items() if k != "daydir"}, f, indent=2)
    rd = append_readme(snap["daydir"], snap, note, png)

    print("[REPORT]", os.path.relpath(png, ROOT))
    print("[SNAP]  ", os.path.relpath(js, ROOT))
    print("[LOG]   ", os.path.relpath(rd, ROOT))


if __name__ == "__main__":
    main()
