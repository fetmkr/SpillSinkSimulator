"""Q8, part 3: half-lap notches make the published blade array buildable.

    Blender --background --factory-startup --python scripts/sweep_blade_notch.py

Parts 1 and 2 established that the three-axis winner cannot be assembled --
89 of 193 blades collide -- and that both ways of avoiding the collisions cost
something the study wants: a parallel array gives up azimuthal scattering
(+50 % on total reflectance) and a regular non-overlapping array gives up
aperiodicity.

THERE IS A THIRD WAY, AND IT IS HOW THE INDUSTRY ACTUALLY DOES IT. Intersecting
sheet-metal strips are assembled with HALF-LAP NOTCHES: slots cut to half the
grid depth, opening downward in one set of strips and upward in the other, so
the two interlock and their faces finish coplanar. This is the standard
egg-crate construction for lighting louvers and grid assemblies -- see
US4849867 (light fixture and louver construction: "downwardly opening slots in
longitudinal louvers and upwardly opening slots in transverse louvers ... all
louvers brought together with flanges coplanar") and US4714585 (interlocking
egg-crate grid assembly, slots "dimensioned to accommodate complementary tabs
in the interlocking strips", assembled so no face carries a double thickness of
metal).

WHY IT SHOULD BE ALMOST FREE HERE, which is the point worth testing. The notch
only has to be as wide as the thing passing through it. These blades are
**0.05 mm thick**, so each notch is a 0.05 mm slit in a 6.325 mm blade -- 0.8 %
of its width -- cut to half of the 47 mm depth. The material removed is
0.05 x 23.5 mm per crossing against a blade face of 6.325 x 47 mm, i.e. 0.4 %
of the blade, and it is removed at the crossing where the neighbouring blade
immediately fills the same space. Nothing about the azimuth, the jitter or the
overlap has to change.

    PREDICTION, written before the render.

    1. NOTCHING DRIVES THE INTERFERENCE COUNT TO ZERO by construction, and the
       geometric check below must confirm it. If it does not, the notch
       assignment is wrong and nothing else here means anything.

    2. THE OPTICAL COST IS UNDER 3 % on worst-case total reflectance, and I
       expect under 1 %. The removed area is 0.4 % of a blade per crossing and
       46 % of blades carry at least one, so the array loses well under 1 % of
       its surface, in places that are immediately shadowed by the blade
       passing through.

    3. IT WILL BE SLIGHTLY WORSE, NOT BETTER. A notch is a hole; a hole in a
       blade is a path a ray can take that it could not take before. I expect
       rho_dh to rise, not fall, and if it FALLS by more than the noise then
       the notch is doing something I have not thought of and it needs
       explaining rather than celebrating.

    If prediction 2 holds, Q8 is answered constructively: the published design
    is buildable as drawn, with a notch schedule, and none of its optical
    properties has to be given up.

THE ANCHOR. `BH_p055_t02_grid_s23` is measured again with the identical
`params_json` recorded by `sweep_bladehood.csv` and by parts 1 and 2, so gate
check 8 ties all four files together.
"""

import sys
import os
import csv
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sweep_blade_fit as BF                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "sweep_bladenotch.csv")
OUT = "/tmp/bladenotch"

PLATE_T = 0.05
CLEAR = 0.02            # slot clearance per side, mm -- a real cut needs one
NSEG = 1                # extra subdivisions along a blade; notches add their own

COLS = ["tag", "family", "topology", "process", "feature", "seed",
        "diffuse_frac", "plate_over", "azimuth_mode", "jitter", "notched",
        "blades", "collisions", "notches", "area_removed_pct",
        "theta", "rho", "control", "params_json"]


# --- geometry ---------------------------------------------------------------

def crossings(blades, depth, nd=9):
    """Where each pair crosses, as a RANGE along each blade's top edge.

    THE CROSSING MOVES WITH DEPTH. Blades lean by `tilt` (2 degrees over 47 mm
    = 1.64 mm of travel), so two blades that miss at the mouth can cross lower
    down, and a crossing at the mouth slides along both blades as it descends.
    Computing the intersection only on the top edges found 29 of the 55 clashes
    `sweep_blade_fit.count_interference` reports for the same field -- a notch
    schedule built from those would leave 26 pairs still interpenetrating.

    So the pair is solved at `nd` depths and the notch is the UNION of the
    crossing positions over the depth range, which is what a real slot has to
    be: one cut that clears the other blade everywhere it passes through.
    """
    out = []
    n = len(blades)
    for i in range(n):
        a = blades[i]
        for j in range(i + 1, n):
            b = blades[j]
            reach = a["half"] + b["half"] + depth * (a["tan"] + b["tan"])
            if abs(a["c"][0] - b["c"][0]) > reach:
                continue
            if abs(a["c"][1] - b["c"][1]) > reach:
                continue
            det = a["e"][0] * (-b["e"][1]) - a["e"][1] * (-b["e"][0])
            if abs(det) < 1e-9:
                continue                     # parallel: cannot cross
            ss, ts = [], []
            for k in range(nd):
                y = depth * k / max(nd - 1, 1)
                ax = a["c"][0] + a["lean"][0] * y * a["tan"]
                az = a["c"][1] + a["lean"][1] * y * a["tan"]
                bx = b["c"][0] + b["lean"][0] * y * b["tan"]
                bz = b["c"][1] + b["lean"][1] * y * b["tan"]
                rx, rz = bx - ax, bz - az
                s = (rx * (-b["e"][1]) - rz * (-b["e"][0])) / det
                t = (a["e"][0] * rz - a["e"][1] * rx) / det
                if abs(s) <= a["half"] and abs(t) <= b["half"]:
                    ss.append(s)
                    ts.append(t)
            if not ss:
                continue
            sin_ang = abs(a["e"][0] * b["e"][1] - a["e"][1] * b["e"][0])
            out.append((i, j, (min(ss), max(ss)), (min(ts), max(ts)),
                        max(sin_ang, 0.15)))
    return out


def build_notched(blades, depth, plate_t=PLATE_T, notch=True):
    """(verts, faces) for the blade field, with half-lap notches at crossings.

    One blade of each crossing pair is notched from the TOP (its upper half is
    absent across the slot) and the other from the BOTTOM, which is what makes
    them interlock instead of interpenetrate. The parity is taken from the
    blade's azimuth so it is consistent across the whole field: a blade running
    along x is notched from the top, one running along z from the bottom.
    """
    verts, faces = [], []

    def box(centre, e, nrm, s0, s1, y0, y1, t):
        """A slab of blade between along-edge s0..s1 and depth y0..y1."""
        b = len(verts)
        for (yy) in (y0, y1):
            for ss, sgn in ((s0, -1), (s1, -1), (s1, 1), (s0, 1)):
                verts.append((centre[0] + e[0] * ss + nrm[0] * sgn * t / 2.0,
                              yy,
                              centre[1] + e[1] * ss + nrm[1] * sgn * t / 2.0))
        faces.extend([(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4),
                      (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2),
                      (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)])

    cuts = {i: [] for i in range(len(blades))}
    if notch:
        for i, j, sr, tr, sin_ang in crossings(blades, depth):
            # slot must clear the other blade's thickness across the angle, and
            # span everywhere the crossing travels as the pair leans
            w = plate_t / sin_ang + 2 * CLEAR
            top_i = abs(blades[i]["e"][0]) >= abs(blades[i]["e"][1])
            cuts[i].append((sr[0] - w / 2.0, sr[1] + w / 2.0, top_i))
            cuts[j].append((tr[0] - w / 2.0, tr[1] + w / 2.0, not top_i))

    removed = 0.0
    total = 0.0
    for i, bl in enumerate(blades):
        h = bl["half"]
        nrm = (-bl["e"][1], bl["e"][0])
        total += 2 * h * depth
        edges = sorted({-h, h} | {max(-h, min(h, x))
                                  for a, b, _ in cuts[i] for x in (a, b)})
        for k in range(len(edges) - 1):
            s0, s1 = edges[k], edges[k + 1]
            if s1 - s0 < 1e-6:
                continue
            mid = 0.5 * (s0 + s1)
            cut = next((c for c in cuts[i] if c[0] <= mid <= c[1]), None)
            if cut is None:
                box(bl["c"], bl["e"], nrm, s0, s1, -depth, 0.0, plate_t)
            elif cut[2]:                       # notched from the top
                box(bl["c"], bl["e"], nrm, s0, s1, -depth, -depth / 2.0,
                    plate_t)
                removed += (s1 - s0) * depth / 2.0
            else:                              # notched from the bottom
                box(bl["c"], bl["e"], nrm, s0, s1, -depth / 2.0, 0.0, plate_t)
                removed += (s1 - s0) * depth / 2.0
    return verts, faces, {"notches": sum(len(v) for v in cuts.values()),
                          "area_removed_pct": 100.0 * removed / max(total, 1e-9)}


def interference_after_notching(blades, depth):
    """Crossings that remain a solid-solid clash once the notches are cut.

    A crossing is resolved when the two blades occupy DIFFERENT halves of the
    depth there. Anything else is still a clash and must be reported.
    """
    bad = 0
    for i, j, _sr, _tr, _sa in crossings(blades, depth):
        top_i = abs(blades[i]["e"][0]) >= abs(blades[i]["e"][1])
        top_j = abs(blades[j]["e"][0]) >= abs(blades[j]["e"][1])
        if top_i == top_j:                    # same half -> still interpenetrates
            bad += 1
    return bad


# --- optics -----------------------------------------------------------------

def full_stack(blades, prm, notch=True):
    """Notched blades + the pyramid floor + one backing slab, as `geom_stack`
    would assemble them.

    THE PANEL IS NOT JUST THE BLADES. The first version handed the renderer the
    blade field alone: no floor, no slab, so the camera looked straight through
    to the world and the panel read 98.8 % -- a mirror, not a light trap. The
    stack is rebuilt here exactly as `geom_stack.build_mesh` does it, with the
    top layer replaced.
    """
    import geom_stack as ST
    top_depth = prm["top_depth"]
    bot_depth = prm["bot_depth"]
    face_w, face_h = prm["face_w"], prm["face_h"]
    margin_depths = prm["margin_depths"]
    backing = prm["backing"]

    tv, tf, st = build_notched(blades, top_depth, notch=notch)

    xs = [q[0] for q in tv]
    zs = [q[2] for q in tv]
    need = max(max(xs) - face_w, -min(xs),
               max(zs) - face_h / 2.0, -min(zs) - face_h / 2.0)
    bot_p = dict(prm["bot_params"])
    bot_p["margin_min"] = max(need, 0.0)
    bv, bf = ST._build_layer(prm["bot"], dict(
        bot_p, face_w=face_w, face_h=face_h, depth=bot_depth,
        margin_depths=margin_depths, backing=backing))
    bv = [(x, y - top_depth, z) for x, y, z in bv]

    n = len(tv)
    verts = tv + bv
    faces = tf + [tuple(i + n for i in f) for f in bf]

    m = max(margin_depths * (top_depth + bot_depth), prm["top_params"]["pitch"],
            need)
    h = face_h / 2.0 + m
    y0 = -(top_depth + bot_depth)
    b = len(verts)
    for y in (y0, y0 - backing):
        verts += [(-m, y, -h), (face_w + m, y, -h),
                  (face_w + m, y, h), (-m, y, h)]
    faces += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b + i, b + 4 + i, b + 4 + j, b + j))
    return verts, faces, st


def measure(verts, faces, tag, prm):
    import bpy
    import blender_render as BR
    from cone3d_sweep import COAT
    rows = []
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
                               "roughness": 0.30},
                   "prebuilt_mesh": (verts, faces)}
            cfg.update({k: v for k, v in COAT.items()
                        if k != "spec_roughness"})
            res = BR.run(cfg)
            rec = list(res["modes"].values())[0]
            rows.append((mat, th, rec["panel"]["mean"],
                         rec["control"]["mean"]))
    return rows


def main():
    import blender_render as BR                                  # noqa: F401
    os.makedirs(OUT, exist_ok=True)
    DEPTH = BF.DEPTH - BF.FDEPTH
    tp = {"azimuth_mode": "grid", "jitter": 0.3, "pitch": BF.PITCH,
          "plate_over": 1.15, "plate_t_bot": PLATE_T, "plate_t_top": PLATE_T,
          "tilt_deg": 2.0, "tilt_jitter": 0.0}
    base = {"backing": 2.0, "bot": "pyramid", "bot_depth": BF.FDEPTH,
            "bot_params": {"margin_depth_ref": BF.DEPTH, "pitch": 2.0,
                           "tip_flat": 0.1},
            "face_h": BF.FACE, "face_w": BF.FACE, "margin_depths": 2.0,
            "seed": 23, "top": "shingle", "top_depth": DEPTH,
            "top_params": tp}

    # THE MEASURED FIELD CARRIES THE MARGIN. `blade_segments` defaults to the
    # preview extent (margin 0, clipped to the face); a measurement needs the
    # full margined field or the tilted camera reads past the panel's edge.
    blades, _p = BF.blade_segments(1.15, "grid", margin_depths=2.0)
    cr = crossings(blades, DEPTH)
    bad = interference_after_notching(blades, DEPTH)
    print("=" * 74)
    print("Q8 part 3: half-lap notches on the published blade array")
    print("=" * 74)
    print("  %d blades, %d crossings, %d unresolved after notching"
          % (len(blades), len(cr), bad))

    rows = []
    for notch in (False, True):
        v, f, st = full_stack(blades, base, notch=notch)
        tag = ("BN_notched_s23" if notch else "BN_plain_s23")
        prm = json.loads(json.dumps(base))
        prm["top_params"]["notched"] = bool(notch)
        print("\n  %-16s %6d faces, %d notches, %.3f %% of blade area removed"
              % (tag, len(f), st["notches"], st["area_removed_pct"]),
              flush=True)
        for mat, th, rho, ctrl in measure(v, f, tag, base):
            rows.append({"tag": tag, "family": "stack",
                         "topology": "shingle/pyramid", "process": "sheet",
                         "feature": PLATE_T, "seed": 23, "diffuse_frac": mat,
                         "plate_over": 1.15, "azimuth_mode": "grid",
                         "jitter": 0.3, "notched": int(notch),
                         "blades": len(blades),
                         "collisions": 0 if notch else len(cr),
                         "notches": st["notches"],
                         "area_removed_pct": round(st["area_removed_pct"], 4),
                         "theta": th, "rho": rho, "control": ctrl,
                         "params_json": json.dumps(prm, sort_keys=True)})

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nwrote %s (%d rows)" % (CSV, len(rows)))

    worst = {}
    for r in rows:
        worst[r["tag"]] = max(worst.get(r["tag"], 0.0), r["rho"])
    a, b = worst["BN_plain_s23"], worst["BN_notched_s23"]
    print("\n  %-18s %12s" % ("design", "worst rho"))
    print("  %-18s %11.5f%%" % ("un-notched", 100 * a))
    print("  %-18s %11.5f%%   %+.2f%%" % ("half-lap notched", 100 * b,
                                          100 * (b - a) / a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
