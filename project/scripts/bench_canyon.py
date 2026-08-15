"""Single scattering on thin walls, against a closed form.

    python3 scripts/bench_canyon.py                        # the analytic curve
    <mts>/bin/python scripts/bench_canyon.py --mts
    Blender --background --python scripts/bench_canyon.py -- --blender

WHY. `FINDINGS_renderer_disagreement.md` narrowed the Cycles/Mitsuba gap to the
SINGLE-SCATTERING term on thin-wall lattices: capped at one bounce the two codes
already differ by -9.5 % at normal incidence and +12.8 % at 40 degrees, while an
integrating sphere at up to 40 bounces is reproduced by both to under 1.3 %.
One bounce has no transport chain, so what is left is the cosine-weighted sky
visibility at each surface point. Neither the sphere nor a flat plate can say
which code computes that correctly on a 0.08 mm wall, because neither has one.

THE BENCHMARK. An infinitely long canyon: two parallel vertical walls of
thickness t and height h, separated by a gap w, with a floor between them. For a
point on the floor a distance x from the left wall, the sky is visible between
the two top edges, and for infinite length the cosine-weighted visible fraction
is exact:

    F(x) = ( sin(theta_L) + sin(theta_R) ) / 2

    sin(theta_L) = x / sqrt(x^2 + h^2)
    sin(theta_R) = (w - x) / sqrt((w - x)^2 + h^2)

theta measured from the floor normal to each top edge. This is the standard
two-dimensional differential-element-to-strip view factor, F = (sin a - sin b)/2
between two directions, applied to the strip of sky between the edges. Under a
uniform environment of radiance L a Lambertian floor of reflectance rho then
leaves, after exactly one bounce,

    L_out(x) = rho * L * F(x)

with no free parameters. The wall TOPS are a second, trivial check in the same
frame: an upward-facing surface with unobstructed sky has F = 1 and must read
exactly rho.

WHAT IT SEPARATES. F(x) does not contain the wall thickness. An opaque wall
occludes the sky whether it is 0.08 mm or 2 mm thick, so any thickness
dependence in a measured profile is the renderer's, and this is precisely the
dependence the honeycomb showed (+44.4 % at a 0.08 mm wall falling to +10.9 % at
2 mm). Running the same canyon at several thicknesses therefore identifies which
code moves away from the closed form as the wall thins -- and that code is the
one whose thin-wall numbers cannot be used.

PREDICTION, written before running. Both codes will match F(x) at t = 2 mm.
As t falls to 0.08 mm one of them will bend away from it, and on the evidence so
far I expect that to be MITSUBA reading high: it is the code that reads high on
every wall-built family (+44 % on comb, +48 % on square, +60 % on blades at 40
degrees) while agreeing with Cycles on the cone, the one family with no thin
feature. I hold this loosely -- the sphere showed Mitsuba is the marginally less
accurate of the two on a smooth cavity (1.22 % against 0.27 %), which is a weak
prior in the same direction and nothing more. If instead BOTH bend away, the
fault is in the shared mesh -- a union of interpenetrating solids with surfaces
buried inside material -- and not in either renderer.
"""

import sys
import os
import math
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = "/tmp/bench_canyon"

W = 6.5           # gap between the walls, mm -- the comb's pitch
H = 20.0          # wall height, mm
LEN = 600.0       # wall length; the closed form is the infinite-length limit
THICK = (0.08, 0.5, 2.0)
RHO = 0.5
RES = 512         # pixels across the framed strip
FRAME = 12.0      # mm of x captured, centred on the gap
SPP = 4096


def F(x, w=W, h=H):
    """Cosine-weighted sky fraction on the canyon floor, x from the left wall."""
    sl = x / math.sqrt(x * x + h * h)
    sr = (w - x) / math.sqrt((w - x) ** 2 + h * h)
    return 0.5 * (sl + sr)


def build(t, w=W, h=H, ln=LEN):
    """Two thin walls and a floor between them, as (verts, quads).

    The floor spans the gap only, so nothing outside the canyon is in frame and
    the profile across the gap is the whole measurement.
    """
    verts, faces = [], []

    def box(x0, x1, y0, y1, z0, z1):
        b = len(verts)
        verts.extend([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1),
                      (x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)])
        faces.extend([(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4),
                      (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2),
                      (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)])

    hz = ln / 2.0
    box(-t, 0.0, -h, 0.0, -hz, hz)            # left wall
    box(w, w + t, -h, 0.0, -hz, hz)           # right wall
    # The floor runs UNDER the walls, not merely up to them. Ending it at
    # x = 0 and x = w left the wall boxes sharing a bare edge with the slab,
    # which is a crack a ray can find; running it wider makes the joint an
    # overlap instead of a seam and removes the question from the benchmark.
    box(-t - 5.0, w + t + 5.0, -h - 2.0, -h, -hz, hz)
    return verts, faces


def profile_from(arr, frame=FRAME, res=RES):
    """Collapse the image to a profile across x, and the world x of each column.

    Both renderers are framed on the same strip; the image may be mirrored in
    x, which is detected and undone by the caller against the analytic curve.
    """
    import numpy as np
    prof = np.asarray(arr).mean(axis=0)
    xs = (np.arange(res) + 0.5) / res * frame - (frame - W) / 2.0
    return xs, prof


def run_mitsuba():
    import numpy as np
    import mitsuba as mi
    mi.set_variant("scalar_rgb")
    from crosscheck_mitsuba import write_ply
    os.makedirs(OUT, exist_ok=True)
    T = mi.ScalarTransform4f
    out = {}
    for t in THICK:
        v, f = build(t)
        ply = os.path.join(OUT, "canyon_%s.ply" % t)
        write_ply(ply, v, f)
        sc = {
            "type": "scene",
            # max_depth 2 = one surface bounce (Mitsuba counts the camera
            # vertex); the closed form is the single-scattering answer.
            "integrator": {"type": "path", "max_depth": 2},
            "sensor": {
                "type": "orthographic",
                "to_world": T().look_at(origin=[W / 2.0, 200.0, 0.0],
                                        target=[W / 2.0, 0.0, 0.0],
                                        up=[0, 0, 1])
                @ T().scale([FRAME / 2.0, FRAME / 2.0, 1.0]),
                "sampler": {"type": "independent", "sample_count": SPP},
                "film": {"type": "hdrfilm", "width": RES, "height": 64,
                         "pixel_format": "luminance",
                         "rfilter": {"type": "box"}},
            },
            "env": {"type": "constant", "radiance": 1.0},
            "canyon": {"type": "ply", "filename": ply,
                       "bsdf": {"type": "twosided", "material": {
                           "type": "diffuse",
                           "reflectance": {"type": "rgb", "value": RHO}}}},
        }
        a = np.array(mi.render(mi.load_dict(sc))).squeeze()
        out[str(t)] = a.mean(axis=0).tolist()
    return out


def run_cycles():
    import bpy
    import numpy as np
    import blender_render as BR
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for t in THICK:
        v, f = build(t)
        BR.clear_scene()
        mesh = bpy.data.meshes.new("canyon")
        mesh.from_pydata([tuple(q) for q in v], [], [tuple(q) for q in f])
        mesh.update()
        ob = bpy.data.objects.new("canyon", mesh)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(BR.make_diffuse("lam", RHO))
        cy = BR.configure_cycles(SPP, True)
        # ZERO, NOT ONE. Blender's `max_bounces` counts INDIRECT bounces on top
        # of the direct hit, so `max_bounces = 0` is single scattering and
        # `= 1` already includes the double-scattering term -- measured here as
        # a uniform +16.8 % against the closed form, with `= 0` landing on it to
        # +0.04 %. Mitsuba's `max_depth` counts path vertices including the
        # camera, so single scattering there is `max_depth = 2`. The correct
        # correspondence is therefore
        #
        #     Cycles max_bounces = N   <->   Mitsuba max_depth = N + 2
        #
        # and an earlier bounce sweep in this project used N + 1, giving Mitsuba
        # one bounce fewer than Cycles at every row of the table.
        for k in ("max_bounces", "diffuse_bounces", "glossy_bounces",
                  "transmission_bounces"):
            setattr(cy, k, 0)
        BR.set_world(1.0)
        BR.setup_camera(W / 2.0, 0.0, FRAME, RES, 64, elev_deg=0.0,
                        dist=200.0)
        exr = os.path.join(OUT, "canyon_%s.exr" % t)
        BR.render_to(exr, exr.replace(".exr", ".png"))
        a = BR.read_exr(exr, RES, 64).mean(axis=2)
        out[str(t)] = a.mean(axis=0).tolist()
    return out


def report(name, data):
    import numpy as np
    xs = (np.arange(RES) + 0.5) / RES * FRAME - (FRAME - W) / 2.0
    inside = (xs > 0.35) & (xs < W - 0.35)      # away from the wall edges
    print("\n  %s   canyon w=%.1f h=%.1f, rho=%.2f, ONE bounce" % (name, W, H,
                                                                   RHO))
    print("  %8s %12s %12s %10s %12s"
          % ("wall t", "floor rms err", "worst err", "top reads", "vs rho"))
    for t in THICK:
        p = np.array(data[str(t)])
        # the image may be mirrored in x; pick the orientation that fits
        best = None
        for q in (p, p[::-1]):
            th = np.array([RHO * F(x) for x in xs])
            e = (q[inside] - th[inside]) / th[inside]
            r = float(np.sqrt((e ** 2).mean()))
            if best is None or r < best[0]:
                best = (r, float(np.abs(e).max()), q)
        rms, worst, q = best
        tops = q[(xs < -0.6) | (xs > W + 0.6)]
        top = float(tops.mean()) if tops.size else float("nan")
        print("  %8.2f %11.2f%% %11.2f%% %10.5f %11.2f%%"
              % (t, 100 * rms, 100 * worst, top, 100 * (top - RHO) / RHO))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv \
        else sys.argv[1:]
    os.makedirs(OUT, exist_ok=True)
    if "--mts" in argv:
        d = run_mitsuba()
        json.dump(d, open(os.path.join(OUT, "mitsuba.json"), "w"))
        report("Mitsuba", d)
    elif "--blender" in argv:
        d = run_cycles()
        json.dump(d, open(os.path.join(OUT, "cycles.json"), "w"))
        report("Cycles", d)
    else:
        print("closed form, canyon w=%.2f h=%.2f, rho=%.2f" % (W, H, RHO))
        for x in (0.5, 1.5, 3.25, 5.0, 6.0):
            print("   x=%5.2f  F=%.6f  L_out=%.6f" % (x, F(x), RHO * F(x)))
