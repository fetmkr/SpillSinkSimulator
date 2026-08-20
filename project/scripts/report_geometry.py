"""The installation geometry, and the corner of the angle map it uses.

THESE ARE INPUTS, NOT MEASUREMENTS. A ring of projectors at eye height on a 6 m
circle, aimed inward and up at 45 deg with a +-25 deg square scan field, a
ceiling at 4.5 m carrying the panel, and an audience keeping to about half the
ring radius. Every angle below is arithmetic on those, and the page says so --
the study has never measured a real rig, and this must not be mistaken for one.

WHY IT MATTERS. `principles/00` section C scores darkness at theta = 0/+-20/+-40.
This room delivers 20-70 deg, so 60 % of what it throws at the panel lands
outside the band the panel was selected in. The report quotes both.
"""

from __future__ import annotations

import math

RING_R = 3.0        # projector ring radius, m (6 m circle)
CEIL_H = 4.5        # ceiling, m
EYE_H = 1.6         # projector and eye height, m
AUD_R = 1.5         # audience keeps to about half the ring radius, m
AIM_EL = 45.0       # aim elevation, deg above horizontal
SCAN = 25.0         # square scan field, +- deg in both axes

SCORED = (0.0, 20.0, 40.0)


def facts():
    rise = CEIL_H - EYE_H
    el_hi, el_lo = AIM_EL + SCAN, AIM_EL - SCAN

    def run(e):
        return rise / math.tan(math.radians(e))

    lit_far = run(el_lo) - RING_R
    return {
        "rise": rise,
        "inc_lo": 90.0 - el_hi,          # incidence at the steepest ray
        "inc_hi": 90.0 - el_lo,          # incidence at the shallowest ray
        "inc_mid": 90.0 - AIM_EL,
        "lit_near": RING_R - run(el_hi),
        "lit_far": lit_far,
        "exit_max": math.degrees(math.atan2(lit_far + AUD_R, rise)),
        "retro_r": run(AIM_EL),
        "overhead_gap": AIM_EL,          # how far off retro an overhead view is
    }


def closest_to_retro(n_az=48, n_r=28, n_obs=16):
    """The smallest angle between an audience sight-line and the retro
    direction, over every lit ceiling point, every projector that can light it
    and every place a person is allowed to stand.

    This is the number the overhead case hides: straight up, a listener is a
    full 45 deg off the ridge, but a grazing look at the far rim of the lit
    ceiling is a different matter."""
    rise = CEIL_H - EYE_H
    f = facts()

    def ang(u, v):
        d = sum(a * b for a, b in zip(u, v))
        n = math.sqrt(sum(a * a for a in u)) * math.sqrt(sum(b * b for b in v))
        return math.degrees(math.acos(max(-1.0, min(1.0, d / n))))

    best = (999.0, None)
    for k in range(n_az):
        th = 2 * math.pi * k / n_az
        for i in range(n_r):
            rc = f["lit_far"] * i / (n_r - 1.0)
            cx, cy = rc * math.cos(th), rc * math.sin(th)
            for pk in range(24):
                pa = 2 * math.pi * pk / 24
                to_p = (RING_R * math.cos(pa) - cx,
                        RING_R * math.sin(pa) - cy, -rise)
                inc = ang(to_p, (0.0, 0.0, -1.0))
                if not (f["inc_lo"] - 1e-9 <= inc <= f["inc_hi"] + 1e-9):
                    continue                      # not a ray this rig delivers
                for ok in range(n_obs):
                    oa = 2 * math.pi * ok / n_obs
                    for ro in (0.0, AUD_R * 0.5, AUD_R):
                        to_e = (ro * math.cos(oa) - cx,
                                ro * math.sin(oa) - cy, -rise)
                        sep = ang(to_p, to_e)
                        if sep < best[0]:
                            best = (sep, {"ceiling_r": rc, "incidence": inc,
                                          "observer_r": ro,
                                          "exit": ang(to_e, (0.0, 0.0, -1.0))})
    return best


def fraction_outside_scored(n=5):
    """Share of delivered rays arriving outside |theta| <= 40."""
    f = facts()
    incs = []
    for i in range(n):
        for j in range(n):
            v = -SCAN + 2 * SCAN * i / (n - 1.0)
            u = -SCAN + 2 * SCAN * j / (n - 1.0)
            el = math.degrees(math.asin(
                math.cos(math.radians(u)) *
                math.sin(math.radians(AIM_EL + v))))
            incs.append(90.0 - el)
    return sum(1 for i in incs if i > max(SCORED)) / float(len(incs)), incs


# --------------------------------------------------------------- the figures
def _defs():
    return ('<defs>'
            '<marker id="ar-d" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="5.5" markerHeight="5.5" orient="auto">'
            '<path d="M0 0 L10 5 L0 10 z" fill="var(--dark)"/></marker>'
            '<marker id="ar-p" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="5.5" markerHeight="5.5" orient="auto">'
            '<path d="M0 0 L10 5 L0 10 z" fill="var(--peak)"/></marker>'
            '</defs>')


def fig_section():
    """Where the light arrives, and where it leaves to."""
    g = facts()
    S = 56.0
    cy = 52.0
    fy = cy + CEIL_H * S
    ey = fy - EYE_H * S
    ax = 392.0
    lx = ax - RING_R * S
    dy = ey - cy
    xh = lx + dy / math.tan(math.radians(AIM_EL + SCAN))
    xm = lx + dy / math.tan(math.radians(AIM_EL))
    xl = lx + dy / math.tan(math.radians(AIM_EL - SCAN))
    al, ar = ax - AUD_R * S, ax + AUD_R * S
    p = []
    p.append('<figure class="fig diag"><svg viewBox="0 0 780 356" role="img" '
             'aria-label="Section through the room. Beams leave the projector '
             'ring at 45 degrees plus or minus 25 and strike the ceiling panel '
             'between 20 and 70 degrees from its normal. The retroreflected '
             'return goes back to the projector; the light reaching a '
             'listener under the convergence leaves the panel at about zero '
             'degrees.">')
    p.append(_defs())
    p.append('<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f" '
             'fill="var(--form)" opacity=".12"/>' % (lx, ey, xh, cy, xl, cy))
    p.append('<line x1="34" y1="%.0f" x2="746" y2="%.0f" stroke="currentColor" '
             'stroke-width="3.5"/>' % (cy, cy))
    p.append('<line x1="34" y1="%.0f" x2="746" y2="%.0f" stroke="currentColor" '
             'stroke-width="1.4" opacity=".4"/>' % (fy, fy))
    p.append('<text x="40" y="%.0f" font-size="12.5" fill="currentColor" '
             'opacity=".8">spill sink &#183; ceiling %.1f m</text>'
             % (cy - 11, CEIL_H))
    p.append('<text x="40" y="%.0f" font-size="12" fill="currentColor" '
             'opacity=".5">floor</text>' % (fy + 17))
    for xx, ang in ((xh, 90 - (AIM_EL + SCAN)), (xm, 90 - AIM_EL),
                    (xl, 90 - (AIM_EL - SCAN))):
        p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
                 'stroke="var(--form)" stroke-width="1.7" opacity=".9"/>'
                 % (lx, ey, xx, cy))
        p.append('<text x="%.0f" y="%.0f" font-size="12" fill="var(--form)" '
                 'text-anchor="middle">%.0f&#176;</text>' % (xx, cy - 10, ang))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="currentColor" stroke-dasharray="4 4" opacity=".45"/>'
             % (xm, cy, xm, cy + 66))
    p.append('<text x="%.0f" y="%.0f" font-size="11" fill="currentColor" '
             'opacity=".55">panel normal</text>' % (xm + 7, cy + 62))
    p.append('<rect x="%.0f" y="%.0f" width="20" height="13" rx="2.5" '
             'fill="var(--form)"/>' % (lx - 10, ey - 6.5))
    p.append('<text x="%.0f" y="%.0f" font-size="12" fill="currentColor" '
             'text-anchor="middle" opacity=".8">projector ring</text>'
             % (lx, ey + 27))
    p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
             'text-anchor="middle" opacity=".5">r = %.0f m, h = %.1f m</text>'
             % (lx, ey + 42, RING_R, EYE_H))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="var(--dark)" stroke-width="2.2" marker-end="url(#ar-d)"/>'
             % (xm - 5, cy + 4, lx + 13, ey - 11))
    p.append('<text x="%.0f" y="%.0f" font-size="12.5" fill="var(--dark)" '
             'text-anchor="middle">retro &#8212; back up the beam</text>'
             % ((xm + lx) / 2 - 10, (cy + ey) / 2 - 14))
    # a standing figure, not a block: the block read as a plinth
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="var(--peak)" stroke-width="4" opacity=".55"/>'
             % (al, fy, ar, fy))
    for dx in (-38.0, 0.0, 38.0):
        p.append('<circle cx="%.0f" cy="%.0f" r="5" fill="var(--peak)" '
                 'opacity=".9"/>' % (ax + dx, ey - 2))
        p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
                 'stroke="var(--peak)" stroke-width="3" opacity=".9"/>'
                 % (ax + dx, ey + 4, ax + dx, fy))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="var(--peak)" stroke-width="2.2" marker-end="url(#ar-p)"/>'
             % (xm + 3, cy + 4, ax + 3, ey - 14))
    p.append('<text x="%.0f" y="%.0f" font-size="12.5" fill="var(--peak)">'
             'to the eye &#8212; 0&#176;</text>' % (ax + 16, (cy + ey) / 2))
    p.append('<text x="%.0f" y="%.0f" font-size="12" fill="currentColor" '
             'text-anchor="middle" opacity=".8">audience, r &#8804; %.1f m'
             '</text>' % (ax, fy + 17, AUD_R))
    p.append('</svg><figcaption>The scan field puts light on the panel between '
             '<b>%.0f&#176; and %.0f&#176; from its normal</b> &#8212; never '
             'near normal. Someone under the convergence looks almost straight '
             'up, so what reaches their eye leaves the panel at about 0&#176;, '
             'while the retroreflected return goes back to the projector at '
             '%.0f&#176;. Those two directions are %.0f&#176; apart, which is '
             'the whole reason this works.</figcaption></figure>'
             % (g["inc_lo"], g["inc_hi"], AIM_EL, g["overhead_gap"]))
    return "\n".join(p)


def fig_plan():
    """Who stands where, and where the return lands."""
    g = facts()
    S = 31.0
    cx, cyy = 390.0, 200.0
    p = []
    p.append('<figure class="fig diag"><svg viewBox="0 0 780 404" role="img" '
             'aria-label="Plan view. The lit patch of ceiling reaches about '
             'five metres radius, the projectors sit on a three metre ring '
             'where the retroreflected light returns, and the audience keeps '
             'inside one and a half metres.">')
    p.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="var(--form)" '
             'opacity=".10"/>' % (cx, cyy, g["lit_far"] * S))
    p.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="none" '
             'stroke="var(--form)" stroke-width="1.2" stroke-dasharray="3 3" '
             'opacity=".7"/>' % (cx, cyy, g["lit_far"] * S))
    p.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="none" '
             'stroke="var(--dark)" stroke-width="2"/>' % (cx, cyy, RING_R * S))
    for k in range(12):
        a = 2 * math.pi * k / 12
        p.append('<rect x="%.1f" y="%.1f" width="9" height="9" rx="1.5" '
                 'fill="var(--dark)"/>'
                 % (cx + RING_R * S * math.cos(a) - 4.5,
                    cyy + RING_R * S * math.sin(a) - 4.5))
    p.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="var(--peak)" '
             'opacity=".18"/>' % (cx, cyy, AUD_R * S))
    p.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="none" '
             'stroke="var(--peak)" stroke-width="1.6"/>'
             % (cx, cyy, AUD_R * S))
    p.append('<text x="%.0f" y="%.0f" font-size="12" fill="var(--peak)" '
             'text-anchor="middle">audience</text>' % (cx, cyy + 4))
    p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="var(--dark)" '
             'text-anchor="middle">projectors &#8212; and where the retro '
             'return lands</text>' % (cx, cyy - RING_R * S - 11))
    p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="var(--form)" '
             'text-anchor="middle">lit ceiling, to r &#8776; %.1f m</text>'
             % (cx, cyy + g["lit_far"] * S + 17, g["lit_far"]))
    p.append('</svg><figcaption>Plan. The audience is held inside %.1f m and '
             'the return comes back on the %.0f m ring, so nobody is standing '
             'in it. The exposure that remains is not overhead &#8212; it is a '
             'grazing look outward at the far rim.</figcaption></figure>'
             % (AUD_R, RING_R))
    return "\n".join(p)


def fig_plane(near):
    """The audience plane: which cells of the angle map this room visits.

    Plot on the left, key on the right. Annotating in place put the grazing
    marker's two lines straight through the rotated ridge label, and a narrow
    viewBox beside two 780-wide ones rendered its type half again as large."""
    g = facts()
    x0, y0, L = 132.0, 344.0, 292.0
    sc = L / 80.0
    kx = 486.0

    def X(t):
        return x0 + t * sc

    def Y(t):
        return y0 - t * sc

    ex = near[1]["exit"]
    inc = near[1]["incidence"]
    p = []
    p.append('<figure class="fig diag"><svg viewBox="0 0 780 400" role="img" '
             'aria-label="The angle map with the operating region marked. '
             'Incidence runs 20 to 70 degrees so normal incidence is never '
             'used, the retro ridge is the diagonal, an overhead view sits 45 '
             'degrees below it, and a grazing look at the far rim comes within '
             'about 4 degrees of it.">')
    p.append(_defs())
    p.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" '
             'fill="currentColor" opacity=".07"/>'
             % (X(0), Y(80), X(40) - X(0), Y(0) - Y(80)))
    p.append('<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" '
             'fill="var(--form)" opacity=".17"/>'
             % (X(g["inc_lo"]), Y(g["exit_max"]),
                X(g["inc_hi"]) - X(g["inc_lo"]), Y(0) - Y(g["exit_max"])))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="currentColor" stroke-width="1.4"/>' % (x0, y0, X(82), y0))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="currentColor" stroke-width="1.4"/>' % (x0, y0, x0, Y(82)))
    for t in (0, 20, 40, 60, 80):
        p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
                 'opacity=".6" text-anchor="middle">%d</text>'
                 % (X(t), y0 + 17, t))
        p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
                 'opacity=".6" text-anchor="end">%d</text>'
                 % (x0 - 8, Y(t) + 4, t))
    p.append('<text x="%.0f" y="%.0f" font-size="12" fill="currentColor" '
             'opacity=".75" text-anchor="middle">incidence on the panel '
             '(&#176;)</text>' % ((x0 + X(80)) / 2, y0 + 36))
    p.append('<text transform="translate(%.0f,%.0f) rotate(-90)" '
             'font-size="12" fill="currentColor" opacity=".75" '
             'text-anchor="middle">observation (&#176;)</text>'
             % (x0 - 36, (y0 + Y(80)) / 2))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="var(--dark)" stroke-width="2.4"/>'
             % (X(0), Y(0), X(80), Y(80)))
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="var(--peak)" stroke-width="1.5" stroke-dasharray="4 3" '
             'marker-end="url(#ar-p)"/>'
             % (X(AIM_EL), Y(3), X(AIM_EL), Y(AIM_EL) - 8))
    p.append('<circle cx="%.0f" cy="%.0f" r="5.5" fill="var(--peak)"/>'
             % (X(AIM_EL), Y(0)))
    p.append('<circle cx="%.0f" cy="%.0f" r="6" fill="none" '
             'stroke="var(--no)" stroke-width="2.4"/>' % (X(inc), Y(ex)))

    # ---- key, clear of the plot
    rows = [("currentColor", ".07", "the band the study scores",
             "|&#952;| &#8804; 40&#176;"),
            ("var(--form)", ".17", "what this room delivers",
             "%.0f&#8211;%.0f&#176; incidence" % (g["inc_lo"], g["inc_hi"]))]
    yy = Y(78)
    for col, op, lab, sub in rows:
        p.append('<rect x="%.0f" y="%.0f" width="22" height="13" fill="%s" '
                 'opacity="%s"/>' % (kx, yy - 10, col, op))
        p.append('<rect x="%.0f" y="%.0f" width="22" height="13" fill="none" '
                 'stroke="currentColor" opacity=".25"/>' % (kx, yy - 10))
        p.append('<text x="%.0f" y="%.0f" font-size="12.5" '
                 'fill="currentColor">%s</text>' % (kx + 31, yy, lab))
        p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
                 'opacity=".6">%s</text>' % (kx + 31, yy + 16, sub))
        yy += 44
    p.append('<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" '
             'stroke="var(--dark)" stroke-width="2.4"/>'
             % (kx, yy - 4, kx + 22, yy - 4))
    p.append('<text x="%.0f" y="%.0f" font-size="12.5" fill="var(--dark)">'
             'the retro ridge</text>' % (kx + 31, yy))
    p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
             'opacity=".6">back at the projectors</text>' % (kx + 31, yy + 16))
    yy += 44
    p.append('<circle cx="%.0f" cy="%.0f" r="5.5" fill="var(--peak)"/>'
             % (kx + 11, yy - 4))
    p.append('<text x="%.0f" y="%.0f" font-size="12.5" fill="var(--peak)">'
             'looking straight up</text>' % (kx + 31, yy))
    p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
             'opacity=".6">%.0f&#176; clear of the ridge</text>'
             % (kx + 31, yy + 16, g["overhead_gap"]))
    yy += 44
    p.append('<circle cx="%.0f" cy="%.0f" r="6" fill="none" '
             'stroke="var(--no)" stroke-width="2.4"/>' % (kx + 11, yy - 4))
    p.append('<text x="%.0f" y="%.0f" font-size="12.5" fill="var(--no)">'
             'grazing look at the far rim</text>' % (kx + 31, yy))
    p.append('<text x="%.0f" y="%.0f" font-size="11.5" fill="currentColor" '
             'opacity=".6">only %.0f&#176; off it &#8212; the one exposure'
             '</text>' % (kx + 31, yy + 16, near[0]))
    p.append('</svg><figcaption>The audience plane. Incidence never falls '
             'below %.0f&#176;, so the left third of the map &#8212; including '
             'normal incidence, where this panel is at its very best &#8212; '
             'is never used. Straight up is %.0f&#176; clear of the retro '
             'ridge. The one place a listener can meet the ridge is a grazing '
             'look outward at the far rim of the lit ceiling.'
             '</figcaption></figure>' % (g["inc_lo"], g["overhead_gap"]))
    return "\n".join(p)
