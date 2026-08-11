"""
The gate: no report is produced from geometry that has not been re-verified.

Import it and call require_lock() at the top of anything that writes a number
where the client can see it. It runs scripts/lock.py check -- 23 seconds -- and
refuses to continue if any frozen value has moved.

This exists because discipline did not work. Five wrong headline numbers were
produced here, and in every case the geometry or the measurement chain had
changed under a figure that had already been reported, with nothing saying so.
Remembering to check is exactly the thing that failed. So the check is not a
habit any more; it is a precondition, and the report cannot be written without
it passing.

    RUN_LOCK=0   skips the gate. It stamps the report SKIPPED, in orange, at
                 the top. If a report says SKIPPED, its numbers are unverified
                 and must not be quoted.
"""

from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLENDER = os.environ.get(
    "BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender")


def require_lock(verbose=True):
    """Returns a short status string for stamping on the report.

    Exits the process on drift. That is the point: a drifted number must not
    be able to reach a page.
    """
    if os.environ.get("RUN_LOCK") == "0":
        if verbose:
            print("[GATE] SKIPPED by RUN_LOCK=0 -- numbers are unverified",
                  flush=True)
        return "LOCK SKIPPED - unverified"

    lock = os.path.join(ROOT, "scripts", "lock.py")
    frozen = os.path.join(ROOT, "results", "LOCK.json")
    if not os.path.exists(frozen):
        print("[GATE] no results/LOCK.json. Freeze the headline numbers "
              "first:\n"
              "  Blender --background --factory-startup --python "
              "scripts/lock.py -- freeze", flush=True)
        sys.exit(2)

    if verbose:
        print("[GATE] re-measuring the frozen designs...", flush=True)
    r = subprocess.run([BLENDER, "--background", "--factory-startup",
                        "--python", lock, "--", "check"],
                       capture_output=True, text=True)
    tail = [ln for ln in r.stdout.splitlines()
            if ln.strip() and not ln.startswith(("Blender", "Read prefs",
                                                 "Fra:", "[RESULT]",
                                                 "[DONE]"))]
    if r.returncode != 0:
        print("\n".join(tail), flush=True)
        print("\n[GATE] BLOCKED. A locked value moved, so the geometry or the\n"
              "measurement chain is not what the last report was written\n"
              "against. Either the change was intended -- say what moved and\n"
              "why, then re-freeze -- or a reported number has just become\n"
              "wrong. No report is written until this is resolved.", flush=True)
        sys.exit(1)

    if verbose:
        print("[GATE] PASS -- geometry and measurement chain unchanged",
              flush=True)
    return "LOCK PASS (3% tol)"


if __name__ == "__main__":
    print(require_lock())
