"""Room section + unit detail + top view for the tilted AR window unit.

Every number is from the study: tilt 25 (phase 10.3 minimum; the mirror law
obs = -(beam + 2*tilt) puts 15 deg inside the audience band), glass 733x620
AR (phase 8 / RFQ), cover lip over the top 25 % (8.2c), trap lined with the
p4/d22 pyramid panel, 1 m dark floor (8.3), beam 7-14 mm (LaserCube MK2).
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge, Circle

INK, GREY, ACC, DIM = "#16181a", "#84878b", "#ff4d00", "#b3aea3"
BLUE, OK = "#1d7fd4", "#1f7a44"
M = {"family": "monospace"}
TILT, GH, LIP, SILL = 25.0, 733.0, 0.25, 1500.0
t = math.radians(TILT)
BX, BY = GH * math.sin(t), SILL - GH * math.cos(t)   # bottom of glass

fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor("white")
gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], height_ratios=[1, 1],
                      wspace=0.10, hspace=0.20,
                      left=0.04, right=0.98, top=0.86, bottom=0.05)
axr = fig.add_subplot(gs[:, 0])     # room section
axd = fig.add_subplot(gs[0, 1])     # unit detail
axt = fig.add_subplot(gs[1, 1])     # top view


def dim_h(ax, x1, x2, y, txt, dy=-90, fs=10):
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.0))
    ax.text((x1 + x2) / 2, y + dy, txt, ha="center", va="top",
            fontsize=fs, color=INK, **M)


def dim_v(ax, y1, y2, x, txt, dx=60, fs=10):
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.0))
    ax.text(x + dx, (y1 + y2) / 2, txt, va="center", fontsize=fs,
            color=INK, **M)


# ---------------- ROOM SECTION ----------------
axr.plot([0, 0], [0, 3000], color=INK, lw=3)
axr.plot([0, 6000], [0, 0], color=INK, lw=2)
axr.text(60, 2900, "WALL", color=INK, fontsize=11, **M)
axr.add_patch(Rectangle((0, 0), 1000, 40, facecolor="#2a2d31", ec="none"))
dim_h(axr, 0, 1000, -180, "dark floor 1 000")

# unit block (schematic at room scale)
axr.add_patch(Rectangle((0, BY - 450), BX + 60, SILL - BY + 450,
                        facecolor="#eaf1f8", ec=BLUE, lw=1.8))
axr.plot([0, BX], [SILL, BY], color=BLUE, lw=4)
axr.text(760, 700, "WINDOW UNIT\n(detail at right)",
         fontsize=10.5, color=BLUE, va="center", **M)
axr.add_patch(Circle((BX / 2, (SILL + BY) / 2), 430, fill=False,
                     color=ACC, lw=1.6))

# ---- installable projector zone and hazard zone (drawn from the unit) ----
# Aperture coverage (phase 8.2, tilt 25): the plate intercepts the full beam
# up to +29 deg, 0.65 of it at +40, nothing past +54.
# Mirror law (phase 10.3): the specular branch lands at -(beam + 2*tilt);
# with tilt 25 it stays below -20 deg (the audience band) for any beam
# above -30 deg elevation.
UMID = (BX / 2, (SILL + BY) / 2)
R = 3900.0
axr.add_patch(Wedge(UMID, R, 0, 29, facecolor="#1f7a44", alpha=0.14, ec="none"))
axr.add_patch(Wedge(UMID, R, 29, 54, facecolor="#1f7a44", alpha=0.07, ec="none"))
axr.add_patch(Wedge(UMID, 2600, -90, -30, facecolor="#c0341c", alpha=0.10,
                    ec="none"))
for a_, lbl, col in ((0, "0 deg", OK), (29, "+29", OK), (54, "+54", OK),
                     (-30, "-30", "#c0341c")):
    ar = math.radians(a_)
    rr = R if a_ >= 0 else 2600
    axr.plot([UMID[0], UMID[0] + rr * math.cos(ar)],
             [UMID[1], UMID[1] + rr * math.sin(ar)], color=col, lw=1.0,
             ls=(0, (6, 4)))
    lr = rr * (0.52 if a_ == 54 else 0.80)
    axr.text(UMID[0] + lr * math.cos(ar),
             UMID[1] + lr * math.sin(ar) + 90, lbl, color=col,
             fontsize=10, va="bottom", ha="center", **M)
axr.text(2350, 1020, "PROJECTOR ZONE\n0 to +29 deg: unit takes the whole beam\n"
         "+29 to +54: partial, still safe\nabove +54: the beam misses the unit",
         fontsize=10.5, color=OK, va="top", **M)
axr.text(2350, -330, "HAZARD: only beams arriving from below -30 deg\n"
         "(e.g. a floor bounce). Nothing above -30 reaches the audience.",
         fontsize=10.5, color="#c0341c", va="top", **M)

# projector high on the far side
px, py = 5450.0, 2950.0
axr.add_patch(Rectangle((px - 220, py - 70), 260, 140, facecolor="#2a2d31",
                        ec=INK))
axr.text(px - 260, py + 210, "LASER PROJECTOR\nceiling-mounted", fontsize=10.5,
         color=INK, ha="right", **M)
mid = (BX / 2, (SILL + BY) / 2)
axr.annotate("", xy=mid, xytext=(px - 220, py - 20),
             arrowprops=dict(arrowstyle="-|>", color=ACC, lw=2.2))
axr.text(2500, 2050, "spill beam 7-14 mm", color=ACC, fontsize=11,
         rotation=-14, **M)

# audience
axr.plot([1100, 6000], [1600, 1600], color=OK, lw=1.1, ls="--")
axr.text(5950, 1680, "audience eye 1 600", color=OK, fontsize=10.5,
         ha="right", **M)
axr.annotate("", xy=(1250, 1450), xytext=mid,
             arrowprops=dict(arrowstyle="-", color=OK, lw=1.0, ls=":"))
axr.text(3450, 1180, "sightline to the unit:\n0.000 % in every measured cell",
         color=OK, fontsize=10.5, va="top", **M)
axr.set_xlim(-500, 6100); axr.set_ylim(-900, 3550)
axr.set_aspect("equal"); axr.axis("off")
axr.set_title("SIDE VIEW · room section (mm)", loc="left", fontsize=13,
              color=GREY, **M)

# ---------------- UNIT DETAIL ----------------
axd.plot([0, 0], [BY - 500, SILL + 260], color=INK, lw=3)
axd.plot([-40, 1150], [BY - 500, BY - 500], color=INK, lw=2)
axd.plot([0, BX], [SILL, BY], color=BLUE, lw=6, solid_capstyle="butt")
lx, ly = BX * LIP, SILL + (BY - SILL) * LIP
axd.plot([0, lx], [SILL, ly], color=INK, lw=11, solid_capstyle="butt")
axd.text(lx + 150, ly + 120, "cover lip", fontsize=10.5, color=INK, **M)

# trap
axd.add_patch(Rectangle((0, BY - 500), BX + 90, 500, facecolor="#e9e7e1",
                        ec=INK, lw=1.5))
k = 0
while k * 30 < BX + 90:
    axd.plot([k * 30, k * 30 + 15], [BY - 500, BY - 440], color=DIM, lw=0.9)
    k += 1
axd.text(-1400, BY - 760, "trap lining:\np4/d22/t0.4 panel",
         fontsize=10.5, color=INK, va="top", **M)

# tilt wedge
axd.plot([0, 320], [SILL, SILL], color=GREY, lw=0.9, ls=":")
axd.plot([0, 0], [SILL, SILL - 340], color=GREY, lw=0.9, ls=":")
axd.add_patch(Wedge((0, SILL), 300, -90, -90 + TILT, width=7, facecolor=ACC))
axd.text(330, SILL - 250, "25 deg", color=ACC, fontsize=12.5, **M)

# rays at the detail scale
mid2 = (BX / 2, (SILL + BY) / 2)
axd.annotate("", xy=mid2, xytext=(mid2[0] + 780, mid2[1] + 640),
             arrowprops=dict(arrowstyle="-|>", color=ACC, lw=2.2))
axd.text(mid2[0] + 700, mid2[1] + 700, "beam in", color=ACC, fontsize=10.5, **M)
axd.annotate("", xy=(BX * 0.35, BY - 330), xytext=mid2,
             arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=2.4))
axd.text(-1400, BY + 260, "99 % through,\ninto the trap",
         color=BLUE, fontsize=10.5, va="top", **M)
mirang = math.radians(-(30 + 2 * TILT))
axd.annotate("", xy=(mid2[0] + 900 * math.cos(mirang),
                     mid2[1] + 900 * math.sin(mirang)), xytext=mid2,
             arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.8,
                             ls=(0, (5, 3))))
axd.text(-1400, BY - 250, "1 % specular,\nalways down",
         color=GREY, fontsize=10.5, va="top", **M)
dim_v(axd, BY, SILL, 1180, "glass 733\nAR R <= 1 %/face", dx=70)
dim_h(axd, 0, BX, BY - 1000, "projection 310")
axd.text(-1400, SILL + 1180, "MIRROR LAW   obs = -(beam + 2 x tilt)\n  tilt 15  ->  -30 deg   FAILS (inside the audience band)\n  tilt 25  ->  -50 deg   SAFE",
         fontsize=10.5, color=INK, va="top", **M)
axd.set_xlim(-1450, 1650); axd.set_ylim(BY - 1250, SILL + 1250)
axd.set_aspect("equal"); axd.axis("off")
axd.set_title("DETAIL · the unit (mm)", loc="left", fontsize=13, color=GREY, **M)

# ---------------- TOP VIEW ----------------
UW = 620.0
axt.plot([-200, 3400], [0, 0], color=INK, lw=3)
axt.text(-650, 480, "WALL (plan)", color=INK, fontsize=11, **M)
for i in range(5):
    x0 = 100 + i * (UW + 30)
    axt.add_patch(Rectangle((x0, 0), UW, 310, facecolor="#eaf1f8",
                            ec=BLUE, lw=1.8))
dim_h(axt, 100, 100 + UW, -420, "620 per unit")
dim_v(axt, 0, 310, -320, "310", dx=-420)
axt.text(3750, -300, "units butt in a row, no gaps", fontsize=10.5,
         color=BLUE, ha="right", **M)

for (pxx, pyy, tgt) in [(1250, 2450, 480), (2000, 2600, 1450),
                        (2750, 2450, 2200), (3350, 2050, 2950)]:
    axt.add_patch(Rectangle((pxx - 80, pyy - 50), 160, 100,
                            facecolor="#2a2d31", ec=INK))
    axt.annotate("", xy=(tgt, 320), xytext=(pxx, pyy - 50),
                 arrowprops=dict(arrowstyle="-|>", color=ACC, lw=1.7))
axt.text(-650, 3150, "projectors spread\nacross the room", fontsize=10.5,
         color=INK, va="top", **M)
axt.text(-450, 3900, "phi 0 / 45 / 90 all measured: the audience branch is set\n"
         "by the FRONT FACE TILT. Groove direction does not change it,\n"
         "so every approach azimuth is equally safe.",
         fontsize=10.5, color=GREY, va="top", **M)
axt.set_xlim(-700, 3800); axt.set_ylim(-750, 4050)
axt.set_aspect("equal"); axt.axis("off")
axt.set_title("TOP VIEW · wall run and projector spread", loc="left",
              fontsize=13, color=GREY, **M)

fig.suptitle("TILTED AR WINDOW UNIT — projector layout and device geometry",
             fontsize=17, color=INK, y=0.955, **M)
fig.text(0.5, 0.905, "tilt 25 deg (phase 10.3 minimum) · glass 733 x 620 AR · "
         "pyramid-lined trap · cover lip over top 25 % · 1 m dark floor",
         fontsize=11.5, color=GREY, ha="center", **M)
fig.text(0.04, 0.015, "fetm.kr · SPILL SINK PANEL · phase 8 device, phase 10 tilt law",
         fontsize=10, color=GREY, **M)
plt.savefig("window_layout.png", dpi=110, bbox_inches="tight", facecolor="white")
print("saved")
