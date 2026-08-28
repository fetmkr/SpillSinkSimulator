# -*- coding: utf-8 -*-
"""모양이 커졌는데 판을 줄여도 같은 답이 나오나.

2026-08-27 관객 훑기는 피라미드를 **판 200 mm** 로 쟀다. 밑변이 50 mm 니
피라미드가 가로 네 개뿐이다. 총량과 뭉개기는 판 500 으로 쟀는데 봉우리만
판 200 이다. 시간을 사려고 그랬다 -- 판 500 짜리 한 각도가 여러 분인데
관객 훑기는 스물넷을 재야 했다.

**그 바꿔치기가 옳은지 이 모양에서는 확인한 적이 없다.**

전에 확인한 것은 다른 모양이다. 2026-08-21 리그 감사가 판 400/700/1000 에서
정면 반짝임이 1.64311 / 1.64309 / 1.64311 로 다섯 자리 같다는 것을 보였는데,
그건 **벌집 간격 6 짜리** 다. 셀이 예순 개 넘게 들어가는 판이었다. 밑변 50 은
간격이 여덟 배라 같은 판에 네 개밖에 안 들어간다. 셀 수가 열 배 넘게 다른데
같은 결론을 옮기면 [[isolate-one-variable-before-blaming-shape]] 를 어기는 것이다.

무엇을 보나
----------
같은 모양·같은 도장·같은 각도에서 판만 바꾼다. 봉우리가 안 움직여야 한다.

    피라미드 밑변 50 / 높이 250 · 판 200 / 300 / 500   (4 / 6 / 10 개)
    벌집 셀 9.53 / 깊이 40      · 판 95.3 / 190.6      (10 / 20 개)

판이 커지면 시야에 든 셀이 늘어난다. 봉우리는 그 자리의 밝기라 셀 수와 무관
해야 하고, 무관하지 않다면 판 200 으로 낸 오늘 결론이 흔들린다.

합격선
------
**상대 1 %.** 렌더러 자체가 같은 요청에 상대 3.1e-08 만큼 흔들리고
(`gate_observer_angle.py` 에 실측이 적혀 있다), 위상 6 짜리 표본 오차가 그보다
훨씬 크다. 1 % 는 오늘 표에서 견주는 차이(벌집 대 피라미드 3.4 배)보다 한참
아래이고, 표본 흔들림보다는 위다.

    zsh scripts/run_batch.sh scripts/gate_panel_size_peak.py panelsize
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb20")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "panel_size_peak.json")

BASE, TOP = "wall_5pct", "musou_fit"
SLIDER, SAMPLES, N_PHASE = 0.19748417658131498, 256, 6
SPRAY = 20.0
THETA, OBS = 40.0, 40.0          # 봉우리가 가장 큰 자리에서 본다
TOL = 0.01                       # 상대 1 %

KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)


def pyr(panel):
    return {"top": "pyramid",
            "top_params": {"pitch": 50.0, "tip_flat": 1.0,
                           "apex_jitter": 0.0, "tip_drop": 0.0},
            "depth": 250.0, "panel": panel, "floor": "none",
            "margin_depths": 0.2}


def comb(panel):
    return {"top": "comb",
            "top_params": {"pitch": 9.53, "wall_top": 0.08, "wall_bot": 0.08,
                           "comb_expand": 1.0, "jitter": 0.0},
            "depth": 40.0, "panel": panel, "floor": "none",
            "margin_depths": 0.2}


FAMILIES = [
    ("피라미드 밑변 50 / 높이 250", pyr, 50.0, [200.0, 300.0, 500.0]),
    ("벌집 셀 9.53 / 깊이 40", comb, 9.53, [95.3, 190.6]),
]

rows = []
FAILED = []
print("판만 바꾸고 봉우리가 움직이나. 빔 %+.0f도 · 관찰자 %.0f도 · "
      "무소 팁 %.0f mm · 바탕 5 %% 페인트 · 표본 %d · 위상 %d"
      % (THETA, OBS, SPRAY, SAMPLES, N_PHASE), flush=True)
print("합격선은 상대 %.0f %%. 그보다 크게 움직이면 판 200 으로 낸 값을 "
      "못 쓴다.\n" % (100 * TOL), flush=True)

for name, mk, pitch, panels in FAMILIES:
    print("== %s ==" % name, flush=True)
    print("%8s %6s | %10s | %9s | %5s"
          % ("판", "칸 수", "봉우리", "가장 작은 판 대비", "초"), flush=True)
    base = None
    for panel in panels:
        t0 = time.time()
        r = SS.form(mk(panel), thetas=[THETA], n_phase=N_PHASE,
                    samples=SAMPLES, phis=[0.0], obs_elev=OBS, **KW)
        v = (r.get("peak_by_theta") or {}).get("%+.0f" % THETA)
        if v is None:
            raise SystemExit("빈 칸 (%s 판 %.0f) -- 인정 안 함" % (name, panel))
        if base is None:
            base = v
        d = v / base - 1.0
        rows.append({"family": name, "panel": panel, "pitch": pitch,
                     "cells_across": panel / pitch, "theta": THETA,
                     "obs_elev": OBS, "peak": v, "rel_vs_smallest": d,
                     "mm_per_px": r.get("mm_per_px"),
                     "mm_per_px_z": r.get("mm_per_px_z"),
                     "n_phase": N_PHASE, "samples": SAMPLES,
                     "spray_mm": SPRAY, "coating": KW,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        bad = abs(d) > TOL
        if bad:
            FAILED.append("%s 판 %.0f" % (name, panel))
        print("%8.1f %6.1f | %10.5f | %+8.2f %% %s | %5.0f"
              % (panel, panel / pitch, v, 100 * d,
                 "<-- 넘음" if bad else "", rows[-1]["sec"]), flush=True)
    print("", flush=True)

# 화소 밀도가 판마다 같았나. 하나라도 성기게 갔으면 위 비교가 뜻이 없다.
mps = sorted(set(round(r["mm_per_px"], 5) for r in rows))
print("쓴 화소 밀도: %s mm/px" % ", ".join("%.5f" % m for m in mps), flush=True)
if len(mps) > 1:
    FAILED.append("판마다 화소 밀도가 달랐다")

print("\n%d 항목 실패" % len(FAILED), flush=True)
if FAILED:
    print("실패: %s" % ", ".join(FAILED), flush=True)
    print("판 200 으로 낸 오늘 봉우리 값들을 다시 봐야 한다.", flush=True)
else:
    print("판을 줄여도 봉우리가 같다. 관객 훑기를 판 200 으로 낸 것이 옳다.",
          flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
sys.exit(1 if FAILED else 0)
