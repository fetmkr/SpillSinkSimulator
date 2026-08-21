"""Invert a published TIS measurement into our GGX roughness.

Nobody publishes "roughness" for black paint. Two groups do publish something
that pins it down anyway:

  Filip & Vavra 2026 (arXiv 2601.05094, Fig. 6) report TIS with a 5 deg
  half-angle specular exclusion cone, per material, as a function of
  illumination angle. TIS is the share of reflected energy that lands OUTSIDE
  that cone, so 1 - TIS is the share that lands INSIDE it.

Our coating is Lambert + GGX mixed by Fresnel (blender_render.coating_split):
at normal incidence the diffuse leg carries df * rho0 and the glossy leg
carries (1 - df) * rho0. So the share inside a cone of half-angle tc is

    inside(df, alpha) = df * sin^2(tc)  +  (1 - df) * g(alpha, tc)

  - Lambert: the cosine-weighted share within polar angle tc is sin^2(tc).
  - GGX at normal incidence: an outgoing ray at polar angle to comes from a
    microfacet normal at to/2, and the cumulative of the cosine-weighted GGX
    normal distribution out to angle tm is tan^2(tm) / (alpha^2 + tan^2(tm)).
    Smith masking is dropped; at normal incidence and small alpha it is ~1.

Given a measured TIS we solve for alpha. This is not fitting our model to a
foreign sample -- Filip & Vavra measured matte acrylic black spray on
aluminium and Musou paint, which are the two coatings this rig actually uses.

Run:  python3 scripts/gate_roughness_from_tis.py
"""

import math
import sys

CONE_HALF_DEG = 5.0                      # Filip & Vavra 2026, section 3.4


def lambert_inside(tc_deg):
    return math.sin(math.radians(tc_deg)) ** 2


def ggx_inside(alpha, tc_deg):
    """Share of a GGX lobe landing within `tc_deg` of the mirror direction."""
    if alpha <= 0.0:
        return 1.0
    t = math.tan(math.radians(tc_deg) / 2.0)     # microfacet angle = half of it
    return t * t / (alpha * alpha + t * t)


def inside_cone(df, alpha, tc_deg=CONE_HALF_DEG):
    return df * lambert_inside(tc_deg) + (1.0 - df) * ggx_inside(alpha, tc_deg)


def solve_alpha(df, tis, tc_deg=CONE_HALF_DEG):
    """Roughness reproducing this TIS, or None if no roughness can."""
    target = 1.0 - tis
    floor = inside_cone(df, 10.0, tc_deg)        # roughest: lobe is all spread
    ceil_ = inside_cone(df, 1e-6, tc_deg)        # smoothest: a mirror
    if target <= floor or target >= ceil_:
        return None
    lo, hi = 1e-6, 10.0
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if inside_cone(df, mid, tc_deg) > target:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


# What Fig. 6 shows at normal incidence. Read off the plot, so a range.
MEASURED = [
    ("acryl paint    (matte acrylic black spray on aluminium)", 0.87, 0.90),
    ("chalkboard paint", 0.96, 0.98),
    ("Musou paint", 0.985, 0.995),
    ("black velvet", 0.99, 1.00),
    ("Vantablack", 0.97, 0.99),
]

DFS = [0.99, 0.97, 0.95, 0.90, 0.80, 0.70, 0.50, 0.30]


def main():
    tc = CONE_HALF_DEG
    print("5 deg cone. A perfect Lambertian already puts %.4f inside it."
          % lambert_inside(tc))
    print("So TIS can never exceed %.4f for a purely diffuse surface.\n"
          % (1.0 - lambert_inside(tc)))

    print("check: share inside the cone, by roughness, at df = 0.97")
    for a in (0.02, 0.05, 0.10, 0.20, 0.30, 0.45, 0.60):
        print("   roughness %.2f -> inside %.5f   TIS %.4f"
              % (a, inside_cone(0.97, a), 1.0 - inside_cone(0.97, a)))
    print()

    holes = 0
    for label, tis_lo, tis_hi in MEASURED:
        print(label)
        print("   measured TIS %.3f - %.3f  ->  inside cone %.3f - %.3f"
              % (tis_lo, tis_hi, 1.0 - tis_hi, 1.0 - tis_lo))
        any_row = False
        for df in DFS:
            a_hi = solve_alpha(df, tis_lo)       # more inside -> sharper lobe
            a_lo = solve_alpha(df, tis_hi)
            if a_hi is None and a_lo is None:
                continue
            any_row = True
            f = lambda v: ("  --  " if v is None else "%6.3f" % v)
            print("      df %.2f -> roughness %s .. %s" % (df, f(a_lo), f(a_hi)))
        if not any_row:
            print("      no (df, roughness) pair in our model reaches this TIS.")
            print("      that is itself the finding -- our model cannot be that "
                  "diffuse and that specular at once.")
            holes += 1
        print()

    if holes == len(MEASURED):
        print("REFUSING: every material came out empty. The gate learned nothing.")
        return 1
    print("@@DONE@@")
    return 0


if __name__ == "__main__":
    sys.exit(main())
