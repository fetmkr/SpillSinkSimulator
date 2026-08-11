"""
Pull panel/control crops out of the 32-bit EXRs into a .npz.

    Blender --background --factory-startup --python scripts/dump_crops.py

The 8-bit PNGs cannot show this: the panel returns 1e-3 to 1e-4 of the control,
which is below one sRGB code value, so the panel half of every PNG clips to
pure black no matter how it is stretched. The EXR keeps the real numbers.
"""

import sys
import os
import glob

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from profile2d import PanelParams                                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MTF = os.path.join(ROOT, "renders", "mtf")
OUT = os.path.join(ROOT, "results", "crops.npz")

RES_X, RES_Y = 1200, 900
BASE = {"slat_deg": 45.0, "slat_len": 79.2, "pitch_mean": 40.0,
        "baffle_rows": 2, "baffle_deg": -45.0, "baffle_len": 48.8,
        "baffle_pitch": 60.0}


def main():
    # windows depend only on the panel envelope, which is the same for every
    # case here, so one scene build is enough to locate them
    cfg = {"params": dict(BASE), "res_x": RES_X, "res_y": RES_Y}
    BR.clear_scene()
    p, _, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    ortho = total_w * 1.02
    BR.setup_camera(total_w / 2.0, 0.0, ortho, RES_X, RES_Y)
    w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)
    px_p = [int(v) for v in BR.to_pixel_window(w_panel)]
    px_c = [int(v) for v in BR.to_pixel_window(w_ctrl)]
    print("[CROP] panel", px_p, "ctrl", px_c)

    out = {"px_panel": np.array(px_p), "px_ctrl": np.array(px_c),
           "mm_per_px": np.array([ortho / RES_X])}
    for f in sorted(glob.glob(os.path.join(MTF, "*.exr"))):
        key = os.path.splitext(os.path.basename(f))[0]
        arr = BR.read_exr(f, RES_X, RES_Y)
        out[key + "|panel"] = arr[px_p[2]:px_p[3], px_p[0]:px_p[1]].mean(axis=2)
        out[key + "|ctrl"] = arr[px_c[2]:px_c[3], px_c[0]:px_c[1]].mean(axis=2)
    np.savez_compressed(OUT, **out)
    print("[DONE]", OUT, len(out), "arrays")


if __name__ == "__main__":
    main()
