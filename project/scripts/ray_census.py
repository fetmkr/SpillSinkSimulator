"""
Count what actually happens to a ray inside each structure.

    python3 scripts/ray_census.py

Material-independent. This traces specular ray paths through the geometry and
records, per design:

    - how many times a ray bounces before it leaves
    - the incidence angle at every one of those bounces
    - how far the exit point is from the entry point

None of that depends on the coating, which matters right now because the two
material models disagree by 41x on the cone and neither is validated. Bounce
counts and bounce angles are geometry, and they are the thing that decides how
badly a coating's Fresnel rise will hurt a given shape.

The specific question: reflectance under the Fresnel coating got worse by 2.0x
for a flat plate, 6.5x for a V-groove, and 41x for a cone. The proposed reason
is that the cone's darkness comes from many bounces and most of them are near
grazing. That is checkable here rather than assumable.

Two tracers, each exact for what it is used on:

    2D  for extruded profiles (V-grooves). A ridge is translation-invariant
        along X, so for a ray in the Y-Z plane the 2D trace is exact, not an
        approximation.
    3D  for the cone array, because the whole point of a cone is that a ray can
        walk around it azimuthally, and a 2D trace cannot see that at all.
"""

from __future__ import annotations

import os
import sys
import math
import json

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profile_ridge as PR                                          # noqa: E402
import geom3d as G3                                                 # noqa: E402
from raytrace2d import loops_to_segments, hit                       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
MAXB = 40


# ---------------------------------------------------------------- 2D, ridges
def trace2d(origin, d, segs):
    """Returns (bounce incidence angles in deg, entry_z, exit_z, escaped)."""
    p, last, angles = origin, -1, []
    for _ in range(MAXB):
        t, i = hit(p, d, segs, skip=last)
        if i < 0:
            return angles, p, True
        q = (p[0] + d[0] * t, p[1] + d[1] * t)
        a, b = segs[i]
        ex, ey = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ex, ey)
        n = (-ey / L, ex / L)
        if d[0] * n[0] + d[1] * n[1] > 0:
            n = (-n[0], -n[1])
        dot = d[0] * n[0] + d[1] * n[1]
        # incidence measured from the LOCAL surface normal
        angles.append(math.degrees(math.acos(min(1.0, abs(dot)))))
        d = (d[0] - 2 * dot * n[0], d[1] - 2 * dot * n[1])
        p, last = q, i
    return angles, p, False


def census_ridge(depth, pitch, tip, theta_deg, n_rays=400):
    p = PR.RidgeParams(face_w=100.0, face_h=100.0, depth=depth,
                       pitch_mean=pitch, tip_width=tip, arc_segments=24,
                       valley_round=0.4, pitch_jitter=0.0, margin_depths=0.2)
    cs = PR.build_cross_section(p)
    segs = []
    for loops in (cs.stage1, cs.stage2, cs.shell):
        if loops:
            segs.extend(loops_to_segments(loops))
    th = math.radians(theta_deg)
    d = (-math.cos(th), math.sin(th))          # travelling toward -Y (into it)
    out = {"bounces": [], "angles": [], "disp": [], "escaped": 0}
    # Start 2 mm above the tips, not 60 mm. At -40 deg a ray launched from
    # y=60 drifts 50 mm sideways before it ever reaches the surface and runs
    # off the end of the tile -- which read as "no bounces" and would have been
    # reported as a structure that does nothing.
    y0 = 2.0
    # sweep the entry point across two full pitches: phase matters
    for k in range(n_rays):
        z0 = -pitch + 2.0 * pitch * k / (n_rays - 1) - y0 * math.tan(th)
        o = (y0, z0)
        ang, pend, esc = trace2d(o, d, segs)
        out["bounces"].append(len(ang))
        out["angles"].extend(ang)
        out["disp"].append(abs(pend[1] - z0))
        out["escaped"] += 1 if esc else 0
    return out


# ------------------------------------------------------------------ 3D, cones
def mesh_arrays(p):
    v, f = G3.build_mesh(p)
    V = np.asarray(v, dtype=np.float64)
    tris = []
    for face in f:
        for i in range(1, len(face) - 1):
            tris.append((face[0], face[i], face[i + 1]))
    T = np.asarray(tris, dtype=np.int64)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    N = np.cross(B - A, C - A)
    L = np.linalg.norm(N, axis=1, keepdims=True)
    keep = (L[:, 0] > 1e-12)
    return A[keep], B[keep], C[keep], N[keep] / L[keep]


def trace3d(origin, d, A, B, C, N):
    """Moller-Trumbore against every triangle, vectorised. Slow but exact."""
    E1, E2 = B - A, C - A
    angles, o = [], np.asarray(origin, dtype=np.float64)
    d = np.asarray(d, dtype=np.float64)
    skip = -1
    for _ in range(MAXB):
        P = np.cross(d, E2)
        det = np.einsum("ij,ij->i", E1, P)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        Tv = o - A
        u = np.einsum("ij,ij->i", Tv, P) * inv
        Q = np.cross(Tv, E1)
        vv = np.einsum("j,ij->i", d, Q) * inv
        t = np.einsum("ij,ij->i", E2, Q) * inv
        good = ok & (u >= -1e-9) & (vv >= -1e-9) & (u + vv <= 1 + 1e-9) & (t > 1e-6)
        if skip >= 0:
            good[skip] = False
        if not good.any():
            return angles, o, True
        idx = int(np.argmin(np.where(good, t, np.inf)))
        o = o + d * t[idx]
        n = N[idx]
        if float(d @ n) > 0:
            n = -n
        dot = float(d @ n)
        angles.append(math.degrees(math.acos(min(1.0, abs(dot)))))
        d = d - 2.0 * dot * n
        skip = idx
    return angles, o, False


def census_cone(depth, pitch, tip, theta_deg, n_rays=120, seed=3):
    p = G3.Cone3DParams(face_w=100.0, face_h=100.0, depth=depth, pitch=pitch,
                        tip_radius=tip, jitter=0.30, radial_seg=16,
                        height_seg=2, margin_depths=0.2, backing=3.0,
                        depth_jitter=0.0)
    A, B, C, N = mesh_arrays(p)
    th = math.radians(theta_deg)
    d = np.array([0.0, -math.cos(th), math.sin(th)])
    rng = np.random.default_rng(seed)
    out = {"bounces": [], "angles": [], "disp": [], "escaped": 0,
           "tris": int(len(A))}
    # geom3d builds (x, y, z) with the DEPTH along y: tips at y=0, bases at
    # y=-depth. Launch just above the tips for the same reason as the 2D case.
    y0 = 2.0
    for _ in range(n_rays):
        x0 = rng.uniform(35.0, 65.0)
        z0 = rng.uniform(-15.0, 15.0) - y0 * math.tan(th)
        o = np.array([x0, y0, z0])
        ang, pend, esc = trace3d(o, d, A, B, C, N)
        out["bounces"].append(len(ang))
        out["angles"].extend(ang)
        out["disp"].append(float(math.hypot(pend[0] - x0, pend[2] - z0)))
        out["escaped"] += 1 if esc else 0
    return out


def summarise(name, c):
    b = np.array(c["bounces"], dtype=float)
    a = np.array(c["angles"], dtype=float)
    dz = np.array(c["disp"], dtype=float)
    graz = float((a > 70).mean() * 100) if a.size else 0.0
    return {"design": name, "mean_bounces": float(b.mean()),
            "median_bounces": float(np.median(b)),
            "mean_angle": float(a.mean()) if a.size else float("nan"),
            "median_angle": float(np.median(a)) if a.size else float("nan"),
            "pct_over_70": graz,
            "median_disp_mm": float(np.median(dz)),
            "n_bounce_samples": int(a.size)}


def main():
    rows = []
    for th in (0.0, -40.0):
        for nm, fn, args in (
                ("groove d50/p13", census_ridge, (50.0, 13.0, 0.4)),
                ("groove d30/p7.5", census_ridge, (30.0, 7.5, 0.4)),
                ("cone d30/p7.5", census_cone, (30.0, 7.5, 0.2)),
                ("cone d30/p3.75", census_cone, (30.0, 3.75, 0.2))):
            c = fn(*args, th)
            s = summarise(nm, c)
            s["theta"] = th
            rows.append(s)
            print("th=%+5.0f  %-16s bounces mean %5.2f med %2.0f | "
                  "incidence mean %5.1f med %5.1f | >70deg %5.1f%% | "
                  "disp med %6.2f mm"
                  % (th, nm, s["mean_bounces"], s["median_bounces"],
                     s["mean_angle"], s["median_angle"], s["pct_over_70"],
                     s["median_disp_mm"]), flush=True)
    json.dump(rows, open(os.path.join(RESULTS, "ray_census.json"), "w"),
              indent=2)
    print("\nwrote results/ray_census.json")


if __name__ == "__main__":
    main()
