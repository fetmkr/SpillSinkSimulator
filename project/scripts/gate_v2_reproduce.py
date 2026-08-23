# -*- coding: utf-8 -*-
"""거칠기 규칙을 하나로 맞춘 뒤에도 2판 보고서 값이 그대로 나오나.

2026-08-23 에 `_coat(..., roughness=)` 를 만들어 규칙을 하나로 맞췄다.
그 전에는 윗면만 요청이 준 거칠기를 쓰고, 깊은 도장과 바닥은 재료 파일의
값을 썼다. 한 판에 두 규칙이 돌고 있었다.

보고서 2판(`report/comb/comb_musou_2026-08-22.html`)은
`results/comb_musou/comb_musou_v2.json` 위에 서 있고, 그 32가지는
거칠기를 sqrt(0.039)=0.1975 로 넘겨서 쟀다.

바뀐 게 없을 것으로 본다 -- 그 스윕이 쓰는 재료(musou_fit, wall_5pct)의
파일 거칠기가 마침 둘 다 0.1975 라 옛 규칙과 새 규칙이 같은 값을 준다.
**하지만 그건 예상이지 확인이 아니다.** 그래서 다시 잰다.

PRE-REGISTERED:
  R1  고른 여섯 가지가 저장값을 0.5 % 안에서 재현한다. 못 하면 보고서를
      다시 내야 하므로, 여기서 멈추고 어긋난 칸을 그대로 낸다.
  R2  무소를 칠한 경우(깊은 도장이 생기는 경우)가 특히 중요하다. 규칙이
      갈라지던 자리가 거기다. 그래서 표본에 반드시 넣는다.
"""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

ROOT = os.path.dirname(HERE)
STORED = os.path.join(ROOT, "results/comb_musou/comb_musou_v2.json")
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
SPP = 256
PANEL = 200.0
FOIL = 0.08
SLIDER = math.sqrt(0.039)
BASE = "wall_5pct"

# 무소 0 (깊은 도장 없음) 과 무소 있음(깊은 도장 생김) 을 섞는다
PICK = [(6.35, 30.0, 0.0), (6.35, 60.0, 15.0), (9.53, 40.0, 10.0),
        (9.53, 40.0, 15.0), (9.53, 60.0, 0.0), (6.35, 40.0, 5.0)]

rows = {(r["pitch"], r["depth"], r["musou"]): r
        for r in json.load(open(STORED))}
print("2판 32가지 중 여섯 가지를 다시 잰다. 거칠기 슬라이더 %.4f\n" % SLIDER,
      flush=True)
print("%-6s %-6s %-6s | %11s %11s %8s | %10s %10s %8s"
      % ("셀", "깊이", "무소", "총량 저장", "총량 지금", "차이",
         "번쩍임 저장", "지금", "차이"), flush=True)

worst = 0.0
out = []
for key in PICK:
    pitch, depth, mus = key
    st = rows[key]
    spec = {"top": "comb",
            "top_params": {"pitch": pitch, "wall_top": FOIL, "wall_bot": FOIL,
                           "comb_expand": 1.0, "jitter": 0.0},
            "depth": depth, "floor": "none", "panel": PANEL}
    if mus > 0:
        kw = dict(coating="musou_fit", deep_coating=BASE, paint_depth=mus)
    else:
        kw = dict(coating=BASE)
    pl = SS.measure(spec, THETAS, None, SLIDER, SPP,
                    phis=[0.0, 45.0, 90.0], **kw)
    tot = {k: max(pl[p][k] for p in pl) for k in pl["0"]}
    f = SS.form(dict(spec, panel=pitch * 10.0), thetas=[0.0], n_phase=6,
                samples=SPP, beam_w=7.5, diffuse_frac=None,
                roughness=SLIDER, **kw)
    pk = f.get("peak")
    if pk is None or any(v is None for v in tot.values()):
        raise SystemExit("빈 칸: %s" % (key,))
    s_tot = max(st["total"].values()); n_tot = max(tot.values())
    d1 = 100 * (n_tot - s_tot) / s_tot
    d2 = 100 * (pk - st["peak"]) / st["peak"]
    worst = max(worst, abs(d1), abs(d2))
    out.append({"key": list(key), "stored_total": s_tot, "now_total": n_tot,
                "stored_peak": st["peak"], "now_peak": pk,
                "d_total_pct": d1, "d_peak_pct": d2})
    print("%-6.2f %-6.0f %-6.0f | %10.5f%% %10.5f%% %7.3f%% | %10.4f %10.4f %7.3f%%"
          % (pitch, depth, mus, 100 * s_tot, 100 * n_tot, d1,
             st["peak"], pk, d2), flush=True)

print("\n저장값과 최대 %.3f %% 어긋난다." % worst, flush=True)
json.dump(out, open("/tmp/simsrv/v2repro.json", "w"), indent=1,
          ensure_ascii=False)
if worst > 0.5:
    print(">>> R1 실패. 보고서 2판을 다시 내야 한다.", flush=True)
else:
    print(">>> 통과. 보고서 2판과 그 아래 32가지가 그대로 유효하다.",
          flush=True)
print("\n@@DONE@@", flush=True)
