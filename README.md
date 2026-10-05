# NEEL — NERSC Engine for Exploring magnetic Lattices

Adaptive high-throughput search for ferromagnetic Fe/Co–heavy-rare-earth
intermetallics (MAGNITO program, target μ0Ms > 2 T), named for Louis Néel,
whose ferrimagnetism is exactly the competing state every candidate here is
tested against. Candidates are mined from public DFT
databases, then every one gets the same two-configuration VASP PBE+U test:
rare-earth moment parallel (fm) vs antiparallel (ferri) to the transition-metal
sublattice. The energy difference is the answer; the whole pipeline is here.

Status (Oct 2026): 353 compounds screened with a Gd surrogate for Tb–Tm;
**one credible ferromagnet survives every validity check — Co16Gd2Mn**
(Th2Zn17-type, Mn on the 6c dumbbell site; dE = +114.5 meV/Gd, μ0Ms = 1.95 T).
Direct explicit-4f calculations on the real Tb/Dy/Ho/Er/Tm compounds and a Mn
site/concentration series are in progress. `MAGNITO_Fe-HREE_screening.pptx`
tells the full story.

## Layout

| Path | What |
|---|---|
| `workflow/` | The VASP pipeline. Start with `workflow/README.md`. |
| `workflow/build_campaign.py` | Candidate list → compound registry (`compounds_campaign.json`); Gd substitution; prototype/polytype classification |
| `workflow/make_inputs.py` | Registry → `runs/<arity>/<HREE>/<polytype>/<compound>/{fm,ferri}/` VASP inputs |
| `workflow/submit_batch.sh`, `templates/` | Perlmutter GPU submission: 1-node array mode or packed multi-node mode; `pick_nodes.py` sizes jobs from live NERSC queue data |
| `workflow/rerun_constrained.py` | Two-stage NUPDOWN protocol (locked → released) for runs whose SCF left the intended magnetic state |
| `workflow/relax_survivor.py`, `lock_native_relax.py`, `mn_site_series.py`, `native_hree_series.py` | Geometry relaxation with locked moment; Tier-2 explicit-4f heavy-RE runs; Mn site-preference / concentration series |
| `workflow/analyze.py` | Stdlib-only analysis: dE, ground state, μ0Ms, validity flags, de Gennes projection to the parent RE → `results.json`, `results_summary.csv` |
| `workflow/sync_results.sh`, `push_new_runs.sh`, `fix_corrupted_incars.py` | NERSC ↔ local transfer (filtered, direction-safe) and recovery tooling |
| `structures/` | 1,259 CIFs by origin: `GNoME/`, `MP/`, `Alexandria/`, `Gd_substituted/`, `generated/` |
| `*.csv` | Screening tables; `all_candidates_master.csv` is the merged, deduplicated master (1,152 formulas with provenance) |
| `make_deck.js`, `assets/` | pptxgenjs source for the slide deck |
| `papers/README.md` | Annotated bibliography (PDFs not redistributed) |

## What is deliberately NOT in this repository

- **POTCAR files** — VASP PAW potentials are licensed. Every run directory keeps a
  `POTCAR.spec` listing the symbols (potpaw_PBE.64; explicit-4f `Gd`, `Tb`, …, never
  the f-in-core `_3` variants for the flippable RE). Set `VASP_PP_PATH` and
  `make_inputs.py` rebuilds them.
- **VASP outputs** (OUTCAR, CONTCAR, WAVECAR, …, ~1.5 GB) — the analysis products
  `results.json` / `results_summary.csv` are committed; raw outputs live on NERSC.
- Journal PDFs.

## Running it

```bash
export VASP_PP_PATH=/path/to/potpaw_PBE.64
cd workflow
python3 build_campaign.py            # registry from the candidate CSVs
python3 make_inputs.py               # run directories with POTCARs
./push_new_runs.sh runs/...          # explicit paths only - see the header comment
NERSC_ACCOUNT=mXXXX PACK_NODES=auto ./submit_batch.sh   # or MANIFEST=file for a subset
./sync_results.sh --fast             # analyse on NERSC, pull results.json
```

Hard-won rules are documented where they bite: completion is detected by VASP's
timing block, never by OUTCAR existence; NUPDOWN targets come from measured
moments, never textbook values, and never from a run already suspected of
drifting; custom manifests are timestamped because the array template reads them
live; pushes to NERSC are explicit-path only.

## Data sources and attribution

- GNoME (Merchant et al., Nature 2023) — structures and stability; data licensed
  CC BY-NC 4.0. GNoME publishes no magnetic ordering, only a single FM-initialised
  calculation; see "Original GNoME extraction" below.
- Materials Project (CC BY 4.0), Alexandria (CC BY 4.0), OQMD, AFLOW — cross-references
  and additional candidates (`multidb_fe_hree_ternary.csv`).
- VASP 6.4.3 (GPU) on NERSC Perlmutter; PBE+U with U = 6.7 / J = 0.7 eV on the RE 4f.

## Original GNoME extraction (2026-08-31)

621 on-hull structures with Fe fraction ≥ 0.50, ≥ 1 heavy RE (Gd–Tm), ≥ 3 elements,
no actinides (`gnome_fe_hree_candidates.csv`). Columns `ms_fm_T` / `ms_ferri_T` are
upper-bound / realistic saturation estimates (2.1 μB/Fe + Hund gJ·J per RE, parallel
vs antiparallel); `alex_*` columns cross-reference Alexandria (73/621 matched, 70 of
them 5d-antiparallel → ferrimagnets). Non-Gd RE potentials in those databases freeze
the 4f in core, so their reported moments exclude the 4f contribution — hence the
Gd-surrogate + de Gennes protocol used throughout this work.
