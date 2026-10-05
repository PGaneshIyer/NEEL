# RE–TM intersublattice exchange workflow (VASP, PBE+U, Perlmutter)

Computes E(ferrimagnetic) − E(ferromagnetic) for the RE-vs-Fe sublattice
orientation: two collinear spin-polarized PBE+U calculations per compound,
identical in everything except the sign of the initial RE moments.

  dE = E(ferri) − E(fm) < 0  →  ferrimagnetic ground state (the heavy-RE default)
  dE > 0                      →  genuine FM RE–TM coupling (the interesting case)

Initialized for **GdAlFe4** and **GdGaFe4** (GNoME Cmmm cells from `../structures/`);
adding a compound = one entry in `compounds.json` + a CIF.

## Layout

    compounds.json     compound registry: structure path, U values (+ literature ref),
                       polytype label, initial moments, ENCUT/kppa, INCAR overrides
    make_inputs.py     writes runs/<arity>/<HREE>/<polytype>/<compound>/{fm,ferri}/
                       with INCAR,POSCAR,KPOINTS,POTCAR (requires pymatgen)
    submit_batch.sh    PREFERRED: one SLURM job array per HREE covering all pending
                       runs (manifests + logs under batch/); DRY=1 to preview,
                       optional args restrict to specific HREE groups
    submit_all.sh      alternative: one sbatch per run directory
    templates/         Perlmutter GPU/CPU job scripts + the array template
    analyze.py         stdlib-only: energies, site moments, dE per RE, and a check
                       that each run KEPT its intended spin configuration

## Steps (on Perlmutter)

    # 1. inputs (pymatgen: module load python; pip install --user pymatgen)
    export VASP_PP_PATH=/path/to/potpaw_PBE.64     # your licensed PAW set
    python3 make_inputs.py

    # NOTE: runs/ for GdAlFe4 + GdGaFe4 were already generated locally with
    # complete POTCARs (potpaw_PBE.64, from ~/Documents/Codes/VASP) - rsync the
    # workflow/ directory to Perlmutter and skip straight to step 2.

    # 2. submit, grouped by HREE. Two modes:
    DRY=1 ./submit_batch.sh                              # preview (array mode)
    NERSC_ACCOUNT=mXXXX ./submit_batch.sh                # job array per HREE
    NERSC_ACCOUNT=mXXXX PACK_NODES=auto ./submit_batch.sh    # packed, auto-sized
    NERSC_ACCOUNT=mXXXX PACK_NODES=auto ./submit_batch.sh Gd # one group only
    # (per-run alternative: NERSC_ACCOUNT=mXXXX ./submit_all.sh gpu)

## array vs packed

Both run one calculation per node; they differ in how the scheduler sees them.

- **array** (default): each run is its own 1-node job. They are genuinely parallel,
  but NERSC caps how many jobs one user may have running, so a 158-task array
  trickles through in waves rather than landing at once.
- **packed** (`PACK_NODES=N`): one N-node allocation per HREE group, with N runs
  executing concurrently - one per node - fed by a `flock`-guarded shared work
  queue. The scheduler sees a single job, so the whole group starts together and
  nothing waits behind a job-count cap. Because the queue is dynamic, a node that
  finishes a 6-atom cell immediately pulls the next run instead of idling, which
  matters here: cells range from 6 to 68 atoms (median 19).

Either way a run with an existing OUTCAR is skipped, so resubmitting after a
timeout or preemption resumes cleanly.

**Walltime** is `auto` by default and means different things in the two modes.
In array mode the clock is PER TASK, so one run's allowance suffices
(`PER_RUN_MIN x 4`, default 2 h). In packed mode a single job must cover every
wave through the work queue, so the limit scales with the group:

    waves   = ceil(runs / nodes)
    walltime = waves x PER_RUN_MIN x 1.3   (clamped to 1 h .. MAX_WALL_MIN, 12 h)

e.g. Tm's 158 runs on 27 nodes = 6 waves -> 03:54:00; the same group on 5 nodes
would be 32 waves and hit the 12 h cap. Set `PER_RUN_MIN` once the pilot gives
real timings, or pass an explicit `WALLTIME=HH:MM:SS` to override. A packed job
that hits its limit is not a disaster - finished runs have OUTCARs and the next
`submit_batch.sh` picks up only what is left.

**Queue wait dominates everything.** From Iris (Perlmutter GPU, regular QOS,
average wait in hours, https://iris.nersc.gov/utils/queueWaitTimes):

    nodes:  1    2-3   4-7   8-15  16-31  32-63  64-127  128-255
    wait:  50.7  34.9  31.1  35.4  27.3   18.7   45.4    63.9

NERSC prioritizes capability jobs, so a 1-node job waits ~50 h while a 32-63 node
job waits ~19 h. Array mode submits N one-node jobs - the slowest band - which is
why `PACK_NODES=auto` now targets 32-63 nodes (`MIN_NODES`/`MAX_NODES`). Two idle
nodes on the tail cost far less than 30 extra hours of queueing.

Use `./submit_batch.sh all` to pool every HREE into ONE job: one queue wait
instead of six. `QOS=debug` (<= 8 nodes, 30 min, ~0.5 h wait) is the cheap way to
measure real per-run timings before sizing the production job.

**`PACK_NODES=optimal` sizes from LIVE queue data.** `pick_nodes.py` queries Iris
(https://iris.nersc.gov/graphql_web - public, no login, same source as the NERSC
queue-wait page), builds a wait model over node bands, and picks the node count
minimising `wait(nodes) + waves x per-run-time` subject to the QOS walltime cap.
It sets WALLTIME to match.

    python3 pick_nodes.py --runs 706 --per-run-min 30      # inspect the trade-off
    NERSC_ACCOUNT=mXXXX PACK_NODES=optimal ./submit_batch.sh all

Every submission prints what it chose and where the numbers came from, so a silent
fallback is visible:

    == all: submitting  (690 runs pending)
       mode      : packed   nodes=59  waves=12  walltime=07:49:00  qos=regular
       sizing    : LIVE Iris queue data  (node band 32+, reached iris.nersc.gov)
       predicted : ~22.1 h queued + 6.0 h running = 28.1 h to results
       assumed   : PER_RUN_MIN=30 min/run   manifest: batch/all.manifest (longest cells first)

If the login node cannot reach Iris the sizing line reads
`!! COULD NOT REACH iris.nersc.gov - used built-in snapshot` instead.

Note the statistics are thin per (band, walltime) cell - often a single job - so
cells with fewer than `--min-cell-jobs` (default 100) are ignored in favour of the
band average, which has hundreds to thousands of jobs. Without that guard the
optimiser "discovers" a 3.8 h wait that was one lucky job. `--offline` uses a
built-in snapshot; the script also falls back to it automatically if Iris is
unreachable, and `PACK_NODES=auto` remains the no-network static heuristic.

**Sizing a packed job.** A packed job is charged `nodes x total wall time`, so it
is NOT free to ask for one node per run: every node would finish its single cell
and then idle until the slowest one completes. For this campaign's size
distribution (VASP cost ~ N^3, cells 6-68 atoms) greedy packing gives:

    nodes=706 (one per run):  billed 22.0x the useful work, 95% idle
    nodes=100:                billed  3.1x,                 68% idle
    nodes=50:                 billed  1.6x,                 36% idle
    nodes=25:                 billed  1.0x,                  0% idle

and the wall time never drops below the single longest run, so nodes past ~25 buy
nothing. `PACK_NODES=auto` sizes each group to ~`RUNS_PER_NODE` (default 6) runs
per node, capped at `MAX_NODES` (default 40): Tm 158 runs -> 27 nodes, Gd 50 -> 9.

Array mode has no idle tail at all - each 1-node job is billed only for its own
duration - so it is the cheaper option whenever the job-count cap is tolerable.
Packed mode buys predictable start-together scheduling, not efficiency.

Cost note: a 19-atom static on 4 A100s is a poor fit for a full node. For a
production sweep consider `-q shared` with `--gpus-per-task=1` (roughly a quarter
of the charge) in the array template, keeping full nodes for the largest cells.

    # 3. after jobs finish
    python3 analyze.py

If `VASP_PP_PATH` is unset at generation time, each run dir gets a `POTCAR.spec`
(ordered potential symbols) instead of a POTCAR; assemble with
`cat $VASP_PP_PATH/$(cat POTCAR.spec | xargs -I{} echo {}/POTCAR) > POTCAR`-style
concatenation, respecting the order in the file.

## The Gd campaign (355 compounds / 710 calculations)

`build_campaign.py` turns the master candidate list into a run-ready registry:

- **native (26)** - the structure already contains Gd; run as-is.
- **Gd surrogates (328)** - a Tb/Dy/Ho/Er/Tm candidate with every heavy-RE site
  replaced by Gd, because Tb-Tm ship as f-in-core `*_3` POTCARs whose 4f cannot
  flip. Surrogates are deduplicated on (substituted formula, space group), so 724
  parent compounds collapse into 328 calculations; the coupling sign transfers
  back to each parent by de Gennes scaling, (g_J - 1)J.
- **validation (1)** - GdFe2 C15, an experimental ferrimagnet (in compounds.json).

Each compound directory carries a `meta.json` with its provenance (parents, parent
HREE, source databases, hull distance); `campaign_manifest.csv` in the repo root is
the same mapping as a table. Rebuild with:

    export VASP_PP_PATH=/path/to/potpaw_PBE.64   # POTCAR symbols are validated against it
    python3 build_campaign.py --max-sites 80
    python3 make_inputs.py --registry compounds_campaign.json
    python3 make_inputs.py --registry compounds.json --only GdFe2_validation

## Two-stage constrained protocol (stage A -> stage B)

The single-stage constrained rerun failed: NUPDOWN fixes the total moment, so its
energy carries a constraint penalty, and where the target was wrong that penalty
reached a median of 194 meV/atom - the constraint manufactured states that were
not ground states at all.

The two-stage version separates the two jobs:

    python3 rerun_constrained.py --stage a      # short CONSTRAINED run, writes WAVECAR/CHGCAR
    # ... submit, wait ...
    python3 rerun_constrained.py --stage b      # FREE run restarting from A; its energy is used

Stage A's only product is a converged density sitting in the intended magnetic
basin (NELM 60, EDIFF 1e-5, LWAVE/LCHARG on - they were .FALSE. in the whole
first campaign, which is why every WAVECAR on disk is 0 bytes). Stage B releases
the constraint and restarts from it, so the energy that gets compared is
unconstrained and the penalty problem disappears.

It also turns the FM question into a test: **a genuine magnetic state survives
release**. If stage B slides back to the other configuration, that state was
never a local minimum.

### Moments come from this campaign's own data

The first pass assumed 2.2 mu_B/Fe everywhere. Measured on our freely-relaxed runs:

    Fe, no P   n=340   mean 1.69 mu_B      <- high-spin branch
    Co, no P   n= 82   mean 1.09 mu_B
    Fe, with P n= 64   mean 0.25 mu_B      <- low-spin branch

The distribution is sharply bimodal with a sparse middle, and the split is almost
entirely phosphorus: 73% of low-spin runs contain P, 0% of high-spin runs do.
Fe-P hybridisation broadens the 3d band and quenches the moment. So P-containing
compounds now get the low-spin reference for both MAGMOM and NUPDOWN - e.g.
Fe12GdP7Sc ferri goes from NUPDOWN 19 (nonsense) to 4, with Fe seeded at 0.25
rather than 2.5.

NUPDOWN targets are taken from a converged FREE run where one exists, never from
a constrained one - using a constrained moment as the reference would simply
re-impose the previous wrong target.

## Magnetisation from the analysis

`analyze.py` now reports the moment alongside the energy difference, so each
finished pair yields a magnet figure of merit rather than just a coupling sign:

- `net_moment_uB` / `mu0Ms_T` - the net cell moment and saturation magnetisation
  **evaluated in the winning configuration**, not whichever config has the larger
  moment. u0Ms = 11.654 x |m| / V, with m in mu_B and V in A^3.
- `total_moment_uB`, `tm_moment_total`, `re_moment_total`, `volume_A3` per run.
- `predicted_by_RE` - the parent compounds' magnetisation, obtained by swapping
  Gd's COMPUTED contribution for the parent RE's free-ion g_J*J while keeping the
  sign the calculation found.
- `results_summary.csv` - one flat row per compound, plus a ranked "highest
  magnetisation" table printed at the end.

The moment comes from the `mag=` field of the final OSZICAR line. That is the
true net moment here because the Gd POTCAR keeps 4f in the valence - unlike the
f-in-core potentials the big databases use, where the reported magnetisation
EXCLUDES the 4f and has to be corrected by hand.

The parent prediction is where the campaign pays off twice, and it cuts both
ways depending on the coupling:

    ferrimagnetic host:  Gd 7 uB -> Dy 10 uB antiparallel  =>  Ms DROPS
                         (1.81 T -> 1.04 T in the test case - the "Dy problem")
    FM-coupled host:     Gd 7 uB -> Dy 10 uB parallel      =>  Ms RISES
                         (1.94 T -> 2.33 T)

Caveat: the volume is held fixed at the Gd cell's, so lanthanide contraction is
ignored - worth a few percent on Ms, and it always acts to increase Ms slightly
for the heavier RE.

## Step 4 - anisotropy: how much Gd must be replaced

The campaign settles EXCHANGE. It says nothing about anisotropy, because Gd is a
4f7 S-state ion (L = 0) and contributes none by construction. A magnet needs a
non-spherical 4f ion on that site, so any dE > 0 hit needs a second question
answered: what fraction x of the Gd must become Tb/Dy/Ho (or Er/Tm)?

    python3 anisotropy.py --scan --a20 +300 --de 277 --m-fe 14.06 \
                          --volume 90.1 --n-re 1 --temp 450

It solves for the smallest x meeting Coey's hardness criterion
kappa = sqrt(K1 / mu0 Ms^2) >= 1, using:

- the exchange field taken from the campaign's own |dE| per Gd, rescaled to the
  substituent by the spin projection (g_J - 1)J;
- K1 from the second-order crystal field and Stevens alpha_J, with the
  Callen-Callen l=2 temperature law (K1 ~ m_RE^3);
- Ms(x) from the TM sublattice moment and the RE moments, signed by the coupling.

Two things the tool enforces that are easy to get wrong by hand. **Only one
Stevens sign family is easy-axis for a given A20** - Tb/Dy/Ho have alpha_J < 0,
Er/Tm have alpha_J > 0, so one family gives uniaxial anisotropy and the other
gives planar; mixing them cancels. And **K1 < 0 is not a magnet at any |K1|**,
so planar solutions are rejected rather than reported as a smaller x.

The one input the campaign does NOT produce is `A20`, the second-order
crystal-field parameter at the RE site (K/a0^2). Get it either from the DFT
electrostatic potential and valence charge asymmetry around that site, or from
the 4f charge-density response in the Gd calculation (Novak's method). Sign
convention matters: check it against a known compound before trusting x.

Why keep any Gd at all: Gd carries the largest de Gennes factor of the series
(15.75 vs Tb 10.5, Dy 7.08), so it contributes the most to Tc. The optimum is
the MINIMUM x that clears the anisotropy bar, with Gd holding the rest.

## Prototype identification - AFLOW first, heuristic fallback

`build_campaign.py` labels each structure with `polytype()`, which now consults
the AFLOW prototype library first (via pymatgen's `AflowPrototypeMatcher`) and
falls back to the stoichiometry heuristic. The AFLOW identity is recorded in each
registry entry as `aflow_prototype` whether or not it is used for the label.

**Measured coverage on this campaign: AFLOW matched 2 of 352 structures (1%)** -
both binary Laves phases, `A2B_cF24_227_d_a` / Strukturbericht C15. It matched
**zero** of the 141 ternary, 157 quaternary and 40 quinary candidates, because
the library pymatgen bundles is dominated by unary and binary prototypes. So
AFLOW is exact where it speaks and silent almost everywhere here; the heuristic
still does the real work.

`SB_ALIAS` maps Strukturbericht codes onto the names this program uses, so an
AFLOW match and the heuristic yield the SAME directory name for the same lattice
(C15 -> `Laves-C15`), and switching the precedence causes no directory churn.

To get real ternary coverage, install the `aflow` binary and use AFLOW-XtalFinder
against the full 1,783-prototype library - that is the maintained tool this
heuristic is approximating, and it also enumerates symmetry-equivalent decorations
and spin configurations. See `papers/Hicks2021_AFLOW-XtalFinder.pdf`.

The heuristic itself was corrected twice while building this: it originally
tested TM/RE instead of (TM+X)/RE, which missed GdFe10Si2 as a 1-12 and wrongly
accepted GdHfFe12P7, and it had no interstitial tests (2-17-3, 1-12-N) or 1-9-4.
All 14 known magnet stoichiometries now classify correctly - but that history is
the argument for moving to XtalFinder rather than extending the heuristic further.

## Expanding the pool - prototype decoration and Wyckoff generation

    python3 generate_candidates.py decorate --dry-run       # see the yield
    python3 generate_candidates.py decorate                 # write CIFs + registry
    python3 generate_candidates.py wyckoff --formula Gd1Fe6Sn6 --spacegroups 191

**decorate** takes each named magnet prototype already in the campaign and
substitutes the X site through a magnet-relevant palette (Al, Si, Ga, Ge, B, C,
N, P, Sn, Sb, Ti, V, Cr, Zr, Nb, Mo, W, Hf, Ta, Cu, Zn), plus an Fe<->Co swap.
It currently yields **146 new candidates** across CaCu5-RT4X, ThMn12-stabilized,
Th2Zn17-interstitial, Nd2Fe14B, LaCo9Si4 and RT3. This is the reasonable one to
run: chemically conservative, cheap, and it reproduces the real 1-12 magnet
chemistry (GdFe11Ti-type variants) rather than inventing frameworks.

**wyckoff** places a stoichiometry on the symmetry orbits of a target space
group (needs `pyxtal`). Genuinely new frameworks, but a low hit rate - these
come out unrelaxed and mostly unstable.

Neither generator produces a hull distance, which is the whole point of the
0.2 eV/atom criterion. **Do not send generated structures straight to DFT.**
MLIP-relax (MACE/CHGNet), compute E_hull against MP + Alexandria, keep
<= 0.2 eV/atom, and only then `make_inputs.py --registry compounds_generated.json`.
For 146 decorations that filter costs minutes; for a Wyckoff sweep of 10^4-10^5
it is the only thing that makes DFT affordable at all.

Note: the prototype classifier in `build_campaign.py` was corrected after the
campaign tree was built (it tested TM/RE instead of (TM+X)/RE, so it missed
GdFe10Si2 as a 1-12 and wrongly accepted GdHfFe12P7). `generate_candidates.py`
recomputes labels from structures, so the live run tree is untouched; rebuilding
the campaign would relabel ~35 directory names and orphan completed OUTCARs, so
defer that until the current jobs finish.

## Anisotropy-bearing and experimental datasets

    python3 external_data.py --list
    python3 external_data.py --fetch novamag --dest ../external

The five big DFT databases carry composition, stability and a moment - not MAE,
exchange or Tc. A few smaller sets do, and are worth more per entry:

| source | role in this campaign |
|---|---|
| **Novamag** | the only open systematic MAE/K1 + exchange + Tc set for RE-lean magnets. Train and validate the anisotropy surrogate; calibrate A20. CC-BY-4.0, auto-fetched from Zenodo (160 MB). |
| **MAGNDATA** | ~2000 EXPERIMENTAL magnetic structures. Ground truth for the fm/ferri coupling sign - every RE-TM entry tests the protocol far more strongly than GdFe2 alone. |
| **C2DB** | systematically computed MAE and exchange in 2D. Wrong dimensionality, right purpose: benchmark an MAE surrogate before trusting it on bulk kagome. |
| **Sanvito Heusler (~236k)** | Tc-model training data and a template for funnel reporting. Mostly 50% TM, so they fail our >=60% criterion as candidates. |
| **Nelson-Sanvito Tc (~2500)** | composition-only Tc regressor, so Tc is screened before exchange constants are computed. |
| **NIMS MatNavi / MDR** | deepest experimental Nd-Fe-B and 1-12 record; best validation targets for the 1-12 track. Registration required. |

MPDS / Pauling File and Springer Materials have the deepest experimental
coverage but are **not open** - do not plan around them.

## Run-tree organization

    runs/<arity>/<HREE>/<polytype>/<compound>/<fm|ferri>/
    e.g. runs/ternary/Gd/CaCu5/GdAlFe4/fm/

- arity is derived from the structure (ternary/quaternary/...).
- HREE is `hree_group`: for a Gd surrogate that is the PARENT compound's rare earth
  (the element the run is answering for), not the Gd actually in the cell. Native
  and validation compounds fall back to `re_element` = Gd.
- polytype is set per compound in `compounds.json`: one of the magnet prototype
  labels being decorated (CaCu5, ThMn12, Th2Zn17, Th2Ni17, Nd2Fe14B, Laves-C14,
  Laves-C15, Heusler, kagome-166, ...) or `new-<label>` for a structure that
  matches no known prototype. GdAlFe4/GdGaFe4 are CaCu5: ordered RFe4X
  decorations of the SmCo5 lattice. Unlabeled compounds land in `unassigned`.
- `submit_all.sh` and `analyze.py` discover runs at any depth, so older flat
  trees keep working.

## Physics / protocol notes

- **U values live in `compounds.json`, per compound, with the literature reference
  in the entry.** Gd: LDAUTYPE=2 with U=6.7, J=0.7 eV on 4f (Ueff = 6 eV, the
  standard Harmon–Antropov-derived choice reused across VASP Gd studies).
  No U on Fe (metallic intermetallic). LASPH=.TRUE. and LMAXMIX=6 are set —
  both matter for f-electron +U runs.
- **Static by default** (`"mode": "static"`): both spin configs on the same fixed
  (already-relaxed GNoME) geometry, so dE isolates the exchange. Set
  `"mode": "relax"` per compound for full ISIF=3 relaxations; then relax fm
  first and reuse its CONTCAR for ferri if you want geometry held in common.
- **Configuration integrity, not just convergence:** the ferri run can drift to
  the FM minimum (or vice versa) during SCF. `analyze.py` compares converged
  RE-vs-TM moment signs to the intended configuration and flags `FLIPPED` runs —
  a flipped run's energy belongs to the other column, so the pair must be redone
  (stronger MAGMOM, NUPDOWN fixed to the target total moment, or VASP's
  constrained-moment machinery / occupation-matrix control).
- **Non-Gd heavy RE (Tb–Tm):** the registry defaults map them to `*_3`
  f-in-core POTCARs, in which the 4f cannot flip — a "ferri" run would be
  meaningless. The intended protocol is the Gd-surrogate: put Gd on the RE site,
  compute dE there, and transfer the sign/magnitude across the series by
  de Gennes scaling, (g_J − 1)J. Explicit-4f Tb–Tm PBE+U is possible but needs
  occupation-matrix control and is not attempted by this workflow.
- **Validation:** `GdFe2_validation` entry (disabled) — a known C15 ferrimagnet.
  Enable it (with a Laves CIF) the first time you run the protocol: it must come
  out ferrimagnetic by a clear margin, or something is wrong.
- Mean-field context for the result: |dE| per RE ≈ 2 z J_RE-TM S_RE·S_TM sets the
  RE-sublattice exchange scale; tens of meV/RE is typical for RE-Fe intermetallics.

## Cost

6-atom cells, ~500-1000 k-points folded: minutes per run on one GPU node
(KPAR=4). The 1-hour walltime in the template is generous.
