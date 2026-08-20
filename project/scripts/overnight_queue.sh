#!/bin/zsh
# Overnight verification queue. One Blender at a time -- these jobs are
# CPU-bound renders and running two halves the throughput of both.
#
# Each job appends to its own JSON under /tmp/simsrv and prints progress lines,
# so a job that dies leaves everything before it intact and readable.
#
# Order is by how much a wrong answer would cost:
#   1  form gates 5-7      does the smear axis converge at all, and the order spec
#   2  redo phase 5.5      a published table known to be wrong today
#   3  gate 2 stock        the 'before' contrast, cheap, already once-run
#   4  ranking redo        every finalist design re-measured on the form axes

set -u
BL="/Applications/Blender.app/Contents/MacOS/Blender"
PROJ="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
LOGDIR="/tmp/simsrv/overnight"
mkdir -p "$LOGDIR"

cd "$PROJ" || exit 1

# Do not fight a render that is already going. sim_server.py is ALSO a
# Blender process running a script and it never exits, so it must be excluded
# or this loop waits forever -- which is exactly what the first launch did.
busy () {
  pgrep -f "Blender.*--python scripts/" 2>/dev/null \
    | while read -r pid; do
        ps -o command= -p "$pid" 2>/dev/null | grep -q "sim_server.py" || echo "$pid"
      done | grep -q .
}
while busy; do sleep 20; done

run () {
  name="$1"; script="$2"
  log="$LOGDIR/$name.log"
  echo "=== START $name $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
  "$BL" --background --factory-startup --python-exit-code 77 \
        --python "scripts/$script" >"$log" 2>&1
  rc=$?
  echo "=== END   $name rc=$rc $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
  grep -E "PASS|FAIL|converged|CONVERGED|ratio|spread|Traceback|Error" "$log" \
      | tail -40 >>"$LOGDIR/queue.log"
}

run redo_phase55  redo_phase55.py
run gate2_stock   rig_v2_gate2_stock.py
run gates2        rig_v2_gates2.py

echo "=== QUEUE DONE $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
