#!/bin/bash
# Batch submission grouped by HREE. Two modes:
#
#   array  (default) - one SLURM job array per rare earth; each task is its own
#                      1-node job. Tasks DO run in parallel, but only as many as
#                      NERSC's per-user running-job limit allows, so a 158-task
#                      array can trickle through rather than land at once.
#   packed           - one multi-node allocation per rare earth; PACK_NODES runs
#                      execute concurrently, one per node, fed by a shared work
#                      queue. The scheduler sees a single job, so the whole group
#                      starts together and no run waits behind a job-count cap.
#
#   NERSC_ACCOUNT=mXXXX ./submit_batch.sh                    # arrays, all HREE
#   NERSC_ACCOUNT=mXXXX ./submit_batch.sh Gd Tb              # only these groups
#   NERSC_ACCOUNT=mXXXX PACK_NODES=auto ./submit_batch.sh    # packed, auto-sized
#   NERSC_ACCOUNT=mXXXX PACK_NODES=25 ./submit_batch.sh Gd   # packed, explicit
#   DRY=1 PACK_NODES=auto ./submit_batch.sh                  # preview only
#
# Do NOT set PACK_NODES to the number of runs: a packed job is billed
# nodes x total wall time, so one node per run leaves nearly every node idle
# waiting on the slowest cell (~95% waste for this set), and it finishes no
# sooner than the longest single run. RUNS_PER_NODE (default 6) and MAX_NODES
# (default 40) tune the "auto" sizing.
#
# A run is pending when it has INCAR+POTCAR and no OUTCAR, so re-running this
# script after a timeout or preemption resubmits only what is left. Manifests and
# logs are written under batch/.
set -euo pipefail
cd "$(dirname "$0")"

[ "${DRY:-0}" = "1" ] || : "${NERSC_ACCOUNT:?set NERSC_ACCOUNT=your allocation (e.g. m1234)}"
PACK_NODES="${PACK_NODES:-0}"        # 0 = array mode, "auto", or an explicit count
RUNS_PER_NODE="${RUNS_PER_NODE:-6}"  # auto-sizing target
# Perlmutter GPU queue-wait by node band (Iris, regular QOS, average hours):
#   1 node 50.7 | 2-3 34.9 | 4-7 31.1 | 8-15 35.4 | 16-31 27.3 | 32-63 18.7
#   64-127 45.4 | 128-255 63.9
# The 32-63 band waits by far the least, so auto-sizing targets it: a couple of
# idle nodes on the tail costs far less than 15-30 extra hours in the queue.
MIN_NODES="${MIN_NODES:-32}"         # floor for auto-sizing (fast-queue band)
MAX_NODES="${MAX_NODES:-63}"         # ceiling for auto-sizing (fast-queue band)
WALLTIME="${WALLTIME:-auto}"         # "auto", or an explicit HH:MM:SS
PER_RUN_MIN="${PER_RUN_MIN:-30}"     # assumed minutes for ONE fm/ferri run
MAX_WALL_MIN="${MAX_WALL_MIN:-720}"  # regular QOS caps at 12 h
QOS="${QOS:-regular}"                # debug (<=8 nodes, 30 min) is great for timing

fmt_hms() { printf '%02d:%02d:00' $(( $1 / 60 )) $(( $1 % 60 )); }

# A run counts as finished only if VASP wrote its end-of-run timing block.
# "OUTCAR exists" is NOT enough: VASP creates OUTCAR at startup, so a run killed
# by a walltime limit leaves a partial OUTCAR that would otherwise be skipped
# forever as though it had completed.
# LDAUPRINT dumps the 4f occupancy matrices AFTER the timing block, and that dump
# grows with the number of Gd atoms (~260 lines each: 526 for GdFe2's 2 Gd, ~2400
# for the 9-Gd cells here). So no fixed tail window is safe - check the tail first
# for speed, then fall back to scanning the whole file. Runs that never started
# have no OUTCAR at all and cost nothing here.
vasp_done() {
  [ -f "$1/OUTCAR" ] || return 1
  tail -n 5000 "$1/OUTCAR" 2>/dev/null | grep -q 'General timing and accounting' && return 0
  grep -q 'General timing and accounting' "$1/OUTCAR" 2>/dev/null
}
if [ "$PACK_NODES" != "0" ]; then
  TEMPLATE="templates/perlmutter_gpu_packed.slurm"
else
  TEMPLATE="templates/perlmutter_gpu_array.slurm"
fi
mkdir -p batch/logs

# which HREE groups to submit (default: all found under runs/<arity>/<HREE>/)
# MANIFEST=file  submits exactly the run dirs listed in that file instead - use
# this when other runs are already in flight, since a plain scan would see
# their unfinished OUTCARs as "pending" and submit them a second time.
if [ -n "${MANIFEST:-}" ]; then
  [ -f "$MANIFEST" ] || { echo "MANIFEST=$MANIFEST not found"; exit 1; }
  HREES="custom"
elif [ $# -gt 0 ]; then HREES="$*"; else
  HREES="$(find runs -mindepth 2 -maxdepth 2 -type d -exec basename {} \; | sort -u)"
fi

for ree in $HREES; do
  # "custom" runs use a unique filename per submission: the array template reads
  # this file LIVE, by line number, when each task actually starts - and with a
  # fixed "batch/custom.manifest" name, a later custom submission overwrites the
  # file an earlier one's still-pending (not-yet-started) tasks depend on. A
  # 10-task array can trickle in over days, so this is not a narrow race - it
  # already silently truncated a real submission's tail tasks to "no such run
  # dir" once. HREE-named manifests (Gd.manifest etc.) don't need this: each
  # HREE group only appears once per invocation.
  if [ "$ree" = "custom" ]; then
    manifest="batch/custom_$(date +%Y%m%d_%H%M%S).manifest"
  else
    manifest="batch/${ree}.manifest"
  fi
  : > "$manifest"
  if [ "$ree" = "custom" ]; then
    # explicit list: absolute or runs-relative paths, one per line
    while IFS= read -r d; do
      [ -z "$d" ] && continue
      case "$d" in /*) ;; *) d="$PWD/$d" ;; esac
      [ -f "$d/INCAR" ] && [ -f "$d/POTCAR" ] && ! vasp_done "$d" && echo "$d" >> "$manifest"
    done < "$MANIFEST"
  else
    # "all" pools every HREE into ONE job - one queue wait instead of six
    if [ "$ree" = "all" ]; then
      findpath="runs"
    else
      findpath="runs -mindepth 2 -path */${ree}/*"
    fi
    # shellcheck disable=SC2086
    find $findpath -type d \( -name fm -o -name ferri \) | sort | \
    while IFS= read -r d; do
      [ -f "$d/INCAR" ] && [ -f "$d/POTCAR" ] && ! vasp_done "$d" && echo "$PWD/$d" >> "$manifest"
    done
  fi
  # Longest-processing-time-first: run the biggest cells first. Cost varies ~40x
  # across this set (6 to 68 atoms), so if the 68-atom cell is picked up last it
  # adds its full runtime as a tail; started first, it overlaps everything else.
  if [ -s "$manifest" ]; then
    while IFS= read -r d; do
      a=$(awk 'NR==7{s=0; for(i=1;i<=NF;i++) s+=$i; print s+0; exit}' "$d/POSCAR" 2>/dev/null)
      echo "${a:-0} $d"
    done < "$manifest" | sort -rn | cut -d' ' -f2- > "$manifest.lpt" \
      && mv "$manifest.lpt" "$manifest"
  fi
  n=$(wc -l < "$manifest" | tr -d ' ')
  if [ "$n" -eq 0 ]; then echo "-- $ree: nothing pending"; rm -f "$manifest"; continue; fi
  job="batch/${ree}.slurm"
  # Node count for packed mode. A packed job is charged nodes x total wall time,
  # so asking for one node per run leaves almost every node idle waiting on the
  # slowest cell. "auto" targets ~RUNS_PER_NODE runs per node, which keeps the
  # queue fed and the idle tail small; the makespan can never beat the single
  # longest run anyway, so more nodes past that point buys nothing.
  sizing_src=""; wait_h=""; run_h=""; band=""
  if [ "$PACK_NODES" = "optimal" ]; then
    # ask pick_nodes.py, which queries live NERSC queue statistics
    opt=$(python3 pick_nodes.py --runs "$n" --per-run-min "$PER_RUN_MIN" \
            --max-wall-h "$(( MAX_WALL_MIN / 60 ))" --shell 2>/dev/null) || opt=""
    if [ -n "$opt" ]; then
      for kv in $opt; do
        case "$kv" in
          PACK_NODES=*) nodes="${kv#*=}" ;;
          WALLTIME=*)   [ "$WALLTIME" = "auto" ] && WALLTIME_OPT="${kv#*=}" ;;
          SOURCE=*)     sizing_src="${kv#*=}" ;;
          WAIT_H=*)     wait_h="${kv#*=}" ;;
          RUN_H=*)      run_h="${kv#*=}" ;;
          BAND=*)       band="${kv#*=}" ;;
        esac
      done
    else
      sizing_src="pick_nodes-unavailable"
      nodes=$(( (n + RUNS_PER_NODE - 1) / RUNS_PER_NODE ))
      [ "$nodes" -lt "$MIN_NODES" ] && nodes="$MIN_NODES"
      [ "$nodes" -gt "$MAX_NODES" ] && nodes="$MAX_NODES"
    fi
  elif [ "$PACK_NODES" = "auto" ]; then
    sizing_src="static-heuristic"
    nodes=$(( (n + RUNS_PER_NODE - 1) / RUNS_PER_NODE ))
    [ "$nodes" -lt "$MIN_NODES" ] && nodes="$MIN_NODES"
    [ "$nodes" -gt "$MAX_NODES" ] && nodes="$MAX_NODES"
  else
    sizing_src="explicit"
    nodes="$PACK_NODES"
  fi
  [ "$nodes" -gt "$n" ] && nodes="$n"

  # Walltime. In ARRAY mode the clock is per task, so one run's allowance is
  # enough. In PACKED mode one job must cover every wave through the queue:
  # waves = ceil(runs / nodes), so the limit has to grow with the group.
  wall="$WALLTIME"
  waves=1
  [ "$PACK_NODES" != "0" ] && waves=$(( (n + nodes - 1) / nodes ))
  if [ -n "${WALLTIME_OPT:-}" ]; then
    wall="$WALLTIME_OPT"; unset WALLTIME_OPT
  elif [ "$WALLTIME" = "auto" ]; then
    if [ "$PACK_NODES" != "0" ]; then
      mins=$(( waves * PER_RUN_MIN * 13 / 10 ))     # +30% headroom
    else
      mins=$(( PER_RUN_MIN * 4 ))                   # generous single-run margin
    fi
    [ "$mins" -lt 60 ] && mins=60
    [ "$mins" -gt "$MAX_WALL_MIN" ] && mins="$MAX_WALL_MIN"
    wall=$(fmt_hms "$mins")
  fi
  sed -e "s/__JOBNAME__/magnito_${ree}/" \
      -e "s/__ACCOUNT__/${NERSC_ACCOUNT:-DRYRUN}/" \
      -e "s/__QOS__/${QOS}/" \
      -e "s/__ARRAYMAX__/$((n - 1))/" \
      -e "s/__NODES__/${nodes}/" \
      -e "s/__WALLTIME__/${wall}/" \
      -e "s|__LOGDIR__|$PWD/batch/logs|" \
      -e "s|__MANIFEST__|$PWD/$manifest|" \
      "$TEMPLATE" > "$job"
  # --- report exactly what was chosen, and where the numbers came from ---
  verb="submitting"; [ "${DRY:-0}" = "1" ] && verb="WOULD submit"
  echo "== $ree: $verb  ($n runs pending)"
  if [ "$PACK_NODES" != "0" ]; then
    echo "   mode      : packed   nodes=$nodes  waves=$waves  walltime=$wall  qos=$QOS"
  else
    echo "   mode      : array    tasks=0-$((n-1))  walltime=$wall per task  qos=$QOS"
  fi
  # array mode consults no queue data; label it honestly rather than "explicit 0"
  [ "$PACK_NODES" = "0" ] && sizing_src="array-mode"
  case "$sizing_src" in
    array-mode)
      echo "   sizing    : n/a - array mode, one node per task (no queue data consulted)" ;;
    iris-live)
      echo "   sizing    : LIVE Iris queue data  (node band ${band}+, reached iris.nersc.gov)"
      echo "   predicted : ~${wait_h} h queued + ${run_h} h running = $(awk -v a="$wait_h" -v b="$run_h" 'BEGIN{printf "%.1f", a+b}') h to results" ;;
    snapshot-fallback)
      echo "   sizing    : !! COULD NOT REACH iris.nersc.gov - used built-in snapshot"
      echo "   predicted : ~${wait_h} h queued + ${run_h} h running (from stale table)" ;;
    pick_nodes-unavailable)
      echo "   sizing    : !! pick_nodes.py failed to run - fell back to static heuristic" ;;
    static-heuristic)
      echo "   sizing    : static heuristic (no queue data; ${RUNS_PER_NODE} runs/node, ${MIN_NODES}-${MAX_NODES} nodes)" ;;
    explicit)
      echo "   sizing    : explicit PACK_NODES=$PACK_NODES (no queue data consulted)" ;;
  esac
  echo "   assumed   : PER_RUN_MIN=$PER_RUN_MIN min/run   manifest: $manifest (longest cells first)"
  if [ "${DRY:-0}" = "1" ]; then
    sed "s|$PWD/||" "$manifest" | head -3 | sed 's/^/     /'
    [ "$n" -gt 3 ] && echo "     ... and $((n - 3)) more"
  else
    sbatch "$job"
  fi
  echo
done
