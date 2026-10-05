#!/usr/bin/env python3
"""Generate paired FM / ferrimagnetic VASP (PBE+U) inputs for RE-TM intersublattice
exchange: for each enabled compound in compounds.json, writes

    runs/<name>/fm/     RE moments initialized parallel to TM
    runs/<name>/ferri/  RE moments initialized antiparallel to TM

E(ferri) - E(fm) < 0  =>  ferrimagnetic ground state (the usual heavy-RE case).

Requires pymatgen. POTCARs are concatenated from $VASP_PP_PATH/<symbol>/POTCAR
(VASP potpaw_PBE layout) when available, otherwise a POTCAR.spec file is written
and the POTCAR must be assembled on the cluster (see README).

Usage:  python3 make_inputs.py [--registry compounds.json] [--only NAME ...]
"""
import argparse
import json
import os
import shutil
import sys

from pymatgen.core import Structure
from pymatgen.io.vasp.inputs import Kpoints, Poscar

HERE = os.path.dirname(os.path.abspath(__file__))

ARITY = {1: "elemental", 2: "binary", 3: "ternary", 4: "quaternary",
         5: "quinary", 6: "senary"}


def compound_dir(cfg, struct):
    """runs/<arity>/<HREE>/<polytype>/<compound>
    polytype: a magnet prototype label (CaCu5, ThMn12, Th2Zn17, Th2Ni17, Nd2Fe14B,
    Laves-C14, Laves-C15, kagome-166, ...) or new-<spacegroup> for structures that
    match none; set per compound in the registry.
    HREE level is `hree_group` when present - for a Gd-surrogate structure that is
    the parent compound's rare earth, not the Gd actually in the cell - so the
    per-HREE batch submission groups runs by the element they are answering for."""
    nel = len(set(sp.symbol for sp in struct.composition))
    arity = cfg.get("arity_override") or ARITY.get(nel, f"{nel}-ary")
    polytype = cfg.get("polytype", "unassigned")
    hree = cfg.get("hree_group") or cfg["re_element"]
    return os.path.join(HERE, "runs", arity, hree, polytype, cfg["name"])


def incar_dict(cfg, species_order, magmoms, name, config):
    """Build the INCAR as an ordered dict. species_order: list of (element, count)."""
    ldau = cfg["ldau"]
    inc = {
        "SYSTEM": f"{name} {config} RE-TM exchange",
        "PREC": "Accurate",
        "ENCUT": cfg["encut"],
        "EDIFF": 1e-6,
        "NELM": 200,
        "ALGO": "Normal",
        "ISMEAR": 1,
        "SIGMA": 0.2,
        "ISPIN": 2,
        "MAGMOM": "  ".join(f"{n}*{m:.2f}" for (_, n), m in zip(species_order, magmoms)),
        "LORBIT": 11,
        "LASPH": True,
        "LMAXMIX": 6,
        "LDAU": True,
        "LDAUTYPE": 2,
        "LDAUL": " ".join(str(ldau.get(el, {}).get("L", -1)) for el, _ in species_order),
        "LDAUU": " ".join(f"{ldau.get(el, {}).get('U', 0.0):.2f}" for el, _ in species_order),
        "LDAUJ": " ".join(f"{ldau.get(el, {}).get('J', 0.0):.2f}" for el, _ in species_order),
        "LDAUPRINT": 1,
        "LREAL": False,
        "LWAVE": False,
        "LCHARG": False,
        "KPAR": 4,
    }
    if cfg["mode"] == "relax":
        inc.update({"IBRION": 2, "ISIF": 3, "NSW": 99, "EDIFFG": -0.01})
    else:
        inc.update({"IBRION": -1, "NSW": 0})
    inc.update(cfg.get("incar_overrides", {}))
    return inc


def write_incar(path, inc):
    with open(path, "w") as f:
        for k, v in inc.items():
            if isinstance(v, bool):
                v = ".TRUE." if v else ".FALSE."
            f.write(f"{k} = {v}\n")


def site_magmoms(species_order, cfg, config):
    """One initial moment per POSCAR species block. In 'ferri' the RE block flips."""
    mm = cfg["magmom_init"]
    out = []
    for el, _ in species_order:
        if el == cfg["re_element"]:
            m = mm.get(el, 7.0)
            out.append(-m if config == "ferri" else m)
        elif el in cfg["tm_elements"]:
            out.append(mm.get(el, 2.5))
        else:
            out.append(mm.get(el, mm.get("default", 0.0)))
    return out


def assemble_potcar(species_order, symbols, dest):
    pp = os.environ.get("VASP_PP_PATH")
    syms = [symbols.get(el, el) for el, _ in species_order]
    with open(os.path.join(dest, "POTCAR.spec"), "w") as f:
        f.write("\n".join(syms) + "\n")
    if not pp:
        return False
    parts = []
    for s in syms:
        cand = os.path.join(pp, s, "POTCAR")
        if not os.path.exists(cand):
            return False
        parts.append(cand)
    with open(os.path.join(dest, "POTCAR"), "wb") as out:
        for p in parts:
            with open(p, "rb") as src:
                shutil.copyfileobj(src, out)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=os.path.join(HERE, "compounds.json"))
    ap.add_argument("--only", nargs="*", help="restrict to these compound names")
    args = ap.parse_args()

    reg = json.load(open(args.registry))
    defaults = reg["defaults"]
    made = 0
    for comp in reg["compounds"]:
        if not comp.get("enabled", True):
            continue
        if args.only and comp["name"] not in args.only:
            continue
        cfg = {**defaults, **comp}
        cfg["magmom_init"] = {**defaults["magmom_init"], **comp.get("magmom_init", {})}
        cfg["incar_overrides"] = {**defaults.get("incar_overrides", {}),
                                  **comp.get("incar_overrides", {})}

        spath = os.path.join(HERE, cfg["structure"])
        if not os.path.exists(spath):
            print(f"SKIP {cfg['name']}: structure not found: {spath}", file=sys.stderr)
            continue
        struct = Structure.from_file(spath).get_sorted_structure()
        poscar = Poscar(struct)
        species_order = [(s.symbol, n) for s, n in
                         zip(poscar.structure.composition.keys(), [0]*0)] or None
        # robust species blocks straight from the POSCAR object:
        species_order = list(zip(poscar.site_symbols, poscar.natoms))

        kpts = Kpoints.automatic_density(struct, cfg["kppa"])
        cdir = compound_dir(cfg, struct)
        os.makedirs(cdir, exist_ok=True)
        json.dump({"name": cfg["name"], "re_element": cfg["re_element"],
                   "tm_elements": cfg["tm_elements"], "polytype": cfg.get("polytype"),
                   "hree_group": cfg.get("hree_group"), "kind": cfg.get("kind"),
                   "ldau": cfg["ldau"], "source_structure": cfg["structure"],
                   "provenance": cfg.get("provenance", {})},
                  open(os.path.join(cdir, "meta.json"), "w"), indent=1)

        for config in ("fm", "ferri"):
            d = os.path.join(cdir, config)
            os.makedirs(d, exist_ok=True)
            poscar.write_file(os.path.join(d, "POSCAR"))
            kpts.write_file(os.path.join(d, "KPOINTS"))
            mags = site_magmoms(species_order, cfg, config)
            write_incar(os.path.join(d, "INCAR"),
                        incar_dict(cfg, species_order, mags, cfg["name"], config))
            got_potcar = assemble_potcar(species_order, cfg["potcar_symbols"], d)
            made += 1
            print(f"wrote {os.path.relpath(d, HERE)}"
                  f"  species={[f'{e}x{n}' for e,n in species_order]}"
                  f"  MAGMOM_RE={'+' if config=='fm' else '-'}"
                  f"  POTCAR={'yes' if got_potcar else 'POTCAR.spec only'}")
    print(f"\n{made} run directories written under {os.path.join(HERE, 'runs')}")


if __name__ == "__main__":
    main()
