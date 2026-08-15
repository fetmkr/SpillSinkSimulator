#!/bin/zsh
# Keep the work moving without Claude in the loop.
#
# WHY THIS EXISTS. The measurement machinery only ever ran while a Claude turn
# was running. Sweeps were launched into the background, they finished, and then
# nothing happened until the user sent another message -- so an eight-hour
# "keep it running" became eight hours of the user chasing it. The user asked
# for a watchdog at the start of the project and got sweeps instead.
#
# This loop needs no model. It polls every 5 minutes: if no sweep is running and
# the queue is not empty, it starts the next one, gates the result, and appends
# to the log. Claude's own cron reads that log and only has to make the
# judgement calls -- what to measure next -- not the mechanical restarts.
#
#   ./scripts/watchdog.sh start    background, writes results/WATCHDOG.log
#   ./scripts/watchdog.sh status
#   ./scripts/watchdog.sh stop

cd "${0:a:h}/.."
ROOT="$PWD"
B=/Applications/Blender.app/Contents/MacOS/Blender
QUEUE="$ROOT/results/WATCHDOG.queue"
LOG="$ROOT/results/WATCHDOG.log"
PIDF="/tmp/spillsink_watchdog.pid"
INTERVAL=300

log() { print -r -- "$(date '+%m-%d %H:%M:%S')  $*" >> "$LOG" }

# The persistent simulator backend is also "Blender running a script in
# scripts/", so the first version of this test saw it and reported busy
# forever -- the queue stopped advancing the moment the simulator came up and
# nothing said so, because "busy" is the normal state.
busy() { pgrep -f "Blender.*--python scripts/" | while read -r pid; do
           ps -o command= -p "$pid" | grep -q "sim_server.py" || { print yes; break }
         done | grep -q yes }

loop() {
  log "watchdog up, pid $$, polling every ${INTERVAL}s"
  local idle=0 last=""
  while true; do
    if busy; then
      idle=0
      log "busy: $(pgrep -f 'Blender.*--python scripts/' | wc -l | tr -d ' ') render job(s)"
    else
      local next=""
      [[ -s "$QUEUE" ]] && next=$(grep -m1 -v '^\s*\(#\|$\)' "$QUEUE")
      if [[ -n "$next" ]]; then
        # Take the line off the queue BEFORE running it, so a crashing job is
        # not retried forever.
        #
        # `&& mv` was wrong: grep -v exits 1 when it prints NOTHING, which is
        # exactly what happens when the line being removed is the last one. So
        # the queue drained normally while it had two entries and silently
        # refused to drain the final entry, re-running it every 5 minutes. It
        # looked harmless because `done_tags` skipped the work -- the job just
        # returned in 0 s forever, and anything queued behind it would never
        # have run at all.
        grep -vxF -- "$next" "$QUEUE" > "$QUEUE.tmp" || true
        mv "$QUEUE.tmp" "$QUEUE"
        if grep -qxF -- "$next" "$QUEUE"; then
          log "BUG    queue did not drain '$next' -- refusing to loop on it"
          print -r -- "# STUCK: $next" >> "$QUEUE"
          continue
        fi
        # NO "same job twice in a row" guard. It was added after the queue
        # failed to drain, and it then blocked the legitimate case: a sweep
        # that ran hours ago, was fixed, and was deliberately re-queued. The
        # guard fired on `last` left over from the earlier run and the rerun
        # never happened -- the Monitor reported it as a BUG, which is how it
        # was found. The drain verification below is the real check: it looks
        # at the QUEUE FILE after removal, so it cannot be fooled by history.
        log "START  $next"
        local t0=$SECONDS
        if $B --background --factory-startup --python-exit-code 77 \
              --python "$next" >> "$ROOT/results/WATCHDOG.run.log" 2>&1; then
          log "OK     $next  ($((SECONDS-t0))s)"
        else
          log "FAIL   $next  (exit $?, see WATCHDOG.run.log)"
        fi
        if python3 "$ROOT/scripts/gate_sweep.py" >> "$LOG" 2>&1; then
          log "GATE   passed"
        else
          log "GATE   FAILED after $next -- results are not reportable"
        fi
      else
        idle=$((idle+1))
        (( idle % 12 == 1 )) && log "idle: queue empty, nothing running"
      fi
    fi
    sleep $INTERVAL
  done
}

case "${1:-status}" in
  start)
    if [[ -f "$PIDF" ]] && kill -0 $(<"$PIDF") 2>/dev/null; then
      print "already running, pid $(<"$PIDF")"; exit 0
    fi
    touch "$QUEUE"
    loop &!
    print $! > "$PIDF"
    print "watchdog started, pid $(<"$PIDF"), log: results/WATCHDOG.log"
    ;;
  stop)
    [[ -f "$PIDF" ]] && kill $(<"$PIDF") 2>/dev/null && rm -f "$PIDF" \
      && print "stopped" || print "not running"
    ;;
  status)
    if [[ -f "$PIDF" ]] && kill -0 $(<"$PIDF") 2>/dev/null; then
      print "RUNNING  pid $(<"$PIDF")"
    else
      print "STOPPED"
    fi
    print "queue: $(grep -cv '^\s*\(#\|$\)' "$QUEUE" 2>/dev/null || print 0) job(s)"
    [[ -f "$LOG" ]] && { print -- "--- last 8 ---"; tail -8 "$LOG" }
    ;;
esac
