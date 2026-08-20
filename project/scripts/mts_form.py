"""Form destruction and head-on brightness, measured in Mitsuba.

The Cycles version is `form_buildable.run_case`. This is the same experiment in
an independent code, and it exists because the cross-check covered only ONE of
the project's three axes: total reflectance. Smear and head-on peak -- the two
the study calls its first priority -- had never been checked against a second
renderer at all, so "the numbers agree between codes" was true of a third of
them.

THE EXPERIMENT, identical in both codes:

    a near-collimated stripe 2 mm wide arrives at incidence theta and lands at
    z = target_z on the face plane. The world is black; the stripe is the only
    source. An orthographic camera looks straight down at the face plane and
    photographs the panel and, 100 mm to its side, a FLAT control plate of the
    same material in the same frame. Each image is collapsed to a profile along
    z, and from that profile come

        rms_mm       how far the returned line has been spread
        peak_ratio   the panel's peak over the flat control's peak

    The stripe then walks N_PHASE positions across exactly one pitch and every
    reported number is the mean over that walk, because for a structure with a
    pitch the answer depends on whether the stripe lands on a wall top or in a
    cell.

WHAT IS DELIBERATELY SHARED, AND WHAT IS NOT. The four statistics come from
`form_metrics`, imported by both codes, so a disagreement cannot be in the
arithmetic. The geometry is the same mesh. What is NOT shared is the light
transport and the emitter model, which is the entire point.

TWO DIFFERENCES THAT CANNOT BE REMOVED, both stated rather than buried:

  * Blender's area lamp has a `spread` (set to 0.05 degrees here, near
    collimated). Mitsuba's `directionalarea` emits along the surface normal
    exactly, i.e. spread 0. The stripe is therefore very slightly sharper in
    Mitsuba, which acts on the CONTROL as well as on the panel and so largely
    divides out of `peak_ratio`.
  * Cycles builds the fitted coating from a Fresnel node feeding a
    diffuse/glossy mix, which Mitsuba has no identical construction for. A
    cross-check therefore runs a pure Lambertian in BOTH codes -- the same BRDF
    in each -- so that what is compared is transport and not materials.
"""

import os
import math

import numpy as np

from form_metrics import z_profile, recentre, rms_width, mtf_at

# COPIES, and the comment that used to sit here claimed they were "read from
# there rather than copied, so the two cannot drift apart". They are copies and
# they DID drift: STRIPE_W was 2.0 here against 7.5 in form_buildable, so any
# cross-check that did not pass a beam compared two different experiments --
# the flat control returns beam/sqrt(12), so the smear denominator was 3.75x
# apart. mts_worker now overwrites every one of these from the request; the
# values below are only what a bare `python mts_form.py` would use.
GAP = 100.0                  # x gap between panel and flat control
STRIPE_W = 7.5               # mm -- the deployment beam, as form_buildable
MM_PER_PX = 0.0              # 0 = legacy fixed pixel count; set from request
RES_X, RES_Y = 1400, 620
NWIN = 361
MEAS_INSET_X = 0.20
MEAS_INSET_Z = 0.30
RHO_CONTROL = 0.05           # the matte black wall the ratio is against
SLIT_Y = 10.0                # height of the slit above the face plane, mm
EYE_Y = 500.0                # orthographic eye height; near_clip hides the slit


def _res_x(face_w):
    """Pixel count follows the scene when a density is set, so mm-per-pixel
    does not drift with the sample -- the same repair form_buildable got."""
    if not MM_PER_PX:
        return RES_X
    ortho = (2.0 * face_w + GAP) * 1.02
    return max(400, min(20000, int(round(ortho / MM_PER_PX))))


def _res_y(face_w, face_h):
    """The frame must contain the face; a fixed aspect ran the window off the
    image above ~500 mm."""
    if not MM_PER_PX:
        return RES_Y
    ortho = (2.0 * face_w + GAP) * 1.02
    return max(200, int(round(_res_x(face_w) * (face_h * 1.06) / ortho)))


def _blocker(mi, cx, z0, z1, slit_y):
    """One half of the slit: opaque, black, and hidden from the camera."""
    return {"type": "rectangle",
            "to_world": (mi.ScalarTransform4f().translate(
                [cx, slit_y, (z0 + z1) / 2.0])
                @ mi.ScalarTransform4f().rotate(axis=[1, 0, 0], angle=-90.0)
                @ mi.ScalarTransform4f().scale([2000.0, (z1 - z0) / 2.0, 1.0])),
            "bsdf": {"type": "twosided",
                     "material": {"type": "diffuse",
                                  "reflectance": {"type": "rgb",
                                                  "value": 0.0}}}}


def _quad(mi, x0, x1, z0, z1, y=0.0):
    """A flat plate in the face plane."""
    return {
        "type": "rectangle",
        "to_world": (mi.ScalarTransform4f().translate(
            [(x0 + x1) / 2.0, y, (z0 + z1) / 2.0])
            @ mi.ScalarTransform4f().rotate(axis=[1, 0, 0], angle=-90.0)
            @ mi.ScalarTransform4f().scale(
                [(x1 - x0) / 2.0, (z1 - z0) / 2.0, 1.0])),
    }


def scene_dict(mi, ply, rho, face_w, face_h, theta_deg, target_z, spp):
    """Panel + flat control + one collimated 2 mm stripe. Nothing else emits.

    HOW THE STRIPE IS MADE, and why it took four attempts. Blender's area lamp
    has a `spread` angle; set to 0.05 degrees it emits near-parallel rays from a
    2 mm strip, which is what makes a stripe rather than a flood. Mitsuba has no
    such control, and the three obvious substitutes were each measured and
    rejected:

      * `directionalarea` -- a rectangle emitting exactly along its normal, the
        physically identical construction -- deposits NOTHING here. Zero in all
        eight combinations of `path`/`ptracer` x normal direction x
        `flip_normals`, in a minimal two-shape scene. Its emission is a delta in
        direction, which next-event estimation cannot sample and BSDF sampling
        hits with probability zero; `ptracer`, which would trace from the light,
        refuses the orthographic sensor outright ("sample_direction(): not
        implemented").
      * `projector` with a stripe texture -- illuminates the whole frame
        uniformly. A checkerboard texture also renders flat, so the irradiance
        texture is not modulating anything in this build.
      * a plain `area` lamp -- is Lambertian, so every point of the panel sees
        it and the whole panel is lit. An area lamp is a flood, not a stripe;
        in Blender it is the `spread` and not the shape that makes the line.

    What works, and is exact rather than approximate: a `directional` emitter,
    which is perfectly collimated and samplable, with an opaque SLIT 2 mm wide
    held 10 mm above the face. Parallel rays through a slit cast no penumbra, so
    the band on the panel is exactly the slit width, and it lands wherever the
    slit is placed. The slit sits in the camera's line of sight, which made the
    first version of this measure light coming back THROUGH the slit rather than
    off the panel -- the camera's `near_clip` is therefore set just short of the
    slit so camera rays skip it entirely while shadow rays still see it.
    Verified: at theta 0 / -40 / +40 the band lands on the aim point to within
    half a pixel and measures 2.2 mm against a nominal 2.0.
    """
    ctrl_x0 = face_w + GAP
    total_w = ctrl_x0 + face_w
    cx = total_w / 2.0
    ortho_w = total_w * 1.02

    t = math.radians(theta_deg)
    z_slit = target_z + SLIT_Y * math.tan(t)

    mat = {"type": "twosided",
           "material": {"type": "diffuse",
                        "reflectance": {"type": "rgb", "value": rho}}}
    ctrl_mat = {"type": "twosided",
                "material": {"type": "diffuse",
                             "reflectance": {"type": "rgb",
                                             "value": RHO_CONTROL}}}
    return {
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 128},
        "sensor": {
            "type": "orthographic",
            # `scale` is NOT half-width x half-height. Measured on this build
            # with markers at known world z: the horizontal half-extent is the
            # x scale, and the VERTICAL half-extent is the y scale divided by
            # the film aspect. Passing (w/2, h/2) therefore squashed the frame
            # by the aspect ratio and every distance read 2.24x too large. A
            # square scale gives square pixels.
            "to_world": mi.ScalarTransform4f().look_at(
                origin=[cx, EYE_Y, 0.0], target=[cx, 0.0, 0.0], up=[0, 0, 1]
            ) @ mi.ScalarTransform4f().scale(
                [ortho_w / 2.0, ortho_w / 2.0, 1.0]),
            # The camera sits at EYE_Y and the slit at SLIT_Y, so the distance
            # along the view ray to the slit is EYE_Y - SLIT_Y. Clipping must
            # start BEYOND that, not short of it: the first version subtracted
            # the margin instead of adding it, left the slit in view, and every
            # off-normal frame came back black because the camera was looking
            # at the back of an opaque blocker.
            "near_clip": EYE_Y - SLIT_Y + 5.0,
            "far_clip": EYE_Y * 4.0,
            "sampler": {"type": "independent", "sample_count": spp},
            "film": {"type": "hdrfilm", "width": _res_x(face_w),
                     "height": _res_y(face_w, face_h),
                     "pixel_format": "rgb", "rfilter": {"type": "box"}},
        },
        "panel": {"type": "ply", "filename": ply, "bsdf": mat},
        "control": dict(_quad(mi, ctrl_x0, ctrl_x0 + face_w,
                              -face_h / 2.0, face_h / 2.0),
                        bsdf=ctrl_mat),
        "sun": {"type": "directional",
                "direction": [0.0, -math.cos(t), -math.sin(t)],
                "irradiance": {"type": "rgb", "value": 100.0}},
        "slitA": _blocker(mi, cx, z_slit - 4000.0, z_slit - STRIPE_W / 2.0,
                          SLIT_Y),
        "slitB": _blocker(mi, cx, z_slit + STRIPE_W / 2.0, z_slit + 4000.0,
                          SLIT_Y),
    }


def _windows(face_w, face_h):
    """Pixel boxes for the panel and the control, from the MEASURED mapping.

    Not from first principles. The image mirrors x -- calibrated on this build
    with an emissive marker at three known world positions, giving
    `world_x = -0.16028 * col + 222.12` for a 60 mm face, i.e. column 0 is the
    LARGEST x. Writing the obvious `col = (x - x_min) / mm_per_px` therefore put
    the panel window on the control plate and the control window on the panel,
    and the cross-check reported the head-on ratio as exactly its own reciprocal
    -- 5.000 against Cycles' 0.200, which is 0.05/0.01 the wrong way up.

    `_setup_check` below exists because the first validation could not catch
    this: it ran a flat plate of the same material in both windows, where a swap
    is invisible. The control is deliberately a different reflectance from the
    panel now, so a swap shows up as a factor of five.
    """
    ctrl_x0 = face_w + GAP
    total_w = ctrl_x0 + face_w
    ortho_w = total_w * 1.02
    ortho_h = ortho_w * RES_Y / float(RES_X)
    cx = total_w / 2.0
    mm_per_px = ortho_w / float(RES_X)

    def px(x, z):
        return ((cx + ortho_w / 2.0 - x) / mm_per_px,      # x is mirrored
                (ortho_h / 2.0 - z) / mm_per_px)

    dx, dz = face_w * MEAS_INSET_X, face_h * MEAS_INSET_Z
    boxes = []
    for x0 in (0.0, ctrl_x0):
        a = px(x0 + dx, -face_h / 2.0 + dz)
        b = px(x0 + face_w - dx, face_h / 2.0 - dz)
        boxes.append((min(a[0], b[0]), max(a[0], b[0]),
                      min(a[1], b[1]), max(a[1], b[1])))
    return boxes[0], boxes[1], mm_per_px


def setup_check(mi, face_w=60.0, face_h=60.0, spp=64, out_dir="/tmp/mts_form"):
    """A flat panel of KNOWN reflectance must read its own value.

    The panel is given rho = 0.01 and the control keeps 0.05, so the head-on
    peak ratio has one right answer -- 0.200 -- and both a window swap (which
    returns 5.000) and a scale error show up immediately. Returns the measured
    ratio; the caller decides what to do about it.
    """
    import os
    from crosscheck_mitsuba import write_ply
    os.makedirs(out_dir, exist_ok=True)
    ply = os.path.join(out_dir, "setup_flat.ply")
    write_ply(ply, [(0.0, 0.0, -face_h), (face_w, 0.0, -face_h),
                    (face_w, 0.0, face_h), (0.0, 0.0, face_h)], [(0, 1, 2, 3)])
    wp, wc, mmpx = _windows(face_w, face_h)
    arr = np.array(mi.render(mi.load_dict(scene_dict(
        mi, ply, 0.01, face_w, face_h, 0.0, 0.0, spp))))
    pp = recentre(z_profile(arr, wp), NWIN)
    pc = recentre(z_profile(arr, wc), NWIN)
    return float(pp.max()) / float(pc.max()) if pc.max() > 0 else float("nan")


def run(mi, ply, rho, face_w, face_h, pitch, thetas=(-40.0, 40.0, 0.0),
        n_phase=6, spp=256):
    w_panel, w_ctrl, mm_per_px = _windows(face_w, face_h)
    phases = [(-pitch / 2.0) + pitch * i / n_phase for i in range(n_phase)]

    out = {"mm_per_px": mm_per_px, "n_phase": n_phase, "thetas": {}}
    for ti, theta in enumerate(thetas):
        acc_p = np.zeros(NWIN)
        acc_c = np.zeros(NWIN)
        peaks = []
        for pi, dz in enumerate(phases):
            # progress marker: sim_server streams these lines from the
            # subprocess so the UI bar moves during a Mitsuba form render too
            print("@@PROG@@ %d %d" % (ti * n_phase + pi,
                                      len(thetas) * n_phase), flush=True)
            img = mi.render(mi.load_dict(scene_dict(
                mi, ply, rho, face_w, face_h, theta, dz, spp)))
            arr = np.array(img)
            pp = recentre(z_profile(arr, w_panel), NWIN)
            pc = recentre(z_profile(arr, w_ctrl), NWIN)
            acc_p += pp
            acc_c += pc
            peaks.append(float(pp.max()) / float(pc.max())
                         if pc.max() > 0 else float("nan"))
        acc_p /= n_phase
        acc_c /= n_phase
        d = {"rms_mm": rms_width(acc_p, mm_per_px),
             "rms_control_mm": rms_width(acc_c, mm_per_px),
             "peak_ratio_mean": float(np.mean(peaks)),
             "peak_ratio_sd": float(np.std(peaks))}
        d.update(mtf_at(acc_p, mm_per_px, (10.0, 20.0, 40.0)))
        out["thetas"]["%+.0f" % theta] = d

    t = out["thetas"]
    a, b = t.get("-40"), t.get("+40")
    out["smear"] = (0.5 * (a["rms_mm"] / a["rms_control_mm"]
                           + b["rms_mm"] / b["rms_control_mm"])
                    if a and b else None)
    z = t.get("+0")
    out["head_on"] = z["peak_ratio_mean"] if z else None
    return out
