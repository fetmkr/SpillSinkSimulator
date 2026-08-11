"""
Fourth geometry family: folded (labyrinth) channels — optical path length
decoupled from panel depth.

The problem this exists to solve
--------------------------------
For a straight V-groove the bounce count is fixed by one ratio:

    half-angle = atan(pitch / 2*depth)
    bounces   ~ 90 / (2 * half-angle)  ~  3.15 * depth / pitch

Measured against the 2D ray trace this holds: depth 150 / pitch 20 gives 23.6
bounces at normal incidence, and the render agrees. It also means depth cannot
be reduced without reducing pitch in proportion, and the tip fraction
(tip width / pitch) — which IS the return — rises just as fast. A 30 mm panel
would need a 4 mm pitch and a 0.04 mm ridge tip.

The way out is that the channel does not have to be straight. Bounce count
follows optical PATH LENGTH divided by channel width, not depth. Folding the
channel sideways buys path length out of the panel's height, which is free,
instead of out of its depth, which is not. A 30 mm deep panel with three
switchbacks of 45 mm carries ~165 mm of path.

The cost is that every fold is a place a ray can turn around, so the folds are
made obtuse and the outer corners are the ones that get the rounding.

Manufacturing is unconstrained for this family: stacked/laminated plates or
printed cores, not bent sheet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from profile2d import Pt, _lcg, CrossSection, fillet_polyline, thicken


@dataclass
class LabyParams:
    # --- envelope (mm) ---
    face_w: float = 500.0
    face_h: float = 500.0
    depth: float = 30.0             # this is the number being minimised

    # --- channel ---
    cell_pitch: float = 40.0        # Z period of one labyrinth cell
    pitch_jitter: float = 0.22
    pitch_seed: int = 17
    wall: float = 1.2               # material thickness between channels
    channel_w: float = 4.0          # channel clear width
    entry_deg: float = 35.0         # entry run angle from the panel normal
    folds: int = 3                  # switchbacks after the entry run
    fold_frac: float = 0.72         # switchback length as a fraction of pitch

    # --- tip ---
    tip_width: float = 0.15         # head-on exposed width per divider

    arc_segments: int = 5

    # ---- derived ----------------------------------------------------------

    def path_len(self) -> float:
        entry = self.depth / max(math.cos(math.radians(self.entry_deg)), 1e-6)
        return entry + self.folds * self.fold_frac * self.cell_pitch

    def aspect(self) -> float:
        """Path length in channel widths -- the bounce budget."""
        return self.path_len() / max(self.channel_w, 1e-6)

    def equiv_vgroove_depth(self) -> float:
        """Depth a straight V-groove of the same pitch would need to match."""
        return self.path_len() * math.cos(math.radians(self.entry_deg))

    def tip_fraction(self) -> float:
        return self.tip_width / max(self.cell_pitch, 1e-9)


def pitch_sequence(p: LabyParams) -> list[float]:
    n = max(2, int(round(p.face_h / p.cell_pitch)))
    if p.pitch_jitter <= 0.0:
        return [p.face_h / n] * n
    rng = _lcg(p.pitch_seed)
    raw = [1.0 + p.pitch_jitter * (2.0 * next(rng) - 1.0) for _ in range(n)]
    s = sum(raw)
    return [r / s * p.face_h for r in raw]


def channel_centerline(p: LabyParams, z_top: float, cell: float) -> list[Pt]:
    """
    Centre line of one folded channel, from its mouth at the face plane.

    Entry run inward at `entry_deg`, then `folds` switchbacks that run back and
    forth in Z at a small inward slope, so the channel keeps creeping deeper
    while spending most of its length sideways.
    """
    a = math.radians(p.entry_deg)
    z = z_top - cell * 0.5
    pts: list[Pt] = [(0.0, z)]

    entry_len = (p.depth * 0.45) / max(math.cos(a), 1e-6)
    y = -entry_len * math.cos(a)
    z = z - entry_len * math.sin(a)
    pts.append((y, z))

    run = p.fold_frac * cell
    creep = (p.depth * 0.55) / max(p.folds, 1)
    for k in range(p.folds):
        z = z + (run if k % 2 == 0 else -run)
        y = y - creep
        pts.append((y, z))
    return pts


def build_cross_section(p: LabyParams) -> CrossSection:
    """
    The dividers between channels are the solid. Each is the channel centre
    line thickened by (channel width + wall), which produces the neighbouring
    channel's opposite wall at the same time.
    """
    cs = CrossSection()

    if p.aspect() < 8.0:
        cs.warnings.append(
            f"path/width aspect {p.aspect():.1f} is low; a straight V-groove "
            f"of the same pitch reaches this at only "
            f"{p.equiv_vgroove_depth():.0f} mm depth, so the folding buys "
            "nothing")

    if p.tip_fraction() > 0.02:
        cs.warnings.append(
            f"divider tip takes {p.tip_fraction()*100:.2f}% of the face; the "
            "head-on exposed edge dominates the return")

    z = p.face_h / 2.0
    for cell in pitch_sequence(p):
        cl = channel_centerline(p, z, cell)
        cl = fillet_polyline(cl, max(0.6 * p.channel_w, 1.0), p.arc_segments)
        cs.stage1.append(thicken(cl, p.channel_w + p.wall, round_ends=True))
        z -= cell

    # solid backing so nothing sees daylight through the panel
    yb = -(p.depth + 6.0)
    zh, zl = p.face_h / 2.0 + 40.0, -p.face_h / 2.0 - 40.0
    cs.shell.append([(-p.depth, zh), (yb, zh), (yb, zl), (-p.depth, zl)])
    return cs


def describe(p: LabyParams) -> dict:
    return {
        "family": "laby",
        "depth_mm": p.depth,
        "cell_pitch_mm": p.cell_pitch,
        "pitch_jitter": p.pitch_jitter,
        "channel_w_mm": p.channel_w,
        "entry_deg": p.entry_deg,
        "folds": p.folds,
        "fold_frac": p.fold_frac,
        "path_len_mm": p.path_len(),
        "aspect": p.aspect(),
        "equiv_vgroove_depth_mm": p.equiv_vgroove_depth(),
        "tip_width_mm": p.tip_width,
        "tip_fraction": p.tip_fraction(),
    }


if __name__ == "__main__":
    for d, f in ((30.0, 3), (30.0, 5), (50.0, 3), (20.0, 4)):
        prm = LabyParams(depth=d, folds=f)
        cs = build_cross_section(prm)
        dd = describe(prm)
        print("depth %4.0f folds %d -> path %6.1f mm  aspect %5.1f  "
              "equiv V-groove depth %6.1f mm  channels %d  warn=%d"
              % (d, f, dd["path_len_mm"], dd["aspect"],
                 dd["equiv_vgroove_depth_mm"], len(cs.stage1),
                 len(cs.warnings)))
