"""
The coating's specular roughness against the FORM metric, with both baselines.

    Blender --background --factory-startup --python scripts/form_roughness.py

TWO JOBS IN ONE RUN, because they need the same renders.

**1. Supply the baseline `metrics/04` is missing.** Peak radiance ratio is
defined against the 0.05 matte black wall. `metrics/01` states the project's own
rule -- a ratio names its baseline, and the meaningful one is a flat plate of
the SAME COATING -- and metric 04 does not follow it. Measured
(results/FINDINGS_form_baseline.md): at theta = 0 a structured panel reads 1.34
against the 0.05 wall and a bare flat plate of its own coating reads 1.64. So
the panel is an IMPROVEMENT of 0.81 on its coating, and reads as a failure only
against the wrong reference. This run produces the flat-coating reference at
every theta and every roughness, which also re-normalises the main
form_buildable.json without re-rendering it.

**2. Sweep the parameter that turns out to dominate form.** Same measurement,
roughness varied, nothing else:

    spec_roughness   0.10     0.30     0.50
    theta=0 peak     119.92   1.644    0.361      (vs the 0.05 wall)

**332x.** The project pins `spec_roughness = 0.30` in every configuration on the
strength of one argument -- that it is an interior optimum for rho_dh (0.15
leaves a lobe narrow enough to aim at an observer, 0.50 approaches a diffuser).
That argument is about TOTAL REFLECTANCE. It has never been checked against the
form metric, which is the stated first priority and which is far more sensitive
to it than rho_dh is.

For scale: the whole nine-topology search spans 1.6x at matched process. This
one coating parameter spans 332x on the metric that matters most.

The flat plate needs no phase averaging -- it has no pitch, so there is no
phase. The structured designs get the full 16-position walk across one pitch,
for the reason metrics/04 gives: a 1D groove's peak spans 214x across stripe
phase, and three arbitrary draws is not a sampling of it.
"""

import sys
import os
import json
import time

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402
from form_buildable import (z_profile, recentre, rms_width, mtf_at,  # noqa: E402
                            NWIN, STRIPE_W, SPREAD_DEG, PERIODS_MM)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "renders", "form_r")
OUTJSON = os.path.join(RESULTS, "form_roughness.json")
CAND = os.path.join(RESULTS, "form_candidates.json")

SAMPLES = 512
RES_X, RES_Y = 1400, 620
THETAS = (-40.0, 0.0, 40.0)
N_PHASE = 16
ROUGHNESS = (0.10, 0.20, 0.30, 0.40, 0.50)
# three designs spanning the topologies, not the whole candidate list: this is
# a sensitivity study on a coating parameter, and if the parameter dominates it
# will dominate all of them
# Read from form_candidates.json rather than hard-coded, so renaming a
# candidate cannot silently drop it. It already did once: two of three tags
# here were stale after the blade was respecified as constant-thickness and the
# honeycomb as 6.5/0.08, the loop's `tag not in cands` guard skipped both, and
# the job reported [DONE] with 10 records instead of 20 and rc=0.
def _design_tags():
    import json as _j
    c = _j.load(open(CAND))
    keep = ("HONE", "CONE", "SHIN", "BL_FLAT")
    return tuple(e["tag"] for e in c
                 if any(k in e["tag"] for k in keep))[:3]


def measure(w_panel, w_ctrl, mm_per_px, phases, theta, cx, ortho, tag):
    """One (design, theta): walk the phases, return stats against the control.

    Takes WORLD windows, not pixel windows. `BR.to_pixel_window` projects
    through `scene.camera`, so calling it before a camera exists raises
    `'NoneType' object has no attribute 'matrix_world'` -- which is exactly what
    the first version of this script did, by hoisting the conversion to the call
    site to keep the signature short. Blender exits 0 even when the script
    raises, so the queue logged it as a success and the job produced nothing for
    a whole cycle. Convert inside, after the camera is set up.
    """
    acc_p = np.zeros(NWIN)
    acc_c = np.zeros(NWIN)
    peaks, peaks_c = [], []
    for zi, dz in enumerate(phases):
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, 0.0, ortho, RES_X, RES_Y, elev_deg=0.0)
        px_panel = BR.to_pixel_window(w_panel)
        px_ctrl = BR.to_pixel_window(w_ctrl)
        BR.set_world(0.0)
        BR.add_stripe(theta, cx, 0.0, STRIPE_W, ortho / 1.02,
                      strength=400.0, spread_deg=SPREAD_DEG, target_z=dz)
        exr = os.path.join(OUT, "%s_th%+05.1f_p%02d.exr" % (tag, theta, zi))
        BR.render_to(exr, exr.replace(".exr", ".png"))
        arr = BR.read_exr(exr, RES_X, RES_Y)
        pp = recentre(z_profile(arr, px_panel), NWIN)
        pc = recentre(z_profile(arr, px_ctrl), NWIN)
        acc_p += pp
        acc_c += pc
        peaks.append(float(pp.max()))
        peaks_c.append(float(pc.max()))
        try:
            os.remove(exr)
        except OSError:
            pass
    acc_p /= len(phases)
    acc_c /= len(phases)
    d = {"peak_panel": float(np.mean(peaks)),
         "peak_control": float(np.mean(peaks_c)),
         "peak_vs_wall": float(np.mean(peaks)) / float(np.mean(peaks_c)),
         "rms_mm": rms_width(acc_p, mm_per_px),
         "rms_control_mm": rms_width(acc_c, mm_per_px)}
    d.update(mtf_at(acc_p, mm_per_px, PERIODS_MM))
    return d


def scene_for(family, prm, rough):
    body, spec = BR.coating_split(0.76)
    cfg = {"tag": "r", "out_dir": OUT, "results_dir": OUT,
           "samples": SAMPLES, "res_x": RES_X, "res_y": RES_Y, "gpu": True,
           "spec_roughness": rough, "params": prm, "renders": [],
           "material_mode": "coating", "family": family,
           "coating": {"body": body, "spec_scale": spec, "roughness": rough}}
    cfg.update({k: v for k, v in COAT.items() if k not in ("spec_roughness",)})
    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    return p, ctrl_x0, total_w


def flat_scene(rough):
    """Flat plate of the coating, built as a SOLID SLAB.

    NOT `make_flat_plate`. That builds a single quad with no volume, so the face
    normal is undetermined, the Fresnel node saturates on the backface, and the
    specular term pins itself at `spec_scale` -- 6.05% instead of ~1.1%. The
    giveaway is that 45 and 60 degrees then read identical to four decimals.
    `make_diffuse` has no Fresnel node, which is why the 0.05 control was never
    affected and a rho=0 plate still reads exactly 0.

    A degenerate ridge panel (depth 0.001, one flat tip spanning the pitch) is
    a genuine slab with an unambiguous outward normal, and it is the same
    construction `fit_coating.py` validated the coating against.
    """
    body, spec = BR.coating_split(0.76)
    cfg = {"tag": "flat", "family": "ridge", "out_dir": OUT,
           "results_dir": OUT, "samples": SAMPLES, "res_x": RES_X,
           "res_y": RES_Y, "gpu": True, "material_mode": "coating",
           "rho_control": 0.05, "spec_roughness": rough,
           "coating": {"body": body, "spec_scale": spec, "ior": BR.MUSOU_IOR,
                       "roughness": rough},
           "params": dict(face_w=60.0, face_h=60.0, depth=0.001,
                          pitch_mean=50.0, tip_width=50.0, tip_round=False,
                          pitch_jitter=0.0, arc_segments=4, valley_round=0.0,
                          margin_depths=2.0),
           "renders": []}
    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    return p, ctrl_x0, ctrl_x0 + p.face_w


def main():
    os.makedirs(OUT, exist_ok=True)
    cands = {e["tag"]: e for e in json.load(open(CAND))}
    out = json.load(open(OUTJSON)) if os.path.exists(OUTJSON) else []
    done = {(r["what"], r["roughness"]) for r in out}
    t0 = time.time()

    for rough in ROUGHNESS:
        # --- the flat-coating reference: no pitch, so one phase is enough ---
        if ("flat", rough) not in done:
            p, ctrl_x0, total_w = flat_scene(rough)
            cx, ortho = total_w / 2.0, total_w * 1.02
            BR.configure_cycles(SAMPLES, True)
            wp, wc = BR.measurement_windows(p, ctrl_x0, None)
            rec = {"what": "flat", "roughness": rough, "thetas": {}}
            for th in THETAS:
                rec["thetas"]["%+.0f" % th] = measure(
                    wp, wc, ortho / RES_X, [0.0], th, cx, ortho,
                    "flat_r%02d" % (rough * 100))
            out.append(rec)
            json.dump(out, open(OUTJSON, "w"), indent=1)
            print("[FLAT ] r=%.2f  " % rough + "  ".join(
                "th%s %.4f" % (k, v["peak_vs_wall"])
                for k, v in rec["thetas"].items()), flush=True)

        for tag in _design_tags():
            if (tag, rough) in done or tag not in cands:
                continue
            e = cands[tag]
            p, ctrl_x0, total_w = scene_for(e["family"], e["params"], rough)
            cx, ortho = total_w / 2.0, total_w * 1.02
            BR.configure_cycles(SAMPLES, True)
            wp, wc = BR.measurement_windows(p, ctrl_x0, None)
            pitch = float(e["pitch"])
            phases = [(-pitch / 2.0) + pitch * i / N_PHASE
                      for i in range(N_PHASE)]
            rec = {"what": tag, "topology": e["topology"], "roughness": rough,
                   "thetas": {}}
            for th in THETAS:
                rec["thetas"]["%+.0f" % th] = measure(
                    wp, wc, ortho / RES_X, phases, th, cx, ortho,
                    "%s_r%02d" % (tag, rough * 100))
            out.append(rec)
            json.dump(out, open(OUTJSON, "w"), indent=1)
            print("[%s] r=%.2f  " % (e["topology"][:5], rough) + "  ".join(
                "th%s %.4f" % (k, v["peak_vs_wall"])
                for k, v in rec["thetas"].items()), flush=True)

    print("[DONE] %s  (%d records, %.0fs)"
          % (OUTJSON, len(out), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
