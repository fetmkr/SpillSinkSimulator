"""
Phase 7: how wrong is the unpolarised assumption?

    <venv>/bin/python scripts/crosscheck_polarized.py

WHY THIS ONE, AND WHY NOW. Cycles cannot model polarization at all, so every
number in phases 1-6 assumes unpolarised light throughout. That assumption is
weakest exactly where this study lives: the scoring is the WORST case over
theta 0/+-20/+-40, and the worst case is almost always +-40. Grazing incidence
is where the s- and p-polarised Fresnel coefficients diverge most -- at 40
degrees on a dielectric of n = 1.5 they already differ by roughly a factor of
two, and a cavity compounds that over several bounces because each bounce
filters the beam further.

Every other open question adds something new. This one can invalidate what is
already published, so it goes first.

Mitsuba 3 has `*_polarized` variants on this machine and was cross-validated
against Cycles to 4 % on the same geometry with a Lambertian
(`FINDINGS_crossvalidation.md`). That gives a controlled way to ask the
question: measure the SAME scene in Mitsuba twice, once unpolarised and once
polarised, and read the difference. Cycles is not involved in the comparison at
all, so its lack of polarization support cannot bias it.

WHAT THE COATING HAS TO BE. A Lambertian does not polarize, so the honest test
needs a surface with a dielectric interface -- which is also what this project's
fitted coating is (a Fresnel-weighted mix over a diffuse body). Mitsuba's
`roughplastic` is that same physical picture built properly: a rough dielectric
boundary over a Lambertian substrate, with the Fresnel term handled internally
and, in a polarized variant, handled as a Mueller matrix. It is NOT identical to
the Cycles node graph, which is why this script never compares the two -- only
polarized against unpolarised, inside one renderer, with everything else held.

THE PRE-REGISTERED PREDICTION, before any render.

1. AT NORMAL INCIDENCE, NOTHING. s and p are degenerate at theta = 0, and a
   cavity entered head-on has no preferred plane. Expect under 1 %, which is
   also the Monte Carlo floor measured in check 1 of the cross-validation.

2. AT 40 DEGREES, A FEW PERCENT ON A SHALLOW STRUCTURE AND MORE ON A DEEP ONE.
   One bounce off a dielectric at 40 degrees polarizes the beam partially; the
   next bounce then sees a beam that is no longer unpolarised, and the error
   compounds. The honeycomb forces more bounces than the cone at grazing
   incidence, so I expect the honeycomb to show the larger discrepancy.
   Magnitude: 2-10 % for both.

3. THE RANKING SURVIVES. Whatever the shift, it should act in the same
   direction on both families, because both are the same coating at the same
   angles. If it does not -- if one family moves up and the other down -- then
   comparisons between families at grazing incidence are contingent on an
   assumption this project never stated, and every worst-case ranking needs a
   caveat.

If (1) fails the setup is wrong, not the physics: check it before reading
anything else.
"""

import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("MTS_OUT", "/tmp/mts_pol")

# the fitted coating, as close as two codes can be asked to agree:
# a rough dielectric boundary over a dark Lambertian body
IOR = 1.5
BODY = 0.00758          # MUSOU_BODY -- the diffuse substrate
ALPHA = 0.30            # the roughness the sweeps run at


def scene_dict(mi, ply, theta_deg, spp, res, face_w=60.0, face_h=60.0):
    th = math.radians(theta_deg)
    cx, cz = face_w / 2.0, 0.0
    dist = max(face_w, face_h) * 6.0
    eye = [cx, dist * math.cos(th), cz + dist * math.sin(th)]
    return {
        "type": "scene",
        "integrator": {"type": "path", "max_depth": 128},
        "sensor": {
            "type": "orthographic",
            "to_world": mi.ScalarTransform4f().look_at(
                origin=eye, target=[cx, 0.0, cz], up=[0, 0, 1]
            ) @ mi.ScalarTransform4f().scale([face_w / 2.0, face_h / 2.0, 1.0]),
            "sampler": {"type": "independent", "sample_count": spp},
            "film": {"type": "hdrfilm", "width": res, "height": res,
                     "pixel_format": "luminance",
                     "rfilter": {"type": "box"}},
        },
        "env": {"type": "constant", "radiance": 1.0},
        "panel": {
            "type": "ply", "filename": ply,
            "bsdf": {"type": "twosided", "material": {
                "type": "roughplastic",
                "distribution": "ggx",
                "alpha": ALPHA,
                "int_ior": IOR,
                "ext_ior": 1.0,
                "diffuse_reflectance": {"type": "rgb", "value": BODY},
            }},
        },
    }


def measure(mi, ply, theta, spp=256, res=160):
    import numpy as np
    img = mi.render(mi.load_dict(scene_dict(mi, ply, theta, spp, res)))
    a = np.array(img).squeeze()
    if a.ndim == 3:                      # polarized films carry Stokes planes
        a = a[..., 0]
    k = int(a.shape[0] * 0.12)
    return float(a[k:-k, k:-k].mean())


def run_variant(mi, variant, plys, thetas, spp):
    mi.set_variant(variant)
    out = {}
    for name, ply in plys.items():
        for th in thetas:
            out["%s@%+.0f" % (name, th)] = measure(mi, ply, th, spp=spp)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    import mitsuba as mi
    import geom3d as G3
    import geom_topo as GT
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from crosscheck_mitsuba import write_ply

    FACE, DEPTH = 60.0, 50.0
    builds = {
        "cone": G3.build_mesh(G3.Cone3DParams(
            face_w=FACE, face_h=FACE, depth=DEPTH, pitch=5.5, tip_radius=0.2,
            jitter=0.30, radial_seg=24, height_seg=12, depth_jitter=0.0,
            profile_power=1.0, margin_depths=2.0, backing=2.0, seed=23)),
        "comb": GT.build_mesh(GT.TopoParams(
            topology="comb", face_w=FACE, face_h=FACE, depth=DEPTH, pitch=6.5,
            wall_top=0.08, wall_bot=0.08, jitter=0.0, margin_depths=2.0,
            backing=2.0, seed=23)),
        "flat": ([(-FACE, 0.0, -FACE), (2 * FACE, 0.0, -FACE),
                  (2 * FACE, 0.0, FACE), (-FACE, 0.0, FACE)], [(3, 2, 1, 0)]),
    }
    plys = {}
    for name, (v, f) in builds.items():
        p = os.path.join(OUT, name + ".ply")
        write_ply(p, v, f)
        plys[name] = p

    THETAS = (0.0, 40.0)
    SPP = 512
    print("mitsuba %s" % mi.__version__)
    print("coating: roughplastic, ior %.2f, alpha %.2f, diffuse %.5f"
          % (IOR, ALPHA, BODY))

    unpol = run_variant(mi, "scalar_rgb", plys, THETAS, SPP)
    pol = run_variant(mi, "scalar_spectral_polarized", plys, THETAS, SPP)

    print("\n  %-14s %12s %12s %9s" % ("scene", "unpolarised", "polarised",
                                       "change"))
    rows = []
    for k in sorted(unpol):
        a, b = unpol[k], pol[k]
        d = (b - a) / a if a else float("nan")
        rows.append((k, a, b, d))
        print("  %-14s %11.6f%% %11.6f%% %+8.2f%%"
              % (k, 100 * a, 100 * b, 100 * d))

    print("\n  PREDICTION 1  theta 0 under 1 %%")
    for k, a, b, d in rows:
        if k.endswith("+0"):
            print("      %-12s %+6.2f%%   %s"
                  % (k, 100 * d, "held" if abs(d) < 0.01 else "FAILED"))
    print("  PREDICTION 2  theta 40 a few percent, comb larger than cone")
    g = {k.split("@")[0]: d for k, a, b, d in rows if k.endswith("+40")}
    for k in ("flat", "cone", "comb"):
        if k in g:
            print("      %-12s %+6.2f%%" % (k, 100 * g[k]))
    if "comb" in g and "cone" in g:
        print("      comb larger than cone: %s"
              % (abs(g["comb"]) > abs(g["cone"])))
        print("  PREDICTION 3  same direction for both: %s"
              % (g["comb"] * g["cone"] > 0))
    json.dump({"unpolarised": unpol, "polarized": pol},
              open(os.path.join(OUT, "polarized.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
