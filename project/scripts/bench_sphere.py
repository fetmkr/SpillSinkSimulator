"""An integrating sphere: the one cavity whose answer is known in closed form.

    python3 scripts/bench_sphere.py --mesh          # write the meshes
    <mts>/bin/python scripts/bench_sphere.py --mts  # measure in Mitsuba
    Blender --background --python scripts/bench_sphere.py -- --blender

WHY. Cycles and Mitsuba disagree about a honeycomb by -10 % at normal incidence
and +44 % at 40 degrees, on an identical mesh, through matched measurement
windows, with both codes reading a flat Lambertian correctly at every angle.
Comparing them to each other cannot say which is right. This compares both to
ARITHMETIC.

THE BENCHMARK. A sphere of Lambertian reflectance rho with a port of fractional
area f. Light entering the port is scattered, a fraction f of each diffuse
bounce finds the port again, and the rest bounces on:

    escape  =  rho f  +  rho(1-f) rho f  +  ...  =  rho f / (1 - rho (1 - f))

This is the standard integrating-sphere multiplier, it is exact for a Lambertian
sphere, and it is the benchmark stray-light practice uses precisely because it
has many bounces and a closed form. `hemi_view` measures the radiance leaving
the port under uniform illumination, which by Helmholtz reciprocity is that
same quantity.

WHAT IT SEPARATES. The formula's bounce count goes as 1/(1 - rho(1-f)), so it is
tunable: at rho = 0.5 a photon leaves after a couple of bounces and truncation
cannot matter, while at rho = 0.98 with f = 0.02 the mean is near 25 bounces and
a renderer that stops early must read LOW. Running the sweep in rho therefore
separates the two candidate faults:

    a truncation fault shows as agreement at low rho and a growing shortfall as
    rho rises, in whichever code truncates sooner;

    an intersection or sampling fault shows as a constant fractional offset
    across rho, because it is a geometric mis-hit and does not care how much
    energy the ray still carries.

PREDICTION, written before running. Both codes will match the formula to within
a few percent at rho <= 0.5. At rho = 0.98 both will read LOW, because both cap
at 128 bounces and the tail there is long, and Mitsuba will fall further because
its `max_depth` counts the camera vertex while Cycles' `max_bounces` counts only
surface events -- so nominally equal limits are not equal. If instead the two
disagree at LOW rho, where truncation cannot reach, then the fault is geometric
and the honeycomb disagreement is not about bounce limits at all.
"""

import sys
import os
import math
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/tmp/bench_sphere"

R = 30.0                 # sphere radius, mm
PORT_HALF_ANGLE = 8.0    # degrees; f = sin^2(half angle) / 2 ... see below
RHOS = (0.1, 0.3, 0.5, 0.7, 0.9, 0.98)
NU, NV = 192, 96         # sphere tessellation


def port_fraction(half_deg):
    """Fractional area of a spherical cap of half-angle `half_deg`.

    cap area = 2 pi R^2 (1 - cos a);  sphere area = 4 pi R^2
    """
    a = math.radians(half_deg)
    return 0.5 * (1.0 - math.cos(a))


def theory(rho, f):
    return rho * f / (1.0 - rho * (1.0 - f))


def build_sphere(radius=R, half_deg=PORT_HALF_ANGLE, nu=NU, nv=NV):
    """A sphere with a circular port at the +Y pole, as (verts, quads).

    The port faces +Y so the same top-down camera and uniform environment the
    rest of this project uses can look straight into it.
    """
    a = math.radians(half_deg)
    verts, faces = [], []
    # THE FAR POLE IS A TRIANGLE FAN, NOT A RING OF DEGENERATE QUADS. The first
    # version ran the rings all the way to pv = pi, where all `nu` vertices
    # collapse onto the same point and every quad there has zero area. A camera
    # ray down the port axis lands exactly on that patch, misses it, and leaves
    # the sphere: the inner 40 % of a 4 degree port read 0.000000, and the
    # benchmark blamed the renderer for a hole this file had put in the mesh.
    # The error scaled with how much of the view the bad patch covered -- -41.7 %
    # at a 4 degree port, -0.5 % at 30 degrees -- which is what a mesh defect
    # looks like and what a transport fault does not.
    rings = nv - 1                      # last ring stops short of the pole
    for j in range(rings + 1):
        pv = a + (math.pi - a) * j / nv
        for i in range(nu):
            pu = 2.0 * math.pi * i / nu
            verts.append((radius * math.sin(pv) * math.cos(pu),
                          radius * math.cos(pv),
                          radius * math.sin(pv) * math.sin(pu)))
    pole = len(verts)
    verts.append((0.0, -radius, 0.0))
    for j in range(rings):
        for i in range(nu):
            a0 = j * nu + i
            b0 = j * nu + (i + 1) % nu
            c0 = (j + 1) * nu + (i + 1) % nu
            d0 = (j + 1) * nu + i
            faces.append((a0, b0, c0, d0))
    last = rings * nu
    for i in range(nu):
        faces.append((last + i, last + (i + 1) % nu, pole))
    return verts, faces


def port_radius(radius=R, half_deg=PORT_HALF_ANGLE):
    return radius * math.sin(math.radians(half_deg))


# --------------------------------------------------------------------------

def run_mitsuba(spp=1024, res=128, max_depth=1024):
    import numpy as np
    import mitsuba as mi
    mi.set_variant("scalar_rgb")
    from crosscheck_mitsuba import write_ply
    os.makedirs(OUT, exist_ok=True)
    v, f = build_sphere()
    ply = os.path.join(OUT, "sphere.ply")
    write_ply(ply, v, f)
    rp = port_radius()
    T = mi.ScalarTransform4f
    out = {}
    for rho in RHOS:
        sc = {
            "type": "scene",
            "integrator": {"type": "path", "max_depth": max_depth},
            "sensor": {
                "type": "orthographic",
                # framed on the port and nothing else
                "to_world": T().look_at(origin=[0, 4 * R, 0],
                                        target=[0, 0, 0], up=[0, 0, 1])
                @ T().scale([rp, rp, 1.0]),
                "sampler": {"type": "independent", "sample_count": spp},
                "film": {"type": "hdrfilm", "width": res, "height": res,
                         "pixel_format": "luminance",
                         "rfilter": {"type": "box"}},
            },
            "env": {"type": "constant", "radiance": 1.0},
            "sphere": {"type": "ply", "filename": ply,
                       "bsdf": {"type": "twosided", "material": {
                           "type": "diffuse",
                           "reflectance": {"type": "rgb", "value": rho}}}},
        }
        a = np.array(mi.render(mi.load_dict(sc))).squeeze()
        # average only inside the port disc, which is inscribed in the frame
        n = a.shape[0]
        yy, xx = np.mgrid[0:n, 0:n]
        r2 = ((xx - (n - 1) / 2.0) ** 2 + (yy - (n - 1) / 2.0) ** 2)
        mask = r2 <= (0.7 * n / 2.0) ** 2      # inner 70 %, away from the rim
        out[rho] = float(a[mask].mean())
    return out


def run_cycles(spp=1024, max_depth=1024):
    import bpy
    import blender_render as BR
    import numpy as np
    os.makedirs(OUT, exist_ok=True)
    v, f = build_sphere()
    rp = port_radius()
    out = {}
    for rho in RHOS:
        BR.clear_scene()
        mesh = bpy.data.meshes.new("sphere")
        mesh.from_pydata([tuple(q) for q in v], [], [tuple(q) for q in f])
        mesh.update()
        ob = bpy.data.objects.new("sphere", mesh)
        bpy.context.collection.objects.link(ob)
        m = BR.make_diffuse("bench", rho)
        ob.data.materials.append(m)

        cy = BR.configure_cycles(spp, True)
        cy.max_bounces = max_depth
        cy.diffuse_bounces = max_depth
        cy.glossy_bounces = max_depth
        cy.transmission_bounces = max_depth
        BR.set_world(1.0)
        res = 128
        # elev_deg is measured FROM THE PANEL NORMAL (+Y), so 0 is the
        # top-down view down the port axis and 90 looks at the sphere edge-on
        # from +Z. Passing 90 photographed the OUTSIDE of the shell, which under
        # a uniform environment reads exactly rho -- 0.100000, 0.300000,
        # 0.500000 straight down the column, a result so clean it was obviously
        # not a cavity measurement at all.
        BR.setup_camera(0.0, 0.0, 2.0 * rp, res, res, elev_deg=0.0,
                        dist=4 * R)
        exr = os.path.join(OUT, "sphere_%03d.exr" % round(rho * 100))
        BR.render_to(exr, exr.replace(".exr", ".png"))
        arr = BR.read_exr(exr, res, res).mean(axis=2)
        n = arr.shape[0]
        yy, xx = np.mgrid[0:n, 0:n]
        r2 = ((xx - (n - 1) / 2.0) ** 2 + (yy - (n - 1) / 2.0) ** 2)
        mask = r2 <= (0.7 * n / 2.0) ** 2
        out[rho] = float(arr[mask].mean())
    return out


def report(name, got):
    f = port_fraction(PORT_HALF_ANGLE)
    print("\n  %s   port fraction f = %.5f" % (name, f))
    print("  %6s %14s %14s %10s %10s"
          % ("rho", "theory", name, "error", "mean bounces"))
    for rho in RHOS:
        t = theory(rho, f)
        g = got.get(rho)
        nb = 1.0 / (1.0 - rho * (1.0 - f))
        print("  %6.2f %14.6f %14.6f %+9.2f%% %10.1f"
              % (rho, t, g, 100 * (g - t) / t, nb))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv \
        else sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    if "--mts" in argv:
        got = run_mitsuba()
        json.dump({str(k): v for k, v in got.items()},
                  open(os.path.join(OUT, "mitsuba.json"), "w"))
        report("Mitsuba", got)
    elif "--blender" in argv:
        # NOT `--cycles`: Blender parses its own argv first and reports
        # "ambiguous option: --cycles could match --cycles-print-stats,
        # --cycles-device", then exits before the script runs.
        got = run_cycles()
        json.dump({str(k): v for k, v in got.items()},
                  open(os.path.join(OUT, "cycles.json"), "w"))
        report("Cycles", got)
    else:
        f = port_fraction(PORT_HALF_ANGLE)
        print("port fraction %.6f" % f)
        for rho in RHOS:
            print("  rho %.2f -> theory %.6f" % (rho, theory(rho, f)))
