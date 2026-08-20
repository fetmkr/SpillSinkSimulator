"""GATE 8: does self-centring erase a real displacement?

form_buildable.py:191-192 recentres the panel profile on ITS OWN centroid and
the control on ITS own:

    pp = recentre(z_profile(arr, px_panel), NWIN)
    pc = recentre(z_profile(arr, px_ctrl), NWIN)

The code this replaced did it deliberately the other way (form_mtf.py:180-191),
with the reason in the comment:

    # both profiles are recentred on the CONTROL centroid, so the
    # panel keeps any real displacement of its return

Self-centring subtracts, per phase, exactly the quantity a wall is judged on:
where the returned light LANDS. A design that moves the line without widening
it scores as if it did nothing. And `form_metrics.recentre`'s own docstring
claims "comparing widths requires a common origin" while giving each profile a
different origin.

Symptom already in the record, no rendering needed: `results/form_buildable.json`
reports the panel rms BELOW the flat control floor in 27 of 123 rows (22 %).
metrics/02 defines the control as the floor.

This measures the two conventions on identical renders, so the difference is
the convention and nothing else.

  A  self-centred      what every published smear number used
  B  control-centred   what form_mtf.py did, and what metric 02 describes

Both beams: 2.09 mm (what form_buildable.json actually used, backed out from
its own control rms via W/sqrt(12)) and 7.5 mm (deployment).

PRE-REGISTERED:
  E1  B >= A for every design -- keeping a displacement can only widen the
      second moment, never narrow it.
  E2  designs that sit BELOW the control floor under A rise ABOVE it under B.
      If any stays below the floor under B, self-centring is not the cause and
      something else is wrong.
  E3  the gap B-A grows with pitch: a coarse field displaces the return by up
      to a cell, a fine one by at most a few millimetres.
  E4  the ORDER of designs changes between A and B. If it does, every
      published smear ranking is a ranking of the wrong statistic.
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
from form_metrics import z_profile, rms_width  # noqa: E402

OUT = "/tmp/simsrv/recentre"
os.makedirs(OUT, exist_ok=True)
THETA = -40.0
NWIN = FB.NWIN


def _shift(prof, centre_idx, n):
    out = np.zeros(n)
    lo = int(round(centre_idx)) - n // 2
    for i in range(n):
        j = lo + i
        if 0 <= j < prof.size:
            out[i] = prof[j]
    return out


def _centroid(prof):
    idx = np.arange(prof.size, dtype=np.float64)
    tot = prof.sum()
    return float((idx * prof).sum() / tot) if tot > 1e-20 else prof.size / 2.0


def run(params, face, beam, n_phase=12, spp=384):
    prm = dict(kind="pyramid", **params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    pitch = params["pitch"]
    sc = R2.build(prm, samples=spp)
    p, ctrl_x0 = sc["p"], sc["ctrl_x0"]
    R2.assert_clear(sc)
    total_w = sc["total_w"]
    ortho = total_w * 1.02
    res_x, res_y, mmpx, capped = R2.resolution_for(ortho, p.face_h)
    wp = (0.0, p.face_w, -p.face_h / 2.0, p.face_h / 2.0)
    wc = (ctrl_x0, ctrl_x0 + p.face_w, -p.face_h / 2.0, p.face_h / 2.0)
    cx, cz = total_w / 2.0, 0.0
    BR.configure_cycles(spp, True)

    accA = np.zeros(NWIN)      # self-centred  (current code)
    accB = np.zeros(NWIN)      # control-centred (form_mtf convention)
    accC = np.zeros(NWIN)      # control, self-centred (same under both)
    shifts = []
    for i in range(n_phase):
        dz = (-pitch / 2.0) + pitch * i / n_phase
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(THETA, cx, cz, beam, total_w, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "r.exr")
        BR.render_to(f, f.replace(".exr", ".png"))
        arr = BR.read_exr(f, res_x, res_y)
        pp = z_profile(arr, BR.to_pixel_window(wp))
        pc = z_profile(arr, BR.to_pixel_window(wc))
        cp, cc = _centroid(pp), _centroid(pc)
        accA += _shift(pp, cp, NWIN)
        accB += _shift(pp, cc, NWIN)
        accC += _shift(pc, cc, NWIN)
        shifts.append((cp - cc) * mmpx)
        try:
            os.remove(f)
        except OSError:
            pass

    rA, rB, rC = (rms_width(accA, mmpx), rms_width(accB, mmpx),
                  rms_width(accC, mmpx))
    return {"res_x": res_x, "mm_per_px": mmpx, "capped": capped,
            "rms_self": rA, "rms_ctrl_centred": rB, "rms_control": rC,
            "smear_self": rA / rC, "smear_ctrl_centred": rB / rC,
            "shift_mm_mean": float(np.mean(shifts)),
            "shift_mm_ptp": float(np.ptp(shifts)),
            "shift_mm_rms": float(np.sqrt(np.mean(np.square(shifts))))}


CASES = [
    ("p2/d18   ", dict(pitch=2.0, depth=18.0, tip_flat=0.0), 200.0),
    ("p4/d20   ", dict(pitch=4.0, depth=20.0, tip_flat=0.1), 300.0),
    ("p4/d22   ", dict(pitch=4.0, depth=22.0, tip_flat=0.4), 300.0),
    ("p5.5/d50 ", dict(pitch=5.5, depth=50.0, tip_flat=0.0), 300.0),
    ("p10/d90  ", dict(pitch=10.0, depth=90.0, tip_flat=0.0), 400.0),
]

rows = []
for beam in (2.09, 7.5):
    print("\n===== beam %.2f mm =====" % beam, flush=True)
    print("%-10s | %-9s %-9s | %-8s %-8s | phase shift of the return"
          % ("design", "smear A", "smear B", "rmsA", "rmsB"), flush=True)
    print("%-10s | %-9s %-9s |" % ("", "self", "ctrl-ctr"), flush=True)
    for label, prm, face in CASES:
        r = run(prm, face, beam)
        rows.append({"design": label.strip(), "beam": beam, **r})
        below = "  <-- BELOW FLOOR" if r["smear_self"] < 1.0 else ""
        print("%-10s | %9.3f %9.3f | %8.3f %8.3f | mean %+.2f mm  swing "
              "%.2f mm  rms %.2f mm%s"
              % (label, r["smear_self"], r["smear_ctrl_centred"],
                 r["rms_self"], r["rms_ctrl_centred"], r["shift_mm_mean"],
                 r["shift_mm_ptp"], r["shift_mm_rms"], below), flush=True)
        with open(os.path.join(OUT, "gate_recentre.json"), "w") as fh:
            json.dump(rows, fh, indent=1)

print("\n--- ORDER on the smear axis (higher smears more) ---", flush=True)
for beam in (2.09, 7.5):
    sub = [r for r in rows if r["beam"] == beam]
    a = "  >  ".join("%s %.2f" % (r["design"], r["smear_self"])
                     for r in sorted(sub, key=lambda r: -r["smear_self"]))
    b = "  >  ".join("%s %.2f" % (r["design"], r["smear_ctrl_centred"])
                     for r in sorted(sub, key=lambda r: -r["smear_ctrl_centred"]))
    print("  beam %.2f  A self     : %s" % (beam, a), flush=True)
    print("  beam %.2f  B ctrl-ctr : %s" % (beam, b), flush=True)
print("@@DONE@@")
