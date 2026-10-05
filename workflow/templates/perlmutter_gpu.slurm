#!/bin/bash
#SBATCH -J __JOBNAME__
#SBATCH -A __ACCOUNT__
#SBATCH -C gpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --ntasks-per-node=4
#SBATCH -c 32
#SBATCH --gpus-per-node=4
#SBATCH -t 01:00:00
#SBATCH -o vasp.%j.out
#SBATCH -e vasp.%j.err

# NERSC Perlmutter GPU VASP (see https://docs.nersc.gov/applications/vasp/)
module load vasp/6.4.3-gpu

export OMP_NUM_THREADS=1
export SLURM_CPU_BIND=cores

srun -n 4 -c 32 --cpu-bind=cores -G 4 --gpu-bind=none vasp_std
