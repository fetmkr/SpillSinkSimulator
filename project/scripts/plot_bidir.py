"""The angle-in / angle-out map, drawn.

    python3 scripts/plot_bidir.py [results/sweep_bidir_*.csv ...]

x is the incidence angle, y is the observation angle, colour is the BRDF in
1/sr on a log scale -- the range runs from a structured panel's floor to a flat
plate's specular ridge and a linear scale shows one of them.

THREE LINES ARE DRAWN ON EVERY FIGURE, in the way `analyze.py` draws its
flat-plate 1.000 and box-cavity 0.2356 on every one of its own: a map without
them is a pretty gradient, and with them it answers the question.

    y = +x    RETRO -- straight back at the projector
    y = -x    the flat-mirror specular direction
    y =  0    THE AUDIENCE

Given several CSVs, one colour scale is used for all of them, because the point
of putting two designs side by side is to compare them and a per-figure
normalisation quietly forbids that.

The numbers under the picture are printed too, and they come from the CSV, not
from the image.
"""

from __future__ import annotations

import csv
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.colors import LogNorm                            # noqa: E402
import numpy as np                                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")

BAND = 40.0                 # the working band the study scores in


def load(path):
    """CSV -> (ins, outs, matrix, meta). Missing cells stay NaN and are drawn
    as holes rather than interpolated: a resumed sweep that died halfway must
    look unfinished."""
    rows = list(csv.DictReader(open(path)))
    if not rows:
        raise SystemExit("%s has no rows" % path)
    ins = sorted({float(r["theta_in"]) for r in rows})
    outs = sorted({float(r["theta_out"]) for r in rows})
    ix = {v: i for i, v in enumerate(ins)}
    ox = {v: i for i, v in enumerate(outs)}
    m = np.full((len(outs), len(ins)), np.nan)
    for r in rows:
        try:
            m[ox[float(r["theta_out"])], ix[float(r["theta_in"])]] = \
                float(r["brdf"])
        except (KeyError, ValueError):
            continue
    last = rows[-1]
    meta = {k: last.get(k, "") for k in
            ("tag", "family", "topology", "material", "rho0", "diffuse_frac",
             "roughness", "sun_angle_deg", "mm_per_px", "samples",
             "margin_depths")}
    meta["cells"] = int(np.isfinite(m).sum())
    meta["want"] = m.size
    meta["worst_control"] = max(
        (float(r.get("control_dev") or 0.0) for r in rows), default=0.0)
    return ins, outs, m, meta


def summarise(ins, outs, m, meta):
    """What the picture shows, as numbers. Printed and returned for a caption."""
    o = np.asarray(outs)
    lines = []
    audience = m[int(np.argmin(np.abs(o))), :]
    fin = m[np.isfinite(m)]
    lines.append("peak %.5g /sr   audience row max %.5g /sr   floor %.3g /sr"
                 % (np.nanmax(m), np.nanmax(audience), np.nanmin(fin)))
    band = [i for i, t in enumerate(ins) if abs(t) <= BAND]
    if band:
        lines.append("within the +-%.0f deg band: peak %.5g /sr, audience "
                     "max %.5g /sr" % (BAND, np.nanmax(m[:, band]),
                                       np.nanmax(audience[band])))
    off = []
    for j, ti in enumerate(ins):
        col = m[:, j]
        if not np.isfinite(col).any():
            continue
        off.append(o[int(np.nanargmax(col))] - (-ti))
    if off:
        lines.append("brightest exit angle vs the mirror direction: median "
                     "offset %+.1f deg, worst %+.1f deg"
                     % (float(np.median(off)),
                        max(off, key=abs)))
    if meta["cells"] < meta["want"]:
        lines.append("INCOMPLETE: %d of %d cells measured"
                     % (meta["cells"], meta["want"]))
    if meta["worst_control"] > 0.02:
        lines.append("CONTROL DRIFT: worst cell %.2f %% -- tilt, window or "
                     "margin suspect" % (100 * meta["worst_control"]))
    return lines


def draw(ax, ins, outs, m, meta, norm):
    xs = np.asarray(ins, dtype=float)
    ys = np.asarray(outs, dtype=float)

    def edges(v):
        d = np.diff(v)
        step = d[0] if len(d) else 1.0
        return np.concatenate(([v[0] - step / 2], v[:-1] + d / 2,
                               [v[-1] + step / 2]))

    pc = ax.pcolormesh(edges(xs), edges(ys), np.ma.masked_invalid(m),
                       cmap="inferno", norm=norm, shading="flat")
    lo, hi = xs[0], xs[-1]
    ax.axhspan(-BAND, BAND, color="w", alpha=0.06, zorder=1)
    ax.axvspan(-BAND, BAND, color="w", alpha=0.06, zorder=1)
    ax.plot([lo, hi], [lo, hi], color="#49c2ca", lw=1.0, ls="--",
            zorder=3, label="retro  (back at the projector)")
    ax.plot([lo, hi], [-lo, -hi], color="#e08a2e", lw=1.0, ls="--",
            zorder=3, label="flat-mirror specular")
    ax.axhline(0.0, color="#8b6fd8", lw=1.0, zorder=3, label="the audience")
    ax.set_xlabel("incidence  theta_in  (deg)")
    ax.set_ylabel("observation  theta_out  (deg)")
    ax.set_title("%s  ·  %s %s" % (meta["tag"], meta["topology"],
                                   meta["material"]), fontsize=10)
    ax.set_aspect("equal")
    ax.set_xticks(range(-80, 81, 20))
    ax.set_yticks(range(-80, 81, 20))
    return pc


def main():
    paths = sys.argv[1:]
    if not paths:
        import glob
        paths = sorted(glob.glob(os.path.join(RESULTS, "sweep_bidir_*.csv")))
    if not paths:
        raise SystemExit("no sweep_bidir_*.csv in results/")

    loaded = [load(p) for p in paths]
    fin = np.concatenate([m[np.isfinite(m)].ravel() for _, _, m, _ in loaded])
    fin = fin[fin > 0]
    if not fin.size:
        raise SystemExit("every cell is zero or missing")
    # one scale for all panels: comparing two designs is the point
    norm = LogNorm(vmin=max(fin.min(), fin.max() * 1e-6), vmax=fin.max())

    n = len(loaded)
    fig, axes = plt.subplots(1, n, figsize=(1 + 4.6 * n, 5.2), squeeze=False)
    pc = None
    for ax, (ins, outs, m, meta) in zip(axes[0], loaded):
        pc = draw(ax, ins, outs, m, meta, norm)
    cb = fig.colorbar(pc, ax=axes[0].tolist(), fraction=0.035, pad=0.02)
    cb.set_label("BRDF  f_r  (1/sr)")
    # legend BELOW the axes: in the top-left corner it covers the grazing
    # corner of the map, which on a flat plate is the brightest thing on it
    h, lb = axes[0][0].get_legend_handles_labels()
    fig.legend(h, lb, loc="lower center", ncol=3, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, -0.02))

    out = os.path.join(RESULTS, "bidir_%s.png"
                       % "_vs_".join(d[3]["tag"] for d in loaded))
    fig.savefig(out, dpi=140, bbox_inches="tight")
    print("wrote %s" % out)

    for path, (ins, outs, m, meta) in zip(paths, loaded):
        print("\n%s" % os.path.basename(path))
        print("   %s %s  ·  rho0 %s  diffuse_frac %s  roughness %s"
              % (meta["family"], meta["topology"], meta["rho0"],
                 meta["diffuse_frac"], meta["roughness"]))
        print("   sun %s deg  ·  %s mm/px  ·  %s spp  ·  margin %s depths"
              % (meta["sun_angle_deg"], meta["mm_per_px"], meta["samples"],
                 meta["margin_depths"]))
        for line in summarise(ins, outs, m, meta):
            print("   %s" % line)


if __name__ == "__main__":
    main()
