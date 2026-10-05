#!/bin/bash
#SBATCH -J __JOBNAME__
#SBATCH -A __ACCOUNT__
#SBATCH -C gpu
#SBATCH -q __QOS__
#SBATCH -N __NODES__
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-node=4
#SBATCH -t __WALLTIME__
#SBATCH -o __LOGDIR__/%x.%j.out
#SBATCH -e __LOGDIR__/%x.%j.err

# ONE allocation of __NODES__ nodes running __NODES__ VASP calculations at a time,
# each on its own node. A shared work queue feeds the workers, so a node that
# finishes a small cell immediately pulls the next run instead of idling - which
# is why this beats static striping for a set with 6- to 68-atom cells.
#
# Per-run output goes to <rundir>/vasp.log; the run is skipped if OUTCAR exists,
# so resubmitting after a timeout resumes cleanly.

module load vasp/6.4.3-gpu

export OMP_NUM_THREADS=1
export SLURM_CPU_BIND=cores

MANIFEST="__MANIFEST__"
NODES=__NODES__
TOTAL=$(wc -l < "$MANIFEST" | tr -d ' ')
CTR="${MANIFEST}.ctr.$SLURM_JOB_ID"
LOCK="${MANIFEST}.lock.$SLURM_JOB_ID"
echo 0 > "$CTR"; touch "$LOCK"
echo "packed job: $TOTAL runs over $NODES nodes"

next_index() {   # atomically pop the next task index
    flock "$LOCK" bash -c "i=\$(cat '$CTR'); echo \$((i+1)) > '$CTR'; echo \$i"
}

# Consecutive near-instant failures mean something systemic is wrong (bad module,
# missing POTCAR, srun rejecting the step geometry). Without this guard the
# workers would race through the whole manifest failing every run in seconds.
FAILS="${MANIFEST}.fails.$SLURM_JOB_ID"; echo 0 > "$FAILS"
FAIL_LIMIT=${FAIL_LIMIT:-10}
PROGRESS="${MANIFEST}.progress.$SLURM_JOB_ID"; : > "$PROGRESS"

worker() {
    local wid=$1
    while :; do
        local idx; idx=$(next_index)
        [ "$idx" -ge "$TOTAL" ] && break
        if [ "$(cat "$FAILS")" -ge "$FAIL_LIMIT" ]; then
            echo "[w$wid] ABORT: $FAIL_LIMIT consecutive fast failures"; break
        fi
        local d; d=$(sed -n "$((idx + 1))p" "$MANIFEST")
        [ -d "$d" ] || { echo "[w$wid] missing dir: $d"; continue; }
        # finished == VASP wrote its timing block; a partial OUTCAR from a
        # walltime kill must be re-run, not mistaken for a completed job.
        # LDAUPRINT prints the 4f occupancy matrices after that block (~260 lines
        # per Gd), so check the tail first, then the whole file.
        if [ -f "$d/OUTCAR" ] && { tail -n 5000 "$d/OUTCAR" 2>/dev/null \
                | grep -q 'General timing and accounting' \
             || grep -q 'General timing and accounting' "$d/OUTCAR" 2>/dev/null; }; then
            echo "[w$wid] skip (done): $d"; continue
        fi
        [ -f "$d/OUTCAR" ] && echo "[w$wid] re-running (partial OUTCAR): $d"
        local t0; t0=$(date +%s)
        echo "+1 $t0 1" >> "$PROGRESS"
        echo "$(date '+%F %T') [w$wid] START $((idx + 1))/$TOTAL $d"
        local rc=0
        (
            cd "$d" || exit 1
            # record which node actually ran this, so packing can be verified
            srun --exclusive -N 1 -n 1 hostname > .node 2>/dev/null || true
            srun --exclusive -N 1 -n 4 -c 32 --cpu-bind=cores \
                 --gpus-per-node=4 --gpu-bind=none vasp_std > vasp.log 2>&1
        ) || rc=$?
        local dt=$(( $(date +%s) - t0 ))
        echo "-1 $(date +%s) 0" >> "$PROGRESS"
        echo "$(date '+%F %T') [w$wid] END   $((idx + 1))/$TOTAL rc=$rc ${dt}s node=$(cat "$d/.node" 2>/dev/null) $d"
        if [ "$rc" -ne 0 ] && [ "$dt" -lt 60 ]; then
            flock "$LOCK" bash -c "f=\$(cat '$FAILS'); echo \$((f+1)) > '$FAILS'"
        else
            echo 0 > "$FAILS"
        fi
    done
}

for w in $(seq 1 "$NODES"); do worker "$w" & done
wait
rm -f "$FAILS"

# Concurrency report: peak number of runs in flight. If this comes back as 1 the
# srun steps serialised instead of packing onto separate nodes, and the whole
# point of packed mode was lost - check the step geometry before resubmitting.
echo "--- packing check ---"
# ties: count ENDs (field3=0) before STARTs (field3=1) so peak is not inflated
sort -k2,2n -k3,3n "$PROGRESS" | awk -v want="$NODES" '
  {cur += $1; if (cur > peak) peak = cur}
  END {
    printf "peak concurrent runs: %d (requested %d nodes)\n", peak, want
    if (peak <= 1)
      print "WARNING: steps did NOT pack - they ran one at a time."
    else if (peak < want * 0.8)
      printf "WARNING: only %d%% of nodes were kept busy.\n", 100 * peak / want
    else
      print "OK: steps packed across nodes as intended."
  }'
echo "distinct nodes used: $(while read -r d; do cat "$d/.node" 2>/dev/null; done < "$MANIFEST" | sort -u | wc -l)"
rm -f "$PROGRESS"
rm -f "$CTR" "$LOCK"
echo "packed job complete"
