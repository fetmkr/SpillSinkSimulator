"""
Phase 3 sweep: two structures stacked, measured on the same three axes.

    Blender --background --factory-startup --python scripts/sweep_stack.py

THE QUESTION. Phase 2 ended with no single layer good at all three axes:

    commercial honeycomb   total #2   form #11   head-on #11
    cone                   total #5   form  #1   head-on  #1
    blade array (grid)     total #3   form  #2   head-on  #4

The honeycomb swallows energy but never moves it sideways, and its flat wall
tops face a viewer exactly like the flat plate it replaced. The cone owns both
viewer-facing axes. So: does putting them in series beat either alone?

THE PREDICTION, WORTH WRITING DOWN BEFORE THE RENDER. Only the TOP layer is
exposed head-on -- a stack cannot hide its own first surface. So

    comb over cone   should inherit the HONEYCOMB's head-on failure (~1.64)
    cone over comb   should inherit the CONE's head-on win (~0.07)

and if that is what comes out, the useful finding is not "stacking works" but
"the top layer decides two of the three axes, so choose it for the viewer and
choose the bottom one for the energy." If it does NOT come out that way, the
prediction was wrong and the reason matters more than the ranking.

Depth is split 25/25 within the same 50 mm envelope, so a stack is compared
against single layers at equal total depth rather than being given twice the
wall to work with.

Scoring identical to phase 2: worst rho_dh over theta 0/+-20/+-40, then worst
over the three coating models, over three geometry seeds.

OUTCOME, added 2026-08-14 -- the prediction above is left exactly as written,
because a pre-registration that gets edited after the result is worthless.

    form      predicted right.  comb on top 0.99x (alone 0.98x)
                                cone on top 3.92x (alone 4.11x)
    head-on   predicted WRONG.  comb over cone 0.140, not ~1.64

Head-on is set by the BOTTOM layer, not the top. The claim in paragraph two --
that the honeycomb's flat wall tops are what faces the viewer -- is false.
Swapping only the FLOOR under an unchanged honeycomb removes 92 % of its
head-on brightness, so the brightness was coming from the flat backing slab
seen down the length of each cell. See results/FINDINGS_phase3_stack.md.
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
RENDERS = os.path.join(ROOT, "renders", "stack")
OUTCSV = os.path.join(RESULTS, "sweep_stack.csv")

FACE = 60.0
SAMPLES = 64
RES = (480, 220)
THETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
DIFFUSE_FRACS = (0.0, 0.76, 1.0)
DEPTH = 50.0
MARGIN = 2.0
SEEDS = (23, 101, 102)

# the four layer types, at the parameters phase 2 settled on
COMB = dict(pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0)
COMB_FINE = dict(pitch=3.17, wall_top=0.04, wall_bot=0.04, jitter=0.0)
CONE = dict(pitch=5.5, tip_radius=0.2, jitter=0.30, radial_seg=24,
            height_seg=12, depth_jitter=0.0, profile_power=1.0)
BLADE = dict(pitch=5.5, plate_t_top=0.1, plate_t_bot=0.1, tilt_deg=2.0,
             tilt_jitter=0.0, azimuth_mode="grid", jitter=0.30)

FIELDS = ["tag", "family", "topology", "process", "feature", "seed",
          "diffuse_frac", "pitch", "depth", "aspect", "exposed_est",
          "top", "bot", "split", "theta", "rho", "control", "params_json"]


def designs():
    out = []
    for seed in SEEDS:
        base = dict(face_w=FACE, face_h=FACE, margin_depths=MARGIN,
                    backing=2.0, seed=seed)

        def st(top, tp, bot, bp, split=0.5, proc="print", feat=0.08):
            out.append((dict(base, top=top, top_depth=DEPTH * split,
                             top_params=dict(tp),
                             bot=bot, bot_depth=DEPTH * (1 - split),
                             bot_params=dict(bp)), proc, feat, split))

        # the pairing the question is about, both ways up
        st("comb", COMB, "cone", CONE, 0.5, "foil + mould", 0.08)
        st("cone", CONE, "comb", COMB, 0.5, "mould + foil", 0.40)
        # two scales of the same bought product
        st("comb", COMB, "comb", COMB_FINE, 0.5, "expanded foil", 0.08)
        st("comb", COMB_FINE, "comb", COMB, 0.5, "expanded foil", 0.04)
        # bought cell over sheet-metal blades -- both cheap
        st("comb", COMB, "shingle", BLADE, 0.5, "foil + sheet", 0.08)
        st("shingle", BLADE, "comb", COMB, 0.5, "sheet + foil", 0.10)
        # how much of the depth should the top layer get
        for sp in (0.25, 0.75):
            st("cone", CONE, "comb", COMB, sp, "mould + foil", 0.40)
            st("comb", COMB, "cone", CONE, sp, "foil + mould", 0.08)
    return out


def tag_for(prm, split):
    return "ST_%s-%s_%02d_s%02d" % (prm["top"][:4], prm["bot"][:4],
                                    split * 100, prm["seed"])



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


def main():
    os.makedirs(RENDERS, exist_ok=True)
    seen = done_tags(OUTCSV)
    fh, w = open_append(OUTCSV, FIELDS)

    grid = designs()
    total = len(grid) * len(DIFFUSE_FRACS)
    print("[STACK] %d designs x %d materials = %d runs, %d done"
          % (len(grid), len(DIFFUSE_FRACS), total, len(seen)), flush=True)

    t0, n = time.time(), 0
    for prm, proc, feat, split in grid:
        tag = tag_for(prm, split)
        sp = ST.StackParams(**prm)
        est = sp.exposed_fraction_est()
        for dfrac in DIFFUSE_FRACS:
            mname = "d%02d" % (dfrac * 100)
            n += 1
            if (tag, mname) in seen:
                continue
            body, spec = BR.coating_split(dfrac)
            cfg = {"tag": "%s_%s" % (tag, mname), "family": "stack",
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
                w.writerow({"tag": tag, "family": "stack",
                            "topology": "%s/%s" % (prm["top"], prm["bot"]),
                            "process": proc, "feature": feat,
                            "seed": prm["seed"], "diffuse_frac": mname,
                            "pitch": sp.pitch, "depth": DEPTH,
                            "aspect": sp.aspect(), "exposed_est": est,
                            "top": prm["top"], "bot": prm["bot"],
                            "split": split, "theta": rec["theta"],
                            "rho": rec["panel"]["mean"],
                            "control": rec["control"]["mean"],
                            "params_json": pj})
            fh.flush()
            el = time.time() - t0
            if n % 9 == 0:
                print("[%3d/%3d] %-26s eta %4.0fs"
                      % (n, total, tag, el / max(n, 1) * (total - n)),
                      flush=True)
    fh.close()
    print("[DONE] %s  (%.0fs)" % (OUTCSV, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
