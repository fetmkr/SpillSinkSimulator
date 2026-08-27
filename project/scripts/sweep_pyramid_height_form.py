# -*- coding: utf-8 -*-
"""피라미드 높이 -- 2단계, 모양 뭉개기와 정면 반짝임.

1단계(`sweep_pyramid_height.py`)가 총량으로 아홉 점을 훑었고 경향은 매끄러웠다
-- 25 mm 마다 10~17 % 씩 좋아지고 250 mm 에서도 안 꺾인다. 그래서 여기서는
양 끝과 가운데 셋만 잰다: **높이 100 / 175 / 250** (높이 대 밑변 2 / 3.5 / 5).

왜 셋뿐인가. 실측한 비용이 그렇다:

    반사 총량 한 각도      0.74 초
    뭉개기·반짝임 한 프레임  높이 100 에서 69 초, 높이 250 에서 **343 초**

프레임 크기가 `(판 + 여백 + 측정창) / 0.215 mm` 라서 깊이가 깊을수록 창이
커지고 프레임이 커진다. 높이 250 에서는 창이 1000 mm 다.

위상 수
------
빔이 7.5 mm 인데 셀이 50 mm 다. **지금까지 발표된 값은 빔이 셀 두 개를
덮는 조건(빔 7.5 / 밑변 4)에서 나왔다.** 여기서는 빔이 경사면 하나 안에
들어간다. 리그 감사 기록이 "빔이 셀보다 작으면 위상 수가 결과를 움직인다"
고 적는다.

위상 8 을 쓴다. 50 / 8 = 6.25 mm 걸음이라 7.5 mm 빔이 서로 겹친다.
위상 6 은 8.3 mm 걸음이라 빔 사이에 틈이 생긴다. 위상을 더 늘리면 좋지만
높이 250 에서 한 프레임이 343 초라 그만큼 그대로 시간이 된다.

**이 값들을 기존 발표 숫자와 나란히 놓으면 안 된다.** 빔 대 셀 조건이 다르다.

    zsh scripts/run_batch.sh scripts/sweep_pyramid_height_form.py pyrform
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "pyramid_height")
os.makedirs(OUT, exist_ok=True)
PATH = os.path.join(OUT, "height_form.json")

PITCH, PANEL, TIP = 50.0, 500.0, 1.0
BASE, TOP = "wall_5pct", "musou_fit"
SPRAY = 20.0
SLIDER, SAMPLES = 0.19748417658131498, 512
N_PHASE = 8
BEAM = 7.5
HEIGHTS = [100.0, 175.0, 250.0]


def spec(depth):
    return {"top": "pyramid",
            "top_params": {"pitch": PITCH, "tip_flat": TIP,
                           "apex_jitter": 0.0, "tip_drop": 0.0},
            "depth": depth, "panel": PANEL, "floor": "none",
            "margin_depths": 0.2}


KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)

rows = []
print("밑변 %.0f · 판 %.0f · 끝 %.1f · 무소 팁에서 %.0f mm · 위상 %d · 빔 %.1f mm"
      % (PITCH, PANEL, TIP, SPRAY, N_PHASE, BEAM), flush=True)
print("빔(%.1f) 이 셀(%.0f) 보다 작다 -- 발표된 값과 조건이 다르다.\n"
      % (BEAM, PITCH), flush=True)
print("%6s | %8s %8s | %8s %8s | %6s"
      % ("높이", "반짝임", "뭉개기", "담겼나", "필요 창", "초"), flush=True)

for h in HEIGHTS:
    r = {"depth": h, "pitch": PITCH, "tip_flat": TIP, "panel": PANEL,
         "aspect": h / PITCH, "spray_mm": SPRAY, "n_phase": N_PHASE,
         "beam_w": BEAM, "alpha": 0.039, "slider": SLIDER,
         "samples": SAMPLES, "coating": KW}

    # 반짝임: 정면 한 각도. 셀 열 개 조각이 곧 판 전체(500 mm)라 조각 요령이
    # 여기서는 아무것도 안 줄여 준다.
    t0 = time.time()
    f0 = SS.form(spec(h), thetas=[0.0], n_phase=N_PHASE, samples=SAMPLES,
                 beam_w=BEAM, diffuse_frac=None, roughness=SLIDER,
                 phis=[0.0], **KW)
    r["head_on"] = f0.get("peak")
    r["head_on_sec"] = round(time.time() - t0, 1)

    # 뭉개기: +-40 도
    t0 = time.time()
    f1 = SS.form(spec(h), thetas=[-40.0, 40.0], n_phase=N_PHASE,
                 samples=SAMPLES, beam_w=BEAM, diffuse_frac=None,
                 roughness=SLIDER, phis=[0.0], **KW)
    r["smear"] = f1.get("smear")
    r["smear_converged"] = f1.get("converged")
    r["window_mm"] = f1.get("window_mm")
    r["window_needed_mm"] = f1.get("window_needed_mm")
    r["mm_per_px"] = f1.get("mm_per_px")
    r["draft_density"] = f1.get("draft_density")
    r["smear_sec"] = round(time.time() - t0, 1)

    if r["head_on"] is None or r["smear"] is None:
        raise SystemExit("빈 칸 (높이 %.0f) -- 인정 안 함" % h)
    rows.append(r)
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%6.0f | %8.4f %8.4f | %8s %8.0f | %6.0f"
          % (h, r["head_on"], r["smear"], r["smear_converged"],
             r["window_needed_mm"] or 0, r["head_on_sec"] + r["smear_sec"]),
          flush=True)

print("\n담겼나(converged) 가 False 면 그 뭉개기는 실제 값이 아니라 **하한**이다.",
      flush=True)
print("필요 창이 판 %.0f mm 를 넘으면 되돌아온 빛이 판 밖으로 나간 것이다."
      % PANEL, flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
