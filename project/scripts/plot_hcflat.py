"""The honeycomb search landscape, every panel on ONE colour scale.

    python3 scripts/plot_hcflat.py [--csv results/sweep_hcflat.csv]

Reads `results/sweep_hcflat.csv`, scores it exactly as `sweep_hcflat` does --
worst rho_dh over theta 0/+-20/+-40, then the mean over seeds -- and draws the
landscape as pitch x depth heatmaps, one panel per wall thickness.

GLOBALLY NORMALISED, and that is the whole point of drawing it this way. One
LogNorm and one colourbar across every panel of every figure, so a cell's colour
means the same reflectance wherever it appears. A per-panel normalisation would
make the worst wall thickness look exactly as good as the best, which is the
comparison the figure exists to make.

Reference lines and markers are drawn on every panel, in the way `analyze.py`
draws its flat-plate 1.000 on all of its own:

    aspect (depth/pitch) 4 and 8   the saturation the search is testing for
    the best cell in the WHOLE grid, ringed, so every panel says how far it is
"""

from __future__ import annotations

import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.colors import LogNorm                            # noqa: E402
from matplotlib.ticker import NullFormatter                       # noqa: E402
import numpy as np                                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")


def score(path):
    """{(pitch,depth,wall,frac): (mean worst rho, sem, n_seeds)} -- the
    scoring rule of principles/00 section C, not a second one."""
    per = {}
    for r in csv.DictReader(open(path)):
        if not r.get("rho"):
            continue
        k = (float(r["pitch"]), float(r["depth"]), float(r["wall"]),
             float(r["paint_frac"]), int(r["seed"]))
        per[k] = max(per.get(k, 0.0), float(r["rho"]))
    agg = {}
    for (p, d, w, f, s), v in per.items():
        agg.setdefault((p, d, w, f), []).append(v)
    out = {}
    for k, vs in agg.items():
        m = sum(vs) / len(vs)
        sem = ((sum((x - m) ** 2 for x in vs) / (len(vs) - 1)) ** 0.5
               / len(vs) ** 0.5) if len(vs) > 1 else 0.0
        out[k] = (m, sem, len(vs))
    return out


def _grid(agg, wall, frac):
    sel = {k: v for k, v in agg.items() if k[2] == wall and k[3] == frac}
    if not sel:
        return None, None, None
    ps = sorted({k[0] for k in sel})
    ds = sorted({k[1] for k in sel})
    m = np.full((len(ds), len(ps)), np.nan)
    for (p, d, _w, _f), (v, _s, _n) in sel.items():
        m[ds.index(d), ps.index(p)] = v
    return ps, ds, m


def _edges(v):
    v = np.asarray(v, dtype=float)
    if len(v) == 1:
        return np.array([v[0] * 0.9, v[0] * 1.1])
    lg = np.log10(v)
    mid = (lg[:-1] + lg[1:]) / 2
    return 10 ** np.concatenate(([lg[0] - (mid[0] - lg[0])], mid,
                                 [lg[-1] + (lg[-1] - mid[-1])]))


def draw(agg, frac, norm, best, out):
    walls = sorted({k[2] for k in agg if k[3] == frac})
    if not walls:
        return None
    fig, axes = plt.subplots(1, len(walls), figsize=(2 + 3.4 * len(walls), 4.6),
                             squeeze=False, sharey=True)
    pc = None
    for ax, wl in zip(axes[0], walls):
        ps, ds, m = _grid(agg, wl, frac)
        if ps is None:
            continue
        pc = ax.pcolormesh(_edges(ps), _edges(ds), np.ma.masked_invalid(m),
                           cmap="viridis_r", norm=norm, shading="flat")
        ax.set_xscale("log"); ax.set_yscale("log")
        for a, ls in ((4.0, ":"), (8.0, "--")):
            xs = np.array([min(ps), max(ps)])
            ax.plot(xs, a * xs, color="w", lw=0.9, ls=ls, alpha=0.65)
        if best and best[2] == wl and best[3] == frac:
            ax.plot([best[0]], [best[1]], "o", mfc="none", mec="#ff4d00",
                    mew=2.0, ms=13, zorder=5)
        # A log axis keeps its own minor labels, which collide with the
        # explicit ones -- the first draw printed "3 x 10^0" through "4".
        ax.set_xticks(ps); ax.set_xticklabels(["%g" % p for p in ps], fontsize=7)
        ax.set_yticks(ds); ax.set_yticklabels(["%g" % d for d in ds], fontsize=7)
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.tick_params(axis="both", which="minor", length=0)
        ax.set_xlabel("cell pitch (mm)")
        ax.set_title("wall %.2f mm" % wl, fontsize=10)
    axes[0][0].set_ylabel("cell depth (mm)")
    cb = fig.colorbar(pc, ax=axes[0].tolist(), fraction=0.03, pad=0.02)
    cb.set_label(r"worst $\rho_{dh}$ over $\theta$ 0/$\pm$20/$\pm$40")
    fig.suptitle("Honeycomb front, flat back — Musou to %.0f %% of depth, "
                 "anodised_hi below" % (100 * frac), fontsize=11)
    h = [plt.Line2D([], [], color="k", ls=":", label="aspect 4"),
         plt.Line2D([], [], color="k", ls="--", label="aspect 8"),
         plt.Line2D([], [], marker="o", mfc="none", mec="#ff4d00", ls="",
                    label="best in the whole search")]
    fig.legend(handles=h, loc="lower center", ncol=3, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, -0.03))
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=os.path.join(RESULTS, "sweep_hcflat.csv"))
    a = ap.parse_args()
    agg = score(a.csv)
    if not agg:
        raise SystemExit("no scored rows in %s" % a.csv)

    vals = np.array([v[0] for v in agg.values()])
    # ONE scale for every panel of every figure
    norm = LogNorm(vmin=vals.min(), vmax=vals.max())
    best = min(agg, key=lambda k: agg[k][0])

    made = []
    for frac in sorted({k[3] for k in agg}, reverse=True):
        out = os.path.join(RESULTS, "hcflat_paint%02.0f.png" % (100 * frac))
        if draw(agg, frac, norm, best, out):
            made.append(out)
            print("wrote %s" % out)

    print("\ncolour scale, shared by every panel: %.6f to %.6f"
          % (vals.min(), vals.max()))
    print("\n=== best 20 (worst theta, mean +- SEM over seeds) ===")
    print("  %-6s %-6s %-6s %-6s %-11s %-10s %-7s %-6s %s"
          % ("pitch", "depth", "wall", "paint", "rho_worst", "SEM", "aspect",
             "tip%", "n"))
    for k in sorted(agg, key=lambda k: agg[k][0])[:20]:
        p, d, w, f = k
        m, sem, n = agg[k]
        print("  %-6.2f %-6.1f %-6.2f %-6.0f %-11.6f %-10.6f %-7.1f %-6.2f %d"
              % (p, d, w, 100 * f, m, sem, d / p, 100 * 2 * w / p, n))
    return made


if __name__ == "__main__":
    main()
