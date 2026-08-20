"""
Search over topologies that are NEITHER a V-groove NOR a cone.

    Blender --background --factory-startup --python scripts/sweep_topo.py
    SMOKE=1 Blender --background --factory-startup --python scripts/sweep_topo.py

Every family measured in this project so far has been one of two things: a Y-Z
cross-section extruded along X (slat, scatter, ridge, laby) or an array of
axisymmetric pillars (cone3d, and the power/bulge/lip shapes in sweep_shapes,
which change a pillar's profile but not its topology). This sweep is the first
that changes the topology itself.

    shingle    overlapping inclined plates, knife-edged at the entrance plane
    truss      sparse 3D strut lattice between jittered node layers
    honeycomb  deep cell walls -- the NEGATIVE CONTROL, see below

SCORING IS DELIBERATELY IDENTICAL TO sweep_shapes.py. Same thetas, same three
diffuse fractions, same face, samples, resolution and margin, same incremental
resumable CSV. Nothing about the objective changes here; only the geometry
does. A new topology that has to be scored a new way has not been shown to be
better, it has been shown to be different.

    theta          0, +/-20, +/-40     the range the rig actually puts on the wall
    diffuse_frac   0.0, 0.76, 1.0      the dominant unmeasured material parameter
    score          worst rho over all thetas AND all three materials

The three-material rule is the point, not a formality: switching from the old
flat-rho glossy to the fitted Fresnel coating moved designs by 2x to 41x and
INVERTED the ranking (metrics/01). Until a printed coupon settles the
diffuse/specular split, a design that wins under one material is a bet and a
design that wins under both is a result.

Why honeycomb is in here to lose
--------------------------------
The exposed-area law -- head-on return is the exposed feature and essentially
nothing else -- has driven every design decision in this project. It predicts
a wall network must lose to a point array, because at pitch 7.5 a 0.4 mm wall
exposes 10.67% of the cell against a 0.2 mm-radius tip's 0.258%. That is 41x,
computed in geom_topo.exposed_fraction_est() BEFORE rendering. If the render
comes back and honeycomb is NOT about 41x worse head-on, the law is wrong, and
that is worth more than any good number in this file. It is here as a
falsification test, and it should be read as one.

Every row carries `params_json`: the complete TopoParams needed to rebuild that
exact design. One row is enough to reproduce anything interesting.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_shard import done_tags, shard_csv, take                # noqa: E402
import blender_render as BR                                        # noqa: E402
import geom_topo as GT                                             # noqa: E402
import geom_cell as GC                                             # noqa: E402
import geom3d as G3                                                # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "topo")
OUTCSV = shard_csv(os.path.join(RESULTS, "sweep_topo.csv"))

# --- budget, copied from sweep_shapes.py so the two files are comparable -----
FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
SPEC_ROUGHNESS = 0.30           # pinned: moves cavity rho_dh by 32%
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
MARGIN_DEPTHS = 6.5             # not reducible; margin 1.0 moved head-on 15%

FIELDS = ["tag", "family", "topology", "diffuse_frac", "pitch", "depth",
          "aspect", "exposed_est", "theta", "rho", "control", "params_json"]


# --- the design list --------------------------------------------------------
#
# Explicit rather than a cartesian product: the three topologies do not share
# their knobs, and a product over the union would spend most of the run on
# combinations where the swept parameter does nothing.

def designs(smoke=False):
    out = []

    # --- reference: the cone, re-measured in this frame -------------------
    # Re-measured, never quoted from an older CSV. The material model changed
    # on 2026-08-11 and CONTEXT.md's rule is "every past comparison must be
    # RE-RUN, not rescaled". Without a reference measured in the same frame,
    # under the same coating, nothing here is comparable to anything.
    for pitch, depth in (((7.5, 30.0),) if smoke else
                         ((7.5, 30.0), (3.75, 30.0), (7.5, 20.0))):
        out.append(("cone3d", "cone",
                    dict(face_w=FACE, face_h=FACE, depth=depth, pitch=pitch,
                         tip_radius=0.2, jitter=0.30, radial_seg=24,
                         height_seg=12, margin_depths=MARGIN_DEPTHS,
                         backing=2.0, depth_jitter=0.0, profile_power=1.0)))

    def topo(topology, **kw):
        p = dict(topology=topology, face_w=FACE, face_h=FACE,
                 margin_depths=MARGIN_DEPTHS, backing=2.0, jitter=0.30)
        p.update(kw)
        out.append(("topo", topology, p))

    if smoke:
        topo("shingle", pitch=7.5, depth=30.0, tilt_deg=60.0)
        topo("truss", pitch=7.5, depth=30.0, layers=5, strut_r=0.35)
        topo("honeycomb", pitch=7.5, depth=30.0, wall_top=0.4)
        return out

    # --- shingle: the bet ---------------------------------------------------
    # tilt is measured from the panel normal: 30 is a steep fin, 75 lies almost
    # flat across the mouth. plate_over > 1 is what makes neighbours overlap
    # and turns the gap into a slot instead of an open hole.
    for depth in (20.0, 30.0):
        for pitch in (3.75, 5.5, 7.5):
            for tilt in (30.0, 45.0, 60.0, 75.0):
                for over in (1.15, 1.45):
                    topo("shingle", pitch=pitch, depth=depth, tilt_deg=tilt,
                         plate_over=over, plate_t_top=0.05, plate_t_bot=0.9,
                         tilt_jitter=10.0, azimuth_jitter=180.0)
    # knife-edge thickness series: the head-on design variable for this family,
    # the way tip radius was for the cone. 0.4 is one nozzle.
    for t_top in (0.2, 0.4):
        topo("shingle", pitch=5.5, depth=30.0, tilt_deg=60.0, plate_over=1.45,
             plate_t_top=t_top, plate_t_bot=0.9)

    # --- LOW TILT: the first block ran 30/45/60/75 and the trend was monotone
    # and strong all the way to the edge of the range, which means the range
    # was wrong, not the trend. Under the specular material, at pitch 5.5 /
    # depth 30:
    #
    #     tilt   75      60      45      30
    #     d00    0.00913 0.00684 0.00431 0.00114
    #
    # and at tilt 30 the theta = 0 figure is 0.00040 against the best cone's
    # 0.00193 in the same frame -- 4.8x on the one axis metrics/02 calls "the
    # unsolved axis", where observer and beam are collinear and no family tried
    # so far has moved the needle.
    #
    # Tilt is measured from the panel NORMAL, so this walks toward vertical
    # plates. At tilt 0 the shingle degenerates into a maze of vertical walls in
    # random azimuths -- which is topologically the honeycomb, arrived at from
    # the other direction. If the two families meet at the same number there,
    # that is a real convergence and not a coincidence; if they do not, one of
    # the two builders is wrong. Either outcome is worth the runs.
    for depth in (20.0, 30.0):
        for pitch in (3.75, 5.5, 7.5):
            for tilt in (5.0, 10.0, 15.0, 20.0, 25.0):
                topo("shingle", pitch=pitch, depth=depth, tilt_deg=tilt,
                     plate_over=1.15, plate_t_top=0.05, plate_t_bot=0.9,
                     tilt_jitter=min(10.0, tilt), azimuth_jitter=180.0)
    # tilt_jitter is clamped to the tilt itself above, because the builder
    # clamps the sum to >= 5 degrees and an unclamped +/-10 on a 5 degree tilt
    # would silently pile designs onto that floor and read as a plateau.

    # --- truss: sparse, high surface area, no preferred direction -----------
    for depth in (20.0, 30.0):
        for pitch in (5.5, 7.5):
            for layers in (3, 5, 8):
                for strut_r in (0.2, 0.35, 0.6):
                    topo("truss", pitch=pitch, depth=depth, layers=layers,
                         strut_r=strut_r, links=2, strut_seg=4,
                         layer_jitter=0.40, link_reach=1.6)
    # link count: 2 vs 3 changes volume fraction and surface area together
    for links in (3,):
        topo("truss", pitch=7.5, depth=30.0, layers=5, strut_r=0.35,
             links=links, strut_seg=4)

    # --- honeycomb: PROMOTED from negative control to the main search -------
    #
    # It was put in to lose by the 41x its exposed area predicts. It lost by
    # 1.30x worst-theta and 1.51x head-on (results/FINDINGS_topo_smoke.md).
    # The exposed-area law does not hold under the fitted coating, so the knob
    # that matters is not wall thickness but cavity aspect -- and a wall cell
    # has an advantage no pillar array can have: it never seals. A cone at
    # pitch 7.5 stops being a cavity at 72.2% of its nominal depth
    # (geom3d.seal_fraction), so "depth 30" is 21.7 mm; a hex cell with vertical
    # walls is 30 mm of cavity at depth 30.
    #
    # The sweep_shapes analysis found usable aspect = seal_frac*depth/pitch to
    # be the best single predictor of the score (Spearman -0.876, R^2 = 0.73).
    # This block walks the honeycomb from usable aspect 4 up to 20, a range no
    # geometry in this project has ever entered, and which the bird-of-paradise
    # cavities sit inside (aspect 7-80, reference/SUMMARY.md 3.1).
    for pitch in (2.5, 3.75, 5.5, 7.5):
        for depth in (20.0, 30.0, 40.0, 50.0):
            for wt in (0.3, 0.4, 0.6):
                # straight wall vs tapered. Tapered is the self-supporting
                # direction for FDM and adds stiffness, but it also eats cavity
                # volume from the bottom up, so it is not obviously better and
                # is measured rather than assumed.
                for wb in (wt, 3.0 * wt):
                    topo("honeycomb", pitch=pitch, depth=depth,
                         wall_top=wt, wall_bot=wb)

    # --- LEANING cells: the two results of the night in one structure -------
    #
    # shingle   inclined plates beat the cone 4.8x at theta=0 under the
    #           SPECULAR material (0.00040 vs 0.00193) and lose under the
    #           diffuse one, where there is no bounce to redirect.
    # honeycomb narrow cells that never seal, so the full nominal depth is
    #           cavity -- which is what holds up under a DIFFUSE material.
    #
    # A leaning cell has both: the cross-section stays narrow and full-depth,
    # and every wall is inclined. Built by displacing the Voronoi sites with
    # depth along a smooth direction field, so the tessellation stays exact.
    # See geom_topo._build_honeycomb for why per-cell random lean does not work
    # -- it dropped 77% of the walls, and the reason is geometry, not code.
    for pitch in (3.75, 5.5):
        for depth in (30.0, 50.0):
            for lean in (0.0, 10.0, 20.0, 30.0):
                topo("honeycomb", pitch=pitch, depth=depth,
                     wall_top=0.4, wall_bot=1.2, cell_lean_deg=lean,
                     cell_lean_domain=16.0)

    # --- geom_cell: the other cavity-lattice family -------------------------
    # A sibling module, built independently. Its `mixed` variant thins the seed
    # set so cell AREA varies ~3x, which is a different kind of irregularity
    # from geom_topo's jittered-but-equal-area Voronoi, and its `reentrant`
    # walls diverge with depth.
    #
    # `reentrant` lean is BOUNDED and the bound is not obvious: diverging walls
    # eventually meet the neighbouring cell's walls, so the cell reseals like a
    # pillar array, just later. The module's own slice-and-flood-fill check
    # measured a 10 degree lean sealing at 95% of depth, which would have made
    # usable_aspect -- the top predictor in analysis_shapes.md 5 -- report a
    # nearly closed structure as fully open. Hence lean <= 6.
    #
    # `nested` is only run at a COARSE primary: at pitch 3.75 it is 2.12 M
    # faces, past the point where geom_topo's truss had to be cut.
    def cell(variant, **kw):
        prm = dict(variant=variant, face_w=FACE, face_h=FACE,
                   margin_depths=MARGIN_DEPTHS, backing=2.0)
        prm.update(kw)
        out.append(("cell", "c_" + variant, prm))

    for variant in ("square", "triangle", "mixed", "reentrant"):
        for pitch in (3.75, 5.5, 7.5):
            for depth in (30.0, 50.0):
                cell(variant, pitch=pitch, depth=depth,
                     wall_top=0.4, wall_bot=1.2)
    for lean in (0.0, 3.0, 6.0):
        cell("reentrant", pitch=5.5, depth=30.0, wall_top=0.4, wall_bot=1.2,
             lean_deg=lean)
    for depth in (30.0, 50.0):
        cell("nested", pitch=11.0, depth=depth, wall_top=0.4, wall_bot=1.2)

    # --- ROUND 3: every winner is still sitting on the edge of its range ----
    #
    # After 352 designs the standings, worst-of-three-materials, against the
    # cone re-measured in the same frame:
    #
    #     shingle  p5.5 d30 tilt 5     0.00215   0.83x the cone
    #     cone     p3.75 d30           0.00258   1.00x
    #     honeycomb p7.5 d50 wall 0.3  0.00265   1.03x
    #     truss    p5.5 d30 L3 r0.6    0.00473   1.83x
    #
    # Three of those are boundary values, which means the range was wrong, not
    # that the optimum was found. This block opens each one further. Truss is
    # NOT extended: it is 1.83x behind and its failure is structural, not a
    # tuning problem -- it presents struts at near-grazing incidence and swings
    # 4.6x between the two materials, the widest of anything measured.

    # tilt 5 was the smallest tilt tried and it won. Tilt is measured from the
    # panel normal, so this walks the plates to nearly vertical. The builder
    # clamps tilt to >= 5 degrees, so tilt_jitter has to come down with it or
    # every design here piles onto that clamp and reads as a false plateau --
    # which is exactly what would have hidden the effect.
    # NOTE: the first attempt at this block was VOID. geom_topo clamped tilt to
    # >= 5 degrees, so tilt 1, 2 and 3 all built the same 5-degree geometry and
    # returned results identical to five decimal places. It read as a plateau.
    # The clamp is now 0; the 450 affected rows are in
    # results/__void__sweep_topo_tiltclamp.csv and removed from the live CSV.
    # tilt 0 is a vertical fin, which is where this series is heading anyway.
    for depth in (20.0, 30.0, 50.0):
        for pitch in (3.75, 5.5, 7.5):
            for tilt in (0.0, 1.0, 2.0, 3.0):
                topo("shingle", pitch=pitch, depth=depth, tilt_deg=tilt,
                     plate_over=1.15, plate_t_top=0.05, plate_t_bot=0.9,
                     tilt_jitter=0.0, azimuth_jitter=180.0)
    # plate_over 1.15 beat 1.45 everywhere, and 1.15 was the smaller of the two
    # values tried. Below 1.0 the plates stop overlapping at all.
    for over in (1.00, 1.05, 1.15):
        for tilt in (2.0, 5.0):
            topo("shingle", pitch=5.5, depth=30.0, tilt_deg=tilt,
                 plate_over=over, plate_t_top=0.05, plate_t_bot=0.9,
                 tilt_jitter=0.0)

    # honeycomb won with wall_top = wall_bot = 0.3, the THINNEST and the only
    # straight-walled value in the grid. Both edges again.
    for pitch in (5.5, 7.5, 11.0):
        for depth in (50.0,):
            for wt in (0.15, 0.2, 0.3):
                topo("honeycomb", pitch=pitch, depth=depth,
                     wall_top=wt, wall_bot=wt)

    # --- ROUND 4: the boundaries round 3 moved but did not close -----------
    #
    #     shingle   p5.5 d50 tilt 5   0.00209   0.81x the cone   <- depth 50 = edge
    #     honeycomb p7.5 d50 w0.15    0.00234   0.91x            <- w 0.15 = edge
    #
    # Straight walls at 0.15 mm now BEAT the cone, and 0.15 was again the
    # thinnest value offered. Below one nozzle (0.4 mm) nothing here is
    # printable as a solid wall, so 0.05-0.10 is an optics-only probe: it says
    # how much of the honeycomb's remaining gap to the shingle is wall area and
    # how much is topology. Tagged as a probe, not as a candidate design.
    for pitch in (5.5, 7.5, 11.0):
        for wt in (0.05, 0.10):
            topo("honeycomb", pitch=pitch, depth=50.0,
                 wall_top=wt, wall_bot=wt)

    # depth 50 was the deepest offered to both families and both chose it. The
    # panel envelope in CONTEXT.md is 30-100 mm, so 80 is inside spec and 100
    # is the wall.
    for depth in (80.0, 100.0):
        for pitch in (5.5, 7.5):
            topo("shingle", pitch=pitch, depth=depth, tilt_deg=2.0,
                 plate_over=1.15, plate_t_top=0.05, plate_t_bot=0.9,
                 tilt_jitter=0.0)
            topo("honeycomb", pitch=pitch, depth=depth,
                 wall_top=0.15, wall_bot=0.15)

    # The knife edge has never been swept for the shingle at its winning tilt.
    # It is that family's tip radius -- the one variable the exposed-area law
    # would have called decisive, and the law is dead, so this is a real
    # question rather than a foregone one. 0.4 is one nozzle.
    for t_top in (0.02, 0.05, 0.10, 0.20, 0.40):
        topo("shingle", pitch=5.5, depth=50.0, tilt_deg=2.0, plate_over=1.15,
             plate_t_top=t_top, plate_t_bot=0.9, tilt_jitter=0.0)

    # --- ROUND 5: resolve the crossing, because that is what sets the optimum
    #
    # With the 5-degree clamp removed the tilt series finally resolved, and it
    # is not the monotone trend it looked like. The two material extremes want
    # OPPOSITE tilts (p5.5 d30):
    #
    #     tilt      1      3      5     15     20     30
    #     d00   0.00344 0.00286 0.00197 0.00091 0.00068 0.00114   <- min at ~20
    #     d100  0.00206 0.00207 0.00215 0.00252 0.00275 0.00337   <- min at ~1
    #
    # So the worst-of-both score is minimised where the two curves CROSS, not
    # at either one's optimum, and the crossing sits between 2 and 10 degrees
    # with only three samples in it. Everything about which design to build
    # turns on a region measured at tilt 3, 5 and 10.
    #
    # This also retires my own extrapolation from round 3 -- "tilt lower is
    # better, keep going" -- which was the clamp plus a combined score that
    # happened to be set by d100 down there. Below 5 degrees d00 gets rapidly
    # worse and it takes the score with it.
    for depth in (30.0, 50.0, 80.0):
        for pitch in (3.75, 5.5, 7.5):
            for tilt in (4.0, 6.0, 7.0, 8.0, 12.0):
                topo("shingle", pitch=pitch, depth=depth, tilt_deg=tilt,
                     plate_over=1.15, plate_t_top=0.05, plate_t_bot=0.9,
                     tilt_jitter=0.0)

    # tilt_jitter has never been swept at the winning tilt. A spread of tilts
    # samples BOTH sides of the crossing within one panel, which is a different
    # thing from picking the crossing point -- the worst case over a mixture
    # can beat the worst case of any single member.
    for tj in (2.0, 5.0, 10.0):
        for tilt in (6.0, 10.0):
            topo("shingle", pitch=5.5, depth=50.0, tilt_deg=tilt,
                 plate_over=1.15, plate_t_top=0.05, plate_t_bot=0.9,
                 tilt_jitter=tj)

    return out


def tag_for(family, topology, prm):
    if family == "cone3d":
        return "CONE_p%04d_d%02d" % (prm["pitch"] * 100, prm["depth"])
    if family == "cell":
        return "CELL_%s_p%04d_d%02d_ln%02d" % (
            prm["variant"][:4].upper(), prm["pitch"] * 100, prm["depth"],
            prm.get("lean_deg", 6.0 if prm["variant"] == "reentrant" else 0.0))
    if topology == "shingle":
        return "SHIN_p%04d_d%02d_t%02d_o%03d_k%03d" % (
            prm["pitch"] * 100, prm["depth"], prm["tilt_deg"],
            prm.get("plate_over", 1.45) * 100,
            prm.get("plate_t_top", 0.05) * 1000)
    if topology == "truss":
        return "TRUS_p%04d_d%02d_L%d_r%03d_k%d" % (
            prm["pitch"] * 100, prm["depth"], prm["layers"],
            prm["strut_r"] * 100, prm.get("links", 2))
    return "HONE_p%04d_d%02d_wt%03d_wb%03d_ln%02d" % (
        prm["pitch"] * 100, prm["depth"],
        prm.get("wall_top", 0.4) * 100, prm.get("wall_bot", 1.2) * 100,
        prm.get("cell_lean_deg", 0.0))


def main():
    smoke = bool(os.environ.get("SMOKE"))
    os.makedirs(RENDERS, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)
    seen = done_tags(OUTCSV)
    new = not os.path.exists(OUTCSV)
    fh = open(OUTCSV, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()
        fh.flush()

    grid = designs(smoke)
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[TOPO] %d designs x %d materials = %d runs, %d already done%s"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen),
             "  (SMOKE)" if smoke else ""), flush=True)

    t0, n = time.time(), 0
    for family, topology, prm in grid:
        tag = tag_for(family, topology, prm)
        if family == "topo":
            est = GT.TopoParams(**prm).exposed_fraction_est()
        elif family == "cell":
            est = GC.CellParams(**prm).exposed_fraction_est()
        else:
            est = G3.Cone3DParams(**prm).tip_fraction()
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            # another shard is measuring this design; NSHARD unset makes
            # take() always true, so an unsharded run is unchanged
            if not take(tag):
                continue
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": family,
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True,
                   "spec_roughness": SPEC_ROUGHNESS,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": SPEC_ROUGHNESS},
                   "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": t}
                               for t in THETAS]}
            cfg.update({k: v for k, v in COAT.items()
                        if k not in ("spec_roughness",)})
            cfg["material_mode"] = "coating"
            t1 = time.time()
            try:
                res = BR.run(cfg)
            except Exception as e:              # one bad design must not end it
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            pj = json.dumps(prm, sort_keys=True)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "family": family,
                            "topology": topology, "diffuse_frac": mname,
                            "pitch": prm["pitch"], "depth": prm["depth"],
                            "aspect": prm["depth"] / prm["pitch"],
                            "exposed_est": est, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            el = time.time() - t0
            print("[%4d/%4d] %-34s %-5s %5.1fs  t+%5.0fs  eta %5.0fs"
                  % (n, total, tag, mname, time.time() - t1, el,
                     el / max(n, 1) * (total - n)), flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
