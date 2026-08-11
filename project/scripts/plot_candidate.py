"""
Draw the current best candidate as a standalone, fully specified drawing.

    python3 scripts/plot_candidate.py

Geometry alone is not the answer here -- the sweeps put coating reflectance and
gloss above every geometric variable -- so the finishes are drawn on the sheet
next to the dimensions rather than living only in a config dict.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from profile2d import PanelParams, build_cross_section, describe
from plot_profile import OUT, next_revision, log_revision

# scripts/form_mtf.py:209 BASE + :219 BEST with rho_slat lowered to 0.005
CANDIDATE = dict(slat_deg=45.0, slat_len=79.2, pitch_mean=40.0,
                 pitch_jitter=0.25, depth=100.0, thickness=1.0,
                 min_inner_radius=1.5, baffle_rows=2, baffle_deg=-45.0,
                 baffle_len=48.8, baffle_pitch=60.0, flare=20.0, chamfer=30.0)

FINISH = [
    ("슬랫 (stage 1)", "rho 0.005, gloss roughness 0.30",
     "Musou-Black class, lightly glossy — NOT matte, NOT mirror"),
    ("슬랫 절단면 = 립", "same coating, and it is the whole story",
     "0.63 x (thickness/pitch) of the return comes from this 1 mm edge"),
    ("챔버 내부 + 백월", "anything from rho 0.05 to 0.90",
     "measured identical to 4 decimals — light that gets in never comes back"),
]


def main():
    p = PanelParams(**CANDIDATE)
    cs = build_cross_section(p)
    d = describe(p)
    rev = next_revision()

    fig = plt.figure(figsize=(15, 8.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.5, 1.25])
    ax0, ax1, ax2 = (fig.add_subplot(gs[0]), fig.add_subplot(gs[1]),
                     fig.add_subplot(gs[2]))

    for ax, zoom, ttl in (
            (ax0, None, "full section (500 mm face)"),
            (ax1, (-108, 12, -60, 60), "zoom — 120 mm of Z")):
        for loop in cs.shell:
            ax.add_patch(Polygon(loop, closed=True, facecolor="#9aa0a6",
                                 edgecolor="#5f6368", lw=0.4))
        for loop in cs.stage2:
            ax.add_patch(Polygon(loop, closed=True, facecolor="#ff9c4d",
                                 edgecolor="#a85f1b", lw=0.4))
        for loop in cs.stage1:
            ax.add_patch(Polygon(loop, closed=True, facecolor="#4da3ff",
                                 edgecolor="#1b5fa8", lw=0.4))
        ax.plot([0, 0], [-250, 250], color="#e04040", lw=0.9, ls="--")
        ax.set_aspect("equal")
        ax.grid(alpha=0.15, lw=0.4)
        ax.set_title(ttl, fontsize=10)
        ax.set_xlabel("Y depth (mm)   <- into wall     light from +Y ->",
                      fontsize=8)
        if zoom:
            ax.set_xlim(zoom[0], zoom[1]); ax.set_ylim(zoom[2], zoom[3])
        else:
            ax.set_xlim(-115, 20); ax.set_ylim(-275, 275)
            ax.set_ylabel("Z (mm)", fontsize=8)

    ax2.axis("off")
    L1, L2 = 0.03, 0.36
    y = 0.97
    ax2.text(0.0, y, "C_lip005  —  current best", fontsize=13,
             fontweight="bold", va="top")
    y -= 0.055
    ax2.text(0.0, y, "scripts/form_mtf.py:232", fontsize=8, color="#666666",
             va="top", family="monospace")

    def block(title, rows, y):
        y -= 0.055
        ax2.text(0.0, y, title, fontsize=10, fontweight="bold", va="top")
        y -= 0.038
        for k, v in rows:
            ax2.text(L1, y, k, fontsize=8.5, va="top")
            ax2.text(L2, y, v, fontsize=8.5, va="top", family="monospace")
            y -= 0.032
        return y

    y = block("GEOMETRY  (X-extruded, bent sheet)", [
        ("panel face", "500 x 500 mm"),
        ("depth D", f"{d['depth_mm']:.0f} mm"),
        ("sheet", f"AL {d['thickness_mm']:.1f} t, min inner R "
                  f"{p.min_inner_radius:.1f}"),
        ("slat angle", f"{d['slat_deg']:.0f} deg, uniform (NOT jittered)"),
        ("slat length", f"{d['slat_len_mm']:.1f} mm"),
        ("slat pitch", f"{d['pitch_mean_mm']:.0f} mm +/-{d['pitch_jitter']*100:.0f}%"
                       f" irregular  ({len(cs.stage1)} slats)"),
        ("sight-line overlap", f"{d['slat_overlap']:.2f}   (must stay > 1.2)"),
        ("slat zone / chamber", f"{d['slat_zone_depth_mm']:.0f} / "
                                f"{d['chamber_depth_mm']:.0f} mm"),
        ("baffles", f"{d['baffle_rows']} rows x {len(cs.stage2)}, "
                    f"{d['baffle_deg']:.0f} deg"),
        ("flare / chamfer", f"{d['flare_mm']:.0f} / {d['chamfer_mm']:.0f} mm"),
    ], y)

    y -= 0.02
    y = block("FINISH  (outranks every geometric variable)", [
        ("slats + lip", "rho 0.005,  roughness 0.30"),
        ("", "not matte, not mirror"),
        ("chamber + back", "free choice — no measurable effect"),
    ], y)

    y -= 0.02
    y = block("MEASURED  (observer brightness, bare wall = 1)", [
        ("theta   0 deg", "0.0013"),
        ("theta +/-20 deg", "0.0010 - 0.0029"),
        ("theta +/-40 deg", "0.0029 - 0.0088"),
        ("worst within +/-40", "0.021"),
        ("form destroyed?", "NO — the line returns as a line"),
    ], y)

    y -= 0.025
    ax2.text(0.0, y, "Design laws behind these numbers", fontsize=9.5,
             fontweight="bold", va="top")
    y -= 0.04
    for line in ("return(0 deg) = 0.0030 + 0.63 x (thickness / pitch)",
                 "worst-case return = 4.2 x rho_slat   (within +/-40 deg)",
                 "                  = 13.8 x rho_slat  (within +/-60 deg)"):
        ax2.text(L1, y, line, fontsize=8.5, va="top", family="monospace")
        y -= 0.032

    fig.suptitle(f"[{rev:03d}]  C_lip005 — best configuration measured so far",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = os.path.join(OUT, f"{rev:03d}_C_lip005.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    log_revision(rev, "C_lip005", d, cs.warnings)
    print(f"[{rev:03d}] {path}")
    print("slats", len(cs.stage1), "baffles", len(cs.stage2),
          "warnings", cs.warnings)


if __name__ == "__main__":
    main()
