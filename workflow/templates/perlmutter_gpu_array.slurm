#!/bin/bash
#SBATCH -J __JOBNAME__
#SBATCH -A __ACCOUNT__
#SBATCH -C gpu
#SBATCH -q __QOS__
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-node=4
#SBATCH -t __WALLTIME__
#SBATCH --array=0-__ARRAYMAX__
#SBATCH -o __LOGDIR__/%x.%A_%a.out
#SBATCH -e __LOGDIR__/%x.%A_%a.err

# One array task = one fm/ferri run directory, read from the manifest.
# NERSC Perlmutter GPU VASP (https://docs.nersc.gov/applications/vasp/)
module load vasp/6.4.3-gpu

export OMP_NUM_THREADS=1
export SLURM_CPU_BIND=cores

MANIFEST="__MANIFEST__"
RUNDIR="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$MANIFEST")"
[ -d "$RUNDIR" ] || { echo "no such run dir: $RUNDIR"; exit 1; }
cd "$RUNDIR"
# finished == VASP wrote its timing block; a partial OUTCAR from a walltime kill
# must be re-run rather than mistaken for a completed job
# LDAUPRINT prints 4f occupancy matrices after the timing block (~260 lines per
# Gd), so no fixed tail window is safe: check the tail, then the whole file.
if [ -f OUTCAR ] && { tail -n 5000 OUTCAR 2>/dev/null | grep -q 'General timing and accounting' \
     || grep -q 'General timing and accounting' OUTCAR 2>/dev/null; }; then
    echo "completed OUTCAR in $RUNDIR - skipping"; exit 0
fi

srun -n 4 -c 32 --cpu-bind=cores -G 4 --gpu-bind=none vasp_std
