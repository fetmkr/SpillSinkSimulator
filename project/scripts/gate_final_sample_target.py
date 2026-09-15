# -*- coding: utf-8 -*-
"""목표 0.040 을 새 잣대로 다시 잰다. 같은 시료, 옛 조건과 새 조건.

    zsh scripts/run_batch.sh scripts/gate_final_sample_target.py target

목표 세 숫자(총량 0.177 %, 뭉개기 1.42, 정면 반짝임 0.040)는 한 시료에서 나왔다.
`results/FINDINGS_phase65_final_envelope.md`, `results/form_p4d20_beam.json`:

    피라미드 밑변 4 / 높이 20 / 끝 0.1, 판 60 mm (mm/px 0.160286 = 220 x 1.02 / 1400)
    빔 7 mm: 뭉개기 1.4170, 반짝임 0.040001     빔 10 mm: 1.0939, 0.040377
    총량: 방위 0 도 최악 0.17668 %, 방위 30 도 0.25109 %
    그때 조건: 옛 코팅 트리, 확산 0.76, 거칠기 0.30, 봉우리 = 최대값, 빔 자리 균등,
               고정 화소 1400 (mm/px 는 판을 따라감), 위상 16

**목표를 내가 정하지 않는다.** 이 검사는 "그 시료가 지금 잣대로 얼마인가" 를 잰다.
그 값을 목표로 받아들일지는 사람이 정한다.

단계
----
  R  옛 조건 재현. 먼저 옛 숫자가 나오는지 본다 -- 안 나오면 새 숫자를 목표 자리에
     놓을 근거가 없다 (검사기는 아는 답으로 먼저 검증한다). 빛 퍼짐은 그때 값이
     기록에 없어 0.05 와 1.0 둘 다 잰다. 빛줄기 512.
  T  새 트리만: reciprocal + 옛 재료, 나머지 옛 조건
  N  지금 규약 전부: reciprocal + musou_fit2, box 봉우리, sobol, 0.215 mm/px,
     빛줄기 16, 빔 7 / 7.5 / 10 mm. 판은 그때와 같은 60 mm.
  총량: R 과 N 을 입사 0, +-20, +-40 / 방위 0, 30 에서 (빛줄기 256)

결과: results/audit_2026_09_14/fix_final_sample_target.json
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

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "audit_2026_09_14",
                   "fix_final_sample_target.json")
SPEC = {"top": "pyramid",
        "top_params": {"pitch": 4.0, "tip_flat": 0.1, "apex_jitter": 0.0,
                       "tip_drop": 0.0},
        "depth": 20.0, "panel": 60.0, "floor": "none"}
PUBLISHED = {"B7": {"smear": 1.4169910167003033, "head_on": 0.040000739327958154},
             "B10": {"smear": 1.0938828538275263, "head_on": 0.040377163771855185},
             "total_phi0_worst": 0.0017668, "total_phi30_worst": 0.0025109}
THETAS_T = [0.0, -20.0, -40.0, 20.0, 40.0]

SAVE = ("MM_PER_PX", "PEAK_STAT", "BEAM_POS", "SPREAD_DEG", "SAMPLES")


def fb_state():
    return {k: getattr(FB, k) for k in SAVE}, BR.COATING_MODEL


def restore(st):
    for k, v in st[0].items():
        setattr(FB, k, v)
    BR.COATING_MODEL = st[1]


def form_run(beam, coating, df, rough):
    f = SS.form(SPEC, None, 16, FB.SAMPLES, beam_w=beam, phis=[0.0],
                diffuse_frac=df, roughness=rough, coating=coating)
    p = f["planes"]["0"]
    return {"smear": f.get("smear"), "smear_legacy": f.get("smear_legacy"),
            "converged": f.get("converged"), "window_mm": f.get("window_mm"),
            "head_on_by_stat": p.get("peak_by_stat"),
            "conditions": f.get("conditions")}


def total_run(coating, df, rough):
    planes, cond = SS.measure(SPEC, THETAS_T, df, rough, 256,
                              coating=coating, phis=[0.0, 30.0],
                              with_conditions=True)
    return {"planes": planes,
            "worst_phi0": max(planes["0"].values()),
            "worst_phi30": max(planes["30"].values()), "conditions": cond}


def main():
    res = {"spec": SPEC, "published": PUBLISHED, "runs": {}}
    base = fb_state()
    t_all = time.time()
    try:
        # R: the old conditions
        for spread in (0.05, 1.0):
            restore(base)
            BR.COATING_MODEL = "fresnel_mix"
            FB.MM_PER_PX = 0.0
            FB.PEAK_STAT = "max"
            FB.BEAM_POS = "uniform"
            FB.SPREAD_DEG = spread
            FB.SAMPLES = 512
            for beam in (7.0, 10.0):
                t0 = time.time()
                r = form_run(beam, "musou_fit", 0.76, 0.30)
                r["seconds"] = round(time.time() - t0, 1)
                res["runs"]["R_spread%g_beam%g" % (spread, beam)] = r
                pub = PUBLISHED["B7" if beam == 7.0 else "B10"]
                print("[R spread %.2f beam %2.0f] smear legacy %s (pub %.4f)  "
                      "head-on max %s (pub %.5f)  (%.0fs)"
                      % (spread, beam, r["smear_legacy"], pub["smear"],
                         (r["head_on_by_stat"] or {}).get("max"),
                         pub["head_on"], r["seconds"]), flush=True)
                json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
        restore(base)
        BR.COATING_MODEL = "fresnel_mix"
        res["runs"]["R_total"] = total_run("musou_fit", 0.76, 0.30)
        print("[R total] worst phi0 %.6f (pub %.6f)  phi30 %.6f (pub %.6f)"
              % (res["runs"]["R_total"]["worst_phi0"],
                 PUBLISHED["total_phi0_worst"],
                 res["runs"]["R_total"]["worst_phi30"],
                 PUBLISHED["total_phi30_worst"]), flush=True)

        # T: only the tree changes
        restore(base)
        BR.COATING_MODEL = "reciprocal"
        FB.MM_PER_PX = 0.0
        FB.PEAK_STAT = "max"
        FB.BEAM_POS = "uniform"
        FB.SAMPLES = 512
        res["runs"]["T_beam7"] = form_run(7.0, "musou_fit", 0.76, 0.30)
        print("[T beam 7] head-on max %s  smear legacy %s"
              % ((res["runs"]["T_beam7"]["head_on_by_stat"] or {}).get("max"),
                 res["runs"]["T_beam7"]["smear_legacy"]), flush=True)

        # N: today's protocol, today's Musou
        restore(base)
        BR.COATING_MODEL = "reciprocal"
        for beam in (7.0, 7.5, 10.0):
            t0 = time.time()
            r = form_run(beam, "musou_fit2", None, None)
            r["seconds"] = round(time.time() - t0, 1)
            res["runs"]["N_beam%g" % beam] = r
            print("[N beam %4.1f] smear %s conv %s  head-on %s  (%.0fs)"
                  % (beam, r["smear"], r["converged"], r["head_on_by_stat"],
                     r["seconds"]), flush=True)
            json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
        res["runs"]["N_total"] = total_run("musou_fit2", None, None)
        print("[N total] worst phi0 %.6f  phi30 %.6f"
              % (res["runs"]["N_total"]["worst_phi0"],
                 res["runs"]["N_total"]["worst_phi30"]), flush=True)
    finally:
        restore(base)
        BR.COATING_MODEL = "reciprocal"
    res["seconds"] = round(time.time() - t_all, 1)
    json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(OUT)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
