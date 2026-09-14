"""The coating BRDF as plain arithmetic. No renderer, no bpy.

    f(wi, wo) = body / pi  +  spec_scale * D(h) G(wi, wo) F(h.wi) / (4 cos_i cos_o)

Lambert body plus a GGX microfacet lobe whose Fresnel is evaluated on the
HALF VECTOR. That is the standard microfacet form (Walter 2007, eq. 20; Cook &
Torrance 1982), and it is reciprocal by construction: every factor is
symmetric in (wi, wo).

WHY THIS FILE EXISTS (2026-09-14). The Cycles coating up to now mixed a
Diffuse and a Glossy BSDF with a Fresnel NODE as the mix factor. That node
evaluates Fresnel against the macro normal and the direction the path came
FROM -- the viewer's side -- so the weight was F(theta_o) and not F(theta_h).
Swapping source and viewer changed the flat-plate BRDF by 55 % at 1024 spp
(`results/audit_2026_09_14/render_probe.json`). `hemi_view` reads the panel
under a uniform sky from one direction and calls that, by Helmholtz
reciprocity, the hemispherical reflectance for a beam arriving FROM that
direction. Without reciprocity that reading is not the quantity it is named.

This module is the reference the renderer is checked against:

  * `directional_albedo(theta_i)`  is THR, Filip & Vavra 2026 eq. 1.
  * `tis(theta_i)`                 is their eq. 3 with a 5 deg exclusion cone.
  * `rs(theta_i)`                  is the specular component, (1 - TIS) * THR.

`scripts/fit_musou_fit2.py` fits (body, spec_scale, alpha) to the chart-read
values in `material/_filip2026_fig6_read.json`, and
`scripts/gate_coating_reciprocity.py` renders the same BRDF in Cycles and
compares the flat-plate reading with `directional_albedo` here.

Parameter meaning is unchanged from `blender_render.coating_split`:
`body` is the angle-free part of rho_dh, `spec_scale` scales one full
dielectric lobe (F0 = 0.04 at n = 1.5), so rho_dh(0) = body + spec_scale*F0.
`alpha` is GGX alpha, the square of the Cycles roughness slider.
"""

import math
import numpy as np


def fresnel_dielectric(cos_i, n):
    """Unpolarised Fresnel reflectance of a dielectric, exact."""
    c = np.clip(np.asarray(cos_i, dtype=np.float64), 0.0, 1.0)
    s2 = 1.0 - c * c
    ct = np.sqrt(np.clip(1.0 - s2 / (n * n), 0.0, 1.0))
    rs = (c - n * ct) / (c + n * ct)
    rp = (n * c - ct) / (n * c + ct)
    return 0.5 * (rs * rs + rp * rp)


def fresnel_schlick(cos_i, n):
    """Schlick's approximation, which is what Cycles' Principled node uses
    (F0 from the IOR, F90 = 1). Kept so the reference can be run either way
    and the difference measured instead of guessed."""
    f0 = ((n - 1.0) / (n + 1.0)) ** 2
    c = np.clip(np.asarray(cos_i, dtype=np.float64), 0.0, 1.0)
    return f0 + (1.0 - f0) * (1.0 - c) ** 5


FRESNEL = {"exact": fresnel_dielectric, "schlick": fresnel_schlick}


def ggx_d(cos_h, alpha):
    """GGX / Trowbridge-Reitz normal distribution, normalised over the
    projected hemisphere (integral of D * cos_h = 1)."""
    a2 = alpha * alpha
    c2 = np.clip(cos_h, 0.0, 1.0) ** 2
    den = c2 * (a2 - 1.0) + 1.0
    return a2 / (math.pi * den * den)


def smith_lambda(cos_t, alpha):
    c = np.clip(cos_t, 1e-9, 1.0)
    t2 = (1.0 - c * c) / (c * c)
    return 0.5 * (np.sqrt(1.0 + alpha * alpha * t2) - 1.0)


def smith_g2(cos_i, cos_o, alpha):
    """Height-correlated Smith masking-shadowing, symmetric in (i, o)."""
    return 1.0 / (1.0 + smith_lambda(cos_i, alpha) + smith_lambda(cos_o, alpha))


def brdf(wi, wo, body, spec_scale, alpha, ior=1.5, fresnel="exact"):
    """f_r for unit vectors wi, wo of shape (..., 3), z along the normal.
    Directions below the horizon return 0."""
    wi = np.asarray(wi, dtype=np.float64)
    wo = np.asarray(wo, dtype=np.float64)
    ci = wi[..., 2]
    co = wo[..., 2]
    up = (ci > 0) & (co > 0)
    h = wi + wo
    hn = np.linalg.norm(h, axis=-1)
    hn = np.where(hn > 0, hn, 1.0)
    h = h / hn[..., None]
    cos_h = h[..., 2]
    cos_hi = np.sum(h * wi, axis=-1)
    F = FRESNEL[fresnel](cos_hi, ior)
    D = ggx_d(cos_h, alpha)
    G = smith_g2(ci, co, alpha)
    den = 4.0 * np.clip(ci, 1e-9, None) * np.clip(co, 1e-9, None)
    spec = spec_scale * D * G * F / den
    f = body / math.pi + spec
    return np.where(up, f, 0.0)


def _dir(theta, phi):
    st = np.sin(theta)
    return np.stack([st * np.cos(phi), st * np.sin(phi), np.cos(theta)], -1)


def hemisphere_grid(n_theta=1800, n_phi=720):
    """Midpoint grid over the outgoing hemisphere: directions (N, 3) and the
    solid-angle weights (N,). Uniform in theta so the zenith is resolved as
    finely as the horizon; a narrow lobe needs that near theta_o = theta_i."""
    th = (np.arange(n_theta) + 0.5) * (0.5 * math.pi / n_theta)
    ph = (np.arange(n_phi) + 0.5) * (2.0 * math.pi / n_phi)
    T, P = np.meshgrid(th, ph, indexing="ij")
    w = np.sin(T) * (0.5 * math.pi / n_theta) * (2.0 * math.pi / n_phi)
    return _dir(T.ravel(), P.ravel()), w.ravel()


_GRID = {}


def _grid(n_theta, n_phi):
    key = (n_theta, n_phi)
    if key not in _GRID:
        _GRID[key] = hemisphere_grid(n_theta, n_phi)
    return _GRID[key]


def integrate(theta_i_deg, body, spec_scale, alpha, ior=1.5, fresnel="exact",
              cone_deg=5.0, n_theta=1800, n_phi=720):
    """THR, TIS and Rs at one incidence angle, all from one quadrature.

    Returns dict(thr, tis, rs, inside) where `inside` is the cosine-weighted
    reflected energy that lands within `cone_deg` of the mirror direction."""
    wo, w = _grid(n_theta, n_phi)
    ti = math.radians(theta_i_deg)
    wi = np.array([math.sin(ti), 0.0, math.cos(ti)])
    f = brdf(np.broadcast_to(wi, wo.shape), wo, body, spec_scale, alpha, ior,
             fresnel)
    contrib = f * wo[:, 2] * w
    thr = float(contrib.sum())
    mirror = np.array([-math.sin(ti), 0.0, math.cos(ti)])
    cos_c = math.cos(math.radians(cone_deg))
    inside = float(contrib[wo @ mirror >= cos_c].sum())
    tis = 1.0 - inside / thr if thr > 0 else float("nan")
    return {"thr": thr, "tis": tis, "rs": thr - inside, "inside": inside}


def terms(theta_i_deg, alpha, ior=1.5, fresnel="exact", cone_deg=5.0,
          n_theta=1800, n_phi=720):
    """The model is LINEAR in body and spec_scale, so a fit only has to
    integrate over alpha. Returns the four numbers that make everything
    else closed-form:

        thr    = body * 1        + spec_scale * e_lobe
        inside = body * l_inside + spec_scale * i_lobe

    `e_lobe` is the directional albedo of one full lobe, `i_lobe` the part of
    it within the cone, `l_inside` the cosine-weighted share of a unit
    Lambertian that lands within the cone about the mirror direction."""
    wo, w = _grid(n_theta, n_phi)
    ti = math.radians(theta_i_deg)
    wi = np.array([math.sin(ti), 0.0, math.cos(ti)])
    lobe = brdf(np.broadcast_to(wi, wo.shape), wo, 0.0, 1.0, alpha, ior,
                fresnel) * wo[:, 2] * w
    mirror = np.array([-math.sin(ti), 0.0, math.cos(ti)])
    in_cone = wo @ mirror >= math.cos(math.radians(cone_deg))
    lam = wo[:, 2] * w / math.pi
    return {"e_lobe": float(lobe.sum()), "i_lobe": float(lobe[in_cone].sum()),
            "l_inside": float(lam[in_cone].sum())}


def from_terms(t, body, spec_scale):
    thr = body + spec_scale * t["e_lobe"]
    inside = body * t["l_inside"] + spec_scale * t["i_lobe"]
    return {"thr": thr, "tis": 1.0 - inside / thr if thr > 0 else float("nan"),
            "rs": thr - inside, "inside": inside}


def profile_terms(theta_deg, phis_deg, alpha, ior=1.5, fresnel="exact"):
    """The in-plane slice Filip & Vavra plot in Fig. 5: theta_i = theta_v,
    view azimuth phi with 180 = the mirror direction. Returns the unit-lobe
    BRDF value at each phi; the full value is body/pi + spec_scale * lobe."""
    t = math.radians(theta_deg)
    wi = np.array([math.sin(t), 0.0, math.cos(t)])
    ph = np.radians(np.asarray(phis_deg, dtype=np.float64))
    wo = np.stack([math.sin(t) * np.cos(ph), math.sin(t) * np.sin(ph),
                   np.full_like(ph, math.cos(t))], -1)
    return brdf(np.broadcast_to(wi, wo.shape), wo, 0.0, 1.0, alpha, ior,
                fresnel)


def directional_albedo(theta_i_deg, body, spec_scale, alpha, ior=1.5,
                       fresnel="exact", **kw):
    return integrate(theta_i_deg, body, spec_scale, alpha, ior, fresnel,
                     **kw)["thr"]


def tis(theta_i_deg, body, spec_scale, alpha, ior=1.5, fresnel="exact", **kw):
    return integrate(theta_i_deg, body, spec_scale, alpha, ior, fresnel,
                     **kw)["tis"]


def rs(theta_i_deg, body, spec_scale, alpha, ior=1.5, fresnel="exact", **kw):
    return integrate(theta_i_deg, body, spec_scale, alpha, ior, fresnel,
                     **kw)["rs"]


def reciprocity_gap(body, spec_scale, alpha, ior=1.5, fresnel="exact",
                    pairs=((80.0, -65.0), (60.0, -40.0), (45.0, 20.0))):
    """|f(a->b) - f(b->a)| / f(a->b) for in-plane direction pairs. Zero to
    rounding for this model; the renderer's own number is what
    `gate_coating_reciprocity.py` measures."""
    out = []
    for a, b in pairs:
        ta, tb = math.radians(a), math.radians(b)
        wa = np.array([math.sin(ta), 0.0, math.cos(ta)])
        wb = np.array([math.sin(tb), 0.0, math.cos(tb)])
        f1 = float(brdf(wa, wb, body, spec_scale, alpha, ior, fresnel))
        f2 = float(brdf(wb, wa, body, spec_scale, alpha, ior, fresnel))
        out.append({"a": a, "b": b, "f_ab": f1, "f_ba": f2,
                    "gap": abs(f1 - f2) / max(f1, 1e-30)})
    return out


def energy_check(body, spec_scale, alpha, ior=1.5, fresnel="exact",
                 thetas=(0.0, 30.0, 60.0, 80.0, 89.0)):
    """Directional albedo must never exceed 1 (passive surface)."""
    return {t: directional_albedo(t, body, spec_scale, alpha, ior, fresnel)
            for t in thetas}


if __name__ == "__main__":
    import json
    import sys
    args = [float(a) for a in sys.argv[1:4]] if len(sys.argv) >= 4 else None
    body, s, a = args or (0.00758, 0.0605, 0.09)
    print("body %.5f  spec_scale %.4f  alpha %.4f" % (body, s, a))
    for t in (0, 15, 30, 45, 60, 75, 80, 85):
        r = integrate(t, body, s, a)
        print("  theta %2d  THR %.5f  TIS %.4f  Rs %.5f"
              % (t, r["thr"], r["tis"], r["rs"]))
    print("reciprocity gaps:", json.dumps(
        [round(x["gap"], 12) for x in reciprocity_gap(body, s, a)]))
