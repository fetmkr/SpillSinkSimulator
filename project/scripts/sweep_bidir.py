"""The angle-in / angle-out sweep: where does the light actually go?

    Blender --background --factory-startup --python-exit-code 77 \
            --python scripts/sweep_bidir.py -- [--coarse] [--only TAG]

Run `scripts/gate_bidir.py` first. 먼저 게이트, 그다음 스윕.

Every published number in this study integrates over exit direction, and
`metrics/01_rho_dh.md` names that as its own blind spot -- "a design that
returns the same energy as a sharp line and one that returns it as a wide smear
score identically". Phase 10 then changed the question from ABSORB to REROUTE.
This sweep is the readout that question needs: one BRDF per (incidence,
observation) pair, drawn as a heatmap on which

    theta_out = +theta_in     is retro -- straight back at the projector
    theta_out = -theta_in     is the flat-mirror specular direction
    theta_out = 0             is the audience

are all straight lines. The normalisation is derived in `bidir.py`; every cell
is read against the flat Lambertian control in its own frame, so the number is
an absolute BRDF in 1/sr and not a ratio to something unstated.

PRE-REGISTERED, written before the first render.

  S1  the flat plate puts its peak on theta_out = -theta_in at every incidence,
      and that peak GROWS toward grazing. The coating is Fresnel; metrics/01
      quotes its flat plate rising 0.998 % to 3.086 % between 0 and 80 deg.
  S2  the pyramid's peak is lower than the flat plate's at every incidence --
      that is what the panel is for -- but I do NOT predict it lands in the
      same place. If the mirror ridge survives at reduced height the structure
      is only dimming; if it moves, the structure is rerouting, and which of
      those two it is has never been measured.
  S3  THE AUDIENCE LINE. Along theta_out = 0, the pyramid must be below the
      flat plate at every incidence. This is the one row a client cares about
      and the one that "worst rho_dh over all angles" cannot see.
  S4  the honeycomb over a flat base shows an EXCESS on both diagonals
      (theta_out = +theta_in and -theta_in) over a smooth background, and the
      excess carries roughly the specular share (1 - diffuse_frac) of the
      return, broadened by the coating roughness.

      This is the ray-tracer session's corner-reflector result restated for a
      real coating. Their specular tracer measured exit polar angle == incidence
      at EVERY incidence (200/200 rays at 0/2/5/20/40 deg) on a mesh that is
      10,248 triangles in exactly two normal classes, 3,470 horizontal and
      6,778 vertical, with zero tilted projected area: mirror bounces off
      mutually perpendicular planes only flip sign components. Their own caveat
      is adopted here rather than the stronger claim -- "all energy on the
      diagonals" is what a PURE mirror does, and the library's anodised finishes
      are 76-85 % Lambertian, so the Lambertian arm has no preferred direction
      and fills the map everywhere. Scoring it as "bright ONLY on the diagonals"
      would fail it for a reason that is not about geometry.
  S5  reciprocity holds across the whole map to the tolerance gate_bidir
      measured, on the structured panels too and not only on the flat plate.

WHAT THIS SWEEP CANNOT SAY, stated here because it will be read off a picture
and pictures are persuasive. It is one azimuth plane. There is no hemisphere
integral in it and therefore no TIS (metric 05 stays planned), except at normal
incidence where azimuthal symmetry closes it -- gate_bidir G6. And the coating's
BRDF SHAPE is the one thing the coating fit does not constrain: metrics/01 says
so directly. This metric reads exactly that. See metrics/08.
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

import bidir as BD                                               # noqa: E402
import materials as MAT                                          # noqa: E402

ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(ROOT, "results")
RENDERS = "/tmp/simsrv/bidir"

SPP = 256                        # the gate's setting, so the two agree

FIELDS = ["tag", "family", "topology", "phi", "seed",
          "material", "rho0", "diffuse_frac", "roughness",
          "theta_in", "theta_out",
          "brdf", "brdf_analytic",
          "panel_mean", "panel_p99", "panel_max", "panel_px",
          "control_mean", "control_expect", "control_dev",
          "sun_angle_deg", "mm_per_px", "res_x", "res_y", "samples",
          "cycles_seed", "margin_depths", "params_json"]


def cases():
    """(tag, family, topology, params, extra) -- the designs to map.

    margin_depths 6.5 throughout: metrics/01 records the camera-side margin
    defect and gate_bidir G5 measures the illumination side, and this sweep
    runs to +-80 on BOTH axes.
    """
    flat_params, flat_extra = BD.flat_plate(100.0)
    return [
        ("flat", "stack", "flat", flat_params, flat_extra),
        ("pyramid_p4_d22", "floor", "pyramid",
         dict(kind="pyramid", pitch=4.0, depth=22.0, tip_flat=0.4,
              face_w=100.0, face_h=100.0, backing=2.0, margin_depths=6.5),
         None),
        # the corner reflector: honeycomb tube over a flat base
        ("honeycomb_flatbase", "stack", "honeycomb",
         dict(face_w=100.0, face_h=100.0, backing=2.0, margin_depths=6.5,
              top="honeycomb", top_depth=47.0, bot="gap", bot_depth=3.0),
         None),
    ]


def load_done(path):
    """Which cells are already on disk. A 1155-cell job outlives one session."""
    done = set()
    if not os.path.exists(path):
        return done
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                done.add((row["tag"], row["material"], float(row["phi"]),
                          int(row["seed"]), round(float(row["theta_in"]), 3),
                          round(float(row["theta_out"]), 3)))
            except (KeyError, ValueError):
                continue
    return done


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    # 5 deg is the protocol grid (33 x 35 = 1155 cells, an overnight queue
    # job). --coarse is 10, --quick is 20 and is for seeing the shape today.
    step = 20.0 if "--quick" in argv else (10.0 if "--coarse" in argv else 5.0)
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    if "--designs" in argv:
        want = set(argv[argv.index("--designs") + 1].split(","))
    else:
        want = None

    theta_in, theta_out = BD.grid(step)
    sun = BD.default_sun_angle(theta_in)
    mat = MAT.resolve(MAT.STUDY_DEFAULT)
    os.makedirs(RESULTS, exist_ok=True)

    print("sweep_bidir  %d incidence x %d observation = %d cells per design"
          % (len(theta_in), len(theta_out), len(theta_in) * len(theta_out)),
          flush=True)
    print("material %s  rho0 %.5f  diffuse_frac %.2f  roughness %.2f  "
          "| sun diameter %.0f deg = the incidence step"
          % (mat.name, mat.rho0, mat.diffuse_frac, mat.roughness, sun),
          flush=True)

    for tag, family, topology, params, extra in cases():
        if only and only != tag:
            continue
        if want and tag not in want:
            continue
        path = os.path.join(RESULTS, "sweep_bidir_%s.csv" % tag)
        done = load_done(path)
        todo = [(a, b) for a in theta_in for b in theta_out
                if (tag, mat.name, 0.0, 23, round(a, 3), round(b, 3))
                not in done]
        print("\n=== %s ===  %d cells, %d already done, %d to run"
              % (tag, len(theta_in) * len(theta_out), len(done), len(todo)),
              flush=True)
        if not todo:
            continue

        sc = BD.build(params, material=mat, samples=SPP, family=family,
                      extra=extra)
        print("    %d x %d px  %.4f mm/px  gap %.0f  %s"
              % (sc["res_x"], sc["res_y"], sc["mm_per_px"], sc["gap"],
                 "CAPPED" if sc["capped"] else "full density"), flush=True)
        pj = json.dumps(params, sort_keys=True, default=str)

        # ZERO BYTES IS NOT "ALREADY STARTED". A crash before the first row
        # leaves the file created but the buffered header unwritten -- Blender
        # dies inside ShaderCache::load_kernel often enough that this happened
        # on the first pyramid run. Resuming onto it would append rows under no
        # header and csv.DictReader would read row one as the field names.
        new = not os.path.exists(path) or os.path.getsize(path) == 0
        fh = open(path, "a", newline="")
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()

        t0, n = time.time(), 0
        # NOT `want`: that name is the --designs filter, and shadowing it here
        # left it holding a set of (theta_in, theta_out) tuples, so every
        # design after the first failed `tag not in want` and was silently
        # skipped. The run reported success having measured one of three.
        todo_set = set(todo)
        for rec in BD.sweep(sc, theta_in, theta_out, sun_angle_deg=sun,
                            skip=lambda a, b: (a, b) not in todo_set,
                            out_dir=RENDERS):
            row = {k: rec.get(k) for k in FIELDS if k in rec}
            row.update(tag=tag, family=family, topology=topology, phi=0.0,
                       seed=23, margin_depths=params.get("margin_depths", 2.0),
                       params_json=pj)
            w.writerow(row)
            fh.flush()                       # a killed queue keeps its columns
            n += 1
            if rec["theta_out"] == theta_out[-1]:
                el = time.time() - t0
                print("    theta_in %+5.1f done  %4d/%4d cells  %5.1f s/cell  "
                      "eta %5.1f min"
                      % (rec["theta_in"], n, len(todo), el / n,
                         (len(todo) - n) * el / n / 60.0), flush=True)
            if rec["control_dev"] > 0.02:
                print("    [WARN] in %+5.1f out %+5.1f control off by %.2f %% "
                      "-- tilt, window or margin, not the panel"
                      % (rec["theta_in"], rec["theta_out"],
                         100 * rec["control_dev"]), flush=True)
        fh.close()
        print("    wrote %s" % path, flush=True)

    print("\n@@DONE@@", flush=True)


if __name__ == "__main__":
    main()
