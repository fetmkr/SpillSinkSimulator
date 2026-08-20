"""GATES 2-4 for rig_v2: the three convergence checks a referee will ask for.

GATE 2 -- SCALE INVARIANCE. Geometric optics has no length scale. Two panels of
the same shape at different sizes, lit and viewed identically, must return the
same rho_dh. This is the only gate in the set with an answer known a priori,
which makes it the strongest. GATE 1 already hinted at it: at face 100 the
repaired rig put p4/d20 and p100/d500 (both aspect 5) within 3 %, while the
stock rig had them 163 % apart. Here it is done properly, with the panel scaled
so every rung holds the SAME number of cells, and the beam scaled with it.

GATE 3 -- SAMPLING CONVERGENCE. Halve mm-per-pixel and the answer must not
move. If it does, the instrument is still resolving the sample rather than
measuring it.

GATE 4 -- LIGHT-TRANSPORT CONVERGENCE. Quadruple the ray samples and the answer
must not move beyond Monte-Carlo noise.

PRE-REGISTERED:
  G2  the five rungs agree within 3 % of their mean (the project's stated
      ~1.3 % measurement floor, doubled for the coarsest rung)
  G3  halving mm-per-pixel moves rho_dh by < 1.5 %
  G4  quadrupling spp moves rho_dh by < 1.5 %
  A rung that hits RES_CAP is reported as CAPPED and excluded from G2's spread,
  because at that point mm-per-pixel is no longer held fixed and the rung is
  not the same instrument.
"""

import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
import rig_v2 as R2  # noqa: E402

OUT = "/tmp/simsrv/rigv2"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -40.0]


def rho(params, face, spp=256, mm_per_px=None, res_cap=None):
    old_mm, old_cap = R2.MM_PER_PX, R2.RES_CAP
    if mm_per_px:
        R2.MM_PER_PX = mm_per_px
    if res_cap:
        R2.RES_CAP = res_cap
    try:
        prm = dict(params)
        prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
        sc = R2.build(prm, samples=spp)
        p, ctrl_x0 = sc["p"], sc["ctrl_x0"]
        R2.assert_clear(sc)
        total_w = sc["total_w"]
        ortho = total_w * 1.02
        res_x, res_y, mmpx, capped = R2.resolution_for(ortho, p.face_h)
        w_panel, w_ctrl = R2.full_face_windows(
            p, ctrl_x0, inset_mm=R2.sky_inset_mm(mmpx))
        cx, cz = total_w / 2.0, 0.0
        BR.configure_cycles(spp, True)
        out = {}
        for th in THETAS:
            for o in list(bpy.data.objects):
                if o.type in ("LIGHT", "CAMERA"):
                    bpy.data.objects.remove(o, do_unlink=True)
            BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=th)
            BR.set_world(1.0)
            f = os.path.join(OUT, "g2.exr")
            BR.render_to(f, f.replace(".exr", ".png"))
            arr = BR.read_exr(f, res_x, res_y)
            out["%+.0f" % th] = {
                "panel": BR.window_stats(arr, BR.to_pixel_window(w_panel))["mean"],
                "ctrl": BR.window_stats(arr, BR.to_pixel_window(w_ctrl))["mean"]}
            try:
                os.remove(f)
            except OSError:
                pass
        gate1 = max(abs(v["ctrl"] - 0.05) for v in out.values()) <= 1e-4
        return {"rho": out, "res_x": res_x, "mm_per_px": mmpx,
                "capped": capped, "gate1": gate1}
    finally:
        R2.MM_PER_PX, R2.RES_CAP = old_mm, old_cap


def main():
    rows = []

    print("\n===== GATE 2: scale invariance (aspect 5, 25 cells a side) =====",
          flush=True)
    g2 = []
    for pitch in [2.0, 4.0, 10.0, 25.0, 50.0]:
        prm = dict(kind="pyramid", pitch=pitch, depth=pitch * 5.0,
                   tip_flat=pitch * 0.025)     # tip scales too: same SHAPE
        face = pitch * 25.0
        r = rho(prm, face, spp=256, res_cap=9000)
        g2.append((pitch, r))
        rows.append({"gate": 2, "pitch": pitch, "face": face, **r})
        print("  pitch %5.1f  face %6.0f | %5d px  %5.3f mm/px%s | "
              "th0 %.6f  th-40 %.6f | control %s"
              % (pitch, face, r["res_x"], r["mm_per_px"],
                 " CAPPED" if r["capped"] else "      ",
                 r["rho"]["+0"]["panel"], r["rho"]["-40"]["panel"],
                 "OK" if r["gate1"] else "FAIL"), flush=True)
    ok = [r for _, r in g2 if not r["capped"] and r["gate1"]]
    for th in ("+0", "-40"):
        vals = [r["rho"][th]["panel"] for r in ok]
        if vals:
            m = sum(vals) / len(vals)
            spread = (max(vals) - min(vals)) / m
            print("  th %-4s mean %.6f  spread %.2f %%  -> %s"
                  % (th, m, 100 * spread,
                     "PASS" if spread <= 0.03 else "**FAIL**"), flush=True)

    print("\n===== GATE 3: halve mm-per-pixel =====", flush=True)
    base = dict(kind="pyramid", pitch=4.0, depth=20.0, tip_flat=0.1)
    a = rho(base, 100.0, spp=256, mm_per_px=0.215)
    b = rho(base, 100.0, spp=256, mm_per_px=0.1075, res_cap=9000)
    for th in ("+0", "-40"):
        d = (b["rho"][th]["panel"] - a["rho"][th]["panel"]) / a["rho"][th]["panel"]
        print("  th %-4s  %5.3f mm/px %.6f -> %5.3f mm/px %.6f   %+.2f %%  %s"
              % (th, a["mm_per_px"], a["rho"][th]["panel"], b["mm_per_px"],
                 b["rho"][th]["panel"], 100 * d,
                 "PASS" if abs(d) <= 0.015 else "**FAIL**"), flush=True)
    rows += [{"gate": 3, "which": "coarse", **a}, {"gate": 3, "which": "fine", **b}]

    print("\n===== GATE 4: quadruple ray samples =====", flush=True)
    c = rho(base, 100.0, spp=1024)
    for th in ("+0", "-40"):
        d = (c["rho"][th]["panel"] - a["rho"][th]["panel"]) / a["rho"][th]["panel"]
        print("  th %-4s  256 spp %.6f -> 1024 spp %.6f   %+.2f %%  %s"
              % (th, a["rho"][th]["panel"], c["rho"][th]["panel"], 100 * d,
                 "PASS" if abs(d) <= 0.015 else "**FAIL**"), flush=True)
    rows.append({"gate": 4, "which": "1024spp", **c})

    with open(os.path.join(OUT, "gates234.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("\n@@DONE@@")


if __name__ == "__main__":
    main()
