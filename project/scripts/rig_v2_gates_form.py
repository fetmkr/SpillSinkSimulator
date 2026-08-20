"""GATES 5-7: the smear and head-on axes under rig_v2, then the order spec.

Totals cleared GATES 1-4 today and stand. These two axes have not:
  smear    the stock window is a fraction of the sample, so a wide return is
           clipped. Same renders, window 24 -> 192 mm: 1.35x -> 23.03x.
  head-on  moved 23 % (0.0179 -> 0.0138) when the window changed in one test.
           Never had a gate at all.

The smear path sets the world to 0.0, so unlike the totals path there is no
sky to leak in and the window may run to the face edge. That was established
by GATE 1, which failed at inset 0 on the totals path only.

GATE 5  WINDOW CONVERGENCE. Open the window on IDENTICAL renders until the
        answer stops moving. A design whose value never settles has no
        measurable value on this axis and must be reported as such, not
        given a number.
GATE 6  SCALE INVARIANCE OF THE FORM AXES. Same shape, five sizes, beam scaled
        with the geometry. Smear and head-on are dimensionless ratios against
        a flat plate in the same frame, so they must not move.
GATE 7  THE ORDER SPEC, re-measured: 3 planes x the deployment beam, with the
        window driven to convergence rather than set by a fraction.

PRE-REGISTERED:
  P5a  fine pitch (4 mm) converges by a 48 mm window, as it did on the stock
       geometry today.
  P5b  coarse pitch (10/90) converges too, but needs ~200 mm.
  P6   smear spread across the five rungs <= 5 %. This is the gate I expect to
       be hardest: the flat control's return is set by the BEAM, and the beam
       is being scaled, so both numerator and denominator scale. If it fails,
       the smear ratio is not a scale-free quantity and that is a real result.
  P7   the order spec's converged phi-0 smear lands at 2.22 +- 0.10, matching
       what was published, because its return is only 10 mm wide.
"""

import os
import sys
import json

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
import form_buildable as FB  # noqa: E402
import rig_v2 as R2  # noqa: E402
from form_metrics import z_profile, recentre, rms_width  # noqa: E402

OUT = "/tmp/simsrv/rigv2form"
os.makedirs(OUT, exist_ok=True)
THETA = -40.0


def form_run(params, face, beam, n_phase=8, spp=256, windows=None, phi=0.0):
    """Render once per phase; read every window off the same frames."""
    prm = dict(params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    pitch = params["pitch"]
    sc = R2.build(prm, samples=spp)
    if phi:
        sc["cfg"]["phi_deg"] = phi
        BR.clear_scene()
        old = BR.GAP
        try:
            BR.GAP = sc["gap"]
            p, cs, ctrl_x0 = BR.build_scene(sc["cfg"])
        finally:
            BR.GAP = old
        sc["p"], sc["ctrl_x0"] = p, ctrl_x0
        sc["total_w"] = ctrl_x0 + p.face_w
    p, ctrl_x0 = sc["p"], sc["ctrl_x0"]
    R2.assert_clear(sc) if not phi else None
    total_w = sc["total_w"]
    ortho = total_w * 1.02
    res_x, res_y, mmpx, capped = R2.resolution_for(ortho, p.face_h)
    cx, cz = total_w / 2.0, 0.0
    if windows is None:
        windows = [p.face_h]                      # full face
    acc = {h: np.zeros(FB.NWIN) for h in windows}
    accc = {h: np.zeros(FB.NWIN) for h in windows}
    BR.configure_cycles(spp, True)
    step = pitch * (2 ** 0.5) if abs(phi - 45.0) < 1e-6 else pitch
    phases = [(-step / 2.0) + step * i / n_phase for i in range(n_phase)]
    for zi, dz in enumerate(phases):
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(THETA, cx, cz, beam, total_w, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "f.exr")
        BR.render_to(f, f.replace(".exr", ".png"))
        arr = BR.read_exr(f, res_x, res_y)
        for h in windows:
            hh = min(h, p.face_h)
            wp = (0.0, p.face_w, -hh / 2.0, hh / 2.0)
            wc = (ctrl_x0, ctrl_x0 + p.face_w, -hh / 2.0, hh / 2.0)
            acc[h] += recentre(z_profile(arr, BR.to_pixel_window(wp)), FB.NWIN)
            accc[h] += recentre(z_profile(arr, BR.to_pixel_window(wc)), FB.NWIN)
        try:
            os.remove(f)
        except OSError:
            pass
    out = {}
    for h in windows:
        rp, rc = rms_width(acc[h], mmpx), rms_width(accc[h], mmpx)
        pmax, cmax = float(acc[h].max()), float(accc[h].max())
        # GATE 6 died here with ZeroDivisionError at pitch 10 / face 1000: the
        # control profile came back all zeros. Report the diagnosis instead of
        # crashing -- a dark control means the frame is wrong, and which of
        # panel/control is dark says whether it is the light or the window.
        bad = None
        if cmax <= 0.0:
            bad = "control window is DARK (sum %.3e, panel sum %.3e)" % (
                float(accc[h].sum()), float(acc[h].sum()))
        elif pmax <= 0.0:
            bad = "panel window is DARK (sum %.3e)" % float(acc[h].sum())
        out[h] = {"smear": (rp / rc) if (rc and rc == rc) else None,
                  "rms": rp, "ctrl": rc,
                  "head_on": (pmax / cmax) if cmax > 0 else None,
                  "panel_sum": float(acc[h].sum()),
                  "ctrl_sum": float(accc[h].sum()), "problem": bad}
    return {"res_x": res_x, "mm_per_px": mmpx, "capped": capped,
            "face_h": p.face_h, "face_w": p.face_w, "ctrl_x0": ctrl_x0,
            "total_w": total_w, "beam": beam, "by_window": out}


def main():
    rows = []
    WINS = [24.0, 48.0, 96.0, 192.0, 384.0]

    print("\n===== GATE 5: window convergence, repaired rig =====", flush=True)
    for label, prm, beam, face in [
            ("order p4/d22/t0.4", dict(kind="pyramid", pitch=4.0, depth=22.0,
                                       tip_flat=0.4), 7.5, 400.0),
            ("coarse p10/d90   ", dict(kind="pyramid", pitch=10.0, depth=90.0,
                                       tip_flat=0.0), 2.0, 400.0)]:
        r = form_run(prm, face, beam, windows=WINS)
        rows.append({"gate": 5, "label": label, **r})
        print("  %s  face %.0f  %d px  %.3f mm/px%s"
              % (label, face, r["res_x"], r["mm_per_px"],
                 " CAPPED" if r["capped"] else ""), flush=True)
        prev = None
        for h in WINS:
            v = r["by_window"][h]
            d = "" if prev is None else "  (%+.1f %%)" % (
                100 * (v["smear"] - prev) / prev)
            print("     window %6.0f mm | smear %8.3fx  head-on %.4f%s"
                  % (h, v["smear"], v["head_on"], d), flush=True)
            prev = v["smear"]
        last = r["by_window"][WINS[-1]]["smear"]
        prev2 = r["by_window"][WINS[-2]]["smear"]
        conv = abs(last - prev2) / last <= 0.02
        print("     -> %s" % ("CONVERGED" if conv else "**NOT CONVERGED**"),
              flush=True)

    print("\n===== GATE 6: scale invariance of smear/head-on =====", flush=True)
    g6 = []
    for pitch in [2.0, 4.0, 10.0, 25.0]:
        prm = dict(kind="pyramid", pitch=pitch, depth=pitch * 5.0,
                   tip_flat=pitch * 0.025)
        r = form_run(prm, pitch * 100.0, beam=pitch * 1.875)   # beam scales
        v = r["by_window"][r["face_h"]]
        g6.append(v)
        rows.append({"gate": 6, "pitch": pitch, **r})
        print("  pitch %5.1f  face %6.0f  beam %6.2f | %5d px %.3f mm/px%s | "
              "smear %8.3fx  head-on %.4f"
              % (pitch, pitch * 100.0, pitch * 1.875, r["res_x"],
                 r["mm_per_px"], " CAP" if r["capped"] else "   ",
                 v["smear"], v["head_on"]), flush=True)
    for key in ("smear", "head_on"):
        vals = [v[key] for v in g6]
        m = sum(vals) / len(vals)
        sp = (max(vals) - min(vals)) / m
        print("  %-8s mean %.4f  spread %.2f %%  -> %s"
              % (key, m, 100 * sp, "PASS" if sp <= 0.05 else "**FAIL**"),
              flush=True)

    print("\n===== GATE 7: the ORDER SPEC, converged, three planes =====",
          flush=True)
    prm = dict(kind="pyramid", pitch=4.0, depth=22.0, tip_flat=0.4)
    for phi in (0.0, 45.0, 90.0):
        r = form_run(prm, 400.0, 7.5, n_phase=12, spp=384,
                     windows=[96.0, 192.0, 384.0], phi=phi)
        rows.append({"gate": 7, "phi": phi, **r})
        s = [r["by_window"][h]["smear"] for h in (96.0, 192.0, 384.0)]
        hh = [r["by_window"][h]["head_on"] for h in (96.0, 192.0, 384.0)]
        conv = abs(s[-1] - s[-2]) / s[-1] <= 0.02
        print("  phi %4.0f | smear %.3f / %.3f / %.3f  head-on %.4f / %.4f / "
              "%.4f  %s" % (phi, s[0], s[1], s[2], hh[0], hh[1], hh[2],
                            "CONVERGED" if conv else "**NOT CONVERGED**"),
              flush=True)

    with open(os.path.join(OUT, "gates_form.json"), "w") as fh:
        json.dump(rows, fh, indent=1, default=str)
    print("\n@@DONE@@")


if __name__ == "__main__":
    main()
