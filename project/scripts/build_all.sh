#!/bin/zsh
# One command. Right order. Stops at the first failure.
#
#   ./scripts/build_all.sh            # from project/
#   ./scripts/build_all.sh --offline  # skip the render-based gate check
#
# WHY THIS EXISTS. The pipeline is five scripts that must run in one order, and
# the order was being remembered rather than written down. It was got wrong:
# `report_buildable.py` ran before `form_roughness.py` finished, so the report
# was published with its most important figure silently missing. Nothing failed;
# the page just had an empty box.
#
# The order is not arbitrary:
#
#   gate       -> refuse to build anything from data that has not been validated
#   analyse    -> the rankings, and the only place ratios are computed
#   samples    -> SAMPLES.md, GENERATED. A supplier acts on this file
#   renders    -> data.json, which snapshots whatever measurements exist NOW
#   report     -> the HTML, from that snapshot
#   gate again -> checks that need data.json, e.g. "every candidate is ranked"
#
# Every step's exit code is checked. A step that fails stops the run, because a
# report built on a failed step is worse than no report -- somebody acts on it.

set -u
cd "$(dirname "$0")/.." || exit 1

BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
OFFLINE=""
[[ "${1:-}" == "--offline" ]] && OFFLINE="--offline"
DATE=$(date +%Y-%m-%d)
STEP=0

run() {
  STEP=$((STEP + 1))
  local name=$1; shift
  print -r -- ""
  print -r -- "── [$STEP] $name ──────────────────────────────────────────"
  if ! "$@"; then
    print -r -- ""
    print -r -- "✗ STOPPED at step $STEP ($name)."
    print -r -- "  Nothing downstream was rebuilt. Fix this before rerunning;"
    print -r -- "  do not hand-edit the outputs to make them agree."
    exit 1
  fi
}

print -r -- "════════════════════════════════════════════════════════════"
print -r -- " BUILD ALL — $DATE"
print -r -- "════════════════════════════════════════════════════════════"

# 1. the gate, before anything is built from the data
run "gate (pre)" python3 scripts/gate_sweep.py --offline

# 2. the rankings, printed so a human sees them before they become a document
run "rankings" python3 scripts/analyze_buildable.py

# 3. the spec sheet, generated -- refuses to write a number with no row
run "SAMPLES.md" python3 scripts/make_samples.py

# 4. renders + the data snapshot the report reads
if [[ -z "$OFFLINE" ]]; then
  run "renders + data.json" "$BLENDER" --background --factory-startup \
      --python-exit-code 77 --python scripts/report_buildable.py
else
  print -r -- ""
  print -r -- "── [skip] renders (--offline) ─────────────────────────────"
fi

# 5. the report
run "report.html" python3 scripts/build_report_2rank.py "$DATE"

# 6. the gate again -- check 6 needs data.json to exist
run "gate (post)" python3 scripts/gate_sweep.py --offline

print -r -- ""
print -r -- "════════════════════════════════════════════════════════════"
print -r -- " ALL STEPS PASSED"
print -r -- "   SAMPLES.md              generated from measurements"
print -r -- "   report/$DATE/report.html"
print -r -- "════════════════════════════════════════════════════════════"
print -r -- ""
print -r -- "Publish the artifact only after reading the rankings above."
