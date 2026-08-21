"""The things every number in the comb report has to be read against.

A reader who has never seen this project needs to know what "0.4 %" and "8x"
mean before a chart of 32 of them says anything. So measure the reference
points on the same rig, in the same units, on the same day:

  plain wall, 5 % paint      the control the head-on ratio is defined against,
                             so it must read 1.00 by construction -- if it does
                             not, the ratio is not what the metric claims
  plain wall, Musou          what a flat wall does if you buy the black paint
                             and nothing else
  order-spec pyramid         the design this project currently recommends
                             (pitch 4, depth 22, tip 0.4, Musou)

Units, stated once:
  total    fraction of incoming light sent back, whole panel, hemisphere-
           averaged. 0.004 = 0.4 %.
  head-on  peak of the returned line divided by the peak the same beam makes
           on a plain matte black wall. 1.00 = same as that wall.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/comb_musou"; os.makedirs(OUT, exist_ok=True)
THETAS = [0.0, -20.0, 20.0, -40.0, 40.0]
SPP = 256
CASES = [
    ("맨 벽 · 무광 검정 5%", {"top": "flat", "top_params": {}, "depth": 0.0,
                             "floor": "none", "panel": 200.0},
     dict(coating="wall_5pct"), 63.5),
    ("맨 벽 · 무소", {"top": "flat", "top_params": {}, "depth": 0.0,
                     "floor": "none", "panel": 200.0},
     dict(coating="musou_fit"), 63.5),
    ("맨 벽 · 아노다이징 그대로", {"top": "flat", "top_params": {}, "depth": 0.0,
                                "floor": "none", "panel": 200.0},
     dict(coating="anodised"), 63.5),
]
rows = []
print("%-26s | %-9s %-9s %-9s | %s"
      % ("비교군", "0도", "20도", "40도", "번쩍임(맨벽=1)"), flush=True)
for label, spec, kw, patch in CASES:
    tot = SS.measure(spec, THETAS, 0.76, 0.30, SPP, **kw)["0"]
    f = SS.form(dict(spec, panel=patch), thetas=[0.0], n_phase=6,
                samples=SPP, beam_w=7.5, diffuse_frac=None, **kw)
    pk = f.get("peak")
    vals = {("%.0f" % t): tot.get("%.0f" % t) for t in THETAS}
    if pk is None or any(v is None for v in vals.values()):
        raise SystemExit("빈 칸: %s" % label)
    rows.append({"label": label, "total": vals, "peak": pk, **{
        k: (v if isinstance(v, (int, float, str)) else str(v))
        for k, v in kw.items()}})
    print("%-26s | %9.5f %9.5f %9.5f | %9.3f"
          % (label, vals["0"], max(vals["-20"], vals["20"]),
             max(vals["-40"], vals["40"]), pk), flush=True)
    json.dump(rows, open(os.path.join(OUT, "baselines.json"), "w"), indent=1,
              ensure_ascii=False)
print("\n@@DONE@@", flush=True)
