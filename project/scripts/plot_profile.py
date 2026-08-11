"""
Draw Y-Z cross-sections to PNG so geometry can be eyeballed before any render
time is spent. Run with system python3 (needs matplotlib), not Blender.

    python3 scripts/plot_profile.py
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "profiles")
INDEX = os.path.join(OUT, "INDEX.md")


def next_revision():
    """
    Profiles are numbered and never overwritten, so the design history stays
    on disk in the order it happened. The counter is recovered from the files
    already present rather than stored, so a deleted index cannot desync it.
    """
    n = 0
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            head = f.split("_", 1)[0]
            if head.isdigit():
                n = max(n, int(head))
    return n + 1


def log_revision(rev, name, d, warnings):
    first = not os.path.exists(INDEX)
    with open(INDEX, "a") as f:
        if first:
            f.write("# Profile revisions\n\n"
                    "Numbered oldest first. Each row is one cross-section as "
                    "it stood when it was generated.\n\n"
                    "| rev | name | slat | pitch | zone/chamber | overlap | "
                    "baffles | notes |\n"
                    "|----:|------|------|------:|-------------|--------:|"
                    "---------|-------|\n")
        note = "; ".join(w.split(":")[0] for w in warnings) or ""
        f.write(f"| {rev:03d} | [{name}]({rev:03d}_{name}.png) | "
                f"{d['slat_mode']} {d['slat_deg']:.0f}deg"
                f"{'' if not d['slat_deg_jitter'] else ' +/-%.0f' % d['slat_deg_jitter']}"
                f" L{d['slat_len_mm']:.0f} | {d['pitch_mean_mm']:.1f} | "
                f"{d['slat_zone_depth_mm']:.0f}/{d['chamber_depth_mm']:.0f} | "
                f"{d['slat_overlap']:.2f} | "
                f"{d['baffle_rows']}r x{d['baffle_count']} @{d['baffle_deg']:.0f}deg | "
                f"{note} |\n")

C_S1 = "#4da3ff"    # stage 1 - slats, deflection
C_S2 = "#ff9c4d"    # stage 2 - baffles
C_SH = "#9aa0a6"    # shell


def draw(ax, p: PanelParams, cs, zoom=None, title=""):
    for loop in cs.shell:
        ax.add_patch(Polygon(loop, closed=True, facecolor=C_SH,
                             edgecolor="#5f6368", linewidth=0.4))
    for loop in cs.stage2:
        ax.add_patch(Polygon(loop, closed=True, facecolor=C_S2,
                             edgecolor="#a85f1b", linewidth=0.4))
    for loop in cs.stage1:
        ax.add_patch(Polygon(loop, closed=True, facecolor=C_S1,
                             edgecolor="#1b5fa8", linewidth=0.4))

    zl, zh = -p.face_h / 2, p.face_h / 2
    ax.plot([0, 0], [zl, zh], color="#e04040", lw=0.8, ls="--", zorder=5)
    ax.plot([-p.slat_zone_depth()] * 2, [zl, zh],
            color="#40a040", lw=0.6, ls=":", zorder=5)

    ax.set_aspect("equal")
    ax.set_xlabel("Y  depth (mm)   <- into wall      light from +Y ->")
    ax.set_ylabel("Z  (mm)")
    ax.set_title(title, fontsize=9)
    if zoom:
        ax.set_xlim(zoom[0], zoom[1])
        ax.set_ylim(zoom[2], zoom[3])
    else:
        m = p.flare + 15
        ax.set_xlim(-p.depth * 1.12, p.depth * 0.18)
        ax.set_ylim(zl - m, zh + m)
    ax.grid(alpha=0.15, lw=0.4)


def render_case(p: PanelParams, name: str, rev: int | None = None):
    cs = build_cross_section(p)
    d = describe(p)
    if rev is None:
        rev = next_revision()

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.8))
    draw(axes[0], p, cs, title=f"[{rev:03d}] {name} — full section")
    span = max(p.pitch_mean * 5, p.baffle_pitch * 2)
    draw(axes[1], p, cs,
         zoom=(-p.depth * 1.06, p.depth * 0.12, -span / 2, span / 2),
         title=f"[{rev:03d}] {name} — zoom ({span:.0f} mm of Z)")

    txt = (f"depth {d['depth_mm']:.0f}   slat L {d['slat_len_mm']:.0f} @ "
           f"{d['slat_deg']:.0f}deg -> zone {d['slat_zone_depth_mm']:.1f}   "
           f"chamber {d['chamber_depth_mm']:.1f}   "
           f"slat overlap {d['slat_overlap']:.2f}\n"
           f"pitch {d['pitch_mean_mm']:.0f} +/-{d['pitch_jitter']*100:.0f}%   "
           f"open face {d['open_face_fraction']:.3f}   "
           f"chamber f {d['chamber_aperture_fraction']:.3f}   "
           f"flare {d['flare_mm']:.0f}   chamfer {d['chamfer_mm']:.0f}\n"
           f"baffles {d['baffle_count']} ({d['baffle_rows']} rows, "
           f"len {d['baffle_len_mm']:.0f}, pitch {d['baffle_pitch_mm']:.0f}, "
           f"{d['baffle_deg']:.0f}deg)   back {d['back_profile']}   "
           f"t {d['thickness_mm']:.1f}  R {d['bend_radius_center_mm']:.1f}")
    if cs.warnings:
        txt += "\nWARN: " + " | ".join(cs.warnings)
    fig.text(0.5, 0.015, txt, ha="center", fontsize=8, family="monospace")
    fig.tight_layout(rect=(0, 0.085, 1, 1))

    path = os.path.join(OUT, f"{rev:03d}_{name}.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    log_revision(rev, name, d, cs.warnings)
    print(f"  [{rev:03d}] {os.path.basename(path)}  slats={len(cs.stage1)} "
          f"baffles={len(cs.stage2)} warn={len(cs.warnings)}")
    return d


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("writing cross-sections:")

    # the configuration the lip law points at: coarsest pitch the depth budget
    # allows, since return at normal incidence goes as thickness / pitch
    render_case(PanelParams(slat_deg=45.0, slat_len=79.2, pitch_mean=40.0,
                            baffle_rows=2, baffle_deg=-45.0, baffle_len=48.8,
                            baffle_pitch=60.0),
                "coarse_p40")
    render_case(PanelParams(slat_deg=45.0, slat_len=79.2, pitch_mean=40.0,
                            slat_deg_jitter=20.0, baffle_rows=2,
                            baffle_deg=-45.0, baffle_len=48.8,
                            baffle_pitch=60.0),
                "coarse_p40_jit20")
    render_case(PanelParams(slat_deg=30.0, slat_len=46.2, pitch_mean=16.5,
                            slat_mode="alternate", baffle_rows=1,
                            baffle_deg=-45.0, baffle_len=30.0),
                "alternate_a30")
    render_case(PanelParams(depth=50.0, chamfer=15.0, flare=12.0,
                            slat_deg=45.0, slat_len=42.4, pitch_mean=21.2,
                            baffle_rows=1, baffle_deg=-45.0, baffle_len=25.0),
                "D50_coarse")
