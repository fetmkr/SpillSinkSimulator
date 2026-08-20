"""GATE 12 (skipped twice, now run): is the cone converged in tessellation?

GATE 2 proved scale invariance with the CELL COUNT held constant -- triangle
count was exactly 7512 on every rung -- so it controlled for mesh density
rather than testing it. A pyramid face is exactly planar, so its triangulation
is exact and there is nothing to converge. A CONE is not: geom3d builds it from
`radial_seg` flat facets, a FIXED COUNT, so what the project calls a cone is
really a 32-gonal pyramid at every size.

That matters because the family's whole claim is rotational symmetry -- "no
azimuth presents a flat to the beam" -- which a 32-gon only approximates, and
because cone and pyramid are ranked against each other on differences of a few
percent. A tessellation bias of that size decides the comparison.

The project's own record already flags the mechanism: `profile_ridge` notes
that a tip built from an EVEN number of chords has no facet facing the observer
while an ODD number puts one exactly normal to it, so a head-on specular return
can switch on with parity rather than with geometry. Both 32 (the default) and
the sweep below cross that boundary.

PRE-REGISTERED:
  T1  rho_dh still moves between radial_seg 32 and 64 by more than the 1-2 %
      measurement floor. If it does, every published cone total carries a
      tessellation bias and the cone-vs-pyramid ranking is not safe.
  T2  head-on moves MORE than rho_dh, and non-monotonically, because it is a
      peak fed by the tip's facets and those flip with parity.
  T3  smear barely moves -- it is a width, and a width does not care which
      facet catches the specular lobe.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy, numpy as np                                   # noqa: E402
import blender_render as BR, form_buildable as FB         # noqa: E402
import rig_v2 as R2                                       # noqa: E402
from form_metrics import z_profile, recentre, rms_width   # noqa: E402

OUT = "/tmp/simsrv/gate12"; os.makedirs(OUT, exist_ok=True)
FACE, SPP, NPH, BEAM = 150.0, 384, 8, 7.5
BASE = dict(pitch=5.5, depth=30.0, tip_radius=0.2, jitter=0.0, height_seg=12)

def run(seg, mmpx=0.215):
    prm = dict(BASE); prm.update(radial_seg=seg, face_w=FACE, face_h=FACE,
                                 margin_depths=2.0, backing=2.0)
    old = R2.MM_PER_PX; R2.MM_PER_PX = mmpx
    try:
        sc = R2.build(prm, samples=SPP, family="cone3d")
        p, cx0 = sc["p"], sc["ctrl_x0"]; tw = sc["total_w"]; ortho = tw * 1.02
        rx, ry, mm, cap = R2.resolution_for(ortho, p.face_h)
    finally:
        R2.MM_PER_PX = old
    ntri = 0
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.calc_loop_triangles(); ntri += len(o.data.loop_triangles)
    wp, wc = R2.full_face_windows(p, cx0, inset_mm=R2.sky_inset_mm(mm))
    BR.configure_cycles(SPP, True)
    worst, ok = 0.0, True
    for th in (0.0, -40.0):
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
    accp = np.zeros(nwin); accc = np.zeros(nwin); pk = []
    for i in range(NPH):
        dz = (-BASE["pitch"]/2) + BASE["pitch"]*i/NPH
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw/2, 0.0, ortho, rx, ry, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(0.0, tw/2, 0.0, BEAM, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "f.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        pp = recentre(z_profile(a, BR.to_pixel_window(
            (0., p.face_w, -p.face_h/2, p.face_h/2))), nwin)
        pc = recentre(z_profile(a, BR.to_pixel_window(
            (cx0, cx0+p.face_w, -p.face_h/2, p.face_h/2))), nwin)
        accp += pp; accc += pc
        pk.append(float(pp.max())/float(pc.max()) if pc.max() > 0 else np.nan)
        os.remove(f)
    return worst, rms_width(accp, mm)/rms_width(accc, mm), float(np.nanmean(pk)), ntri, ok

rows = []
print("콘 간격5.5/깊이30/팁반지름0.2 · 판 %.0f — 둥근 면을 몇 조각으로 쪼개나" % FACE, flush=True)
print("%-8s %-10s %-11s %-10s %-10s %-7s %s"
      % ("조각수", "삼각형", "총량%", "뭉개기", "정면", "대조", "시간"), flush=True)
prev = None
for seg in (8, 16, 32, 64, 128):
    t0 = time.time()
    try:
        rho, sm, hd, nt, ok = run(seg)
    except Exception as e:
        print("%-8d 실패: %s" % (seg, repr(e)[:80]), flush=True); continue
    d = "" if prev is None else " (%+.2f %%)" % (100*(rho-prev)/prev)
    rows.append(dict(seg=seg, rho=rho, smear=sm, head_on=hd, tris=nt, ctrl=ok))
    print("%-8d %-10d %-11.5f%-11s %-10.5f %-7s %.0fs"
          % (seg, nt, 100*rho, d, hd, "OK" if ok else "FAIL", time.time()-t0),
          flush=True)
    print("         뭉개기 %.4f" % sm, flush=True)
    prev = rho
    json.dump(rows, open(os.path.join(OUT, "gate12.json"), "w"), indent=1)

print("\n=== 판정 ===", flush=True)
if len(rows) >= 2:
    for key, name, lim in (("rho","총량",0.02), ("smear","뭉개기",0.02),
                           ("head_on","정면",0.02)):
        a, b = rows[-2][key], rows[-1][key]
        print("  %-6s 조각 %d -> %d : %+6.2f %%  %s"
              % (name, rows[-2]["seg"], rows[-1]["seg"], 100*(b-a)/a,
                 "수렴" if abs(b-a)/b <= lim else "**아직 움직임**"), flush=True)
    d32 = [r for r in rows if r["seg"] == 32]
    if d32:
        print("  기본값 32 대비 최종: 총량 %+.2f %%  정면 %+.2f %%"
              % (100*(rows[-1]["rho"]-d32[0]["rho"])/d32[0]["rho"],
                 100*(rows[-1]["head_on"]-d32[0]["head_on"])/d32[0]["head_on"]),
              flush=True)
print("@@DONE@@", flush=True)
