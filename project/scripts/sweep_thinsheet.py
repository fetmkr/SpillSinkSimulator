"""Which renderer is right about a 0.05 mm blade?

    Blender --background --factory-startup --python scripts/sweep_thinsheet.py

WHY THIS AND NOT A DESIGN QUESTION. The listed candidates for this turn are
answered: floor pitch is in `sweep_floorpitch.csv`, the pyramid apex flat in
`sweep_tipflat.csv`, the cone floor in `sweep_conefloor.csv`, and the blade
neighbourhood at tilt / azimuth / pitch under a pyramid in
`sweep_bladehood.csv`. What is NOT answered, and what makes further blade
optimisation premature, is this:

    plate_t          0.05 mm   0.2 mm   0.5 mm   1.0 mm   2.0 mm
    Mitsuba - Cycles  +26.9 %   +8.7 %   -1.3 %   -6.1 %   -9.1 %

Measured this session at 1024 spp with matched measurement windows, Lambertian
0.01, normal incidence. The disagreement is flat from 256 to 4096 spp, so it is
not sampling. The study's three-axis winner is a 0.05 mm blade -- exactly where
two independent codes disagree by 27 % -- and refining tilt or azimuth around a
design whose reflectance carries an unquantified 27 % systematic is measuring
noise with a micrometer. Which code is right comes first.

THE TWO MECHANISMS, AND HOW TO TELL THEM APART. For a dark cavity,

    rho_dh  ~=  f_first * rho  +  (interior, which carries rho^n)

so a disagreement can live in the FIRST hit -- how much blade edge each code
sees at the mouth, a geometry-sampling question at 0.05 mm -- or in the NUMBER
OF BOUNCES n, a transport question. They separate cleanly by sweeping the
Lambertian reflectance: measure rho_dh at rho = 0.01, 0.1 and 0.5 and read the
effective bounce count

    n_eff  =  ln(rho_dh) / ln(rho)

A first-hit disagreement leaves n_eff equal between the codes and shifts the
whole curve. A transport disagreement moves n_eff itself.

    PREDICTION 1. At rho = 1.0 a closed cavity must return 1.000 in BOTH codes
    at every thickness. Energy conservation does not care whether a ray passes
    through a blade -- it only cares whether light is lost -- so I expect this
    to hold everywhere and to NOT discriminate. It runs first because if it
    fails, the harness is wrong and nothing below means anything.

    PREDICTION 2. n_eff will AGREE between the codes to better than 5 % at
    every thickness, and the 27 % gap will show up as a scale offset. Reason: a
    0.05 mm sheet in a 100 mm panel is a 2000:1 aspect, and the thing that
    changes at that scale is whether a ray-triangle test finds a sliver, not
    how many times light bounces once it is inside. The gap grows monotonically
    as the sheet thins, which is the signature of a geometric threshold, not of
    a transport difference -- transport would depend on cavity depth and pitch,
    which are held fixed here.

    PREDICTION 3. If prediction 2 holds, CYCLES is the one to trust at 0.05 mm.
    Blender builds the blade as a closed solid from the same vertices and
    renders it with watertight Woop-style triangle intersection; the Mitsuba
    path reads a PLY written by `write_ply`, which triangulates the same quads,
    and reads HIGHER -- more light returning means fewer effective bounces,
    which is what missing a sliver of blade and letting a ray out early would
    do. I put this at maybe 60/40 and it is the weakest of the three.

    If prediction 2 FAILS -- if n_eff moves -- then the two codes disagree
    about transport in a high-aspect cavity, every blade number in phases 2-5
    is in question rather than merely offset, and that is a larger finding than
    any design result this study has produced.

THE ANCHOR. `BL_FLAT_t050_p0550_a02_grid_s23` is re-measured here under the
study's standard protocol -- 5 angles x 3 coating models, the fitted coating,
roughness 0.30 -- with the identical `params_json` that `sweep_blade.csv`
recorded, so gate check 8 has a design in common and can tell whether this
sweep's Cycles path agrees with the published one.
"""

import sys
import os
import json
import csv
import math
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
OUT = "/tmp/thinsheet"
CSV = os.path.join(RESULTS, "sweep_thinsheet.csv")

MTS_PY = os.environ.get("MTS_PYTHON", os.path.join(
    "/private/tmp/claude-501",
    "-Users-hojunsong-Desktop-Desktop---hojun-s-mbp-SpillSinkSimulator",
    "ea0cb560-6b35-43aa-9df7-9e47dc4396fa", "scratchpad",
    "mts_env", "bin", "python"))

FACE, DEPTH = 60.0, 50.0
THICK = (0.05, 0.1, 0.2, 0.5, 1.0, 2.0)
RHOS = (0.01, 0.1, 0.5, 1.0)
SPP = 1024

COLS = ["tag", "family", "topology", "renderer", "plate_t", "rho_material",
        "seed", "diffuse_frac", "theta", "rho", "control", "n_eff",
        "params_json"]


def blade_params(t):
    """Exactly the keys `sweep_blade.csv` recorded, so fingerprints match."""
    return {"azimuth_jitter": 180.0, "azimuth_mode": "grid", "backing": 2.0,
            "depth": DEPTH, "face_h": FACE, "face_w": FACE, "jitter": 0.3,
            "margin_depths": 2.0, "pitch": 5.5, "plate_over": 1.15,
            "plate_t_bot": t, "plate_t_top": t, "seed": 23,
            "tilt_deg": 2.0, "tilt_jitter": 0.0, "topology": "shingle"}


def cycles_lambert(prm, rho, theta=0.0, spp=SPP, tag="t"):
    """rho_dh(theta) in Cycles with a pure Lambertian of reflectance `rho`."""
    cfg = {"tag": tag, "family": "topo", "out_dir": OUT, "results_dir": OUT,
           "samples": spp, "res_x": 480, "res_y": 220, "gpu": True,
           "spec_roughness": 0.30, "params": prm,
           "renders": [{"mode": "hemi_view", "theta": theta}],
           "material_mode": "all_diffuse"}
    cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
    cfg.update(rho_slat=rho, rho_chamber=rho, rho_specular=rho)
    res = BR.run(cfg)
    rec = list(res["modes"].values())[0]
    return rec["panel"]["mean"], rec["control"]["mean"]


def mitsuba_lambert(prm, rho, theta=0.0, spp=SPP):
    import subprocess
    req = {"family": "topo", "params": prm, "rho": rho, "theta": theta,
           "spp": spp}
    p = subprocess.run([MTS_PY, os.path.join(HERE, "mts_worker.py")],
                       input=json.dumps(req), capture_output=True, text=True,
                       timeout=3600)
    for line in reversed((p.stdout or "").splitlines()):
        i = line.find("@@RESULT@@")
        if i >= 0:
            return json.loads(line[i + 10:])["rho_dh"]
    raise RuntimeError((p.stderr or p.stdout or "no output")[-300:])


def n_eff(rho_dh, rho):
    if rho <= 0 or rho >= 1 or rho_dh <= 0:
        return ""
    return math.log(rho_dh) / math.log(rho)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("THIN SHEET: which renderer is right about a 0.05 mm blade?")
    print("  %d thicknesses x %d reflectances x 2 codes, %d spp"
          % (len(THICK), len(RHOS), SPP))
    print("=" * 74)
    print("  %-8s %-6s %13s %13s %9s %8s %8s"
          % ("plate_t", "rho", "Cycles", "Mitsuba", "diff", "n Cyc", "n Mts"))

    for t in THICK:
        prm = blade_params(t)
        for rho in RHOS:
            tag = "TS_t%03d_r%03d" % (round(t * 1000), round(rho * 100))
            c, ctrl = cycles_lambert(prm, rho, tag=tag)
            m = mitsuba_lambert(prm, rho)
            nc, nm = n_eff(c, rho), n_eff(m, rho)
            d = (m - c) / c if c else float("nan")
            print("  %-8.2f %-6.2f %13.8f %13.8f %+8.2f%% %8s %8s"
                  % (t, rho, c, m, 100 * d,
                     "%.3f" % nc if nc != "" else "-",
                     "%.3f" % nm if nm != "" else "-"), flush=True)
            for who, v, ne in (("cycles", c, nc), ("mitsuba", m, nm)):
                rows.append({"tag": "%s_%s_s23" % (tag, who), "family": "topo",
                             "topology": "shingle", "renderer": who,
                             "plate_t": t, "rho_material": rho, "seed": 23,
                             "diffuse_frac": "lambert", "theta": 0.0,
                             "rho": v, "control": ctrl if who == "cycles" else "",
                             "n_eff": ne,
                             "params_json": json.dumps(prm, sort_keys=True)})

    # --- the anchor: the study's standard protocol on a published design ----
    print("\n  anchor: BL_FLAT_t050_p0550_a02_grid_s23 under the standard "
          "protocol")
    prm = blade_params(0.05)
    body_of = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
    for mat, df in body_of.items():
        body, spec = BR.coating_split(df)
        for th in (0.0, -20.0, 20.0, -40.0, 40.0):
            cfg = {"tag": "AN_%s_%+03.0f" % (mat, th), "family": "topo",
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
            rows.append({"tag": "BL_FLAT_t050_p0550_a02_grid_s23",
                         "family": "topo", "topology": "shingle",
                         "renderer": "cycles", "plate_t": 0.05,
                         "rho_material": "", "seed": 23, "diffuse_frac": mat,
                         "theta": th, "rho": rec["panel"]["mean"],
                         "control": rec["control"]["mean"], "n_eff": "",
                         "params_json": json.dumps(prm, sort_keys=True)})
            print("    %-5s th%+5.0f  %.8f" % (mat, th, rec["panel"]["mean"]),
                  flush=True)

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nwrote %s  (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
