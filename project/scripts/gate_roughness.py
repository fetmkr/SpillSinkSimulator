# -*- coding: utf-8 -*-
"""거칠기를 아무도 안 쟀다. 그게 문제인가 아닌가.

확산 비율은 2026-08-22 에 실측값을 찾았다 (DePoy et al. 2014). 거칠기는
어느 논문도 숫자로 안 준다 -- DePoy 는 세 각도만 재서 제일 밝은 값의 폭을 못 내고,
Filip & Vavra 2026 은 모양을 그림으로만 준다. 0.30 은 이 연구가 처음부터
쓰던 가정값이고, 정면 번쩍임 값 전부가 거기 매달려 있다.

훑어서 갈라야 한다:
  거의 안 변하면   안 잰 값이지만 문제가 아니다. 그렇게 적고 넘어간다.
  크게 변하면      고니오미터로 재기 전까지 정면 번쩍임 절대값을 못 쓴다.

확산 비율은 재료 실측값(무소 0.99, 무광 검정 0.97)으로 고정하고 거칠기만
바꾼다.

PRE-REGISTERED:
  R1  반사 총량은 거칠기에 거의 안 변한다. 총량은 모든 방향의 합이고,
      거칠기는 나가는 방향을 좁히거나 넓힐 뿐 양을 안 바꾼다.
  R2  정면 번쩍임은 크게 변한다. 덩어리를 좁히면 같은 에너지가 더 높이
      쌓인다. 거칠기 0.05 에서 0.60 사이로 몇 배는 움직일 것이다.
  R3  설계 사이의 순위는 거칠기에 안 뒤집힌다. 뒤집히면 형상 비교 자체를
      거칠기 실측 전까지 못 한다.
"""
import os, sys, json
HERE=os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0,HERE)
import sim_server as SS  # noqa: E402

OUT="/tmp/simsrv/rough"; os.makedirs(OUT, exist_ok=True)
THETAS=[0.0,-20.0,20.0,-40.0,40.0]; SPP=256
RG=[0.05,0.10,0.20,0.30,0.45,0.60]
def sq(p): return round(p*30.0,1)
DESIGNS=[
 ("민판",              {"top":"flat","top_params":{},"depth":0.0,
                        "floor":"none","panel":120.0}, "wall_5pct", 63.5),
 ("피라미드 p4/d22",    {"top":"pyramid","top_params":{"pitch":4.0,"tip_flat":0.4},
                        "depth":22.0,"floor":"none","panel":sq(4.0)},
                        "musou_fit", 40.0),
 ("벌집 6.35/d40",     {"top":"comb","top_params":{"pitch":6.35,"wall_top":0.08,
                        "wall_bot":0.08,"comb_expand":1.0,"jitter":0.0},
                        "depth":40.0,"floor":"none","panel":sq(6.35)},
                        "musou_fit", 63.5),
]
rows=[]
print("확산 비율은 재료 실측값으로 고정. 거칠기만 바꾼다.\n", flush=True)
print("%-18s %6s | %10s %10s | %10s"
      % ("설계","거칠기","총량 정면","총량 밝은쪽","정면 번쩍임"), flush=True)
for lab, spec, coat, patch in DESIGNS:
    got={}
    for rg in RG:
        pl=SS.measure(spec, THETAS, None, rg, SPP, phis=[0.0,45.0,90.0],
                      coating=coat)
        tot={k: max(pl[q][k] for q in pl) for k in pl["0"]}
        pk=SS.form(dict(spec, panel=patch), thetas=[0.0], n_phase=6,
                   samples=SPP, beam_w=7.5, coating=coat,
                   diffuse_frac=None)["peak"]
        got[rg]=(tot["0"], max(tot.values()), pk)
        print("%-18s %6.2f | %10.5f %10.5f | %10.4f"
              % (lab, rg, 100*tot["0"], 100*max(tot.values()), pk), flush=True)
    t0=[got[r][0] for r in RG]; tw=[got[r][1] for r in RG]; pk=[got[r][2] for r in RG]
    rows.append({"design":lab,"coat":coat,
                 "rows":{("%g"%r): list(got[r]) for r in RG}})
    print("   %-15s 총량 정면 %.1f %% 폭 · 총량 밝은쪽 %.1f %% 폭 · 번쩍임 %.1f 배 폭\n"
          % ("→", 100*(max(t0)-min(t0))/min(t0), 100*(max(tw)-min(tw))/min(tw),
             max(pk)/min(pk)), flush=True)
    json.dump(rows, open(os.path.join(OUT,"rough.json"),"w"), indent=1, ensure_ascii=False)
print("=== 순위가 거칠기에 뒤집히나 (총량, 밝은 각도) ===", flush=True)
for rg in RG:
    o=sorted([r for r in rows if r["design"]!="민판"],
             key=lambda r: r["rows"]["%g"%rg][1])
    print("   거칠기 %.2f : %s" % (rg, "  <  ".join(r["design"] for r in o)), flush=True)
print("\n@@DONE@@", flush=True)
