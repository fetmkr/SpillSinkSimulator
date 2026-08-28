# -*- coding: utf-8 -*-
"""이 방이 실제로 쓰는 각도 전부에서, 관객 자리별 밝기.

2026-08-27 첫 훑기(`sweep_observer_scan.py`)는 빔 40 도만 봤다. 방은 30 도에서
45 도까지 다 쓴다 -- 프로젝터가 60 도로 쏘면 패널에 30 도, 45 도로 쏘면 45 도.
그래서 여기서는 **빔 30 / 40 / 45 도를 다 재고**, 피라미드는 높이 셋을 잰다.

정면(0 도)은 뺐다. 이 방에서 안 일어난다. 그 대신 각 빔마다 부호 둘을 다 잰다.

    빔 +30 에 관찰자 +40   빛이 온 쪽. 밝은 쪽이다.
    빔 -30 에 관찰자 +40   거울 방향. 오히려 어둡다.

부호가 뭘 뜻하는지는 코드에 있다. `add_stripe` 는 램프를
`(cx, d cos t, z + d sin t)` 에, `setup_camera` 는 카메라를 글자 그대로 같은
식으로 놓는다. 첫 훑기에서 한 부호만 읽고 결론을 뒤집을 뻔했다.

피라미드 높이를 셋 재는 이유
--------------------------
높이 250 이 40 도에서 0.4675 로 되쏘는 것을 봤다. 밑변 50 에 높이 250 이면
옆면이 바닥에서 84.3 도로 서고, 마주 보는 두 면이 반각 5.7 도짜리 좁은 골을
이룬다. 두 번 튕긴 빛이 온 길로 나가는 구조다.

**높이를 낮추면 골이 벌어지니 되쏨이 무뎌질 것이다** [추측]. 높이 100 이면
옆면이 76.0 도, 골 반각 14.0 도다. 이 추측이 맞는지가 이번 훑기의 요점이다.
맞으면 "총량은 높이가 올릴수록 좋고 되쏨은 높이가 올릴수록 나쁘다" 는
맞바꿈이 숫자로 나온다.

    각도(도) = atan(높이 / (밑변/2)),  골 반각 = 90 - 그 각도

    높이 100 -> 76.0 도, 골 반각 14.0 도
    높이 175 -> 81.9 도, 골 반각  8.1 도
    높이 250 -> 84.3 도, 골 반각  5.7 도

판 크기
------
봉우리는 그 자리의 밝기라 큰 창이 필요 없다. 뭉개기와 달리 되돌아온 빛을 다
담을 필요가 없다. 그래서 판을 작게 잡아 시간을 산다.
**이 판으로는 뭉개기를 인정하지 않는다.** 값이 나와도 기록만 하고 안 쓴다.

    zsh scripts/run_batch.sh scripts/sweep_observer_room.py obsroom
"""
import os
import sys
import json
import math
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb20")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "observer_room.json")

BASE, TOP = "wall_5pct", "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 256
N_PHASE = 6
SPRAY = 20.0
# 방이 쓰는 각도만. 정면은 뺐다. 부호 둘을 다 잰다.
THETAS = [30.0, -30.0, 40.0, -40.0, 45.0, -45.0]
OBS = [0.0, 20.0, 30.0, 40.0, 50.0, 60.0]


def pyr(h, panel):
    return {"top": "pyramid",
            "top_params": {"pitch": 50.0, "tip_flat": 1.0,
                           "apex_jitter": 0.0, "tip_drop": 0.0},
            "depth": h, "panel": panel, "floor": "none",
            "margin_depths": 0.2}


CASES = [
    ("벌집 9.53 / 깊이 40",
     {"top": "comb",
      "top_params": {"pitch": 9.53, "wall_top": 0.08, "wall_bot": 0.08,
                     "comb_expand": 1.0, "jitter": 0.0},
      "depth": 40.0, "panel": 95.3, "floor": "none", "margin_depths": 0.2}),
    ("피라미드 밑변 50 / 높이 100", pyr(100.0, 200.0)),
    ("피라미드 밑변 50 / 높이 175", pyr(175.0, 200.0)),
    ("피라미드 밑변 50 / 높이 250", pyr(250.0, 200.0)),
]
KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)

rows = []
print("관객 자리별 봉우리. 민판 무광 검정 = 1.0.", flush=True)
print("바탕 5 %% 페인트 · 무소는 팁에서 %.0f mm · 표본 %d · 위상 %d"
      % (SPRAY, SAMPLES, N_PHASE), flush=True)
print("이 방이 쓰는 빔 각도는 30~45 도다. 정면은 안 잰다.\n", flush=True)

for name, sp in CASES:
    if sp["top"] == "pyramid":
        face = math.degrees(math.atan(sp["depth"] / (50.0 / 2.0)))
        print("== %s (판 %.0f · 옆면 %.1f도 · 골 반각 %.1f도) =="
              % (name, sp["panel"], face, 90.0 - face), flush=True)
    else:
        print("== %s (판 %.0f) ==" % (name, sp["panel"]), flush=True)
    hdr = "%8s |" % "관찰자"
    for t in THETAS:
        hdr += " %9s" % ("빔 %+.0f" % t)
    print(hdr + " |    초", flush=True)

    for oe in OBS:
        t0 = time.time()
        r = SS.form(sp, thetas=THETAS, n_phase=N_PHASE, samples=SAMPLES,
                    phis=[0.0], obs_elev=oe, **KW)
        pbt = r.get("peak_by_theta") or {}
        if not pbt:
            raise SystemExit("peak_by_theta 가 비었다 (%s %.0f도) -- 인정 안 함"
                             % (name, oe))
        rows.append({"case": name, "spec": sp, "coating": KW,
                     "obs_elev": oe, "thetas": THETAS, "peak_by_theta": pbt,
                     "rms_by_theta": r.get("rms_by_theta"),
                     "smear": r.get("smear"), "smear_trustworthy": False,
                     "obs_elev_deg": r.get("obs_elev_deg"),
                     "mm_per_px": r.get("mm_per_px"),
                     "mm_per_px_z": r.get("mm_per_px_z"),
                     "n_phase": N_PHASE, "samples": SAMPLES,
                     "spray_mm": SPRAY,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        line = "%7.0f도 |" % oe
        for t in THETAS:
            v = pbt.get("%+.0f" % t)
            line += " %9s" % (("%.4f" % v) if v is not None else "·")
        print(line + " | %5.0f" % rows[-1]["sec"], flush=True)
    print("", flush=True)

# 이 훑기의 요점: 되쏨이 얼마나 뾰족한가. 같은 쪽 값의 최대와 최소를 견준다.
print("빛이 온 쪽에서 본 값 -- 얼마나 평평한가 (봉우리 / 골)", flush=True)
for name, _ in CASES:
    mine = [x for x in rows if x["case"] == name]
    for t in (30.0, 40.0, 45.0):
        vs = [(x["obs_elev"], (x["peak_by_theta"] or {}).get("%+.0f" % t))
              for x in mine]
        vs = [(a, b) for a, b in vs if b is not None]
        if not vs:
            continue
        hi = max(vs, key=lambda p: p[1])
        lo = min(vs, key=lambda p: p[1])
        print("  %-28s 빔 %2.0f도 : 가장 밝은 %2.0f도 %.4f · "
              "가장 어두운 %2.0f도 %.4f · %.1f 배"
              % (name, t, hi[0], hi[1], lo[0], lo[1], hi[1] / lo[1]),
              flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
