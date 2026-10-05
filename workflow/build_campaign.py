#!/usr/bin/env python3
"""Build the Gd campaign registry from the master candidate list.

Two classes of compound:
  native      - the structure already contains Gd; run it as-is.
  Gd-surrogate- a Tb/Dy/Ho/Er/Tm compound with every heavy-RE site replaced by Gd,
                so the 4f can actually flip in VASP (Tb-Tm ship as f-in-core *_3
                POTCARs). One surrogate can stand in for several parent compounds
                that share a structure; the coupling sign transfers back to each
                parent by de Gennes scaling, (g_J - 1)J.

Surrogates are deduplicated on (substituted formula, space group) and dropped when
they duplicate a native Gd candidate. Each compound records its parents in
provenance, and lands under the HREE of its primary parent so the per-HREE batch
submission still splits the campaign into manageable arrays.

Usage:  python3 build_campaign.py [--max-sites 80] [--out compounds_campaign.json]
"""
import argparse
import csv
import glob
import json
import os
import re
from collections import defaultdict
from functools import reduce
from math import gcd

from pymatgen.core import Structure
from pymatgen.io.vasp.sets import MPRelaxSet

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HREE = ["Gd", "Tb", "Dy", "Ho", "Er", "Tm"]
TM = {"Fe", "Co"}
# radioactive / unusable in a real magnet
BANNED = {"Tc", "Pm", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf",
          "Es", "Fm", "Md", "No", "Lr", "Po", "At", "Rn", "Fr", "Ra"}
ARITY = {1: "elemental", 2: "binary", 3: "ternary", 4: "quaternary", 5: "quinary",
         6: "senary"}
POTCAR_MAP = dict(MPRelaxSet.CONFIG["POTCAR"])
# Gd must keep its 4f in the valence for the fm/ferri flip to mean anything.
POTCAR_MAP["Gd"] = "Gd"
# Any OTHER rare earth appearing as a third element is a spectator here: pin it to
# the f-in-core (_3) potential so only the Gd sublattice carries a flippable 4f
# moment and the fm/ferri energy difference stays a two-sublattice quantity.
for _re, _sym in (("La", "La"), ("Ce", "Ce_3"), ("Pr", "Pr_3"), ("Nd", "Nd_3"),
                  ("Sm", "Sm_3"), ("Eu", "Eu_2"), ("Yb", "Yb_2"), ("Lu", "Lu_3")):
    POTCAR_MAP[_re] = _sym


def resolve_potcars(pp_path):
    """Keep only symbols that actually exist in the local PAW library, falling back
    through the usual variants (potpaw_PBE.64 renamed some, e.g. W_pv -> W_sv)."""
    if not pp_path or not os.path.isdir(pp_path):
        return
    for el, sym in list(POTCAR_MAP.items()):
        if os.path.exists(os.path.join(pp_path, sym, "POTCAR")):
            continue
        for cand in (f"{el}_sv", f"{el}_pv", el, f"{el}_d", f"{el}_3"):
            if os.path.exists(os.path.join(pp_path, cand, "POTCAR")):
                POTCAR_MAP[el] = cand
                break
        else:
            POTCAR_MAP.pop(el)   # unusable element; compounds using it are skipped


resolve_potcars(os.environ.get("VASP_PP_PATH"))


def canon(comp):
    ints = {k: int(round(v)) for k, v in comp.items() if round(v) > 0}
    g = reduce(gcd, ints.values()) or 1
    return "".join(k + (str(n // g) if n // g > 1 else "") for k, n in sorted(ints.items()))


# Strukturbericht -> the name this program actually uses for that lattice, so an
# AFLOW match and the heuristic produce the same directory name for the same thing.
SB_ALIAS = {
    "C15": "Laves-C15", "C14": "Laves-C14", "C36": "Laves-C36",
    "D2_d": "CaCu5", "D8_5": "Th2Zn17", "D8_11": "ThMn12",
    "L2_1": "Heusler", "C1_b": "half-Heusler", "C16": "ThCr2Si2-122",
}
_AFLOW_MATCHER = None
_AFLOW_CACHE = {}


def aflow_prototype(struct):
    """Authoritative prototype identity from the AFLOW library, or None.

    Uses pymatgen's bundled AFLOW prototype set. NOTE the coverage limit measured
    on this campaign: it matches ~1% of these structures (2/352) because the
    bundled library is dominated by unary and binary prototypes, while every
    candidate here is ternary or richer. It is exact where it does match, so it
    is consulted first and recorded as metadata; the stoichiometry heuristic
    below carries the rest. Full ternary coverage needs the `aflow` binary
    (AFLOW-XtalFinder) against the complete 1,783-prototype library.
    """
    global _AFLOW_MATCHER
    key = (struct.composition.reduced_formula, len(struct))
    if key in _AFLOW_CACHE:
        return _AFLOW_CACHE[key]
    try:
        if _AFLOW_MATCHER is None:
            from pymatgen.analysis.prototypes import AflowPrototypeMatcher
            _AFLOW_MATCHER = AflowPrototypeMatcher()
        hits = _AFLOW_MATCHER.get_prototypes(struct)
    except Exception:
        hits = None
    out = None
    if hits:
        tags = hits[0].get("tags", {}) or {}
        out = {"aflow": tags.get("aflow"), "strukturbericht": tags.get("strukturbericht"),
               "mineral": tags.get("mineral"), "pearson": tags.get("pearson")}
    _AFLOW_CACHE[key] = out
    return out


def polytype(struct, sg):
    """Prototype label: AFLOW first, stoichiometry heuristic as fallback."""
    a = aflow_prototype(struct)
    if a:
        sb, mineral = a.get("strukturbericht"), a.get("mineral")
        if sb and sb in SB_ALIAS:
            return SB_ALIAS[sb]
        if mineral:
            return mineral.replace(" ", "-") + (f"-{sb}" if sb else "")
        if sb:
            return f"SB-{sb}"
        if a.get("aflow"):
            return a["aflow"]
    return polytype_heuristic(struct, sg)


def polytype_heuristic(struct, sg):
    """Heuristic prototype label from RE:TM:X stoichiometry and symmetry.
    Falls back to new-<spacegroup> for structures matching no known magnet type."""
    c = struct.composition.element_composition
    n = {el.symbol: c[el] for el in c}
    nre = sum(v for k, v in n.items() if k in HREE)
    ntm = sum(v for k, v in n.items() if k in TM)
    nx = sum(v for k, v in n.items() if k not in HREE and k not in TM)
    tag = f"new-{sg.replace('/', '_')}" if sg else "new-unknown"
    if nre == 0 or ntm == 0:
        return tag
    # These families are named by the TOTAL non-RE count per RE (the "1-12" in
    # ThMn12 counts Fe AND its stabiliser), with the stabiliser fraction
    # distinguishing sub-types. Testing TM/RE alone mislabels both ways: it
    # misses GdFe10Si2 (a real 1-12) and accepts GdHfFe12P7 (not one).
    R = (ntm + nx) / nre          # total non-RE per RE
    xr = nx / (ntm + nx)          # what fraction of that is non-magnetic
    hexlike = sg.startswith(("P6", "P-6", "R-3", "R3", "P3", "P-3"))
    close = lambda a, b: abs(a - b) < 0.06

    # 2-14-1 is R = 7.5 with a small interstitial; check before the R~7 cases
    if close(ntm / nre, 7) and close(nx / nre, 0.5):
        return "Nd2Fe14B"
    # Interstitial families (2-17-3, 1-12-N) keep the TM/RE backbone intact and
    # ADD light atoms, so the total-ratio test above would miss them.
    if nx > 0 and close(ntm / nre, 8.5) and nx / nre <= 3.5:
        return "Th2Zn17-interstitial"
    if nx > 0 and close(ntm / nre, 12) and nx / nre <= 3.0:
        return "ThMn12-interstitial"
    if close(R, 2) and xr < 0.05:
        return "Laves-C15" if sg.startswith("Fd") else ("Laves-C14" if hexlike else "Laves")
    if close(R, 3) and xr < 0.05:
        return "RT3-PuNi3"
    if close(R, 4) and close(xr, 0.5):
        return "ThCr2Si2-122"
    if close(R, 5):
        return "CaCu5" if xr < 0.05 else ("CaCu5-RT4X" if xr < 0.3 else tag)
    if close(R, 7) and xr < 0.05:
        return "RT7-TbCu7"
    if close(R, 8.5):
        if xr < 0.05:
            return "Th2Zn17" if sg.startswith("R") else "Th2Ni17"
        return "Th2Zn17-interstitial"
    if close(ntm / nre, 9) and close(nx / nre, 4):
        return "LaCo9Si4-194"
    if close(R, 12):
        # kagome 166 (RT6X6) is also R = 12, but half of it is the X net
        if close(xr, 0.5):
            return "kagome-166"
        if xr < 0.3:
            return "ThMn12" if xr < 0.05 else "ThMn12-stabilized"
    return tag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-sites", type=int, default=80,
                    help="skip structures with more atoms than this")
    ap.add_argument("--out", default=os.path.join(HERE, "compounds_campaign.json"))
    args = ap.parse_args()

    cif_by_id = {os.path.basename(p)[:-4].split("_")[-1]: p
                 for p in glob.glob(os.path.join(ROOT, "structures", "*", "*.CIF"))}

    master = os.path.join(ROOT, "all_candidates_master.csv")
    rows = []
    for r in csv.DictReader(open(master)):
        cif = next((cif_by_id[t.split(":", 1)[1]] for t in r["db_ids"].split(";")
                    if t.split(":", 1)[1] in cif_by_id), None)
        if cif:
            r["cif"] = cif
            rows.append(r)

    # Classify on the presence of a NON-Gd heavy RE, not on the presence of Gd:
    # a mixed compound like Co17GdTb must still have its Tb substituted, or the
    # calculation would carry an f-in-core RE that cannot flip.
    other_hree = set(HREE) - {"Gd"}
    native, parents = [], []
    for r in rows:
        els = set(r["elements"].split())
        if els & BANNED:
            continue
        if els & other_hree:
            parents.append(r)
        elif "Gd" in els:
            native.append(r)

    subdir = os.path.join(ROOT, "structures", "Gd_substituted")
    os.makedirs(subdir, exist_ok=True)

    entries, skipped = [], defaultdict(int)
    used_paths = set()

    def add(name, cif_rel, struct, sg, prov, kind):
        if len(struct) > args.max_sites:
            skipped["too_many_sites"] += 1
            return
        els = [el.symbol for el in struct.composition]
        missing = [e for e in els if e not in POTCAR_MAP]
        if missing:
            skipped[f"no_potcar_{'_'.join(missing)}"] += 1
            return
        tms = sorted(set(els) & TM)
        if not tms:
            skipped["no_TM"] += 1
            return
        pt = polytype(struct, sg)
        aflow = aflow_prototype(struct)
        arity = ARITY.get(len(set(els)), f"{len(set(els))}-ary")
        # distinct polymorphs can share formula + prototype label; keep both by
        # disambiguating the directory name with the space group.
        base = name
        key = (arity, prov["hree_group"], pt, name)
        if key in used_paths:
            name = f"{base}_{sg.replace('/', '_').replace(' ', '')}"
            key = (arity, prov["hree_group"], pt, name)
            n = 2
            while key in used_paths:
                name = f"{base}_v{n}"
                key = (arity, prov["hree_group"], pt, name)
                n += 1
        used_paths.add(key)
        entries.append({
            "name": name,
            "structure": cif_rel,
            "re_element": "Gd",
            "tm_elements": tms,
            "polytype": pt,
            "aflow_prototype": aflow,      # None when AFLOW has no match
            "spacegroup": sg,
            "arity_override": arity,
            "hree_group": prov["hree_group"],
            "kind": kind,
            "ldau": {"Gd": {"L": 3, "U": 6.7, "J": 0.7,
                            "ref": "Ueff=6 eV on Gd 4f (Harmon-Antropov; standard for Gd intermetallics)"}},
            "potcar_symbols": {e: POTCAR_MAP[e] for e in els},
            "magmom_init": {e: (2.5 if e == "Fe" else 1.5 if e == "Co" else 7.0 if e == "Gd" else 0.0)
                            for e in els},
            "provenance": prov,
        })

    # ---- native Gd ----
    native_formulas = set()
    for r in native:
        try:
            s = Structure.from_file(r["cif"])
        except Exception:
            skipped["unreadable_cif"] += 1
            continue
        native_formulas.add(r["formula"])
        sg = s.get_space_group_info()[0]
        add(f"{r['formula']}_nat", os.path.relpath(r["cif"], HERE), s, sg,
            {"kind": "native", "hree_group": "Gd", "sources": r["sources"],
             "db_ids": r["db_ids"], "parents": [r["formula"]],
             "e_hull_min": r["e_hull_min_eV_atom"]}, "native")

    # ---- Gd surrogates ----
    groups = defaultdict(list)
    for r in parents:
        s = None
        try:
            s = Structure.from_file(r["cif"])
        except Exception:
            skipped["unreadable_cif"] += 1
            continue
        sub = s.copy()
        sub.replace_species({el: "Gd" for el in
                             {sp.symbol for sp in sub.composition} & set(HREE)})
        f2 = canon({el.symbol: sub.composition[el] for el in sub.composition})
        sg = sub.get_space_group_info()[0]
        groups[(f2, sg)].append((r, sub))

    for (f2, sg), members in sorted(groups.items()):
        if f2 in native_formulas:
            skipped["duplicate_of_native"] += 1
            continue
        members.sort(key=lambda m: float(m[0]["e_hull_min_eV_atom"] or 9))
        rep, sub = members[0]
        # group under the rare earth the run is answering FOR - the non-Gd one in
        # a mixed compound, since the Gd part needs no surrogate
        rep_hree = (sorted(set(rep["elements"].split()) & other_hree)
                    or sorted(set(rep["elements"].split()) & set(HREE)))
        path = os.path.join(subdir, f"{f2}_from_{rep['formula']}.CIF")
        try:
            sub.to(filename=path)
        except Exception:
            skipped["cif_write_failed"] += 1
            continue
        add(f"{f2}_sub", os.path.relpath(path, HERE), sub, sg,
            {"kind": "Gd_surrogate", "hree_group": rep_hree[0],
             "substituted_from": rep["formula"],
             "parent_hree": sorted({h for m in members
                                    for h in set(m[0]["elements"].split()) & set(HREE)}),
             "parents": [m[0]["formula"] for m in members],
             "parent_db_ids": [m[0]["db_ids"] for m in members],
             "sources": rep["sources"], "e_hull_min": rep["e_hull_min_eV_atom"],
             "note": "all heavy-RE sites replaced by Gd; transfer coupling to parents "
                     "by de Gennes scaling (g_J-1)J"},
            "Gd_surrogate")

    reg = {
        "defaults": {"encut": 520, "kppa": 8000, "mode": "static",
                     "potcar_symbols": POTCAR_MAP,
                     "magmom_init": {"Fe": 2.5, "Co": 1.5, "Gd": 7.0, "default": 0.0},
                     "incar_overrides": {}},
        "compounds": entries,
    }
    json.dump(reg, open(args.out, "w"), indent=1)

    from collections import Counter
    print(f"compounds: {len(entries)}  ->  {2*len(entries)} calculations")
    print("  by kind:  ", dict(Counter(e["kind"] for e in entries)))
    print("  by HREE:  ", dict(Counter(e["hree_group"] for e in entries)))
    print("  by arity: ", dict(Counter(e["arity_override"] for e in entries)))
    top = Counter(e["polytype"] for e in entries).most_common(12)
    print("  polytypes:", top)
    print("  skipped:  ", dict(skipped))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
