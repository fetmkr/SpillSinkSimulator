"""
Sweep driver. Runs every case in ONE Blender process (startup would otherwise
dominate) and writes one CSV plus one JSON per case.

    Blender --background --factory-startup --python scripts/sweep.py -- [name ...]

Primary axis is hemi_view: uniform illumination with the camera tilted to
theta, which by reciprocity reads the total fraction reflected by a beam
arriving from theta. Swept -80..+80 in 10 degree steps, NOT 0..80 -- the slats
are asymmetric, so light from below meets a completely different geometry than
light from above, and the earlier runs showed the panel goes from 0.037 to
1.000 across that sign flip.
"""

import sys
import os
import csv
import math
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                       # noqa: E402
from profile2d import PanelParams, build_cross_section            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = os.path.join(ROOT, "renders")
RESULTS = os.path.join(ROOT, "results")

ANGLES = list(range(-80, 81, 10))
SAMPLES = 384
RES_X, RES_Y = 1100, 500

VIEW = [{"mode": "hemi_view", "theta": t} for t in ANGLES]


def case(tag, params, sub, renders=None, **extra):
    cfg = {
        "tag": tag,
        "out_dir": os.path.join(RENDERS, sub),
        "results_dir": os.path.join(RESULTS, sub),
        "samples": SAMPLES,
        "res_x": RES_X,
        "res_y": RES_Y,
        "gpu": True,
        "params": params,
        "renders": renders if renders is not None else VIEW,
    }
    cfg.update(extra)
    return cfg


def slat_len_for(overlap, angle_deg, pitch=20.0):
    """Slat length that gives the requested sight-line overlap at this angle."""
    return overlap * pitch / math.sin(math.radians(angle_deg))


def shallow(**kw):
    """D = 50 variant with the chamber features scaled to fit."""
    base = dict(depth=50.0, chamfer=15.0, flare=12.0, flare_ramp=14.0,
                baffle_rows=1, baffle_len=30.0, baffle_pitch=45.0)
    base.update(kw)
    return base


# --------------------------------------------------------------------------

def sweep_slat_angle():
    """
    Slat angle, with slat length adjusted to hold the sight-line overlap fixed
    at 1.1. Holding overlap constant is the point: otherwise a longer slat and
    a steeper slat change the result together and neither can be attributed.
    """
    cases = []
    for a in (20.0, 30.0, 45.0, 60.0, 75.0):
        cases.append(case(
            f"ang{int(a):02d}",
            {"slat_deg": a, "slat_len": slat_len_for(1.1, a)},
            "slat_angle"))
    return cases


def sweep_overlap():
    """
    Sight-line overlap at a fixed 45 degree slat.

    Below 1.0 a straight path runs through the slat layer; above it the layer
    is closed but the slats get longer, eating chamber depth and adding lip
    area. The aperture-ratio principle says this has an interior optimum.
    """
    cases = []
    for ov in (0.7, 0.9, 1.1, 1.4, 1.8):
        cases.append(case(
            f"ovl{int(ov*10):02d}",
            {"slat_deg": 45.0, "slat_len": slat_len_for(ov, 45.0)},
            "overlap"))
    return cases


def sweep_baffles():
    """Baffle rows, and a no-baffle control to price them."""
    cases = []
    for n in (0, 1, 2, 3, 4):
        cases.append(case(f"baf{n}", {"baffle_rows": n}, "baffles"))
    # same row count, different plate coverage
    for ln, pt in ((25.0, 60.0), (40.0, 60.0), (50.0, 60.0)):
        cases.append(case(
            f"baf2_L{int(ln)}",
            {"baffle_rows": 2, "baffle_len": ln, "baffle_pitch": pt},
            "baffles"))
    return cases


def sweep_depth():
    """The two panel depths on the table, plus flare and back-wall variants."""
    cases = [
        case("D100_flat", {}, "depth"),
        case("D100_flare00", {"flare": 0.0, "flare_ramp": 0.0}, "depth"),
        case("D100_flare40", {"flare": 40.0, "flare_ramp": 45.0}, "depth"),
        case("D100_wedge", {"back_profile": "wedge"}, "depth"),
        case("D100_cyl", {"back_profile": "cyl"}, "depth"),
        case("D50_flat", shallow(), "depth"),
        case("D50_wedge", shallow(back_profile="wedge", back_amp=8.0,
                                  back_period=40.0), "depth"),
    ]
    return cases


def sweep_material():
    """
    What the specular stage-1 material is actually worth.

    Stage 1 must not scatter: light scattered on first contact never enters the
    cavity. This prices that requirement, and also prices a middling roughness
    in case a real coating cannot be made properly specular.
    """
    cases = [
        case("mat_specular", {}, "material"),
        case("mat_rough20", {}, "material", spec_roughness=0.20),
        case("mat_rough50", {}, "material", spec_roughness=0.50),
        case("mat_alldiffuse", {}, "material", material_mode="all_diffuse"),
    ]
    return cases


def sweep_baffle_angle():
    """
    Baffle tilt. This is the axis the first run got wrong.

    At 0 degrees the plate is face-parallel, so its normal points straight at
    the aperture: a diffuse plate centres its cosine lobe on the exit and a
    specular one retroreflects. Tilting swings the lobe off the exit by twice
    the tilt, but also shrinks the Z span each plate blocks by cos(tilt), so
    the plate length is grown alongside to hold the closure margin above 1.
    """
    cases = []
    for a in (0.0, 15.0, 30.0, 45.0, 60.0, 75.0):
        cases.append(case(f"bang{int(a):02d}", closed_baffles(a), "baffle_angle"))
    # sign and alternation, at the two tilts most likely to matter
    for a in (45.0, 60.0):
        cases.append(case(f"bang{int(a):02d}_neg",
                          closed_baffles(-a), "baffle_angle"))
        cases.append(case(f"bang{int(a):02d}_alt",
                          closed_baffles(a, alternate=True), "baffle_angle"))
    return cases


def closed_baffles(tilt_deg, alternate=False, target_closure=1.15, **extra):
    """
    Pick baffle length and pitch so a given tilt still closes every sight line.

    A tilted plate spans len*sin(tilt) in depth and blocks only len*cos(tilt)
    in Z, so the chamber depth caps the length and the blocked span collapses
    as the tilt steepens. Past roughly 55 degrees a 60 mm pitch simply cannot
    be closed in a 100 mm panel, so the pitch has to come down with the tilt.
    Rather than deriving that in closed form against a moving geometry, this
    asks the generator itself and steps the pitch down until it stops warning.
    """
    ca = max(math.cos(math.radians(tilt_deg)), 1e-6)
    for pitch in (60.0, 50.0, 40.0, 32.0, 25.0, 20.0, 15.0):
        # length chosen so the BLOCKED Z SPAN is the same at every tilt; that
        # keeps sight-line closure fixed so only the tilt is being compared,
        # instead of letting a shallow tilt quietly grow a 400 mm plate
        params = {"baffle_deg": tilt_deg, "baffle_alternate": alternate,
                  "baffle_pitch": pitch,
                  "baffle_len": round(0.5 * target_closure * pitch / ca, 2),
                  **extra}
        cs = build_cross_section(PanelParams(**params))
        rep = cs.baffle_rows_report
        if rep and min(r["closure"] for r in rep) >= target_closure - 1e-3:
            return params
    print(f"[SWEEP] tilt {tilt_deg}: cannot reach closure {target_closure}; "
          f"best {min(r['closure'] for r in rep):.2f} at pitch {pitch}")
    return params


def slat_family(angle_deg, zone_depth, overlap=1.4, mode="straight", **extra):
    """
    Pick slat length and pitch to hit a target slat-zone depth and sight-line
    overlap at a given angle.

        zone    = L * cos(a)
        overlap = L * sin(a) / pitch          (halved for a chevron)

    so  pitch = zone * tan(a) / overlap  -- and for a chevron, half that.

    Holding zone depth fixed is what makes the angle comparison honest: a
    shallow slat otherwise silently eats the whole panel depth (20 deg at
    overlap 1.4 and 20 mm pitch needs a 77 mm zone out of 100 mm), so a
    shallow-vs-steep comparison at fixed pitch is really a comparison of how
    much chamber is left.
    """
    a = math.radians(angle_deg)
    vee = (mode == "vee")
    L = zone_depth / math.cos(a)
    span = L * math.sin(a) * (0.5 if vee else 1.0)
    pitch = span / overlap
    p = {"slat_deg": angle_deg, "slat_len": round(L, 2),
         "pitch_mean": round(pitch, 2), "slat_mode": mode,
         "baffle_rows": 1, "baffle_deg": -45.0, "baffle_len": 30.0,
         "baffle_pitch": 40.0}
    p.update(extra)
    return p


def sweep_pitch():
    """
    Slat pitch at a fixed angle and overlap. Never swept before, and it is the
    lever that decides how much depth is left for the chamber.
    """
    cases = []
    for pitch in (6.0, 10.0, 14.0, 20.0):
        L = 1.4 * pitch / math.sin(math.radians(20.0))
        cases.append(case(
            f"pitch{int(pitch):02d}",
            {"slat_deg": 20.0, "slat_len": round(L, 2), "pitch_mean": pitch,
             "baffle_rows": 1, "baffle_deg": -45.0, "baffle_len": 30.0},
            "pitch"))
    return cases


def sweep_slat_fine():
    """Slat angle at constant zone depth, so only the angle changes."""
    cases = []
    for a in (10.0, 15.0, 20.0, 30.0, 45.0):
        cases.append(case(f"fine_a{int(a):02d}",
                          slat_family(a, 40.0, 1.4), "slat_fine"))
    for ov in (1.1, 2.0, 3.0):
        cases.append(case(f"fine_ov{int(ov*10):02d}",
                          slat_family(20.0, 40.0, ov), "slat_fine"))
    return cases


def sweep_symmetry():
    """
    Straight vs alternating vs chevron slats.

    Every straight-slat case returns ~1.0 for light arriving from below,
    because the slats present their backs to it. These two variants give both
    signs of incidence a forward-facing surface, at the cost of a finer pitch
    (a chevron covers only half the Z span of a straight slat of equal length).
    """
    cases = []
    for a in (20.0, 30.0, 45.0):
        for mode in ("straight", "alternate", "vee"):
            cases.append(case(
                f"sym_{mode[:3]}_a{int(a):02d}",
                slat_family(a, 40.0, 1.4, mode=mode), "symmetry"))
    return cases


def sweep_lip():
    """
    Decisive test of the lip hypothesis.

    Across the pitch sweep the ratio (return at normal incidence) / (t / pitch)
    came out 0.70, 0.72, 0.75, 0.73 -- constant to within noise, which says the
    whole normal-incidence return is the exposed slat edge and nothing else.
    Pure geometry would be scale invariant; it is not, because the 1.0 mm sheet
    thickness is the one length that does not scale.

    If that is right, then holding everything else fixed:
        return  proportional to  thickness   at fixed pitch
        return  proportional to  1 / pitch   at fixed thickness
    Both are checked here, and both must hold for the model to stand.
    """
    cases = []
    for t in (0.3, 0.5, 1.0, 1.5, 2.0):
        prm = slat_family(45.0, 40.0, 2.0)      # pitch lands on 20 mm
        prm["thickness"] = t
        cases.append(case(f"lip_t{int(t*10):02d}", prm, "lip"))
    for pitch in (10.0, 20.0, 30.0, 40.0):
        a = 45.0
        L = 40.0 / math.cos(math.radians(a))
        prm = {"slat_deg": a, "slat_len": round(L, 2), "pitch_mean": pitch,
               "baffle_rows": 1, "baffle_deg": -45.0, "baffle_len": 30.0,
               "baffle_pitch": 40.0}
        cases.append(case(f"lip_p{int(pitch):02d}", prm, "lip"))
    return cases


def sweep_glint():
    """
    Peak return toward a front observer, sampled finely enough to catch a
    specular glint.

    hemi_view integrates over the whole outgoing hemisphere, so it reported
    0.036 for a panel that the form test then caught returning 417x a flat
    plate straight at the camera at one specific incidence. The audience sits
    in one direction, so that peak -- not the integral -- is what gets seen,
    and a scanning beam crosses the glint angle repeatedly.

    Two candidate cures are priced here: spreading the specular lobe with
    coating roughness, and spreading the glint over incidence by jittering the
    slat angles so the panel never lights coherently.
    """
    fine = [{"mode": "angle", "theta": float(t), "sun_angle_deg": 0.5}
            for t in range(-60, 61, 4)]
    base = {"slat_deg": 45.0, "slat_len": 79.2, "pitch_mean": 40.0,
            "baffle_rows": 2, "baffle_deg": -45.0, "baffle_len": 48.8,
            "baffle_pitch": 60.0}
    cases = []
    for r in (0.05, 0.15, 0.30):
        cases.append(case(f"glint_r{int(r*100):02d}", dict(base),
                          "glint", renders=fine, spec_roughness=r))
    for j in (5.0, 10.0, 20.0):
        cases.append(case(f"glint_j{int(j):02d}",
                          dict(base, slat_deg_jitter=j),
                          "glint", renders=fine))
    cases.append(case("glint_j10_r15", dict(base, slat_deg_jitter=10.0),
                      "glint", renders=fine, spec_roughness=0.15))
    cases.append(case("glint_diffuse", dict(base), "glint", renders=fine,
                      material_mode="all_diffuse"))
    return cases


def sweep_coating():
    """
    The one remaining decisive spec: how black, and how glossy, the entrance
    coating has to be.

    Everything the observer sees comes from the entrance surfaces, so this sets
    the answer almost on its own. Sampled finely over incidence because what
    matters is the WORST angle a scanning beam will cross, not the average.

    Reference points for the reflectance axis:
        0.05   ordinary matte black paint / black anodise
        0.02   good black anodise
        0.01   high-grade optical black
        0.005  Musou-Black class sprayable coating
    """
    fine = [{"mode": "angle", "theta": float(t), "sun_angle_deg": 0.5}
            for t in range(-60, 61, 4)]
    geom = {"slat_deg": 45.0, "slat_len": 79.2, "pitch_mean": 40.0,
            "baffle_rows": 2, "baffle_deg": -45.0, "baffle_len": 48.8,
            "baffle_pitch": 60.0}
    cases = []
    for rho in (0.005, 0.01, 0.02, 0.05):
        for rough in (0.15, 0.30, 0.50):
            cases.append(case(
                f"coat_r{int(rho*1000):03d}_g{int(rough*100):02d}",
                dict(geom), "coating", renders=fine,
                rho_slat=rho, rho_specular=rho, spec_roughness=rough,
                rho_chamber=0.90))
    return cases


SWEEPS = {
    "coating": sweep_coating,
    "glint": sweep_glint,
    "lip": sweep_lip,
    "pitch": sweep_pitch,
    "slat_fine": sweep_slat_fine,
    "symmetry": sweep_symmetry,
    "baffle_angle": sweep_baffle_angle,
    "slat_angle": sweep_slat_angle,
    "overlap": sweep_overlap,
    "baffles": sweep_baffles,
    "depth": sweep_depth,
    "material": sweep_material,
}


def flatten(res):
    rows = []
    d = res["derived"]
    for name, rec in res["modes"].items():
        mode = name.split("__")[1].rsplit("_th", 1)[0]
        row = {
            "tag": res["tag"],
            "mode": mode,
            "theta": rec["theta"],
            "ratio_vs_flat": rec["ratio_mean"],
            "panel_mean": rec["panel"]["mean"],
            "control_mean": rec["control"]["mean"],
            "panel_p99": rec["panel"]["p99"],
            "panel_max": rec["panel"]["max"],
            "material_mode": res["material_mode"],
            "spec_roughness": res["spec_roughness"],
            "n_slats": res["n_slats"],
            "n_baffles": res["n_baffles"],
            "png": rec["png"],
        }
        row.update({k: d[k] for k in (
            "depth_mm", "slat_len_mm", "slat_deg", "slat_zone_depth_mm",
            "chamber_depth_mm", "slat_overlap", "pitch_mean_mm",
            "open_face_fraction", "chamber_aperture_fraction", "flare_mm",
            "chamfer_mm", "baffle_rows", "baffle_count", "baffle_len_mm",
            "back_profile")})
        rows.append(row)
    return rows


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    names = argv if argv else list(SWEEPS)

    all_rows = []
    t0 = time.time()
    for name in names:
        cases = SWEEPS[name]()
        n_r = len(cases[0]["renders"])
        print(f"[SWEEP] {name}: {len(cases)} cases x {n_r} renders",
              flush=True)
        for i, cfg in enumerate(cases, 1):
            print(f"[SWEEP] ({i}/{len(cases)}) {name}/{cfg['tag']}  "
                  f"t+{time.time()-t0:.0f}s", flush=True)
            all_rows.extend(flatten(BR.run(cfg)))

    os.makedirs(RESULTS, exist_ok=True)
    csv_path = os.path.join(RESULTS, "sweep_" + "_".join(names) + ".csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)
    print(f"[SWEEP] wrote {csv_path}  ({len(all_rows)} rows, "
          f"{time.time()-t0:.0f}s total)", flush=True)


if __name__ == "__main__":
    main()
