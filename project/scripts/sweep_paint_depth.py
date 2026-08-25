# -*- coding: utf-8 -*-
"""좋은 검정을 관 안쪽 몇 mm 까지 넣어야 하나. 벌집 9.53 mm / 깊이 40 mm.

왜 재나. 2026-08-24 에 중국 업체가 "9.53 mm 셀에 깊이 40 mm 면 안쪽까지
검게 칠할 수 없다, 아노다이징도 안 된다" 고 답했다. 관이 깊이 대 지름
4.2 대 1 이라 뿌리는 도료도 가루 도장도 안쪽 벽에 못 닿는다.

그런데 32가지 연구(comb_musou_v2.json)를 다시 보면 9.53/40 에서
무소를 5 mm 넣으나 15 mm 넣으나 정면 총량이 0.12142 % 와 0.12114 % 로
같다. 차이 0.2 %. 즉 **깊은 데까지 안 칠해도 될지 모른다.**

그 32가지는 무소 깊이를 0, 5, 10, 15 네 점에서만 봤다. 그래서 어디서
멈추는지 모른다. 2 mm 면 되는지 8 mm 는 있어야 하는지가 견적을 가른다.
여기서 촘촘히 재서 그 지점을 찾는다.

세 축을 다 잰다. 총량만 보면 나머지 두 축의 문제를 숨긴다.

    반사 총량   `measure` -- 여러 각도의 ρ_dh
    모양 뭉개기 `form` -- 되돌아온 빛의 rms, 평판을 1.0 으로 본다
    정면 반짝임 `form` -- 정면 봉우리 비, 평평한 무광 검정을 1.0 으로 본다

바탕은 5 % 무광 검정(wall_5pct). 관 안쪽에 보통 검정 도료는 들어간다고
보고, 그 위에 좋은 검정(무소 1.0 %)을 위에서부터 N mm 만 얹는 그림이다.
안쪽에 아무것도 못 넣는 경우는 이 스윕이 답하지 않는다 -- 맨 알루미늄
값이 우리 재료표에 없고, 없는 재료로 숫자를 내지 않는다.

자기 블렌더에서 돈다. 서버를 거치지 않는다.

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/sweep_paint_depth.py
"""
import os
import sys
import json
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "results", "paint_depth")
os.makedirs(OUT, exist_ok=True)

PITCH = 9.53
DEPTH = 40.0
FOIL = 0.08
PANEL = 200.0
BASE = "wall_5pct"      # 5.0 % -- 관 안쪽까지 들어가는 보통 무광 검정
TOP = "musou_fit"       # 1.0 % -- 위에서부터 N mm 만 얹는 좋은 검정

# 32가지 연구와 같은 설정. 숫자가 서로 비교되어야 한다.
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
PHIS = [0, 45, 90]
SAMPLES = 512
SLIDER = 0.19748417658131498    # alpha 0.039. 슬라이더는 알파의 제곱근이다

# 0 과 5 사이에서 무슨 일이 일어나는지가 견적을 가른다. 그 구간을 촘촘히.
DEPTHS = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0, 40.0]

SPEC = {"top": "comb",
        "top_params": {"pitch": PITCH, "wall_top": FOIL, "wall_bot": FOIL,
                       "comb_expand": 1.0, "jitter": 0.0},
        "depth": DEPTH, "panel": PANEL, "floor": "none",
        "margin_depths": 0.2}

# 뭉개기·반짝임은 한 점에 11 분 걸린다 (16 위상 x 2 각 x 3 면 = 96 프레임).
# 열두 점을 다 그렇게 재면 두 시간이고, 그러면 총량 곡선조차 두 시간 뒤에
# 나온다. 그래서 순서를 나눈다. 총량을 열두 점 다 먼저 재고 (한 점 12 초),
# 나머지 두 축은 곡선의 모양을 잡는 다섯 점만 재되 위상을 6 으로 줄인다.
#
# 위상 6 은 서버의 빠른 설정이고, 보고서에 실린 통계와 같은 수가 아니다.
# 그 값의 추정치다. 여기 숫자를 보고서에 그대로 옮기지 않는다.
FORM_AT = [0.0, 2.0, 5.0, 10.0, 40.0]
FORM_N_PHASE = 6


def arms(d):
    if d <= 0.0:
        # 좋은 검정이 아예 없다. 판 전체가 5 % 보통 검정.
        return dict(coating=BASE)
    if d >= DEPTH:
        # 끝까지 좋은 검정. 업체가 못 한다고 한 바로 그것.
        return dict(coating=TOP)
    return dict(coating=TOP, deep_coating=BASE, paint_depth=d)


rows = []
path = os.path.join(OUT, "paint_depth_9p53_40.json")
print("벌집 %.2f mm / 깊이 %.0f mm. 좋은 검정을 위에서부터 N mm 넣는다.\n"
      % (PITCH, DEPTH), flush=True)
print("1단계 -- 반사 총량 (열두 점)\n", flush=True)
print("%6s | %10s %10s %10s | %5s"
      % ("N mm", "총량 0도%", "총량 20도%", "총량 40도%", "초"), flush=True)

for d in DEPTHS:
    t0 = time.time()
    # `measure` 는 [면][각도] 로 돌려준다. 바깥이 면(phi 0/45/90), 안이
    # 보는 각도다. 처음에 뒤집어 써서 KeyError 로 죽었다.
    # 32가지 연구(sweep_comb_musou_v2.py:108)는 각 각도에서 세 면 중
    # 가장 밝은 값을 쓴다. 숫자가 서로 비교되려면 여기서도 그래야 한다.
    planes = SS.measure(SPEC, THETAS, None, SLIDER, SAMPLES,
                        phis=PHIS, **arms(d))
    tot = {k: max(planes[p][k] for p in planes) for k in planes["0"]}
    r = {"paint_depth": d, "pitch": PITCH, "depth": DEPTH, "foil": FOIL,
         "panel": PANEL, "base": BASE, "top": TOP, "alpha": 0.039,
         "slider": SLIDER, "samples": SAMPLES,
         "total": tot, "total_phi0": planes["0"], "planes": planes,
         "smear": None, "head_on": None, "form_n_phase": None,
         "sec": round(time.time() - t0, 1)}
    rows.append(r)
    json.dump(rows, open(path, "w"), indent=1, ensure_ascii=False)
    print("%6.1f | %10.5f %10.5f %10.5f | %5.0f"
          % (d, 100 * tot["0"], 100 * tot["20"], 100 * tot["40"], r["sec"]),
          flush=True)

print("\n2단계 -- 모양 뭉개기와 정면 반짝임 (다섯 점, 위상 %d 로 줄인 추정)\n"
      % FORM_N_PHASE, flush=True)
print("%6s | %8s %8s | %5s" % ("N mm", "뭉개기", "반짝임", "초"), flush=True)
by_d = {r["paint_depth"]: r for r in rows}
for d in FORM_AT:
    t0 = time.time()
    fm = SS.form(SPEC, thetas=[-40.0, 40.0], n_phase=FORM_N_PHASE,
                 samples=SAMPLES, phis=PHIS, **arms(d))
    r = by_d[d]
    r["smear"] = fm.get("smear")
    r["head_on"] = fm.get("head_on")
    r["form_n_phase"] = FORM_N_PHASE
    r["form_sec"] = round(time.time() - t0, 1)
    json.dump(rows, open(path, "w"), indent=1, ensure_ascii=False)
    print("%6.1f | %8s %8s | %5.0f"
          % (d, ("%.4f" % r["smear"]) if r["smear"] is not None else "-",
             ("%.4f" % r["head_on"]) if r["head_on"] is not None else "-",
             r["form_sec"]), flush=True)
print("", flush=True)

# 끝까지 칠한 것 대비 얼마나 따라잡았나. 견적을 가르는 숫자는 이것이다.
full = rows[-1]
none = rows[0]


def get(r, key):
    return r["total"][key] if key in ("0", "20", "40") else r[key]


def caught(key, r):
    a, b = get(none, key), get(full, key)
    v = get(r, key)
    if a is None or b is None or v is None or abs(a - b) < 1e-12:
        return None
    return 100.0 * (a - v) / (a - b)


print("\n끝까지 칠한 것을 100 %% 로 볼 때, N mm 만 칠하면 몇 %% 를 얻나",
      flush=True)
print("%6s | %9s %9s %9s" % ("N mm", "총량 0도", "총량 40도", "반짝임"),
      flush=True)
for r in rows:
    cells = []
    for key in ("0", "40", "head_on"):
        c = caught(key, r)
        cells.append("%8.1f%%" % c if c is not None else "%9s" % "-")
    print("%6.1f | %s %s %s" % (r["paint_depth"], *cells), flush=True)

json.dump(rows, open(path, "w"), indent=1, ensure_ascii=False)
print("\n%s" % path, flush=True)
print("@@DONE@@", flush=True)
