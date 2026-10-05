#!/bin/bash
# Push NEW local run directories (inputs only) up to NERSC, safely.
#
#   ./push_new_runs.sh --dry-run   # show what would transfer
#   ./push_new_runs.sh             # do it
#
# Mirrors sync_results.sh's philosophy in reverse: only send what a NEW run
# needs to be submitted (POSCAR, INCAR, KPOINTS, POTCAR, meta.json) plus the
# workflow scripts themselves. Never sends VASP outputs (OUTCAR, OSZICAR,
# CONTCAR, vasprun.xml, vaspout.h5, PROCAR, DOSCAR, EIGENVAL, WAVECAR, CHG*,
# IBZKPT, vasp.log) or archived generations (*_01, *_02, ...) - those are
# either large, remote-authoritative, or already covered by sync_results.sh
# in the OTHER direction. This is what the earlier bare `rsync -av` push
# should have used; it corrupted ~350 live INCARs by overwriting them with a
# stale local snapshot (recovered via fix_corrupted_incars.py).
#
# PREFER passing explicit paths:
#   ./push_new_runs.sh [--dry-run] runs/ternary/Tb/new-R3m/NewCompound_sub ...
# Only those paths are sent (rsync -R keeps them at the same place under the
# remote tree). A whole-tree push is only safe when every local INCAR is at
# least as new as its remote copy - which is NOT the case after remote-only
# work such as fix_corrupted_incars.py or relax_survivor.py: sync_results.sh
# never pulls INCARs back, so a bare push would quietly revert them.
set -euo pipefail
cd "$(dirname "$0")"

: "${NERSC_USER:=gpanchap}"
HOST="${NERSC_HOST:-perlmutter.nersc.gov}"
REMOTE="${REMOTE_DIR:-/pscratch/sd/g/gpanchap/workflow}"
MODE=""
if [ "${1:-}" = "--dry-run" ]; then MODE="--dry-run"; shift; fi
PATHS=("$@")

RSYNC_OPTS=(-a -m -z --progress
            --exclude='*_[0-9][0-9]'
            --exclude='OUTCAR' --exclude='OSZICAR' --exclude='CONTCAR'
            --exclude='vasprun.xml' --exclude='vaspout.h5' --exclude='PROCAR'
            --exclude='DOSCAR' --exclude='EIGENVAL' --exclude='IBZKPT'
            --exclude='WAVECAR' --exclude='CHG*' --exclude='vasp.log'
            --exclude='*.bak_corrupted')
[ "$MODE" = "--dry-run" ] && RSYNC_OPTS+=(--dry-run --stats)

if [ "${#PATHS[@]}" -gt 0 ]; then
  for p in "${PATHS[@]}"; do [ -e "$p" ] || { echo "no such path: $p"; exit 1; }; done
  echo "pushing ONLY: ${PATHS[*]}"
  rsync -R "${RSYNC_OPTS[@]}" "${PATHS[@]}" "$NERSC_USER@$HOST:$REMOTE/"
else
  echo "WARNING: whole-tree push - only safe if no INCAR was edited remotely since the last pull."
  echo "pushing new/changed inputs to $NERSC_USER@$HOST:$REMOTE/ ..."
  rsync "${RSYNC_OPTS[@]}" ./ "$NERSC_USER@$HOST:$REMOTE/"
fi

if [ "$MODE" = "--dry-run" ]; then
  echo "(dry run - nothing written)"
fi
