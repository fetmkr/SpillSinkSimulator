"""Figures for report section 5.4 — drawn to true scale, no renderer.

    python3 scripts/phase54_figs.py

Top row: side profiles of the three aspect-9 scales at ONE mm-per-px scale, so
the panel-thickness trade is visible at a glance (90 vs 50 vs 18 mm).
Bottom row: the top 12 mm of the pitch-10 profile with tip 0.0 / 0.5 / 2.0 mm.
ASCII labels only (PIL default font mangles anything else).
"""

import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(os.path.dirname(HERE), "report", "phase5", "img")

BG = (255, 255, 255)
MAT = (200, 200, 202)
EDGE = (120, 120, 124)
INK = (40, 40, 44)


def profile(draw, x0, y0, scale, pitch, depth, tip, width_mm, backing=3.0):
    """Material silhouette, entrance plane at y0, tips up."""
    n = int(width_mm / pitch)
    pts = [(x0, y0 + depth * scale)]
    for i in range(n):
        cx = x0 + (i + 0.5) * pitch * scale
        half_t = 0.5 * tip * scale
        pts += [(cx - half_t, y0), (cx + half_t, y0)]
        pts.append((x0 + (i + 1) * pitch * scale, y0 + depth * scale))
    base = y0 + (depth + backing) * scale
    pts += [(x0 + n * pitch * scale, base), (x0, base)]
    draw.polygon(pts, fill=MAT, outline=EDGE)


def main():
    S = 5.2                       # px per mm
    W_MM = 42.0                   # panel width drawn per column
    colw = int(W_MM * S) + 40
    top_h = int((90 + 3) * S) + 74
    zoom_h = 240
    img = Image.new("RGB", (3 * colw + 20, top_h + zoom_h + 60), BG)
    d = ImageDraw.Draw(img)

    cases = [("pitch 5.5 / depth 50  (champion)", 5.5005, 50.0, 0.0),
             ("pitch 10 / depth 90 / tip 0.5  (build spec)", 10.0, 90.0, 0.5),
             ("pitch 2 / depth 18  (thin option)", 2.0, 18.0, 0.0)]
    for i, (label, p, dep, t) in enumerate(cases):
        x0 = 20 + i * colw
        d.text((x0, 8), label, fill=INK)
        d.text((x0, 22), "aspect 9.0", fill=EDGE)
        y0 = 40
        d.line([(x0 - 6, y0), (x0 + W_MM * S + 6, y0)], fill=EDGE)
        profile(d, x0, y0, S, p, dep, t, W_MM)
        yb = y0 + (dep + 3) * S
        d.text((x0, yb + 6), "%d mm thick" % round(dep + 3), fill=INK)

    # scale bar
    d.line([(20, top_h - 16), (20 + 10 * S, top_h - 16)], fill=INK, width=2)
    d.text((20, top_h - 32), "10 mm", fill=INK)

    # --- zoom row: top 12 mm of the pitch-10 cell, three tips -------------
    ZS = 26.0                     # px per mm, zoomed
    zw = 3 * colw + 20
    zy = top_h + 30
    d.text((20, zy - 22), "tip detail, pitch 10, top 12 mm:", fill=INK)
    for i, t in enumerate((0.0, 0.5, 2.0)):
        x0 = 20 + i * colw
        d.text((x0, zy), "tip %.1f mm  (flat %.2f %% of face)"
               % (t, 100 * (t / 10.0) ** 2), fill=INK)
        yz = zy + 18
        # clip: draw full profile into a tall temp image, crop 12 mm
        tmp = Image.new("RGB", (int(20 * ZS), int(12 * ZS)), BG)
        td = ImageDraw.Draw(tmp)
        profile(td, 0, 0, ZS, 10.0, 90.0, t, 20.0)
        td.line([(0, 0), (tmp.width, 0)], fill=EDGE)
        img.paste(tmp, (x0, yz))
    out = os.path.join(IMG, "grid_tip.png")
    img.save(out)
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
