"""FLOOR PITCH = CELL PITCH: one pyramid per honeycomb cell. HEAD-ON only.

The cheapest floor conceivable: the tool is the same 6.5 mm grid the comb
already is, so the two register by construction and there is no fine
feature to hold. Recorded in phase 6.3 as the user's "cell-matched 45
degree floor" and never measured on the repaired rig.

Baselines: bare honeycomb 1.643 · pyramid order spec 0.182 ·
fine floor (pitch 2, depth 6) 0.118 · pitch 1 depth 0.2 gives 0.293.

Head-on is the axis a floor can actually move: adding a fine floor took it from
1.643 to 0.118 while smear did not budge (0.9831 -> 0.9803). Totals and smear
are therefore not measured here; this asks one question only, which is how
shallow the floor can get before head-on gives up.

Shallow matters because it decides the process. A 45 degree pyramid at pitch 2
is 1 mm deep and vacuum-forms off a cheap tool; a 6 mm floor at pitch 2 is
aspect 3 and needs the same casting the main panel does.

Measured at theta 0 on a 10-cell patch at the density the floor's own tip needs
(tip/4, GATE 16), because head-on is a PEAK and a peak dilutes with pixel size.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import bpy, numpy as np                                   # noqa: E402
import blender_render as BR, form_buildable as FB         # noqa: E402
import rig_v2 as R2, sim_server as SS                     # noqa: E402
from form_metrics import z_profile, recentre              # noqa: E402

OUT = "/tmp/simsrv/cellmatch"; os.makedirs(OUT, exist_ok=True)
PITCH, CELL, SPP, NPH, BEAM = 6.5, 6.0, 384, 8, 7.5
PATCH = PITCH * 10.0
TIP = 0.1   # a cell-pitch floor is coarse; its tip need not be 0.05
MMPX = TIP / 4.0            # 0.0125 -- the floor tip is the finest feature


def head_on(spec):
    m = dict(spec, panel=PATCH, margin_depths=2.0)
    prm = SS._render_params(m); fam = SS._render_family(m)
    old = R2.MM_PER_PX; R2.MM_PER_PX = MMPX
    try:
        sc = R2.build(prm, samples=SPP, family=fam)
        p, cx0 = sc["p"], sc["ctrl_x0"]; tw = sc["total_w"]; ortho = tw * 1.02
        rx, ry, mm, cap = R2.resolution_for(ortho, p.face_h)
    finally:
        R2.MM_PER_PX = old
    nwin = min(60001, max(361, int(round(p.face_h / mm)) | 1))
    BR.configure_cycles(SPP, True)
    pk = []
    for i in range(NPH):
        dz = (-PITCH/2) + PITCH*i/NPH
        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)
        BR.setup_camera(tw/2, 0.0, ortho, rx, ry, elev_deg=0.0)
        BR.set_world(0.0)
        BR.add_stripe(0.0, tw/2, 0.0, BEAM, tw, strength=400.0,
                      spread_deg=FB.SPREAD_DEG, target_z=dz)
        f = os.path.join(OUT, "s.exr"); BR.render_to(f, f.replace(".exr", ".png"))
        a = BR.read_exr(f, rx, ry)
        pp = recentre(z_profile(a, BR.to_pixel_window(
            (0., p.face_w, -p.face_h/2, p.face_h/2))), nwin)
        pc = recentre(z_profile(a, BR.to_pixel_window(
            (cx0, cx0+p.face_w, -p.face_h/2, p.face_h/2))), nwin)
        pk.append(float(pp.max())/float(pc.max()) if pc.max() > 0 else np.nan)
        os.remove(f)
    return float(np.nanmean(pk)), rx


CASES = [
  ("바닥 없음",                 None, None),
  # FLOOR PITCH = CELL PITCH: one pyramid per honeycomb cell, registered to it.
  # This is the cheapest floor that exists -- the tool is the same 6.5 mm grid
  # the comb already is -- and it is the user's own earlier proposal, recorded
  # in phase 6.3 as "cell-matched 45 degree floor". A 45 degree pyramid on a
  # 6.5 mm pitch is 3.25 mm deep.
  ("칸맞춤 간격6.5 · 깊이1",    6.5,  1.0),
  ("칸맞춤 간격6.5 · 깊이2",    6.5,  2.0),
  ("칸맞춤 45도 · 깊이3.25",    6.5,  3.25),
  ("칸맞춤 간격6.5 · 깊이5",    6.5,  5.0),
  ("칸맞춤 간격6.5 · 깊이8",    6.5,  8.0),
  # half the cell pitch: two pyramids per cell, still one simple tool
  ("절반 간격3.25 · 깊이1.6",   3.25, 1.63),
  ("절반 간격3.25 · 깊이3",     3.25, 3.0),
]
print("벌집 칸 %.1f · 칸깊이 %.0f · 조각 %.0fmm · 밀도 %.4f · 정면(0도)만"
      % (PITCH, CELL, PATCH, MMPX), flush=True)
print("기준: 벌집 단독 1.643 · 피라미드 발주 사양 0.182\n", flush=True)
print("%-24s %-8s %-11s %-9s %s" % ("바닥", "종횡비", "정면 반짝임", "화면px", "시간"),
      flush=True)
rows = []
for name, fp, fd in CASES:
    if fp is None:
        spec = dict(top="honeycomb", top_params={"pitch": PITCH,
                    "wall_top": 0.08, "wall_bot": 0.08, "jitter": 0.0},
                    depth=CELL, floor="none")
        asp = "-"
    else:
        spec = dict(top="honeycomb", top_params={"pitch": PITCH,
                    "wall_top": 0.08, "wall_bot": 0.08, "jitter": 0.0},
                    depth=CELL + fd, floor="pyramid", floor_depth=fd,
                    floor_params={"pitch": fp, "tip_flat": TIP})
        asp = "%.2f" % (fd/fp)
    t0 = time.time()
    try:
        hd, rx = head_on(spec)
    except Exception as e:
        print("%-24s 실패: %s" % (name, repr(e)[:70]), flush=True); continue
    rows.append(dict(name=name, pitch=fp, depth=fd, aspect=asp, head_on=hd))
    print("%-24s %-8s %-11.5f %-9d %.0fs" % (name, asp, hd, rx, time.time()-t0),
          flush=True)
    json.dump(rows, open(os.path.join(OUT, "cellmatch.json"), "w"), indent=1)

print("\n=== 정리 ===", flush=True)
base = [r for r in rows if r["pitch"] is None]
if base:
    b = base[0]["head_on"]
    for r in rows[1:]:
        print("  %-24s 바닥없음 대비 %6.1f배 개선 · 피라미드(0.182) 대비 %s"
              % (r["name"], b/r["head_on"],
                 "이김" if r["head_on"] < 0.182 else "짐"), flush=True)
print("@@DONE@@", flush=True)
