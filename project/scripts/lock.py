"""
Regression lock: the headline numbers are frozen, and any change to the
geometry or the measurement chain that moves them fails loudly and at once.

    Blender --background --factory-startup --python scripts/lock.py -- check
    Blender --background --factory-startup --python scripts/lock.py -- noise
    Blender --background --factory-startup --python scripts/lock.py -- freeze

Every wrong headline number this project has produced was a silent one: a
margin defect, a tessellation artifact, base-overlap gaps, a backing slab that
crept up and filled the valleys. In each case the geometry changed under a
number that had already been reported, and nothing said so. Four of the five
would have been caught here, in the ten seconds this takes, instead of three
reports later.

    noise    same cases, four different sampling seeds, to measure the Monte
             Carlo spread. The tolerance is set from this, not guessed.
    freeze   write results/LOCK.json  (run only when a change is INTENDED,
             and say in the commit what moved and why)
    check    re-measure and diff against the lock. Non-zero exit on drift.

The cases are deliberately few and the angles three, so that there is never a
reason not to run it.
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders", "lock")
LOCK = os.path.join(ROOT, "results", "LOCK.json")

# head-on, the +/-40 working band, and a grazing angle -- grazing is where the
# margin defect lived, so it has to be in the lock
ANGLES = (0.0, -40.0, -70.0)

# the geometry here is copied from export_cone.py and from the report cases on
# purpose: if those drift apart, that IS the failure being tested for
# These are the four designs the report quotes, at the parameters it quotes
# them at, including tileable=True on the cones. That last one matters: the
# cones were once measured with tileable off while the STL and the picture had
# it on, which re-snaps the lattice and moved head-on by 7.5%. A lock that
# guards a design nobody reports would not have caught it.
CASES = {
    "cone_d30_p75": ("cone3d",
                     dict(depth=30.0, pitch=7.5, tip_radius=0.2, jitter=0.30,
                          radial_seg=24, height_seg=3, margin_depths=6.5,
                          centre_margin_pitches=1.0, backing=3.0,
                          tileable=True, depth_jitter=0.0)),
    "cone_d30_p375": ("cone3d",
                      dict(depth=30.0, pitch=3.75, tip_radius=0.2,
                           jitter=0.30, radial_seg=24, height_seg=3,
                           margin_depths=6.5, centre_margin_pitches=1.0,
                           backing=3.0, tileable=True, depth_jitter=0.0)),
    "groove_d30_p75": ("ridge",
                       dict(depth=30.0, pitch_mean=7.5, tip_width=0.4,
                            arc_segments=24, valley_round=0.4,
                            margin_depths=6.5)),
    "groove_d50_p13": ("ridge",
                       dict(depth=50.0, pitch_mean=13.0, tip_width=0.4,
                            arc_segments=24, valley_round=0.4,
                            margin_depths=6.5)),
    # A genuinely flat plate carrying the PANEL coating: the reference the
    # "Nx darker than the coating alone" claim is measured against, and the
    # one case whose answer is known independently -- it must read 0.4953%.
    #
    # This was wrong until reviewed, and the way it was wrong is worth keeping
    # written down. tip_round defaults True, which caps each ridge with a
    # half-cylinder of radius tip_width/2 -- here 24.95 mm. The "flat plate"
    # was a washboard of 25 mm half-cylinders over 25 mm slots, and read
    # 0.353%. The build even emitted "tip takes 99.8% of the face" and nothing
    # read it. So the lock's own self-check was the only inert thing in it.
    "flat_coating": ("ridge",
                     dict(depth=0.001, pitch_mean=50.0, tip_width=50.0,
                          tip_round=False, pitch_jitter=0.0, arc_segments=4,
                          valley_round=0.0, margin_depths=6.5)),
}

# the diffuse reference plate that sits beside every panel in every frame. It
# is 0.05 by construction, so if it ever reads otherwise the measurement chain
# has moved and nothing else in the lock means anything. It was already being
# computed in every render and thrown away.
CONTROL_NOMINAL = 0.05
CONTROL_TOL = 5e-4


def measure(name, seed):
    family, params = CASES[name]
    cfg = {"tag": "lock_%s_s%d" % (name, seed), "family": family,
           "out_dir": RENDERS, "results_dir": os.path.join(RENDERS, "json"),
           "samples": 512, "res_x": 900, "res_y": 420, "gpu": True,
           "cycles_seed": seed, "params": params,
           "renders": [{"mode": "hemi_view", "theta": t} for t in ANGLES]}
    cfg.update(COAT)
    res = BR.run(cfg)
    out = {}
    for rec in res["modes"].values():
        out[str(rec["theta"])] = rec["panel"]["mean"]
        # the measurement chain check, on every case rather than a special one
        c = rec["control"]["mean"]
        if abs(c - CONTROL_NOMINAL) > CONTROL_TOL:
            out.setdefault("_control_bad", []).append(
                "%s th=%s control=%.6f (nominal %.4f)"
                % (name, rec["theta"], c, CONTROL_NOMINAL))
    return out


def run_all(seed=0):
    return {name: measure(name, seed) for name in CASES}


def control_problems(cur):
    """Every reading of the 0.05 diffuse plate that came back wrong."""
    bad = []
    for d in cur.values():
        bad.extend(d.get("_control_bad", []))
    return bad


def values_only(cur):
    return {n: {k: v for k, v in d.items() if not k.startswith("_")}
            for n, d in cur.items()}


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    what = argv[0] if argv else "check"
    os.makedirs(RENDERS, exist_ok=True)
    t0 = time.time()

    if what == "noise":
        # what does the same geometry read when only the sampling seed moves?
        # the tolerance has to be bigger than this and nothing else.
        runs = [run_all(s) for s in (0, 1, 2, 3)]
        worst = 0.0
        print("\n%-22s %6s %12s %12s %8s"
              % ("case", "theta", "min", "max", "spread"))
        for name in CASES:
            for th in (str(float(t)) for t in ANGLES):
                vals = [r[name][th] for r in runs]
                lo, hi = min(vals), max(vals)
                sp = (hi - lo) / lo if lo > 0 else 0.0
                worst = max(worst, sp)
                print("%-22s %6s %12.6f %12.6f %7.2f%%"
                      % (name, th, lo * 100, hi * 100, sp * 100))
        print("\nworst seed-to-seed spread: %.2f%%" % (worst * 100))
        print("=> set TOL to comfortably above this, and nothing else")
        return

    if what == "freeze":
        cur = run_all(0)
        for msg in control_problems(cur):
            print("[CONTROL]", msg, flush=True)
        json.dump({"tol": 0.03, "angles": ANGLES,
                   "values": values_only(cur)}, open(LOCK, "w"), indent=2)
        print("[FROZEN]", LOCK, "(%.0fs)" % (time.time() - t0))
        for name, d in cur.items():
            print("  %-22s %s" % (name, "  ".join(
                "%s:%.4f%%" % (t, v * 100) for t, v in sorted(d.items()))))
        return

    if not os.path.exists(LOCK):
        print("[LOCK] no lock file; run `freeze` first")
        sys.exit(2)
    ref = json.load(open(LOCK))
    tol = ref["tol"]
    cur = run_all(0)
    bad = []
    print("\n%-22s %6s %10s %10s %8s  %s"
          % ("case", "theta", "locked", "now", "drift", ""))
    for name in CASES:
        for th in (str(float(t)) for t in ANGLES):
            a = ref["values"].get(name, {}).get(th)
            b = cur[name][th]
            if a is None:
                print("%-22s %6s %10s %10.4f %8s  NEW" % (name, th, "-",
                                                          b * 100, "-"))
                continue
            drift = (b - a) / a if a > 0 else 0.0
            ok = abs(drift) <= tol
            if not ok:
                bad.append((name, th, a, b, drift))
            print("%-22s %6s %10.4f %10.4f %+7.1f%%  %s"
                  % (name, th, a * 100, b * 100, drift * 100,
                     "ok" if ok else "*** DRIFT ***"))
    ctrl_bad = control_problems(cur)
    for msg in ctrl_bad:
        print("[CONTROL] *** %s" % msg)
    print("\n%.0fs, tolerance %.0f%%" % (time.time() - t0, tol * 100))
    if ctrl_bad:
        print("\nThe 0.05 diffuse reference plate did not read 0.05. The\n"
              "measurement chain itself has moved, so no other number in this\n"
              "run means anything. Fix this before looking at the drifts above.")
        sys.exit(1)
    if bad:
        print("\n%d locked value(s) moved. Either the change was intended --"
              % len(bad))
        print("in which case say what moved and why, then re-freeze -- or a")
        print("reported number has just become wrong. Do not report anything")
        print("measured after this until it is resolved.")
        sys.exit(1)
    print("PASS -- the measurement chain and the geometry are unchanged")


if __name__ == "__main__":
    main()
