"""Measure one design in Cycles, from a JSON spec on stdin.

    Blender --background --factory-startup --python scripts/cyc_worker.py \
        -- < spec.json

WHY THIS EXISTS. The simulator used to BE Blender: `sim_server.py` was launched
by `Blender --background --python`, so the browser could not be opened without
starting a 400 MB renderer, and everything the server does without a renderer
-- build a lattice, preview it, write an STL -- was locked behind it too. That
is backwards. Verified before writing this: every geometry module
(`geom3d`, `geom_topo`, `geom_cell`, `geom_floor`, `geom_stack`,
`profile_ridge`) contains zero references to `bpy`, and a 8796-face comb builds
in plain `python3`.

So the server now runs in plain Python and Cycles is dispatched here, exactly
as Mitsuba already was through `mts_worker.py`. Preview, parameters, STL export
and the published-number lookup need no Blender at all; pressing Measure
launches one.

THE COST, stated rather than discovered: a subprocess pays Blender's startup on
every measurement, about 1.5 s here, where the in-process server paid it once.
`sim_server.py` therefore still runs inside Blender when it is started that way
-- it dispatches to this worker only when `bpy` is absent. Same server, same
answers, two launch modes.

ONE DISPATCH (2026-09-15). This file used to unpack the request itself, and it
forwarded only five of the fifteen arguments `form` takes: coating, deep
coating, paint depth, observer angle, sampling density and the rest were
dropped, so a plain-Python server measured the default Musou head-on at the
default density whatever was asked (results/audit_2026_09_14/
dispatch_probe.json). The in-process path unpacked the same request in a
separate lambda that did forward them. Two hand-written argument lists, one of
them wrong. Both paths now call `sim_server.run_op`, and
`scripts/gate_dispatch_equivalence.py` checks that they cannot diverge.

Input:  {"op": "measure" | "lambert" | "form" | "form_lambert", ...arguments}
Output: one line, "@@RESULT@@" + JSON. The marker is required because Blender
        writes its own banner and Cycles its progress to stdout.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    req = json.load(sys.stdin)
    op = req.pop("op", "measure")

    # `sim_server` is imported for its measurement functions only. Importing it
    # must not start a second HTTP server on the same port, which is why the
    # listener lives under `if __name__ == "__main__"` there.
    import sim_server as S
    out = S.run_op(op, req)

    sys.stdout.write("\n@@RESULT@@" + json.dumps(out) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        import traceback
        traceback.print_exc()
        sys.stdout.write("\n@@RESULT@@" + json.dumps(
            {"error": "%s: %s" % (type(exc).__name__, exc)}) + "\n")
        sys.stdout.flush()
        sys.exit(1)
