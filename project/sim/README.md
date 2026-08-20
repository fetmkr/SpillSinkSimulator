# Running the panel simulator

Two ways to start it. They serve the same pages and, verified below, return
bit-identical numbers.

## Standalone — no Blender needed to open it

    python3 scripts/sim_server.py
    open http://127.0.0.1:8777

Plain CPython. Structure picking, every slider, **the materials inspector**,
the 3D preview, the derived figures, the published-number lookup and
**STL export** all run here, because
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

## Materials

A panel is not one finish. The **Materials** block on the left lists the parts
of whatever structure is loaded, with the share of the area each covers, and
**Assign materials** opens an inspector docked over the right of the viewport
— not a modal, because you are assigning finishes to regions of a shape you
need to keep looking at.

| part | what it is |
|---|---|
| tips | everything facing the sky. One bounce here and the light leaves with the beam's position intact. On honeycomb 6.5/0.08 it is **under 1 % of the area** and it decides the answer. |
| inner sides | the flanks — where light must survive several bounces to be destroyed, and almost all of the material. |
| base | the floor under the structure: a shaped floor layer, or the slab the cells stand on. A separate part in any real build. |
| hidden | buried in the union, plus the slab's underside. Listed so the areas add to 100 %. |

Which face belongs to which part is derived from the built mesh rather than
tabulated per family, so it cannot go stale, and it works for a structure this
file has never heard of. `python3 scripts/audit_slots.py` checks the tip area
against a closed form written from the design intent — 2·wall/pitch of crown,
(tip_flat/pitch)² of pyramid flat, πr² per cone cell.

Each material carries four numbers — ρ₀, diffuse fraction, roughness, IOR —
and **says which of them nobody has measured**. Only `musou_fit` has a measured
shape; anodised is translated from Kaster 2025 and is labelled as an estimate.
Changing a value marks it, amends the provenance note, and the generated PDF
prints an "estimated, not measured" row. A session override must not be able
to pass as a cited product.

Assigning the same material everywhere takes the single-material path, so the
Cycles scene is byte-identical and a published row still reproduces. Verified
on comb 6.5/0.08: no materials block and uniform `musou_fit` both return
`0.0006134170689620078`, while anodised inner sides return 1.444× that.

The old **paint reaches N mm** control is gone from the page. A depth plane
could never be drawn in the viewport, because a honeycomb wall is one quad from
the mouth to the floor — which is exactly why that split needed a
position-dependent shader. `paint_depth` still works from a job file, and
`geom_kit.split_at_depth` is the geometric replacement, not yet wired to it.

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
