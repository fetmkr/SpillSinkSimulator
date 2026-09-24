# -*- coding: utf-8 -*-
"""스치는 각도까지 (±55~75 도) 잰 반사 총량. 다섯 설계.

    zsh scripts/run_batch.sh scripts/grazing_2026_09_18.py grazing

천장이 3.5 m 라 빔이 천장에 맞는 각이 45~78 도다. 규약 각도(0~45)는 그대로 두고
요청에만 각도를 더한다. 화면의 "스치는 각도까지 재기" 칸과 같은 목록이다.

2026-09-18 두 번째 판: 처음에는 55·65·75 셋만 쟀다. 근거 없는 선택이었고
사용자가 "70 도가 왜 빠졌냐" 로 잡았다. 5 도 간격(55·60·65·70·75)으로 다시 잰다.
결과: results/grazing_2026_09_18.json
"""
import os
import sys
import json
import time

ROOT = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sim_server as SS            # noqa: E402
import form_metrics as FM          # noqa: E402

OUT = os.path.join(ROOT, "results", "grazing_2026_09_18.json")
M2, P5 = "musou_fit2", "wall_5pct"
ALLM = dict(coating=M2, floor_coating=M2)

# 각도 목록의 집은 form_metrics 한 곳이다. 여기 손으로 적지 않는다.
GRAZE = tuple(FM.GRAZE_THETAS)
THETAS = [int(t) for t in tuple(FM.ROOM_TOTAL_THETAS) + GRAZE]
PHIS = list(FM.ROOM_TOTAL_PHIS)


def flat(panel=200.0):
    return {"top": "none", "top_params": {}, "depth": 10.0, "panel": panel,
            "floor": "none", "margin_depths": 0.2}


def comb(pitch, depth, panel):
    return {"top": "comb", "top_params": {"pitch": pitch, "wall_top": 0.08,
            "wall_bot": 0.08, "comb_expand": 1.0, "jitter": 0.0},
            "depth": depth, "panel": panel, "floor": "none", "margin_depths": 0.2}


def pyr(pitch, depth, tip, panel):
    return {"top": "pyramid", "top_params": {"pitch": pitch, "tip_flat": tip,
            "apex_jitter": 0.0, "tip_drop": 0.0}, "depth": depth, "panel": panel,
            "floor": "none", "margin_depths": 0.2}


CASES = [
    ("무소 민판 판 200", flat(), ALLM),
    ("5 % 민판 판 200", flat(), dict(coating=P5, floor_coating=P5)),
    ("벌집 셀 10 / 깊이 20 / 판 500 (결론)", comb(10, 20, 500), ALLM),
    ("벌집 셀 20 / 깊이 20 / 판 500", comb(20, 20, 500), ALLM),
    ("발주 피라미드 4/22 끝 0.4 판 116", pyr(4, 22, 0.4, 116),
     dict(coating=M2, deep_coating=P5, paint_depth=20.0, floor_coating=P5)),
]


def main():
    state = json.load(open(OUT)) if os.path.exists(OUT) else {}
    state["what"] = ("스치는 각도까지 (±55·60·65·70·75 도) 잰 반사 총량. "
                     "규약 각도(0~45)는 그대로 두고 요청에만 각도를 더했다.")
    state["thetas"] = THETAS
    state["phis"] = PHIS
    state["samples"] = FM.RHO_SAMPLES
    rows = state.setdefault("rows", {})

    def save():
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)

    for name, spec, fin in CASES:
        r = rows.setdefault(name, {})
        if r.get("thetas_done") == THETAS:
            continue
        t0 = time.time()
        planes = SS.measure(spec, list(THETAS), None, None, FM.RHO_SAMPLES,
                            phis=list(PHIS), **ALLM if fin is ALLM else fin)
        r.update({"spec": spec, "finish": fin, "sec": round(time.time() - t0, 1),
                  "rho_planes": planes, "thetas_done": THETAS})
        r["room_45max"] = max(pl["%.0f" % t] for pl in planes.values()
                              for t in FM.RANK_TOTAL_THETAS)
        r["graze_max"] = max(pl["%.0f" % t] for pl in planes.values() for t in GRAZE)
        save()
        print("[%s] 방 조건 %.4f %%   스침 %.4f %%   (%.0fs)"
              % (name, 100 * r["room_45max"], 100 * r["graze_max"], r["sec"]), flush=True)

    save()
    print(OUT)
    print("@@DONE@@", flush=True)


main()
