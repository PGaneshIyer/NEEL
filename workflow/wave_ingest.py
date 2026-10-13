#!/usr/bin/env python3
"""Turn finished wave runs into GP training labels.

Scans runs/wave*/<RE>/<name>/relax (and runs/light/* from the first light-RE
batch), parses each OUTCAR with light_re_results.parse (h, Fe/Co moment, Ms,
volume, convergence); the training label h is the Gd-EQUIVALENT polarisation
(measured f-in-core h divided by the H1 factor, Nd 1.55 / Sm 1.62), so Gd-pair
rows and wave rows live on one scale, recomputes the geometry descriptors on the RELAXED cell
(CONTCAR) and appends to analysis/pool/labels.csv - the table wave_gp.py
reads as f-in-core training rows. Also prints prediction-vs-measurement for
the wave (the standing test of hypothesis H1).

Usage:  python3 wave_ingest.py            # after ./sync_results.sh --mirror
"""
import csv
import glob
import json
import os
import sys

from pymatgen.core import Structure

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wave_features as WF
import light_re_results as LR

OUT = os.path.join(HERE, "analysis", "pool")


def main():
    os.makedirs(OUT, exist_ok=True)
    runs = sorted(glob.glob(os.path.join(HERE, "runs", "wave*", "*", "*", "relax"))) + \
           sorted(glob.glob(os.path.join(HERE, "runs", "light", "*", "*", "*", "relax")))
    labels_p = os.path.join(OUT, "labels.csv")
    old = {r["run"]: r for r in csv.DictReader(open(labels_p))} if os.path.isfile(labels_p) else {}
    rows, new = list(old.values()), 0
    for d in runs:
        rel = os.path.relpath(d, HERE)
        r = LR.parse(d)
        if r.get("status") not in ("CONVERGED", "FINISHED_NSW_HIT") or "h_uB" not in r:
            continue
        if rel in old and old[rel].get("status") == r["status"]:
            continue
        geom = os.path.join(d, "CONTCAR") if os.path.getsize(os.path.join(d, "CONTCAR")) > 0 else os.path.join(d, "POSCAR")
        s = Structure.from_file(geom)
        f = WF.features(s, r.get("RE"))
        if f is None:
            continue
        meta_p = os.path.join(d, "..", "meta.json")
        meta = json.load(open(meta_p)) if os.path.isfile(meta_p) else {}
        row = {"run": rel, "name": os.path.basename(os.path.dirname(d)), "cid": meta.get("cid", ""), "wave": meta.get("wave", 0),
               "status": r["status"], "h": r.get("h_gd_equiv_uB", r["h_uB"]), "h_fc_measured": r["h_uB"], "mu0Ms_T": r["mu0Ms_T"], "m_TM_total_uB": r["m_TM_total_uB"],
               "V_A3": r["V_A3"], "P_kB": r.get("P_kB", ""), "h_pred": meta.get("h_pred", ""), "gap_pred_meV": meta.get("gap_pred_meV", ""),
               "polytype": meta.get("polytype", ""), "parent": meta.get("parent", meta.get("parent_host", ""))}
        row.update({k: round(v, 4) if isinstance(v, float) else v for k, v in f.items()})
        rows = [x for x in rows if x["run"] != rel] + [row]; new += 1
    keys = ["run", "name", "cid", "wave", "status", "re_el", "h", "h_fc_measured", "h_pred", "gap_pred_meV", "mu0Ms_T", "m_TM_total_uB", "V_A3", "P_kB",
            "polytype", "parent", "n_RE", "n_TM", "natoms"] + WF.FEATURES
    with open(labels_p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    print(f"labels.csv: {len(rows)} rows ({new} new/updated)")
    test = [r for r in rows if r.get("h_pred") not in ("", None)]
    if test:
        import numpy as np
        hp = np.array([float(r["h_pred"]) for r in test]); hm = np.array([float(r["h"]) for r in test])
        print(f"H1 check on {len(test)} wave runs: r(pred, measured h) = {np.corrcoef(hp, hm)[0,1]:.2f}, "
              f"mean bias {np.mean(hm-hp):+.3f} muB, RMSE {np.sqrt(np.mean((hm-hp)**2)):.3f}")


if __name__ == "__main__":
    main()
