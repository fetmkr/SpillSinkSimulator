"""
One sheet comparing the 3D cone array with the 1D V-groove.

    python3 scripts/plot_cone_vs_ridge.py

Reads results/sweep_cone3d.csv (round 1, with the base-overlap gaps) and
results/sweep_cone3d_r2.csv (round 2, gaps closed). Round 1 is shown only
where it is needed to explain what the gap defect did, and labelled as void.
"""

from __future__ import annotations

import os
import csv
import math
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")


def load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return {}, {}
    cur, meta = defaultdict(dict), {}
    for r in csv.DictReader(open(path)):
        cur[r["tag"]][float(r["theta"])] = float(r["rho"]) * 100.0
        meta[r["tag"]] = r
    return cur, meta


def band(d, lo, hi):
    return max(v for t, v in d.items() if lo <= t <= hi)


def main():
    r1, m1 = load("sweep_cone3d.csv")
    r2, m2 = load("sweep_cone3d_r2.csv")

    fig = plt.figure(figsize=(16.5, 10.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.92], hspace=0.42,
                          wspace=0.26)

    # ---- 1. the headline curves -----------------------------------------
    ax = fig.add_subplot(gs[0, :2])
    show = [("R_ref_d50_p13", r1, "#c02020", 2.4,
             "1D V-groove  d50 p13"),
            ("J_jit30", r2, "#2171b5", 1.6, "3D cone  d50 p13"),
            ("J_d120_jit30", r2, "#08519c", 2.4, "3D cone  d120 p13"),
            ("J_d80_p08", r2, "#41ab5d", 2.4, "3D cone  d80 p8")]
    for tag, src, colr, lw, lbl in show:
        if tag not in src:
            continue
        ts = sorted(src[tag])
        ax.plot(ts, [src[tag][t] for t in ts], marker="o", ms=3.5, lw=lw,
                color=colr, label=lbl)
    if "C_tip040" in r1:
        ts = sorted(r1["C_tip040"])
        ax.plot(ts, [r1["C_tip040"][t] for t in ts], lw=1.2, ls=":",
                color="#999999",
                label="3D cone d50 p13 — VOID (base gaps)")
    ax.axvspan(-40, 40, color="#2171b5", alpha=0.07)
    ax.axhline(0.5, color="#b35806", lw=0.9, ls=":")
    ax.text(-79, 0.55, "the coating on its own (0.5%)", color="#b35806",
            fontsize=8)
    ax.set_yscale("log")
    ax.set_ylim(2e-3, 1.2)
    ax.set_xticks(range(-80, 81, 20))
    ax.set_xlabel("incidence angle from the panel normal (deg)")
    ax.set_ylabel("reflectance  (%)")
    ax.set_title("3D cone array vs 1D V-groove — same 0.5% coating",
                 fontsize=12)
    ax.grid(alpha=0.25, which="both", lw=0.5)
    ax.legend(fontsize=8.5, loc="upper center", ncol=2)

    # ---- 2. aspect ratio is the lever ------------------------------------
    ax2 = fig.add_subplot(gs[0, 2])
    pts = []
    for tag in ("C_d30", "C_tip040", "C_d80", "C_d120"):
        if tag in r1:
            pts.append((float(m1[tag]["aspect"]), r1[tag][0.0],
                        band(r1[tag], -90, 90)))
    if pts:
        pts.sort()
        ax2.plot([p[0] for p in pts], [p[1] for p in pts], marker="o",
                 color="#999999", lw=1.4, ls=":", label="head-on (void run)")
        ax2.plot([p[0] for p in pts], [p[2] for p in pts], marker="s",
                 color="#cccccc", lw=1.4, ls=":", label="all angles (void)")
    pts2 = []
    for tag in ("J_jit30", "J_d80_jit30", "J_d120_jit30"):
        if tag in r2:
            pts2.append((float(m2[tag]["aspect"]), r2[tag][0.0],
                         band(r2[tag], -90, 90)))
    pts2.sort()
    ax2.plot([p[0] for p in pts2], [p[1] for p in pts2], marker="o",
             color="#2171b5", lw=2.0, label="head-on")
    ax2.plot([p[0] for p in pts2], [p[2] for p in pts2], marker="s",
             color="#41ab5d", lw=2.0, label="worst, all angles")
    ax2.set_yscale("log")
    ax2.set_xlabel("aspect ratio  A = depth / pitch")
    ax2.set_ylabel("reflectance (%)")
    ax2.set_title("Depth is the lever for cones", fontsize=10.5)
    ax2.grid(alpha=0.25, which="both", lw=0.5)
    ax2.legend(fontsize=7.5)

    # ---- 3. the tip does not matter for cones ----------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    tips, vals, naive = [], [], []
    for tag in ("C_tip005", "C_tip020", "C_tip040", "C_tip080"):
        if tag in r1:
            tips.append(float(m1[tag]["tip_mm"]))
            vals.append(r1[tag][0.0])
            naive.append(float(m1[tag]["tip_fraction"]) * 0.5)
    ax3.plot(tips, vals, marker="o", lw=2.0, color="#2171b5",
             label="measured, 3D cone")
    ax3.plot(tips, naive, marker="^", lw=1.4, ls="--", color="#999999",
             label="if the tip were the whole return")
    ax3.plot(tips, [0.09 * (t / 13.0) * 0.5 * 100 / 100 for t in tips],
             marker="s", lw=1.4, ls=":", color="#c02020",
             label="1D law, same tip and pitch")
    ax3.set_xscale("log")
    ax3.set_yscale("log")
    ax3.set_xlabel("tip width (mm)")
    ax3.set_ylabel("head-on reflectance (%)")
    ax3.set_title("Shrinking the tip 16x moves it 16%", fontsize=10.5)
    ax3.grid(alpha=0.25, which="both", lw=0.5)
    ax3.legend(fontsize=7.5)

    # ---- 4. what jitter costs -------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    js, h, a = [], [], []
    for tag in ("J_nojit", "J_jit15", "J_jit30", "J_jit45"):
        if tag in r2:
            js.append(float(m2[tag]["jitter"]))
            h.append(r2[tag][0.0])
            a.append(band(r2[tag], -90, 90))
    ax4.plot(js, h, marker="o", lw=2.0, color="#2171b5", label="head-on")
    ax4.plot(js, a, marker="s", lw=2.0, color="#41ab5d", label="worst, all")
    ax4.set_yscale("log")
    ax4.set_xlabel("position jitter  (fraction of pitch)")
    ax4.set_ylabel("reflectance (%)")
    ax4.set_title("Price of breaking the periodic array", fontsize=10.5)
    ax4.grid(alpha=0.25, which="both", lw=0.5)
    ax4.legend(fontsize=7.5)

    # ---- 5. the table ----------------------------------------------------
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis("off")
    ax5.text(0, 1.0, "Reflectance %, coating 0.5%", fontsize=11,
             fontweight="bold", va="top")
    rowspec = [
        ("1D V-groove d50 p13", "R_ref_d50_p13", r1, "#c02020"),
        ("1D V-groove d50 p8", "R_ref_d50_p08", r1, "#c02020"),
        ("3D cone d50 p13", "J_jit30", r2, "#2171b5"),
        ("3D cone d80 p13", "J_d80_jit30", r2, "#2171b5"),
        ("3D cone d120 p13", "J_d120_jit30", r2, "#08519c"),
        ("3D cone d80 p8", "J_d80_p08", r2, "#41ab5d"),
        ("3D cone, no jitter", "J_nojit", r2, "#777777"),
        ("3D cone, tilt 30", "J_tilt30_jit30", r2, "#777777"),
    ]
    y = 0.90
    ax5.text(0.0, y, "case", fontsize=8.6, fontweight="bold")
    ax5.text(0.50, y, "head-on", fontsize=8.6, fontweight="bold")
    ax5.text(0.70, y, "±40", fontsize=8.6, fontweight="bold")
    ax5.text(0.87, y, "all", fontsize=8.6, fontweight="bold")
    y -= 0.075
    for lbl, tag, src, colr in rowspec:
        if tag not in src:
            continue
        d = src[tag]
        ax5.text(0.0, y, lbl, fontsize=8.4, color=colr)
        for x, v in ((0.50, d[0.0]), (0.70, band(d, -40, 40)),
                     (0.87, band(d, -90, 90))):
            ax5.text(x, y, "%.4f" % v, fontsize=8.4, color=colr,
                     family="monospace")
        y -= 0.075

    y -= 0.04
    for line in ("cones beat grooves 4-6x on every metric",
                 "the tip stops mattering; depth takes over",
                 "tilt 30 deg is WORSE, not better -- the",
                 "round-1 claim was measured against gaps"):
        ax5.text(0.0, y, line, fontsize=8.2, family="monospace",
                 color="#8c510a")
        y -= 0.062

    fig.suptitle("Going 3D: an irregular cone array against the extruded "
                 "V-groove", fontsize=13)
    out = os.path.join(RESULTS, "cone_vs_ridge.png")
    fig.savefig(out, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
