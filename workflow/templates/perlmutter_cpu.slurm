#!/bin/bash
#SBATCH -J __JOBNAME__
#SBATCH -A __ACCOUNT__
#SBATCH -C cpu
#SBATCH -q regular
#SBATCH -N 1
#SBATCH --ntasks-per-node=128
#SBATCH -c 2
#SBATCH -t 02:00:00
#SBATCH -o vasp.%j.out
#SBATCH -e vasp.%j.err

# NERSC Perlmutter CPU VASP (see https://docs.nersc.gov/applications/vasp/)
module load vasp/6.4.3-cpu

export OMP_NUM_THREADS=1

srun -n 128 -c 2 --cpu-bind=cores vasp_std
