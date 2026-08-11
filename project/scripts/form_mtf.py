"""
Axis 2, done properly: how much form survives.

    Blender --background --factory-startup --python scripts/form_mtf.py

The thing to kill is legibility. In the reference photo the aerial word is soft
while the same word, written by the beams that flew past it, reads razor sharp
on the side walls. Total reflected energy does not describe that at all: a dim
but sharp line still reads as a letter, and the same photons smeared over the
aperture read as haze.

Method
------
Light transport is linear, so the response to ONE thin line -- the line spread
function -- determines the response to any pattern. Fire a 2 mm collimated line
at the panel and at the flat control in the same frame, take the Z profile of
what comes back, and everything else follows:

    fwhm_mm       how wide a single line comes back. The flat control returns
                  the beam itself; the panel should return something on the
                  order of its slat pitch or wider.
    peak_over_med how much the line stands out from its own surroundings.
    mtf(period)   |FFT(LSF)| normalised at DC, read at the spatial periods a
                  viewer would actually resolve. MTF near 0 at a given period
                  means stripe detail at that period cannot be reconstructed
                  from what the wall returns, whatever its brightness.

The panel has irregular pitch, so its response is not shift invariant. Each
case is therefore measured at several line positions and averaged, rather than
trusting one lucky landing spot.
"""

import sys
import os
import json

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402

# one dispatcher for all three geometry families, kept in blender_render so
# there is a single place that knows which family a parameter object belongs to
describe = BR.describe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "mtf")
RESULTS = os.path.join(ROOT, "results")

RES_X, RES_Y = 1200, 900
SAMPLES = 1024
STRIPE_W = 2.0
# The first run used spread 1.0 deg at 900 mm, which blurs the "2 mm" line to
# 2 + 900*tan(1) = 18 mm before it ever reaches the panel; the control measured
# 8.4 mm FWHM, so there was no sharp line to destroy in the first place.
SPREAD_DEG = 0.05
THETAS = (-40.0, -20.0, 0.0, 20.0, 40.0)
LINE_Z = (-60.0, -13.0, 41.0)          # deliberately not on the slat pitch
PERIODS_MM = (10.0, 20.0, 40.0, 80.0)


def z_profile(arr, win):
    x0, x1, z0, z1 = win
    sub = arr[int(z0):int(z1), int(x0):int(x1), :].mean(axis=2)
    return sub.mean(axis=1)            # index 0 = bottom row


def recentre(prof, mm_per_px, n):
    """Shift a profile so its centroid sits at the centre of an n-sample window."""
    idx = np.arange(prof.size, dtype=np.float64)
    tot = prof.sum()
    c = float((idx * prof).sum() / tot) if tot > 1e-20 else prof.size / 2.0
    out = np.zeros(n)
    lo = int(round(c)) - n // 2
    for i in range(n):
        j = lo + i
        if 0 <= j < prof.size:
            out[i] = prof[j]
    return out


def fwhm(prof, mm_per_px):
    if prof.max() <= 0:
        return float("nan")
    half = prof.max() / 2.0
    above = np.where(prof >= half)[0]
    if above.size == 0:
        return float("nan")
    return (above[-1] - above[0] + 1) * mm_per_px


def mtf_at(prof, mm_per_px, periods):
    p = prof - prof.min()
    tot = p.sum()
    if tot <= 1e-20:
        return {f"mtf_{int(q)}mm": float("nan") for q in periods}
    f = np.fft.rfft(p / tot)
    freqs = np.fft.rfftfreq(p.size, d=mm_per_px)      # cycles per mm
    out = {}
    for q in periods:
        target = 1.0 / q
        k = int(np.argmin(np.abs(freqs - target)))
        out[f"mtf_{int(q)}mm"] = float(np.abs(f[k]) / np.abs(f[0]))
    return out


def stats(prof, mm_per_px, periods):
    tot = float(prof.sum())
    # Concentration, not peak-over-median: most of the profile is exactly zero
    # here, so a median background divides by zero and reports inf for every
    # case. This asks instead what fraction of the returned energy lands in the
    # central 10 mm -- 1.0 means the line came back intact, and a value near
    # 10mm/profile_width means it came back as a formless smear.
    n = prof.size
    half = max(1, int(round(5.0 / mm_per_px)))
    core = float(prof[n // 2 - half: n // 2 + half + 1].sum())
    d = {
        "fwhm_mm": fwhm(prof, mm_per_px),
        "peak": float(prof.max()),
        "total": tot,
        "core_frac": core / tot if tot > 1e-20 else float("nan"),
        "rms_mm": rms_width(prof, mm_per_px),
    }
    d.update(mtf_at(prof, mm_per_px, periods))
    return d


def rms_width(prof, mm_per_px):
    tot = prof.sum()
    if tot <= 1e-20:
        return float("nan")
    z = (np.arange(prof.size) - prof.size / 2.0) * mm_per_px
    w = prof / tot
    c = float((z * w).sum())
    return float(np.sqrt(max(float(((z - c) ** 2 * w).sum()), 0.0)))


def run_case(tag, params, extra=None):
    cfg = {"tag": tag, "out_dir": OUT, "results_dir": RESULTS,
           "samples": SAMPLES, "res_x": RES_X, "res_y": RES_Y, "gpu": True,
           "params": params, "renders": []}
    cfg.update(extra or {})

    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    cx, cz = total_w / 2.0, 0.0
    ortho = total_w * 1.02
    mm_per_px = ortho / RES_X
    BR.configure_cycles(SAMPLES, True)
    w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)

    nwin = 361                                  # ~ +/- 180 mm of profile
    out = {"tag": tag, "derived": describe(p), "warnings": cs.warnings,
           "stripe_w_mm": STRIPE_W, "mm_per_px": mm_per_px, "thetas": {}}

    for theta in THETAS:
        acc_p = np.zeros(nwin)
        acc_c = np.zeros(nwin)
        png_ref = None
        for zi, z0 in enumerate(LINE_Z):
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(cx, cz, ortho, RES_X, RES_Y, elev_deg=0.0)
            px_panel = BR.to_pixel_window(w_panel)
            px_ctrl = BR.to_pixel_window(w_ctrl)
            BR.set_world(0.0)
            BR.add_stripe(theta, cx, cz, STRIPE_W, total_w, strength=400.0,
                          spread_deg=SPREAD_DEG, target_z=z0)

            name = f"{tag}__mtf_th{theta:+05.1f}_z{zi}"
            exr = os.path.join(OUT, name + ".exr")
            png = os.path.join(OUT, name + ".png")
            BR.render_to(exr, png)
            png_ref = png_ref or png
            arr = BR.read_exr(exr, RES_X, RES_Y)

            # both profiles are recentred on the CONTROL centroid, so the
            # panel keeps any real displacement of its return
            pc = z_profile(arr, px_ctrl)
            pp = z_profile(arr, px_panel)
            tot = pc.sum()
            c = float((np.arange(pc.size) * pc).sum() / tot) if tot > 1e-20 else pc.size / 2
            lo = int(round(c)) - nwin // 2
            for i in range(nwin):
                j = lo + i
                if 0 <= j < pc.size:
                    acc_c[i] += pc[j]
                    acc_p[i] += pp[j]

        sp = stats(acc_p, mm_per_px, PERIODS_MM)
        sc = stats(acc_c, mm_per_px, PERIODS_MM)
        out["thetas"][f"{theta:+.0f}"] = {
            "panel": sp, "control": sc,
            "widen": sp["fwhm_mm"] / sc["fwhm_mm"] if sc["fwhm_mm"] else float("nan"),
            "energy_ratio": sp["total"] / sc["total"] if sc["total"] else float("nan"),
            "panel_profile": acc_p.tolist(),
            "control_profile": acc_c.tolist(),
            "png": png_ref,
        }
        print("[MTF] %-22s th=%+05.1f  rms %7.2f/%5.2f mm  core %.3f/%.3f  "
              "MTF20 %.4f MTF40 %.4f  energy %.4g"
              % (tag, theta, sp["rms_mm"], sc["rms_mm"],
                 sp["core_frac"], sc["core_frac"],
                 sp["mtf_20mm"], sp["mtf_40mm"],
                 out["thetas"][f"{theta:+.0f}"]["energy_ratio"]), flush=True)
    return out


BASE = {"slat_deg": 45.0, "slat_len": 79.2, "pitch_mean": 40.0,
        "baffle_rows": 2, "baffle_deg": -45.0, "baffle_len": 48.8,
        "baffle_pitch": 60.0}

DIFF = {"material_mode": "all_diffuse"}

# Everything below sits on the best combination found so far: a near-black
# entrance so single bounces are suppressed, a bright interior so whatever does
# get in forgets where it entered, and a partly-rough deflector so the specular
# lobe is spread instead of aimed.
BEST = {"spec_roughness": 0.30, "rho_slat": 0.02, "rho_chamber": 0.90}

# At normal incidence every case so far returned core ~1.0: a ray reflecting
# between PARALLEL 45 degree slats is only translated, never displaced in Z, so
# it exits at the height it entered. These break that parallelism.
CASES_PARALLEL = [
    ("C_base", dict(BASE), dict(BEST)),
    ("C_jit10", dict(BASE, slat_deg_jitter=10.0), dict(BEST)),
    ("C_jit25", dict(BASE, slat_deg_jitter=25.0), dict(BEST)),
    ("C_alt", dict(BASE, slat_mode="alternate"), dict(BEST)),
    ("C_alt_jit25", dict(BASE, slat_mode="alternate", slat_deg_jitter=25.0),
     dict(BEST)),
    # blackest achievable entrance, on its own and combined
    ("C_lip005", dict(BASE), dict(BEST, rho_slat=0.005)),
    ("C_lip005_alt_jit25",
     dict(BASE, slat_mode="alternate", slat_deg_jitter=25.0),
     dict(BEST, rho_slat=0.005)),
]

CASES_OLD = [
    # --- the all-black family: what has been measured so far ---
    ("A_spec_black", dict(BASE),
     {"spec_roughness": 0.05, "rho_slat": 0.05, "rho_chamber": 0.05}),
    ("A_rough30_black", dict(BASE),
     {"spec_roughness": 0.30, "rho_slat": 0.05, "rho_chamber": 0.05}),
    ("A_alldiffuse_black", dict(BASE),
     dict(DIFF, rho_slat=0.05, rho_chamber=0.05)),

    # --- black entrance, bright diffusing interior ---
    # Single bounces off anything the observer can see keep the beam's
    # position, so they are suppressed with the darkest entrance. Light that
    # does get in then has to survive long enough to forget where it entered,
    # which needs a BRIGHT interior, not a black one.
    ("B_chamber30", dict(BASE), dict(DIFF, rho_slat=0.02, rho_chamber=0.30)),
    ("B_chamber60", dict(BASE), dict(DIFF, rho_slat=0.02, rho_chamber=0.60)),
    ("B_chamber90", dict(BASE), dict(DIFF, rho_slat=0.02, rho_chamber=0.90)),
    # same, but keep the specular deflector on the way in
    ("B_chamber90_spec", dict(BASE),
     {"spec_roughness": 0.30, "rho_slat": 0.02, "rho_chamber": 0.90}),
    # bright interior with a finer entrance, i.e. a smaller exit aperture
    ("B_chamber90_p20", dict(BASE, pitch_mean=20.0, slat_len=39.6,
                             baffle_len=48.8),
     dict(DIFF, rho_slat=0.02, rho_chamber=0.90)),
]


CASES = CASES_PARALLEL


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    res = [run_case(t, p, e) for t, p, e in CASES]
    path = os.path.join(RESULTS, "form_mtf.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=2)
    print("[DONE]", path, flush=True)


if __name__ == "__main__":
    main()
