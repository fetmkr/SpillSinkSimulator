"""The in-plane BRDF slice: one number per (incidence, observation) pair.

Every published number in this study integrates over exit direction.
`metrics/01_rho_dh.md` says so itself -- "ρ_dh is a single scalar; a design that
returns the same energy as a sharp line and one that returns it as a wide smear
score identically". Phase 10 then changed the question from ABSORB to REROUTE,
and `probe_tiltsweep.py` answered it with a hand-typed 5 x 4 grid of
SUNS x OBS that writes no CSV, records no conditions and carries no control
plate. This module is that grid made into an instrument.

WHAT IS MEASURED, with the normalisation written out rather than assumed.

Sun at theta_in, orthographic camera at elevation theta_out. Both angles use
the SAME sign convention -- from the panel normal +Y, positive = above -- pinned
in `blender_render.setup_camera` and `blender_render.sun_rotation_for`. So on
the resulting map:

    theta_out = +theta_in     retro: straight back at the projector
    theta_out = -theta_in     the flat-mirror specular direction
    theta_out = 0             the audience

A Blender sun of `energy` E delivers E W/m^2 to a surface facing it, so a panel
whose normal is +Y receives E*cos(theta_in). The flat Lambertian control plate
that sits in every frame therefore leaves with radiance

    L_c = (rho_c/pi) * E * cos(theta_in)

and the panel with

    L_p = f_r(theta_in, theta_out) * E * cos(theta_in)

so that

    f_r(theta_in, theta_out) = (L_p / L_c) * rho_c / pi        [1/sr]

E and cos(theta_in) cancel. There is NO bin solid angle, NO cos(theta_out)
division and NO source calibration in that -- the BRDF comes out absolute from
a ratio of two window means in one frame, which is the shape of every other
number here.

THREE THINGS FALL OUT OF THAT, AND THEY ARE THE VALIDATION.

1.  The control is analytic ground truth in EVERY cell at once. A Lambertian is
    isotropic, so its cell must read rho_c/pi = 0.0159155 whatever the two
    angles are. `cell()` computes that deviation per cell and returns it, which
    is the per-cell generalisation of `blender_render`'s `control_drift` flag.
    It is also the only thing that would catch the control being shadowed at
    grazing incidence.
2.  Reciprocity is free: f_r(a,b) = f_r(b,a), so the raw map must be symmetric
    about its leading diagonal. `gate_bidir.py` uses it.
3.  The bin width IS the sun's angular size. `add_sun`'s own docstring records
    why a delta source is unusable against a specular surface; here the source
    diameter is set equal to the theta_in step, which makes each column an
    honest bin average instead of a delta with a fudge factor. It is written
    into every row, because an instrument gets no private settings.

WHY THIS DOES NOT GO THROUGH `blender_render.run()`. That path windows with
`measurement_windows()` (inset 20 % / 30 %, audit defect #1) and takes its pixel
count as a constant (defect #2). Both were repaired in `rig_v2` on 2026-08-20
and a brand-new metric must not re-import them. The world here is 0.0, not 1.0,
so there is no sky to shield against and `full_face_windows(inset_mm=0)` is
correct -- rig_v2's docstring says full-face is right for a black-world path
"and only there", which is this one.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy                                                       # noqa: E402
import blender_render as BR                                      # noqa: E402
import materials as MAT                                          # noqa: E402
import rig_v2 as R2                                              # noqa: E402

# The 0.05 diffuse control plate that is in every frame of this study.
RHO_CONTROL = 0.05
# What a Lambertian of that reflectance reads as a BRDF, in every direction.
LAMBERT_BRDF = RHO_CONTROL / math.pi          # 0.015915494309189534

# An ortho camera at 90 deg sees the face edge-on and reads nothing, so the
# observation axis stops short of it. The incidence axis stops earlier still:
# cos(theta_in) is the whole signal and at 85 deg there is 8.7 % of it left.
THETA_OUT_LIMIT = 85.0
THETA_IN_LIMIT = 80.0

# Above this the camera-side margin defect bites (metrics/01, "Margin defect"):
# a view tilted to theta travels D/tan(90-theta) in Z before it sees the valley
# floor. The illumination side has the mirror-image problem and nothing in the
# repo checked it before this module -- gate_bidir.py check 4 is that check.
DEEP_MARGIN_THETA = 50.0
DEEP_MARGIN_DEPTHS = 6.5


def flat_plate(face=100.0, margin=60.0):
    """A genuinely flat panel: one quad at y=0, built exactly like the control
    plate, handed to `build_scene` through its `prebuilt_mesh` door.

    Every "flat plate" this study has used is a degenerate case of a structured
    family, and each one turned out to be flat only approximately: lock.py's
    ridge at pitch 50 does not cover its own face (see
    `rig_v2.assert_window_covered`), and a floor pyramid at depth 0.01 mm still
    reads 1.7-2.7 % off a Lambertian's closed form -- worse, not better, as the
    depth shrinks, because coincident surfaces 1e-4 mm apart are numerically
    the same surface. A quad has no such parameter.

    The quad runs `margin` beyond the face on all sides so a tilted view or a
    tilted sun cannot see past it.
    """
    m = float(margin)
    verts = [(-m, 0.0, -face / 2.0 - m), (face + m, 0.0, -face / 2.0 - m),
             (face + m, 0.0, face / 2.0 + m), (-m, 0.0, face / 2.0 + m)]
    faces = [(0, 1, 2, 3)]
    params = dict(face_w=face, face_h=face, backing=2.0, margin_depths=0.0,
                  top="comb", top_depth=1.0, bot="cone", bot_depth=1.0)
    return params, {"prebuilt_mesh": (verts, faces)}


def build(params, material=None, samples=256, family="floor", gpu=True,
          cycles_seed=None, extra=None):
    """Build once; every cell reuses the same geometry and the same camera
    frame. Returns rig_v2's scene dict with the frame and windows added.

    `material` is anything `materials.resolve` takes -- a library key, a
    {"base": ..., overrides} dict, an inline dict, or a Material. It defaults
    to the study's own coating. There is deliberately no `roughness` or
    `lambert_rho` argument: a finish is one object with a provenance string,
    not loose numbers scattered across a call site, which is the whole point of
    `materials.py`.

    A Material with model "lambert" is the gate's instrument: its BRDF is
    rho0/pi in every direction, in closed form, and a rig that cannot reproduce
    a known answer is not a rig.
    """
    m = MAT.resolve(material)
    extra = dict(extra or {})
    if m.model == "lambert":
        # rig_v2 wires a Lambertian through material_mode "all_diffuse"
        lam, rough = m.rho0, m.roughness
    else:
        lam, rough = None, m.roughness
        # rig_v2 hardcodes coating_split(0.76) at the study rho0; `extra` is
        # applied last, so this is what actually reaches build_scene.
        body, spec_scale = m.split()
        extra.setdefault("coating", {"body": body, "spec_scale": spec_scale,
                                     "roughness": m.roughness})
    sc = R2.build(params, samples=samples, roughness=rough,
                  lambert_rho=lam, family=family, extra=extra)
    p, ctrl_x0 = sc["p"], sc["ctrl_x0"]
    R2.assert_clear(sc)

    ortho = sc["total_w"] * 1.02
    res_x, res_y, mm_per_px, capped = R2.resolution_for(ortho, p.face_h)
    # World = 0.0 here, so there is no sky to leak and the PANEL needs no
    # shield: `assert_window_covered` below guarantees the sample runs past its
    # own window on every side.
    #
    # THE CONTROL DOES NOT. `make_flat_plate` builds it as exactly the face
    # rectangle, so a full-face window ends on the plate's own edge and its
    # outermost pixels are half background. Truncating those float bounds with
    # int() then drops them, and the plate reads 0.3-0.4 % HIGH -- measured
    # +0.42 % at theta_out 0 and +-80, +0.30 % at +-40, the pattern of a
    # one-pixel quantisation on a 465 px window. That lands directly in the
    # denominator of every BRDF here. The stock rig never saw it because its
    # 20/30 % inset put the control window far inside the plate; full-face
    # windowing (rig_v2 D3) is what exposes it.
    #
    # Two pixels of inset on the control only. Verified: the panel then reads a
    # Lambertian's rho/pi to 0.00 % in every cell.
    w_panel, _ = R2.full_face_windows(p, ctrl_x0, inset_mm=0.0)
    _, w_ctrl = R2.full_face_windows(
        p, ctrl_x0, inset_mm=R2.sky_inset_mm(mm_per_px, pixels=2.0))
    R2.assert_window_in_frame(w_panel, ortho, res_x, res_y, "panel window")
    R2.assert_window_in_frame(w_ctrl, ortho, res_x, res_y, "control window")
    # full-face windowing assumes the geometry reaches the full face, and
    # lock.py's degenerate flat plate does not. See rig_v2.assert_window_covered.
    R2.assert_window_covered(sc, w_panel, "panel window")

    # The scene is built once and ~1000 cells are looped over it, changing only
    # camera and sun, so persistent data is exactly the case it exists for.
    try:
        BR.configure_cycles(samples, gpu, seed=cycles_seed, persistent=True)
    except TypeError:                       # older harness without the kwarg
        BR.configure_cycles(samples, gpu, seed=cycles_seed)

    sc.update({"ortho": ortho, "res_x": res_x, "res_y": res_y,
               "mm_per_px": mm_per_px, "capped": capped,
               "w_panel": w_panel, "w_ctrl": w_ctrl,
               "cx": sc["total_w"] / 2.0, "cz": 0.0,
               "samples": samples, "material": m, "family": family,
               "cycles_seed": cycles_seed,
               # always the 0.05 Lambertian reference plate, whatever the panel
               # is coated with (blender_render.py:864)
               "rho_control": sc["cfg"].get("rho_control", RHO_CONTROL)})
    return sc


def _clear_lights_and_cameras():
    for o in list(bpy.data.objects):
        if o.type in ("LIGHT", "CAMERA"):
            bpy.data.objects.remove(o, do_unlink=True)


def cell(sc, theta_in, theta_out, sun_angle_deg, out_dir="/tmp/simsrv/bidir",
         keep=False):
    """One (theta_in, theta_out) cell. Returns the record that becomes a row.

    The camera is rebuilt every cell because only its elevation changes; the
    sun is rebuilt with it, which costs nothing next to a render.
    """
    os.makedirs(out_dir, exist_ok=True)
    _clear_lights_and_cameras()
    BR.setup_camera(sc["cx"], sc["cz"], sc["ortho"], sc["res_x"], sc["res_y"],
                    elev_deg=theta_out)
    BR.set_world(0.0)
    BR.add_sun(theta_in, strength=1.0, angular_size_deg=sun_angle_deg)

    # to_pixel_window projects through the camera that was just placed, so it
    # follows the tilt. It has to be called AFTER setup_camera, every cell.
    px_panel = BR.to_pixel_window(sc["w_panel"])
    px_ctrl = BR.to_pixel_window(sc["w_ctrl"])

    name = "bidir_i%+05.1f_o%+05.1f" % (theta_in, theta_out)
    exr = os.path.join(out_dir, name + ".exr")
    png = os.path.join(out_dir, name + ".png")
    BR.render_to(exr, png)
    arr = BR.read_exr(exr, sc["res_x"], sc["res_y"])
    if not keep:
        for f in (exr, png):
            try:
                os.remove(f)
            except OSError:
                pass

    s_panel = BR.window_stats(arr, px_panel)
    s_ctrl = BR.window_stats(arr, px_ctrl)

    rho_c = sc["rho_control"]
    # What the control MUST read: a Lambertian is isotropic, so its radiance is
    # rho/pi times the irradiance it receives, and it receives cos(theta_in).
    ctrl_expect = (rho_c / math.pi) * math.cos(math.radians(theta_in))
    ctrl_dev = (abs(s_ctrl["mean"] - ctrl_expect) / ctrl_expect
                if ctrl_expect > 1e-12 else float("nan"))

    # measured control: catches anything the analytic value cannot know about
    # (a shadowed plate, a wrong window). analytic: still readable if the
    # measured control has been ruined, so the two can be compared.
    brdf = (s_panel["mean"] / s_ctrl["mean"] * rho_c / math.pi
            if s_ctrl["mean"] > 1e-12 else float("nan"))
    brdf_analytic = (s_panel["mean"] / math.cos(math.radians(theta_in))
                     if abs(theta_in) < 89.0 else float("nan"))

    return {"theta_in": float(theta_in), "theta_out": float(theta_out),
            "brdf": brdf, "brdf_analytic": brdf_analytic,
            "panel_mean": s_panel["mean"], "panel_p99": s_panel["p99"],
            "panel_max": s_panel["max"], "panel_px": s_panel["px"],
            "control_mean": s_ctrl["mean"], "control_expect": ctrl_expect,
            "control_dev": ctrl_dev,
            "sun_angle_deg": float(sun_angle_deg),
            "material": sc["material"].name or "inline",
            "rho0": sc["material"].rho0,
            "diffuse_frac": sc["material"].diffuse_frac,
            "roughness": sc["material"].roughness,
            "mm_per_px": sc["mm_per_px"], "res_x": sc["res_x"],
            "res_y": sc["res_y"], "samples": sc["samples"],
            "cycles_seed": sc["cycles_seed"],
            "exr": exr if keep else None}


def sweep(sc, theta_ins, theta_outs, sun_angle_deg=None, skip=None,
          out_dir="/tmp/simsrv/bidir", keep=False, on_cell=None):
    """Yield one record per cell, theta_in outer so a column completes first.

    A column is the useful unit: it is one incidence angle's whole exit
    profile, so an interrupted run still says something and the UI can paint a
    stripe as soon as it lands.

    `skip(theta_in, theta_out) -> bool` lets a resumed run pass over cells that
    are already on disk without rebuilding the scene.
    """
    if sun_angle_deg is None:
        sun_angle_deg = default_sun_angle(theta_ins)
    for ti in theta_ins:
        for to in theta_outs:
            if skip is not None and skip(ti, to):
                continue
            rec = cell(sc, ti, to, sun_angle_deg, out_dir=out_dir, keep=keep)
            if on_cell is not None:
                on_cell(rec)
            yield rec


def default_sun_angle(theta_ins):
    """The source diameter is the sampling step, so a column is a bin average
    rather than a delta with a fudge. Blender's sun `angle` is the angular
    DIAMETER, which is what a bin width is."""
    xs = sorted(float(t) for t in theta_ins)
    if len(xs) < 2:
        return 0.5
    return min(b - a for a, b in zip(xs, xs[1:]))


def margin_for(theta_ins, theta_outs, default=2.0):
    """Both the view and the illumination need depth of margin at grazing.
    metrics/01 records the camera-side rule; the illumination side is the same
    geometry seen from the other end and had never been checked."""
    worst = max([abs(float(t)) for t in list(theta_ins) + list(theta_outs)]
                or [0.0])
    return DEEP_MARGIN_DEPTHS if worst >= DEEP_MARGIN_THETA else default


def grid(step=5.0, in_limit=THETA_IN_LIMIT, out_limit=THETA_OUT_LIMIT):
    """The two axes as lists. Symmetric about zero: the geometries are not
    symmetric in theta and the sign is never redundant."""
    n_in = int(math.floor(in_limit / step))
    n_out = int(math.floor(out_limit / step))
    return ([round(-n_in * step + k * step, 6) for k in range(2 * n_in + 1)],
            [round(-n_out * step + k * step, 6) for k in range(2 * n_out + 1)])
