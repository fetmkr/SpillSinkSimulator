# -*- coding: utf-8 -*-
"""빛줄기를 몇 개 쏴야 하나. 실제 측정 경로로, 2026-09-15 판.

    zsh scripts/run_batch.sh scripts/gate_sample_budget.py samplegate

옛 판이 틀렸던 것 (2026-09-14 감사 7 절, 코드로 확인)
------------------------------------------------------
  1  빛 퍼짐 SPREAD 1.0 도. 실제 측정은 form_metrics.SPREAD_DEG 0.05 도.
  2  코팅 상수를 cfg 맨 위에 넣었는데 build_scene 은 cfg["coating"] 에서 읽는다.
     그래서 옛 무소 상수(확산 0.76 시절)로 렌더했다.
  3  두 번 잰다면서 씨앗이 같았다. "렌더러 흔들림" 칸이 구조상 0 이었다.
  4  빔 자리 하나, 봉우리는 max / p99 뿐.
그 결과(results/comb20/sample_budget.json)는 지우지 않고 둔다. 16 의 근거로는
쓰지 않는다.

이번 판
------
장면을 따로 짓지 않는다. `sim_server.form` 을 그대로 부른다 -- 화면과 배치가
재는 바로 그 길이다. 바꾸는 것은 빛줄기 수와 씨앗뿐이다.

    모양 셋 x (빔 각, 관찰자 각) 넷 = 열두 경우       (옛 판과 같은 경우)
    빛줄기 4 / 8 / 16 / 32 / 64 / 256
    씨앗 두 개 (1, 2): 같은 설정을 독립으로 두 번
    위상 16, 빔 자리 sobol, 빔 7.5 mm, 0.215 mm/px    (규약값)
    재료: 기본 무소(musou_fit2) 팁에서 20 mm, 그 아래 5 % 페인트
    읽는 것: 뭉개기, 봉우리 box / p99 / max, 수렴 여부

판정
----
빛줄기 256 의 두 씨앗 평균을 참값으로 둔다. 어떤 빛줄기 수가 **열두 경우 전부**
에서 (a) 참값과 1 % 안, (b) 두 씨앗 차이가 1 % 안이면 그 수로 충분하다.
뭉개기와 box 봉우리를 따로 판정한다. 1 % 는 옛 판과 같은 자다.
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np                  # noqa: E402
import sim_server as SS             # noqa: E402
import form_buildable as FB         # noqa: E402
import form_metrics as FM           # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb20")
PATH = os.path.join(OUT, "sample_budget_v2.json")

SHAPES = [
    ("민판 (평판)",
     {"top": "none", "top_params": {}, "depth": 10.0, "panel": 200.0,
      "floor": "none", "margin_depths": 0.2}),
    ("벌집 9.53 / 깊이 40",
     {"top": "comb",
      "top_params": {"pitch": 9.53, "wall_top": 0.08, "wall_bot": 0.08,
                     "comb_expand": 1.0, "jitter": 0.0},
      "depth": 40.0, "panel": 95.3, "floor": "none", "margin_depths": 0.2}),
    ("피라미드 밑변 50 / 높이 250",
     {"top": "pyramid",
      "top_params": {"pitch": 50.0, "tip_flat": 1.0, "apex_jitter": 0.0,
                     "tip_drop": 0.0},
      "depth": 250.0, "panel": 200.0, "floor": "none", "margin_depths": 0.2}),
]
ANGLES = [(40.0, 0.0), (40.0, 40.0), (40.0, 60.0), (30.0, 30.0)]
LADDER = [4, 8, 16, 32, 64, 256]
SEEDS = (1, 2)
TOL = 0.01
KW = dict(coating="musou_fit2", deep_coating="wall_5pct", paint_depth=20.0)
STATS = ("smear", "box", "p99", "max")


def one(spec, theta, obs, spp, seed):
    FB.CYCLES_SEED = seed
    try:
        f = SS.form(spec, thetas=[theta], samples=spp, phis=[0.0],
                    obs_elev=obs, diffuse_frac=None, roughness=None, **KW)
    finally:
        FB.CYCLES_SEED = None
    p = f["planes"]["0"]
    k = "%+.0f" % theta
    pk = (p.get("peak_by_stat_by_theta") or {}).get(k) or {}
    return {"smear": (p.get("smear_by_theta") or {}).get(k),
            "box": pk.get("box"), "p99": pk.get("p99"), "max": pk.get("max"),
            "converged": (p.get("converged_by_theta") or {}).get(k),
            "conditions": f.get("conditions")}


def main():
    rows = []
    if os.path.exists(PATH):
        rows = json.load(open(PATH)).get("rows", [])
    have = {(r["case"], r["spp"], r["seed"]) for r in rows}
    t_all = time.time()
    for nm, spec in SHAPES:
        for theta, obs in ANGLES:
            case = "%s · 빔 %+.0f · 관찰 %.0f" % (nm, theta, obs)
            print("\n== %s" % case, flush=True)
            for spp in LADDER:
                for seed in SEEDS:
                    if (case, spp, seed) in have:
                        continue
                    t0 = time.time()
                    r = dict(one(spec, theta, obs, spp, seed), case=case,
                             spp=spp, seed=seed, sec=round(time.time() - t0, 1))
                    rows.append(r)
                    json.dump({"rows": rows}, open(PATH, "w"), indent=1,
                              ensure_ascii=False)
                    print("   빛줄기 %3d 씨앗 %d  뭉개기 %s  box %s  p99 %s  "
                          "max %s  (%.0fs)"
                          % (spp, seed, r["smear"], r["box"], r["p99"],
                             r["max"], r["sec"]), flush=True)

    # verdict
    cases = sorted({r["case"] for r in rows})
    table = {}
    for case in cases:
        mine = [r for r in rows if r["case"] == case]
        ref = {s: np.mean([r[s] for r in mine if r["spp"] == LADDER[-1]
                           and r[s] is not None] or [np.nan]) for s in STATS}
        table[case] = {}
        for spp in LADDER:
            rr = [r for r in mine if r["spp"] == spp]
            cell = {}
            for s in STATS:
                v = [r[s] for r in rr if r[s] is not None]
                if len(v) < 2 or not ref[s] or ref[s] != ref[s]:
                    cell[s] = None
                    continue
                cell[s] = {"bias": float(np.mean(v) / ref[s] - 1.0),
                           "seed_spread": float(abs(v[1] - v[0])
                                                / max(abs(np.mean(v)), 1e-30))}
            table[case][spp] = cell
    enough = {}
    for s in STATS:
        enough[s] = None
        for spp in LADDER:
            ok = all(table[c][spp].get(s) is not None
                     and abs(table[c][spp][s]["bias"]) <= TOL
                     and table[c][spp][s]["seed_spread"] <= TOL
                     for c in cases)
            if ok:
                enough[s] = spp
                break
    out = {"rows": rows, "table": table, "enough": enough, "tol": TOL,
           "protocol_samples": FM.SAMPLES, "seconds": round(time.time() - t_all)}
    json.dump(out, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("\n충분한 빛줄기 수 (열두 경우 전부, 참값과 %.0f %% · 씨앗 차 %.0f %% 안): %s"
          % (100 * TOL, 100 * TOL, enough), flush=True)
    print("지금 규약값 SAMPLES = %d" % FM.SAMPLES, flush=True)
    for case in cases:
        print("  %s" % case, flush=True)
        for spp in LADDER:
            c = table[case][spp]
            print("    %3d  " % spp + "  ".join(
                "%s %s" % (s, ("bias %+.2f%% seeds %.2f%%" % (100 * c[s]["bias"],
                                                             100 * c[s]["seed_spread"]))
                           if c[s] else "—") for s in ("smear", "box")),
                  flush=True)
    print(PATH, flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
