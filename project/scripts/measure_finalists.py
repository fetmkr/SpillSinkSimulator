# -*- coding: utf-8 -*-
"""마지막 후보들과 결론을 가른 도장 조합만, 지금 규약으로 세 축을 다시 잰다.

    zsh scripts/run_batch.sh scripts/measure_finalists.py finalists

왜 1,643 개 전부가 아니라 이것만인가 (2026-09-15, 사용자와 합의)
---------------------------------------------------------------
큰 순위를 다시 세우려는 것이 아니라, **마지막 후보들 사이의 순서가 뒤집히는지**를
보려는 것이다. 뒤집히면 그 계열만 넓힌다. `recompute_published.py` 는 12 개에서
멈춰 두었고, 결과 파일에서 이어 돌릴 수 있다.

바뀐 규약 (감사 조치 전부 반영)
    코팅 트리 reciprocal / 기본 무소 musou_fit2 / 봉우리 box 2 mm / 빔 자리 sobol
    빛줄기 256 (gate_sample_budget v2 가 box 에 요구한 값) / 위상 16 / 빔 7.5 mm
    0.215 mm/px / 뭉개기는 가장 넓은 창 판정 / 대조판은 필드 밖

각도 (방 조건: 천장 패널, 빔 30~45 도, 관객 0~60 도)
    총량   hemi_view 0, 20, 30, 40, 45, -20, -40 도 x 방위 0, 45
    형태   빔 -40, 0, 30, 40 도 x 관찰자 0, 20, 40, 60 도, 방위 0
           뭉개기 대표값은 옛 정의와 같은 +-40 평균. 각도별 값도 다 적는다.

후보
    발주 사양 피라미드 4/22 끝 0.4, 판 116   무소 팁 20 mm + 5 %  /  전부 5 %
    표준 샘플 피라미드 4/20 끝 0.1, 판 60    무소 전부              (목표 0.040 의 시료)
    벌집 9.53 / 깊이 40, 판 200              전부 5 %  /  무소 팁 20 + 5 %
                                             / 무소 팁 20 + 바닥판 무소
                                             / 테두리 0.03 + 피라미드 바닥 15, 무소 팁 20 + 바닥 무소
    피라미드 밑변 50 / 높이 250 끝 1, 판 500  무소 팁 20 + 5 %
    뒤집힌 피라미드 끝 0.4                   results/comb_depth/pyramid_inverted.json 의 형상, 무소 팁 20 + 5 %
    발표 설계 (파라미터는 발표 행 그대로, 무소 전부)
        날 0.05 + 피라미드 바닥 3 (★ 3 축 최고로 적힌 것) / 벌집 6.5/0.08 + 피라미드 바닥
        / 원뿔 위 벌집 (정면 최고) / 원뿔 5.5 / V 홈 13 mm

이어서 돌 수 있다. 끝난 (후보, 조합) 은 건너뛴다.
결과: results/finalists_2026_09_15.json (새 폴더 안 만든다)
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS             # noqa: E402
import form_buildable as FB         # noqa: E402
import blender_render as BR         # noqa: E402
import form_metrics as FM           # noqa: E402
import recompute_published as RP    # noqa: E402
from cone3d_sweep import COAT       # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "finalists_2026_09_15.json")
TMP = "/tmp/simsrv/finalists"
# 방 조건 각도와 총량 빛줄기는 form_metrics 한 곳에서 읽는다. 시뮬레이터 화면도
# 같은 목록을 읽으므로, 사용자가 화면에서 같은 값을 다시 낼 수 있다.
TOTAL_THETAS = list(FM.ROOM_TOTAL_THETAS)
TOTAL_PHIS = list(FM.ROOM_TOTAL_PHIS)
FORM_THETAS = tuple(FM.FORM_THETAS)
OBS = tuple(FM.ROOM_OBSERVERS)
TOTAL_SPP = FM.RHO_SAMPLES

M2, P5 = "musou_fit2", "wall_5pct"
# THE FINISH EXACTLY AS THE SIMULATOR SENDS IT (2026-09-15). The screen always
# sends a floor finish: "same as base" goes out as the base material's id
# (index.html FLOORMAT). The first eight rows here left the floor slot empty, so
# the server painted the backing through the depth split instead -- the same
# material by a different route, and not the same request the user will make.
# `gate_finalists_ui_path.py` found it. A stored row whose finish differs from
# these is kept under `superseded` and measured again.
MUSOU20 = dict(coating=M2, deep_coating=P5, paint_depth=20.0, floor_coating=P5)
ALL5 = dict(coating=P5, floor_coating=P5)
ALLM = dict(coating=M2, floor_coating=M2)


def pyr(pitch, depth, tip, panel):
    return {"top": "pyramid",
            "top_params": {"pitch": pitch, "tip_flat": tip, "apex_jitter": 0.0,
                           "tip_drop": 0.0},
            "depth": depth, "panel": panel, "floor": "none",
            "margin_depths": 0.2}


def comb(wall_top=0.08, floor=None, floor_depth=None):
    s = {"top": "comb",
         "top_params": {"pitch": 9.53, "wall_top": wall_top, "wall_bot": 0.08,
                        "comb_expand": 1.0, "jitter": 0.0},
         "depth": 40.0, "panel": 200.0, "floor": floor or "none",
         "margin_depths": 0.2}
    if floor:
        s["floor_depth"] = floor_depth
        s["floor_params"] = {"pitch": 9.53}
    return s


def inverted_spec():
    rows = json.load(open(os.path.join(ROOT, "results", "comb_depth",
                                       "pyramid_inverted.json")))
    return [r for r in rows if r["name"].startswith("뒤집힌 피라미드 끝0.4")][0]["spec"]


UI_CASES = [
    ("발주 피라미드 4/22 끝0.4", pyr(4.0, 22.0, 0.4, 116.0),
     [("무소 팁 20 + 5 %", MUSOU20), ("전부 5 %", ALL5)]),
    ("표준 샘플 피라미드 4/20 끝0.1", pyr(4.0, 20.0, 0.1, 60.0),
     [("무소 전부", ALLM)]),
    ("벌집 9.53/40", comb(),
     [("전부 5 %", ALL5), ("무소 팁 20 + 5 %", MUSOU20),
      ("무소 팁 20 + 바닥판 무소", dict(MUSOU20, floor_coating=M2))]),
    ("벌집 9.53/40 테두리 0.03 + 피라미드 바닥 15",
     comb(wall_top=0.03, floor="pyramid", floor_depth=15.0),
     [("무소 팁 20 + 바닥 무소", dict(MUSOU20, floor_coating=M2))]),
    ("뒤집힌 피라미드 끝0.4", None, [("무소 팁 20 + 5 %", MUSOU20)]),
    ("피라미드 밑변 50/높이 250 끝1", pyr(50.0, 250.0, 1.0, 500.0),
     [("무소 팁 20 + 5 %", MUSOU20)]),
]
# 기준 줄 (2026-09-16, 사용자 요청 "보고서에 민판 줄 추가해"). 순위에 넣지 않는다.
# 14 개 후보와 같은 측정 호출로 잰다. 판 200 은 벌집과 같은 크기, 깊이 10 은 화면
# 기본값 (NORMAL["none"]). 민판은 판 크기·깊이에 값이 안 흔들린다 [추측].
# 결과는 rows 가 아니라 reference 에 적는다. rows 를 늘리면 화면 요청 검사
# (14/14) 와 보고서 순위가 같이 바뀐다.
REF_CASES = [
    ("민판", {"top": "none", "top_params": {}, "depth": 10.0, "panel": 200.0,
             "floor": "none", "margin_depths": 0.2},
     [("무소 전부", ALLM), ("전부 5 %", ALL5)]),   # 5 % 는 2026-09-17 추가
]
PUB_CASES = [
    ("날 0.05 + 피라미드 바닥 3 (★)", "FL_bl050o115_pyramid_d30"),
    ("벌집 6.5/0.08 + 피라미드 바닥 3", "FL_p650f080_pyramid_d30"),
    ("원뿔 위 벌집 (정면 최고)", "ST_cone-comb_50"),
    ("원뿔 5.5", "B_CONE_p0550"),
    ("V 홈 13 mm (압출 최고)", "P1_groove_p13_t04"),
]
# 발표 설계는 **시뮬레이터 화면이 불러오는 프리셋 그대로** 잰다 (2026-09-15).
# 첫 판은 발표 행의 파라미터로 form_buildable 을 직접 불렀는데, 그러면 사용자가
# 화면에서 프리셋을 골라 잰 값과 같은 길이 아니다. 요청 모양도 화면과 같게:
# 무소를 모든 면에 칠한 것은 화면에서 "칠 100 %, 바탕 무소, 바닥 = 바탕" 이고
# 그때 화면이 보내는 것이 coating = 무소, 바닥 = 무소다.
PUB_FINISH = dict(coating=M2, floor_coating=M2)


def form_summary(f):
    p = f["planes"]["0"]
    return {"smear_pm40": f.get("smear"), "converged_pm40": f.get("converged"),
            "window_mm": f.get("window_mm"),
            "window_needed_mm": f.get("window_needed_mm"),
            "smear_by_theta": p.get("smear_by_theta"),
            "converged_by_theta": p.get("converged_by_theta"),
            "peak_by_stat_by_theta": p.get("peak_by_stat_by_theta")}


def ui_run(spec, fin):
    t0 = time.time()
    planes, cond = SS.measure(spec, TOTAL_THETAS, None, None, TOTAL_SPP,
                              phis=TOTAL_PHIS, with_conditions=True, **fin)
    out = {"totals": planes, "total_conditions": cond,
           "worst_total": max(v for pl in planes.values() for v in pl.values()),
           "form": {}, "total_sec": round(time.time() - t0, 1)}
    for obs in OBS:
        t1 = time.time()
        f = SS.form(spec, list(FORM_THETAS), None, None,
                    phis=list(FM.FORM_PHIS),
                    obs_elev=obs, diffuse_frac=None, roughness=None, **fin)
        out["form"]["%g" % obs] = dict(form_summary(f),
                                       sec=round(time.time() - t1, 1))
        out["form_conditions"] = f.get("conditions")
        print("   관찰 %2.0f  뭉개기 %s (수렴 %s)  box %s  (%.0fs)"
              % (obs, f.get("smear"), f.get("converged"),
                 {k: (v or {}).get("box") for k, v in
                  (f["planes"]["0"].get("peak_by_stat_by_theta") or {}).items()},
                 time.time() - t1), flush=True)
    return out


def pub_run(params):
    fam, prm = RP.family_of(params)
    coat = SS._coat(SS.DEFAULT_COATING)
    out = {"family": fam, "coating": SS._finish_record(coat), "totals": {},
           "form": {}}
    t0 = time.time()
    for phi in TOTAL_PHIS:
        cfg = {"tag": "fin_t", "family": fam, "out_dir": TMP, "results_dir": TMP,
               "samples": TOTAL_SPP, "res_x": 480, "res_y": 220, "gpu": True,
               "spec_roughness": float(coat["roughness"]),
               "coating": {"body": coat["body"], "spec_scale": coat["spec_scale"],
                           "roughness": float(coat["roughness"])},
               "params": dict(prm), "phi_deg": phi,
               "renders": [{"mode": "hemi_view", "theta": t}
                           for t in TOTAL_THETAS]}
        cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
        cfg["material_mode"] = "coating"
        res = BR.run(cfg)
        out["totals"]["%g" % phi] = {"%.0f" % r["theta"]: r["panel"]["mean"]
                                     for r in res["modes"].values()}
    out["worst_total"] = max(v for pl in out["totals"].values()
                             for v in pl.values())
    out["total_sec"] = round(time.time() - t0, 1)
    pitch = (prm.get("pitch") or prm.get("pitch_mean")
             or (prm.get("top_params") or {}).get("pitch") or 6.5)
    old = (FB.THETAS, FB.OBS_ELEV)
    try:
        for obs in OBS:
            t1 = time.time()
            FB.THETAS = FORM_THETAS
            FB.OBS_ELEV = obs
            entry = {"tag": "fin_f", "family": fam, "topology": fam,
                     "process": "finalist", "params": dict(prm),
                     "pitch": float(pitch),
                     "coating": {"body": coat["body"],
                                 "spec_scale": coat["spec_scale"]},
                     "roughness": float(coat["roughness"])}
            rec = FB.run_case(entry)
            t = rec["thetas"]
            a, b = t.get("-40"), t.get("+40")
            out["form"]["%g" % obs] = {
                "smear_pm40": (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                                      + b["rms_mm"] / b["rms_control_mm"])
                               if a and b else None),
                "converged_pm40": bool(a and b and a["converged"]
                                       and b["converged"]),
                "smear_by_theta": {k: (v["rms_mm"] / v["rms_control_mm"]
                                       if v.get("rms_control_mm") else None)
                                   for k, v in t.items()},
                "converged_by_theta": {k: v.get("converged")
                                       for k, v in t.items()},
                "peak_by_stat_by_theta": {
                    k: {s: v.get("peak_ratio_%s_mean" % s)
                        for s in ("box", "p99", "max")} for k, v in t.items()},
                "face_mm": rec.get("face_h"),
                "sec": round(time.time() - t1, 1)}
            print("   관찰 %2.0f  뭉개기 %s  box %s  (%.0fs)"
                  % (obs, out["form"]["%g" % obs]["smear_pm40"],
                     {k: v["box"] for k, v in
                      out["form"]["%g" % obs]["peak_by_stat_by_theta"].items()},
                     time.time() - t1), flush=True)
    finally:
        FB.THETAS, FB.OBS_ELEV = old
    return out


def main():
    os.makedirs(TMP, exist_ok=True)
    state = {"meta": {}, "rows": {}}
    if os.path.exists(OUT):
        state = json.load(open(OUT))
    state["meta"] = {
        "date": "2026-09-15", "coating_model": BR.COATING_MODEL,
        "default_coating": SS.DEFAULT_COATING,
        "total_thetas": TOTAL_THETAS, "total_phis": TOTAL_PHIS,
        "total_samples": TOTAL_SPP, "form_thetas": list(FORM_THETAS),
        "observers": list(OBS), "form_samples": FM.SAMPLES,
        "n_phase": FM.N_PHASE, "beam_w": FM.STRIPE_W,
        "mm_per_px": FM.MM_PER_PX, "peak_stat": FM.PEAK_STAT,
        "peak_box_mm": FM.PEAK_BOX_MM, "beam_pos": FM.BEAM_POS}
    presets = {p["design"]: p for p in SS.presets()}

    def save():
        json.dump(state, open(OUT, "w"), indent=1, ensure_ascii=False)

    t_all = time.time()
    state.setdefault("superseded", {})

    def current(key, spec, fin):
        """True if the stored row was measured with this spec and finish."""
        old = state["rows"].get(key)
        if not old or "error" in old:
            return False
        same = (json.dumps(old.get("finish"), sort_keys=True)
                == json.dumps(fin, sort_keys=True)
                and json.dumps(old.get("spec"), sort_keys=True)
                == json.dumps(spec, sort_keys=True))
        if not same:
            state["superseded"]["%s @ %s" % (key, old.get("measured_at", "before"))] = old
            del state["rows"][key]
            save()
            print("[finalist re-measure] %s -- stored finish/spec differs from "
                  "what the simulator sends; old row kept under superseded" % key,
                  flush=True)
        return same

    for name, spec, combos in UI_CASES:
        if spec is None:
            spec = inverted_spec()
        for cname, fin in combos:
            key = "%s | %s" % (name, cname)
            if current(key, spec, fin):
                continue
            print("\n[finalist] %s" % key, flush=True)
            row = {"case": name, "combo": cname, "spec": spec, "finish": fin,
                   "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            try:
                row.update(ui_run(spec, fin))
            except Exception as exc:
                import traceback
                traceback.print_exc()
                row["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
            state["rows"][key] = row
            save()
            print("[finalist done] %s  worst total %s" % (key, row.get("worst_total")),
                  flush=True)
    for name, design in PUB_CASES:
        key = "%s | 무소 전부" % name
        e = presets.get(design)
        spec = dict(e["spec"], panel=e["spec"].get("face", 60)) if e else None
        if current(key, spec, PUB_FINISH):
            continue
        print("\n[finalist] %s" % key, flush=True)
        row = {"case": name, "combo": "무소 전부", "design": design,
               "source": e and e["source"], "spec": spec, "finish": PUB_FINISH,
               "old_worst_rho": e and e.get("worst_rho"),
               "path": "simulator preset + UI-shaped request",
               "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        try:
            if e is None:
                raise KeyError("design %s not in presets()" % design)
            row.update(ui_run(spec, PUB_FINISH))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            row["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
        state["rows"][key] = row
        save()
        print("[finalist done] %s  worst total %s" % (key, row.get("worst_total")),
              flush=True)
    ref = state.setdefault("reference", {})
    for name, spec, combos in REF_CASES:
        for cname, fin in combos:
            key = "%s | %s" % (name, cname)
            old = ref.get(key)
            if (old and "error" not in old
                    and old.get("spec") == spec and old.get("finish") == fin):
                continue
            print("\n[reference] %s" % key, flush=True)
            row = {"case": name, "combo": cname, "spec": spec, "finish": fin,
                   "measured_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            try:
                row.update(ui_run(spec, fin))
            except Exception as exc:
                import traceback
                traceback.print_exc()
                row["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])
            ref[key] = row
            save()
            print("[reference done] %s  worst total %s"
                  % (key, row.get("worst_total")), flush=True)
    state["seconds_last_run"] = round(time.time() - t_all, 1)
    save()
    print(OUT)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
