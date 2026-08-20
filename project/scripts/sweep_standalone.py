"""Honeycomb + pyramid, every size, three axes -- in ITS OWN Blender.

Runs nothing through the simulator server. Every batch script written today
called /api/form, which was convenient and wrong: Blender renders one frame at
a time, so a user pressing Render sat behind dozens of my frames and the button
looked dead. A honeycomb frame at the density its 0.08 mm wall needs is 15 000
pixels wide and takes minutes. The instrument and the interactive tool must not
share a queue.

Conditions, per design, all measured today rather than assumed:
  density   = min_feature / 4      GATE 16: head-on converged at 4 px across
                                   the tip (0.18898 / 0.18907 / 0.18874)
  window    opens until two readings agree, ~6x the return's 90 % width
  profile   array follows the window (defect 9: a fixed 361 SAMPLES spanned
            9 mm at 0.025 mm/px and clipped a 10 mm return, collapsing smear
            from 2.234 to 1.008)
  sample    >= 25 cells (GATE 11: rho was still falling at 50)

PRE-REGISTERED:
  W1  pyramid total flat within 2 % for >= 25 cells, both tip variants
  W2  smear flat with size in both families
  W3  head-on at the FEATURE-RESOLVED density is well above every published
      value, and the gap is largest for the finest feature: the honeycomb's
      0.08 mm wall is 10.8x under-resolved at the 0.215 protocol against 2.1x
      for the order spec's 0.4 mm tip
  W4  the honeycomb's published head-on of 1.639 -- the number that rejected it
      as "no better than a flat plate" -- rises materially once its wall is
      resolved
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy, numpy as np                                   # noqa: E402
import blender_render as BR, form_buildable as FB         # noqa: E402
import rig_v2 as R2                                       # noqa: E402
from form_metrics import z_profile, recentre, rms_width   # noqa: E402

OUT = "/tmp/simsrv/standalone"; os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(OUT, "sweep.json")

FAMS = {
  "pyramid p4/d22/t0.4": dict(prm=dict(kind="pyramid", pitch=4.0, depth=22.0,
                                       tip_flat=0.4), pitch=4.0, feat=0.4),
  "pyramid p4/d20/t0.1": dict(prm=dict(kind="pyramid", pitch=4.0, depth=20.0,
                                       tip_flat=0.1), pitch=4.0, feat=0.1),
  # honeycomb is built by geom_topo, not geom_floor: its params are
  # TopoParams(topology=...) and it has walls, not tips. Passing FloorParams
  # keywords killed the first run with "unexpected keyword argument wall_top".
  "honeycomb 6.5/w0.08": dict(prm=dict(topology="honeycomb", pitch=6.5,
                                       depth=30.0, wall_top=0.08,
                                       wall_bot=0.08, jitter=0.0),
                              pitch=6.5, feat=0.08, family="topo"),
}
PANELS = [100.0, 200.0, 400.0]
ONLY = os.environ.get("ONLY")
BEAM, NPH, SPP = 7.5, 8, 256


def build(prm, face, mmpx, spp=SPP, lam=None, family="floor"):
    q = dict(prm); q.update(face_w=face, face_h=face, margin_depths=2.0,
                            backing=2.0)
    old = R2.MM_PER_PX
    R2.MM_PER_PX = mmpx
    try:
        sc = R2.build(q, samples=spp, lambert_rho=lam, family=family)
    finally:
        R2.MM_PER_PX = old
    p, cx0 = sc["p"], sc["ctrl_x0"]
    tw = sc["total_w"]; ortho = tw * 1.02
    oldm = R2.MM_PER_PX; R2.MM_PER_PX = mmpx
    try:
        rx, ry, mm, cap = R2.resolution_for(ortho, p.face_h)
    finally:
        R2.MM_PER_PX = oldm
    return sc, p, cx0, tw, ortho, rx, ry, mm, cap


def totals(prm, face, mmpx, family="floor"):
    sc, p, cx0, tw, ortho, rx, ry, mm, cap = build(prm, face, mmpx, family=family)
    wp, wc = R2.full_face_windows(p, cx0, inset_mm=R2.sky_inset_mm(mm))
    BR.configure_cycles(SPP, True)
    worst, ctrl_ok = 0.0, True
    for th in (0.0, -40.0, 40.0):
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw / 2.0, 0.0, ortho, rx, ry, elev_deg=th)
        BR.set_world(1.0)
        f = os.path.join(OUT, "t.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        worst = max(worst, BR.window_stats(a, BR.to_pixel_window(wp))["mean"])
        c = BR.window_stats(a, BR.to_pixel_window(wc))["mean"]
        ctrl_ok &= abs(c - 0.05) <= 1e-4
        os.remove(f)
    return worst, ctrl_ok, rx, mm, cap


def form(prm, face, mmpx, pitch, wins, theta=-40.0, family="floor"):
    sc, p, cx0, tw, ortho, rx, ry, mm, cap = build(prm, face, mmpx, family=family)
    nwin = min(60001, max(361, int(round(p.face_h / mm)) | 1))
    acc = {h: np.zeros(nwin) for h in wins}
    acc_c = {h: np.zeros(nwin) for h in wins}
    pk = []
    BR.configure_cycles(SPP, True)
    for i in range(NPH):
        dz = (-pitch / 2.0) + pitch * i / NPH
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw / 2.0, 0.0, ortho, rx, ry, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(theta, tw / 2.0, 0.0, BEAM, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "f.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        for h in wins:
            hh = min(h, p.face_h)
            acc[h] += recentre(z_profile(a, BR.to_pixel_window(
                (0.0, p.face_w, -hh / 2, hh / 2))), nwin)
            acc_c[h] += recentre(z_profile(a, BR.to_pixel_window(
                (cx0, cx0 + p.face_w, -hh / 2, hh / 2))), nwin)
        pp = recentre(z_profile(a, BR.to_pixel_window(
            (0.0, p.face_w, -p.face_h / 2, p.face_h / 2))), nwin)
        pc = recentre(z_profile(a, BR.to_pixel_window(
            (cx0, cx0 + p.face_w, -p.face_h / 2, p.face_h / 2))), nwin)
        pk.append(float(pp.max()) / float(pc.max()) if pc.max() > 0 else np.nan)
        os.remove(f)
    curve = []
    for h in wins:
        rp, rc = rms_width(acc[h], mm), rms_width(acc_c[h], mm)
        curve.append((h, rp / rc if rc else None))
    conv, best = False, curve[-1]
    for i in range(1, len(curve)):
        a0, b0 = curve[i - 1][1], curve[i][1]
        if a0 and b0 and abs(b0 - a0) / b0 <= 0.02:
            conv, best = True, curve[i]; break
    return best[1], best[0], conv, float(np.nanmean(pk)), rx, mm, cap


rows = []
for name, fam in FAMS.items():
    if ONLY and ONLY not in name:
        continue
    mmpx = fam["feat"] / 4.0
    print("\n===== %s   최소피처 %.2f mm -> 밀도 %.3f mm/px ====="
          % (name, fam["feat"], mmpx), flush=True)
    print("%-7s %-7s %-9s %-9s %-10s %-9s %-8s %-7s %s"
          % ("판mm", "칸수", "총량%", "뭉개기", "창mm", "정면", "화면px", "대조", "시간"),
          flush=True)
    # HEAD-ON: theta 0, feature-resolved density, on a 10-cell patch. It is a
    # PEAK and a peak is LOCAL -- resolving the honeycomb's 0.08 mm wall across
    # a 400 mm panel is 15 000 px and hours per row, while ten cells of it is
    # minutes and measures the same feature. Measured today: head-on does not
    # move with panel size once the feature is resolved (0.18881 / 0.18895 at
    # 100 and 200 mm), so the patch is legitimate.
    patch = fam["pitch"] * 10.0
    famly = fam.get("family", "floor")
    _, _, _, hd0, rxh, mmh, _ = form(fam["prm"], patch, mmpx, fam["pitch"],
                                     [patch], theta=0.0, family=famly)
    print("  정면(0도) 10칸 조각 %.0f mm, 밀도 %.3f, 화면 %d px -> %.5f"
          % (patch, mmh, rxh, hd0), flush=True)
    for face in PANELS:
        t0 = time.time()
        try:
            # totals and smear are density-blind (measured over a 40x range),
            # so they run at the protocol density and stay fast
            rho, ok, rx1, mm1, c1 = totals(fam["prm"], face, 0.215,
                                           family=famly)
            wins = [w for w in (24., 48., 96., 192., 384., face) if w <= face]
            sm, win, conv, hd, rx2, mm2, c2 = form(fam["prm"], face, 0.215,
                                                   fam["pitch"], sorted(set(wins)),
                                                   family=famly)
            hd = hd0
        except Exception as e:
            print("%-7.0f  실패: %s" % (face, repr(e)[:80]), flush=True); continue
        rows.append(dict(family=name, face=face, rho=rho, smear=sm, head_on=hd,
                         window=win, converged=conv, mm_per_px=mm2, res_x=rx2,
                         feat_px=fam["feat"] / mm2, ctrl_ok=ok))
        print("%-7.0f %-7.0f %-9.4f %-9.4f %-10s %-9.5f %-8d %-7s %.0fs"
              % (face, face / fam["pitch"], 100 * rho, sm,
                 "%.0f%s" % (win, "" if conv else "!"), hd, rx2,
                 "OK" if ok else "FAIL", time.time() - t0), flush=True)
        json.dump(rows, open(LOG, "w"), indent=1)
print("\n@@DONE@@", flush=True)
