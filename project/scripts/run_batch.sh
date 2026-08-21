#!/bin/zsh
# Run a Blender batch and REFUSE to call it finished without its own marker.
#
# Three runs of the furnace sweep stopped partway through with no traceback and
# exit code 0 -- Cycles' Metal shader cache double-frees on recompile. Two more
# jobs died on a loud TypeError that nobody read, because the log's last line
# was a data row and the table looked plausible. Both failures LOOK like
# success in a log file, so the marker is the only honest test.
#
# usage: run_batch.sh <script.py> [log-name]   (env ONLY= passes through)
set -u
ROOT="/Users/hojunsong/Desktop/Desktop - hojun’s mbp/SpillSinkSimulator/project"
BL=/Applications/Blender.app/Contents/MacOS/Blender
S="$1"; NAME="${2:-$(basename ${1%.py})}"
LOG="/tmp/simsrv/${NAME}.log"
MAN=/tmp/simsrv/BATCH_STATUS.tsv
cd "$ROOT"

run_once() { "$BL" --background --factory-startup --python "$S" > "$LOG" 2>&1; print $? }

t0=$SECONDS
code=$(run_once)
if ! grep -q "@@DONE@@" "$LOG"; then
  if grep -qi "Traceback\|Error:" "$LOG"; then
    why="crashed with an error"
  elif ! grep -q "Blender quit" "$LOG"; then
    # Blender prints "Blender quit" on a clean exit and does NOT when it
    # aborts, so a log with neither the marker nor that line is the Metal
    # shader-cache abort. This is also the only check available for the ~98
    # older sweep scripts that print no marker of their own.
    why="aborted before Blender could quit -- the Metal shader cache"
    # no traceback means the Metal cache is the prime suspect; give it one
    # more go with a warm cache before believing it
    print "  retrying $NAME once (no error, no marker)"
    code=$(run_once)
  fi
fi
el=$((SECONDS - t0))
if grep -q "@@DONE@@" "$LOG"; then
  st="DONE"; why="-"
else
  st="**DIED**"
  grep -qi "Traceback\|Error:" "$LOG" && why="$(grep -i 'Error' "$LOG" | tail -1 | cut -c1-110)" \
    || why="no error, no marker, exit $code -- suspect the Metal shader cache"
fi
print -r -- "$(date '+%H:%M:%S')\t$st\t$NAME\t${el}s\t$why" >> $MAN
print -r -- "$st  $NAME  ${el}s  $why"
