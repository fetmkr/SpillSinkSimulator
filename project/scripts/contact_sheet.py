"""
Build side-by-side comparison sheets from the renders already on disk.

    python3 scripts/contact_sheet.py

Axis 2 is judged by eye, so this puts the panel and the flat control next to
each other under the same laser line, at the same exposure, for the cases that
matter. Left half of every render is the flat control, right half is the panel
(the front view mirrors X, which is why the panel lands on the right).
"""

from __future__ import annotations

import os
import glob

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MTF = os.path.join(ROOT, "renders", "mtf")
OUT = os.path.join(ROOT, "results")


def load_linear(path):
    a = np.asarray(Image.open(path)).astype(np.float64)
    a = a[..., :3].mean(axis=2) / max(a.max(), 1.0)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def sheet(cases, thetas, out_name, title, vmax, zi=1):
    fig, axes = plt.subplots(len(cases), len(thetas),
                             figsize=(3.1 * len(thetas), 2.4 * len(cases)),
                             squeeze=False)
    for r, (tag, label) in enumerate(cases):
        for c, th in enumerate(thetas):
            ax = axes[r][c]
            pat = os.path.join(MTF, f"{tag}__mtf_th{th:+05.1f}_z{zi}.png")
            hits = glob.glob(pat)
            if not hits:
                ax.text(0.5, 0.5, "missing", ha="center", va="center",
                        fontsize=7)
                ax.set_xticks([]); ax.set_yticks([])
                continue
            im = load_linear(hits[0])
            ax.imshow(im, cmap="inferno", vmin=0.0, vmax=vmax,
                      interpolation="nearest")
            ax.set_xticks([]); ax.set_yticks([])
            if r == 0:
                ax.set_title(f"θ = {th:+.0f}°", fontsize=9)
            if c == 0:
                ax.set_ylabel(label, fontsize=8)
    fig.suptitle(title + "   (left = flat control, right = panel;"
                 f"  same exposure, linear 0–{vmax:g})", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.965))
    path = os.path.join(OUT, out_name)
    fig.savefig(path, dpi=125)
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))
    return path


if __name__ == "__main__":
    thetas = (-40.0, -20.0, 0.0, 20.0, 40.0)

    # exposure set so the control line is clearly visible; the panel is then
    #読み as "how much of that is left"
    sheet([("C_lip005", "rho 0.005\nrough 0.30"),
           ("C_base", "rho 0.02\nrough 0.30"),
           ("C_jit25", "rho 0.02 + 25°\nangle jitter"),
           ("C_alt", "rho 0.02\nalternating")],
          thetas, "sheet_candidates.png",
          "Laser line on panel vs flat wall", vmax=0.02)

    # heavily stretched, to show the SHAPE of what little comes back
    sheet([("C_lip005", "rho 0.005\nrough 0.30"),
           ("C_base", "rho 0.02\nrough 0.30")],
          thetas, "sheet_shape.png",
          "Same renders, stretched 100x to show the returned shape",
          vmax=0.0002)
