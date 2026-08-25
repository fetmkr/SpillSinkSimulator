# -*- coding: utf-8 -*-
"""뒤집힌 피라미드가 선 피라미드보다 나은가. 그리고 벌집 바닥으로 쓰면.

어디서 나온 생각인가. 2026-08-25 에 사용자가 물었다 -- "역으로 뒤집힌
피라미드, 지금 피라미드의 몰드 형태 말이야." 시트를 눌러 피라미드를 만들면
반대면이 그대로 뒤집힌 피라미드다. **같은 부품을 뒤집어 다는 것**이라
공정이 하나도 안 는다.

남들이 이미 쟀다. 태양전지 쪽에서 둘을 나란히 놓고 비교하는데, 이유가 우리
계산과 같다: **뒤집힌 쪽에서 빛이 한두 번 더 튕긴다.** 파인 홈은 광선을
가운데로 모으고 솟은 봉우리는 밖으로 흘려보내기 때문이다. 실리콘에서
400~1000 nm 가중 반사율이 선 피라미드 12~14 %, 뒤집힌 것 7 % 미만
[Solar Energy 2023, doi:10.1016/j.solener.2023.03.049].

우리한테는 저쪽보다 훨씬 크다. 무소는 한 번 튕길 때 0.998 % 만 남기므로
튕김이 하나 더 붙으면 그 경로가 **백분의 일**이 된다.

여기서 재는 것:

    1  홀로 세운 것    선 피라미드 대 뒤집힌 피라미드. 간격 4 / 깊이 22,
                      끝 평평 0.1(연구 표준 샘플)과 0.4(발주 사양) 둘 다.
    2  벌집 바닥       오늘 측정에서 벌집 밑에 선 피라미드를 깔았더니 정면
                      반짝임이 6.7 배 내려갔다. 뒤집힌 것으로 깔면 더 내려가나.

기하 검사는 먼저 통과시켰다 -- `gate_model_fitness` 에서 열린 모서리 0,
똑같은 면 0, 겹침 0.51 (선 피라미드 0.55). 첫 판은 열린 모서리가 9,604 개라
숫자를 아예 안 냈다.

    zsh scripts/run_batch.sh scripts/sweep_pyramid_inverted.py pyrinv
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
PATH = os.path.join(OUT, "pyramid_inverted.json")

TOP = "musou_fit"
SLIDER, SAMPLES = 0.19748417658131498, 512
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
PANEL = 116.0            # 발주 사양이 쓰는 판 크기
COMB_PANEL = 200.0

# --- 1. 홀로 세운 것: 간격 4 / 깊이 22 ---
STANDALONE = [("선 피라미드 끝0.1", "pyramid", 0.1),
              ("뒤집힌 피라미드 끝0.1", "pyramid_inv", 0.1),
              ("선 피라미드 끝0.4", "pyramid", 0.4),
              ("뒤집힌 피라미드 끝0.4", "pyramid_inv", 0.4)]

# --- 2. 벌집 바닥: 오늘 이긴 조합(테두리 0.05 + 바닥 깊이 10)에서 바닥만 바꿈 ---
COMB_FLOORS = [("벌집 + 평판 바닥", None),
               ("벌집 + 선 피라미드 10", "pyramid"),
               ("벌집 + 뒤집힌 피라미드 10", "pyramid_inv")]
SMEAR_AT = {"선 피라미드 끝0.1", "뒤집힌 피라미드 끝0.1",
            "벌집 + 뒤집힌 피라미드 10"}


def spec_solo(kind, tip, panel=None):
    return {"top": kind, "top_params": {"pitch": 4.0, "tip_flat": tip,
                                        "apex_jitter": 0.0, "tip_drop": 0.0},
            "depth": 22.0, "panel": panel or PANEL, "floor": "none",
            "margin_depths": 0.2}


def spec_comb(floor, panel=None):
    s = {"top": "comb",
         "top_params": {"pitch": 9.53, "wall_top": 0.05, "wall_bot": 0.08,
                        "comb_expand": 1.0, "jitter": 0.0},
         "depth": 40.0, "panel": panel or COMB_PANEL, "margin_depths": 0.2}
    if floor:
        s["floor"] = floor
        s["floor_depth"] = 10.0
        s["floor_params"] = {"pitch": 9.53}
    else:
        s["floor"] = "none"
    return s


def run(name, sp, sp_patch):
    t0 = time.time()
    planes = SS.measure(sp, THETAS, None, SLIDER, SAMPLES, phis=PHIS,
                        coating=TOP)
    tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
    f = SS.form(sp_patch, thetas=[0.0], n_phase=6, samples=SAMPLES,
                beam_w=7.5, diffuse_frac=None, roughness=SLIDER, coating=TOP)
    pk = f.get("peak")
    if pk is None or tot.get("0") is None:
        raise SystemExit("빈 칸 (%s) -- 인정 안 함" % name)
    r = {"name": name, "total": tot, "planes": planes, "head_on": pk,
         "spec": sp, "top": TOP, "alpha": 0.039, "slider": SLIDER,
         "samples": SAMPLES, "smear": None, "sec": round(time.time() - t0, 1)}
    print("%-26s | %9.5f%% %9.5f%% %9.5f%% | %8.4f | %5.0f"
          % (name, 100 * tot["0"], 100 * tot["20"], 100 * tot["40"], pk,
             r["sec"]), flush=True)
    return r


rows = []
print("전부 무소. 세 축 다 잰다.\n", flush=True)
print("%-26s | %10s %10s %10s | %8s | %5s"
      % ("경우", "총량 정면", "총량 20도", "총량 40도", "반짝임", "초"),
      flush=True)
print("-- 1. 홀로 세운 것: 간격 4 / 깊이 22 --", flush=True)
for name, kind, tip in STANDALONE:
    rows.append(run(name, spec_solo(kind, tip), spec_solo(kind, tip, 40.0)))
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)

print("-- 2. 벌집 9.53 / 깊이 40 / 테두리 0.05, 바닥만 바꿈 --", flush=True)
for name, floor in COMB_FLOORS:
    rows.append(run(name, spec_comb(floor), spec_comb(floor, 95.3)))
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)

print("\n모양 뭉개기 (한 점에 5 분)\n", flush=True)
print("%-26s | %8s | %6s | %5s" % ("경우", "뭉개기", "담겼나", "초"), flush=True)
by = {r["name"]: r for r in rows}
for name in [n for n, _, _ in STANDALONE] + [n for n, _ in COMB_FLOORS]:
    if name not in SMEAR_AT:
        continue
    t0 = time.time()
    fm = SS.form(by[name]["spec"], thetas=[-40.0, 40.0], n_phase=6,
                 samples=SAMPLES, phis=PHIS, coating=TOP)
    r = by[name]
    r["smear"] = fm.get("smear")
    r["smear_converged"] = fm.get("converged")
    r["smear_n_phase"] = 6
    json.dump(rows, open(PATH, "w"), indent=1, ensure_ascii=False)
    print("%-26s | %8s | %6s | %5.0f"
          % (name, ("%.4f" % r["smear"]) if r["smear"] is not None else "-",
             r["smear_converged"], time.time() - t0), flush=True)

print("\n짝지어 견주기 (1 보다 작으면 뒤집힌 쪽이 어둡다 = 낫다)", flush=True)
for up, inv in (("선 피라미드 끝0.1", "뒤집힌 피라미드 끝0.1"),
                ("선 피라미드 끝0.4", "뒤집힌 피라미드 끝0.4"),
                ("벌집 + 선 피라미드 10", "벌집 + 뒤집힌 피라미드 10")):
    u, v = by[up], by[inv]
    print("  %-26s 정면 %.3f · 20도 %.3f · 40도 %.3f · 반짝임 %.3f"
          % (inv, v["total"]["0"] / u["total"]["0"],
             v["total"]["20"] / u["total"]["20"],
             v["total"]["40"] / u["total"]["40"],
             v["head_on"] / u["head_on"]), flush=True)
print("\n%s" % PATH, flush=True)
print("@@DONE@@", flush=True)
