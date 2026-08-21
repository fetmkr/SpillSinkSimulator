# -*- coding: utf-8 -*-
"""확산 비율 0.97 에서 발표 순위가 바뀌는가.

발표 CSV 는 확산 0 / 0.76 / 1.00 세 가지로 훑어 놓았고, 규약은 그 셋 중
최악을 쓴다. 2026-08-22 에 확산 비율이 재료 값이라는 것이 확인됐다 --
검정 도료는 0.97, 무소는 0.99. 실측값이 d100 바로 옆이므로, 세 점에서
보간하면 다시 렌더하지 않고 답을 얻을 수 있다. 되는지부터 확인한다.

PRE-REGISTERED:
  P1  세 점(0, 0.76, 1.00) 사이에서 rho 는 부드럽게 움직인다. 0.97 을 직접
      재면 d76 과 d100 을 잇는 선에서 5 % 안에 든다. 들지 않으면 보간은
      못 쓰고 전부 다시 돌려야 한다.
  P2  0.97 에서의 값은 d100 에 가깝다.
  P3  설계 사이의 순위는 0.76 과 0.97 에서 같다. 바뀌면 발표된 모든 순위를
      다시 내야 한다.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import sim_server as SS  # noqa: E402

OUT="/tmp/simsrv/df097"; os.makedirs(OUT, exist_ok=True)
THETAS=[0.0,-20.0,20.0,-40.0,40.0]; SPP=256
DESIGNS=[
 ("피라미드 p4/d22/t0.4", {"top":"pyramid","top_params":{"pitch":4.0,"tip_flat":0.4},
                          "depth":22.0,"floor":"none","panel":100.0}),
 ("피라미드 p4/d20/t0.1", {"top":"pyramid","top_params":{"pitch":4.0,"tip_flat":0.1},
                          "depth":20.0,"floor":"none","panel":100.0}),
 ("벌집 6.35/d40",       {"top":"comb","top_params":{"pitch":6.35,"wall_top":0.08,
                          "wall_bot":0.08,"comb_expand":1.0,"jitter":0.0},
                          "depth":40.0,"floor":"none","panel":63.5}),
 ("민판",               {"top":"flat","top_params":{},"depth":0.0,
                          "floor":"none","panel":63.5}),
]
DFS=[0.0,0.76,0.97,1.00]
rows=[]
print("확산 비율만 바꾼다. 도료는 무소 고정. 세 평면 중 최악.\n", flush=True)
print("%-22s %8s %8s %8s %8s | %s" % ("설계","확산0","확산0.76","확산0.97","확산1.00","보간 오차"), flush=True)
for lab, spec in DESIGNS:
    got={}
    for df in DFS:
        pl=SS.measure(spec, THETAS, df, 0.30, SPP, phis=[0.0,45.0,90.0],
                      coating="musou_fit")
        got[df]={k: max(pl[q][k] for q in pl) for k in pl["0"]}
    worst=lambda d: max(got[d].values())
    lin = worst(0.76) + (worst(1.00)-worst(0.76))*(0.97-0.76)/(1.00-0.76)
    err = 100*(worst(0.97)-lin)/max(lin,1e-12)
    rows.append({"design":lab, **{("d%g"%d): {k: got[d][k] for k in got[d]} for d in DFS},
                 "interp_err_pct": err})
    print("%-22s %8.4f %8.4f %8.4f %8.4f | %+6.1f %%"
          % (lab, 100*worst(0.0), 100*worst(0.76), 100*worst(0.97),
             100*worst(1.00), err), flush=True)
    json.dump(rows, open(os.path.join(OUT,"df097.json"),"w"), indent=1, ensure_ascii=False)
print("\n=== 순위가 바뀌나 (최악 세타, 낮을수록 좋음) ===", flush=True)
for df in (0.76, 0.97):
    order=sorted(rows, key=lambda r: max(r["d%g"%df].values()))
    print("   확산 %.2f : %s" % (df, "  <  ".join(r["design"] for r in order)), flush=True)
print("\n@@DONE@@", flush=True)
