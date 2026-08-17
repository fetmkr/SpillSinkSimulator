"""Kaster reconciliation: is his 0.65x explained by his own planar cap?

    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --factory-startup --python scripts/sweep_kaster.py

WHY. QUESTIONS.md Q19-4: the closest prior art (Kaster 2025,
arXiv:2507.05152, J. Appl. Phys. 138 174904) was cited from its abstract
only. The PDF has now been read page by page (2026-08-17). What it says:

    Material  [p.7]: reflectance 5 %, of which 85 % Lambertian and 15 %
        Gaussian (FWHM 25 deg). Absorbance 95 %. One material for
        specimen AND planar reference.
    Geometry  [p.2, p.7]: Gyroid (period 5 mm), Schwarz D (6.25 mm),
        strut lattice (2.85 mm); volumetric density 30.6 %; min feature
        0.5 mm; 40 mm discs. "To mitigate direct wide-angular
        backscatter from curved structures, we generate a planar cap
        layer" -- the top face is a PLANE cut through a 30.6 %-dense
        solid, so ~30.6 % of the frontal area is flat land at the cap.
    Results   [p.3, Table 1]: avg intensity ratio specimen/planar
        0.544-0.701 across AOI {0, 37.5, 75} x {XZ, YZ}; peak ratio
        0.259-0.613.
    Method    [p.7-8]: forward non-sequential tracing, 1e8 rays,
        hemispherical far-field receiver, ratio of receiver-cell means.

Our published claim is ~0.19x against the same-coating flat plate
(0.2145 % vs 1.141 %, QUESTIONS.md Q1 corrected). SUMMARY.md flags the
3x gap to Kaster's 0.65x as "the single number a referee will attack
first". Our tip law says flat land at the entrance plane returns like a
flat plate, in proportion to its area. Kaster's cap IS 30.6 % flat land.
Hypothesis: the gap is his cap, not our physics.

THE ANALOG. We rebuild the three players in one harness with HIS
material (rho0 = 5 %, diffuse fraction 0.85 -- coating_split(0.85,
rho0=0.05) -- glossy remainder): a flat plate; our final pyramid
(p4/d20/tip 0.1, land (0.1/4)^2 = 0.06 %); and a "Kaster cap" pyramid
p4/d20/tip 2.2127 whose flat-land fraction (2.2127/4)^2 = 30.6 % equals
his volumetric density at the cap plane. Pyramidal pits stand in for
gyroid channels: both are deep absorbing cavities behind the same flat
entrance fraction, which the tip law says is the variable that matters.
AOI set = his: 0, -37.5, -75. margin_depths 6.5 everywhere (the steep-
angle margin, phase 6.7 / sim_server precedent).

    PREDICTIONS, numeric, before any render.

    P1  FLAT PLATE READS THE MATERIAL: rho_dh(0) = 5.0 % within 3 %
        relative (coating_split holds rho_dh(0) = rho0 by construction);
        at -37.5 within 5.0-5.5 %; at -75 it RISES to 6.5-9 % (the 15 %
        glossy share is Fresnel-weighted in our model; Kaster's is not).
    P2  OUR PYRAMID vs FLAT, same material, ratio at 0 deg in
        0.13-0.25 (the family's published same-coating ratio ~0.19);
        at -75 the ratio stays below 0.35 (phase 6.7: graceful grazing).
    P3  THE CAP EXPLAINS KASTER. K_cap31 ratio at 0 deg =
        0.306 + 0.694 x (P2 ratio) = 0.40-0.50; at -75 it climbs to
        >= 0.50 (pits shadow at grazing, the cap face takes over). If
        P3 lands in 0.40-0.70 while our pyramid sits 3x lower AT THE
        SAME MATERIAL AND ANGLES, the 3x gap to his published 0.65 is
        his 30.6 % planar cap, and the comparison in SUMMARY.md ss4 can
        stop calling it a discrepancy.
    P4  ROUGHNESS IS NOT THE STORY: every ratio above moves less than
        15 % relative between glossy roughness 0.30 and 0.15 (the
        bracket stands in for his 25-deg-FWHM Gaussian lobe, which sits
        between them; form_roughness.json showed flat and structured
        panels tracking together across roughness).

    NOT COMPARED, and why. Kaster's "avg intensity ratio" is a mean
    over receiver CELLS of a far-field intensity map; ours is the
    energy ratio rho_dh(specimen)/rho_dh(flat). His statistic weights
    directions, ours weights energy. Landing inside his 0.54-0.70 band
    is therefore supporting evidence, not an identity; the FINDINGS
    must state this. Smear / head-on axes: not in his paper at all, so
    this sweep compares the total axis only and says so.

Anchor: KA_anchor_s23 re-measures FL_p650f080_flat (comb 6.5/0.08,
depth 50, seed 23) at the full 5-theta x 3-material identity of
sweep_floor.csv, same cfg to the letter, so gate check 8 pairs the two
files and demands agreement to 1e-9.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_kaster.csv")
OUT = "/tmp/kaster"

KASTER_RHO0 = 0.05               # his reflectance          [p.7]
KASTER_DFRAC = 0.85              # his Lambertian share     [p.7]
KASTER_LAND = 0.306              # his volumetric density = cap-plane land
CAP_TIP = 4.0 * KASTER_LAND ** 0.5   # 2.2127 mm on pitch 4 -> land 30.6 %

# the flat plate exactly as phase 6.7 measured it at grazing
FLAT = dict(face_w=100.0, face_h=100.0, depth=0.001, pitch_mean=50.0,
            tip_width=50.0, tip_round=False, pitch_jitter=0.0,
            arc_segments=4, valley_round=0.0, margin_depths=6.5)
# margin_depths 4.5, NOT the sim_server steep default 6.5. At depth 20 a
# 6.5 margin runs the field to x = 198, under the control window that
# starts at x = 172 (ctrl_x0 160 + inset 12) -- the grate40b overrun
# again, and the first run of this sweep proved it: cap31's 30.6 % flat
# tips are COPLANAR with the control plate at y = 0 and the coincident
# faces read as -4.5 % control drift at theta 0/-37.5. K_ours has the
# same overrun but only 0.06 % tip area, so its drift hid at -0.01 %.
# 4.5 x 20 = 90 mm still covers the -75 deg shadow (20 x tan 75 = 75 mm)
# and stops the field at x = 158, short of the control zone. The
# margin-6.5 first run is kept as results/__void__sweep_kaster_margin65.csv.
OURS = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
        "pitch": 4.0, "tip_flat": 0.1, "margin_depths": 4.5, "backing": 2.0}
CAP31 = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 20.0,
         "pitch": 4.0, "tip_flat": CAP_TIP, "margin_depths": 4.5,
         "backing": 2.0}

# the anchor, verbatim from sweep_floor.py's flat control (build_params)
ANCHOR_PRM = dict(topology="comb", face_w=60.0, face_h=60.0, depth=50.0,
                  margin_depths=2.0, backing=2.0, seed=23, pitch=6.5,
                  wall_top=0.08, wall_bot=0.08, jitter=0.0)

KTHETAS = (0.0, -37.5, -75.0)    # his AOI set              [p.8]
ROUGH = (0.30, 0.15)             # P4 bracket
ATHETAS = (0.0, -20.0, -40.0, 20.0, 40.0)
ADF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}

COLS = ["tag", "family", "topology", "seed", "diffuse_frac", "roughness",
        "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def run_one(cfg):
        res = BR.run(cfg)
        return list(res["modes"].values())[0]

    def base_cfg(tag, family, prm, th, body, spec, rough):
        cfg = {"tag": tag, "family": family, "out_dir": OUT,
               "results_dir": OUT, "samples": 64, "res_x": 480,
               "res_y": 220, "gpu": True, "spec_roughness": 0.30,
               "params": prm,
               "renders": [{"mode": "hemi_view", "theta": th}],
               "material_mode": "coating",
               "coating": {"body": body, "spec_scale": spec,
                           "roughness": rough}}
        cfg.update({k: v for k, v in COAT.items()
                    if k != "spec_roughness"})
        return cfg

    print("=" * 74)
    print("KASTER RECONCILIATION -- is 0.65x his cap, not his physics?")
    print("=" * 74)

    # --- anchor: 15 cells identical to sweep_floor's FL_p650f080_flat ------
    apj = json.dumps(ANCHOR_PRM, sort_keys=True, default=str)
    for mat, dfrac in ADF.items():
        body, spec = BR.coating_split(dfrac)
        for th in ATHETAS:
            rec = run_one(base_cfg("KAanch_%s_%+03.0f" % (mat, th), "topo",
                                   ANCHOR_PRM, th, body, spec, 0.30))
            rows.append({"tag": "KA_anchor_s23", "family": "topo",
                         "topology": "comb", "seed": 23,
                         "diffuse_frac": mat, "roughness": "",
                         "theta": th, "rho": rec["panel"]["mean"],
                         "control": rec["control"]["mean"],
                         "params_json": apj})
    print("  anchor done (15 cells)", flush=True)

    # --- the experiment ----------------------------------------------------
    body, spec = BR.coating_split(KASTER_DFRAC, rho0=KASTER_RHO0)
    got = {}
    for rough in ROUGH:
        for name, family, prm in (("K_flat", "ridge", FLAT),
                                  ("K_ours", "floor", OURS),
                                  ("K_cap31", "floor", CAP31)):
            pj = json.dumps(dict(prm, material="kaster_d85_rho5"),
                            sort_keys=True, default=str)
            tag = "%s_r%02d_s23" % (name, rough * 100)
            for th in KTHETAS:
                rec = run_one(base_cfg("%s_%+03.0f" % (tag, th), family,
                                       prm, th, body, spec, rough))
                got[(name, rough, th)] = rec["panel"]["mean"]
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "flat"),
                             "seed": 23, "diffuse_frac": "d85",
                             "roughness": "%.2f" % rough,
                             "theta": th, "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
            print("  %-14s " % tag + "  ".join(
                "%g:%.4f%%" % (t, 100 * got[(name, rough, t)])
                for t in KTHETAS), flush=True)

    # --- the ratios the docstring predicts ---------------------------------
    for rough in ROUGH:
        for th in KTHETAS:
            fl = got[("K_flat", rough, th)]
            print("  r%.2f th%+05.1f  flat %.4f%%   ours/flat %.3f   "
                  "cap31/flat %.3f"
                  % (rough, th, 100 * fl,
                     got[("K_ours", rough, th)] / fl,
                     got[("K_cap31", rough, th)] / fl), flush=True)

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
