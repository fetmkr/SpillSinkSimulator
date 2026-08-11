#!/usr/bin/env python3
"""
PostToolUse hook: after any edit to a measurement or geometry script, say so.

Claude Code sends the tool call on stdin as JSON; tool_input.file_path carries
the edited path. Exit 2 puts stderr in front of Claude as feedback -- that is
the documented channel for PostToolUse, which cannot block (the edit already
happened) but can make sure the consequence is not silent.

The point is narrow. Five wrong headline numbers were produced in this project,
and every one of them was a number that had already been reported while the
geometry or the measurement chain quietly moved underneath it. Nothing said so
at the time. This says so at the time.

Path filtering is done here rather than in the settings `if` field, which is
documented as best-effort and failing open.
"""
import json
import os
import subprocess
import sys

PROJECT = "/Users/hojunsong/Desktop/SpillSinkSimulator/project"
WATCHED = os.path.join(PROJECT, "scripts")


def main():
    try:
        ev = json.load(sys.stdin)
    except Exception:
        sys.exit(0)                       # malformed input is not our business

    path = (ev.get("tool_input") or {}).get("file_path") or ""
    path = os.path.realpath(path) if path else ""
    if not path.endswith(".py") or not path.startswith(os.path.realpath(WATCHED)):
        sys.exit(0)

    try:
        out = subprocess.run([sys.executable, "scripts/review_needed.py"],
                             cwd=PROJECT, capture_output=True, text=True,
                             timeout=60).stdout.strip()
    except Exception:
        sys.exit(0)

    if not out.startswith("CHANGED"):
        sys.exit(0)

    sys.stderr.write(
        "The evidence behind the optical claims just moved (%s).\n\n"
        "Before any number from this project is put in a report or quoted to "
        "the client:\n"
        "  1. the report scripts already gate on it, but you can run the lock "
        "directly:\n"
        "     Blender --background --factory-startup --python scripts/lock.py "
        "-- check\n"
        "  2. if a locked value drifted, say what moved and why before "
        "re-freezing.\n"
        "  3. have the reviewer at .claude/agents/optics-reviewer.md audit the "
        "live claims,\n"
        "     then run: python3 scripts/review_needed.py --mark\n"
        % os.path.basename(path))
    sys.exit(2)


if __name__ == "__main__":
    main()
