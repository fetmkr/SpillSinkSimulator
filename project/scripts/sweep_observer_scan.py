# -*- coding: utf-8 -*-
"""관객이 어디 서 있느냐에 따라 얼마나 밝게 보이나 -- 벌집과 피라미드.

2026-08-27. 오늘까지 이 프로젝트의 카메라는 판 법선에 붙박이였다. 그래서
발표된 모든 봉우리는 "판에서 똑바로 나오는 밝기" 였다. 관객이 어디 서
있느냐는 한 번도 안 쟀다.

방을 알고 나니 그게 맞는 질문이 아니었다. 패널은 천장 6 m 에 붙고 프로젝터는
2 m 에서 45~60 도로 쏜다. 패널은 30~45 도로 맞는다. 관객은 10 x 10 m 바닥에
흩어져 있고 한 패널을 저마다 다른 각도로 본다.

부호가 답을 가른다
------------------
`blender_render.add_stripe` 는 램프를 `(cx, d cos t, z + d sin t)` 에 놓고,
`setup_camera` 는 카메라를 **글자 그대로 같은 식**으로 놓는다. 그러니

    빔 +40, 관찰자 +40   두 개가 같은 자리. 빛이 온 쪽에서 되본다.
    빔 -40, 관찰자 +40   거울 방향. 빛이 온 쪽의 반대다.

첫 훑기에서 `-40` 만 읽고 "관객 자리는 어둡다" 고 쓸 뻔했다. `+40` 이
16 배 밝다. 그래서 이 스크립트는 **두 부호를 다 잰다.**

왜 같은 쪽이 밝은가 (렌더러가 그렇게 나온 뒤에 맞춰본 설명이다)
------------------------------------------------------------
빔이 40 도로 들어오면 셀 한쪽 벽이 팁에서 `간격/tan(40도)` = 11.4 mm 까지
밝아진다. 그 벽의 법선은 관 축과 직각이다. 그래서

    관 축을 똑바로 내려다보면   벽이 옆으로 서서 안 보인다. 어두운 바닥만 보인다.
    빛이 온 쪽에서 보면          밝아진 벽이 그대로 보인다.
    반대쪽에서 보면              밝아진 벽의 뒷면이라 안 보인다.

좁은 봉우리가 아니라 **한쪽 넓은 범위가 통째로 밝다.** 이것이 맞다면
피라미드도 같은 이유로 한쪽이 밝아야 한다. 그래서 둘 다 잰다.

피라미드 판 크기
----------------
봉우리는 그 자리의 밝기라 큰 창이 필요 없다. 뭉개기와 달리 되돌아온 빛을
다 담을 필요가 없다. 그래서 판을 200 mm (피라미드 4 개) 로 줄여 시간을 산다.
**이 판으로는 뭉개기를 인정하지 않는다.** 값이 나와도 기록만 하고 안 쓴다.

    zsh scripts/run_batch.sh scripts/sweep_observer_scan.py obsscan
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
PATH = os.path.join(OUT, "observer_scan_both.json")

BASE, TOP = "wall_5pct", "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 256
N_PHASE = 6
THETAS = [0.0, 40.0, -40.0]          # 정면 · 같은 쪽 · 반대쪽
OBS = [0.0, 20.0, 30.0, 40.0, 50.0, 60.0]

CASES = [
    # 이름, 사양, 도장, 뭉개기를 인정하나
    ("벌집 9.53 / 깊이 40",
     {"top": "comb",
      "top_params": {"pitch": 9.53, "wall_top": 0.08, "wall_bot": 0.08,
                     "comb_expand": 1.0, "jitter": 0.0},
      "depth": 40.0, "panel": 95.3, "floor": "none", "margin_depths": 0.2},
     dict(coating=TOP, deep_coating=BASE, paint_depth=20.0), False),
    ("피라미드 밑변 50 / 높이 250",
     {"top": "pyramid",
      "top_params": {"pitch": 50.0, "tip_flat": 1.0, "apex_jitter": 0.0,
                     "tip_drop": 0.0},
      "depth": 250.0, "panel": 200.0, "floor": "none", "margin_depths": 0.2},
     dict(coating=TOP, deep_coating=BASE, paint_depth=20.0), False),
]

rows = []
print("관찰자 각도별 봉우리. 민판 무광 검정 = 1.0.\n", flush=True)
print("바탕 5 %% 페인트 · 무소는 팁에서 20 mm · 표본 %d · 위상 %d\n"
      % (SAMPLES, N_PHASE), flush=True)

for name, spec, kw, smear_ok in CASES:
    print("== %s (판 %.0f mm) ==" % (name, spec["panel"]), flush=True)
    hdr = "%8s |" % "관찰자"
    for t in THETAS:
        hdr += " %14s" % ("빔 %+.0f도" % t)
    print(hdr + " |    초", flush=True)
    for oe in OBS:
        t0 = time.time()
        r = SS.form(spec, thetas=THETAS, n_phase=N_PHASE, samples=SAMPLES,
                    phis=[0.0], obs_elev=oe, **kw)
        pbt = r.get("peak_by_theta") or {}
        if not pbt:
            raise SystemExit("peak_by_theta 가 비었다 (%s %.0f도) -- 인정 안 함"
                             % (name, oe))
        rows.append({"case": name, "spec": spec, "coating": kw,
                     "obs_elev": oe, "thetas": THETAS,
                     "peak_by_theta": pbt,
                     "rms_by_theta": r.get("rms_by_theta"),
                     "smear": r.get("smear"),
                     "smear_trustworthy": smear_ok,
                     "obs_elev_deg": r.get("obs_elev_deg"),
                     "mm_per_px": r.get("mm_per_px"),
                     "mm_per_px_z": r.get("mm_per_px_z"),
                     "n_phase": N_PHASE, "samples": SAMPLES,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        line = "%7.0f도 |" % oe
        for t in THETAS:
            v = pbt.get("%+.0f" % t)
            line += " %14s" % (("%.4f" % v) if v is not None else "·")
        print(line + " | %5.0f" % rows[-1]["sec"], flush=True)
    print("", flush=True)

# 같은 쪽이 반대쪽보다 몇 배 밝나. 이것이 이 훑기의 요점이다.
print("빔이 같은 쪽에서 올 때가 반대쪽일 때보다 몇 배 밝나", flush=True)
for name, _, _, _ in CASES:
    print("  %s" % name, flush=True)
    for r in [x for x in rows if x["case"] == name]:
        a = (r["peak_by_theta"] or {}).get("+40")
        b = (r["peak_by_theta"] or {}).get("-40")
        if a and b:
            print("    관찰자 %2.0f도 : 같은 쪽 %.4f · 반대쪽 %.4f · %.0f 배"
                  % (r["obs_elev"], a, b, a / b), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
