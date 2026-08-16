"""Re-measure the decision-carrying designs after the winding fix.

    Blender --background --factory-startup --python scripts/sweep_rewind.py

WHY. `FINDINGS_winding.md`: three families (cone, shingle, floor-pyramid, plus
the stack's own slab) were wound inside-out for the project's whole life, and
winding moves specular rows by up to ~90 % while leaving diffuse rows
bit-identical. 773 of 2 531 published designs have their worst-rho set by a
d00 row. This sweep re-measures the designs that decisions actually rest on,
with the fixed (auto-oriented) builders, and reports which published numbers
and rankings move.

Pre-scan of the published argmax (which coating set each design's worst):

    cone B_CONE_p0550_s23          d100 @ 40   -> expect UNCHANGED
    blade stack BH_p055_t02_grid   d100 @ 40   -> expect unchanged (slab fix
                                                  is one buried component)
    comb AZ_comb_p00_s23           d100 @ -40  -> outward already; CONTROL
    solid pyramid AN_pyr_a909      d00  @ 40   -> INFLATED; will drop
    truncated AN_trn_a909          d00  @ 40   -> inflated; will drop

    PREDICTION, written before any render.

    1. Controls hold: comb, cone anchor and the blade stack within +-2 % of
       their published worst.

    2. The solid pyramid's worst DROPS to whatever its d100 row is -- its d00
       row was the artifact. Consequence for the anechoic table: the sharp
       pyramid's lead over the cone (0.18151 vs 0.21548, 16 %) either grows or
       holds as a lead at every aspect where its d100 row is below the cone's;
       I have NOT looked those rows up and this is the honest test of the
       ranking.

    3. The truncated pyramid stays the worst solid shape by a wide margin --
       its flat top is a diffuse liability too, and its published d100 rows
       are far above everyone's.

    4. The honeycomb representative drops if its worst was d00-set (checked
       and printed at run time rather than assumed).

    5. No ranking among {sharp pyramid, cone, comb, blade stack} flips
       DOWNWARD; the winding fix only ever deflated numbers, so designs whose
       worst was diffuse-set keep their value while d00-set designs improve.

Rows are recorded with `"winding": "out"` injected into `params_json`, so gate
check 8 sees a recorded difference against the pre-fix files instead of
reporting the same geometry scoring two ways -- the same treatment
`margin_min` got.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_rewind.csv")
OUT = "/tmp/rewind"

TARGETS = [
    ("sweep_conefloor.csv", "B_CONE_p0550_s23"),
    ("sweep_bladehood.csv", "BH_p055_t02_grid_s23"),
    ("sweep_azimuth.csv", "AZ_comb_p00_s23"),
    ("sweep_buildable.csv", "B_HONE_p0086_f030_s23"),
    ("sweep_blade.csv", "BL_FLAT_t050_p0550_a02_grid_s23"),
    ("sweep_anechoic.csv", "AN_pyr_a283"),
    ("sweep_anechoic.csv", "AN_pyr_a909"),
    ("sweep_anechoic.csv", "AN_trn_a283"),
    ("sweep_anechoic.csv", "AN_trn_a909"),
    ("sweep_anechoic.csv", "AN_wdg_a909"),
    ("sweep_anechoic.csv", "AN_cone_p550_s23"),
]

MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)

COLS = ["tag", "source", "family", "topology", "seed", "diffuse_frac",
        "theta", "rho", "control", "pub_worst", "pub_worst_mat",
        "params_json"]


def fam_of(row, prm):
    # PARAMS FIRST, column second. `sweep_conefloor.csv` stores the cone rows
    # with family="floor" because the column names the EXPERIMENT, not the
    # builder -- trusting it handed Cone3DParams to FloorParams and killed the
    # first run on target 1 with "unexpected keyword argument 'depth_jitter'".
    # The params_json is unambiguous about which dataclass made it.
    if "top" in prm:
        return "stack"
    if "tip_radius" in prm:
        return "cone3d"
    if "topology" in prm:
        return "topo"
    if "variant" in prm:
        return "cell"
    if "kind" in prm:
        return "floor"
    f = row.get("family", "")
    if f in ("cone3d", "floor", "topo", "cell", "stack", "perf"):
        return f
    return None


def main():
    import blender_render as BR
    from cone3d_sweep import COAT
    os.makedirs(OUT, exist_ok=True)
    out_rows = []
    print("=" * 76)
    print("REWIND: the decision set, re-measured with oriented geometry")
    print("=" * 76)
    for src, tag in TARGETS:
        path = os.path.join(RESULTS, src)
        rows = [r for r in csv.DictReader(open(path)) if r["tag"] == tag]
        if not rows:
            print("  %-34s NOT FOUND in %s" % (tag, src))
            continue
        prm = json.loads(rows[0]["params_json"])
        fam = fam_of(rows[0], prm)
        pub = max(float(r["rho"]) for r in rows)
        pub_mat = max(rows, key=lambda r: float(r["rho"]))["diffuse_frac"]
        print("\n  %-34s %-7s published worst %.5f%% (from %s)"
              % (tag, fam, 100 * pub, pub_mat), flush=True)
        if fam is None:
            print("     SKIP: family unknown")
            continue
        worst = 0.0
        for mat, df in MATS:
            body, spec = BR.coating_split(df)
            for th in THETAS:
                cfg = {"tag": "RW_%s_%s_%+03.0f" % (tag[:18], mat, th),
                       "family": fam, "out_dir": OUT, "results_dir": OUT,
                       "samples": 64, "res_x": 480, "res_y": 220,
                       "gpu": True, "spec_roughness": 0.30, "params": prm,
                       "renders": [{"mode": "hemi_view", "theta": th}],
                       "material_mode": "coating",
                       "coating": {"body": body, "spec_scale": spec,
                                   "roughness": 0.30}}
                cfg.update({k: v for k, v in COAT.items()
                            if k != "spec_roughness"})
                res = BR.run(cfg)
                rec = list(res["modes"].values())[0]
                rho = rec["panel"]["mean"]
                worst = max(worst, rho)
                out_rows.append({
                    "tag": tag, "source": src, "family": fam,
                    "topology": rows[0].get("topology", ""),
                    "seed": prm.get("seed", 23), "diffuse_frac": mat,
                    "theta": th, "rho": rho,
                    "control": rec["control"]["mean"],
                    "pub_worst": pub, "pub_worst_mat": pub_mat,
                    "params_json": json.dumps(dict(prm, winding="out"),
                                              sort_keys=True)})
        print("     re-measured worst %.5f%%   shift %+.1f%%"
              % (100 * worst, 100 * (worst - pub) / pub))

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in out_rows:
            w.writerow(r)
    print("\nwrote %s (%d rows)" % (CSV, len(out_rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
