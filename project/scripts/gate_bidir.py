"""GATE 17: is the angle-in / angle-out map an instrument?

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/gate_bidir.py

The project's standing order is 먼저 게이트, 그다음 스윕 -- gate first, then
sweep (principles/00 §E). A new metric that has never reproduced a known answer
is not a metric, and this study has withdrawn nine claims that were setup errors
rather than physics.

The map's normalisation is derived in `bidir.py`. The useful consequence is that
a LAMBERTIAN HAS A BRDF WE KNOW IN CLOSED FORM -- rho/pi, the same in every
direction -- so a flat Lambertian panel beside the flat Lambertian control gives
the rig two independent known answers in every one of the ~81 cells at once,
with two DIFFERENT values so a window mix-up cannot pass.

PRE-REGISTERED:
  G1  a flat Lambertian panel of rho 0.20 reads 0.20/pi = 0.063662 /sr and the
      0.05 control reads 0.015915 /sr, in every cell, to within 1 %. If either
      moves with theta_out the tilt or the windows are wrong; if either moves
      with theta_in the cos(theta_in) normalisation is wrong.
  G2  a flat plate of the FITTED COATING puts its brightest exit angle on
      theta_out = -theta_in (the mirror direction) at every incidence, and the
      ridge grows toward grazing -- the coating is Fresnel and metrics/01
      quotes its flat plate rising 0.998 % head-on to 3.08 % at 80 deg.
  G3  reciprocity: f(a,b) = f(b,a). Exact symmetry is NOT expected, because the
      theta_in axis is bin-averaged by the sun's angular size and theta_out is
      a delta. So the residual is a diagnostic, not a pass mark: where it
      exceeds the seed-to-seed noise, the map is under-sampled there.
  G4  the map is a window MEAN under a directional source, so it is an area
      average and should be density-INDIFFERENT like the totals axis (the audit
      measured 0.9 % over a 13x density range) rather than density-decisive
      like head-on (55 % over 5.6x). Predicted: under 2 % over 4x.
  G5  the illumination side needs margin exactly as the view side does. Nothing
      in this repo has ever checked it: metrics/01 records the camera-side
      margin defect and its 6.5-depth fix, and a tilted SUN is the same
      geometry seen from the other end. Predicted: a structured panel measured
      at margin 2.0 and 6.5 agrees at |theta| <= 40 and disagrees at 80.
"""

from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bidir as BD                                               # noqa: E402
import materials as MAT                                          # noqa: E402
import rig_v2 as R2                                              # noqa: E402

OUT = "/tmp/simsrv/bidir_gate"
os.makedirs(OUT, exist_ok=True)

SPP = 256
STEP = 20.0                       # coarse on purpose: a gate nobody runs is
                                  # not a gate (lock.py's own reasoning)
THETA_IN, THETA_OUT = BD.grid(STEP, in_limit=80.0, out_limit=80.0)

# THE FLAT PLATE IS A SINGLE QUAD, not a degenerate case of a structured
# family, because every degenerate case tried here was flat only approximately:
#
#   lock.py flat_coating (ridge p50, depth 0.001) reads 25 % DARK under a
#       full-face window -- it lays its two periods over z -25..+75 on a 100 mm
#       face and does not cover its own window. Measured 0.047654 against the
#       0.063662 a Lambertian 0.20 owes: exactly the 0.7485 coverage. The stock
#       rig's 30 % z inset hid it, because z -20..+20 sits inside the covered
#       band. Now refused by rig_v2.assert_window_covered.
#   floor pyramid at depth 0.01 mm (facet slope 0.29 deg) reads 1.7-2.7 % off,
#       and gets WORSE as the depth shrinks -- 20.6 % at 0.001 mm, 75.5 % at
#       0.0001 mm -- because surfaces 1e-4 mm apart over a 100 mm span are
#       numerically the same surface.
#
# The quad has no such parameter, and reads a Lambertian's rho/pi to 0.00 %.
FLAT_FAMILY = "stack"                 # the family prebuilt_mesh rides in on


def _flat():
    return BD.flat_plate(100.0)

# A real structured panel, the order spec, for the two checks that need one.
PYRAMID = dict(kind="pyramid", pitch=4.0, depth=22.0, tip_flat=0.4,
               face_w=100.0, face_h=100.0, backing=2.0)

fails = []


def note(ok, label, detail):
    tag = "PASS" if ok else "**FAIL**"
    if not ok:
        fails.append(label)
    print("   %-8s %s  %s" % (tag, label, detail), flush=True)


def collect(sc, ins, outs, sun=None):
    """{(theta_in, theta_out): record} for a whole grid."""
    return {(r["theta_in"], r["theta_out"]): r
            for r in BD.sweep(sc, ins, outs, sun_angle_deg=sun, out_dir=OUT)}


# ---------------------------------------------------------------- G1
def g1():
    print("\n=== G1  a Lambertian reads rho/pi in every cell ===", flush=True)
    prm, extra = _flat()
    # model "lambert": BRDF = rho0/pi, isotropic, known in closed form.
    lam = MAT.Material(rho0=0.20, model="lambert", name="gate_lambert",
                       note="not a finish anyone would use -- a known answer "
                            "to test the rig against")
    sc = BD.build(prm, material=lam, samples=SPP, family=FLAT_FAMILY,
                  extra=extra)
    cells = collect(sc, THETA_IN, THETA_OUT)

    want_panel = lam.rho0 / math.pi
    want_ctrl = BD.LAMBERT_BRDF
    # brdf_analytic divides by cos(theta_in) alone, so it tests the panel
    # against the closed form without going through the control at all.
    dp = max(abs(r["brdf_analytic"] - want_panel) / want_panel
             for r in cells.values())
    dc = max(r["control_dev"] for r in cells.values())
    note(dp <= 0.01, "G1 panel",
         "flat Lambertian 0.20: worst |err| %.3f %% against %.6f /sr"
         % (100 * dp, want_panel))
    note(dc <= 0.01, "G1 control",
         "0.05 control plate: worst |err| %.3f %% against %.6f /sr"
         % (100 * dc, want_ctrl))

    # the two failure modes worth separating, because they point at different
    # bugs: drift along theta_out is the tilt, drift along theta_in is cos
    by_out, by_in = {}, {}
    for (ti, to), r in cells.items():
        by_out.setdefault(to, []).append(r["brdf_analytic"])
        by_in.setdefault(ti, []).append(r["brdf_analytic"])
    sp_out = max(abs(sum(v) / len(v) - want_panel) for v in by_out.values())
    sp_in = max(abs(sum(v) / len(v) - want_panel) for v in by_in.values())
    print("        drift along theta_out %.3f %%   along theta_in %.3f %%"
          % (100 * sp_out / want_panel, 100 * sp_in / want_panel), flush=True)
    return cells


# ---------------------------------------------------------------- G2, G3
def g2_g3():
    print("\n=== G2  the fitted coating on a flat plate ===", flush=True)
    prm, extra = _flat()
    sc = BD.build(prm, material=MAT.STUDY_DEFAULT, samples=SPP,
                  family=FLAT_FAMILY, extra=extra)
    cells = collect(sc, THETA_IN, THETA_OUT)

    worst_off = 0.0
    for ti in THETA_IN:
        row = [(cells[(ti, to)]["brdf"], to) for to in THETA_OUT]
        peak_to = max(row)[1]
        off = abs(peak_to - (-ti))
        worst_off = max(worst_off, off)
        print("        theta_in %+5.1f   peak at theta_out %+5.1f "
              "(mirror %+5.1f)   f = %.5f /sr"
              % (ti, peak_to, -ti, max(row)[0]), flush=True)
    note(worst_off <= STEP, "G2 mirror",
         "brightest exit angle is the mirror direction, worst miss %.0f deg "
         "against a %.0f deg bin" % (worst_off, STEP))

    # the ridge must GROW toward grazing: that is the Fresnel behaviour the
    # coating was refitted for, and the old flat-rho material had it backwards
    ridge = {ti: cells[(ti, -ti)]["brdf"] for ti in THETA_IN
             if (ti, -ti) in cells}
    lo, hi = ridge.get(0.0), ridge.get(-80.0)
    note(lo is not None and hi is not None and hi > lo, "G2 fresnel",
         "mirror-direction f: %.5f at 0 deg -> %.5f at 80 deg (%.2fx)"
         % (lo or 0, hi or 0, (hi / lo) if lo else float("nan")))

    print("\n=== G3  reciprocity, f(a,b) vs f(b,a) ===", flush=True)
    res, worst = [], (0.0, None)
    for a in THETA_IN:
        for b in THETA_IN:
            if b <= a or (a, b) not in cells or (b, a) not in cells:
                continue
            x, y = cells[(a, b)]["brdf"], cells[(b, a)]["brdf"]
            m = 0.5 * (x + y)
            if m <= 1e-9:
                continue
            d = abs(x - y) / m
            res.append(d)
            if d > worst[0]:
                worst = (d, (a, b))
    med = sorted(res)[len(res) // 2] if res else float("nan")
    print("        %d pairs   median %.2f %%   worst %.2f %% at %s"
          % (len(res), 100 * med, 100 * worst[0], worst[1]), flush=True)
    # G3 is a DIAGNOSTIC, so it reports rather than gates. The one thing it
    # does gate is gross asymmetry, which would mean the two angles are not
    # the same angle.
    note(med <= 0.25, "G3 recip",
         "median reciprocity residual %.2f %% (diagnostic: the theta_in axis "
         "is bin-averaged by the %.0f deg sun and theta_out is not)"
         % (100 * med, BD.default_sun_angle(THETA_IN)))
    return cells


# ---------------------------------------------------------------- G4
def g4():
    print("\n=== G4  density indifference ===", flush=True)
    corner = ([-40.0, 0.0, 40.0], [-40.0, 0.0, 40.0])
    got = {}
    # 2x THE DENSITY, NOT 4x. Density is an area, so 4x density is 16x the
    # pixels -- ~11 Mpx a frame, and the first version of this gate spent 20
    # minutes there. `lock.py` makes the argument: a gate nobody runs is not a
    # gate. 2x is 4x the pixels and still resolves the 0.4 mm tip twice over.
    base = R2.MM_PER_PX
    try:
        for mmpx in (base, base / 2.0):
            R2.MM_PER_PX = mmpx
            sc = BD.build(dict(PYRAMID, margin_depths=2.0),
                          material=MAT.STUDY_DEFAULT, samples=SPP)
            got[mmpx] = collect(sc, *corner, sun=STEP)
            print("        %.4f mm/px  %d x %d px"
                  % (sc["mm_per_px"], sc["res_x"], sc["res_y"]), flush=True)
    finally:
        R2.MM_PER_PX = base
    a, b = got[base], got[base / 2.0]
    worst = 0.0
    for k in a:
        m = 0.5 * (a[k]["brdf"] + b[k]["brdf"])
        if m > 1e-9:
            worst = max(worst, abs(a[k]["brdf"] - b[k]["brdf"]) / m)
    note(worst <= 0.02, "G4 density",
         "worst cell moved %.2f %% over 4x the pixels -- an area average, "
         "like the totals axis, not a peak" % (100 * worst))
    return got


# ---------------------------------------------------------------- G5
def g5():
    print("\n=== G5  margin on the ILLUMINATION side ===", flush=True)
    ins = [0.0, -40.0, -80.0]
    outs = [0.0, -40.0, 40.0]
    got = {}
    for md in (2.0, 6.5):
        sc = BD.build(dict(PYRAMID, margin_depths=md),
                      material=MAT.STUDY_DEFAULT, samples=SPP)
        got[md] = collect(sc, ins, outs, sun=STEP)
    ok_band, bad_graze = 0.0, 0.0
    for k in got[2.0]:
        m = 0.5 * (got[2.0][k]["brdf"] + got[6.5][k]["brdf"])
        if m <= 1e-9:
            continue
        d = abs(got[2.0][k]["brdf"] - got[6.5][k]["brdf"]) / m
        if max(abs(k[0]), abs(k[1])) <= 40.0:
            ok_band = max(ok_band, d)
        else:
            bad_graze = max(bad_graze, d)
    print("        within +-40 deg: worst %.2f %%    beyond: worst %.2f %%"
          % (100 * ok_band, 100 * bad_graze), flush=True)
    note(ok_band <= 0.02, "G5 band",
         "margin 2.0 and 6.5 agree inside the working band (%.2f %%)"
         % (100 * ok_band))
    # NOT a pass/fail: this is the measurement that decides the sweep's margin
    print("        -> the sweep must use margin_depths %.1f, because %s"
          % (BD.DEEP_MARGIN_DEPTHS,
             "the grazing cells move %.1f %%" % (100 * bad_graze)
             if bad_graze > 0.02 else
             "even the grazing cells agree (%.2f %%)" % (100 * bad_graze)),
          flush=True)
    return got


# ---------------------------------------------------------------- G6
def _closure(mat, spp, label):
    """2*pi * INT f(0,t) cos t sin t dt over the in-plane slice, against the
    closed form. At theta_in = 0 the BRDF is azimuthally symmetric, so the
    slice determines the hemisphere and the integral closes -- at any other
    incidence it does not, and no quadrature recovers the missing azimuths."""
    prm, extra = _flat()
    sc = BD.build(prm, material=mat, samples=spp, family=FLAT_FAMILY,
                  extra=extra)
    outs = [x * 5.0 for x in range(0, 18)]                 # 0..85
    fs = {t: BD.cell(sc, 0.0, t, 5.0, out_dir=OUT)["brdf"] for t in outs}
    tot = 0.0
    for u, v in zip(outs, outs[1:]):
        ru, rv = math.radians(u), math.radians(v)
        tot += 0.5 * (fs[u] * math.cos(ru) * math.sin(ru) +
                      fs[v] * math.cos(rv) * math.sin(rv)) * (rv - ru)
    got, want = 2.0 * math.pi * tot, mat.rho_dh(0.0)
    print("        %-20s integral %.6f  closed form %.6f  %+7.2f %%"
          % (label, got, want, 100 * (got - want) / want), flush=True)
    return got, want, fs, sc


def g6():
    """Does the map integrate back to the project's primary scalar?

    `materials.Material.rho_dh()` is a closed form for a flat plate, verified
    to 0.04 % against Cycles. It is therefore a gate for this map -- but only
    for a material that HAS a reciprocal BRDF.

    GATED ON THE LAMBERTIAN, DIAGNOSTIC ON THE COATING, and the reason is a
    result rather than a convenience. Measured 2026-08-20, identical geometry,
    identical quadrature, identical code path:

        Lambertian 0.20      -0.98 %   (the 85-90 deg truncation, predicted)
        musou_fit            +23.17 %

    Only the material differs, so the rig and the quadrature are not what fails.
    The coating is built as `mix(diffuse, glossy, fac)` with `fac` driven by a
    Fresnel node, and that node keys off the VIEW direction -- so the diffuse
    arm is attenuated by an amount that depends on where the camera is. At
    theta_in = 0 a reciprocal material's off-lobe level is flat in theta_out,
    as the Lambertian's is to five digits (0.06366 at 0/20/40/60). The
    coating's is not: 0.00363 / 0.00320 / 0.00347 / 0.00361.

    So f(a,b) != f(b,a). Measured off the lobe at 1024 spp with a 5 deg sun,
    where sampling cannot explain it:

        f(0,80)/f(80,0) = 0.681      f(0,60)/f(60,0) = 0.707
        f(20,80)/f(80,20) = 0.816

    WHY THAT MATTERS BEYOND THIS METRIC. `metrics/01` reads rho_dh by Helmholtz
    reciprocity -- uniform world, tilted camera -- and that identity needs a
    reciprocal BRDF. What `hemi_view` reads is the hemispherical-directional
    reflectance, which equals the directional-hemispherical one ONLY under
    reciprocity. `Material.rho_dh()` was fitted and verified against that same
    configuration, so it describes what the rig reads self-consistently; what
    is now open is whether the two reflectances are the same number for this
    material. Recorded in FINDINGS_bidir_2026_08_20.md, not resolved here.
    """
    print("\n=== G6  the map integrates back to rho_dh(0) ===", flush=True)
    lam = MAT.Material(rho0=0.20, model="lambert", name="gate_lambert")
    got, want, _, _ = _closure(lam, SPP * 2, "Lambertian 0.20")
    err = abs(got - want) / want
    note(err <= 0.02, "G6 closure",
         "a reciprocal material's slice integrates to rho_dh(0) within "
         "%.2f %% -- the rig and the quadrature are sound" % (100 * err))

    m = MAT.resolve(MAT.STUDY_DEFAULT)
    cgot, cwant, fs, sc = _closure(m, SPP * 2, m.name)
    flat = [fs[t] for t in (20.0, 40.0, 60.0, 80.0)]
    print("        off-lobe f(0,out) spread %.1f %% (a reciprocal material is "
          "flat here; the Lambertian is, to five digits)"
          % (100 * (max(flat) - min(flat)) / (sum(flat) / len(flat))),
          flush=True)
    print("        -> NOT A GATE FAILURE AND NOT A RIG ERROR: the coating's "
          "Fresnel mix keys off the VIEW direction, so f(a,b) != f(b,a).",
          flush=True)
    print("        -> %s closure %+.2f %%, recorded as the size of that "
          "non-reciprocity" % (m.name, 100 * (cgot - cwant) / cwant),
          flush=True)

    print("\n=== G7  off-lobe reciprocity of the material ===", flush=True)
    worst = 0.0
    for a, b in ((0.0, 80.0), (0.0, 60.0), (20.0, 80.0)):
        x = BD.cell(sc, a, b, 5.0, out_dir=OUT)["brdf"]
        y = BD.cell(sc, b, a, 5.0, out_dir=OUT)["brdf"]
        r = y / x if x else float("nan")
        worst = max(worst, abs(math.log(r)) if r > 0 else 0.0)
        print("        f(%+5.1f,%+5.1f)=%.6f  f(%+5.1f,%+5.1f)=%.6f  ratio "
              "%.3f" % (a, b, x, b, a, y, r), flush=True)
    # reported, never gated: this measures the MATERIAL, and failing the rig
    # for a property of the material is how a real finding gets suppressed
    print("        worst departure from reciprocity: %.2fx. Reported, not "
          "gated -- it is a property of the coating model, not of this rig."
          % math.exp(worst), flush=True)
    return fs


def main():
    print("GATE 17 — the in-plane BRDF slice", flush=True)
    print("grid %d x %d at %.0f deg, %d spp, sun diameter %.0f deg"
          % (len(THETA_IN), len(THETA_OUT), STEP, SPP,
             BD.default_sun_angle(THETA_IN)), flush=True)
    saved = {}
    saved["g1"] = {str(k): v for k, v in g1().items()}
    saved["g2"] = {str(k): v for k, v in g2_g3().items()}
    g4()
    g5()
    g6()
    with open(os.path.join(OUT, "gate_bidir.json"), "w") as fh:
        json.dump(saved, fh, indent=1)
    print("\n%s" % ("ALL CHECKS PASS" if not fails
                    else "FAILED: " + ", ".join(fails)), flush=True)
    print("@@DONE@@", flush=True)
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
