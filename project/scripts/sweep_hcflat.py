"""Global search: honeycomb front, flat back, Musou tips + a painted band,
anodised aluminium below it.

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/sweep_hcflat.py -- [--minutes 180] [--stage A|B|C]

THE BUILD THIS IS SEARCHING FOR. Musou Black is the good coating and the
expensive one. Anodised aluminium honeycomb is what you buy. The proposal is to
pay for Musou only where it decides the answer -- the tips, and as far down the
cell as a spray actually reaches -- and take the as-bought anodising for the
rest of the wall. The floor is a separate pressed sheet, painted flat before
assembly, so it is Musou again.

That is three finishes stacked in depth, and it is ONE material here, not three:
`make_depth_split` switches `body` and `spec_scale` at a plane, and `deep_until`
gives the as-bought finish a BAND rather than a half-space, so the floor below
it is painted again. Per-slot materials cannot do this -- `mat_slots` says so in
its own docstring, because a honeycomb wall is one quad from mouth to floor and
no labelling of faces can cut it. The two mechanisms are mutually exclusive in
`build_scene` (blender_render.py: `if pd is None and cfg.get("materials")`), and
the depth split is the one that answers this question.

    y = 0            tips, and the painted band          musou_fit
    y = -paint       ------------------------------
                     the wall, as bought                 anodised_hi
    y = -deep_until  ------------------------------
                     the floor, painted flat             musou_fit

MEASURED BEFORE SEARCHING, p6.5 / d50 / w0.08, worst of theta 0/+-20/+-40:

    all musou_fit                       0.001753
    all anodised_hi                     0.010649      6.1x worse
    musou 0 % of depth + anodised_hi    0.009424      tips alone buy little
    musou 5 %  (2.5 mm)                 0.004440
    musou 15 % (7.5 mm)                 0.001862      6 % off all-Musou

So the band is the whole lever, and 15 % of depth is close to free. The search
is over what geometry does with it.

WHY 128 SAMPLES. Measured, not assumed: 128 and 256 spp agree to four digits on
three designs spanning the grid (0.00175/0.00175, 0.00199/0.00199,
0.00165/0.00165). The spread that matters here is the geometry realisation, not
Monte Carlo, which is why every design is measured at three seeds and ranked on
the mean.

SCORING is `principles/00` section C, unchanged: rho_dh at 0 / +-20 / +-40, take
the WORST angle, then the mean over seeds. The coating-assumption axis of that
rule does not apply -- the finishes here are named, not assumed.

PRE-REGISTERED:
  H1  a deeper cell is darker at fixed pitch, and it saturates: past aspect
      (depth/pitch) of about 8 the wall is already black before the light
      reaches the floor, so more depth buys nothing.
  H2  the optimum pitch is NOT the smallest. The tips are 2*wall/pitch of the
      face and they set the floor of the answer, so a fine pitch is a bigger
      tip area; against that, a fine pitch at fixed depth is a higher aspect.
      Those pull opposite ways and there should be a minimum in between.
  H3  thinner wall is monotonically better, because tip area is linear in it,
      and the gain flattens once the tips stop dominating.
  H4  the painted band matters most where the aspect is LOW. A deep cell kills
      the light before it reaches the anodising; a shallow one does not.
  H5  no configuration with anodised walls beats all-Musou on the same
      geometry, but the best gets within 10 %.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sim_server as S                                           # noqa: E402

ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
CSV = os.path.join(RESULTS, "sweep_hcflat.csv")

THETAS = [0.0, -20.0, -40.0, 20.0, 40.0]
SPP = 128
SEEDS = (23, 101, 102)
SHALLOW, DEEP = "musou_fit", "anodised_hi"
FACE = 60.0

# commercial expanded-foil cell sizes bracket 3-19 mm; 2 and 16 are outside
# what is bought, kept as the ends of the curve rather than as candidates
PITCH = [2.0, 3.2, 4.0, 5.2, 6.5, 8.0, 10.0, 13.0, 16.0]
DEPTH = [10.0, 15.0, 20.0, 30.0, 40.0, 50.0, 65.0, 80.0]
WALL = [0.03, 0.05, 0.08, 0.12, 0.20]
PAINT = [0.15, 0.10, 0.05, 0.0]        # fraction of depth; 0.15 is the cap

FIELDS = ["tag", "family", "topology", "seed", "pitch", "depth", "wall",
          "paint_frac", "paint_mm", "deep_until", "shallow", "deep",
          "aspect", "tip_frac", "samples", "theta", "rho", "params_json"]


def tag_of(pitch, depth, wall, frac, seed):
    return "HC_p%04.1f_d%04.1f_w%04.2f_f%03.0f_s%d" % (
        pitch, depth, wall, 100 * frac, seed)


def spec_of(pitch, depth, wall, seed):
    return {"top": "honeycomb", "panel": FACE, "depth": float(depth),
            "floor": "none", "seed": int(seed),
            "top_params": {"pitch": float(pitch), "wall_top": float(wall),
                           "wall_bot": float(wall), "jitter": 0.3,
                           "cell_lean_domain": 16.0}}


def load_done():
    done = set()
    if os.path.exists(CSV) and os.path.getsize(CSV) > 0:
        for r in csv.DictReader(open(CSV)):
            done.add(r["tag"])
    return done


def measure_one(pitch, depth, wall, frac, seed):
    spec = spec_of(pitch, depth, wall, seed)
    pd = float(frac) * float(depth)
    r = S.measure(spec, THETAS, 0.76, 0.30, SPP, SHALLOW,
                  deep_coating=DEEP, paint_depth=pd,
                  deep_until=float(depth) - 1.0, paint_fade=0.0)
    # {phi: {theta: rho}} -- one phi here
    inner = list(r.values())[0]
    return {float(k): float(v) for k, v in inner.items()}, pd, spec


def run_jobs(jobs, done, w, fh, deadline, label):
    n_new, t0 = 0, time.time()
    for (pitch, depth, wall, frac, seed) in jobs:
        tag = tag_of(pitch, depth, wall, frac, seed)
        if tag in done:
            continue
        if time.time() > deadline:
            print("    [budget] stopping %s with %d jobs unrun" %
                  (label, len(jobs) - n_new), flush=True)
            return n_new, True
        try:
            rho, pd, spec = measure_one(pitch, depth, wall, frac, seed)
        except Exception as exc:
            print("    [FAIL] %s  %s: %s" % (tag, type(exc).__name__, exc),
                  flush=True)
            continue
        pj = json.dumps(spec, sort_keys=True)
        for th in THETAS:
            w.writerow({"tag": tag, "family": "topo", "topology": "honeycomb",
                        "seed": seed, "pitch": pitch, "depth": depth,
                        "wall": wall, "paint_frac": frac, "paint_mm": pd,
                        "deep_until": depth - 1.0, "shallow": SHALLOW,
                        "deep": DEEP, "aspect": depth / pitch,
                        "tip_frac": 2.0 * wall / pitch, "samples": SPP,
                        "theta": th, "rho": rho.get(th), "params_json": pj})
        fh.flush()
        done.add(tag)
        n_new += 1
        if n_new % 25 == 0:
            el = time.time() - t0
            print("    %s %4d/%4d  %.1f s/design  eta %5.1f min"
                  % (label, n_new, len(jobs), el / n_new,
                     (len(jobs) - n_new) * el / n_new / 60.0), flush=True)
    return n_new, False


def worst_by_design(rows=None):
    """{(pitch,depth,wall,frac): (mean worst rho, sem, n_seeds)}"""
    if rows is None:
        if not os.path.exists(CSV):
            return {}
        rows = list(csv.DictReader(open(CSV)))
    per = {}
    for r in rows:
        if r["rho"] in ("", None):
            continue
        k = (float(r["pitch"]), float(r["depth"]), float(r["wall"]),
             float(r["paint_frac"]), int(r["seed"]))
        per[k] = max(per.get(k, 0.0), float(r["rho"]))
    agg = {}
    for (p, d, w_, f, s), v in per.items():
        agg.setdefault((p, d, w_, f), []).append(v)
    out = {}
    for k, vs in agg.items():
        m = sum(vs) / len(vs)
        sem = ((sum((x - m) ** 2 for x in vs) / (len(vs) - 1)) ** 0.5
               / len(vs) ** 0.5) if len(vs) > 1 else 0.0
        out[k] = (m, sem, len(vs))
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    minutes = float(argv[argv.index("--minutes") + 1]) if "--minutes" in argv \
        else 180.0
    deadline = time.time() + minutes * 60.0
    os.makedirs(RESULTS, exist_ok=True)
    done = load_done()

    new = not os.path.exists(CSV) or os.path.getsize(CSV) == 0
    fh = open(CSV, "a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        w.writeheader()

    print("sweep_hcflat  budget %.0f min  %d designs already done"
          % (minutes, len(done)), flush=True)
    print("  %s above the paint line, %s below, %s again at the floor"
          % (SHALLOW, DEEP, SHALLOW), flush=True)

    # ---- STAGE A: the geometry grid, at the paint cap the user allows
    jobs = [(p, d, wl, 0.15, s)
            for p in PITCH for d in DEPTH for wl in WALL for s in SEEDS]
    print("\n=== stage A: pitch x depth x wall at paint 15 %%  (%d runs) ==="
          % len(jobs), flush=True)
    _, stopped = run_jobs(jobs, done, w, fh, deadline, "A")

    if not stopped:
        # ---- STAGE B: what the paint band is worth, on the best geometries
        agg = worst_by_design()
        best = sorted((k for k in agg if k[3] == 0.15),
                      key=lambda k: agg[k][0])[:40]
        jobs = [(p, d, wl, f, s) for (p, d, wl, _f) in best
                for f in (0.10, 0.05, 0.0) for s in SEEDS]
        print("\n=== stage B: paint 10/5/0 %% on the best 40 geometries "
              "(%d runs) ===" % len(jobs), flush=True)
        _, stopped = run_jobs(jobs, done, w, fh, deadline, "B")

    if not stopped:
        # ---- STAGE C: refine around the optimum
        agg = worst_by_design()
        top = sorted(agg, key=lambda k: agg[k][0])[:8]
        ref = set()
        for (p, d, wl, f) in top:
            for pp in (p * 0.8, p, p * 1.25):
                for dd in (d * 0.8, d, d * 1.25):
                    if not (1.0 <= pp <= 20.0 and 5.0 <= dd <= 80.0):
                        continue
                    ref.add((round(pp, 2), round(dd, 1), wl, f))
        jobs = [(p, d, wl, f, s) for (p, d, wl, f) in sorted(ref)
                for s in SEEDS]
        print("\n=== stage C: refine around the best 8 (%d runs) ==="
              % len(jobs), flush=True)
        run_jobs(jobs, done, w, fh, deadline, "C")

    fh.close()
    agg = worst_by_design()
    print("\n=== best 15 so far (worst theta, mean +- SEM over seeds) ===",
          flush=True)
    print("  %-6s %-6s %-6s %-6s %-10s %-9s %-7s %s"
          % ("pitch", "depth", "wall", "paint", "rho_worst", "SEM", "aspect",
             "tip%"), flush=True)
    for k in sorted(agg, key=lambda k: agg[k][0])[:15]:
        p, d, wl, f = k
        m, sem, n = agg[k]
        print("  %-6.2f %-6.1f %-6.2f %-6.0f %-10.6f %-9.6f %-7.1f %.2f"
              % (p, d, wl, 100 * f, m, sem, d / p, 100 * 2 * wl / p),
              flush=True)
    print("\nwrote %s  (%d designs)" % (CSV, len(agg)), flush=True)
    print("@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
