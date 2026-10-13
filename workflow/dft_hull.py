#!/usr/bin/env python3
"""DFT convex hull for the light-RE finalists, Materials-Project compatible.

--make   one static per relaxed run (runs/light|wave*/.../relax) at the relaxed
         geometry, with MP-compatible settings for intermetallics: PBE, ENCUT 520,
         no +U (MP applies U only to oxides/fluorides), the same PAW set MP uses
         (Fe_pv, Co, Nd_3, Sm_3, Y_sv, Zr_sv, V_pv, Lu_3 ...), ISMEAR=-5 for the
         final energy. Written to <rundir>/../hull/ ; manifest batch/dft_hull_runs.txt
--fit    fetch MP GGA/GGA+U entries (energy_per_atom) for every sub-system, build a
         pymatgen PhaseDiagram with our DFT energies added, report E_hull and the
         decomposition. For intermetallics the MP2020 corrections are zero, so the
         energies are directly comparable.
         --mu-N <eV>  also report the N-open grand-potential hull with the nitrogen
         chemical potential raised by <eV> above N2/2 (reactive-nitrogen synthesis,
         Sun 2017); default 0 = N2 reference.
Needs the MP key (workflow/.mp_api_key or $MP_API_KEY) for --fit.
"""
import argparse
import csv
import json
import os
import re
import shutil
import time

import requests
from pymatgen.core import Structure, Composition
from pymatgen.io.vasp import Kpoints

HERE = os.path.dirname(os.path.abspath(__file__))
MP = "https://api.materialsproject.org/materials/summary/"
TM = {"Fe", "Co", "Mn", "Ni"}


def key():
    p = os.path.join(HERE, ".mp_api_key")
    k = os.environ.get("MP_API_KEY") or (open(p).read().strip() if os.path.isfile(p) else "")
    if not k:
        raise SystemExit("no MP key")
    return k


def make(rd, out):
    rd = rd.rstrip("/")
    geom = os.path.join(rd, "CONTCAR") if os.path.getsize(os.path.join(rd, "CONTCAR")) > 0 else os.path.join(rd, "POSCAR")
    s = Structure.from_file(geom)
    d = os.path.normpath(os.path.join(rd, "..", "hull"))
    os.makedirs(d, exist_ok=True)
    s.to(filename=os.path.join(d, "POSCAR"), fmt="poscar")
    shutil.copy(os.path.join(rd, "POTCAR"), d)
    Kpoints.automatic_density(s, 8000).write_file(os.path.join(d, "KPOINTS"))
    inc = [l for l in open(os.path.join(rd, "INCAR")).read().splitlines()
           if l.split("=")[0].strip() not in ("IBRION", "ISIF", "NSW", "EDIFFG", "POTIM", "ISMEAR", "SIGMA", "SYSTEM", "MAGMOM", "LORBIT")]
    species = [sp.symbol for sp in s.species]
    mm = " ".join("2.50" if e in TM else "0.00" for e in species)
    inc += [f"SYSTEM = {os.path.basename(os.path.dirname(d))} DFT hull static (MP-compatible)",
            "IBRION = -1", "NSW = 0", "ISMEAR = -5", f"MAGMOM = {mm}", "LORBIT = 11"]
    open(os.path.join(d, "INCAR"), "w").write("\n".join(inc) + "\n")
    out.append(os.path.relpath(d, HERE))


def mp_entries(chemsys_list):
    cache = os.path.join(HERE, "analysis", "light_re", "mp_gga_entries.json")
    store = json.load(open(cache)) if os.path.isfile(cache) else {}
    k = key()
    for c in chemsys_list:
        if c in store:
            continue
        for t in range(3):
            r = requests.get(MP, headers={"X-API-KEY": k}, params={"chemsys": c, "_fields": "material_id,formula_pretty,energy_per_atom,nsites,composition,energy_above_hull,theoretical", "_limit": 1000}, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(5)
        store[c] = [{"id": d["material_id"], "formula": d["formula_pretty"], "epa": d["energy_per_atom"], "comp": d["composition"], "ehull": d["energy_above_hull"], "theoretical": d.get("theoretical")} for d in r.json()["data"] if d.get("energy_per_atom") is not None]
        json.dump(store, open(cache, "w"))
    return store


def final_energy(outcar):
    t = open(outcar, errors="replace").read()
    e = re.findall(r"free  energy\s+TOTEN\s*=\s*(-?\d+\.\d+)", t)
    return (float(e[-1]) if e else None), ("General timing and accounting" in t)


def fit(dirs, mu_n):
    from itertools import combinations
    from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry, GrandPotentialPhaseDiagram
    from pymatgen.core import Element
    rows = []
    ours = []
    for rd in dirs:
        d = os.path.normpath(os.path.join(rd.rstrip("/"), "..", "hull"))
        oc = os.path.join(d, "OUTCAR")
        if not os.path.isfile(oc):
            continue
        e, done = final_energy(oc)
        if e is None or not done:
            continue
        s = Structure.from_file(os.path.join(d, "POSCAR"))
        ours.append((os.path.basename(os.path.dirname(d)), s.composition, e))
    systems = set()
    for _, comp, _ in ours:
        els = sorted(el.symbol for el in comp.elements)
        for k in range(1, len(els) + 1):
            for sub in combinations(els, k):
                systems.add("-".join(sub))
    store = mp_entries(sorted(systems))
    for name, comp, e in ours:
        els = {el.symbol for el in comp.elements}
        entries = [PDEntry(Composition(d["comp"]), d["epa"] * Composition(d["comp"]).num_atoms, name=d["formula"])
                   for c, lst in store.items() if set(c.split("-")) <= els for d in lst]
        me = PDEntry(comp, e, name=name)
        pd = PhaseDiagram(entries)
        decomp, eh = pd.get_decomp_and_e_above_hull(me, allow_negative=True)
        row = {"compound": name, "formula": comp.reduced_formula, "E_hull_DFT_meV": round(1000 * eh, 1),
               "decomposition": " + ".join(f"{v:.2f} {k.name}" for k, v in sorted(decomp.items(), key=lambda kv: -kv[1]))}
        if "N" in els and mu_n:
            n2 = min(d["epa"] for d in store.get("N", []))          # N2 reference per atom
            gpd = GrandPotentialPhaseDiagram(entries + [me], {Element("N"): n2 + mu_n})
            # stability under open N: is our entry on the grand-potential hull?
            stable = any(ent.original_entry.name == name for ent in gpd.stable_entries)
            row["stable_at_muN"] = stable; row["mu_N_shift_eV"] = mu_n
        rows.append(row)
        print(f"{name:<22} E_hull(DFT) = {1000*eh:7.1f} meV/atom   -> {row['decomposition']}" + (f"   open-N (+{mu_n} eV): {'STABLE' if row.get('stable_at_muN') else 'unstable'}" if 'stable_at_muN' in row else ""))
    os.makedirs(os.path.join(HERE, "analysis", "light_re"), exist_ok=True)
    with open(os.path.join(HERE, "analysis", "light_re", "dft_hull.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["compound", "formula", "E_hull_DFT_meV", "decomposition", "stable_at_muN", "mu_N_shift_eV"], extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print("wrote analysis/light_re/dft_hull.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make", nargs="*", default=[])
    ap.add_argument("--fit", nargs="*", default=[])
    ap.add_argument("--mu-N", type=float, default=0.0)
    ap.add_argument("--out", default=os.path.join(HERE, "batch", "dft_hull_runs.txt"))
    A = ap.parse_args()
    made = []
    for rd in A.make:
        make(rd, made)
    if made:
        open(A.out, "w").write("\n".join(made) + "\n"); print(f"{len(made)} hull statics -> {os.path.relpath(A.out, HERE)}")
    if A.fit:
        fit(A.fit, A.mu_N)


if __name__ == "__main__":
    main()
