# -*- coding: utf-8 -*-
"""테두리를 깎고 바닥판을 피라미드로 바꾸면 얼마나 좋아지나.

어디서 나온 생각인가. 2026-08-25 측정에서 셀 9.53 / 깊이 40 벌집의 정면
반사가 이렇게 갈렸다.

    포일 테두리   51.4 %
    셀 벽         0.4 %
    바닥판        48.3 %

깊이로는 둘 다 못 없앤다. 둘 다 정면을 향한 평평한 면이기 때문이다.
그래서 남은 지렛대는 **그 두 면의 모양을 바꾸는 것**뿐이다.

전파 쪽 최신 연구에서 가져온 것은 원리 하나다. 무반향실 피라미드도,
3D 프린트 기울기 임피던스 구조도, 하는 일이 같다 -- **갑자기 바꾸지 말고
서서히 바꾼다.** 전파는 그걸 임피던스(377 옴에서 0 옴)로 하지만 우리
파장은 구조의 2만분의 1 이라 임피던스 정합이 성립하지 않는다. 우리 쪽
번역은 **살 두께를 깊이에 따라 바꾸는 것**이다.

세 갈래를 잰다.

    A  테두리만 깎는다      wall_top 을 wall_bot 보다 얇게. 벌집 강도는
                            아래벽이 정하고, 정면 반사는 위벽이 정한다
                            (`geom_topo.py:248` 의 노출 넓이가 wall_top 만 쓴다).
                            테두리 넓이가 2.24 % 에서 0.56 % 까지 준다.
    B  바닥판을 피라미드로   평평한 받침판 대신 피라미드를 깐다. 정면으로
                            곧게 들어온 빛이 평면이 아니라 기울어진 면을 만난다.
    AB 둘 다

기준은 오늘 추천한 조합이다: 셀 9.53 · 깊이 40 · 전부 무소.
비교는 세 축 전부로 한다.

    zsh scripts/run_batch.sh scripts/sweep_rim_and_floor.py rimfloor
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb_depth")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "rim_and_floor.json")

PITCH, DEPTH, PANEL = 9.53, 40.0, 200.0
TOP = "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
WALL_BOT = 0.08          # 강도를 정하는 쪽. 고정한다.

# 0.05 는 사용자가 정한 취급 한계다 ("너무 얇으면 손으로 쉽게 찌그러지니").
# 0.03 과 0.02 는 그 아래이고, 만들 수 있는지는 별개 문제라 표에 표시만 한다.
CASES = [
    ("기준",            dict(wall_top=0.08), None,  None),
    ("A 테두리 0.05",   dict(wall_top=0.05), None,  None),
    ("A 테두리 0.03",   dict(wall_top=0.03), None,  None),
    ("A 테두리 0.02",   dict(wall_top=0.02), None,  None),
    ("B 피라미드 바닥 10", dict(wall_top=0.08), "pyramid", 10.0),
    ("B 피라미드 바닥 15", dict(wall_top=0.08), "pyramid", 15.0),
    ("AB 0.05 + 피라미드 10", dict(wall_top=0.05), "pyramid", 10.0),
    ("AB 0.03 + 피라미드 15", dict(wall_top=0.03), "pyramid", 15.0),
]
SMEAR_AT = {"기준", "AB 0.05 + 피라미드 10"}


def spec(tp_extra, floor, fdepth, panel=None):
    tp = {"pitch": PITCH, "wall_top": WALL_BOT, "wall_bot": WALL_BOT,
          "comb_expand": 1.0, "jitter": 0.0}
    tp.update(tp_extra)
    s = {"top": "comb", "top_params": tp, "depth": DEPTH,
         "panel": panel or PANEL, "margin_depths": 0.2}
    if floor:
        s["floor"] = floor
        s["floor_depth"] = fdepth
        s["floor_params"] = {"pitch": PITCH}
    else:
        s["floor"] = "none"
    return s


rows = []
print("셀 %.2f / 깊이 %.0f / 아래벽 %.2f 고정 / 전부 무소.\n"
      % (PITCH, DEPTH, WALL_BOT), flush=True)
print("%-24s | %10s %10s %10s | %8s | %5s"
      % ("경우", "총량 정면", "총량 20도", "총량 40도", "반짝임", "초"),
      flush=True)

for name, tp_extra, floor, fdepth in CASES:
    t0 = time.time()
    s = spec(tp_extra, floor, fdepth)
    planes = SS.measure(s, THETAS, None, SLIDER, SAMPLES, phis=PHIS,
                        coating=TOP)
    tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
    f = SS.form(spec(tp_extra, floor, fdepth, panel=PITCH * 10.0),
                thetas=[0.0], n_phase=6, samples=SAMPLES, beam_w=7.5,
                diffuse_frac=None, roughness=SLIDER, coating=TOP)
    pk = f.get("peak")
    if pk is None or tot.get("0") is None:
        raise SystemExit("빈 칸 (%s) -- 인정 안 함" % name)
    rows.append({"name": name, "pitch": PITCH, "depth": DEPTH,
                 "wall_top": tp_extra["wall_top"], "wall_bot": WALL_BOT,
                 "floor": floor, "floor_depth": fdepth, "top": TOP,
                 "alpha": 0.039, "slider": SLIDER, "samples": SAMPLES,
                 "rim_fraction_est": 3.0 * tp_extra["wall_top"] / PITCH,
                 "total": tot, "planes": planes, "head_on": pk,
                 "smear": None, "sec": round(time.time() - t0, 1)})
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-24s | %9.5f%% %9.5f%% %9.5f%% | %8.4f | %5.0f"
          % (name, 100 * tot["0"], 100 * tot["20"], 100 * tot["40"], pk,
             rows[-1]["sec"]), flush=True)

print("\n모양 뭉개기 -- 두 점만 (한 점에 5 분)\n", flush=True)
print("%-24s | %8s | %6s | %5s" % ("경우", "뭉개기", "담겼나", "초"), flush=True)
by = {r["name"]: r for r in rows}
for name, tp_extra, floor, fdepth in CASES:
    if name not in SMEAR_AT:
        continue
    t0 = time.time()
    fm = SS.form(spec(tp_extra, floor, fdepth), thetas=[-40.0, 40.0],
                 n_phase=6, samples=SAMPLES, phis=PHIS, coating=TOP)
    r = by[name]
    r["smear"] = fm.get("smear")
    r["smear_converged"] = fm.get("converged")
    r["smear_n_phase"] = 6
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-24s | %8s | %6s | %5.0f"
          % (name, ("%.4f" % r["smear"]) if r["smear"] is not None else "-",
             r["smear_converged"], time.time() - t0), flush=True)

ref = rows[0]
print("\n기준을 1 로 놓으면 (작을수록 어둡다 = 좋다)", flush=True)
print("%-24s | %8s %8s %8s %8s"
      % ("경우", "정면", "20도", "40도", "반짝임"), flush=True)
for r in rows:
    print("%-24s | %8.3f %8.3f %8.3f %8.3f"
          % (r["name"], r["total"]["0"] / ref["total"]["0"],
             r["total"]["20"] / ref["total"]["20"],
             r["total"]["40"] / ref["total"]["40"],
             r["head_on"] / ref["head_on"]), flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
