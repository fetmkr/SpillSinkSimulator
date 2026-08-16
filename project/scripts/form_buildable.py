"""
Form destruction — the project's stated FIRST priority — on the buildable set.

    Blender --background --factory-startup --python scripts/form_buildable.py

WHY THIS EXISTS. Every ranking this project has produced measures how much light
comes back. The stated priority is the opposite one: destroy the FORM of what
comes back, so the wall reads as texture and not as letters. `results/
PEER_REVIEW.md` calls this out as a serious objection -- a figure of merit that
does not measure the first priority -- and it is correct.

WHAT IS FIXED HERE relative to `form_mtf.py`:

**Stripe phase is averaged, not sampled three times.** `form_mtf.LINE_Z` is
three hand-picked Z positions "deliberately not on the slat pitch". For a
structure with a pitch, the answer depends on whether the stripe lands on a wall
top or in a cell, and `metrics/04_peak_radiance.md` records that a 1D groove's
peak spans **214x** across that phase. Three arbitrary draws is not a sampling
of phase; it is three arbitrary draws. Here the stripe walks **N_PHASE positions
across exactly one pitch** of the design under test, and every reported number is
the mean over that walk. That is the precondition metrics/04 sets before its
numbers are quotable at all.

**Metric 03 is not computed.** `core_frac` is retired: its denominator is the
energy inside the measurement window, so a design that smears light out of the
window improves its own score. Measured demonstration in metrics/03: a cone at
depth 120 has twice the rms smear of one at depth 50 and a HIGHER core fraction.
It is not in this script and must not be added back.

WHAT IS REPORTED, in order of how much weight it can carry:

    rms_mm       metric 02. No known defect. Ranks designs monotonically.
                 Read against the flat control in the same frame, which is the
                 stripe's own footprint and therefore the floor.
    peak_ratio   metric 04. Peak of the panel profile over peak of the control
                 profile, same stripe, same frame. This is the quantity that
                 decides whether the wall copy is visible, and it folds
                 brightness and blur together -- but see its own file for why it
                 was not quotable before phase averaging.
    mtf_20mm     metric 07. Supporting only: |FFT| discards phase, so a smear
                 that is SHIFTED rather than SPREAD is not penalised, and for a
                 3D array that spreads azimuthally this UNDER-reports.

theta = 0 is included even though metrics/02 says it cannot rank designs there
-- observer and beam are collinear, the first hit is visible, one bounce cannot
displace a photon, and every family ever tried returns an unsmeared line. It is
included precisely so that statement is either confirmed on this new set or
broken by it.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "renders", "form_b")
OUTJSON = os.path.join(RESULTS, "form_buildable.json")
CAND = os.path.join(RESULTS, "form_candidates.json")

SAMPLES = 512
RES_X, RES_Y = 1400, 620
# Default probe = the DEPLOYMENT beam (user 2026-08-16: "빔 2mm 쓰지마.
# 기본을 5-10mm"). 7.5 mm is the midpoint of the expected 5-10 mm at the
# wall (LaserCube Ultra MK2, 3-6 m throw). Historical numbers were taken
# at 2.0; any comparison against them must set STRIPE_W explicitly.
STRIPE_W = 7.5
SPREAD_DEG = 0.05
THETAS = (-40.0, 0.0, 40.0)
N_PHASE = 16                     # stripe positions across one pitch
PERIODS_MM = (10.0, 20.0, 40.0)
NWIN = 361                       # profile window, samples


# The four statistics live in `form_metrics` so the Mitsuba cross-check scores
# its images with the SAME code. A second renderer that reimplemented `rms_width`
# could disagree because of the statistic rather than the transport, and the
# cross-check would prove nothing.
from form_metrics import z_profile, recentre, rms_width, mtf_at   # noqa: E402


def run_case(entry):
    tag = entry["tag"]
    family = entry["family"]
    prm = entry["params"]
    pitch = float(entry["pitch"])

    # Roughness is an entry-level knob (phase 5.6 sweeps it); every caller
    # that omits it gets the historical 0.30 and reproduces old numbers.
    # `phi` rotates the PANEL about its normal (phase 5.9) — the stripe, the
    # control and the windows stay fixed, so this is beam azimuth. Callers
    # that omit it get the historical phi = 0. Note the phase walk still
    # steps world-z by pitch/N_PHASE; at phi != 0 the pattern period along
    # world z stretches by 1/cos(phi), so the walk under-covers one period
    # by that factor — acceptable for phi <= 30 (13 %), recorded here.
    rough = float(entry.get("roughness", 0.30))
    cfg = {"tag": tag, "out_dir": OUT, "results_dir": OUT,
           "samples": SAMPLES, "res_x": RES_X, "res_y": RES_Y, "gpu": True,
           "spec_roughness": rough, "params": prm, "renders": [],
           "material_mode": "coating"}
    if entry.get("phi"):
        cfg["phi_deg"] = float(entry["phi"])
    # Phase 8: the AR window family reads its plate/void spec from cfg["ar"]
    if entry.get("ar") is not None:
        cfg["ar"] = entry["ar"]
    # Phase 9.2: partial paint -- coating above the depth plane, bare below
    if entry.get("paint_depth") is not None:
        cfg["paint_depth"] = float(entry["paint_depth"])
        cfg["deep_coating"] = entry.get("deep_coating", {})
    body, spec = BR.coating_split(0.76)          # the fitted nominal split
    cfg["coating"] = {"body": body, "spec_scale": spec, "roughness": rough}
    cfg.update({k: v for k, v in COAT.items() if k not in ("spec_roughness",)})
    cfg["family"] = family
    # A CROSS-CHECK NEEDS THE SAME MATERIAL IN BOTH CODES. The fitted coating is
    # a Fresnel node feeding a diffuse/glossy mix, which Mitsuba cannot be asked
    # to reproduce exactly, so a disagreement on it would be about materials
    # rather than transport. `entry["rho"]` switches this run to a pure
    # Lambertian -- the same BRDF in both -- and is set only by the cross-check.
    # It comes after the COAT update because that update owns `rho_slat`.
    if entry.get("rho") is not None:
        r = float(entry["rho"])
        cfg["material_mode"] = "all_diffuse"
        cfg.update(rho_slat=r, rho_chamber=r, rho_specular=r)
        cfg["rho_control"] = float(entry.get("rho_control", 0.05))

    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    cx, cz = total_w / 2.0, 0.0
    ortho = total_w * 1.02
    mm_per_px = ortho / RES_X
    BR.configure_cycles(SAMPLES, True)
    w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)
    # ADAPTIVE WINDOW (user 2026-08-16: "측정창 키워"). The phase walk spans
    # one pitch; if the default 30 % z-inset leaves a window smaller than
    # pitch + stripe, the stripe exits the window at extreme phases and the
    # peak ratio divides zero by zero (the Phase 7 box read NaN). Open the
    # inset just enough, floor at 5 % of the face.
    need = pitch + 2.0 * STRIPE_W
    have = w_panel[3] - w_panel[2]
    if have < need:
        dz = max(0.05 * p.face_h, (p.face_h - need) / 2.0)
        w_panel = (w_panel[0], w_panel[1],
                   -p.face_h / 2 + dz, p.face_h / 2 - dz)
        w_ctrl = (w_ctrl[0], w_ctrl[1],
                  -p.face_h / 2 + dz, p.face_h / 2 - dz)

    out = {"tag": tag, "topology": entry["topology"],
           "process": entry["process"], "pitch": pitch,
           "mm_per_px": mm_per_px, "n_phase": N_PHASE, "thetas": {}}

    # phases walk exactly one pitch, so the mean is over the full period rather
    # than over three arbitrary draws
    phases = [(-pitch / 2.0) + pitch * i / N_PHASE for i in range(N_PHASE)]

    for theta in THETAS:
        rec = {"per_phase": [], "peak_ratio": [], "rms_mm": []}
        acc_p = np.zeros(NWIN)
        acc_c = np.zeros(NWIN)
        for zi, dz in enumerate(phases):
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(cx, cz, ortho, RES_X, RES_Y, elev_deg=0.0)
            px_panel = BR.to_pixel_window(w_panel)
            px_ctrl = BR.to_pixel_window(w_ctrl)
            BR.set_world(0.0)
            BR.add_stripe(theta, cx, cz, STRIPE_W, total_w, strength=400.0,
                          spread_deg=SPREAD_DEG, target_z=dz)
            name = "%s__th%+05.1f_p%02d" % (tag, theta, zi)
            exr = os.path.join(OUT, name + ".exr")
            BR.render_to(exr, os.path.join(OUT, name + ".png"))
            arr = BR.read_exr(exr, RES_X, RES_Y)
            pp = recentre(z_profile(arr, px_panel), NWIN)
            pc = recentre(z_profile(arr, px_ctrl), NWIN)
            acc_p += pp
            acc_c += pc
            pk = float(pp.max()) / float(pc.max()) if pc.max() > 0 else float("nan")
            rec["peak_ratio"].append(pk)
            rec["rms_mm"].append(rms_width(pp, mm_per_px))
            try:
                os.remove(exr)
            except OSError:
                pass

        acc_p /= N_PHASE
        acc_c /= N_PHASE
        d = {"rms_mm": rms_width(acc_p, mm_per_px),
             "rms_control_mm": rms_width(acc_c, mm_per_px),
             "peak_ratio_mean": float(np.mean(rec["peak_ratio"])),
             "peak_ratio_sd": float(np.std(rec["peak_ratio"])),
             "peak_ratio_max": float(np.max(rec["peak_ratio"])),
             "peak_ratio_span": (float(np.max(rec["peak_ratio"]))
                                 / max(float(np.min(rec["peak_ratio"])), 1e-12)),
             "rms_sd_mm": float(np.std(rec["rms_mm"]))}
        d.update(mtf_at(acc_p, mm_per_px, PERIODS_MM))
        out["thetas"]["%+.0f" % theta] = d
        print("   th%+5.0f  rms %6.2f mm (ctrl %5.2f)  peak %.5f +/-%.5f  "
              "span %5.1fx  mtf20 %.3f"
              % (theta, d["rms_mm"], d["rms_control_mm"],
                 d["peak_ratio_mean"], d["peak_ratio_sd"],
                 d["peak_ratio_span"], d.get("mtf_20mm", float("nan"))),
              flush=True)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cands = json.load(open(CAND))
    done = {}
    if os.path.exists(OUTJSON):
        done = {e["tag"]: e for e in json.load(open(OUTJSON))}
    results = list(done.values())
    t0 = time.time()
    for i, e in enumerate(cands, 1):
        if e["tag"] in done:
            print("[%2d/%2d] %-30s cached" % (i, len(cands), e["tag"]),
                  flush=True)
            continue
        print("[%2d/%2d] %-30s %s" % (i, len(cands), e["tag"], e["topology"]),
              flush=True)
        try:
            results.append(run_case(e))
        except Exception as exc:
            print("[FAIL] %s: %s" % (e["tag"], exc), flush=True)
            continue
        json.dump(results, open(OUTJSON, "w"), indent=1)
    print("[DONE] %s  (%d cases, %.0fs)"
          % (OUTJSON, len(results), time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
