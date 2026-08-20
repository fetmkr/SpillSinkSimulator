"""What the audience actually sees, named in the units people use.

THE TOP-LINE QUESTION IS NOT rho_dh. rho_dh is the fraction of an arriving beam
that leaves again in ANY direction -- a hemispherical total, useful for ranking
absorbers and meaningless as a description of how bright the ceiling looks. The
client's question is how visible the spill copy is to a person standing under
it, and that is a directional quantity.

THREE NAMES FOR IT, all the same measurement.

    BRDF                f_r(theta_in, theta_out)          [1/sr]
        what `bidir.py` measures, absolute, against the Lambertian control.

    RADIANCE FACTOR     beta = pi * f_r                    [dimensionless]
        the CIE reflectance factor: this surface's radiance divided by that of
        a PERFECT LAMBERTIAN WHITE under identical illumination. beta = 1 is
        the white standard. This is the number to quote to a scientist, and it
        is the one that survives being compared with anyone else's goniometer.

    x WHITE PAPER       beta / BETA_PAPER                  [dimensionless]
        the same number for everyone else. Office paper is 75-85 % reflective
        and near-Lambertian, so beta ~ 0.80. "One eightieth of a sheet of paper
        held in the same place" is a sentence a client can check by holding up
        a sheet of paper.

THREE ANGLES, NOT TWO, AND THAT WAS THE BUG. A room lights a point from every
azimuth at once. The first version of this file keyed cells on
(theta_in, theta_out) and threw the azimuth away, so `measure_audience` sampled
every cell on the RETRO side of the map -- the side a honeycomb is brightest on.
Measured share of the light an eye actually receives, by the azimuth between the
source and the eye:

    dphi      0     30    60    90    120   150   180
    share   6.2%  9.7%  8.6% 11.0% 19.1% 27.8% 17.7%

24.5 % near retro, 64.5 % near specular, and the MODE at 150 deg, which an
in-plane rig cannot reach at all. The published beta = 0.0037 was wrong for
that reason. See `results/FINDINGS_audience_azimuth_2026_08_21.md`.

WEIGHTED BY THE ROOM, NOT BY A CONVENTION. A cell of the map only counts for as
much light as the room actually puts through it. Each projector paints its scan
field with uniform power per unit solid angle -- a scanner spends equal time per
unit scan angle -- so a ceiling patch subtending dOmega receives power
proportional to dOmega, and its irradiance goes as cos(theta_in)/distance^2.
The weight of a cell is that irradiance summed over every projector, every part
of the scan field, and every place a person is allowed to stand.

Measured that way, 17 cells carry 90 % of what reaches an eye, and they sit at
theta_in 20-60 and theta_out 10-50 -- NOT at normal incidence, and not on the
retro ridge. See `report_geometry.py` for the room itself.

TWO NUMBERS, because they answer different questions:
    mean   how bright the ceiling looks           -- the wash
    peak   the brightest patch anyone can see     -- the glare
"""

from __future__ import annotations

import math
from collections import defaultdict

import report_geometry as RG

# Perfect Lambertian white is 1.0 by definition. Office paper measures 75-85 %
# and is close to Lambertian; 0.80 is the middle of that and is quoted as an
# approximation, never as a measurement of anyone's actual paper.
BETA_PAPER = 0.80

N_PROJ = 16
N_SCAN = 21
N_OBS_AZ = 12
OBS_R = (0.0, 0.75, RG.AUD_R)


def cells(step=10.0, phi_step=45.0):
    """{(theta_in, theta_out, delta_phi): weight} -- normalised to sum 1.

    `delta_phi` is the azimuth between the direction back to the projector and
    the direction to the eye, measured at the ceiling point. 0 is retro, 180 is
    specular, and the room puts most of its light in between.

    The weight is irradiance-at-the-patch, so it already carries cos(theta_in)
    and the inverse square. What it does NOT carry is the panel's response;
    that is the thing being measured.
    """
    rise = RG.CEIL_H - RG.EYE_H
    W = defaultdict(float)
    for k in range(N_PROJ):
        pa = 2 * math.pi * k / N_PROJ
        px, py = RG.RING_R * math.cos(pa), RG.RING_R * math.sin(pa)
        az0 = math.atan2(-py, -px)
        for i in range(N_SCAN):
            for j in range(N_SCAN):
                u = math.radians(-RG.SCAN + 2 * RG.SCAN * i / (N_SCAN - 1))
                v = math.radians(-RG.SCAN + 2 * RG.SCAN * j / (N_SCAN - 1))
                el = math.asin(math.cos(u) *
                               math.sin(math.radians(RG.AIM_EL) + v))
                if el <= 1e-6:
                    continue
                az = az0 + u
                d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                     math.sin(el))
                t = rise / d[2]
                cx, cy = px + d[0] * t, py + d[1] * t
                th_in = 90.0 - math.degrees(el)
                E = math.cos(math.radians(th_in)) / (t * t)
                bx, by = px - cx, py - cy        # back toward the projector
                for ok in range(N_OBS_AZ):
                    oa = 2 * math.pi * ok / N_OBS_AZ
                    for ro in OBS_R:
                        ex = ro * math.cos(oa) - cx  # toward the eye
                        ey = ro * math.sin(oa) - cy
                        dh = math.hypot(ex, ey)
                        th_out = math.degrees(math.atan2(dh, rise))
                        nb, ne = math.hypot(bx, by), dh
                        if nb < 1e-9 or ne < 1e-9:
                            dphi = 0.0       # straight down: azimuth is moot
                        else:
                            c = (bx * ex + by * ey) / (nb * ne)
                            dphi = math.degrees(
                                math.acos(max(-1.0, min(1.0, c))))
                        W[(round(th_in / step) * step,
                           round(th_out / step) * step,
                           round(dphi / phi_step) * phi_step)] += E
    tot = sum(W.values())
    return {k: v / tot for k, v in W.items()}


def axes(step=10.0, phi_step=45.0):
    w = cells(step, phi_step)
    return (sorted({a for a, _b, _p in w}), sorted({b for _a, b, _p in w}),
            sorted({p for _a, _b, p in w}))


def score(brdf, step=10.0, phi_step=45.0):
    """(mean beta, peak beta, coverage) from {(in,out,dphi): f_r in 1/sr}.

    `coverage` is the share of the room's weight that the supplied cells
    actually cover -- a mean over 60 % of the light is not a mean, and the
    caller is told rather than left to assume.
    """
    w = cells(step, phi_step)
    num = den = 0.0
    peak = 0.0
    for k, wt in w.items():
        f = brdf.get(k)
        if f is None:
            continue
        num += wt * math.pi * f
        den += wt
        if wt > 0:
            peak = max(peak, math.pi * f)
    if den <= 0:
        return float("nan"), float("nan"), 0.0
    return num / den, peak, den


def as_paper(beta):
    return beta / BETA_PAPER
