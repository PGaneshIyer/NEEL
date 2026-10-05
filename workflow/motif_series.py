#!/usr/bin/env python3
"""Tier-1 robustness check for the Co16Gd2Mn 'motif': is the FM-over-ferri
preference found on Tb's native lattice a general feature of this Co16Mn-RE2
structure family, or specific to one geometry?

Co16Gd2Mn_sub was built from Co16MnTb2, the lowest-hull member of a group of
five GNoME-predicted parents (Tb, Dy, Ho, Er, Tm variants) that build_campaign.py
collapsed to one representative. The other four were never discarded outright -
their own independently DFT-relaxed native lattices are still on disk. This
script builds the SAME Gd-substituted compound on each of the other four native
lattices (Tb's is already running via relax_survivor.py), so all five can be
relaxed and compared on equal footing.

Unlike the rest of the campaign, these start directly in RELAX mode (ISIF=2,
fixed cell - each lattice is already close to ITS OWN equilibrium, only the
element-swap to Gd needs settling) rather than static-then-rerun, since the
static-frozen protocol is exactly what this check exists to get past.

Usage
  python3 motif_series.py --dry-run
  python3 motif_series.py
"""
import argparse
import json
import os

from pymatgen.core import Structure

import build_campaign as BC
import make_inputs as MI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (native GNoME CIF, GNoME id, heavy RE this lattice belongs to)
NATIVE = [
    ("Tb2MnCo16_c5c3fa2e33.CIF", "c5c3fa2e33", "Tb"),   # already relaxing as Co16Gd2Mn_sub
    ("Dy2MnCo16_0e6c8cfb41.CIF", "0e6c8cfb41", "Dy"),
    ("Ho2MnCo16_2c152f71a1.CIF", "2c152f71a1", "Ho"),
    ("Er2MnCo16_3e14a9c304.CIF", "3e14a9c304", "Er"),
    ("Tm2MnCo16_a27df9df29.CIF", "a27df9df29", "Tm"),
]
RELAX_INCAR = {
    "IBRION": 2, "ISIF": 2, "NSW": 60, "EDIFFG": -0.02, "EDIFF": "1E-06",
    "ISTART": 0, "ICHARG": 2, "LWAVE": ".TRUE.", "LCHARG": ".TRUE.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-tb", action="store_true", default=True,
                    help="Tb's native lattice IS Co16Gd2Mn_sub, already relaxing "
                         "via relax_survivor.py - skip it here by default")
    args = ap.parse_args()

    subdir = os.path.join(ROOT, "structures", "Gd_substituted")
    os.makedirs(subdir, exist_ok=True)
    made = []

    for cif_name, gid, hree in NATIVE:
        if hree == "Tb" and args.skip_tb:
            print(f"skip Tb (native lattice already in use by Co16Gd2Mn_sub)")
            continue

        struct = Structure.from_file(os.path.join(ROOT, "structures/GNoME", cif_name))
        sub = struct.copy()
        sub.replace_species({hree: "Gd"})
        sg = sub.get_space_group_info()[0]
        pt = BC.polytype(sub, sg)
        name = f"Co16Gd2Mn_at{hree}_sub"

        cif_path = os.path.join(subdir, f"{name}.CIF")
        if not args.dry_run:
            sub.to(filename=cif_path)

        els = [e.symbol for e in sub.composition]
        arity = MI.ARITY.get(len(set(els)), f"{len(set(els))}-ary")
        cfg = {
            "name": name, "encut": 520, "kppa": 8000, "mode": "relax",
            "structure": os.path.relpath(cif_path, HERE),
            "re_element": "Gd", "tm_elements": sorted(set(els) & {"Fe", "Co"}),
            "polytype": pt, "hree_group": hree, "kind": "Gd_surrogate_native",
            "ldau": {"Gd": {"L": 3, "U": 6.7, "J": 0.7,
                            "ref": "same Gd 4f Ueff=6 eV used throughout"}},
            "potcar_symbols": {e: BC.POTCAR_MAP[e] for e in els},
            "magmom_init": {"Fe": 2.5, "Co": 1.5, "Gd": 7.0, "default": 0.0},
            "provenance": {"kind": "motif_series",
                           "note": f"same Gd2MnCo16 substitution as Co16Gd2Mn_sub, "
                                   f"but on {hree}'s OWN native GNoME-relaxed "
                                   f"lattice (id {gid}), not Tb's transferred one",
                           "source_gnome_id": gid, "parent_hree": [hree]},
        }
        print(f"{name:<22} <- {hree}'s native lattice ({gid})  polytype={pt}"
              f"  {len(sub)} atoms")

        if args.dry_run:
            continue

        struct_obj = Structure.from_file(cif_path)
        cdir = MI.compound_dir(cfg, struct_obj)
        os.makedirs(cdir, exist_ok=True)
        json.dump({"name": name, "re_element": "Gd", "tm_elements": cfg["tm_elements"],
                   "polytype": pt, "hree_group": hree, "kind": "Gd_surrogate_native",
                   "ldau": cfg["ldau"], "source_structure": cfg["structure"],
                   "provenance": cfg["provenance"]},
                  open(os.path.join(cdir, "meta.json"), "w"), indent=1)

        poscar = MI.Poscar(struct_obj)
        species_order = list(zip(poscar.site_symbols, poscar.natoms))
        kpts = MI.Kpoints.automatic_density(struct_obj, 8000)
        for config in ("fm", "ferri"):
            d = os.path.join(cdir, config)
            os.makedirs(d, exist_ok=True)
            poscar.write_file(os.path.join(d, "POSCAR"))
            kpts.write_file(os.path.join(d, "KPOINTS"))
            mags = MI.site_magmoms(species_order, cfg, config)
            inc = MI.incar_dict(cfg, species_order, mags, name, config)
            inc.update(RELAX_INCAR)   # relax mode from the start, not static
            MI.write_incar(os.path.join(d, "INCAR"), inc)
            got = MI.assemble_potcar(species_order, cfg["potcar_symbols"], d)
            print(f"  wrote {os.path.relpath(d, HERE)}  POTCAR={'yes' if got else 'spec only'}")
        made.append(name)

    if not args.dry_run:
        print(f"\n{len(made)} compounds written: {made}")
        print("These land in the normal runs/ tree under their own HREE folder, "
              "so `./sync_results.sh` / `submit_batch.sh all` pick them up "
              "alongside the rest of the campaign automatically.")
        print("Because they start in relax mode, the RELEASE step (unconstrained "
              "static at the relaxed geometry) still needs running afterwards - "
              "reuse relax_survivor.py's --stage release logic, or add these "
              "compound names to a small follow-up call once relax finishes.")


if __name__ == "__main__":
    main()
