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

THE COST THAT WAS, and what replaced it. One subprocess per measurement paid
Blender's startup every time. Measured at the UI's 64-sample default: 1.30 s of
wall clock for a measurement whose Cycles render is 0.56 s of it -- more than
half the click spent starting and exiting a renderer. So this worker now has a
SERVE MODE:

    Blender --background --factory-startup --python scripts/cyc_worker.py \
        -- --serve

one long-lived process reading one JSON request per line and answering each
with an "@@RESULT@@" line. `sim_server` keeps it warm and talks to it over a
pipe. What that buys is not only the startup: the first render in a fresh
Blender also pays Metal shader-cache load, and a warm worker has paid it once.

The cost of THAT, stated in turn, and measured rather than guessed: an idle
worker is 33 MB resident. It was assumed to be ~1.4 GB, on the strength of the
"Mem:1345M" Cycles prints -- that is the DEVICE allocation during a render and
it is released when the render ends; process RSS sawtooths 110-250 MB while
measuring and settles back to 33 MB. Watched across 30 consecutive 3-angle
measurements with persistent data on: no monotonic growth, so nothing leaks.

And a serve-mode worker outlives a bad request on purpose -- see `serve`.

Cross-measurement state is not a new risk here. `blender_render.run` opens with
`clear_scene()`, a full factory reset, and the sweeps have always driven
hundreds of measurements through one process on exactly that basis.

`sim_server.py` still runs inside Blender when it is started that way -- it
dispatches here only when `bpy` is absent. Same server, same answers.

Input:  {"op": "measure" | "lambert" | "form" | "bidir", ...its arguments}
Output: one line, "@@RESULT@@" + JSON. The marker is required because Blender
        writes its own banner and Cycles its progress to stdout.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RESULT = "@@RESULT@@"
READY = "@@READY@@"
PROG = "@@PROG@@"


def _relay_progress(S):
    """Make the worker's progress visible to the server that is waiting on it.

    Moving the render into a long-lived subprocess moved `_prog` with it, so
    `sim_server`'s PROG -- the thing /api/progress serves and every button's
    bar polls -- stopped being written by anything. The bar had nothing to do
    with the renderer's health; it simply had no source any more. A one-second
    measurement hides that. A sweep of dozens of renders does not.

    The wire format is the one `mts_worker` already uses and `_mts` already
    parses, "@@PROG@@ done total", so this adds a producer rather than a
    protocol.
    """
    def emit(done, total):
        S.PROG["done"], S.PROG["total"] = int(done), int(total)
        sys.stdout.write("%s %d %d\n" % (PROG, int(done), int(total)))
        sys.stdout.flush()
    S._prog = emit


def handle(req):
    """Run one request and return its result dict.

    Shared by both modes, so a one-shot run and a served run cannot drift into
    answering the same question differently.
    """
    op = req.get("op", "measure")

    # `sim_server` is imported for its measurement functions only. Importing it
    # must not start a second HTTP server on the same port, which is why the
    # listener lives under `if __name__ == "__main__"` there.
    import sim_server as S
    _relay_progress(S)

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
    elif op == "bidir":
        out = S.bidir_sweep(req["spec"], req.get("step", 20.0),
                            req.get("in_limit", 80.0),
                            req.get("out_limit", 80.0),
                            req.get("samples", 256), req.get("coating"))
    else:
        out = {"error": "no such op: %s" % op}
    return out


def _emit(out):
    sys.stdout.write("\n" + RESULT + json.dumps(out) + "\n")
    sys.stdout.flush()


def _failure(exc):
    import traceback
    traceback.print_exc()
    return {"error": "%s: %s" % (type(exc).__name__, exc)}


def serve():
    """Answer one request per stdin line until stdin closes.

    A FAILING REQUEST MUST NOT COST THE WARM PROCESS. The whole point of this
    mode is the Blender startup and the Metal shader-cache load already paid;
    exiting on a malformed spec would throw both away and hand the next
    request a cold worker. So every request is answered -- with an error if
    that is the answer -- and the loop continues. The caller cannot tell a
    served error from a one-shot one, which is what keeps the two modes
    interchangeable.

    Ends on EOF (the server closing the pipe) or on {"op": "quit"}.
    """
    import sim_server                                            # noqa: F401
    sys.stdout.write("\n" + READY + "\n")     # the expensive import is done
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as exc:
            _emit(_failure(exc))
            continue
        if req.get("op") == "quit":
            return 0
        try:
            _emit(handle(req))
        except Exception as exc:
            _emit(_failure(exc))
    return 0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--serve" in argv:
        return serve()
    _emit(handle(json.load(sys.stdin)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        _emit(_failure(exc))
        sys.exit(1)
