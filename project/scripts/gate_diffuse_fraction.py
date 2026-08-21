"""How much of the totals number is the COATING's diffuse fraction, not the shape?

The fitted coating is 76 % Lambertian plus a 24 % Fresnel lobe. That split is a
fit, not a measurement, so anything it drags along is a systematic on every
published rho_dh. Sweep the fraction with the geometry held fixed and read what
moves.

This ran once through the sim server and died on an HTTP 500 when the server
restarted under it, leaving a header row and a traceback. It calls `measure`
in-process now: same function, same code path, no socket to lose. Batch work
must not depend on the app the user is clicking.

Two angles, because the two are not the same question:
  theta = 0    head-on incidence, where a specular lobe returns straight back
  theta = -40  the deployment angle, where the lobe leaves at +40

A FLAT plate is measured beside every design. A flat plate has no geometry to
contribute, so whatever the fraction does to the flat plate is the coating's
own sensitivity; whatever it does to the pyramid ON TOP of that is the shape.

PRE-REGISTERED:
  D1  the flat plate moves little with the fraction at theta=0 -- a Lambertian
      and a specular lobe both send light back out of a plane, and the window
      is the whole face.
  D2  the pyramid moves MORE than the flat plate at both angles: a specular
      lobe survives a valley differently from a diffuse one.
  D3  the spread across the swept fractions is larger at -40 than at 0. Recorded
      earlier as 2.8 % at 0 and 15 % at 40 -- this is the check of that pair.
  D4  the ORDER of the two designs never changes with the fraction. If it does,
      the coating fit alone can decide which shape wins, and no ranking in the
      study means anything until the fit is measured rather than assumed.
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sim_server as SS  # noqa: E402

OUT = "/tmp/simsrv/difffrac"
os.makedirs(OUT, exist_ok=True)

FRACS = [0.50, 0.65, 0.76, 0.88, 1.00]
THETAS = [0.0, -40.0]
DESIGNS = [
    ("평판", {"top": "flat", "top_params": {}, "depth": 0.0,
              "panel": 100.0, "floor": "none"}),
    ("피라미드 p4/d22", {"top": "pyramid",
                        "top_params": {"pitch": 4.0, "tip_flat": 0.4},
                        "depth": 22.0, "panel": 100.0, "floor": "none"}),
]
SPP = 256
rows = []
print("도료의 확산 비율만 바꾼다. 형상은 고정. 총 반사율은 도료 fit 그대로.", flush=True)
for label, spec in DESIGNS:
    print("\n===== %s =====" % label, flush=True)
    print("%-8s %s" % ("확산비율", "  ".join("%8s" % ("%g도" % t) for t in THETAS)),
          flush=True)
    got = {}
    for fr in FRACS:
        vals = []
        for th in THETAS:
            try:
                out = SS.measure(spec, [th], fr, 0.30, SPP)
                # measure() returns {phi: {theta: mean}}, keyed "%g" and
                # "%.0f". Reading a key that is not there gave None for every
                # cell and the script still printed its DONE marker -- the
                # exact silent success it was written to stop. Fail loudly.
                v = out["%g" % 0.0]["%.0f" % th]
            except Exception as exc:
                print("   %.2f  %g도 실패: %r" % (fr, th, exc), flush=True)
                v = None
            vals.append(v)
        got[fr] = vals
        rows.append({"design": label, "frac": fr,
                     **{"%g" % t: v for t, v in zip(THETAS, vals)}})
        print("%-8.2f %s" % (fr, "  ".join(
            "%8.5f" % v if v is not None else "%8s" % "-" for v in vals)),
            flush=True)
        json.dump(rows, open(os.path.join(OUT, "diffuse_fraction.json"), "w"),
                  indent=1)
    for i, th in enumerate(THETAS):
        vs = [got[f][i] for f in FRACS if got[f][i] is not None]
        if len(vs) >= 2:
            print("   %g도 에서 확산비율이 바꾼 폭: %.5f ~ %.5f  (%.1f %%)"
                  % (th, min(vs), max(vs), 100.0 * (max(vs) - min(vs)) / min(vs)),
                  flush=True)
missing = sum(1 for r in rows for k, v in r.items()
              if k not in ("design", "frac", "stack", "floor_coat", "rho0")
              and v is None)
if missing or not rows:
    raise SystemExit("%d empty cells out of %d rows -- refusing to report this "
                     "as a finished run" % (missing, len(rows)))
print("\n@@DONE@@", flush=True)
