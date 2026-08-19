"""Phase 8.6 figure — splitting the pane, the edge-glow failure, and the fix.

All numbers measured 2026-08-19 by scripts/probe_louvre.py (audience matrix,
12 cells each: sun {0,+20,+40,-20} x observer {0,-10,-20}, tilt 25).
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

INK, GREY, ACC, DIM = "#16181a", "#84878b", "#ff4d00", "#b3aea3"
BLUE, OK, NO = "#1d7fd4", "#1f7a44", "#c0341c"
M = {"family": "monospace"}
T = math.radians(25.0)

fig = plt.figure(figsize=(14.5, 10))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.18], height_ratios=[1.45, 1],
                      wspace=0.16, hspace=0.16,
                      left=0.045, right=0.975, top=0.855, bottom=0.05)
a1 = fig.add_subplot(gs[0, 0])   # one pane vs louvre stack
a2 = fig.add_subplot(gs[0, 1])   # edge glow + fix
a3 = fig.add_subplot(gs[1, :])   # measured bar chart


def pane_poly(ax, z_top, length, color, lw=5.0, ls="-"):
    y0, z0 = 0.0, z_top
    y1 = length * math.sin(T)
    z1 = z_top - length * math.cos(T)
    ax.plot([y0, y1], [z0, z1], color=color, lw=lw, ls=ls,
            solid_capstyle="butt")
    return (y1, z1)


# ---------------- A: one pane vs four louvres ----------------
H = 733.0
a1.plot([-40, -40], [-180, 900], color=INK, lw=3)          # wall
b = pane_poly(a1, 780, H, BLUE)
a1.annotate("", xy=(b[0], -120), xytext=(0, -120),
            arrowprops=dict(arrowstyle="<->", color=INK, lw=1.0))
a1.text(b[0] / 2, -220, "projection 310", ha="center", fontsize=11, color=INK, **M)
a1.text(0, 900, "ONE PANE 733", fontsize=11.5, color=BLUE, **M)

XO = 900.0                                                  # second drawing
a1.plot([XO - 40, XO - 40], [-180, 900], color=INK, lw=3)
seg = (H - 3 * 8.0) / 4.0
for i in range(4):
    ztop = 780 - i * (seg * math.cos(T) + 8.0)
    y0 = XO
    y1 = y0 + seg * math.sin(T)
    z1 = ztop - seg * math.cos(T)
    a1.plot([y0, y1], [ztop, z1], color=BLUE, lw=5, solid_capstyle="butt")
a1.annotate("", xy=(XO + seg * math.sin(T), -120), xytext=(XO, -120),
            arrowprops=dict(arrowstyle="<->", color=INK, lw=1.0))
a1.text(XO + 40, -220, "projection 77", fontsize=11, color=OK, **M)
a1.text(XO, 900, "FOUR LOUVRES 183 each", fontsize=11.5, color=BLUE, **M)
a1.text(XO - 240, -430, "same tilt -> same mirror law,\nquarter the projection depth",
        fontsize=11, color=OK, va="top", **M)
a1.text(-200, -430, "one big sheet:\nawkward to carry\nand to mount",
        fontsize=11, color=GREY, va="top", **M)
a1.set_xlim(-220, 1420); a1.set_ylim(-700, 1080)
a1.set_aspect("equal"); a1.axis("off")
a1.set_title("A · splitting the pane (side view, mm)", loc="left",
             fontsize=13, color=GREY, **M)

# ---------------- B: the edge-glow failure and the fix ----------------
def draw_case(ax, x0, edge_black, title, color):
    ztop = 520.0
    y1 = x0 + 300 * math.sin(T)
    z1 = ztop - 300 * math.cos(T)
    ax.plot([x0, y1], [ztop, z1], color=BLUE, lw=7, solid_capstyle="butt")
    # light piped inside the pane
    for k in (0.30, 0.55, 0.80):
        ax.annotate("", xy=(x0 + (y1 - x0) * k, ztop + (z1 - ztop) * k),
                    xytext=(x0 + (y1 - x0) * k - 150,
                            ztop + (z1 - ztop) * k + 190),
                    arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.5))
    ax.annotate("", xy=(y1 - 12, z1 + 8), xytext=(x0 + 18, ztop - 12),
                arrowprops=dict(arrowstyle="-|>", color="#e0a400", lw=2.6))
    if edge_black:
        ax.plot([y1, y1 + 14], [z1, z1 - 30], color=INK, lw=9,
                solid_capstyle="butt")
        ax.text(y1 + 60, z1 - 70, "cut edge\nBLACKED", fontsize=11,
                color=OK, va="top", **M)
    else:
        for a_ in (10, 0, -12, -26):
            ar = math.radians(a_)
            ax.annotate("", xy=(y1 + 330 * math.cos(ar), z1 + 330 * math.sin(ar)),
                        xytext=(y1, z1),
                        arrowprops=dict(arrowstyle="-|>", color=NO, lw=1.8))
        ax.text(y1 + 120, z1 - 180, "cut edge GLOWS\ninto the room",
                fontsize=11, color=NO, va="top", **M)
    ax.text(x0 - 60, 700, title, fontsize=12, color=color, **M)


a2.text(0, 990, "light entering at a steep angle is trapped inside the pane\n"
        "(total internal reflection) and runs to the cut end",
        fontsize=11, color=ACC, va="top", **M)
draw_case(a2, 0, False, "RAW CUT EDGE\nworst 116", NO)
draw_case(a2, 1000, True, "BLACKED EDGE\nworst 0.009", OK)
a2.text(0, -300, "One big pane hides both its edges (top under the lip, "
        "bottom in the trough).\nEvery extra pane adds two edges in the open "
        "aperture — those must be blacked.",
        fontsize=11, color=INK, va="top", **M)
a2.set_xlim(-160, 1780); a2.set_ylim(-560, 1000)
a2.set_aspect("equal"); a2.axis("off")
a2.set_title("B · why splitting is not free — and the fix", loc="left",
             fontsize=13, color=GREY, **M)

# ---------------- C: measured audience-matrix worst values ----------------
rows = [("one pane, edges hidden", 0.0, OK, "12 of 12 cells exactly zero"),
        ("one pane + blacked edges", 0.0, OK, "12 of 12 cells exactly zero"),
        ("4 louvres, blacked edges", 0.009, OK,
         "usable: 0.009 worst, all cells faint"),
        ("4 louvres, bright frames", 0.10, NO,
         "every cell lit — frames must be black and recessed"),
        ("4 louvres, RAW cut edges", 116.0, NO,
         "edge glow: 12 000x the blacked version")]
ypos = range(len(rows))
for i, (lbl, v, col, note) in enumerate(rows):
    y = len(rows) - 1 - i
    w = 0.0 if v <= 0 else (math.log10(v * 1000 + 1) / math.log10(116e3))
    a3.add_patch(FancyBboxPatch((0.30, y - 0.28), max(w, 0.004) * 0.42, 0.56,
                                boxstyle="round,pad=0.002", facecolor=col,
                                edgecolor="none", alpha=0.85))
    a3.text(0.295, y, lbl, ha="right", va="center", fontsize=12, color=INK, **M)
    a3.text(0.30 + max(w, 0.004) * 0.42 + 0.012, y,
            ("0.000" if v <= 0 else ("%.3f" % v if v < 1 else "%.0f" % v)),
            va="center", fontsize=12, color=col, **M)
    a3.text(0.80, y, note, va="center", fontsize=11, color=GREY, **M)
a3.text(0.0, len(rows) + 0.05,
        "worst audience-matrix value — 12 cells each "
        "(beam 0/+20/+40/-20 x observer 0/-10/-20, tilt 25)",
        fontsize=11, color=GREY, **M)
a3.set_xlim(-0.02, 1.32); a3.set_ylim(-0.7, len(rows) + 0.55)
a3.axis("off")
a3.set_title("C · measured (log bars; a flat Musou plate reads "
             "0.0006-0.029 in this rig)", loc="left", fontsize=13,
             color=GREY, **M)

fig.suptitle("SPLITTING THE WINDOW PANE — install in pieces, black the cut edges",
             fontsize=16.5, color=INK, y=0.955, **M)
fig.text(0.5, 0.905, "tilt 25 deg · the mirror law depends on tilt alone, so "
         "N panes behave as one — the price of splitting is the exposed cut edges",
         fontsize=11.5, color=GREY, ha="center", **M)
fig.text(0.045, 0.015, "fetm.kr · SPILL SINK PANEL · phase 8.6 · "
         "measured by scripts/probe_louvre.py", fontsize=10, color=GREY, **M)
plt.savefig("results/fig_split_panes.png", dpi=110, bbox_inches="tight",
            facecolor="white")
print("saved")
