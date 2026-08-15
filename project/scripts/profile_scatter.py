"""
Second geometry family: scatter troughs, aimed at destroying form rather than
merely attenuating it.

Why this exists
---------------
The slat family attenuates extremely well (down to 1e-3 of a bare wall) but the
line comes back as a line. Measurements pinned the reason: everything reaching
the observer is a SINGLE bounce off the entrance surfaces, and one bounce can
never move a photon sideways, so the return always remembers where the beam
landed. Raising the hidden chamber's reflectance from 0.05 to 0.90 -- an 18x
change -- moved the result by less than 1e-4, which says the chamber
contributes nothing at all: diffuse light inside cannot get back out past the
black slats.

So the concavity has to be the thing the observer LOOKS AT, not something
hidden behind a valve. This family makes the visible surface a deep trough:

    a beam enters the mouth, bounces 2-4 times off the trough's diffuse
    interior, travelling of order the trough width between bounces, and leaves
    from a position uncorrelated with where it entered.

Spread scale is the trough width. Escape fraction falls roughly as
rho^(bounces), so a grey interior plus a deep trough gives a dim, wide,
positionless return instead of a very dim, sharp one.

Geometry, constraints unchanged
-------------------------------
Everything is still a Y-Z cross-section extruded along X, still uniform sheet
thickness, still no 90 degree interior corners (a V of depth 1.5 x width has a
37 degree apex, and the apex is rounded to the bend radius anyway), still
irregular pitch so the mouths do not form a periodic grating.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from profile2d import (                                            # noqa: F401
    Pt, fillet_polyline, thicken, _lcg, CrossSection,
)


@dataclass
class ScatterParams:
    # --- envelope (mm) ---
    face_w: float = 500.0
    face_h: float = 500.0
    depth: float = 100.0            # total panel depth available

    # --- sheet ---
    thickness: float = 1.0
    min_inner_radius: float = 1.5

    # --- trough ---
    width_mean: float = 80.0        # mouth width in Z; this sets the smear
    width_jitter: float = 0.25
    width_seed: int = 3
    # Troughs generated this many depths past the face on each side. Without
    # it a camera tilted to theta looking at depth D travels D/tan(90-theta)
    # in Z before reaching the floor and runs off the end of the panel, reading
    # world background as if it were geometry. `profile_ridge` found and fixed
    # exactly this ("an impossible 27% at theta = 80") and the fix was never
    # carried across to this module or to profile2d, so the trough and slat
    # families have never been measurable at all. 0.0 reproduces the old
    # behaviour for the picture paths; any measurement must set it.
    margin_depths: float = 0.0

    def span(self) -> float:
        return self.face_h + 2.0 * self.margin_depths * self.depth
    depth_ratio: float = 1.5        # trough depth / mouth width
    shape: str = "vee"              # vee | u | asym
    asym: float = 0.35              # apex offset for shape="asym", -0.5..0.5

    # --- mouth lip ---
    # A short black return at the mouth hides the brightest part of the trough
    # (the shallow part near the entrance, which is only one bounce from the
    # observer) without closing the aperture. Zero disables it.
    lip_len: float = 0.0
    lip_deg: float = 60.0

    # --- tessellation ---
    arc_segments: int = 10

    def bend_radius(self) -> float:
        return self.min_inner_radius + self.thickness / 2.0

    def trough_depth(self) -> float:
        return self.width_mean * self.depth_ratio

    def apex_angle_deg(self) -> float:
        """Interior angle at the bottom of a V. 90 would retroreflect."""
        return 2.0 * math.degrees(math.atan(0.5 / max(self.depth_ratio, 1e-9)))

    def wall_len(self) -> float:
        """One trough wall, mouth to apex."""
        w = self.width_mean / 2.0
        return math.hypot(w, self.trough_depth())

    def aperture_fraction(self) -> float:
        """Mouth divided by mouth plus interior perimeter, per cell."""
        mouth = max(self.width_mean - 2.0 * self.lip_projection(), 1e-6)
        return mouth / (mouth + 2.0 * self.wall_len())

    def lip_projection(self) -> float:
        return self.lip_len * math.cos(math.radians(self.lip_deg))

    def est_bounces(self) -> float:
        """
        Rough count of wall hits before escape, from the aperture fraction:
        a cavity that leaks a fraction f per hit empties after about 1/f hits.
        Only an order-of-magnitude guide -- the render is the measurement.
        """
        return 1.0 / max(self.aperture_fraction(), 1e-9)


def width_sequence(p: ScatterParams) -> list[float]:
    """Irregular but exactly space-filling trough widths."""
    span = p.span()
    n = max(2, int(round(span / p.width_mean)))
    if p.width_jitter <= 0.0:
        return [span / n] * n
    rng = _lcg(p.width_seed)
    raw = [1.0 + p.width_jitter * (2.0 * next(rng) - 1.0) for _ in range(n)]
    s = sum(raw)
    return [r / s * span for r in raw]


def trough_centerline(p: ScatterParams, z_top: float, w: float) -> list[Pt]:
    """
    One trough, traced from its top mouth edge down to its bottom mouth edge.

    vee   straight walls to a rounded apex
    u     circular arc, so there is no apex at all
    asym  apex pushed off centre, which stops the two walls being mirror
          images and removes the symmetric escape path straight back out
    """
    d = p.depth_ratio * w
    z_bot = z_top - w
    if p.shape == "u":
        # half ellipse: half-width w/2 in Z, depth d in Y, so there is no apex
        # for a ray to bounce straight back out of
        zc = (z_top + z_bot) / 2.0
        r = w / 2.0
        n = max(8, p.arc_segments * 2)
        return [(-d * math.cos(math.pi / 2 - math.pi * k / n),
                 zc + r * math.sin(math.pi / 2 - math.pi * k / n))
                for k in range(n + 1)]
    off = p.asym if p.shape == "asym" else 0.0
    apex_z = (z_top + z_bot) / 2.0 - off * w
    return [(0.0, z_top), (-d, apex_z), (0.0, z_bot)]


def lip_centerlines(p: ScatterParams, z_top: float, w: float) -> list[list[Pt]]:
    """Short returns at both mouth edges, angled into the trough."""
    if p.lip_len <= 0.0:
        return []
    a = math.radians(p.lip_deg)
    din = (-math.cos(a), -math.sin(a))
    dup = (-math.cos(a), math.sin(a))
    return [
        [(0.0, z_top), (din[0] * p.lip_len, z_top + din[1] * p.lip_len)],
        [(0.0, z_top - w), (dup[0] * p.lip_len, z_top - w + dup[1] * p.lip_len)],
    ]


def shell_centerline(p: ScatterParams) -> list[Pt]:
    """Back box behind the troughs, with the two rear corners chamfered."""
    d = p.trough_depth() + 8.0
    z_hi, z_lo = p.span() / 2.0 + 10.0, -p.span() / 2.0 - 10.0
    ch = 25.0
    return [(0.0, z_hi), (-(d - ch), z_hi), (-d, z_hi - ch),
            (-d, z_lo + ch), (-(d - ch), z_lo), (0.0, z_lo)]


def build_cross_section(p: ScatterParams) -> CrossSection:
    """
    stage1 carries the mouth lips (the surfaces one bounce from the observer,
    so the ones that want the blackest finish); stage2 carries the trough
    walls, whose finish is the variable this family exists to sweep.
    """
    cs = CrossSection()
    R = p.bend_radius()

    if abs(p.apex_angle_deg() - 90.0) < 12.0:
        cs.warnings.append(
            f"apex angle {p.apex_angle_deg():.0f} deg is near 90; a right-angle "
            "trough acts as a corner cube and returns light to the source")

    if p.trough_depth() + 10.0 > p.depth:
        cs.warnings.append(
            f"trough depth {p.trough_depth():.0f} mm exceeds the {p.depth:.0f} mm "
            "panel depth budget")

    z = p.span() / 2.0
    for w in width_sequence(p):
        cl = trough_centerline(p, z, w)
        cl = fillet_polyline(cl, max(R, 0.06 * w), p.arc_segments)
        cs.stage2.append(thicken(cl, p.thickness))
        for lp in lip_centerlines(p, z, w):
            cs.stage1.append(thicken(lp, p.thickness, round_ends=True))
        z -= w

    shell = fillet_polyline(shell_centerline(p), R, p.arc_segments)
    cs.shell.append(thicken(shell, p.thickness))
    return cs


def describe(p: ScatterParams) -> dict:
    return {
        "family": "scatter",
        "depth_mm": p.depth,
        "width_mean_mm": p.width_mean,
        "width_jitter": p.width_jitter,
        "depth_ratio": p.depth_ratio,
        "trough_depth_mm": p.trough_depth(),
        "shape": p.shape,
        "asym": p.asym,
        "apex_angle_deg": p.apex_angle_deg(),
        "wall_len_mm": p.wall_len(),
        "aperture_fraction": p.aperture_fraction(),
        "est_bounces": p.est_bounces(),
        "lip_len_mm": p.lip_len,
        "lip_deg": p.lip_deg,
        "thickness_mm": p.thickness,
        "bend_radius_center_mm": p.bend_radius(),
    }


if __name__ == "__main__":
    import json
    for dr in (0.75, 1.5, 2.5):
        prm = ScatterParams(depth_ratio=dr, depth=400.0)
        cs = build_cross_section(prm)
        d = describe(prm)
        print("d/w=%.2f  trough %5.1f mm  apex %5.1f deg  f=%.4f  "
              "~bounces %4.1f  troughs=%d  warn=%d"
              % (dr, d["trough_depth_mm"], d["apex_angle_deg"],
                 d["aperture_fraction"], d["est_bounces"], len(cs.stage2),
                 len(cs.warnings)))
