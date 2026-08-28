# -*- coding: utf-8 -*-
"""빔 자리를 렌더 한 번에 넣을 수 있나. 재서 확인한다.

지금은 빔 자리마다 사진을 한 장씩 찍는다. 자리 6 개면 6 장, 24 개면 24 장이다.
실측으로 시간이 자리 수에 정비례한다 (피라미드 한 각도: 자리 6 에 36 초,
24 에 153 초). 자리를 수백 개로 늘려야 하는데 이 구조로는 못 한다.

문헌은 한 번에 넣으라고 한다. Radiance genBSDF 는 원점 2000 개를 rfluxmtx
호출 **한 번**에 넘기고 (`genBSDF.pl:200`, `-c $nsamp`), RayFlare 도 자리
900 개에 광선 예산을 나눠 준다. 근거는 Cook 1986 이다 -- 적분 변수를 차원을
하나 더 늘린 것으로 보고 그 축에 표본을 흩뿌린다. PBRT 는 "몬테카를로 수렴
속도는 차원 수와 무관하다" 고 적는다. 그래서 자리를 늘려도 렌더가 안 비싸진다.

**그런데 우리 도구가 그걸 할 수 있는지는 아무도 안 봤다.**

Cycles 의 띠 조명은 면 광원이다. 그림자 광선마다 그 면 위의 한 점을 골라
쏜다. 그러니 **띠를 자리마다 하나씩 놓고 한 번에 렌더**하면, Cycles 가 광선
마다 그 중 하나를 골라 쓴다. 세기를 자리 수로 나눠 주면 합이 지금과 같다.

무엇을 재는가
------------
    A  지금 방식   자리마다 렌더, 프로파일을 더해 평균
    B  한 번 렌더  자리마다 띠를 놓고 세기를 나눠, 한 장
    총 광선 수를 맞춘다 (A 는 표본 S 짜리 N 장, B 는 표본 S x N 짜리 1 장)

**뭉개기와 정면 반짝임이 서로 다르게 나올 것으로 본다.**

뭉개기는 프로파일을 **더한 다음** 폭을 잰다. B 도 더한 프로파일을 준다.
같아야 한다.

정면 반짝임은 자리마다 최대값을 뽑고 **그것들을 평균**한다. B 는 더한
프로파일의 최대값을 준다. **평균의 최대 대 최대의 평균이라 다른 양이다.**
어느 쪽이 맞는지는 이 검사가 정하지 않는다. 다만 다르다는 것을 숫자로
확인해 둔다 -- 다르다는 걸 모르고 바꾸면 발표된 값이 조용히 달라진다.

    zsh scripts/run_batch.sh scripts/probe_onepass_beam.py onepass
"""
import os
import sys
import json
import math
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np              # noqa: E402
import blender_render as BR     # noqa: E402
import sim_server as SS         # noqa: E402
import form_buildable as FB     # noqa: E402
from form_mtf import z_profile, recentre, rms_width   # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb20")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "onepass_beam.json")
TMP = "/tmp/simsrv"

SPEC = {"top": "pyramid",
        "top_params": {"pitch": 50.0, "tip_flat": 1.0, "apex_jitter": 0.0,
                       "tip_drop": 0.0},
        "depth": 250.0, "panel": 200.0, "floor": "none", "margin_depths": 0.2}
THETA, OBS = 40.0, 60.0        # 자리마다 값이 2853 배 갈렸던 그 자리
NPOS = 6
SAMPLES = 256
BEAM = 7.5
SPREAD = 1.0
KW = dict(coating="musou_fit", deep_coating="wall_5pct", paint_depth=20.0)


def build():
    """장면을 세우고 창과 화소 배치를 돌려준다. 두 방식이 같은 장면을 쓴다."""
    m = dict(SPEC, margin_depths=2.0)          # form() 이 하는 그대로
    prm = SS._render_params(m)
    cfg = {"tag": "onepass", "out_dir": TMP, "results_dir": TMP,
           "family": SS._render_family(m), "params": prm, "renders": [],
           "spec_roughness": 0.19748417658131498}
    cfg["paint_depth"] = KW["paint_depth"]
    cfg["deep_coating"] = SS._coat(KW["deep_coating"])
    cfg.update(SS._coat(KW["coating"]))
    BR.clear_scene()
    p, cs, ctrl_x0 = BR.build_scene(cfg)
    total_w = ctrl_x0 + p.face_w
    cx, cz = total_w / 2.0, 0.0
    ortho = total_w * 1.02
    res_x = max(400, min(FB.RES_CAP, int(round(ortho / FB.MM_PER_PX))))
    res_y = max(200, int(round(res_x * (p.face_h * 1.06) / ortho)))
    BR.setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=OBS)
    mm_px = ortho / res_x
    mm_pz = mm_px / max(math.cos(math.radians(OBS)), 1e-6)
    w_panel, w_ctrl = BR.measurement_windows(p, ctrl_x0, None)
    return (p, cx, cz, total_w, res_x, res_y, mm_px, mm_pz,
            BR.to_pixel_window(w_panel), BR.to_pixel_window(w_ctrl))


def shoot(tag, positions, strength, samples):
    """띠를 `positions` 자리마다 놓고 한 장 찍는다. 프로파일 둘을 돌려준다."""
    for o in [x for x in bpy.data.objects if x.name.startswith("stripe")]:
        bpy.data.objects.remove(o, do_unlink=True)
    BR.set_world(0.0)
    for z in positions:
        BR.add_stripe(THETA, cx, cz, BEAM, total_w, strength=strength,
                      spread_deg=SPREAD, target_z=z)
    BR.configure_cycles(samples, True)
    exr = os.path.join(TMP, tag + ".exr")
    BR.render_to(exr, os.path.join(TMP, tag + ".png"))
    arr = BR.read_exr(exr, res_x, res_y)
    nwin = max(FB.NWIN, int(round(p.face_h / mm_px)) | 1)
    pp = recentre(z_profile(arr, px_panel), mm_px, nwin)
    pc = recentre(z_profile(arr, px_ctrl), mm_px, nwin)
    try:
        os.remove(exr)
    except OSError:
        pass
    return pp, pc


import bpy  # noqa: E402  (블렌더 안에서만 있다)

(p, cx, cz, total_w, res_x, res_y, mm_px, mm_pz,
 px_panel, px_ctrl) = build()
pitch = 50.0
POS = [(-pitch / 2.0) + pitch * i / NPOS for i in range(NPOS)]

print("피라미드 밑변 50 / 높이 250 · 판 200 · 빔 %+.0f도 · 관찰자 %.0f도"
      % (THETA, OBS), flush=True)
print("자리 %d 개, 자리마다 %.2f mm\n" % (NPOS, pitch / NPOS), flush=True)

# ---- A. 지금 방식: 자리마다 한 장
t0 = time.time()
acc_p = np.zeros(max(FB.NWIN, int(round(p.face_h / mm_px)) | 1))
acc_c = np.zeros_like(acc_p)
peaks = []
for i, z in enumerate(POS):
    pp, pc = shoot("A%02d" % i, [z], 400.0, SAMPLES)
    acc_p += pp
    acc_c += pc
    peaks.append(float(pp.max()) / float(pc.max()))
secA = time.time() - t0
acc_p /= NPOS
acc_c /= NPOS
A = {"way": "자리마다 한 장 (지금)", "renders": NPOS, "samples": SAMPLES,
     "sec": round(secA, 1),
     "smear": rms_width(acc_p, mm_pz) / rms_width(acc_c, mm_pz),
     "peak_mean_of_peaks": float(np.mean(peaks)),
     "peak_of_mean": float(acc_p.max()) / float(acc_c.max()),
     "peak_by_pos": peaks}
print("A 자리마다 한 장   : %d 장 · %5.1f 초 · 뭉개기 %.4f · "
      "봉우리(자리별 평균) %.5f · 봉우리(합친 뒤) %.5f"
      % (A["renders"], A["sec"], A["smear"], A["peak_mean_of_peaks"],
         A["peak_of_mean"]), flush=True)

# ---- B. 한 번에: 띠를 자리마다 놓고 세기를 나눈다
t0 = time.time()
pp, pc = shoot("B", POS, 400.0 / NPOS, SAMPLES * NPOS)
secB = time.time() - t0
B = {"way": "한 번에 (띠 %d 개)" % NPOS, "renders": 1,
     "samples": SAMPLES * NPOS, "sec": round(secB, 1),
     "smear": rms_width(pp, mm_pz) / rms_width(pc, mm_pz),
     "peak_of_mean": float(pp.max()) / float(pc.max())}
print("B 한 번에         : %d 장 · %5.1f 초 · 뭉개기 %.4f · "
      "봉우리(합친 뒤) %.5f"
      % (B["renders"], B["sec"], B["smear"], B["peak_of_mean"]), flush=True)

print("\n견줌", flush=True)
ds = 100.0 * (B["smear"] / A["smear"] - 1.0)
dp = 100.0 * (B["peak_of_mean"] / A["peak_of_mean"] - 1.0)
print("  뭉개기          A %.4f  B %.4f  차이 %+.2f %%" % (A["smear"], B["smear"], ds),
      flush=True)
print("  봉우리(합친 뒤)  A %.5f  B %.5f  차이 %+.2f %%"
      % (A["peak_of_mean"], B["peak_of_mean"], dp), flush=True)
print("  시간            A %.1f 초  B %.1f 초  %.2f 배"
      % (A["sec"], B["sec"], B["sec"] / max(A["sec"], 1e-9)), flush=True)
print("\n**자리별 평균과 합친 뒤 최대값은 서로 다른 양이다.**", flush=True)
print("  자리별 평균 %.5f  대  합친 뒤 %.5f  = %.2f 배"
      % (A["peak_mean_of_peaks"], A["peak_of_mean"],
         A["peak_mean_of_peaks"] / max(A["peak_of_mean"], 1e-12)), flush=True)
print("  B 는 합친 뒤 값만 줄 수 있다. 자리별 값은 사라진다.", flush=True)

json.dump({"spec": SPEC, "theta": THETA, "obs_elev": OBS, "positions": POS,
           "beam_w": BEAM, "coating": KW, "A": A, "B": B},
          open(PATH, "w"), indent=1, ensure_ascii=False)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
