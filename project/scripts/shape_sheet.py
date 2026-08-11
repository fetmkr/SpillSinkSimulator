"""
Comparison sheets built from the 32-bit crops, not the 8-bit PNGs.

    python3 scripts/shape_sheet.py

Two sheets, because the two questions need different exposures:

  sheet_A_brightness  every tile on ONE exposure, scaled to the flat control.
                      Answers "how much dimmer is the wall spill".

  sheet_B_shape       every tile normalised to its OWN peak. Answers "and what
                      is left of the line's shape", which brightness hides.
"""

from __future__ import annotations

import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
NPZ = os.path.join(RESULTS, "crops.npz")

THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)
CASES = [
    ("C_lip005", "rho 0.005\nrough 0.30"),
    ("C_base", "rho 0.02\nrough 0.30"),
    ("C_jit25", "rho 0.02\n+25° jitter"),
    ("C_alt", "rho 0.02\nalternating"),
]
ZI = 1


def key(tag, th, what):
    return f"{tag}__mtf_th{th:+05.1f}_z{ZI}|{what}"


def build(d, mode, out_name, title):
    ncol = len(THETAS)
    nrow = len(CASES) + 1
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.9 * ncol, 2.0 * nrow),
                             squeeze=False)

    # top row: the flat control, i.e. what a plain coated wall does
    ref = {}
    for c, th in enumerate(THETAS):
        a = d[key(CASES[0][0], th, "ctrl")]
        ref[th] = float(a.max())
        ax = axes[0][c]
        ax.imshow(a, cmap="inferno", vmin=0, vmax=ref[th] if mode == "shape"
                  else ref[th], interpolation="nearest", aspect="auto")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"θ = {th:+.0f}°", fontsize=9)
        if c == 0:
            ax.set_ylabel("FLAT WALL\n(control)", fontsize=8,
                          color="#c02020", fontweight="bold")

    for r, (tag, label) in enumerate(CASES, start=1):
        for c, th in enumerate(THETAS):
            ax = axes[r][c]
            k = key(tag, th, "panel")
            if k not in d:
                ax.text(0.5, 0.5, "missing", ha="center", va="center", fontsize=7)
                ax.set_xticks([]); ax.set_yticks([])
                continue
            a = d[k]
            pk = float(a.max())
            vmax = pk if mode == "shape" else ref[th]
            ax.imshow(a, cmap="inferno", vmin=0, vmax=max(vmax, 1e-12),
                      interpolation="nearest", aspect="auto")
            ax.set_xticks([]); ax.set_yticks([])
            rel = pk / ref[th] if ref[th] > 0 else float("nan")
            ax.text(0.02, 0.94, f"peak {rel:.4f}x", transform=ax.transAxes,
                    fontsize=7, color="#ffffff", va="top")
            if c == 0:
                ax.set_ylabel(label, fontsize=8)

    fig.suptitle(title, fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    path = os.path.join(RESULTS, out_name)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print("wrote", os.path.relpath(path, ROOT))
    return path


if __name__ == "__main__":
    d = np.load(NPZ)
    build(d, "bright", "sheet_A_brightness.png",
          "A single laser line — every tile at the SAME exposure as the flat wall.\n"
          "Panel rows look black because that is the actual result; the label gives peak vs the wall.")
    build(d, "shape", "sheet_B_shape.png",
          "Same renders, each tile normalised to its OWN peak — brightness removed, only shape left.\n"
          "A line means the form survived; a smear or scatter means it did not.")
