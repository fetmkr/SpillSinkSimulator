"""
Live simulator backend. Runs INSIDE Blender so it can render, and serves the
browser UI over HTTP.

    Blender --background --factory-startup --python scripts/sim_server.py
    open http://127.0.0.1:8777

WHY IT LIVES IN BLENDER. The numbers in every report come from Cycles. A
path tracer reimplemented in the browser would be fast and would produce
DIFFERENT numbers, which destroys the one thing this tool is for: checking that
what you see live matches what was published. So the browser draws geometry and
nothing else; every reflectance figure comes from the same `blender_render.run`
the sweeps call.

WHY IT IS PERSISTENT. Blender cold start is 0.44 s and a measurement is 0.63 s.
Paying the start-up per click would nearly double the latency and make the tool
feel broken. One process, many requests.

MEASURED COSTS, so the UI can be honest about which control is a slider and
which is a button:

    build geometry (preview margin)      1-21 ms
    derived scalars                      < 1 ms
    rho at one angle, study quality      0.63 s
    rho at five angles                   2.0 s
    full study score (3 coatings x 3 seeds)  ~18 s
    form destruction (48 frames, 512 spp)    ~300 s

The last one cannot go on a slider and is not offered here as a blocking call;
the UI queues it through the watchdog instead.
"""

import sys
import os
import io
import json
import math
import time
import struct
import threading
import traceback
import queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

PORT = int(os.environ.get("SIM_PORT", "8777"))
UI = os.path.join(ROOT, "sim")

# TWO CONSTRAINTS THAT PULL OPPOSITE WAYS, and the shape that satisfies both.
#
# 1. `bpy` may only be touched from the thread Blender started on. Version one
#    used ThreadingHTTPServer and the first /api/measure killed the process:
#    blender.crash.txt showed `bpy_op_fn_call` under `pythread_wrapper`.
# 2. A single-threaded HTTP server plus HTTP/1.1 keep-alive deadlocks against a
#    browser. `serve_forever` services one connection at a time, and a browser
#    holds connections open; the server sat blocked on an idle socket and never
#    accepted the connection carrying the click. `curl` worked throughout,
#    because curl closes. That is why the UI looked wired but did nothing while
#    the identical request from the shell returned in 2.1 s.
#
# So: HTTP on worker threads (constraint 2), and anything that touches bpy
# marshalled back to the main thread through a queue (constraint 1). Geometry,
# STL and CSV lookups are pure Python and stay on the worker, so dragging a
# slider is not blocked by a render in flight.
JOBS = queue.Queue()

# Progress of the render currently occupying the main thread. Renders run one
# at a time (the queue serialises them), so one dict is enough; worker threads
# serve it at /api/progress while the render blocks. `done` counts sub-renders
# STARTED, so the bar reads "which frame am I on", not "which finished".
PROG = {"done": 0, "total": 0, "at": 0.0}


def _prog(done, total):
    PROG["done"], PROG["total"], PROG["at"] = int(done), int(total), time.time()

# 3. STANDALONE OR INSIDE BLENDER. Every geometry module here is pure Python --
#    `geom3d`, `geom_topo`, `geom_cell`, `geom_floor`, `geom_stack` and
#    `profile_ridge` contain no reference to `bpy` at all, and an 8796-face
#    comb builds in plain `python3`. Only the three measurements need Cycles.
#    Running the whole server inside Blender therefore locked preview,
#    parameters and STL export behind a renderer that has nothing to do with
#    them. When `bpy` is absent the server still starts, serves all of that,
#    and dispatches a measurement to `cyc_worker.py` in a Blender subprocess --
#    the same separation `mts_worker.py` already uses for Mitsuba.
try:
    import bpy                                                   # noqa: F401
    IN_BLENDER = True
except ImportError:
    IN_BLENDER = False

BLENDER = os.environ.get(
    "BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender")


def on_main(fn, *a, **kw):
    """Run `fn` on Blender's main thread; block this thread for the result."""
    box, done = {}, threading.Event()
    JOBS.put((fn, a, kw, box, done))
    done.wait()
    if "err" in box:
        raise box["err"]
    return box["val"]


def in_blender(op, **req):
    """Run one measurement op, wherever Blender happens to be.

    In-process when the server was started by Blender, and in a subprocess when
    it was not. The caller cannot tell the difference, which is the point: the
    numbers come from one code path either way.
    """
    if IN_BLENDER:
        fn = {"measure": lambda: measure(
                  req["spec"], req["thetas"], req["diffuse_frac"],
                  req["roughness"], req["samples"], req.get("coating",
                  "musou_fit"), req.get("deep_coating"),
                  req.get("paint_depth"), req.get("deep_until"),
                  req.get("paint_fade", 0.0), req.get("phis")),
              "lambert": lambda: measure_lambert(
                  req["spec"], req["theta"], req["rho"], req["samples"]),
              "form": lambda: form(req["spec"], req.get("thetas"),
                                   req.get("n_phase"), req.get("samples"),
                                   req.get("beam_w"), req.get("phis")),
              "form_lambert": lambda: form_lambert(
                  req["spec"], req.get("rho", 0.01),
                  req.get("n_phase", 6), req.get("samples", 256),
                  beam_w=req.get("beam_w"))}[op]
        val = on_main(fn)
        return {"rho": val} if op in ("measure", "lambert") else val

    import subprocess
    if not os.path.exists(BLENDER):
        return {"error": "Blender not found at %s -- set BLENDER_BIN. "
                         "Preview and STL work without it; measurement does "
                         "not." % BLENDER}
    # ONE RETRY. A launch immediately after another Blender exits has been seen
    # to die inside `ShaderCache::load_kernel` with an uncaught NSException --
    # Metal kernel compilation, not anything this code does. The same command
    # succeeded when run by hand, from a thread, and on every attempt after.
    # The collision is the likely cause but is NOT proven, so this is a
    # workaround and is labelled one: retry once, and report the real error if
    # the second attempt fails too.
    last = ""
    for attempt in (1, 2):
        p = subprocess.run(
            [BLENDER, "--background", "--factory-startup",
             "--python", os.path.join(HERE, "cyc_worker.py")],
            input=json.dumps(dict(req, op=op)), capture_output=True,
            text=True, timeout=1800)
        for line in reversed((p.stdout or "").splitlines()):
            i = line.find("@@RESULT@@")
            if i >= 0:
                try:
                    return json.loads(line[i + 10:])
                except Exception:
                    break
        last = (p.stderr or p.stdout or "no output")[-400:]
        if attempt == 1:
            print("[SIM] Blender subprocess produced no result; retrying once",
                  flush=True)
    return {"error": last}


RENDER_LOCK = threading.Lock()


# --- what the UI can build -------------------------------------------------

# What each structure looks like when it is the thing this study actually
# measured -- NOT the dataclass default. `TopoParams` is shared by comb,
# honeycomb, shingle and truss, so its defaults are a compromise that belongs
# to none of them: opening `comb` gave wall_top 0.4 / wall_bot 1.2, which is
# the honeycomb's flared wall and makes a commercial comb render as cells
# growing into each other. The bought product is 0.08 / 0.08.
# NORMAL IS THE PUBLISHED DESIGN, NOT A TASTEFUL STARTING POINT. Anything
# omitted here falls through to the dataclass default, and for four families
# that default was NOT what the sweeps measured: the cone rendered at
# radial 32 / height 3 against 24 / 12 in all 1860 published rows (a 4x coarser
# wall, and the whole of a 23 % Cycles-vs-Mitsuba disagreement), `comb` carried
# jitter 0.30 when a commercial honeycomb is periodic by construction and every
# row used 0.0, and the V-groove lost its micro-texture entirely. The simulator
# was showing and measuring a different part from the one in the reports.
# `scripts/audit_normal.py` compares this table against params_json and fails
# if they ever diverge again.
NORMAL = {
    "pyramid":  dict(pitch=5.5, tip_flat=0.0, apex_jitter=0.0, tip_drop=0.0,
                     depth=50.0),
    "comb":     dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, comb_expand=1.0,
                     jitter=0.0, depth=50.0),
    "shingle":  dict(pitch=5.5, plate_t_top=0.05, plate_t_bot=0.05,
                     tilt_deg=2.0, tilt_jitter=0.0, azimuth_mode="grid",
                     jitter=0.30, plate_over=1.15, plate_len=1.0, depth=50.0),
    "cone":     dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=24,
                     height_seg=12, depth=50.0),
    "honeycomb": dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.30,
                      cell_lean_domain=16.0, depth=50.0),
    "vgroove":  dict(pitch_mean=13.0, tip_width=0.4, valley_round=0.4,
                     pitch_jitter=0.25, arc_segments=24, micro_depth=0.3,
                     micro_pitch=1.0, depth=50.0),
    "square":   dict(pitch=6.5, wall_top=0.1, wall_bot=0.1, depth=50.0),
    "triangle": dict(pitch=6.5, wall_top=0.1, wall_bot=0.1, depth=50.0),
    "mixed":    dict(pitch=6.5, wall_top=0.1, wall_bot=0.1, depth=50.0),
    "reentrant": dict(pitch=6.5, wall_top=0.1, wall_bot=0.1, lean_deg=6.0,
                      depth=50.0),
    "nested":   dict(pitch=11.0, wall_top=0.1, wall_bot=0.1, depth=50.0),
    "flat":     dict(depth=10.0),
    "pyramid":  dict(pitch=2.0, tip_flat=0.1, depth=3.0),
    "wave":     dict(pitch=2.0, depth=3.0),
    "gap":      dict(depth=3.0),
}

# Which structures are still in play, and what each one is FOR. The dropdown
# used to list thirteen with no distinction, including three the study threw
# away: `truss` was last on every axis, and `slat` and `trough` are phase 1
# dead ends that cannot even be measured (their modules have no margin, so a
# tilted camera reads world background). Offering a control that cannot be
# measured as if it were a candidate is worse than not offering it.
GROUPS = [
    ("Candidates", ["pyramid", "comb", "shingle", "cone", "flat"]),
    ("Reference and controls", ["honeycomb", "vgroove", "square", "triangle",
                                "mixed", "reentrant", "nested"]),
]
RETIRED = {"truss": "last on every axis in phase 2",
           "slat": "phase 1 dead end; no margin parameter, not measurable",
           "trough": "phase 1 dead end; no margin parameter, not measurable"}

FAMILIES = {
    # Phase 5 champion: the standalone sharp pyramid (geom_floor at full
    # depth). Registered here so depth-vs-pitch and jitter questions can be
    # asked live instead of via a sweep script.
    "pyramid":  ("geom_floor", "FloorParams",  {"kind": "pyramid"}),
    "cone":     ("geom3d",     "Cone3DParams", {}),
    "comb":     ("geom_topo",  "TopoParams",   {"topology": "comb"}),
    "honeycomb": ("geom_topo", "TopoParams",   {"topology": "honeycomb"}),
    "shingle":  ("geom_topo",  "TopoParams",   {"topology": "shingle"}),
    "truss":    ("geom_topo",  "TopoParams",   {"topology": "truss"}),
    "square":   ("geom_cell",  "CellParams",   {"variant": "square"}),
    "triangle": ("geom_cell",  "CellParams",   {"variant": "triangle"}),
    "mixed":    ("geom_cell",  "CellParams",   {"variant": "mixed"}),
    "reentrant": ("geom_cell", "CellParams",   {"variant": "reentrant"}),
    "nested":   ("geom_cell",  "CellParams",   {"variant": "nested"}),
    "vgroove":  ("profile_ridge", "RidgeParams", {}),
    # Flat plate: the reference every ratio divides by. geom_floor's "gap"
    # kind is already exactly this -- nothing but the smooth slab, built for
    # the zero-cost control -- and being a real 3D mesh the Mitsuba
    # cross-check works too. Two earlier attempts LOOKED wrong on screen
    # (2026-08-17): profile_ridge with tip_width == pitch extruded into
    # broken overlapping chunks, and pyramid with tip_flat == pitch kept
    # hairline grooves between the tiles. No parameters of its own.
    "flat":     ("geom_floor", "FloorParams", {"kind": "gap"}),
    "slat":     ("profile2d",  "PanelParams",  {}),
    "trough":   ("profile_scatter", "ScatterParams", {}),
}
FLOORS = {
    "none":    None,
    "pyramid": ("geom_floor", "FloorParams", {"kind": "pyramid"}),
    "wave":    ("geom_floor", "FloorParams", {"kind": "wave"}),
    "gap":     ("geom_floor", "FloorParams", {"kind": "gap"}),
    "cone":    ("geom3d",     "Cone3DParams", {}),
    "comb":    ("geom_topo",  "TopoParams",  {"topology": "comb"}),
}
# which geom_stack layer name each family maps to
STACK_KIND = {"cone": "cone", "comb": "comb", "honeycomb": "honeycomb",
              "shingle": "shingle", "truss": "truss", "square": "square",
              "triangle": "triangle", "mixed": "mixed",
              "reentrant": "reentrant", "nested": "nested",
              "pyramid": "pyramid", "wave": "wave", "gap": "gap"}

# Slider ranges, by field-name suffix. Written down rather than guessed at
# render time so that a field nobody thought about shows up as a number box
# instead of silently getting a nonsense range.
RANGES = [
    # Integer counts and a few odd ones out. Without an entry here a field
    # falls through to the generic "0 .. 4x its default" rule, which is fine
    # for a length and wrong for a count: it offered 0 truss layers and 20,
    # both of which have no geometry, and it capped `baffle_pitch` at 20 when
    # its own default is 60 -- a slider that could not show its starting value.
    # The upper bounds below were found by probing, not guessed.
    ("layers", 1.0, 12.0, 1.0), ("links", 0.0, 6.0, 1.0),
    ("mixed_ring", 0.0, 8.0, 1.0), ("baffle_rows", 0.0, 6.0, 1.0),
    ("baffle_pitch", 10.0, 120.0, 1.0), ("baffle_len", 5.0, 120.0, 1.0),
    ("baffle_deg", -80.0, 80.0, 1.0),
    ("pitch_mean", 2.0, 40.0, 0.5), ("pitch", 1.0, 20.0, 0.1),
    ("depth_ratio", 0.5, 4.0, 0.1), ("depth", 5.0, 80.0, 1.0),
    ("tip_radius", 0.02, 1.0, 0.01), ("tip_width", 0.02, 2.0, 0.01),
    ("tip_flat", 0.0, 0.5, 0.01),
    ("wall_top", 0.02, 1.5, 0.01), ("wall_bot", 0.02, 2.0, 0.01),
    ("plate_t_top", 0.02, 1.0, 0.01), ("plate_t_bot", 0.02, 1.5, 0.01),
    ("plate_over", 0.8, 2.0, 0.05), ("plate_len", 0.3, 1.2, 0.05),
    ("comb_expand", 0.5, 2.0, 0.05),
    ("width_mean", 5.0, 80.0, 1.0), ("width_jitter", 0.0, 0.6, 0.05),
    ("slat_len", 5.0, 60.0, 1.0), ("slat_deg", 0.0, 80.0, 1.0),
    ("lean_deg", 0.0, 12.0, 0.5), ("cell_lean_deg", 0.0, 60.0, 1.0),
    ("tilt_jitter", 0.0, 30.0, 1.0), ("tilt_deg", 0.0, 60.0, 1.0),
    ("azimuth_jitter", 0.0, 180.0, 5.0),
    ("jitter", 0.0, 0.6, 0.02), ("valley_round", 0.0, 2.0, 0.05),
    ("micro_pitch", 0.2, 4.0, 0.1), ("micro_depth", 0.0, 2.0, 0.05),
    ("profile_power", 0.5, 2.0, 0.05), ("second_ratio", 0.0, 1.0, 0.05),
    ("second_depth_frac", 0.0, 1.0, 0.05), ("thickness", 0.2, 3.0, 0.1),
    ("asym", -0.5, 0.5, 0.05), ("backing", 0.5, 6.0, 0.5),
]
# never shown: fixed by the measurement protocol, or meaningless to vary here
HIDDEN = {"face_w", "face_h", "margin_depths", "margin_depth_ref", "seed",
          "pitch_seed", "width_seed", "baffle_seed", "topology", "variant",
          "kind",
          "tileable", "centre_margin_pitches", "grid", "arc_segments",
          "radial_seg", "height_seg", "strut_seg", "min_inner_radius"}


_USES = {}


def uses(mod, cname, fixed):
    """Which fields the chosen variant's builder ACTUALLY reads.

    `TopoParams` is shared by comb, honeycomb, shingle and truss, and
    `CellParams` by five cell variants. Listing every field for every variant
    put `plate_over` and `azimuth_mode` on a honeycomb -- controls that change
    nothing, which is worse than a missing control because the user turns them
    and concludes the tool is broken.

    The set is read out of the builder's own source at start-up rather than
    typed here. A hand-written list is exactly the thing that goes stale when
    someone adds a parameter, which is how `plate_over` ended up unrecorded in
    a whole sweep. If the source cannot be parsed the field is shown, because
    showing a useless control is a smaller failure than hiding a real one.
    """
    key = (mod, cname, tuple(sorted(fixed.items())))
    if key in _USES:
        return _USES[key]
    import re
    import inspect
    variant = fixed.get("topology") or fixed.get("variant") or fixed.get("kind")
    got = None
    if variant:
        try:
            # import FIRST. Reading sys.modules before anything imported the
            # module raised KeyError, the bare `except` swallowed it, and the
            # filter silently turned itself off -- but only for whichever
            # variant happened to be listed first for its module, so three of
            # four topologies looked correct and `comb` showed every field in
            # TopoParams including the shingle and truss ones.
            __import__(mod)
            src = inspect.getsource(sys.modules[mod])
            i = src.index("def _build_%s(" % variant)
            j = src.find("\ndef ", i + 1)
            body = src[i:(j if j > 0 else len(src))]
            got = set(re.findall(r"\bp\.([a-z_0-9]+)", body))
            # helpers the builder calls with p
            for helper in re.findall(r"\b(_[a-z_0-9]+)\(", body):
                k = src.find("def %s(" % helper)
                if k >= 0:
                    e = src.find("\ndef ", k + 1)
                    got |= set(re.findall(r"\bp\.([a-z_0-9]+)",
                                          src[k:(e if e > 0 else len(src))]))
        except Exception as exc:
            print("[SIM] uses(%s/%s) failed, showing all fields: %r"
                  % (mod, variant, exc), flush=True)
            got = None
    _USES[key] = got
    return got


def _cls(mod, name):
    __import__(mod)
    return getattr(sys.modules[mod], name)


def _fit(mod, cname, kw):
    """Drop keys the dataclass does not declare, and report what was dropped.

    `profile2d.PanelParams` and `profile_scatter.ScatterParams` predate
    `margin_depths` and do not have it, so passing the shared envelope keys to
    every family raised TypeError and those two structures could not even be
    previewed. Dropping silently would be worse than the crash: `margin_depths`
    is what keeps a tilted camera from reading world background, so a family
    without it cannot be MEASURED correctly at +-40 even though it renders
    fine. The caller gets the list back and refuses to measure.
    """
    import dataclasses
    fields = {f.name: f for f in dataclasses.fields(_cls(mod, cname))}
    out = {}
    for k, v in kw.items():
        if k not in fields:
            continue
        # A slider is a float control. `layers`, `links`, `mixed_ring` and
        # `baffle_rows` are counts that end up inside range(), so 1.0 raises
        # TypeError where 1 works -- the value was right and the type was not.
        # Every one of those looked to the test like "geometry vanished".
        d = fields[k].default
        if isinstance(d, int) and not isinstance(d, bool) \
                and isinstance(v, float) and v == int(v):
            v = int(v)
        out[k] = v
    return out, sorted(set(kw) - set(fields))


# a family that cannot take a margin cannot be measured at +-40 deg: the
# camera sees past the panel edge and reads the world, not the design
NEEDS_MARGIN = "margin_depths"

# request-scoped: which envelope keys a family could not accept, keyed by the
# params object built for that request. Never stored on the object itself.
DROPPED = {}


def field_spec(mod, cname, fixed, key=None):
    import dataclasses
    used = uses(mod, cname, fixed)
    norm = NORMAL.get(key or "", {})
    out = []
    for f in dataclasses.fields(_cls(mod, cname)):
        if f.name in HIDDEN or f.name in fixed:
            continue
        if used is not None and f.name not in used:
            continue
        default = norm.get(f.name, f.default)
        if default is dataclasses.MISSING:
            continue
        if isinstance(default, bool):
            out.append({"name": f.name, "kind": "bool", "default": default})
            continue
        if isinstance(default, str):
            out.append({"name": f.name, "kind": "str", "default": default})
            continue
        if not isinstance(default, (int, float)):
            continue
        rng = next((r for r in RANGES if f.name.endswith(r[0])), None)
        if rng:
            out.append({"name": f.name, "kind": "num", "default": default,
                        "min": rng[1], "max": rng[2], "step": rng[3]})
        else:
            out.append({"name": f.name, "kind": "num", "default": default,
                        "min": 0.0, "max": max(1.0, float(default) * 4),
                        "step": 0.01})
    return out


def families_json():
    out = {"top": {}, "floor": {}}
    for k, v in FAMILIES.items():
        if k in RETIRED:
            continue
        mod, cname, fixed = v
        out["top"][k] = field_spec(mod, cname, fixed, k)
    for k, v in FLOORS.items():
        if v is None:
            out["floor"][k] = []
        else:
            mod, cname, fixed = v
            out["floor"][k] = field_spec(mod, cname, fixed, k)
    out["groups"] = [[g, [k for k in ks if k in out["top"]]]
                     for g, ks in GROUPS]
    out["normal_depth"] = {k: NORMAL.get(k, {}).get("depth", 50.0)
                           for k in out["top"]}
    out["floor_depth"] = {k: NORMAL.get(k, {}).get("depth", 3.0)
                          for k in out["floor"]}
    # Which tops `geom_stack` can actually put a floor under. The 1D families
    # are cross-sections the renderer extrudes and have no mesh builder it can
    # call, so the UI must not offer them a floor at all.
    out["stackable"] = sorted(k for k in out["top"] if k in STACK_KIND)
    return out


# --- geometry ---------------------------------------------------------------

def build(spec):
    """spec -> (verts, faces, describe-dict). Preview margin unless asked."""
    # Fill anything the caller left out from NORMAL, not from the dataclass.
    # `field_spec` applies NORMAL so the UI's sliders start at the values this
    # study measured, but `build` did not, so an API call with an empty
    # `top_params` silently got `TopoParams`' own defaults -- pitch 7.5,
    # plate_over 1.45, tilt 60 -- which lays the blades almost flat and spreads
    # a 100 mm panel over 375 mm. The UI was fine and every direct test of the
    # endpoint was measuring a different design from the one on screen.
    top = spec["top"]
    tp = dict(NORMAL.get(top, {}), **(spec.get("top_params") or {}))
    tp.pop("depth", None)
    floor = spec.get("floor", "none")
    fp = dict(NORMAL.get(floor, {}), **(spec.get("floor_params") or {}))
    fp.pop("depth", None)
    # PANEL SIZE, one number for both layers. It was 60 mm hard-coded and
    # hidden, which is fine for a measurement -- the window is the face and the
    # margin runs past it -- and wrong for a picture or an STL, where the two
    # layers then have no common size at all. The floor sets it and the tube
    # follows.
    face = float(spec.get("panel", spec.get("face", 100.0)))
    depth = float(spec.get("depth", 50.0))
    fdepth = float(spec.get("floor_depth", 0.0)) if floor != "none" else 0.0
    # PREVIEW BUILDS AT ZERO MARGIN. The margin exists so a tilted camera
    # cannot see past the panel during a MEASUREMENT; a picture of the part
    # does not want it, and the trim throws it away anyway. Two reasons to
    # build without it rather than build and discard:
    #   - the 1D families return their whole cross-section as ONE polyline, so
    #     a strict per-face trim drops the entire V-groove at once. At zero
    #     margin the polyline already spans exactly face_h.
    #   - a 100 mm comb at margin 0.2 lays 276 mm of cells and took 480 ms to
    #     build; almost all of it was then cut off.
    margin = float(spec.get("margin_depths", 0.2))
    if margin <= 0.5 and not spec.get("full_extent"):
        margin = 0.0
    seed = int(spec.get("seed", 23))
    common = dict(face_w=face, face_h=face, margin_depths=margin,
                  backing=float(spec.get("backing", 2.0)))
    # A wave floor at grid 12 across a full measurement margin is half a
    # million triangles and 560 ms -- fine for a render, far too slow for
    # something that rebuilds while a slider moves. Only the PREVIEW is
    # coarsened; `margin` is 2.0 on the measurement path, so a measured wave is
    # always the real one. The first attempt at this patch matched a line that
    # existed only in `_render_params`, where none of `floor`, `margin` or `fp`
    # is defined yet -- it took down measure, form and published at once and
    # was found by running them, not by reading the diff.
    if floor == "wave" and margin <= 0.5:
        fp.setdefault("grid", 5)

    if floor == "none":
        mod, cname, fixed = FAMILIES[top]
        kw, dropped = _fit(mod, cname, dict(fixed, **tp, **common,
                                            **_depth_kw(mod, depth),
                                            **_seed_kw(mod, seed)))
        p = _cls(mod, cname)(**kw)
        # `dropped` is deliberately NOT attached to `p`. `geom3d` builds its
        # second cone array with Cone3DParams(**vars(p)), so any attribute
        # stapled on here comes back as an unexpected keyword and the whole
        # family dies the moment `second_ratio` is non-zero. State about the
        # request belongs to the request.
        DROPPED[id(p)] = dropped
        v, f = sys.modules[mod].build_mesh(p) if hasattr(
            sys.modules[mod], "build_mesh") else _profile_mesh(mod, p)
        return v, f, p

    import geom_stack as ST
    # NOT EVERY TOP CAN TAKE A FLOOR. `geom_stack` composes 3D modules; the 1D
    # families are cross-sections extruded by the renderer and have no
    # (verts, faces) builder it can call. `STACK_KIND` therefore has no entry
    # for them, and asking for one raised KeyError inside a worker thread --
    # which the mesh endpoint turned into a 0-byte reply, so the browser drew
    # nothing and said nothing. Refuse it in words instead.
    if top not in STACK_KIND:
        raise ValueError(
            "%s is a 1D extruded profile and cannot take a floor layer; "
            "set floor to none" % top)
    if floor not in STACK_KIND:
        raise ValueError("no floor named %s" % floor)
    # the stack path builds its layers inside geom_stack, so it never sees
    # `_fit` -- the same float-for-int problem reaches the floor params by a
    # different door. Coerce both sides against their own dataclasses.
    if top in FAMILIES:
        tp, _ = _fit(*FAMILIES[top][:2], tp)
    if floor in FLOORS and FLOORS[floor]:
        fp, _ = _fit(*FLOORS[floor][:2], fp)
    sp = ST.StackParams(face_w=face, face_h=face, margin_depths=margin,
                        backing=float(spec.get("backing", 2.0)), seed=seed,
                        top=STACK_KIND[top], top_depth=depth - fdepth,
                        top_params=tp,
                        bot=STACK_KIND[floor], bot_depth=fdepth,
                        bot_params=dict(fp, **({"margin_depth_ref": depth}
                                               if floor in ("pyramid", "wave",
                                                            "gap") else {})))
    v, f = ST.build_mesh(sp)
    return v, f, sp


def _depth_kw(mod, depth):
    return {"depth": depth}


def _seed_kw(mod, seed):
    if mod == "profile_ridge":
        return {"pitch_seed": seed}
    if mod == "profile2d":
        return {"pitch_seed": seed}
    if mod == "profile_scatter":
        return {"width_seed": seed}
    return {"seed": seed}


def _profile_mesh(mod, p):
    """1D families return cross-section loops; extrude them to a mesh.

    THE AXES MUST MATCH THE MEASUREMENT, and for a while they did not.
    `blender_render.loops_to_object` -- the path every published number came
    through -- writes a cross-section point (a, b) as `(x0, a, b)` and extrudes
    along X: depth on Y, across on Z, face on the XZ plane, exactly like every
    3D family. This preview wrote `(a, b, +-face_w/2)` and extruded along Z,
    which is the same solid rotated 90 degrees. Nothing measured was affected;
    the picture was simply of a differently-oriented panel, and a V-groove
    appeared to have its floor facing sideways while the honeycomb beside it
    did not.

    `shell` is also dropped. It is the back box of the slat and trough
    families, drawn behind the working surface, and rendering it put a second
    slab under the first -- read, reasonably, as the floor being doubled.
    """
    m = sys.modules[mod]
    cs = m.build_cross_section(p)
    verts, faces = [], []
    # Extrude 0..face_w, NOT +-face_w/2. `loops_to_object` runs the extrusion
    # from -margin to face_w + margin, so the part occupies 0..face_w in x
    # exactly like every 3D family. Centring it here put the whole V-groove at
    # negative x, and the corner-origin trim then dropped every face: the
    # preview came back empty while the measurement was fine.
    for loops in (getattr(cs, "stage1", None), getattr(cs, "stage2", None)):
        if not loops:
            continue
        for loop in loops:
            n = len(verts)
            k = len(loop)
            for (y, z) in loop:                      # depth, across
                verts.append((0.0, y, z))
            for (y, z) in loop:
                verts.append((p.face_w, y, z))
            for i in range(k):
                j = (i + 1) % k
                faces.append((n + i, n + j, n + k + j, n + k + i))
    return verts, faces


def clip_to_panel(verts, faces, face_w, face_h):
    """Trim the preview to the part: corner at the origin, cut only the far side.

    Rewritten after four incremental patches each broke something else. The
    rule is now ONE rule, and the reasons the alternatives were rejected are
    kept because each was tried and measured:

      * clip to [0,W] with the geometry left where it was built -- the
        lattices start at negative x (a comb begins at -pitch even with no
        margin, a V-groove cross-section at -43 mm), so the FIRST feature got
        cut as well as the last. There is no reason to cut at the corner the
        part is referenced from.
      * drop any face with a vertex outside -- gutted the arrays. A blade is
        one quad `plate_over * pitch` across, so most of them touch an edge
        somewhere; a 100 mm array came back as 748 triangles of floating
        plates out of 3306 faces.
      * clamp every vertex onto the cut plane -- fine for a cone or a pyramid,
        fatal for a sheet: a blade's xz footprint is a line 0.05 mm wide, so
        clamping collapses it to zero area and it disappears entirely.

    What survives all three: keep a face when its CENTRE is inside. Features
    straddling the far edge stay whole and overhang by up to half a feature,
    which is what a part cut on that line looks like, and nothing collapses.
    The backing slab is the one exception -- a single quad whose centre is
    always inside, so it would survive at full margin size and ring the part
    with a bare border. It is removed and rebuilt to the panel.

    Measurement never calls this.
    """
    slab = None
    if len(faces) >= 6 and all(len(f) == 4 for f in faces[-6:]):
        ys = {round(verts[i][1], 3) for f in faces[-6:] for i in f}
        if len(ys) == 2:
            slab = (min(ys), max(ys))
            verts, faces = verts[:-8], faces[:-6]
    # A mesh that was NOTHING BUT the slab (the flat plate / gap control) is
    # not empty -- the slab gets rebuilt to panel size at the end like anyone
    # else's. Early-returning here made `flat` "produce no geometry at all".
    if (not verts or not faces) and slab is None:
        return [], []

    # THE ORIGIN IS THE DESIGN'S, NOT THE MESH'S EXTREME VERTEX. Every family
    # builds its face at x in [0, face_w] and z in [-face_h/2, +face_h/2] and
    # overruns it by a margin, so moving the corner to (0, 0) is one fixed
    # translation in z and none in x.
    #
    # Shifting by `min(x), min(z)` instead -- which is what this did -- makes
    # the origin depend on the single most outlying vertex in the whole mesh.
    # For a jittered family that vertex is one cell that happened to wander:
    # `honeycomb` reaches x = -31 mm where the bulk of the field starts near
    # -15, so the whole part slid 16 mm and the trim then cut a 16 mm bare
    # strip along the edge the part is machined from. Measured as 24.8 % of the
    # face carrying no structure, and visible as a stepped diamond of cells
    # sitting on a square slab.
    verts = [(x, y, z + face_h / 2.0) for x, y, z in verts]

    # THE PART MUST BE THE SIZE THAT WAS ASKED FOR. Keeping a whole feature
    # whenever its CENTRE fell inside was the previous rule, and it let every
    # feature straddling an edge hang over: a 100 mm `nested` panel came out
    # 105.4 x 113.0 mm, `honeycomb` 104.4. That is not a 100 mm part. So each
    # polygon is really CUT against the four vertical planes -- Sutherland
    # -Hodgman, which is exact and, unlike clamping every vertex onto the
    # plane, does not collapse a 0.05 mm blade to zero area.
    #
    # The cut leaves open cross-sections where solids were sliced, which is
    # what a sawn part has; `derived` reports the extent so the number on
    # screen is the number a caliper would read.
    def _clip(poly, axis, lo, keep_above):
        out = []
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            da = (a[axis] - lo) if keep_above else (lo - a[axis])
            db = (b[axis] - lo) if keep_above else (lo - b[axis])
            if da >= -1e-9:
                out.append(a)
            if (da > 1e-9 and db < -1e-9) or (da < -1e-9 and db > 1e-9):
                t = da / (da - db)
                out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
        return out

    v2, f2, seen = [], [], {}

    def _idx(v):
        k = (round(v[0], 6), round(v[1], 6), round(v[2], 6))
        if k not in seen:
            seen[k] = len(v2)
            v2.append(k)
        return seen[k]

    for f in faces:
        poly = [verts[i] for i in f]
        for axis, lo, above in ((0, 0.0, True), (0, face_w, False),
                                (2, 0.0, True), (2, face_h, False)):
            if not poly:
                break
            poly = _clip(poly, axis, lo, above)
        if len(poly) >= 3:
            f2.append(tuple(_idx(q) for q in poly))

    if slab is not None:
        lo, hi = slab
        b = len(v2)
        for y in (hi, lo):
            v2 += [(0.0, y, 0.0), (face_w, y, 0.0),
                   (face_w, y, face_h), (0.0, y, face_h)]
        f2 += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4)]
        for i in range(4):
            j = (i + 1) % 4
            f2.append((b + i, b + 4 + i, b + 4 + j, b + j))
    return v2, f2


def mesh_binary(verts, faces):
    """Flat-shaded triangles as float32 [px,py,pz,nx,ny,nz] * 3 per tri."""
    buf = io.BytesIO()
    for f in faces:
        idx = list(f)
        for a in range(1, len(idx) - 1):
            tri = (verts[idx[0]], verts[idx[a]], verts[idx[a + 1]])
            ux, uy, uz = (tri[1][0] - tri[0][0], tri[1][1] - tri[0][1],
                          tri[1][2] - tri[0][2])
            vx, vy, vz = (tri[2][0] - tri[0][0], tri[2][1] - tri[0][1],
                          tri[2][2] - tri[0][2])
            nx, ny, nz = (uy * vz - uz * vy, uz * vx - ux * vz,
                          ux * vy - uy * vx)
            L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            nx, ny, nz = nx / L, ny / L, nz / L
            for q in tri:
                buf.write(struct.pack("<6f", q[0], q[1], q[2], nx, ny, nz))
    return buf.getvalue()


def stl_binary(verts, faces, name="panel"):
    tris = []
    for f in faces:
        idx = list(f)
        for a in range(1, len(idx) - 1):
            tris.append((verts[idx[0]], verts[idx[a]], verts[idx[a + 1]]))
    out = io.BytesIO()
    out.write(b"SpillSink simulator export".ljust(80, b"\0"))
    out.write(struct.pack("<I", len(tris)))
    for t in tris:
        ux, uy, uz = (t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2])
        vx, vy, vz = (t[2][0] - t[0][0], t[2][1] - t[0][1], t[2][2] - t[0][2])
        nx, ny, nz = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        L = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        out.write(struct.pack("<3f", nx / L, ny / L, nz / L))
        for q in t:
            out.write(struct.pack("<3f", q[0], q[1], q[2]))
        out.write(struct.pack("<H", 0))
    return out.getvalue()


def derived(p, verts, spec):
    """The scalars that cost nothing and decide most of the answer."""
    import analyze_buildable as AB
    d = {}
    for attr in ("aspect", "exposed_fraction_est"):
        fn = getattr(p, attr, None)
        if callable(fn):
            try:
                d[attr] = fn()
            except Exception:
                pass
    pitch = getattr(p, "pitch", None) or getattr(p, "pitch_mean", None) \
        or getattr(p, "width_mean", None)
    depth = float(spec.get("depth", 50.0))
    if pitch:
        d.setdefault("aspect", depth / pitch)
        d["pitch"] = pitch
    d["verts"] = len(verts)
    dropped = DROPPED.pop(id(p), [])
    if NEEDS_MARGIN in dropped:
        d["measure_ok"] = False
        d["measure_note"] = ("this family has no margin parameter, so a "
                             "tilted camera reads past the panel edge — "
                             "preview only")
    else:
        d["measure_ok"] = True
    feat, proc = min_feature(spec)
    d["min_feature_mm"] = feat
    d["process"] = proc
    if feat is not None:
        ok, why = AB.buildable(proc, feat)
        d["buildable"] = ok
        d["buildable_note"] = why
    return d


# `strut_r` was missing, so every truss reported "min feature: none" and could
# not be scored for buildability at all -- the one family whose feature is a
# radius rather than a wall.
FEATURE_KEYS = ("wall_top", "wall_bot", "plate_t_top", "plate_t_bot",
                "tip_width", "thickness", "tip_flat", "strut_r")
PROC_OF = {"comb": "expanded foil", "honeycomb": "expanded foil",
           "shingle": "sheet, grid", "truss": "sheet, lanced",
           "cone": "mould", "pyramid": "press", "wave": "press",
           "gap": "none", "vgroove": "print", "slat": "print",
           "trough": "print", "square": "print", "triangle": "print",
           "mixed": "print", "reentrant": "print", "nested": "print"}


def min_feature(spec):
    best = None
    for kind, prm in ((spec["top"], spec.get("top_params") or {}),
                      (spec.get("floor", "none"),
                       spec.get("floor_params") or {})):
        if kind == "none":
            continue
        # a recorded 0 means "as sharp as the process allows", not "0 mm of
        # material". Treating it as a feature made the panel read 0.000 mm and
        # unbuildable for every pressed floor.
        vals = [float(prm[k]) for k in FEATURE_KEYS
                if k in prm and float(prm[k]) > 1e-9]
        if kind in ("cone",) and "tip_radius" in prm:
            vals.append(2.0 * float(prm["tip_radius"]))
        if kind == "truss" and "strut_r" in prm:      # radius -> diameter
            vals = [v * 2.0 if k == "strut_r" else v
                    for k, v in zip(FEATURE_KEYS, vals)] or vals
        if not vals:
            continue
        v = min(vals)
        if best is None or v < best[0]:
            best = (v, PROC_OF.get(kind, "print"))
    return best if best else (None, None)


# --- coatings ---------------------------------------------------------------
#
# A named coating is one number: rho_dh at normal incidence. The diffuse
# fraction then splits it between a Lambertian body and a Fresnel lobe, and
# `roughness` shapes that lobe. Only rho0 distinguishes the products.
#
# EVERY VALUE HERE HAS A SOURCE, and the two that do not agree say so.
COATINGS = {
    "musou_air": (0.0060, "Musou Black, airbrushed \u2014 0.6 % total "
                          "reflectance at 550 nm, AOI 8 deg integrating "
                          "sphere [musoublack.com product spec]"),
    "musou_fit": (0.00998, "Musou Black as fitted in this project \u2014 "
                           "Filip & V\u00e1vra 2026 JOSA A 43, 1037, "
                           "RGB-weighted 380\u2013700 nm. Every number in "
                           "phases 2\u20135 uses this."),
    "musou_brush": (0.0110, "Musou Black, brush-applied \u2014 1.1 % or "
                            "lower [the-black-market.com]. 1.8x the airbrushed "
                            "figure; application method is a larger lever than "
                            "any geometry parameter measured so far."),
    "anodised_lo": (0.030, "Black anodised aluminium, optimistic end. Sources "
                           "disagree: 'below 5 % in the visible' vs 'at least "
                           "5 %'. Swept, not assumed."),
    "anodised": (0.045, "Black anodised aluminium, nominal \u2014 what bought "
                        "honeycomb actually arrives as [arXiv 1407.8265; "
                        "Rubin M2 baffle]."),
    "anodised_hi": (0.060, "Black anodised aluminium, pessimistic end."),
    "wall_5pct": (0.050, "Plain matte black wall \u2014 the control patch in "
                         "every render."),
}


def coatings_json():
    return {k: {"rho0": v[0], "note": v[1]} for k, v in COATINGS.items()}


def _coat(name, diffuse_frac, default="musou_fit"):
    import blender_render as BR
    rho0 = COATINGS.get(name, COATINGS[default])[0]
    body, spec = BR.coating_split(float(diffuse_frac), rho0=rho0)
    return {"body": body, "spec_scale": spec}


# --- measurement ------------------------------------------------------------

def _t(msg):
    print("[SIM] %s" % msg, flush=True)


AUDIT_THETA_LIMIT = 60.0  # 2026-08-17 audit: margin_depths=2.0 leaks
# background past the panel above ~69 deg; lock/sweeps use 6.5 and are safe.

def measure(spec, thetas, diffuse_frac, roughness, samples,
            coating="musou_fit", deep_coating=None, paint_depth=None,
            deep_until=None, paint_fade=0.0, phis=None):
    _t("measure: enter")
    import blender_render as BR
    from cone3d_sweep import COAT
    cc = _coat(coating, diffuse_frac)
    body, sspec = cc["body"], cc["spec_scale"]
    # measurement margin, NOT the preview margin: a tilted camera reads world
    # background otherwise and the number is quietly wrong.
    # The mesh is NOT built here: BR.run builds its own scene from `params`.
    # Building it twice cost a full extra copy of a 200k-vert mesh per click.
    # 2026-08-17 audit: margin 2.0 leaks background past the panel above
    # ~69 deg; widen to the lock-grade 6.5 when any requested angle is steep.
    steep = any(abs(float(t)) > AUDIT_THETA_LIMIT for t in thetas)
    m = dict(spec, margin_depths=6.5 if steep else 2.0)
    _t("measure: build ok")
    prm = _render_params(m)
    cfg = {"tag": "sim_%d" % int(time.time() * 1000),
           "family": _render_family(m),
           "out_dir": "/tmp/simsrv", "results_dir": "/tmp/simsrv",
           "samples": int(samples), "res_x": 480, "res_y": 220, "gpu": True,
           "spec_roughness": float(roughness),
           "coating": {"body": body, "spec_scale": sspec,
                       "roughness": float(roughness)},
           "params": prm,
           "renders": [{"mode": "hemi_view", "theta": float(t)}
                       for t in thetas]}
    cfg.update({k: v2 for k, v2 in COAT.items() if k != "spec_roughness"})
    cfg["material_mode"] = "coating"
    # Paint only reaches so far into a cell; below `paint_depth` the surface
    # is whatever the part was bought as. Without BOTH a depth and a deep
    # coating there is no split and the whole mesh keeps one finish.
    if paint_depth is not None and deep_coating:
        cfg["paint_depth"] = float(paint_depth)
        cfg["deep_coating"] = _coat(deep_coating, diffuse_frac,
                                    default="anodised")
        # a stacked design's floor is its own painted part
        if deep_until is None and spec.get("floor", "none") != "none":
            deep_until = float(spec.get("depth", 50.0)) \
                - float(spec.get("floor_depth", 0.0))
        if deep_until is not None:
            cfg["deep_until"] = float(deep_until)
        cfg["paint_fade"] = float(paint_fade or 0.0)
        _t("measure: paint to %.1f mm, %s below" % (float(paint_depth),
                                                    deep_coating))
    # The camera tilts in one plane, so one run is ONE azimuth of incidence.
    # phi rotates the panel about its normal (blender_render handles it); each
    # extra plane is a full re-run -- scene rebuilt, all thetas re-read.
    phis = [float(x) for x in (phis or [0.0])]
    n_all = len(phis) * len(cfg["renders"])
    _t("measure: calling BR.run, %d angle(s) x %d plane(s)"
       % (len(cfg["renders"]), len(phis)))
    planes = {}
    try:
        for pi, phi in enumerate(phis):
            c2 = dict(cfg, phi_deg=phi, tag="%s_p%g" % (cfg["tag"], phi))
            BR.PROGRESS_CB = (lambda i, n, off=pi * len(cfg["renders"]):
                              _prog(off + i, n_all))
            res = BR.run(c2)
            planes["%g" % phi] = {"%.0f" % r["theta"]: r["panel"]["mean"]
                                  for r in res["modes"].values()}
    finally:
        _prog(n_all, n_all)
    _t("measure: BR.run returned")
    return planes


def measure_lambert(spec, theta, rho, samples):
    """Cycles, same design, same pure Lambertian -- the other half of the pair."""
    import blender_render as BR
    from cone3d_sweep import COAT
    # progress is counted per ANGLE by the /api/measure loop that calls this;
    # a leftover per-frame hook from measure() would stomp it with "0/1"
    BR.PROGRESS_CB = None
    m = dict(spec, margin_depths=2.0)
    cfg = {"tag": "xc_%d" % int(time.time() * 1000),
           "family": _render_family(m),
           "out_dir": "/tmp/simsrv", "results_dir": "/tmp/simsrv",
           "samples": int(samples), "res_x": 480, "res_y": 220, "gpu": True,
           "material_mode": "all_diffuse", "rho_slat": rho,
           "rho_chamber": rho, "rho_specular": rho, "rho_control": 0.05,
           "params": _render_params(m),
           "renders": [{"mode": "hemi_view", "theta": float(theta)}]}
    cfg.update({k: v for k, v in COAT.items()
                if k not in ("rho_slat", "rho_chamber", "rho_specular")})
    res = BR.run(cfg)
    return list(res["modes"].values())[0]["panel"]["mean"]


def _render_family(spec):
    if spec.get("floor", "none") != "none":
        return "stack"
    return {"cone": "cone3d", "comb": "topo", "honeycomb": "topo",
            "shingle": "topo", "truss": "topo", "vgroove": "ridge",
            "flat": "floor", "slat": "slat", "trough": "scatter",
            "pyramid": "floor"}.get(spec["top"], "cell")


def _render_params(spec):
    face = float(spec.get("panel", spec.get("face", 100.0)))
    depth = float(spec.get("depth", 50.0))
    seed = int(spec.get("seed", 23))
    common = dict(face_w=face, face_h=face, margin_depths=2.0,
                  backing=float(spec.get("backing", 2.0)))
    if spec.get("floor", "none") == "none":
        mod, cname, fixed = FAMILIES[spec["top"]]
        # Same fill as `build`. Without it an API call that omits `top_params`
        # measured the dataclass defaults while the viewport, which always gets
        # slider values, showed the published design -- two different parts
        # under one answer.
        tp = dict(NORMAL.get(spec["top"], {}), **(spec.get("top_params") or {}))
        tp.pop("depth", None)
        return dict(fixed, **tp, **common, depth=depth, **_seed_kw(mod, seed))
    fd = float(spec.get("floor_depth", 0.0))
    fp = dict(spec.get("floor_params") or {})
    if spec["floor"] in ("pyramid", "wave", "gap"):
        fp["margin_depth_ref"] = depth
    return dict(common, seed=seed, top=STACK_KIND[spec["top"]],
                top_depth=depth - fd,
                top_params=dict(spec.get("top_params") or {}),
                bot=STACK_KIND[spec["floor"]], bot_depth=fd, bot_params=fp)


# --- form destruction and head-on brightness --------------------------------

def form(spec, thetas=None, n_phase=None, samples=None, beam_w=None,
         phis=None):
    """The other two axes, through `form_buildable`'s own code.

    NOT reimplemented here. `form_buildable.run_case` is what produced every
    smear and head-on figure in phases 2-4; calling it means a live number and
    a published number cannot drift apart by construction. The only things
    overridden are the ones that buy latency:

        N_PHASE  16 -> 6    stripe positions across one pitch
        THETAS   3  -> 2    drop 0 deg for smear (it is a +-40 metric)
        SAMPLES  512 -> 256

    Full fidelity is 48 frames at 512 spp, about 300 s. The reduced setting is
    ~12 frames and lands near a minute, which is a button rather than a batch
    job. The UI must say which it ran, because a 6-phase smear is NOT the
    number in the report -- it is an estimate of it, and this project has
    already shipped one figure that was quietly a different statistic from the
    one beside it.
    """
    import form_buildable as FB
    m = dict(spec, margin_depths=2.0)
    prm = _render_params(m)
    pitch = (spec.get("top_params") or {}).get("pitch") \
        or (spec.get("top_params") or {}).get("pitch_mean") or 6.5
    # `run_case` copies entry["topology"] straight into its record, so the key
    # is required even though nothing computes with it.
    topo = spec["top"] if spec.get("floor", "none") == "none" \
        else "%s/%s" % (spec["top"], spec["floor"])
    entry = {"tag": "sim_form_%d" % int(time.time() * 1000),
             "family": _render_family(m), "topology": topo,
             "process": min_feature(spec)[1] or "unknown",
             "params": prm, "pitch": pitch}
    # The probe beam width at the wall. Phase 5.4/5.5 showed smear depends on
    # beam/pitch, so this is a first-class knob, not a protocol constant. The
    # default stays the historical 2.0 so old numbers keep reproducing.
    phis = [float(x) for x in (phis or [0.0])]
    old = (FB.N_PHASE, FB.THETAS, FB.SAMPLES, FB.STRIPE_W)
    FB.N_PHASE = int(n_phase or 6)
    FB.THETAS = tuple(thetas or (-40.0, 40.0, 0.0))
    FB.SAMPLES = int(samples or 256)
    FB.STRIPE_W = float(beam_w or 7.5)
    n_frames = FB.N_PHASE * len(FB.THETAS)
    planes = {}
    try:
        for pi, phi in enumerate(phis):
            e2 = dict(entry, tag="%s_p%g" % (entry["tag"], phi))
            if abs(phi) > 1e-9:
                e2["phi"] = phi
            # The stripe's phase walk spans one `pitch` of world z. Rotated
            # 45 deg, a square grid repeats along z every pitch*sqrt(2); walk
            # that, or the phase mean under-covers its period by 29 % (the
            # run_case comment accepts phi <= 30 only). Exact for the square
            # pyramid grid; for other families it is an approximation, and
            # 90 deg needs no correction (the grid maps onto itself).
            if abs(phi % 90.0 - 45.0) < 1e-9:
                e2["pitch"] = float(entry["pitch"]) * math.sqrt(2.0)
            FB.PROGRESS_CB = (lambda i, n, off=pi * n_frames:
                              _prog(off + i, len(phis) * n_frames))
            rec = FB.run_case(e2)
            t = rec.get("thetas", {})
            a, b = t.get("-40"), t.get("+40")
            planes["%g" % phi] = {
                "smear": (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                                 + b["rms_mm"] / b["rms_control_mm"])
                          if a and b else None),
                "peak": (t.get("+0") or {}).get("peak_ratio_mean")}
    finally:
        FB.N_PHASE, FB.THETAS, FB.SAMPLES, FB.STRIPE_W = old
        _prog(len(phis) * n_frames, len(phis) * n_frames)
    # the dashboard reports the WORST plane: smear-up is good so worst is the
    # lowest; head-on-down is good so worst is the highest
    sm = [p["smear"] for p in planes.values() if p["smear"] is not None]
    pk = [p["peak"] for p in planes.values() if p["peak"] is not None]
    return {"smear": min(sm) if sm else None,
            "peak": max(pk) if pk else None,
            "planes": planes,
            "n_phase": int(n_phase or 6),
            "samples": int(samples or 256),
            "beam_w": float(beam_w or 7.5), "reduced": True}


def form_lambert(spec, rho=0.01, n_phase=6, samples=256,
                 thetas=(-40.0, 40.0, 0.0), beam_w=None):
    """The form axes in Cycles with a PURE LAMBERTIAN, for the cross-check.

    `form` runs the fitted coating and is the published path. This runs the
    identical experiment on the one material both renderers can be asked for
    exactly, which is the only way a difference between them means transport
    rather than materials.
    """
    import form_buildable as FB
    m = dict(spec, margin_depths=2.0)
    prm = _render_params(m)
    pitch = (spec.get("top_params") or {}).get("pitch") \
        or (spec.get("top_params") or {}).get("pitch_mean") or 6.5
    topo = spec["top"] if spec.get("floor", "none") == "none" \
        else "%s/%s" % (spec["top"], spec["floor"])
    entry = {"tag": "sim_xform_%d" % int(time.time() * 1000),
             "family": _render_family(m), "topology": topo,
             "process": min_feature(spec)[1] or "unknown",
             "params": prm, "pitch": pitch, "rho": float(rho),
             "rho_control": 0.05}
    old = (FB.N_PHASE, FB.THETAS, FB.SAMPLES, FB.STRIPE_W)
    FB.N_PHASE = int(n_phase)
    FB.THETAS = tuple(thetas)
    FB.SAMPLES = int(samples)
    FB.STRIPE_W = float(beam_w or 7.5)
    FB.PROGRESS_CB = _prog
    _prog(0, FB.N_PHASE * len(FB.THETAS))
    try:
        rec = FB.run_case(entry)
    finally:
        FB.N_PHASE, FB.THETAS, FB.SAMPLES, FB.STRIPE_W = old
    t = rec.get("thetas", {})
    a, b, z = t.get("-40"), t.get("+40"), t.get("+0")
    return {"smear": (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                             + b["rms_mm"] / b["rms_control_mm"])
                      if a and b else None),
            "head_on": z["peak_ratio_mean"] if z else None,
            "thetas": t}


def form_mitsuba(spec, rho=0.01, n_phase=6, spp=256, beam_w=None):
    """The same, in Mitsuba, as a subprocess."""
    return _mts(dict(_mts_req(spec, rho=rho), op="form",
                     pitch=(spec.get("top_params") or {}).get("pitch")
                     or (spec.get("top_params") or {}).get("pitch_mean")
                     or 6.5,
                     n_phase=int(n_phase), spp=int(spp),
                     beam_w=float(beam_w or 2.0)))


def _mts_req(spec, rho=0.01, theta=0.0, spp=256):
    m = dict(spec, margin_depths=2.0)
    return {"family": _render_family(m), "params": _render_params(m),
            "rho": rho, "theta": theta, "spp": spp}


def _mts(req):
    """Run `mts_worker` in the Mitsuba venv and read its marker line."""
    import subprocess
    venv = os.environ.get("MTS_PYTHON", os.path.join(
        "/private/tmp/claude-501",
        "-Users-hojunsong-Desktop-Desktop---hojun-s-mbp-SpillSinkSimulator",
        "ea0cb560-6b35-43aa-9df7-9e47dc4396fa", "scratchpad",
        "mts_env", "bin", "python"))
    if not os.path.exists(venv):
        return {"error": "Mitsuba venv not found at %s" % venv}
    # Streamed, not run(): the worker prints @@PROG@@ lines per frame and the
    # UI polls /api/progress, so the output must be read while it renders.
    # stderr merges into stdout -- separate pipes deadlock once one fills.
    p = subprocess.Popen([venv, os.path.join(HERE, "mts_worker.py")],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    lines = []
    try:
        p.stdin.write(json.dumps(req))
        p.stdin.close()
        for line in p.stdout:
            lines.append(line)
            if line.startswith("@@PROG@@"):
                try:
                    _, d, t = line.split()
                    _prog(int(d), int(t))
                except Exception:
                    pass
        p.wait(timeout=3600)
    except Exception as e:
        p.kill()
        return {"error": str(e)}
    if p.returncode != 0:
        return {"error": "".join(lines)[-300:]}
    for line in reversed(lines):
        i = line.find("@@RESULT@@")
        if i >= 0:
            try:
                return json.loads(line[i + 10:])
            except Exception:
                break
    return {"error": "".join(lines)[-300:]}


def measure_mitsuba(spec, theta=0.0, rho=0.01, spp=256):
    """The same design in the other renderer, as a subprocess.

    Returns Cycles' answer for the SAME Lambertian alongside it, because a
    single number from a second code is not a cross-check -- the pair is.
    """
    import subprocess
    venv = os.environ.get("MTS_PYTHON", os.path.join(
        "/private/tmp/claude-501",
        "-Users-hojunsong-Desktop-Desktop---hojun-s-mbp-SpillSinkSimulator",
        "ea0cb560-6b35-43aa-9df7-9e47dc4396fa", "scratchpad",
        "mts_env", "bin", "python"))
    if not os.path.exists(venv):
        return {"error": "Mitsuba venv not found at %s" % venv}
    m = dict(spec, margin_depths=2.0)
    req = {"family": _render_family(m), "params": _render_params(m),
           "rho": rho, "theta": theta, "spp": spp}
    p = subprocess.run([venv, os.path.join(HERE, "mts_worker.py")],
                       input=json.dumps(req), capture_output=True, text=True,
                       timeout=900)
    if p.returncode != 0:
        return {"error": (p.stderr or "")[-300:]}
    for line in reversed((p.stdout or "").splitlines()):
        i = line.find("@@RESULT@@")
        if i >= 0:
            try:
                return json.loads(line[i + 10:])
            except Exception:
                break
    return {"error": (p.stdout or p.stderr or "")[-300:]}


# --- checking the live number against what was published --------------------

_PUB = None
_PUB_STAMP = None


def _sweep_stamp():
    """Newest mtime across the sweep CSVs, so the cache can tell it is stale."""
    import glob
    t = 0.0
    for path in glob.glob(os.path.join(ROOT, "results", "sweep_*.csv")):
        if "__void__" in path:
            continue
        try:
            t = max(t, os.path.getmtime(path))
        except OSError:
            pass
    return t


def published():
    """Every scored design in the study, keyed by its recorded params.

    This is the whole point of the tool: dial in a design that was published
    and confirm the live path produces the same number. It is gate check 8 with
    a slider on it.
    """
    # Reload when a sweep changes. The first version cached forever, so a
    # server left running through a re-measurement kept serving the old
    # numbers -- and this panel exists precisely to notice when a number moves.
    # The V-groove sat at its pre-fix 0.3863 % in the menu while the CSV on
    # disk said 0.3553 %.
    global _PUB, _PUB_STAMP
    stamp = _sweep_stamp()
    if _PUB is not None and _PUB_STAMP == stamp:
        return _PUB
    _PUB_STAMP = stamp
    import csv
    import glob
    import collections
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "results",
                                              "sweep_*.csv"))):
        if "__void__" in path:
            continue
        try:
            rows = list(csv.DictReader(open(path)))
        except Exception:
            continue
        if not rows or "params_json" not in rows[0] or "rho" not in rows[0]:
            continue
        per, meta = collections.defaultdict(dict), {}
        for r in rows:
            key = (r["tag"], r.get("diffuse_frac", "d76"))
            try:
                per[key][float(r["theta"])] = float(r["rho"])
            except (TypeError, ValueError):
                continue
            meta[r["tag"]] = r
        worst = {}
        for (tag, mat), d in per.items():
            if len(d) == 5:
                worst.setdefault(tag, {})[mat] = max(d.values())
        by = collections.defaultdict(list)
        for tag, m in worst.items():
            by[tag.rsplit("_s", 1)[0]].append(max(m.values()))
        for base, vals in by.items():
            tag = next(t for t in worst if t.rsplit("_s", 1)[0] == base)
            try:
                prm = json.loads(meta[tag]["params_json"])
            except Exception:
                continue
            out.append({"source": os.path.basename(path), "design": base,
                        "worst_rho": sum(vals) / len(vals), "n": len(vals),
                        "params": prm})
    _PUB = out
    return out


# params that describe how a thing was MEASURED, not what it is
BOILERPLATE = {"face_w", "face_h", "backing", "margin_depths", "seed",
               "margin_depth_ref", "pitch_seed", "width_seed"}


def presets():
    """Every published design, as something the UI can load in one click.

    The tool used to open on `TopoParams`' own defaults -- pitch 7.5, wall
    0.4/1.2 -- which is not a product anyone would buy and is not a design in
    any report, so the study-comparison panel read "0% match" on a fresh load
    and the first impression of the whole tool was a number that meant nothing.
    The presets come from the same CSVs the reports were built from, so the
    first thing on screen is a real measured design.
    """
    inv = {v[2].get("topology") or v[2].get("variant") or k: k
           for k, v in FAMILIES.items()}
    inv.update({"cone": "cone", "shingle": "shingle"})
    out = []
    for e in published():
        prm = e["params"]
        stacked = "top" in prm
        top = prm.get("top") or prm.get("topology") or prm.get("variant")
        if top is None and "tip_radius" in prm:
            top = "cone"
        if top is None and "tip_width" in prm:
            top = "vgroove"
        if top not in FAMILIES:
            continue
        floor = prm.get("bot") if stacked else "none"
        if floor is not None and floor not in FLOORS:
            continue
        drop = {"face_w", "face_h", "margin_depths", "backing", "seed",
                "depth", "top", "bot", "top_depth", "bot_depth",
                "top_params", "bot_params", "topology", "variant",
                "pitch_seed", "width_seed", "margin_depth_ref"}
        tp = dict(prm.get("top_params") or
                  {k: v for k, v in prm.items() if k not in drop})
        fp = {k: v for k, v in (prm.get("bot_params") or {}).items()
              if k not in drop}
        depth = (prm.get("top_depth", 0) + prm.get("bot_depth", 0)) \
            if stacked else prm.get("depth", 50.0)
        out.append({
            "design": e["design"], "source": e["source"],
            "worst_rho": e["worst_rho"], "n_seeds": e["n"],
            "spec": {"top": top, "top_params": tp,
                     "floor": floor or "none", "floor_params": fp,
                     "depth": depth,
                     "floor_depth": prm.get("bot_depth", 0.0),
                     "face": 60, "margin_depths": 0.2}})
    out.sort(key=lambda r: r["worst_rho"])
    # 897 entries in a dropdown is not a menu, it is a haystack. Only the
    # designs the reports actually argue about are named and offered; the rest
    # stay reachable through the study-comparison panel, which finds the
    # nearest published row to whatever the sliders currently say.
    # One row per DESIGN, not per source file. `B_CONE_p0550` is measured in
    # three sweeps and appeared three times in the menu with three different
    # numbers -- which are three seed samples of one geometry, not three
    # designs. Keep the best-sampled one and say how many seeds it rests on.
    best = {}
    for e in out:
        e["headline"] = HEADLINE.get(e["design"])
        cur = best.get(e["design"])
        if cur is None or e["n_seeds"] > cur["n_seeds"]:
            best[e["design"]] = e
    return sorted(best.values(), key=lambda r: r["worst_rho"])


# design id -> the name it carries in a report, and which phase it belongs to
HEADLINE = {
    "P1_groove_p13_t04":       "1 · V-groove 13 mm (best extruded)",
    "B_CONE_p0550":            "2 · Cone 5.5 (the incumbent)",
    "CB_p0650_f080_x10":       "2 · Honeycomb 6.5 / 0.08 (bought)",
    "CB_p0520_f040_x10":       "2 · Honeycomb 5.2 / 0.04 (below floor)",
    "BL_FLAT_t050_p0550_a02_grid": "2 · Blade 0.05 grid (darkest buildable)",
    "BL_FLAT_t100_p0550_a02_grid": "2 · Blade 0.10 grid",
    "B_HONE_p0650_f080":       "2 · Honeycomb, Voronoi cells",
    "ST_comb-comb_50":         "3 · Honeycomb over finer honeycomb",
    "ST_comb-cone_50":         "3 · Honeycomb over cones",
    "ST_cone-comb_50":         "3 · Cones over honeycomb (best head-on)",
    "ST_shin-comb_50":         "3 · Blades over honeycomb",
    "FL_p650f080_flat_d00":    "4 · Honeycomb, flat floor (control)",
    "FL_p650f080_pyramid_d30": "4 · Honeycomb + pyramid floor 3 mm",
    "FL_p650f080_gap_d30":     "4 · Honeycomb + air gap (does nothing)",
    "FL_bl050o115_flat_d00":   "4 · Blade 0.05, flat floor (control)",
    "FL_bl050o115_pyramid_d30": "4 · Blade 0.05 + pyramid  ★ 3-axis best",
}


def nearest(spec):
    """The published design closest to what is on screen, and how close."""
    target = _render_params(spec)

    def flat(d, pre=""):
        o = {}
        for k, v in d.items():
            if isinstance(v, dict):
                o.update(flat(v, pre + k + "."))
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                o[pre + k] = float(v)
            elif isinstance(v, str):
                o[pre + k] = v
        return o
    t = flat(target)
    best = None
    for e in published():
        p = flat(e["params"])
        common = set(t) & set(p)
        if len(common) < 5:
            continue
        num = [c for c in common if isinstance(t[c], float)
               and isinstance(p[c], float)]
        if not num:
            continue
        # Identity first. The first version scored on numeric distance alone
        # and confidently reported a blade array as an EXACT match for a
        # honeycomb, because the two share face_w, face_h, depth, backing,
        # margin_depths and seed -- six numbers that describe the MEASUREMENT,
        # not the design.
        if any(isinstance(t[c], str) and t[c] != p[c] for c in common):
            continue
        real = [c for c in num if c.split(".")[-1] not in BOILERPLATE]
        if len(real) < 2:
            continue
        err = sum(abs(t[c] - p[c]) / (abs(p[c]) + 1e-6) for c in real) \
            / len(real)
        if best is None or err < best[0]:
            best = (err, e, len(common))
    if best is None:
        return None
    err, e, ncommon = best
    return {"design": e["design"], "source": e["source"],
            "worst_rho": e["worst_rho"], "n_seeds": e["n"],
            "match": max(0.0, 1.0 - err), "shared_params": ncommon,
            "exact": err < 1e-9}


# --- HTTP -------------------------------------------------------------------

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            f = os.path.join(UI, "index.html")
            if not os.path.exists(f):
                return self._send(404, "build the UI first", "text/plain")
            # the UI changes between reloads while this server stays up; a
            # cached copy means the user presses buttons wired to old code
            return self._send(200, open(f, "rb").read(), "text/html",
                              {"Cache-Control": "no-store"})
        if p == "/api/families":
            return self._send(200, json.dumps(families_json()))
        if p == "/api/coatings":
            return self._send(200, json.dumps(coatings_json()))
        if p == "/api/presets":
            return self._send(200, json.dumps({"presets": presets()}))
        if p == "/api/health":
            return self._send(200, json.dumps({"ok": True, "port": PORT}))
        if p == "/api/progress":
            return self._send(200, json.dumps(PROG))
        return self._send(404, json.dumps({"error": "no such path"}))

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send(400, json.dumps({"error": str(e)}))
        try:
            if self.path == "/api/mesh":
                t0 = time.perf_counter()
                try:
                    v, f, p = build(req)
                    if not req.get("full_extent"):
                        fw = float(req.get("panel", req.get("face", 100.0)))
                        v, f = clip_to_panel(v, f, fw, fw)
                except Exception as exc:
                    # A slider can be dragged into a combination the geometry
                    # cannot express -- 0 truss layers, a cone whose secondary
                    # array is the same size as the primary. That is not a
                    # crash to show a traceback for; it is a state the UI
                    # should name and recover from.
                    return self._send(200, b"", "application/octet-stream",
                                      {"X-Derived": json.dumps(
                                          {"invalid": True,
                                           "why": "%s: %s" % (
                                               type(exc).__name__,
                                               str(exc)[:160])})})
                # An EMPTY build is a legal answer, not a success. `mixed`
                # at mixed_keep = 0 keeps none of its cells, `gap` floors are
                # empty by definition, and a clip can leave nothing behind.
                # Reported as valid it drew a black viewport and no text, which
                # is indistinguishable from a crash. Name it.
                if not v or not f:
                    return self._send(200, b"", "application/octet-stream",
                                      {"X-Derived": json.dumps(
                                          {"invalid": True,
                                           "why": "this setting produces no "
                                                  "geometry at all"})})
                d = derived(p, v, req)
                blob = mesh_binary(v, f)
                d["build_ms"] = round((time.perf_counter() - t0) * 1000, 1)
                return self._send(200, blob, "application/octet-stream",
                                  {"X-Derived": json.dumps(d)})
            if self.path == "/api/measure":
                t0 = time.perf_counter()
                rend = req.get("renderer", "cycles")
                if rend in ("mitsuba", "both"):
                    # Mitsuba has no construction identical to the Cycles
                    # coating node graph, so anything it measures is on a pure
                    # Lambertian -- the one material both codes share exactly.
                    # The UI says so; it is not the published coating.
                    rho0 = float(req.get("lambert_rho", 0.01))
                    ths = req.get("thetas", [0.0])
                    # one continuous scale over both codes: Mitsuba angles
                    # first, then (for "both") the same angles in Cycles
                    n_steps = len(ths) * (2 if rend == "both" else 1)
                    mts = {}
                    for i, th in enumerate(ths):
                        _prog(i, n_steps)
                        one = measure_mitsuba(req["spec"], float(th), rho0,
                                              int(req.get("samples", 256)))
                        if "error" in one:
                            return self._send(200, json.dumps(one))
                        mts["%g" % float(th)] = one["rho_dh"]
                    out = {"renderer": rend, "lambert_rho": rho0,
                           "mitsuba": mts,
                           "seconds": round(time.perf_counter() - t0, 2)}
                    if rend == "both":
                        cyc = {}
                        for i, th in enumerate(ths):
                            _prog(len(ths) + i, n_steps)
                            r2 = in_blender("lambert", spec=req["spec"],
                                            theta=float(th), rho=rho0,
                                            samples=int(req.get("samples",
                                                                512)))
                            if "error" in r2:
                                return self._send(200, json.dumps(r2))
                            cyc["%g" % float(th)] = r2["rho"]
                        out["cycles"] = cyc
                        out["diff"] = {k: (mts[k] - cyc[k]) / max(cyc[k], 1e-15)
                                       for k in cyc}
                    out["rho"] = mts
                    out["seconds"] = round(time.perf_counter() - t0, 2)
                    return self._send(200, json.dumps(out))
                r = in_blender("measure", spec=req["spec"],
                               thetas=req.get("thetas", [0.0]),
                               diffuse_frac=req.get("diffuse_frac", 0.76),
                               roughness=req.get("roughness", 0.30),
                               samples=req.get("samples", 64),
                               coating=req.get("coating", "musou_fit"),
                               deep_coating=req.get("deep_coating"),
                               paint_depth=req.get("paint_depth"),
                               deep_until=req.get("deep_until"),
                               paint_fade=req.get("paint_fade", 0.0),
                               phis=req.get("phis"))
                if "error" in r:
                    return self._send(200, json.dumps(r))
                # `rho` stays the phi-0 plane so old callers keep working;
                # `rho_planes` carries every measured azimuth plane
                planes = r["rho"]
                return self._send(200, json.dumps(
                    {"rho": planes.get("0") or next(iter(planes.values())),
                     "rho_planes": planes,
                     "seconds": round(time.perf_counter() - t0, 2)}))
            if self.path == "/api/form":
                t0 = time.perf_counter()
                rend = req.get("renderer", "cycles")
                if rend in ("mitsuba", "both"):
                    rho0 = float(req.get("lambert_rho", 0.01))
                    m = form_mitsuba(req["spec"], rho0,
                                     int(req.get("n_phase") or 6),
                                     int(req.get("samples") or 256),
                                     beam_w=req.get("beam_w"))
                    if "error" in m:
                        return self._send(200, json.dumps(m))
                    out = {"renderer": rend, "lambert_rho": rho0,
                           "smear": m["smear"], "head_on": m["head_on"],
                           "mitsuba": {"smear": m["smear"],
                                       "head_on": m["head_on"]}}
                    if rend == "both":
                        c = in_blender("form_lambert", spec=req["spec"],
                                       rho=rho0,
                                       n_phase=int(req.get("n_phase") or 6),
                                       samples=int(req.get("samples") or 256),
                                       beam_w=req.get("beam_w"))
                        if "error" in c:
                            return self._send(200, json.dumps(c))
                        out["cycles"] = {"smear": c["smear"],
                                         "head_on": c["head_on"]}
                        out["diff"] = {
                            k: ((m[k] - c[k]) / c[k]) if c.get(k) else None
                            for k in ("smear", "head_on")}
                    out["seconds"] = round(time.perf_counter() - t0, 1)
                    return self._send(200, json.dumps(out))
                out = in_blender("form", spec=req["spec"], thetas=None,
                                 n_phase=req.get("n_phase"),
                                 samples=req.get("samples"),
                                 beam_w=req.get("beam_w"),
                                 phis=req.get("phis"))
                if "error" in out:
                    return self._send(200, json.dumps(out))
                out["seconds"] = round(time.perf_counter() - t0, 1)
                return self._send(200, json.dumps(out))
            if self.path == "/api/crosscheck":
                t0 = time.perf_counter()
                th = float(req.get("theta", 0.0))
                rho = float(req.get("rho", 0.01))
                mts = measure_mitsuba(req["spec"], th, rho,
                                      int(req.get("spp", 256)))
                cyc = None
                if "error" not in mts:
                    r = in_blender("lambert", spec=req["spec"], theta=th,
                                    rho=rho, samples=int(req.get("spp", 512)))
                    if "error" in r:
                        return self._send(200, json.dumps(
                            {"mitsuba": mts, "cycles": None,
                             "error": r["error"]}))
                    cyc = r["rho"]
                out = {"mitsuba": mts, "cycles": cyc,
                       "seconds": round(time.perf_counter() - t0, 1)}
                if cyc and "error" not in mts:
                    out["diff"] = (mts["rho_dh"] - cyc) / max(cyc, 1e-12)
                return self._send(200, json.dumps(out))
            if self.path == "/api/report_pdf":
                # Real-text PDF with no print dialog: the page sends its
                # fully-inlined print HTML (view/chart/logo as data URIs) and
                # headless Chrome typesets it. Fonts stay fonts -- the first
                # report was one big JPEG and the user caught it. Runs on a
                # worker thread; no bpy involved.
                html = req.get("html", "")
                if not html:
                    return self._send(400, json.dumps({"error": "no html"}))
                chrome = ("/Applications/Google Chrome.app/Contents/MacOS"
                          "/Google Chrome")
                if not os.path.exists(chrome):
                    return self._send(200, json.dumps(
                        {"error": "Chrome not found at %s" % chrome}))
                import subprocess
                import tempfile
                import shutil
                out_dir = "/tmp/simsrv"
                os.makedirs(out_dir, exist_ok=True)
                # ONE fresh dir per request holds profile, input and output:
                # - a reused profile keeps its SingletonLock if chrome ever
                #   dies mid-run, and every later print fails with "Failed
                #   to create a ProcessSingleton" (seen live 2026-08-18)
                # - shared src/dst names would let two concurrent clicks
                #   read each other's files
                work = tempfile.mkdtemp(prefix="pdf_", dir=out_dir)
                src = os.path.join(work, "report.html")
                dst = os.path.join(work, "report.pdf")
                with open(src, "w") as f:
                    f.write(html)
                pdf = None
                try:
                    # Chrome 151 headless on this machine writes the PDF in
                    # seconds and then NEVER exits -- waiting for the process
                    # put a flat 60 s on every report (measured 60.07 s for a
                    # one-line page). So: watch for the finished file (chrome
                    # writes it once, at the end; one stable size check to be
                    # safe) and kill chrome ourselves.
                    proc = subprocess.Popen(
                        [chrome, "--headless", "--disable-gpu",
                         "--no-pdf-header-footer",
                         # let deferred work (big data-URI images decoding)
                         # finish before the print fires: one cold-start run
                         # shipped the page without its 3D view (330 KB
                         # instead of 1.1 MB, 2026-08-18)
                         "--virtual-time-budget=10000",
                         "--user-data-dir=" + os.path.join(work, "prof"),
                         "--print-to-pdf=" + dst, "file://" + src],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    deadline, last = time.time() + 60, -1
                    while time.time() < deadline:
                        if os.path.exists(dst):
                            sz = os.path.getsize(dst)
                            if sz > 0 and sz == last:
                                pdf = open(dst, "rb").read()
                                break
                            last = sz
                        elif proc.poll() is not None:
                            break              # exited without producing one
                        time.sleep(0.25)
                    proc.kill()
                finally:
                    shutil.rmtree(work, ignore_errors=True)
                if pdf is None:
                    return self._send(200, json.dumps(
                        {"error": "chrome produced no PDF within 60 s"}))
                return self._send(200, pdf, "application/pdf")
            if self.path == "/api/rays":
                # Pure Python; no renderer involved. See `raytrace_viz`.
                import raytrace_viz as RV
                t0 = time.perf_counter()
                v, f, _p = build(dict(req.get("spec", {}),
                                      margin_depths=0.0))
                fw = float(req.get("spec", {}).get(
                    "panel", req.get("spec", {}).get("face", 100.0)))
                v, f = clip_to_panel(v, f, fw, fw)
                out = RV.trace(v, f, fw, fw,
                               theta_deg=float(req.get("theta", 0.0)),
                               phi_deg=float(req.get("phi", 0.0)),
                               n_rays=int(req.get("n_rays", 120)),
                               max_bounces=int(req.get("max_bounces", 12)),
                               rho=float(req.get("rho", 0.5)),
                               mode=str(req.get("mode", "diffuse")),
                               seed=int(req.get("seed", 23)))
                out["seconds"] = round(time.perf_counter() - t0, 2)
                return self._send(200, json.dumps(out))
            if self.path == "/api/published":
                return self._send(200, json.dumps(
                    {"nearest": nearest(req)}))
            if self.path == "/api/stl":
                v, f, p = build(dict(req, margin_depths=0.0))
                fw = float(req.get("panel", req.get("face", 100.0)))
                v, f = clip_to_panel(v, f, fw, fw)
                blob = stl_binary(v, f)
                return self._send(200, blob, "model/stl",
                                  {"Content-Disposition":
                                   'attachment; filename="panel.stl"'})
        except Exception:
            return self._send(500, json.dumps(
                {"error": traceback.format_exc(limit=4)}))
        return self._send(404, json.dumps({"error": "no such path"}))


def main():
    os.makedirs("/tmp/simsrv", exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print("[SIM] http://127.0.0.1:%d  (families: %d top, %d floor)"
          % (PORT, len(FAMILIES), len(FLOORS)), flush=True)
    if not IN_BLENDER:
        print("[SIM] standalone: preview, parameters and STL need no Blender; "
              "measurement launches %s" % BLENDER, flush=True)
        srv.serve_forever()          # nothing to marshal; this thread waits
        return
    # Blender's main thread becomes the render worker and never returns.
    while True:
        fn, a, kw, box, done = JOBS.get()
        try:
            box["val"] = fn(*a, **kw)
        except Exception as exc:
            box["err"] = exc
        finally:
            done.set()


if __name__ == "__main__":
    main()
