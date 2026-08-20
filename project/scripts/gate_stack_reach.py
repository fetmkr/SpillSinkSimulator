"""Is the honeycomb's smear stuck at 1.0 because the floor is UNREACHABLE?

Adding a fine pyramid floor under a 6.5 mm honeycomb fixed head-on (1.643 ->
0.118, better than the pyramid's 0.182) and did nothing at all for smear
(0.9831 -> 0.9803). Both numbers were converged, so neither is clipped.

Proposed mechanism, from geometry rather than from the render: smear is decided
at 40 deg incidence, and a ray at 40 deg travels 0.84 mm sideways per 1 mm of
depth. In a 6.5 mm cell it meets a wall after 7.7 mm. The honeycomb above the
floor is 24 mm deep, so the oblique beam never sees the floor -- it bounces
between vertical walls, which move light up and down but not sideways, and
comes back still a line. Head-on light does reach the floor, which is why only
that axis moved.

If that is right, smear must start moving as soon as the cells are shallow
enough for a 40 deg ray to reach the floor:

    reach depth = cell pitch / tan(40 deg) = 6.5 / 0.839 = 7.75 mm

So sweep the honeycomb's own depth across that threshold with the floor fixed.

PRE-REGISTERED:
  R1  at cell depth well above 7.75 mm (24, 16) smear stays ~0.98
  R2  at cell depth at or below 7.75 mm (6, 4) smear rises materially, because
      the oblique beam now lands on the pyramid floor
  R3  total gets WORSE as the cells shallow, because a shallow honeycomb traps
      less -- the project's own aspect-ratio law. So even if smear is rescued,
      it is rescued by turning the honeycomb into a shallow grid over a
      pyramid field, i.e. by making the pyramid do the work.
  R4  if smear does NOT move even when the floor is reachable, the mechanism is
      wrong and the vertical walls are re-collimating the light by themselves.
"""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import math                                               # noqa: E402
from gate_stack_honeycomb import measure                  # noqa: E402

OUT = "/tmp/simsrv/reach"; os.makedirs(OUT, exist_ok=True)
PITCH = 6.5
REACH = PITCH / math.tan(math.radians(40.0))
print("벌집 칸 %0.1f mm — 40도 빛이 바닥에 닿으려면 칸 깊이 %.2f mm 이하여야 함\n"
      % (PITCH, REACH), flush=True)
print("%-10s %-9s %-9s %-10s %-9s %-10s %s"
      % ("칸깊이", "바닥닿나", "총량%", "뭉개기", "쓴창", "정면", "시간"), flush=True)
rows = []
for cell in (24.0, 16.0, 10.0, 6.0, 4.0):
    spec = dict(top="honeycomb",
                top_params={"pitch": PITCH, "wall_top": 0.08,
                            "wall_bot": 0.08, "jitter": 0.0},
                depth=cell + 6.0, floor="pyramid", floor_depth=6.0,
                floor_params={"pitch": 2.0, "tip_flat": 0.05})
    t0 = time.time()
    try:
        rho, sm, win, conv, hd, ok, rx = measure(spec, PITCH)
    except Exception as e:
        print("%-10.1f 실패: %s" % (cell, repr(e)[:70]), flush=True); continue
    rows.append(dict(cell=cell, rho=rho, smear=sm, head_on=hd, conv=conv))
    print("%-10.1f %-9s %-9.4f %-10.4f %-9s %-10.5f %.0fs"
          % (cell, "예" if cell <= REACH else "아니오", 100*rho, sm,
             "%.0f%s" % (win, "" if conv else "!"), hd, time.time()-t0),
          flush=True)
    json.dump(rows, open(os.path.join(OUT, "reach.json"), "w"), indent=1)

print("\n=== 판정 ===", flush=True)
deep = [r for r in rows if r["cell"] > REACH]
shal = [r for r in rows if r["cell"] <= REACH]
if deep and shal:
    d = sum(r["smear"] for r in deep)/len(deep)
    s = sum(r["smear"] for r in shal)/len(shal)
    print("  바닥 못 닿는 깊이 평균 뭉개기 %.3f" % d, flush=True)
    print("  바닥 닿는 깊이   평균 뭉개기 %.3f  (%+.1f %%)" % (s, 100*(s-d)/d),
          flush=True)
    print("  -> %s" % ("기전 확인: 바닥이 닿으면 뭉개진다" if s > d*1.15
                       else "**기전 틀림: 바닥이 닿아도 안 뭉개진다**"), flush=True)
    print("  비교: 피라미드 발주 사양 2.240 · 벌집 단독 0.983", flush=True)
print("@@DONE@@", flush=True)
