"""Does the simulator show the design the reports measured?

    python3 scripts/audit_normal.py          # no Blender needed

WHY THIS EXISTS. `sim_server.NORMAL` is meant to be the published design: pick
a structure, touch nothing, and the panel on screen is the one behind the
numbers in the reports. It was not. `NORMAL` listed only the headline
parameters and everything else fell through to the geometry dataclass's own
default, which for four families was a different value from the one every
published row used:

    cone       radial_seg 32 / height_seg  3   vs   24 / 12 in all 1860 rows
    comb       jitter 0.30                     vs   0.0
    honeycomb  cell_lean_domain 8.0            vs   16.0
    vgroove    arc_segments 6, micro 0/0       vs   24, 0.3 / 1.0

The cone one was not cosmetic. A cone wall at height_seg 3 is a three-band
approximation of a curve, and it is the whole of the 23 % disagreement between
Cycles and Mitsuba that sat unexplained in the open-questions list -- at 24/12
the same comparison is a few percent. The comb one contradicts its own module:
a commercial expanded honeycomb is periodic by construction and cannot be
jittered, which `_build_comb`'s docstring says in as many words.

WHAT IT CHECKS. For every family, for every parameter the published sweeps
pinned to a SINGLE value (swept parameters are skipped -- there is no one right
default for those), the value the simulator would use must equal it.

Exit code is the number of mismatches, so it can gate a build.
"""

import ast
import sys
import os
import csv
import json
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Envelope and bookkeeping: set per measurement, never a design choice.
SKIP = {"face_w", "face_h", "margin_depths", "backing", "seed", "pitch_seed",
        "width_seed", "depth", "topology", "variant", "margin_depth_ref"}

MODULES = {
    "cone": ("geom3d", "Cone3DParams"),
    "comb": ("geom_topo", "TopoParams"),
    "honeycomb": ("geom_topo", "TopoParams"),
    "shingle": ("geom_topo", "TopoParams"),
    "truss": ("geom_topo", "TopoParams"),
    "square": ("geom_cell", "CellParams"),
    "triangle": ("geom_cell", "CellParams"),
    "mixed": ("geom_cell", "CellParams"),
    "reentrant": ("geom_cell", "CellParams"),
    "nested": ("geom_cell", "CellParams"),
    "vgroove": ("profile_ridge", "RidgeParams"),
    # THE FAMILIES THIS AUDIT COULD NOT SEE. `geom_floor` names its shape in a
    # `kind` field, and `which_family` only ever looked at `topology`,
    # `variant`, `tip_radius` and `tip_width` -- so every pyramid, wave and gap
    # row in 30-odd sweep files fell through to None and was skipped, and the
    # audit reported "every family's default is the design the reports
    # measured" over a family it had never once checked. `pyramid` is not a
    # minor member: it is the phase 5 champion and the standalone sharp-tip
    # design the whole floor line descends from.
    "pyramid": ("geom_floor", "FloorParams"),
    "wave": ("geom_floor", "FloorParams"),
    "gap": ("geom_floor", "FloorParams"),
}


def _normal_src():
    """(source of the NORMAL literal, its first line number in sim_server.py)"""
    src = open(os.path.join(HERE, "sim_server.py")).read()
    # Anchored at a line start. `FLOOR_NORMAL = {` CONTAINS `NORMAL = {`, so a
    # bare .index would silently audit the wrong dict the day one is added.
    a = src.index("\nNORMAL = {") + 1
    return src[a:src.index("\n}", a) + 2], src.count("\n", 0, a) + 1


def load_normal():
    """Read NORMAL out of sim_server without importing it -- it needs bpy."""
    ns = {}
    exec(_normal_src()[0], ns)
    return ns["NORMAL"]


def duplicate_keys():
    """Keys written twice in the NORMAL literal. The second silently wins.

    WHY THIS IS A CHECK AND NOT A CODE REVIEW. `NORMAL` had "pyramid" twice --
    once as the phase 5 champion (pitch 5.5, sharp tip, 50 mm) and once, 21
    lines later, as the small floor-layer variant (pitch 2.0, tip_flat 0.1,
    3 mm) that a stacked design puts UNDER a tube. Python keeps the last, so
    choosing pyramid as a top structure silently built the floor part, at a
    pitch 2.75x off the design its own comment cites. Neither `exec` nor `dict`
    nor any linter in this repo says a word: a duplicate key is legal Python.
    The whole audit ran green over it because the family was also invisible to
    `which_family`. Reading the literal as a syntax tree is the only way to see
    both halves.
    """
    src, base = _normal_src()
    tree = ast.parse(src).body[0].value
    seen, dup = {}, []
    for k in tree.keys:
        if not isinstance(k, ast.Constant):
            continue
        line = base + k.lineno - 1          # real line in sim_server.py
        if k.value in seen:
            dup.append((k.value, seen[k.value], line))
        seen[k.value] = line
    return dup


def which_family(prm):
    if prm.get("topology"):
        return prm["topology"]
    if prm.get("variant"):
        return prm["variant"]
    if prm.get("kind"):
        return prm["kind"]           # geom_floor: pyramid | wave | gap | cone
    if "tip_radius" in prm:
        return "cone"
    if "tip_width" in prm:
        return "vgroove"
    return None


def published():
    """family -> param -> set of values seen in non-void sweeps."""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    files = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "results", "sweep_*.csv"))):
        if "__void__" in path:
            continue
        try:
            rows = list(csv.DictReader(open(path)))
        except Exception:
            continue
        if not rows or "params_json" not in rows[0]:
            continue
        files += 1
        for r in rows:
            try:
                prm = json.loads(r["params_json"])
            except Exception:
                continue
            fam = which_family(prm)
            if fam not in MODULES:
                continue
            for k, v in prm.items():
                if k in SKIP or not isinstance(v, (int, float, str, bool)):
                    continue
                out[fam][k].add(v)
    return out, files


def main():
    normal = load_normal()
    pub, nfiles = published()
    if not pub:
        print("no published sweeps found -- nothing to audit")
        return 0

    bad = []
    checked = 0
    for fam, params in sorted(pub.items()):
        if fam not in normal or fam not in MODULES:
            continue
        mod, cls = MODULES[fam]
        try:
            dflt = getattr(__import__(mod), cls)()
        except Exception as exc:
            print("  cannot load %s.%s: %s" % (mod, cls, exc))
            continue
        for k, vals in sorted(params.items()):
            if len(vals) != 1:
                continue            # swept: no single published value
            want = next(iter(vals))
            if not hasattr(dflt, k) and k not in normal[fam]:
                continue
            got = normal[fam].get(k, getattr(dflt, k, None))
            if got is None:
                continue
            checked += 1
            try:
                same = abs(float(got) - float(want)) < 1e-9
            except (TypeError, ValueError):
                same = got == want
            if not same:
                src = "NORMAL" if k in normal[fam] else "%s default" % cls
                bad.append((fam, k, got, want, src))

    dup = duplicate_keys()
    print("=" * 72)
    print("SIMULATOR DEFAULTS vs PUBLISHED DESIGNS")
    print("  %d sweep files, %d pinned parameters checked, %d families"
          % (nfiles, checked, len(set(f for f in pub if f in MODULES))))
    print("=" * 72)
    for name, first, line in dup:
        print("  DUPLICATE KEY  NORMAL[%r] at sim_server.py:%d and :%d "
              "-- the second wins. Split the roles instead."
              % (name, first, line))
    if not bad and not dup:
        print("  every family's default is the design the reports measured")
        return 0
    print("  %-11s %-18s %12s %12s   %s"
          % ("family", "parameter", "simulator", "published", "comes from"))
    for fam, k, got, want, src in bad:
        print("  %-11s %-18s %12s %12s   %s" % (fam, k, got, want, src))
    print("-" * 72)
    print("  %d mismatch(es), %d duplicate key(s). The simulator is not "
          "showing what it cites." % (len(bad), len(dup)))
    return len(bad) + len(dup)


if __name__ == "__main__":
    sys.exit(min(main(), 120))
