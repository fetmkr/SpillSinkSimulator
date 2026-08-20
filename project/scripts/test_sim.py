"""
Exercise the live simulator the way a person with a mouse would.

    python3 scripts/test_sim.py            # everything, ~3 min
    python3 scripts/test_sim.py --quick    # skip renders

WHY A SCRIPT AND NOT A SESSION OF CURLS. Every defect this tool has had so far
was found by running it, never by reading it: a crash from calling bpy off the
main thread, a black viewport from a matrix multiplied in the wrong order, a
dead UI from an idle keep-alive socket, and a patch that landed in the wrong
function and took down three endpoints at once while the fourth kept working.
None of those are visible in a diff. So the checks live in a file that can be
re-run after every change.

WHAT IT COVERS, in the order a person meets it:

    1. every top layer builds, at its defaults
    2. every floor builds under a honeycomb
    3. EVERY SLIDER AT BOTH ENDS of its declared range -- the part nobody
       tests, and the only part a user can reach by accident
    4. a measurement reproduces the published number for a design in the study
    5. the form/head-on path returns something in the right ballpark
    6. STL is a structurally valid binary STL, not just bytes
    7. presets load into a spec the mesh endpoint accepts

Exit code is the number of failures, so it can gate a commit.
"""

import sys
import os
import json
import time
import struct
import urllib.request
import urllib.error

BASE = os.environ.get("SIM_URL", "http://127.0.0.1:8777")
QUICK = "--quick" in sys.argv
FAILS = []
NCHECK = 0


def check(name, ok, detail=""):
    global NCHECK
    NCHECK += 1
    if not ok:
        FAILS.append("%s: %s" % (name, detail))
        print("  FAIL  %-42s %s" % (name, detail[:90]))
    return ok


def get(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as f:
        return json.loads(f.read())


def post(path, obj, timeout=600):
    r = urllib.request.Request(BASE + path, data=json.dumps(obj).encode(),
                               headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as f:
            return f.read(), dict(f.headers), time.time() - t0, None
    except urllib.error.HTTPError as e:
        return None, {}, time.time() - t0, e.read().decode()[:200]
    except Exception as e:
        return None, {}, time.time() - t0, str(e)[:200]


def defaults(fields, skip=("depth", "backing")):
    return {f["name"]: f["default"] for f in fields if f["name"] not in skip}


def main():
    t_all = time.time()
    print("=" * 72)
    print("SIMULATOR TEST  %s" % BASE)
    print("=" * 72)

    try:
        get("/api/health", timeout=8)
    except Exception as e:
        print("server not answering: %s" % e)
        return 1
    fam = get("/api/families")

    # --- 1 & 2: everything builds ------------------------------------------
    print("\n[1] every top layer builds at its defaults")
    slow = []
    for t in fam["top"]:
        spec = {"top": t, "top_params": defaults(fam["top"][t]),
                "floor": "none", "depth": 50, "face": 60}
        b, h, dt, err = post("/api/mesh", spec)
        if not check("build %s" % t, err is None, err or ""):
            continue
        d = json.loads(h.get("X-Derived", "{}"))
        check("%s has triangles" % t, len(b) > 72, "%d bytes" % len(b))
        check("%s reports a feature or says why" % t,
              d.get("min_feature_mm") is not None or d.get("process") is None,
              "min_feature None with process %s" % d.get("process"))
        if dt > 0.45:
            slow.append("%s %.0fms" % (t, 1000 * dt))
    # 450 ms, not 350. The cone now previews at its PUBLISHED tessellation
    # (radial 24 / height 12, from `NORMAL`) instead of the dataclass default
    # of 32 / 3, which is four times the wall segments and the reason the
    # second renderer agreed to 3.9 % instead of 22.7 %. The budget follows the
    # correct geometry, not the other way round.
    check("no top layer is slower than 450 ms to preview", not slow,
          ", ".join(slow))

    print("\n[2] every floor builds under a honeycomb")
    slow = []
    for fl in fam["floor"]:
        spec = {"top": "comb",
                "top_params": {"pitch": 6.5, "wall_top": 0.08,
                               "wall_bot": 0.08},
                "floor": fl, "floor_params": defaults(fam["floor"][fl]),
                "floor_depth": 3, "depth": 50, "face": 60,
                "margin_depths": 0.2}
        b, h, dt, err = post("/api/mesh", spec)
        if not check("build comb+%s" % fl, err is None, err or ""):
            continue
        if dt > 0.45:
            slow.append("%s %.0fms" % (fl, 1000 * dt))
    check("no floor is slower than 450 ms to preview", not slow,
          ", ".join(slow))

    # --- 3: the sliders, at both ends --------------------------------------
    print("\n[3] every slider at BOTH ends of its range")
    n_ext = 0
    for t, fields in fam["top"].items():
        base = defaults(fields)
        for f in fields:
            if f["kind"] != "num" or f["name"] in ("depth", "backing"):
                continue
            for end in ("min", "max"):
                prm = dict(base)
                prm[f["name"]] = f[end]
                spec = {"top": t, "top_params": prm, "floor": "none",
                        "depth": 50, "face": 60}
                b, h, dt, err = post("/api/mesh", spec, timeout=120)
                n_ext += 1
                ok = check("%s.%s=%s(%s)" % (t, f["name"], f[end], end),
                           err is None, (err or "").replace("\n", " "))
                if ok:
                    # An empty build is allowed -- `mixed` at mixed_keep = 0
                    # keeps none of its cells, which is a real answer -- but it
                    # must SAY so. Silent emptiness is a black viewport with no
                    # text, indistinguishable from a crash, and that is what
                    # this check is really guarding.
                    try:
                        why = json.loads((h or {}).get("X-Derived") or "{}"
                                         ).get("why")
                    except Exception:
                        why = None
                    check("%s.%s=%s builds or explains itself"
                          % (t, f["name"], f[end]),
                          len(b) > 72 or bool(why),
                          "%d bytes and no reason given" % len(b))
    print("      %d extreme values exercised" % n_ext)

    # --- 3b: the geometry audit, run here so one command covers both -------
    # The size, coverage and origin checks live in `audit_geometry.py` because
    # they need no server. They run from here too, because the defects they
    # catch were all found by a person looking at THIS simulator's output and
    # nothing else in the suite would have caught them.
    print("\n[3b] geometry audit (size, floor coverage, origin, lattice)")
    import subprocess
    a = subprocess.run([sys.executable,
                        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "audit_geometry.py")],
                       capture_output=True, text=True)
    for line in (a.stdout or "").splitlines():
        if line.strip().startswith("FAIL"):
            check(line.strip()[:70], False, "")
    check("geometry audit", a.returncode == 0,
          "%d failure(s) -- run scripts/audit_geometry.py" % a.returncode)

    # --- 3c: the slot audit, same reasoning -------------------------------
    # Which face belongs to which part cannot be checked from a reflectance:
    # a wrong slot map paints a third of the area with the wrong finish and
    # every number still looks plausible. `audit_slots.py` measures the tip
    # area on the built mesh and compares it with a closed form written from
    # the design intent, so a classifier bug and an algebra bug would have to
    # agree to pass.
    print("\n[3c] slot audit (which face is which part, and how much area)")
    b2 = subprocess.run([sys.executable,
                         os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "audit_slots.py")],
                        capture_output=True, text=True)
    for line in (b2.stdout or "").splitlines():
        if "FAIL" in line:
            check(line.strip()[:70], False, "")
    check("slot audit", b2.returncode == 0,
          "%d failure(s) -- run scripts/audit_slots.py" % b2.returncode)

    # --- 4: a measured number still matches the study ----------------------
    if not QUICK:
        print("\n[4] a live measurement reproduces the published number")
        spec = {"top": "comb",
                "top_params": {"pitch": 6.5, "wall_top": 0.08,
                               "wall_bot": 0.08},
                "floor": "none", "depth": 50, "face": 60}
        b, h, dt, err = post("/api/measure",
                             {"spec": spec, "thetas": [0, -20, -40, 20, 40],
                              "diffuse_frac": 0.76, "samples": 64})
        if check("measure returns", err is None, err or ""):
            rho = json.loads(b)["rho"]
            import csv
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            pub = {float(r["theta"]): float(r["rho"])
                   for r in csv.DictReader(
                       open(os.path.join(root, "results",
                                         "sweep_floor.csv")))
                   if r["tag"] == "FL_p650f080_flat_d00_s23"
                   and r["diffuse_frac"] == "d76"}
            worst = 0.0
            for k, v in rho.items():
                p = pub.get(float(k))
                if p:
                    worst = max(worst, abs(v - p) / p)
            check("live == published within rounding", worst < 1e-3,
                  "worst %.3f%%" % (100 * worst))

        print("\n[5] form / head-on path")
        b, h, dt, err = post("/api/form", {"spec": spec, "n_phase": 4,
                                           "samples": 128}, timeout=600)
        if check("form returns", err is None, err or ""):
            j = json.loads(b)
            check("smear is a number near the published 0.98",
                  j.get("smear") and 0.7 < j["smear"] < 1.4,
                  "smear=%s" % j.get("smear"))
            check("head-on is a number near the published 1.634",
                  j.get("peak") and 1.2 < j["peak"] < 2.2,
                  "peak=%s" % j.get("peak"))

    # --- 6: STL is really an STL -------------------------------------------
    print("\n[6] STL export is structurally valid")
    for spec in ({"top": "comb",
                  "top_params": {"pitch": 6.5, "wall_top": 0.08,
                                 "wall_bot": 0.08},
                  "floor": "pyramid",
                  "floor_params": {"pitch": 2.0, "tip_flat": 0.1},
                  "floor_depth": 3, "depth": 50, "face": 60},
                 {"top": "cone", "top_params": {"pitch": 5.5,
                                                "tip_radius": 0.2},
                  "floor": "none", "depth": 50, "face": 60}):
        b, h, dt, err = post("/api/stl", spec, timeout=180)
        nm = "%s+%s" % (spec["top"], spec.get("floor"))
        if not check("stl %s" % nm, err is None, err or ""):
            continue
        n = struct.unpack("<I", b[80:84])[0]
        check("stl %s length matches its triangle count" % nm,
              len(b) == 84 + 50 * n, "%d bytes, header says %d tris"
              % (len(b), n))
        check("stl %s is not empty" % nm, n > 100, "%d triangles" % n)

    # --- 7: presets round-trip ---------------------------------------------
    print("\n[7] every named preset loads into a buildable spec")
    pres = [p for p in get("/api/presets")["presets"] if p.get("headline")]
    check("named presets exist", len(pres) >= 10, "%d found" % len(pres))
    seen_names = {}
    for p in pres:
        seen_names.setdefault(p["headline"], []).append(p["design"])
        b, h, dt, err = post("/api/mesh", p["spec"], timeout=120)
        check("preset %s" % p["design"], err is None,
              (err or "").replace("\n", " "))
    dupes = {k: v for k, v in seen_names.items() if len(v) > 1}
    check("no preset name appears twice", not dupes,
          "; ".join("%s x%d" % (k, len(v)) for k, v in dupes.items()))

    print("\n" + "=" * 72)
    print("%d checks, %d failures, %.0f s"
          % (NCHECK, len(FAILS), time.time() - t_all))
    for f in FAILS:
        print("  - %s" % f)
    print("=" * 72)
    return len(FAILS)


if __name__ == "__main__":
    sys.exit(min(main(), 120))
