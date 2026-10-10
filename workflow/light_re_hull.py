#!/usr/bin/env python3
"""Light-RE substitution + machine-learned convex-hull screen.

For each strongly-coupled Fe-rich host from the Gd campaign, replace Gd by Nd
and by Sm (other REs such as Y/Lu stay), relax every structure - parent Gd
included - with MACE-MP-0 (medium), and place it on a convex hull built from
Materials Project competing phases that are RE-EVALUATED WITH THE SAME MODEL,
so the hull is internally consistent (no DFT/MLIP energy mixing).

Stages (each caches to analysis/light_re/):
  gen    write POSCARs runs-light/<host>/<RE>/POSCAR from the ferri CONTCAR
  relax  MACE relaxation (cell + positions), energies -> mace_energies.json
  hull   fetch MP entries for every chemical system, MACE-evaluate them,
         pymatgen PhaseDiagram, e_above_hull per structure -> hull.csv
  all    the three in sequence

Needs the siteseer venv (torch + mace + ase + pymatgen + mp-api) and the MP
key in workflow/.mp_api_key or $MP_API_KEY.

Usage:  /Users/g5q/Documents/GitHub/siteseer/.venv/bin/python light_re_hull.py all [--fmax 0.05] [--hosts A,B]
"""
import argparse
import csv
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "analysis", "light_re")
LIGHT = os.path.join(HERE, "runs-light")
RES = json.load(open(os.path.join(HERE, "results.json")))

# host -> run (relative to runs/); Nd projection >= 1.4 T, new prototypes, credible
HOSTS = {
    # Fe-rich new hosts, Nd >= 1.6 T
    "Fe11GdW_nat": "ternary/Gd/new-Imm2/Fe11GdW_nat",
    "Fe5GdSi_nat": "ternary/Gd/new-Immm/Fe5GdSi_nat",
    "BFe4Gd_nat": "ternary/Gd/CaCu5-RT4X/BFe4Gd_nat",
    "Al2Fe10Gd_sub": "ternary/Er/new-Immm/Al2Fe10Gd_sub",
    "AlC3Fe16Gd2_sub": "quaternary/Ho/new-C2_m/AlC3Fe16Gd2_sub",
    "Fe10GdY_sub": "ternary/Tb/new-Pmmm/Fe10GdY_sub",
    "AlB2Fe12Gd3_sub": "quaternary/Tb/CaCu5-RT4X/AlB2Fe12Gd3_sub",
    "Fe5GdV_nat": "ternary/Gd/new-Immm/Fe5GdV_nat",
    "CoFe13Gd3Y_sub": "quaternary/Er/new-R3m/CoFe13Gd3Y_sub",
    # RE-rich controls
    "Co7Fe16Gd6_sub": "ternary/Tm/new-Fm-3m/Co7Fe16Gd6_sub",
    "Co2Fe7Gd3_sub": "ternary/Er/RT3-PuNi3/Co2Fe7Gd3_sub",
    "CoFe3Gd2_nat": "ternary/Gd/Laves-C14/CoFe3Gd2_nat",
    "Al3Fe20Gd6_sub": "ternary/Tm/new-R3m/Al3Fe20Gd6_sub",
    "Co9Fe5Gd4_sub": "ternary/Er/new-R-3m/Co9Fe5Gd4_sub",
    "Co17Fe6Gd6_sub": "ternary/Tm/new-Immm/Co17Fe6Gd6_sub",
    "Fe9Gd2Zr_sub": "ternary/Tb/new-R3m/Fe9Gd2Zr_sub",
    "Fe9Gd2Sc_sub": "ternary/Dy/new-R3m/Fe9Gd2Sc_sub",
    # strong-coupling Fe/Y hosts, 1.4-1.6 T
    "CoFe6GdY_sub": "quaternary/Tb/new-Cm/CoFe6GdY_sub",
    "Co19Fe4Gd6_sub": "ternary/Dy/new-C2_m/Co19Fe4Gd6_sub",
    "CoFe13Gd2Y2_sub": "quaternary/Tm/new-R-3m/CoFe13Gd2Y2_sub",
    "Fe7GdY_sub": "ternary/Er/new-R-3m/Fe7GdY_sub",
    "Fe9Gd2Y_sub": "ternary/Ho/new-R-3m/Fe9Gd2Y_sub",
    "Co2Fe12GdY3_sub": "quaternary/Tb/new-Cm/Co2Fe12GdY3_sub",
    "Fe18Gd2LuY3_sub": "quaternary/Tm/new-P3m1/Fe18Gd2LuY3_sub",
    "CoFe13GdY3_sub": "quaternary/Er/new-R3m/CoFe13GdY3_sub",
    "Fe14GdY3_sub": "ternary/Er/new-R3m/Fe14GdY3_sub",
    # 1:9 R3m family representatives
    "Fe9GdTiZr_sub": "quaternary/Dy/new-R3m/Fe9GdTiZr_sub",
    "Fe9GdScTi_sub": "quaternary/Tb/new-R3m/Fe9GdScTi_sub",
    "Fe9GdLuZr_sub": "quaternary/Ho/new-R3m/Fe9GdLuZr_sub",
}
RES_LIGHT = ["Gd", "Nd", "Sm"]          # Gd = parent, the calibration point
# initial moments for the MACE run are irrelevant (non-magnetic model), but the
# projection table needs these: light RE gJ*J parallel to TM, Gd 7 antiparallel
GJJ = {"Nd": 3.27, "Sm": 0.71}


def mp_key():
    k = os.environ.get("MP_API_KEY")
    if not k and os.path.isfile(os.path.join(HERE, ".mp_api_key")):
        k = open(os.path.join(HERE, ".mp_api_key")).read().strip()
    if not k:
        sys.exit("no MP key: set MP_API_KEY or write workflow/.mp_api_key")
    return k


# ---------------------------------------------------------------- gen
def stage_gen(hosts):
    from pymatgen.core import Structure
    n = 0
    for h in hosts:
        src = os.path.join(HERE, "runs", HOSTS[h], "ferri", "CONTCAR")
        s0 = Structure.from_file(src)
        for re_ in RES_LIGHT:
            s = s0.copy()
            if re_ != "Gd":
                s.replace_species({"Gd": re_})
            d = os.path.join(LIGHT, h, re_)
            os.makedirs(d, exist_ok=True)
            s.to(filename=os.path.join(d, "POSCAR"), fmt="poscar")
            n += 1
    print(f"gen: wrote {n} POSCARs under runs-light/")


# ---------------------------------------------------------------- relax
def make_calc():
    from mace.calculators import mace_mp
    # MPS cannot load the float64 checkpoint; cpu/float64 is fast enough for <=30-atom cells
    return mace_mp(model="medium", device="cpu", default_dtype="float64")


def relax(atoms, calc, fmax, steps, cell=True):
    from ase.filters import FrechetCellFilter
    from ase.optimize import FIRE
    atoms.calc = calc
    target = FrechetCellFilter(atoms) if cell else atoms
    opt = FIRE(target, logfile=None)
    opt.run(fmax=fmax, steps=steps)
    f = abs(atoms.get_forces()).max()
    return atoms.get_potential_energy(), f, opt.nsteps


def stage_relax(hosts, fmax, steps):
    from ase.io import read, write
    os.makedirs(OUT, exist_ok=True)
    cache = os.path.join(OUT, "mace_energies.json")
    E = json.load(open(cache)) if os.path.isfile(cache) else {}
    calc = make_calc()
    t0 = time.time()
    for h in hosts:
        for re_ in RES_LIGHT:
            key = f"{h}/{re_}"
            d = os.path.join(LIGHT, h, re_)
            if key in E and os.path.isfile(os.path.join(d, "CONTCAR_mace")):
                continue
            a = read(os.path.join(d, "POSCAR"))
            v0 = a.get_volume()
            e, f, n = relax(a, calc, fmax, steps)
            write(os.path.join(d, "CONTCAR_mace"), a, format="vasp")
            E[key] = {"E_eV": e, "natoms": len(a), "fmax": f, "steps": n,
                      "V0_A3": v0, "V_A3": a.get_volume(), "formula": a.get_chemical_formula()}
            json.dump(E, open(cache, "w"), indent=1)
            print(f"  {key:<24} E={e:10.3f} eV  dV={100*(a.get_volume()/v0-1):+5.1f}%  fmax={f:.3f}  steps={n}", flush=True)
    print(f"relax: {len(E)} structures, {time.time()-t0:.0f} s")


# ---------------------------------------------------------------- hull
def fetch_competitors(chemsys_list):
    """MP near-hull entries (<=100 meV/atom) for each chemsys via the REST API
    (mp_api's client does not import on this py3.10 venv); cached."""
    import requests
    cache = os.path.join(OUT, "mp_entries.json")
    store = json.load(open(cache)) if os.path.isfile(cache) else {}
    need = [c for c in chemsys_list if c not in store]
    hdr = {"X-API-KEY": mp_key()}
    for c in need:
        url = ("https://api.materialsproject.org/materials/summary/?chemsys=" + c +
               "&energy_above_hull_max=0.1&_limit=500&_fields=material_id,formula_pretty,structure,energy_above_hull")
        for attempt in range(3):
            r = requests.get(url, headers=hdr, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(5)
        r.raise_for_status()
        docs = r.json()["data"]
        store[c] = [{"id": d["material_id"], "formula": d["formula_pretty"], "structure": d["structure"],
                     "mp_ehull": d["energy_above_hull"]} for d in docs]
        print(f"  MP {c}: {len(store[c])} entries", flush=True)
        json.dump(store, open(cache, "w"))
    return store


def stage_hull(hosts, fmax, steps):
    from itertools import combinations
    from ase.io import read
    from pymatgen.core import Structure, Composition
    from pymatgen.io.ase import AseAtomsAdaptor
    from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
    E = json.load(open(os.path.join(OUT, "mace_energies.json")))
    # all chemical systems (full system per structure, MP search is inclusive of subsystems)
    systems = set()
    for h in hosts:
        for re_ in RES_LIGHT:
            els = sorted(set(read(os.path.join(LIGHT, h, re_, "POSCAR")).get_chemical_symbols()))
            for k in range(1, len(els) + 1):          # every sub-system: elements, binaries, ...
                for sub in combinations(els, k):
                    systems.add("-".join(sub))
    store = fetch_competitors(sorted(systems))

    # MACE-evaluate every distinct MP structure once (relax positions+cell, loose fmax)
    ccache = os.path.join(OUT, "mp_mace_energies.json")
    CE = json.load(open(ccache)) if os.path.isfile(ccache) else {}
    calc = make_calc()
    todo = {e["id"]: e for c in store.values() for e in c if e["id"] not in CE}
    print(f"hull: {len(todo)} MP competitor structures to evaluate with MACE")
    for i, (mid, e) in enumerate(todo.items()):
        s = Structure.from_dict(e["structure"])
        if len(s) > 120:                    # skip giant cells; MP already says they are rarely on the hull
            continue
        a = AseAtomsAdaptor.get_atoms(s)
        en, f, n = relax(a, calc, max(fmax, 0.1), steps)
        CE[mid] = {"E_eV": en, "natoms": len(a), "formula": e["formula"], "composition": a.get_chemical_formula()}
        if i % 10 == 0:
            json.dump(CE, open(ccache, "w")); print(f"  {i}/{len(todo)}", flush=True)
    json.dump(CE, open(ccache, "w"))

    # elemental references: lowest MACE energy among MP elemental entries
    rows = []
    for h in hosts:
        for re_ in RES_LIGHT:
            key = f"{h}/{re_}"
            a = read(os.path.join(LIGHT, h, re_, "POSCAR"))
            els = sorted(set(a.get_chemical_symbols())); sysname = "-".join(els)
            entries = []
            for c, lst in store.items():
                if set(c.split("-")) <= set(els):
                    for e in lst:
                        if e["id"] in CE:
                            entries.append(PDEntry(Composition(CE[e["id"]]["composition"]), CE[e["id"]]["E_eV"], name=e["formula"]))
            if not entries:
                continue
            pd = PhaseDiagram(entries)
            me = PDEntry(Composition(E[key]["formula"]), E[key]["E_eV"], name=key)
            decomp, ehull = pd.get_decomp_and_e_above_hull(me, allow_negative=True)   # negative = below the MP hull
            eform = pd.get_form_energy_per_atom(me)
            dstr = " + ".join(f"{v:.2f} {k.name}" for k, v in sorted(decomp.items(), key=lambda kv: -kv[1]))
            rows.append({"host": h, "RE": re_, "formula": E[key]["formula"], "chemsys": sysname,
                         "E_form_eV_atom": round(eform, 4), "E_hull_eV_atom": round(ehull, 4),
                         "dV_percent": round(100 * (E[key]["V_A3"] / E[key]["V0_A3"] - 1), 1),
                         "decomposition": dstr})
            print(f"  {key:<24} Ef={eform:+7.3f}  Ehull={ehull*1000:6.0f} meV/at  dV={rows[-1]['dV_percent']:+5.1f}%  -> {dstr}")
    with open(os.path.join(OUT, "hull.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"hull: wrote analysis/light_re/hull.csv ({len(rows)} rows)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["gen", "relax", "hull", "all"])
    ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--hosts", default="")
    A = ap.parse_args()
    hosts = A.hosts.split(",") if A.hosts else list(HOSTS)
    if A.stage in ("gen", "all"):
        stage_gen(hosts)
    if A.stage in ("relax", "all"):
        stage_relax(hosts, A.fmax, A.steps)
    if A.stage in ("hull", "all"):
        stage_hull(hosts, A.fmax, A.steps)
