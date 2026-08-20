"""How shallow can the floor under a honeycomb be, and still do its job?

The floor rescued head-on (1.643 -> 0.118) and did nothing for smear
(0.9831 -> 0.9803) at floor depth 6 mm, pitch 2 mm -- aspect 3. A shallower
floor is cheaper: the project's own Phase 6.3 note says "under a deep honeycomb
the floor can be something cheap like a vacuum-formed 45 degree pyramid", and
a 45 degree pyramid at pitch 2 is only 1 mm deep.

So sweep the floor's depth with the cell above it fixed, and include a true
45 degree floor. The cell is set SHALLOW (6 mm) on purpose: at 6.5 mm pitch a
40 degree ray reaches a wall after 7.75 mm, so only a shallow cell lets the
oblique beam see the floor at all. Testing floor depth under a 24 mm cell would
measure nothing, because the floor is not lit at that angle.

PRE-REGISTERED:
  F1  head-on improves with floor depth and saturates -- the floor only has to
      break up the flat bottom, and past some depth there is no flat bottom
      left to break. I expect saturation by aspect ~1.5 (depth 3 at pitch 2).
  F2  a 4 mm floor is within 20 % of the 6 mm one on head-on. If so, the
      cheaper floor is the answer.
  F3  a true 45 degree floor (pitch 4, depth 2) is materially worse than the
      fine floors on head-on, because its facets are only 45 degrees from the
      observer -- but it may still be enough, and it is the cheapest thing that
      can be made.
  F4  smear is unmoved by ANY floor depth, because the wall does that job and
      the wall has not changed.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from gate_stack_honeycomb import measure                  # noqa: E402

OUT = "/tmp/simsrv/floordepth"; os.makedirs(OUT, exist_ok=True)
PITCH, CELL = 6.5, 6.0

CASES = [
    ("바닥 없음",            None,  None, None),
    ("잔바닥 p2 · 깊이 2",   2.0,   2.0,  0.05),
    ("잔바닥 p2 · 깊이 4",   2.0,   4.0,  0.05),
    ("잔바닥 p2 · 깊이 6",   2.0,   6.0,  0.05),
    ("잔바닥 p2 · 깊이 10",  2.0,  10.0,  0.05),
    ("45도 p4 · 깊이 2",     4.0,   2.0,  0.05),
]
print("벌집 칸 %.1f · 칸깊이 %.0f (40도 빛이 바닥에 닿는 깊이) · 판 200 · 빔 7.5"
      % (PITCH, CELL), flush=True)
print("%-22s %-8s %-9s %-10s %-10s %s"
      % ("바닥", "종횡비", "총량%", "뭉개기", "정면", "시간"), flush=True)
rows = []
for name, fp, fd, ft in CASES:
    if fp is None:
        spec = dict(top="honeycomb",
                    top_params={"pitch": PITCH, "wall_top": 0.08,
                                "wall_bot": 0.08, "jitter": 0.0},
                    depth=CELL, floor="none")
        asp = "-"
    else:
        spec = dict(top="honeycomb",
                    top_params={"pitch": PITCH, "wall_top": 0.08,
                                "wall_bot": 0.08, "jitter": 0.0},
                    depth=CELL + fd, floor="pyramid", floor_depth=fd,
                    floor_params={"pitch": fp, "tip_flat": ft})
        asp = "%.2f" % (fd / fp)
    t0 = time.time()
    try:
        rho, sm, win, conv, hd, ok, rx = measure(spec, PITCH)
    except Exception as e:
        print("%-22s 실패: %s" % (name, repr(e)[:70]), flush=True); continue
    rows.append(dict(name=name, floor_pitch=fp, floor_depth=fd, aspect=asp,
                     rho=rho, smear=sm, head_on=hd, conv=conv))
    print("%-22s %-8s %-9.4f %-10.4f %-10.5f %.0fs%s"
          % (name, asp, 100*rho, sm, hd, time.time()-t0,
             "" if conv else "  창 미수렴!"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "floordepth.json"), "w"), indent=1)

print("\n=== 판정 ===", flush=True)
d = {r["name"]: r for r in rows}
if "잔바닥 p2 · 깊이 6" in d and "잔바닥 p2 · 깊이 4" in d:
    a, b = d["잔바닥 p2 · 깊이 6"]["head_on"], d["잔바닥 p2 · 깊이 4"]["head_on"]
    print("  깊이 4 는 깊이 6 대비 정면 %+.1f %%  -> %s"
          % (100*(b-a)/a, "4mm 로 충분" if abs(b-a)/a <= 0.20 else "4mm 는 부족"),
          flush=True)
if "45도 p4 · 깊이 2" in d and "잔바닥 p2 · 깊이 6" in d:
    print("  45도 싼 바닥은 깊이6 잔바닥 대비 정면 %+.1f %%"
          % (100*(d["45도 p4 · 깊이 2"]["head_on"]-d["잔바닥 p2 · 깊이 6"]["head_on"])
             / d["잔바닥 p2 · 깊이 6"]["head_on"]), flush=True)
sm = [r["smear"] for r in rows]
print("  뭉개기 전체 흩어짐 %.1f %%  -> %s"
      % (100*(max(sm)-min(sm))/(sum(sm)/len(sm)),
         "F4 확인: 바닥은 뭉개기를 못 건드림" if (max(sm)-min(sm))/(sum(sm)/len(sm)) < 0.1
         else "바닥이 뭉개기를 움직임"), flush=True)
print("  비교: 피라미드 발주 사양 뭉개기 2.240 · 정면 0.182", flush=True)
print("@@DONE@@", flush=True)
