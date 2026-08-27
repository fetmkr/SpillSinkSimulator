# -*- coding: utf-8 -*-
"""높이가 주는 이득이 모양 덕인가 도장 덕인가. 변수를 하나만 남긴다.

1단계(`sweep_pyramid_height.py`)는 무소를 **팁에서 20 mm 로 고정**해서 쟀다.
만드는 조건으로는 그게 맞다 -- 뿌려서 닿는 깊이는 높이와 무관하다. 그런데
그러면 높이가 올라갈수록 무소가 덮는 몫이 줄어든다:

    높이  50 mm  ->  무소 40 %
    높이 250 mm  ->  무소  8 %

즉 저 표에는 **모양이 좋아지는 것과 도장이 나빠지는 것이 섞여 있다.**
그런데도 총량이 계속 내려갔으니 모양의 이득은 표에 보이는 것보다 크다.
얼마나 큰지는 재야 안다.

여기서는 재료를 **높이와 무관하게** 고정해서 모양만 남긴다.

    A  전부 5 % 페인트   -- 모양의 이득만. 도료는 어디서나 같다.
    B  전부 무소         -- 도료가 갈 수 있는 바닥에서의 모양 이득.

1단계의 "팁에서 20 mm" 는 실제로 만들 물건이고, A 와 B 는 그 숫자를 읽는
자다. 셋을 나란히 놓아야 "높이를 늘리면 좋아진다" 가 무엇 덕인지 말할 수
있다. [[isolate-one-variable-before-blaming-shape]] 와 같은 계열이다.

    zsh scripts/run_batch.sh scripts/sweep_pyramid_height_iso.py pyrheightiso
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
PATH = os.path.join(OUT, "height_isolated.json")

PITCH, PANEL, TIP = 50.0, 500.0, 1.0
BASE, TOP = "wall_5pct", "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
HEIGHTS = [50.0, 75.0, 100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0]
ARMS = [("A 전부 5 % 페인트", dict(coating=BASE)),
        ("B 전부 무소", dict(coating=TOP))]


def spec(depth):
    return {"top": "pyramid",
            "top_params": {"pitch": PITCH, "tip_flat": TIP,
                           "apex_jitter": 0.0, "tip_drop": 0.0},
            "depth": depth, "panel": PANEL, "floor": "none",
            "margin_depths": 0.2}


rows = []
print("밑변 %.0f · 판 %.0f · 끝 평평 %.1f. 재료를 높이와 무관하게 고정.\n"
      % (PITCH, PANEL, TIP), flush=True)
print("%-18s %6s | %10s %10s %10s | %5s"
      % ("재료", "높이", "총량 정면", "총량 20도", "총량 40도", "초"), flush=True)

for label, kw in ARMS:
    for h in HEIGHTS:
        t0 = time.time()
        planes = SS.measure(spec(h), THETAS, None, SLIDER, SAMPLES,
                            phis=PHIS, **kw)
        tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
        if tot.get("0") is None:
            raise SystemExit("빈 칸 (%s %s) -- 인정 안 함" % (label, h))
        rows.append({"arm": label, "depth": h, "pitch": PITCH,
                     "tip_flat": TIP, "aspect": h / PITCH, "coating": kw,
                     "total": tot, "planes": planes, "alpha": 0.039,
                     "slider": SLIDER, "samples": SAMPLES,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        print("%-18s %6.0f | %9.5f%% %9.5f%% %9.5f%% | %5.0f"
              % (label, h, 100 * tot["0"], 100 * tot["20"],
                 100 * tot["40"], rows[-1]["sec"]), flush=True)

by = {(r["arm"], r["depth"]): r for r in rows}
print("\n높이 50 을 1 로 놓으면 -- 모양만의 이득", flush=True)
print("%6s | %-22s %-22s" % ("높이", "A 전부 5 % 페인트", "B 전부 무소"),
      flush=True)
for h in HEIGHTS:
    line = "%6.0f |" % h
    for label, _ in ARMS:
        a, b = by[(label, 50.0)], by[(label, h)]
        line += (" 정면 %.3f 40도 %.3f  "
                 % (b["total"]["0"] / a["total"]["0"],
                    b["total"]["40"] / a["total"]["40"]))
    print(line, flush=True)

print("\n두 재료 사이의 비 (5 % 를 무소로 바꾸면 몇 배 어두워지나)", flush=True)
for h in HEIGHTS:
    a, b = by[("A 전부 5 % 페인트", h)], by[("B 전부 무소", h)]
    print("  높이 %3.0f : 정면 %.2f 배 · 40도 %.2f 배"
          % (h, a["total"]["0"] / b["total"]["0"],
             a["total"]["40"] / b["total"]["40"]), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
