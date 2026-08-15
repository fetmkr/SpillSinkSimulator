#!/bin/zsh
# Restart run_queue.sh whenever it disappears. Also record a progress heartbeat
# so a HANG can be told apart from SLOWNESS after the fact.
#
#   ./scripts/keepalive.sh &          # from project/
#   tail -f logs/keepalive.log
#   touch logs/STOP                   # stops the queue AND this
#
# WHY NOT AN AGENT. A watchdog agent was tried and it terminated after four
# minutes while reporting that it was "standing by" -- an agent lives inside a
# session and cannot poll overnight. Supervision has to be a process on disk,
# for the same reason the job queue had to be: the failure mode is that nobody
# is at the keyboard.
#
# WHY NOT launchd. That is the right macOS answer and would survive a reboot,
# but it installs a LaunchAgent into the user's system. Not doing that without
# being asked. This is the smaller thing that solves the actual problem.

set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p logs
LOG=logs/keepalive.log

log() { print -r -- "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG" }

# size of the file each job appends to, so "no growth" is measurable
sizes() {
  local a b
  a=$(wc -c < results/sweep_buildable.csv 2>/dev/null || print 0)
  b=$(wc -c < results/form_buildable.json 2>/dev/null || print 0)
  print -r -- "$a $b"
}

log "keepalive up, pid $$"
restarts=0
last=$(sizes)
stalled=0

while true; do
  if [[ -f logs/STOP ]]; then log "STOP present, exiting"; break; fi

  if ! pgrep -f "run_queue.sh" >/dev/null 2>&1; then
    restarts=$((restarts + 1))
    log "queue driver ABSENT -- restarting (restart #$restarts)"
    nohup ./scripts/run_queue.sh >/dev/null 2>&1 &
    sleep 10
  fi

  now=$(sizes)
  if [[ "$now" == "$last" ]]; then
    stalled=$((stalled + 1))
    # 9 quiet polls at 5 min = 45 min. A Blender process that is alive while
    # nothing grows for 45 min is hung, not slow -- the slowest single job here
    # is one form case, and that writes after every case.
    if (( stalled == 9 )); then
      log "STALL: no output growth in 45 min. blender=$(pgrep -cf 'Blender --background') queue=$(pgrep -cf run_queue.sh)"
      log "STALL: last queue line: $(tail -1 logs/queue.log)"
    fi
  else
    (( stalled >= 9 )) && log "stall cleared, output growing again"
    stalled=0
    last=$now
  fi

  sleep 300
done

log "keepalive down after $restarts restart(s)"
