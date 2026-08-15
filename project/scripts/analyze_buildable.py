"""
Both rankings, with the error bars that decide whether either is a ranking.

    python3 scripts/analyze_buildable.py            # plain python3, no Blender

**Ranking 1 — darkness.** worst rho_dh over theta 0/+-20/+-40, then worst over
the three coating diffuse fractions, then **mean +/- SEM over the geometry
seeds**. The seeds are the point. A single seed put the top 13 designs inside
1.09x while the measured geometry-realisation spread is ~3.5%, so most of that
order was one draw of `seed = 23` and not a property of the designs. Anything
whose intervals overlap the leader is reported as tied, not ranked.

**Ranking 2 — form destruction.** rms smear against the flat control in the same
frame, at theta +/-40. This is the project's stated FIRST priority and no
ranking before 2026-08-13 measured it at all.

Baselines, named, both from measurement in this project:

    flat plate of the SAME coating, worst over theta and material   6.1218 %
    0.05 matte black wall (the control in every frame)              5.0000 %

The first is the one that matters: it is what the same paint on a flat panel
would do, so the ratio against it is what the STRUCTURE bought. 30x, for the
best design. Between the nine topologies the spread is 1.6x -- having a
structure is decisive, which structure is nearly irrelevant.
"""

import sys
import os
import csv
import json
import math
import collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
# Flat plate of the SAME coating, worst over theta 0/+-20/+-40 and over the
# three diffuse fractions. MEASURED with the same construction the coating fit
# was validated with -- a solid slab (ridge family, depth 0.001) rendered
# through `BR.run`, not `make_flat_plate`.
#
# The previous value here was 0.061218 and it was WRONG BY 5.4x. It came from a
# bare single-sided plane built by `make_flat_plate`: with no volume the face
# normal is undetermined, the Fresnel node saturates on the backface, and the
# specular term pins itself at `spec_scale` = 6.05%. The giveaway was that 45
# and 60 degrees read identical to four decimals -- a constant, not physics.
# `make_diffuse` has no Fresnel node, so the 0.05 control in every render is
# unaffected, and a rho=0 plate still reads exactly 0 at every angle.
#
# Cross-checked three ways: this render (1.1413%), an independent analytic
# reconstruction of make_coating (1.141%), and `scripts/fit_coating.py`
# reproducing the published Musou Black curve to 9.5% worst-case over 0-80.
#
# CONSEQUENCE: "structure buys 28-30x" was wrong; it buys about 5.3x. That is
# also the figure this project had already published on 2026-08-12 against
# rho_dh(0) = 0.00998. No measurement was ever taken at the moment the
# denominator changed to 0.061218.
FLAT_COATING_WORST = 0.011413
WALL = 0.05
MATS = ("d00", "d76", "d100")
NTH = 5

# The minimum feature each named process can actually hold, and the reason.
# EVERY ranking in this project must print this next to the number. The same
# error has now put an unmanufacturable design at the top of a ranking three
# times -- a 0.05 mm knife edge, an 8x tip mismatch, and CELLNEST's 0.1 mm wall
# 50 mm tall (1:500) labelled "print". An optimiser walks to the edge of
# whatever box it is given; if the box is not printed beside the result, the
# ranking is of the box and not of the designs. See JOURNAL.md.
PROCESS_FLOOR = {
    # 0.03 mm foil is made and sold, but the panel has to survive being carried
    # and mounted, and the user set the handling floor directly: "벌집셀도
    # 두께가 0.05~0.1 이 될수 있어. 너무 얇으면 손으로 쉽게 찌그러지니."
    # The floor is therefore 0.05, not the process minimum. Raising it demotes
    # the two designs that led the darkness ranking -- ST_comb-comb_50 and
    # CB_p0317_f040_x10, both 0.04 mm -- which is exactly why the constraint
    # has to live in the table and not in a sentence someone might skip.
    "expanded foil":   (0.05, "expanded aluminium foil; 0.03 is sold but "
                              "crushes by hand, so 0.05 is the handling floor"),
    "sheet, parallel": (0.05, "laser-cut / folded sheet"),
    "sheet, lanced":   (0.05, "laser-cut, lanced, bent, spot-welded sheet"),
    # slotted together like an egg crate: notches cut halfway through two sets
    # of strips, pushed together. No base plate, no welding. Missing from this
    # table for one build, which made every grid design return `None` from
    # buildable() and silently dropped them from "best that can be made" --
    # the report then named the cone, which is 4th on darkness.
    "sheet, grid":     (0.05, "notched strips slotted together, no welding"),
    # A pressed sheet is a die and a press: the die can hold a sharper edge
    # than a mould can fill, but not sharper than the sheet is thick. Missing
    # from this table until 2026-08-14, which made every phase 4 pyramid floor
    # return "process not characterised" the moment it was the binding feature.
    "press":           (0.10, "embossed sheet; apex flat >= sheet thickness"),
    "mould":           (0.40, "moulded cone tip; sharper buys 7% and loses "
                              "robustness, cleanability and mould filling"),
    "print":           (0.40, "FDM, one nozzle width"),
}


# which process makes each layer type, and how to read its thinnest solid
# dimension out of that layer's parameters
LAYER_PROCESS = {
    "comb":      ("expanded foil", ("wall_top", "wall_bot")),
    "honeycomb": ("expanded foil", ("wall_top", "wall_bot")),
    "cone":      ("mould",         ("tip_radius",)),
    "shingle":   ("sheet, grid",   ("plate_t_top", "plate_t_bot")),
    "truss":     ("sheet, lanced", ("wall_top", "wall_bot")),
}


def stack_process(row):
    """(process, feature) for a stacked design, derived from its geometry.

    A stack is two products bolted together, so it has two processes and two
    minimum features, and `sweep_stack.py` records only one of each -- it wrote
    "mould + foil / 0.40" for a design containing a 0.08 mm honeycomb wall,
    which is not that design's minimum feature at all. Taking the recorded pair
    at face value would let a stack pass a floor that one of its layers misses.

    So both layers are read back out of params_json and the binding one wins:
    the thinnest solid dimension anywhere in the stack, tagged with the process
    that has to produce it. `tip_radius` is a radius; the mould sees the tip
    diameter, the same convention the cone family is scored on elsewhere.
    """
    prm = json.loads(row["params_json"])
    worst = None
    for side in ("top", "bot"):
        kind = prm.get(side)
        proc, keys = LAYER_PROCESS.get(kind, (None, ()))
        if proc is None:
            return "process not characterised", ""
        lp = prm.get("%s_params" % side, {})
        vals = [float(lp[k]) * (2.0 if k == "tip_radius" else 1.0)
                for k in keys if k in lp]
        if not vals:
            return "process not characterised", ""
        f = min(vals)
        if worst is None or f < worst[1]:
            worst = (proc, f)
    return worst[0], "%.2f" % worst[1]


def buildable(process, feature):
    """(ok, note). `feature` is the minimum solid dimension in mm."""
    try:
        f = float(feature)
    except (TypeError, ValueError):
        return None, "feature not recorded"
    floor, why = PROCESS_FLOOR.get(process, (None, "process not characterised"))
    if floor is None:
        return None, why
    return (f >= floor - 1e-9), "%s floor %.2f mm" % (process, floor)


def darkness():
    """Every buildable-comparison row, from BOTH sweeps.

    `sweep_blade.csv` was added when the blade array had to be re-measured at
    constant thickness, and reading only `sweep_buildable.csv` silently dropped
    it: the design appeared in the report gallery with rank "—" on darkness
    while its number was being quoted by hand in the summary. A candidate that
    cannot be ranked must not be reportable -- see `check_candidates_ranked`
    in gate_sweep.py, added for exactly this.
    """
    rows = []
    # EVERY sweep that produces a buildable-comparison row belongs here. Two
    # designs have now been silently dropped by this list being short: the
    # blade array (sweep_blade.csv) and the commercial honeycomb
    # (sweep_comb.csv). gate_sweep check 6 exists because of the first and
    # caught the second before the report shipped.
    for name in ("sweep_buildable.csv", "sweep_blade.csv", "sweep_comb.csv",
                 "sweep_stack.csv"):
        path = os.path.join(RESULTS, name)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path)):
            # sweep_blade has no process/feature columns; fill them from what
            # the design actually is, so the process-floor check still applies
            r.setdefault("process", "sheet, grid"
                         if r.get("azimuth_mode") == "grid" else
                         "sheet, parallel" if r.get("azimuth_mode") == "parallel"
                         else "sheet, lanced")
            r.setdefault("feature", r.get("thickness", ""))
            r.setdefault("topology", "shingle")
            if r.get("family") == "stack":
                r["process"], r["feature"] = stack_process(r)
            rows.append(r)
    per = collections.defaultdict(dict)
    meta = {}
    for r in rows:
        key = (r["tag"], r["diffuse_frac"])
        per[key][float(r["theta"])] = float(r["rho"])
        meta[r["tag"]] = r
    # worst over theta, then over material, per (design, seed)
    score = {}
    for (tag, mat), d in per.items():
        if len(d) == NTH:
            score.setdefault(tag, {})[mat] = max(d.values())
    score = {t: max(v.values()) for t, v in score.items() if len(v) == len(MATS)}

    # collapse the seed out of the tag: ..._s23 / _s101 ...
    byd = collections.defaultdict(list)
    for tag, s in score.items():
        base = tag.rsplit("_s", 1)[0]
        byd[base].append(s)
    out = []
    for base, vals in byd.items():
        n = len(vals)
        m = sum(vals) / n
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
        sem = sd / math.sqrt(n) if n > 1 else float("nan")
        any_tag = next(t for t in score if t.rsplit("_s", 1)[0] == base)
        out.append({"design": base, "n": n, "mean": m, "sd": sd, "sem": sem,
                    "cv": (sd / m if m else float("nan")),
                    "topology": meta[any_tag]["topology"],
                    "process": meta[any_tag]["process"],
                    "pitch": float(meta[any_tag]["pitch"]),
                    "feature": meta[any_tag]["feature"]})
    return sorted(out, key=lambda r: r["mean"])


def form():
    path = os.path.join(RESULTS, "form_buildable.json")
    if not os.path.exists(path):
        return []
    out = []
    for e in json.load(open(path)):
        t = e["thetas"]
        a, b = t.get("-40"), t.get("+40")
        if not a or not b:
            continue
        smear = 0.5 * (a["rms_mm"] / a["rms_control_mm"]
                       + b["rms_mm"] / b["rms_control_mm"])
        z = t.get("+0", {})
        out.append({"design": e["tag"].rsplit("_s", 1)[0],
                    "topology": e["topology"], "process": e["process"],
                    "smear": smear,
                    # head-on peak: what a viewer standing in front actually
                    # receives. A THIRD axis, and the one the honeycomb fails
                    # -- it cuts total reflectance 5x while its head-on peak
                    # stays equal to a bare flat plate. Reporting only the
                    # other two reads as "just buy the honeycomb".
                    "peak0": z.get("peak_ratio_mean"),
                    "rms_m40": a["rms_mm"], "rms_p40": b["rms_mm"],
                    "rms_ctrl": a["rms_control_mm"],
                    "peak_m40": a["peak_ratio_mean"],
                    "peak_p40": b["peak_ratio_mean"],
                    "mtf20": a.get("mtf_20mm", float("nan"))})
    return sorted(out, key=lambda r: -r["smear"])


def main():
    dk = darkness()
    if not dk:
        sys.exit("no scored designs yet")
    seeds = dk[0]["n"]
    print("RANKING 1 — DARKNESS   (worst rho_dh over theta and material, "
          "mean +/- SEM over %d seed%s)" % (seeds, "" if seeds == 1 else "s"))
    print("baselines: flat plate of the same coating %.4f%%   plain black wall "
          "%.2f%%" % (100 * FLAT_COATING_WORST, 100 * WALL))
    print()
    lead = dk[0]
    print("%-3s %-26s %-16s %6s %10s %9s %8s %6s %s"
          % ("#", "design", "process", "feat", "rho_dh", "+/-SEM",
             "vs flat", "tie?", "build"))
    n_unbuildable = 0
    for i, r in enumerate(dk, 1):
        # "tie" means the design cannot be separated from the leader once the
        # geometry seed is treated as a random variable, which it is
        if r["n"] > 1 and lead["n"] > 1:
            se = math.sqrt(r["sem"] ** 2 + lead["sem"] ** 2)
            tie = "tied" if (r["mean"] - lead["mean"]) < 2.0 * se else ""
        else:
            tie = "n=1"
        ok, _ = buildable(r["process"], r["feature"])
        mark = "OK" if ok else ("**NO**" if ok is False else "?")
        if ok is False:
            n_unbuildable += 1
        print("%-3d %-26s %-16s %6s %9.4f%% %8.4f%% %7.1fx %6s %s"
              % (i, r["design"][2:], r["process"], r["feature"],
                 100 * r["mean"], 100 * r["sem"] if r["n"] > 1 else float("nan"),
                 FLAT_COATING_WORST / r["mean"], tie, mark))
    if n_unbuildable:
        print()
        print("!! %d of %d designs are below their own process floor and CANNOT "
              "BE MADE." % (n_unbuildable, len(dk)))
        print("   They are left in the table on purpose -- deleting them hides "
              "how much of the")
        print("   ranking is bought with feature size rather than with shape. "
              "See JOURNAL.md.")
        best = next((r for r in dk if buildable(r["process"], r["feature"])[0]),
                    None)
        if best:
            print("   Best design that CAN be made: %s (%s, %s mm) at %.4f%%, "
                  "%.1fx vs flat."
                  % (best["design"][2:], best["process"], best["feature"],
                     100 * best["mean"], FLAT_COATING_WORST / best["mean"]))
    if seeds > 1:
        cv = [r["cv"] for r in dk if r["n"] > 1]
        print()
        print("realisation spread across seeds: median CV %.2f%%, worst %.2f%%"
              % (100 * sorted(cv)[len(cv) // 2], 100 * max(cv)))

    fm = form()
    if fm:
        print()
        print("RANKING 2 — FORM DESTRUCTION   (smear vs the flat control in the "
              "same frame, theta +/-40)")
        print("%-3s %-26s %-12s %10s %9s %9s %8s"
              % ("#", "design", "topology", "smear", "peak-40", "peak+40",
                 "MTF20"))
        for i, r in enumerate(fm, 1):
            print("%-3d %-26s %-12s %9.2fx %9.5f %9.5f %8.3f"
                  % (i, r["design"][2:], r["topology"], r["smear"],
                     r["peak_m40"], r["peak_p40"], r["mtf20"]))
        print()
        print("smear 1.00x means the returned line is exactly as narrow as on a "
              "flat wall: form intact.")

        dpos = {r["design"]: i for i, r in enumerate(dk, 1)}
        print()
        print("THE TWO RANKINGS DISAGREE")
        print("%-26s %10s %8s" % ("design", "darkness", "form"))
        for i, r in enumerate(fm, 1):
            j = dpos.get(r["design"])
            if j:
                print("%-26s %10s %8s" % (r["design"][2:], "#%d" % j, "#%d" % i))


if __name__ == "__main__":
    main()
