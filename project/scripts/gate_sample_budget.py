# -*- coding: utf-8 -*-
"""빛줄기를 몇 개 쏴야 하나. 지금 256 이 어디서 온 숫자인지 아무도 모른다.

우리는 사진 한 장에 빛줄기(sample) 를 화소마다 256 개 쏜다. 그 사진에서
뽑아내는 것은 점 229 개짜리 곡선 하나다. 점 하나에 빛줄기 24 만 개를 쓰는
셈이다 (가로 945 열을 평균하고 열마다 256 개).

남들이 쓰는 숫자는 이렇다.

    Zemax 권장                점 하나당 1 만
    Radiance rfluxmtx 기본값   점 하나당 1 만
    genBSDF 기본값            점 하나당 2 천

**24 배 많다.** 그리고 그 24 배가 필요한지 잰 적이 없다. 위상 수 검사도 있고
해상도 검사도 있는데 빛줄기 수 검사만 없다.

왜 많이 쓰게 됐는지는 짐작이 간다
--------------------------------
정면 반짝임(head-on peak) 이 곡선의 **최대값**이다. 빛줄기가 적으면 그림이
지글거리고, 지글거리는 곡선의 최대값은 **위로 치우친다.** 잡음 봉우리를
신호로 읽기 때문이다. 그래서 잡음을 없애려고 빛줄기를 많이 쏘게 된다.

뭉개기(smear) 는 곡선 전체의 폭이라 지글거림에 훨씬 덜 흔들린다.
반사 총량(total reflectance) 은 이 길을 안 쓴다 (하늘 조명, 넓이 평균).

**이게 맞다면 최대값을 잡음에 강한 값으로 바꾸는 것만으로 빛줄기를 크게
줄일 수 있다.** 그래서 이 검사는 최대값과 함께 상위 1 % 지점(p99) 도 같이
재서 어느 쪽이 덜 흔들리는지 보인다.

무엇을 보나
----------
빛줄기를 16 / 32 / 64 / 128 / 256 / 512 로 올리며 세 값을 잰다.
**512 를 참값으로 놓고** 각 값이 몇 % 어긋나는지 본다.

    뭉개기 (smear)          곡선의 폭
    반짝임 최대값 (peak)     곡선의 최대값. 지금 쓰는 값
    반짝임 p99              위에서 1 % 지점. 잡음에 강한 대안

같은 자리를 두 번씩 잰다. 렌더러 자체가 흔들리는 폭과, 빛줄기를 줄여서
생기는 차이를 갈라 봐야 하기 때문이다.

    zsh scripts/run_batch.sh scripts/gate_sample_budget.py samplegate
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
import bpy                      # noqa: E402
import blender_render as BR     # noqa: E402
import sim_server as SS         # noqa: E402
import form_buildable as FB     # noqa: E402
from form_mtf import z_profile, recentre, rms_width   # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb20")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "sample_budget.json")
TMP = "/tmp/simsrv"

# 한 경우만 보고 빛줄기 수를 정할 수 없다. 되돌아오는 모양이 셋 다 다르다.
# 민판은 좁고 밝고, 벌집은 좁고 어둡고, 피라미드는 넓게 퍼진다. 잡음이
# 어디에 얼마나 붙는지가 다르므로 셋을 다 본다.
# 모양 셋에 각도 조합 넷. 한 경우만 보고 빛줄기 수를 정할 수 없다.
#
# 되돌아오는 모양이 셋 다 다르다. 민판은 좁고 밝고, 벌집은 좁고 어둡고,
# 피라미드는 넓게 퍼진다. 잡음이 어디에 얼마나 붙는지가 다르다.
#
# 각도도 바꾼다. 관찰자 0 도(정면)는 어두운 바닥만 보이고, 40 도는 밝은
# 벽이 보이고, 60 도는 자리마다 값이 2853 배 갈렸던 자리다. **어두울수록
# 잡음이 크게 보인다** -- 신호가 작으니 잡음의 몫이 커진다. 그래서 가장
# 어두운 조합이 빛줄기를 제일 많이 요구할 것으로 본다 [추측].
SHAPES = [
    ("민판 (평판)",
     {"top": "none", "top_params": {}, "depth": 10.0, "panel": 200.0,
      "floor": "none", "margin_depths": 0.2}),
    ("벌집 9.53 / 깊이 40",
     {"top": "comb",
      "top_params": {"pitch": 9.53, "wall_top": 0.08, "wall_bot": 0.08,
                     "comb_expand": 1.0, "jitter": 0.0},
      "depth": 40.0, "panel": 95.3, "floor": "none", "margin_depths": 0.2}),
    ("피라미드 밑변 50 / 높이 250",
     {"top": "pyramid",
      "top_params": {"pitch": 50.0, "tip_flat": 1.0, "apex_jitter": 0.0,
                     "tip_drop": 0.0},
      "depth": 250.0, "panel": 200.0, "floor": "none", "margin_depths": 0.2}),
]
# (빔 각도, 관찰자 각도)
ANGLES = [(40.0, 0.0), (40.0, 40.0), (40.0, 60.0), (30.0, 30.0)]
CASES = [("%s · 빔%+.0f 관찰%.0f" % (nm, th, ob), sp, th, ob)
         for nm, sp in SHAPES for th, ob in ANGLES]
BEAM, SPREAD = 7.5, 1.0
BEAM_POS = 0.0                  # 자리 하나만. 여기서 보는 것은 빛줄기 수다.
# 앞선 한 경우에서 16 도 512 와 0.1 % 안에서 같았다. 아래쪽을
# 더 보고 위는 참값 하나만 둔다. 경우가 12 개라 사다리를 줄인다.
LADDER = [4, 8, 16, 32, 64, 256]
REPEATS = 2                     # 렌더러 자체 흔들림을 갈라 보려고
KW = dict(coating="musou_fit", deep_coating="wall_5pct", paint_depth=20.0)


def p99(prof):
    """위에서 1 % 지점. 최대값은 잡음 봉우리 하나에 끌려가는데 이건 안 그렇다."""
    return float(np.percentile(prof, 99.0))


rows = []
for CASE_NAME, SPEC, THETA, OBS in CASES:
    print("\n== %s · 빔 %+.0f도 · 관찰자 %.0f도 =="
          % (CASE_NAME, THETA, OBS), flush=True)
    m = dict(SPEC, margin_depths=2.0)
    prm = SS._render_params(m)
    cfg = {"tag": "sbudget", "out_dir": TMP, "results_dir": TMP,
           "family": SS._render_family(m), "params": prm, "renders": [],
           "spec_roughness": 0.19748417658131498,
           "paint_depth": KW["paint_depth"],
           "deep_coating": SS._coat(KW["deep_coating"])}
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
    px_panel, px_ctrl = BR.to_pixel_window(w_panel), BR.to_pixel_window(w_ctrl)
    nwin = max(FB.NWIN, int(round(p.face_h / mm_px)) | 1)

    bins = int(round((w_panel[3] - w_panel[2]) / mm_px))
    cols = int(round((w_panel[1] - w_panel[0]) / mm_px))
    print("화소 %d x %d · 곡선 점 %d 개 · 점 하나가 %d 열을 평균"
          % (res_x, res_y, bins, cols), flush=True)
    print("점 하나당 빛줄기 = 열 %d x 빛줄기 수\n" % cols, flush=True)
    print("%6s %4s | %10s %10s %10s | %10s | %6s"
          % ("빛줄기", "회", "뭉개기", "반짝임 최대", "반짝임 p99",
             "점당 빛줄기", "초"), flush=True)

    for spp in LADDER:
        for k in range(REPEATS):
            for o in [x for x in bpy.data.objects if x.name.startswith("stripe")]:
                bpy.data.objects.remove(o, do_unlink=True)
            BR.set_world(0.0)
            BR.add_stripe(THETA, cx, cz, BEAM, total_w, strength=400.0,
                          spread_deg=SPREAD, target_z=BEAM_POS)
            BR.configure_cycles(spp, True)
            t0 = time.time()
            exr = os.path.join(TMP, "sb_%d_%d.exr" % (spp, k))
            BR.render_to(exr, os.path.join(TMP, "sb.png"))
            arr = BR.read_exr(exr, res_x, res_y)
            pp = recentre(z_profile(arr, px_panel), mm_px, nwin)
            pc = recentre(z_profile(arr, px_ctrl), mm_px, nwin)
            try:
                os.remove(exr)
            except OSError:
                pass
            r = {"case": CASE_NAME, "obs_elev": OBS, "spp": spp, "rep": k,
                 "smear": rms_width(pp, mm_pz) / rms_width(pc, mm_pz),
                 "peak_max": float(pp.max()) / float(pc.max()),
                 "peak_p99": p99(pp) / p99(pc),
                 "per_bin": cols * spp,
                 "sec": round(time.time() - t0, 1)}
            rows.append(r)
            json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
            print("%6d %4d | %10.4f %10.5f %10.5f | %10s | %6.1f"
                  % (spp, k, r["smear"], r["peak_max"], r["peak_p99"],
                     f"{r['per_bin']:,}", r["sec"]), flush=True)

    # 512 를 참값으로 놓고 각 값이 몇 % 어긋나나
    mineall = [r for r in rows if r["case"] == CASE_NAME and r["obs_elev"] == OBS]
    ref = {k: float(np.mean([r[k] for r in mineall if r["spp"] == LADDER[-1]]))
           for k in ("smear", "peak_max", "peak_p99")}
    print("\n빛줄기 %d 을 참값으로 놓고 어긋난 정도" % LADDER[-1], flush=True)
    print("%6s | %12s %12s %12s | %8s"
          % ("빛줄기", "뭉개기", "반짝임 최대", "반짝임 p99", "회당 초"), flush=True)
    for spp in LADDER:
        mine = [r for r in mineall if r["spp"] == spp]
        cell = []
        for k in ("smear", "peak_max", "peak_p99"):
            v = float(np.mean([r[k] for r in mine]))
            cell.append("%+.2f %%" % (100 * (v / ref[k] - 1.0)))
        print("%6d | %12s %12s %12s | %8.1f"
              % (spp, cell[0], cell[1], cell[2],
                 float(np.mean([r["sec"] for r in mine]))), flush=True)

    print("\n같은 설정을 두 번 재서 갈린 폭 (렌더러 자체 흔들림)", flush=True)
    for spp in LADDER:
        mine = [r for r in mineall if r["spp"] == spp]
        if len(mine) < 2:
            continue
        print("  빛줄기 %3d : 뭉개기 %+.2f %% · 최대 %+.2f %% · p99 %+.2f %%"
              % (spp,
                 100 * (mine[1]["smear"] / mine[0]["smear"] - 1),
                 100 * (mine[1]["peak_max"] / mine[0]["peak_max"] - 1),
                 100 * (mine[1]["peak_p99"] / mine[0]["peak_p99"] - 1)), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
