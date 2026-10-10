#!/usr/bin/env python3
"""Geometry-only descriptors for the GP: everything here is computable from a
structure BEFORE any DFT (so from a MACE-relaxed candidate as well as from a
finished run), and it is the same function for training rows and pool rows.

Descriptors (per structure, RE-site averaged):
  N_TM_nn          TM atoms in the RE first shell (periodic images counted)
  d_RE_TM_nn_mean  mean RE-TM first-shell distance (A)
  d_RE_TM_min      shortest RE-TM distance (A)
  f_Fe             Fe fraction of the TM sublattice
  f_Co             Co fraction of the TM sublattice
  d_count          mean 3d count of the TM sublattice (Mn 5 ... Ni 8)
  TM_per_RE        TM atoms per RE atom
  x_dil            fraction of atoms that are neither TM nor RE
  tm_density       TM atoms per 100 A^3  (the Ms lever)
  vol_per_atom     A^3 / atom
  f_early          early-TM fraction of all non-RE, non-TM atoms (Ti V Zr Nb Hf Ta Sc W Mo Cr)
  n_metalloid_shell  metalloid / p-block atoms in the RE first shell (B C N Al Si P Ga Ge Be)
  n_H_shell, n_N_shell, n_C_shell  interstitial light atoms in the RE first shell
  re_el            which RE (Gd, Nd, Sm, ...) - the GP carries it as a one-hot
The first shell is everything within 1.18 x the shortest RE-TM distance, as in
exchange_trends.py.
"""
import numpy as np
from pymatgen.core import Structure

TM = {"Fe", "Co", "Mn", "Ni"}
RE_ALL = {"Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Nd", "Sm", "Pr", "Ce", "La", "Y", "Lu", "Sc"}
RE_MAG = {"Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Nd", "Sm", "Pr"}      # the one that carries 4f / is substituted
EARLY = {"Ti", "V", "Zr", "Nb", "Hf", "Ta", "W", "Mo", "Cr"}
METAL = {"B", "C", "N", "Al", "Si", "P", "Ga", "Ge", "Be", "Sn", "Sb"}
D_COUNT = {"Mn": 5, "Fe": 6, "Co": 7, "Ni": 8}
FEATURES = ["N_TM_nn", "d_RE_TM_nn_mean", "d_RE_TM_min", "f_Fe", "f_Co", "d_count", "TM_per_RE", "x_dil",
            "tm_density", "vol_per_atom", "f_early", "n_metalloid_shell", "n_H_shell", "n_N_shell", "n_C_shell"]


def features(struct: Structure, re_el=None):
    els = [sp.symbol for sp in struct.species]
    if re_el is None:
        cand = [e for e in els if e in RE_MAG]
        re_el = max(set(cand), key=cand.count) if cand else None
    re_idx = [i for i, e in enumerate(els) if e == re_el]
    tm_idx = [i for i, e in enumerate(els) if e in TM]
    if not re_idx or not tm_idx:
        return None
    tm_set = set(tm_idx)
    nb_all = {i: struct.get_neighbors(struct[i], 4.4) for i in re_idx}
    dmin = min(nb.nn_distance for i in re_idx for nb in nb_all[i] if nb.index in tm_set)
    rcut = 1.18 * dmin
    n_nn, d_nn, n_met, n_h, n_n, n_c = [], [], [], 0, 0, 0
    for i in re_idx:
        shell = [nb for nb in nb_all[i] if nb.nn_distance <= rcut]
        tm_sh = [nb for nb in shell if nb.index in tm_set]
        n_nn.append(len(tm_sh)); d_nn += [nb.nn_distance for nb in tm_sh]
        n_met.append(sum(1 for nb in shell if els[nb.index] in METAL))
        n_h += sum(1 for nb in shell if els[nb.index] == "H")
        n_n += sum(1 for nb in shell if els[nb.index] == "N")
        n_c += sum(1 for nb in shell if els[nb.index] == "C")
    tm_els = [els[j] for j in tm_idx]
    other = [e for e in els if e not in TM and e not in RE_ALL]
    nre = len(re_idx)
    return {
        "re_el": re_el, "n_RE": nre, "n_TM": len(tm_idx), "natoms": len(els),
        "N_TM_nn": float(np.mean(n_nn)), "d_RE_TM_nn_mean": float(np.mean(d_nn)), "d_RE_TM_min": float(dmin),
        "f_Fe": tm_els.count("Fe") / len(tm_els), "f_Co": tm_els.count("Co") / len(tm_els),
        "d_count": float(np.mean([D_COUNT[e] for e in tm_els])),
        "TM_per_RE": len(tm_idx) / nre, "x_dil": 1 - (len(tm_idx) + nre) / len(els),
        "tm_density": 100 * len(tm_idx) / struct.volume, "vol_per_atom": struct.volume / len(els),
        "f_early": (sum(1 for e in other if e in EARLY) / len(other)) if other else 0.0,
        "n_metalloid_shell": float(np.mean(n_met)), "n_H_shell": n_h / nre, "n_N_shell": n_n / nre, "n_C_shell": n_c / nre,
    }


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(p, features(Structure.from_file(p)))
