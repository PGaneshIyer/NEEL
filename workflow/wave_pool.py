#!/usr/bin/env python3
"""Build the candidate pool the GP chooses waves from.

Sources (all substituted to a LIGHT rare earth, Nd and Sm by default, because
the wave label is one f-in-core relaxation per cell):
  master     every formula in all_candidates_master.csv that now has a CIF
             (including the structures recovered by recover_structures.py)
  generated  structures/generated/*.CIF (slide-24 prototype decorations)
  hosts      the strongest-coupling Gd hosts of the campaign (J_eff >= 0.5 or
             gap >= 250 meV) with the data-backed levers applied: light RE, and
             a partial-Co variant (one in eight Fe -> Co, the Fe sites closest
             to the RE first)
Each candidate is: relaxed with MACE-MP-0 (cell + positions), placed on the
same-model MP hull, and described with wave_features.py. Output:
  analysis/pool/pool.csv            one row per candidate (features, E_hull, Ms_proj)
  runs-pool/<cid>/POSCAR_mace       the relaxed cell the wave inputs start from
Everything is cached; re-running only processes new candidates.

Needs the MACE venv:  /Users/g5q/Documents/GitHub/siteseer/.venv/bin/python wave_pool.py
  [--re Nd,Sm] [--sources master,recovered,generated,hosts]   (recovered = only the structures recover_structures.py fetched) [--max-atoms 40] [--limit N] [--hull-max 0.03]
"""
import argparse
import csv
import glob
import hashlib
import json
import os
import re
import sys
import time
import warnings

warnings.filterwarnings("ignore")
import numpy as np
from pymatgen.core import Structure, Composition
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import wave_features as WF
import light_re_hull as LH

POOL_DIR = os.path.join(HERE, "runs-pool")
OUT = os.path.join(HERE, "analysis", "pool")
HEAVY = {"Gd", "Tb", "Dy", "Ho", "Er", "Tm"}
GJJ = {"Nd": 3.27, "Sm": 0.71, "Pr": 3.20}
C_T = 9.274e-24 * 4 * 3.14159e-7 / 1e-30
M_TM = {"Fe": 2.15, "Co": 1.45, "Mn": 2.5, "Ni": 0.5}      # campaign medians, used only for the Ms projection


def cid_of(struct, tag):
    key = tag + "|" + struct.composition.reduced_formula + "|" + str(len(struct)) + "|" + "%.3f" % struct.volume
    return hashlib.md5(key.encode()).hexdigest()[:10]


def substitute_light(struct, re_el):
    s = struct.copy()
    heavy = [sp.symbol for sp in s.species if sp.symbol in HEAVY]
    if not heavy:
        # already a light-RE cell (interstitial generator output): keep only the matching RE
        return s if any(sp.symbol == re_el for sp in s.species) else None
    s.replace_species({h: re_el for h in set(heavy)})
    return s


def partial_co(struct, re_el, frac=1 / 8):
    """Replace round(n_Fe*frac) Fe by Co, choosing the Fe closest to the RE."""
    s = struct.copy()
    fe = [i for i, sp in enumerate(s.species) if sp.symbol == "Fe"]
    k = int(round(len(fe) * frac))
    if k == 0 or any(sp.symbol == "Co" for sp in s.species):
        return None
    re_idx = [i for i, sp in enumerate(s.species) if sp.symbol == re_el]
    dist = {i: min(s.get_distance(i, j) for j in re_idx) for i in fe}
    for i in sorted(fe, key=lambda i: dist[i])[:k]:
        s.replace(i, "Co")
    return s


def collect(sources, res_light, max_atoms):
    cands = []   # (tag, source, parent, structure)
    if "master" in sources or "recovered" in sources:
        for r in csv.DictReader(open(os.path.join(ROOT, "all_candidates_master.csv"))):
            if not r["cif_path"]:
                continue
            # "recovered" = structures fetched from MP/OQMD by recover_structures.py (the
            # GNoME/Alexandria originals were all staged in the Gd campaign already)
            if "master" not in sources and not r["cif_path"].startswith(("structures/MP/", "structures/OQMD/")):
                continue
            p = os.path.join(ROOT, r["cif_path"])
            if not os.path.isfile(p):
                continue
            try:
                s0 = Structure.from_file(p)
            except Exception:
                continue
            if len(s0) > max_atoms:
                continue
            for re_ in res_light:
                s = substitute_light(s0, re_)
                if s is not None:
                    cands.append((f"master:{r['formula']}:{re_}", "master", r["formula"], s))
    if sources & {"generated", "kagome", "interstitial", "mixed"} if isinstance(sources, set) else any(x in sources for x in ("generated", "kagome", "interstitial", "mixed")):
        pats = []
        if "generated" in sources: pats.append(os.path.join(ROOT, "structures", "generated", "*.CIF"))
        if "kagome" in sources: pats.append(os.path.join(ROOT, "structures", "generated_kagome", "*.CIF"))
        if "interstitial" in sources: pats.append(os.path.join(ROOT, "structures", "generated_interstitial", "*.CIF"))
        if "mixed" in sources: pats.append(os.path.join(ROOT, "structures", "generated_mixed", "*.CIF"))
        for p in sorted(q for pat in pats for q in glob.glob(pat)):
            try:
                s0 = Structure.from_file(p)
            except Exception:
                continue
            if len(s0) > max_atoms:
                continue
            for re_ in res_light:
                s = substitute_light(s0, re_)
                if s is not None:
                    src = "kagome" if "generated_kagome" in p else ("interstitial" if "generated_interstitial" in p else ("mixed" if "generated_mixed" in p else "generated"))
                    cands.append((f"gen:{os.path.basename(p)}:{re_}", src, os.path.basename(p), s))
    if "hosts" in sources or "credible" in sources or "campaign" in sources:
        # hosts     strongest-coupling credible Gd hosts (J_eff >= 0.5 or gap >= 250 meV)
        # credible  every credible Gd host, weak couplers included (the GP decides)
        # campaign  campaign compounds WITHOUT a credible fm/ferri label: their structures are
        #           database-relaxed and fine as hosts; the f-in-core run has no +U and tends
        #           to converge where the Gd pair did not
        feats = {r["compound"]: r for r in csv.DictReader(open(os.path.join(HERE, "analysis", "exchange_features.csv")))}
        res = json.load(open(os.path.join(HERE, "results.json")))
        for rel, rec in res.items():
            name = rel.split("/")[-1]
            f = feats.get(name)
            cred = bool(rec.get("credible"))
            strong = cred and f and (float(f["J_eff"]) >= 0.5 or abs(float(f["dE_per_RE_meV"])) >= 250)
            take = ("hosts" in sources and strong) or ("credible" in sources and cred) or ("campaign" in sources and not cred)
            if not take:
                continue
            p = os.path.join(HERE, "runs", rel, "ferri", "CONTCAR")
            if not os.path.isfile(p) or os.path.getsize(p) == 0:
                p = os.path.join(HERE, "runs", rel, "ferri", "POSCAR")
            try:
                s0 = Structure.from_file(p)
            except Exception:
                continue
            if len(s0) > max_atoms:
                continue
            src = "hosts" if strong else ("credible" if cred else "campaign")
            for re_ in res_light:
                s = substitute_light(s0, re_)
                if s is None:
                    continue
                cands.append((f"host:{name}:{re_}", src, name, s))
                if strong or "expand" in sources:
                    sc = partial_co(s, re_)
                    if sc is not None:
                        cands.append((f"host:{name}:{re_}:Co", src + "+Co", name, sc))
    if "expand" in sources:
        # neighbourhood of the best labelled / best predicted candidates so far: the levers the
        # data support, applied locally.  Reads labels.csv (measured h) if present, else the
        # latest wave_<k>.csv (predicted), takes the top EXPAND_TOP by Ms x min(1, gap/100).
        import glob as _g
        rows = []
        lab = os.path.join(OUT, "labels.csv")
        if os.path.isfile(lab):
            for r in csv.DictReader(open(lab)):
                if r.get("h") and r.get("cid"):
                    gap = 1574 * float(r["h"]) * {"Nd": 1.227, "Sm": 1.786, "Pr": 0.8}.get(r["re_el"], 1) / 3.5
                    rows.append((float(r["mu0Ms_T"]) * min(1, gap / 100), r["cid"]))
        else:
            waves = sorted(_g.glob(os.path.join(OUT, "wave_*.csv")))
            if waves:
                for r in csv.DictReader(open(waves[-1])):
                    rows.append((float(r["Ms_proj_T"]) * min(1, float(r["gap_pred_meV"]) / 100), r["cid"]))
        rows.sort(reverse=True)
        pool_rows = {r["cid"]: r for r in csv.DictReader(open(os.path.join(OUT, "pool.csv")))} if os.path.isfile(os.path.join(OUT, "pool.csv")) else {}
        for _, cid in rows[:int(os.environ.get("EXPAND_TOP", 25))]:
            pr = pool_rows.get(cid)
            if not pr or not os.path.isfile(os.path.join(HERE, pr["poscar"])):
                continue
            s0 = Structure.from_file(os.path.join(HERE, pr["poscar"]))
            re0 = pr["re_el"]
            for re_ in ("Nd", "Sm", "Pr"):                       # RE swap
                s = s0.copy(); s.replace_species({re0: re_})
                if re_ != re0:
                    cands.append((f"expand:{cid}:{re_}", "expand", pr["formula"], s))
                for frac in (1 / 8, 2 / 8):                      # partial Co, two levels
                    sc = partial_co(s, re_, frac)
                    if sc is not None:
                        cands.append((f"expand:{cid}:{re_}:Co{int(frac*8)}", "expand", pr["formula"], sc))
                for et in ("Ti", "V", "Zr", "Nb"):               # one early-TM on the Fe site farthest from the RE
                    se = s.copy()
                    fe = [i for i, sp in enumerate(se.species) if sp.symbol == "Fe"]
                    rei = [i for i, sp in enumerate(se.species) if sp.symbol == re_]
                    if fe and rei:
                        far = max(fe, key=lambda i: min(se.get_distance(i, j) for j in rei))
                        se.replace(far, et)
                        cands.append((f"expand:{cid}:{re_}:{et}", "expand", pr["formula"], se))
    # dedupe on reduced formula + space group
    seen, out = set(), []
    for tag, src, parent, s in cands:
        try:
            sg = SpacegroupAnalyzer(s, symprec=0.1).get_space_group_number()
        except Exception:
            sg = 0
        key = (s.composition.reduced_formula, sg)
        if key in seen:
            continue
        seen.add(key); out.append((tag, src, parent, s, sg))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--re", default="Nd,Sm")
    ap.add_argument("--sources", default="recovered,generated,kagome,interstitial,mixed,hosts,credible,campaign", help="also: expand (neighbourhood of the best labelled/predicted candidates; EXPAND_TOP env)")
    ap.add_argument("--max-atoms", type=int, default=40)
    ap.add_argument("--limit", type=int, default=0, help="process at most N new candidates this call")
    ap.add_argument("--fmax", type=float, default=0.1, help="screening tolerance; VASP re-relaxes anyway")
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--no-hull", action="store_true", help="skip the MP competitor hull (features + relax only)")
    A = ap.parse_args()
    res_light = A.re.split(","); sources = A.sources.split(",")
    os.makedirs(OUT, exist_ok=True); os.makedirs(POOL_DIR, exist_ok=True)
    pool_csv = os.path.join(OUT, "pool.csv")
    done = {r["cid"]: r for r in csv.DictReader(open(pool_csv))} if os.path.isfile(pool_csv) else {}

    cands = collect(sources, res_light, A.max_atoms)
    new = [(cid_of(s, tag), tag, src, parent, s, sg) for tag, src, parent, s, sg in cands]
    new = [c for c in new if c[0] not in done]
    print(f"pool: {len(cands)} unique candidates, {len(done)} already processed, {len(new)} new")
    if A.limit:
        new = new[:A.limit]
    if not new:
        print("nothing to do"); return
    calc = LH.make_calc()
    rows = list(done.values())
    t0 = time.time()
    for k, (cid, tag, src, parent, s, sg) in enumerate(new):
        from pymatgen.io.ase import AseAtomsAdaptor
        from ase.io import write
        a = AseAtomsAdaptor.get_atoms(s)
        try:
            e, fmax, nst = LH.relax(a, calc, A.fmax, A.steps)
        except Exception as ex:
            print(f"  relax failed {tag}: {ex}"); continue
        d = os.path.join(POOL_DIR, cid); os.makedirs(d, exist_ok=True)
        write(os.path.join(d, "POSCAR_mace"), a, format="vasp")
        sr = AseAtomsAdaptor.get_structure(a)
        re_el = next(x for x in res_light if x in [sp.symbol for sp in sr.species])
        f = WF.features(sr, re_el)
        if f is None:
            continue
        n_tm = f["n_TM"]; m_tm = sum(M_TM.get(sp.symbol, 0) for sp in sr.species if sp.symbol in WF.TM)
        ms = (m_tm + f["n_RE"] * GJJ[re_el]) / sr.volume * C_T
        row = {"cid": cid, "tag": tag, "source": src, "parent": parent, "formula": sr.composition.reduced_formula,
               "spacegroup": sg, "E_mace_eV": e, "fmax": fmax, "V_A3": sr.volume, "Ms_proj_T": round(ms, 3),
               "E_hull_meV": "", "poscar": os.path.relpath(os.path.join(d, "POSCAR_mace"), HERE)}
        row.update({k2: (round(v, 4) if isinstance(v, float) else v) for k2, v in f.items()})
        rows.append(row)
        json.dump(row, open(os.path.join(d, "meta.json"), "w"), indent=1)
        if k % 10 == 0:
            print(f"  {k}/{len(new)}  {tag:<40} Ms={ms:.2f} T  {time.time()-t0:.0f}s", flush=True)
            write_pool(pool_csv, rows)
    write_pool(pool_csv, rows)
    if not A.no_hull:
        hull_stage(rows, pool_csv, calc, A.fmax)
    print(f"pool written: {pool_csv} ({len(rows)} rows)")


def write_pool(path, rows):
    keys = ["cid", "tag", "source", "parent", "formula", "spacegroup", "re_el", "n_RE", "n_TM", "natoms", "E_mace_eV", "fmax", "V_A3",
            "Ms_proj_T", "E_hull_meV", "poscar"] + WF.FEATURES
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def hull_stage(rows, pool_csv, calc, fmax):
    """Same-model hull: MP competitors re-evaluated with MACE (cached in analysis/light_re)."""
    from itertools import combinations
    from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
    from pymatgen.io.ase import AseAtomsAdaptor
    todo = [r for r in rows if r["E_hull_meV"] in ("", None)]
    if not todo:
        return
    systems = set()
    for r in todo:
        els = sorted(set(re.findall(r"[A-Z][a-z]?", r["formula"])))
        for k in range(1, len(els) + 1):
            for sub in combinations(els, k):
                systems.add("-".join(sub))
    store = LH.fetch_competitors(sorted(systems))
    ccache = os.path.join(LH.OUT, "mp_mace_energies.json")
    CE = json.load(open(ccache)) if os.path.isfile(ccache) else {}
    need = {e["id"]: e for c in store.values() for e in c if e["id"] not in CE}
    print(f"hull: {len(need)} new MP competitors to evaluate")
    for i, (mid, e) in enumerate(need.items()):
        s = Structure.from_dict(e["structure"])
        if len(s) > 120:
            continue
        a = AseAtomsAdaptor.get_atoms(s)
        try:
            en, f, n = LH.relax(a, calc, max(fmax, 0.1), 300)
        except Exception:
            continue
        CE[mid] = {"E_eV": en, "natoms": len(a), "formula": e["formula"], "composition": a.get_chemical_formula()}
        if i % 20 == 0:
            json.dump(CE, open(ccache, "w")); print(f"  {i}/{len(need)}", flush=True)
    json.dump(CE, open(ccache, "w"))
    for r in todo:
        els = set(re.findall(r"[A-Z][a-z]?", r["formula"]))
        entries = [PDEntry(Composition(CE[e["id"]]["composition"]), CE[e["id"]]["E_eV"], name=e["formula"])
                   for c, lst in store.items() if set(c.split("-")) <= els for e in lst if e["id"] in CE]
        if not entries:
            continue
        try:
            pd = PhaseDiagram(entries)
            me = PDEntry(Composition(r["formula"]) * 1, float(r["E_mace_eV"]) / int(r["natoms"]) * Composition(r["formula"]).num_atoms, name=r["cid"])
            _, eh = pd.get_decomp_and_e_above_hull(me, allow_negative=True)
            r["E_hull_meV"] = round(1000 * eh, 1)
        except Exception as ex:
            r["E_hull_meV"] = ""
    write_pool(pool_csv, rows)


if __name__ == "__main__":
    main()
