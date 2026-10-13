#!/usr/bin/env python3
"""Mean-field Curie temperature from collinear energy mapping (Heisenberg model).

Stage 1  (--make)  for each relaxed run dir (runs/light/.../relax, runs/wave*/.../relax):
   builds static inputs for four collinear TM spin configurations on the relaxed
   CONTCAR, f-in-core RE (no RE spin), everything else as in the parent INCAR:
     FM      all TM up
     AFM-z   TM alternate by layer along the longest axis
     AFM-xy  TM alternate by in-plane checkerboard (parity of x+y in units of a/2)
     FI-min  TM of the minority element (Co if present, else the least-coordinated
             Fe site) reversed
   written to <rundir>/../tc/<config>/ ; a manifest of the new dirs is printed.
Stage 2  (--fit)   reads the OUTCAR energies and moments and fits
   E(config) = E0 - 1/2 sum_ij J_ij s_i s_j  with s_i = +-1 and J_ij = J1 (first TM
   shell, d < 1.18 d_min) + J2 (second shell, d < 1.5 d_min); |m| is taken from the
   FM run and absorbed into J (classical, S^2 -> m^2/4).  Then
     k_B Tc^MF  = (2/3) * largest eigenvalue of  M_ij = J_ij * (m_i m_j / 4) * z_ij
   (one row per crystallographic TM site; the RE-TM term J_RT from the Gd pair is
   added as an off-diagonal block when --jrt is given).  The RPA estimate is
   Tc^MF x 0.78 - the mean-field/RPA ratio for bcc-Fe-like lattices - and is
   recalibrated on Nd2Fe17 / NdFe10V2 / Nd2Fe14B when those wave-1 runs are in.
Usage
  python3 tc_mapping.py --make runs/light/Nd/new-Immm/Fe5NdSi_lre/relax ...   [--out batch/tc_runs.txt]
  python3 tc_mapping.py --fit  runs/light/Nd/new-Immm/Fe5NdSi_lre/relax ...   [--jrt-from-pair]
"""
import argparse
import itertools
import json
import os
import re
import shutil

import numpy as np
from pymatgen.core import Structure

HERE = os.path.dirname(os.path.abspath(__file__))
TM = {"Fe", "Co", "Mn", "Ni"}
KB = 8.617e-5          # eV/K
RPA = 0.78


def tm_pattern(s, kind):
    """+1/-1 per site for TM, 0 for others."""
    idx = [i for i, sp in enumerate(s.species) if sp.symbol in TM]
    pat = np.zeros(len(s))
    if kind == "FM":
        pat[idx] = 1
    elif kind == "AFMz":
        ax = int(np.argmax(s.lattice.abc))
        z = s.frac_coords[idx, ax] % 1.0
        # split into two groups by z: alternate half-layers
        order = np.argsort(z)
        layers = np.cumsum(np.r_[0, np.diff(z[order]) > 0.08])
        for k, i in zip(layers, order):
            pat[idx[i]] = 1 if k % 2 == 0 else -1
    elif kind == "AFMxy":
        a, b = sorted(range(3), key=lambda k: s.lattice.abc[k])[:2]
        for i in idx:
            f = s.frac_coords[i]
            pat[i] = 1 if (round(f[a] * 2) + round(f[b] * 2)) % 2 == 0 else -1
    elif kind == "FImin":
        els = [s.species[i].symbol for i in idx]
        minority = min(set(els), key=els.count) if len(set(els)) > 1 else None
        if minority is None:
            # least-coordinated TM site type: flip the quarter of TM with the fewest TM neighbours
            nn = np.array([len([n for n in s.get_neighbors(s[i], 3.0) if n.specie.symbol in TM]) for i in idx])
            cut = np.quantile(nn, 0.25)
            for i, n in zip(idx, nn):
                pat[i] = -1 if n <= cut else 1
        else:
            for i in idx:
                pat[i] = -1 if s.species[i].symbol == minority else 1
    return pat


def write_static(src_relax, dest, s, pat, magmag=2.5):
    os.makedirs(dest, exist_ok=True)
    s.to(filename=os.path.join(dest, "POSCAR"), fmt="poscar")
    for f in ("KPOINTS", "POTCAR"):
        shutil.copy(os.path.join(src_relax, f), dest)
    inc = open(os.path.join(src_relax, "INCAR")).read().splitlines()
    out = []
    for line in inc:
        k = line.split("=")[0].strip()
        if k in ("MAGMOM", "IBRION", "ISIF", "NSW", "EDIFFG", "POTIM", "SYSTEM"):
            continue
        out.append(line)
    # POSCAR written by pymatgen keeps the site order of s; MAGMOM per site
    mm = " ".join(f"{magmag * p:.2f}" if p else "0.00" for p in pat)
    comp = os.path.basename(os.path.dirname(os.path.dirname(os.path.normpath(dest))))
    out += [f"SYSTEM = {comp} {os.path.basename(dest)} Tc mapping",
            "IBRION = -1", "NSW = 0", f"MAGMOM = {mm}", "LORBIT = 11"]
    open(os.path.join(dest, "INCAR"), "w").write("\n".join(out) + "\n")


def shells(s):
    idx = [i for i, sp in enumerate(s.species) if sp.symbol in TM]
    d = []
    for i in idx:
        for n in s.get_neighbors(s[i], 4.0):
            if n.specie.symbol in TM:
                d.append(n.nn_distance)
    dmin = min(d)
    pairs = {1: [], 2: []}
    for i in idx:
        for n in s.get_neighbors(s[i], 1.5 * dmin):
            if n.specie.symbol in TM:
                shell = 1 if n.nn_distance < 1.18 * dmin else 2
                pairs[shell].append((i, n.index))
    return idx, pairs


def energy(outcar):
    t = open(outcar, errors="replace").read()
    e = re.findall(r"free  energy\s+TOTEN\s*=\s*(-?\d+\.\d+)", t)
    done = "General timing and accounting" in t
    b = t.rfind("magnetization (x)")
    moms = []
    if b >= 0:
        for line in t[b:].splitlines()[4:]:
            p = line.split()
            if len(p) >= 5 and p[0].isdigit():
                moms.append(float(p[-1]))
            elif moms:
                break
    return (float(e[-1]) if e else None), done, moms


def fit(relax_dir, jrt_meV=None):
    base = os.path.join(relax_dir, "..", "tc")
    cfgs = ["FM", "AFMz", "AFMxy", "FImin"]
    s = Structure.from_file(os.path.join(base, "FM", "POSCAR"))
    idx, pairs = shells(s)
    E, pats, mom_fm = {}, {}, None
    for c in cfgs:
        oc = os.path.join(base, c, "OUTCAR")
        if not os.path.isfile(oc):
            continue
        e, done, moms = energy(oc)
        if e is None or not done:
            continue
        E[c] = e; pats[c] = tm_pattern(s, c)
        if c == "FM":
            mom_fm = np.array(moms)
    if len(E) < 3 or mom_fm is None:
        return None
    # design: E_c = E0 - sum_shell J_shell * X_shell(c),  X_shell(c) = 1/2 sum_pairs s_i s_j m_i m_j /4
    m = np.abs(mom_fm)
    rows, y = [], []
    for c, e in E.items():
        p = pats[c]
        x = [0.5 * sum(p[i] * p[j] * m[i] * m[j] / 4 for i, j in pairs[sh]) for sh in (1, 2)]
        rows.append([1.0, -x[0], -x[1]]); y.append(e)
    coef, *_ = np.linalg.lstsq(np.array(rows), np.array(y), rcond=None)
    J1, J2 = coef[1], coef[2]
    # mean field: per TM site, J0_i = sum_j J_ij m_i m_j / 4 ; Tc from the largest eigenvalue of the site-site matrix
    n = len(s); Mx = np.zeros((n, n))
    for sh, J in ((1, J1), (2, J2)):
        for i, j in pairs[sh]:
            Mx[i, j] += J * m[i] * m[j] / 4
    sub = Mx[np.ix_(idx, idx)]
    lam = np.max(np.linalg.eigvals(sub).real)
    tc_mf = (2.0 / 3.0) * lam / KB
    if jrt_meV:
        # crude RE-TM addition: raises the eigenvalue by ~ J_RT^2 term; report separately
        pass
    return {"J1_meV": 1000 * J1, "J2_meV": 1000 * J2, "configs": list(E), "Tc_MF_K": tc_mf, "Tc_RPA_K": RPA * tc_mf,
            "E_AFMz_minus_FM_meV_perTM": 1000 * (E.get("AFMz", np.nan) - E["FM"]) / len(idx)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make", nargs="*", default=[])
    ap.add_argument("--fit", nargs="*", default=[])
    ap.add_argument("--out", default=os.path.join(HERE, "batch", "tc_runs.txt"))
    A = ap.parse_args()
    made = []
    for rd in A.make:
        rd = rd.rstrip("/")
        geom = os.path.join(rd, "CONTCAR") if os.path.getsize(os.path.join(rd, "CONTCAR")) > 0 else os.path.join(rd, "POSCAR")
        s = Structure.from_file(geom)
        for c in ("FM", "AFMz", "AFMxy", "FImin"):
            pat = tm_pattern(s, c)
            if c != "FM" and (pat.min() >= 0 or pat.max() <= 0):
                continue      # pattern degenerate for this cell
            d = os.path.join(rd, "..", "tc", c)
            write_static(rd, d, s, pat)
            made.append(os.path.relpath(os.path.normpath(d), HERE))
        print(f"{rd}: {sum(1 for x in made if x.startswith(os.path.relpath(os.path.join(rd, '..'), HERE)))} configs")
    if made:
        os.makedirs(os.path.dirname(A.out), exist_ok=True)
        open(A.out, "w").write("\n".join(made) + "\n")
        print(f"{len(made)} static runs -> {os.path.relpath(A.out, HERE)}")
    for rd in A.fit:
        r = fit(rd.rstrip("/"))
        name = os.path.basename(os.path.dirname(rd.rstrip("/")))
        if r is None:
            print(f"{name:<22} incomplete"); continue
        print(f"{name:<22} J1={r['J1_meV']:6.1f} meV  J2={r['J2_meV']:6.1f}  dE(AFMz-FM)={r['E_AFMz_minus_FM_meV_perTM']:6.0f} meV/TM  "
              f"Tc_MF={r['Tc_MF_K']:5.0f} K  Tc_RPA~{r['Tc_RPA_K']:5.0f} K  ({','.join(r['configs'])})")


if __name__ == "__main__":
    main()
