# -*- coding: utf-8 -*-
"""벌집 깊이를 몇으로 할까. 셀 6.35 와 9.53, 깊이 20~60.

32가지 연구(comb_musou_v2)에도 깊이가 있지만 그것은 바탕이 전부 5 % 도료인
경우다. 오늘(2026-08-24) 알아낸 것이 답을 바꾼다: **바닥판은 관 속이 아니라
평평한 받침판이고, 벌집을 붙이기 전에 따로 칠할 수 있다.** 바닥판이 무소면
깊이가 사는 몫이 크게 줄어든다. 그래서 두 경우를 나란히 잰다.

    A  바닥판 못 칠함 -- 위에서 15 mm 만 무소, 벽과 바닥은 5 % 도료
    B  바닥판까지 칠함 -- 판 전체가 무소

실제로 만들 물건은 B 에 가깝다. 오늘 측정에서 깊은 벽(1~20 mm)이 정면
변화의 0.4 % 밖에 안 맡았으므로, "벽 깊은 데는 5 % 인 B" 와 "전부 무소인 B"
가 거의 같기 때문이다. A 는 바닥판을 못 칠했을 때의 바닥값이다.

깊이가 왜 정면만 바꾸나. 바닥에서 출구를 보는 반각이 `atan((간격/2)/깊이)`
라서 깊어질수록 좁아진다. 비스듬한 빛은 얕은 데서 벽에 닿고 나가므로
깊이와 상관이 없다. 이 예상이 맞는지도 표에서 확인된다.

세 축을 다 잰다. 뭉개기는 한 점에 5분이라 추천 셀에서만 잰다.

    zsh scripts/run_batch.sh scripts/sweep_comb_depth_pick.py depthpick
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
PATH = os.path.join(OUT, "comb_depth_pick.json")

FOIL = 0.08
BASE = "wall_5pct"
TOP = "musou_fit"
SLIDER = 0.19748417658131498      # alpha 0.039
SAMPLES = 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
SPRAY = 15.0                      # 뿌려서 닿는 깊이. 오늘 측정에서 40도가 멈춘 값.

PITCHES = [6.35, 9.53]
DEPTHS = [20.0, 30.0, 40.0, 50.0, 60.0]
SMEAR_PITCH = 9.53                # 뭉개기는 한 점에 5 분이라 한 셀만


def spec(pitch, depth, panel=None):
    return {"top": "comb",
            "top_params": {"pitch": pitch, "wall_top": FOIL, "wall_bot": FOIL,
                           "comb_expand": 1.0, "jitter": 0.0},
            "depth": depth, "panel": panel or 200.0, "floor": "none",
            "margin_depths": 0.2}


def arms(kind):
    if kind == "A":
        return dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)
    return dict(coating=TOP)


rows = []
print("셀과 깊이를 바꿔 가며 잰다. A = 바닥판 못 칠함, B = 바닥판까지 칠함.\n",
      flush=True)
print("%-6s %-6s %-3s | %10s %10s %10s | %8s | %5s"
      % ("셀", "깊이", "칠", "총량 정면", "총량 20도", "총량 40도",
         "반짝임", "초"), flush=True)

for pitch in PITCHES:
    for depth in DEPTHS:
        for kind in ("A", "B"):
            t0 = time.time()
            kw = arms(kind)
            planes = SS.measure(spec(pitch, depth), THETAS, None, SLIDER,
                                SAMPLES, phis=PHIS, **kw)
            tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
            # 정면 반짝임은 셀 열 개짜리 조각에서. 32가지 연구와 같은 방법.
            f = SS.form(spec(pitch, depth, panel=pitch * 10.0), thetas=[0.0],
                        n_phase=6, samples=SAMPLES, beam_w=7.5,
                        diffuse_frac=None, roughness=SLIDER, **kw)
            pk = f.get("peak")
            if pk is None or tot.get("0") is None:
                raise SystemExit("빈 칸 (셀 %.2f 깊이 %.0f %s) -- 인정 안 함"
                                 % (pitch, depth, kind))
            half = math.degrees(math.atan((pitch / 2.0) / depth))
            rows.append({"pitch": pitch, "depth": depth, "arm": kind,
                         "spray_mm": SPRAY if kind == "A" else depth,
                         "foil": FOIL, "base": BASE, "top": TOP,
                         "alpha": 0.039, "slider": SLIDER, "samples": SAMPLES,
                         "total": tot, "planes": planes, "head_on": pk,
                         "smear": None,
                         "exit_half_deg": half,
                         "exit_frac": math.sin(math.radians(half)) ** 2,
                         "sec": round(time.time() - t0, 1)})
            json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
            print("%-6.2f %-6.0f %-3s | %9.5f%% %9.5f%% %9.5f%% | %8.4f | %5.0f"
                  % (pitch, depth, kind, 100 * tot["0"], 100 * tot["20"],
                     100 * tot["40"], pk, rows[-1]["sec"]), flush=True)

print("\n모양 뭉개기 -- 셀 %.2f, 바닥판까지 칠한 경우만 (한 점에 5 분)\n"
      % SMEAR_PITCH, flush=True)
print("%-6s | %8s | %5s" % ("깊이", "뭉개기", "초"), flush=True)
by = {(r["pitch"], r["depth"], r["arm"]): r for r in rows}
for depth in DEPTHS:
    t0 = time.time()
    fm = SS.form(spec(SMEAR_PITCH, depth), thetas=[-40.0, 40.0], n_phase=6,
                 samples=SAMPLES, phis=PHIS, **arms("B"))
    r = by[(SMEAR_PITCH, depth, "B")]
    r["smear"] = fm.get("smear")
    r["smear_converged"] = fm.get("converged")
    r["smear_n_phase"] = 6
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-6.0f | %8s | %5.0f"
          % (depth, ("%.4f" % r["smear"]) if r["smear"] is not None else "-",
             time.time() - t0), flush=True)

print("\n깊이가 정면만 바꾸는지 확인 -- 20 mm 대비 60 mm", flush=True)
for pitch in PITCHES:
    for kind in ("A", "B"):
        a, b = by[(pitch, 20.0, kind)], by[(pitch, 60.0, kind)]
        # 처음에 백분율 값을 찍으면서 이름을 "배" 라고 붙였다. 값은 맞고
        # 이름만 틀렸는데, 그런 칸 하나 때문에 이 프로젝트가 이미 한 번
        # 틀린 결론을 냈다.
        print("  셀 %.2f %s: 정면 %.5f %% -> %.5f %%, "
              "40도 %.5f%% -> %.5f%% (%.1f %% 변화)"
              % (pitch, kind, 100 * a["total"]["0"], 100 * b["total"]["0"],
                 100 * a["total"]["40"], 100 * b["total"]["40"],
                 100 * abs(b["total"]["40"] - a["total"]["40"])
                 / a["total"]["40"]), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
