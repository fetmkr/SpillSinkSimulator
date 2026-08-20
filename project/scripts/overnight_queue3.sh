#!/bin/zsh
# Leg 3. Chained, not appended -- zsh parses a running script incrementally.
set -u
BL="/Applications/Blender.app/Contents/MacOS/Blender"
PROJ="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
LOGDIR="/tmp/simsrv/overnight"; mkdir -p "$LOGDIR"; cd "$PROJ" || exit 1
busy () {
  pgrep -f "Blender.*--python scripts/" 2>/dev/null | while read -r pid; do
    ps -o command= -p "$pid" 2>/dev/null | grep -q "sim_server.py" || echo "$pid"
  done | grep -q .
}
while pgrep -f "overnight_queue2.sh" >/dev/null 2>&1 || busy; do sleep 30; done
run () {
  echo "=== START $1 $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
  "$BL" --background --factory-startup --python-exit-code 77 \
        --python "scripts/$2" >"$LOGDIR/$1.log" 2>&1
  echo "=== END   $1 rc=$? $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
  grep -E "CONVERGED|published|ratio|PASS|FAIL|Traceback|Error" "$LOGDIR/$1.log" \
    | tail -40 >>"$LOGDIR/queue.log"
}
run phase62   gate_phase62.py
run gates_form rig_v2_gates_form.py
echo "=== QUEUE 3 DONE $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
