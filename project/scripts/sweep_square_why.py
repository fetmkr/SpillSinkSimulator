# -*- coding: utf-8 -*-
"""사각 격자가 비스듬한 각도에서 왜 지나. 모양 탓인가 구멍 크기 탓인가.

2026-08-25 측정: 같은 간격 9.53 / 벽 0.08 / 바닥판까지 칠함에서

    정면   벌집 0.03949 %  사각 0.03735 %   사각이 6 % 낫다 (테두리가 적어서)
    40도   벌집 0.20073 %  사각 0.21350 %   사각이 6 % 나쁘다

정면은 예상대로였다. 40도는 반대였다. 이유가 둘 중 하나다.

    구멍 크기  같은 '간격' 이면 사각 셀 넓이가 `p^2`, 육각은 `0.866 p^2` 다.
               사각이 15 % 큰 구멍이다. 큰 구멍은 덜 가둔다.
    모양       사각은 모서리가 90 도라 두 벽이 빛을 온 방향으로 되돌린다.
               육각은 120 도라 안 그렇다.

가르는 방법. `honeycomb` 가족은 벽이 전부 홑겹인 수학적 육각이라
테두리 넓이가 사각과 **똑같다** (앱 계산으로 둘 다 1.68 %). 그래서

    honeycomb 9.53  대  square 9.53      테두리 같음, 구멍은 육각이 15 % 작음
    honeycomb 9.53  대  square 8.87      테두리 거의 같음, 구멍 같음
                                         (8.87 = 9.53 x sqrt(0.866))

둘째 줄에서 차이가 사라지면 원인은 구멍 크기다. 남아 있으면 모양이다.

    zsh scripts/run_batch.sh scripts/sweep_square_why.py squarewhy
"""
import os
import sys
import json
import time
import math

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb_depth")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "square_why.json")

DEPTH, PANEL, WALL = 40.0, 200.0, 0.08
TOP = "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
HEX_P = 9.53
EQ_AREA_P = HEX_P * math.sqrt(math.sqrt(3.0) / 2.0)   # 같은 셀 넓이인 사각 간격

CASES = [("honeycomb", HEX_P, "홑겹 육각, 간격 9.53"),
         ("square", HEX_P, "사각, 간격 9.53 -- 구멍이 15 % 크다"),
         ("square", EQ_AREA_P, "사각, 간격 %.2f -- 구멍 넓이가 같다"
          % EQ_AREA_P),
         ("comb", HEX_P, "펼친 벌집 (두 겹 벽), 간격 9.53 -- 기준")]


def spec(family, pitch, panel=None):
    tp = {"pitch": pitch, "wall_top": WALL, "wall_bot": WALL}
    if family == "comb":
        tp.update(comb_expand=1.0, jitter=0.0)
    else:
        tp.update(jitter=0.0)
    return {"top": family, "top_params": tp, "depth": DEPTH,
            "panel": panel or PANEL, "floor": "none", "margin_depths": 0.2}


rows = []
print("전부 무소, 깊이 %.0f, 벽 %.2f mm. 바닥판까지 칠한 경우.\n"
      % (DEPTH, WALL), flush=True)
print("%-10s %-6s | %10s %10s %10s | %8s | %8s | %5s"
      % ("모양", "간격", "총량 정면", "총량 20도", "총량 40도", "반짝임",
         "셀 넓이", "초"), flush=True)

for family, pitch, note in CASES:
    t0 = time.time()
    planes = SS.measure(spec(family, pitch), THETAS, None, SLIDER, SAMPLES,
                        phis=PHIS, coating=TOP)
    tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
    f = SS.form(spec(family, pitch, panel=pitch * 10.0), thetas=[0.0],
                n_phase=6, samples=SAMPLES, beam_w=7.5, diffuse_frac=None,
                roughness=SLIDER, coating=TOP)
    pk = f.get("peak")
    if pk is None or tot.get("0") is None:
        raise SystemExit("빈 칸 (%s %.2f) -- 인정 안 함" % (family, pitch))
    area = (pitch ** 2 if family == "square"
            else math.sqrt(3.0) / 2.0 * pitch ** 2)
    rows.append({"family": family, "pitch": pitch, "note": note,
                 "wall": WALL, "depth": DEPTH, "cell_area_mm2": area,
                 "top": TOP, "alpha": 0.039, "slider": SLIDER,
                 "samples": SAMPLES, "total": tot, "planes": planes,
                 "head_on": pk, "sec": round(time.time() - t0, 1)})
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-10s %-6.2f | %9.5f%% %9.5f%% %9.5f%% | %8.4f | %7.1f | %5.0f"
          % (family, pitch, 100 * tot["0"], 100 * tot["20"], 100 * tot["40"],
             pk, area, rows[-1]["sec"]), flush=True)

by = {(r["family"], round(r["pitch"], 2)): r for r in rows}
hexr = by[("honeycomb", round(HEX_P, 2))]
print("\n홑겹 육각을 1 로 놓으면 (1 보다 크면 그쪽이 밝다 = 나쁘다)", flush=True)
for family, pitch, note in CASES[1:]:
    r = by[(family, round(pitch, 2))]
    print("  %-34s 정면 %.3f · 20도 %.3f · 40도 %.3f"
          % (note, r["total"]["0"] / hexr["total"]["0"],
             r["total"]["20"] / hexr["total"]["20"],
             r["total"]["40"] / hexr["total"]["40"]), flush=True)
print("\n같은 넓이에서도 차이가 남으면 모양 탓, 사라지면 구멍 크기 탓이다.",
      flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
