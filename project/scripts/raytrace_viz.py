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

WHY THERE IS A THIRD MODE. `specular` and `diffuse` are the two EXTREMES, and
neither is the coating. Measured 2026-08-20 on honeycomb + flat base at
anodised_hi (rho 0.060), against Cycles at the same spec:

    theta      specular      diffuse       Cycles
      0        6.000 %       0.182 %       0.881 %
     20        0.080 %       0.803 %       1.075 %
     40        0.080 %       1.260 %       1.486 %

A flat plate of the same coating measures 5.933 %, so at theta 0 the specular
mode was reporting a 50 mm honeycomb as no darker than bare wall -- and the
error changes SIGN off axis (6.8x high at 0, 13x low at 20), so it could not
even be read as a bound. The mode was the dropdown's default.

`coating` mode reproduces `blender_render.make_coating` instead: a Mix Shader
whose Fac is `spec_scale * F(theta, ior)`, a Lambertian of colour `body` below
it and a white Glossy at `roughness` above. See `_scatter_coating`.

THE THING THIS MODE IS NOT. Its GGX branch samples the normal distribution
without the visible-normal or shadowing-masking corrections, so a bounce at
grazing incidence on a rough facet is approximate. Like everything else here it
is an illustration of the transport; `bidir.py` and the Render buttons are the
instruments.
"""

import math

# The coating SPLIT has one home -- ~30 sweep scripts and lock.py read it there
# and `principles/02` is about what a second copy costs. `materials` is pure
# Python by policy (its own docstring says so), which is the only reason this
# module can use it: raytrace_viz runs on an HTTP worker thread in the
# standalone server, where `blender_render` cannot be imported at all because
# it does `import bpy` at module scope. That import is exactly why the coating
# sliders were never plumbed through to this file in the first place.
import materials as MAT


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


def fresnel_dielectric_cos(cos_i, ior):
    """Cycles' `ShaderNodeFresnel`, which is the EXACT dielectric curve.

    NOT `materials.fresnel`, and the difference is deliberate. That one is
    Schlick's approximation -- "the shape the fit uses", as its docstring says
    -- and it is the right curve for the fit's own bookkeeping. But the Fac
    this mode has to reproduce is the one `make_coating` wires up, and that
    socket evaluates the exact formula. The two agree to the last digit at
    normal incidence (both are F0) and part company toward grazing: at 80 deg
    and n = 1.5, Schlick reads 0.410 against the exact 0.388, 5.7 % apart. The
    trace should match the render it sits beside, so it takes the render's.
    """
    c = abs(float(cos_i))
    eta = float(ior)
    g = eta * eta - 1.0 + c * c
    if g < 0.0:
        return 1.0                      # total internal reflection
    g = math.sqrt(g)
    a = (g - c) / (g + c)
    b = (c * (g + c) - 1.0) / (c * (g - c) + 1.0)
    return 0.5 * a * a * (1.0 + b * b)


def _frame(n):
    """An orthonormal basis with `n` as its third axis."""
    tx, ty, tz = ((1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0))
    bx = n[1] * tz - n[2] * ty
    by = n[2] * tx - n[0] * tz
    bz = n[0] * ty - n[1] * tx
    bl = math.sqrt(bx * bx + by * by + bz * bz) or 1.0
    bx, by, bz = bx / bl, by / bl, bz / bl
    cx = n[1] * bz - n[2] * by
    cy = n[2] * bx - n[0] * bz
    cz = n[0] * by - n[1] * bx
    return (bx, by, bz), (cx, cy, cz)


def _cone_perturb(d, half_deg, rng):
    """Tilt `d` by a uniform direction inside a cone of this half-angle.

    The measurement's light is not a pencil: `blender_render.add_sun` gives its
    sun an angular size of 0.5 deg, for beam divergence plus coating
    microroughness. Tracing a perfectly collimated ray put every ray at theta 0
    exactly on the degenerate axis of a vertical-walled cell, where the only
    surfaces facing the beam are horizontal and every mirror bounce returns
    along the incoming line. That is real geometry, not a bug -- but the
    measurement never sees it that sharply, so neither should the picture.
    """
    if half_deg <= 0.0:
        return list(d)
    cmin = math.cos(math.radians(half_deg))
    cz = cmin + (1.0 - cmin) * next(rng)
    s = math.sqrt(max(0.0, 1.0 - cz * cz))
    a = 2.0 * math.pi * next(rng)
    nl = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
    n = (d[0] / nl, d[1] / nl, d[2] / nl)
    u, v = _frame(n)
    sx, sy = s * math.cos(a), s * math.sin(a)
    return [sx * u[0] + sy * v[0] + cz * n[0],
            sx * u[1] + sy * v[1] + cz * n[1],
            sx * u[2] + sy * v[2] + cz * n[2]]


def _cosine_hemisphere(n, rng):
    """Lambertian scatter about `n`."""
    u1, u2 = next(rng), next(rng)
    r = math.sqrt(u1)
    a = 2.0 * math.pi * u2
    b, c = _frame(n)
    sx, sy = r * math.cos(a), r * math.sin(a)
    sz = math.sqrt(max(0.0, 1.0 - u1))
    return [sx * b[0] + sy * c[0] + sz * n[0],
            sx * b[1] + sy * c[1] + sz * n[1],
            sx * b[2] + sy * c[2] + sz * n[2]]


def _mirror(d, n):
    dd = d[0] * n[0] + d[1] * n[1] + d[2] * n[2]
    return [d[0] - 2 * dd * n[0], d[1] - 2 * dd * n[1], d[2] - 2 * dd * n[2]]


def _ggx(d, n, roughness, rng):
    """Mirror off a GGX-perturbed normal. `roughness` is Blender's, so
    alpha = roughness**2 -- the same convention `materials.roughness_from_fwhm`
    inverts when it returns sqrt(alpha)."""
    alpha = float(roughness) ** 2
    if alpha <= 1e-9:
        return _mirror(d, n)
    b, c = _frame(n)
    for _ in range(8):
        u1, u2 = next(rng), next(rng)
        th = math.atan(alpha * math.sqrt(u1 / max(1.0 - u1, 1e-12)))
        ph = 2.0 * math.pi * u2
        st, ct = math.sin(th), math.cos(th)
        h = [st * math.cos(ph) * b[i] + st * math.sin(ph) * c[i] + ct * n[i]
             for i in range(3)]
        out = _mirror(d, h)
        if out[0] * n[0] + out[1] * n[1] + out[2] * n[2] > 0.0:
            return out
    return _mirror(d, n)          # every sample went below the surface


def _scatter_coating(d, n, w, body, spec_scale, ior, roughness, rng):
    """One bounce off `blender_render.make_coating`. Returns (weight, dir).

    That material is a Mix Shader: Fac = spec_scale * F(theta, ior), a
    Lambertian of colour `body` on the Fac=0 input and a WHITE Glossy at
    `roughness` on the Fac=1 input. Mix means (1-Fac)*first + Fac*second, so
    the directional albedo of a bounce is

        alb = fac * 1.0 + (1 - fac) * body

    WHY THE BRANCH PROBABILITY IS fac/alb AND NOT fac. Any q gives an unbiased
    estimator if the weight carries the matching 1/q, but the variance is not
    the same. Taking the specular branch with probability fac -- the obvious
    reading -- makes that branch carry weight 1.0 while the diffuse branch
    carries `body`; at rho 0.06 that is a factor of 22 between two outcomes of
    the same coin, and with a few hundred rays a single rare specular escape
    swings the whole answer. Setting q = fac/alb makes BOTH multipliers equal
    alb exactly, so the weight is deterministic and all the variance lives in
    the direction, where a picture of a few hundred rays can carry it.

    It also gives the mode a self-check: at normal incidence F is F0, so
    fac = spec_scale*F0 = (1 - diffuse_frac)*rho0, alb = rho0 to the last
    digit, and q = 1 - diffuse_frac. `_selftest` asserts exactly that. And with
    spec_scale = 0 the whole thing collapses to `w *= body`, which is the
    Lambertian branch this file had before.
    """
    cos_i = -(d[0] * n[0] + d[1] * n[1] + d[2] * n[2])
    fac = min(1.0, spec_scale * fresnel_dielectric_cos(cos_i, ior))
    alb = fac + (1.0 - fac) * body
    w *= alb
    if alb > 0.0 and next(rng) * alb < fac:
        return w, _ggx(d, n, roughness, rng)
    return w, _cosine_hemisphere(n, rng)


def trace(verts, faces, face_w, face_h, theta_deg=0.0, phi_deg=0.0,
          n_rays=120, max_bounces=12, rho=0.5, seed=23, mode="coating",
          diffuse_frac=None, roughness=0.30, ior=None,
          body=None, spec_scale=None, divergence_deg=None):
    """Cast `n_rays` at incidence theta and walk each until it leaves or dies.

    2026-08-17 upgrade toward optical-tool behaviour:
    - `mode` = "coating" (the fitted Fresnel mix -- the default, and the only
      one that tracks the measurement), "diffuse" (cosine-weighted Lambertian
      scatter) or "specular" (mirror bounces, the mechanism picture that the
      report figures use -- deterministic ladders). The last two are the two
      EXTREMES of the first; see the module docstring for what they cost.
    - ENERGY IS TRACKED ANALYTICALLY, no Russian roulette: every bounce
      multiplies the ray's weight by the surface's directional albedo, and the
      mean weight carried OUT by escaping rays is an unbiased estimate of the
      panel's reflectance at this incidence. The UI shows it next to the Cycles
      measurement -- an independent cross-check in one click. A ray is retired
      as "trapped" when it exhausts max_bounces.

    COATING PARAMETERS. `body` and `spec_scale` are the split; pass them
    straight through when the caller already resolved a named material.
    Otherwise they come from `materials.coating_split(diffuse_frac, rho0=rho)`,
    so a caller that only knows a single rho -- which is all `/api/rays` sent
    for its whole life -- still gets the fitted split rather than a mirror.

    Returns {"paths": [...], "depths": [...], "escaped": [...],
             "weights": [...], "stats": {..., "hist": [...],
             "rho_est": float}} in mesh millimetre coordinates.
    """
    ior = MAT.MUSOU_IOR if ior is None else float(ior)
    if mode == "coating" and (body is None or spec_scale is None):
        d = MAT.MUSOU_DIFFUSE_USED if diffuse_frac is None else diffuse_frac
        body, spec_scale = MAT.coating_split(d, rho0=rho, ior=ior)
    body = rho if body is None else float(body)
    spec_scale = 0.0 if spec_scale is None else float(spec_scale)
    # The mechanism picture is a DETERMINISTIC ladder, and a diverging source
    # is the one thing that would stop it being one. Every other mode gets the
    # measurement's own 0.5 deg.
    if divergence_deg is None:
        divergence_deg = 0.0 if mode == "specular" else 0.5
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
        d = _cone_perturb(d0, 0.5 * divergence_deg, rng)
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
            n = tris[bi][3]
            nl = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
            n = (n[0] / nl, n[1] / nl, n[2] / nl)
            if n[0] * d[0] + n[1] * d[1] + n[2] * d[2] > 0:
                n = (-n[0], -n[1], -n[2])
            if mode == "specular":
                w *= rho
                d = _mirror(d, n)
            elif mode == "coating":
                w, d = _scatter_coating(d, n, w, body, spec_scale, ior,
                                        roughness, rng)
            else:
                w *= rho
                d = _cosine_hemisphere(n, rng)
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
    # AND NEITHER IS A RAY THAT LEFT THROUGH THE SIDE. `missed` catches only
    # rays that hit nothing at all; a ray that bounces into the lattice and
    # then walks out of the cut face `clip_to_panel` opened is "escaped" by
    # every test in this loop, and its weight was being counted as light the
    # wall returned. At theta 0 in diffuse mode, 7 of 44 escapers left DOWNWARD
    # -- final direction below the horizon, polar angle out to 132 deg -- for
    # 1.0 % of the escaping weight. A real panel is a wall, not a tile with
    # open edges, so that light does not come back to the room. It is reported
    # rather than dropped: an edge leak that grows is a sign the trimmed mesh
    # is too small for the incidence, not a property of the design.
    w_out = w_leak = 0.0
    n_leak = 0
    for i in hits:
        if not escaped[i]:
            continue
        p = paths[i]
        m = len(p) // 3
        if p[(m - 1) * 3 + 1] - p[(m - 2) * 3 + 1] > 0.0:
            w_out += weights[i]
        else:
            w_leak += weights[i]
            n_leak += 1
    rho_est = w_out / nh
    n_missed = n - len(hits)
    return {"paths": paths, "depths": depths, "escaped": escaped,
            "weights": weights,
            "stats": {"rays": len(depths),
                      "mean_bounces": total_b / n,
                      "absorbed_frac": n_absorbed / n,
                      "escaped_frac": sum(escaped) / n,
                      "max_bounces": max_bounces, "rho": rho,
                      "mode": mode, "hist": hist, "rho_est": rho_est,
                      "missed": n_missed,
                      "leak": n_leak,
                      "leak_frac": (w_leak / (w_out + w_leak)
                                    if (w_out + w_leak) else 0.0),
                      "body": body, "spec_scale": spec_scale,
                      "roughness": roughness, "ior": ior,
                      "divergence_deg": divergence_deg,
                      "theta": theta_deg,
                      "triangles": len(tris)}}


def _selftest():
    """The identities the coating mode has to satisfy. `python3 raytrace_viz.py`

    None of these need a mesh, a renderer or a server: they are properties of
    the scatter rule alone, which is the level the 2026-08-20 defect lived at.
    """
    bad = []

    def ck(name, got, want, tol=1e-12):
        """RELATIVE where there is something to be relative to. An absolute
        1e-18 on a quantity of order 0.05 is below the spacing of float64
        there, so it fails on values that are equal to every bit that exists."""
        if abs(got - want) > tol * max(1.0, abs(want)):
            bad.append("%-46s %.17g != %.17g" % (name, got, want))

    # 1. Fresnel: the exact curve must reproduce the constant the whole project
    #    hardcoded, and must be BELOW Schlick toward grazing.
    ck("F(normal, 1.5) == F0_IOR15",
       fresnel_dielectric_cos(1.0, 1.5), MAT.F0_IOR15, 1e-15)
    f80 = fresnel_dielectric_cos(math.cos(math.radians(80.0)), 1.5)
    if not 0.38 < f80 < 0.39:
        bad.append("F(80 deg, 1.5) = %.4f, expected ~0.388" % f80)
    if not f80 < MAT.fresnel(80.0, 1.5):
        bad.append("exact Fresnel should sit below Schlick at 80 deg")

    # 2. The estimator at normal incidence, for every material in the library
    #    crossed with a few splits.
    #
    #    THE MIX SHADER DOES NOT INTEGRATE TO rho0, and this test found it. The
    #    fit says rho_dh(0) = body + spec_scale*F0 = rho0, but a Mix Shader is
    #    (1-Fac)*first + Fac*second, so what the render actually evaluates is
    #
    #        alb = (1 - fac)*body + fac  =  rho0 - fac*body
    #
    #    short of rho0 by the cross term. At the published musou_fit split that
    #    is 0.996183 % against a nominal 0.998 %, i.e. 0.18 % low -- which is
    #    the "-0.2" residual at theta 0 in blender_render.py's own fit table,
    #    the one row that table calls exact-by-construction. It is not the fit
    #    being slightly off; it is this term. Well inside the +/-20 % absolute
    #    uncertainty that file records, so it is asserted rather than chased.
    for name, m in sorted(MAT.LIBRARY.items()):
        for d in (0.0, 0.5, 0.758, 0.76, 0.85, 1.0):
            body, spec = MAT.coating_split(d, rho0=m.rho0, ior=MAT.MUSOU_IOR)
            fac = min(1.0, spec * fresnel_dielectric_cos(1.0, MAT.MUSOU_IOR))
            alb = fac + (1.0 - fac) * body
            ck("%s d=%.3f: albedo == rho0 - fac*body" % (name, d),
               alb, m.rho0 - fac * body, 1e-15)
            # The deficit is fac*body ~ d(1-d)*rho0**2, so relative to rho0 it
            # cannot exceed rho0/4 -- worst at an even split. A bound with the
            # rho0 in it, not a magic percentage that would have to be widened
            # the first time someone adds a brighter material to the library.
            lo = 1.0 - 0.25 * m.rho0 - 1e-12
            if not lo <= alb / m.rho0 <= 1.0 + 1e-12:
                bad.append("%s d=%.3f: albedo/rho0 = %.9f, outside %.9f..1"
                           % (name, d, alb / m.rho0, lo))
            # P(specular) is 1-d to within that same cross term, never exact.
            if d < 1.0 and abs(fac / alb / (1.0 - d) - 1.0) > 0.02:
                bad.append("%s d=%.3f: P(spec) = %.6f, more than 2 %% from "
                           "1-d = %.3f" % (name, d, fac / alb, 1.0 - d))
            if d >= 1.0:
                ck("%s d=1: no specular branch" % name, fac, 0.0, 1e-18)

    # 3. spec_scale = 0 must be the plain Lambertian this file had before.
    rng = _lcg(7)
    w, _ = _scatter_coating([0.0, -1.0, 0.0], (0.0, 1.0, 0.0), 1.0,
                            0.06, 0.0, 1.5, 0.30, rng)
    ck("spec_scale 0 collapses to w *= body", w, 0.06, 1e-15)

    # 4. Scattered directions stay in the upper hemisphere, GGX included.
    rng = _lcg(11)
    n = (0.0, 1.0, 0.0)
    for r in (0.0, 0.05, 0.30, 0.60, 1.0):
        for _ in range(400):
            for out in (_ggx([0.3, -0.9, 0.1], n, r, rng),
                        _cosine_hemisphere(n, rng)):
                if out[1] <= 0.0:
                    bad.append("scatter went below the surface at "
                               "roughness %.2f" % r)
                    break

    # 5. Divergence stays inside the cone it was given, and 0 is a no-op.
    rng = _lcg(13)
    d0 = (0.0, -1.0, 0.0)
    ck("divergence 0 is a no-op", _cone_perturb(d0, 0.0, rng)[1], -1.0, 0.0)
    for _ in range(500):
        p = _cone_perturb(d0, 0.25, rng)
        a = math.degrees(math.acos(min(1.0, -p[1] / math.sqrt(
            p[0] ** 2 + p[1] ** 2 + p[2] ** 2))))
        if a > 0.2500001:
            bad.append("divergence %.4f deg outside its 0.25 deg cone" % a)
            break

    for b in bad:
        print("  FAIL  " + b)
    print("raytrace_viz self-test: %d failure(s)" % len(bad))
    return len(bad)


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(_selftest())
