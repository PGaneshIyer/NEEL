#!/usr/bin/env python3
"""Kagome RE-TM prototypes for the candidate pool.

The one RE-containing kagome family with Fe/Co is RT6X6 (HfFe6Ge6 type, P6/mmm,
No. 191): kagome T layers at z = 1/4, 3/4, RE in the hexagonal channel with X
above/below, X also in the honeycomb layers. Known members: RFe6Sn6, RFe6Ge6
(R = Y, Gd-Lu), RMn6Sn6 (TbMn6Sn6), MgFe6Ge6, LiFe6Ge6. Light-RE members tend
to adopt disordered/superstructure variants; the ordered P6/mmm cell is the
right screening approximation and the hull filter says whether it holds.

Generated here, all with Gd as the heavy-RE placeholder (wave_pool substitutes
Gd -> Nd/Sm):
  RT6X6     T = Fe6, Co6, Fe5Co   X = Sn, Ge, Si, Ga, Al     (15 cells, 13 atoms)
  RT6X5     one channel X removed (the 2e site) - the vacancy variant seen in
            the stuffed/defective 1:6:6 phases                 (15 cells, 12 atoms)
Template: a real RFe6X6 structure from Materials Project when one exists for
that X (Y or Gd compound), else the HfFe6Ge6 Wyckoff prototype scaled to the X
radius. Writes ../structures/generated_kagome/*.CIF.

Usage:  python3 generate_kagome.py
"""
import os
import time

import requests
from pymatgen.core import Structure, Lattice

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "structures", "generated_kagome")
MP = "https://api.materialsproject.org/materials/summary/"
X_LIST = ["Sn", "Ge", "Si", "Ga", "Al"]
# HfFe6Ge6-type prototype (a, c scaled to X); Wyckoff: R 1a, T 6i (1/2,0,z), X 2c, 2d, 2e (0,0,z)
A_C = {"Sn": (5.37, 8.90), "Ge": (5.13, 8.10), "Si": (5.00, 7.90), "Ga": (5.12, 8.15), "Al": (5.10, 8.20)}


def mp_key():
    p = os.path.join(HERE, ".mp_api_key")
    return os.environ.get("MP_API_KEY") or (open(p).read().strip() if os.path.isfile(p) else "")


def from_mp(x):
    """Try Y-Fe-X and Gd-Fe-X on MP for an RFe6X6 structure in SG 191."""
    k = mp_key()
    if not k:
        return None
    for chem in (f"Fe-{x}-Y", f"Fe-Gd-{x}"):
        els = "-".join(sorted(chem.split("-")))
        try:
            r = requests.get(MP, headers={"X-API-KEY": k}, params={"chemsys": els, "_fields": "material_id,formula_pretty,structure,symmetry,energy_above_hull", "_limit": 200}, timeout=120)
            for d in r.json().get("data", []):
                s = Structure.from_dict(d["structure"])
                comp = s.composition.get_el_amt_dict()
                n_re = comp.get("Y", 0) + comp.get("Gd", 0)
                if n_re and abs(comp["Fe"] / n_re - 6) < 1e-3 and abs(comp[x] / n_re - 6) < 1e-3 and d["symmetry"]["number"] == 191:
                    s.replace_species({"Y": "Gd"})
                    return s.get_primitive_structure() if len(s) > 13 else s
        except Exception:
            time.sleep(2)
    return None


def prototype(x):
    a, c = A_C[x]
    lat = Lattice.hexagonal(a, c)
    return Structure.from_spacegroup(191, lat, ["Gd", "Fe", x, x, x],
                                     [[0, 0, 0], [0.5, 0, 0.25], [1 / 3, 2 / 3, 0], [1 / 3, 2 / 3, 0.5], [0, 0, 0.34]])


def main():
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for x in X_LIST:
        mp = from_mp(x)
        base = mp or prototype(x)
        # figure out which Fe sites are the kagome 6i set (all Fe here) and the channel X (2e: on the c axis, not in a honeycomb plane)
        for tm_tag, co_sites in (("Fe6", 0), ("Co6", 6), ("Fe5Co", 1)):
            s = base.copy()
            fe = [i for i, sp in enumerate(s.species) if sp.symbol == "Fe"]
            for i in fe[:co_sites]:
                s.replace(i, "Co")
            name = f"Gd{tm_tag}{x}6_kagome-191"
            s.to(filename=os.path.join(OUT, name + ".CIF"), fmt="cif"); n += 1
            # vacancy variant: remove one channel X (sites with x=y=0 fractional, not the RE)
            ch = [i for i, site in enumerate(s) if site.specie.symbol == x and abs(site.frac_coords[0]) < 1e-3 and abs(site.frac_coords[1]) < 1e-3]
            if ch:
                sv = s.copy(); sv.remove_sites([ch[0]])
                sv.to(filename=os.path.join(OUT, f"Gd{tm_tag}{x}5_kagome-191-vac.CIF"), fmt="cif"); n += 1
        print(f"{x}: template {'MP' if mp else 'prototype'}  a={base.lattice.a:.2f} c={base.lattice.c:.2f}  {len(base)} atoms")
    print(f"wrote {n} kagome structures to structures/generated_kagome/")


if __name__ == "__main__":
    main()
