# -*- coding: utf-8 -*-
"""거칠기 단위를 바로잡고, 논문 값으로 다시 잰다.

2026-08-22 낮에 단위를 틀렸다. 논문에서 얻은 GGX α 를 렌더러의 거칠기
슬라이더에 그대로 넣었는데, **Cycles 의 Glossy 노드는 슬라이더를 제곱해서
α 로 쓴다.** α 0.012 를 넣으려다 0.000144 를 렌더했다. 83 배 뾰족했다.

우리가 잰 12 점이 이걸 증명한다:
    (1-df)/(4·슬라이더^4) 예측  오차 0.00 ~ 5.4 %
    (1-df)/(4·슬라이더^2) 예측  오차 100 %
슬라이더가 √α 이므로, 물리 법칙은 교과서 그대로다:

    정면 반짝임 = 1 + (1 - 확산비율) / (4 α²)

그래서 어제 낸 '574 배 폭', '백만 배' 는 전부 단위 오류였다.
슬라이더 0.30 은 α 0.09 이고, Filip 창의 위 끝이 0.089 다.
**우리 값은 창 밖이 아니라 창의 가장자리였다.**

여기서 재는 것: 논문 α 를 제대로 넣었을 때 세 축이 얼마인가.

PRE-REGISTERED:
  R1  반사 총량은 여전히 거의 안 움직인다.
  R2  정면 반짝임이 백만이 아니라 한 자릿수에서 백 언저리로 내려온다.
  R3  렌더 값이 1 + (1-df)/(4 α²) 과 몇 % 안에서 맞는다. 안 맞으면 법칙이
      틀렸거나 슬라이더 해석이 틀린 것이고, 그 경우 아무 숫자도 안 낸다.
"""
import os, sys, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/alphaunits"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
SPP = 256

# (확산비율, GGX 알파, 이름)
CASES = [
    (0.9993, 0.190, "구슬분사 검정 아노다이징  TAMU2018 + MERL 흑착색강"),
    (0.9943, 0.190, "그대로 검정 아노다이징    TAMU2018 + MERL 흑착색강"),
    (0.9990, 0.039, "무광 검정 스프레이        TAMU2014 + MERL paint-black"),
    (0.9900, 0.039, "5 % 무광 페인트           Zeng2019 + MERL paint-black"),
    (0.9000, 0.039, "얇게 칠한 아크릴          Filip2026 + MERL paint-black"),
    (0.9000, 0.012, "Filip 창의 제일 뾰족한 끝"),
    (0.5000, 0.089, "Filip 창의 제일 무딘 끝"),
    (0.9930, 0.039, "무소 (거칠기는 [모름], 페인트 값 빌림)"),
]

SPEC = {"top": "flat", "top_params": {}, "depth": 0.0,
        "floor": "none", "panel": 120.0}
PATCH = 63.5

rows = []
print("5 %% 무광 페인트 민판. 논문 α 를 제대로 넣는다.")
print("슬라이더에는 √α 를 넣는다. 렌더러가 제곱하기 때문이다.\n", flush=True)
print("%6s %7s %8s | %10s | %11s %11s %6s  %s"
      % ("확산", "α", "슬라이더", "총량 밝은쪽", "잰 반짝임", "식 예측", "오차", "이름"),
      flush=True)

worst = 0.0
for df, alpha, name in CASES:
    slider = math.sqrt(alpha)
    pl = SS.measure(SPEC, THETAS, df, slider, SPP, phis=[0.0, 45.0, 90.0],
                    coating="wall_5pct")
    tot = {k: max(pl[q][k] for q in pl) for k in pl["0"]}
    pk = SS.form(dict(SPEC, panel=PATCH), thetas=[0.0], n_phase=6,
                 samples=SPP, beam_w=7.5, coating="wall_5pct",
                 diffuse_frac=df, roughness=slider)["peak"]
    if pk is None:
        raise SystemExit("반짝임이 비었다: %s" % name)
    law = 1.0 + (1.0 - df) / (4.0 * alpha * alpha)
    err = 100.0 * (law - pk) / pk
    worst = max(worst, abs(err))
    rows.append({"df": df, "alpha": alpha, "slider": slider, "name": name,
                 "total_brightest": max(tot.values()), "peak": pk,
                 "law": law, "err_pct": err})
    print("%6.4f %7.3f %8.4f | %10.5f | %11.4f %11.4f %5.1f%%  %s"
          % (df, alpha, slider, 100 * max(tot.values()), pk, law, err, name),
          flush=True)
    json.dump(rows, open(os.path.join(OUT, "alphaunits.json"), "w"),
              indent=1, ensure_ascii=False)

print("\n식과 렌더가 최대 %.1f %% 어긋난다." % worst, flush=True)
if worst > 15.0:
    raise SystemExit("15 %% 를 넘는다. 법칙이나 단위 해석이 틀렸다. 숫자를 안 낸다.")

tot = [r["total_brightest"] for r in rows]
pks = [r["peak"] for r in rows]
print("반사 총량 폭 %.1f %% · 정면 반짝임 폭 %.1f 배"
      % (100 * (max(tot) - min(tot)) / min(tot), max(pks) / min(pks)), flush=True)
print("\n@@DONE@@", flush=True)
