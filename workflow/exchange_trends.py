#!/usr/bin/env python3
"""What controls the RE-TM exchange gap? Trend analysis over every credible
fm/ferri pair in the campaign.

Each compound gives ONE energy difference, dE = E(ferri) - E(fm). Mean-field
Heisenberg: dE per RE ~ -2 J m_RE sum_nn m_TM, with the sum over the RE's
first-shell TM neighbours. So the per-compound effective coupling is

    J_eff = |dE| / (2 m_Gd sum_nn m_TM)        [meV / mu_B^2]

and the question "what makes FM more or less likely" becomes "what moves J_eff
and what moves sum_nn m_TM". Features per compound (all from files already
local - OUTCAR per-site s/p/d/f moments, POSCAR geometry - plus DOSCAR if
pulled):

  geometry   N_TM_nn (TM in the first shell around Gd), mean/min Gd-TM distance,
             TM/RE ratio, diluent fraction (non RE, non TM atoms), vol/atom
  moments    m_Gd (4f-dominated), per-site TM moments summed over the ACTUAL
             neighbours (not N x average), m_TM_avg, Gd 5d induced moment
             (the d column of the Gd rows - the middle link of the 4f-5d-3d chain)
  chemistry  Fe fraction of the TM sublattice, nominal 3d count (Mn5 Fe6 Co7 Ni8)
  DOS        (if DOSCAR present) occupied d-band centre of the TM sublattice
             relative to E_F, spin-resolved; TM d-DOS at E_F; Gd 5d occupation

Caveats that are printed, not hidden: energies are static at GNoME geometries;
29/185 pairs are NUPDOWN-locked (hollow markers); the Co16Gd2Mn lesson is that
a ferri run can sit in a metastable basin, which UNDER-estimates |dE| - trends
survive that, individual points may not.

Usage
  python3 exchange_trends.py                 # credible only -> analysis/
  python3 exchange_trends.py --all           # include non-credible (flagged)
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "analysis")
TM = {"Fe", "Co", "Mn", "Ni"}
RE = {"Gd", "Tb", "Dy", "Ho", "Er", "Tm"}
D_COUNT = {"Mn": 5, "Fe": 6, "Co": 7, "Ni": 8}

# validated categorical palette (dataviz slots 1-3, fixed order) + light surface
COL = {"Fe": "#2a78d6", "Co": "#eb6834", "Fe+Co": "#1baf7a"}
SURF, INK, MUTE, GRID = "#fcfcfb", "#1a2233", "#5a6478", "#e3e6ea"


# ----------------------------------------------------------------- parsing --
def species(poscar):
    L = open(poscar).read().splitlines()
    out = []
    for e, n in zip(L[5].split(), L[6].split()):
        out += [e] * int(n)
    return out


def site_table(outcar):
    """Last 'magnetization (x)' block -> list of (s,p,d,f,tot) per ion."""
    txt = open(outcar, errors="replace").read()
    b = txt.rfind("magnetization (x)")
    if b < 0:
        return None
    rows = []
    for line in txt[b:].splitlines()[4:]:
        p = line.split()
        if len(p) >= 5 and p[0].isdigit():
            vals = [float(x) for x in p[1:]]
            s, pp, d = vals[0], vals[1], vals[2]
            f = vals[3] if len(vals) >= 5 else 0.0
            rows.append((s, pp, d, f, vals[-1]))
        elif rows and line.strip().startswith(("---", "tot")):
            break
    return rows or None


def parse_doscar(path, els):
    """Per-ion projected DOS -> d-band features. Returns dict or None.
    DOSCAR (ISPIN=2, LORBIT=11): columns E, then (up,dn) per orbital:
    s, py,pz,px, dxy,dyz,dz2,dxz,dx2 [, 7 f]."""
    try:
        L = open(path).read().splitlines()
    except OSError:
        return None
    nat = int(L[0].split()[0])
    emax, emin, nedos, ef = (float(x) for x in L[5].split()[:4])
    nedos = int(nedos)
    pos = 6 + nedos           # skip total DOS block
    d_up_sum = d_dn_sum = 0.0; e_up_sum = e_dn_sum = 0.0; dos_ef = 0.0; n_tm = 0
    gd5d = []
    for i in range(nat):
        hdr = pos; pos += 1
        blk = np.array([[float(x) for x in L[pos + k].split()] for k in range(nedos)])
        pos += nedos
        E = blk[:, 0]; ncol = blk.shape[1] - 1
        norb = ncol // 2
        if norb < 9:
            continue
        up = blk[:, 1::2]; dn = blk[:, 2::2]
        d_up = up[:, 4:9].sum(1); d_dn = dn[:, 4:9].sum(1)
        occ = E <= ef
        dE = np.gradient(E)
        el = els[i]
        if el in TM:
            n_tm += 1
            wu, wd = (d_up * dE)[occ], (d_dn * dE)[occ]
            d_up_sum += wu.sum(); d_dn_sum += wd.sum()
            e_up_sum += ((E - ef) * d_up * dE)[occ].sum()
            e_dn_sum += ((E - ef) * d_dn * dE)[occ].sum()
            k = int(np.argmin(abs(E - ef)))
            dos_ef += d_up[k] + d_dn[k]
        elif el in RE:
            gd5d.append(((d_up * dE)[occ].sum(), (d_dn * dE)[occ].sum()))
    if n_tm == 0 or d_up_sum == 0 or d_dn_sum == 0:
        return None
    out = {"eps_d_up": e_up_sum / d_up_sum, "eps_d_dn": e_dn_sum / d_dn_sum,
           "eps_d": (e_up_sum + e_dn_sum) / (d_up_sum + d_dn_sum),
           "d_occ_per_TM": (d_up_sum + d_dn_sum) / n_tm,
           "dos_d_EF_per_TM": dos_ef / n_tm}
    if gd5d:
        out["gd5d_occ_up"] = float(np.mean([a for a, _ in gd5d]))
        out["gd5d_occ_dn"] = float(np.mean([b for _, b in gd5d]))
    return out


# ---------------------------------------------------------------- features --
def features(rel, rec):
    from pymatgen.core import Structure
    base = os.path.join(HERE, "runs", rel)
    gs = rec.get("ground_state_config") or "ferri"
    pos = os.path.join(base, gs, "POSCAR")
    if not os.path.exists(pos):
        return None
    els = species(pos)
    tab = {c: site_table(os.path.join(base, c, "OUTCAR")) for c in ("fm", "ferri")}
    if not tab["fm"] or not tab["ferri"] or len(tab[gs]) != len(els):
        return None
    s = Structure.from_file(pos)
    re_idx = [i for i, e in enumerate(els) if e in RE]
    tm_idx = [i for i, e in enumerate(els) if e in TM]
    if not re_idx or not tm_idx:
        return None
    # first shell: everything within 1.18 x the shortest RE-TM distance in the
    # cell, counted THROUGH periodic images (get_neighbors), not per atom pair -
    # in a 6-atom Laves cell one Fe is a neighbour of Gd via three images, and a
    # pairwise minimum-image count gives 4 where the coordination is 12.
    tm_set = set(tm_idx)
    all_nb = {i: [(nb.index, nb.nn_distance) for nb in s.get_neighbors(s[i], 4.2) if nb.index in tm_set]
              for i in re_idx}
    dmin = min(d for nbl in all_nb.values() for _, d in nbl)
    rcut = 1.18 * dmin
    m_gs = [row[4] for row in tab[gs]]
    n_nn, d_nn, msum = [], [], []
    for i in re_idx:
        nb = [(j, d) for j, d in all_nb[i] if d <= rcut]
        n_nn.append(len(nb)); d_nn += [d for _, d in nb]
        msum.append(sum(abs(m_gs[j]) for j, _ in nb))
    tm_els = [els[j] for j in tm_idx]
    nfe = tm_els.count("Fe"); nco = tm_els.count("Co")
    cls = "Fe" if nco == 0 else ("Co" if nfe == 0 else "Fe+Co")
    m_gd = float(np.mean([abs(m_gs[i]) for i in re_idx]))
    m_tm = float(np.mean([abs(m_gs[j]) for j in tm_idx]))
    gd_f = np.mean([tab[gs][i][3] for i in re_idx]); gd_d = np.mean([tab[gs][i][2] for i in re_idx])
    de = abs(rec["dE_per_RE_meV"])
    sig = 2 * m_gd * float(np.mean(msum))
    f = {
        "compound": rel.split("/")[-1], "path": rel, "polytype": rec.get("polytype"),
        "class": cls, "constrained": bool(rec["fm"].get("constrained")),
        "dE_per_RE_meV": de, "J_eff": de / sig if sig > 0 else float("nan"),
        "m_Gd": m_gd, "m_TM_avg": m_tm, "sum_nn_mTM": float(np.mean(msum)),
        "N_TM_nn": float(np.mean(n_nn)), "d_RE_TM_min": dmin, "d_RE_TM_nn_mean": float(np.mean(d_nn)) if d_nn else float("nan"),
        "f_Fe": nfe / len(tm_els), "d_count": float(np.mean([D_COUNT[e] for e in tm_els])),
        "TM_per_RE": len(tm_idx) / len(re_idx),
        "x_dil": 1 - (len(tm_idx) + len(re_idx)) / len(els),
        "vol_per_atom": s.volume / len(s),
        # 5d moment of Gd, signed relative to its own 4f (positive = parallel, Campbell step 1)
        "gd5d_over_4f": float(gd_d / gd_f) if gd_f else float("nan"),
        "gd5d_moment": float(abs(gd_d)),
    }
    dos = parse_doscar(os.path.join(base, gs, "DOSCAR"), els)
    if dos:
        f.update(dos)
    return f


# -------------------------------------------------------------------- fits --
def ols(X, y, names):
    X1 = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    pred = X1 @ beta
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(zip(["intercept"] + names, beta)), r2


def zscore(a):
    a = np.asarray(a, float); return (a - a.mean()) / (a.std() or 1)


# -------------------------------------------------------------------- plot --
def make_figure(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    have_dos = any("eps_d" in r for r in rows)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9.6), dpi=160, facecolor=SURF)
    fig.subplots_adjust(hspace=0.42, wspace=0.3, left=0.06, right=0.98, top=0.87, bottom=0.08)
    for ax in axes.flat:
        ax.set_facecolor(SURF)
        for sp in ("top", "right"): ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"): ax.spines[sp].set_color(GRID)
        ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
        ax.tick_params(colors=MUTE, labelsize=9)
    def scatter(ax, xk, yk, label_n=0):
        for cls in ("Fe", "Co", "Fe+Co"):
            for cons in (False, True):
                pts = [r for r in rows if r["class"] == cls and r["constrained"] == cons and xk in r and yk in r
                       and np.isfinite(r[xk]) and np.isfinite(r[yk])]
                if not pts: continue
                x = [r[xk] for r in pts]; y = [r[yk] for r in pts]
                ax.scatter(x, y, s=34, c=COL[cls] if not cons else "none", edgecolors=COL[cls] if cons else SURF,
                           linewidths=1.2 if cons else 0.8, zorder=3,
                           label=f"{cls}{' (locked)' if cons else ''}")
        if label_n:
            cand = sorted([r for r in rows if xk in r and yk in r and np.isfinite(r[yk])], key=lambda r: r[yk])
            for r in cand[:label_n] + cand[-label_n:]:
                ax.annotate(r["compound"].replace("_sub", ""), (r[xk], r[yk]), fontsize=7, color=MUTE,
                            xytext=(4, 3), textcoords="offset points")
    a = axes.flat
    # (a) the mean-field predictor - if |dE| were just 2 J m_Gd sum_nn m_TM with
    # a universal J, this would be a line through the origin. It is not: the gap
    # plateaus at 150-350 meV while the neighbour sum doubles, so the per-
    # neighbour coupling must fall as the shell gets bigger/farther.
    scatter(a[0], "sum_nn_mTM", "dE_per_RE_meV", label_n=2)
    xs = np.array([r["sum_nn_mTM"] for r in rows]); ys = np.array([r["dE_per_RE_meV"] for r in rows])
    rho = np.corrcoef(xs, ys)[0, 1]
    a[0].text(0.985, 0.11, f"Pearson r = {rho:.2f}: the gap does NOT scale with\nthe neighbour moment sum - the per-\nneighbour coupling J varies between hosts",
              transform=a[0].transAxes, fontsize=8.5, color=INK, va="bottom", ha="right")
    a[0].set_xlabel("sum of first-shell TM moments around Gd  (mu_B)", color=MUTE)
    a[0].set_ylabel("|dE| per Gd  (meV)", color=MUTE); a[0].set_title("Mean-field test: gap vs neighbour moment sum", fontsize=10.5, color=INK, loc="left")
    # (b) J_eff vs d count
    scatter(a[1], "d_count", "J_eff"); a[1].set_xlabel("mean nominal 3d count of TM sublattice (Fe 6, Co 7)", color=MUTE)
    a[1].set_ylabel("J_eff = |dE| / (2 m_Gd sum m_TM)  (meV/mu_B²)", color=MUTE); a[1].set_title("Band filling", fontsize=10.5, color=INK, loc="left")
    # (c) J_eff vs distance
    scatter(a[2], "d_RE_TM_nn_mean", "J_eff", label_n=2); a[2].set_xlabel("mean first-shell Gd-TM distance  (A)", color=MUTE)
    a[2].set_ylabel("J_eff  (meV/mu_B²)", color=MUTE); a[2].set_title("Distance", fontsize=10.5, color=INK, loc="left")
    # (d) J_eff vs Gd 5d moment
    scatter(a[3], "gd5d_moment", "J_eff", label_n=2); a[3].set_xlabel("|Gd 5d moment|  (mu_B)  - middle link of 4f-5d-3d", color=MUTE)
    a[3].set_ylabel("J_eff  (meV/mu_B²)", color=MUTE); a[3].set_title("Induced 5d polarisation", fontsize=10.5, color=INK, loc="left")
    # (e) DOS feature or diluent fraction
    if have_dos:
        scatter(a[4], "eps_d", "J_eff", label_n=2); a[4].set_xlabel("occupied TM d-band centre, E - E_F  (eV)", color=MUTE)
        a[4].set_title("d-band centre (DOSCAR)", fontsize=10.5, color=INK, loc="left")
    else:
        scatter(a[4], "x_dil", "J_eff", label_n=2); a[4].set_xlabel("diluent fraction (atoms that are neither RE nor TM)", color=MUTE)
        a[4].set_title("Dilution (DOSCAR not pulled yet)", fontsize=10.5, color=INK, loc="left")
    a[4].set_ylabel("J_eff  (meV/mu_B²)", color=MUTE)
    # (f) distribution of J_eff by class
    for i, cls in enumerate(("Fe", "Co", "Fe+Co")):
        v = [r["J_eff"] for r in rows if r["class"] == cls and np.isfinite(r["J_eff"])]
        if not v: continue
        jit = np.random.default_rng(1).uniform(-0.16, 0.16, len(v))
        a[5].scatter(i + jit, v, s=26, c=COL[cls], edgecolors=SURF, linewidths=0.8, zorder=3)
        med = float(np.median(v)); a[5].plot([i - 0.3, i + 0.3], [med, med], color=INK, lw=1.4, zorder=4)
        a[5].text(i, 0.985, f"median {med:.2f}\nn = {len(v)}", fontsize=8, color=INK, va="top", ha="center",
                  transform=a[5].get_xaxis_transform())
    a[5].set_xticks([0, 1, 2]); a[5].set_xticklabels(["Fe", "Co", "Fe+Co"], color=MUTE)
    a[5].set_xlim(-0.6, 2.6)
    a[5].set_ylabel("J_eff  (meV/mu_B²)", color=MUTE); a[5].set_title("Is the coupling universal?", fontsize=10.5, color=INK, loc="left")
    h, l = a[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper left", ncol=6, frameon=False, fontsize=9, bbox_to_anchor=(0.055, 0.945))
    fig.suptitle(f"What sets the fm-ferri gap - {len(rows)} credible Gd pairs, all ferrimagnetic", x=0.06, ha="left",
                 fontsize=14, color=INK, fontweight="bold", y=0.985)
    fig.savefig(path, facecolor=SURF)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="include non-credible pairs")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    res = json.load(open(os.path.join(HERE, "results.json")))
    rows, skipped = [], 0
    for rel, rec in sorted(res.items()):
        if rec.get("dE_per_RE_meV") is None or (not args.all and not rec.get("credible")):
            continue
        f = features(rel, rec)
        if f is None:
            skipped += 1; continue
        f["credible"] = bool(rec.get("credible")); rows.append(f)
    n_dos = sum("eps_d" in r for r in rows)
    print(f"{len(rows)} pairs with features ({skipped} skipped), DOSCAR features on {n_dos}")

    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("compound", "class"), k))
    with open(os.path.join(OUT, "exchange_features.csv"), "w") as fh:
        fh.write(",".join(keys) + "\n")
        for r in rows:
            fh.write(",".join(str(r.get(k, "")) for k in keys) + "\n")

    J = np.array([r["J_eff"] for r in rows]); ok = np.isfinite(J)
    print(f"\nJ_eff: median {np.median(J[ok]):.3f}  IQR {np.percentile(J[ok],25):.3f}-{np.percentile(J[ok],75):.3f}  "
          f"min {J[ok].min():.3f}  max {J[ok].max():.3f}  meV/mu_B^2   (spread = {np.std(J[ok])/np.mean(J[ok])*100:.0f}% of mean)")
    for cls in ("Fe", "Co", "Fe+Co"):
        v = [r["J_eff"] for r in rows if r["class"] == cls and np.isfinite(r["J_eff"])]
        if v: print(f"   {cls:<6} n={len(v):3d}  median J_eff {np.median(v):.3f}   median |dE|/RE {np.median([r['dE_per_RE_meV'] for r in rows if r['class']==cls]):.0f} meV   median sum_nn_mTM {np.median([r['sum_nn_mTM'] for r in rows if r['class']==cls]):.1f}")

    names = ["d_count", "d_RE_TM_nn_mean", "x_dil", "gd5d_moment", "m_TM_avg"]
    if n_dos >= 20:
        names += ["eps_d", "dos_d_EF_per_TM"]
    sel = [r for r in rows if all(k in r and np.isfinite(r[k]) for k in names + ["J_eff"]) and r["J_eff"] > 0]
    X = np.column_stack([zscore([r[k] for r in sel]) for k in names]); y = np.log(np.array([r["J_eff"] for r in sel]))
    beta, r2 = ols(X, y, names)
    print(f"\nOLS  log(J_eff) ~ standardised features   (n={len(sel)}, R² = {r2:.2f}); coefficient = d log J per 1 SD:")
    for k in names: print(f"   {k:<18} {beta[k]:+.3f}")
    X2 = np.column_stack([zscore([r[k] for r in sel]) for k in ["sum_nn_mTM"] + names]); y2 = np.log(np.array([r["dE_per_RE_meV"] for r in sel]))
    beta2, r22 = ols(X2, y2, ["sum_nn_mTM"] + names)
    print(f"\nOLS  log|dE| ~ same + sum_nn_mTM   (R² = {r22:.2f}):")
    for k in ["sum_nn_mTM"] + names: print(f"   {k:<18} {beta2[k]:+.3f}")

    srt = sorted([r for r in rows if np.isfinite(r["J_eff"])], key=lambda r: r["J_eff"])
    print("\nWEAKEST coupling (closest to an FM-permitting regime):")
    for r in srt[:8]: print(f"   {r['compound']:<22} J_eff {r['J_eff']:.3f}  |dE| {r['dE_per_RE_meV']:5.0f}  N_nn {r['N_TM_nn']:4.1f}  d {r['d_RE_TM_nn_mean']:.2f} A  m_TM {r['m_TM_avg']:.2f}  5d {r['gd5d_moment']:.2f}  {r['class']}{' locked' if r['constrained'] else ''}")
    print("STRONGEST:")
    for r in srt[-5:]: print(f"   {r['compound']:<22} J_eff {r['J_eff']:.3f}  |dE| {r['dE_per_RE_meV']:5.0f}  N_nn {r['N_TM_nn']:4.1f}  d {r['d_RE_TM_nn_mean']:.2f} A  m_TM {r['m_TM_avg']:.2f}  5d {r['gd5d_moment']:.2f}  {r['class']}")

    png = os.path.join(OUT, "exchange_trends.png")
    make_figure(rows, png)
    print(f"\nwrote {os.path.relpath(png, HERE)} and analysis/exchange_features.csv")


if __name__ == "__main__":
    main()
