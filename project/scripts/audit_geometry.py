"""Geometric defects a number cannot show you. No Blender, no server.

    python3 scripts/audit_geometry.py

WHY THIS EXISTS, STATED PLAINLY. Three separate geometry defects in this
project were found by a person looking at a picture, not by any check:

  * the `comb` lattice had its two axes swapped, so no cell shared an edge with
    any neighbour and 30 % of the face was open channel;
  * `clip_to_panel` cut the first feature as well as the last, because the
    lattices start at negative x and the cut was made where the part was built
    rather than where it is referenced from;
  * the shaped floor covered less ground than the tube standing on it, leaving
    13.8 mm of blades on nothing at the origin corner.

Every one was invisible in the measurements. The window only ever sees the
face, so geometry that is wrong OUTSIDE the window -- or wrong in a way that a
uniform environment averages over -- changes no number while making the part
unbuildable and the render a lie. Asking a person to notice is not a check.

Each test below is the machine version of one thing an eye caught, plus the
cases those defects imply. Exit code is the number of failures.
"""

import sys
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FAILS = []

# The designs the study actually uses, at the parameters it published.
TOPS = {
    "shingle": dict(pitch=5.5, plate_t_top=0.05, plate_t_bot=0.05,
                    tilt_deg=2.0, tilt_jitter=0.0, azimuth_mode="grid",
                    jitter=0.30, plate_over=1.15, plate_len=1.0),
    "comb": dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0),
    "honeycomb": dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.30,
                      cell_lean_domain=16.0),
    "cone": dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=24,
                 height_seg=12),
    "square": dict(pitch=6.5, wall_top=0.1, wall_bot=0.1),
    "nested": dict(pitch=11.0, wall_top=0.1, wall_bot=0.1),
}
FLOORS = {"pyramid": dict(pitch=2.0, tip_flat=0.1),
          "wave": dict(pitch=2.0),
          "gap": dict()}

# Both ends of the range that matters: 0.0 is the preview and the STL export,
# which want the part; 2.0 is what every measurement runs at. The floor bug
# lived entirely at 0.0 and was therefore invisible to every sweep.
MARGINS = (0.0, 2.0)


def say(ok, name, detail=""):
    print("  %-5s %-46s %s" % ("ok" if ok else "FAIL", name, detail),
          flush=True)
    if not ok:
        FAILS.append(name)


def extent(verts):
    return (min(v[0] for v in verts), max(v[0] for v in verts),
            min(v[2] for v in verts), max(v[2] for v in verts))


# --- 1. the floor must reach at least as far as what stands on it -----------

def check_floor_covers():
    """The defect: a 3 mm floor sized by a rule meant for a 50 mm tube."""
    print("\n[1] the shaped floor covers the tube standing on it")
    import geom_stack as ST
    worst = 0.0
    for md in MARGINS:
        for top, tp in TOPS.items():
            for fl, fp in FLOORS.items():
                if fl == "gap":
                    continue            # legitimately empty; nothing to cover
                sp = ST.StackParams(
                    face_w=100.0, face_h=100.0, margin_depths=md, backing=2.0,
                    seed=23, top=top, top_depth=47.0, top_params=tp,
                    bot=fl, bot_depth=3.0, bot_params=dict(fp))
                tv, _ = ST._build_layer(top, dict(
                    tp, face_w=100.0, face_h=100.0, depth=47.0,
                    margin_depths=md, backing=2.0, seed=23))
                v, _ = ST.build_mesh(sp)
                fv = [q for q in v if q[1] < -47.0 + 1e-6]
                if not tv or not fv:
                    continue
                tx0, tx1, tz0, tz1 = extent(tv)
                fx0, fx1, fz0, fz1 = extent(fv)
                gap = max(fx0 - tx0, tx1 - fx1, fz0 - tz0, tz1 - fz1)
                worst = max(worst, gap)
                if gap > 1e-6:
                    say(False, "%s on %s, margin %.1f" % (top, fl, md),
                        "%.2f mm of tube stands on nothing" % gap)
    say(worst <= 1e-6, "every top x floor x margin combination",
        "worst uncovered strip %.3f mm" % worst)


# --- 2. nothing above the entrance plane, and one slab at the bottom --------

def check_envelope():
    print("\n[2] nothing rises above the entrance plane")
    import geom_stack as ST
    for top, tp in TOPS.items():
        for fl, fp in FLOORS.items():
            sp = ST.StackParams(
                face_w=60.0, face_h=60.0, margin_depths=2.0, backing=2.0,
                seed=23, top=top, top_depth=47.0, top_params=tp,
                bot=fl, bot_depth=3.0, bot_params=dict(fp))
            v, f = ST.build_mesh(sp)
            hi = max(q[1] for q in v)
            if hi > 1e-9:
                say(False, "%s on %s" % (top, fl),
                    "rises %.4f mm above y = 0" % hi)
    say(not [x for x in FAILS if " on " in x], "every stack stays under y = 0")


# --- 3. the part is the size that was asked for -----------------------------

def check_size():
    """The defect: a "100 mm" panel that measures 105.4 x 113.0 mm.

    Keeping a feature whole whenever its centre fell inside let everything
    straddling an edge hang over by up to a pitch. A part is ordered by its
    size; a caliper across the delivered panel has to read what was typed. So
    the extent is checked against the request at three sizes, including the
    smallest, where one overhanging cell is the largest fraction of the part.

    Tolerance is 0.01 mm -- the cut is exact, so anything bigger is a bug and
    not a rounding.
    """
    print("\n[3] the part measures what was asked for")
    import sim_server as S
    worst, worst_who = 0.0, ""
    for panel in (40.0, 100.0, 160.0):
        for top, tp in TOPS.items():
            for fl in ("none", "pyramid"):
                spec = {"top": top, "top_params": dict(tp), "floor": fl,
                        "depth": 50.0, "panel": panel, "margin_depths": 0.0}
                if fl != "none":
                    spec["floor_params"] = dict(FLOORS[fl])
                    spec["floor_depth"] = 3.0
                try:
                    v, f, _ = S.build(spec)
                    v, f = S.clip_to_panel(v, f, panel, panel)
                except Exception as exc:
                    say(False, "%s + %s at %.0f mm" % (top, fl, panel),
                        str(exc)[:70])
                    continue
                if not v:
                    say(False, "%s + %s at %.0f mm" % (top, fl, panel),
                        "empty")
                    continue
                x0, x1, z0, z1 = extent(v)
                err = max(abs(x0), abs(x1 - panel),
                          abs(z0), abs(z1 - panel))
                if err > worst:
                    worst, worst_who = err, "%s + %s at %.0f mm" % (
                        top, fl, panel)
                if err > 0.01:
                    say(False, "%s + %s at %.0f mm" % (top, fl, panel),
                        "measures %.2f x %.2f mm" % (x1 - x0, z1 - z0))
    say(worst <= 0.01, "every family x floor x panel size",
        "worst deviation %.4f mm (%s)" % (worst, worst_who))


# --- 3b. and it reaches the corner it is machined from ---------------------

def check_corner():
    """The defect: a 16 mm bare strip along the edge the part starts at.

    The trim used to move the part by its most outlying vertex, so one jittered
    cell that wandered 16 mm out slid the whole field 16 mm in. The structure
    must reach the origin corner within one feature pitch -- a lattice cannot
    start mid-cell, but it cannot start a pitch and a half late either.
    """
    print("\n[3b] the structure reaches the origin corner")
    import sim_server as S
    for top, tp in TOPS.items():
        spec = {"top": top, "top_params": dict(tp), "floor": "none",
                "depth": 50.0, "panel": 100.0, "margin_depths": 0.0}
        try:
            v, f, _ = S.build(spec)
            v, f = S.clip_to_panel(v, f, 100.0, 100.0)
        except Exception as exc:
            say(False, "%s builds" % top, str(exc)[:70])
            continue
        body = [q for q in v if q[1] > -49.0]
        if not body:
            say(False, "%s has structure above the slab" % top, "none")
            continue
        x0, x1, z0, z1 = extent(body)
        pitch = float(tp.get("pitch", 6.5))
        bad = max(x0, z0, 100.0 - x1, 100.0 - z1)
        say(bad <= pitch + 1e-6, "%s" % top,
            "structure spans x %.1f..%.1f z %.1f..%.1f, worst bare edge "
            "%.2f mm (pitch %.1f)" % (x0, x1, z0, z1, bad, pitch))


# --- 4. a lattice must actually tessellate ---------------------------------

def check_tessellation():
    """The defect: a hex lattice whose cells shared no edges at all."""
    print("\n[4] the commercial honeycomb is still a tessellation")
    import geom_topo as GT
    try:
        GT.build_mesh(GT.TopoParams(
            topology="comb", face_w=60.0, face_h=60.0, depth=50.0, pitch=6.5,
            wall_top=0.08, wall_bot=0.08, jitter=0.0, margin_depths=2.0,
            backing=2.0, seed=23))
        say(True, "comb cells share 6 of 6 edges",
            "_assert_tessellates passed")
    except AssertionError as exc:
        say(False, "comb cells share 6 of 6 edges", str(exc)[:70])


def main():
    print("=" * 72)
    print("GEOMETRY AUDIT — the defects a measurement cannot show")
    print("=" * 72)
    check_floor_covers()
    check_envelope()
    check_size()
    check_corner()
    check_tessellation()
    print("\n" + "=" * 72)
    print("%d failed" % len(FAILS))
    for f in FAILS:
        print("  - %s" % f)
    print("=" * 72)
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(min(main(), 120))
