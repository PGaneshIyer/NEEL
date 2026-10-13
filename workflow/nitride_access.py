#!/usr/bin/env python3
"""Topotactic accessibility of the interstitial nitrides / carbides.

The open-nitrogen grand-potential hull does NOT rescue dilute RE-Fe nitrides:
raising mu_N stabilises the N-rich competitors (REN, Fe4N) faster than the
interstitial phase, which is why Sm2Fe17N3 decomposes to SmN + Fe above ~600 C.
These phases are made KINETICALLY, by gas-phase nitriding of the parent
intermetallic below its decomposition temperature, with the metal sublattice
frozen. The criterion that matches that route is therefore
   (1) the PARENT host is on / near the hull, and
   (2) N (or C) insertion into the frozen host is exothermic:
       dE_insert = [E(host + n X) - E(host)] / n - mu_X  <  0
       mu_N = E(N2)/2 (MACE reference) or shifted by --mu-N for NH3 / plasma;
       mu_C = graphite-like reference from the MP competitor cache.
Reads analysis/pool/pool.csv (MACE energies) and writes analysis/pool/interstitial_access.csv.
"""
import argparse, csv, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, "analysis/pool/pool.csv"))))
store = json.load(open(os.path.join(HERE, "analysis/light_re/mp_entries.json")))
CE = json.load(open(os.path.join(HERE, "analysis/light_re/mp_mace_energies.json")))
def ref(el):
    return min(CE[e["id"]]["E_eV"] / CE[e["id"]]["natoms"] for e in store.get(el, []) if e["id"] in CE)
ap = argparse.ArgumentParser(); ap.add_argument("--mu-N", type=float, default=0.0); ap.add_argument("--mu-C", type=float, default=0.0); A = ap.parse_args()
mu = {"N": ref("N") + A.mu_N, "C": ref("C") + A.mu_C}
by_cid = {r["cid"]: r for r in rows}
by_poscar = {r["poscar"].split("/")[1]: r for r in rows}       # runs-pool/<cid>/POSCAR_mace
out = []
for r in rows:
    if r["source"] != "interstitial":
        continue
    m = re.match(r"gen:([0-9a-f]+)_([NC])(\d+)\.CIF:(\w+)", r["tag"])
    if not m:
        continue
    pcid, X, n, re_ = m.groups(); n = int(n)
    parent = by_cid.get(pcid)
    if not parent:
        continue
    dE = (float(r["E_mace_eV"]) - float(parent["E_mace_eV"])) / n - mu[X]
    out.append({"compound": r["formula"], "re_el": re_, "X": X, "n_X": n, "parent": parent["formula"], "parent_E_hull_meV": parent["E_hull_meV"],
                "nitride_E_hull_meV": r["E_hull_meV"], "dE_insert_eV_perX": round(dE, 3), "Ms_proj_T": r["Ms_proj_T"],
                "accessible": (parent["E_hull_meV"] not in ("", None) and float(parent["E_hull_meV"]) <= 30 and -5 < dE < 0)})   # |dE|>5 eV = diverged relaxation
with open(os.path.join(HERE, "analysis/pool/interstitial_access.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
acc = [o for o in out if o["accessible"]]
print(f"{len(out)} interstitial cells; {len(acc)} topotactically accessible (parent hull <= 30 meV and insertion exothermic at mu shift N {A.mu_N:+.2f} eV, C {A.mu_C:+.2f} eV)")
print(f"{'compound':<16}{'X':>2}{'n':>3}{'parent':<14}{'pHull':>6}{'dE_ins':>8}{'Ms':>6}")
for o in sorted(acc, key=lambda o: -float(o["Ms_proj_T"]))[:25]:
    print(f"{o['compound']:<16}{o['X']:>2}{o['n_X']:>3}{o['parent']:<14}{float(o['parent_E_hull_meV']):6.1f}{o['dE_insert_eV_perX']:8.2f}{float(o['Ms_proj_T']):6.2f}")
