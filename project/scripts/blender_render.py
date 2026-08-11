"""
Headless Cycles harness for the anechoic panel study.

    Blender --background --factory-startup --python scripts/blender_render.py -- --job job.json

The script builds the scene from a Y-Z cross-section, renders one or more
measurement modes, reads the resulting EXR back through bpy (so no external
EXR dependency is needed) and writes a JSON result next to it.

Measurement modes
-----------------
hemi   Uniform hemispherical illumination (world background, strength 1.0),
       front orthographic camera.

       Measured, not assumed: a flat Lambertian rho = 0.05 plate reads
       0.050001 here, NOT 0.0389. Under a uniform environment of radiance L0
       the irradiance is pi*L0, the radiosity is rho*pi*L0, and the outgoing
       radiance is rho*L0 -- the camera measures radiance, so the "only part
       of the hemisphere is collected" loss is already accounted for and must
       not be applied twice. See scripts/validate.py check 2.

       So a hemi pixel value IS the effective reflectance rho_eff. The flat
       control is still rendered in the same frame, because the ratio is what
       stays meaningful once materials are no longer purely Lambertian.

hemi_view
       PRIMARY numerical axis. Uniform illumination again, but with the camera
       tilted to elevation theta.

       By Helmholtz reciprocity the radiance leaving toward theta under a
       uniform environment L0 is

           L(theta) = L0 * integral f_r(wi, theta) cos(wi) dwi
                    = L0 * rho_dh(theta)

       so this reads the TOTAL fraction reflected by a collimated beam
       arriving from theta -- exactly the "reduce total reflected light" axis,
       and with no delta-function glint to destabilise the mean. The flat
       Lambertian control must read 0.05 at every theta, which is the built-in
       check that the tilt is being applied correctly.

angle  World black, one sun at incidence theta measured from the panel normal
       (+Y) in the Y-Z plane, front camera. This is the "what does an observer
       in front actually see" axis. With a specular stage 1 it is dominated by
       glints, so mean, p99 and max are all recorded rather than mean alone.

       The fin is asymmetric, so +theta (light from above) and -theta (light
       from below) are different geometries and both must be swept.

form   A narrow near-collimated stripe at incidence theta. This one is not
       numerical -- it answers "does a laser line still read as a line, or as
       a smudge". Judged by putting PNGs side by side.
"""

import sys
import os
import json
import math

import bpy
import bmesh
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from profile2d import PanelParams, build_cross_section             # noqa: E402


def describe(p):
    """Dispatch to whichever geometry family this parameter object belongs to."""
    import profile2d
    name = type(p).__name__
    if name == "ScatterParams":
        import profile_scatter
        return profile_scatter.describe(p)
    if name == "RidgeParams":
        import profile_ridge
        return profile_ridge.describe(p)
    return profile2d.describe(p)


# --------------------------------------------------------------------------
# scene layout (world mm; 1 Blender unit = 1 mm)
# --------------------------------------------------------------------------

SEED = 0            # Cycles sampling seed; set per-run to measure the spread
GAP = 100.0          # X gap between panel and flat control
MEAS_INSET_X = 0.20  # fraction of width trimmed off each side of a window
MEAS_INSET_Z = 0.30  # trimmed harder in Z: fins run past the panel there


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# --------------------------------------------------------------------------
# materials
# --------------------------------------------------------------------------

def make_diffuse(name, rho):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfDiffuse")
    bsdf.inputs["Color"].default_value = (rho, rho, rho, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.0
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return m


def make_glossy(name, rho, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfAnisotropic") if "ShaderNodeBsdfAnisotropic" in dir(bpy.types) else nt.nodes.new("ShaderNodeBsdfGlossy")
    bsdf.inputs["Color"].default_value = (rho, rho, rho, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return m


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def loops_to_object(loops, width, x0, name, material):
    """Extrude a list of closed Y-Z loops along X into one object."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for loop in loops:
        # drop duplicate consecutive points; bmesh refuses degenerate faces
        pts = []
        for y, z in loop:
            if not pts or (abs(pts[-1][0] - y) > 1e-7 or abs(pts[-1][1] - z) > 1e-7):
                pts.append((y, z))
        if len(pts) > 2 and abs(pts[0][0] - pts[-1][0]) < 1e-7 and abs(pts[0][1] - pts[-1][1]) < 1e-7:
            pts.pop()
        if len(pts) < 3:
            continue
        verts = [bm.verts.new((x0, y, z)) for y, z in pts]
        try:
            f = bm.faces.new(verts)
        except ValueError:
            continue
        r = bmesh.ops.extrude_face_region(bm, geom=[f])
        moved = [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=moved, vec=(width, 0.0, 0.0))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    bpy.context.collection.objects.link(obj)
    return obj


def make_flat_plate(p, x0, name, material):
    """Flat control: a plane in the face plane, same coating, same frame."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    zl, zh = -p.face_h / 2, p.face_h / 2
    vs = [bm.verts.new(v) for v in
          [(x0, 0.0, zl), (x0 + p.face_w, 0.0, zl),
           (x0 + p.face_w, 0.0, zh), (x0, 0.0, zh)]]
    bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    bpy.context.collection.objects.link(obj)
    return obj


# --------------------------------------------------------------------------
# camera / render config
# --------------------------------------------------------------------------

def setup_camera(cx, cz, ortho_scale, res_x, res_y, elev_deg=0.0, dist=3000.0):
    """
    Orthographic camera looking at the face plane from elevation `elev_deg`,
    measured from the panel normal (+Y) in the Y-Z plane. Positive elevation
    puts the camera above the panel looking down, matching the sign convention
    used for incidence angle.

    With Rz(180)*Rx(90 - elev) the camera forward becomes (0, -cos, -sin),
    which is the direction from the camera toward the panel.
    """
    t = math.radians(elev_deg)
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_scale
    cam_data.clip_start = 1.0
    cam_data.clip_end = 20000.0
    cam = bpy.data.objects.new("cam", cam_data)
    cam.location = (cx, dist * math.cos(t), cz + dist * math.sin(t))
    cam.rotation_euler = (math.pi / 2 - t, 0.0, math.pi)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    sc = bpy.context.scene
    sc.render.resolution_x = res_x
    sc.render.resolution_y = res_y
    sc.render.resolution_percentage = 100
    sc.render.pixel_aspect_x = 1.0
    sc.render.pixel_aspect_y = 1.0
    return cam


def world_to_pixel(x, z):
    """
    Project a face-plane point (y = 0) to pixel coordinates.

    Uses Blender's own projection rather than re-deriving the ortho mapping,
    so camera orientation and aspect conventions cannot be got wrong. Returned
    pixel rows count from the BOTTOM, matching the raw EXR buffer layout.
    """
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    u, v, _ = world_to_camera_view(sc, sc.camera, Vector((x, 0.0, z)))
    return u * sc.render.resolution_x, v * sc.render.resolution_y


def configure_cycles(samples, use_gpu=True, seed=None):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles

    # Max Bounces is the critical setting. At the default of 12, Cycles
    # discards rays that hit the limit and renders them black, which makes
    # every cavity look better than it is. Cavities here need dozens of
    # bounces by design, so any result from a low bounce limit is void.
    cy.max_bounces = 128
    cy.diffuse_bounces = 128
    cy.glossy_bounces = 128
    cy.transmission_bounces = 128
    cy.transparent_max_bounces = 128
    cy.volume_bounces = 0

    cy.use_denoising = False
    cy.sample_clamp_direct = 0.0
    cy.sample_clamp_indirect = 0.0
    cy.samples = samples
    cy.use_adaptive_sampling = False
    # a fixed seed makes runs reproducible but hides the Monte Carlo spread, so
    # it is settable and every result carries the seed it was made with
    cy.seed = SEED if seed is None else seed

    # linear pixel values; Filmic / AgX would break numerical comparison
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = "sRGB"
    sc.sequencer_colorspace_settings.name = "Non-Color"

    if use_gpu:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        enabled = []
        for d in prefs.devices:
            # enabling the CPU alongside Metal costs more than it adds here
            d.use = (d.type == "METAL")
            if d.use:
                enabled.append(d.name)
        cy.device = "GPU"
        print("[CFG] metal devices enabled: %s" % enabled)
    else:
        cy.device = "CPU"

    return cy


def report_cycles_settings():
    cy = bpy.context.scene.cycles
    vs = bpy.context.scene.view_settings
    print("[CFG] engine=%s device=%s samples=%d" %
          (bpy.context.scene.render.engine, cy.device, cy.samples))
    print("[CFG] max_bounces=%d diffuse=%d glossy=%d transmission=%d" %
          (cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces))
    print("[CFG] denoise=%s clamp_dir=%.3f clamp_indir=%.3f" %
          (cy.use_denoising, cy.sample_clamp_direct, cy.sample_clamp_indirect))
    print("[CFG] view_transform=%s gamma=%.3f exposure=%.3f" %
          (vs.view_transform, vs.gamma, vs.exposure))


# --------------------------------------------------------------------------
# lighting
# --------------------------------------------------------------------------

def set_world(strength):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs["Surface"])


def sun_rotation_for(theta_deg):
    """
    Return the Euler X rotation that aims a sun's -Z axis along the
    propagation direction (0, -cos t, -sin t): theta measured from the panel
    normal +Y, positive = arriving from above.
    """
    t = math.radians(theta_deg)
    return math.atan2(-math.cos(t), math.sin(t))


def add_sun(theta_deg, strength=1.0, angular_size_deg=0.5):
    """
    A strictly delta-function sun (angle = 0) against a specular stage 1 makes
    the front camera sample the BRDF at a single direction: near zero almost
    everywhere and enormous at the glint angle, so window means become
    sample-noise on top of rare spikes. A small finite angular size stands in
    for real beam divergence plus coating microroughness and keeps the
    measurement conditioned. It does not fix the glint physics -- that is real,
    and is why max and p99 are reported alongside the mean.
    """
    d = bpy.data.lights.new("sun", type="SUN")
    d.energy = strength
    d.angle = math.radians(angular_size_deg)
    o = bpy.data.objects.new("sun", d)
    o.rotation_euler = (sun_rotation_for(theta_deg), 0.0, 0.0)
    bpy.context.collection.objects.link(o)
    return o


def add_stripe(theta_deg, cx, cz, stripe_w, panel_w, strength=200.0,
               spread_deg=1.0, target_z=None):
    """
    Near-collimated stripe standing in for a scanned laser line.

    `target_z` is where the stripe lands on the face plane; the lamp is placed
    back along the incidence direction from that point, so the line hits the
    same Z no matter the angle.
    """
    d = bpy.data.lights.new("stripe", type="AREA")
    d.shape = "RECTANGLE"
    d.size = panel_w * 1.2
    d.size_y = stripe_w
    d.energy = strength
    d.spread = math.radians(spread_deg)
    o = bpy.data.objects.new("stripe", d)
    t = math.radians(theta_deg)
    dist = 900.0
    z0 = cz if target_z is None else target_z
    o.location = (cx, dist * math.cos(t), z0 + dist * math.sin(t))
    o.rotation_euler = (sun_rotation_for(theta_deg), 0.0, 0.0)
    bpy.context.collection.objects.link(o)
    return o


# --------------------------------------------------------------------------
# render + measure
# --------------------------------------------------------------------------

def render_to(path_exr, path_png):
    """Render once; write both outputs from the same result."""
    sc = bpy.context.scene
    ims = sc.render.image_settings
    ims.file_format = "OPEN_EXR"
    ims.color_depth = "32"
    ims.color_mode = "RGB"
    ims.exr_codec = "ZIP"
    sc.render.filepath = path_exr
    bpy.ops.render.render(write_still=True)

    result = bpy.data.images.get("Render Result")
    ims.file_format = "PNG"
    ims.color_depth = "16"
    result.save_render(filepath=path_png, scene=sc)


def read_exr(path, res_x, res_y):
    img = bpy.data.images.load(path, check_existing=False)
    buf = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(buf)
    ch = len(buf) // (res_x * res_y)
    a = buf.reshape((res_y, res_x, ch))[:, :, :3]      # row 0 = bottom
    bpy.data.images.remove(img)
    return a


def window_stats(arr, win):
    x0, x1, z0, z1 = win
    sub = arr[int(z0):int(z1), int(x0):int(x1), :]
    lum = sub.mean(axis=2)
    return {
        "mean": float(lum.mean()),
        "p50": float(np.median(lum)),
        "p99": float(np.percentile(lum, 99)),
        "max": float(lum.max()),
        "px": int(lum.size),
    }


# --------------------------------------------------------------------------
# job
# --------------------------------------------------------------------------

def build_scene(cfg):
    # two geometry families share this harness: "slat" (profile2d) attenuates,
    # "scatter" (profile_scatter) aims at destroying form instead
    fam = cfg.get("family", "slat")
    if fam == "scatter":
        import profile_scatter as PS
        p = PS.ScatterParams(**cfg["params"])
        cs = PS.build_cross_section(p)
    elif fam == "ridge":
        import profile_ridge as PR
        p = PR.RidgeParams(**cfg["params"])
        cs = PR.build_cross_section(p)
    else:
        p = PanelParams(**cfg["params"])
        cs = build_cross_section(p)

    # The control plate is always the reference coating, never the panel's own
    # materials -- it is the "what a plain coated wall would do" baseline and
    # must not move when the panel's finishes are swapped.
    rho_control = cfg.get("rho_control", 0.05)
    # Entrance and interior are separate finishes. Any single bounce off a
    # surface the observer can see preserves the beam's position, so the
    # entrance wants to be as black as possible; the interior wants the
    # OPPOSITE, because lateral spreading before exit is what destroys form
    # and that needs the light to survive several bounces.
    rho_slat = cfg.get("rho_slat", cfg.get("rho_diffuse", 0.05))
    rho_chamber = cfg.get("rho_chamber", cfg.get("rho_diffuse", 0.05))
    rho_spec = cfg.get("rho_specular", rho_slat)
    rough = cfg.get("spec_roughness", 0.05)
    mat_mode = cfg.get("material_mode", "mixed")

    m_slat_d = make_diffuse("coat_slat", rho_slat)
    m_chamber = make_diffuse("coat_chamber", rho_chamber)
    m_ctrl = make_diffuse("coat_control", rho_control)
    m_s1 = m_slat_d if mat_mode == "all_diffuse" else make_glossy(
        "coat_specular", rho_spec, rough)

    loops_to_object(cs.stage1, p.face_w, 0.0, "slats", m_s1)
    loops_to_object(cs.stage2, p.face_w, 0.0, "baffles", m_chamber)
    loops_to_object(cs.shell, p.face_w, 0.0, "shell", m_chamber)

    ctrl_x0 = p.face_w + GAP
    make_flat_plate(p, ctrl_x0, "control", m_ctrl)

    return p, cs, ctrl_x0


def measurement_windows(p, ctrl_x0, cam):
    dx = p.face_w * MEAS_INSET_X
    dz = p.face_h * MEAS_INSET_Z
    panel = (dx, p.face_w - dx, -p.face_h / 2 + dz, p.face_h / 2 - dz)
    ctrl = (ctrl_x0 + dx, ctrl_x0 + p.face_w - dx,
            -p.face_h / 2 + dz, p.face_h / 2 - dz)
    return panel, ctrl


def to_pixel_window(win):
    x0, x1, z0, z1 = win
    a = world_to_pixel(x0, z0)
    b = world_to_pixel(x1, z1)
    return (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]))


def run(cfg):
    out_dir = cfg["out_dir"]
    tag = cfg["tag"]
    os.makedirs(out_dir, exist_ok=True)

    clear_scene()
    p, cs, ctrl_x0 = build_scene(cfg)

    total_w = ctrl_x0 + p.face_w
    cx, cz = total_w / 2.0, 0.0
    res_x = cfg.get("res_x", 1100)
    res_y = cfg.get("res_y", 500)
    ortho = total_w * 1.02

    configure_cycles(cfg.get("samples", 512), cfg.get("gpu", True),
                     seed=cfg.get("cycles_seed"))
    report_cycles_settings()

    w_panel, w_ctrl = measurement_windows(p, ctrl_x0, None)

    results = {
        "tag": tag,
        "params": cfg["params"],
        "derived": describe(p),
        "warnings": cs.warnings,
        "material_mode": cfg.get("material_mode", "mixed"),
        "rho_diffuse": cfg.get("rho_diffuse", 0.05),
        "rho_slat": cfg.get("rho_slat", cfg.get("rho_diffuse", 0.05)),
        "rho_chamber": cfg.get("rho_chamber", cfg.get("rho_diffuse", 0.05)),
        "rho_control": cfg.get("rho_control", 0.05),
        "rho_specular": cfg.get("rho_specular", 0.05),
        "spec_roughness": cfg.get("spec_roughness", 0.05),
        "samples": cfg.get("samples", 512),
        "n_slats": len(cs.stage1),
        "n_baffles": len(cs.stage2),
        "modes": {},
    }

    for job in cfg["renders"]:
        mode = job["mode"]
        theta = job.get("theta", 0.0)
        name = f"{tag}__{mode}_th{theta:+05.1f}"

        for o in list(bpy.data.objects):
            if o.type in ("LIGHT", "CAMERA"):
                bpy.data.objects.remove(o, do_unlink=True)

        # hemi_view tilts the observer; every other mode observes from the
        # front and tilts the light instead
        elev = theta if mode == "hemi_view" else 0.0
        setup_camera(cx, cz, ortho, res_x, res_y, elev_deg=elev)
        px_panel = to_pixel_window(w_panel)
        px_ctrl = to_pixel_window(w_ctrl)

        if mode in ("hemi", "hemi_view"):
            set_world(1.0)
        elif mode == "angle":
            set_world(0.0)
            add_sun(theta, strength=1.0,
                    angular_size_deg=job.get("sun_angle_deg", 0.5))
        elif mode == "form":
            set_world(0.0)
            add_stripe(theta, cx, cz, job.get("stripe_w", 8.0), total_w,
                       strength=job.get("strength", 200.0))
        else:
            raise ValueError(mode)

        exr = os.path.join(out_dir, name + ".exr")
        png = os.path.join(out_dir, name + ".png")
        render_to(exr, png)

        arr = read_exr(exr, res_x, res_y)
        s_panel = window_stats(arr, px_panel)
        s_ctrl = window_stats(arr, px_ctrl)
        ratio = s_panel["mean"] / s_ctrl["mean"] if s_ctrl["mean"] > 1e-12 else float("nan")

        rec = {"theta": theta, "panel": s_panel, "control": s_ctrl,
               "ratio_mean": ratio, "exr": exr, "png": png,
               "px_panel": px_panel, "px_ctrl": px_ctrl}
        results["modes"][name] = rec

        # the Lambertian control must read rho at every theta in hemi_view;
        # if it drifts, the tilt or the windows are wrong, not the panel
        flag = ""
        if mode == "hemi_view" and abs(s_ctrl["mean"] - cfg.get("rho_control", 0.05)) > 2e-3:
            flag = "  <-- CONTROL DRIFT, tilt/window suspect"
        print("[RESULT] %s  panel=%.6g  ctrl=%.6g  ratio=%.4f%s" %
              (name, s_panel["mean"], s_ctrl["mean"], ratio, flag))

    rpath = os.path.join(cfg.get("results_dir", out_dir), tag + ".json")
    os.makedirs(os.path.dirname(rpath), exist_ok=True)
    with open(rpath, "w") as f:
        json.dump(results, f, indent=2)
    print("[DONE]", rpath)
    return results


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    if len(argv) >= 2 and argv[0] == "--job":
        with open(argv[1]) as f:
            cfg = json.load(f)
    else:
        raise SystemExit("usage: ... -- --job <config.json>")
    run(cfg)


if __name__ == "__main__":
    main()
