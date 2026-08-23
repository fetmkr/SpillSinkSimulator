# -*- coding: utf-8 -*-
"""받침판을 따로 칠할 수 있게 열어도 되나.

`floor: none` 이어도 셀 바닥에는 받침판이 있고 그 면이 방을 향한다. 서버는
이미 그걸 다룰 준비가 돼 있다 -- `floor_coating` 이 오면
`floor_boundary_depth = depth` 로 잡고, 렌더러가 그 평면에서 메시를 잘라
아래쪽 면에 다른 재료를 붙인다. **막고 있는 건 브라우저 한 줄이다:**

    floor_coating: ($('#floor').value !== 'none') ? $('#floorcoat').value : null

그냥 열면 기본값(`musou_fit`)이 실려 나가서 지금까지의 모든 무바닥 측정이
바뀐다. 그래서 UI 기본을 "바탕과 같게" 로 두려는데, 그러려면 먼저
**재료가 같을 때 자르기 자체가 숫자를 바꾸는지** 알아야 한다.
자르면 면이 늘어난다. 광학적으로는 같은 면이지만, 재보기 전에는 모른다.

PRE-REGISTERED:
  B1  받침판에 바탕과 같은 재료를 지정하면, 지정 안 한 것과 같은 값이 나온다.
      다르면 "바탕과 같게" 라는 기본값이 거짓말이 되므로 그 설계를 버린다.
  B2  받침판에 다른 재료를 주면 값이 움직인다. 안 움직이면 이 기능은
      아무 일도 안 하는 것이므로 열 이유가 없다.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/backing"
os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -40.0, 40.0]
SPP = 256
SLIDER = 0.1975            # sqrt(0.039), the paint's alpha

CASES = [
    ("벌집 6.35 / 깊이 40", {"top": "comb",
        "top_params": {"pitch": 6.35, "wall_top": 0.08, "wall_bot": 0.08,
                       "comb_expand": 1.0, "jitter": 0.0},
        "depth": 40.0, "floor": "none", "panel": 120.0}),
    ("피라미드 p4 / 깊이 22", {"top": "pyramid",
        "top_params": {"pitch": 4.0, "tip_flat": 0.4},
        "depth": 22.0, "floor": "none", "panel": 120.0}),
]
BASE = "anodised"

rows = []
print("floor: none. 받침판에 무엇을 주느냐로 세 번 잰다.\n", flush=True)
print("%-22s %-26s %11s %11s"
      % ("설계", "받침판", "정면 %", "40도 %"), flush=True)

for name, spec in CASES:
    got = {}
    for tag, fc in (("안 보냄 (지금 동작)", None),
                    ("바탕과 같게", BASE),
                    ("5 % 페인트", "wall_5pct")):
        pl = SS.measure(spec, THETAS, None, SLIDER, SPP, phis=[0.0],
                        coating=BASE, floor_coating=fc)
        v = pl["0"]
        if any(v.get(k) is None for k in ("0", "40")):
            raise SystemExit("빈 칸: %s / %s" % (name, tag))
        got[tag] = (100 * v["0"], 100 * v["40"])
        print("%-22s %-26s %11.5f %11.5f"
              % (name, tag, got[tag][0], got[tag][1]), flush=True)
    rows.append({"design": name, "rows": got})
    a = got["안 보냄 (지금 동작)"]; b = got["바탕과 같게"]; c = got["5 % 페인트"]
    d_same = max(abs(b[i] - a[i]) / a[i] for i in (0, 1)) * 100
    d_diff = max(abs(c[i] - a[i]) / a[i] for i in (0, 1)) * 100
    print("   B1 같은 재료면 차이 %.4f %% · B2 다른 재료면 차이 %.2f %%\n"
          % (d_same, d_diff), flush=True)
    json.dump(rows, open(os.path.join(OUT, "backing.json"), "w"),
              indent=1, ensure_ascii=False)

worst_same = 0.0
moved = []
for r in rows:
    a = r["rows"]["안 보냄 (지금 동작)"]; b = r["rows"]["바탕과 같게"]
    c = r["rows"]["5 % 페인트"]
    worst_same = max(worst_same,
                     max(abs(b[i] - a[i]) / a[i] for i in (0, 1)) * 100)
    moved.append(max(abs(c[i] - a[i]) / a[i] for i in (0, 1)) * 100)

print("B1: '바탕과 같게' 가 지금 동작과 최대 %.4f %% 차이" % worst_same, flush=True)
print("B2: 다른 재료를 주면 최대 %.2f %% 움직임" % max(moved), flush=True)
if worst_same > 0.5:
    print("\n>>> B1 실패. 자르기 자체가 숫자를 바꾼다. "
          "'바탕과 같게' 를 기본으로 두면 안 된다.", flush=True)
elif max(moved) < 0.5:
    print("\n>>> B2 실패. 받침판 재료가 아무 일도 안 한다. 열 이유가 없다.",
          flush=True)
else:
    print("\n>>> 통과. 기본을 '바탕과 같게' 로 두면 지금 숫자가 유지되고, "
          "고르면 실제로 달라진다.", flush=True)
print("\n@@DONE@@", flush=True)
