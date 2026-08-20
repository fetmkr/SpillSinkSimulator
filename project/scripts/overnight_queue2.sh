#!/bin/zsh
# Second leg of the overnight queue. Chained rather than appended because zsh
# parses a running script incrementally -- editing overnight_queue.sh while it
# runs is exactly the trap this project already recorded once.
#
# Waits for leg 1 to finish, then runs the independent-code cross-verification:
# every number GATES 1-4 blessed was Cycles checking Cycles, which is repetition
# rather than verification. This leg brings in Mitsuba and the pure-Python
# tracer, both on the one BRDF all three implement identically.

set -u
BL="/Applications/Blender.app/Contents/MacOS/Blender"
PROJ="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
LOGDIR="/tmp/simsrv/overnight"
mkdir -p "$LOGDIR"
cd "$PROJ" || exit 1

busy () {
  pgrep -f "Blender.*--python scripts/" 2>/dev/null \
    | while read -r pid; do
        ps -o command= -p "$pid" 2>/dev/null | grep -q "sim_server.py" || echo "$pid"
      done | grep -q .
}

# wait for leg 1's queue AND any render it owns
while pgrep -f overnight_queue.sh >/dev/null 2>&1 || busy; do sleep 30; done

run () {
  name="$1"; script="$2"
  log="$LOGDIR/$name.log"
  echo "=== START $name $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
  "$BL" --background --factory-startup --python-exit-code 77 \
        --python "scripts/$script" >"$log" 2>&1
  echo "=== END   $name rc=$? $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
  grep -E "sigma|%\)|PASS|FAIL|GATE1|Traceback|Error" "$log" | tail -40 \
      >>"$LOGDIR/queue.log"
}

run crossverify crossverify_rig_v2.py

echo "=== QUEUE 2 DONE $(date '+%H:%M:%S') ===" | tee -a "$LOGDIR/queue.log"
