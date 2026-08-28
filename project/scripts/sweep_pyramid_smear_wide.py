# -*- coding: utf-8 -*-
"""피라미드 높이 250 의 뭉개기를 판이 모자라지 않게 다시 잰다.

`sweep_pyramid_height_form.py` 가 판 500 mm 로 쟀는데 되돌아온 빛을 담으려면
**창이 509 mm** 필요했다. `smear_converged` 가 False 로 나왔다. 그 19.65 는
실제 값이 아니라 **하한**이다. 보고서에도 그렇게 적혀 있다.

    높이 100 · 창 179 mm 필요 · 담김
    높이 175 · 창 344 mm 필요 · 담김
    높이 250 · 창 509 mm 필요 · **안 담김** (판 500)

판을 키운다. 값이 얼마나 올라가는지가 답이다.

비용
----
프레임 크기가 `(판 + 여백 + 측정창) / 0.215 mm` 다. 판 500 에서 뭉개기 한
점이 14.2 분이었다. 판을 600 으로 키우면 가로세로가 같이 커지므로 프레임
넓이가 대략 (600/500)² = 1.44 배, 20 분쯤으로 본다 [추측].

**두 판을 다 잰다.** 판 500 을 같이 재야 "판을 키워서 달라진 것" 이라고
말할 수 있다. 옛 값과 견주는 게 아니라 같은 실행 안에서 견준다.
[[isolate-one-variable-before-blaming-shape]] 와 같은 계열이다.

빔이 7.5 mm 인데 셀이 50 mm 라 위상 8 을 쓴다 (50/8 = 6.25 mm 걸음이라 빔이
서로 겹친다). 발표된 값들은 빔이 셀 두 개를 덮는 조건이었으므로 **나란히
놓으면 안 된다.** 원래 훑기와 같은 설정을 그대로 쓴다.

    zsh scripts/run_batch.sh scripts/sweep_pyramid_smear_wide.py pyrwide
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
PATH = os.path.join(OUT, "smear_wide.json")

PITCH, TIP, DEPTH = 50.0, 1.0, 250.0
BASE, TOP = "wall_5pct", "musou_fit"
SPRAY = 20.0
SLIDER, SAMPLES = 0.19748417658131498, 512
N_PHASE, BEAM = 8, 7.5
PANELS = [500.0, 600.0, 700.0]

KW = dict(coating=TOP, deep_coating=BASE, paint_depth=SPRAY)

rows = []
print("피라미드 밑변 %.0f · 높이 %.0f · 끝 %.1f · 무소 팁에서 %.0f mm · "
      "위상 %d · 빔 %.1f mm" % (PITCH, DEPTH, TIP, SPRAY, N_PHASE, BEAM),
      flush=True)
print("판 500 에서 창이 509 mm 필요해 안 담겼다. 판을 키워 다시 잰다.\n",
      flush=True)
print("%6s | %9s %9s | %9s %9s | %6s"
      % ("판", "뭉개기", "담겼나", "쓴 창", "필요 창", "분"), flush=True)

for panel in PANELS:
    sp = {"top": "pyramid",
          "top_params": {"pitch": PITCH, "tip_flat": TIP,
                         "apex_jitter": 0.0, "tip_drop": 0.0},
          "depth": DEPTH, "panel": panel, "floor": "none",
          "margin_depths": 0.2}
    t0 = time.time()
    f = SS.form(sp, thetas=[-40.0, 40.0], n_phase=N_PHASE, samples=SAMPLES,
                beam_w=BEAM, diffuse_frac=None, roughness=SLIDER,
                phis=[0.0], **KW)
    if f.get("smear") is None:
        raise SystemExit("빈 칸 (판 %.0f) -- 인정 안 함" % panel)
    rows.append({"panel": panel, "depth": DEPTH, "pitch": PITCH,
                 "tip_flat": TIP, "spray_mm": SPRAY, "n_phase": N_PHASE,
                 "beam_w": BEAM, "samples": SAMPLES, "slider": SLIDER,
                 "smear": f.get("smear"),
                 "smear_converged": f.get("converged"),
                 "window_mm": f.get("window_mm"),
                 "window_needed_mm": f.get("window_needed_mm"),
                 "mm_per_px": f.get("mm_per_px"),
                 "rms_by_theta": f.get("rms_by_theta"),
                 "coating": KW, "sec": round(time.time() - t0, 1)})
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%6.0f | %9.4f %9s | %9.0f %9.0f | %6.1f"
          % (panel, rows[-1]["smear"], rows[-1]["smear_converged"],
             rows[-1]["window_mm"] or 0, rows[-1]["window_needed_mm"] or 0,
             rows[-1]["sec"] / 60.0), flush=True)

    # 담겼으면 더 키울 이유가 없다. 프레임 값이 비싸다.
    if rows[-1]["smear_converged"]:
        print("  담겼다. 더 키우지 않는다.", flush=True)
        break

base = rows[0]
print("\n판 500 (안 담김) 을 1 로 놓으면", flush=True)
for r in rows[1:]:
    print("  판 %3.0f : 뭉개기 %.4f -> %.4f (%+.1f %%)"
          % (r["panel"], base["smear"], r["smear"],
             100 * (r["smear"] / base["smear"] - 1)), flush=True)

print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
