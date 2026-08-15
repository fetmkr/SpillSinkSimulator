"""Q8: can the winning blade array actually be assembled from sheet metal?

    Blender --background --factory-startup --python scripts/sweep_blade_fit.py

WHY THIS ONE. `results/QUESTIONS.md` Q8 is still tagged `[추측]` -- nobody has
checked it -- and it asks the only question about the three-axis winner that
does not need a renderer to answer: **330 blades 6.3 mm wide, dropped at 5.5 mm
spacing with random azimuth, must physically collide.** `geom_topo` says so
itself at the point where it builds them: *"overlap is free: the union is the
geometry"*. In a union of solids that is true. In 0.05 mm steel it is not --
two plates cannot occupy the same space -- and `SAMPLES.md` sends the supplier a
drawing with no mention of it.

The blade neighbourhood at tilt / azimuth / pitch is already swept
(`sweep_bladehood.csv`, 27 designs). What was never asked is whether the point
that sweep picked can be built, and what it costs optically to make it
buildable. That is worth more than another parameter around a design that may
not exist.

WHAT IS COUNTED. Each blade hangs from a top edge of length `plate_over *
pitch`, centred on a jittered lattice point, running along its azimuth, leaning
by `tilt`. At any depth its cross-section is that same segment displaced by the
lean. Two blades interfere if their cross-sections cross at any shared depth,
within their combined half-thickness. The count is over the whole field, and
the interference-free limit is the largest `plate_over` at which it is zero.

    PREDICTION 1. At the published `plate_over = 1.15` with `azimuth_mode
    = grid`, interference is NOT zero and is not small. The blade is 6.325 mm
    across on a 5.5 mm lattice with 0.30 jitter, and a grid azimuth makes half
    the blades perpendicular to the other half, which is the worst case for
    crossing: any two perpendicular neighbours whose centres are closer than
    half a blade must cross. I expect **30-60 % of blades involved in at least
    one collision**.

    PREDICTION 2. The interference-free limit is near `plate_over = 1.0` for a
    grid azimuth, and BELOW 1.0 for random azimuth, because a random angle
    removes the protection a shared orientation gives. If the limit turns out
    to be above 1.15 the premise of Q8 is wrong and this ends here.

    PREDICTION 3. Enforcing it costs total reflectance. `plate_over > 1` is
    what makes a blade cover the mouth its neighbour left open; at 1.0 the
    array becomes a set of separate plates with a clear line of sight to the
    floor between them, so rho_dh at normal incidence should RISE. Phase 3
    measured 1.15 against 1.45 and found 1.15 better on all four numbers, which
    says the trend is not monotonic and gives no guide to what happens below
    1.0. I will guess a **10-40 % rise** and hold it loosely.

    If prediction 3 fails and the optical cost is negligible, the buildable
    array is simply the better design and the study should move to it.

THE ANCHOR. `BH_p055_t02_grid_s23` is re-measured here under the study's
standard protocol with the identical `params_json` that `sweep_bladehood.csv`
recorded, so gate check 8 has a design in common between the two files.
"""

import sys
import os
import csv
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUT = "/tmp/bladefit"
CSV = os.path.join(RESULTS, "sweep_bladefit.csv")

FACE, DEPTH, FDEPTH = 60.0, 50.0, 3.0
PITCH = 5.5
OVERS = (0.70, 0.80, 0.90, 0.95, 1.00, 1.05, 1.15, 1.30, 1.45)
MODES = ("grid", "random", "parallel")
DEPTH_SAMPLES = 5          # cross-sections down the blade

COLS = ["tag", "family", "topology", "process", "feature", "seed",
        "diffuse_frac", "plate_over", "azimuth_mode", "blades", "collisions",
        "blades_hit", "hit_frac", "theta", "rho", "control", "params_json"]


# --- geometry: does this field of blades physically fit? -------------------

def blade_segments(over, mode, pitch=PITCH, face=FACE, tilt_deg=2.0,
                   jitter=0.30, seed=23, depth=DEPTH - FDEPTH,
                   azimuth_jitter=180.0, margin_depths=0.0):
    """Top-edge segments and lean, exactly as `_build_shingle` lays them out."""
    import geom_topo as GT
    p = GT.TopoParams(topology="shingle", face_w=face, face_h=face,
                      depth=depth, pitch=pitch, plate_over=over,
                      plate_t_top=0.05, plate_t_bot=0.05, tilt_deg=tilt_deg,
                      tilt_jitter=0.0, azimuth_mode=mode, jitter=jitter,
                      azimuth_jitter=azimuth_jitter,
                      margin_depths=margin_depths,
                      backing=2.0, seed=seed)
    rng = GT._lcg(p.seed * 31 + 7)
    half = 0.5 * p.plate_over * p.pitch
    out = []
    for cx, cz in GT._centres(p):
        m = p.margin()
        if not (-m - pitch <= cx <= face + m + pitch and
                -face / 2 - m - pitch <= cz <= face / 2 + m + pitch):
            # still consume the stream so the layout matches the mesh exactly
            next(rng)
            next(rng)
            continue
        if p.azimuth_mode == "grid":
            az = (math.pi / 2.0) if next(rng) < 0.5 else 0.0
        elif p.azimuth_mode == "parallel":
            az = 0.0
            next(rng)
        else:
            az = math.radians((2.0 * next(rng) - 1.0) * p.azimuth_jitter)
        tl = math.radians(max(0.0, min(85.0, p.tilt_deg
                                       + (2.0 * next(rng) - 1.0)
                                       * p.tilt_jitter)))
        e = (math.cos(az), math.sin(az))
        lean = (-math.sin(az), math.cos(az))
        out.append({"c": (cx, cz), "e": e, "lean": lean,
                    "half": half, "tan": math.tan(tl)})
    return out, p


def _cross(a, b, c):
    return ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))


def _segments_cross(p1, p2, q1, q2):
    d1 = _cross(q1, q2, p1)
    d2 = _cross(q1, q2, p2)
    d3 = _cross(p1, p2, q1)
    d4 = _cross(p1, p2, q2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def count_interference(blades, depth=DEPTH - FDEPTH, nd=DEPTH_SAMPLES):
    """Pairs whose cross-sections cross at any shared depth."""
    n = len(blades)
    # bucket by centre so the pair test is local; a blade cannot reach further
    # than its own half-length plus the lean
    reach = max(b["half"] + depth * b["tan"] for b in blades) if blades else 0.0
    cell = max(reach * 2.0, 1e-6)
    buckets = {}
    for i, b in enumerate(blades):
        key = (int(b["c"][0] / cell), int(b["c"][1] / cell))
        buckets.setdefault(key, []).append(i)

    hits = set()
    pairs = 0
    seen_pairs = set()
    for (kx, kz), idxs in buckets.items():
        near = []
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                near.extend(buckets.get((kx + dx, kz + dz), ()))
        for i in idxs:
            for j in near:
                if j <= i:
                    continue
                if (i, j) in seen_pairs:
                    continue
                seen_pairs.add((i, j))
                a, b = blades[i], blades[j]
                for s in range(nd):
                    y = depth * s / max(nd - 1, 1)
                    oa = (a["c"][0] + a["lean"][0] * y * a["tan"],
                          a["c"][1] + a["lean"][1] * y * a["tan"])
                    ob = (b["c"][0] + b["lean"][0] * y * b["tan"],
                          b["c"][1] + b["lean"][1] * y * b["tan"])
                    a1 = (oa[0] - a["half"] * a["e"][0],
                          oa[1] - a["half"] * a["e"][1])
                    a2 = (oa[0] + a["half"] * a["e"][0],
                          oa[1] + a["half"] * a["e"][1])
                    b1 = (ob[0] - b["half"] * b["e"][0],
                          ob[1] - b["half"] * b["e"][1])
                    b2 = (ob[0] + b["half"] * b["e"][0],
                          ob[1] + b["half"] * b["e"][1])
                    if _segments_cross(a1, a2, b1, b2):
                        pairs += 1
                        hits.add(i)
                        hits.add(j)
                        break
    return {"blades": n, "collisions": pairs, "blades_hit": len(hits),
            "hit_frac": len(hits) / max(n, 1)}


# --- optics: what does it cost to make it buildable? -----------------------

def measure_case(over, mode, tag, seed=23):
    import blender_render as BR
    from cone3d_sweep import COAT
    rows = []
    tp = {"azimuth_mode": mode, "jitter": 0.3, "pitch": PITCH,
          "plate_over": over, "plate_t_bot": 0.05, "plate_t_top": 0.05,
          "tilt_deg": 2.0, "tilt_jitter": 0.0}
    # RECORD THE PARAMETER THAT CHANGED THE GEOMETRY. `geom_floor.margin_min`
    # was added this session so a shaped floor reaches the tube standing on it;
    # for a blade field at face 60 the tube overhangs by 103.42 mm against the
    # 100.00 mm the old rule gave, so the floor grew by 3.42 mm and every
    # blade-stack measurement moved by up to 0.76 %. Leaving it out of
    # `params_json` would let gate check 8 compare these rows against
    # `sweep_bladehood.csv` as if they were the same geometry -- the exact
    # failure `plate_over` caused. Recorded, the gate reports them as measuring
    # different things, which is true.
    prm = {"backing": 2.0, "bot": "pyramid", "bot_depth": FDEPTH,
           "bot_params": {"margin_depth_ref": DEPTH, "pitch": 2.0,
                          "tip_flat": 0.1},
           "face_h": FACE, "face_w": FACE, "margin_depths": 2.0, "seed": seed,
           "top": "shingle", "top_depth": DEPTH - FDEPTH, "top_params": tp}
    for mat, df in (("d00", 0.0), ("d76", 0.76), ("d100", 1.0)):
        body, spec = BR.coating_split(df)
        for th in (0.0, -20.0, 20.0, -40.0, 40.0):
            cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th), "family": "stack",
                   "out_dir": OUT, "results_dir": OUT, "samples": 64,
                   "res_x": 480, "res_y": 220, "gpu": True,
                   "spec_roughness": 0.30, "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": th}],
                   "material_mode": "coating",
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": 0.30}}
            cfg.update({k: v for k, v in COAT.items()
                        if k != "spec_roughness"})
            res = BR.run(cfg)
            rec = list(res["modes"].values())[0]
            rows.append({"mat": mat, "theta": th,
                         "rho": rec["panel"]["mean"],
                         "control": rec["control"]["mean"],
                         "params_json": json.dumps(prm, sort_keys=True)})
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 76)
    print("Q8: DOES THE BLADE ARRAY FIT? interference count over the field")
    print("=" * 76)
    print("  %8s %10s %9s %12s %12s %10s"
          % ("over", "mode", "blades", "collisions", "blades hit", "hit %"))
    geo = {}
    for mode in MODES:
        for over in OVERS:
            b, _p = blade_segments(over, mode)
            r = count_interference(b)
            geo[(mode, over)] = r
            print("  %8.2f %10s %9d %12d %12d %9.1f%%"
                  % (over, mode, r["blades"], r["collisions"],
                     r["blades_hit"], 100 * r["hit_frac"]), flush=True)
        print()

    limit = {}
    for mode in MODES:
        ok = [o for o in OVERS if geo[(mode, o)]["collisions"] == 0]
        limit[mode] = max(ok) if ok else None
        print("  %-9s interference-free up to plate_over = %s"
              % (mode, limit[mode] if limit[mode] else "none of the range"))

    # --- optical cost, plus the anchor -------------------------------------
    cases = [(1.15, "grid", "BH_p055_t02_grid_s23")]          # the anchor
    for mode in ("grid",):
        lo = limit.get(mode)
        if lo and abs(lo - 1.15) > 1e-9:
            cases.append((lo, mode, "BF_over%03d_%s_s23"
                          % (round(lo * 100), mode)))
    print("\n  measuring %d case(s) under the standard protocol" % len(cases))

    rows = []
    for over, mode, tag in cases:
        print("   %s  over %.2f %s" % (tag, over, mode), flush=True)
        g = geo[(mode, over)]
        for r in measure_case(over, mode, tag):
            rows.append({"tag": tag, "family": "stack",
                         "topology": "shingle/pyramid", "process": "sheet",
                         "feature": 0.05, "seed": 23,
                         "diffuse_frac": r["mat"], "plate_over": over,
                         "azimuth_mode": mode, "blades": g["blades"],
                         "collisions": g["collisions"],
                         "blades_hit": g["blades_hit"],
                         "hit_frac": round(g["hit_frac"], 5),
                         "theta": r["theta"], "rho": r["rho"],
                         "control": r["control"],
                         "params_json": r["params_json"]})

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nwrote %s  (%d rows)" % (CSV, len(rows)))

    by = {}
    for r in rows:
        by.setdefault(r["tag"], []).append(r["rho"])
    print("\n  %-26s %12s %12s" % ("design", "worst rho", "vs anchor"))
    base = max(by.get("BH_p055_t02_grid_s23", [float("nan")]))
    for tag, v in by.items():
        w = max(v)
        print("  %-26s %11.5f%% %11s"
              % (tag, 100 * w,
                 "-" if tag.startswith("BH_") else "%+.1f%%"
                 % (100 * (w - base) / base)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
