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
# Sampling density in mm per pixel, held FIXED so the instrument does not
# change with the sample (see the note in run_case). Set to 0 to restore the
# pre-2026-08-20 behaviour of a constant pixel count, which is what every
# published number was measured with.
MM_PER_PX = 0.215
# NOT A QUALITY KNOB. The rig renders at whatever the protocol density asks
# for; this only stops a request that would not fit in memory. 6000 was my own
# render-time budget and it silently coarsened the sampling on any panel over
# ~590 mm -- the same class of hidden setting as the 40 %-of-sample window and
# the constant 1400 px it was meant to replace. Correctness first: raise the
# frame, accept the time. Exceeding this raises rather than degrading.
RES_CAP = 20000
ALLOW_COARSE = False
GAP_EST = 100.0
# Default probe = the DEPLOYMENT beam (user 2026-08-16: "빔 2mm 쓰지마.
# 기본을 5-10mm"). 7.5 mm is the midpoint of the expected 5-10 mm at the
# wall (LaserCube Ultra MK2, 3-6 m throw). Historical numbers were taken
# at 2.0; any comparison against them must set STRIPE_W explicitly.
STRIPE_W = 7.5
SPREAD_DEG = 0.05
THETAS = (-40.0, 0.0, 40.0)
N_PHASE = 16                     # stripe positions across one pitch
# Optional per-frame progress hook, same contract as blender_render.PROGRESS_CB:
# sim_server points it at its counter; batch sweeps leave it None.
PROGRESS_CB = None
PERIODS_MM = (10.0, 20.0, 40.0)
# PROFILE WINDOW. This was a fixed SAMPLE COUNT, so its physical length shrank
# as the sampling got finer -- 361 samples is 77.6 mm at 0.215 mm/px but only
# 9.0 mm at 0.025. A return 10 mm wide then gets clipped by the very array it
# is recentred into, and rms collapses onto the core: measured 2.234 -> 1.730
# -> 1.008 as density went 0.100 -> 0.050 -> 0.025 while head-on (which needs
# the fine density) held at 0.189. Same defect class as the 40 %-of-sample
# window and the constant pixel count: a length written as a count.
# It is now derived per run from the measurement window, so it always holds
# whatever the window holds. NWIN stays as the floor and the legacy value.
NWIN = 361                       # floor only; run_case derives the real one


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
    # A SEPARATE FINISH FOR THE FLOOR, on the form path too (2026-08-21).
    # `measure` has taken `floor_coating` since the stack work, but this rig
    # never did, so smear and head-on could not be measured with a painted
    # floor AT ALL -- only the total could. That is why a floor-finish result
    # was reported on one axis, against the project's own rule that a
    # comparison shows every agreed axis. `blender_render.build_scene` reads
    # both keys; they only had to be passed.
    if entry.get("floor_coating") is not None:
        cfg["floor_coating"] = entry["floor_coating"]
        fbd = entry.get("floor_boundary_depth")
        if fbd is None:
            fbd = (float(prm.get("top_depth", prm.get("depth", 50.0)))
                   if "top_depth" in prm else float(prm.get("depth", 50.0)))
        cfg["floor_boundary_depth"] = float(fbd)
    body, spec = BR.coating_split(0.76)          # the fitted nominal split
    cfg["coating"] = {"body": body, "spec_scale": spec, "roughness": rough}
    # A CALLER-SUPPLIED TOP COATING. Without this the rig always painted the
    # fitted Musou, so a panel specified as "5 % paint everywhere, Musou only
    # in the top 10 mm" could not be scored on smear or head-on at all.
    if entry.get("coating") is not None:
        cfg["coating"] = dict(entry["coating"], roughness=rough)
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
    # FIXED SAMPLING DENSITY (2026-08-20). RES_X used to be a constant while
    # `ortho` tracks the scene, so mm-per-pixel scaled with the sample: 0.15 at
    # a 50 mm panel, 1.9 at a 1250 mm one. The same instrument sampled 13x
    # coarser on a bigger sample, which is not an instrument. Hold the density
    # the study used at its 100 mm panel and let the pixel count follow.
    # rho_dh survived that (it is an area average) but a WIDTH does not, and
    # the control stripe stops being resolved: a 7.5 mm beam is 34 px at a
    # 100 mm panel and 4.9 px at a 1000 mm one.
    # MM_PER_PX = 0 restores the legacy constant-pixel behaviour exactly.
    res_x, res_y = RES_X, RES_Y
    if not MM_PER_PX:
        # legacy sampling, but never a frame shorter than the face
        res_y = max(RES_Y, int(round(res_x * (p.face_h * 1.06) / ortho)))
    if MM_PER_PX:
        want = int(round(ortho / MM_PER_PX))
        if want > RES_CAP and not ALLOW_COARSE:
            # AN INSTRUMENT DOES NOT SILENTLY DEGRADE. RES_CAP is a render-time
            # budget, not a physical constant, so quietly sampling coarser than
            # the protocol asks for would hide a rig setting inside a result --
            # the same defect as the 40 %-of-sample window and the constant
            # 1400 px this replaced. Refuse, and say what would work.
            need_face = MM_PER_PX * RES_CAP / (2.04) - GAP_EST / 2.0
            raise ValueError(
                "sample too large to measure at the protocol's %.3f mm/px: it "
                "needs %d px and the budget is %d. Either reduce the sample to "
                "about %.0f mm (a periodic surface only needs enough cells, "
                "not the whole wall), or set form_buildable.ALLOW_COARSE = True "
                "to accept %.3f mm/px -- which dilutes the head-on PEAK and "
                "must not be quoted."
                % (MM_PER_PX, want, RES_CAP, max(need_face, 0.0),
                   ortho / RES_CAP))
        res_x = max(400, min(RES_CAP, want))
        # THE FRAME MUST CONTAIN THE FACE. res_y used to be a fixed 0.443 of
        # res_x, so the frame's height was 0.443 x ortho whatever the panel
        # was: at face 1000 in a 2104 mm scene that is 951 mm of frame for a
        # 1000 mm face, and the measurement window ran off the top and bottom
        # of the image. The control profile came back empty and head-on read
        # NaN. face 500 sat exactly on the boundary (499 mm of frame), so the
        # 50-500 mm ladder was one millimetre from silent truncation.
        # Height now follows the face, with 6 % of air.
        res_y = max(200, int(round(res_x * (p.face_h * 1.06) / ortho)))
        if want > RES_CAP:
            print("   [rig] COARSE, EXPLICITLY ALLOWED: wanted %d px for "
                  "%.3f mm/px, using %d px at %.3f mm/px -- head-on is not "
                  "quotable from this run"
                  % (want, MM_PER_PX, res_x, ortho / res_x), flush=True)
    mm_per_px = ortho / res_x
    # profile array long enough to hold the whole measured window (see NWIN)
    nwin = max(NWIN, int(round(p.face_h / mm_per_px)) | 1)
    nwin = min(nwin, 60001)
    # the frame must contain the face, or the window is read off the image
    _frame_h = ortho * float(res_y) / float(res_x)
    if p.face_h > _frame_h * 1.0001:
        raise ValueError(
            "frame is %.1f mm tall but the face is %.1f mm -- the measurement "
            "window would run off the image (ortho %.1f, %dx%d px)"
            % (_frame_h, p.face_h, ortho, res_x, res_y))
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
           "mm_per_px": mm_per_px, "n_phase": N_PHASE,
           # NEVER omit these again: 15 result files carry a beam
           # width recoverable only by inverting the control rms.
           "beam_w_mm": STRIPE_W, "spread_deg": SPREAD_DEG,
           "res_x": res_x, "res_y": res_y, "samples": SAMPLES,
           "face_w": p.face_w, "face_h": p.face_h,
           "rig": "v2" if MM_PER_PX else "legacy", "thetas": {}}

    # phases walk exactly one pitch, so the mean is over the full period rather
    # than over three arbitrary draws
    phases = [(-pitch / 2.0) + pitch * i / N_PHASE for i in range(N_PHASE)]

    # WINDOW LADDER (2026-08-20). The legacy window is 40 % of the face, so a
    # design whose return is wider than that is clipped -- and rms_width divides
    # by the energy INSIDE the window, so the clipped reading collapses onto the
    # core instead of merely shrinking. Measured: p10/d90 reads 1.35x through a
    # 24 mm window, 23.03x through a converged one, off IDENTICAL renders; and
    # a synthetic return of true rms 17.8 mm reads 0.80 mm through 24 mm, which
    # is indistinguishable from a design that does not smear at all.
    #
    # The renders are unchanged; only the region read off them varies. So the
    # ladder costs nothing but arithmetic. `rms_mm` becomes the CONVERGED value,
    # `rms_mm_legacy` keeps the old fixed-window number so published figures stay
    # reproducible, and `converged` says whether the value may be quoted at all.
    _h0 = max(w_panel[3] - w_panel[2], pitch + 2.0 * STRIPE_W)
    LADDER = []
    _h = _h0
    while _h < p.face_h * 0.999:
        LADDER.append(_h)
        _h *= 2.0
    LADDER.append(p.face_h)                       # the whole face, the ceiling
    LEGACY_H = w_panel[3] - w_panel[2]

    def _win(h, x0, x1):
        return (x0, x1, -h / 2.0, h / 2.0)

    for ti, theta in enumerate(THETAS):
        rec = {"per_phase": [], "peak_ratio": [], "rms_mm": []}
        acc_p = np.zeros(nwin)
        acc_c = np.zeros(nwin)
        lad_p = {h: np.zeros(nwin) for h in LADDER}
        lad_c = {h: np.zeros(nwin) for h in LADDER}
        for zi, dz in enumerate(phases):
            # live progress for the interactive server; None for batch sweeps
            if PROGRESS_CB:
                try:
                    PROGRESS_CB(ti * N_PHASE + zi, len(THETAS) * N_PHASE)
                except Exception:
                    pass
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=0.0)
            px_panel = BR.to_pixel_window(w_panel)
            px_ctrl = BR.to_pixel_window(w_ctrl)
            BR.set_world(0.0)
            BR.add_stripe(theta, cx, cz, STRIPE_W, total_w, strength=400.0,
                          spread_deg=SPREAD_DEG, target_z=dz)
            name = "%s__th%+05.1f_p%02d" % (tag, theta, zi)
            exr = os.path.join(OUT, name + ".exr")
            BR.render_to(exr, os.path.join(OUT, name + ".png"))
            arr = BR.read_exr(exr, res_x, res_y)
            pp = recentre(z_profile(arr, px_panel), nwin)
            pc = recentre(z_profile(arr, px_ctrl), nwin)
            acc_p += pp
            acc_c += pc
            pk = float(pp.max()) / float(pc.max()) if pc.max() > 0 else float("nan")
            rec["peak_ratio"].append(pk)
            rec["rms_mm"].append(rms_width(pp, mm_per_px))
            for h in LADDER:                      # same frame, wider readings
                lad_p[h] += recentre(
                    z_profile(arr, BR.to_pixel_window(
                        _win(h, w_panel[0], w_panel[1]))), nwin)
                lad_c[h] += recentre(
                    z_profile(arr, BR.to_pixel_window(
                        _win(h, w_ctrl[0], w_ctrl[1]))), nwin)
            try:
                os.remove(exr)
            except OSError:
                pass

        acc_p /= N_PHASE
        acc_c /= N_PHASE

        # walk the ladder outward and stop where two successive windows agree
        curve = []
        for h in LADDER:
            rp = rms_width(lad_p[h], mm_per_px)
            rc = rms_width(lad_c[h], mm_per_px)
            curve.append({"window_mm": h, "rms_mm": rp, "rms_control_mm": rc,
                          "smear": (rp / rc) if rc and rc == rc else None})
        conv_i, converged = len(curve) - 1, False
        for i in range(1, len(curve)):
            a, b = curve[i - 1]["smear"], curve[i]["smear"]
            if a and b and abs(b - a) / b <= 0.02:
                conv_i, converged = i, True
                break
        best = curve[conv_i]

        # How wide the return actually is, so a caller that did NOT converge
        # can size the next sample instead of shrugging. z90 is the half-width
        # holding 90 % of the energy -- robust to a faint tail, unlike rms.
        # Today's two convergences both needed a window near 6 x z90
        # (p10/d90: z90 30 mm, converged at 192; p4/d22: z90 10 mm, at 48).
        _w = lad_p[LADDER[-1]]
        _tot = _w.sum()
        if _tot > 1e-20:
            _z = (np.arange(_w.size) - _w.size / 2.0) * mm_per_px
            _q = _w / _tot
            _c = float((_z * _q).sum())
            _d = np.abs(_z - _c)
            _o = np.argsort(_d)
            _cum = np.cumsum(_q[_o])
            z90 = float(_d[_o][min(int(np.searchsorted(_cum, 0.90)),
                                   _w.size - 1)])
        else:
            z90 = float("nan")

        d = {"rms_mm": best["rms_mm"],
             "rms_control_mm": best["rms_control_mm"],
             "converged": converged,
             "window_mm": best["window_mm"],
             "window_legacy_mm": LEGACY_H,
             "z90_mm": z90,
             "window_needed_mm": (6.0 * z90) if z90 == z90 else None,
             "window_curve": curve,
             "rms_mm_legacy": rms_width(acc_p, mm_per_px),
             "rms_control_legacy_mm": rms_width(acc_c, mm_per_px),
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
