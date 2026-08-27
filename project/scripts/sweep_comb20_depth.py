# -*- coding: utf-8 -*-
"""셀 20 mm 벌집은 깊이를 얼마로 해야 20~40 도가 좋은가.

2026-08-27. 방 조건이 정해졌다. 10 x 10 m, 천장 6 m, 프로젝터 높이 2 m 에서
수평보다 45~60 도 위로 쏜다. 패널은 **천장**에 붙는다. 그러면

    쏘는 각 45 도 -> 천장에 닿는 각 45 도
    쏘는 각 60 도 -> 천장에 닿는 각 30 도

**정면(0 도)은 이 방에서 안 일어난다.** 프로젝터가 천장 바로 밑에 있어야
하는데 그러면 빔이 위로 안 간다. 그래서 여기서는 30~45 도가 답을 정하고,
지금까지 봐 온 정면 값은 참고로만 둔다.

각도를 늘렸다. 지금까지 0/20/40 만 쟀는데 방이 30~45 를 쓰므로
**0, 20, 30, 40, 45** 를 잰다.

셀을 20 mm 로 키우면 무엇이 달라지나
------------------------------------
비스듬한 빛이 벽에 닿는 깊이가 `간격 / tan(각도)` 다. 셀이 커지면 그만큼
깊이 들어간다.

    셀 9.53 · 40 도 -> 11.4 mm      셀 20 · 40 도 -> 23.8 mm
    셀 9.53 · 30 도 -> 16.5 mm      셀 20 · 30 도 -> 34.6 mm
    셀 9.53 · 20 도 -> 26.2 mm      셀 20 · 20 도 -> 55.0 mm

그러니 셀 20 mm 는 20 도까지 챙기려면 55 mm 넘게 깊어야 한다는 뜻이다.
그게 맞는지 재서 확인한다.

테두리는 오히려 준다. 넓이가 `3t/p` 라 셀이 커지면 작아진다.

    셀 9.53 · 포일 0.08 -> 2.52 %      셀 20 · 포일 0.08 -> 1.20 %

도장
----
바닥판을 무소로 못 칠한다는 조건이다 (사용자 확인 2026-08-27). 바탕은
5 % 페인트, 무소는 뿌려서 닿는 만큼만 팁에서 20 mm.

    zsh scripts/run_batch.sh scripts/sweep_comb20_depth.py comb20
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
PATH = os.path.join(OUT, "comb20_depth.json")

FOIL = 0.08
BASE, TOP = "wall_5pct", "musou_fit"
SPRAY = 20.0
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -30.0, 30.0, -40.0, 40.0, -45.0, 45.0]
PHIS = [0, 45, 90]
DEPTHS = [20.0, 30.0, 40.0, 50.0, 60.0, 80.0, 100.0]
PITCH = 20.0
PANEL = 300.0          # 셀 20 mm 이므로 15 칸. 9.53 짜리의 200 mm(21 칸)와 비슷


def spec(pitch, depth, panel=PANEL):
    return {"top": "comb",
            "top_params": {"pitch": pitch, "wall_top": FOIL, "wall_bot": FOIL,
                           "comb_expand": 1.0, "jitter": 0.0},
            "depth": depth, "panel": panel, "floor": "none",
            "margin_depths": 0.2}


KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)


def run(label, sp):
    t0 = time.time()
    planes = SS.measure(sp, THETAS, None, SLIDER, SAMPLES, phis=PHIS, **KW)
    tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
    if tot.get("0") is None:
        raise SystemExit("빈 칸 (%s) -- 인정 안 함" % label)
    return tot, planes, round(time.time() - t0, 1)


rows = []
print("셀 %.0f mm · 포일 %.2f · 판 %.0f · 무소 팁 %.0f mm · 바닥판은 5 %% 페인트"
      % (PITCH, FOIL, PANEL, SPRAY), flush=True)
print("천장 패널이 실제로 받는 각도는 30~45 도다. 정면은 안 온다.\n", flush=True)
hdr = "%6s |" % "깊이"
for t in (0, 20, 30, 40, 45):
    hdr += " %8s" % ("%d도" % t)
print(hdr + " |  벽 닿는 깊이(40도) |    초", flush=True)

for d in DEPTHS:
    tot, planes, sec = run("깊이 %.0f" % d, spec(PITCH, d))
    reach40 = PITCH / math.tan(math.radians(40.0))
    r = {"pitch": PITCH, "depth": d, "foil": FOIL, "panel": PANEL,
         "spray_mm": SPRAY, "base": BASE, "top": TOP, "alpha": 0.039,
         "slider": SLIDER, "samples": SAMPLES, "thetas": THETAS,
         "total": tot, "planes": planes,
         "reach_40deg_mm": reach40,
         "rim_fraction": 3.0 * FOIL / PITCH,
         "exit_half_deg": math.degrees(math.atan((PITCH / 2.0) / d)),
         "sec": sec}
    rows.append(r)
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    line = "%6.0f |" % d
    for t in ("0", "20", "30", "40", "45"):
        line += " %7.4f%%" % (100 * tot[t])
    print(line + " | %8.1f mm | %5.0f" % (reach40, sec), flush=True)

# 견줄 자리: 지금까지 써 온 셀 9.53
print("\n-- 견줌: 셀 9.53 --", flush=True)
for d in (30.0, 40.0):
    tot, planes, sec = run("9.53 깊이 %.0f" % d, spec(9.53, d, 200.0))
    rows.append({"pitch": 9.53, "depth": d, "foil": FOIL, "panel": 200.0,
                 "spray_mm": SPRAY, "total": tot, "planes": planes,
                 "alpha": 0.039, "slider": SLIDER, "samples": SAMPLES,
                 "thetas": THETAS,
                 "rim_fraction": 3.0 * FOIL / 9.53,
                 "reach_40deg_mm": 9.53 / math.tan(math.radians(40.0)),
                 "exit_half_deg": math.degrees(math.atan((9.53/2.0)/d)),
                 "sec": sec})
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    line = "%6.0f |" % d
    for t in ("0", "20", "30", "40", "45"):
        line += " %7.4f%%" % (100 * tot[t])
    print(line + " | (셀 9.53)         | %5.0f" % sec, flush=True)

c20 = [r for r in rows if r["pitch"] == PITCH]
print("\n한 칸 더 깊게 갈 때 30~45 도가 얼마나 좋아지나", flush=True)
for a, b in zip(c20, c20[1:]):
    g = lambda r, k: r["total"][k]
    print("  %3.0f -> %3.0f mm : 30도 %+5.1f %% · 40도 %+5.1f %% · 45도 %+5.1f %%"
          % (a["depth"], b["depth"],
             100 * (1 - g(b, "30") / g(a, "30")),
             100 * (1 - g(b, "40") / g(a, "40")),
             100 * (1 - g(b, "45") / g(a, "45"))), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
