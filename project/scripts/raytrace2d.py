"""
Draw actual ray paths through a Y-Z cross-section.

    python3 scripts/raytrace2d.py

Cycles gives the numbers but not the story. This traces specular rays through
the same cross-section the renderer builds and draws where they go, which is
the only honest way to answer questions like "won't light hitting between the
slats just bounce straight back out?".

Specular only, on purpose: the specular path is the worst case for form,
because it is the component that remembers where the beam landed. A diffuse
bounce would be drawn as a random direction and would say nothing.
"""

from __future__ import annotations

import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from profile2d import PanelParams, build_cross_section
from plot_profile import OUT, next_revision

EPS = 1e-7


def loops_to_segments(loops):
    segs = []
    for loop in loops:
        n = len(loop)
        for i in range(n):
            a, b = loop[i], loop[(i + 1) % n]
            if abs(a[0] - b[0]) > EPS or abs(a[1] - b[1]) > EPS:
                segs.append((a, b))
    return segs


def hit(origin, d, segs, skip=-1):
    """Nearest segment intersection along direction d. Returns (t, index)."""
    best_t, best_i = float("inf"), -1
    ox, oy = origin
    dx, dy = d
    for i, (a, b) in enumerate(segs):
        if i == skip:
            continue
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - ox) * ey - (a[1] - oy) * ex) / den
        u = ((a[0] - ox) * dy - (a[1] - oy) * dx) / den
        if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9 and t < best_t:
            best_t, best_i = t, i
    return best_t, best_i


def trace(origin, d, segs, max_bounces=40):
    """Return the polyline the ray follows, plus how it ended."""
    path = [origin]
    p = origin
    last = -1
    for _ in range(max_bounces):
        t, i = hit(p, d, segs, skip=last)
        if i < 0:
            path.append((p[0] + d[0] * 900.0, p[1] + d[1] * 900.0))
            return path, ("escaped" if d[0] > 0 else "lost"), len(path) - 2
        q = (p[0] + d[0] * t, p[1] + d[1] * t)
        path.append(q)
        a, b = segs[i]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        n = (-ey / L, ex / L)
        if d[0] * n[0] + d[1] * n[1] > 0:
            n = (-n[0], -n[1])
        dot = d[0] * n[0] + d[1] * n[1]
        d = (d[0] - 2 * dot * n[0], d[1] - 2 * dot * n[1])
        p, last = q, i
    return path, "absorbed", max_bounces


def draw(p, thetas, name, z_span=140.0, n_rays=9, builder=None, depth=None):
    cs = (builder or build_cross_section)(p)
    segs = loops_to_segments(cs.stage1 + cs.stage2 + cs.shell)
    depth = depth or getattr(p, "depth", 100.0)

    fig, axes = plt.subplots(1, len(thetas),
                             figsize=(4.6 * len(thetas), 6.4), squeeze=False)
    rev = next_revision()
    stats = []
    for c, th in enumerate(thetas):
        ax = axes[0][c]
        for loop in cs.shell:
            ax.add_patch(Polygon(loop, closed=True, facecolor="#d8dade",
                                 edgecolor="#7a7f85", lw=0.4, zorder=1))
        for loop in cs.stage2:
            ax.add_patch(Polygon(loop, closed=True, facecolor="#ffd6b0",
                                 edgecolor="#a85f1b", lw=0.4, zorder=2))
        for loop in cs.stage1:
            ax.add_patch(Polygon(loop, closed=True, facecolor="#b7d9ff",
                                 edgecolor="#1b5fa8", lw=0.4, zorder=2))

        t = math.radians(th)
        d = (-math.cos(t), -math.sin(t))
        esc = 0
        depths, bounces, shifts = [], [], []
        for k in range(n_rays):
            z0 = z_span / 2 - z_span * k / (n_rays - 1)
            # step back along -d from the face point, so every ray lands inside
            # the framed Z range whatever the incidence angle
            start = (-60.0 * d[0], z0 - 60.0 * d[1])
            path, how, nb = trace(start, d, segs)
            depths.append(min(q[0] for q in path))
            if how == "escaped":
                bounces.append(nb)
                # how far the exit point moved in Z from where the ray landed:
                # this IS the form-destruction scale, and it is what a single
                # bounce can never provide
                shifts.append(abs(path[-2][1] - path[1][1]))
            col = "#d02020" if how == "escaped" else "#2060c0"
            if how == "escaped":
                esc += 1
            ax.plot([q[0] for q in path], [q[1] for q in path],
                    color=col, lw=1.0, alpha=0.85, zorder=5)
            ax.plot([path[1][0]], [path[1][1]], "o", ms=2.5, color=col, zorder=6)

        ax.plot([0, 0], [-z_span, z_span], color="#e04040", lw=0.8, ls="--",
                zorder=4)
        ax.set_aspect("equal")
        ax.set_xlim(-depth * 1.05, 40)
        ax.set_ylim(-z_span * 0.62, z_span * 0.62)
        mb = sum(bounces) / len(bounces) if bounces else 0.0
        ms = sum(shifts) / len(shifts) if shifts else 0.0
        ax.set_title(f"θ = {th:+.0f}°   escaped {esc}/{n_rays}\n"
                     f"{mb:.1f} bounces,  Z shift {ms:.0f} mm", fontsize=9)
        stats.append((th, esc, mb, ms))
        ax.set_xlabel("Y depth (mm)", fontsize=8)
        if c == 0:
            ax.set_ylabel("Z (mm)", fontsize=8)
        ax.grid(alpha=0.15, lw=0.4)

    fig.suptitle(f"[{rev:03d}] {name} — specular ray paths   "
                 "(red = found its way back out, blue = trapped)", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = os.path.join(OUT, f"{rev:03d}_rays_{name}.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    print(f"[{rev:03d}] {os.path.basename(path)}")
    for th, esc, mb, ms in stats:
        print("        th=%+4.0f  escaped %d/%d  bounces %.1f  Z shift %5.1f mm"
              % (th, esc, n_rays, mb, ms))
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    cand = PanelParams(slat_deg=45.0, slat_len=79.2, pitch_mean=40.0,
                       baffle_rows=2, baffle_deg=-45.0, baffle_len=48.8,
                       baffle_pitch=60.0)
    draw(cand, (-60.0, -30.0, 0.0, 30.0, 60.0), "C_lip005")

    # scatter troughs, for comparison: the question is how many wall hits a ray
    # takes and how far it moves in Z before it leaves
    import profile_scatter as PS
    for dr, w, shape in ((1.5, 60.0, "vee"), (2.5, 40.0, "vee"),
                         (1.5, 60.0, "asym"), (1.5, 60.0, "u")):
        sp = PS.ScatterParams(width_mean=w, depth_ratio=dr, shape=shape,
                              depth=100.0)
        draw(sp, (-60.0, -30.0, 0.0, 30.0, 60.0),
             f"scatter_{shape}_w{int(w)}_d{dr:.1f}".replace(".", ""),
             z_span=200.0, n_rays=9,
             builder=PS.build_cross_section, depth=sp.trough_depth() + 20.0)
