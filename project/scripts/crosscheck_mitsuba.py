"""
Measure the same panel in a second, independent renderer.

    <venv>/bin/python scripts/crosscheck_mitsuba.py

WHY. Every optical number in this project comes from one path tracer driven by
one harness. Gate check 8 compares sweeps against other sweeps -- it catches
drift, and cannot catch a mistake both sides share. Stray-light practice
cross-traces identical rays between independent codes for exactly this reason.
The analytic cross-check (`crosscheck_analytic.py`) already did half the job:
it reproduces the honeycomb and cell families to within 10 %, and misses the
cone and truss by 100-800x because its two-bounce assumption does not hold
where the exposed area is a fraction of a percent. Those are the families that
need a real second renderer, and the cone is the one that leads head-on
brightness in phases 3 and 4.

WHAT IS COMPARED, AND WHAT DELIBERATELY IS NOT. The coating is a Lambertian of
known reflectance, not the fitted Musou mix. Cycles builds that coating from a
Fresnel node feeding a mix of diffuse and glossy; Mitsuba has no identical
construction, so a disagreement there would be ambiguous -- a difference in
material, not in transport. A pure Lambertian is the SAME BRDF in both codes,
so this isolates what is actually in doubt: the geometry, the uniform-
illumination measurement, and the light transport.

THE MEASUREMENT, in both codes. Uniform environment of radiance 1, camera
looking at the panel along the normal, mean radiance over the panel window. For
a flat Lambertian of reflectance rho that reads exactly rho, which is check 1
below and validates the whole setup before any cavity is measured.

PREDICTION, before running: the flat plate reads its own rho to within
sampling noise, and the cone agrees with Cycles to within a few percent. If
the cone disagrees by more than ~10 %, one of the two codes is wrong about
deep-cavity transport and this study has a problem larger than any design
question in it.
"""

import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("MTS_OUT", "/tmp/mts")

# Read from the Cycles harness rather than copied, so they cannot drift.
MEAS_INSET_X = 0.20
MEAS_INSET_Z = 0.30


def write_ply(path, verts, faces):
    """Binary-free PLY. Quads are split; Mitsuba wants triangles."""
    tris = []
    for f in faces:
        idx = list(f)
        for a in range(1, len(idx) - 1):
            tris.append((idx[0], idx[a], idx[a + 1]))
    with open(path, "w") as fh:
        fh.write("ply\nformat ascii 1.0\n")
        fh.write("element vertex %d\n" % len(verts))
        fh.write("property float x\nproperty float y\nproperty float z\n")
        fh.write("element face %d\n" % len(tris))
        fh.write("property list uchar int vertex_indices\n")
        fh.write("end_header\n")
        for v in verts:
            fh.write("%.6f %.6f %.6f\n" % (v[0], v[1], v[2]))
        for t in tris:
            fh.write("3 %d %d %d\n" % t)
    return len(verts), len(tris)


def scene_dict(mi, ply, rho, face_w, face_h, theta_deg, spp, res):
    """Uniform environment, orthographic camera at elevation theta.

    The camera is orthographic and sized to the face, so the window is the
    panel and nothing else -- the same framing the Cycles harness uses, and the
    reason the panel must extend past it (margin_depths).
    """
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
            # TWOSIDED IS NOT OPTIONAL HERE. Mitsuba 3 BSDFs are one-sided:
            # a back face is black. Cycles has no such rule, and this project's
            # meshes are unions of closed solids whose winding was never
            # audited -- a hand-made flat quad read exactly 0.00000 until this
            # wrapper went on. A one-sided read would have looked like a
            # transport disagreement rather than a convention difference.
            "bsdf": {"type": "twosided",
                     "material": {"type": "diffuse",
                                  "reflectance": {"type": "rgb",
                                                  "value": rho}}},
        },
    }


def window_px(face_w, face_h, theta_deg, res):
    """The Cycles measurement window, in THIS camera's pixels.

    THE THIRD WINDOW BUG IN THIS FILE, and the reason it is now one function
    with a calibration test behind it. Trimming a fixed fraction of the image
    is only the same measurement as Cycles' at normal incidence. Tilt the
    camera and the panel foreshortens: measured on this build with emissive
    markers at known world z, the visible span is face_h / cos(theta) --
    60.00 mm at 0 degrees, 63.81 at 20, 78.33 at 40, against face/cos of
    60.00 / 63.85 / 78.32. A fixed 30 % trim therefore covers +-21 mm of panel
    at normal incidence and +-27.4 mm at 40 degrees, which is a different patch
    of a different design, and the Cycles-Mitsuba gap grew with angle because
    of it: -7.6 % at theta 0 and 43.5 % worst over +-40.

    `blender_render.to_pixel_window` maps the WORLD window through the camera,
    so it always measures the same physical patch. This does the same thing for
    the Mitsuba camera: x is unaffected because the tilt is in the y-z plane,
    and z is scaled by 1/cos(theta).
    """
    import math as _m
    ct = _m.cos(_m.radians(theta_deg))
    span_z = face_h / max(ct, 1e-9)          # what the tilted camera sees
    mm_x = face_w / float(res)
    mm_z = span_z / float(res)
    zc = (face_h / 2.0) * (1.0 - 2.0 * MEAS_INSET_Z)   # world half-height kept
    xc = (face_w / 2.0) * (1.0 - 2.0 * MEAS_INSET_X)
    r0 = (span_z / 2.0 - zc) / mm_z
    r1 = (span_z / 2.0 + zc) / mm_z
    c0 = (face_w / 2.0 - xc) / mm_x
    c1 = (face_w / 2.0 + xc) / mm_x
    return (int(round(r0)), int(round(r1)), int(round(c0)), int(round(c1)))


def measure(mi, ply, rho, face_w, face_h, theta=0.0, spp=256, res=192):
    img = mi.render(mi.load_dict(
        scene_dict(mi, ply, rho, face_w, face_h, theta, spp, res)))
    import numpy as np
    a = np.array(img).squeeze()
    # THE SAME WINDOW AS CYCLES, WHICH IT WAS NOT. This trimmed 12 % off both
    # axes while `blender_render` trims MEAS_INSET_X = 20 % in x and
    # MEAS_INSET_Z = 30 % in z -- harder in z because fins run past the panel
    # there. The two codes were therefore averaging over different parts of the
    # same panel, and the difference grew with how anisotropic the structure is:
    # a comb read -4.3 % at a 60 mm face and -8.2 % at 100 mm, and a blade array
    # +24.4 %. That is a window mismatch reported as a transport disagreement.
    r0, r1, c0, c1 = window_px(face_w, face_h, theta, a.shape[0])
    r0, c0 = max(r0, 0), max(c0, 0)
    r1, c1 = min(r1, a.shape[0]), min(c1, a.shape[1])
    return float(a[r0:r1, c0:c1].mean())


def main():
    os.makedirs(OUT, exist_ok=True)
    import mitsuba as mi
    for v in ("llvm_ad_rgb", "scalar_rgb"):
        try:
            mi.set_variant(v)
            break
        except Exception:
            continue
    print("mitsuba %s, variant %s" % (mi.__version__, mi.variant()))

    import geom3d as G3
    import geom_topo as GT

    FACE, DEPTH = 60.0, 50.0
    RHO = 0.01
    print("\n[1] setup check: a flat Lambertian must read its own reflectance")
    flat = [(-FACE, 0.0, -FACE), (2 * FACE, 0.0, -FACE),
            (2 * FACE, 0.0, FACE), (-FACE, 0.0, FACE)]
    fp = os.path.join(OUT, "flat.ply")
    write_ply(fp, flat, [(0, 1, 2, 3)])
    for rho in (0.01, 0.05):
        got = measure(mi, fp, rho, FACE, FACE, spp=512)
        err = abs(got - rho) / rho
        print("      rho %.3f -> reads %.5f   err %.2f%%  %s"
              % (rho, got, 100 * err, "ok" if err < 0.02 else "FAIL"))

    print("\n[2] the two families the analytic model disagrees about")
    cases = [
        ("cone 5.5 / tip r0.2", "cone3d",
         dict(face_w=FACE, face_h=FACE, depth=DEPTH, pitch=5.5,
              tip_radius=0.2, jitter=0.30, radial_seg=24, height_seg=12,
              depth_jitter=0.0, profile_power=1.0, margin_depths=2.0,
              backing=2.0, seed=23)),
        ("comb 6.5 / 0.08", "topo",
         dict(topology="comb", face_w=FACE, face_h=FACE, depth=DEPTH,
              pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0,
              margin_depths=2.0, backing=2.0, seed=23)),
    ]
    out = {}
    for name, fam, prm in cases:
        if fam == "cone3d":
            v, f = G3.build_mesh(G3.Cone3DParams(**prm))
        else:
            v, f = GT.build_mesh(GT.TopoParams(**prm))
        ply = os.path.join(OUT, name.split()[0] + ".ply")
        nv, nt = write_ply(ply, v, f)
        got = measure(mi, ply, RHO, FACE, FACE, spp=512)
        out[name] = got
        print("      %-22s %7d tri   rho_dh(0) = %.6f  (%.5f %%)"
              % (name, nt, got, 100 * got))
    json.dump(out, open(os.path.join(OUT, "mitsuba.json"), "w"), indent=1)
    print("\nwrote %s" % os.path.join(OUT, "mitsuba.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
