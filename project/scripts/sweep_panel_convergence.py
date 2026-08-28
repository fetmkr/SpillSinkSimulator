# -*- coding: utf-8 -*-
"""칸이 몇 개 들어가야 답이 안 변하나 -- 판 크기 수렴 사다리.

2026-08-27. `gate_panel_size_peak.py` 가 떨어졌다. 밑변 50 피라미드의 봉우리가
판 200 에서 0.46746, 판 300 에서 0.53523, 판 500 에서 0.50772 로 움직인다.
칸 수로는 4 / 6 / 10 개다.

**화소 문제가 아니다.** mm/px 는 세 판 다 0.215 이고, 판이 커지면 화소가
그만큼 는다 (판 200 이 2.3 백만, 판 500 이 12.9 백만). 리그는 밀도를 못
지키면 조용히 성기게 가는 대신 `RES_CAP` 에서 거절한다.

되풀이되는 무늬는 **칸을 충분히 보면 답이 안 변해야 한다.** 그 자리를 찾는
것이 이 사다리다. 안 변하는 자리를 찾으면 그것이 앞으로의 규약이 된다.

전에 확인한 것은 다른 모양이다. 2026-08-21 리그 감사가 판 400/700/1000 에서
다섯 자리까지 같다는 것을 보였는데 그건 **벌집 간격 6** 이라 칸이 예순 개
넘게 들어간다. 간격 50 은 판 500 에 열 개다. 여섯 배 적은데 같은 결론을
옮겨 쓴 것이 이번 실수다. [[isolate-one-variable-before-blaming-shape]]

비용
----
시간이 화소를 따라간다. 실측으로 판 200 이 34 초, 300 이 80 초, 500 이 301 초.
판 700 은 24.6 백만 화소라 10 분쯤, 900 은 40.0 백만이라 16 분쯤 걸린다.
그래서 한 각도(빔 40, 관찰자 40)만 재고 위상 6 으로 둔다. **여기서 보는 것은
절대값이 아니라 판을 늘릴 때 값이 멈추느냐다.**

    zsh scripts/run_batch.sh scripts/sweep_panel_convergence.py panelconv
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
PATH = os.path.join(OUT, "panel_convergence.json")

BASE, TOP = "wall_5pct", "musou_fit"
SAMPLES, N_PHASE = 256, 6
SPRAY = 20.0
THETA, OBS = 40.0, 40.0
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


LADDERS = [
    ("피라미드 밑변 50 / 높이 250", pyr, 50.0,
     [200.0, 300.0, 500.0, 700.0, 900.0]),
    ("벌집 셀 9.53 / 깊이 40", comb, 9.53, [95.3, 190.6, 381.2]),
]

rows = []
print("빔 %+.0f도 · 관찰자 %.0f도 · 무소 팁 %.0f mm · 바탕 5 %% 페인트 · "
      "표본 %d · 위상 %d" % (THETA, OBS, SPRAY, SAMPLES, N_PHASE), flush=True)
print("보는 것은 절대값이 아니라 **판을 늘릴 때 값이 멈추느냐**다.\n", flush=True)

for name, mk, pitch, panels in LADDERS:
    print("== %s ==" % name, flush=True)
    print("%8s %6s | %10s | %11s | %6s"
          % ("판", "칸 수", "봉우리", "한 칸 전 대비", "분"), flush=True)
    prev = None
    for panel in panels:
        t0 = time.time()
        r = SS.form(mk(panel), thetas=[THETA], n_phase=N_PHASE,
                    samples=SAMPLES, phis=[0.0], obs_elev=OBS, **KW)
        v = (r.get("peak_by_theta") or {}).get("%+.0f" % THETA)
        if v is None:
            raise SystemExit("빈 칸 (%s 판 %.0f) -- 인정 안 함" % (name, panel))
        step = None if prev is None else (v / prev - 1.0)
        rows.append({"family": name, "panel": panel, "pitch": pitch,
                     "cells_across": panel / pitch, "peak": v,
                     "step_vs_prev": step, "theta": THETA, "obs_elev": OBS,
                     "mm_per_px": r.get("mm_per_px"), "n_phase": N_PHASE,
                     "samples": SAMPLES, "spray_mm": SPRAY, "coating": KW,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        print("%8.1f %6.1f | %10.5f | %11s | %6.1f"
              % (panel, panel / pitch, v,
                 "-" if step is None else "%+.2f %%" % (100 * step),
                 rows[-1]["sec"] / 60.0), flush=True)
        prev = v
    print("", flush=True)

# 멈춘 자리를 찾는다. 한 칸 전 대비 1 % 안으로 들어오면 거기서부터 쓸 수 있다.
print("한 칸 더 넓혀도 1 %% 안에서만 움직이는 첫 자리", flush=True)
for name, _, pitch, _ in LADDERS:
    mine = [r for r in rows if r["family"] == name]
    hit = None
    for r in mine:
        if r["step_vs_prev"] is not None and abs(r["step_vs_prev"]) <= 0.01:
            hit = r
            break
    if hit:
        print("  %-28s 판 %.0f mm (칸 %.0f 개) 부터"
              % (name, hit["panel"], hit["cells_across"]), flush=True)
    else:
        print("  %-28s **아직 안 멈췄다.** 사다리를 더 늘려야 한다." % name,
              flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
