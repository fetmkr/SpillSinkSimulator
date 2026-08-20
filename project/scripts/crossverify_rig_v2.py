"""Re-verify today's surviving result with two codes that share no source.

GATES 1-4 said the totals axis stands: scale-invariant to 0.55-1.70 % over a
25x size span, insensitive to pixel size over 13x, control plate exact, and
2-3 % between the stock and repaired rigs. All of that was Cycles checking
Cycles. A number that has only ever been produced by one code has not been
verified, it has been repeated.

So measure the SAME geometry three ways:

  Cycles      through rig_v2 (repaired), uniform-hemisphere read
  Mitsuba     3.9.1, scalar_rgb, via scripts/mts_worker.py in its own venv
  a third     scripts/raytrace_viz.py -- plain Python, Moller-Trumbore, its own
              grid, no Blender and no Mitsuba in its import graph. It casts a
              beam at theta and sums the weight that escapes, which is
              rho_dh(theta) directly rather than by reciprocity.

The material must be the ONE BRDF all three implement identically: a Lambertian
of rho 0.01. The fitted Musou coating is a Fresnel node graph that Mitsuba
cannot be asked to reproduce, so a disagreement on it would be about materials
rather than transport. This is the same discipline
FINDINGS_renderer_disagreement.md used.

PRE-REGISTERED:
  C1  Cycles and the third tracer agree within the third tracer's own Monte
      Carlo error (report the sigma, do not hand-wave it).
  C2  Mitsuba reads HIGH on the pyramid, as it did today (+27 % at theta 0,
      +15 % at -40). That gap is an open item in the project record and this
      pins it down on the repaired rig rather than the stock one, which is
      what a referee will ask.
  C3  the gap does NOT grow with panel size. If it does, it is a rig artifact
      of ours; if it is flat, it is a property of the two codes.
"""

import os
import sys
import json
import math
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import blender_render as BR  # noqa: E402
import rig_v2 as R2  # noqa: E402
from geom_floor import FloorParams, build_mesh  # noqa: E402

OUT = "/tmp/simsrv/crossverify"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -40.0]
RHO = 0.01

CASES = [
    ("p4/d20  face 100", dict(pitch=4.0, depth=20.0, tip_flat=0.1), 100.0),
    ("p4/d22  face 100", dict(pitch=4.0, depth=22.0, tip_flat=0.4), 100.0),
    ("p4/d20  face 250", dict(pitch=4.0, depth=20.0, tip_flat=0.1), 250.0),
]


def cycles_rho(params, face, spp=512):
    prm = dict(kind="pyramid", **params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    sc = R2.build(prm, samples=spp, lambert_rho=RHO)
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
        f = os.path.join(OUT, "cv.exr")
        BR.render_to(f, f.replace(".exr", ".png"))
        arr = BR.read_exr(f, res_x, res_y)
        out["%+.0f" % th] = BR.window_stats(
            arr, BR.to_pixel_window(w_panel))["mean"]
        ctrl = BR.window_stats(arr, BR.to_pixel_window(w_ctrl))["mean"]
        if abs(ctrl - 0.05) > 1e-4:
            out["gate1_fail_%+.0f" % th] = ctrl
        try:
            os.remove(f)
        except OSError:
            pass
    return out, {"res_x": res_x, "mm_per_px": mmpx, "capped": capped}


def mitsuba_rho(params, face, spp=512):
    venv = os.path.expanduser("~/.spillsink/mts_env/bin/python")
    if not os.path.exists(venv):
        return {"error": "no venv"}
    prm = dict(kind="pyramid", **params)
    prm.update(face_w=face, face_h=face, margin_depths=2.0, backing=2.0)
    out = {}
    for th in THETAS:
        req = {"family": "floor", "params": prm, "rho": RHO,
               "theta": th, "spp": spp}
        p = subprocess.run([venv, os.path.join(HERE, "mts_worker.py")],
                           input=json.dumps(req), capture_output=True,
                           text=True)
        line = [l for l in (p.stdout + p.stderr).splitlines()
                if l.startswith("@@RESULT@@")]
        if not line:
            out["%+.0f" % th] = None
            continue
        out["%+.0f" % th] = json.loads(line[0][len("@@RESULT@@"):])["rho_dh"]
    return out


def third_rho(params, face, n_rays=4000, seed=23):
    """The pure-Python tracer. Its rho_est IS rho_dh(theta); the sigma is the
    standard error of the escaping weights, reported so C1 can be graded."""
    import raytrace_viz as RV
    fp = FloorParams(kind="pyramid", face_w=face, face_h=face,
                     margin_depths=0.0, backing=2.0, **params)
    v, f = build_mesh(fp)
    out = {}
    for th in THETAS:
        r = RV.trace(v, f, face, face, theta_deg=th, n_rays=n_rays,
                     max_bounces=24, rho=RHO, seed=seed, mode="diffuse")
        w = r.get("weights") or []
        est = r["stats"].get("rho_est")
        if w:
            n = len(w)
            m = sum(w) / n
            var = sum((x - m) ** 2 for x in w) / max(n - 1, 1)
            sig = math.sqrt(var / n)
        else:
            sig = float("nan")
        out["%+.0f" % th] = {"rho": est, "sigma": sig, "n": len(w)}
    return out


def main():
    rows = []
    for label, params, face in CASES:
        print("\n=== %s ===" % label, flush=True)
        cyc, meta = cycles_rho(params, face)
        print("  Cycles (rig_v2, %d px, %.3f mm/px%s)"
              % (meta["res_x"], meta["mm_per_px"],
                 " CAPPED" if meta["capped"] else ""), flush=True)
        for th in THETAS:
            k = "%+.0f" % th
            print("     th %-4s  %.6f%s"
                  % (k, cyc[k],
                     "   GATE1 FAIL ctrl=%.6f" % cyc["gate1_fail_" + k]
                     if ("gate1_fail_" + k) in cyc else ""), flush=True)
        mts = mitsuba_rho(params, face)
        thi = third_rho(params, face)
        for th in THETAS:
            k = "%+.0f" % th
            c = cyc[k]
            m = mts.get(k)
            t = thi[k]
            dm = (m - c) / c * 100 if m else float("nan")
            dt = (t["rho"] - c) / c * 100 if t["rho"] else float("nan")
            nsig = abs(t["rho"] - c) / t["sigma"] if t["sigma"] else float("nan")
            print("     th %-4s | Cycles %.6f | Mitsuba %.6f (%+6.1f %%) | "
                  "third %.6f +- %.6f (%+6.1f %%, %.1f sigma)"
                  % (k, c, m or float("nan"), dm, t["rho"] or float("nan"),
                     t["sigma"], dt, nsig), flush=True)
            rows.append({"case": label, "theta": th, "cycles": c,
                         "mitsuba": m, "third": t, "meta": meta})
        with open(os.path.join(OUT, "crossverify.json"), "w") as fh:
            json.dump(rows, fh, indent=1)
    print("\n@@DONE@@")


if __name__ == "__main__":
    main()
