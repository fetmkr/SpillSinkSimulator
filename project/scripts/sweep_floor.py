"""
Phase 4: how little depth does the FLOOR of a honeycomb cell actually need?

    Blender --background --factory-startup --python scripts/sweep_floor.py

THE QUESTION. Phase 3 proved the honeycomb's head-on failure lives at the
BOTTOM of the cell, not at its walls or its mouth:

    honeycomb alone                   1.639
    honeycomb over FINER HONEYCOMB    1.640     control: tube still ends flat
    honeycomb over CONE               0.121     only the floor changed

But phase 3 bought that by giving the cone half the envelope, and a cone needs
its depth in one continuous cavity -- 25 mm of cone reads 0.2709 % against
0.2170 % for 50 mm of cone. So the stack won head-on and lost total.

If the mechanism is really the FLOOR, the floor should not need 25 mm. It
should need two or three. This sweep spends 2, 3 or 5 mm of the same 50 mm
envelope on a shaped floor and keeps the rest as tube.

THE PRE-REGISTERED PREDICTION, written before any render. If phase 3's
mechanism is right:

    head-on   collapses at the SHALLOWEST floor tried, because what matters is
              that a normal-incidence ray no longer meets a surface square-on,
              and a 2 mm feature already guarantees that.
    total     barely moves, because 47 mm of tube is 94 % of 50 mm of tube.
    form      does NOT improve. Form is the TOP layer's job and the top layer
              is unchanged honeycomb; anything else would contradict phase 3.

If head-on instead scales with floor depth, the mechanism is not "the ray meets
a slope" but "the ray gets lost in a deep cavity", and the floor is just a
short cone -- which would mean phase 4 has no answer and the cone wins.

`gap` is the control that separates SHAPE from DISTANCE: same 47 mm tube, same
3 mm of envelope, but the slab is simply moved back and left flat. If gap
matches a shaped floor, nobody needs to emboss anything.

WHAT IS NOT TESTED HERE, and why. A rougher or more diffuse COATING on the
floor was the fourth option asked for. It needs no sweep: `form_roughness.json`
already measured a flat plate and a honeycomb across five specular roughnesses
and they track each other to within 0.4 % at every one of them --

    roughness   0.1     0.2     0.3     0.4     0.5
    flat      119.925   7.649   1.644   0.635   0.361
    honeycomb  93.259   7.522   1.639   0.634   0.360

-- so coating moves both together and never separates the honeycomb from the
flat plate it is trying to beat. Geometry is the only lever that does.

Scoring identical to phases 2 and 3: worst rho_dh over theta 0/+-20/+-40, then
worst over the three coating models, over three geometry seeds.
"""

import sys
import os
import csv
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
import geom_stack as ST                                            # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
RENDERS = os.path.join(ROOT, "renders", "floor")
OUTCSV = os.path.join(RESULTS, "sweep_floor.csv")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
ENVELOPE = 50.0                  # total, ALWAYS -- the floor is taken from it
MARGIN = 2.0
SEEDS = (23, 101, 102)

# THE TUBE, and why there are two kinds of it.
#
# comb: the bought honeycomb. 6.5/0.08 is the product at the user's handling
# floor, 5.2/0.05 the finest foil that still survives being carried. These are
# the CLEAN mechanism test -- a honeycomb top layer contributes nothing to form
# destruction (0.98x, phase 2), so anything that moves is the floor's doing and
# there is exactly one variable.
#
# blade: the design that can actually win all three axes, which the honeycomb
# cannot. Phase 3 proved form is set by the TOP layer, so a comb-topped panel
# is stuck at 0.98x smear forever and phase 4 on comb alone can win at most two
# of three. The blade array is FIRST on total among buildable designs (0.2065 %
# at 0.05 mm) and 3.44x on form -- and fails head-on at 1.150 for the same
# reason the honeycomb does: looking straight in, you see the flat slab between
# the blades. If a 2-3 mm floor fixes the blade the way it fixes the comb, all
# three axes land on one design.
TUBES = {
    "p650f080": ("comb", dict(pitch=6.5, wall_top=0.08, wall_bot=0.08,
                              jitter=0.0)),
    "p520f050": ("comb", dict(pitch=5.2, wall_top=0.05, wall_bot=0.05,
                              jitter=0.0)),
    # plate_over is plate width / pitch: >1 makes neighbours overlap. It is
    # spelled out rather than left to default because the first run of this
    # sweep omitted it, took geom_topo's 1.45, and wrote a params_json that did
    # not say so -- a CSV that does not record the geometry it measured. Those
    # rows were voided.
    #
    # BOTH values are carried because they disagree. `sweep_topo.py` line 284
    # records "plate_over 1.15 beat 1.45 everywhere" from phase 2, measured at
    # 30 mm depth; the accidental 1.45 run here, at 50 mm, came out 1.65x
    # DARKER. One of those is depth-dependent and the other is wrong, and the
    # only way to find out which is to measure them side by side at the same
    # depth in the same sweep.
    "bl050o115": ("shingle", dict(pitch=5.5, plate_t_top=0.05,
                                  plate_t_bot=0.05, tilt_deg=2.0,
                                  tilt_jitter=0.0, azimuth_mode="grid",
                                  jitter=0.30, plate_over=1.15)),
    "bl050o145": ("shingle", dict(pitch=5.5, plate_t_top=0.05,
                                  plate_t_bot=0.05, tilt_deg=2.0,
                                  tilt_jitter=0.0, azimuth_mode="grid",
                                  jitter=0.30, plate_over=1.45)),
    "bl100o115": ("shingle", dict(pitch=5.5, plate_t_top=0.10,
                                  plate_t_bot=0.10, tilt_deg=2.0,
                                  tilt_jitter=0.0, azimuth_mode="grid",
                                  jitter=0.30, plate_over=1.15)),
    "bl100o145": ("shingle", dict(pitch=5.5, plate_t_top=0.10,
                                  plate_t_bot=0.10, tilt_deg=2.0,
                                  tilt_jitter=0.0, azimuth_mode="grid",
                                  jitter=0.30, plate_over=1.45)),
}


def tube_feature(kind, tp):
    """Minimum solid dimension of the tube layer, and who makes it."""
    if kind == "comb":
        return "expanded foil", tp["wall_top"]
    return "sheet, grid", tp["plate_t_top"]

FLOOR_DEPTHS = (2.0, 3.0, 5.0)
FLOOR_PITCH = 2.0                # features per cell: ~3x3 in a 6.5 mm cell

FIELDS = ["tag", "family", "topology", "process", "feature", "seed",
          "diffuse_frac", "tube", "tube_kind", "tube_pitch", "tube_wall",
          "tube_depth",
          "floor", "floor_depth", "floor_pitch", "depth", "aspect",
          "exposed_est", "theta", "rho", "control", "params_json"]


def floor_params(kind, ref):
    """Bottom-layer parameters. `margin_depth_ref` is the whole envelope so a
    3 mm floor still reaches under every part of the tube a tilted camera can
    see -- without it the floor stops 6 mm out and the tube stands on nothing."""
    if kind == "cone":
        return dict(pitch=FLOOR_PITCH, tip_radius=0.1, jitter=0.30,
                    radial_seg=16, height_seg=6, depth_jitter=0.0,
                    profile_power=1.0)
    if kind == "gap":
        return dict(margin_depth_ref=ref)
    if kind == "pyramid":
        return dict(pitch=FLOOR_PITCH, margin_depth_ref=ref, tip_flat=0.1)
    return dict(pitch=FLOOR_PITCH, margin_depth_ref=ref)      # wave


# process and minimum feature of the FLOOR, which is a separate part bought or
# pressed on its own. The tube's own 0.05-0.08 mm foil is handled by
# analyze_buildable.stack_process, which takes the finer of the two layers.
FLOOR_PROC = {"cone": ("mould", 0.20),        # tip radius 0.1 -> 0.2 diameter
              "pyramid": ("press", 0.10),     # apex flat
              "wave": ("press", 0.30),        # no edge; min radius of curvature
              "gap": ("none", 99.0)}          # nothing is made


def designs():
    out = []
    for seed in SEEDS:
        for tname, (tk, tp) in TUBES.items():
            # the control: full-depth tube, flat slab, no floor at all
            out.append(("FL_%s_flat_d00_s%02d" % (tname, seed), tname, tk, tp,
                        "flat", 0.0, seed))
            for kind in ("cone", "pyramid", "wave", "gap"):
                for fd in FLOOR_DEPTHS:
                    out.append(("FL_%s_%s_d%02d_s%02d"
                                % (tname, kind, fd * 10, seed),
                                tname, tk, tp, kind, fd, seed))
    return out



def open_append(path, fields):
    """Append to `path`, but ONLY if its header is exactly `fields`.

    `csv.DictWriter` does not compare its fieldnames against the header already
    on disk. Adding one column to FIELDS and re-running a resumable sweep
    therefore appends 22-column rows under a 21-column header, and every later
    `DictReader` silently shifts each new row by one -- `rho` reads a `theta`,
    and nothing anywhere raises. That happened here on 2026-08-14 with
    `tube_kind`; the rows were recoverable only because the two widths were
    distinguishable by length.

    A schema change is a new file or a migration, never an append.
    """
    import csv as _csv
    if os.path.exists(path):
        with open(path) as fh:
            have = next(_csv.reader(fh), None)
        if have is not None and have != list(fields):
            raise SystemExit(
                "%s has header\n  %s\nbut this script writes\n  %s\n"
                "Appending would shift every new row. Migrate the file or "
                "write a new one." % (os.path.basename(path),
                                      ",".join(have), ",".join(fields)))
        new = False
    else:
        new = True
    fh = open(path, "a", newline="")
    w = _csv.DictWriter(fh, fieldnames=list(fields))
    if new:
        w.writeheader()
        fh.flush()
    return fh, w

def done_tags(path):
    if not os.path.exists(path):
        return set()
    return {(r["tag"], r["diffuse_frac"]) for r in csv.DictReader(open(path))}


def build_params(tk, tp, kind, fd, seed):
    """Stack parameters, or single-layer parameters for the flat control."""
    if kind == "flat":
        return None, dict(topology=tk, face_w=FACE, face_h=FACE,
                          depth=ENVELOPE, margin_depths=MARGIN, backing=2.0,
                          seed=seed, **tp)
    prm = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN, backing=2.0,
               seed=seed,
               top=tk, top_depth=ENVELOPE - fd, top_params=dict(tp),
               bot=kind, bot_depth=fd,
               bot_params=floor_params(kind, ENVELOPE))
    return ST.StackParams(**prm), prm


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)

    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[FLOOR] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for tag, tname, tk, tp, kind, fd, seed in grid:
        sp, prm = build_params(tk, tp, kind, fd, seed)
        family = "topo" if kind == "flat" else "stack"
        tproc, tfeat = tube_feature(tk, tp)
        if kind == "flat":
            import geom_topo as GT
            est = GT.TopoParams(**prm).exposed_fraction_est()
            aspect = ENVELOPE / tp["pitch"]
            proc, feat = tproc, tfeat
        else:
            est = sp.exposed_fraction_est()
            aspect = sp.aspect()
            fp, ff = FLOOR_PROC[kind]
            # the binding constraint is whichever part has the finer feature
            proc, feat = (fp, ff) if ff < tfeat else (tproc, tfeat)
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": family,
                   "out_dir": RENDERS, "results_dir": RENDERS,
                   "samples": SAMPLES, "res_x": RES[0], "res_y": RES[1],
                   "gpu": True, "spec_roughness": 0.30,
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": 0.30},
                   "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": t}
                               for t in THETAS]}
            cfg.update({k: v for k, v in COAT.items()
                        if k not in ("spec_roughness",)})
            cfg["material_mode"] = "coating"
            try:
                res = BR.run(cfg)
            except Exception as e:
                print("[FAIL] %s %s: %s" % (tag, mname, e), flush=True)
                continue
            pj = json.dumps(prm, sort_keys=True, default=str)
            for rec in res["modes"].values():
                w.writerow({"tag": tag, "family": "floor",
                            "topology": "%s/%s" % (tk, kind),
                            "process": proc, "feature": feat, "seed": seed,
                            "diffuse_frac": mname, "tube": tname,
                            "tube_kind": tk,
                            "tube_pitch": tp["pitch"],
                            "tube_wall": tfeat,
                            "tube_depth": ENVELOPE - fd,
                            "floor": kind, "floor_depth": fd,
                            "floor_pitch": (0.0 if kind in ("flat", "gap")
                                            else FLOOR_PITCH),
                            "depth": ENVELOPE, "aspect": aspect,
                            "exposed_est": est, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            if n % 12 == 0:
                el = time.time() - t0
                print("[%3d/%3d] %-30s eta %4.0fs"
                      % (n, total, tag, el / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
