# -*- coding: utf-8 -*-
"""포일을 얇게 하면 얼마나 좋아지나. 셀 9.53 / 깊이 40.

왜 이걸 재나. 바닥판까지 칠하고 나면 정면으로 되돌아오는 빛에서 남는 것이
거의 **포일 테두리** 뿐이다. 테두리 넓이는 `3t/간격` 이라 포일 두께에
그대로 비례한다. 깊이를 40 에서 60 으로 늘려도 1.27 배밖에 안 좋아지는데,
포일을 0.08 에서 0.04 로 줄이면 테두리가 반이 된다. 지금 남은 지렛대 중
제일 큰 것일 수 있다.

    깊이 40 -> 60   0.03949 % -> 0.03100 %   1.27 배   판이 1.5 배 두꺼워진다
    포일 0.08 -> ?  여기서 잰다                       두께는 그대로다

Huarui 는 포일 0.04~0.1 mm 라고 적어 놓았다. 다만 그 표는 얕은 조명용
그리드 기준이고, 깊이 40 mm 에서 0.04 mm 가 서는지는 우리가 확인 못 했다.
광학적으로 얼마나 이득인지만 여기서 정하고, 서는지는 업체에 묻는다.

세 축 중 총량과 반짝임을 잰다. 뭉개기는 모양이 정하는 값이고 포일 두께는
모양을 거의 안 바꾸므로(넓이 2.5 % 대 1.3 %) 추천 조합에서만 잰다.

    zsh scripts/run_batch.sh scripts/sweep_comb_foil.py foilpick
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
PATH = os.path.join(OUT, "comb_foil.json")

PITCH, DEPTH = 9.53, 40.0
BASE, TOP = "wall_5pct", "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
SPRAY = 15.0
FOILS = [0.03, 0.04, 0.05, 0.06, 0.08, 0.10]


def spec(foil, panel=None):
    return {"top": "comb",
            "top_params": {"pitch": PITCH, "wall_top": foil, "wall_bot": foil,
                           "comb_expand": 1.0, "jitter": 0.0},
            "depth": DEPTH, "panel": panel or 200.0, "floor": "none",
            "margin_depths": 0.2}


def arms(kind):
    if kind == "A":
        return dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)
    return dict(coating=TOP)


rows = []
print("셀 %.2f / 깊이 %.0f. 포일만 바꾼다. "
      "A = 바닥판 못 칠함, B = 바닥판까지 칠함.\n" % (PITCH, DEPTH), flush=True)
print("%-6s %-3s | %10s %10s %10s | %8s | %8s | %5s"
      % ("포일", "칠", "총량 정면", "총량 20도", "총량 40도", "반짝임",
         "테두리비", "초"), flush=True)

for foil in FOILS:
    for kind in ("A", "B"):
        t0 = time.time()
        kw = arms(kind)
        planes = SS.measure(spec(foil), THETAS, None, SLIDER, SAMPLES,
                            phis=PHIS, **kw)
        tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
        f = SS.form(spec(foil, panel=PITCH * 10.0), thetas=[0.0], n_phase=6,
                    samples=SAMPLES, beam_w=7.5, diffuse_frac=None,
                    roughness=SLIDER, **kw)
        pk = f.get("peak")
        if pk is None or tot.get("0") is None:
            raise SystemExit("빈 칸 (포일 %.2f %s) -- 인정 안 함" % (foil, kind))
        rim = 3.0 * foil / PITCH
        rows.append({"pitch": PITCH, "depth": DEPTH, "foil": foil,
                     "arm": kind, "spray_mm": SPRAY if kind == "A" else DEPTH,
                     "base": BASE, "top": TOP, "alpha": 0.039,
                     "slider": SLIDER, "samples": SAMPLES,
                     "total": tot, "planes": planes, "head_on": pk,
                     "rim_fraction": rim, "sec": round(time.time() - t0, 1)})
        json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
        print("%-6.2f %-3s | %9.5f%% %9.5f%% %9.5f%% | %8.4f | %7.2f%% | %5.0f"
              % (foil, kind, 100 * tot["0"], 100 * tot["20"], 100 * tot["40"],
                 pk, 100 * rim, rows[-1]["sec"]), flush=True)

# 테두리가 정말 남은 몫의 주인인지. 포일을 절반으로 하면 정면도 그만큼 줄까.
by = {(r["foil"], r["arm"]): r for r in rows}
print("\n포일을 절반으로 하면 정면이 얼마나 주나 (바닥판까지 칠한 경우)",
      flush=True)
for a, b in ((0.08, 0.04), (0.10, 0.05), (0.06, 0.03)):
    ra, rb = by[(a, "B")], by[(b, "B")]
    print("  %.2f -> %.2f : %.5f %% -> %.5f %%  (%.2f 배)"
          % (a, b, 100 * ra["total"]["0"], 100 * rb["total"]["0"],
             ra["total"]["0"] / rb["total"]["0"]), flush=True)

# 추천할 조합은 세 축이 다 차 있어야 한다. 총량만 보고 고르면 나머지 두 축의
# 문제를 숨기게 된다 -- 이 프로젝트에서 실제로 그랬다.
SMEAR_FOILS = [0.04, 0.08]
print("\n모양 뭉개기 -- 바닥판까지 칠한 경우 (한 점에 5 분)\n", flush=True)
print("%-6s | %8s | %6s | %5s" % ("포일", "뭉개기", "담겼나", "초"), flush=True)
for foil in SMEAR_FOILS:
    t0 = time.time()
    fm = SS.form(spec(foil), thetas=[-40.0, 40.0], n_phase=6, samples=SAMPLES,
                 phis=PHIS, **arms("B"))
    r = by[(foil, "B")]
    r["smear"] = fm.get("smear")
    r["smear_converged"] = fm.get("converged")
    r["smear_n_phase"] = 6
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-6.2f | %8s | %6s | %5.0f"
          % (foil, ("%.4f" % r["smear"]) if r["smear"] is not None else "-",
             r["smear_converged"], time.time() - t0), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
