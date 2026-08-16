"""Phase 5.12: the finalists under the parameter nobody measured, jointly
with the azimuth nobody controls.

    Blender --background --factory-startup --python scripts/sweep_phase512.py

WHY. 5.6 measured the pyramid's roughness sensitivity (3.9x swing) at phi 0
only, and never measured the cone's at all. The deployed panel faces BOTH
unknowns at once: paint lobe width (until a coupon is measured) and beam
azimuth (never controlled). The honest pre-coupon worst case is
worst-over-(phi x roughness), and neither finalist has it.

KNOWN ANCHORS. Pyramid phi0: r10 0.0987 (d00/d76), r30 0.1139 (d00/d76) /
0.13015 (3-mat, d100@40-owned), r50 0.3843. Pyramid phi30 r30: 0.2260
(d100@40-owned). Cone r30: 0.2122 (3-mat). d100 is roughness-invariant
(5.6 self-test) and owns every low-roughness envelope.

    PREDICTIONS, numeric, before any render.

    P1  CONE AT r0.10 IS d100-OWNED AND FLAT: 0.212 ± 0.008 (no gain from
        smooth paint — the diffuse envelope floor does not move).

    P2  CONE AT r0.50 BLOWS UP LESS THAN THE PYRAMID DID: pyramid's
        r50/r30 3-mat ratio was 2.95; the cone's interstice flats already
        leak first bounces at r0.30, so there is less left to lose:
        ratio 2.2 ± 0.6 -> cone r50 worst = 0.47 ± 0.13 %.

    P3  PYRAMID AT phi30 IS d100-OWNED AT LOW ROUGHNESS: r0.10 reads
        0.226 ± 0.010 (the d100@40 phi-30 value, roughness-invariant).

    P4  PYRAMID AT phi30 x r0.50 IS THE PROJECT'S HONEST WORST NUMBER:
        the phi-30 d76@40 value (0.1506 at r0.30) scales like the phi-0
        d76 did (x3.3) -> worst 0.50 ± 0.10 %.

    P5  THE DECISION LINE: at worst-over-(phi x rough) the two finalists
        stay within 15 % of each other (pyramid ~0.50, cone ~0.47) and
        BOTH advantages over flat (1.141 %, roughness-invariant) compress
        to ~2.3-2.4x. If that holds, the single most valuable object in
        this project is a painted coupon — it collapses a 2.3x-to-11.6x
        advantage range to one number. The simulator cannot buy it.

Anchor: P5_j00 + P510_cone_r003 (identical params to sweep_phase510.csv).
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_phase512.csv")
OUT = "/tmp/phase512"

P0 = 5.500550055005501
ANCHOR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 50.0,
          "pitch": P0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
PYR = {"kind": "pyramid", "face_w": 60.0, "face_h": 60.0, "depth": 18.0,
       "pitch": 2.0, "tip_flat": 0.0, "margin_depths": 2.0, "backing": 2.0}
S = 2.0 / 5.5
CONE = {"face_w": 60.0, "face_h": 60.0, "depth": 50.0 * S, "pitch": 2.0,
        "tip_radius": 0.03, "jitter": 0.3, "depth_jitter": 0.0,
        "profile_power": 1.0, "radial_seg": 24, "height_seg": 12,
        "seed": 23, "margin_depths": 2.0, "backing": 2.0}

ALL = ("d00", "d76", "d100")
DF = {"d00": 0.0, "d76": 0.76, "d100": 1.0}
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
# (tag, family, params, phi, roughness)
DESIGNS = [
    ("P5_j00",            "floor",  ANCHOR, 0.0,  0.30),
    ("P510_cone_r003",    "cone3d", CONE,   0.0,  0.30),   # anchor re-run
    ("P512_cone_rg10",    "cone3d", CONE,   0.0,  0.10),
    ("P512_cone_rg50",    "cone3d", CONE,   0.0,  0.50),
    ("P512_pyr_p30_rg10", "floor",  PYR,    30.0, 0.10),
    ("P512_pyr_p30_rg50", "floor",  PYR,    30.0, 0.50),
]
COLS = ["tag", "family", "topology", "phi", "roughness", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    rows = []
    print("=" * 74)
    print("PHASE 5.12 — the finalists under roughness x azimuth")
    print("=" * 74)
    for tag, family, prm, phi, rough in DESIGNS:
        pj = json.dumps(dict(prm, winding="out",
                             **({"phi": phi} if phi else {})),
                        sort_keys=True)
        w = 0.0
        for mat in ALL:
            body, spec = BR.coating_split(DF[mat])
            for th in THETAS:
                cfg = {"tag": "%s_%s_%+03.0f" % (tag, mat, th),
                       "family": family, "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220, "gpu": True,
                       "spec_roughness": rough, "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": rough}}
                if phi:
                    cfg["phi_deg"] = phi
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                w = max(w, rec["panel"]["mean"])
                rows.append({"tag": tag, "family": family,
                             "topology": prm.get("kind", "cone"),
                             "phi": phi, "roughness": rough, "seed": 23,
                             "diffuse_frac": mat, "theta": th,
                             "rho": rec["panel"]["mean"],
                             "control": rec["control"]["mean"],
                             "params_json": pj})
        print("  %-18s phi %4.1f rough %.2f  worst %.5f %%"
              % (tag, phi, rough, 100 * w), flush=True)

    with open(CSV, "w", newline="") as fh:
        wcsv = csv.DictWriter(fh, fieldnames=COLS)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)
    print("wrote %s (%d rows)" % (CSV, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
