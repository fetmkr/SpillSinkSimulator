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

Input:  {"op": "measure" | "lambert" | "form", ...the op's arguments}
Output: one line, "@@RESULT@@" + JSON. The marker is required because Blender
        writes its own banner and Cycles its progress to stdout.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    req = json.load(sys.stdin)
    op = req.get("op", "measure")

    # `sim_server` is imported for its measurement functions only. Importing it
    # must not start a second HTTP server on the same port, which is why the
    # listener lives under `if __name__ == "__main__"` there.
    import sim_server as S

    if op == "measure":
        out = {"rho": S.measure(
            req["spec"], req["thetas"], req["diffuse_frac"], req["roughness"],
            req["samples"], req.get("coating", "musou_fit"),
            req.get("deep_coating"), req.get("paint_depth"),
            req.get("deep_until"), req.get("paint_fade", 0.0))}
    elif op == "lambert":
        out = {"rho": S.measure_lambert(
            req["spec"], req["theta"], req["rho"], req["samples"])}
    elif op == "form_lambert":
        out = S.form_lambert(req["spec"], req.get("rho", 0.01),
                             req.get("n_phase", 6), req.get("samples", 256),
                             tuple(req.get("thetas", (-40.0, 40.0, 0.0))),
                             beam_w=req.get("beam_w"))
    elif op == "form":
        out = S.form(req["spec"], req.get("thetas"), req.get("n_phase"),
                     req.get("samples"), beam_w=req.get("beam_w"))
    else:
        out = {"error": "no such op: %s" % op}

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
