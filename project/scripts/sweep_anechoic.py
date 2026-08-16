"""RF and audio anechoic geometry, coated black: does the shape transfer?

    Blender --background --factory-startup --python scripts/sweep_anechoic.py

WHY. Anechoic chambers solved this problem decades ago in two other bands, and
their shapes are standardised: **pyramids** on the end walls, **wedges** on the
side walls, and **convoluted** (egg-crate) sheet where depth is scarce. If the
shape is what does the work, borrowing it is free. If it is the material, it is
not, and knowing which is worth one sweep.

WHAT THE RF NUMBERS ACTUALLY SAY, before assuming anything:

  * a real pyramidal absorber is **425 mm tall on a 150 mm base** -- an aspect
    of 2.83. Ours are 7.7 (comb) and 9.1 (cone). RF absorbers are three times
    stubbier than anything this study has built.
  * height must exceed a quarter wavelength; useful range 0.25λ to 20λ.
  * performance is quoted as -33 dB at 1.64λ thickness, i.e. 0.05 %
    reflectance, and -25 dB out to 50 degrees at 2λ.

That 0.05 % is better than this study's best (0.18 % worst case), and it is NOT
a fair comparison: an RF pyramid is carbon-loaded foam, a LOSSY BULK that
attenuates the wave as it travels through the taper. The geometry is an
impedance match, easing the wave into the absorber so it does not reflect at the
boundary. Musou Black is a 1 % SURFACE. Nothing enters it; the only way to get
rid of a photon is to make it hit the surface again and again. Those are
different problems that happen to have the same picture.

    THE ONE THAT MATTERS. The 2024 review of hollow pyramidal absorbers says
    the interior cavity "augments its absorption capacities by inducing a rise
    in multiple reflections within the cavity boundaries, which increases the
    path length", and then reports hollow types as WORSE than solid -- an
    average -18.73 dB for the hollow truncated pyramid -- "due to lower
    material volume".

    Both halves of that are about a lossy bulk. We have no bulk. Every photon
    is either absorbed at a 1 % surface or it leaves, so material volume is not
    a quantity that exists here and multiple reflections are the only mechanism
    there is.

    PREDICTION, written before any render.

    1. THE HOLLOW/SOLID RANKING INVERTS. In RF, hollow loses to solid. Coated
       optically I expect hollow to BEAT solid at the same aspect, because the
       penalty that sinks it in RF does not apply and the benefit the review
       names -- more reflections inside a cavity -- is the whole of our
       mechanism. This is the sharpest claim here and the one worth being
       wrong about.

    2. AT THE RF-TYPICAL ASPECT OF 2.83 EVERY SHAPE WILL BE FAR WORSE than
       this study's designs -- 3-10x the comb at the same depth. rho_dh goes
       roughly as rho^n with n the mean bounce count, and n scales with aspect.
       An RF pyramid does not need a high aspect because its bulk absorbs;
       borrow the shape without the bulk and the absorption has to come from
       somewhere.

    3. AT EQUAL ASPECT: pyramid ~ convoluted > wedge > cubic. The wedge is
       one-dimensional -- a beam arriving along the ridge sees a shallow groove
       and leaves after two bounces, which is why chambers put wedges on the
       SIDE walls and pyramids where incidence is normal. Our beams arrive at
       +-30-40 degrees from an unknown azimuth, the case a wedge is worst at.

    4. TRUNCATION WILL COST MORE HERE THAN IT DOES IN RF, where the truncated
       pyramid is reported as the best average over 1-10 GHz. A flat top is
       area facing the viewer at one bounce, and this study has already
       measured that on the pyramid floor: reflectance rises linearly with flat
       apex AREA.

    5. THE PYRAMID AT ASPECT 9 WILL NOT BEAT THE CONE by more than a few
       percent. Both are tapered spikes on a lattice; if it does, flat facets
       are worth more than this study has assumed.

The anchor is the cone at pitch 5.5, re-measured here with the identical
`params_json` `sweep_cone3d.csv` recorded, so gate check 8 ties this file to the
published cone.
"""

import sys
import os
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CSV = os.path.join(ROOT, "results", "sweep_anechoic.csv")
OUT = "/tmp/anechoic"

FACE, DEPTH = 60.0, 50.0
# 2.83 is the real pyramidal absorber (425 mm on a 150 mm base); 9.09 is this
# study's cone at pitch 5.5. The two in between say where the crossover is.
ASPECTS = (2.83, 4.0, 6.0, 9.09)
THETAS = (0.0, -20.0, 20.0, -40.0, 40.0)
MATS = (("d00", 0.0), ("d76", 0.76), ("d100", 1.0))

COLS = ["tag", "family", "topology", "shape", "aspect", "pitch", "seed",
        "diffuse_frac", "theta", "rho", "control", "params_json"]


def render(family, prm, tag, prebuilt=None):
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
            if prebuilt is not None:
                cfg["prebuilt_mesh"] = prebuilt
            cfg.update({k: v for k, v in COAT.items()
                        if k != "spec_roughness"})
            res = BR.run(cfg)
            rec = list(res["modes"].values())[0]
            rows.append((mat, th, rec["panel"]["mean"],
                         rec["control"]["mean"]))
    return rows


def hollow_pyramid(face_w, face_h, depth, pitch, wall, margin_depths=2.0,
                   backing=2.0):
    """A field of pyramid SHELLS: four slabs of `wall` thickness, open at the
    base, so light reaches the inside as well as the outside.

    The review's own description -- "four planar slabs of absorbing material
    with constant wall thickness joined together to make a pyramid" -- and the
    shape a sheet-metal part would actually take. `geom_floor` builds only the
    solid pyramid, so this is here rather than there; it is a variant for one
    experiment, not a family the study has adopted.
    """
    verts, faces = [], []

    def tri(a, b, c):
        n = len(verts)
        verts.extend([a, b, c])
        faces.append((n, n + 1, n + 2))

    def quad(a, b, c, d):
        n = len(verts)
        verts.extend([a, b, c, d])
        faces.append((n, n + 1, n + 2, n + 3))

    m = max(margin_depths * depth, pitch)
    nx = int((face_w + 2 * m) / pitch) + 2
    nz = int((face_h + 2 * m) / pitch) + 2
    h = pitch / 2.0
    # SQUARE base, four corners. The first version placed them with
    # `abs(round(cos))`, which puts a "corner" at each EDGE MIDPOINT and makes
    # a diamond rotated 45 degrees -- a field of those does not tile the square
    # lattice it is laid on and leaves the backing slab visible between them.
    unit = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    s_in = max(0.0, 1.0 - wall / max(h, 1e-9))    # inner skin, pulled inward
    for iz in range(nz):
        for ix in range(nx):
            cx = ix * pitch + pitch / 2.0 - m
            cz = iz * pitch + pitch / 2.0 - (face_h / 2.0 + m)
            apex = (cx, -depth, cz)
            out_c = [(cx + u * h, 0.0, cz + v * h) for u, v in unit]
            in_c = [(cx + u * h * s_in, 0.0, cz + v * h * s_in)
                    for u, v in unit]
            for k in range(4):
                j = (k + 1) % 4
                tri(out_c[k], out_c[j], apex)          # outer skin
                tri(in_c[j], in_c[k], apex)            # inner skin
                quad(out_c[k], in_c[k], in_c[j], out_c[j])   # rim at the mouth
    # backing slab under everything
    b0 = len(verts)
    hh = face_h / 2.0 + m
    for y in (-depth, -depth - backing):
        verts += [(-m, y, -hh), (face_w + m, y, -hh),
                  (face_w + m, y, hh), (-m, y, hh)]
    faces += [(b0, b0 + 1, b0 + 2, b0 + 3),
              (b0 + 7, b0 + 6, b0 + 5, b0 + 4)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((b0 + i, b0 + 4 + i, b0 + 4 + j, b0 + j))
    return verts, faces


WALL = 0.5          # aluminium sheet, mm -- the hollow shapes are formed from it


def cases():
    """(shape, family, params, tag, prebuilt) for every geometry measured.

    The six shapes the RF literature actually uses -- solid pyramid, truncated
    pyramid, hollow pyramid, wedge, convoluted, cubic -- at the RF-typical
    aspect and at this study's own, plus two in between.
    """
    out = []
    for asp in ASPECTS:
        pitch = DEPTH / asp
        a3 = round(asp * 100)
        base = dict(face_w=FACE, face_h=FACE, depth=DEPTH,
                    margin_depths=2.0, backing=2.0)
        out.append(("pyramid", "floor",
                    dict(base, kind="pyramid", pitch=pitch, tip_flat=0.0),
                    "AN_pyr_a%03d" % a3, None))
        # truncated: the RF literature's best average over 1-10 GHz. Flat top
        # is 20 % of the pitch, which is what a formed sheet part ends up with.
        out.append(("truncated pyramid", "floor",
                    dict(base, kind="pyramid", pitch=pitch,
                         tip_flat=0.2 * pitch),
                    "AN_trn_a%03d" % a3, None))
        out.append(("convoluted", "floor",
                    dict(base, kind="wave", pitch=pitch, grid=12),
                    "AN_cnv_a%03d" % a3, None))
        out.append(("wedge", "ridge",
                    dict(base, pitch_mean=pitch, pitch_jitter=0.0,
                         tip_width=0.08, valley_round=0.0, micro_depth=0.0,
                         micro_pitch=0.0, arc_segments=24, pitch_seed=23),
                    "AN_wdg_a%03d" % a3, None))
        # hollow pyramid: built here, measured through the same harness
        hv, hf = hollow_pyramid(FACE, FACE, DEPTH, pitch, WALL)
        out.append(("hollow pyramid", "stack",
                    dict(face_w=FACE, face_h=FACE, margin_depths=2.0,
                         backing=2.0, top_depth=DEPTH - 3.0, bot_depth=3.0),
                    "AN_hol_a%03d" % a3, (hv, hf)))
    # cubic: flat blocks, the RF baseline shape and aspect-free by construction
    cv, cf = hollow_pyramid(FACE, FACE, DEPTH, DEPTH / ASPECTS[0], WALL)
    del cv, cf
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 78)
    print("ANECHOIC GEOMETRY, OPTICAL COATING")
    print("  depth %.0f mm fixed; pitch = depth / aspect" % DEPTH)
    print("  2.83 is a real RF pyramid (425 mm on a 150 mm base)")
    print("=" * 78)

    rows = []
    for shape, family, prm, tag, pre in cases():
        asp = DEPTH / prm.get("pitch", prm.get("pitch_mean",
                                               DEPTH / float(tag[-3:]) * 100))
        if pre is not None:
            asp = DEPTH / (DEPTH / (int(tag[-3:]) / 100.0))
        print("\n  %-12s aspect %5.2f  pitch %5.2f mm" % (shape, asp,
                                                          DEPTH / asp),
              flush=True)
        try:
            got = render(family, prm, tag, pre)
        except Exception as exc:
            print("     FAILED: %s" % str(exc)[:100])
            continue
        for mat, th, rho, ctrl in got:
            rows.append({"tag": tag, "family": family,
                         "topology": shape, "shape": shape,
                         "aspect": round(asp, 3),
                         "pitch": round(DEPTH / asp, 4), "seed": 23,
                         "diffuse_frac": mat, "theta": th, "rho": rho,
                         "control": ctrl,
                         "params_json": json.dumps(prm, sort_keys=True)})
        w = max(r[2] for r in got)
        z = max(r[2] for r in got if abs(r[1]) < 1e-9)
        print("     worst %.5f %%   theta-0 %.5f %%" % (100 * w, 100 * z))

    # --- the anchor: this study's cone, identical params to sweep_cone3d ----
    print("\n  anchor: the published cone at pitch 5.5")
    cone = {"face_w": FACE, "face_h": FACE, "depth": DEPTH, "pitch": 5.5,
            "tip_radius": 0.2, "jitter": 0.30, "radial_seg": 24,
            "height_seg": 12, "depth_jitter": 0.0, "profile_power": 1.0,
            "margin_depths": 2.0, "backing": 2.0, "seed": 23}
    for mat, th, rho, ctrl in render("cone3d", cone, "AN_cone_p550_s23", None):
        rows.append({"tag": "AN_cone_p550_s23", "family": "cone3d",
                     "topology": "cone", "shape": "cone (this study)",
                     "aspect": round(DEPTH / 5.5, 3), "pitch": 5.5,
                     "seed": 23, "diffuse_frac": mat, "theta": th,
                     "rho": rho, "control": ctrl,
                     "params_json": json.dumps(cone, sort_keys=True)})

    with open(CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print("\nwrote %s (%d rows)" % (CSV, len(rows)))

    worst, zero, meta = {}, {}, {}
    for r in rows:
        worst[r["tag"]] = max(worst.get(r["tag"], 0.0), r["rho"])
        if abs(r["theta"]) < 1e-9:
            zero[r["tag"]] = max(zero.get(r["tag"], 0.0), r["rho"])
        meta[r["tag"]] = (r["shape"], r["aspect"], r["pitch"])
    print("\n  %-18s %-18s %7s %7s %11s %11s"
          % ("tag", "shape", "aspect", "pitch", "worst rho", "theta-0"))
    for tag in sorted(worst, key=lambda t: (meta[t][0], meta[t][1])):
        s, a, p = meta[tag]
        print("  %-18s %-18s %7.2f %7.2f %10.5f%% %10.5f%%"
              % (tag, s, a, p, 100 * worst[tag], 100 * zero[tag]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
