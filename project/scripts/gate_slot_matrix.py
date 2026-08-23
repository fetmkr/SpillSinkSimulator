# -*- coding: utf-8 -*-
"""위층 x 아래층 조합마다, 세 자리가 실제로 일을 하나.

지금까지 자리(바탕/덧칠/바닥)를 화면에 항상 셋 다 보여 줬다. 그런데
2026-08-24 에 평판(top: none)에서 재보니 셋 중 하나만 진짜였다:

    덧칠  무소를 1 mm 든 9 mm 든 칠해도 4.99650 % 로 같다 (아무 일도 안 함)
    바닥  5 % 페인트 판에 무소 바닥을 주면 0.99772 % -- 판 전체가 무소가 된다
          ("안 보이는 뒷면" 이라고 적어 놨던 자리가 판을 통째로 정하고 있었다)

하나씩 지적받아 고칠 게 아니라 조합을 전부 훑는다. 자리마다 재료를
확 바꿔 보고 숫자가 움직이는지로 판정한다. 움직이면 그 자리는 실재하고,
안 움직이면 화면에 있으면 안 된다.

판정
    OK      바뀐다 -- 이 조합에서 그 자리는 진짜다
    없음    0.1 % 미만 -- 아무 일도 안 한다. 자리를 보여 주면 거짓말이다
    가로챔  다른 자리의 값까지 바꾼다 -- 자리 구분이 거짓이다

PRE-REGISTERED:
  S1  top: none 은 '바탕' 하나만 OK 여야 한다. 나머지 둘은 없음/가로챔.
  S2  구조가 있고 아래층이 없으면 바탕·덧칠은 OK. 바닥(받침판)은 관이
      깊은 벌집에서는 OK, 골이 맞물리는 피라미드에서는 없음일 것이다.
  S3  아래층이 있으면 셋 다 OK.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/slotmatrix"
os.makedirs(OUT, exist_ok=True)
SPP = 192
SLIDER = 0.1975
LIGHT = "wall_5pct"     # 5.0 %
DARK = "musou_fit"      # 1.0 %  -- 다섯 배 차이. 못 알아채면 자리가 죽은 것이다

TOPS = [("none", {}, 10.0), ("pyramid", {"pitch": 4.0, "tip_flat": 0.4}, 22.0),
        ("comb", {"pitch": 6.35, "wall_top": 0.08, "wall_bot": 0.08,
                  "comb_expand": 1.0, "jitter": 0.0}, 40.0),
        ("cone", {}, 40.0)]
FLOORS = [("none", 0.0), ("gap", 4.0)]
STACKABLE = set(SS.families_json()["stackable"])


def run(top, tp, dep, floor, fdep, base, paint, floorc):
    # STACKED RUNS DROP THE TOP'S OWN PARAMETERS. `geom_stack` builds a
    # pyramid through `CellParams`, which has no `tip_flat`, so passing the
    # standalone parameters crashes it. That is a real defect in the stack
    # path -- the UI offers pyramid + a floor and it dies the same way -- but
    # it is not what this gate is measuring, so here we ask for defaults.
    spec = {"top": top, "top_params": ({} if floor != "none" else tp),
            "depth": dep, "floor": floor, "panel": 120.0}
    if floor != "none":
        spec["floor_depth"] = fdep
    kw = {}
    if paint:
        kw = dict(coating=paint, deep_coating=base, paint_depth=dep * 0.20)
    else:
        kw = dict(coating=base)
    if floorc:
        kw["floor_coating"] = floorc
    pl = SS.measure(spec, [0.0], None, SLIDER, SPP, phis=[0.0], **kw)
    return 100.0 * pl["0"]["0"]


def verdict(ref, got, other_moved):
    d = abs(got - ref) / ref * 100.0
    if other_moved:
        return "가로챔", d
    return ("OK" if d >= 0.1 else "없음"), d


rows = []
print("자리마다 재료를 5 %% -> 1 %% 로 바꿔 보고 숫자가 움직이나 본다.\n",
      flush=True)
print("%-9s %-7s | %10s | %-12s %-12s %-12s"
      % ("위층", "아래층", "기준 정면", "바탕", "덧칠", "바닥"), flush=True)

for top, tp, dep in TOPS:
    for floor, fdep in FLOORS:
        if floor != "none" and top not in STACKABLE:
            continue
        ref = run(top, tp, dep, floor, fdep, LIGHT, None, None)
        v_base = run(top, tp, dep, floor, fdep, DARK, None, None)
        v_paint = run(top, tp, dep, floor, fdep, LIGHT, DARK, None)
        v_floor = run(top, tp, dep, floor, fdep, LIGHT, None, DARK)
        # 바닥이 판 전체를 덮어쓰면 '가로챔' -- 바탕만 바꾼 것과 같은 값이 된다
        hijack = abs(v_floor - v_base) / max(v_base, 1e-9) < 0.005
        r = {"top": top, "floor": floor, "ref": ref}
        cells = []
        for name, val, hij in (("base", v_base, False), ("paint", v_paint, False),
                               ("floor", v_floor, hijack)):
            vd, d = verdict(ref, val, hij)
            r[name] = {"value": val, "verdict": vd, "delta_pct": d}
            cells.append("%-6s %5.1f%%" % (vd, d))
        rows.append(r)
        print("%-9s %-7s | %9.5f%% | %s %s %s"
              % (top, floor, ref, cells[0], cells[1], cells[2]), flush=True)
        json.dump(rows, open(os.path.join(OUT, "slotmatrix.json"), "w"),
                  indent=1, ensure_ascii=False)

print("\n=== 화면이 보여 줘야 할 자리 ===", flush=True)
for r in rows:
    live = [k for k in ("base", "paint", "floor") if r[k]["verdict"] == "OK"]
    bad = [k for k in ("base", "paint", "floor") if r[k]["verdict"] == "가로챔"]
    print("   %-9s + %-7s -> %s%s"
          % (r["top"], r["floor"], ", ".join(live) or "없음",
             ("   *** 가로챔: " + ", ".join(bad)) if bad else ""), flush=True)
# `r["floor"]` 는 문자열인데 위에서 %-7s 로 찍으면서 dict 을 넣었었다 --
# 요약 줄에만 나던 오타. 값 자체는 위 표가 정본이다.

flat = [r for r in rows if r["top"] == "none"]
if flat and flat[0]["paint"]["verdict"] == "OK":
    print("\n>>> S1 실패: 평판에서 덧칠이 일을 한다. 자리를 지우면 안 된다.",
          flush=True)
print("\n@@DONE@@", flush=True)
