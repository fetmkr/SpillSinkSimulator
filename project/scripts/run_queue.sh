#!/bin/zsh
# Keep the search running without an assistant turn to drive it.
#
#   ./scripts/run_queue.sh &            # from project/
#   tail -f logs/queue.log
#   touch logs/STOP                     # stop after the current job
#
# WHY THIS EXISTS. The sweeps were being launched one shot at a time from a
# chat turn. sweep_topo finished at 00:34 and nothing started the next job,
# because the only thing that ever started a job was a turn, and no turn ran
# for eight hours. The machine sat idle. A queue on disk does not have that
# failure mode: it outlives the session, survives a session moving to another
# machine, and its state is a log file anyone can read.
#
# Every job is RESUMABLE -- each sweep loads its own CSV, skips the
# (tag, material) pairs already present, and appends. So re-running a finished
# job costs one startup and exits; killing one mid-way loses at most the design
# in flight. That is what makes an unattended loop safe here.

set -u
cd "$(dirname "$0")/.." || exit 1

BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p logs
LOG=logs/queue.log

log() { print -r -- "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG" }

# run_job <name> <script> [ENV=VAL ...]
run_job() {
  local name=$1 script=$2; shift 2
  if [[ -f logs/STOP ]]; then log "STOP present, not starting $name"; return 1; fi
  log "START $name"
  local t0=$SECONDS
  # any remaining args are NAME=VALUE and are passed as environment to this job
  # only -- STAGE=2 is how the seed-replicate pass reuses the same script
  # --python-exit-code 77: Blender exits 0 even when the Python script raises,
  # so rc alone is NOT a health check. form_roughness died on an AttributeError
  # one second in and was logged as a clean success; a 40-minute job produced
  # nothing for a whole cycle and the only symptom was an empty output file.
  # This flag makes an exception reach the exit status. [확인: blender --help]
  env "$@" "$BLENDER" --background --factory-startup --python-exit-code 77 \
      --python "$script" >> "logs/$name.log" 2>&1
  local rc=$?
  local dt=$((SECONDS - t0))
  log "END   $name rc=$rc  ${dt}s"
  # a crashing job must NOT stop the queue; a job that crashes every cycle
  # shows up as a repeating non-zero rc, which is the thing to grep for
  if [[ $rc -eq 77 ]]; then
    log "WARN  $name raised a PYTHON EXCEPTION -- see logs/$name.log"
  elif [[ $rc -ne 0 ]]; then
    log "WARN  $name rc=$rc -- see logs/$name.log"
  fi
  # BLENDER EXITS 0 EVEN WHEN THE PYTHON SCRIPT RAISES. form_roughness died on
  # an AttributeError, ran for one second, and was logged as a success -- a
  # 40-minute job silently produced nothing for a whole cycle and the only
  # symptom was an empty output file. rc alone is not a health check here.
  if tail -60 "logs/$name.log" 2>/dev/null | grep -q "^Traceback"; then
    log "WARN  $name raised a Python exception despite rc=$rc -- see logs/$name.log"
  fi
  return 0
}

log "queue up, pid $$"

# One pass per cycle. Jobs are ordered cheapest-first so a fresh design list
# starts producing rows early rather than after the slowest job.
while true; do
  [[ -f logs/STOP ]] && { log "STOP present, exiting"; rm -f logs/STOP; break }

  # Ordered by what the next report needs. Each is a no-op once its own output
  # is complete, so the order only bites on a cold start.

  # 1. darkness, one seed -- the list everything else selects from
  run_job sweep_buildable scripts/sweep_buildable.py || break

  # 2. FORM -- the project's stated FIRST priority, and never measured until
  #    now. Slowest job here: 11 designs x 3 thetas x 16 stripe phases. The 16
  #    phases are the point; metrics/04 records a 214x swing across stripe
  #    phase and refuses to be quoted until it is averaged over one full pitch.
  run_job form_buildable  scripts/form_buildable.py || break

  # 3. darkness again over 12 geometry seeds, for error bars. Without this
  #    there is no ranking claim at all: the measured realisation spread is
  #    ~3.5% and the top 13 of the darkness ranking sit inside 1.09x.
  # 3a. the coating's specular roughness against the FORM metric, plus the
  #     flat-coating baseline metrics/04 is missing. Roughness moves theta=0
  #     peak by 332x (0.10 -> 0.50) while the whole nine-topology search moves
  #     it by 1.6x, so this is a bigger lever than any geometry decision so far
  #     and it has never been examined against form.
  run_job form_roughness  scripts/form_roughness.py || break

  # 3c. the two fabrication questions for the blade array: how much a tilt
  #     error costs, and whether restricting the blades to 0/90 degrees (which
  #     lets them be slotted together like an egg crate, with no base plate and
  #     no welding) keeps the 31% that random azimuth buys.
  run_job sweep_fab       scripts/sweep_fab.py || break

  # 3b. darkness over 12 geometry seeds, for error bars. Long -- 2160 designs.
  run_job sweep_seeds     scripts/sweep_buildable.py STAGE=2 || break

  run_job sweep_feature scripts/sweep_feature.py || break
  run_job sweep_topo   scripts/sweep_topo.py   || break
  run_job sweep_shapes scripts/sweep_shapes.py || break

  # Both jobs are no-ops once their design lists are exhausted, so without a
  # pause this spins on Blender startups. Sleep, then look again -- the point
  # is that when a design list GROWS, the queue picks it up on its own instead
  # of waiting for someone to notice.
  log "cycle complete, sleeping 300s"
  sleep 300
done

log "queue down"
