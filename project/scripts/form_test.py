"""
Axis 2: form destruction.

    Blender --background --factory-startup --python scripts/form_test.py

Axis 1 (total reflected light) says nothing about whether what comes back
still reads as a line. A dim but sharp coil line still steals attention; the
same photon count spread into a formless smudge reads as atmosphere and gets
ignored. So this fires a narrow near-collimated stripe at the panel and at the
flat control in the same frame, and measures the Z profile of what returns.

Metrics, per surface:
    rms_width   second moment of the returned Z profile, in mm. The incident
                stripe is `stripe_w` mm wide, so a flat plate should return
                roughly stripe_w / cos(theta) and a working cavity should
                return something on the order of its aperture pitch or wider.
    peak_ratio  profile peak divided by profile mean. A sharp line has a high
                peak against a dark background; a smudge approaches 1.
    spread_gain rms_width(panel) / rms_width(control) -- the headline number.

Both surfaces are lit by the same stripe in the same render, so beam power and
cos(theta) falloff cancel.
"""

import sys
import os
import json

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile2d import PanelParams, build_cross_section, describe   # noqa: E402
import blender_render as BR                                        # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "form")
RESULTS = os.path.join(ROOT, "results")

RES_X, RES_Y = 1400, 700
SAMPLES = 1024
STRIPE_W = 6.0
THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)


def z_profile(arr, px_win, mm_per_px):
    """Sum a measurement window across X and return (z_mm, profile)."""
    x0, x1, z0, z1 = px_win
    sub = arr[int(z0):int(z1), int(x0):int(x1), :].mean(axis=2)
    prof = sub.mean(axis=1)                      # index 0 = bottom row
    z = (np.arange(prof.size) - prof.size / 2.0) * mm_per_px
    return z, prof


def profile_stats(z, prof):
    tot = float(prof.sum())
    if tot <= 1e-12:
        return {"rms_width_mm": float("nan"), "peak_ratio": float("nan"),
                "total": tot}
    w = prof / tot
    c = float((z * w).sum())
    var = float(((z - c) ** 2 * w).sum())
    return {
        "rms_width_mm": float(np.sqrt(max(var, 0.0))),
        "peak_ratio": float(prof.max() / (prof.mean() + 1e-30)),
        "centroid_mm": c,
        "total": tot,
    }


def run_case(tag, params, extra=None):
    cfg = {
        "tag": tag,
        "out_dir": OUT,
        "results_dir": RESULTS,
        "samples": SAMPLES,
        "res_x": RES_X,
        "res_y": RES_Y,
        "gpu": True,
        "params": params,
        "renders": [],
    }
    cfg.update(extra or {})

    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    cx, cz = total_w / 2.0, 0.0
    ortho = total_w * 1.02
    BR.configure_cycles(SAMPLES, True)

    w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)
    mm_per_px = ortho / RES_X

    out = {"tag": tag, "derived": describe(p), "warnings": cs.warnings,
           "stripe_w_mm": STRIPE_W, "thetas": {}}

    for theta in THETAS:
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, cz, ortho, RES_X, RES_Y, elev_deg=0.0)
        px_panel = BR.to_pixel_window(w_panel)
        px_ctrl = BR.to_pixel_window(w_ctrl)

        BR.set_world(0.0)
        BR.add_stripe(theta, cx, cz, STRIPE_W, total_w, strength=400.0,
                      spread_deg=1.0)

        name = f"{tag}__form_th{theta:+05.1f}"
        exr = os.path.join(OUT, name + ".exr")
        png = os.path.join(OUT, name + ".png")
        BR.render_to(exr, png)
        arr = BR.read_exr(exr, RES_X, RES_Y)

        zp, pp = z_profile(arr, px_panel, mm_per_px)
        zc, pc = z_profile(arr, px_ctrl, mm_per_px)
        sp = profile_stats(zp, pp)
        sc = profile_stats(zc, pc)
        gain = sp["rms_width_mm"] / sc["rms_width_mm"] if sc["rms_width_mm"] else float("nan")

        out["thetas"][f"{theta:+.0f}"] = {
            "panel": sp, "control": sc, "spread_gain": gain,
            "energy_ratio": sp["total"] / sc["total"] if sc["total"] else float("nan"),
            "png": png,
        }
        print("[FORM] %-18s th=%+05.1f  rms panel %7.2f mm  ctrl %6.2f mm  "
              "gain %6.2fx   peak/mean %7.1f vs %7.1f   energy %.4f"
              % (tag, theta, sp["rms_width_mm"], sc["rms_width_mm"], gain,
                 sp["peak_ratio"], sc["peak_ratio"],
                 out["thetas"][f"{theta:+.0f}"]["energy_ratio"]), flush=True)
    return out


CASES = [
    # coarse pitch: the configuration the lip law points at
    ("coarse_p40", {"slat_deg": 45.0, "slat_len": 79.2, "pitch_mean": 40.0,
                    "baffle_rows": 2, "baffle_deg": -45.0, "baffle_len": 48.8,
                    "baffle_pitch": 60.0}, None),
    # same, with the chamber stripped out: does stage 2 matter for FORM even
    # though it did not move the brightness number at all?
    ("coarse_p40_nobaffle", {"slat_deg": 45.0, "slat_len": 79.2,
                             "pitch_mean": 40.0, "baffle_rows": 0}, None),
    # fine pitch, for the visual comparison
    ("fine_p10", {"slat_deg": 45.0, "slat_len": 19.8, "pitch_mean": 10.0,
                  "baffle_rows": 2, "baffle_deg": -45.0, "baffle_len": 48.8}, None),
    # symmetric slats
    ("alt_p20", {"slat_deg": 30.0, "slat_len": 46.2, "pitch_mean": 16.5,
                 "slat_mode": "alternate", "baffle_rows": 1,
                 "baffle_deg": -45.0, "baffle_len": 30.0}, None),
    # all-diffuse, to see what losing the specular stage 1 does to form
    ("coarse_p40_diffuse", {"slat_deg": 45.0, "slat_len": 79.2,
                            "pitch_mean": 40.0, "baffle_rows": 2,
                            "baffle_deg": -45.0, "baffle_len": 48.8},
     {"material_mode": "all_diffuse"}),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    results = [run_case(t, p, e) for t, p, e in CASES]
    path = os.path.join(RESULTS, "form.json")
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
