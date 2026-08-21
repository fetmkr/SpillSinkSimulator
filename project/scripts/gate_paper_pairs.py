# -*- coding: utf-8 -*-
"""논문이 허용하는 (확산비율, 거칠기) 짝으로 실제로 재본다.

gate_roughness_from_tis.py 가 Filip & Vavra 2026 의 TIS 실측을 우리 모델에
거꾸로 풀어서, 5 % 무광 아크릴 페인트가 가질 수 있는 짝을 좁혔다:

    확산비율 0.97  ->  답 없음. 광택이 3 % 뿐이면 5 도 원뿔 안에 10 % 를
                      절대 못 넣는다. 우리가 쓰던 값이 논문과 안 맞는다.
    확산비율 0.90  ->  거칠기 0.012
    확산비율 0.80  ->  거칠기 0.034 ~ 0.046
    확산비율 0.70  ->  거칠기 0.052 ~ 0.064
    확산비율 0.50  ->  거칠기 0.075 ~ 0.089

무소 페인트는 정면 TIS 가 거의 확산 천장(0.9924)에 붙어 있다. 정면에서는
잴 수 있는 광택 덩어리가 없다는 뜻이다. 확산비율 0.99 를 그대로 둔다.

여기서 재는 것: 이 짝들에서 5 % 페인트 민판의 세 축이 얼마나 움직이나.
지금까지 쓰던 (0.97, 0.30) 과 나란히 놓는다.

PRE-REGISTERED:
  R1  반사 총량은 짝을 바꿔도 거의 안 변한다. 총량은 방향의 합이라 확산과
      광택을 어떻게 나누든 ρ0 가 고정이면 같아야 한다.
  R2  정면 번쩍임은 크게 오른다. 논문 짝은 전부 우리 0.30 보다 덩어리가
      훨씬 좁다. 같은 에너지가 더 높이 쌓인다.
  R3  R2 가 맞으면 보고서의 번쩍임 칸은 전부 다시 내야 한다.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/paperpairs"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
SPP = 256

# (이름, 확산비율, 거칠기, 출처)
PAIRS = [
    ("지금까지 쓰던 값",   0.97, 0.30, "가정. 근거 없음"),
    ("논문 짝 df 0.90",   0.90, 0.012, "Filip&Vavra Fig.6 TIS 0.87"),
    ("논문 짝 df 0.80",   0.80, 0.046, "TIS 0.87"),
    ("논문 짝 df 0.80 b", 0.80, 0.034, "TIS 0.90"),
    ("논문 짝 df 0.70",   0.70, 0.064, "TIS 0.87"),
    ("논문 짝 df 0.70 b", 0.70, 0.052, "TIS 0.90"),
    ("논문 짝 df 0.50",   0.50, 0.089, "TIS 0.87"),
]

# 민판만 본다. 형상이 섞이면 무엇이 움직였는지 못 가린다.
SPEC = {"top": "flat", "top_params": {}, "depth": 0.0,
        "floor": "none", "panel": 120.0}
PATCH = 63.5

rows = []
print("5 %% 무광 페인트 민판. 논문이 허용하는 짝으로만 잰다.\n", flush=True)
print("%-18s %5s %6s | %10s %10s | %12s"
      % ("짝", "확산", "거칠기", "총량 정면", "총량 밝은쪽", "정면 번쩍임"),
      flush=True)

for lab, df, rg, src in PAIRS:
    pl = SS.measure(SPEC, THETAS, df, rg, SPP, phis=[0.0, 45.0, 90.0],
                    coating="wall_5pct")
    tot = {k: max(pl[q][k] for q in pl) for k in pl["0"]}
    pk = SS.form(dict(SPEC, panel=PATCH), thetas=[0.0], n_phase=6,
                 samples=SPP, beam_w=7.5, coating="wall_5pct",
                 diffuse_frac=df, roughness=rg)["peak"]
    if pk is None:
        raise SystemExit("번쩍임이 비었다. 값 없이 끝내지 않는다: %s" % lab)
    rows.append({"label": lab, "df": df, "roughness": rg, "source": src,
                 "total_head_on": tot["0"], "total_brightest": max(tot.values()),
                 "peak": pk})
    print("%-18s %5.2f %6.3f | %10.5f %10.5f | %12.4f"
          % (lab, df, rg, 100 * tot["0"], 100 * max(tot.values()), pk),
          flush=True)
    json.dump(rows, open(os.path.join(OUT, "pairs.json"), "w"),
              indent=1, ensure_ascii=False)

if any(r["peak"] is None for r in rows) or len(rows) != len(PAIRS):
    raise SystemExit("칸이 비었다. 끝났다고 안 한다.")

base = rows[0]
print("\n지금까지 쓰던 값과 견주면", flush=True)
for r in rows[1:]:
    print("   %-18s 총량 %+6.1f %% · 번쩍임 %8.1f 배"
          % (r["label"],
             100 * (r["total_brightest"] - base["total_brightest"])
             / base["total_brightest"],
             r["peak"] / base["peak"]), flush=True)

pks = [r["peak"] for r in rows[1:]]
print("\n논문 짝들 안에서만 봐도 번쩍임이 %.1f 배 벌어진다." % (max(pks) / min(pks)),
      flush=True)
print("\n@@DONE@@", flush=True)
