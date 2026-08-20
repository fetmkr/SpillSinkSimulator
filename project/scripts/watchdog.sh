#!/bin/zsh
# Watches a background measurement and writes a one-line verdict the moment it
# ends, so a crash is visible without anyone asking.
#
# The first version had a race: launched before the job started, pgrep found
# nothing and it immediately wrote **DIED** for a job that had not begun. It
# now WAITS FOR THE PROCESS TO APPEAR (up to `waitfor` seconds) and says
# NEVER STARTED if it does not, which is a different fault from a crash and
# must not be reported as the same thing.
set -u
name="$1"; log="$2"; pat="$3"; waitfor="${4:-7200}"
S=/tmp/simsrv/WATCH.log
t=0
while ! pgrep -f "$pat" >/dev/null 2>&1; do
  sleep 5; t=$((t+5))
  if [ "$t" -ge "$waitfor" ]; then
    echo "[$(date '+%H:%M:%S')] $name  **NEVER STARTED** (${waitfor}s 대기)" >> $S
    exit 1
  fi
done
echo "[$(date '+%H:%M:%S')] $name  시작됨" >> $S
while pgrep -f "$pat" >/dev/null 2>&1; do sleep 15; done
if grep -q "@@DONE@@" "$log" 2>/dev/null; then
  echo "[$(date '+%H:%M:%S')] $name  DONE" >> $S
else
  echo "[$(date '+%H:%M:%S')] $name  **DIED**" >> $S
  grep -E "Error|Traceback|TypeError|ValueError|AssertionError|KeyError" "$log" \
    2>/dev/null | tail -4 | sed 's/^/    /' >> $S
  tail -3 "$log" 2>/dev/null | sed 's/^/    | /' >> $S
fi
