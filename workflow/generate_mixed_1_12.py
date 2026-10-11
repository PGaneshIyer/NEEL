#!/usr/bin/env python3
"""Mixed-RE, fractional-stabiliser 1:12 nitrides, e.g. (Pr,Nd)Fe10.5V1.5N - the
composition class of the real NdFe12-based magnets, which ordered single cells
cannot express. Built as 2-formula-unit supercells of the pool's RFe11V cell:
  Fe21V3        one extra V on the Fe site farthest from the RE (= Fe10.5V1.5)
  RE pairs      Nd2, NdPr, NdSm   (Dy-doped variants are NOT built: Dy is heavy, its
                effect on Ms is the de Gennes projection of the Gd label, and it needs
                4f-in-valence - outside the f-in-core wave label)
  N             0, 1 and 2 atoms in the largest RE-adjacent voids (= N0.5, N1 per f.u.)
Writes ../structures/generated_mixed/*.CIF (light RE kept) for wave_pool source "mixed".

Usage: python3 generate_mixed_1_12.py
"""
import csv
import os

from pymatgen.core import Structure

import generate_interstitials as GI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "structures", "generated_mixed")


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(HERE, "analysis", "pool", "pool.csv"))))
    base = next((r for r in rows if r["formula"] == "NdVFe11" and r["re_el"] == "Nd"), None)
    if base is None:
        raise SystemExit("NdVFe11 not in pool.csv")
    s0 = Structure.from_file(os.path.join(HERE, base["poscar"]))
    sc = s0 * (2, 1, 1) if s0.lattice.a <= s0.lattice.b else s0 * (1, 2, 1)
    re_idx = [i for i, sp in enumerate(sc.species) if sp.symbol == "Nd"]
    fe = [i for i, sp in enumerate(sc.species) if sp.symbol == "Fe"]
    far = max(fe, key=lambda i: min(sc.get_distance(i, j) for j in re_idx))
    sc.replace(far, "V")                                  # Nd2 Fe21 V3
    n = 0
    for tag, swap in (("Nd2", None), ("NdPr", "Pr"), ("NdSm", "Sm")):
        s = sc.copy()
        if swap:
            s.replace(re_idx[1], swap)
        for nN in (0, 1, 2):
            sN = s.copy()
            if nN:
                v = GI.voids(sN, "Nd")
                if not v:
                    continue
                pts = [vv[0] for vv in v][:nN]            # distinct RE-adjacent voids, largest first
                if len(pts) < nN:
                    continue
                for p in pts:
                    sN.append("N", p)
            name = f"{tag}Fe21V3N{nN}_1-12-mixed"
            sN.to(filename=os.path.join(OUT, name + ".CIF"), fmt="cif"); n += 1
            print(name, len(sN), "atoms", sN.composition.reduced_formula)
    print(f"wrote {n} structures -> structures/generated_mixed/")


if __name__ == "__main__":
    main()
