"""Can a BOUGHT honeycomb be rescued by putting a floor under it?

The honeycomb was rejected on two axes and today's re-measurement confirmed
both, with the window driven to convergence and its 0.08 mm wall fully resolved
(13 671 px):

    total   0.1733-0.1744 %   comparable to the pyramid's 0.1495-0.1512
    smear   0.985             BELOW 1.0 -- narrower than a flat plate
    head-on 1.643             published 1.639, so the old number was right

Both failures have ONE cause: the cell floor is flat and faces the observer, so
it is bright and it returns the line unsmeared. Fix the floor and both might
move together.

The project already measured that once (report/ko/phase6.html): honeycomb 12.7
over a fine floor gave total 0.212 %, smear 1.03, head-on 0.0853 -- head-on
improved 19x. But smear stayed at 1.03, and smear is the stated first priority.

**That 1.03 was measured with the broken window.** Every smear in the project
before today was, and one of them was wrong by 19x. So it has to be re-measured
before the honeycomb can be ruled out on it.

This matters commercially: a honeycomb is BOUGHT, in aluminium, off a shelf.
The pyramid needs a master, silicone moulds and cast urethane.

PRE-REGISTERED:
  S1  head-on drops from 1.64 to under 0.15 once a textured floor is under the
      cells -- the old 0.0853 was a peak measurement and peaks were biased LOW
      by the coarse pixel, so expect the repaired value to be HIGHER than
      0.0853, not lower
  S2  smear with a converged window is ABOVE the old 1.03. How far above is the
      whole question: over ~1.4 and the honeycomb is back in contention, near
      1.0 and it is finished for the reason originally given
  S3  total stays near 0.21 %, worse than the pyramid's 0.15 %
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy, numpy as np                                   # noqa: E402
import blender_render as BR, form_buildable as FB         # noqa: E402
import rig_v2 as R2                                       # noqa: E402
import sim_server as SS                                   # noqa: E402
from form_metrics import z_profile, recentre, rms_width   # noqa: E402

OUT = "/tmp/simsrv/stack"; os.makedirs(OUT, exist_ok=True)
FACE, SPP, NPH, BEAM = 200.0, 384, 8, 7.5

CASES = [
  ("벌집 단독 (오늘 확인)", dict(top="honeycomb",
        top_params={"pitch": 6.5, "wall_top": 0.08, "wall_bot": 0.08,
                    "jitter": 0.0}, depth=30.0, floor="none"), 6.5),
  ("벌집 + 피라미드 바닥", dict(top="honeycomb",
        top_params={"pitch": 6.5, "wall_top": 0.08, "wall_bot": 0.08,
                    "jitter": 0.0}, depth=30.0,
        floor="pyramid", floor_depth=6.0,
        floor_params={"pitch": 2.0, "tip_flat": 0.05}), 6.5),
  ("피라미드 발주 사양 (기준)", dict(top="pyramid",
        top_params={"pitch": 4.0, "tip_flat": 0.4}, depth=22.0,
        floor="none"), 4.0),
]


def measure(spec, pitch, mmpx=0.215):
    m = dict(spec, panel=FACE, margin_depths=2.0)
    prm = SS._render_params(m); fam = SS._render_family(m)
    old = R2.MM_PER_PX; R2.MM_PER_PX = mmpx
    try:
        sc = R2.build(prm, samples=SPP, family=fam)
        p, cx0 = sc["p"], sc["ctrl_x0"]; tw = sc["total_w"]; ortho = tw * 1.02
        rx, ry, mm, cap = R2.resolution_for(ortho, p.face_h)
    finally:
        R2.MM_PER_PX = old
    wp, wc = R2.full_face_windows(p, cx0, inset_mm=R2.sky_inset_mm(mm))
    BR.configure_cycles(SPP, True)
    worst, ok = 0.0, True
    for th in (0.0, -40.0, 40.0):
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw/2, 0.0, ortho, rx, ry, elev_deg=th)
        BR.set_world(1.0)
        f = os.path.join(OUT, "t.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        worst = max(worst, BR.window_stats(a, BR.to_pixel_window(wp))["mean"])
        ok &= abs(BR.window_stats(a, BR.to_pixel_window(wc))["mean"] - .05) <= 1e-4
        os.remove(f)
    nwin = min(60001, max(361, int(round(p.face_h / mm)) | 1))
    wins = [24., 48., 96., 192., p.face_h]
    acc = {h: np.zeros(nwin) for h in wins}; accc = {h: np.zeros(nwin) for h in wins}
    pk = []
    for i in range(NPH):
        dz = (-pitch/2) + pitch*i/NPH
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw/2, 0.0, ortho, rx, ry, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(0.0, tw/2, 0.0, BEAM, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "h.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        pp = recentre(z_profile(a, BR.to_pixel_window(
            (0., p.face_w, -p.face_h/2, p.face_h/2))), nwin)
        pc = recentre(z_profile(a, BR.to_pixel_window(
            (cx0, cx0+p.face_w, -p.face_h/2, p.face_h/2))), nwin)
        pk.append(float(pp.max())/float(pc.max()) if pc.max() > 0 else np.nan)
        os.remove(f)
    for i in range(NPH):
        dz = (-pitch/2) + pitch*i/NPH
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw/2, 0.0, ortho, rx, ry, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(-40.0, tw/2, 0.0, BEAM, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "s.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        for h in wins:
            hh = min(h, p.face_h)
            acc[h] += recentre(z_profile(a, BR.to_pixel_window(
                (0., p.face_w, -hh/2, hh/2))), nwin)
            accc[h] += recentre(z_profile(a, BR.to_pixel_window(
                (cx0, cx0+p.face_w, -hh/2, hh/2))), nwin)
        os.remove(f)
    curve = [(h, rms_width(acc[h], mm)/rms_width(accc[h], mm)) for h in wins]
    best, conv = curve[-1], False
    for i in range(1, len(curve)):
        if curve[i][1] and abs(curve[i][1]-curve[i-1][1])/curve[i][1] <= 0.02:
            best, conv = curve[i], True; break
    return worst, best[1], best[0], conv, float(np.nanmean(pk)), ok, rx


rows = []
print("판 %.0f · 빔 %.1f · 줄옮김 %d · 밀도 0.215" % (FACE, BEAM, NPH), flush=True)
print("%-26s %-9s %-10s %-9s %-10s %-6s %s"
      % ("설계", "총량%", "뭉개기", "쓴창mm", "정면", "대조", "시간"), flush=True)
for name, spec, pitch in CASES:
    t0 = time.time()
    try:
        rho, sm, win, conv, hd, ok, rx = measure(spec, pitch)
    except Exception as e:
        print("%-26s 실패: %s" % (name, repr(e)[:70]), flush=True); continue
    rows.append(dict(name=name, rho=rho, smear=sm, window=win, conv=conv,
                     head_on=hd, ctrl=ok))
    print("%-26s %-9.4f %-10.4f %-9s %-10.5f %-6s %.0fs"
          % (name, 100*rho, sm, "%.0f%s" % (win, "" if conv else "!"),
             hd, "OK" if ok else "FAIL", time.time()-t0), flush=True)
    json.dump(rows, open(os.path.join(OUT, "stack.json"), "w"), indent=1)

print("\n=== 옛 기록과 대조 ===", flush=True)
print("  벌집+바닥, 옛 발표: 총량 0.212 %  뭉개기 1.03  정면 0.0853", flush=True)
if len(rows) >= 2:
    r = rows[1]
    print("  벌집+바닥, 오늘  : 총량 %.3f %%  뭉개기 %.3f  정면 %.4f"
          % (100*r["rho"], r["smear"], r["head_on"]), flush=True)
    print("\n  판정: 뭉개기 %.3f -> %s"
          % (r["smear"], "1.4 이상, 재검토 가치 있음" if r["smear"] >= 1.4
             else "1.4 미만, 모양 뭉개기로는 여전히 부족"), flush=True)
print("@@DONE@@", flush=True)
