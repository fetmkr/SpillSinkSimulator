"""
Phase 3: two structures stacked, one behind the other.

Phase 1 was extruded 2D cross-sections. Phase 2 was nine 3D topologies, each
measured on three axes that turned out to want different things:

    total reflectance   commercial honeycomb  #2   cone #5
    form destruction    cone #1                    honeycomb #11
    head-on brightness  cone #1                    honeycomb #11

**No single layer is good at all three.** The honeycomb is second on total
reflectance and last on the other two: its vertical walls trap light but never
move it sideways, and their flat tops face the viewer exactly like the flat
plate they replaced. The cone owns both viewer-facing axes and is mid-table on
total. The blade array is 2nd-4th on everything and first on nothing.

So the phase 3 question is whether two scales in series do better than either
alone -- a coarse cell that swallows the energy, with something underneath or
on top that destroys what little comes back out.

HOW IT IS BUILT. Every family here already returns `(verts, faces)` as a union
of closed solids with a backing slab appended last -- exactly 8 vertices and 6
quads, verified for all four modules. So a stack is: build the top layer, strip
its slab, build the bottom layer, strip its slab, translate the bottom down by
the top's depth, concatenate with an index offset, and put ONE slab underneath
everything. No booleans, because for an opaque surface the union is the
geometry.

WHAT TO WATCH. The top layer's own exposed features are still exposed. Putting
a honeycomb over a cone field does not hide the honeycomb's wall tops, and
those tops are what makes its head-on brightness equal to a flat plate. If the
stack inherits the top layer's head-on failure, that is the answer -- and it is
worth knowing rather than assuming either way.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# --- the four families a layer can be -------------------------------------

def _build_layer(kind: str, prm: dict):
    """(verts, faces) for one layer, WITHOUT its backing slab.

    Every module appends the slab last as 8 verts + 6 quads. Verified for
    comb, shingle, cone and cell on 2026-08-13; asserted here so a change in
    any of them fails loudly instead of leaving a plate buried mid-stack.
    """
    if kind == "cone":
        import geom3d as M
        v, f = M.build_mesh(M.Cone3DParams(**prm))
    elif kind in ("pyramid", "wave", "gap"):
        # phase 4 floors: a 2-5 mm shaped bottom for a full-depth cell. They
        # honour the same slab contract, so they need no special case beyond
        # this line -- and `gap` legitimately returns an EMPTY layer.
        import geom_floor as M
        v, f = M.build_mesh(M.FloorParams(kind=kind, **prm))
    elif kind in ("comb", "honeycomb", "shingle", "truss"):
        import geom_topo as M
        v, f = M.build_mesh(M.TopoParams(topology=kind, **prm))
    else:
        import geom_cell as M
        v, f = M.build_mesh(M.CellParams(variant=kind, **prm))

    assert len(f) >= 6 and all(len(x) == 4 for x in f[-6:]), \
        "%s: last 6 faces are not the slab" % kind
    ys = {round(q[1], 3) for q in v[-8:]}
    assert len(ys) == 2, "%s: last 8 verts are not a slab (y=%s)" % (kind, ys)
    return v[:-8], f[:-6]


def _shift(verts, dy):
    return [(x, y + dy, z) for x, y, z in verts]


def _concat(a_v, a_f, b_v, b_f):
    n = len(a_v)
    return a_v + b_v, a_f + [tuple(i + n for i in face) for face in b_f]


@dataclass
class StackParams:
    # --- envelope, shared by both layers ---
    face_w: float = 60.0
    face_h: float = 60.0
    backing: float = 2.0
    margin_depths: float = 2.0
    seed: int = 23

    # --- top layer: the one the beam meets first ---
    top: str = "comb"
    top_depth: float = 25.0
    top_params: dict = field(default_factory=dict)

    # --- bottom layer ---
    bot: str = "cone"
    bot_depth: float = 25.0
    bot_params: dict = field(default_factory=dict)

    # ---- derived, so the report and the gate can read them ----

    @property
    def depth(self):
        return self.top_depth + self.bot_depth

    @property
    def pitch(self):
        """The COARSER of the two, because that is the cell a beam enters."""
        return max(self.top_params.get("pitch", 0.0),
                   self.bot_params.get("pitch", 0.0))

    def aspect(self):
        return self.depth / max(self.pitch, 1e-9)

    def exposed_fraction_est(self):
        """Only the TOP layer is exposed head-on -- that is the whole point.

        A stack cannot hide its own first surface. If the top layer's tops are
        what ruin its head-on brightness, the stack inherits that, and the
        estimate should say so before the render does.
        """
        import geom_topo as GT
        import geom_cell as GC
        import geom3d as G3
        p = dict(self.top_params, face_w=self.face_w, face_h=self.face_h,
                 depth=self.top_depth, margin_depths=self.margin_depths,
                 backing=self.backing, seed=self.seed)
        if self.top == "cone":
            return G3.Cone3DParams(**p).tip_fraction()
        if self.top in ("comb", "honeycomb", "shingle", "truss"):
            return GT.TopoParams(topology=self.top, **p).exposed_fraction_est()
        return GC.CellParams(variant=self.top, **p).exposed_fraction_est()


def build_mesh(p: StackParams):
    common = dict(face_w=p.face_w, face_h=p.face_h,
                  margin_depths=p.margin_depths, backing=p.backing,
                  seed=p.seed)

    tv, tf = _build_layer(p.top, dict(p.top_params, depth=p.top_depth,
                                      **common))
    # THE FLOOR MUST COVER WHAT THE TUBE ACTUALLY OCCUPIES, not what its
    # nominal margin says. `_build_comb` and friends round their cell counts
    # up and overshoot: a 47 mm comb asked for a 9.4 mm margin lays down 199 mm
    # of cells, while a 3 mm floor built to the same rule is 84 mm across. The
    # tube then hangs over the edge of its own floor by more than a factor of
    # two -- invisible in the measurement, because the window only sees the
    # 60 mm face, and plainly wrong in a render and in any exported part.
    # So the floor's margin is derived from the tube's REAL extent.
    if tv:
        xs = [q[0] for q in tv]
        zs = [q[2] for q in tv]
        need = max(max(xs) - p.face_w, -min(xs),
                   max(zs) - p.face_h / 2.0, -min(zs) - p.face_h / 2.0)
        bot_p = dict(p.bot_params)
        if p.bot in ("pyramid", "wave", "gap"):
            # Both, and they say the same thing two ways. `margin_depth_ref` is
            # a RATIO that `FloorParams.margin` multiplies by `margin_depths`,
            # so it vanishes when that is zero -- the preview and STL path,
            # where the floor then shrank to one pitch and left the tube
            # standing on nothing near the origin corner. `margin_min` is the
            # same requirement as a length and holds at any `margin_depths`.
            # The ratio is kept so sweeps that set it directly still behave
            # exactly as they were measured.
            bot_p["margin_depth_ref"] = max(need, 1e-6) / max(
                p.margin_depths, 1e-9)
            bot_p["margin_min"] = max(need, 0.0)
        else:
            bot_p = dict(bot_p)
    else:
        bot_p = dict(p.bot_params)
    bv, bf = _build_layer(p.bot, dict(bot_p, depth=p.bot_depth,
                                      **{**common, "seed": p.seed + 7}))
    bv = _shift(bv, -p.top_depth)
    verts, faces = _concat(tv, tf, bv, bf)

    # one slab under the whole stack
    m = max(p.margin_depths * p.depth, p.pitch)
    h = p.face_h / 2.0 + m
    y0 = -p.depth
    b = len(verts)
    for y in (y0, y0 - p.backing):
        verts += [(-m, y, -h), (p.face_w + m, y, -h),
                  (p.face_w + m, y, h), (-m, y, h)]
    faces += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b + i, b + 4 + i, b + 4 + j, b + j))
    # oriented exit like every other builder; the hand-made slab above was the
    # one inward-wound component in an otherwise correct stack
    import geom_kit as _GK
    return _GK.orient_outward(verts, faces)


def describe(p: StackParams) -> dict:
    return {"family": "stack",
            "topology": "%s/%s" % (p.top, p.bot),
            "depth_mm": p.depth,
            "top": p.top, "top_depth_mm": p.top_depth,
            "bot": p.bot, "bot_depth_mm": p.bot_depth,
            "pitch_mm": p.pitch, "pitch_mean_mm": p.pitch,
            "aspect": p.aspect(),
            "exposed_fraction_est": p.exposed_fraction_est(),
            "margin_depths": p.margin_depths}


if __name__ == "__main__":
    CASES = [
        ("comb/cone", dict(top="comb", top_depth=25.0,
                           top_params=dict(pitch=6.5, wall_top=0.08,
                                           wall_bot=0.08, jitter=0.0),
                           bot="cone", bot_depth=25.0,
                           bot_params=dict(pitch=5.5, tip_radius=0.2,
                                           jitter=0.30, radial_seg=24,
                                           height_seg=12, depth_jitter=0.0))),
        ("comb/comb fine", dict(top="comb", top_depth=25.0,
                                top_params=dict(pitch=6.5, wall_top=0.08,
                                                wall_bot=0.08, jitter=0.0),
                                bot="comb", bot_depth=25.0,
                                bot_params=dict(pitch=3.17, wall_top=0.04,
                                                wall_bot=0.04, jitter=0.0))),
        ("comb/blades", dict(top="comb", top_depth=25.0,
                             top_params=dict(pitch=6.5, wall_top=0.08,
                                             wall_bot=0.08, jitter=0.0),
                             bot="shingle", bot_depth=25.0,
                             bot_params=dict(pitch=5.5, plate_t_top=0.1,
                                             plate_t_bot=0.1, tilt_deg=2.0,
                                             tilt_jitter=0.0,
                                             azimuth_mode="grid",
                                             jitter=0.30))),
        ("cone/comb", dict(top="cone", top_depth=25.0,
                           top_params=dict(pitch=5.5, tip_radius=0.2,
                                           jitter=0.30, radial_seg=24,
                                           height_seg=12, depth_jitter=0.0),
                           bot="comb", bot_depth=25.0,
                           bot_params=dict(pitch=6.5, wall_top=0.08,
                                           wall_bot=0.08, jitter=0.0))),
    ]
    print("%-16s %9s %9s %9s %8s" % ("stack", "verts", "faces", "exposed%",
                                     "y range"))
    for name, kw in CASES:
        p = StackParams(face_w=40.0, face_h=40.0, margin_depths=0.5, **kw)
        v, f = build_mesh(p)
        ys = [q[1] for q in v]
        print("%-16s %9d %9d %9.3f  %.1f..%.1f"
              % (name, len(v), len(f), 100 * p.exposed_fraction_est(),
                 min(ys), max(ys)))
        assert max(ys) <= 1e-9, "%s rises above the entrance plane" % name
    print("OK — nothing above Y=0, slabs stripped, one slab at the bottom")
