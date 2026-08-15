# Running the panel simulator

Two ways to start it. They serve the same pages and, verified below, return
bit-identical numbers.

## Standalone — no Blender needed to open it

    python3 scripts/sim_server.py
    open http://127.0.0.1:8777

Plain CPython. Structure picking, every slider, the 3D preview, the derived
figures, the published-number lookup and **STL export** all run here, because
every geometry module is pure Python — `geom3d`, `geom_topo`, `geom_cell`,
`geom_floor`, `geom_stack` and `profile_ridge` contain no reference to `bpy`.

Pressing **Measure** launches Blender as a subprocess (`scripts/cyc_worker.py`)
for that one render and lets it exit. Set `BLENDER_BIN` if Blender is not at
`/Applications/Blender.app/Contents/MacOS/Blender`. Without Blender installed
the page still works; only the three measurements report an error saying so.

## Inside Blender — the renderer stays warm

    Blender --background --factory-startup --python scripts/sim_server.py

No GUI window; Blender runs headless and its main thread becomes the render
worker. Identical behaviour, minus the process launch per measurement. Use this
when running many measurements in a row.

## Which renderer

| | runs in | what it is for |
|---|---|---|
| **Cycles** | Blender, either mode above | every published number: ρ, form smear, head-on |
| **Mitsuba 3.9.1** | its own venv, always a subprocess (`scripts/mts_worker.py`) | the **Cross-check in Mitsuba** button — an independent second code on the same mesh |

The cross-check deliberately feeds **both codes a Lambertian ρ = 0.01**, not the
fitted Musou coating: Cycles builds that coating from a Fresnel node feeding a
diffuse/glossy mix, Mitsuba has no identical construction, and a disagreement
there would be about the material rather than the light transport. A Lambertian
is the same BRDF in both, which isolates geometry and transport — the things
actually in doubt. Mitsuba needs no Blender for its own render.

Point it at a different venv with `MTS_PYTHON`.

## What was checked, and how

    python3 scripts/test_sim.py        # 335 checks against a running server
    python3 scripts/audit_normal.py    # defaults == the designs the reports measured

Both launch modes were run through the full suite: **335 checks, 0 failures**
each, including the check that a live measurement reproduces the published
number. The same design measured through both paths returned
`0.0006162782083265483` — the same digits, not merely the same rounding.

One rough edge, recorded rather than hidden: a Blender subprocess launched
immediately after another Blender exits has been seen to die inside
`ShaderCache::load_kernel` with an uncaught `NSException` (Metal kernel
compilation). The identical command succeeded run by hand, from a thread, and
on every attempt since. A collision over the Metal shader cache is the likely
cause but is **not proven**, so the server simply retries once and reports the
real error if the second attempt also fails.
