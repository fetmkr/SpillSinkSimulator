"""Trace rays through the panel and hand the browser their paths to draw.

This is not a picture of a render. It is the actual transport: rays are cast at
the requested incidence, intersected against the same triangles the measurement
uses, scattered from a Lambertian at each hit, and the polyline each one walks
is returned. What the viewport draws is where the light went and where it was
absorbed, which is the thing every number in this study is a summary of.

WHY IT IS WORTH THE CODE. `FINDINGS_renderer_disagreement.md` spent a session
narrowing a 44 % Cycles/Mitsuba gap to the single-scattering visibility term on
thin walls. Every step of that was a scalar compared against another scalar. A
ray count per depth, and a picture of which rays leave after one bounce and
which are still rattling at ten, is the same information in the form a person
can check at a glance.

THE INTERSECTION. A brute-force ray-triangle test over every triangle is
O(n) per ray and the comb is 78 000 triangles, so this uses a uniform grid over
the x-z plane: each triangle is inserted into the cells its footprint covers,
and a ray walks the cells it passes through. That is enough for a few hundred
rays interactively, and it is exact -- no acceleration structure approximation,
just fewer candidates. Moller-Trumbore for the test itself.

NOTHING HERE FEEDS A MEASUREMENT. It is a display, and the numbers it reports
(mean bounces, absorbed fraction) come from the same scattering rule the
measurement assumes rather than from Cycles, so they are an illustration of the
transport and not a second opinion about it.
"""

import math


def _tris(verts, faces):
    """Fan-triangulate, dropping degenerate triangles."""
    out = []
    for f in faces:
        idx = list(f)
        for a in range(1, len(idx) - 1):
            i, j, k = idx[0], idx[a], idx[a + 1]
            p, q, r = verts[i], verts[j], verts[k]
            ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
            vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            if nx * nx + ny * ny + nz * nz > 1e-18:
                out.append((p, q, r, (nx, ny, nz)))
    return out


class Grid:
    """Uniform grid over x and z. Y is not divided: the panel is thin in x-z
    and deep in y, so cells along the depth would all be visited anyway."""

    def __init__(self, tris, nx=64, nz=64):
        self.tris = tris
        xs = [v[0] for t in tris for v in t[:3]]
        zs = [v[2] for t in tris for v in t[:3]]
        self.x0, self.x1 = min(xs), max(xs)
        self.z0, self.z1 = min(zs), max(zs)
        self.nx, self.nz = nx, nz
        self.dx = max((self.x1 - self.x0) / nx, 1e-9)
        self.dz = max((self.z1 - self.z0) / nz, 1e-9)
        self.cells = [[] for _ in range(nx * nz)]
        for ti, t in enumerate(tris):
            tx0 = min(v[0] for v in t[:3])
            tx1 = max(v[0] for v in t[:3])
            tz0 = min(v[2] for v in t[:3])
            tz1 = max(v[2] for v in t[:3])
            i0 = max(0, min(nx - 1, int((tx0 - self.x0) / self.dx)))
            i1 = max(0, min(nx - 1, int((tx1 - self.x0) / self.dx)))
            j0 = max(0, min(nz - 1, int((tz0 - self.z0) / self.dz)))
            j1 = max(0, min(nz - 1, int((tz1 - self.z0) / self.dz)))
            for j in range(j0, j1 + 1):
                row = j * nx
                for i in range(i0, i1 + 1):
                    self.cells[row + i].append(ti)

    def candidates(self, o, d, tmax):
        """Triangle indices in the cells the ray crosses, near to far.

        Walks the x-z projection of the ray. A ray travelling almost straight
        down in y barely moves in x-z and visits one column, which is the
        common case here and the reason the grid pays for itself.
        """
        seen = set()
        # STEP BY HALF A CELL ALONG THE ACTUAL X-Z TRAVEL, not by a fixed count.
        # The first version took `max(nx, nz) * 2` samples over the whole 400 mm
        # ray length -- 3.1 mm apart against a 1.6 mm cell -- so a ray moving
        # sideways skipped cells, missed the triangles in them and escaped a
        # cavity it should have been trapped in. A 50 mm deep comb reported
        # 56 % of rays escaping at normal incidence and a mean of 1.04 bounces;
        # correctly stepped it absorbs essentially all of them.
        span_xz = math.hypot(d[0], d[2]) * tmax
        cell = 0.5 * min(self.dx, self.dz)
        steps = int(span_xz / cell) + 2
        steps = min(steps, 4000)
        for s in range(steps + 1):
            t = tmax * s / steps
            x = o[0] + d[0] * t
            z = o[2] + d[2] * t
            i = int((x - self.x0) / self.dx)
            j = int((z - self.z0) / self.dz)
            if 0 <= i < self.nx and 0 <= j < self.nz:
                for ti in self.cells[j * self.nx + i]:
                    seen.add(ti)
        return seen


def _hit(o, d, tri, eps=1e-6):
    """Moller-Trumbore. Returns t or None."""
    p, q, r, _ = tri
    e1 = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
    e2 = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
    hx = d[1] * e2[2] - d[2] * e2[1]
    hy = d[2] * e2[0] - d[0] * e2[2]
    hz = d[0] * e2[1] - d[1] * e2[0]
    a = e1[0] * hx + e1[1] * hy + e1[2] * hz
    if -1e-12 < a < 1e-12:
        return None
    f = 1.0 / a
    s = (o[0] - p[0], o[1] - p[1], o[2] - p[2])
    u = f * (s[0] * hx + s[1] * hy + s[2] * hz)
    if u < 0.0 or u > 1.0:
        return None
    qx = s[1] * e1[2] - s[2] * e1[1]
    qy = s[2] * e1[0] - s[0] * e1[2]
    qz = s[0] * e1[1] - s[1] * e1[0]
    v = f * (d[0] * qx + d[1] * qy + d[2] * qz)
    if v < 0.0 or u + v > 1.0:
        return None
    t = f * (e2[0] * qx + e2[1] * qy + e2[2] * qz)
    return t if t > eps else None


def _lcg(seed):
    x = (seed * 1103515245 + 12345) & 0x7FFFFFFF
    while True:
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
        yield x / 2147483648.0


def trace(verts, faces, face_w, face_h, theta_deg=0.0, phi_deg=0.0,
          n_rays=120, max_bounces=12, rho=0.5, seed=23, mode="diffuse",
          diffuse_frac=None, roughness=0.30):
    """Cast `n_rays` at incidence theta and walk each until it leaves or dies.

    2026-08-17 upgrade toward optical-tool behaviour:
    - `mode` = "diffuse" (cosine-weighted Lambertian scatter, the transport
      picture) or "specular" (mirror bounces, the mechanism picture that the
      report figures use -- deterministic ladders).
    - ENERGY IS TRACKED ANALYTICALLY, no Russian roulette: every bounce
      multiplies the ray's weight by `rho`, and the mean weight carried OUT
      by escaping rays is an unbiased estimate of the panel's reflectance at
      this incidence. The UI shows it next to the Cycles measurement -- an
      independent cross-check in one click. A ray is retired as "trapped"
      when it exhausts max_bounces (weight <= rho^max_bounces).

    Returns {"paths": [...], "depths": [...], "escaped": [...],
             "weights": [...], "stats": {..., "hist": [...],
             "rho_est": float}} in mesh millimetre coordinates.
    """
    tris = _tris(verts, faces)
    grid = Grid(tris)
    rng = _lcg(seed)
    th = math.radians(theta_deg)
    ph = math.radians(phi_deg)
    # travel direction of the incoming beam: down -y, tilted by theta in the
    # plane picked by phi. Matches `blender_render.add_sun`'s convention.
    d0 = (-math.sin(th) * math.sin(ph), -math.cos(th), -math.sin(th) *
          math.cos(ph))

    paths, depths, escaped, weights = [], [], [], []
    total_b, n_absorbed = 0, 0
    # THE INCOMING BEAM HAS TO BE VISIBLE. Starting 1 mm above the panel drew
    # the arriving ray as a stub the panel itself hid; the picture then showed
    # only what happens inside. A standoff of a third of the panel gives the
    # beam a run long enough to read its direction at a glance, and costs
    # nothing -- it is empty space, so the first intersection is unchanged.
    y_top = max(v[1] for v in verts) + 0.35 * max(face_w, face_h)
    span = max(face_w, face_h) * 4.0

    # ENTRY POINTS COME FROM THE MESH, NOT FROM AN ASSUMED FRAME. The measured
    # geometry has its face at x in [0, face_w] and z in [-face_h/2, +face_h/2],
    # but the previewed and exported part is TRIMMED and shifted to
    # z in [0, face_h]. Casting into the assumed frame put most rays beside the
    # trimmed panel where they hit nothing, and a 50 mm deep comb reported 56 %
    # of rays escaping at normal incidence. The bounds are read off the
    # vertices, and inset by a tenth so no ray starts on the cut edge.
    mx0 = min(v[0] for v in verts)
    mx1 = max(v[0] for v in verts)
    mz0 = min(v[2] for v in verts)
    mz1 = max(v[2] for v in verts)
    ix = 0.10 * (mx1 - mx0)
    iz = 0.10 * (mz1 - mz0)

    for _ in range(n_rays):
        # entry point spread over the face, so the picture shows the field and
        # not one cell
        x = mx0 + ix + next(rng) * (mx1 - mx0 - 2 * ix)
        z = mz0 + iz + next(rng) * (mz1 - mz0 - 2 * iz)
        # step back along the beam so the ray starts above everything
        k = (y_top - 0.0) / max(-d0[1], 1e-9)
        o = [x - d0[0] * k, y_top, z - d0[2] * k]
        d = list(d0)
        pts = [list(o)]
        alive = True
        w = 1.0
        b = 0
        while b <= max_bounces:
            best, bi = span, None
            for ti in grid.candidates(o, d, span):
                t = _hit(o, d, tris[ti])
                if t is not None and t < best:
                    best, bi = t, ti
            if bi is None:
                pts.append([o[0] + d[0] * span * 0.35,
                            o[1] + d[1] * span * 0.35,
                            o[2] + d[2] * span * 0.35])
                break
            o = [o[0] + d[0] * best, o[1] + d[1] * best, o[2] + d[2] * best]
            pts.append(list(o))
            b += 1
            w *= rho
            n = tris[bi][3]
            nl = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
            n = (n[0] / nl, n[1] / nl, n[2] / nl)
            if n[0] * d[0] + n[1] * d[1] + n[2] * d[2] > 0:
                n = (-n[0], -n[1], -n[2])
            # THE SAME MATERIAL THE RENDER USES, when the caller asks for it.
            # "diffuse" and "specular" are the two pure pictures; `fitted`
            # mixes them per bounce with the panel's own diffuse fraction and
            # blurs the mirror leg by its roughness. Until this existed the
            # trace and the Render could not be compared on a painted panel at
            # all: the trace was one pure mode while the Render was 76/24.
            want_spec = (mode == "specular")
            if mode == "fitted" and diffuse_frac is not None:
                want_spec = next(rng) >= float(diffuse_frac)
            if want_spec:
                dd = d[0] * n[0] + d[1] * n[1] + d[2] * n[2]
                d = [d[0] - 2 * dd * n[0], d[1] - 2 * dd * n[1],
                     d[2] - 2 * dd * n[2]]
                if mode == "fitted" and roughness > 0.0:
                    # blur the mirror leg. Not GGX -- a spherical jitter of
                    # the reflected direction, kept in the upper hemisphere.
                    for _ in range(8):
                        j = [(2.0 * next(rng) - 1.0) * roughness
                             for _ in range(3)]
                        e = [d[0] + j[0], d[1] + j[1], d[2] + j[2]]
                        el = math.sqrt(e[0]**2 + e[1]**2 + e[2]**2)
                        if el < 1e-9:
                            continue
                        e = [e[0]/el, e[1]/el, e[2]/el]
                        if e[0]*n[0] + e[1]*n[1] + e[2]*n[2] > 1e-4:
                            d = e
                            break
            else:
                # cosine-weighted hemisphere about n
                u1, u2 = next(rng), next(rng)
                r = math.sqrt(u1)
                a = 2.0 * math.pi * u2
                tx, ty, tz = ((1.0, 0.0, 0.0) if abs(n[0]) < 0.9
                              else (0.0, 1.0, 0.0))
                bx = n[1] * tz - n[2] * ty
                by = n[2] * tx - n[0] * tz
                bz = n[0] * ty - n[1] * tx
                bl = math.sqrt(bx * bx + by * by + bz * bz) or 1.0
                bx, by, bz = bx / bl, by / bl, bz / bl
                cx = n[1] * bz - n[2] * by
                cy = n[2] * bx - n[0] * bz
                cz = n[0] * by - n[1] * bx
                sx = r * math.cos(a)
                sy = r * math.sin(a)
                sz = math.sqrt(max(0.0, 1.0 - u1))
                d = [sx * bx + sy * cx + sz * n[0],
                     sx * by + sy * cy + sz * n[1],
                     sx * bz + sy * cz + sz * n[2]]
            o = [o[0] + n[0] * 1e-4, o[1] + n[1] * 1e-4, o[2] + n[2] * 1e-4]
        else:
            # bounce budget exhausted while still inside: trapped
            alive = False
            n_absorbed += 1
        total_b += b
        paths.append([c for p in pts for c in p])
        depths.append(b)
        escaped.append(1 if alive else 0)
        weights.append(w)

    n = max(len(depths), 1)
    hist = [0] * (max_bounces + 1)
    for dpt in depths:
        hist[min(dpt, max_bounces)] += 1
    # rays that never touched the panel are GEOMETRY MISSES (edge of the
    # trimmed mesh at oblique incidence), not reflectance -- excluding them
    # keeps rho_est honest. Found when 3.5 % edge misses at theta 40 carried
    # weight 1.0 and swamped a 1e-19 specular estimate.
    hits = [i for i, dpt in enumerate(depths) if dpt > 0]
    nh = max(len(hits), 1)
    rho_est = sum(weights[i] for i in hits if escaped[i]) / nh
    n_missed = n - len(hits)
    return {"paths": paths, "depths": depths, "escaped": escaped,
            "weights": weights,
            "stats": {"rays": len(depths),
                      "mean_bounces": total_b / n,
                      "absorbed_frac": n_absorbed / n,
                      "escaped_frac": sum(escaped) / n,
                      "max_bounces": max_bounces, "rho": rho,
                      "mode": mode, "diffuse_frac": diffuse_frac,
                      "roughness": roughness,
                      "hist": hist, "rho_est": rho_est,
                      "missed": n_missed,
                      "theta": theta_deg,
                      "triangles": len(tris)}}
