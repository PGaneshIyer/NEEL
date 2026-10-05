#!/usr/bin/env python3
"""Tier-2 direct verification: compute fm-vs-ferri DIRECTLY on each real heavy
RE (Tb, Dy, Ho, Er, Tm) at its own native GNoME-relaxed lattice - no Gd
surrogate, no de Gennes projection. potpaw_PBE.64 ships an explicit-4f POTCAR
for every one of these (verified: unsuffixed variant has ZVAL 19-23, growing
by one electron per element exactly as expected for 4f8->4f12; the "_3"
variant is f-in-core, ZVAL=9 flat). This was the whole point of the Gd
surrogate + de Gennes projection - it let the campaign screen 352 compounds
without needing a converged calculation per RE. Now that Co16RE2Mn survived
five separate Gd-substituted geometries, it's worth spending five REAL
calculations to confirm the projection instead of trusting it.

Same relax-from-the-start protocol as motif_series.py (learned the hard way
from Co16Gd2Mn_sub: starting static on a frozen, un-relaxed geometry risks
mistaking a relaxation artifact for a real fm/ferri energy difference).

ASSUMPTION carried over unchanged from the rest of the campaign: LDAU U=6.7 /
J=0.7 eV (Harmon-Antropov, derived for Gd intermetallics) is reused for every
heavy RE here, since 4f orbitals are similarly core-like/localized across the
whole lanthanide series and no compound-specific literature value was sourced
per element. Flagging this explicitly - it's the one physics choice this
script does NOT independently verify.

Usage
  python3 native_hree_series.py --dry-run
  python3 native_hree_series.py
"""
import argparse
import json
import os

from pymatgen.core import Structure

import build_campaign as BC
import make_inputs as MI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# (native GNoME CIF, GNoME id, heavy RE, Hund's-rule 2S for RE3+)
NATIVE = [
    ("Tb2MnCo16_c5c3fa2e33.CIF", "c5c3fa2e33", "Tb", 6.0),   # 4f8, S=3
    ("Dy2MnCo16_0e6c8cfb41.CIF", "0e6c8cfb41", "Dy", 5.0),   # 4f9, S=5/2
    ("Ho2MnCo16_2c152f71a1.CIF", "2c152f71a1", "Ho", 4.0),   # 4f10, S=2
    ("Er2MnCo16_3e14a9c304.CIF", "3e14a9c304", "Er", 3.0),   # 4f11, S=3/2
    ("Tm2MnCo16_a27df9df29.CIF", "a27df9df29", "Tm", 2.0),   # 4f12, S=1
]
RELAX_INCAR = {
    "IBRION": 2, "ISIF": 2, "NSW": 60, "EDIFFG": -0.02, "EDIFF": "1E-06",
    "ISTART": 0, "ICHARG": 2, "LWAVE": ".TRUE.", "LCHARG": ".TRUE.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    made = []

    for cif_name, gid, hree, two_s in NATIVE:
        struct = Structure.from_file(os.path.join(ROOT, "structures/GNoME", cif_name))
        sg = struct.get_space_group_info()[0]
        pt = BC.polytype(struct, sg)
        name = f"Co16{hree}2Mn_native"

        els = [e.symbol for e in struct.composition]
        cfg = {
            "name": name, "encut": 520, "kppa": 8000, "mode": "relax",
            "structure": os.path.relpath(
                os.path.join(ROOT, "structures/GNoME", cif_name), HERE),
            "re_element": hree, "tm_elements": sorted(set(els) & {"Fe", "Co"}),
            "polytype": pt, "hree_group": hree, "kind": "native_direct",
            "ldau": {hree: {"L": 3, "U": 6.7, "J": 0.7,
                            "ref": "Gd Ueff reused across heavy RE series "
                                   "(Harmon-Antropov) - not independently "
                                   "verified per element"}},
            "potcar_symbols": {e: BC.POTCAR_MAP.get(e, e) for e in els} | {hree: hree},
            "magmom_init": {"Fe": 2.5, "Co": 1.5, hree: two_s, "default": 0.0},
            "provenance": {"kind": "native_hree_series",
                           "note": f"direct explicit-4f DFT+U on {hree} itself "
                                   f"(GNoME id {gid}), no Gd surrogate, no de "
                                   f"Gennes projection - verifies the "
                                   f"Gd-substituted motif-series projection",
                           "source_gnome_id": gid, "parent_hree": [hree]},
        }
        print(f"{name:<20} <- {hree}'s own native lattice ({gid})  "
              f"polytype={pt}  2S={two_s}  {len(struct)} atoms")

        if args.dry_run:
            continue

        cdir = MI.compound_dir(cfg, struct)
        os.makedirs(cdir, exist_ok=True)
        json.dump({"name": name, "re_element": hree, "tm_elements": cfg["tm_elements"],
                   "polytype": pt, "hree_group": hree, "kind": "native_direct",
                   "ldau": cfg["ldau"], "source_structure": cfg["structure"],
                   "provenance": cfg["provenance"]},
                  open(os.path.join(cdir, "meta.json"), "w"), indent=1)

        poscar = MI.Poscar(struct)
        species_order = list(zip(poscar.site_symbols, poscar.natoms))
        kpts = MI.Kpoints.automatic_density(struct, 8000)
        for config in ("fm", "ferri"):
            d = os.path.join(cdir, config)
            os.makedirs(d, exist_ok=True)
            poscar.write_file(os.path.join(d, "POSCAR"))
            kpts.write_file(os.path.join(d, "KPOINTS"))
            mags = MI.site_magmoms(species_order, cfg, config)
            inc = MI.incar_dict(cfg, species_order, mags, name, config)
            inc.update(RELAX_INCAR)
            MI.write_incar(os.path.join(d, "INCAR"), inc)
            got = MI.assemble_potcar(species_order, cfg["potcar_symbols"], d)
            print(f"  wrote {os.path.relpath(d, HERE)}  POTCAR={'yes' if got else 'spec only'}")
        made.append(name)

    if not args.dry_run:
        print(f"\n{len(made)} compounds written: {made}")
        print("These start in relax mode directly (ISIF=2), same lesson as "
              "motif_series.py. After relax finishes, run relax_survivor.py's "
              "--stage release logic against each (it only needs the compound "
              "name and OSZICAR to work, no code change required).")


if __name__ == "__main__":
    main()
