# -*- coding: utf-8 -*-
"""빔이 들어오는 각도와 셀 깊이 — 얕은 셀이 어느 각도부터 되나.

    zsh scripts/run_batch.sh scripts/depth_vs_angle_2026_09_18.py depth_vs_angle

계기 (2026-09-18): 천장이 6 m 가 아니라 3.5 m 라, 빔이 천장에 닿는 각이 45~78 도다.
깊이 훑기(2026-09-16)는 방 조건 30~45 도에서만 했다. 스치는 각에서도 깊이 20 이
필요한지 안 재봤다. 기하로는 첫 벽 닿는 깊이가 (셀/2)/tan(입사각) 이라 각도가
커질수록 얕아도 된다. 재서 확인한다.

셀 10 mm 고정(결론 설계), 전부 무소, 판 500, 바닥판 없음. 깊이만 바꾼다.
규약 상수는 안 건드린다. 총량은 hemi_view 그대로, 빛줄기 FM.RHO_SAMPLES.
결과: results/depth_vs_angle_2026_09_18.json
"""
import os
import sys
import json
import time

ROOT = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sim_server as SS            # noqa: E402
import form_metrics as FM          # noqa: E402

OUT = os.path.join(ROOT, "results", "depth_vs_angle_2026_09_18.json")
M2 = "musou_fit2"
ALLM = dict(coating=M2, floor_coating=M2)

CELL = 10.0
DEPTHS = [20.0, 15.0, 10.0, 6.0, 4.0, 3.0, 2.0]
# 각도 목록의 집은 form_metrics 한 곳이다. 여기 손으로 적지 않는다.
GRAZE = tuple(t for t in FM.GRAZE_THETAS if t > 0)
THETAS = [int(t) for t in (0.0, 30.0, 40.0, 45.0) + GRAZE]
PHIS = list(FM.ROOM_TOTAL_PHIS)


def comb(pitch, depth, panel=500.0):
    return {"top": "comb", "top_params": {"pitch": pitch, "wall_top": 0.08,
            "wall_bot": 0.08, "comb_expand": 1.0, "jitter": 0.0},
            "depth": depth, "panel": panel, "floor": "none", "margin_depths": 0.2}


def main():
    state = json.load(open(OUT)) if os.path.exists(OUT) else {}
    state["what"] = ("셀 10 mm 벌집의 깊이를 바꿔 가며 스치는 각까지 잰 반사 총량. "
                     "규약 각도(0~45)는 그대로 두고 요청에만 각도를 더했다.")
    state["fixed"] = {"cell_mm": CELL, "panel_mm": 500.0, "coating": M2,
                      "floor_coating": M2, "wall_foil_mm": 0.08,
                      "samples": FM.RHO_SAMPLES}
    state["thetas"] = THETAS
    state["phis"] = PHIS
    rows = state.setdefault("rows", {})

    def save():
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)

    for d in DEPTHS:
        key = "깊이 %g" % d
        r = rows.setdefault(key, {"depth_mm": d})
        if "rho_planes" in r:
            continue
        spec = comb(CELL, d)
        t0 = time.time()
        planes = SS.measure(spec, list(THETAS), None, None, FM.RHO_SAMPLES,
                            phis=list(PHIS), **ALLM)
        r["spec"] = spec
        r["rho_planes"] = planes
        r["sec"] = round(time.time() - t0, 1)
        r["room_45max"] = max(pl["%.0f" % t] for pl in planes.values()
                              for t in (30, 40, 45))
        r["graze_max"] = max(pl["%.0f" % t] for pl in planes.values()
                             for t in GRAZE)
        save()
        print("[깊이 %5.1f] 방 조건 %.4f %%   스침 %.4f %%   (%.0fs)"
              % (d, 100 * r["room_45max"], 100 * r["graze_max"], r["sec"]), flush=True)

    save()
    print(OUT)
    print("@@DONE@@", flush=True)


main()
