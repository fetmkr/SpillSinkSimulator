"""Different shapes, one exact answer: convex Lambertian bodies must read rho.

    Blender --background --factory-startup --python scripts/validate_equal_radiance.py

THE INVARIANT. Under a uniform environment of radiance L, a Lambertian surface
of reflectance rho leaves radiance rho * L in EVERY direction, from every point
whose sky is unobstructed. A CONVEX body obstructs its own sky nowhere, so a
camera looking at any convex Lambertian shape -- a plate at any tilt, a sphere,
a single pyramid, a single cone -- must read exactly rho across the whole
silhouette. Shape drops out entirely. Concave panels differ from rho only
through self-occlusion and interreflection, which is the entire signal this
project measures; this test proves the harness adds nothing else.

WHAT IT EXERCISES that the flat-plate check does not: normals and winding on
curved and faceted builders, shading over many orientations at once, and the
camera/env pipeline on arbitrary meshes. The winding defect this project just
recovered from was invisible to diffuse light, so this test would NOT have
caught it (that is what the specular baseline is for) -- but any error that
touches diffuse shading, normal length, or double-counting of faces lands
here as a deviation from rho with no free parameters.

The camera window is placed INSIDE each shape's silhouette, so every pixel is
the shape and no background enters the mean. PASS is 1 % -- the flat plate
reads to 0.5 % at 512 spp, and nothing here is allowed to be worse than the
plate by more than sampling noise.
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RHO = 0.5
SPP = 512
RES = 192
OUT = "/tmp/equal_radiance"


def plate(tilt_deg, size=200.0):
    t = math.radians(tilt_deg)
    c, s = math.cos(t), math.sin(t)
    v = [(-size, 0.0, -size), (size, 0.0, -size),
         (size, 0.0, size), (-size, 0.0, size)]
    v = [(x, y * c - z * s, y * s + z * c) for x, y, z in v]
    return v, [(0, 1, 2, 3)]


def sphere(r=60.0, nu=96, nv=48):
    v, f = [], []
    for j in range(nv + 1):
        pv = math.pi * j / nv
        for i in range(nu):
            pu = 2 * math.pi * i / nu
            v.append((r * math.sin(pv) * math.cos(pu),
                      r * math.cos(pv),
                      r * math.sin(pv) * math.sin(pu)))
    for j in range(nv):
        for i in range(nu):
            a = j * nu + i
            b = j * nu + (i + 1) % nu
            c = (j + 1) * nu + (i + 1) % nu
            d = (j + 1) * nu + i
            f.append((a, b, c, d))
    return v, f


def single_pyramid(base=120.0, h=60.0):
    b = base / 2.0
    v = [(-b, 0.0, -b), (b, 0.0, -b), (b, 0.0, b), (-b, 0.0, b),
         (0.0, h, 0.0)]
    f = [(k, (k + 1) % 4, 4) for k in range(4)] + [(3, 2, 1, 0)]
    return v, f


def single_cone(r=70.0, h=60.0, n=96):
    v = [(r * math.cos(2 * math.pi * i / n), 0.0,
          r * math.sin(2 * math.pi * i / n)) for i in range(n)]
    v += [(0.0, h, 0.0), (0.0, 0.0, 0.0)]
    f = [(i, (i + 1) % n, n) for i in range(n)]          # side
    f += [((i + 1) % n, i, n + 1) for i in range(n)]     # base
    return v, f


CASES = [
    ("plate 0 deg", plate(0.0), 60.0),
    ("plate 40 deg", plate(40.0), 60.0),
    ("sphere", sphere(), 55.0),
    ("single pyramid", single_pyramid(), 50.0),
    ("single cone", single_cone(), 40.0),
]


def main():
    import bpy
    import blender_render as BR
    os.makedirs(OUT, exist_ok=True)
    print("=" * 68)
    print("EQUAL RADIANCE: convex Lambertian shapes must all read rho = %.2f"
          % RHO)
    print("=" * 68)
    fails = 0
    for name, (v, f), window in CASES:
        BR.clear_scene()
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(q) for q in v], [], [tuple(q) for q in f])
        mesh.update()
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(BR.make_diffuse("lam", RHO))
        BR.configure_cycles(SPP, True)
        BR.set_world(1.0)
        # window strictly inside the silhouette, seen from above
        BR.setup_camera(0.0, 0.0, window, RES, RES, elev_deg=0.0, dist=500.0)
        exr = os.path.join(OUT, name.replace(" ", "_") + ".exr")
        BR.render_to(exr, exr.replace(".exr", ".png"))
        a = BR.read_exr(exr, RES, RES).mean(axis=2)
        got = float(a.mean())
        err = (got - RHO) / RHO
        ok = abs(err) < 0.01
        fails += (not ok)
        print("  %-5s %-16s mean %.5f   err %+6.2f %%"
              % ("ok" if ok else "FAIL", name, got, 100 * err))
    print("-" * 68)
    print("  %d failed -- shape must not matter, and it %s"
          % (fails, "does not" if fails == 0 else "DOES"))
    return fails


if __name__ == "__main__":
    sys.exit(min(main(), 120))
