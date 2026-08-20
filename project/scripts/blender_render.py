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
    if name == "Cone3DParams":
        import geom3d
        return geom3d.describe(p)
    if name == "TopoParams":
        import geom_topo
        return geom_topo.describe(p)
    if name == "CellParams":
        import geom_cell
        return geom_cell.describe(p)
    if name == "StackParams":
        import geom_stack
        return geom_stack.describe(p)
    if name == "FloorParams":
        import geom_floor
        return geom_floor.describe(p)
    if name == "PerfParams":
        import geom_perf
        return geom_perf.describe(p)
    # NOTE: this fallthrough is silent, and it is how a TopoParams run failed
    # with "no attribute 'slat_len'" -- profile2d.describe was handed a params
    # object from a different family. Any new family MUST be registered above.
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


def make_ar_glass(name, r_surface, roughness=0.02):
    """Idealised AR-coated glass for the Phase 8 window: each SURFACE
    reflects `r_surface` into the specular lobe and transmits the rest.
    The plate mesh is a closed slab, so a through ray crosses two
    surfaces and the plate's specular return is ~2R, which is the "R per
    surface" the vendor curves quote.

    Deliberate simplifications, all recorded in the sweep:
    - R is CONSTANT over angle. Real AR coatings hold R only inside
      their design cone and rise steeply toward grazing; that curve is
      exactly what the physical coupon must supply (report 8.1 marks the
      vendor numbers 추측-class). Simulating an invented curve would
      dress up a guess as transport.
    - No refraction offset (Transparent BSDF, not Refraction): a 2 mm
      plate displaces a 40-degree ray by ~1 mm laterally, irrelevant at
      every distance in the scene, and skipping the index keeps R the
      only free parameter.
    - No absorption: low-iron glass loses well under 1 %/pass, invisible
      beside R and the trap.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    gl.inputs["Roughness"].default_value = roughness
    mix.inputs["Fac"].default_value = r_surface
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


# --- the coating, fitted to a real measurement --------------------------------
#
# make_glossy has no Fresnel: its directional-hemispherical reflectance is flat
# with angle (0.4953% head-on, 0.4521% at 80 deg for rho=0.005). Real black
# coatings do the opposite -- they get worse toward grazing, steeply.
#
# Filip & Vavra 2026 (reference/2601.05094v1.pdf, Fig. 6, p.7) measured Musou
# Black paint on a goniometer, 24488 samples, and report THR -- which is
# defined by their eq. 1 as exactly the quantity hemi_view reads:
#
#     theta_i    0      15     30     45     60     75     80
#     THR      1.00%  1.00%  1.03%  1.13%  1.43%  2.33%  3.18%
#
# So the coating we have been assuming is 2x optimistic head-on and about 7x
# optimistic at 80 deg, with the angular trend running the wrong way.
#
# This model is a FIT to that curve, not a derivation. A bare dielectric over
# an absorber would give ~4% at normal incidence; Musou Black reads 1.00%
# because its own micro-roughness is already trapping light. Rather than invent
# a mechanism, split the measurement into the two pieces that reproduce it:
#
#     rho_dh(theta) = rho_body  +  spec_scale * F(theta, IOR)
#
# a body term with no angular dependence, plus a Fresnel-shaped term scaled
# down from a full dielectric. Fitting rho(0) = 1.00% and rho(80) = 3.18% with
# IOR 1.5 gives rho_body = 0.758%, spec_scale = 0.0605 (6% of a full dielectric
# lobe).
#
# MEASURED in Cycles on a genuinely flat plate (scripts/fit_coating.py), against
# the five angles NOT used in the fit:
#
#     theta      0      15     30     45     60     75     80
#     target   1.000  1.000  1.030  1.130  1.430  2.330  3.180  %
#     Cycles   0.998  0.999  1.007  1.060  1.294  2.278  3.085  %
#     residual -0.2   -0.1   -2.2   -6.2   -9.5   -2.2   -3.0   %
#
# 2026-08-20 CORRECTION -- WHAT THAT RESIDUAL ROW IS, AND IS NOT.
#
# It was read here as the accuracy of the implementation, and the theta-0 row
# was described as exact by construction. Neither survives measurement. The
# model this file actually builds, evaluated in pure Python, reproduces the
# Cycles row to better than 0.04% at EVERY angle:
#
#     theta        0      15      30      45      60      75      80
#     Cycles    .00998  .00999  .01007  .01060  .01294  .02278  .03085
#     model     .00998  .00999  .01007  .01060  .01293  .02277  .03086
#     error     +.02%   -.03%   +.03%   -.03%   -.04%   -.03%   +.03%
#
# So the residual row is the MODEL disagreeing with Filip & Vavra's paper, not
# the implementation disagreeing with the model. Those are different claims and
# only the second would be a defect. See materials.Material.rho_dh, whose
# self-test locks the agreement above.
#
# Two things had to be right to close it, both found by the session working on
# the ray tracer:
#
#   * THE FRESNEL TERM IS THE EXACT DIELECTRIC CURVE, NOT SCHLICK. Anything
#     reproducing what ShaderNodeFresnel evaluates must use the exact one; they
#     agree at normal incidence and diverge by -21.5% at 60 deg and +5.7% at
#     80. materials.fresnel() is exact; Schlick survives under its own name.
#
#   * THE MIX SHADER CARRIES A CROSS-TERM. mix(diffuse, glossy, fac) is
#     (1-fac)*body + fac*1, so the diffuse arm is attenuated by the same fac
#     that weights the specular arm. It integrates to rho0 - fac*body, NOT
#     rho0. At the fitted split that is 0.99818% against a nominal 0.998 --
#     which IS the "-0.2" in the row above. The theta-0 row is not exact by
#     construction; it is short by exactly the cross-term.
#
# Worst residual 9.5%, at 60 deg, and always on the optimistic side in the
# 45-60 band. A parameter sweep found body=0.0082 gives a lower WORST residual
# (6.1%) by spreading the error, but it costs +6% at normal incidence, which is
# the angle every headline number is quoted at. Exact-at-normal is kept
# deliberately; the mid-band bound is documented instead of hidden. That
# trade-off is unaffected by the correction above -- it is a choice about which
# angle to favour against the PAPER, and the paper is still what it was.
#
# For scale: this replaces a model that was 100% wrong at normal incidence and
# 600% wrong at 80 deg, with the angular trend running the wrong way.
#
# DO NOT read the 9.5% as the accuracy of the coating model -- and, per the
# correction above, do not read it as the accuracy of this implementation
# either. The paper reports
# BRDF "in relative units" and never states how THR is put on an absolute
# scale; their own Vantablack reads 0.0023 against a 3.5e-4 spec, and their
# Musou reads 0.0100 against a 6e-3 spec. An absolute uncertainty of order
# 0.002 is 20% of the 1.00% headline. So the SHAPE of this curve is well
# supported and the absolute level is +/-20%. The lock target below is our own
# measured implementation, which is the right thing to guard against drift --
# it is not a claim to have matched reality to four digits.
#
# The glossy lobe is white, so roughness redistributes the reflected light
# without changing how much of it there is: rho_dh is roughness-independent
# here and roughness controls only the SHAPE of the return, which is what form
# destruction depends on. Sweep it per geometry -- the viper's scales got
# DARKER when coated with Au-Pd (Mouchet 2024 p.8), so coating and geometry are
# not separable.

# THESE NOW LIVE IN scripts/materials.py and are re-exported here.
# ~30 sweep scripts read them as BR.MUSOU_BODY and BR.coating_split, and
# lock.py::material_check guards the coating against drift -- so a second copy
# of the constants is a second thing to keep in step, which is exactly what
# `principles/02` says goes wrong. One home, re-exported.
from materials import (                                            # noqa: E402
    MUSOU_THR, MUSOU_BODY, MUSOU_SPEC_SCALE, MUSOU_IOR,
)


# The single most consequential UNMEASURED parameter in the project.
#
# The fit was made against a flat-plate rho_dh(theta) curve, and that curve
# cannot distinguish a diffuse return from a specular one -- both integrate to
# the same hemispherical total. The split was therefore chosen, not measured:
# body 0.00758 of a total 0.00998 makes the coating 76% Lambertian at normal
# incidence.
#
# That choice turns out to drive everything. Holding rho fixed and rendering
# each design under a Lambertian vs a specular BSDF reproduces the ENTIRE
# 2x-to-41x spread between designs; the Fresnel term itself contributes only
# 1.23-1.50x and is nearly design-independent. Under a specular surface a
# bounce on a flank sends light deeper; under a Lambertian one every square
# millimetre of wall has a direct view of the sky and simply leaks.
#
# So this is swept as an axis rather than fixed. coating_split(d) returns the
# (body, spec_scale) that give diffuse fraction d while keeping rho_dh(0) at
# the measured flat-plate value -- the one thing that IS constrained.

from materials import (                                            # noqa: E402
    F0_IOR15,        # Fresnel reflectance at normal, n = 1.5
    MUSOU_RHO0,      # measured flat-plate rho_dh(0)
    coating_split,   # (body, spec_scale) for a diffuse fraction at fixed rho0
)


def make_depth_split(name, paint_depth, shallow, deep, roughness=0.30,
                     ior=MUSOU_IOR, deep_until=None, paint_fade=0.0):
    """`make_coating`, but its two constants switch at a depth plane.

    Musou Black and black anodising differ only in `body` and `spec_scale`, so
    the tree does not need duplicating -- only those two scalars are made
    position-dependent. The first attempt copied a whole finished node tree
    twice and mixed the results; the copy dropped links and the panel rendered
    at 54 % where its own material could not exceed 5, which is how the
    approach was rejected.

    `shallow` and `deep` are (body, spec_scale). The boundary is the plane
    y = -paint_depth: paint above it, as-bought below.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    # fac = 1 below the paint line
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    # THE BOUNDARY IS A STEP UNLESS ASKED OTHERWISE, and a real one is not.
    # Paint sprayed into a cell thins with depth and fades out; it does not
    # stop on a plane. `paint_fade` is the width of that transition in mm,
    # centred on `paint_depth`: 0 keeps the hard step, 6 means the film runs
    # out linearly between 7 and 13 mm for a 10 mm nominal depth.
    fade = abs(float(paint_fade or 0.0))
    if fade > 1e-6:
        below = nt.nodes.new("ShaderNodeMapRange")
        below.inputs["From Min"].default_value = -abs(paint_depth) + fade / 2
        below.inputs["From Max"].default_value = -abs(paint_depth) - fade / 2
        below.inputs["To Min"].default_value = 0.0
        below.inputs["To Max"].default_value = 1.0
        below.clamp = True
        nt.links.new(sep.outputs["Y"], below.inputs["Value"])
    else:
        below = nt.nodes.new("ShaderNodeMath")
        below.operation = "LESS_THAN"
        below.inputs[1].default_value = -abs(float(paint_depth))
        nt.links.new(sep.outputs["Y"], below.inputs[0])
    # A real panel is not one part. A bought honeycomb arrives anodised and a
    # spray gun reaches a few mm in; the floor under it is a SEPARATE pressed
    # sheet, painted flat before assembly and therefore black all over. So the
    # as-bought finish occupies a BAND -- below the paint line but above the
    # floor -- not everything below the paint line. Without `deep_until` the
    # floor would inherit the tube's anodising, which is not a part anyone
    # would build.
    if deep_until is not None:
        above_floor = nt.nodes.new("ShaderNodeMath")
        above_floor.operation = "GREATER_THAN"
        above_floor.inputs[1].default_value = -abs(float(deep_until))
        nt.links.new(sep.outputs["Y"], above_floor.inputs[0])
        band = nt.nodes.new("ShaderNodeMath")
        band.operation = "MULTIPLY"
        nt.links.new(below.outputs[0], band.inputs[0])
        nt.links.new(above_floor.outputs["Value"], band.inputs[1])
        below = band

    def switch(v_shallow, v_deep):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = "MULTIPLY_ADD"          # deep*fac + shallow*(1-fac)
        d = nt.nodes.new("ShaderNodeMath")
        d.operation = "MULTIPLY"
        d.inputs[1].default_value = float(v_deep) - float(v_shallow)
        nt.links.new(below.outputs[0], d.inputs[0])
        add = nt.nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        add.inputs[1].default_value = float(v_shallow)
        nt.links.new(d.outputs["Value"], add.inputs[0])
        return add.outputs["Value"]

    fac = below.outputs[0]
    body_out = switch(shallow[0], deep[0])
    spec_out = switch(shallow[1], deep[1])

    fres = nt.nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = ior
    scale = nt.nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    nt.links.new(fres.outputs["Fac"], scale.inputs[0])
    nt.links.new(spec_out, scale.inputs[1])

    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Roughness"].default_value = 0.0
    # Blender 5.x renamed CombineRGB to CombineColor; ask for whichever this
    # build actually has rather than assuming.
    rgb = nt.nodes.new("ShaderNodeCombineColor"
                       if hasattr(bpy.types, "ShaderNodeCombineColor")
                       else "ShaderNodeCombineRGB")
    for i in range(3):
        nt.links.new(body_out, rgb.inputs[i])
    nt.links.new(rgb.outputs[0], diff.inputs["Color"])

    spec = (nt.nodes.new("ShaderNodeBsdfAnisotropic")
            if "ShaderNodeBsdfAnisotropic" in dir(bpy.types)
            else nt.nodes.new("ShaderNodeBsdfGlossy"))
    spec.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    spec.inputs["Roughness"].default_value = roughness

    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(scale.outputs[0], mix.inputs["Fac"])
    nt.links.new(diff.outputs[0], mix.inputs[1])
    nt.links.new(spec.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def make_coating(name, roughness=0.30, body=MUSOU_BODY,
                 spec_scale=MUSOU_SPEC_SCALE, ior=MUSOU_IOR):
    """A dark coating whose reflectance rises toward grazing, as real ones do.

    body        angle-independent part of rho_dh
    spec_scale  fraction of a full dielectric Fresnel lobe to keep
    ior         index used for the Fresnel curve shape
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")

    fres = nt.nodes.new("ShaderNodeFresnel")
    fres.inputs["IOR"].default_value = ior
    scale = nt.nodes.new("ShaderNodeMath")
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = spec_scale
    nt.links.new(fres.outputs["Fac"], scale.inputs[0])

    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (body, body, body, 1.0)
    diff.inputs["Roughness"].default_value = 0.0

    spec = (nt.nodes.new("ShaderNodeBsdfAnisotropic")
            if "ShaderNodeBsdfAnisotropic" in dir(bpy.types)
            else nt.nodes.new("ShaderNodeBsdfGlossy"))
    spec.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    spec.inputs["Roughness"].default_value = roughness

    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(scale.outputs[0], mix.inputs["Fac"])
    nt.links.new(diff.outputs[0], mix.inputs[1])
    nt.links.new(spec.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def loops_to_object(loops, width, x0, name, material):
    """Extrude a list of closed Y-Z loops along X into one object.

    `width` is the FULL extrusion length and `x0` its start. The 1D families
    have `margin_depths` on their cross-section, which widens them in Z, and
    nothing at all along X -- the extrusion has always run exactly face_w.
    That was invisible for as long as the camera tilted only in the Z plane.
    The moment `phi_deg` rotates a panel 90 degrees, the un-margined axis lands
    in the tilt plane, the camera looks past the end of the panel, and a
    V-groove reads 28 % against a 1.14 % flat plate -- 25x a black coating,
    which is the signature of measuring the panel's own edge. Callers that
    measure must pass an extrusion that overruns the window on both sides.
    """
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


def mesh_to_object(verts, faces, name, material, deep_material=None,
                   paint_depth=None, slot_ids=None, slot_materials=None):
    """Build an object from an explicit 3D mesh.

    TWO FINISHES, SPLIT BY DEPTH. A panel is not painted uniformly. The
    honeycomb arrives anodized because that is how it is sold, and a spray gun
    reaches a few millimetres into a 6.5 mm cell, not 47. So the real part is
    "as-bought everywhere, painted near the mouth" -- and this project's own
    harness has always said the two regions want OPPOSITE things:

        the entrance wants to be as black as possible, because one bounce off
        a surface the observer can see preserves the beam's position;
        the interior wants the opposite, because lateral spreading before exit
        is what destroys form, and that needs light to survive several bounces.

    `paint_depth` is how far the paint reaches below y = 0, in mm. Faces whose
    lowest vertex sits within that band get `material`; everything deeper gets
    `deep_material`. The test is on the face's LOWEST vertex, not its centroid:
    a wall that straddles the boundary is only counted as painted if all of it
    is inside the band, so the split never flatters the paint.
    """
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(v[0], v[1], v[2]) for v in verts], [], faces)
    mesh.validate(verbose=False)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    if deep_material is not None and paint_depth is not None:
        obj.data.materials.append(deep_material)
        lim = -abs(float(paint_depth))
        n_deep = 0
        for poly in mesh.polygons:
            lowest = min(mesh.vertices[i].co.y for i in poly.vertices)
            if lowest < lim:
                poly.material_index = 1
                n_deep += 1
        print("[COAT] %s: %d of %d faces below %.1f mm get the deep finish"
              % (name, n_deep, len(mesh.polygons), abs(lim)), flush=True)
    elif slot_ids is not None and slot_materials:
        # PER-PART FINISHES. `slot_ids[i]` is which part face i belongs to, in
        # the order the faces were handed in; `slot_materials` maps that id to
        # a material. See `mat_slots`.
        #
        # THE POLYGON COUNT IS ASSERTED, not assumed. `mesh.validate()` above
        # is allowed to delete degenerate or duplicate faces, and if it ever
        # does, indexing polygons by enumeration position silently
        # desynchronises from `slot_ids` -- every face below the deletion
        # shifts by one and takes the wrong finish, with nothing in the render
        # to say so. Same posture as geom_stack's slab assert.
        if len(mesh.polygons) != len(faces):
            raise RuntimeError(
                "%s: mesh.validate() changed the face count (%d -> %d); slot "
                "ids can no longer be trusted" % (name, len(faces),
                                                  len(mesh.polygons)))
        # One bpy material per DISTINCT material, not per slot: two slots
        # resolving to the same finish share one. A mesh carrying eight
        # identical materials is a .blend that lies about the design.
        order, index_of = [], {}
        for sid in sorted(set(slot_ids)):
            m = slot_materials.get(sid)
            if m is None:
                continue
            k = m.name
            if k not in index_of:
                index_of[k] = len(order)
                order.append(m)
        for m in order:
            obj.data.materials.append(m)
        n_by = {}
        for i, poly in enumerate(mesh.polygons):
            m = slot_materials.get(slot_ids[i])
            if m is None:
                continue
            poly.material_index = index_of[m.name]
            n_by[m.name] = n_by.get(m.name, 0) + 1
        # AREA, not face count: area is the physical quantity and the counts
        # are wildly misleading here -- a honeycomb's tips are a quarter of its
        # faces and under a hundredth of its area.
        area = {}
        for i, poly in enumerate(mesh.polygons):
            m = slot_materials.get(slot_ids[i])
            if m is not None:
                area[m.name] = area.get(m.name, 0.0) + poly.area
        tot = sum(area.values()) or 1.0
        print("[SLOT] %s: %s" % (name, ";  ".join(
            "%s %d f / %.2f%% area" % (k, n_by.get(k, 0), 100 * v / tot)
            for k, v in sorted(area.items()))), flush=True)
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


def configure_cycles(samples, use_gpu=True, seed=None, persistent=False):
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

    # The scene is built once and the angles are looped over it, changing only
    # camera and lights, so re-syncing the mesh to the device on every angle is
    # pure waste. Measured on the 5-angle V-groove measurement: 10.06 s off,
    # 9.52 s on. Only set for multi-render jobs -- for a single render there is
    # nothing to persist and it only holds device memory. See `run`.
    sc.render.use_persistent_data = bool(persistent)

    if use_gpu:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        enabled = []
        for d in prefs.devices:
            # Enabling the CPU alongside Metal costs more than it adds here,
            # measured rather than assumed: the same 5-angle measurement takes
            # 10.06 s on Metal alone and 21.83 s on Metal + CPU. The CPU tiles
            # finish late and the GPU waits on them.
            d.use = (d.type == "METAL")
            if d.use:
                enabled.append(d.name)
        print("[CFG] metal devices enabled: %s" % enabled)

        # WITHOUT THIS GUARD A GPU RUN CAN QUIETLY BE A CPU RUN. Cycles does
        # not refuse `device = "GPU"` when no device is enabled -- it falls
        # back to the CPU, silently, and `report_cycles_settings` below still
        # prints device=GPU. Measured: 6.09 s against 2.0 s for the same frame,
        # with nothing in the log to say why. A number produced that way is not
        # wrong, but a sweep that says GPU while running 3x slower on the CPU
        # is exactly the kind of thing this project has been bitten by.
        if not enabled:
            if os.environ.get("ALLOW_CPU") == "1":
                cy.device = "CPU"
                print("[CFG] no Metal device; ALLOW_CPU=1 -- rendering on CPU "
                      "deliberately, expect ~3x the time")
            else:
                raise RuntimeError(
                    "gpu=True but no Metal device could be enabled. Cycles "
                    "would fall back to the CPU without saying so. Set "
                    "ALLOW_CPU=1 to render on the CPU on purpose.")
        else:
            cy.device = "GPU"
    else:
        cy.device = "CPU"

    return cy


def render_provenance():
    """What rendered this frame, read back off the scene rather than assumed."""
    cy = bpy.context.scene.cycles
    prefs = bpy.context.preferences.addons["cycles"].preferences
    return {
        "blender": bpy.app.version_string,
        "device": cy.device,
        "devices": [d.name for d in prefs.devices if d.use],
        "metalrt": getattr(prefs, "metalrt", None),
        "persistent_data": bool(bpy.context.scene.render.use_persistent_data),
    }


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
    # 8, NOT 16. The PNG is a picture for a person to look at; every number in
    # this project is read from the EXR beside it, which stays 32-bit float.
    # A 16-bit PNG of a 1400x950 preview is 5.3 MB against 1.4 MB for the same
    # image at 8-bit, and the difference is below one 8-bit level (measured:
    # max 0.992 of a level, mean 0.353). 36 gallery images cost 142 MB for it,
    # and project/renders/ holds 9.4 GB of the same waste.
    ims.color_depth = "8"
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

def _material_from(m, name):
    """One `materials.Material` -> one bpy material, by its own model.

    The discriminator matters: `make_glossy` is a bare Glossy BSDF and is NOT
    this model at diffuse_frac 0, which would put spec_scale = rho/F0 behind a
    Fresnel term. Reproducing an old number means emitting the old tree.
    """
    if m.model == "lambert":
        return make_diffuse(name, m.rho0)
    if m.model == "glossy":
        return make_glossy(name, m.rho0, m.roughness)
    body, spec_scale = m.split()
    return make_coating(name, roughness=m.roughness, body=body,
                        spec_scale=spec_scale, ior=m.ior)


def _slot_materials(cfg, verts, faces):
    """(slot_ids, {slot_id: bpy material}) for a per-part job.

    Returns (None, None) when every slot resolves to the same finish, so the
    caller can take the single-material path and keep the scene identical.
    """
    import materials as _MAT
    import mat_slots as _MS
    res = {k: _MAT.resolve(((cfg["materials"].get("slots") or {}).get(k)),
                           default=_MAT.LIBRARY[_MAT.STUDY_DEFAULT],
                           defaults=cfg["materials"].get("defaults") or {})
           for k in _MS.ASSIGNABLE}
    if len({m.key() for m in res.values()}) <= 1:
        return None, None
    prm = cfg.get("params", {}) or {}
    dep = prm.get("depth")
    if dep is None:                      # a stack states its two layers
        dep = (prm.get("top_depth", 0.0) or 0.0) + (prm.get("bot_depth", 0.0)
                                                    or 0.0)
    ids, _stats = _MS.classify(
        verts, faces, depth=abs(float(dep or 50.0)),
        floor_depth=float(cfg.get("floor_depth", 0.0) or 0.0))
    built = {}
    for key in _MS.ASSIGNABLE:
        built[_MS.BY_KEY[key]["id"]] = _material_from(res[key], "coat_" + key)
    # hidden faces are inside the union and see no light; give them the flank
    # finish so the .blend has no material-less polygons
    built[_MS.HIDDEN] = built[_MS.BY_KEY["walls"]["id"]]
    return ids, built


def _slot_uniform_material(cfg):
    import materials as _MAT
    import mat_slots as _MS
    blk = cfg["materials"]
    m = _MAT.resolve((blk.get("slots") or {}).get(_MS.ASSIGNABLE[0]),
                     default=_MAT.LIBRARY[_MAT.STUDY_DEFAULT],
                     defaults=blk.get("defaults") or {})
    return _material_from(m, "coat_uniform")


def build_scene(cfg):
    # two geometry families share this harness: "slat" (profile2d) attenuates,
    # "scatter" (profile_scatter) aims at destroying form instead
    fam = cfg.get("family", "slat")
    # families that hand back an explicit 3D mesh instead of a cross-section to
    # extrude. `mesh_fn` stays None for the extruded families.
    mesh_fn = None
    # A MESH BUILT BY THE CALLER, for geometry no family module produces. The
    # half-lap notched blade array (`sweep_blade_notch`) is a variant of the
    # shingle that `geom_topo` does not build, and measuring it through any
    # other path would mean a different harness -- different control patch,
    # different windows, different coating -- and therefore a number that
    # cannot be put beside the published ones. `params` still describes the
    # envelope so the windows and the control plate are placed exactly as
    # usual; only the panel's triangles come from outside.
    if cfg.get("prebuilt_mesh") is not None:
        import geom_stack as ST
        p = ST.StackParams(**cfg["params"])
        _pv, _pf = cfg["prebuilt_mesh"]
        mesh_fn = lambda _p, _v=_pv, _f=_pf: (_v, _f)          # noqa: E731
        cs = None
    elif fam == "scatter":
        import profile_scatter as PS
        p = PS.ScatterParams(**cfg["params"])
        cs = PS.build_cross_section(p)
    elif fam == "ridge":
        import profile_ridge as PR
        p = PR.RidgeParams(**cfg["params"])
        cs = PR.build_cross_section(p)
    elif fam == "cone3d":
        import geom3d as G3
        p = G3.Cone3DParams(**cfg["params"])
        mesh_fn = G3.build_mesh
        cs = None
    elif fam == "topo":
        import geom_topo as GT
        p = GT.TopoParams(**cfg["params"])
        mesh_fn = GT.build_mesh
        cs = None
    elif fam == "perf":
        import geom_perf as GP
        p = GP.PerfParams(**cfg["params"])
        mesh_fn = GP.build_mesh
        cs = None
    elif fam == "floor":
        # `geom_floor` was written as the BOTTOM of a stack, but the shapes it
        # builds -- pyramid, wave -- are the RF absorber families in their own
        # right, and measuring them at full depth as a top surface needs no new
        # module, only this entry.
        import geom_floor as GF
        p = GF.FloorParams(**cfg["params"])
        mesh_fn = GF.build_mesh
        cs = None
    elif fam == "stack":
        import geom_stack as ST
        p = ST.StackParams(**cfg["params"])
        mesh_fn = ST.build_mesh
        cs = None
    elif fam == "cell":
        import geom_cell as GC
        p = GC.CellParams(**cfg["params"])
        mesh_fn = GC.build_mesh
        cs = None
    elif fam == "corner":
        # Phase 9.c: a wall panel meeting a floor panel at a 90-degree
        # inside corner -- the junction the venue photo shows spill on.
        # The wall field is the normal floor-family build; the floor is
        # a second field rotated tips-up and run toward the camera.
        # Windows stay on the wall plane; observers must sit ABOVE the
        # corner (theta >= +20) so the floor's far end face projects
        # outside the window -- enforced in run() callers, recorded in
        # the sweep. cfg["corner"] = {"floor_len": mm, "smooth": bool}.
        import geom_floor as GF
        p = GF.FloorParams(**cfg["params"])
        mesh_fn = None
        cs = None
    elif fam == "arplate":
        # Phase 8: tilted AR window over an absorbing void. `cfg["params"]`
        # is a FloorParams ENVELOPE (face_w/face_h place the windows and
        # the control); the plate and box are built below, not by geom_floor.
        import geom_floor as GF
        p = GF.FloorParams(**cfg["params"])
        mesh_fn = None
        cs = None
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
    if mat_mode == "all_diffuse":
        m_s1 = m_slat_d
    elif mat_mode == "coating":
        # the Fresnel-bearing coating fitted to a real goniometer measurement.
        # cfg["coating"] overrides the fit constants; defaults are the Musou
        # Black fit in make_coating.
        c = cfg.get("coating", {})
        m_s1 = make_coating("coat_real",
                            roughness=c.get("roughness", rough),
                            body=c.get("body", MUSOU_BODY),
                            spec_scale=c.get("spec_scale", MUSOU_SPEC_SCALE),
                            ior=c.get("ior", MUSOU_IOR))
        m_chamber = m_s1 if c.get("interior_too", True) else m_chamber
    else:
        m_s1 = make_glossy("coat_specular", rho_spec, rough)

    if fam == "corner":
        from types import SimpleNamespace
        import geom_floor as GF
        cn = cfg.get("corner", {})
        flen = float(cn.get("floor_len", 300.0))
        wall_prm = dict(cfg["params"])
        floor_prm = dict(cfg["params"], face_h=flen)
        if cn.get("smooth"):
            # the smooth-Musou control: same envelopes, texture removed.
            # pitch stays FINE (4) so the lattice overshoot stays at the
            # textured case's ~8 mm -- pitch 50 overshot 100 mm into the
            # control plate's region (caught in preview, control 0.031).
            for d in (wall_prm, floor_prm):
                d.update(depth=0.001, tip_flat=0.0)
        wv, wf = GF.build_mesh(GF.FloorParams(**wall_prm))
        mesh_to_object(wv, wf, "corner_wall", m_s1)
        fv, ff = GF.build_mesh(GF.FloorParams(**floor_prm))
        # NOTE: a wall-wall VERTICAL corner needs no scene of its own.
        # Under the isotropic world, rotating the whole wall-floor
        # corner about the VIEW axis maps it onto the vertical corner
        # with identical rho_dh -- the 9.c numbers cover it by symmetry
        # (recorded in FINDINGS_phase9c.md). A draft "vertical" build
        # was removed here: it left a 60 mm gap at the junction and the
        # elevation-tilt camera cannot frame that corner anyway.
        # wall-floor corner: rotate +90 about x (tips point up +z),
        # slide so the field runs from the corner line toward the camera
        fv = [(x, -z + flen / 2.0, y) for (x, y, z) in fv]
        mesh_to_object(fv, ff, "corner_floor", m_s1)
        cs = SimpleNamespace(warnings=[], stage1=[], stage2=[], shell=[])
    elif fam == "arplate":
        from types import SimpleNamespace
        ar = cfg.get("ar", {})
        R = float(ar.get("r_surface", 0.01))
        tilt = math.radians(float(ar.get("tilt_deg", 25.0)))
        t_pl = float(ar.get("thickness", 2.0))
        # The plate is LONGER than the face so its tilted projection still
        # covers the measurement window (face_h * 1.18 covers tilt 25).
        Hp = float(ar.get("plate_h", p.face_h * 1.18))
        # 90 clears the plate's swung-back bottom edge (-50 at tilt 25 on a
        # 118 plate) with room for the trap field in front of the back wall
        D = float(ar.get("void_depth", 90.0))
        m_ar = make_ar_glass("ar_glass", R,
                             float(ar.get("ar_roughness", 0.02)))
        m_void = make_diffuse("void_black", float(ar.get("void_rho", 0.0)))
        xm = 6.0
        x0v, x1v = -xm, p.face_w + xm

        # The plate hinges at its TOP edge (kept at the wall plane); the
        # BOTTOM edge swings back into the void -- a hopper, not a leaning
        # mirror -- so the glass faces DOWN by `tilt`. Sign chased twice
        # and finally pinned by a preview RENDER, not by intuition: rotate
        # about x by alpha maps the normal (0,1,0) to (0,cos a,sin a), so
        # top-back (a=+25) faces the CEILING and throws a +40 beam back
        # into the room near-horizontal (the preview measured exactly
        # that); bottom-back (a=-25) faces down, and a beam from
        # elevation +theta reflects to -(theta + 2*tilt): beam 0 lands in
        # a trough at the wall base, beam +40 goes straight down and dies
        # inside the box. The only beam a level observer could catch
        # mirrored must rise from 2*tilt BELOW the horizon -- the floor.
        # Bonus: the exposed face points downward, so it sheds dust; the
        # up-facing side is sealed inside the void (coupon still owed).
        def pl(zp, yp):
            z = Hp / 2.0 - (Hp / 2.0 - zp) * math.cos(tilt) \
                - yp * math.sin(tilt)
            y = -(Hp / 2.0 - zp) * math.sin(tilt) + yp * math.cos(tilt)
            return y, z
        pv, pf = [], []
        for yp in (0.0, -t_pl):
            for zp in (Hp / 2.0, -Hp / 2.0):
                y, z = pl(zp, yp)
                pv.append((x0v, y, z))
                pv.append((x1v, y, z))
        # Consistent OUTWARD winding, face by face (the audit found the
        # first draft mixed 3 in / 3 out; cross-products checked by hand:
        # front +y, back -y, top +z, bottom -z, sides +-x, all before the
        # orientation-preserving rotation). Measured A/B: see FINDINGS 8.2.
        pf = [(0, 1, 3, 2), (6, 7, 5, 4), (4, 5, 1, 0),
              (2, 3, 7, 6), (0, 2, 6, 4), (5, 7, 3, 1)]
        mesh_to_object(pv, pf, "ar_plate", m_ar)

        # the void: an open box behind the wall plane. rho defaults to 0 --
        # an IDEALISED interior; anything the observer sees past the plate
        # edges reads black, which is the concept's own claim (hidden void)
        # and is flagged as idealised in the sweep notes.
        zb = Hp / 2.0 + 2.0
        xb0, xb1 = x0v - 2.0, x1v + 2.0
        bv = []
        for y in (0.0, -D):
            for z in (zb, -zb):
                bv.append((xb0, y, z))
                bv.append((xb1, y, z))
        bf = [(4, 5, 7, 6),                     # back wall y=-D
              (0, 1, 5, 4), (2, 3, 7, 6),      # top / bottom
              (0, 2, 6, 4), (1, 3, 7, 5)]      # sides
        mesh_to_object(bv, bf, "ar_void", m_void)

        # 8.2b found everything dangerous retreats to a TOP STRIP of the
        # glass (the only region whose mirror path clears the sill). The
        # buildable unit closes it with a rim lip: an opaque cover in the
        # wall plane from the box top down to `lip_to`. Idealised black
        # here (the real lip is tile-clad), consistent with the void.
        # Phase 8.3: a Lambertian floor plane in FRONT of the unit, at
        # the sill level, standing in for the real room floor that a
        # below-horizon sightline actually sees mirrored (the uniform
        # white world is the worst case; this is the deployed case).
        # v2 after a VOID first attempt: an infinite sill-level floor
        # OCCLUDES a below-horizon camera (it measured the floor's own
        # rho and drifted the control). A 300 mm STRIP limited to the
        # panel's own x-range is the mirrored scene without blocking
        # either the camera (clears down to about -15 deg at the 3 m
        # camera distance) or the control plate's sky.
        if ar.get("room_floor") is not None:
            # v3: the floor sits BELOW the unit (a wall-mounted box), at
            # `floor_drop` under the sill, running `floor_len` forward.
            # v2's sill-level 300 strip let the mirror see white world
            # past its far edge from -12 on; dropping the floor lets it
            # run long without occluding the 3 m camera.
            m_floor = make_diffuse("room_floor",
                                   float(ar["room_floor"]))
            fz = -zb - float(ar.get("floor_drop", 220.0))
            fl = float(ar.get("floor_len", 1000.0))
            fv = [(x0v - 10, -0.5, fz), (x1v + 10, -0.5, fz),
                  (x0v - 10, fl, fz), (x1v + 10, fl, fz)]
            mesh_to_object(fv, [(0, 1, 3, 2)], "room_floor", m_floor)

        if ar.get("lip_to") is not None:
            lz = float(ar["lip_to"])
            lv = [(x0v, -0.5, zb), (x1v, -0.5, zb),
                  (x0v, -0.5, lz), (x1v, -0.5, lz)]
            mesh_to_object(lv, [(0, 1, 3, 2)], "ar_lip", m_void)

        # system runs put the final-sample pyramid field at the back of the
        # void as the real trap; its tips face the room at y = -(D - 22).
        if ar.get("backing") == "pyramid":
            tv, tf = GF.build_mesh(p)
            off = -(D - 24.0)        # tips at -(D-24) = -66, base -88,
            tv = [(x, y + off, z) for (x, y, z) in tv]   # 2 mm off the wall
            m_trap = make_coating("coat_trap", roughness=0.30)
            mesh_to_object(tv, tf, "ar_trap", m_trap)

        cs = SimpleNamespace(warnings=[], stage1=[], stage2=[], shell=[])
    elif cs is None:
        from types import SimpleNamespace
        v, f = mesh_fn(p)
        # `paint_depth` opts a 3D family into the two-finish split. Absent, the
        # whole mesh keeps one material and every earlier measurement is
        # reproduced exactly.
        pd = cfg.get("paint_depth")
        if pd is not None:
            cc = cfg.get("coating", {})
            dp = cfg.get("deep_coating", {})
            mat = make_depth_split(
                "coat_split", pd,
                (cc.get("body", MUSOU_BODY),
                 cc.get("spec_scale", MUSOU_SPEC_SCALE)),
                (dp.get("body", 0.05), dp.get("spec_scale", 0.05)),
                roughness=cc.get("roughness", rough),
                deep_until=cfg.get("deep_until"),
                paint_fade=cfg.get("paint_fade", 0.0))
        else:
            mat = m_s1
        # PER-PART FINISHES, when the job asks for them. `cfg["materials"]` is
        # the slot -> material assignment; absent, nothing here runs and every
        # earlier measurement is reproduced through the identical code path.
        sids, smats = None, None
        if pd is None and cfg.get("materials"):
            sids, smats = _slot_materials(cfg, v, f)
            if smats is None:
                # UNIFORM IS A FAST PATH, NOT AN OPTIMISATION. When every slot
                # resolves to the same finish there must be ONE material and
                # today's code path, so the Cycles scene is byte-identical and
                # a published row still reproduces. A second material carrying
                # the same numbers is not free: it changes nothing physical and
                # everything about what the .blend claims.
                mat = _slot_uniform_material(cfg)
                sids = None
        mesh_to_object(v, f, "panel_mesh", mat,
                       slot_ids=sids, slot_materials=smats)
        cs = SimpleNamespace(warnings=[], stage1=[], stage2=[], shell=[])
    else:
        # Overrun the face along the extrusion axis by the same margin the
        # cross-section already gets, so the panel is longer than the window
        # from every azimuth. At phi = 0 this changes nothing measurable -- the
        # extra length sits outside the frame -- and it is what makes any
        # rotated measurement of a 1D family mean anything at all.
        _ex = getattr(p, "margin_depths", 0.0) * getattr(p, "depth", 0.0)
        _ex = max(_ex, getattr(p, "face_h", p.face_w) * 0.5)
        loops_to_object(cs.stage1, p.face_w + 2 * _ex, -_ex, "slats", m_s1)
        loops_to_object(cs.stage2, p.face_w + 2 * _ex, -_ex, "baffles",
                        m_chamber)
        loops_to_object(cs.shell, p.face_w + 2 * _ex, -_ex, "shell",
                        m_chamber)

    # --- azimuth of incidence ------------------------------------------
    # The camera in `hemi_view` tilts in ONE plane, so every number this
    # project has published is at a single azimuth. For an extruded V-groove or
    # an all-parallel blade array that is not a property of the design, it is a
    # property of which way it happened to be laid down -- and the brief says
    # the beam direction is unknown. Rotating the PANEL about its own normal is
    # equivalent to moving the source in azimuth and leaves the control plate,
    # the camera and the measurement windows exactly where they were.
    phi = float(cfg.get("phi_deg", 0.0) or 0.0)
    if abs(phi) > 1e-9 and fam == "arplate":
        # the lip, room floor and hopper are gravity-defined; rotating
        # them about the panel normal builds a scene that cannot exist.
        raise ValueError("phi rotation is not defined for the arplate "
                         "family (audit 2026-08-17)")
    if abs(phi) > 1e-9:
        import math as _m
        a = _m.radians(phi)
        ca, sa = _m.cos(a), _m.sin(a)
        cx, cz = p.face_w / 2.0, 0.0
        for ob in bpy.data.objects:
            if ob.type != "MESH" or ob.name.startswith("control"):
                continue
            for vt in ob.data.vertices:
                x, z = vt.co.x - cx, vt.co.z - cz
                vt.co.x = cx + x * ca - z * sa
                vt.co.z = cz + x * sa + z * ca
            ob.data.update()

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


# Optional per-render progress hook. sim_server points this at its progress
# counter so the UI can poll a live "3/5" while the queue blocks; sweeps leave
# it None. A hook failure must never kill a render, hence the bare except.
PROGRESS_CB = None


def _progress(done, total):
    if PROGRESS_CB:
        try:
            PROGRESS_CB(done, total)
        except Exception:
            pass


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
                     seed=cfg.get("cycles_seed"),
                     persistent=len(cfg["renders"]) > 1)
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
        "rho_specular": cfg.get("rho_specular",
                                cfg.get("rho_slat",
                                        cfg.get("rho_diffuse", 0.05))),
        "spec_roughness": cfg.get("spec_roughness", 0.05),
        "samples": cfg.get("samples", 512),
        "cycles_seed": cfg.get("cycles_seed", SEED),
        "phi_deg": cfg.get("phi_deg", 0.0),
        "coating": cfg.get("coating"),
        "ar": cfg.get("ar"),
        "paint_depth": cfg.get("paint_depth"),
        "n_slats": len(cs.stage1),
        "n_baffles": len(cs.stage2),
        # what actually rendered this, not what was asked for -- so a row can
        # be checked after the fact rather than trusted
        "renderer": render_provenance(),
        "modes": {},
    }

    for ri, job in enumerate(cfg["renders"]):
        _progress(ri, len(cfg["renders"]))
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

        drift = (mode == "hemi_view"
                 and abs(s_ctrl["mean"] - cfg.get("rho_control", 0.05))
                 > 2e-3)
        rec = {"theta": theta, "panel": s_panel, "control": s_ctrl,
               "ratio_mean": ratio, "exr": exr, "png": png,
               "px_panel": px_panel, "px_ctrl": px_ctrl,
               "control_drift": bool(drift)}
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
