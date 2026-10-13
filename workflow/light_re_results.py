#!/usr/bin/env python3
"""Read the light-RE (Nd_3 / Sm_3 f-in-core) relaxations and apply the 5d method.

Per run (runs/light/<RE>/<polytype>/<name>/relax):
  * convergence: ionic loop done (forces < EDIFFG) and SCF converged
  * volume change vs the MACE start and vs the Gd parent
  * Fe/Co sublattice moment (OUTCAR per-site, last block)
  * h = -(RE s+p+d moment), the TM-tied RE polarisation (f-in-core => the
    whole RE moment is hybridisation-induced; sign convention: positive =
    antiparallel to the TM, as in apply_5d_method.py)
  * mu0 Ms = (TM total + n_RE * gJ*J) / V, light-RE free-ion moment parallel
  * predicted RE-TM gap: the measured f-in-core h is divided by the H1 factor
    (Nd 1.55, Sm 1.62) to the Gd-pair scale, then 1574 h meV, scaled by
    (gJ-1)J/3.5 for the actual RE; T* = gap_RE / (2 k_B); B_RT = gap_Gd / (2 * 7 mu_B)
Writes analysis/light_re/vasp_results.csv and prints the table.

Usage:  python3 light_re_results.py
"""
import csv
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
K_H = 1574.0                 # meV per mu_B of Gd-pair h (apply_5d_method.py, 180 Gd pairs, r=0.89)
# H1 result (2026-10-12, 17 hosts, r = 0.98): the f-in-core RE s+p+d polarisation is a constant
# factor larger than the TM-tied h extracted from the Gd pair of the same host -
# Nd_3: x1.55, Sm_3: x1.62 (sd 0.05). Convert to Gd-equivalent h before using the calibration.
FC_TO_GD = {"Nd": 1.546, "Sm": 1.616, "Pr": 1.52}
GJ1J = {"Nd": 1.227, "Sm": 1.786}
GJJ = {"Nd": 3.27, "Sm": 0.71}
KB = 0.08617                 # meV/K
MUB_T = 0.05788              # meV/T
C_T = 9.274e-24 * 4 * 3.14159e-7 / 1e-30   # T per (mu_B / A^3)
TM = {"Fe", "Co"}


def species(poscar):
    L = open(poscar).read().splitlines()
    out = []
    for e, n in zip(L[5].split(), L[6].split()):
        out += [e] * int(n)
    return out


def parse(d):
    out = {"run": os.path.relpath(d, HERE)}
    oc = os.path.join(d, "OUTCAR")
    if not os.path.isfile(oc):
        out["status"] = "NOT_STARTED"; return out
    txt = open(oc, errors="replace").read()
    els = species(os.path.join(d, "POSCAR"))
    out["natoms"] = len(els)
    out["finished"] = "General timing and accounting" in txt[-20000:] or "General timing and accounting" in txt
    out["ionic_steps"] = txt.count("free  energy   TOTEN")
    forces_ok = "reached required accuracy" in txt
    out["status"] = "CONVERGED" if (out["finished"] and forces_ok) else ("FINISHED_NSW_HIT" if out["finished"] else "RUNNING_OR_KILLED")
    m = re.findall(r"volume of cell :\s+([\d.]+)", txt)
    if m:
        out["V0_A3"], out["V_A3"] = float(m[0]), float(m[-1])
    e = re.findall(r"free  energy\s+TOTEN\s*=\s*(-?\d+\.\d+)", txt)
    if e:
        out["E_eV"] = float(e[-1])
    p = re.findall(r"external pressure =\s+(-?[\d.]+) kB", txt)
    if p:
        out["P_kB"] = float(p[-1])
    b = txt.rfind("magnetization (x)")
    if b < 0:
        return out
    tm_tot, re_spd, re_el = 0.0, [], None
    for line in txt[b:].splitlines()[4:4 + len(els)]:
        q = line.split()
        if len(q) < 5 or not q[0].isdigit():
            break
        i = int(q[0]) - 1
        s, pp, dd = float(q[1]), float(q[2]), float(q[3])
        tot = float(q[-1])
        if els[i] in TM:
            tm_tot += tot
        elif els[i] in GJJ:
            re_spd.append(s + pp + dd); re_el = els[i]
    n_re = len(re_spd)
    out["RE"] = re_el; out["n_RE"] = n_re
    out["m_TM_total_uB"] = round(tm_tot, 3)
    if n_re and "V_A3" in out:
        sign = 1 if tm_tot >= 0 else -1
        h = -sign * sum(re_spd) / n_re           # positive = antiparallel to TM
        out["h_uB"] = round(h, 3)                               # as measured (f-in-core)
        h = h / FC_TO_GD.get(re_el, 1.55)                       # Gd-equivalent, what 1574 was fitted on
        out["h_gd_equiv_uB"] = round(h, 3)
        out["mu0Ms_T"] = round((abs(tm_tot) + n_re * GJJ[re_el]) / out["V_A3"] * C_T, 3)
        out["mu0Ms_TM_only_T"] = round(abs(tm_tot) / out["V_A3"] * C_T, 3)
        gap_gd = K_H * h
        gap_re = gap_gd * GJ1J[re_el] / 3.5
        out["gap_Gd_equiv_meV"] = round(gap_gd, 0)
        out["gap_RE_meV"] = round(gap_re, 0)
        out["T_star_K"] = round(gap_re / (2 * KB), 0)
        out["B_RT_T"] = round(gap_gd / (2 * 7 * MUB_T), 0)
    return out


def main():
    runs = sorted(glob.glob(os.path.join(HERE, "runs", "light", "*", "*", "*", "relax")))
    rows = [parse(d) for d in runs]
    # Gd parent volume for the comparison column
    from light_re_hull import HOSTS
    res = json.load(open(os.path.join(HERE, "results.json")))
    for r in rows:
        meta = os.path.join(HERE, r["run"], "..", "meta.json")
        if os.path.isfile(meta):
            m = json.load(open(meta)); r["parent"] = m["parent_host"]
            pv = res.get(m["parent_run"], {}).get("ferri", {}).get("volume_A3")
            if pv and "V_A3" in r:
                r["dV_vs_Gd_pct"] = round(100 * (r["V_A3"] / pv - 1), 1)
    keys = ["run", "status", "ionic_steps", "V_A3", "dV_vs_Gd_pct", "P_kB", "m_TM_total_uB", "h_uB", "h_gd_equiv_uB",
            "mu0Ms_T", "mu0Ms_TM_only_T", "gap_Gd_equiv_meV", "gap_RE_meV", "T_star_K", "B_RT_T", "E_eV", "parent"]
    os.makedirs(os.path.join(HERE, "analysis", "light_re"), exist_ok=True)
    with open(os.path.join(HERE, "analysis", "light_re", "vasp_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"{'compound':<20}{'status':<18}{'steps':>5}{'dV%':>6}{'P kB':>7}{'mTM':>7}{'h':>7}{'Ms':>6}{'gap_RE':>8}{'T*':>6}")
    for r in rows:
        name = r["run"].split("/")[-2]
        print(f"{name:<20}{r.get('status',''):<18}{r.get('ionic_steps',''):>5}{r.get('dV_vs_Gd_pct',''):>6}"
              f"{r.get('P_kB',''):>7}{r.get('m_TM_total_uB',''):>7}{r.get('h_uB',''):>7}{r.get('mu0Ms_T',''):>6}"
              f"{r.get('gap_RE_meV',''):>8}{r.get('T_star_K',''):>6}")
    print("wrote analysis/light_re/vasp_results.csv")


if __name__ == "__main__":
    main()
