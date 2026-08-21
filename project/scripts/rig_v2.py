"""rig_v2 — the measurement rig with three known defects repaired, plus the
gates that prove the repair. Nothing here changes `blender_render`; it sets
module globals per run so old numbers stay reproducible beside new ones.

The three defects, all previously recorded and none previously fixed:

D1  THE CONTROL PLATE SITS INSIDE THE PANEL FIELD.
    `GAP = 100` puts the flat control at x = face_w + 100, while the field runs
    to face_w + margin, and margin = 2 x depth. Any design deeper than 50 mm
    buries its own control. Measured today: p10/d90 builds the field over
    x -180..300 with the control at x 200..300 -- fully overlapped.
    Recorded 2026-08-12 in FINDINGS_control_overlap.md as "cause proven, fix
    NOT applied". Fix: place the control clear of the field.

D2  THE INSTRUMENT'S RESOLUTION FOLLOWS THE SAMPLE.
    `res_x` is a constant while `ortho_scale` tracks the scene width, so
    mm-per-pixel is 0.22 at a 100 mm panel and 1.53 at a 1000 mm one. The same
    instrument samples 7x coarser on a bigger sample. The 2026-08-12 note spots
    this ("holding pixels per mm constant, which is the whole point") and it
    was never made a rule. Fix: fix mm-per-pixel, derive the pixel count.

D3  60 % OF THE MEASURED FACE IS DISCARDED.
    `measurement_windows` trims 20 % off each side in x and 30 % in z, so a 1 m
    panel is read over 600 x 400 mm. What that removes on the smear axis is the
    tail of the returned light, which IS the signal: a p10/d90 return is 60 mm
    wide and the old window was 40 mm.
    Fix: measure the whole face -- BUT ONLY WHERE THAT IS SAFE. See below.

WHAT GATE 1 TAUGHT, AND WHAT IT COST (2026-08-20)
  D1 is NOT a defect for the pyramid family. The stock rig reads the control at
  exactly 0.050000 even when the field overlaps it, because the control plate
  occludes the geometry behind it and a pyramid exposes almost nothing at y=0
  (a 0.1 mm tip on a 4 mm pitch is 0.06 % of the area). The 2026-08-12 failure
  was a honeycomb, which exposes 13 %. The gap fix is kept because it costs
  nothing and makes the frame honest, but it changes no pyramid number.

  D3 must NOT be applied to the totals path. That path fills the world with
  radiance 1.0, so a window running to the exact face edge catches a pixel or
  two of BACKGROUND, which is 20x brighter than the 0.05 control: measured
  0.0530 against 0.0500, a 6 % error from a 0.3 % sliver. The inset is also a
  sky shield, not only an edge-effect shield. The smear path sets the world to
  0.0 and has no sky, so full-face is correct there and only there.

  The headline totals are indifferent to all of this: rho_dh matched to six
  decimals between stock and repaired on p4/d20, p4/d22 and p10/d90.

Every number this rig produces must clear GATE 1 before it is quoted.
"""

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import blender_render as BR  # noqa: E402
import form_buildable as FB  # noqa: E402
from form_metrics import z_profile, recentre, rms_width  # noqa: E402

# The study sampled its standard 100 mm panel at this density. Holding it fixed
# is the whole point of D2; changing it is a re-baseline, not a tuning knob.
MM_PER_PX = 0.215
RES_CAP = 20000         # a MEMORY ceiling only. Never a quality knob:
                        # 6000 quietly coarsened any panel over ~590 mm.
SLACK = 60.0            # clear air between the panel field and the control


def _field_x(exclude="control"):
    """Measured x extent of the built geometry. GATE 1 showed `p.margin()` does
    not predict it -- a face_w 100 / margin 1000 build reached x = 1300, not
    1100 -- so the gap is set from what is actually on screen."""
    import bpy
    lo = hi = None
    for o in bpy.data.objects:
        if o.type != "MESH" or exclude in o.name:
            continue
        xs = [(o.matrix_world @ v.co).x for v in o.data.vertices]
        if not xs:
            continue
        lo = min(xs) if lo is None else min(lo, min(xs))
        hi = max(xs) if hi is None else max(hi, max(xs))
    return lo, hi


def resolution_for(ortho, face_h=None):
    """Pixel count follows the scene so mm-per-pixel does not (D2).

    `face_h` makes the FRAME contain the face. The old fixed 620/1400 aspect
    gave a frame 0.443 x ortho tall regardless of the panel, so a 1000 mm face
    in a 2104 mm scene got 951 mm of frame and the window ran off the image --
    empty control profile, NaN head-on. face 500 sat one millimetre inside it.
    Returns (res_x, res_y, mm_per_px, capped).
    """
    want = int(round(ortho / MM_PER_PX))
    res_x = min(RES_CAP, want)
    if face_h:
        res_y = max(200, int(round(res_x * (float(face_h) * 1.06) / ortho)))
    else:
        res_y = max(200, int(round(res_x * 620.0 / 1400.0)))
    return res_x, res_y, ortho / res_x, want > RES_CAP


def full_face_windows(p, ctrl_x0, inset_mm=0.0):
    """The whole face, minus a FIXED inset in millimetres (D3).

    `inset_mm = 0` is right for the smear path, whose world is black.
    The totals path fills the world with radiance 1.0 and must keep a couple of
    pixels of shield, or background 20x brighter than the control leaks in; use
    `sky_inset_mm()` there. The inset is a constant in mm, never a fraction of
    the face, so the measured region does not shrink or grow with the sample.
    """
    d = float(inset_mm)
    panel = (d, p.face_w - d, -p.face_h / 2.0 + d, p.face_h / 2.0 - d)
    ctrl = (ctrl_x0 + d, ctrl_x0 + p.face_w - d,
            -p.face_h / 2.0 + d, p.face_h / 2.0 - d)
    return panel, ctrl


def sky_inset_mm(mm_per_px, pixels=4.0):
    """Shield width for the totals path: a few pixels, expressed in mm at the
    rig's own sampling. Four pixels was chosen to sit well clear of the 1-2
    pixel leak GATE 1 measured, while still discarding ~1 mm rather than the
    stock rule's 20-30 mm."""
    return pixels * mm_per_px


# WHICH MODULE OWNS A SET OF PARAMETERS. `family` used to default to "floor"
# for every caller, so a caller that forgot to name its family got the floor
# module whatever it had asked for. Two gate scripts died on exactly that --
#
#   rig_v2_gates_mesh.py  kind="cone", tip_radius=0.2
#     -> FloorParams.__init__() got an unexpected keyword argument 'tip_radius'
#   sweep_standalone.py   wall_top=...
#     -> FloorParams.__init__() got an unexpected keyword argument 'wall_top'
#
# -- and both took their whole batch down with them. The mis-routing is loud
# rather than silent (a dataclass rejects an unknown keyword, and geom_floor
# raises on an unknown `kind`), so no wrong shape was ever measured; but the
# job stops, and a stopped batch looks like a finished one in a log file.
_FAMILY_CLASS = [
    ("floor",  "geom_floor",  "FloorParams"),
    ("cone3d", "geom3d",      "Cone3DParams"),
    ("topo",   "geom_topo",   "TopoParams"),
    ("perf",   "geom_perf",   "PerfParams"),
    ("cell",   "geom_cell",   "CellParams"),
    ("stack",  "geom_stack",  "StackParams"),
]


def _infer_family(params):
    """Name the family that can take these parameters, and the params to pass.

    Returns (family, params). The second value matters: when `kind` is acting
    as a FAMILY selector rather than a floor sub-shape it must be dropped, or
    the class it selected rejects it -- Cone3DParams has no `kind` field, so
    inferring "cone3d" and then handing it `kind="cone"` fails at the next
    line for a new reason. Inference and the call have to agree on one set.

    `floor` is tried FIRST and wins whenever it fits, so every call that works
    today keeps the family it has always had -- this only rescues the calls
    that currently crash. If nothing fits, say what each family rejected
    instead of letting one module's TypeError stand for the whole answer.
    """
    import importlib
    import dataclasses
    rejected = []
    for fam, mod_name, cls_name in _FAMILY_CLASS:
        try:
            cls = getattr(importlib.import_module(mod_name), cls_name)
        except Exception as exc:                       # module not importable
            rejected.append("%s: %s" % (fam, exc))
            continue
        allowed = {f.name for f in dataclasses.fields(cls)}
        extra = set(params) - allowed
        if extra:
            rejected.append("%s: does not take %s"
                            % (fam, ", ".join(sorted(extra))))
            continue
        kind = params.get("kind")
        if fam == "floor" and kind is not None:
            import geom_floor as GF
            if kind not in GF._BUILDERS:
                rejected.append("floor: no builder for kind %r" % kind)
                continue
        return fam, dict(params)
    # `kind` CARRIES TWO MEANINGS. In geom_floor it names the sub-shape
    # (pyramid, wave, boxgrid); in the gate scripts it names the family
    # itself -- kind="cone" means the 3D cone module, which has no `kind`
    # field at all and so rejects the whole set. Retry without it, but only
    # for a name no floor builder claims, so a real floor kind can never be
    # thrown away to make some other family fit.
    kind = params.get("kind")
    if kind is not None:
        import geom_floor as GF
        if kind not in GF._BUILDERS:
            rest = {k: v for k, v in params.items() if k != "kind"}
            for fam, mod_name, cls_name in _FAMILY_CLASS:
                if fam == "floor":
                    continue
                try:
                    cls = getattr(importlib.import_module(mod_name), cls_name)
                except Exception:
                    continue
                if not set(rest) - {f.name for f in dataclasses.fields(cls)} \
                        and fam.startswith(kind):
                    return fam, rest
    raise ValueError(
        "no geometry family takes these parameters (%s).\n  %s"
        % (", ".join(sorted(params)), "\n  ".join(rejected)))


def build(params, samples=256, roughness=0.30, lambert_rho=None,
          family=None, coating=None, deep_coating=None, paint_depth=None,
          floor_coating=None, floor_boundary_depth=None):
    """Build the scene with the control placed clear. Returns everything the
    callers need, including the geometry's real extent so overlap can be
    asserted rather than assumed.

    `family` may be left out; it is then inferred from the parameter names.
    """
    import bpy
    if family is None:
        family, params = _infer_family(dict(params))
    cfg = {"tag": "rigv2", "out_dir": "/tmp/simsrv/rigv2",
           "results_dir": "/tmp/simsrv/rigv2", "samples": samples,
           "res_x": 1400, "res_y": 620, "gpu": True,
           "spec_roughness": roughness, "params": dict(params),
           "renders": [], "material_mode": "coating", "family": family}
    body, spec = BR.coating_split(0.76)
    cfg["coating"] = {"body": body, "spec_scale": spec, "roughness": roughness}
    # A CALLER-SUPPLIED FINISH. Without these the rig always painted the fitted
    # Musou everywhere, so a script that thought it was sweeping coatings was
    # rendering one coating over and over. Each is a {"body","spec_scale"} dict
    # as `sim_server._coat` returns.
    if coating is not None:
        cfg["coating"] = dict(coating, roughness=roughness)
    if paint_depth is not None and deep_coating is not None:
        cfg["paint_depth"] = float(paint_depth)
        cfg["deep_coating"] = dict(deep_coating)
    if floor_coating is not None:
        cfg["floor_coating"] = dict(floor_coating)
        if floor_boundary_depth is not None:
            cfg["floor_boundary_depth"] = float(floor_boundary_depth)
    cfg.update({k: v for k, v in FB.COAT.items() if k != "spec_roughness"})
    if lambert_rho is not None:
        cfg["material_mode"] = "all_diffuse"
        cfg.update(rho_slat=lambert_rho, rho_chamber=lambert_rho,
                   rho_specular=lambert_rho, rho_control=0.05)

    # build once to see where the field really ends, then rebuild clear of it
    BR.clear_scene()
    p0, _, _ = BR.build_scene(cfg)
    _, hi0 = _field_x()
    want_gap = max(BR.GAP, (hi0 - p0.face_w) + SLACK)
    old_gap = BR.GAP
    try:
        BR.GAP = want_gap
        BR.clear_scene()
        p, cs, ctrl_x0 = BR.build_scene(cfg)
        field = _field_x()
    finally:
        BR.GAP = old_gap

    return {"p": p, "ctrl_x0": ctrl_x0, "gap": want_gap, "field_x": field,
            "total_w": ctrl_x0 + p.face_w, "cfg": cfg}


def assert_window_in_frame(win, ortho, res_x, res_y, what="window"):
    """The frame must contain the window. Until 2026-08-20 res_y was a fixed
    0.443 of res_x, so the frame height was 0.443 x ortho whatever the panel
    was; a 1000 mm face in a 2104 mm scene got 951 mm of frame and the window
    ran off the image -- the control profile came back EMPTY and head-on read
    NaN, silently. face 500 sat one millimetre inside the boundary. An
    assertion, not a comment, so it cannot happen quietly again."""
    frame_h = ortho * float(res_y) / float(res_x)
    need = abs(win[3] - win[2])
    if need > frame_h * 1.0001:
        raise AssertionError(
            "%s is %.1f mm tall but the frame is only %.1f mm "
            "(ortho %.1f, %dx%d px) -- it would be read off the edge of the "
            "image" % (what, need, frame_h, ortho, res_x, res_y))
    return frame_h


def assert_clear(sc):
    """D1's gate as an assertion, not a hope."""
    lo, hi = sc["field_x"]
    if hi >= sc["ctrl_x0"]:
        raise AssertionError(
            "panel field reaches x=%.1f, control starts at x=%.1f -- still "
            "overlapping" % (hi, sc["ctrl_x0"]))
    return hi, sc["ctrl_x0"]
