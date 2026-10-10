#!/usr/bin/env python3
"""The 5d-moment method: predict the RE-TM exchange gap from ONE calculation.

Liebs & Fahnle (JMMM 128, L8, 1993): dE(4f flip) = 2 I_4f-5d (gJ-1) dJ_4f S_5d.
The 5d moment in the ground state has two parts: one induced by the TM 3d via
hybridisation (tied to the TM, does NOT flip with the 4f) and one induced by
the ion's own 4f (flips with it, cancels in the energy difference). With both
configurations in hand the TM-tied part is

    h = -( m_RE(ferri) + m_RE(fm) ) / 2      (per RE site, non-4f moment)

and it is the quantity that exists in a 4f-free host too: Y, or Sm with the
f-frozen Sm_3 potential - exactly what Tao et al. (arXiv 2608.25270) report as
the RE site moment (-0.24 ... -0.33 mu_B). So: calibrate |dE| = k h on our 180
Gd pairs, then read the Gd-equivalent gap of any host off a single run.

Outputs per host: gap for Gd, the (gJ-1)J-scaled gap for the actual RE, J_RT in
the two-sublattice convention, the RE molecular field B_RT = dE/(2 mu_RE), and
T* = dE_RE/(2 k_B) - the temperature at which the RE's Zeeman energy in that
field equals k_B T, i.e. roughly where the RE sublattice (and the anisotropy
it carries) starts to let go of the TM.

Usage:  python3 apply_5d_method.py
"""
import csv
import json
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MUB_MEV_PER_T = 0.05788       # mu_B in meV/T
KB_MEV = 0.08617              # k_B in meV/K
RE = {"Gd", "Tb", "Dy", "Ho", "Er", "Tm"}
GJ1J = {"Gd": 3.5, "Tb": 3.0, "Dy": 2.5, "Ho": 2.0, "Er": 1.5, "Tm": 1.0,
        "Sm": 1.786, "Nd": 1.227, "Pr": 0.8, "Ce": 0.357, "Y": 0.0}   # |(gJ-1)J|


def re_nonf(outcar, els):
    """Mean over RE sites of the non-4f moment (s+p+d), signed, last block."""
    txt = open(outcar, errors="replace").read()
    b = txt.rfind("magnetization (x)")
    if b < 0:
        return None
    vals, tot4f = [], []
    for line in txt[b:].splitlines()[4:4 + len(els)]:
        p = line.split()
        if len(p) >= 5 and p[0].isdigit():
            i = int(p[0]) - 1
            if i < len(els) and els[i] in RE:
                s, pp, d = float(p[1]), float(p[2]), float(p[3])
                vals.append(s + pp + d); tot4f.append(float(p[4]) if len(p) >= 6 else 0.0)
    return (float(np.mean(vals)), float(np.mean([abs(x) for x in tot4f]))) if vals else None


def species(poscar):
    L = open(poscar).read().splitlines(); out = []
    for e, n in zip(L[5].split(), L[6].split()): out += [e] * int(n)
    return out


def main():
    res = json.load(open(os.path.join(HERE, "results.json")))
    feats = {r["compound"]: r for r in csv.DictReader(open(os.path.join(HERE, "analysis/exchange_features.csv")))}
    H, D, D5, names = [], [], [], []
    for rel, rec in res.items():
        if not rec.get("credible"):
            continue
        base = os.path.join(HERE, "runs", rel)
        try:
            els = species(os.path.join(base, "ferri/POSCAR"))
            a = re_nonf(os.path.join(base, "fm/OUTCAR"), els); b = re_nonf(os.path.join(base, "ferri/OUTCAR"), els)
        except OSError:
            continue
        if not a or not b:
            continue
        h = -(a[0] + b[0]) / 2            # TM-tied non-4f polarisation (positive = antiparallel to TM)
        name = rel.split("/")[-1]
        H.append(h); D.append(abs(rec["dE_per_RE_meV"])); names.append(name)
        D5.append(float(feats[name]["gd5d_moment"]) if name in feats else np.nan)
    H, D, D5 = np.array(H), np.array(D), np.array(D5)

    def fit0(x, y):
        k = (x * y).sum() / (x * x).sum(); r2 = 1 - ((y - k * x) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        return k, r2, np.corrcoef(x, y)[0, 1]
    k_h, r2_h, r_h = fit0(H, D)
    ok = np.isfinite(D5); k_5, r2_5, r_5 = fit0(D5[ok], D[ok])
    print(f"calibration on {len(D)} credible Gd pairs")
    print(f"  TM-tied non-4f polarisation h (comparable to Y / f-frozen Sm):  |dE| = {k_h:6.0f} h   r = {r_h:.2f}  R2(origin) = {r2_h:.2f}   median h = {np.median(H):.3f} mu_B")
    print(f"  ground-state 5d d-column (used in exchange_trends.py):           |dE| = {k_5:6.0f} m   r = {r_5:.2f}  R2(origin) = {r2_5:.2f}")
    print(f"  implied I_4f-5d from h-fit: {k_h/7:.0f} meV  (Gd: dE = 7 I h)")

    # ---- Tao et al. Table V: site-averaged RE moments (f-frozen Sm_3 / Y: pure hybridisation polarisation) ----
    tao = [("SmFe5", "Sm", -0.25, 2.07, 1.303), ("Sm3Fe14Mn", "Sm", -0.24, 2.02, 1.270), ("Sm3Fe14Cr", "Sm", -0.27, 2.23, 1.177),
           ("Y2Fe7", "Y", -0.33, 2.03, 1.178), ("Y3Fe14Mn", "Y", -0.25, 2.00, 1.319), ("Y3Fe14Cr", "Y", -0.27, 2.06, 1.164)]
    print(f"\nTao et al. hosts (RE moment from their Table V -> h):")
    print(f"  {'host':<11} {'h':>5}  {'Gd-gap':>7} {'for RE':>7} {'J_RT':>13} {'B_RT(Gd)':>9} {'T*(RE)':>7}   note")
    for host, el, m, mfe, ms in tao:
        h = abs(m); gap_gd = k_h * h
        gap_re = gap_gd * GJ1J[el] / 3.5
        # two-sublattice J_RT per neighbour: dE_R = 4 J S_R S_T Z_RT; use Z_RT ~ 18 (CaCu5-derived R has 18 TM nn), S_T = mfe/2
        J = gap_gd / (4 * 3.5 * (mfe / 2) * 18)
        B = gap_gd / (2 * 7 * MUB_MEV_PER_T)
        Tstar = gap_re / (2 * KB_MEV) if gap_re > 0 else 0
        note = "Y: no 4f - gap listed is what Gd/Sm WOULD have in this host" if el == "Y" else "Sm: gap x0.51 of Gd (de Gennes spin projection)"
        print(f"  {host:<11} {h:5.2f}  {gap_gd:5.0f} meV {gap_re:5.0f} meV  {J:.2f} meV={J*1.602:.2f}e-22J {B:6.0f} T {Tstar:6.0f} K   {note}")
    print("\n  reference, same method on our own compounds:")
    for n in ("Co17Gd2_sub", "BFe14Gd2_nat", "CFe17Gd2_nat", "Fe17Gd2H3_nat", "GdFe2_validation"):
        if n in names:
            i = names.index(n); print(f"  {n:<18} h={H[i]:.3f}  predicted {k_h*H[i]:4.0f} meV   actual {D[i]:4.0f} meV   T*(Gd) = {D[i]/(2*KB_MEV):4.0f} K")


if __name__ == "__main__":
    main()
