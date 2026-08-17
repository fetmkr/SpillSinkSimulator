"""Figure for FINDINGS_kaster.md: why Kaster's cap sets his floor.

    python3 scripts/fig_kaster.py     -> results/fig_kaster.png

Three panels, one per specimen of sweep_kaster.csv, drawn as the TRUE
cross-section through a pyramid apex row (the plane in which +-x face
normals lie, so an in-plane specular ray stays in-plane -- the 2D trace
is exact physics for these rays, not a cartoon). The polyline the rays
reflect off IS the polyline that is drawn: one closed loop per panel,
equal aspect, true angles. Rays are drawn at 15 deg incidence so the
exit path separates from the entry (at 0 deg a flat-land ray retraces
itself and the two lines overlap); the numbers under each panel are the
CYCLES measurements at theta 0 from sweep_kaster.csv, not the 2D trace.

First version of this figure had the u-parameter sign flipped in the
segment intersection, so rays sailed through the solid -- caught by
looking at the picture, which is what the picture is for.
"""

import os
import csv
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "fig_kaster.png")
CSV = os.path.join(ROOT, "results", "sweep_kaster.csv")

PITCH, DEPTH = 4.0, 20.0
RHO = 0.05
THETA_DRAW = 15.0


def profile(tip_flat, n_cells, depth=DEPTH, pitch=PITCH):
    """Closed outline of the apex-row cross-section: tips at y=0, valleys
    at y=-depth, plus the slab underneath. Returns list of (x, y)."""
    pts = []
    half_tip = tip_flat / 2.0
    for i in range(n_cells):
        cx = (i + 0.5) * pitch
        pts.append((i * pitch, -depth))
        if tip_flat > 1e-9:
            pts.append((cx - half_tip, 0.0))
            pts.append((cx + half_tip, 0.0))
        else:
            pts.append((cx, 0.0))
    pts.append((n_cells * pitch, -depth))
    pts.append((n_cells * pitch, -depth - 2.0))
    pts.append((0.0, -depth - 2.0))
    return pts


def cross(ax_, ay, bx, by):
    return ax_ * by - ay * bx


def trace2d(pts, x_hit, theta_deg, max_b=24):
    """Specular 2D walk against the closed polyline.

    Returns (path, n_bounces, escaped). The ray is AIMED so its first
    surface crossing of the y=0 plane happens at x_hit."""
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    th = math.radians(theta_deg)
    d = [math.sin(th), -math.cos(th)]
    o = [x_hit - 26.0 * d[0], 26.0 * -d[1] * 1.0]
    o = [x_hit - 26.0 * d[0], -26.0 * d[1]]          # 26 mm before y=0
    path, nb = [tuple(o)], 0
    for _ in range(max_b):
        best, bt = None, 1e30
        for (a, b) in segs:
            ex, ey = b[0] - a[0], b[1] - a[1]
            den = cross(d[0], d[1], ex, ey)
            if abs(den) < 1e-12:
                continue
            wx, wy = a[0] - o[0], a[1] - o[1]
            t = cross(wx, wy, ex, ey) / den
            u = cross(wx, wy, d[0], d[1]) / den
            if t > 1e-9 and -1e-12 <= u <= 1 + 1e-12 and t < bt:
                bt, best = t, (a, b)
        if best is None:                              # escaped upward
            path.append((o[0] + 34.0 * d[0], o[1] + 34.0 * d[1]))
            return path, nb, True
        o = [o[0] + bt * d[0], o[1] + bt * d[1]]
        path.append(tuple(o))
        nb += 1
        (a, b) = best
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        n = (-ey / L, ex / L)
        dot = d[0] * n[0] + d[1] * n[1]
        d = [d[0] - 2 * dot * n[0], d[1] - 2 * dot * n[1]]
    return path, nb, False                            # trapped


def measured():
    """Cycles numbers from the sweep CSV (r0.30 rows, theta 0)."""
    vals = {}
    for r in csv.DictReader(open(CSV)):
        if r["roughness"] == "0.30" and float(r["theta"]) == 0.0:
            vals[r["tag"].split("_r")[0]] = float(r["rho"])
    return vals


def main():
    m = measured()
    panels = [
        ("flat plate", None,
         "rho %.2f%%  --  the denominator" % (100 * m["K_flat"])),
        ("our pyramid  tip 0.1 mm (land 0.06%)", 0.1,
         "rho %.2f%%  =  %.3f x flat"
         % (100 * m["K_ours"], m["K_ours"] / m["K_flat"])),
        ("Kaster-cap analog  tip 2.21 mm (land 30.6%)", 2.2127,
         "rho %.2f%%  =  %.3f x flat"
         % (100 * m["K_cap31"], m["K_cap31"] / m["K_flat"])),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.6))
    for ax, (title, tip, label) in zip(axes, panels):
        if tip is None:
            pts = [(0.0, 0.0), (20.0, 0.0), (20.0, -2.0), (0.0, -2.0)]
        else:
            pts = profile(tip, 5)
        xs = [p[0] for p in pts] + [pts[0][0]]
        ys = [p[1] for p in pts] + [pts[0][1]]
        ax.fill(xs, ys, color="0.55", zorder=1)
        ax.plot(xs, ys, color="0.25", lw=1.0, zorder=2)
        span = max(p[0] for p in pts)
        # Aim only at the middle three pitches (edge cells catch the side
        # exits a real, wider field would), and stride the aim points with
        # an offset that does NOT divide the 4 mm pitch: the first version
        # aimed at span*(k+0.5)/9, which put rays 1, 4, 7 EXACTLY on the
        # three tip centres -- a 0.06 % land drawn as a 33 % land.
        n_ray = 11
        lo, hi = span * 0.2, span * 0.8
        for k in range(n_ray):
            xh = lo + (hi - lo) * ((k + 0.5) / n_ray + 0.0137) % (hi - lo)
            path, nb, esc = trace2d(pts, xh, THETA_DRAW)
            one = esc and nb == 1
            col = "#c81e14" if one else ("#2a6e35" if esc else "#1b3a86")
            ax.plot([p[0] for p in path], [p[1] for p in path],
                    color=col, lw=1.2 if one else 0.8, zorder=3,
                    alpha=0.95 if one else 0.6)
        ax.set_title(title, fontsize=10)
        ax.text(0.5, -0.10, label, transform=ax.transAxes,
                ha="center", fontsize=10)
        ax.set_aspect("equal")
        ax.set_xlim(-3.5, span + 3.5)
        ax.set_ylim(-24.5, 13.0)
        ax.axis("off")
    fig.suptitle(
        "One material (rho 5 %, Kaster's) at the same angles -- what the flat "
        "fraction does.\nred = ray leaves after ONE bounce carrying 5 % (the "
        "flat-land return) - green = ray enters a pit, escapes only after "
        "several rho-multiplications - blue = still inside at bounce 24\n"
        "(rays drawn at 15 deg so entry and exit separate; the numbers below "
        "are Cycles measurements at 0 deg.\nA section shows tip WIDTH over "
        "pitch -- 2.5 % and 55 % here; the areal land fraction is the square: "
        "0.06 % and 30.6 %)", fontsize=9)
    fig.tight_layout(rect=(0, 0.02, 1, 0.86))
    fig.savefig(OUT, dpi=160)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
