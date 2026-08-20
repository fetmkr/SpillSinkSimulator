"""Does the slot classifier put each face on the part a person would name?

Runs without a server and without Blender. `test_sim.py` calls it the way it
already calls `audit_geometry.py`; the exit code is the number of failures.

WHY THE NUMBERS ARE IN THE FILE. A slot map cannot be checked from a CSV -- the
panel renders with the wrong finish on a third of its area and every
reflectance still looks plausible. `principles/04` says draw it and look; these
are the numbers looking produced, frozen so that a builder change which stops
emitting wall crowns fails here rather than three reports later.

THE TIP CHECKS ARE INDEPENDENT, not self-referential. Each compares the tip
area measured on the built mesh against a closed form written from the design
intent -- 2*wall/pitch of crown per unit area, (tip_flat/pitch)^2 of pyramid
flat, pi*r^2 per cone cell. A classifier bug and an algebra bug would have to
agree in order to pass.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import math                                                        # noqa: E402
import mat_slots as MS                                             # noqa: E402
import sim_server as SS                                            # noqa: E402

FAIL = []
NCHECK = [0]


def check(name, ok, detail=""):
    NCHECK[0] += 1
    print("  %-48s %s" % (name, "ok" if ok else "FAIL  " + detail))
    if not ok:
        FAIL.append(name)
    return ok


def near(name, got, want, rel=0.15):
    d = abs(got - want) / want if want else abs(got)
    return check("%s %.5f ~ %.5f" % (name, got, want), d <= rel,
                 "off %.1f%%, allowed %.0f%%" % (100 * d, 100 * rel))


COMMON = dict(face_w=40.0, face_h=40.0, margin_depths=0.0)

CASES = [
    ("honeycomb", "geom_topo", "TopoParams", {"topology": "honeycomb"},
     dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.30, depth=50.0)),
    ("comb", "geom_topo", "TopoParams", {"topology": "comb"},
     dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, depth=50.0)),
    ("shingle", "geom_topo", "TopoParams", {"topology": "shingle"},
     dict(depth=50.0)),
    ("square", "geom_cell", "CellParams", {"variant": "square"},
     dict(pitch=6.5, wall_top=0.1, wall_bot=0.1, depth=50.0)),
    ("nested", "geom_cell", "CellParams", {"variant": "nested"},
     dict(pitch=11.0, wall_top=0.1, wall_bot=0.1, depth=50.0)),
    ("cone", "geom3d", "Cone3DParams", {},
     dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=16,
          height_seg=8, depth=50.0)),
    ("pyr_flat", "geom_floor", "FloorParams", {"kind": "pyramid"},
     dict(pitch=4.0, tip_flat=0.1, depth=20.0)),
    ("pyr_sharp", "geom_floor", "FloorParams", {"kind": "pyramid"},
     dict(pitch=4.0, tip_flat=0.0, depth=20.0)),
    ("flat", "geom_floor", "FloorParams", {"kind": "gap"}, dict(depth=10.0)),
]


def build(mod, cls, fixed, prm):
    M = __import__(mod)
    kw = dict(fixed)
    kw.update(COMMON)
    kw.update(prm)
    p = getattr(M, cls)(**kw)
    v, f = M.build_mesh(p)
    return p, v, f


def panel_slots(p, v, f, depth, clip=True):
    """Slots of the TRIMMED part -- the thing the preview draws."""
    if clip:
        v, f = SS.clip_to_panel(v, f, p.face_w, p.face_h)
    _ids, st = MS.classify(v, f, depth=depth)
    return {s["key"]: s for s in st}


def tip_frac(p, by):
    return by.get("tips", {"area_mm2": 0.0})["area_mm2"] / (p.face_w * p.face_h)


def main():
    built = {}

    print("[slots] every face lands on a part, and the areas add up")
    for name, mod, cls, fixed, prm in CASES:
        p, v, f = build(mod, cls, fixed, prm)
        d = prm.get("depth", 50.0)
        ids, st = MS.classify(v, f, depth=d)
        check("%s: one id per face" % name, len(ids) == len(f),
              "%d ids vs %d faces" % (len(ids), len(f)))
        check("%s: areas sum to 1" % name,
              abs(sum(s["area_frac"] for s in st) - 1.0) < 1e-9)
        check("%s: every id is a known slot" % name, set(ids) <= set(MS.BY_ID))
        built[name] = (p, v, f, d)

    print("\n[slots] structure shows both a tip and a flank")
    for name in ("honeycomb", "comb", "square", "nested", "cone", "pyr_flat"):
        p, v, f, d = built[name]
        by = panel_slots(p, v, f, d)
        check("%s has tips and walls, both non-zero" % name,
              by.get("tips", {}).get("area_mm2", 0) > 0
              and by.get("walls", {}).get("area_mm2", 0) > 0)

    # A SHARP PYRAMID HAS NO TIP. Not a missing slot -- a slot with no area,
    # which is the honest answer and the one exposed_fraction_est gives too.
    p, v, f, d = built["pyr_sharp"]
    check("pyr_sharp reports no tip area",
          tip_frac(p, panel_slots(p, v, f, d)) < 1e-9)

    # The flat control's optical surface is its slab top, not a base.
    p, v, f, d = built["flat"]
    check("flat control's surface is tips",
          panel_slots(p, v, f, d, clip=False).get("tips", {}).get("faces", 0) == 1)

    print("\n[slots] tip area against an independent closed form")
    p, v, f, d = built["honeycomb"]
    near("honeycomb tips", tip_frac(p, panel_slots(p, v, f, d)), 2 * 0.08 / 6.5)
    p, v, f, d = built["comb"]
    near("comb tips", tip_frac(p, panel_slots(p, v, f, d)),
         p.exposed_fraction_est(), rel=0.20)
    p, v, f, d = built["square"]
    near("square tips", tip_frac(p, panel_slots(p, v, f, d)), 2 * 0.1 / 6.5)
    p, v, f, d = built["pyr_flat"]
    near("pyr_flat tips", tip_frac(p, panel_slots(p, v, f, d)), (0.1 / 4.0) ** 2)
    p, v, f, d = built["cone"]
    near("cone tips", tip_frac(p, panel_slots(p, v, f, d)),
         math.pi * 0.2 ** 2 / (5.5 ** 2 * math.sqrt(3) / 2), rel=0.25)

    # The asymmetry the whole feature exists for: the surface that decides the
    # answer is a fraction of a percent of the material being finished.
    print("\n[slots] the tips are a small minority of the AREA")
    for name in ("honeycomb", "comb", "cone"):
        p, v, f, d = built[name]
        fr = panel_slots(p, v, f, d).get("tips", {}).get("area_frac", 0.0)
        check("%s tips are 0 < area < 1%% of total" % name, 0.0 < fr < 0.01,
              "%.4f%%" % (100 * fr))

    print("\n%d checks, %d failures" % (NCHECK[0], len(FAIL)))
    if FAIL:
        print("FAILURES: %s" % ", ".join(FAIL))
    return len(FAIL)


if __name__ == "__main__":
    raise SystemExit(main())
