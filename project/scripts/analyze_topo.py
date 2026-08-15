"""
Rank sweep_topo.csv the way the project scores designs, and flag what smells.

    python3 scripts/analyze_topo.py [csv]        # plain python3, no Blender

Scoring, identical to how sweep_shapes results are read (results/analysis_
shapes.md), so the two files are directly comparable:

    per design, per material:  worst rho over the 5 thetas
    combined score:            worst of that over d00 / d76 / d100

The combined rule exists because the coating's diffuse/specular split is the
dominant unmeasured parameter -- it moved designs by 2x to 41x and inverted the
ranking (metrics/01). A design that wins under one material is a bet; a design
that wins under both is a result.

BUT read the combined score knowing what it actually is. `coating_split(0.0)`
gives the specular arm a grazing ceiling of 24.95%, while `coating_split(1.0)`
is Lambertian at 0.998% with no angular rise at all. Splitting the two arms at
equal rho_dh(0) pins them at the one angle where they agree and lets them
diverge 25x everywhere else, so d00 sets the combined score for the large
majority of designs. This script prints which material set each score, so that
is visible rather than hidden.

Baselines, always named (metrics/01):
    flat plate of the same coating   rho_dh(0) = 0.00998
    0.05 matte black control          in every frame, printed from the CSV
"""

import sys
import os
import csv
import json
import math
import collections

FLAT_COATING_RHO0 = 0.00998        # blender_render.MUSOU_RHO0
MATS = ("d00", "d76", "d100")


def load(path):
    rows = list(csv.DictReader(open(path)))
    if not rows:
        sys.exit("no rows in %s" % path)
    return rows


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "sweep_topo.csv")
    rows = load(path)

    per = collections.defaultdict(dict)      # (tag, mat) -> {theta: rho}
    meta = {}
    ctrl = []
    for r in rows:
        per[(r["tag"], r["diffuse_frac"])][float(r["theta"])] = float(r["rho"])
        meta[r["tag"]] = r
        ctrl.append(float(r["control"]))

    worst = collections.defaultdict(dict)    # tag -> mat -> worst rho
    for (tag, mat), d in per.items():
        if len(d) == 5:                      # only complete runs are scored
            worst[tag][mat] = max(d.values())

    complete = {t: v for t, v in worst.items() if len(v) == len(MATS)}
    partial = len(worst) - len(complete)

    print("%s" % path)
    print("rows %d   designs scored %d   partial %d   control mean %.5f"
          % (len(rows), len(complete), partial,
             sum(ctrl) / len(ctrl)))
    print("baseline: flat plate of the same coating, rho_dh(0) = %.5f"
          % FLAT_COATING_RHO0)
    print()

    # --- ranking ---------------------------------------------------------
    ranked = sorted(complete.items(), key=lambda kv: max(kv[1].values()))
    print("%-4s %-30s %-10s %8s %8s %8s %9s %6s %7s"
          % ("#", "tag", "topology", "d00", "d76", "d100",
             "COMBINED", "set by", "vs flat"))
    for i, (tag, v) in enumerate(ranked, 1):
        comb = max(v.values())
        setter = max(v, key=lambda m: v[m])
        print("%-4d %-30s %-10s %8.5f %8.5f %8.5f %9.5f %6s %6.2fx"
              % (i, tag, meta[tag]["topology"], v["d00"], v["d76"], v["d100"],
                 comb, setter, FLAT_COATING_RHO0 / comb))
    print()

    # --- best per topology, and the cone reference ------------------------
    best = {}
    for tag, v in complete.items():
        topo = meta[tag]["topology"]
        c = max(v.values())
        if topo not in best or c < best[topo][1]:
            best[topo] = (tag, c)
    ref = best.get("cone", (None, float("nan")))[1]
    print("best per topology, against the cone measured in the same frame:")
    for topo, (tag, c) in sorted(best.items(), key=lambda kv: kv[1][1]):
        rel = c / ref if ref == ref and ref else float("nan")
        print("  %-10s %-30s %9.5f   %5.2fx the cone" % (topo, tag, c, rel))
    print()

    # --- the exposed-area law, tested rather than assumed -----------------
    # The law says head-on return ~= exposed_fraction x rho. Every design here
    # carries an analytic exposed-area estimate computed BEFORE it was
    # rendered, so the law can be checked directly instead of argued about.
    print("exposed-area law check   (head-on rho vs the pre-render estimate)")
    print("  %-30s %9s %10s %10s" % ("tag", "exposed%", "rho(0) d00", "ratio"))
    pts = []
    for tag, v in sorted(complete.items(),
                         key=lambda kv: float(meta[kv[0]]["exposed_est"])):
        e = float(meta[tag]["exposed_est"])
        r0 = per[(tag, "d00")].get(0.0)
        if r0 is None or e <= 0:
            continue
        pts.append((e, r0, tag))
    if pts:
        e0, r0_0, _ = pts[0]
        show = pts if len(pts) <= 12 else pts[:6] + pts[-6:]
        for e, r0, tag in show:
            # ratio = how much brighter it actually got, divided by how much
            # brighter the area law says it should have got. 1.0 = law holds.
            print("  %-30s %9.4f %10.5f %10.2f"
                  % (tag, 100 * e, r0, (r0 / r0_0) / (e / e0)))
        # If the law held, rho(0) would be proportional to exposed area and
        # this correlation would be near +1 on the logs.
        n = len(pts)
        lx = [math.log(p[0]) for p in pts]
        ly = [math.log(p[1]) for p in pts]
        mx, my = sum(lx) / n, sum(ly) / n
        sxy = sum((a - mx) * (b - my) for a, b in zip(lx, ly))
        sxx = sum((a - mx) ** 2 for a in lx)
        syy = sum((b - my) ** 2 for b in ly)
        if sxx > 0 and syy > 0:
            print("  log-log slope %.3f (law predicts 1.0), r = %.3f, n = %d"
                  % (sxy / sxx, sxy / math.sqrt(sxx * syy), n))
    print()

    # --- smells -----------------------------------------------------------
    # Same checks that found four real defects in this project. Every one of
    # them presented as a surprising result first.
    print("flags")
    bad = 0
    for (tag, mat), d in sorted(per.items()):
        if len(d) != 5:
            print("  INCOMPLETE %s %s: %d thetas" % (tag, mat, len(d)))
            bad += 1
    cmean = sum(ctrl) / len(ctrl)
    for r in rows:
        if float(r["rho"]) > cmean:
            print("  ABOVE THE 0.05 CONTROL: %s %s th%+.0f  rho %.5f"
                  % (r["tag"], r["diffuse_frac"], float(r["theta"]),
                     float(r["rho"])))
            bad += 1
    # +theta / -theta should be statistically identical: nothing here is tilted.
    # A systematic bias means a lattice-sampling problem, not noise.
    for tag, v in complete.items():
        for mat in MATS:
            d = per[(tag, mat)]
            for t in (20.0, 40.0):
                a, b = d.get(t), d.get(-t)
                if a and b and abs(a / b - 1.0) > 0.08:
                    print("  ASYMMETRY %s %s +/-%.0f: %.5f vs %.5f (%.1f%%)"
                          % (tag, mat, t, a, b, 100 * (a / b - 1)))
                    bad += 1
    if not bad:
        print("  none")


if __name__ == "__main__":
    main()
