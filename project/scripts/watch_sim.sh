#!/bin/zsh
# Keep the simulator up, and keep checking that it still works.
#
# Two jobs, and only one of them has ever been needed.
#
#   CHECKING is what earns its keep: an edit quietly breaks something and
#   nobody finds out until it ships. Ten-odd edits on 2026-08-24 were each
#   confirmed clean within three minutes by this loop.
#
#   RESTARTING has never fired. 332 consecutive checks over 19 hours, zero
#   restarts; the server sat at 0.0 % CPU the whole time. The first version of
#   this comment claimed "the server dies or gets wedged and nothing notices
#   for hours" -- that was written without checking, and it is not true of the
#   server. What did die silently were BATCH jobs (the Cycles Metal shader
#   cache, in their own Blender), and what stalled for eight hours was the JOB
#   QUEUE. I moved someone else's failure onto the server's record.
#   The restart path stays because it costs nothing and a wedged server would
#   otherwise be invisible -- but it is insurance, not experience.
#
# So: every INTERVAL seconds, ping the server; restart it if it is not
# answering, and run the checklist. Anything that fails is written to
# WATCH_STATUS with a timestamp, and the log keeps the last failure's detail.
#
#   ./scripts/watch_sim.sh &          start
#   touch /tmp/simsrv/WATCH_STOP      stop
#   cat  /tmp/simsrv/WATCH_STATUS     what it has seen
set -u
ROOT="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
BL=/Applications/Blender.app/Contents/MacOS/Blender
PORT=8777
INTERVAL=${INTERVAL:-180}
DIR=/tmp/simsrv
STATUS=$DIR/WATCH_STATUS
LOG=$DIR/watch.log
STOP=$DIR/WATCH_STOP
mkdir -p $DIR
rm -f $STOP
cd "$ROOT"

up() { curl -s -m 5 -o /dev/null "http://127.0.0.1:$PORT/api/health" }

start_server() {
  # mts_worker survives a pkill of the server and eats CPU forever; take both
  pkill -f mts_worker 2>/dev/null
  pkill -f sim_server.py 2>/dev/null
  sleep 2
  nohup "$BL" --background --factory-startup --python scripts/sim_server.py \
        > $DIR/server.log 2>&1 &
  for i in {1..30}; do sleep 2; if up; then return 0; fi; done
  return 1
}

stamp() { date "+%Y-%m-%d %H:%M:%S" }
say()   { print -r -- "$(stamp)  $1" | tee -a $LOG >> $STATUS }

print -r -- "$(stamp)  watch started, every ${INTERVAL}s" > $STATUS
while [[ ! -f $STOP ]]; do
  if ! up; then
    say "server not answering -- restarting"
    if start_server; then say "server back up"
    else say "RESTART FAILED -- see $DIR/server.log"; fi
  fi
  if up; then
    if out=$(python3 scripts/check_sim.py A C E 2>&1); then
      n=$(print -r -- "$out" | grep -c "\[PASS\]")
      say "checklist ok ($n items)"
    else
      say "CHECKLIST FAILED:"
      print -r -- "$out" | grep -E "\[FAIL\]|실패:" | head -8 \
        | while read -r l; do print -r -- "            $l" >> $STATUS; done
      print -r -- "$out" >> $LOG
    fi
  fi
  # sleep in slices so a stop request lands quickly
  for i in {1..$INTERVAL}; do [[ -f $STOP ]] && break; sleep 1; done
done
say "watch stopped"
