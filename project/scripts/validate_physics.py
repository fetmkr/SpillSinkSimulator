"""
Does the measurement measure what it claims? Three checks a reviewer asks first.

    Blender --background --factory-startup --python scripts/validate_physics.py

WHY NOW. Stray-light practice (Zemax non-sequential, FRED, ASAP, TracePro)
rests on measured BSDF fitted with an ABg model, and the failure mode those
tools warn about most is "surfaces with incorrect BSDF data". This project's
coating is a two-parameter Fresnel mix fitted to a published rho_dh(theta)
curve -- a weaker surface model, and one whose limits should be stated rather
than discovered. But before arguing about the surface model, the harness
itself has never been validated. These three checks do that, and each has a
known right answer that does not depend on the coating at all.

    A  ENERGY CONSERVATION. A closed cavity of Lambertian rho = 1 must return
       everything: rho_dh = 1.000 at every angle. Any shortfall is light the
       renderer lost -- bounce limits, clamping, a leaking mesh -- and it puts
       a floor under how dark a real design can be *measured* to be, quite
       apart from how dark it is. With max_bounces = 128 the expected shortfall
       is (1 - 1/2^128), i.e. none.

    B  RECIPROCITY. `hemi_view` does not illuminate the panel at theta and
       measure what comes back. It illuminates uniformly and reads the radiance
       leaving toward theta, then invokes Helmholtz reciprocity to call that
       rho_dh(theta). Every number in this project depends on that step and it
       has never been tested. `angle` mode does the direct thing -- one sun at
       theta, world black. The two must agree.

    C  CONVERGENCE. Every sweep ran at 64 samples per pixel. Designs have been
       separated by as little as 1 %. If the sampling noise at 64 spp is larger
       than that, those distinctions are noise wearing a decimal point. The
       test re-renders one design at 16 / 64 / 256 / 1024 spp and reports the
       spread against the 1024 reference.

Exit code is the number of failed checks.
"""

import sys
import os
import math
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blender_render as BR                                        # noqa: E402
from cone3d_sweep import COAT                                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "/tmp/validate_physics"
FAILS = []


def say(ok, name, detail):
    print("  %-5s %-34s %s" % ("ok" if ok else "FAIL", name, detail),
          flush=True)
    if not ok:
        FAILS.append(name)


def render(params, family, modes, samples=64, material=None, coating=None,
           tag="v"):
    cfg = {"tag": tag, "family": family, "out_dir": OUT, "results_dir": OUT,
           "samples": samples, "res_x": 480, "res_y": 220, "gpu": True,
           "spec_roughness": 0.30, "params": params, "renders": modes}
    cfg.update({k: v for k, v in COAT.items() if k != "spec_roughness"})
    if coating is not None:
        cfg["coating"] = coating
        cfg["material_mode"] = "coating"
    else:
        cfg["material_mode"] = material or "all_diffuse"
    return BR.run(cfg)


# --- A. energy conservation -------------------------------------------------

def check_energy():
    """A perfectly white honeycomb must return everything that enters it."""
    print("\n[A] energy conservation: rho = 1 cavity must read 1.000")
    prm = dict(topology="comb", face_w=60.0, face_h=60.0, depth=50.0,
               pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0,
               margin_depths=2.0, backing=2.0, seed=23)
    worst = 0.0
    for rho in (1.0, 0.9):
        res = render(prm, "topo",
                     [{"mode": "hemi_view", "theta": t}
                      for t in (0.0, -40.0)],
                     samples=256, material="all_diffuse",
                     tag="energy_%02d" % (rho * 100))
        # all_diffuse paints every panel surface with rho_slat
        for rec in res["modes"].values():
            got = rec["panel"]["mean"]
            # a rho cavity returns rho^(mean bounces); for rho = 1 it is 1
            err = abs(got - rho) / rho if rho == 1.0 else None
            if err is not None:
                worst = max(worst, err)
                say(err < 0.02, "rho=1.000 at theta %+.0f" % rec["theta"],
                    "reads %.4f  (loss %.2f%%)" % (got, 100 * err))
            else:
                say(got < rho, "rho=0.900 at theta %+.0f" % rec["theta"],
                    "reads %.4f  -- must be below %.3f" % (got, rho))
    return worst


def check_energy_setup():
    """`all_diffuse` paints the panel with `rho_slat`; set it to 1."""
    return {"rho_slat": 1.0, "rho_chamber": 1.0, "rho_specular": 1.0}


# --- B. reciprocity ---------------------------------------------------------

def check_reciprocity():
    """hemi_view (reciprocity) against angle mode (direct illumination)."""
    print("\n[B] reciprocity: hemi_view == direct illumination at the same "
          "theta")
    body, spec = BR.coating_split(0.76)
    coat = {"body": body, "spec_scale": spec, "roughness": 0.30}
    prm = dict(topology="comb", face_w=60.0, face_h=60.0, depth=50.0,
               pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0,
               margin_depths=2.0, backing=2.0, seed=23)
    worst = 0.0
    for th in (0.0, -40.0):
        a = render(prm, "topo", [{"mode": "hemi_view", "theta": th}],
                   samples=512, coating=coat, tag="recip_h%+03.0f" % th)
        b = render(prm, "topo", [{"mode": "angle", "theta": th}],
                   samples=512, coating=coat, tag="recip_a%+03.0f" % th)
        ha = list(a["modes"].values())[0]
        ab = list(b["modes"].values())[0]
        # both are reported as panel mean over the same window, normalised by
        # the same control patch, so the ratio panel/control is the comparable
        # quantity: it removes the different absolute source strengths.
        ra = ha["panel"]["mean"] / max(ha["control"]["mean"], 1e-12)
        rb = ab["panel"]["mean"] / max(ab["control"]["mean"], 1e-12)
        err = abs(ra - rb) / max(rb, 1e-12)
        worst = max(worst, err)
        say(err < 0.10, "theta %+.0f" % th,
            "hemi %.5f  direct %.5f  ratio-of-ratios %.3f  (%.1f%%)"
            % (ra, rb, ra / max(rb, 1e-12), 100 * err))
    return worst


# --- C. convergence ---------------------------------------------------------

def check_convergence():
    """Is 64 spp tight enough to separate designs by 1 %?"""
    print("\n[C] convergence: sampling noise at the sweep's 64 spp")
    body, spec = BR.coating_split(0.76)
    coat = {"body": body, "spec_scale": spec, "roughness": 0.30}
    prm = dict(topology="comb", face_w=60.0, face_h=60.0, depth=50.0,
               pitch=6.5, wall_top=0.08, wall_bot=0.08, jitter=0.0,
               margin_depths=2.0, backing=2.0, seed=23)
    ref, got = None, {}
    for spp in (1024, 16, 64, 256):
        t0 = time.time()
        res = render(prm, "topo",
                     [{"mode": "hemi_view", "theta": t} for t in (0.0, -40.0)],
                     samples=spp, coating=coat, tag="conv_%04d" % spp)
        v = {round(r["theta"]): r["panel"]["mean"]
             for r in res["modes"].values()}
        got[spp] = (v, time.time() - t0)
        if ref is None:
            ref = v
    worst = 0.0
    for spp in (16, 64, 256, 1024):
        v, dt = got[spp]
        e = max(abs(v[t] - ref[t]) / ref[t] for t in ref)
        worst = max(worst, e if spp == 64 else 0.0)
        print("      %5d spp   th0 %.6f  th-40 %.6f   err vs 1024 %5.2f%%"
              "   %4.1f s" % (spp, v[0], v[-40], 100 * e, dt))
    say(worst < 0.01, "64 spp within 1 % of 1024 spp",
        "worst %.2f%% -- designs closer than this cannot be told apart"
        % (100 * worst))
    return worst


def main():
    os.makedirs(OUT, exist_ok=True)
    print("=" * 70)
    print("PHYSICS VALIDATION")
    print("=" * 70)
    # A needs a white material, which `all_diffuse` takes from COAT
    COAT.update(check_energy_setup())
    check_energy()
    COAT.update({"rho_slat": 0.005, "rho_chamber": 0.005,
                 "rho_specular": 0.005})
    check_reciprocity()
    check_convergence()
    print("\n" + "=" * 70)
    print("%d failed" % len(FAILS))
    for f in FAILS:
        print("  - %s" % f)
    print("=" * 70)
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(min(main(), 120))
