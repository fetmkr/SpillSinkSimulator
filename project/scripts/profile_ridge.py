"""
Third geometry family: deep sharp V-grooves -- the wall-scale version of a
laser beam dump.

Where this comes from
---------------------
Beam-dump practice, not invention. The standard high-performance dump is a
black cone inside a ribbed canister, and the stated reason it works is that
"only the point of the cone is exposed to the beam head-on; mostly, incoming
light grazes the cone at an angle". Optimised traps reach back-reflection
below 0.1%. V-groove cavity theory says the same thing quantitatively:
apparent absorptivity of a collapsing V with specular walls approaches unity,
and V slots beat rectangular slots.

That is exactly the rule the earlier families kept failing: at retro-incidence
the observer sees whatever the beam hits first, and a single bounce can never
displace a photon. A cone has no head-on area to see. A ridge is the extruded
version of a cone tip -- head-on exposure collapses to a line.

Two consequences, both of which the sweep has to confirm:

  the coating requirement collapses. A ray entering parallel to a groove of
  half-angle a takes roughly 90/(2a) bounces before it can leave; at pitch 20
  and depth 100 that is about 8, so even ordinary 5% black paint leaves
  0.05^8 = 4e-11.

  what does come back has bounced many times and travelled laterally, so it is
  position-scrambled for free. Attenuation and form destruction stop fighting
  each other -- they become the same requirement.

What is left is the ridge TIP. It is the only surface with head-on exposure,
so it plays the role the slat lip played before, and the same law should hold:
return ~ 0.63 * (tip width / pitch) * rho. Tip sharpness therefore becomes the
single manufacturing spec that matters, which is why it is the first sweep.

Manufacturing is deliberately unconstrained here -- no bending limit, no
uniform thickness. The geometry is modelled as a solid, not a folded sheet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from profile2d import Pt, _lcg, CrossSection


@dataclass
class RidgeParams:
    # --- envelope (mm) ---
    face_w: float = 500.0
    face_h: float = 500.0
    depth: float = 100.0           # groove depth, ridge tip to valley floor
    backing: float = 10.0          # solid material behind the valley floor

    # --- ridges ---
    pitch_mean: float = 20.0
    pitch_jitter: float = 0.25     # irregular, so a scanning beam meets no
                                   # periodic array and makes no periodic spots
    pitch_seed: int = 11
    tip_width: float = 0.2         # THE lip. head-on exposed width per ridge
    tip_round: bool = True         # rounded tip instead of a flat land
    valley_round: float = 0.5      # radius at the groove floor

    # --- micro serration on the flanks (hierarchical structure) ---
    # Bounce count depends only on pitch/depth, so depth can be traded against
    # pitch one for one -- but the tip fraction (tip width / pitch) then grows
    # in proportion, and the tip is the whole return. Hierarchy is the way out:
    # serrating each flank turns one macro bounce into several micro bounces,
    # so the flank behaves as if its reflectance were rho^k. The macro groove
    # then needs far fewer bounces, hence far less depth. This is the same
    # trick as moth-eye, CNT forests and ultra-black deep-sea fish skin.
    micro_pitch: float = 0.0       # 0 disables; measured along the flank
    micro_depth: float = 0.0       # ABSOLUTE notch depth, not a multiple of
                                   # pitch: the earlier version tied the two
                                   # together and produced 3 mm teeth inside a
                                   # 20 mm groove, which blocked the mouth

    # --- asymmetry ---
    # Tilting the groove axis aims the trap at where the beams actually come
    # from; 0 keeps it normal to the wall.
    tilt_deg: float = 0.0
    tilt_jitter: float = 0.0
    margin_depths: float = 6.5     # ridges generated this many depths past the
                                   # face on each side; see pitch_sequence

    # --- tessellation ---
    arc_segments: int = 6

    # ---- derived ----------------------------------------------------------

    def half_angle_deg(self) -> float:
        """Half the groove opening angle, measured from the groove axis."""
        return math.degrees(math.atan(0.5 * self.pitch_mean / max(self.depth, 1e-9)))

    def est_bounces(self) -> float:
        """
        Reflections before an axial ray can turn around in a 2D wedge of
        half-angle a: it rotates 2a per bounce and needs to pass 90 degrees.
        """
        return 90.0 / max(2.0 * self.half_angle_deg(), 1e-9)

    def tip_fraction(self) -> float:
        """Head-on exposed fraction of the face. This is the whole ball game."""
        return min(1.0, self.tip_width / max(self.pitch_mean, 1e-9))

    def predicted_return(self, rho: float) -> float:
        """
        Lip law carried over from the slat family, which measured
        return/rho = 0.63 * (thickness / pitch) with a 0.003 structural floor.
        Here the floor should be far lower because the groove takes ~8 bounces
        instead of ~2, so it is dropped and the prediction is tip-only.
        """
        return 0.63 * self.tip_fraction() * rho / 0.05


def pitch_sequence(p: RidgeParams) -> list[float]:
    """
    Pitches covering the face PLUS a margin on each side.

    A camera tilted to theta looking at depth D travels D / tan(90 - theta) in
    Z before reaching the valley floor -- 5.7 D at theta = 80. Without ridges
    that far past the measurement window the tilted view runs off the end of
    the panel and reads world background instead of geometry. This was found
    when the 3D family returned an impossible 27% at theta = 80; the same
    defect silently inflated the |theta| >= 50 arm of every 1D sweep before it.
    """
    span = p.face_h + 2.0 * p.margin_depths * p.depth
    n = max(2, int(round(span / p.pitch_mean)))
    if p.pitch_jitter <= 0.0:
        return [span / n] * n
    rng = _lcg(p.pitch_seed)
    raw = [1.0 + p.pitch_jitter * (2.0 * next(rng) - 1.0) for _ in range(n)]
    s = sum(raw)
    return [r / s * span for r in raw]


def _arc(c: Pt, r: float, a0: float, a1: float, n: int) -> list[Pt]:
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n),
             c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def serrate(a: Pt, b: Pt, air: Pt, pitch: float, depth: float,
            taper_frac: float = 0.12) -> list[Pt]:
    """
    Replace the straight flank a->b with V-notches cut INTO the material.

    The first version of this was wrong in three ways that the drawing made
    obvious and the numbers did not: the notch depth was set as a multiple of
    the notch pitch (so 2 mm teeth became 3 mm deep on a groove only 20 mm
    wide), nothing stopped the teeth of adjacent grooves meeting across the
    ridge tip and pinching the mouth shut, and the outward direction was taken
    from a single groove-centroid reference, which points the wrong way over
    part of a long flank.

    Fixed here:
      - `depth` is an absolute notch depth, independent of pitch
      - notches are faded out over the first and last `taper_frac` of the
        flank, so the ridge tip and the valley floor stay clean
      - the outward normal is taken per segment from the flank itself, and the
        teeth only ever cut away from the groove
    """
    dy, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dy, dz)
    if pitch <= 0.0 or depth <= 0.0 or L < 3.0 * pitch:
        return [a, b]
    u = (dy / L, dz / L)
    n = (-u[1], u[0])
    if n[0] * (air[0] - a[0]) + n[1] * (air[1] - a[1]) > 0:
        n = (-n[0], -n[1])

    teeth = max(1, int(L / pitch))
    step = L / teeth
    pts = [a]
    for k in range(teeth):
        s_mid = step * (k + 0.5)
        f = s_mid / L
        # taper the teeth to zero at both ends of the flank
        w = min(1.0, f / taper_frac, (1.0 - f) / taper_frac)
        if w <= 0.0:
            pts.append((a[0] + u[0] * step * (k + 1),
                        a[1] + u[1] * step * (k + 1)))
            continue
        d = depth * w
        pts.append((a[0] + u[0] * s_mid + n[0] * d,
                    a[1] + u[1] * s_mid + n[1] * d))
        pts.append((a[0] + u[0] * step * (k + 1),
                    a[1] + u[1] * step * (k + 1)))
    return pts


def front_profile(p: RidgeParams) -> list[Pt]:
    """
    The illuminated surface, traced from the top of the panel downward.

    ridge tip -> flank down to the valley floor -> flank up to the next tip.
    Tips get a rounded cap of radius tip_width/2 (a real machined edge is never
    a mathematical point, and the radius IS the lip), valleys get a fillet so
    the floor is not a perfect corner.
    """
    pts: list[Pt] = []
    z = p.face_h / 2.0 + p.margin_depths * p.depth
    pitches = pitch_sequence(p)
    rng = _lcg(p.pitch_seed * 7 + 3)
    tw = max(p.tip_width, 1e-4)

    for i, w in enumerate(pitches):
        tilt = math.radians(p.tilt_deg +
                            (2.0 * next(rng) - 1.0) * p.tilt_jitter)
        # ridge tip
        if p.tip_round:
            r = tw / 2.0
            pts += _arc((-r, z), r, math.pi / 2, -math.pi / 2,
                        max(2, p.arc_segments))
        else:
            pts += [(0.0, z + tw / 2.0), (0.0, z - tw / 2.0)]

        # valley floor, offset along Z by the tilt
        zv = z - w / 2.0 - p.depth * math.tan(tilt)
        vr = max(p.valley_round, 1e-3)
        valley = _arc((-p.depth + vr, zv), vr,
                      math.pi + math.atan2(-w / 2.0, -p.depth),
                      -math.pi + math.atan2(w / 2.0, -p.depth),
                      max(2, p.arc_segments))

        if p.micro_pitch > 0.0 and p.micro_depth > 0.0:
            # a point inside this groove's open volume, used to aim the notches
            air = (-p.depth / 3.0, (z + zv + (z - w)) / 3.0)
            down = serrate(pts[-1], valley[0], air,
                           p.micro_pitch, p.micro_depth)
            pts += down[1:]
            pts += valley
            nxt = (0.0, z - w + tw / 2.0)
            up = serrate(valley[-1], nxt, air, p.micro_pitch, p.micro_depth)
            pts += up[1:-1]
        else:
            pts += valley
        z -= w
    return pts


def build_cross_section(p: RidgeParams) -> CrossSection:
    """
    One closed solid: the grooved front surface plus a flat back. Modelled as
    a solid rather than a folded sheet because manufacturing is unconstrained
    for this family.
    """
    cs = CrossSection()

    if p.half_angle_deg() > 30.0:
        cs.warnings.append(
            f"half angle {p.half_angle_deg():.1f} deg gives only "
            f"{p.est_bounces():.1f} bounces; the groove is too open to trap")

    if p.tip_fraction() > 0.1:
        cs.warnings.append(
            f"tip takes {p.tip_fraction()*100:.1f}% of the face; the head-on "
            "exposed ridge is the dominant return path")

    front = front_profile(p)
    z_hi = front[0][1]
    z_lo = front[-1][1]
    yb = -(p.depth + p.backing)
    loop = list(front) + [(yb, z_lo), (yb, z_hi)]
    # stage1, so it takes the specular coating: V-groove theory says a
    # collapsing groove with SPECULAR walls approaches unit absorptance, while
    # a diffuse first bounce throws light back out of the groove
    cs.stage1.append(loop)
    return cs


def describe(p: RidgeParams) -> dict:
    return {
        "family": "ridge",
        "depth_mm": p.depth,
        "pitch_mean_mm": p.pitch_mean,
        "pitch_jitter": p.pitch_jitter,
        "tip_width_mm": p.tip_width,
        "tip_fraction": p.tip_fraction(),
        "half_angle_deg": p.half_angle_deg(),
        "est_bounces": p.est_bounces(),
        "tilt_deg": p.tilt_deg,
        "tilt_jitter": p.tilt_jitter,
        "valley_round_mm": p.valley_round,
        "margin_depths": p.margin_depths,
        "predicted_return_rho05": p.predicted_return(0.05),
    }


if __name__ == "__main__":
    for d in (25.0, 50.0, 100.0, 200.0):
        prm = RidgeParams(depth=d)
        cs = build_cross_section(prm)
        dd = describe(prm)
        print("depth %5.0f  half-angle %5.2f deg  bounces %5.1f  "
              "tip frac %.4f  rho^n(0.05) %.2e  warn=%d"
              % (d, dd["half_angle_deg"], dd["est_bounces"],
                 dd["tip_fraction"], 0.05 ** dd["est_bounces"],
                 len(cs.warnings)))
