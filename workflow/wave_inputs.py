#!/usr/bin/env python3
"""Turn a GP wave (analysis/pool/wave_<k>.csv) into VASP run directories.

One f-in-core relaxation per candidate, the same recipe as light_re_series.py:
ISIF=3 from the MACE-relaxed cell, ENCUT 520, no LDAU (no 4f in the valence),
Fe/Co initialised at 2.5 muB, LORBIT=11 so h can be read from the OUTCAR.
Layout   runs/wave<k>/<RE>/<cid>_<formula>/relax/
Manifest batch/wave_<k>_runs.txt   (runs-relative, for MANIFEST=... submit_batch.sh)

Usage:  VASP_PP_PATH=/path/potpaw_PBE.64 python3 wave_inputs.py --wave 1 [--dry-run]
"""
import argparse
import csv
import json
import os

from pymatgen.core import Structure
from pymatgen.io.vasp import Kpoints, Poscar

import make_inputs as MI
import build_campaign as BC

HERE = os.path.dirname(os.path.abspath(__file__))
TM = {"Fe", "Co", "Mn", "Ni"}
KPPA = 8000


def write_relax_run(s, name, d, meta, dry=False):
    """Shared single-run writer (also usable by light_re_series)."""
    s = s.get_sorted_structure()
    p = Poscar(s)
    species = list(zip(p.site_symbols, p.natoms))
    mag = [2.5 if el in TM else 0.0 for el, _ in species]
    inc = {
        "SYSTEM": f"{name} relax light-RE f-in-core", "PREC": "Accurate", "ENCUT": 520, "EDIFF": 1e-6, "NELM": 200,
        "ALGO": "Normal", "ISMEAR": 1, "SIGMA": 0.2, "ISPIN": 2,
        "MAGMOM": "  ".join(f"{n}*{m:.2f}" for (_, n), m in zip(species, mag)),
        "LORBIT": 11, "LASPH": True, "LMAXMIX": 4, "LREAL": False, "LWAVE": False, "LCHARG": False, "KPAR": 4,
        "IBRION": 2, "ISIF": 3, "NSW": 80, "EDIFFG": -0.02, "POTIM": 0.3,
    }
    pot = {el: BC.POTCAR_MAP.get(el, el) for el, _ in species}
    if dry:
        return pot, True
    os.makedirs(d, exist_ok=True)
    p.write_file(os.path.join(d, "POSCAR"))
    Kpoints.automatic_density(s, KPPA).write_file(os.path.join(d, "KPOINTS"))
    MI.write_incar(os.path.join(d, "INCAR"), inc)
    ok = MI.assemble_potcar(species, pot, d)
    json.dump(meta, open(os.path.join(d, "..", "meta.json"), "w"), indent=1)
    return pot, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    A = ap.parse_args()
    wave = list(csv.DictReader(open(os.path.join(HERE, "analysis", "pool", f"wave_{A.wave}.csv"))))
    made, missing_pp = [], False
    for r in wave:
        s = Structure.from_file(os.path.join(HERE, r["poscar"]))
        name = f"{r['cid']}_{r['formula'].replace('(', '').replace(')', '')}"
        d = os.path.join(HERE, "runs", f"wave{A.wave}", r["re_el"], name, "relax")
        meta = {"cid": r["cid"], "wave": A.wave, "tag": r["tag"], "source": r["source"], "parent": r["parent"],
                "formula": r["formula"], "re_el": r["re_el"], "h_pred": r["h_pred"], "h_sd": r["h_sd"],
                "gap_pred_meV": r["gap_pred_meV"], "Ms_proj_T": r["Ms_proj_T"], "E_hull_meV": r["E_hull_meV"],
                "mode": "relax_isif3_f_in_core", "start": "MACE-MP-0 relaxed cell"}
        pot, ok = write_relax_run(s, name, d, meta, A.dry_run)
        missing_pp |= not ok
        print(f"{name:<34} {len(s):3d} atoms  POTCAR {' '.join(pot.values())}")
        made.append(os.path.relpath(d, HERE))
    if A.dry_run:
        return
    os.makedirs(os.path.join(HERE, "batch"), exist_ok=True)
    mf = os.path.join(HERE, "batch", f"wave_{A.wave}_runs.txt")
    open(mf, "w").write("\n".join(made) + "\n")
    print(f"\n{len(made)} run dirs; manifest {os.path.relpath(mf, HERE)}")
    if missing_pp:
        print("WARNING: POTCAR not assembled (set VASP_PP_PATH)")


if __name__ == "__main__":
    main()
