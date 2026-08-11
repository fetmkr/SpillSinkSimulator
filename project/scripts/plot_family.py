"""
One numbered cross-section drawing per design, for any of the three geometry
families, appended to profiles/INDEX.md in the order they were made.

    python3 scripts/plot_family.py

The numbering is the point: nothing is overwritten, so the folder is a record
of what was tried and in what order, and a later report can show the dead ends
next to the survivors instead of only the survivors.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

import profile2d as F_SLAT
import profile_scatter as F_SCAT
import profile_ridge as F_RIDGE
from plot_profile import OUT, INDEX, next_revision

FAMILIES = {
    "slat": (F_SLAT.PanelParams, F_SLAT.build_cross_section, F_SLAT.describe),
    "scatter": (F_SCAT.ScatterParams, F_SCAT.build_cross_section, F_SCAT.describe),
    "ridge": (F_RIDGE.RidgeParams, F_RIDGE.build_cross_section, F_RIDGE.describe),
}

C_S1 = "#4da3ff"
C_S2 = "#ff9c4d"
C_SH = "#9aa0a6"


def log(rev, family, name, d, warnings, note):
    first = not os.path.exists(INDEX)
    with open(INDEX, "a") as f:
        if first:
            f.write("# Profile revisions\n\n")
        f.write(f"| {rev:03d} | {family} | [{name}]({rev:03d}_{name}.png) | "
                f"{note} | {'; '.join(w.split(':')[0] for w in warnings)} |\n")


def key_line(family, d):
    if family == "ridge":
        return (f"pitch {d['pitch_mean_mm']:.0f} +/-{d['pitch_jitter']*100:.0f}%  "
                f"depth {d['depth_mm']:.0f}  half-angle {d['half_angle_deg']:.1f}deg  "
                f"~{d['est_bounces']:.1f} bounces\n"
                f"ridge tip {d['tip_width_mm']:.2f} mm = {d['tip_fraction']*100:.2f}% "
                f"of the face   predicted return {d['predicted_return_rho05']:.4f} at rho 0.05")
    if family == "scatter":
        return (f"trough width {d['width_mean_mm']:.0f} +/-{d['width_jitter']*100:.0f}%  "
                f"depth {d['trough_depth_mm']:.0f} (ratio {d['depth_ratio']:.2f})  "
                f"shape {d['shape']}\n"
                f"apex {d['apex_angle_deg']:.1f}deg   aperture f {d['aperture_fraction']:.3f}   "
                f"~{d['est_bounces']:.1f} bounces   lip {d['lip_len_mm']:.0f} mm")
    return (f"slat {d['slat_mode']} {d['slat_deg']:.0f}deg L{d['slat_len_mm']:.0f}  "
            f"pitch {d['pitch_mean_mm']:.1f} +/-{d['pitch_jitter']*100:.0f}%  "
            f"overlap {d['slat_overlap']:.2f}\n"
            f"zone {d['slat_zone_depth_mm']:.0f} / chamber {d['chamber_depth_mm']:.0f}   "
            f"baffles {d['baffle_rows']}r @{d['baffle_deg']:.0f}deg   "
            f"open face {d['open_face_fraction']:.3f}")


def render(family, name, note="", zoom_span=None, **params):
    Params, build, describe = FAMILIES[family]
    p = Params(**params)
    cs = build(p)
    d = describe(p)
    rev = next_revision()

    depth = getattr(p, "depth", 100.0)
    if family == "scatter":
        depth = p.trough_depth() + 20.0
    span = zoom_span or {"ridge": 120.0, "scatter": 260.0, "slat": 140.0}[family]

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 7.6))
    for ax, zm, ttl in ((axes[0], None, "full section"),
                        (axes[1], span, f"zoom — {span:.0f} mm of Z")):
        for loop in cs.shell:
            ax.add_patch(Polygon(loop, closed=True, facecolor=C_SH,
                                 edgecolor="#5f6368", lw=0.4))
        for loop in cs.stage2:
            ax.add_patch(Polygon(loop, closed=True, facecolor=C_S2,
                                 edgecolor="#a85f1b", lw=0.4))
        for loop in cs.stage1:
            ax.add_patch(Polygon(loop, closed=True, facecolor=C_S1,
                                 edgecolor="#1b5fa8", lw=0.4))
        ax.plot([0, 0], [-p.face_h, p.face_h], color="#e04040", lw=0.8, ls="--")
        ax.set_aspect("equal")
        ax.grid(alpha=0.15, lw=0.4)
        ax.set_title(f"[{rev:03d}] {name} — {ttl}", fontsize=9)
        ax.set_xlabel("Y depth (mm)   <- into wall     light from +Y ->",
                      fontsize=8)
        if zm:
            ax.set_xlim(-depth * 1.08, depth * 0.14)
            ax.set_ylim(-zm / 2, zm / 2)
        else:
            m = p.face_h * 0.06
            ax.set_xlim(-depth * 1.08, depth * 0.18)
            ax.set_ylim(-p.face_h / 2 - m, p.face_h / 2 + m)
            ax.set_ylabel("Z (mm)", fontsize=8)

    txt = key_line(family, d)
    if note:
        txt = note + "\n" + txt
    if cs.warnings:
        txt += "\nWARN: " + " | ".join(w[:90] for w in cs.warnings)
    fig.text(0.5, 0.015, txt, ha="center", fontsize=8, family="monospace")
    fig.tight_layout(rect=(0, 0.085, 1, 1))

    path = os.path.join(OUT, f"{rev:03d}_{name}.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    log(rev, family, name, d, cs.warnings, note)
    print(f"  [{rev:03d}] {os.path.basename(path)}   warn={len(cs.warnings)}")
    return rev


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("ridge family (beam-dump V-grooves):")

    # the tip-width series: the axis that turned out to carry the whole result
    for tw in (0.05, 0.2, 1.0, 2.0):
        render("ridge", f"ridge_tip{int(tw*100):03d}",
               note=f"tip width series — measured return at theta 0: "
                    f"{ {0.05:0.00422, 0.2:0.00879, 1.0:0.02942, 2.0:0.05456}[tw]:.5f}",
               depth=100.0, pitch_mean=20.0, tip_width=tw, zoom_span=90.0)

    # the depth series: the axis that decides the WORST angle, not theta 0
    for dp, worst in ((25.0, 0.99996), (50.0, 0.99041), (100.0, 0.23453),
                      (150.0, 0.05233)):
        render("ridge", f"ridge_depth{int(dp):03d}",
               note=f"depth series — worst return over all angles: {worst:.5f}",
               depth=dp, pitch_mean=20.0, tip_width=0.2, zoom_span=90.0)

    # tilted grooves, aiming the trap where the beams actually come from
    render("ridge", "ridge_tilt20",
           note="tilted groove axis — aims the trap at the incoming beams",
           depth=100.0, pitch_mean=20.0, tip_width=0.2, tilt_deg=20.0,
           zoom_span=90.0)
    render("ridge", "ridge_tilt_jitter",
           note="tilt jittered per ridge — spreads any glint over incidence",
           depth=100.0, pitch_mean=20.0, tip_width=0.2, tilt_deg=0.0,
           tilt_jitter=12.0, zoom_span=90.0)
