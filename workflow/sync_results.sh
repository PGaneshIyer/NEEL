#!/bin/bash
# Pull finished DFT results back from NERSC into the local run tree.
#
#   ./sync_results.sh --fast      # analyse REMOTELY, pull 0.3 MB  <- use this
#   ./sync_results.sh --check     # how many are done, how big
#   ./sync_results.sh             # full pull, then analyse locally
#   ./sync_results.sh --dry-run   # show what would transfer
#
# Defaults to gpanchap@perlmutter.nersc.gov:/pscratch/sd/g/gpanchap/workflow;
# override with NERSC_USER / NERSC_HOST / REMOTE_DIR.
#
# NOTE /pscratch is PURGED (files untouched for ~8 weeks are deleted). The run
# tree there is ~38 GB of archives plus results - copy anything you need to keep
# to CFS (/global/cfs/cdirs/<project>/) before it ages out.
#
# Pulls ONLY what analysis needs (OUTCAR, OSZICAR, vasp.log, CONTCAR, .node) and
# never WAVECAR/CHGCAR/POTCAR - those are large, already local, or regenerable.
# There is no --delete in this direction: a local file is never removed because
# the remote run has not finished yet.
set -euo pipefail
cd "$(dirname "$0")"

: "${NERSC_USER:=gpanchap}"
HOST="${NERSC_HOST:-perlmutter.nersc.gov}"
REMOTE="${REMOTE_DIR:-/pscratch/sd/g/gpanchap/workflow}"
MODE="${1:-}"

# VASP writes OUTCAR at startup, so "file exists" does not mean finished; the
# timing block does. LDAUPRINT dumps the 4f occupancy AFTER it (~260 lines per
# Gd), so check the tail generously, then the whole file.
DONE_TEST='tail -n 5000 "$1" 2>/dev/null | grep -q "General timing and accounting" \
           || grep -q "General timing and accounting" "$1" 2>/dev/null'

if [ "$MODE" = "--check" ]; then
  echo "querying $NERSC_USER@$HOST:$REMOTE ..."
  ssh "$NERSC_USER@$HOST" "cd $REMOTE || exit 1
    total=\$(find runs -name INCAR | wc -l)
    started=\$(find runs -name OUTCAR | wc -l)
    done=\$(find runs -name OUTCAR -exec sh -c '$DONE_TEST' _ {} \; -print | wc -l)
    echo \"  runs total    : \$total\"
    echo \"  started       : \$started\"
    echo \"  FINISHED      : \$done\"
    echo \"  transfer size : \$(find runs \\( -name OUTCAR -o -name OSZICAR -o -name vasp.log -o -name CONTCAR \\) -print0 | du -ch --files0-from=- 2>/dev/null | tail -1)\"
  "
  exit 0
fi

if [ "$MODE" = "--fast" ]; then
  # OUTCARs are 98% of the payload (468 MB of 477 MB) and the tree carries ~38 GB
  # of archived _01/_02 files that rsync must stat even though it never sends
  # them. analyze.py is stdlib-only so it runs on a login node: do the analysis
  # where the data already is and bring back only the result.
  echo "running analyze.py on $HOST (no bulk transfer) ..."
  ssh "$NERSC_USER@$HOST" "cd $REMOTE && python3 analyze.py" | tail -25
  rsync -az --info=progress2 \
    "$NERSC_USER@$HOST:$REMOTE/results.json" \
    "$NERSC_USER@$HOST:$REMOTE/results_summary.csv" .
  echo "pulled results.json + results_summary.csv only"
  exit 0
fi

RSYNC_OPTS=(-a -m -z --progress
            --exclude='*_[0-9][0-9]'      # archived attempts: never transfer, and
                                          # pruning them early also stops rsync
                                          # stat-ing ~38 GB of files it will skip
            --include='*/' --include='OUTCAR' --include='OSZICAR' --include='vasp.log'
            --include='CONTCAR' --include='.node' --exclude='*')
[ "$MODE" = "--dry-run" ] && RSYNC_OPTS+=(--dry-run --stats)

echo "pulling results from $NERSC_USER@$HOST:$REMOTE/runs/ ..."
rsync "${RSYNC_OPTS[@]}" "$NERSC_USER@$HOST:$REMOTE/runs/" runs/

# the job logs are small and worth keeping: they hold the packing check,
# per-run timings and the node each calculation ran on
rsync -a -m -z --include='*/' --include='*.out' --include='*.err' --exclude='*' \
      "$NERSC_USER@$HOST:$REMOTE/batch/logs/" batch/logs/ 2>/dev/null || true

if [ "$MODE" = "--dry-run" ]; then
  echo "(dry run - nothing written)"; exit 0
fi

echo
echo "=== local completion status ==="
tot=$(find runs -name INCAR | wc -l | tr -d ' ')
fin=$(find runs -name OUTCAR -exec sh -c "$DONE_TEST" _ {} \; -print | wc -l | tr -d ' ')
echo "  finished locally: $fin / $tot"
echo
python3 analyze.py
