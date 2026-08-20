"""
Measure one design in Mitsuba, from a JSON spec on stdin.

    <venv>/bin/python scripts/mts_worker.py < spec.json

The simulator runs inside Blender's Python, which has no Mitsuba, so the second
renderer cannot be imported into the server. It is invoked as a subprocess
against its own venv instead. That separation is not a workaround -- it is what
keeps the two codes independent, which is the only reason a cross-check means
anything.

Input:  {"family","params","rho","theta"}   Lambertian only; see below.
Output: {"rho_dh": float, "tris": int, "version": str, "variant": str}

WHY LAMBERTIAN ONLY. Cycles builds this project's coating from a Fresnel node
feeding a mix of diffuse and glossy. Mitsuba has no identical construction, so
comparing the two on that coating measures a difference in materials, not in
transport. A Lambertian is the same BRDF in both, which is what makes the
comparison a check rather than a curiosity. The UI must say so.
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    req = json.load(sys.stdin)
    import mitsuba as mi
    mi.set_variant("scalar_rgb")
    from crosscheck_mitsuba import write_ply, measure

    fam, prm = req["family"], req["params"]
    if "top" in prm:
        import geom_stack as M
        v, f = M.build_mesh(M.StackParams(**prm))
    elif fam == "cone3d":
        import geom3d as M
        v, f = M.build_mesh(M.Cone3DParams(**prm))
    elif fam == "cell":
        import geom_cell as M
        v, f = M.build_mesh(M.CellParams(**prm))
    elif fam == "floor":
        # the standalone pyramid/wave/gap family -- the same dataclass the
        # Cycles path builds from. It was missing from this dispatch, so a
        # pyramid cross-check died inside TopoParams with a TypeError about
        # 'kind' (2026-08-17).
        import geom_floor as M
        v, f = M.build_mesh(M.FloorParams(**prm))
    elif fam in ("ridge", "slat", "scatter"):
        # 1D cross-section families are extruded to a mesh by the Blender-side
        # server; there is no shared mesh builder here. Say so instead of
        # crashing in the wrong dataclass.
        sys.stdout.write("\n@@RESULT@@" + json.dumps(
            {"error": "family %r is a 1D extruded profile with no Mitsuba "
                      "builder; cross-check a 3D family, or use Cycles"
                      % fam}) + "\n")
        sys.stdout.flush()
        return
    else:
        import geom_topo as M
        v, f = M.build_mesh(M.TopoParams(**prm))

    out = os.environ.get("MTS_OUT", "/tmp/mts_ui")
    os.makedirs(out, exist_ok=True)
    if req.get("op") == "form":
        # The other two axes, in the second code. See `mts_form` for why the
        # stripe is a collimated source through a slit and not an area lamp.
        import mts_form as MF
        # Beam width at the wall is a first-class knob (phase 5.5); both
        # renderers must read the SAME value or the cross-check compares
        # different experiments.
        # THE WHOLE RIG CROSSES, NOT JUST THE BEAM. mts_form carries its own
        # copies of the rig constants, and on 2026-08-20 form_buildable's were
        # repaired (window opened to the face instead of a fixed 40 % of it,
        # sampling density held at mm-per-pixel instead of a constant pixel
        # count, frame height made to contain the face). A cross-check that
        # sends only the beam compares the new rig against the old one and
        # reports the difference as renderer disagreement -- which is exactly
        # what the beam default already did (7.5 here, 2.0 there).
        MF.STRIPE_W = float(req.get("beam_w", 7.5))
        if req.get("mm_per_px"):
            MF.MM_PER_PX = float(req["mm_per_px"])
        if req.get("full_face_window"):
            MF.MEAS_INSET_X = 0.0
            MF.MEAS_INSET_Z = 0.0
        ply_f = os.path.join(out, "panel_form.ply")
        nv_f, nt_f = write_ply(ply_f, v, f)
        face_f = float(prm.get("face_w", 60.0))
        r = MF.run(mi, ply_f, float(req.get("rho", 0.01)), face_f, face_f,
                   float(req.get("pitch", 6.5)),
                   thetas=tuple(req.get("thetas", (-40.0, 40.0, 0.0))),
                   n_phase=int(req.get("n_phase", 6)),
                   spp=int(req.get("spp", 256)))
        r.update(tris=nt_f, version=mi.__version__, variant=mi.variant())
        sys.stdout.write("\n@@RESULT@@" + json.dumps(r) + "\n")
        sys.stdout.flush()
        return
    os.makedirs(out, exist_ok=True)
    ply = os.path.join(out, "panel.ply")
    nv, nt = write_ply(ply, v, f)
    face = float(prm.get("face_w", 60.0))
    r = measure(mi, ply, float(req.get("rho", 0.01)), face, face,
                theta=float(req.get("theta", 0.0)),
                spp=int(req.get("spp", 256)))
    # Mitsuba's logger writes to stdout, so the result cannot simply BE
    # stdout -- the first attempt returned a PLY performance warning glued to
    # the front of the JSON and the caller reported a failure for a render
    # that had worked. Marker line, parsed from the end.
    sys.stdout.write("\n@@RESULT@@" + json.dumps({"rho_dh": r, "tris": nt,
                                            "version": mi.__version__,
                                            "variant": mi.variant()})
                     + "\n")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
