"""Phase 5.5 re-measured with converged windows. The published table is wrong.

FINDINGS_phase55_beamwidth.md concluded, from a 60 mm panel whose measurement
window was 24 mm:

    "Coarse pitch is not rehabilitated by a big beam. Pitch 10 returns a stripe
     NARROWER than the flat wall's at every width (smear 0.65-1.27): its 10 mm
     flanks act as mirrors and keep the stripe a stripe."

Today, on identical renders, that design reads 1.35x through a 24 mm window and
23.03x through a converged one. The window clipped a 60 mm-wide return. The
conclusion is an artifact of the instrument, and the rejection of pitch 10 that
rests on it is unsafe.

This redoes the whole 3 pitches x 3 beams table with the window opened until
the answer stops moving, and reports the convergence beside every value so the
table can be audited rather than trusted.

Same designs as the original (scripts/sweep_phase55.py):
    p02  depth 18  pitch 2      p55  depth 50  pitch 5.5      p10  depth 90  pitch 10
Same beams: 2, 5, 10 mm. Same theta -40. Same statistic.
Different: panel large enough to hold the return, window driven to convergence,
mm-per-pixel held fixed instead of pixel count.

PRE-REGISTERED:
  R1  p02 and p55 land within 25 % of their published values (their returns are
      3-4 mm wide and the old 24 mm window held them).
  R2  p10 lands 10-20x ABOVE its published value at every beam width.
  R3  the published claim "smear falls with beam width for every pitch" still
      holds after the fix, because it is driven by the flat control blurring,
      which the window never clipped.
  R4  the ORDER of the three pitches on the smear axis INVERTS: published has
      p2 > p55 > p10, and I expect p10 > p55 > p2 once nothing is clipped.
"""

import os
import sys
import json

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rig_v2 as R2  # noqa: E402
from rig_v2_gates_form import form_run  # noqa: E402

OUT = "/tmp/simsrv/redo55"
os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(OUT, "redo_phase55.json")

DESIGNS = {
    "p02": dict(kind="pyramid", depth=18.0, pitch=2.0, tip_flat=0.0),
    "p55": dict(kind="pyramid", depth=50.0, pitch=5.5005500550055, tip_flat=0.0),
    "p10": dict(kind="pyramid", depth=90.0, pitch=10.0, tip_flat=0.0),
}
BEAMS = [2.0, 5.0, 10.0]
WINS = [24.0, 48.0, 96.0, 192.0, 384.0]
FACE = 400.0

PUBLISHED = {                      # from FINDINGS_phase55_beamwidth.md
    ("p02", 2.0): 4.104, ("p02", 5.0): 1.793, ("p02", 10.0): 1.040,
    ("p55", 2.0): 4.159, ("p55", 5.0): 1.825, ("p55", 10.0): 1.075,
    ("p10", 2.0): 1.272, ("p10", 5.0): 0.786, ("p10", 10.0): 0.655,
}

rows = []
for name, prm in DESIGNS.items():
    for beam in BEAMS:
        r = form_run(prm, FACE, beam, n_phase=12, spp=384, windows=WINS)
        s = [r["by_window"][h]["smear"] for h in WINS]
        h_on = [r["by_window"][h]["head_on"] for h in WINS]
        conv = abs(s[-1] - s[-2]) / s[-1] <= 0.02
        pub = PUBLISHED[(name, beam)]
        rec = {"design": name, "beam": beam, "published": pub,
               "converged": s[-1], "ratio_to_published": s[-1] / pub,
               "by_window": {str(h): r["by_window"][h] for h in WINS},
               "convergence_ok": conv, "res_x": r["res_x"],
               "mm_per_px": r["mm_per_px"], "capped": r["capped"]}
        rows.append(rec)
        print("%-4s beam %4.1f | window sweep %s | converged %8.3fx  "
              "published %6.3f  ratio %6.2fx  %s"
              % (name, beam, " ".join("%.2f" % x for x in s), s[-1], pub,
                 s[-1] / pub, "OK" if conv else "**NOT CONVERGED**"),
              flush=True)
        print("       head-on across the same windows: %s"
              % " ".join("%.4f" % x for x in h_on), flush=True)
        with open(LOG, "w") as fh:
            json.dump(rows, fh, indent=1)

print("\n--- smear ORDER, converged (higher smears more) ---", flush=True)
for beam in BEAMS:
    order = sorted([r for r in rows if r["beam"] == beam],
                   key=lambda r: -r["converged"])
    print("  beam %4.1f : %s" % (beam, "  >  ".join(
        "%s %.2f" % (r["design"], r["converged"]) for r in order)), flush=True)
print("\n  published order was p02 > p55 > p10 at every beam", flush=True)
print("@@DONE@@")
