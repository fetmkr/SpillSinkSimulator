# -*- coding: utf-8 -*-
"""밑변 50 mm 피라미드의 높이를 얼마로 할까 -- 1단계, 반사 총량만.

2026-08-27. 벌집은 칠하기가 어려워 보류하고 피라미드로 돌아왔다. 사용자가
정한 조건:

    모양      사각 피라미드
    밑변      50 mm 고정 (간격도 50 mm)
    판        500 x 500 mm -> 피라미드 10 x 10 = 100 개
    높이      50 ~ 250 mm 를 바꿔가며 (250 이면 1 대 5)
    바탕      무광 검정 5 % 페인트
    덧칠      무소블랙을 **팁에서 20 mm**, 높이와 무관하게 mm 로 고정
    끝 평평   1.0 mm (사용자 확인 2026-08-27)

**끝 평평은 가정이 아니라 확인받은 값이다.** 눌러 찍는 판은 수학적인 점을
못 만들고, 앱의 공정 표가 "누른 판: 끝 평평 >= 판 두께" 라고 적는다. 그리고
그 평평한 면은 정면을 똑바로 본다 -- 벌집에서 포일 테두리가 정면 반사의
51 % 를 맡았던 것과 같은 자리다. 3단계에서 따로 훑는다.

왜 총량만 먼저 재나. 실측한 비용이 그렇게 강제한다:

    반사 총량 한 각도    0.74 초
    뭉개기·반짝임 한 각도  10 분을 넘겨서 끊었다

600 배다. 그래서 총량으로 아홉 점을 훑어 경향을 보고, 거기서 셋을 골라
2단계에서 나머지 두 축을 잰다. 순서는 사용자가 제안한 것이고, 비용이
그것 말고 다른 길을 안 준다.

기준선을 같이 잰다. 비율만 있고 기준이 없으면 읽는 사람이 크기를 모른다.

    민판 5 %      모든 비율의 분모
    민판 무소     도료가 갈 수 있는 바닥
    발주 사양     밑변 4 / 높이 22 / 끝 0.4. 다만 같은 도장 규칙(팁에서 20 mm)
                  을 적용하면 높이 22 짜리는 사실상 전체가 무소가 된다.
                  그 사실을 표에 적는다.

    zsh scripts/run_batch.sh scripts/sweep_pyramid_height.py pyrheight
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "pyramid_height")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "height_totals.json")

PITCH, PANEL, TIP = 50.0, 500.0, 1.0
BASE, TOP = "wall_5pct", "musou_fit"
SPRAY = 20.0                     # 팁에서 몇 mm 를 무소로. mm 고정.
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
HEIGHTS = [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0]


def spec_pyr(depth, pitch=PITCH, tip=TIP, panel=PANEL):
    return {"top": "pyramid",
            "top_params": {"pitch": pitch, "tip_flat": tip,
                           "apex_jitter": 0.0, "tip_drop": 0.0},
            "depth": depth, "panel": panel, "floor": "none",
            "margin_depths": 0.2}


def spec_flat():
    # `none` 은 구조가 없는 민판이다. 모든 비율의 분모.
    return {"top": "none", "top_params": {}, "depth": 10.0, "panel": PANEL,
            "floor": "none", "margin_depths": 0.2}


def run(label, spec, kw, note=""):
    t0 = time.time()
    planes = SS.measure(spec, THETAS, None, SLIDER, SAMPLES, phis=PHIS, **kw)
    tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
    if tot.get("0") is None:
        raise SystemExit("빈 칸 (%s) -- 인정 안 함" % label)
    r = {"label": label, "spec": spec, "coating": kw, "note": note,
         "total": tot, "total_phi0": planes["0"], "planes": planes,
         "alpha": 0.039, "slider": SLIDER, "samples": SAMPLES,
         "sec": round(time.time() - t0, 1)}
    print("%-26s | %9.5f%% %9.5f%% %9.5f%% | %5.0f"
          % (label, 100 * tot["0"], 100 * tot["20"], 100 * tot["40"], r["sec"]),
          flush=True)
    return r


rows = []
print("밑변 %.0f mm · 판 %.0f mm · 끝 평평 %.1f mm · 무소는 팁에서 %.0f mm\n"
      % (PITCH, PANEL, TIP, SPRAY), flush=True)
print("%-26s | %10s %10s %10s | %5s"
      % ("경우", "총량 정면", "총량 20도", "총량 40도", "초"), flush=True)

print("-- 기준선 --", flush=True)
rows.append(run("민판 5 % 페인트", spec_flat(), dict(coating=BASE),
                "모든 비율의 분모"))
rows.append(run("민판 무소", spec_flat(), dict(coating=TOP),
                "도료가 갈 수 있는 바닥"))
rows.append(run("발주 사양 4/22", spec_pyr(22.0, pitch=4.0, tip=0.4, panel=116.0),
                dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY),
                "높이 22 라 팁에서 20 mm 면 사실상 전체가 무소다"))

print("-- 높이 훑기 (밑변 50 고정) --", flush=True)
for h in HEIGHTS:
    r = run("높이 %3.0f" % h, spec_pyr(h),
            dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY))
    r["depth"] = h
    r["pitch"] = PITCH
    r["tip_flat"] = TIP
    r["aspect"] = h / PITCH
    r["spray_mm"] = SPRAY
    r["spray_frac"] = SPRAY / h
    # 끝의 평평한 면이 차지하는 넓이. 벌집의 포일 테두리와 같은 자리다.
    r["tip_area_frac"] = (TIP / PITCH) ** 2
    rows.append(r)
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)

json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)

flat = rows[0]
print("\n민판 5 %% 를 1 로 놓으면 (작을수록 어둡다)", flush=True)
print("%-26s | %8s %8s %8s | %8s %8s"
      % ("경우", "정면", "20도", "40도", "높이/밑변", "무소 몫"), flush=True)
for r in rows[3:]:
    print("%-26s | %8.4f %8.4f %8.4f | %8.1f %7.0f %%"
          % (r["label"], r["total"]["0"] / flat["total"]["0"],
             r["total"]["20"] / flat["total"]["20"],
             r["total"]["40"] / flat["total"]["40"],
             r["aspect"], 100 * r["spray_frac"]), flush=True)

# 높이를 더 주는 값어치가 어디서 꺾이나. 다음 높이로 갈 때 몇 % 나아지나.
print("\n한 칸 더 깊게 가면 (정면 총량 기준)", flush=True)
hs = [r for r in rows if r.get("depth")]
for a, b in zip(hs, hs[1:]):
    d = 100.0 * (1 - b["total"]["0"] / a["total"]["0"])
    print("  %3.0f -> %3.0f mm : %+5.1f %%" % (a["depth"], b["depth"], d),
          flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
