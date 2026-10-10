#!/usr/bin/env python3
"""Light-RE (Nd, Sm) VASP inputs for the hull survivors of light_re_hull.py.

One run per compound, not an fm/ferri pair: Nd_3 / Sm_3 are f-in-core, so there
is no 4f spin to flip. What the run measures is
  * the relaxed cell (ISIF=3; the Nd/Sm ion is 5-8 % larger than Gd and MACE
    already predicts +2-5 % volume, so positions-only would leave 4-7 GPa in),
  * the Fe/Co sublattice moments -> magnetisation with the free-ion light-RE
    moment added parallel (J = L - S),
  * h, the TM-tied RE s+p+d polarisation -> RE-TM gap via |dE| = 1574 h meV
    (apply_5d_method.py calibration on 180 Gd pairs).
Starting geometry is the MACE-MP-0 relaxed cell (runs-light/<host>/<RE>/
CONTCAR_mace); the campaign ENCUT (520 eV) already exceeds 1.3 x ENMAX of
every POTCAR here, so Pulay stress is under control without a change.
No LDAU: the only element that carried U was Gd, and Gd is gone.

Layout:  runs/light/<RE>/<polytype>/<Compound>_lre/relax/
Manifest: batch/light_re_runs.txt (runs-relative, one dir per line) for
          MANIFEST=... ./submit_batch.sh on Perlmutter.

Usage
  python3 light_re_series.py --dry-run
  VASP_PP_PATH=/Users/g5q/Documents/Codes/VASP/potpaw_PBE.64 python3 light_re_series.py
"""
import argparse
import json
import os
import re

from pymatgen.core import Structure
from pymatgen.io.vasp import Kpoints, Poscar

import make_inputs as MI
import build_campaign as BC
from light_re_hull import HOSTS

HERE = os.path.dirname(os.path.abspath(__file__))
# hull survivors (Nd within ~12 meV/atom of the MACE/MP hull); Sm twins ride along
SURVIVORS = ["Fe5GdSi_nat", "Al2Fe10Gd_sub", "Fe5GdV_nat", "Co9Fe5Gd4_sub", "Co2Fe12GdY3_sub",
             "CoFe13GdY3_sub", "Fe9GdLuZr_sub", "CoFe6GdY_sub", "Fe10GdY_sub", "Fe14GdY3_sub"]
LIGHT = ["Nd", "Sm"]
TM = {"Fe", "Co"}
KPPA = 8000


def name_for(host, re_):
    base = re.sub(r"_(nat|sub)$", "", host).replace("Gd", re_)
    return base + "_lre"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    A = ap.parse_args()
    pp = os.environ.get("VASP_PP_PATH")
    made, missing_pp = [], False
    for host in SURVIVORS:
        polytype = HOSTS[host].split("/")[2]
        for re_ in LIGHT:
            src = os.path.join(HERE, "runs-light", host, re_, "CONTCAR_mace")
            s = Structure.from_file(src)
            s = s.get_sorted_structure()
            name = name_for(host, re_)
            d = os.path.join(HERE, "runs", "light", re_, polytype, name, "relax")
            p = Poscar(s)
            species = list(zip(p.site_symbols, p.natoms))
            mag = [2.5 if el in TM else 0.0 for el, _ in species]
            inc = {
                "SYSTEM": f"{name} relax light-RE f-in-core",
                "PREC": "Accurate", "ENCUT": 520, "EDIFF": 1e-6, "NELM": 200, "ALGO": "Normal",
                "ISMEAR": 1, "SIGMA": 0.2, "ISPIN": 2,
                "MAGMOM": "  ".join(f"{n}*{m:.2f}" for (_, n), m in zip(species, mag)),
                "LORBIT": 11, "LASPH": True, "LMAXMIX": 4,
                "LREAL": False, "LWAVE": False, "LCHARG": False, "KPAR": 4,
                "IBRION": 2, "ISIF": 3, "NSW": 80, "EDIFFG": -0.02, "POTIM": 0.3,
            }
            pot = {el: BC.POTCAR_MAP.get(el, el) for el, _ in species}
            print(f"{name:<22} {polytype:<12} {len(s):3d} atoms  V={s.volume:7.1f}  "
                  f"POTCAR {' '.join(pot[el] for el,_ in species)}")
            if A.dry_run:
                continue
            os.makedirs(d, exist_ok=True)
            Poscar(s).write_file(os.path.join(d, "POSCAR"))
            Kpoints.automatic_density(s, KPPA).write_file(os.path.join(d, "KPOINTS"))
            MI.write_incar(os.path.join(d, "INCAR"), inc)
            if not MI.assemble_potcar(species, pot, d):
                missing_pp = True
            json.dump({"name": name, "parent_host": host, "parent_run": HOSTS[host], "re": re_,
                       "re_potcar": pot[re_], "polytype": polytype, "mode": "relax_isif3_f_in_core",
                       "start": "MACE-MP-0 medium relaxed cell", "purpose": "light-RE Ms + h (5d method)"},
                      open(os.path.join(d, "..", "meta.json"), "w"), indent=1)
            made.append(os.path.relpath(d, HERE))
    if A.dry_run:
        return
    os.makedirs(os.path.join(HERE, "batch"), exist_ok=True)
    with open(os.path.join(HERE, "batch", "light_re_runs.txt"), "w") as f:
        f.write("\n".join(made) + "\n")
    print(f"\n{len(made)} run dirs written; manifest batch/light_re_runs.txt")
    if missing_pp:
        print("WARNING: POTCAR not assembled (set VASP_PP_PATH); POTCAR.spec written instead")


if __name__ == "__main__":
    main()
