#!/bin/bash
# NEEL GP wave loop - one command per half-cycle.
#
#   ./wave_loop.sh plan   <k> [size]   build/extend pool -> GP picks wave k -> VASP inputs -> push -> (print) submit cmd
#   ./wave_loop.sh submit <k>          submit wave k on Perlmutter (packed job sized by pick_nodes)
#   ./wave_loop.sh ingest              pull finished runs -> labels.csv -> H1 report -> GP CV
#   ./wave_loop.sh status              what is in the queue and how many labels exist
#
# Where each step runs:
#   laptop  : pool (MACE, venv python), GP (system python + sklearn), inputs, push, ingest
#   NERSC   : submit (ssh), VASP.  When deployed ON Perlmutter (see DEPLOY_NERSC.md) the
#             ssh/push steps are no-ops and PY_MACE / PY_GP point at the conda env.
set -euo pipefail
cd "$(dirname "$0")"

: "${PY_MACE:=/Users/g5q/Documents/GitHub/siteseer/.venv/bin/python}"   # torch + mace + pymatgen
: "${PY_GP:=python3}"                                                    # pymatgen + sklearn + scipy
: "${VASP_PP_PATH:=/Users/g5q/Documents/Codes/VASP/potpaw_PBE.64}"
: "${NERSC_USER:=gpanchap}"; : "${NERSC_HOST:=perlmutter.nersc.gov}"; : "${REMOTE_DIR:=/pscratch/sd/g/gpanchap/workflow}"
: "${NERSC_ACCOUNT:=m2113}"; : "${QOS:=regular}"; : "${PER_RUN_MIN:=90}"
: "${ON_NERSC:=0}"       # 1 when this script itself runs on a Perlmutter login node
export VASP_PP_PATH
SSL_CERT_FILE=$($PY_MACE -c "import certifi;print(certifi.where())" 2>/dev/null || true); export SSL_CERT_FILE

cmd="${1:-status}"; k="${2:-1}"; size="${3:-40}"
case "$cmd" in
  plan)
    echo "== 1/4 pool (MACE relax + same-model hull + descriptors)"
    $PY_MACE wave_pool.py ${POOL_ARGS:-}
    echo "== 2/4 GP: train on Gd pairs + ingested waves, acquire wave $k ($size runs)"
    $PY_GP wave_gp.py --wave "$k" --size "$size" ${GP_ARGS:-}
    echo "== 3/4 VASP inputs"
    $PY_GP wave_inputs.py --wave "$k"
    if [ "$ON_NERSC" = 0 ]; then
      echo "== 4/4 push inputs to $NERSC_HOST"
      ./push_new_runs.sh "runs/wave$k" "batch/wave_${k}_runs.txt" wave_*.py wave_features.py light_re_results.py
      echo; echo "next:  ./wave_loop.sh submit $k"
    else
      echo "== 4/4 (on NERSC) nothing to push"; echo "next:  ./wave_loop.sh submit $k"
    fi ;;
  submit)
    n=$(wc -l < "batch/wave_${k}_runs.txt" | tr -d ' ')
    opt=$($PY_GP pick_nodes.py --runs "$n" --per-run-min "$PER_RUN_MIN" --max-wall-h 4 --shell 2>/dev/null | grep '^PACK_NODES' || true)
    nodes=$(echo "$opt" | sed -n 's/.*PACK_NODES=\([0-9]*\).*/\1/p'); nodes="${nodes:-$n}"
    [ "$nodes" -gt "$n" ] && nodes="$n"
    sub="cd $REMOTE_DIR && NERSC_ACCOUNT=$NERSC_ACCOUNT MANIFEST=batch/wave_${k}_runs.txt PACK_NODES=$nodes PER_RUN_MIN=$PER_RUN_MIN WALLTIME=03:00:00 QOS=$QOS ./submit_batch.sh"
    echo "submitting wave $k: $n runs on $nodes nodes ($QOS)"
    if [ "$ON_NERSC" = 1 ]; then bash -c "$sub"; else ssh "$NERSC_USER@$NERSC_HOST" "$sub"; fi ;;
  ingest)
    if [ "$ON_NERSC" = 0 ]; then ./sync_results.sh --mirror; fi
    $PY_GP wave_ingest.py
    echo "== GP cross-validation with the new labels"
    $PY_GP wave_gp.py --cv ;;
  status)
    [ "$ON_NERSC" = 0 ] && ssh "$NERSC_USER@$NERSC_HOST" 'squeue --me -o "%.10i %.8q %.4D %.10l %.8T %.12M %R"' || squeue --me -o "%.10i %.8q %.4D %.10l %.8T %.12M %R"
    [ -f analysis/pool/labels.csv ] && echo "labels: $(( $(wc -l < analysis/pool/labels.csv) - 1 ))"
    [ -f analysis/pool/pool.csv ] && echo "pool:   $(( $(wc -l < analysis/pool/pool.csv) - 1 ))"
    ls analysis/pool/wave_*.csv 2>/dev/null || true ;;
  *) echo "usage: $0 plan <k> [size] | submit <k> | ingest | status"; exit 1 ;;
esac
