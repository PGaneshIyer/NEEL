#!/usr/bin/env python3
"""Interstitial N / C decoration of the Fe-rich hosts that already pass the pool filters.

The lever with the best record in real magnets (Sm2Fe17N3, NdFe12N, NdFe11TiN) and
the one the pool lacked: every "N" in the pool so far was SUBSTITUTIONAL (N on an Fe
site, 250 meV above the hull) - not what the literature does. Here the light atom
goes into the largest void that touches the rare earth: the 2b site of ThMn12-type
cells, the 9e site of Th2Zn17-type cells, and the analogous channel in the GNoME
frameworks. Procedure per host (taken from analysis/pool/pool.csv):
  1. grid search for void centres: points maximising the distance to the nearest
     atom, with at least one RE within 2.8 A (N sits next to the RE in all known
     nitrides) and no atom closer than 1.85 A
  2. symmetry-expand the best void with the host's space-group operations
  3. write three variants: one atom in the void (dilute), the full equivalent
     set (stoichiometric nitride / carbide), for X = N and C
Output: ../structures/generated_interstitial/<cid>_<X><n>.CIF  (light RE kept),
read by wave_pool.py source "interstitial".

Usage:  python3 generate_interstitials.py [--hull-max 30 --ms-min 1.4 --tm-per-re 8 --max 60]
"""
import argparse
import csv
import os

import numpy as np
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "structures", "generated_interstitial")
RE_LIGHT = {"Nd", "Sm", "Pr"}


def voids(s, re_el, min_dist=1.85, re_cut=2.9, grid=0.25):
    """Candidate interstitial centres: grid points far from all atoms, near an RE."""
    lat = s.lattice
    na, nb, nc = [max(4, int(round(x / grid))) for x in lat.abc]
    fr = np.array([[i / na, j / nb, k / nc] for i in range(na) for j in range(nb) for k in range(nc)])
    cart = lat.get_cartesian_coords(fr)
    # distances to all atoms with periodic images via pymatgen's lattice helper
    d_all = lat.get_all_distances(fr, s.frac_coords)          # (npts, natoms)
    dmin = d_all.min(axis=1)
    re_idx = [i for i, sp in enumerate(s.species) if sp.symbol == re_el]
    d_re = d_all[:, re_idx].min(axis=1) if re_idx else np.full(len(fr), 9.0)
    ok = (dmin >= min_dist) & (d_re <= re_cut)
    if not ok.any():
        return []
    order = np.argsort(-dmin * ok)
    picks = []
    for i in order:
        if not ok[i]:
            break
        if all(lat.get_distance_and_image(fr[i], fr[j])[0] > 1.2 for j in picks):
            picks.append(i)
        if len(picks) >= 3:
            break
    return [(fr[i], dmin[i]) for i in picks]


def equivalents(s, frac, symprec=0.1):
    try:
        ops = SpacegroupAnalyzer(s, symprec=symprec).get_symmetry_operations()
    except Exception:
        return [frac]
    pts = []
    for op in ops:
        p = op.operate(frac) % 1.0
        if all(s.lattice.get_distance_and_image(p, q)[0] > 0.5 for q in pts):
            pts.append(p)
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hull-max", type=float, default=30.0)
    ap.add_argument("--ms-min", type=float, default=1.4)
    ap.add_argument("--tm-per-re", type=float, default=8.0)
    ap.add_argument("--max", type=int, default=60, help="max hosts to decorate")
    A = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(HERE, "analysis", "pool", "pool.csv"))))
    hosts = [r for r in rows if r["E_hull_meV"] not in ("", None) and float(r["E_hull_meV"]) <= A.hull_max
             and float(r["Ms_proj_T"]) >= A.ms_min and float(r["TM_per_RE"]) >= A.tm_per_re
             and not set(r["formula"]).intersection(set()) and "N" not in r["formula"].replace("Nd", "") and "C" not in r["formula"].replace("Co", "").replace("Cr", "").replace("Cu", "")]
    hosts.sort(key=lambda r: -float(r["Ms_proj_T"]))
    n = 0
    seen = set()
    for r in hosts:
        if len(seen) >= A.max:
            break
        key = (r["formula"], r["spacegroup"])
        if key in seen:
            continue
        s = Structure.from_file(os.path.join(HERE, r["poscar"]))
        v = voids(s, r["re_el"])
        if not v:
            continue
        seen.add(key)
        frac, dmin = v[0]
        eq = equivalents(s, frac)
        for X in ("N", "C"):
            s1 = s.copy(); s1.append(X, frac)
            s1.to(filename=os.path.join(OUT, f"{r['cid']}_{X}1.CIF"), fmt="cif"); n += 1
            if 1 < len(eq) <= 6:
                sf = s.copy()
                for p in eq:
                    sf.append(X, p)
                sf.to(filename=os.path.join(OUT, f"{r['cid']}_{X}{len(eq)}.CIF"), fmt="cif"); n += 1
        print(f"{r['formula']:<16} sg {r['spacegroup']:>4}  void r={dmin:.2f} A  equivalents {len(eq)}")
    print(f"wrote {n} interstitial structures for {len(seen)} hosts -> structures/generated_interstitial/")


if __name__ == "__main__":
    main()
