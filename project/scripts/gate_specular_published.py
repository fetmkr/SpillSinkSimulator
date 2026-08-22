# -*- coding: utf-8 -*-
"""발표된 정반사 실측값들을 우리 모델에 넣고 세 축을 잰다.

2026-08-22 밤에 논문 넷을 더 찾았고, 그 과정에서 내가 낸 오류 하나를 찾았다.

  **DePoy 2014 그림 6 의 세로축은 "Specular Reflectance Ratio (%)" 이고
  눈금이 0 에서 1 까지다. 퍼센트다.** "0.03" 은 3 % 가 아니라 0.03 % 다.
  나는 이걸 분수로 읽어서 확산비율을 0.97 로 적었다. 실제로는 0.9997 이다.
  100 배 틀렸고, 재료 파일 다섯 개가 그 값으로 서 있다.

발표된 정반사 몫 (총반사 대비), 전부 가시광:

  TAMU 2018 표 2, HeNe 633 nm, MADLaSR, 10~44 도를 2 도 간격
    구슬분사 주조알루미늄 검정 아노다이징 CBB   0.07 %   -> 확산 0.9993
    기계가공 주조알루미늄 검정 아노다이징 CMB   0.15 %   -> 확산 0.9985
    그대로   주조알루미늄 검정 아노다이징 CRB   0.57 %   -> 확산 0.9943
    연마     6061 알루미늄 아노다이징    APH   0.59 %   -> 확산 0.9941
    (견줌) 연마 스테인리스 무전해니켈  SPN  76.3 %   -> 확산 0.237

  TAMU 2014 그림 6, 같은 방식, 세 각도(10·22·44)
    무광 검정 스프레이                        약 0.1 %  -> 확산 약 0.999

  Zeng 2019 (NASA GSFC) 표 1A, 600 nm
    Z307 무광 검정 도료: 0/45 도 BRF 를 8 도 총반사로 나눈 값 1.008
    -> 정면에서 램버시안과 1 % 안에서 같다. 확산 0.99 이상.

  Filip & Vavra 2026 그림 6, 정면 TIS
    연마 알루미늄에 얇게 칠한 무광 아크릴 스프레이: 5 도 원뿔 안에 10~13 %
    -> 확산 0.90 이하. 거칠기 0.012~0.089.

이 넷은 서로 안 맞는다. 그리고 검출기 크기로는 화해가 안 된다:
5 도 원뿔과 0.6 도 원뿔의 몫 비는 GGX 덩어리 하나로는 아무리 넓혀도
69.5 배가 한계인데, 두 실측을 동시에 만족하려면 92.6 배가 필요하다.
그러니 **표면이 서로 다른 것이다.** Shirsekar 2019 도 같은 말을 한다 --
같은 도료라도 1 회 도포한 시료는 거칠고 3 회 도포한 시료는 광택이 난다.

**즉 "무광 검정 페인트의 정반사"는 상수가 아니라 도장 공정이 정하는 값이다.**

PRE-REGISTERED:
  R1  반사 총량은 확산비율을 0.90 에서 0.9993 까지 올려도 거의 안 변한다.
  R2  확산비율이 0.999 면 거칠기를 아무리 좁혀도 정면 반짝임이 거의 안 오른다.
      광택으로 갈 에너지 자체가 0.1 % 뿐이기 때문이다.
  R3  그래서 반짝임을 못 쓰게 만든 574 배 폭은 거칠기가 아니라 확산비율이
      진짜 원인이다. 확산비율만 확정되면 거칠기는 덜 중요해진다.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/specpub"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
SPP = 256

# (확산비율, 출처)
DFS = [
    (0.9993, "TAMU 2018 표2 CBB 구슬분사 검정 아노다이징 0.07 %"),
    (0.9990, "TAMU 2014 그림6 무광 검정 스프레이 약 0.1 %"),
    (0.9943, "TAMU 2018 표2 CRB 그대로 검정 아노다이징 0.57 %"),
    (0.9900, "Zeng 2019 표1A Z307, 정면에서 램버시안과 1 % 안"),
    (0.9700, "지금 재료 파일 값 (내가 100 배 잘못 읽은 값)"),
    (0.9000, "Filip&Vavra 2026 그림6 아크릴 무광, 5 도 원뿔 안 10 %"),
]
# 거칠기는 거의 램버시안인 재료에서는 실측이 안 묶는다. 양 끝을 둘 다 낸다.
RGS = [0.012, 0.30]

SPEC = {"top": "flat", "top_params": {}, "depth": 0.0,
        "floor": "none", "panel": 120.0}
PATCH = 63.5

rows = []
print("5 %% 무광 페인트 민판. 발표된 정반사 실측값들.\n", flush=True)
print("%-7s %6s | %10s %10s | %14s   %s"
      % ("확산", "거칠기", "총량 정면", "총량 밝은쪽", "정면 반짝임", "출처"),
      flush=True)

for df, src in DFS:
    for rg in RGS:
        pl = SS.measure(SPEC, THETAS, df, rg, SPP, phis=[0.0, 45.0, 90.0],
                        coating="wall_5pct")
        tot = {k: max(pl[q][k] for q in pl) for k in pl["0"]}
        pk = SS.form(dict(SPEC, panel=PATCH), thetas=[0.0], n_phase=6,
                     samples=SPP, beam_w=7.5, coating="wall_5pct",
                     diffuse_frac=df, roughness=rg)["peak"]
        if pk is None:
            raise SystemExit("반짝임이 비었다: df %.4f rg %.3f" % (df, rg))
        rows.append({"df": df, "roughness": rg, "source": src,
                     "total_head_on": tot["0"],
                     "total_brightest": max(tot.values()), "peak": pk})
        print("%-7.4f %6.3f | %10.5f %10.5f | %14.4f   %s"
              % (df, rg, 100 * tot["0"], 100 * max(tot.values()), pk,
                 src if rg == RGS[0] else ""), flush=True)
        json.dump(rows, open(os.path.join(OUT, "specpub.json"), "w"),
                  indent=1, ensure_ascii=False)

if len(rows) != len(DFS) * len(RGS):
    raise SystemExit("칸이 빈다. 끝났다고 안 한다.")

print("\n확산비율마다, 거칠기를 0.012 에서 0.30 까지 바꾸면 반짝임이:", flush=True)
for df, src in DFS:
    r = [x for x in rows if x["df"] == df]
    lo = min(x["peak"] for x in r); hi = max(x["peak"] for x in r)
    print("   확산 %.4f : %12.4f ~ %12.4f   (%.1f 배 폭)"
          % (df, lo, hi, hi / lo), flush=True)

tot = [x["total_brightest"] for x in rows]
print("\n반사 총량은 전체에서 %.1f %% 안에서만 움직인다."
      % (100 * (max(tot) - min(tot)) / min(tot)), flush=True)
print("\n@@DONE@@", flush=True)
