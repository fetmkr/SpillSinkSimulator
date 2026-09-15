# -*- coding: utf-8 -*-
"""기준 시료 하나로, 고치기 전과 뒤의 세 축을 같은 프레임 조건에서 잰다.

    zsh scripts/run_batch.sh scripts/gate_reference_before_after.py refba

**실제 렌더다.** 합성 반례(`gate_form_stats.py`)가 "통계가 뜻대로 움직인다" 를
보였다면, 이건 "그래서 실제 숫자가 얼마나 움직였나" 를 본다.

시료: 발주 사양 4/22 (`results/pyramid_height/height_totals.json` 의 그 행).
피라미드 밑변 4, 높이 22, 끝 평평 0.4, 판 116 mm, 팁에서 20 mm 무소, 그 아래
5 % 페인트. 판 크기·도장 깊이는 사용자가 정한 값 그대로다.

세 설정. 한 번에 하나씩만 바꾼다.

    before     옛 코팅 트리 (fresnel_mix) + 옛 무소 (musou_fit)
    tree_only  새 코팅 트리 (reciprocal)  + 옛 무소          <- 트리만의 효과
    after      새 코팅 트리              + 새 무소 (musou_fit2) <- 재료의 효과

봉우리 통계는 설정마다 box / p99 / max 셋을 한 렌더에서 같이 읽고, 뭉개기는
새 판정과 옛 판정(처음 맞은 두 창)을 같은 사다리에서 같이 적는다. 그래서
통계 변경은 렌더를 더 안 하고 갈라 볼 수 있다.

    총량       hemi_view, 입사 0 / 40 도, 방위 0 / 45, 빛줄기 256
    뭉개기·반짝임  form, 빔 입사 -40/0/+40, 관찰자 0 도와 40 도, 위상 16,
               빛줄기 16 (규약값), 빔 7.5 mm, 0.215 mm/px, 방위 0
    잡음 대조   after, 관찰자 0 도를 빛줄기 256 으로 한 번 더:
               16 에서 읽은 box 봉우리가 잡음으로 부푼 만큼을 본다

결과: results/audit_2026_09_14/fix_reference_before_after.json
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS                                             # noqa: E402
import blender_render as BR                                         # noqa: E402
import form_metrics as FM                                           # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "audit_2026_09_14",
                   "fix_reference_before_after.json")
PUB = os.path.join(ROOT, "results", "pyramid_height", "height_totals.json")

ref = [r for r in json.load(open(PUB)) if r.get("label") == "발주 사양 4/22"][0]
SPEC = ref["spec"]
DEEP, SPRAY = ref["coating"]["deep_coating"], ref["coating"]["paint_depth"]
CONFIGS = (("before", "fresnel_mix", "musou_fit"),
           ("tree_only", "reciprocal", "musou_fit"),
           ("after", "reciprocal", "musou_fit2"))
TOTAL_SPP = 256


def form_row(f):
    p = (f.get("planes") or {}).get("0") or {}
    sv = p.get("smear_verdict") or {}
    fa = [((sv.get(k) or {}).get("first_agreement") or {}) for k in ("-40", "+40")]
    rc = [((sv.get(k) or {}).get("first_agreement") or {}).get("rms_control_mm")
          for k in ("-40", "+40")]
    old_smear = (0.5 * sum(x["rms_mm"] / x["rms_control_mm"] for x in fa)
                 if all(x.get("rms_mm") and x.get("rms_control_mm") for x in fa)
                 else None)
    return {"smear": f.get("smear"), "converged": f.get("converged"),
            "window_mm": f.get("window_mm"),
            "smear_first_agreement": old_smear,
            "first_agreement_reversed": [
                (sv.get(k) or {}).get("first_agreement_reversed")
                for k in ("-40", "+40")],
            "edge_moment": [(sv.get(k) or {}).get("edge_moment")
                            for k in ("-40", "+40")],
            "peak_by_stat": p.get("peak_by_stat"),
            "peak_by_theta": p.get("peak_by_theta"),
            "conditions": f.get("conditions"), "_unused": rc}


def main():
    t_all = time.time()
    res = {"spec": SPEC, "deep_coating": DEEP, "paint_depth": SPRAY,
           "published_totals_musou_fit": {"planes": ref.get("planes")},
           "configs": {}}
    try:
        for name, model, top in CONFIGS:
            BR.COATING_MODEL = model
            kw = dict(coating=top, deep_coating=DEEP, paint_depth=SPRAY)
            row = {"coating_model": model, "top": top}
            t0 = time.time()
            planes, cond = SS.measure(SPEC, [0.0, 40.0], None, None, TOTAL_SPP,
                                      phis=[0.0, 45.0], with_conditions=True,
                                      **kw)
            row["total"] = {"planes": planes, "conditions": cond,
                            "seconds": round(time.time() - t0, 1)}
            for obs in (0.0, 40.0):
                t0 = time.time()
                f = SS.form(SPEC, None, None, None, phis=[0.0],
                            obs_elev=obs, diffuse_frac=None, roughness=None,
                            **kw)
                row["form_obs%02d" % obs] = dict(form_row(f),
                                                 seconds=round(time.time() - t0, 1))
                print("[%s obs %2.0f] smear %.3f (old rule %s) conv %s  "
                      "peak box %s p99 %s max %s  (%.0fs)"
                      % (name, obs, f.get("smear") or float("nan"),
                         row["form_obs%02d" % obs]["smear_first_agreement"],
                         f.get("converged"),
                         *[(row["form_obs%02d" % obs]["peak_by_stat"] or {})
                           .get(s) for s in ("box", "p99", "max")],
                         time.time() - t0), flush=True)
            res["configs"][name] = row
            json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
            print("[%s] total phi0: %s  phi45: %s"
                  % (name, planes.get("0"), planes.get("45")), flush=True)

        BR.COATING_MODEL = "reciprocal"
        t0 = time.time()
        f = SS.form(SPEC, None, None, 256, phis=[0.0], obs_elev=0.0,
                    diffuse_frac=None, roughness=None, coating="musou_fit2",
                    deep_coating=DEEP, paint_depth=SPRAY)
        res["noise_after_obs00_256spp"] = dict(form_row(f),
                                               seconds=round(time.time() - t0, 1))
        print("[after 256spp obs 0] peak %s smear %s (%.0fs)"
              % (res["noise_after_obs00_256spp"]["peak_by_stat"],
                 f.get("smear"), time.time() - t0), flush=True)
    finally:
        BR.COATING_MODEL = "reciprocal"
    res["seconds"] = round(time.time() - t_all, 1)
    json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(OUT)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
