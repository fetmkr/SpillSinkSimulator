"""Head-on brightness WITHOUT pixels.

Head-on is the one axis that collapses with pixel size: 0.215 -> 1.200 mm/px
took it 0.1835 -> 0.0821 while smear held at 2.238 -> 2.227. It is a PEAK, and
a peak has nothing to cancel against when the pixel grows, unlike an area
average (total) or a ratio of two widths in one frame (smear). Resolving the
feature that makes the peak -- a 0.4 mm tip, a 0.08 mm honeycomb wall -- across
a whole panel costs 13 to 324 megapixels.

The third tracer has no pixels at all. It casts rays and follows them, so the
tip is resolved by construction. Today it was shown scale-invariant to 0.4 %
over a 1000x size range, its error falls as 1/sqrt(N) (measured ratios 0.585 /
0.564 / 0.563 against the ideal 0.548), and its converged rho_dh sits 0.07
sigma from Cycles. So it can arbitrate this axis.

WHAT IS COMPUTED, and the normalisation written out rather than assumed.
Every escaped ray carries a weight and a final direction. Collect the weight
leaving within a cone of half-angle A about the panel normal:

    W_cone = sum of weights with exit angle <= A

The radiance toward the normal is that weight per unit solid angle, and the
solid angle of the cone is  omega = 2*pi*(1 - cos A).

A flat Lambertian of the same reflectance rho, under the same incident power,
emits radiance  L_flat = rho / pi  per unit incident irradiance. So

    head_on = (W_cone / omega) / (rho / pi)

which is the same quantity the pixel rig estimates as panel peak over flat-plate
peak, and it does not contain a pixel anywhere.

PRE-REGISTERED:
  P1  the answer is stable as the cone A is narrowed from 20 to 5 degrees --
      if it is not, the estimator is dominated by the cone choice, not by the
      panel
  P2  it agrees with the pixel method at the FINE density (0.18881 at
      0.108 mm/px), not with the protocol one (0.18349 at 0.215)
  P3  it does not move with panel size, because a tracer has no window
"""
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from geom_floor import FloorParams, build_mesh   # noqa: E402
import raytrace_viz as RV                        # noqa: E402


def exit_dirs(res):
    """Final direction of every escaped ray, from the last two path points."""
    out = []
    for i, p in enumerate(res["paths"]):
        if not res["escaped"][i]:
            continue
        n = len(p)
        if n < 6 or n % 3:
            continue
        a = p[n - 6:n - 3]
        b = p[n - 3:n]
        d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]
        m = math.sqrt(sum(x * x for x in d))
        if m < 1e-12:
            continue
        out.append(([x / m for x in d], res["weights"][i]))
    return out


def head_on(v, f, face, theta, rho, n_rays, cone_deg=10.0, seed=23,
            max_bounces=24):
    r = RV.trace(v, f, face, face, theta_deg=theta, n_rays=n_rays,
                 max_bounces=max_bounces, rho=rho, seed=seed, mode="diffuse")
    ds = exit_dirs(r)
    if not ds:
        return None
    A = math.radians(cone_deg)
    omega = 2.0 * math.pi * (1.0 - math.cos(A))
    # the panel faces +y in this builder; escaping rays leave with d[1] > 0
    w_cone = sum(w for d, w in ds if d[1] > math.cos(A))
    per_ray = w_cone / float(n_rays)          # weight per incident ray
    return (per_ray / omega) / (rho / math.pi), len(ds), r["stats"]["rho_est"]


if __name__ == "__main__":
    fp = FloorParams(kind="pyramid", pitch=4.0, depth=22.0, tip_flat=0.4,
                     face_w=100.0, face_h=100.0, margin_depths=0.0,
                     backing=2.0)
    v, f = build_mesh(fp)
    print("간격 4 · 깊이 22 · 팁 0.4 · 램버시안 1%", flush=True)
    print("픽셀 방식이 낸 값: 규약밀도 0.18349 · 고운밀도 0.18881\n", flush=True)
    print("%-9s %-8s %-12s %-11s %s"
          % ("입사각", "원뿔도", "정면(광선)", "탈출광선", "rho_est"), flush=True)
    for theta in (0.0, -40.0):
        for cone in (20.0, 10.0, 5.0):
            r = head_on(v, f, 100.0, theta, 0.01, 30000, cone_deg=cone)
            if r is None:
                print("  없음", flush=True); continue
            print("%-9.0f %-8.0f %-12.5f %-11d %.6f"
                  % (theta, cone, r[0], r[1], r[2]), flush=True)
        print("", flush=True)
    print("@@DONE@@", flush=True)
