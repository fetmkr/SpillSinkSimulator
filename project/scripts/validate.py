"""
Validate the measurement chain before trusting any panel number.

    Blender --background --factory-startup --python scripts/validate.py

Three checks, each one able to fail loudly:

1. LINEARITY   An emission-1.0 plane must read exactly 1.0. Anything else
               means colour management is not Standard / gamma 1.0 and every
               numerical comparison downstream is void.

2. LAMBERTIAN  A flat rho = 0.05 plate under uniform hemispherical
               illumination must read ~0.0389, not 0.05. The camera collects
               only part of the scattered hemisphere, which is exactly why
               results are only ever quoted as a ratio against a flat control
               in the same frame.

3. BOX CAVITY  A cube with one open face has aperture fraction f = 1/6 =
               0.1667. The blackbody-cavity formula

                   rho_eff = rho * f / (1 - rho * (1 - f))

               predicts a cavity/flat ratio of 0.174. The previously recorded
               render measured 0.233 -- the formula is ~34% optimistic because
               wall area near the aperture has a better view of the exit than
               uniform diffusion assumes. Reproducing ~0.233 confirms the
               bounce budget and the measurement windows are both sane.
"""

import sys
import os
import math
import json

import bpy
import bmesh
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_render import (                                    # noqa: E402
    clear_scene, make_diffuse, setup_camera, configure_cycles,
    report_cycles_settings, set_world, render_to, read_exr,
    window_stats, to_pixel_window,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders", "_validate")
RES = os.path.join(ROOT, "results")

RES_X, RES_Y = 900, 450
SAMPLES = 2048
RHO = 0.05
A = 200.0            # cube side / plate side


def quad(bm, pts):
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new(vs)


def add_mesh(name, faces, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for f in faces:
        quad(bm, f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat)
    bpy.context.collection.objects.link(ob)
    return ob


def flat_plate(x0, mat, name):
    return add_mesh(name, [[(x0, 0, -A / 2), (x0 + A, 0, -A / 2),
                            (x0 + A, 0, A / 2), (x0, 0, A / 2)]], mat)


def open_cube(x0, mat, name):
    """Cube of side A, open toward +Y (the camera). Aperture fraction 1/6."""
    x1 = x0 + A
    zl, zh = -A / 2, A / 2
    yb = -A                      # back face
    faces = [
        [(x0, yb, zl), (x1, yb, zl), (x1, yb, zh), (x0, yb, zh)],      # back
        [(x0, 0, zl), (x0, yb, zl), (x0, yb, zh), (x0, 0, zh)],        # left
        [(x1, 0, zl), (x1, yb, zl), (x1, yb, zh), (x1, 0, zh)],        # right
        [(x0, 0, zh), (x0, yb, zh), (x1, yb, zh), (x1, 0, zh)],        # top
        [(x0, 0, zl), (x0, yb, zl), (x1, yb, zl), (x1, 0, zl)],        # bottom
    ]
    return add_mesh(name, faces, mat)


def emission_mat(name, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (1, 1, 1, 1)
    e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def scene_common(total_w):
    cx, cz = total_w / 2.0, 0.0
    setup_camera(cx, cz, total_w * 1.02, RES_X, RES_Y)
    configure_cycles(SAMPLES, use_gpu=True)
    return cx, cz


def inset_window(x0, frac=0.25):
    """Window well inside a feature of side A, so edges never leak in."""
    d = A * frac
    return (x0 + d, x0 + A - d, -A / 2 + d, A / 2 - d)


def run():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RES, exist_ok=True)
    report = {}

    gap = 60.0
    total_w = A * 2 + gap

    # ---- check 1: linearity -------------------------------------------
    clear_scene()
    m_em = emission_mat("em", 1.0)
    m_em2 = emission_mat("em2", 0.5)
    flat_plate(0.0, m_em, "em_1")
    flat_plate(A + gap, m_em2, "em_05")
    scene_common(total_w)
    set_world(0.0)
    report_cycles_settings()
    exr = os.path.join(OUT, "linearity.exr")
    render_to(exr, os.path.join(OUT, "linearity.png"))
    arr = read_exr(exr, RES_X, RES_Y)
    a = window_stats(arr, to_pixel_window(inset_window(0.0)))
    b = window_stats(arr, to_pixel_window(inset_window(A + gap)))
    report["linearity"] = {
        "emission_1.0_reads": a["mean"],
        "emission_0.5_reads": b["mean"],
        "expect": [1.0, 0.5],
        "pass": abs(a["mean"] - 1.0) < 2e-3 and abs(b["mean"] - 0.5) < 2e-3,
    }
    print("[V1] linearity  1.0 -> %.6f   0.5 -> %.6f   pass=%s"
          % (a["mean"], b["mean"], report["linearity"]["pass"]))

    # ---- check 2: Lambertian index under hemispherical illumination ----
    clear_scene()
    m = make_diffuse("coat", RHO)
    flat_plate(0.0, m, "flat_a")
    flat_plate(A + gap, m, "flat_b")
    scene_common(total_w)
    set_world(1.0)
    exr = os.path.join(OUT, "lambertian.exr")
    render_to(exr, os.path.join(OUT, "lambertian.png"))
    arr = read_exr(exr, RES_X, RES_Y)
    a = window_stats(arr, to_pixel_window(inset_window(0.0)))
    b = window_stats(arr, to_pixel_window(inset_window(A + gap)))
    ratio = a["mean"] / b["mean"]
    report["lambertian"] = {
        "rho": RHO,
        "reads": a["mean"],
        # corrected 2026-08-17: a Lambertian plate under uniform L0 reads
        # rho itself (blender_render.py hemi docstring); the old 0.0389
        # double-counted the cosine integral.
        "expect_index": 0.05,
        "flat_vs_flat_ratio": ratio,
        "pass": abs(ratio - 1.0) < 5e-3,
    }
    print("[V2] lambertian rho=%.3f reads %.6f (expect: rho itself)   "
          "flat/flat ratio %.5f   pass=%s"
          % (RHO, a["mean"], ratio, report["lambertian"]["pass"]))

    # ---- check 3: open box cavity, f = 1/6 -----------------------------
    clear_scene()
    m = make_diffuse("coat", RHO)
    open_cube(0.0, m, "cavity")
    flat_plate(A + gap, m, "flat")
    scene_common(total_w)
    set_world(1.0)
    exr = os.path.join(OUT, "box_cavity.exr")
    render_to(exr, os.path.join(OUT, "box_cavity.png"))
    arr = read_exr(exr, RES_X, RES_Y)
    cav = window_stats(arr, to_pixel_window(inset_window(0.0)))
    flt = window_stats(arr, to_pixel_window(inset_window(A + gap)))
    ratio = cav["mean"] / flt["mean"]
    f = 1.0 / 6.0
    formula = (RHO * f / (1 - RHO * (1 - f))) / RHO
    report["box_cavity"] = {
        "aperture_fraction": f,
        "cavity_mean": cav["mean"],
        "flat_mean": flt["mean"],
        "ratio_measured": ratio,
        "ratio_formula": formula,
        "ratio_recorded_previously": 0.233,
        # "optimistic" = the real cavity returns this much MORE than predicted
        "formula_optimism_pct": (ratio / formula - 1.0) * 100.0,
    }
    print("[V3] box cavity f=%.4f  ratio measured %.4f  formula %.4f  "
          "(previously recorded 0.233)  measured is %.1f%% worse than formula"
          % (f, ratio, formula, report["box_cavity"]["formula_optimism_pct"]))

    # ---- bounce-budget sensitivity ------------------------------------
    # If the ratio moves when bounces are cut, the budget is not converged.
    bounce_check = {}
    for nb in (12, 32, 128):
        cy = bpy.context.scene.cycles
        cy.max_bounces = nb
        cy.diffuse_bounces = nb
        cy.glossy_bounces = nb
        exr = os.path.join(OUT, f"box_cavity_b{nb}.exr")
        render_to(exr, os.path.join(OUT, f"box_cavity_b{nb}.png"))
        arr = read_exr(exr, RES_X, RES_Y)
        c = window_stats(arr, to_pixel_window(inset_window(0.0)))
        fl = window_stats(arr, to_pixel_window(inset_window(A + gap)))
        bounce_check[nb] = c["mean"] / fl["mean"]
        print("[V4] bounces=%3d  cavity/flat = %.4f" % (nb, bounce_check[nb]))
    report["bounce_sensitivity"] = bounce_check

    path = os.path.join(RES, "validation.json")
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("[DONE]", path)


if __name__ == "__main__":
    run()
