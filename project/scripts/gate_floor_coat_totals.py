"""What does the FLOOR's finish alone do, on ALL THREE AXES?

Rewritten 2026-08-21. The first version measured the TOTAL only, and I then
wrote "a deep cell's floor finish is meaningless" from it. One axis of three is
not a verdict; this project's own rule is that a comparison shows every agreed
axis, and the reason it did not is that `form_buildable` had no way to take a
floor coating -- so smear and head-on had NEVER been measurable with a painted
floor. That path is now open, and this reads all three.

A bought honeycomb arrives anodised. The floor under it is a new part, so it is
the one surface a buyer can choose the finish of. Anodised is roughly 4.5 %
reflectance and Musou is roughly 1 %, so the question is worth an answer with a
number on it: how much of the panel's total does the floor decide?

This ran once as typed-in code against the sim server and died on an HTTP 500
when the server restarted under it. Nothing survived but a header. It is a
script now, in its own Blender, calling `measure` in-process.

Head-on (theta = 0) and the deployment angle (theta = -40), because a floor is
reachable at one and not the other: above a cell depth of pitch / tan(40) the
40-degree beam never lands on the floor at all, and the finish there cannot
matter however black it is.

ALREADY MEASURED on the total: shallow moves 34.5 % head-on and 1.9 % at -40;
deep moves 1.7 % and 0.0 %. Painting a shallow cell's floor Musou instead of
leaving it anodised is worth 26 % of the head-on total.

PRE-REGISTERED for the two axes that were never read:
  G1  head-on PEAK follows the total on the shallow stack and moves at least as
      much, because the peak is set by the brightest thing the observer can see
      down a cell and at theta = 0 that IS the floor.
  G2  on the deep stack head-on barely moves, for the same reason the total
      did not: the floor is not lit.
  G3  smear barely moves on either. Smear is a ratio of two widths in one
      frame, and a floor finish changes how much light comes back, not where it
      lands. If smear DOES move, "the floor only changes brightness" is wrong
      and the reach argument has to be re-made.
  G4  if G1-G3 hold, "a deep cell's floor finish is meaningless" is supported on
      all three axes rather than one -- and only for pitch 6 / depth 50, which
      is the single geometry measured.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/floorcoat_totals"
os.makedirs(OUT, exist_ok=True)

FLOOR_COATS = ["musou_fit", "wall_5pct", "anodised", "anodised_hi"]
THETAS = [0.0, -40.0]
SPP = 256
# pitch 6 / tan(40) = 7.15 mm is where a 40-degree beam stops reaching the
# floor, so one stack sits below it and one well above.
STACKS = [
    ("얕은 셀 6 · 바닥 4", {"top": "honeycomb", "top_params": {"pitch": 6.0},
                           "depth": 10.0, "floor": "pyramid",
                           "floor_depth": 4.0, "floor_params": {"pitch": 2.0},
                           "panel": 60.0}),
    ("깊은 셀 6 · 바닥 4", {"top": "honeycomb", "top_params": {"pitch": 6.0},
                           "depth": 50.0, "floor": "pyramid",
                           "floor_depth": 4.0, "floor_params": {"pitch": 2.0},
                           "panel": 60.0}),
]
rows = []
print("바닥 도료만 바꾼다. 벌집과 바닥 모양은 고정. 세 축 전부 읽는다.", flush=True)
for label, spec in STACKS:
    print("\n===== %s =====" % label, flush=True)
    print("%-13s %9s %9s %9s %9s" % ("바닥 도료", "총량0도", "총량-40도",
                                     "뭉개기", "정면"), flush=True)
    seen = {"t0": [], "t40": [], "smear": [], "peak": []}
    for fc in FLOOR_COATS:
        vals = []
        for th in THETAS:
            out = SS.measure(spec, [th], 0.76, 0.30, SPP, floor_coating=fc)
            vals.append(out["%g" % 0.0]["%.0f" % th])
        f = SS.form(spec, n_phase=6, samples=SPP, beam_w=7.5,
                    floor_coating=fc)
        sm, pk = f.get("smear"), f.get("peak")
        if None in vals or sm is None or pk is None:
            raise SystemExit("empty cell for %s -- refusing to report" % fc)
        seen["t0"].append(vals[0]); seen["t40"].append(vals[1])
        seen["smear"].append(sm); seen["peak"].append(pk)
        rows.append({"stack": label, "floor_coat": fc,
                     "rho0": SS.COATINGS[fc][0], "total_0": vals[0],
                     "total_m40": vals[1], "smear": sm, "peak": pk})
        print("%-13s %9.5f %9.5f %9.4f %9.5f   (도료 자체 %.3f %%)"
              % (fc, vals[0], vals[1], sm, pk, 100 * SS.COATINGS[fc][0]),
              flush=True)
        json.dump(rows, open(os.path.join(OUT, "floor_coat_axes.json"), "w"),
                  indent=1, ensure_ascii=False)
    print("   바닥 도료가 바꾼 폭:", flush=True)
    for k, name in (("t0", "총량 0도"), ("t40", "총량 -40도"),
                    ("smear", "모양 뭉개기"), ("peak", "정면 반짝임")):
        v = seen[k]
        print("      %-12s %.5f ~ %.5f   %.1f %%"
              % (name, min(v), max(v), 100 * (max(v) - min(v)) / min(v)),
              flush=True)
print("\n@@DONE@@", flush=True)
