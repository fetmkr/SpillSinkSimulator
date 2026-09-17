# -*- coding: utf-8 -*-
"""읽는 창 60 x 40 (지금 규약) 과 50 x 50 을 같은 프로세스에서 견준다.

    zsh scripts/run_batch.sh scripts/window_50x50.py window_50x50

사용자 질문 (2026-09-17): "50 대 50 으로 하면 안 되는건가? 해봐."
규약 상수(form_metrics.MEAS_INSET_X/Z)는 건드리지 않는다. 이 프로세스 안에서만
blender_render 의 두 값을 바꿔 잰다. 측정 호출은 measure_finalists.ui_run 과 같다
(sim_server.measure / sim_server.form, 방 조건 각도, 빛줄기 256).
결과: results/window_50x50_2026_09_17.json
"""
import os
import sys
import json
import time

ROOT = "/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sim_server as SS            # noqa: E402
import blender_render as BR        # noqa: E402
import form_metrics as FM          # noqa: E402

OUT = os.path.join(ROOT, "results", "window_50x50_2026_09_17.json")
WINDOWS = {"60x40": (0.20, 0.30), "50x50": (0.25, 0.25)}
M2, P5 = "musou_fit2", "wall_5pct"
ALLM = dict(coating=M2, floor_coating=M2)
MUSOU20 = dict(coating=M2, deep_coating=P5, paint_depth=20.0, floor_coating=P5)


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
    ("5 % 민판", flat(), dict(coating=P5, floor_coating=P5)),
    ("무소 민판", flat(), ALLM),
    ("벌집 셀 10 / 깊이 20 / 판 500 (결론)", comb(10.0, 20.0, 500.0), ALLM),
    ("벌집 9.53/40 판 200 무소 팁 20 + 바닥판 무소", comb(9.53, 40.0, 200.0),
     dict(MUSOU20, floor_coating=M2)),
    ("발주 피라미드 4/22 끝 0.4 판 116 무소 팁 20 + 5 %", pyr(4.0, 22.0, 0.4, 116.0), MUSOU20),
    ("표준 샘플 피라미드 4/20 끝 0.1 판 60 무소 전부", pyr(4.0, 20.0, 0.1, 60.0), ALLM),
]
# 반짝임은 오래 걸려서 짧은 것부터. 결론 벌집은 맨 뒤.
FORM_CASES = [5, 4, 2]
OBS = (20.0, 40.0, 60.0)


def set_window(k):
    BR.MEAS_INSET_X, BR.MEAS_INSET_Z = WINDOWS[k]


def main():
    state = json.load(open(OUT)) if os.path.exists(OUT) else {}
    state["meta"] = {"windows": {k: {"inset_x": v[0], "inset_z": v[1],
                                     "reads": "%.0f %% x %.0f %% of the face"
                                     % (100 * (1 - 2 * v[0]), 100 * (1 - 2 * v[1]))}
                                 for k, v in WINDOWS.items()},
                     "total_thetas": list(FM.ROOM_TOTAL_THETAS),
                     "total_phis": list(FM.ROOM_TOTAL_PHIS),
                     "rank_total_thetas": list(FM.RANK_TOTAL_THETAS),
                     "form_thetas": list(FM.FORM_THETAS), "observers": list(OBS),
                     "samples": FM.RHO_SAMPLES, "form_samples": FM.SAMPLES,
                     "n_phase": FM.N_PHASE, "beam_w": FM.STRIPE_W}
    rows = state.setdefault("rows", {})

    def save():
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)

    for name, spec, fin in CASES:
        for wk in WINDOWS:
            key = "%s | %s" % (name, wk)
            r = rows.setdefault(key, {"case": name, "window": wk, "spec": spec, "finish": fin})
            if "totals" in r:
                continue
            set_window(wk)
            t0 = time.time()
            planes = SS.measure(spec, list(FM.ROOM_TOTAL_THETAS), None, None,
                                FM.RHO_SAMPLES, phis=list(FM.ROOM_TOTAL_PHIS), **fin)
            r["totals"] = planes
            r["room_max"] = max(pl["%.0f" % t] for pl in planes.values()
                                for t in FM.RANK_TOTAL_THETAS)
            r["all_max"] = max(v for pl in planes.values() for v in pl.values())
            r["total_sec"] = round(time.time() - t0, 1)
            save()
            print("[total] %-50s %s  방 조건 %.5f %%  (%.0fs)"
                  % (name, wk, 100 * r["room_max"], r["total_sec"]), flush=True)

    for i in FORM_CASES:
        name, spec, fin = CASES[i]
        for obs in OBS:
            for wk in WINDOWS:
                key = "%s | %s" % (name, wk)
                r = rows[key]
                fo = r.setdefault("form", {})
                if "%g" % obs in fo:
                    continue
                set_window(wk)
                t0 = time.time()
                f = SS.form(spec, list(FM.FORM_THETAS), None, None,
                            phis=list(FM.FORM_PHIS), obs_elev=obs,
                            diffuse_frac=None, roughness=None, **fin)
                p0 = (f.get("planes") or {}).get("0") or {}
                fo["%g" % obs] = {
                    "smear": f.get("smear"), "converged": f.get("converged"),
                    "box": {k: (v or {}).get("box") for k, v in
                            (p0.get("peak_by_stat_by_theta") or {}).items()},
                    "sec": round(time.time() - t0, 1)}
                save()
                print("[form] %-50s %s 관객 %g  box %s  smear %s  (%.0fs)"
                      % (name, wk, obs, fo["%g" % obs]["box"], f.get("smear"),
                         time.time() - t0), flush=True)
    save()
    print(OUT)
    print("@@DONE@@", flush=True)


main()
