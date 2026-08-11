"""
One page showing why depth 30 / pitch 13 wins inside +/-40 degrees, and what
it costs outside that band.

    python3 scripts/plot_pitch_choice.py

Reads results/sweep_fdm.csv (ridge family, tip pinned at 0.4 mm for a 0.4 mm
nozzle, plus one unprintable 0.04 mm reference).

The whole point of putting these on one sheet is that the ranking flips
depending on which angles are counted. Any single number would hide that.
"""

from __future__ import annotations

import os
import csv
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

PITCHES = [3.0, 5.0, 8.0, 13.0, 20.0]
COL = {3.0: "#8c2d04", 5.0: "#d94801", 8.0: "#f16913",
       13.0: "#2171b5", 20.0: "#6a51a3"}


def load():
    rows = list(csv.DictReader(open(os.path.join(RESULTS, "sweep_fdm.csv"))))
    cur = defaultdict(dict)
    for r in rows:
        if r["mode"] != "hemi_view":
            continue
        key = (float(r["depth_mm"]), float(r["pitch_mm"]),
               float(r["tip_width_mm"]))
        cur[key][float(r["theta"])] = float(r["ratio_vs_flat"])
    return cur


def worst(d, lo, hi):
    return max(v for t, v in d.items() if lo <= t <= hi)


def main():
    cur = load()
    fig = plt.figure(figsize=(15.5, 9.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 1.0], hspace=0.34,
                          wspace=0.28)

    # ---- top left: the angle curves at depth 30 --------------------------
    ax = fig.add_subplot(gs[0, :2])
    ax.axvspan(-40, 40, color="#2171b5", alpha=0.07, zorder=0)
    ax.text(0, 1.35, "the band this choice is made in", ha="center",
            fontsize=9, color="#2171b5")
    for p in PITCHES:
        k = (30.0, p, 0.4)
        if k not in cur:
            continue
        d = cur[k]
        ts = sorted(d)
        lw = 2.6 if p == 13.0 else 1.3
        ax.plot(ts, [d[t] for t in ts], marker="o", ms=3.5, lw=lw,
                color=COL[p], label=f"pitch {p:.0f} mm   (A = {30/p:.1f})",
                zorder=5 if p == 13.0 else 3)
    k = (30.0, 4.0, 0.04)
    if k in cur:
        d = cur[k]
        ts = sorted(d)
        ax.plot(ts, [d[t] for t in ts], lw=1.6, ls="--", color="#444444",
                label="pitch 4, tip 0.04 mm (not printable)")

    ax.set_yscale("log")
    ax.set_ylim(8e-4, 2.0)
    ax.axhline(1.0, color="#c02020", lw=1.0, ls=":")
    ax.text(-79, 1.08, "plain black wall", color="#c02020", fontsize=8)
    ax.set_xticks(range(-80, 81, 20))
    ax.set_xlabel("incidence angle from the panel normal (deg)")
    ax.set_ylabel("return / plain wall   (log)")
    ax.set_title("Depth 30 mm, 0.4 mm tip — return against incidence angle",
                 fontsize=11)
    ax.grid(alpha=0.25, which="both", lw=0.5)
    ax.legend(fontsize=8.5, loc="lower left")

    # ---- top right: worst inside +/-40, per pitch, per depth -------------
    ax2 = fig.add_subplot(gs[0, 2])
    for depth, mk, c in ((30.0, "o", "#2171b5"), (50.0, "s", "#41ab5d"),
                         (80.0, "^", "#807dba")):
        xs, ys = [], []
        for p in PITCHES:
            k = (depth, p, 0.4)
            if k in cur:
                xs.append(p)
                ys.append(worst(cur[k], -40, 40))
        ax2.plot(xs, ys, marker=mk, color=c, lw=1.6, ms=6,
                 label=f"depth {depth:.0f} mm")
    k = (30.0, 13.0, 0.4)
    ax2.plot([13.0], [worst(cur[k], -40, 40)], marker="o", ms=15, mfc="none",
             mec="#e6550d", mew=2.4, zorder=6)
    ax2.annotate("best inside\n+/-40 deg", (13.0, worst(cur[k], -40, 40)),
                 textcoords="offset points", xytext=(6, 26), fontsize=9,
                 color="#e6550d", ha="center")
    ax2.set_yscale("log")
    ax2.set_xlabel("pitch (mm)")
    ax2.set_ylabel("worst return inside +/-40 deg")
    ax2.set_title("Inside the band: pitch 13 is the minimum", fontsize=10.5)
    ax2.grid(alpha=0.25, which="both", lw=0.5)
    ax2.legend(fontsize=8.5)

    # ---- bottom left: the same, but counting every angle ------------------
    ax3 = fig.add_subplot(gs[1, 0])
    for depth, mk, c in ((30.0, "o", "#2171b5"), (50.0, "s", "#41ab5d"),
                         (80.0, "^", "#807dba")):
        xs, ys = [], []
        for p in PITCHES:
            k = (depth, p, 0.4)
            if k in cur:
                xs.append(p)
                ys.append(worst(cur[k], -90, 90))
        ax3.plot(xs, ys, marker=mk, color=c, lw=1.6, ms=6,
                 label=f"depth {depth:.0f}")
    k = (30.0, 13.0, 0.4)
    ax3.plot([13.0], [worst(cur[k], -90, 90)], marker="o", ms=15, mfc="none",
             mec="#c02020", mew=2.4, zorder=6)
    ax3.annotate("same design,\nnow the worst", (13.0, worst(cur[k], -90, 90)),
                 textcoords="offset points", xytext=(-2, -42), fontsize=9,
                 color="#c02020", ha="center")
    ax3.set_yscale("log")
    ax3.set_xlabel("pitch (mm)")
    ax3.set_ylabel("worst return, all angles")
    ax3.set_title("Counting +/-80 deg too: the ranking inverts", fontsize=10.5)
    ax3.grid(alpha=0.25, which="both", lw=0.5)
    ax3.legend(fontsize=8.5)

    # ---- bottom middle: the trade-off plane ------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    for depth, mk, c in ((30.0, "o", "#2171b5"), (50.0, "s", "#41ab5d"),
                         (80.0, "^", "#807dba")):
        for p in PITCHES:
            k = (depth, p, 0.4)
            if k not in cur:
                continue
            x, y = worst(cur[k], -40, 40), worst(cur[k], -90, 90)
            ax4.scatter([x], [y], marker=mk, s=52, color=c, zorder=4)
            ax4.annotate(f"{p:.0f}", (x, y), textcoords="offset points",
                         xytext=(6, -3), fontsize=7.5, color=c)
    k = (30.0, 13.0, 0.4)
    ax4.scatter([worst(cur[k], -40, 40)], [worst(cur[k], -90, 90)], s=210,
                facecolors="none", edgecolors="#e6550d", linewidths=2.2,
                zorder=5)
    ax4.set_xscale("log")
    ax4.set_yscale("log")
    ax4.set_xlabel("worst inside +/-40 deg   (lower better ->)")
    ax4.set_ylabel("worst all angles")
    ax4.set_title("No design wins both axes", fontsize=10.5)
    ax4.grid(alpha=0.25, which="both", lw=0.5)

    # ---- bottom right: the numbers ---------------------------------------
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis("off")
    ax5.text(0, 1.0, "depth 30 mm, tip 0.4 mm", fontsize=10.5,
             fontweight="bold", va="top")
    y = 0.90
    ax5.text(0.0, y, "pitch", fontsize=9, fontweight="bold")
    ax5.text(0.22, y, "A", fontsize=9, fontweight="bold")
    ax5.text(0.36, y, "tip%", fontsize=9, fontweight="bold")
    ax5.text(0.56, y, "+/-40", fontsize=9, fontweight="bold")
    ax5.text(0.80, y, "all", fontsize=9, fontweight="bold")
    y -= 0.085
    for p in PITCHES:
        k = (30.0, p, 0.4)
        if k not in cur:
            continue
        w40, wall = worst(cur[k], -40, 40), worst(cur[k], -90, 90)
        hi = (p == 13.0)
        c = "#e6550d" if hi else "#333333"
        fw = "bold" if hi else "normal"
        ax5.text(0.0, y, f"{p:.0f} mm", fontsize=9, color=c, fontweight=fw)
        ax5.text(0.22, y, f"{30/p:.1f}", fontsize=9, color=c, fontweight=fw)
        ax5.text(0.36, y, f"{0.4/p*100:.1f}%", fontsize=9, color=c, fontweight=fw)
        ax5.text(0.56, y, f"{w40:.4f}", fontsize=9, color=c, fontweight=fw,
                 family="monospace")
        ax5.text(0.80, y, f"{wall:.4f}", fontsize=9, color=c, fontweight=fw,
                 family="monospace")
        y -= 0.085
    y -= 0.05
    ax5.text(0.0, y, "why it flips", fontsize=10, fontweight="bold")
    y -= 0.075
    for line in (
            "coarse pitch  -> small tip fraction",
            "              -> good head-on",
            "coarse pitch  -> low aspect ratio A",
            "              -> few bounces",
            "              -> bad at grazing",
            "",
            "so the answer depends entirely on",
            "which incidence angles the rig",
            "actually puts on the wall."):
        ax5.text(0.02, y, line, fontsize=8.6, family="monospace")
        y -= 0.062

    fig.suptitle("Choosing the pitch — ridge panel, 0.4 mm printable tip, "
                 "return measured against a plain wall of the same coating",
                 fontsize=12.5)
    out = os.path.join(RESULTS, "pitch_choice.png")
    fig.savefig(out, dpi=125, bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main()
