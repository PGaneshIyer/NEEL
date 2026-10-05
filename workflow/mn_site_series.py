#!/usr/bin/env python3
"""Mn site-preference and concentration series for the Co16Gd2Mn_sub motif.

Co16Gd2Mn_sub has its single Mn on the Th2Zn17 6c "dumbbell" site - the Co-Co
pair that replaces one third of the RE positions of the parent CaCu5 lattice,
sitting on the 3-fold axis right beside Gd. Two questions follow:

  1. Is FM still the ground state with Mn on each of the OTHER three Co sites
     (18f, 18h, 9d), and which site does Mn prefer (= lowest total energy)?
  2. Does the FM/ferri ordering cross over as Mn concentration rises on the
     site where FM was found? The dumbbell holds two atoms per cell, so the
     series on THIS site is one more point: both dumbbell atoms Mn
     (Co15Gd2Mn2, x = 2/17, which restores full R-3m symmetry). Anything
     higher puts Mn on other sites - and where it goes is what (1) answers,
     so Mn3 is built after, on the winning site, not guessed now.

Every observation of Mn's alignment so far (parallel to the RE, opposite to
Co) comes from the dumbbell site alone. Buried in the Co sublattice, Mn could
just as well couple like Co does - so each new-site compound gets two locked
twins: fm/ferri with Mn parallel to Gd, and an `_mnanti` copy with Mn opposed.
The ground state per site is the minimum of the four released energies; this
costs ~6 extra 20-minute runs and avoids presupposing the answer.

Same locked-relax protocol as everything else in the bundle (ISIF=2, NSW=60,
NUPDOWN locked). Lock targets use the per-site moments MEASURED on
Co16Gd2Mn_sub's own validated fm/ferri runs (OUTCAR_04), including the
~-0.2 (fm) / ~-1.6 (ferri) mu_B offset between the sphere-projected sum and
the band-integrated total that NUPDOWN actually constrains - that is what
reproduces the 41 / 5 locks that already converged cleanly for the parent.
Mn's magnitude on the dumbbell (3.1-3.4 mu_B) is assumed for the other sites;
+-0.5 mu_B barely moves the rounded lock, and release removes the constraint.

Usage
  python3 mn_site_series.py --dry-run
  VASP_PP_PATH=/path/to/potpaw_PBE.64 python3 mn_site_series.py
"""
import argparse
import json
import os
from collections import defaultdict

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

import make_inputs as MI
try:
    import build_campaign as BC
    POTCARS = {"Gd": "Gd", "Mn": BC.POTCAR_MAP.get("Mn", "Mn_pv"), "Co": BC.POTCAR_MAP.get("Co", "Co")}
except Exception:
    POTCARS = {"Gd": "Gd", "Mn": "Mn_pv", "Co": "Co"}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(ROOT, "structures/Gd_substituted/Co16Gd2Mn_from_Co16MnTb2.CIF")

# measured on Co16Gd2Mn_sub OUTCAR_04 (validated release-stage static)
M = {
    "fm":    {"Gd": 6.7475, "Mn": 3.127, "Co": 24.621 / 16, "offset": 40.9227 - 41.116},
    "ferri": {"Gd": 7.0495, "Mn": 3.382, "Co": 23.628 / 16, "offset": 4.5752 - 6.153},
}
INIT = {"Gd": 7.0, "Mn": 3.0, "Co": 1.5}      # initial MAGMOM magnitudes
WYCK_LABEL = {"c": "6c", "d": "9d", "f": "18f", "h": "18h"}   # hexagonal-setting names
RELAX_INCAR = {
    "IBRION": 2, "ISIF": 2, "NSW": 60, "EDIFFG": -0.02, "EDIFF": "1E-06",
    "ISTART": 0, "ICHARG": 2, "LWAVE": ".TRUE.", "LCHARG": ".TRUE.",
}
SPECIES_ORDER = ["Gd", "Mn", "Co"]


def nupdown(counts, config, mn_anti):
    m = M[config]
    s_gd = 1 if config == "fm" else -1
    s_mn = -s_gd if mn_anti else s_gd
    total = (counts["Co"] * m["Co"] + s_gd * counts["Gd"] * m["Gd"]
             + s_mn * counts["Mn"] * m["Mn"] + m["offset"])
    return int(round(abs(total))), total


def magmoms(species_order, config, mn_anti):
    s_gd = 1 if config == "fm" else -1
    s_mn = -s_gd if mn_anti else s_gd
    sign = {"Gd": s_gd, "Mn": s_mn, "Co": 1}
    return [sign[el] * INIT[el] for el, _ in species_order]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = Structure.from_file(SOURCE)
    mn_idx = [i for i, s in enumerate(base) if s.specie.symbol == "Mn"]
    host = base.copy()
    host.replace_species({"Mn": "Co"})
    ds = SpacegroupAnalyzer(host, symprec=0.1).get_symmetry_dataset()
    orbits = defaultdict(list)
    for i, rep in enumerate(ds.equivalent_atoms):
        if host[i].specie.symbol == "Co":
            orbits[ds.wyckoffs[rep]].append(i)
    current = next(w for w, idx in orbits.items() if mn_idx[0] in idx)
    print(f"host Co17Gd2: {ds.international}  Co orbits: "
          + ", ".join(f"{WYCK_LABEL[w]}x{len(idx)}" for w, idx in orbits.items())
          + f"   Mn currently on {WYCK_LABEL[current]}\n")

    # (name, Mn site indices, mn_anti, note)
    plan = []
    for w, idx in orbits.items():
        if w == current:
            continue
        lab = WYCK_LABEL[w]
        plan.append((f"Co16Gd2Mn_{lab}_sub", [idx[0]], False,
                     f"single Mn moved from the {WYCK_LABEL[current]} dumbbell to the {lab} site; Mn initialised parallel to Gd"))
        plan.append((f"Co16Gd2Mn_{lab}_mnanti_sub", [idx[0]], True,
                     f"single Mn on the {lab} site; Mn initialised ANTIparallel to Gd (locked to that state) - twin of Co16Gd2Mn_{lab}_sub"))
    plan.append((f"Co15Gd2Mn2_{WYCK_LABEL[current]}_sub", list(orbits[current]), False,
                 f"both {WYCK_LABEL[current]} dumbbell atoms Mn - the saturated-current-site concentration point (x = 2/17)"))

    gd_sites = [i for i, s in enumerate(host) if s.specie.symbol == "Gd"]
    made = []
    for name, sites, mn_anti, note in plan:
        s = host.copy()
        for i in sites:
            s.replace(i, "Mn")
        d_gd = min(s.get_distance(i, g) for i in sites for g in gd_sites)
        sg = s.get_space_group_info(symprec=0.1)[0]
        s = s.get_sorted_structure(key=lambda site: SPECIES_ORDER.index(site.specie.symbol))
        counts = {el: int(s.composition[el]) for el in SPECIES_ORDER}
        locks = {cfg: nupdown(counts, cfg, mn_anti) for cfg in ("fm", "ferri")}
        print(f"{name:<28} sg={sg:<6} Mn-Gd min {d_gd:.3f} A   "
              f"NUPDOWN fm={locks['fm'][0]} ({locks['fm'][1]:+.2f})  "
              f"ferri={locks['ferri'][0]} ({locks['ferri'][1]:+.2f})")
        if args.dry_run:
            continue

        cif_path = os.path.join(ROOT, "structures/Gd_substituted", f"{name}.CIF")
        s.to(filename=cif_path)
        cfg = {
            "name": name, "encut": 520, "kppa": 8000, "mode": "relax",
            "structure": os.path.relpath(cif_path, HERE),
            "re_element": "Gd", "tm_elements": ["Co"], "polytype": "new-R3m",
            "hree_group": "Tb", "kind": "Gd_surrogate",
            "ldau": {"Gd": {"L": 3, "U": 6.7, "J": 0.7, "ref": "same Gd 4f Ueff=6 eV used throughout"}},
            "potcar_symbols": POTCARS,
            "provenance": {"kind": "mn_site_series", "parent": "Co16Gd2Mn_sub",
                           "mn_sites": sites, "mn_antiparallel_to_gd": mn_anti, "note": note,
                           "lock_targets": {c: locks[c][0] for c in locks}},
        }
        cdir = MI.compound_dir(cfg, s)
        os.makedirs(cdir, exist_ok=True)
        json.dump({k: v for k, v in cfg.items() if k != "encut"},
                  open(os.path.join(cdir, "meta.json"), "w"), indent=1)
        poscar = MI.Poscar(s)
        species_order = list(zip(poscar.site_symbols, poscar.natoms))
        kpts = MI.Kpoints.automatic_density(s, cfg["kppa"])
        for config in ("fm", "ferri"):
            d = os.path.join(cdir, config)
            os.makedirs(d, exist_ok=True)
            poscar.write_file(os.path.join(d, "POSCAR"))
            kpts.write_file(os.path.join(d, "KPOINTS"))
            inc = MI.incar_dict(cfg, species_order, magmoms(species_order, config, mn_anti), name, config)
            inc.update(RELAX_INCAR)
            inc["NUPDOWN"] = locks[config][0]
            MI.write_incar(os.path.join(d, "INCAR"), inc)
            got = MI.assemble_potcar(species_order, POTCARS, d)
            print(f"   wrote {os.path.relpath(d, HERE)}  POTCAR={'yes' if got else 'spec only'}")
        made.append(os.path.relpath(cdir, HERE))

    if not args.dry_run:
        print(f"\n{len(made)} compounds written. Run dirs for the manifest:")
        for c in made:
            print(f"  {c}/fm\n  {c}/ferri")


if __name__ == "__main__":
    main()
