#!/usr/bin/env python3
"""Mechanism-2 test on Co15Gd2Mn2 (both 6c dumbbell atoms Mn, 2.36 A apart).

Context: released energies show Co16Gd2Mn is an ordinary Neel ferrimagnet
(Gd down, Mn WITH Co) and that one Mn barely dents the Gd-TM coupling
(229 -> 208 meV/Gd). The one route left to a Gd-with-Co state is Mn-Mn
antiferromagnetism: the Mn dumbbell pair sits at the shortest TM-TM distance
in the cell, squarely in the AFM region of the Bethe-Slater curve. If the pair
reverses against Co, Gd - antiparallel to its nearest (Mn) neighbours - would
end up parallel to the dominant Co sublattice: a three-sublattice state with
a large net moment (~30 mu_B, ~1.5 T). The NUPDOWN=0 lock we put on this
compound's "ferri" assumed Mn with Gd and collapsed the Mn moments instead -
consistent with the lock fighting a state the system does not want.

Four locked relaxes (ISIF=2, hardened SCF), each a candidate ordering, all
released afterwards and compared with the already-released fm (-147.43 eV):
   A  Gd dn  Mn up up  Co up   plain ferrimagnet, Mn with Co        lock 13
   B  Gd dn  Mn up dn  Co up   AFM Mn pair, Gd against Co            lock  6
   C  Gd up  Mn dn dn  Co up   Mn pair reversed, Gd WITH Co          lock 30
   D  Gd up  Mn up dn  Co up   AFM Mn pair inside the FM background  lock 36
Locks use the per-site moments measured on the parent (same convention as
mn_site_series.py, incl. the band-vs-sphere offset). Initial MAGMOM is written
per site so the two Mn can start opposite; VASP lowers the symmetry itself.

Usage
  python3 mn2_states.py --dry-run
  VASP_PP_PATH=... python3 mn2_states.py
"""
import argparse
import json
import os
import shutil

from rerun_constrained import read_incar, write_incar

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "runs/ternary/Tb/new-R3m/Co15Gd2Mn2_6c_sub")
TEMPLATE = os.path.join(BASE, "fm")

# measured on Co16Gd2Mn_sub (validated statics); Co per atom, Gd per atom
M = {"fm":    {"Gd": 6.7475, "Mn": 3.127, "Co": 1.5388, "off": -0.193},
     "ferri": {"Gd": 7.0495, "Mn": 3.382, "Co": 1.4768, "off": -1.578}}
N_GD, N_MN, N_CO = 2, 2, 15

STATES = {
    # name: (gd_sign, (mn1, mn2) signs, which measured set)
    "A_GdDn_MnUpUp": (-1, (+1, +1), "ferri"),
    "B_GdDn_MnAFM":  (-1, (+1, -1), "ferri"),
    "C_GdUp_MnDnDn": (+1, (-1, -1), "fm"),
    "D_GdUp_MnAFM":  (+1, (+1, -1), "fm"),
}
HARDEN = {"NELM": 400, "AMIX": 0.2, "BMIX": 0.0001, "AMIX_MAG": 0.8, "BMIX_MAG": 0.0001}


def lock(gd_s, mn_s, which):
    m = M[which]
    tot = N_CO * m["Co"] + gd_s * N_GD * m["Gd"] + sum(mn_s) * m["Mn"] + m["off"]
    return int(round(abs(tot))), tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    inc0 = read_incar(os.path.join(TEMPLATE, "INCAR"))
    assert inc0, f"template INCAR missing: {TEMPLATE}"
    made = []
    for name, (gd_s, mn_s, which) in STATES.items():
        nup, tot = lock(gd_s, mn_s, which)
        magmom = (f"{N_GD}*{gd_s*7.0:.2f}  " + "  ".join(f"{s*3.0:.2f}" for s in mn_s)
                  + f"  {N_CO}*1.50")
        print(f"{name:<16} MAGMOM = {magmom:<38} NUPDOWN={nup:>3} ({tot:+.2f})")
        if args.dry_run:
            continue
        d = os.path.join(BASE, name)
        os.makedirs(d, exist_ok=True)
        for f in ("POSCAR", "KPOINTS", "POTCAR", "POTCAR.spec"):
            src = os.path.join(TEMPLATE, f)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(d, f))
        inc = dict(inc0)
        inc["SYSTEM"] = f"Co15Gd2Mn2 {name} locked relax"
        inc["MAGMOM"] = magmom
        inc["NUPDOWN"] = str(nup)
        inc.update({k: str(v) for k, v in HARDEN.items()})
        inc.update({"ISTART": "0", "ICHARG": "2"})
        write_incar(os.path.join(d, "INCAR"), inc)
        made.append(d)
    if not args.dry_run:
        json.dump({"purpose": "mechanism-2 test: Mn-Mn AFM on the 6c dumbbell",
                   "states": {k: {"gd": v[0], "mn": list(v[1]), "lock": lock(*v)[0]} for k, v in STATES.items()},
                   "compare_with": "fm (released -147.43 eV, 42.3 uB)"},
                  open(os.path.join(BASE, "states_meta.json"), "w"), indent=1)
        print(f"\n{len(made)} state dirs written under {os.path.relpath(BASE, HERE)}/")
        print("manifest lines:"); [print("  " + os.path.relpath(d, HERE)) for d in made]


if __name__ == "__main__":
    main()
