"""When the hole is smaller than the sheet is thick, it stops being a window.

    Blender --background --factory-startup --python scripts/sweep_perf2.py

`sweep_perf.py` perforated a pyramid shell and found that holes help -- 0.338 %
unperforated down to 0.283 % at 70 % open, pitch 5.5 -- but that a shell of any
kind loses to a solid sharp pyramid (0.179 %), because the sheet edge at the
mouth is exposed area no perforation can remove.

Those holes were 0.86 mm in a 0.5 mm sheet: **1.7 times wider than the sheet is
thick**, which is a window. A hole narrower than the sheet is thick is not a
window, it is a TUBE of aspect `t/d`, and a ray entering it off-axis hits the
bore before it gets through. That is the same distinction acoustics draws
between a perforated panel and a MICRO-perforated one, where the losses move
from the cavity behind into the holes themselves.

So this holds the open area fixed and shrinks the holes, which is the only way
to change the ratio that matters:

    hole aspect = sheet thickness / hole width

    nu = 4    hole 0.86 mm    aspect 0.6      window
    nu = 8    hole 0.43 mm    aspect 1.2      borderline
    nu = 16   hole 0.21 mm    aspect 2.3      tube

and separately thickens the sheet at a fixed hole size, which moves the same
ratio the other way and costs mouth area while doing it.

    PREDICTION, written before any render.

    1. SHRINKING THE HOLES AT FIXED OPEN AREA WILL HELP, by 10-30 % from
       nu = 4 to nu = 16. Each hole becomes a small deep well: a ray that would
       have passed straight through a window now hits the bore at least once,
       and every extra bounce is another factor of the coating's 1 %.

    2. IT WILL NOT BE ENOUGH TO BEAT THE SOLID SHARP PYRAMID. The sheet edge at
       the mouth is 18 % of the cell at pitch 5.5 and is untouched by anything
       done to the holes. I expect the best perforated shell to land near
       0.24-0.26 % against the solid pyramid's 0.179 %. If it DOES beat it, the
       exposed-area law that has ordered five sweeps is weaker than it looks
       and that is the finding, not the design.

    3. THICKENING THE SHEET AT A FIXED HOLE SIZE WILL LOSE, not win, even
       though it raises the hole aspect. It raises the mouth edge in exact
       proportion -- 4t/p -- and the exposed-area law says the mouth is worth
       more than the bore. This is the cleanest test of that law in the whole
       study: two effects with opposite signs, one knob.

    If prediction 3 fails and a thicker sheet wins, the bore matters more than
    the mouth and the whole family should be re-optimised around thick,
    finely-perforated plate.

The anchor is the perforated shell at pitch 5.5, open 0.35, nu 4 -- the identical
`params_json` `sweep_perf.csv` recorded -- so gate check 8 ties the two files.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "sweep_perf2.csv")
OUT = "/tmp/perf2"

FACE, DEPTH, PITCH = 60.0, 50.0, 5.5
OPEN = 0.35
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))

# (nu, nv, wall) -- first block shrinks the hole at 0.5 mm sheet, second
# thickens the sheet at the finest hole the mesh can afford.
CASES = [(4, 6, 0.5), (8, 12, 0.5), (12, 18, 0.5),
         (8, 12, 0.25), (8, 12, 1.0)]

COLS = ["tag", "family", "topology", "shape", "pitch", "open_frac", "wall",
        "nu", "nv", "hole_mm", "hole_aspect", "edge_frac_est", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def hole_mm(pitch, nu, open_frac):
    """Hole width: the gap left when each cell keeps sqrt(1-open) of its side."""
    return (pitch / nu) * (1.0 - (1.0 - open_frac) ** 0.5)


def render(prm, tag):
    import blender_render as BR
    from cone3d_sweep import COAT
    rows = []
    for mat, df in MATS:
        body, spec = BR.coating_split(df)
        for th in THETAS:
            cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th), "family": "perf",
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
    print("=" * 78)
    print("HOLE SIZE AGAINST SHEET THICKNESS, open area held at %.0f %%"
          % (100 * OPEN))
    print("=" * 78)
    rows = []
    for nu, nv, wall in CASES:
        d = hole_mm(PITCH, nu, OPEN)
        asp = wall / max(d, 1e-9)
        edge = 2.0 * wall / PITCH
        prm = {"face_w": FACE, "face_h": FACE, "depth": DEPTH,
               "pitch": PITCH, "wall": wall, "open_frac": OPEN,
               "nu": nu, "nv": nv, "margin_depths": 2.0, "backing": 2.0,
               "seed": 23}
        tag = "PF_p0550_o35" if (nu, nv, wall) == (4, 6, 0.5) else \
            "P2_n%02d_w%03d" % (nu, round(wall * 100))
        print("\n  nu %2d  wall %.2f mm  hole %.3f mm  aspect t/d %.2f  "
              "mouth edge %.1f %%" % (nu, wall, d, asp, 100 * edge),
              flush=True)
        try:
            got = render(prm, tag)
        except Exception as exc:
            print("     FAILED: %s" % str(exc)[:110])
            continue
        for mat, th, rho, ctrl in got:
            rows.append({"tag": tag, "family": "perf",
                         "topology": "perforated pyramid",
                         "shape": "perforated pyramid", "pitch": PITCH,
                         "open_frac": OPEN, "wall": wall, "nu": nu, "nv": nv,
                         "hole_mm": round(d, 5),
                         "hole_aspect": round(asp, 4),
                         "edge_frac_est": round(edge, 5), "seed": 23,
                         "diffuse_frac": mat, "theta": th, "rho": rho,
                         "control": ctrl,
                         "params_json": json.dumps(prm, sort_keys=True)})
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
        meta[r["tag"]] = (r["nu"], r["wall"], r["hole_mm"], r["hole_aspect"],
                          r["edge_frac_est"])
    print("\n  %-16s %4s %7s %9s %11s %11s %11s"
          % ("tag", "nu", "wall", "hole mm", "t/d", "mouth edge", "worst rho"))
    for t in sorted(worst, key=lambda t: (meta[t][1], meta[t][0])):
        nu, wall, d, asp, edge = meta[t]
        print("  %-16s %4d %7.2f %9.3f %11.2f %10.1f%% %10.5f%%"
              % (t, nu, wall, d, asp, 100 * edge, 100 * worst[t]))
    print("\n  for reference: solid sharp pyramid at pitch 5.5 = 0.17910 %")
    return 0


if __name__ == "__main__":
    sys.exit(main())
