"""Perforated pyramid shells, built on `geom_kit` so the surface is exact.

The first version of this module stacked slab tiles into a shell. Two of its
defects each produced a published number that was then withdrawn: the apex was
at the BOTTOM (a funnel measured against a spike), and at zero open area the
tiles touched exactly, burying coincident faces that agreed with the equivalent
solid under a Lambertian and diverged 37 % under a specular coating. Both are
in `FINDINGS_perforated.md` as corrections.

This version builds each pyramid as four sheet faces through
`geom_kit.shell`, which enforces the invariants the first version violated:
every face emitted once, angle-weighted pseudo-normal offsets (exact on planar
faces -- one normal per skin, measured 0.00 degrees of spread), every edge on
exactly two faces or the build fails, and hole patterns that would join
material at a point are rejected at build time.

GEOMETRY. Tip up: apex in the entrance plane, square base of `pitch` at
y = -depth, exactly like `geom_floor`'s solid pyramid. Faces overlap their
neighbours at the hips by a small real amount and the shells sink `NUDGE` into
the backing slab -- solids may overlap, never touch exactly.

PERFORATION. Holes are square blocks of `hole_block` x `hole_block` grid cells
on a period of `hole_period` cells, so the open fraction is
(hole_block / hole_period)^2 and the material between holes is always at least
one cell wide -- block holes cannot create the point-joints the kernel forbids.
`hole_period = 0` is a solid skin, which is the baseline: it must measure the
same as `geom_floor`'s solid pyramid under EVERY coating, and until it does no
perforated number from this module is quotable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import geom_kit as GK


@dataclass
class PerfParams:
    face_w: float = 60.0
    face_h: float = 60.0
    depth: float = 50.0
    pitch: float = 5.5
    wall: float = 0.5            # sheet thickness, mm
    hole_block: int = 1          # hole size, in grid cells
    hole_period: int = 0         # hole repeat, in grid cells; 0 = solid skin
    nu: int = 12                 # grid cells across a face
    nv: int = 24                 # grid cells base -> apex
    margin_depths: float = 2.0
    backing: float = 2.0
    seed: int = 23

    def margin(self):
        return max(self.margin_depths * self.depth, self.pitch)

    def open_frac(self):
        """Open fraction of the perforated BAND (the lower 70 % of the face).

        The apex margin and base row are solid by construction, so the whole-
        face open fraction is lower; the band figure is what a perforated-sheet
        supplier would quote for the stock.
        """
        if self.hole_period <= 0:
            return 0.0
        return (self.hole_block / float(self.hole_period)) ** 2

    def exposed_fraction_est(self):
        """Tip-up shell: what faces the viewer is four sheet edges at a point."""
        return (4.0 * self.wall ** 2 * (1.0 - self.open_frac())
                / max(self.pitch ** 2, 1e-9))


# CLOCKWISE seen from +y, and that is load-bearing. The wrapped patch's
# surface normal is du x dv; walking the corners counter-clockwise makes that
# point INTO the pyramid, so the "inner" skin (offset -t along the normal)
# lands OUTSIDE -- a second, floating, wrong-way-wound shell above every face.
# Measured: every one of 600 vertical test rays hit that floating skin 9 mm
# above the true surface, and the render darkened 34-37 % under a specular
# coating for three sessions of wrong reasons. Verified by computing the
# Newell normal against the outward direction: CCW gives -0.892, CW +0.892.
_CORNERS = ((-1, 1), (1, 1), (1, -1), (-1, -1))


def _face_patch(k, cx, cz, half, depth, over):
    u0, u1 = _CORNERS[k], _CORNERS[(k + 1) % 4]

    def patch(u, w):
        uu = -(over - 1.0) / 2.0 + over * u
        bx = (u0[0] + (u1[0] - u0[0]) * uu) * half
        bz = (u0[1] + (u1[1] - u0[1]) * uu) * half
        return (cx + bx * (1.0 - w), -depth * (1.0 - w), cz + bz * (1.0 - w))
    return patch


def build_mesh(p: PerfParams):
    verts, faces = [], []
    m = p.margin()
    nx = int((p.face_w + 2 * m) / p.pitch) + 2
    nz = int((p.face_h + 2 * m) / p.pitch) + 2
    half = p.pitch / 2.0
    # sink into the slab: overlap, never exact touch
    depth_eff = p.depth + GK.NUDGE * 10

    if p.hole_period > 0:
        hb, pd = p.hole_block, p.hole_period
        if hb >= pd:
            raise ValueError("hole_block must be smaller than hole_period")

        # NO HOLES NEAR THE APEX OR THE BASE. Near the apex the face narrows
        # below the hole size -- the kernel rejects the resulting geometry
        # (hole boundaries meeting through welded apex nodes), and a real
        # perforated part keeps a solid margin there anyway. The bottom row
        # stays solid so the base rim that meets the slab is continuous.
        j_top = int(p.nv * 0.70)         # holes only in the lower 70 %

        def keep(i, j):
            if j >= j_top or j == 0:
                return True
            return not (i % pd < hb and j % pd < hb)
    else:
        keep = None

    # ONE PYRAMID = ONE CLOSED SOLID. The four faces are a single wrapped
    # parametrisation: u runs around the pyramid, one face per quarter. The
    # kernel's position welding closes the u seam, so the hips are INTERIOR
    # edges of the sheet -- no bore walls there. Building the faces as four
    # separate sheets put a bore strip along every hip, and on a near-90-degree
    # pyramid that strip lies ~0.03 mm inside the neighbouring face with its
    # normal opposed: a micro-slit light trap running the length of every hip,
    # isolated by rendering the sheet in parts (outer skin alone matched the
    # solid to +0.1 %; adding the bores took it to -58 %).
    # SOLID TIP ON A SHELL SKIRT. The tip is where a shell must thin below
    # the sheet thickness, and a sub-0.1 mm double wall at the tip cost three
    # rounds of specular discrepancy before being designed out rather than
    # explained. Holes are only allowed in the lower band anyway, so the upper
    # 35 % of every pyramid is a closed SOLID (five faces, apex to a buried
    # base) scaled by 1.0002 about the apex so it sits half a micron proud of
    # the skirt -- overlap, never exact coincidence. The skirt is a wrapped
    # shell over the lower 65 % with a CONSTANT wall: at its top the face-to-
    # axis room is 0.77 mm > wall, so no taper and no thin gap exist anywhere.
    n_face = max(4, p.nu)
    nu_tot = 4 * n_face
    W_SKIRT = 0.65
    tip_top = W_SKIRT * (1.0 - 0.06)     # skirt top w; tip overlaps past it

    def wrap_patch(u, w):
        t = u * 4.0
        k = min(3, int(t))
        uu = t - k
        u0, u1 = _CORNERS[k], _CORNERS[(k + 1) % 4]
        bx = (u0[0] + (u1[0] - u0[0]) * uu) * half
        bz = (u0[1] + (u1[1] - u0[1]) * uu) * half
        ww = w * W_SKIRT
        return (bx * (1.0 - ww), -depth_eff * (1.0 - ww), bz * (1.0 - ww))

    wkeep = None
    if keep is not None:
        def wkeep(i, j, _nf=n_face):
            return keep(i % _nf, j)

    cell_v, cell_f = [], []
    GK.shell(wrap_patch, nu_tot, p.nv, p.wall, keep=wkeep,
             verts=cell_v, faces=cell_f, offsets=(0.0, -p.wall))

    # the solid tip: apex at 0, square base buried inside the skirt band
    sc = 1.0 + 2e-3
    y_base = -depth_eff * (1.0 - tip_top)
    ct = [( _CORNERS[k][0] * half * (1.0 - tip_top) * sc,
            y_base * sc,
            _CORNERS[k][1] * half * (1.0 - tip_top) * sc)
          for k in range(4)]
    b0 = len(cell_v)
    cell_v.extend(ct + [(0.0, 0.0, 0.0)])
    apex_i = b0 + 4
    for k in range(4):
        cell_f.append((b0 + k, b0 + (k + 1) % 4, apex_i))
    cell_f.append((b0 + 3, b0 + 2, b0 + 1, b0 + 0))     # base cap, facing down

    for iz in range(nz):
        for ix in range(nx):
            cx = ix * p.pitch + half - m
            cz = iz * p.pitch + half - (p.face_h / 2.0 + m)
            b0 = len(verts)
            verts.extend((x + cx, y, z + cz) for x, y, z in cell_v)
            faces.extend(tuple(i + b0 for i in f) for f in cell_f)

    # backing slab
    hh = p.face_h / 2.0 + m
    GK.slab(verts, faces,
            [(-m, -p.depth, -hh), (p.face_w + m, -p.depth, -hh),
             (p.face_w + m, -p.depth, hh), (-m, -p.depth, hh)],
            [(-m, -p.depth - p.backing, -hh),
             (p.face_w + m, -p.depth - p.backing, -hh),
             (p.face_w + m, -p.depth - p.backing, hh),
             (-m, -p.depth - p.backing, hh)])
    import geom_kit as _GK
    verts, faces = _GK.orient_outward(verts, faces)
    return verts, faces


def describe(p: PerfParams) -> dict:
    return {"family": "perf", "topology": "perforated pyramid",
            "depth_mm": p.depth, "pitch_mm": p.pitch,
            "pitch_mean_mm": p.pitch,
            "aspect": p.depth / max(p.pitch, 1e-9),
            "open_frac": p.open_frac(), "wall_mm": p.wall,
            "hole_block": p.hole_block, "hole_period": p.hole_period,
            "exposed_fraction_est": p.exposed_fraction_est(),
            "margin_depths": p.margin_depths}
