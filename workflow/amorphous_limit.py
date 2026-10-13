#!/usr/bin/env python3
"""Amorphous limit of synthesisability (Aykol, Dwaraknath, Sun, Persson 2018):
no crystalline phase above the energy of the amorphous phase at the same
composition can be made. Estimated with MACE-MP-0 by melt-quench:
  supercell of the relaxed cell (>= 96 atoms) -> Langevin MD at 3000 K (melt)
  -> linear quench to 300 K -> relax (positions + cell) -> E_amorphous/atom
  compared with the relaxed crystal E/atom from the same model.
Reports dE_am = E_am - E_cryst (meV/atom); a candidate is excluded if its DFT
hull distance exceeds dE_am. Writes analysis/light_re/amorphous_limit.csv.

MACE venv:  /Users/g5q/Documents/GitHub/siteseer/.venv/bin/python amorphous_limit.py runs/light/.../relax ...
            [--melt-ps 2 --quench-ps 4 --dt 2 --natoms 96]
"""
import argparse
import csv
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
import numpy as np
from ase.io import read
from ase import units
from ase.md.langevin import Langevin
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.filters import FrechetCellFilter
from ase.optimize import FIRE

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import light_re_hull as LH


def supercell(atoms, nmin):
    n = len(atoms); k = 1
    while n * k ** 3 < nmin:
        k += 1
    rep = [k, k, k]
    # prefer the smallest cell with >= nmin atoms (allow anisotropic)
    best, bestn = rep, n * k ** 3
    for a in range(1, k + 1):
        for b in range(1, k + 1):
            for c in range(1, k + 1):
                m = n * a * b * c
                if nmin <= m < bestn:
                    best, bestn = [a, b, c], m
    return atoms.repeat(best)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--melt-ps", type=float, default=2.0)
    ap.add_argument("--quench-ps", type=float, default=4.0)
    ap.add_argument("--dt", type=float, default=2.0, help="fs")
    ap.add_argument("--natoms", type=int, default=96)
    ap.add_argument("--tmelt", type=float, default=3000.0)
    A = ap.parse_args()
    calc = LH.make_calc()
    out = os.path.join(HERE, "analysis", "light_re", "amorphous_limit.csv")
    rows = {r["compound"]: r for r in csv.DictReader(open(out))} if os.path.isfile(out) else {}
    for rd in A.dirs:
        rd = rd.rstrip("/"); name = os.path.basename(os.path.dirname(rd))
        if name in rows:
            print(f"{name}: cached dE_am = {rows[name]['dE_am_meV']} meV/atom"); continue
        t0 = time.time()
        geom = os.path.join(rd, "CONTCAR") if os.path.getsize(os.path.join(rd, "CONTCAR")) > 0 else os.path.join(rd, "POSCAR")
        cryst = read(geom); cryst.calc = calc
        # crystal reference: MACE-relaxed energy of the same cell
        e_c, _, _ = LH.relax(cryst, calc, 0.05, 200)
        e_c /= len(cryst)
        a = supercell(cryst.copy(), A.natoms); a.calc = calc
        MaxwellBoltzmannDistribution(a, temperature_K=A.tmelt)
        dyn = Langevin(a, A.dt * units.fs, temperature_K=A.tmelt, friction=0.02)
        dyn.run(int(A.melt_ps * 1000 / A.dt))
        nq = int(A.quench_ps * 1000 / A.dt); steps = 20
        for i in range(steps):
            T = A.tmelt - (A.tmelt - 300.0) * (i + 1) / steps
            dyn.set_temperature(temperature_K=T)
            dyn.run(nq // steps)
        e_a, fmax, _ = LH.relax(a, calc, 0.05, 400)
        e_a /= len(a)
        de = 1000 * (e_a - e_c)
        rows[name] = {"compound": name, "natoms_amorphous": len(a), "E_cryst_eV_atom": round(e_c, 4), "E_amorph_eV_atom": round(e_a, 4), "dE_am_meV": round(de, 1),
                      "melt_ps": A.melt_ps, "quench_ps": A.quench_ps}
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[name].keys())); w.writeheader(); w.writerows(rows.values())
        print(f"{name:<22} {len(a)} atoms  E_cryst {e_c:.4f}  E_am {e_a:.4f}  dE_am = {de:6.1f} meV/atom  ({time.time()-t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main()
