"""
Y-Z cross-section generator for the optical anechoic wall panel.

Pure Python (no bpy) so profiles can be plotted and sanity-checked in
milliseconds before any render time is spent.

Coordinate system (shared with the Blender build script)
--------------------------------------------------------
    X = extrusion axis. Everything runs along X. Nothing varies along X.
    Y = depth. Panel face at Y = 0, back wall at Y = -D. Light arrives from +Y.
    Z = vertical (up).

Structure
---------
Three separable parts, matching the two-stage role separation:

  stage 1   a shallow front layer of SHORT discrete slats. Deflection only.
            Each slat is a flat strip of length L1 at angle a1. They do not
            reach into the chamber.

  stage 2   ONE shared open chamber behind the slat layer, laterally expanded
            past the slat zone, containing face-parallel baffle plates
            staggered in both depth and Z so no straight path runs from the
            aperture to the back wall.

  shell     the bent-sheet enclosure: top run, back wall, bottom run, with
            chamfers replacing the two back corners so nothing acts as a
            corner cube.

Why the slats are short
-----------------------
An earlier revision ran one continuous fin from the face all the way to the
back. A material-ID render showed the front view was 97.8% stage-1 fin and
0.0% chamber, and consequently the stage1:stage2 depth ratio moved the
measured return by less than 2% across a 0.20-0.65 sweep -- the chamber was
never reached, so its geometry could not matter. Short slats let light through
into the chamber, which is the only way stage 2 can do any work.

Sight-line condition
--------------------
For the slat layer to close off a straight view at normal incidence, the
projected Z extent of one slat must cover the pitch:

    slat_overlap = L1 * |sin(a1)| / pitch  >= 1

`describe()` reports this, and `build_cross_section` warns when it drops below
1, because below that the chamber is visible through gaps and the panel starts
behaving like an open box.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# parameters
# --------------------------------------------------------------------------

@dataclass
class PanelParams:
    # --- panel envelope (mm) ---
    face_w: float = 500.0        # X extent
    face_h: float = 500.0        # Z extent of the slatted face
    depth: float = 100.0         # D, face plane to back wall

    # --- sheet metal (confirmed spec: AL 1.0t, min inner bend R 1.5) ---
    thickness: float = 1.0
    min_inner_radius: float = 1.5

    # --- stage 1: short slats, deflection only ---
    slat_len: float = 30.0       # L1
    slat_deg: float = 45.0       # a1 from horizontal; positive = descends
                                 # as it goes deeper (accepts light from above)
    pitch_mean: float = 20.0
    pitch_jitter: float = 0.25   # 0 = uniform, 0.25 = +/-25%
    pitch_seed: int = 1
    # See profile_scatter.margin_depths -- same defect, same fix. 0.0 keeps the
    # picture paths unchanged; a measurement must set it.
    margin_depths: float = 0.0

    def span(self) -> float:
        return self.face_h + 2.0 * self.margin_depths * self.depth
    slat_recess: float = 0.0     # how far behind the face plane the tips sit
    slat_deg_jitter: float = 0.0
    # Irregular pitch converts a regular stripe pattern into noise. This is the
    # angular version of the same principle, and it exists because the form
    # test found the specular slats returning 417x a flat plate toward a front
    # observer at one specific incidence while returning 1e-4 everywhere else.
    # A single slat angle means the whole panel glints coherently at one angle;
    # spreading the angles spreads that glint over incidence instead, so a
    # scanning beam never lights the whole face at once.
    slat_mode: str = "straight"  # straight | alternate | vee
    # A one-way tilt makes the panel one-way: every straight-slat case measured
    # so far returns ~1.0 for light arriving from below, because the slats
    # present their backs to it. "alternate" flips the tilt slat by slat and
    # "vee" bends each slat into a chevron, so both signs of incidence meet a
    # forward-facing surface. Both stay single-thickness bent sheet.

    # --- stage 2: shared chamber ---
    flare: float = 20.0          # lateral expansion past the slat zone,
                                 # applied at top and bottom
    flare_ramp: float = 25.0     # depth over which the flare opens; a ramp
                                 # rather than a step keeps the joint obtuse
    chamfer: float = 30.0        # corner removal at the two back corners

    # --- baffle plates in the chamber ---
    baffle_rows: int = 2         # depth stations
    baffle_pitch: float = 60.0   # Z spacing within a row
    baffle_len: float = 50.0     # plate length; at 45 deg tilt this covers
                                 # 35.4 mm of Z, enough to close a 60 mm pitch
    baffle_deg: float = 45.0     # tilt from face-parallel
    baffle_alternate: bool = False   # flip the tilt sign row by row
    baffle_seed: int = 7

    # --- back wall profile ---
    back_profile: str = "flat"   # flat | wedge | cyl
    back_amp: float = 15.0
    back_period: float = 60.0
    back_convex: bool = True     # ridges toward the viewer: spreads, does not
                                 # retroreflect the way a concave V would

    # --- tessellation ---
    arc_segments: int = 8

    # ---- derived ----------------------------------------------------------

    def bend_radius(self) -> float:
        """Centerline radius that yields the specified minimum INNER radius."""
        return self.min_inner_radius + self.thickness / 2.0

    def slat_zone_depth(self) -> float:
        return abs(self.slat_len * math.cos(math.radians(self.slat_deg))) + self.slat_recess

    def chamber_depth(self) -> float:
        return self.depth - self.slat_zone_depth()

    def slat_overlap(self) -> float:
        """
        Projected Z coverage of one slat divided by the pitch.

        A chevron folds back on itself, so it covers only half the Z span a
        straight slat of the same length would.
        """
        span = abs(self.slat_len * math.sin(math.radians(self.slat_deg)))
        if self.slat_mode == "vee":
            span *= 0.5
        return span / max(self.pitch_mean, 1e-9)

    def open_face_fraction(self) -> float:
        """
        Fraction of the face plane not blocked by slat edges, viewed normally.
        Only the slat thickness blocks; overlap closes the sight line without
        closing the aperture, which is what lets the face stay open while the
        trapping is done with depth.
        """
        return max(0.0, 1.0 - self.thickness / self.pitch_mean)

    def chamber_aperture_fraction(self) -> float:
        """
        Blackbody-cavity f for the chamber alone: chamber mouth divided by
        total chamber wall length, in the 2D cross-section. Lower is better,
        and this is what `flare` and the baffles are for.
        """
        mouth = self.face_h
        cd = self.chamber_depth()
        walls = 2.0 * cd + (self.face_h + 2.0 * self.flare) + 4.0 * self.flare
        walls += self.baffle_wall_len()
        return mouth / max(mouth + walls, 1e-9)

    def baffle_wall_len(self) -> float:
        n = self.baffle_count()
        return 2.0 * n * self.baffle_len

    def baffle_count(self) -> int:
        if self.baffle_rows <= 0 or self.baffle_pitch <= 0:
            return 0
        per_row = int(self.face_h // self.baffle_pitch)
        return self.baffle_rows * max(per_row, 0)

    def baffle_z_cover(self) -> float:
        """Z extent one tilted plate actually blocks."""
        return self.baffle_len * abs(math.cos(math.radians(self.baffle_deg)))

    def baffle_closure(self) -> float:
        """
        Two rows staggered by half a pitch close every sight line when each
        plate covers at least half the pitch. This is that margin; >= 1 closes.
        """
        if self.baffle_rows < 2 or self.baffle_pitch <= 0:
            return 0.0
        return self.baffle_z_cover() / (0.5 * self.baffle_pitch)


# --------------------------------------------------------------------------
# deterministic pseudo-random
# --------------------------------------------------------------------------

def _lcg(seed: int):
    """Small deterministic PRNG, reproducible across machines and versions."""
    state = (seed * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
    while True:
        state = (state * 6364136223846793005 + 1442695040888963407) & ((1 << 64) - 1)
        yield ((state >> 33) & 0x7FFFFFFF) / float(0x7FFFFFFF)


def pitch_sequence(p: PanelParams) -> list[float]:
    """
    Irregular but exactly space-filling pitches covering face_h.

    This is a fixed panel, not a working blind, so slot positions are free.
    Irregular spacing turns a regular stripe pattern into noise the eye reads
    as texture -- but it must still tile the panel height exactly.
    """
    n = max(2, int(round(p.span() / p.pitch_mean)))
    if p.pitch_jitter <= 0.0:
        return [p.span() / n] * n
    rng = _lcg(p.pitch_seed)
    raw = [1.0 + p.pitch_jitter * (2.0 * next(rng) - 1.0) for _ in range(n)]
    s = sum(raw)
    return [r / s * p.span() for r in raw]


# --------------------------------------------------------------------------
# polyline helpers
# --------------------------------------------------------------------------

Pt = tuple[float, float]


def fillet_polyline(pts: list[Pt], radius: float, segments: int) -> list[Pt]:
    """
    Replace every interior corner with a tangent circular arc of `radius`.

    The radius is clamped per-corner to what the adjacent segments can
    accommodate, so a short segment degrades gracefully instead of producing
    a self-intersecting loop.
    """
    if len(pts) < 3 or radius <= 0.0:
        return list(pts)

    out: list[Pt] = [pts[0]]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v0 = (p0[0] - p1[0], p0[1] - p1[1])
        v1 = (p2[0] - p1[0], p2[1] - p1[1])
        l0 = math.hypot(*v0)
        l1 = math.hypot(*v1)
        if l0 < 1e-9 or l1 < 1e-9:
            continue
        u0 = (v0[0] / l0, v0[1] / l0)
        u1 = (v1[0] / l1, v1[1] / l1)
        cosang = max(-1.0, min(1.0, u0[0] * u1[0] + u0[1] * u1[1]))
        ang = math.acos(cosang)
        if ang > math.pi - 1e-6 or ang < 1e-6:
            out.append(p1)
            continue
        tan_d = radius / math.tan(ang / 2.0)
        tan_d = min(tan_d, 0.48 * l0, 0.48 * l1)
        r_eff = tan_d * math.tan(ang / 2.0)
        t0 = (p1[0] + u0[0] * tan_d, p1[1] + u0[1] * tan_d)
        t1 = (p1[0] + u1[0] * tan_d, p1[1] + u1[1] * tan_d)
        bis = (u0[0] + u1[0], u0[1] + u1[1])
        bl = math.hypot(*bis)
        if bl < 1e-9:
            out.append(p1)
            continue
        bis = (bis[0] / bl, bis[1] / bl)
        cdist = r_eff / math.sin(ang / 2.0)
        c = (p1[0] + bis[0] * cdist, p1[1] + bis[1] * cdist)
        a0 = math.atan2(t0[1] - c[1], t0[0] - c[0])
        a1 = math.atan2(t1[1] - c[1], t1[0] - c[0])
        da = a1 - a0
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        for k in range(segments + 1):
            a = a0 + da * k / segments
            out.append((c[0] + r_eff * math.cos(a), c[1] + r_eff * math.sin(a)))
    out.append(pts[-1])
    return out


def _vertex_normals(pts: list[Pt]) -> list[Pt]:
    """Averaged left-hand normals, miter-scaled so offset distance is uniform."""
    n = len(pts)
    seg_n: list[Pt] = []
    for i in range(n - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        l = math.hypot(dx, dy) or 1.0
        seg_n.append((-dy / l, dx / l))
    out: list[Pt] = []
    for i in range(n):
        if i == 0:
            nx, ny = seg_n[0]
        elif i == n - 1:
            nx, ny = seg_n[-1]
        else:
            ax, ay = seg_n[i - 1]
            bx, by = seg_n[i]
            nx, ny = ax + bx, ay + by
            l = math.hypot(nx, ny)
            if l < 1e-9:
                nx, ny = bx, by
            else:
                nx, ny = nx / l, ny / l
                cosh_ = nx * bx + ny * by
                if cosh_ > 1e-6:
                    nx, ny = nx / cosh_, ny / cosh_
        out.append((nx, ny))
    return out


def thicken(pts: list[Pt], t: float, round_ends: bool = False,
            cap_segments: int = 6) -> list[Pt]:
    """Turn an open centerline polyline into a closed constant-thickness loop."""
    nrm = _vertex_normals(pts)
    h = t / 2.0
    left = [(p[0] + n[0] * h, p[1] + n[1] * h) for p, n in zip(pts, nrm)]
    right = [(p[0] - n[0] * h, p[1] - n[1] * h) for p, n in zip(pts, nrm)]

    loop: list[Pt] = list(left)
    if round_ends:
        loop += _cap_arc(pts[-1], left[-1], right[-1], cap_segments)
    loop += list(reversed(right))
    if round_ends:
        loop += _cap_arc(pts[0], right[0], left[0], cap_segments)
    return loop


def _cap_arc(centre: Pt, a: Pt, b: Pt, segments: int) -> list[Pt]:
    r = math.hypot(a[0] - centre[0], a[1] - centre[1])
    a0 = math.atan2(a[1] - centre[1], a[0] - centre[0])
    a1 = math.atan2(b[1] - centre[1], b[0] - centre[0])
    da = a1 - a0
    while da > math.pi:
        da -= 2 * math.pi
    while da < -math.pi:
        da += 2 * math.pi
    return [(centre[0] + r * math.cos(a0 + da * k / segments),
             centre[1] + r * math.sin(a0 + da * k / segments))
            for k in range(1, segments)]


# --------------------------------------------------------------------------
# part builders
# --------------------------------------------------------------------------

def slat_centerlines(p: PanelParams) -> list[list[Pt]]:
    """
    Short deflection slats at irregular pitch, tips near the face plane.

    A slat is one straight strip; in production these are tabs bent off a
    carrier strip or slotted into the side rails, both of which keep uniform
    thickness and need no inaccessible inward folds.
    """
    z_hi = p.span() / 2.0
    out = []
    z = z_hi
    jrng = _lcg(p.pitch_seed * 31 + 5)
    for i, h in enumerate(_tile_pitches(p)):
        jit = (2.0 * next(jrng) - 1.0) * p.slat_deg_jitter
        a = math.radians(p.slat_deg + jit)
        tip = (-p.slat_recess, z)
        if p.slat_mode == "vee":
            # chevron: half the length descending, half rising, so a surface
            # faces light from above AND from below
            half = p.slat_len / 2.0
            d1 = (-math.cos(a), -math.sin(a))
            d2 = (-math.cos(a), +math.sin(a))
            knee = (tip[0] + d1[0] * half, tip[1] + d1[1] * half)
            tail = (knee[0] + d2[0] * half, knee[1] + d2[1] * half)
            out.append([tip, knee, tail])
        else:
            sign = -1.0 if (p.slat_mode == "alternate" and i % 2) else 1.0
            d = (-math.cos(a), -math.sin(a) * sign)
            tail = (tip[0] + d[0] * p.slat_len, tip[1] + d[1] * p.slat_len)
            out.append([tip, tail])
        z -= h
    return out


def _tile_pitches(p: PanelParams) -> list[float]:
    """Pitches covering the face, repeated as needed."""
    seq = pitch_sequence(p)
    out, total = [], 0.0
    i = 0
    while total < p.span() - 1e-9:
        h = seq[i % len(seq)]
        out.append(h)
        total += h
        i += 1
    return out


def shell_centerline(p: PanelParams) -> list[Pt]:
    """
    The bent-sheet enclosure, traced from the top front edge around to the
    bottom front edge.

    Top run -> flare ramp -> chamber roof -> back chamfer -> back wall ->
    back chamfer -> chamber floor -> flare ramp -> bottom run.

    The chamfers exist because a 90 degree interior corner acts as a corner
    cube and retroreflects toward the source; every corner here is obtuse.
    """
    z_hi = p.span() / 2.0
    z_lo = -z_hi
    d0 = p.slat_zone_depth()
    D = p.depth
    fl = p.flare
    ch = p.chamfer
    ramp = p.flare_ramp

    zt = z_hi + fl
    zb = z_lo - fl

    top = [
        (0.0, z_hi),
        (-d0, z_hi),
        (-d0 - ramp, zt),
    ]
    bottom = [
        (-d0 - ramp, zb),
        (-d0, z_lo),
        (0.0, z_lo),
    ]

    back = list(back_wall_centerline(p, zt - ch, zb + ch))

    pts = top + [(-(D - ch), zt)] + back + [(-(D - ch), zb)] + bottom
    return pts


def back_wall_centerline(p: PanelParams, z_top: float, z_bot: float) -> list[Pt]:
    """
    Back wall profile between the two chamfers, traced top to bottom.

    flat  : a plane at y = -depth
    wedge : triangular ridges; convex ones point toward the viewer and split
            light sideways instead of retroreflecting it
    cyl   : sinusoidal corrugation
    """
    y0 = -p.depth
    if p.back_profile == "flat":
        return [(y0, z_top), (y0, z_bot)]

    sign = 1.0 if p.back_convex else -1.0
    span = z_top - z_bot
    n = max(1, int(round(span / p.back_period)))
    per = span / n
    pts: list[Pt] = []
    if p.back_profile == "wedge":
        for k in range(n + 1):
            z = z_top - per * k
            pts.append((y0, z))
            if k < n:
                pts.append((y0 + sign * p.back_amp, z - per / 2.0))
    elif p.back_profile == "cyl":
        steps = n * 16
        for k in range(steps + 1):
            z = z_top - span * k / steps
            y = y0 + sign * p.back_amp * 0.5 * (
                1.0 - math.cos(2 * math.pi * k / (steps / n)))
            pts.append((y, z))
    else:
        raise ValueError(f"unknown back_profile {p.back_profile!r}")
    return pts


def baffle_centerlines(p: PanelParams, report: list | None = None) -> list[list[Pt]]:
    """
    Plates standing in the chamber, staggered in depth and in Z so no straight
    path runs from the aperture to the back wall.

    They must NOT be left face-parallel. At baffle_deg = 0 the plate normal
    points straight at the aperture, so a diffuse plate centres its cosine
    lobe on the exit and a specular one retroreflects outright -- the plate
    becomes the brightest thing in the chamber. Tilting swings the lobe off
    the exit direction by twice the tilt, which is why baffle_deg defaults to
    45 and is swept rather than assumed.

    Rows alternate their Z phase by half a pitch; within a row the positions
    carry a small deterministic jitter, for the same reason the slat pitch is
    irregular.
    """
    if p.baffle_rows <= 0 or p.baffle_len <= 0 or p.baffle_pitch <= 0:
        return []

    d0 = p.slat_zone_depth()
    D = p.depth
    # the chamfers only cut the top and bottom corners, so they must not
    # constrain how far back a mid-height baffle can sit
    margin = max(3.0 * p.thickness, 0.06 * p.chamber_depth())
    usable_front = d0 + margin
    usable_back = D - margin
    if usable_back <= usable_front:
        return []

    rng = _lcg(p.baffle_seed)

    z_hi = p.span() / 2.0 + p.flare
    z_lo = -z_hi
    out = []
    for k in range(p.baffle_rows):
        frac = (k + 1) / (p.baffle_rows + 1)
        y = -(usable_front + (usable_back - usable_front) * frac)
        sign = -1.0 if (p.baffle_alternate and k % 2) else 1.0
        ang = math.radians(p.baffle_deg) * sign
        d = (math.sin(ang), -math.cos(ang))     # face-parallel at ang = 0

        # A tilted plate spans len*|sin(tilt)| in depth. Left unclamped it
        # punches out through the face plane and in through the back wall, so
        # the length is capped by whichever chamber face this row sits nearer.
        half_room = min(abs(y + usable_front), abs(usable_back + y))
        L = p.baffle_len
        s = abs(math.sin(ang))
        if s > 1e-6:
            L = min(L, 2.0 * half_room / s)

        # a tilted plate blocks only L*cos(tilt) in Z -- not its own length
        cover = L * abs(math.cos(ang))
        # jitter stays inside the row-to-row overlap margin, so staggering
        # still closes every path: a hole here is a straight run from the
        # aperture to the back wall
        jmax = max(0.0, 0.5 * (cover - 0.5 * p.baffle_pitch) - 2.0)

        phase = (k % 2) * 0.5 * p.baffle_pitch
        z = z_hi - phase - 0.5 * cover
        while z - 0.5 * cover > z_lo:
            jz = (2.0 * next(rng) - 1.0) * jmax
            # centred on the anchor, so the plate stays inside the chamber
            c = (y, z + jz)
            out.append([(c[0] - d[0] * L / 2.0, c[1] - d[1] * L / 2.0),
                        (c[0] + d[0] * L / 2.0, c[1] + d[1] * L / 2.0)])
            z -= p.baffle_pitch

        if report is not None:
            report.append({"row": k, "y": y, "len": L, "cover": cover,
                           "closure": cover / (0.5 * p.baffle_pitch)})
    return out


# --------------------------------------------------------------------------
# whole cross-section
# --------------------------------------------------------------------------

@dataclass
class CrossSection:
    """Closed 2D loops making up one Y-Z cross-section, tagged by role."""
    stage1: list[list[Pt]] = field(default_factory=list)   # slats, specular
    stage2: list[list[Pt]] = field(default_factory=list)   # baffles, diffuse
    shell: list[list[Pt]] = field(default_factory=list)    # enclosure, diffuse
    warnings: list[str] = field(default_factory=list)
    baffle_rows_report: list = field(default_factory=list)


def build_cross_section(p: PanelParams) -> CrossSection:
    cs = CrossSection()
    R = p.bend_radius()

    if p.min_inner_radius < p.thickness:
        cs.warnings.append(
            f"min inner radius {p.min_inner_radius} < thickness {p.thickness}; "
            "5052 aluminium typically needs R >= 1t")

    if p.chamber_depth() <= 5.0:
        cs.warnings.append(
            f"chamber depth {p.chamber_depth():.1f} mm leaves stage 2 nothing "
            f"to work with (slat zone eats {p.slat_zone_depth():.1f} of "
            f"{p.depth:.1f})")

    if p.baffle_rows > 0 and abs(p.baffle_deg) < 10.0:
        cs.warnings.append(
            f"baffle tilt {p.baffle_deg:.0f} deg is nearly face-parallel; the "
            "plate normal points at the aperture and sends light straight back "
            "out")

    ov = p.slat_overlap()
    if ov < 1.0:
        cs.warnings.append(
            f"slat overlap {ov:.2f} < 1: a straight sight line runs through "
            "the slat layer at normal incidence, so the chamber is exposed")

    R = p.bend_radius()
    for cl in slat_centerlines(p):
        if len(cl) > 2:
            cl = fillet_polyline(cl, R, p.arc_segments)
        cs.stage1.append(thicken(cl, p.thickness, round_ends=True))

    rep: list = []
    for cl in baffle_centerlines(p, report=rep):
        cs.stage2.append(thicken(cl, p.thickness, round_ends=True))
    cs.baffle_rows_report = rep

    if p.baffle_rows >= 2 and rep:
        worst = min(r["closure"] for r in rep)
        if worst < 1.0:
            cs.warnings.append(
                f"baffle closure {worst:.2f} < 1: after depth clamping a plate "
                f"blocks only {min(r['cover'] for r in rep):.1f} mm of Z "
                f"against a {p.baffle_pitch:.0f} mm pitch, leaving straight "
                "paths from the aperture to the back wall")
    if rep and any(r["len"] < p.baffle_len - 0.05 for r in rep):
        cs.warnings.append(
            f"baffle length clamped from {p.baffle_len:.0f} to "
            f"{min(r['len'] for r in rep):.1f} mm to keep the tilted plate "
            "inside the chamber")

    shell = fillet_polyline(shell_centerline(p), R, p.arc_segments)
    cs.shell.append(thicken(shell, p.thickness))

    return cs


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

def describe(p: PanelParams) -> dict:
    return {
        "depth_mm": p.depth,
        "slat_len_mm": p.slat_len,
        "slat_deg": p.slat_deg,
        "slat_mode": p.slat_mode,
        "slat_deg_jitter": p.slat_deg_jitter,
        "slat_zone_depth_mm": p.slat_zone_depth(),
        "chamber_depth_mm": p.chamber_depth(),
        "slat_overlap": p.slat_overlap(),
        "pitch_mean_mm": p.pitch_mean,
        "pitch_jitter": p.pitch_jitter,
        "open_face_fraction": p.open_face_fraction(),
        "chamber_aperture_fraction": p.chamber_aperture_fraction(),
        "flare_mm": p.flare,
        "chamfer_mm": p.chamfer,
        "baffle_rows": p.baffle_rows,
        "baffle_count": p.baffle_count(),
        "baffle_len_mm": p.baffle_len,
        "baffle_pitch_mm": p.baffle_pitch,
        "baffle_deg": p.baffle_deg,
        "baffle_alternate": p.baffle_alternate,
        "baffle_z_cover_mm": p.baffle_z_cover(),
        "baffle_closure": p.baffle_closure(),
        "back_profile": p.back_profile,
        "bend_radius_center_mm": p.bend_radius(),
        "thickness_mm": p.thickness,
    }


if __name__ == "__main__":
    import json
    prm = PanelParams()
    cs = build_cross_section(prm)
    print(json.dumps(describe(prm), indent=2))
    print("slats:", len(cs.stage1), "baffles:", len(cs.stage2),
          "warnings:", cs.warnings)
