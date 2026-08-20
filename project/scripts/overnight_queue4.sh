#!/bin/zsh
set -u
BL="/Applications/Blender.app/Contents/MacOS/Blender"
PROJ="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
LOGDIR="/tmp/simsrv/overnight"; mkdir -p "$LOGDIR"; cd "$PROJ" || exit 1
busy () { pgrep -f "Blender.*--python scripts/" 2>/dev/null | while read -r pid; do
  ps -o command= -p "$pid" 2>/dev/null | grep -q "sim_server.py" || echo "$pid"; done | grep -q .; }
while pgrep -f "overnight_queue3.sh" >/dev/null 2>&1 || busy; do sleep 30; done
echo "=== START displacement $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
"$BL" --background --factory-startup --python-exit-code 77 \
      --python scripts/gate_displacement.py >"$LOGDIR/displacement.log" 2>&1
echo "=== END displacement rc=$? $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
grep -E "slope|offset|PASS|FAIL|Traceback" "$LOGDIR/displacement.log" | tail -30 >>"$LOGDIR/queue.log"
echo "=== QUEUE 4 DONE $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
