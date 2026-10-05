#!/bin/bash
# Submit every prepared fm/ferri run under runs/ to Perlmutter.
#   NERSC_ACCOUNT=mXXXX ./submit_all.sh [gpu|cpu]
# Skips directories that already contain an OUTCAR (rerun by deleting it).
set -euo pipefail
cd "$(dirname "$0")"

ARCH="${1:-gpu}"
: "${NERSC_ACCOUNT:?set NERSC_ACCOUNT=your allocation (e.g. m1234)}"
TEMPLATE="templates/perlmutter_${ARCH}.slurm"
[ -f "$TEMPLATE" ] || { echo "no template $TEMPLATE"; exit 1; }

# runs are nested as runs/<arity>/<HREE>/<polytype>/<compound>/<fm|ferri>
find runs -type d \( -name fm -o -name ferri \) | sort | while IFS= read -r d; do
  [ -f "$d/INCAR" ] || continue
  [ -f "$d/POTCAR" ] || { echo "SKIP $d (no POTCAR - see README)"; continue; }
  [ -f "$d/OUTCAR" ] && { echo "SKIP $d (OUTCAR exists)"; continue; }
  # job name: <compound>_<fm|ferri>
  name="$(basename "$(dirname "$d")")_$(basename "$d")"
  sed -e "s/__JOBNAME__/${name}/" -e "s/__ACCOUNT__/${NERSC_ACCOUNT}/" \
      "$TEMPLATE" > "$d/job.slurm"
  (cd "$d" && sbatch job.slurm)
done
