#!/usr/bin/env python3
"""Recover the candidate structures the first screen could not download.

all_candidates_master.csv has 1,152 formulas; 396 have no cif_path because
  * OQMD's API was failing (220 OQMD-only formulas), and
  * no Materials Project key was available (171 formulas with an MP id).
This fetches what is now reachable and records provenance:
  1. every formula with an MP id  -> MP REST by material_id (needs the key)
  2. OQMD-only formulas           -> OQMD with short retries; if OQMD is down,
                                     MP by chemical system, matched on reduced
                                     formula (+ space group when available)
CIFs go to ../structures/{MP,OQMD}/<formula>_<id>.CIF; the master CSV gets its
cif_path filled (a .bak copy is written first) and analysis/recovery_log.csv
says what happened to each formula.

Usage:  python3 recover_structures.py [--dry-run] [--no-oqmd]
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MASTER = os.path.join(ROOT, "all_candidates_master.csv")
MP = "https://api.materialsproject.org/materials/summary/"
OQMD = "https://oqmd.org/oqmdapi/formationenergy"


def mp_key():
    k = os.environ.get("MP_API_KEY") or (open(os.path.join(HERE, ".mp_api_key")).read().strip()
                                         if os.path.isfile(os.path.join(HERE, ".mp_api_key")) else "")
    if not k:
        raise SystemExit("no MP key (MP_API_KEY or workflow/.mp_api_key)")
    return k


def mp_get(params, key, tries=3):
    for t in range(tries):
        r = requests.get(MP, headers={"X-API-KEY": key}, params=params, timeout=120)
        if r.status_code == 200:
            return r.json()["data"]
        time.sleep(3 * (t + 1))
    r.raise_for_status()


def reduced(formula):
    """composition key insensitive to formula style (Er(Fe5Si)2 == Er2Fe10Si2)."""
    c = Composition(formula).fractional_composition
    return tuple(sorted((el.symbol, round(c[el], 4)) for el in c))


def save_cif(struct, folder, formula, ident):
    os.makedirs(os.path.join(ROOT, "structures", folder), exist_ok=True)
    fn = f"{formula}_{ident.replace(':', '-')}.CIF"
    path = os.path.join(ROOT, "structures", folder, fn)
    struct.to(filename=path, fmt="cif")
    return os.path.relpath(path, ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-oqmd", action="store_true", help="skip the OQMD attempt (API down)")
    A = ap.parse_args()
    rows = list(csv.DictReader(open(MASTER)))
    fields = list(rows[0].keys())
    missing = [r for r in rows if not r["cif_path"]]
    print(f"{len(rows)} formulas, {len(missing)} without a structure")
    key = mp_key()
    log = []

    # ---- 1. MP by id ------------------------------------------------------
    with_mp = [(r, re.search(r"MP:(mp-[A-Za-z0-9]+)", r["db_ids"]).group(1)) for r in missing if "MP:" in r["db_ids"]]
    print(f"MP ids to fetch: {len(with_mp)}")
    got = {}
    for i in range(0, len(with_mp), 40):
        chunk = with_mp[i:i + 40]
        ids = ",".join(m for _, m in chunk)
        data = mp_get({"material_ids": ids, "_fields": "material_id,formula_pretty,structure,energy_above_hull,symmetry", "_limit": 100}, key)
        for d in data:
            got[d["material_id"]] = d
        print(f"  {min(i+40, len(with_mp))}/{len(with_mp)}", flush=True)
    for r, mid in with_mp:
        d = got.get(mid)
        if not d:
            log.append({"formula": r["formula"], "status": "MP id not found", "source": "MP", "id": mid, "cif_path": ""}); continue
        s = Structure.from_dict(d["structure"])
        if reduced(r["formula"]) != reduced(d["formula_pretty"]):
            log.append({"formula": r["formula"], "status": f"MP formula mismatch {d['formula_pretty']}", "source": "MP", "id": mid, "cif_path": ""}); continue
        path = "" if A.dry_run else save_cif(s, "MP", r["formula"], mid)
        r["cif_path"] = path
        if d.get("symmetry"):
            r["spacegroup"] = r["spacegroup"] or str(d["symmetry"].get("number", ""))
        log.append({"formula": r["formula"], "status": "recovered", "source": "MP", "id": mid, "cif_path": path,
                    "e_hull_mp": d.get("energy_above_hull")})

    # ---- 2. OQMD-only -----------------------------------------------------
    oq = [r for r in missing if not r["cif_path"] and "OQMD:" in r["db_ids"] and "MP:" not in r["db_ids"]]
    print(f"OQMD-only formulas: {len(oq)}")
    oqmd_alive = not A.no_oqmd
    if oqmd_alive:
        try:
            t = requests.get(OQMD, params={"composition": "Fe-Gd", "limit": 1}, timeout=20)
            oqmd_alive = t.status_code == 200
        except requests.RequestException:
            oqmd_alive = False
        print(f"  OQMD reachable: {oqmd_alive}")
    mp_cache = {}
    for n, r in enumerate(oq):
        oid = re.search(r"OQMD:(\d+)", r["db_ids"]).group(1)
        done = False
        if oqmd_alive:
            try:
                d = requests.get(OQMD, params={"id": oid, "fields": "name,entry_id,spacegroup,unit_cell,sites,delta_e,stability"}, timeout=30).json()
                e = (d.get("data") or [None])[0]
                if e and e.get("unit_cell") and e.get("sites"):
                    species, coords = [], []
                    for site in e["sites"]:
                        el, xyz = site.split("@")
                        species.append(el.strip()); coords.append([float(x) for x in xyz.split()])
                    s = Structure(e["unit_cell"], species, coords)
                    path = "" if A.dry_run else save_cif(s, "OQMD", r["formula"], f"oqmd-{oid}")
                    r["cif_path"] = path
                    log.append({"formula": r["formula"], "status": "recovered", "source": "OQMD", "id": oid, "cif_path": path}); done = True
            except Exception as ex:   # noqa: BLE001 - keep going, record the failure
                log.append({"formula": r["formula"], "status": f"OQMD error {type(ex).__name__}", "source": "OQMD", "id": oid, "cif_path": ""})
        if done:
            continue
        # fall back: MP by chemical system, match reduced formula (and space group if known)
        els = "-".join(sorted(r["elements"].split()))
        if els not in mp_cache:
            try:
                mp_cache[els] = mp_get({"chemsys": els, "_fields": "material_id,formula_pretty,structure,energy_above_hull,symmetry", "_limit": 500}, key)
            except Exception:
                mp_cache[els] = []
        want = reduced(r["formula"])
        hits = [d for d in mp_cache[els] if reduced(d["formula_pretty"]) == want]
        if r["spacegroup"]:
            sg = [d for d in hits if str(d["symmetry"]["number"]) == str(r["spacegroup"])]
            hits = sg or hits
        if hits:
            d = min(hits, key=lambda d: d["energy_above_hull"] or 0)
            s = Structure.from_dict(d["structure"])
            path = "" if A.dry_run else save_cif(s, "MP", r["formula"], d["material_id"])
            r["cif_path"] = path
            log.append({"formula": r["formula"], "status": "recovered via MP composition match", "source": "MP", "id": d["material_id"], "cif_path": path,
                        "e_hull_mp": d.get("energy_above_hull")})
        else:
            log.append({"formula": r["formula"], "status": "not found (OQMD down, no MP match)", "source": "OQMD", "id": oid, "cif_path": ""})
        if n % 25 == 0:
            print(f"  {n}/{len(oq)}", flush=True)

    # ---- write ------------------------------------------------------------
    os.makedirs(os.path.join(HERE, "analysis"), exist_ok=True)
    keys = ["formula", "status", "source", "id", "cif_path", "e_hull_mp"]
    with open(os.path.join(HERE, "analysis", "recovery_log.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(log)
    rec = sum(1 for l in log if l["status"].startswith("recovered"))
    print(f"\nrecovered {rec} / {len(missing)} structures; log: analysis/recovery_log.csv")
    if not A.dry_run:
        shutil.copy(MASTER, MASTER + ".bak_before_recovery")
        with open(MASTER, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
        print("all_candidates_master.csv updated (backup .bak_before_recovery)")


if __name__ == "__main__":
    main()
