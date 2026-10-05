#!/usr/bin/env python3
"""Expand the candidate pool beyond what the databases happen to contain.

Two generators, in increasing order of cost and risk:

  decorate   Take each NAMED magnet prototype already in the campaign (CaCu5,
             ThMn12, Th2Zn17, Nd2Fe14B, Laves, kagome-166, ...) and substitute
             the non-magnetic X site through a chemistry palette, and swap the
             TM sublattice Fe <-> Co. This is cheap, chemically conservative,
             and historically how most real magnets were found - nearly every
             known magnet is a decoration of a handful of lattices.

  wyckoff    Symmetry-constrained de novo generation: place the same
             stoichiometry on Wyckoff orbits of a target space group. Explores
             genuinely new frameworks, but the hit rate is low and the output
             must be MLIP-relaxed and hull-screened before any DFT is spent.
             Requires pyxtal.

Both write CIFs to structures/generated/ and a registry fragment that
make_inputs.py consumes exactly like compounds_campaign.json.

Usage
  python3 generate_candidates.py decorate --dry-run
  python3 generate_candidates.py decorate --out compounds_generated.json
  python3 generate_candidates.py wyckoff --spacegroups 191 139 --formula Gd1Fe6Sn6
"""
import argparse
import json
import os
import sys
from collections import defaultdict

from pymatgen.core import Structure

import build_campaign as BC     # reuse polytype(), POTCAR_MAP, ARITY, canon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GENDIR = os.path.join(ROOT, "structures", "generated")

TM = {"Fe", "Co"}
RE_SITE = "Gd"          # campaign convention: the RE site always carries Gd

# X-site palette. Chosen for magnet relevance rather than completeness:
# p-block stabilisers and interstitials that appear in real magnet chemistry,
# plus the early TM that stabilise ThMn12.
X_PALETTE = ["Al", "Si", "Ga", "Ge", "B", "C", "N", "P", "Sn", "Sb",
             "Ti", "V", "Cr", "Zr", "Nb", "Mo", "W", "Hf", "Ta", "Cu", "Zn"]


def site_roles(struct):
    els = {sp.symbol for sp in struct.composition}
    return (els & {RE_SITE}, els & TM, els - {RE_SITE} - TM)


def decorate(args):
    reg = json.load(open(os.path.join(HERE, "compounds_campaign.json")))
    entries = reg["compounds"]

    # Recompute the prototype label from the structure rather than trusting the
    # label stored in the registry: the campaign on disk was built with an older
    # classifier that mislabelled the 1-12 family. Recomputing here keeps the
    # live run tree untouched (its directory names are only cosmetic) while the
    # decoration still targets the right prototypes.
    reps, relabelled = {}, 0
    for c in entries:
        try:
            st = Structure.from_file(os.path.join(HERE, c["structure"]))
            sg = st.get_space_group_info()[0]
        except Exception:
            continue
        pt = BC.polytype(st, sg)
        if pt != c.get("polytype"):
            relabelled += 1
        if pt.startswith("new-") and not args.include_new:
            continue
        key = (pt, c["arity_override"])
        if key not in reps:
            reps[key] = dict(c, polytype=pt, _struct=st)
    if relabelled:
        print(f"note: {relabelled} campaign entries get a different prototype label "
              f"under the corrected classifier (run-tree names unchanged)")
    print(f"prototypes to decorate: {len(reps)}  "
          f"({'including' if args.include_new else 'excluding'} new-* frameworks)")

    os.makedirs(GENDIR, exist_ok=True)
    # everything already in the campaign, so we do not re-propose it
    seen = set()
    for c in entries:
        try:
            s = Structure.from_file(os.path.join(HERE, c["structure"]))
            seen.add((s.composition.reduced_formula, s.get_space_group_info()[0]))
        except Exception:
            pass

    made, skipped = [], defaultdict(int)
    for (pt, arity), c in sorted(reps.items()):
        base = c.get("_struct")
        if base is None:
            skipped["unreadable"] += 1
            continue
        re_s, tm_s, x_s = site_roles(base)
        if not tm_s:
            skipped["no_TM"] += 1
            continue

        variants = []
        # (a) X-site substitution, one palette element at a time
        if x_s and not args.no_x:
            for x_old in sorted(x_s):
                for x_new in X_PALETTE:
                    if x_new == x_old or x_new in re_s or x_new in tm_s:
                        continue
                    v = base.copy()
                    v.replace_species({x_old: x_new})
                    variants.append((v, f"X:{x_old}->{x_new}"))
        # (b) TM sublattice swap, Fe <-> Co (both are program-relevant)
        if not args.no_tm:
            for tm_old in sorted(tm_s):
                tm_new = "Co" if tm_old == "Fe" else "Fe"
                if tm_new in tm_s:
                    continue
                v = base.copy()
                v.replace_species({tm_old: tm_new})
                variants.append((v, f"TM:{tm_old}->{tm_new}"))

        for v, tag in variants:
            if len(v) > args.max_sites:
                skipped["too_big"] += 1
                continue
            els = [e.symbol for e in v.composition]
            if any(e not in BC.POTCAR_MAP for e in els):
                skipped["no_potcar"] += 1
                continue
            tmfrac = sum(v.composition[e] for e in els if e in TM) / v.composition.num_atoms
            if tmfrac < args.min_tm_frac:
                skipped["tm_frac"] += 1
                continue
            try:
                sg = v.get_space_group_info()[0]
            except Exception:
                sg = "P1"
            key = (v.composition.reduced_formula, sg)
            if key in seen:
                skipped["duplicate"] += 1
                continue
            seen.add(key)
            made.append({
                "name": f"{v.composition.reduced_formula}_gen",
                "polytype": pt, "spacegroup": sg, "arity": arity,
                "from": c["name"], "op": tag, "struct": v,
                "tm_frac": round(tmfrac, 3), "nsites": len(v),
            })

    print(f"generated: {len(made)}   skipped: {dict(skipped)}")
    if args.dry_run:
        by_pt = defaultdict(int)
        for m in made:
            by_pt[m["polytype"]] += 1
        for pt, n in sorted(by_pt.items(), key=lambda kv: -kv[1]):
            print(f"   {pt:<24}{n:>5}")
        print("\n(dry run - nothing written)")
        return

    out = []
    for m in made[: args.limit] if args.limit else made:
        path = os.path.join(GENDIR, f"{m['name']}_{m['spacegroup'].replace('/', '_')}.CIF")
        try:
            m["struct"].to(filename=path)
        except Exception:
            continue
        els = [e.symbol for e in m["struct"].composition]
        out.append({
            "name": m["name"], "structure": os.path.relpath(path, HERE),
            "re_element": RE_SITE, "tm_elements": sorted(set(els) & TM),
            "polytype": m["polytype"], "spacegroup": m["spacegroup"],
            "arity_override": BC.ARITY.get(len(set(els)), f"{len(set(els))}-ary"),
            "hree_group": "Gd", "kind": "generated",
            "ldau": {"Gd": {"L": 3, "U": 6.7, "J": 0.7, "ref": "same Gd 4f Ueff=6 eV"}},
            "potcar_symbols": {e: BC.POTCAR_MAP[e] for e in els},
            "magmom_init": {e: (2.5 if e == "Fe" else 1.5 if e == "Co"
                                else 7.0 if e == "Gd" else 0.0) for e in els},
            "provenance": {"kind": "prototype_decoration", "parent": m["from"],
                           "operation": m["op"], "prototype": m["polytype"],
                           "note": "generated, NOT from a database - hull "
                                   "distance unknown until screened"},
        })
    reg_out = {"defaults": reg["defaults"], "compounds": out}
    dest = os.path.join(HERE, args.out)
    json.dump(reg_out, open(dest, "w"), indent=1)
    print(f"wrote {len(out)} entries -> {dest}")
    print(f"CIFs in {GENDIR}")
    print("\nNEXT: these have no hull distance. Relax and rank with an MLIP "
          "before committing DFT:\n"
          "  mace / chgnet relax -> E_hull vs MP+Alexandria -> keep <= 0.2 eV/atom\n"
          "  then: python3 make_inputs.py --registry " + args.out)


def wyckoff(args):
    try:
        from pyxtal import pyxtal
    except ImportError:
        sys.exit("pyxtal not installed. pip install pyxtal\n"
                 "Wyckoff generation places a given stoichiometry on the symmetry\n"
                 "orbits of a target space group; without it use 'decorate'.")
    from pymatgen.core import Composition
    os.makedirs(GENDIR, exist_ok=True)
    comp = Composition(args.formula)
    species = [str(e) for e in comp.elements]
    counts = [int(comp[e]) for e in comp.elements]
    n = 0
    for sg in args.spacegroups:
        for trial in range(args.per_spacegroup):
            xtal = pyxtal()
            try:
                xtal.from_random(3, sg, species, counts)
            except Exception:
                continue
            if not xtal.valid:
                continue
            s = xtal.to_pymatgen()
            path = os.path.join(GENDIR, f"{comp.reduced_formula}_sg{sg}_{trial}.CIF")
            s.to(filename=path)
            n += 1
    print(f"wrote {n} symmetry-constrained structures to {GENDIR}")
    print("These are UNRELAXED and mostly unstable: MLIP-relax, hull-screen, "
          "and only then consider DFT.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("decorate", help="substitute known magnet prototypes")
    d.add_argument("--out", default="compounds_generated.json")
    d.add_argument("--dry-run", action="store_true")
    d.add_argument("--include-new", action="store_true",
                   help="also decorate the unnamed new-<spacegroup> frameworks")
    d.add_argument("--no-x", action="store_true", help="skip X-site substitution")
    d.add_argument("--no-tm", action="store_true", help="skip Fe<->Co swap")
    d.add_argument("--min-tm-frac", type=float, default=0.6)
    d.add_argument("--max-sites", type=int, default=80)
    d.add_argument("--limit", type=int, default=0)
    d.set_defaults(func=decorate)

    w = sub.add_parser("wyckoff", help="symmetry-constrained de novo generation")
    w.add_argument("--formula", required=True)
    w.add_argument("--spacegroups", type=int, nargs="+", required=True)
    w.add_argument("--per-spacegroup", type=int, default=20)
    w.set_defaults(func=wyckoff)

    args = ap.parse_args()
    args.func(args)
