"""
Turn a sweep CSV into the axis that decides the design.

    python3 scripts/analyze.py results/sweep_*.csv

Axis 1  brightness      total reflected fraction vs the flat control, per
                        incidence angle (hemi_view / reciprocity)
Axis 2  form destruction  judged from PNGs side by side, not from here

Reference lines used throughout:
    1.000  flat plate, i.e. the panel is doing nothing
    0.236  open box cavity with aperture fraction 1/6, measured in
           scripts/validate.py -- the bar a real cavity has to beat
"""

from __future__ import annotations

import os
import sys
import csv
import glob
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

BOX_CAVITY = 0.2356

NUMERIC = ("theta", "ratio_vs_flat", "panel_mean", "control_mean",
           "panel_p99", "panel_max", "spec_roughness", "depth_mm",
           "slat_len_mm", "slat_deg", "slat_zone_depth_mm",
           "chamber_depth_mm", "slat_overlap", "pitch_mean_mm",
           "open_face_fraction", "chamber_aperture_fraction", "flare_mm",
           "chamfer_mm", "baffle_rows", "baffle_count", "baffle_len_mm")


def load(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in NUMERIC:
            if k in r:
                r[k] = float(r[k])
    return rows


def group_by_sweep(rows):
    """Recover which sweep each tag came from via its output directory."""
    g = defaultdict(list)
    for r in rows:
        sub = os.path.basename(os.path.dirname(r["png"]))
        g[sub].append(r)
    return g


def curves(rows):
    by = defaultdict(list)
    for r in rows:
        if r["mode"] == "hemi_view":
            by[r["tag"]].append(r)
    for tag in by:
        by[tag].sort(key=lambda r: r["theta"])
    return by


def plot_group(name, rows, out):
    by = curves(rows)
    if not by:
        return
    fig, ax = plt.subplots(figsize=(11, 6.4))
    for tag in sorted(by):
        rs = by[tag]
        ax.plot([r["theta"] for r in rs], [r["ratio_vs_flat"] for r in rs],
                marker="o", ms=3.5, lw=1.5, label=tag)

    ax.axhline(1.0, color="#c02020", lw=1.0, ls="--")
    ax.text(-79, 1.02, "flat plate — panel doing nothing", color="#c02020",
            fontsize=8)
    ax.axhline(BOX_CAVITY, color="#2060c0", lw=1.0, ls=":")
    ax.text(-79, BOX_CAVITY * 1.06, f"open box cavity ({BOX_CAVITY:.3f})",
            color="#2060c0", fontsize=8)
    ax.axvline(0.0, color="#888888", lw=0.6)

    ax.set_yscale("log")
    ax.set_ylim(1e-3, 1.6)
    ax.set_xlabel("incidence angle from panel normal (deg)   "
                  "negative = laser arriving from BELOW")
    ax.set_ylabel("total reflected fraction / flat plate   (log, lower better)")
    ax.set_title(f"{name} — reciprocity measurement (hemi_view)")
    ax.set_xticks(range(-80, 81, 20))
    ax.grid(alpha=0.25, lw=0.5, which="both")
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print("  wrote", os.path.relpath(out, ROOT))


def band(rs, lo, hi):
    v = [r["ratio_vs_flat"] for r in rs if lo <= r["theta"] <= hi]
    return sum(v) / len(v) if v else float("nan")


def summarise(name, rows):
    by = curves(rows)
    print(f"\n=== {name} ===")
    print(f"{'tag':<16} {'best':>14} {'@0deg':>8} {'mean+':>8} {'mean-':>8} "
          f"{'worst':>14}  {'usable band':>13}")
    for tag in sorted(by):
        rs = by[tag]
        best = min(rs, key=lambda r: r["ratio_vs_flat"])
        worst = max(rs, key=lambda r: r["ratio_vs_flat"])
        at0 = next(r["ratio_vs_flat"] for r in rs if r["theta"] == 0)
        # widest contiguous run of angles that beats the open box cavity
        good = [r["theta"] for r in rs if r["ratio_vs_flat"] < BOX_CAVITY]
        if good:
            runs, cur = [], [good[0]]
            for t in good[1:]:
                if t - cur[-1] <= 10:
                    cur.append(t)
                else:
                    runs.append(cur)
                    cur = [t]
            runs.append(cur)
            longest = max(runs, key=len)
            bandtxt = f"{longest[0]:+.0f}..{longest[-1]:+.0f} ({len(longest)*10-10:.0f}d)"
        else:
            bandtxt = "none"
        print(f"{tag:<16} {best['ratio_vs_flat']:>8.4f}@{best['theta']:+04.0f} "
              f"{at0:>8.4f} {band(rs, 0, 80):>8.4f} {band(rs, -80, 0):>8.4f} "
              f"{worst['ratio_vs_flat']:>8.4f}@{worst['theta']:+04.0f}  "
              f"{bandtxt:>13}")


def main():
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(RESULTS, "sweep_*.csv")))
    rows = []
    for p in paths:
        rows += load(p)
    print(f"{len(rows)} rows from {len(paths)} file(s)")

    for name, rs in sorted(group_by_sweep(rows).items()):
        summarise(name, rs)
        plot_group(name, rs, os.path.join(RESULTS, f"angle_{name}.png"))


if __name__ == "__main__":
    main()
