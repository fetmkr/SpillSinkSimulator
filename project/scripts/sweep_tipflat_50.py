# -*- coding: utf-8 -*-
"""밑변 50 피라미드의 끝 평평 사다리 -- 0.5 / 1.0 / 2.0 mm.

눌러 찍는 판은 수학적인 점을 못 만든다. 앱의 공정 표가 "누른 판: 끝 평평 >=
판 두께" 라고 적고, 사용자가 1.0 mm 로 정했다 (2026-08-27).

그 평평한 면은 **판 겉면과 나란하다.** 벌집에서 포일 테두리가 정면 반사의
51.4 % 를 맡았던 것과 정확히 같은 자리다. 넓이는 `(끝/밑변)²` 이라

    끝 0.5 -> 0.0001 (판의 0.01 %)
    끝 1.0 -> 0.0004 (0.04 %)
    끝 2.0 -> 0.0016 (0.16 %)

벌집 테두리가 2.52 % 였으니 그보다 훨씬 작다. 그래도 재는 이유는 이 자리가
지금까지 두 번 크게 물었기 때문이다 -- 벌집 테두리에서, 그리고 발주 사양
끝 0.4 가 끝 0.1 보다 정면에서 8 % 나았을 때.

**이 방은 30~45 도를 쓴다.** 그래서 정면만 보지 않고 30/40/45 도를 같이 잰다.
평평한 면은 판과 나란하니 비스듬한 빛에는 덜 물릴 것이다 [추측]. 확인한다.

    zsh scripts/run_batch.sh scripts/sweep_tipflat_50.py tipflat
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
PATH = os.path.join(OUT, "tipflat_50.json")

PITCH, PANEL = 50.0, 500.0
BASE, TOP = "wall_5pct", "musou_fit"
SPRAY = 20.0
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -30.0, 30.0, -40.0, 40.0, -45.0, 45.0]
PHIS = [0, 45, 90]
TIPS = [0.5, 1.0, 2.0]
HEIGHTS = [100.0, 250.0]        # 낮은 것과 높은 것. 끝의 몫이 다를 수 있다.

KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)

rows = []
print("밑변 %.0f · 판 %.0f · 무소 팁에서 %.0f mm · 바탕 5 %% 페인트\n"
      % (PITCH, PANEL, SPRAY), flush=True)
print("%6s %5s | %9s %9s %9s %9s | %8s | %5s"
      % ("높이", "끝", "정면", "30도", "40도", "45도", "끝 넓이", "초"),
      flush=True)

for h in HEIGHTS:
    for tip in TIPS:
        sp = {"top": "pyramid",
              "top_params": {"pitch": PITCH, "tip_flat": tip,
                             "apex_jitter": 0.0, "tip_drop": 0.0},
              "depth": h, "panel": PANEL, "floor": "none",
              "margin_depths": 0.2}
        t0 = time.time()
        planes = SS.measure(sp, THETAS, None, SLIDER, SAMPLES, phis=PHIS, **KW)
        tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
        if tot.get("0") is None:
            raise SystemExit("빈 칸 (높이 %.0f 끝 %.1f) -- 인정 안 함" % (h, tip))
        rows.append({"depth": h, "pitch": PITCH, "tip_flat": tip,
                     "panel": PANEL, "spray_mm": SPRAY, "thetas": THETAS,
                     "total": tot, "planes": planes,
                     "tip_area_frac": (tip / PITCH) ** 2,
                     "alpha": 0.039, "slider": SLIDER, "samples": SAMPLES,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        print("%6.0f %5.1f | %8.5f%% %8.5f%% %8.5f%% %8.5f%% | %7.3f%% | %5.0f"
              % (h, tip, 100 * tot["0"], 100 * tot["30"], 100 * tot["40"],
                 100 * tot["45"], 100 * rows[-1]["tip_area_frac"],
                 rows[-1]["sec"]), flush=True)

print("\n끝을 키우면 각 각도가 얼마나 나빠지나 (끝 0.5 를 1 로 놓고)", flush=True)
for h in HEIGHTS:
    base = next(r for r in rows if r["depth"] == h and r["tip_flat"] == 0.5)
    for r in [x for x in rows if x["depth"] == h and x["tip_flat"] != 0.5]:
        print("  높이 %3.0f 끝 %.1f : 정면 %+5.1f %% · 30도 %+5.1f %% · "
              "40도 %+5.1f %% · 45도 %+5.1f %%"
              % (h, r["tip_flat"],
                 100 * (r["total"]["0"] / base["total"]["0"] - 1),
                 100 * (r["total"]["30"] / base["total"]["30"] - 1),
                 100 * (r["total"]["40"] / base["total"]["40"] - 1),
                 100 * (r["total"]["45"] / base["total"]["45"] - 1)),
              flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
