#!/bin/bash
# Pull finished DFT results back from NERSC into the local run tree.
#
#   ./sync_results.sh --fast               # analyse REMOTELY, pull 0.3 MB  <- quickest look
#   ./sync_results.sh --check              # how many are done, how big each mode is
#   ./sync_results.sh                      # results pull (OUTCAR/OSZICAR/CONTCAR/vasp.log/.node), then analyse
#   ./sync_results.sh --mirror             # analysis mirror: + INCAR KPOINTS POSCAR XDATCAR DOSCAR EIGENVAL IBZKPT (~5 GB)
#   ./sync_results.sh --mirror --archives  # + archived generations of the SMALL files (OUTCAR_01 ...), provenance
#   add --dry-run to any pull mode to see what would transfer
#
# Defaults to gpanchap@perlmutter.nersc.gov:/pscratch/sd/g/gpanchap/workflow;
# override with NERSC_USER / NERSC_HOST / REMOTE_DIR.
#
# NOTE /pscratch is PURGED (files untouched for ~8 weeks are deleted). --mirror
# is the local insurance copy of everything an analysis can need; still copy
# keepers to CFS (/global/cfs/cdirs/<project>/) on the NERSC side.
#
# What is NEVER pulled, in any mode: WAVECAR, CHG, CHGCAR, WAVEDER (restart
# files, 50+ MB/run) and vasprun.xml, vaspout.h5, PROCAR (~90 MB/run, ~65 GB
# over the campaign - and pure duplicates: vasprun = OUTCAR+DOSCAR+EIGENVAL in
# XML, vaspout.h5 the same in HDF5, PROCAR k-resolved projections for band
# structures). Fetch those per compound on demand if ever needed.
# There is no --delete in this direction: a local file is never removed because
# the remote run has not finished yet. Pull only; nothing on NERSC is written.
set -euo pipefail
cd "$(dirname "$0")"

: "${NERSC_USER:=gpanchap}"
HOST="${NERSC_HOST:-perlmutter.nersc.gov}"
REMOTE="${REMOTE_DIR:-/pscratch/sd/g/gpanchap/workflow}"

MODE="results"; DRY=0; ARCHIVES=0
for a in "$@"; do
  case "$a" in
    --fast|--check) MODE="${a#--}" ;;
    --mirror) MODE="mirror" ;;
    --archives) ARCHIVES=1 ;;
    --dry-run) DRY=1 ;;
    *) echo "unknown option $a"; exit 1 ;;
  esac
done

# VASP writes OUTCAR at startup, so "file exists" does not mean finished; the
# timing block does. LDAUPRINT dumps the 4f occupancy AFTER it (~260 lines per
# Gd), so check the tail generously, then the whole file.
DONE_TEST='tail -n 5000 "$1" 2>/dev/null | grep -q "General timing and accounting" \
           || grep -q "General timing and accounting" "$1" 2>/dev/null'

RESULT_FILES=(OUTCAR OSZICAR vasp.log CONTCAR .node)
MIRROR_FILES=("${RESULT_FILES[@]}" INCAR KPOINTS POSCAR XDATCAR DOSCAR EIGENVAL IBZKPT PCDAT REPORT meta.json)
ARCHIVE_SMALL=(OUTCAR OSZICAR CONTCAR INCAR vasp.log XDATCAR .node)   # archived *_NN worth keeping
BIG_NEVER=(WAVECAR WAVEDER CHG CHGCAR vasprun.xml vaspout.h5 PROCAR)

if [ "$MODE" = "check" ]; then
  echo "querying $NERSC_USER@$HOST:$REMOTE ..."
  rf=$(printf -- "-name %s -o " "${RESULT_FILES[@]}"); rf="${rf% -o }"
  mf=$(printf -- "-name %s -o " "${MIRROR_FILES[@]}"); mf="${mf% -o }"
  af=$(printf -- "-name %s_[0-9][0-9] -o " "${ARCHIVE_SMALL[@]}"); af="${af% -o }"
  ssh "$NERSC_USER@$HOST" "cd $REMOTE || exit 1
    total=\$(find runs -name INCAR -not -name '*_[0-9][0-9]' | wc -l)
    started=\$(find runs -name OUTCAR | wc -l)
    done=\$(find runs -name OUTCAR -exec sh -c '$DONE_TEST' _ {} \; -print | wc -l)
    echo \"  runs total          : \$total\"
    echo \"  started             : \$started\"
    echo \"  FINISHED            : \$done\"
    echo \"  results pull size   : \$(find runs \\( $rf \\) -print0 | du -ch --files0-from=- 2>/dev/null | tail -1 | cut -f1)\"
    echo \"  --mirror size       : \$(find runs \\( $mf \\) -print0 | du -ch --files0-from=- 2>/dev/null | tail -1 | cut -f1)\"
    echo \"  --archives extra    : \$(find runs \\( $af \\) -print0 | du -ch --files0-from=- 2>/dev/null | tail -1 | cut -f1)\"
    echo \"  never pulled (big)  : \$(find runs \\( -name 'WAVECAR*' -o -name 'CHG*' -o -name 'vasprun.xml*' -o -name 'vaspout.h5*' -o -name 'PROCAR*' \\) -print0 | du -ch --files0-from=- 2>/dev/null | tail -1 | cut -f1)\"
  "
  exit 0
fi

if [ "$MODE" = "fast" ]; then
  # OUTCARs are 98% of the results payload and the tree carries ~38 GB of
  # archives rsync must stat even though it never sends them. analyze.py is
  # stdlib-only so it runs on a login node: analyse where the data is.
  echo "running analyze.py on $HOST (no bulk transfer) ..."
  ssh "$NERSC_USER@$HOST" "cd $REMOTE && python3 analyze.py" | tail -25
  rsync -az --progress \
    "$NERSC_USER@$HOST:$REMOTE/results.json" \
    "$NERSC_USER@$HOST:$REMOTE/results_summary.csv" .
  echo "pulled results.json + results_summary.csv only"
  exit 0
fi

# ---- pull modes ----------------------------------------------------------------
# Filter rules are evaluated in order, first match wins:
#   1. the big files are excluded by name, archived or not
#   2. archived generations: excluded (default) or the small ones included
#   3. every directory is traversable, the wanted basenames are included
#   4. everything else is excluded
RSYNC_OPTS=(-a -m -z --progress)
for f in "${BIG_NEVER[@]}"; do RSYNC_OPTS+=(--exclude="$f" --exclude="${f}_[0-9][0-9]"); done
if [ "$MODE" = "mirror" ]; then
  FILES=("${MIRROR_FILES[@]}")
  if [ "$ARCHIVES" = 1 ]; then
    for f in "${ARCHIVE_SMALL[@]}"; do RSYNC_OPTS+=(--include="${f}_[0-9][0-9]"); done
  fi
  RSYNC_OPTS+=(--exclude='*_[0-9][0-9]')
  what="analysis mirror${ARCHIVES:+ (+ small archives)}"
else
  FILES=("${RESULT_FILES[@]}")
  RSYNC_OPTS+=(--exclude='*_[0-9][0-9]')     # archives: never transfer, and pruning
                                             # early stops rsync stat-ing ~38 GB
  what="results"
fi
RSYNC_OPTS+=(--include='*/')
for f in "${FILES[@]}"; do RSYNC_OPTS+=(--include="$f"); done
RSYNC_OPTS+=(--exclude='*')
[ "$DRY" = 1 ] && RSYNC_OPTS+=(--dry-run --stats)

echo "pulling $what from $NERSC_USER@$HOST:$REMOTE/runs/ ..."
rsync "${RSYNC_OPTS[@]}" "$NERSC_USER@$HOST:$REMOTE/runs/" runs/

# the job logs are small and worth keeping: they hold the packing check,
# per-run timings and the node each calculation ran on
rsync -a -m -z --include='*/' --include='*.out' --include='*.err' --include='*.manifest' --exclude='*' \
      "$NERSC_USER@$HOST:$REMOTE/batch/" batch/ 2>/dev/null || true

if [ "$DRY" = 1 ]; then
  echo "(dry run - nothing written)"; exit 0
fi

echo
echo "=== local completion status ==="
tot=$(find runs -name INCAR -not -name '*_[0-9][0-9]' | wc -l | tr -d ' ')
fin=$(find runs -name OUTCAR -exec sh -c "$DONE_TEST" _ {} \; -print | wc -l | tr -d ' ')
echo "  finished locally: $fin / $tot"
echo
python3 analyze.py
