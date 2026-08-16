"""Does perforating the skin of a pyramid help, and when?

    Blender --background --factory-startup --python scripts/sweep_perf.py

WHERE THIS COMES FROM. `FINDINGS_anechoic_shapes.md` found one law running
through every shape it measured: what separates them is the FLAT AREA FACING
THE VIEWER at the mouth. A sharp pyramid exposes a point and won; a truncated
one exposes a flat and came last; a hollow one folded from 0.5 mm sheet exposed
a rim that grows to 33 % of the mouth as the pitch falls, and came second last.
The cavity idea inside the hollow pyramid was never tested, only the rim in
front of it.

So: a shell with NO rim -- the skin meets the entrance plane at a knife edge --
and holes in the skin, so light gets into the cavity across the whole face
rather than only at the mouth. Interior and exterior are the same coating.
Perforated aluminium sheet is a stock product.

THE ARITHMETIC THAT SETS THE PREDICTION. A sheet of thickness `t` seen edge-on
at the mouth of a cell of pitch `p` exposes about `4 p t / p^2 = 4 t / p` of the
cell, halved where neighbours share an edge. At the study's usual pitch of
5.5 mm with 0.5 mm sheet that is 18 %, which is the same disease the hollow
pyramid had. At the RF-like pitch of 17.67 mm it is 5.7 %.

    PREDICTION, written before any render.

    1. AT PITCH 5.5 THE PERFORATED PYRAMID LOSES to the solid one, and by a lot
       -- I expect it to land near the hollow pyramid's 0.45 %, roughly 2.5x the
       solid pyramid's 0.18 %. The sheet edge is 18 % of the mouth and the
       exposed-area law says that is what decides it. Holes cannot help with
       area that is already facing the viewer.

    2. AT PITCH 17.67 IT IS COMPETITIVE, and this is the interesting case. The
       edge drops to 5.7 % and the previous sweep showed aspect ratio to be a
       weak lever -- the solid pyramid only moved 39 % across the whole 2.83 to
       9.09 range. If the coarse pitch costs little and the perforation buys a
       cavity, the two could cross.

    3. MORE OPEN AREA IS BETTER UP TO A POINT, then worse. A hole lets light in
       and the interior traps it; too many holes and there is no skin left to
       trap anything, and the structure tends toward an empty box with a
       backing slab. I expect the best open fraction between 30 and 50 %, and a
       clear turn by 70 %.

    4. THE PERFORATED PYRAMID WILL NOT BEAT THE SOLID SHARP PYRAMID at its own
       best pitch. The solid one exposes a point; nothing here exposes less
       than that. The honest hope is that it comes close while being a stock
       sheet part.

    If prediction 1 fails and perforation wins at a fine pitch, the exposed-area
    law is not as dominant as four sweeps have said, and that is worth more than
    the design result.

The anchor is the solid sharp pyramid at pitch 5.5, identical `params_json` to
the row `sweep_anechoic.csv` recorded, so gate check 8 ties the two files.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "sweep_perf.csv")
OUT = "/tmp/perf"

FACE, DEPTH = 60.0, 50.0
PITCHES = (5.5, 17.67)
OPENS = (0.0, 0.35, 0.55, 0.70)
WALL = 0.5
NU, NV = 4, 6
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))

COLS = ["tag", "family", "topology", "shape", "pitch", "open_frac", "wall",
        "edge_frac_est", "seed", "diffuse_frac", "theta", "rho", "control",
        "params_json"]


def render(family, prm, tag):
    import blender_render as BR
    from cone3d_sweep import COAT
    rows = []
    for mat, df in MATS:
        body, spec = BR.coating_split(df)
        for th in THETAS:
            cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th), "family": family,
                   "out_dir": OUT, "results_dir": OUT, "samples": 64,
                   "res_x": 480, "res_y": 220, "gpu": True,
                   "spec_roughness": 0.30, "params": prm,
                   "renders": [{"mode": "hemi_view", "theta": th}],
                   "material_mode": "coating",
                   "coating": {"body": body, "spec_scale": spec,
                               "roughness": 0.30}}
            cfg.update({k: v for k, v in COAT.items()
                        if k != "spec_roughness"})
            res = BR.run(cfg)
            rec = list(res["modes"].values())[0]
            rows.append((mat, th, rec["panel"]["mean"],
                         rec["control"]["mean"]))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 74)
    print("PERFORATED PYRAMID: does a holed skin beat a solid one?")
    print("=" * 74)
    rows = []

    for pitch in PITCHES:
        edge = 2.0 * WALL / pitch          # neighbours share the edge
        for op in OPENS:
            prm = {"face_w": FACE, "face_h": FACE, "depth": DEPTH,
                   "pitch": pitch, "wall": WALL, "open_frac": op,
                   "nu": NU, "nv": NV, "margin_depths": 2.0, "backing": 2.0,
                   "seed": 23}
            tag = "PF_p%04d_o%02d" % (round(pitch * 100), round(op * 100))
            print("\n  perforated  pitch %5.2f  open %3.0f %%  "
                  "(sheet edge ~%.1f %% of the mouth)"
                  % (pitch, 100 * op, 100 * edge), flush=True)
            try:
                got = render("perf", prm, tag)
            except Exception as exc:
                print("     FAILED: %s" % str(exc)[:110])
                continue
            for mat, th, rho, ctrl in got:
                rows.append({"tag": tag, "family": "perf",
                             "topology": "perforated pyramid",
                             "shape": "perforated pyramid", "pitch": pitch,
                             "open_frac": op, "wall": WALL,
                             "edge_frac_est": round(edge, 5), "seed": 23,
                             "diffuse_frac": mat, "theta": th, "rho": rho,
                             "control": ctrl,
                             "params_json": json.dumps(prm, sort_keys=True)})
            print("     worst %.5f %%" % (100 * max(r[2] for r in got)))

        # the solid sharp pyramid at the same pitch, for the comparison
        sp = {"kind": "pyramid", "face_w": FACE, "face_h": FACE,
              "depth": DEPTH, "pitch": pitch, "tip_flat": 0.0,
              "margin_depths": 2.0, "backing": 2.0}
        # NAME THE TAG AFTER THE PITCH IT ACTUALLY HAS. Calling this
        # `AN_pyr_a909` collided with `sweep_anechoic.csv`, where the same tag
        # means pitch 50/9.09 = 5.5006 rather than the 5.5 used here -- two
        # different designs under one name, reading 0.17910 % and 0.18151 %,
        # a 1.34 % difference that looked like a measurement disagreement and
        # was a naming one.
        tag = "SP_p%04d" % round(pitch * 100)
        print("\n  solid sharp pyramid  pitch %5.2f  (anchor)" % pitch,
              flush=True)
        got = render("floor", sp, tag)
        for mat, th, rho, ctrl in got:
            rows.append({"tag": tag, "family": "floor",
                         "topology": "pyramid", "shape": "solid pyramid",
                         "pitch": pitch, "open_frac": 0.0, "wall": 0.0,
                         "edge_frac_est": 0.0, "seed": 23,
                         "diffuse_frac": mat, "theta": th, "rho": rho,
                         "control": ctrl,
                         "params_json": json.dumps(sp, sort_keys=True)})
        print("     worst %.5f %%" % (100 * max(r[2] for r in got)))

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nwrote %s (%d rows)" % (CSV, len(rows)))

    worst, meta = {}, {}
    for r in rows:
        worst[r["tag"]] = max(worst.get(r["tag"], 0.0), r["rho"])
        meta[r["tag"]] = (r["shape"], r["pitch"], r["open_frac"])
    print("\n  %-18s %-20s %7s %7s %11s"
          % ("tag", "shape", "pitch", "open", "worst rho"))
    for t in sorted(worst, key=lambda t: (meta[t][1], meta[t][2])):
        s, p, o = meta[t]
        print("  %-18s %-20s %7.2f %6.0f%% %10.5f%%"
              % (t, s, p, 100 * o, 100 * worst[t]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
