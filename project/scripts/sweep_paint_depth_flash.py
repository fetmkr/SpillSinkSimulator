# -*- coding: utf-8 -*-
"""정면 반짝임만 따로 채운다. `sweep_paint_depth.py` 의 2단계가 비워 둔 칸이다.

왜 따로 도나. 2단계에서 반짝임 칸이 전부 비었다. 이유가 둘이었다.

    1. `form` 을 -40, +40 도로만 불렀다. 반짝임은 정면(0도) 값이다.
       -40/+40 은 모양 뭉개기용 각도다. 0도가 없으면 봉우리가 안 나온다.
    2. 반환 키를 `head_on` 으로 읽었다. `form` 이 주는 이름은 `peak` 다.

한 줄에 실수 두 개였다. 뭉개기는 그 호출로 제대로 나왔으므로 그대로 두고,
여기서는 반짝임만 32가지 연구와 똑같은 방법으로 재서 같은 파일에 채운다.

같은 방법이란 (sweep_comb_musou_v2.py:110-114):
    셀 열 개짜리 조각에 정면 한 각도, 위상 6, 빔 7.5 mm.
    판 전체로 재도 같은 수가 나오고 시간은 15분의 1 이다.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/sweep_paint_depth_flash.py
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

ROOT = os.path.dirname(HERE)
PATH = os.path.join(ROOT, "results", "paint_depth", "paint_depth_9p53_40.json")
FLASH_AT = [0.0, 2.0, 5.0, 10.0, 40.0]

rows = json.load(open(PATH))
r0 = rows[0]
PITCH, DEPTH = r0["pitch"], r0["depth"]
BASE, TOP = r0["base"], r0["top"]
SLIDER, SAMPLES = r0["slider"], r0["samples"]

SPEC = {"top": "comb",
        "top_params": {"pitch": PITCH, "wall_top": r0["foil"],
                       "wall_bot": r0["foil"], "comb_expand": 1.0,
                       "jitter": 0.0},
        "depth": DEPTH, "panel": PITCH * 10.0, "floor": "none",
        "margin_depths": 0.2}


def arms(d):
    if d <= 0.0:
        return dict(coating=BASE)
    if d >= DEPTH:
        return dict(coating=TOP)
    return dict(coating=TOP, deep_coating=BASE, paint_depth=d)


by_d = {r["paint_depth"]: r for r in rows}
print("정면 반짝임. 셀 열 개 조각, 정면 한 각도, 위상 6, 빔 7.5 mm.\n",
      flush=True)
print("%6s | %9s | %5s" % ("N mm", "반짝임", "초"), flush=True)
for d in FLASH_AT:
    t0 = time.time()
    f = SS.form(SPEC, thetas=[0.0], n_phase=6, samples=SAMPLES, beam_w=7.5,
                diffuse_frac=None, roughness=SLIDER, **arms(d))
    pk = f.get("peak")
    if pk is None:
        raise SystemExit("N=%s 에서 봉우리가 비었다 -- 결과로 인정 안 함" % d)
    r = by_d[d]
    r["head_on"] = pk
    r["head_on_method"] = "10-cell patch, theta 0, n_phase 6, beam 7.5 mm"
    r["head_on_sec"] = round(time.time() - t0, 1)
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%6.1f | %9.4f | %5.0f" % (d, pk, r["head_on_sec"]), flush=True)

lo = by_d[0.0]["head_on"]
hi = by_d[DEPTH]["head_on"]
print("\n안 칠했을 때 %.4f, 끝까지 칠했을 때 %.4f -- %.1f %% 움직인다."
      % (lo, hi, 100.0 * abs(hi - lo) / lo), flush=True)
print("@@DONE@@", flush=True)
