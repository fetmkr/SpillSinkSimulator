# -*- coding: utf-8 -*-
"""위상(phase) 수를 늘리면 값이 안 움직이나.

빔은 한 칸(unit cell) 안에서 여러 자리에 놓고 재서 평균을 낸다. 그 자리 수가
위상 수다. 자리가 모자라면 평균이 자리 뽑기에 휘둘린다.

2026-08-27 에 그게 실제로 일어난 것을 봤다. 관객 각도별 훑기를 위상 6 으로
돌렸는데, 기록된 흩어짐이 이렇다 (빔 40 도, 무소 팁 20 mm, 바탕 5 % 페인트):

    벌집 셀 9.53 / 깊이 40        관찰자 20~60 도   흔들림 0~3 %,  최대/최소 1.0~1.1 배
    피라미드 밑변 50 / 높이 100   관찰자  0 도      흔들림 89 %,   최대/최소 39 배
    피라미드 밑변 50 / 높이 250   관찰자 60 도      흔들림 46 %,   최대/최소 2853 배

**벌집은 안 흔들리고 피라미드는 심하게 흔들린다.** 빔 7.5 mm 가 셀 9.53 mm
안에서는 어디에 놓든 비슷한 것을 보는데, 밑변 50 mm 짜리 경사면 위에서는
놓는 자리마다 다른 것을 보기 때문이다 [추측 -- 흔들림은 잰 값이고, 이 설명은
아직 확인 안 했다].

이 검사가 지키는 것
------------------
**위상을 두 배로 늘려도 값이 안 움직여야 한다.** 움직이면 지금 위상 수로 낸
값은 그 자리 뽑기의 결과이지 판의 값이 아니다.

    A  벌집,   위상 6 대 12    -> 같아야 한다 (흩어짐이 없으니)
    B  피라미드, 위상 6 대 12   -> **여기서 떨어질 것으로 본다**
    C  피라미드, 위상 12 대 24  -> 어디서 멎는지 본다

RayFlare 문서는 한 칸 안을 50 x 50 = 2500 지점으로 훑고, "광선 수를 늘리는
것보다 지점 수를 늘리는 게 훨씬 효율적" 이라고 적는다. 우리는 6 이다.

합격선
------
**상대 2 %.** 뭉개기의 창 사다리가 두 칸이 2 % 안에서 같으면 멎었다고 보는데
(`form_buildable`), 같은 자를 쓴다. 렌더러 자체 흔들림 3.1e-08 보다 한참 위고
(`gate_observer_angle` 에 실측이 적혀 있다), 오늘 표에서 견주는 차이(벌집 대
피라미드 3.4 배) 보다는 한참 아래다.

이 검사기는 **지금 코드에서 떨어지는 것이 정상이다.** 통과하면 검사기가 틀린
것이다. 고치기 전에 떨어지는 것을 먼저 확인한다.

    zsh scripts/run_batch.sh scripts/gate_phase_convergence.py phasegate
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "comb20")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "phase_convergence.json")

BASE, TOP = "wall_5pct", "musou_fit"
SAMPLES = 256
SPRAY = 20.0
THETA = 40.0
TOL = 0.02
KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)

# 흔들림이 가장 컸던 자리와 가장 작았던 자리를 같이 본다. 하나만 보면
# 우연에 기댄다.
CASES = [
    ("벌집 9.53 / 깊이 40 · 관찰자 40",
     {"top": "comb",
      "top_params": {"pitch": 9.53, "wall_top": 0.08, "wall_bot": 0.08,
                     "comb_expand": 1.0, "jitter": 0.0},
      "depth": 40.0, "panel": 95.3, "floor": "none", "margin_depths": 0.2},
     40.0, [6, 12, 24]),
    ("피라미드 50/250 · 관찰자 40 (흔들림 1 %)",
     {"top": "pyramid",
      "top_params": {"pitch": 50.0, "tip_flat": 1.0, "apex_jitter": 0.0,
                     "tip_drop": 0.0},
      "depth": 250.0, "panel": 200.0, "floor": "none", "margin_depths": 0.2},
     40.0, [6, 12, 24]),
    ("피라미드 50/250 · 관찰자 60 (흔들림 46 %)",
     {"top": "pyramid",
      "top_params": {"pitch": 50.0, "tip_flat": 1.0, "apex_jitter": 0.0,
                     "tip_drop": 0.0},
      "depth": 250.0, "panel": 200.0, "floor": "none", "margin_depths": 0.2},
     60.0, [6, 12, 24]),
]

rows = []
FAILED = []
print("위상(phase) 수를 늘리면 값이 안 움직이나. 빔 %+.0f도 · 무소 팁 %.0f mm · "
      "바탕 5 %% 페인트 · 표본 %d" % (THETA, SPRAY, SAMPLES), flush=True)
print("합격선 상대 %.0f %%. **지금 코드에서 떨어지는 것이 정상이다.**\n"
      % (100 * TOL), flush=True)

for name, spec, obs, phases in CASES:
    print("== %s ==" % name, flush=True)
    print("%8s | %10s | %12s | %6s" % ("위상", "봉우리", "앞칸 대비", "분"),
          flush=True)
    prev = None
    for np_ in phases:
        t0 = time.time()
        r = SS.form(spec, thetas=[THETA], n_phase=np_, samples=SAMPLES,
                    phis=[0.0], obs_elev=obs, **KW)
        v = (r.get("peak_by_theta") or {}).get("%+.0f" % THETA)
        if v is None:
            raise SystemExit("빈 칸 (%s 위상 %d) -- 인정 안 함" % (name, np_))
        step = None if prev is None else (v / prev - 1.0)
        bad = step is not None and abs(step) > TOL
        if bad:
            FAILED.append("%s 위상 %d" % (name, np_))
        rows.append({"case": name, "obs_elev": obs, "theta": THETA,
                     "n_phase": np_, "peak": v, "step_vs_prev": step,
                     "spec": spec, "coating": KW, "samples": SAMPLES,
                     "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        print("%8d | %10.5f | %12s | %6.1f"
              % (np_, v, "-" if step is None else "%+.2f %%" % (100 * step),
                 rows[-1]["sec"] / 60.0), flush=True)
        prev = v
    print("", flush=True)

print("한 단계 더 늘려도 %.0f %% 안에서만 움직이는 첫 자리" % (100 * TOL),
      flush=True)
for name, _, _, _ in CASES:
    mine = [r for r in rows if r["case"] == name]
    hit = next((r for r in mine if r["step_vs_prev"] is not None
                and abs(r["step_vs_prev"]) <= TOL), None)
    print("  %-38s %s" % (name,
          ("위상 %d 부터" % hit["n_phase"]) if hit
          else "**아직 안 멎었다. 사다리를 더 늘려야 한다.**"), flush=True)

print("\n%d 항목 실패" % len(FAILED), flush=True)
if FAILED:
    print("실패: %s" % ", ".join(FAILED), flush=True)
    print("위상 6 으로 낸 값은 그 자리 뽑기의 결과다. 판의 값이 아니다.",
          flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
sys.exit(1 if FAILED else 0)
