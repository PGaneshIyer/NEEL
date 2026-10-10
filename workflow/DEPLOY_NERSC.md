# Deploying the GP wave loop on Perlmutter

The loop has two halves. `plan` needs a machine-learned potential (MACE) and
the GP; `ingest` needs only Python. Both can run on a Perlmutter login node or
in a small CPU job, so the whole cycle can live on NERSC with no laptop in the
path. The VASP waves are ordinary packed GPU jobs submitted by
`submit_batch.sh`.

## 1. One-time environment

```bash
module load python
conda create -n neel python=3.11 -y
conda activate neel
pip install torch --index-url https://download.pytorch.org/whl/cpu   # MACE on CPU is enough for <= 40-atom cells
pip install mace-torch pymatgen scikit-learn scipy requests certifi ase
```

Put the Materials Project key in `workflow/.mp_api_key` (gitignored, mode 600)
or export `MP_API_KEY`. The MACE-MP-0 medium checkpoint downloads on first use
(~100 MB) into `~/.cache/mace`.

MACE relaxations of 30-atom cells take 2-5 s each on a login-node core; a pool
of 1,000 candidates is under an hour. If login-node limits bite, run `plan`
inside a 1-node CPU job (`-C cpu -q shared -c 16 -t 2:00:00`).

## 2. Paths and variables

```bash
cd /pscratch/sd/g/gpanchap/workflow
export ON_NERSC=1
export PY_MACE=$(which python)   # the neel conda env
export PY_GP=$(which python)
export VASP_PP_PATH=/pscratch/sd/g/gpanchap/potpaw_PBE.64   # never in git
export NERSC_ACCOUNT=m2113 QOS=regular PER_RUN_MIN=90
```

`/pscratch` is purged after 8 weeks of inactivity. Keep `analysis/pool/`
(pool, waves, labels) and `batch/wave_*` under `$CFS/m2113/neel/` with a
weekly `rsync`; the run directories are re-creatable from the pool.

## 3. One cycle

```bash
./wave_loop.sh plan 1 40      # pool -> GP -> inputs (runs/wave1/...) -> batch/wave_1_runs.txt
./wave_loop.sh submit 1       # pick_nodes sizes the packed job, submit_batch.sh submits it
# ... queue (1-2 days regular) + ~3 h run ...
./wave_loop.sh ingest         # parse OUTCARs -> analysis/pool/labels.csv ; H1 check ; GP CV
./wave_loop.sh plan 2 40      # the GP now includes wave-1 labels
```

`plan` is idempotent: the pool is cached per candidate, and the GP excludes
anything already labelled or already in an earlier wave file.

## 4. Automating with scrontab

Run `ingest` every 6 hours and `plan`+`submit` for the next wave whenever the
previous wave's job is no longer in the queue. A guard file prevents double
submission.

```cron
# scrontab -e
#SCRON -q cron
#SCRON -A m2113
#SCRON -t 01:00:00
0 */6 * * * bash -lc 'cd /pscratch/sd/g/gpanchap/workflow && conda activate neel && export ON_NERSC=1 && ./wave_loop.sh ingest >> batch/logs/wave_ingest.log 2>&1 && ./wave_next.sh >> batch/logs/wave_next.log 2>&1'
```

`wave_next.sh` (three lines, create when ready):

```bash
k=$(ls analysis/pool/wave_*.csv 2>/dev/null | wc -l); k=$((k+1))
squeue --me -h -n magnito_custom | grep -q . && exit 0        # a wave is still queued/running
./wave_loop.sh plan $k 40 && ./wave_loop.sh submit $k
```

## 5. Stopping rules (decided by the data, not the cron)

* the GP's feasible count in `analysis/pool/gp_report.txt` drops to zero, or
* two consecutive waves add no candidate to the Pareto front of
  (gap_RE, Ms, E_hull) in `labels.csv`, or
* hypothesis H1 fails: `wave_ingest.py` reports r(pred, measured h) < 0.5 on a
  full wave, in which case the Gd-pair labels must not be pooled with the
  f-in-core labels and the GP should be retrained on f-in-core rows only
  (`wave_gp.py` already carries the RE one-hot for exactly this case).

## 6. What never goes in git

POTCAR files, `.mp_api_key`, `runs-pool/`, `runs-light/`, VASP outputs. The
pool, wave and label CSVs are small and are the scientific record; commit
those.
