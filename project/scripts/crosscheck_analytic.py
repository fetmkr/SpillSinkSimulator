"""
Predict the render without rendering, then see how wrong it is.

    python3 scripts/crosscheck_analytic.py        # no Blender, no GPU

WHY. Every number in this project comes from one path tracer. Gate check 8
compares sweeps to other sweeps, which catches drift but cannot catch a shared
mistake -- if Cycles, or the way this harness drives it, is wrong in some
systematic way, nothing here would notice. Stray-light practice cross-traces
identical rays between independent codes for exactly this reason.

A second renderer is the eventual answer. This is the cheap version of the same
idea: a closed-form model that uses ONLY geometry and one flat-plate number,
shares no code with the renderer, and can be checked in a second.

THE MODEL. At normal incidence a cavity returns light by two routes:

    1. the ENTRANCE. Whatever solid material faces the viewer at the mouth --
       cell wall tops, cone tips, blade edges -- is a flat surface one bounce
       away. It returns f_exposed * rho_flat, and it returns it undeflected.
    2. the INTERIOR. A ray that misses the solid enters the cavity, bounces n
       times against walls at near-grazing incidence, and leaves carrying
       rho^n. For a coating at 1 % and a cavity deep enough to force even two
       bounces, that is 1e-4 of what entered -- negligible beside route 1.

So the prediction is simply

    rho_dh(0)  ~=  f_exposed * rho_flat(0)

with f_exposed computed by each geometry module's own
`exposed_fraction_est()`, written long before this check existed and for a
different purpose.

WHAT A DISAGREEMENT WOULD MEAN. If measured >> predicted, the interior is
returning more than the two-bounce argument allows -- either the cavity is
shallower than it looks, or the walls are not catching what they should. If
measured << predicted, the exposed estimate is too pessimistic: real tips are
rounded and shadowed. Either way the RATIO across families is the interesting
part, because a constant offset is a calibration and a varying one is a
mechanism.
"""

import sys
import os
import csv
import json
import math
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

# Flat plate of the same coating at normal incidence. Measured, not typed:
# `analyze_buildable.FLAT_COATING_WORST` is the worst over angle and material;
# at theta = 0 the same render reads rho_dh(0), which is the coating's own
# fitted constant.
RHO_FLAT_0 = 0.00998


def exposed(family, params):
    """Ask the geometry module itself. No duplicate of its arithmetic here."""
    p = dict(params)
    try:
        if "top" in p:                       # a stack: only the top is exposed
            import geom_stack as ST
            return ST.StackParams(**p).exposed_fraction_est()
        if family == "cone3d" or "tip_radius" in p:
            import geom3d as G3
            return G3.Cone3DParams(**p).tip_fraction()
        if "topology" in p:
            import geom_topo as GT
            return GT.TopoParams(**p).exposed_fraction_est()
        if "variant" in p:
            import geom_cell as GC
            return GC.CellParams(**p).exposed_fraction_est()
        if "tip_width" in p:                 # 1D V-groove: the lip is the tip
            return float(p["tip_width"]) / float(p.get("pitch_mean", 1.0))
    except Exception:
        return None
    return None


def measured_theta0():
    """rho_dh at theta = 0, worst over coating, mean over seeds, per design."""
    import glob
    out = {}
    for path in sorted(glob.glob(os.path.join(RESULTS, "sweep_*.csv"))):
        if "__void__" in path:
            continue
        try:
            rows = list(csv.DictReader(open(path)))
        except Exception:
            continue
        if not rows or "params_json" not in rows[0] or "rho" not in rows[0]:
            continue
        z = collections.defaultdict(lambda: collections.defaultdict(list))
        meta = {}
        for r in rows:
            if abs(float(r["theta"])) > 1e-9:
                continue
            # only the coating the study runs at; roughness variants excluded
            if r.get("roughness") and abs(float(r["roughness"]) - 0.30) > 1e-9:
                continue
            if r.get("phi") and abs(float(r["phi"])) > 1e-9:
                continue
            b = r["tag"].rsplit("_s", 1)[0]
            z[b][r["diffuse_frac"]].append(float(r["rho"]))
            meta[b] = r
        for b, m in z.items():
            if len(m) == 3:
                out[b] = (max(sum(v) / len(v) for v in m.values()),
                          meta[b], os.path.basename(path))
    return out


def main():
    got = measured_theta0()
    rows = []
    for design, (rho, meta, src) in sorted(got.items()):
        try:
            prm = json.loads(meta["params_json"])
        except Exception:
            continue
        f = exposed(meta.get("family", ""), prm)
        if not f or f <= 0:
            continue
        pred = f * RHO_FLAT_0
        rows.append((design, meta.get("topology", "?"), f, pred, rho,
                     rho / pred, src))
    if not rows:
        print("no comparable designs found")
        return 1

    rows.sort(key=lambda r: r[5])
    print("=" * 78)
    print("ANALYTIC vs RENDERED, normal incidence")
    print("  prediction = exposed_fraction x rho_flat(0),  rho_flat(0) = %.5f"
          % RHO_FLAT_0)
    print("=" * 78)
    print("  %-28s %8s %10s %10s %7s" % ("design", "exposed", "predicted",
                                         "rendered", "ratio"))
    for d, topo, f, pred, rho, ratio, src in rows:
        print("  %-28s %7.2f%% %9.5f%% %9.5f%% %6.2fx"
              % (d[:28], 100 * f, 100 * pred, 100 * rho, ratio))
    r = [x[5] for x in rows]
    r.sort()
    med = r[len(r) // 2]
    lo, hi = r[0], r[-1]
    print("-" * 78)
    print("  %d designs   median ratio %.2fx   range %.2f - %.2f  (%.1fx wide)"
          % (len(r), med, lo, hi, hi / lo))
    print()
    if hi / lo < 3.0:
        print("  The offset is roughly CONSTANT across families, so the two")
        print("  methods agree on the mechanism and differ by a calibration:")
        print("  the exposed-area estimate is systematically %.2fx off."
              % med)
    else:
        print("  The offset VARIES by %.1fx across families, so exposed area"
              % (hi / lo))
        print("  alone does not explain normal-incidence return -- something")
        print("  family-dependent is missing from the model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
