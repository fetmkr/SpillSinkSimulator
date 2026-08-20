"""GATE 7 (never ran): the order spec on three azimuth planes.

It was queued twice and lost both times -- once to a divide-by-zero earlier in
the same script, once to a server restart I did myself. It is the measurement
that decides whether the published total of 0.185 % and today's 0.150 % differ
because of the rig or because published was the worst of three planes and
today's was phi 0 only.

phi rotates the PANEL about its normal; the camera, stripe and control stay
put, so this is beam azimuth. At phi 45 the pattern period along world z
stretches by sqrt(2) for a square grid, so the stripe walk is scaled to match.

PRE-REGISTERED:
  G7a  phi 45 is the worst plane on totals, by about 24 % (recorded in phase
       5.9 and never re-checked since the rig was repaired)
  G7b  0.150 % at phi 0 x 1.24 = 0.186 %, which would account for the published
       0.185 % exactly and mean the rig repair did NOT move the headline total
  G7c  smear is worst (lowest) at phi 45 as well
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy, numpy as np                                    # noqa: E402
import blender_render as BR, form_buildable as FB          # noqa: E402
import rig_v2 as R2                                        # noqa: E402
from form_metrics import z_profile, recentre, rms_width    # noqa: E402

OUT = "/tmp/simsrv/gate7"; os.makedirs(OUT, exist_ok=True)
PRM = dict(kind="pyramid", pitch=4.0, depth=22.0, tip_flat=0.4)
FACE, SPP, NPH, BEAM = 200.0, 384, 12, 7.5


def scene(phi, mmpx):
    q = dict(PRM); q.update(face_w=FACE, face_h=FACE, margin_depths=2.0,
                            backing=2.0)
    old = R2.MM_PER_PX; R2.MM_PER_PX = mmpx
    try:
        sc = R2.build(q, samples=SPP)
        if phi:
            sc["cfg"]["phi_deg"] = float(phi)
            g = BR.GAP
            try:
                BR.GAP = sc["gap"]; BR.clear_scene()
                p, cs, cx0 = BR.build_scene(sc["cfg"])
            finally:
                BR.GAP = g
            sc["p"], sc["ctrl_x0"] = p, cx0
            sc["total_w"] = cx0 + p.face_w
        p, cx0 = sc["p"], sc["ctrl_x0"]
        tw = sc["total_w"]; ortho = tw * 1.02
        rx, ry, mm, cap = R2.resolution_for(ortho, p.face_h)
    finally:
        R2.MM_PER_PX = old
    return p, cx0, tw, ortho, rx, ry, mm


rows = []
print("발주 사양 간격4/깊이22/팁0.4 · 판 %.0f · 빔 %.1f · 줄옮김 %d"
      % (FACE, BEAM, NPH), flush=True)
print("%-7s %-11s %-11s %-9s %s" % ("phi", "총량%(최악)", "뭉개기", "쓴창mm", "시간"),
      flush=True)
for phi in (0.0, 45.0, 90.0):
    t0 = time.time()
    p, cx0, tw, ortho, rx, ry, mm = scene(phi, 0.215)
    wp, wc = R2.full_face_windows(p, cx0, inset_mm=R2.sky_inset_mm(mm))
    BR.configure_cycles(SPP, True)
    worst = 0.0; ctrl_ok = True
    for th in (0.0, -20.0, 20.0, -40.0, 40.0):
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw / 2, 0.0, ortho, rx, ry, elev_deg=th)
        BR.set_world(1.0)
        f = os.path.join(OUT, "t.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        worst = max(worst, BR.window_stats(a, BR.to_pixel_window(wp))["mean"])
        ctrl_ok &= abs(BR.window_stats(a, BR.to_pixel_window(wc))["mean"] - .05) <= 1e-4
        os.remove(f)
    # smear: the stripe walk stretches by sqrt(2) on the diagonal
    step = 4.0 * (2 ** 0.5) if abs(phi - 45.0) < 1e-6 else 4.0
    nwin = min(60001, max(361, int(round(p.face_h / mm)) | 1))
    wins = [24., 48., 96., 192., p.face_h]
    acc = {h: np.zeros(nwin) for h in wins}; accc = {h: np.zeros(nwin) for h in wins}
    for i in range(NPH):
        dz = (-step / 2) + step * i / NPH
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw / 2, 0.0, ortho, rx, ry, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(-40.0, tw / 2, 0.0, BEAM, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "f.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        for h in wins:
            hh = min(h, p.face_h)
            acc[h] += recentre(z_profile(a, BR.to_pixel_window(
                (0., p.face_w, -hh/2, hh/2))), nwin)
            accc[h] += recentre(z_profile(a, BR.to_pixel_window(
                (cx0, cx0+p.face_w, -hh/2, hh/2))), nwin)
        os.remove(f)
    curve = [(h, rms_width(acc[h], mm) / rms_width(accc[h], mm)) for h in wins]
    best = curve[-1]
    for i in range(1, len(curve)):
        if curve[i][1] and abs(curve[i][1]-curve[i-1][1])/curve[i][1] <= 0.02:
            best = curve[i]; break
    rows.append(dict(phi=phi, rho=worst, smear=best[1], window=best[0],
                     ctrl_ok=ctrl_ok))
    print("%-7.0f %-11.4f %-11.4f %-9.0f %.0fs  대조 %s"
          % (phi, 100*worst, best[1], best[0], time.time()-t0,
             "OK" if ctrl_ok else "FAIL"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "gate7.json"), "w"), indent=1)

w = max(r["rho"] for r in rows); z = [r for r in rows if r["phi"] == 0][0]["rho"]
print("\n세 평면 최악 총량 %.4f %%   phi0 대비 %+.1f %%" % (100*w, 100*(w-z)/z),
      flush=True)
print("발표값 0.185 %% 와의 차이: %+.1f %%" % (100*(100*w-0.185)/0.185), flush=True)
print("가장 뭉개기 나쁜 평면: phi %.0f  %.4f"
      % (min(rows, key=lambda r: r["smear"])["phi"],
         min(r["smear"] for r in rows)), flush=True)
print("@@DONE@@", flush=True)
