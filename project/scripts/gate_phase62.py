"""GATE 9: was the published "shadow effect" a physical result or a clipped window?

report/ko/phase6.html tells the CLIENT:

    "실제 빔폭 9mm에서는 굵은 피라미드(10/50)가 반사된 줄을 평판보다 좁게
     돌려보냅니다(뭉개기 0.675). 순수 무광 대조 실험으로 원인을 확인했습니다.
     빔을 마주보는 경사면만 빛나는 그림자 효과입니다."

0.675 is BELOW the flat-plate floor. Today's synthetic check shows that is the
exact signature of a window that lost the tails: rms_width normalises by the
energy INSIDE the window, so light thrown outside leaves the numerator AND the
denominator and the reading collapses onto the core. A profile whose true rms
is 17.8 mm reads 0.80 mm through a 24 mm window -- indistinguishable from a
design that does not smear at all.

Phase 6.2 used face 60, i.e. a 24 mm window.

So: same design, same beam, window swept to convergence.

PRE-REGISTERED:
  Q1  p10/d50 at beam 9 converges WELL above 1.0 -- I expect 5-25x, by analogy
      with p10/d90 which went 1.365 -> 24.864.
  Q2  the 24 mm window reproduces something near the published 0.675.
      If it does, the published number is the artifact and the shadow-effect
      explanation is unsupported.
  Q3  if instead it converges near 0.675, the published claim stands and the
      shadow effect is real. That would be the better outcome and it must be
      given a fair chance -- hence measuring rather than assuming.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
from rig_v2_gates_form import form_run  # noqa: E402

OUT = "/tmp/simsrv/phase62"; os.makedirs(OUT, exist_ok=True)
WINS = [24.0, 48.0, 96.0, 192.0, 384.0, 600.0]
rows = []
for label, prm, beam, face in [
        ("p10/d50 beam 9  (the published claim)",
         dict(kind="pyramid", pitch=10.0, depth=50.0, tip_flat=0.0), 9.0, 700.0),
        ("p10/d50 beam 7.5 (deployment)",
         dict(kind="pyramid", pitch=10.0, depth=50.0, tip_flat=0.0), 7.5, 700.0)]:
    r = form_run(prm, face, beam, n_phase=12, spp=384, windows=WINS)
    rows.append({"label": label, **r})
    print("\n%s   face %.0f  %d px  %.3f mm/px%s"
          % (label, face, r["res_x"], r["mm_per_px"],
             "  CAPPED" if r["capped"] else ""), flush=True)
    prev = None
    for h in WINS:
        v = r["by_window"][h]
        s = v["smear"]
        d = "" if (prev is None or s is None) else "  (%+.1f %%)" % (100*(s-prev)/prev)
        print("   window %6.0f mm | smear %s  head-on %s%s%s"
              % (h, ("%8.3fx" % s) if s is not None else "   None ",
                 ("%.4f" % v["head_on"]) if v["head_on"] is not None else "None",
                 d, ("   " + v["problem"]) if v["problem"] else ""), flush=True)
        prev = s
    a, b = r["by_window"][WINS[-1]]["smear"], r["by_window"][WINS[-2]]["smear"]
    if a and b:
        print("   -> %s   published 0.675   ratio %.1fx"
              % ("CONVERGED" if abs(a-b)/a <= 0.02 else "**NOT CONVERGED**",
                 a/0.675), flush=True)
    with open(os.path.join(OUT, "gate_phase62.json"), "w") as fh:
        json.dump(rows, fh, indent=1, default=str)
print("\n@@DONE@@")
