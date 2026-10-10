#!/usr/bin/env python3
"""Figures for the deck: (a) gap vs TM-tied RE polarisation h with validation
points and Tao et al. hosts; (b) light-RE Nd/Sm projected Ms vs MACE/MP hull.
Writes ../assets/gap_vs_h.png and ../assets/light_re_hull.png."""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
os.makedirs(ASSETS, exist_ok=True)
FE, RE, GOLD, INK, MUTE = "#E4572E", "#2E86AB", "#F2B134", "#1A2233", "#5A6478"

import apply_5d_method as A5

# ---------------------------------------------------------------- (a)
res = json.load(open(os.path.join(HERE, "results.json")))
H, D, names, cls = [], [], [], []
for rel, rec in res.items():
    if not rec.get("credible"):
        continue
    base = os.path.join(HERE, "runs", rel)
    try:
        els = A5.species(os.path.join(base, "ferri/POSCAR"))
        a = A5.re_nonf(os.path.join(base, "fm/OUTCAR"), els); b = A5.re_nonf(os.path.join(base, "ferri/OUTCAR"), els)
    except OSError:
        continue
    if not a or not b:
        continue
    H.append(-(a[0] + b[0]) / 2); D.append(abs(rec["dE_per_RE_meV"])); names.append(rel.split("/")[-1])
    tm = set(e for e in els if e in ("Fe", "Co"))
    cls.append("Fe+Co" if len(tm) == 2 else ("Fe" if "Fe" in tm else "Co"))
H, D = np.array(H), np.array(D)
k = (H * D).sum() / (H * H).sum()
r = np.corrcoef(H, D)[0, 1]

fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=200)
col = {"Fe": FE, "Co": RE, "Fe+Co": "#7B4FA3"}
for c in ("Fe", "Co", "Fe+Co"):
    m = np.array([x == c for x in cls])
    ax.scatter(H[m], D[m], s=26, c=col[c], alpha=0.75, edgecolor="white", linewidth=0.4, label=f"{c} hosts (n={m.sum()})")
xx = np.linspace(0, 0.32, 10)
ax.plot(xx, k * xx, color=INK, lw=1.4, ls="--", label=f"|ΔE| = {k:.0f}·h meV   (r = {r:.2f}, through origin)")
# validation / reference points
marks = {"GdFe2_validation": "GdFe₂", "Co17Gd2_sub": "Gd₂Co₁₇", "BFe14Gd2_nat": "Gd₂Fe₁₄B",
         "Fe5GdV_nat": "GdFe₁₀V₂", "Fe17Gd2H3_nat": "Gd₂Fe₁₇H₃ (suspect)"}
# experiment-implied gap: J_RT(expt) x 4 S_R S_T Z_RT, placed at the compound's own h
import csv as _csv
feat = {r["compound"]: r for r in _csv.DictReader(open(os.path.join(HERE, "analysis/exchange_features.csv")))}
EXPT = {"GdFe2_validation": 2.99, "BFe14Gd2_nat": 1.46, "Fe5GdV_nat": 1.30}
for n, lab in marks.items():
    if n in names:
        i = names.index(n)
        ax.scatter([H[i]], [D[i]], s=120, facecolor="none", edgecolor=GOLD, linewidth=2.0, zorder=5)
        off = {"GdFe2_validation": (10, -16), "Fe17Gd2H3_nat": (8, -22), "Co17Gd2_sub": (10, -22), "BFe14Gd2_nat": (-62, 12), "Fe5GdV_nat": (-72, -20)}[n]
        ax.annotate(lab, (H[i], D[i]), textcoords="offset points", xytext=off, fontsize=7.5, color=INK)
        if n in EXPT:
            f = feat[n]; gap_x = EXPT[n] / 1.602 * 4 * 3.5 * float(f["m_TM_avg"]) / 2 * float(f["N_TM_nn"])
            ax.scatter([H[i]], [gap_x], marker="*", s=150, c="white", edgecolor=FE, linewidth=1.4, zorder=7)
ax.scatter([], [], s=120, facecolor="none", edgecolor=GOLD, linewidth=2.0, label="circled: compounds with a measured J_RT")
ax.scatter([], [], marker="*", s=150, c="white", edgecolor=FE, linewidth=1.4, label="star: gap implied by the experimental J_RT")
# Tao hosts: their Y / f-frozen Sm site moment is h directly
tao = {"SmFe₅": 0.25, "Sm₃Fe₁₄Mn": 0.24, "Sm₃Fe₁₄Cr": 0.27, "Y₂Fe₇": 0.33, "Y₃Fe₁₄Mn": 0.25, "Y₃Fe₁₄Cr": 0.27}
for j, (n, h) in enumerate(tao.items()):
    ax.scatter([h], [k * h], marker="D", s=46, c=GOLD, edgecolor=INK, linewidth=0.6, zorder=6)
ax.scatter([], [], marker="D", s=46, c=GOLD, edgecolor=INK, label="Tao et al. 2026 hosts (h from their Table V, gap predicted)")
ax.annotate("Y₂Fe₇", (0.33, k * 0.33), textcoords="offset points", xytext=(-30, 8), fontsize=7.5, color=INK)
ax.annotate("SmFe₅ · Sm₃Fe₁₄(Mn,Cr)\nY₃Fe₁₄(Mn,Cr)", (0.255, k * 0.255), textcoords="offset points", xytext=(14, -40), fontsize=7.5, color=INK)
ax.set_xlabel("h = TM-tied RE 5d polarisation  (μB per RE, from the fm/ferri pair)", fontsize=10)
ax.set_ylabel("|ΔE(ferri − fm)| per Gd  (meV)", fontsize=10)
ax.set_xlim(0, 0.36); ax.set_ylim(0, 600)
ax.grid(alpha=0.25); ax.legend(fontsize=7.5, loc="upper left", frameon=False)
ax.set_title("RE–TM exchange gap is set by one number: the 5d spin the host induces on the RE", fontsize=10.5, color=INK)
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "gap_vs_h.png")); plt.close(fig)
print("gap_vs_h.png  k=%.0f r=%.2f n=%d" % (k, r, len(H)))

# ---------------------------------------------------------------- (b)
rows = list(csv.DictReader(open(os.path.join(HERE, "analysis/light_re/hull.csv"))))
C_T = 9.274e-24 * 4 * 3.14159e-7 / 1e-30
GJJ = {"Nd": 3.27, "Sm": 0.71}
from light_re_hull import HOSTS
surv = {"Fe5GdSi_nat", "Al2Fe10Gd_sub", "Fe5GdV_nat", "Co9Fe5Gd4_sub", "Co2Fe12GdY3_sub",
        "CoFe13GdY3_sub", "Fe9GdLuZr_sub", "CoFe6GdY_sub", "Fe10GdY_sub", "Fe14GdY3_sub"}
fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=200)
for re_, mk, c in (("Nd", "o", FE), ("Sm", "s", RE)):
    xs, ys, labs = [], [], []
    for rw in rows:
        if rw["RE"] != re_:
            continue
        rec = res[HOSTS[rw["host"]]]["ferri"]
        ms = (abs(rec["tm_moment_total"]) + rec["n_re"] * GJJ[re_]) / rec["volume_A3"] * C_T
        xs.append(1000 * float(rw["E_hull_eV_atom"])); ys.append(ms); labs.append(rw["host"])
    xs, ys = np.array(xs), np.array(ys)
    ax.scatter(xs, ys, marker=mk, s=42, c=c, alpha=0.8, edgecolor="white", linewidth=0.5, label=f"Gd → {re_} (29 hosts)")
    if re_ == "Nd":
        for x, y, l in zip(xs, ys, labs):
            if l in surv:
                short = l.replace("_sub", "").replace("_nat", "").replace("Gd", "Nd")
                dx, dy = {"Co2Fe12NdY3": (-78, -2), "Fe9NdLuZr": (6, 4), "CoFe13NdY3": (6, -9), "Fe14NdY3": (6, -6),
                          "Al2Fe10Nd": (6, -9), "Co9Fe5Nd4": (6, 5), "Fe10NdY": (6, 6), "Fe5NdV": (-40, -10), "CoFe6NdY": (6, -4)}.get(short, (5, 3))
                ax.annotate(short, (x, y), textcoords="offset points", xytext=(dx, dy), fontsize=6.8, color=INK)
ax.axvspan(-40, 12, color=GOLD, alpha=0.12, lw=0)
ax.text(-42, 1.13, "within model noise\nof the hull → VASP", fontsize=7.5, color="#8A6A1E", va="bottom")
ax.axhline(1.66, color=MUTE, lw=1, ls=":"); ax.text(60, 1.675, "NdFe₁₂N, 1.66 T (expt.)", fontsize=7.5, color=MUTE)
ax.axhline(1.78, color=MUTE, lw=1, ls=":"); ax.text(60, 1.795, "Sm(Fe₀.₈Co₀.₂)₁₂, 1.78 T (expt.)", fontsize=7.5, color=MUTE)
ax.set_xlabel("E above hull, MACE-MP-0 vs MP competitors re-evaluated with MACE  (meV/atom)", fontsize=9.5)
ax.set_ylabel("projected μ₀Ms, 0 K, free-ion light-RE moment parallel  (T)", fontsize=9.5)
ax.set_xlim(-45, 75); ax.set_ylim(1.1, 2.0)
ax.grid(alpha=0.25); ax.legend(fontsize=8, loc="upper right", frameon=False)
ax.set_title("Light-RE substitution on the strongly-coupled Fe-rich hosts: stability vs magnetisation", fontsize=10.5, color=INK)
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "light_re_hull.png")); plt.close(fig)
print("light_re_hull.png")
