"""Cell 6.35 mm, light at 20 degrees: from what depth does the floor stop mattering?

Straight geometry says the direct beam stops reaching the floor at
depth = pitch / tan(theta) = 6.35 / tan(20) = 17.4 mm, and 20.1 mm if the beam
comes in along the cell's long diagonal. It also says the fall is LINEAR, not a
cliff: the lit width is pitch - depth*tan(theta).

Geometry is not the answer, because light also arrives at the floor after
bouncing off a wall, and because the quantity that matters is not "is the floor
lit" but "does painting it change what leaves the panel". So sweep depth and
paint the floor two ways, and read ALL THREE axes.

Musou (1.0 %) against anodised_hi (6.0 %) is the widest realistic pair: it is
the difference between a floor somebody paid to paint and a floor left as the
comb arrives.

THE ANSWER FROM THE LAST GATE, which is why head-on is in this table at all:
at pitch 6 / depth 50 the floor's finish moved the TOTAL by 1.7 % and the
head-on PEAK by 14.1 %. A mean over the whole cell hides a small bright spot;
the peak is that spot. I called that depth "not worth painting" from the total
alone and it was wrong.

PRE-REGISTERED:
  R1  at theta = 20 the total's sensitivity to the floor finish falls smoothly
      with depth and is small by 17-20 mm, matching the geometric cutoff.
  R2  head-on peak sensitivity does NOT follow it. Head-on light is at theta 0,
      travels straight down the cell, and reaches the floor at ANY depth, so
      the peak should stay sensitive well past 20 mm.
  R3  smear does not move at either depth or either finish.
  R4  if R1 and R2 both hold, the rule is: the CUTOFF DEPTH applies only to the
      angle you cut it for. There is no depth that makes a floor finish
      irrelevant to an observer looking straight at the panel.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402
import math  # noqa: E402

OUT = "/tmp/simsrv/reach20"
os.makedirs(OUT, exist_ok=True)
PITCH = 6.35
THETA = -20.0
SPP = 256
DEPTHS = [4.0, 8.0, 12.0, 17.0, 22.0, 30.0]
PAIR = ["musou_fit", "anodised_hi"]


def spec_for(d):
    return {"top": "honeycomb", "top_params": {"pitch": PITCH},
            "depth": d + 4.0, "floor": "pyramid", "floor_depth": 4.0,
            "floor_params": {"pitch": 2.0}, "panel": 60.0}


print("셀 %.2f mm, 빛 %g도. 바닥을 무소로 칠했을 때와 안 칠했을 때의 차이."
      % (PITCH, abs(THETA)), flush=True)
print("계산상 직접 닿는 한계 깊이: %.1f mm (모서리 방향이면 %.1f mm)\n"
      % (PITCH / math.tan(math.radians(abs(THETA))),
         PITCH * 2 / math.sqrt(3) / math.tan(math.radians(abs(THETA)))),
      flush=True)
print("%-8s %10s %10s %10s %10s" % ("셀 깊이", "빛의양20도", "빛의양정면",
                                    "뭉개짐", "정면번쩍임"), flush=True)
rows = []
for d in DEPTHS:
    sp = spec_for(d)
    got = {}
    for fc in PAIR:
        t20 = SS.measure(sp, [THETA], 0.76, 0.30, SPP, floor_coating=fc)
        t00 = SS.measure(sp, [0.0], 0.76, 0.30, SPP, floor_coating=fc)
        f = SS.form(sp, n_phase=6, samples=SPP, beam_w=7.5, floor_coating=fc)
        got[fc] = (t20["0"]["%.0f" % THETA], t00["0"]["0"],
                   f.get("smear"), f.get("peak"))
        if any(v is None for v in got[fc]):
            raise SystemExit("빈 칸 (%s, 깊이 %g) -- 결과로 인정 안 함" % (fc, d))
    a, b = got[PAIR[0]], got[PAIR[1]]
    pct = [100.0 * (y - x) / x for x, y in zip(a, b)]
    lit = max(0.0, 1.0 - d * math.tan(math.radians(abs(THETA))) / PITCH)
    rows.append({"depth": d, "lit_frac": lit,
                 "musou": a, "anodised_hi": b, "pct": pct})
    print("%-8.0f %9.1f%% %9.1f%% %9.1f%% %9.1f%%    (계산상 바닥 노출 %.0f%%)"
          % (d, pct[0], pct[1], pct[2], pct[3], 100 * lit), flush=True)
    json.dump(rows, open(os.path.join(OUT, "reach20.json"), "w"), indent=1)

print("\n칸의 숫자는 '안 칠했을 때가 칠했을 때보다 몇 % 나쁜가' 입니다.", flush=True)
print("@@DONE@@", flush=True)
