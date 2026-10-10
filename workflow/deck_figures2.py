#!/usr/bin/env python3
"""Second set of deck figures (all from exchange_features.csv / results.json):
  trends_neighbours.png   |dE| vs summed neighbour TM moment: the gap is not a neighbour count
  trends_geometry.png     J_eff vs RE-TM distance  +  J_eff by host class
  validation_jrt.png      J_RT this work vs experiment (Liebs-Fahnle refs, Duc 1998)
  principles_effects.png  effect of each design lever on J_eff (median ratio to baseline, bootstrap CI)
  campbell_ms.png         projected Ms per RE for the best hosts vs literature magnets
"""
import csv
import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
FE, RE, GOLD, INK, MUTE, PUR = "#E4572E", "#2E86AB", "#F2B134", "#1A2233", "#5A6478", "#7B4FA3"
rows = [r for r in csv.DictReader(open(os.path.join(HERE, "analysis/exchange_features.csv"))) if r["credible"] in ("True", "1", "true")]
if not rows:
    rows = list(csv.DictReader(open(os.path.join(HERE, "analysis/exchange_features.csv"))))
res = json.load(open(os.path.join(HERE, "results.json")))
F = lambda r, k: float(r[k])
def elements(name):
    return set(re.findall(r"[A-Z][a-z]?", re.sub(r"_(sub|nat|validation|native|mnanti)$", "", name).replace("_", "")))
for r in rows:
    r["els"] = elements(r["compound"]); r["J"] = F(r, "J_eff"); r["dE"] = abs(F(r, "dE_per_RE_meV"))
    r["cls"] = "Fe+Co" if {"Fe", "Co"} <= r["els"] else ("Fe" if "Fe" in r["els"] else "Co")
col = {"Fe": FE, "Co": RE, "Fe+Co": PUR}

# ---------------------------------------------------------------- 1. neighbours
fig, ax = plt.subplots(figsize=(7.0, 4.9), dpi=200)
for c in ("Fe", "Co", "Fe+Co"):
    rr = [r for r in rows if r["cls"] == c]
    ax.scatter([F(r, "sum_nn_mTM") for r in rr], [r["dE"] for r in rr], s=28, c=col[c], alpha=0.75,
               edgecolor="white", linewidth=0.4, label=f"{c} hosts (n={len(rr)})")
xx = np.linspace(8, 50, 5)
for J, lab, xt in ((0.25, "J_eff = 0.25", 49), (0.5, "0.5", 49), (1.0, "1.0 meV/μB²", 38)):
    ax.plot(xx, 2 * 7 * J * xx, color=MUTE, lw=0.9, ls=":")
    ax.text(xt, min(2 * 7 * J * xt, 540), lab, fontsize=7.5, color=MUTE, va="bottom", ha="right")
for n, lab, dx, dy in (("Fe17Gd2H3_nat", "Gd₂Fe₁₇H₃", 6, -4), ("GdFe2_validation", "GdFe₂", 6, 4), ("Co19Fe4Gd6_sub", "Co₁₉Fe₄Gd₆", 6, 4), ("Fe17Gd2N2_nat", "Gd₂Fe₁₇N₂", -60, -12)):
    r = next((r for r in rows if r["compound"] == n), None)
    if r:
        ax.annotate(lab, (F(r, "sum_nn_mTM"), r["dE"]), textcoords="offset points", xytext=(dx, dy), fontsize=7.5, color=INK)
ax.set_xlabel("Σ nearest-neighbour TM moment around Gd  (μB)", fontsize=10)
ax.set_ylabel("|ΔE(ferri − fm)| per Gd  (meV)", fontsize=10)
ax.set_ylim(0, 560); ax.set_xlim(8, 52); ax.grid(alpha=0.25); ax.legend(fontsize=8, frameon=False, loc="upper left")
ax.set_title("Same neighbour moment, 5× different gap: the per-neighbour coupling is a host property", fontsize=10, color=INK)
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "trends_neighbours.png")); plt.close(fig)

# ---------------------------------------------------------------- 2. geometry + class
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 4.6), dpi=200, gridspec_kw={"width_ratios": [1.6, 1]})
for c in ("Fe", "Co", "Fe+Co"):
    rr = [r for r in rows if r["cls"] == c]
    a1.scatter([F(r, "d_RE_TM_nn_mean") for r in rr], [r["J"] for r in rr], s=28, c=col[c], alpha=0.75, edgecolor="white", linewidth=0.4, label=c)
ds = np.array([F(r, "d_RE_TM_nn_mean") for r in rows]); js = np.array([r["J"] for r in rows])
rr_ = np.corrcoef(ds, js)[0, 1]
a1.axvspan(3.15, 3.4, color=FE, alpha=0.08, lw=0); a1.text(3.16, 1.3, "open cages:\nH, metalloid shells", fontsize=7.5, color=FE)
a1.axvspan(2.85, 3.0, color=RE, alpha=0.08, lw=0); a1.text(2.86, 1.3, "12-fold, 2.9-3.0 Å:\nFe/Y hosts", fontsize=7.5, color=RE)
a1.set_xlabel("mean Gd-TM nearest-neighbour distance  (Å)", fontsize=9.5); a1.set_ylabel("J_eff  (meV / μB²)", fontsize=9.5)
a1.set_title(f"Coupling falls with RE-TM distance  (r = {rr_:.2f})", fontsize=9.5, color=INK); a1.grid(alpha=0.25); a1.legend(fontsize=8, frameon=False)
rng = np.random.default_rng(0)
for i, c in enumerate(("Fe", "Co", "Fe+Co")):
    v = np.array([r["J"] for r in rows if r["cls"] == c])
    a2.scatter(i + rng.uniform(-0.18, 0.18, len(v)), v, s=22, c=col[c], alpha=0.7, edgecolor="white", linewidth=0.4)
    a2.hlines(np.median(v), i - 0.3, i + 0.3, color=INK, lw=2)
    a2.text(i, 1.52, f"median {np.median(v):.2f}\nn = {len(v)}", ha="center", fontsize=8, color=INK)
a2.set_xticks([0, 1, 2]); a2.set_xticklabels(["Fe", "Co", "Fe+Co"]); a2.set_ylim(0, 1.7)
a2.set_title("Mixed Fe+Co couples hardest", fontsize=9.5, color=INK); a2.grid(alpha=0.25, axis="y")
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "trends_geometry.png")); plt.close(fig)

# ---------------------------------------------------------------- 3. validation J_RT
# Liebs-Fahnle two-sublattice convention: dE = 4 J_RT S_R S_T Z_RT  (S_R = 3.5, S_T = m_TM/2)
def jrt(r):
    return r["dE"] / (4 * 3.5 * (F(r, "m_TM_avg") / 2) * F(r, "N_TM_nn")) * 1.602   # 1e-22 J
val = [  # (our compound, label, expt value 1e-22 J, expt source, flag)
    ("GdFe2_validation", "GdFe₂", 2.99, "Liebs & Fähnle 1993 (expt. compilation)", ""),
    ("BFe14Gd2_nat", "Gd₂Fe₁₄B", 1.46, "Loewenhaupt et al., INS (LHF 1992 Tab. III)", ""),
    ("Fe5GdV_nat", "GdFe₁₀V₂", 1.30, "Duc et al. 1998, A_GdFe at x = 2", ""),
    ("Fe17Gd2N2_nat", "Gd₂Fe₁₇N₂ ↔ Ho₂Fe₁₇", 1.30, "Loewenhaupt INS, Ho₂Fe₁₇ 1.2-1.4 (no Gd₂Fe₁₇ in set)", "≈"),
]
fig, ax = plt.subplots(figsize=(6.4, 4.9), dpi=200)
ax.plot([0, 3.5], [0, 3.5], color=MUTE, lw=1, ls="--"); ax.fill_between([0, 3.5], [0, 2.8], [0, 4.2], color=MUTE, alpha=0.08, lw=0)
ax.text(2.55, 3.3, "±20 %", fontsize=8, color=MUTE)
for n, lab, ex, src, flag in val:
    r = next((r for r in rows if r["compound"] == n), None)
    if not r:
        continue
    ours = jrt(r)
    ax.scatter([ex], [ours], s=90, c=GOLD if not flag else "white", edgecolor=INK, linewidth=1.2, zorder=5)
    ax.annotate(f"{lab}\nexpt {ex:.2f}  ·  ours {ours:.2f}", (ex, ours), textcoords="offset points", xytext=(10, -4 if "GdFe₂" not in lab else -22), fontsize=7.6, color=INK)
# Duc early-TM trend as inset-like text
ax.text(0.12, 3.25, "Duc 1998, GdFe₁₂₋ₓVₓ: A_GdFe rises 1.13 → 2.25 (×10⁻²² J) for x = 0 → 4\nthis work: early-TM hosts J_eff ×0.97 of Fe baseline (CI 0.88-1.07) - no concentration series yet", fontsize=7.6, color=INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="#EEF2F7", ec="none"))
ax.set_xlim(0, 3.5); ax.set_ylim(0, 3.5)
ax.set_xlabel("J_RT, experiment  (10⁻²² J)", fontsize=10); ax.set_ylabel("J_RT, this work from the fm/ferri gap  (10⁻²² J)", fontsize=10)
ax.set_title("RE-TM exchange constant: campaign vs experiment (two-sublattice convention)", fontsize=9.5, color=INK)
ax.grid(alpha=0.25)
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "validation_jrt.png")); plt.close(fig)
print("J_RT ours:", {lab: round(jrt(next(r for r in rows if r["compound"] == n)), 2) for n, lab, *_ in val if any(r["compound"] == n for r in rows)})

# ---------------------------------------------------------------- 4. design-lever effect sizes
EARLY = {"Ti", "V", "Zr", "Nb", "Hf", "Ta", "Sc", "W", "Mo"}
METAL = {"B", "Si", "Al", "Ga", "Ge", "C", "P", "Be"}
def base(r):  # reference population: every Fe-only host
    return r["cls"] == "Fe"
B = np.array([r["J"] for r in rows if base(r)])
levers = [
    ("partial Co in Fe host (Brooks)", [r["J"] for r in rows if r["cls"] == "Fe+Co"]),
    ("Co instead of Fe", [r["J"] for r in rows if r["cls"] == "Co"]),
    ("early TM present (Duc)", [r["J"] for r in rows if r["els"] & EARLY and r["cls"] == "Fe"]),
    ("metalloid in formula (B, Si, Al, Ga, C, P)", [r["J"] for r in rows if r["els"] & METAL and r["cls"] == "Fe" and "H" not in r["els"]]),
    ("RE-TM distance > 3.15 Å", [r["J"] for r in rows if F(r, "d_RE_TM_nn_mean") > 3.15]),
    ("H interstitial", [r["J"] for r in rows if "H" in r["els"]]),
]
def boot_ratio(v, b, n=2000):
    v = np.array(v); out = []
    for _ in range(n):
        out.append(np.median(rng.choice(v, len(v))) / np.median(rng.choice(b, len(b))))
    return np.median(v) / np.median(b), np.percentile(out, 2.5), np.percentile(out, 97.5)
fig, ax = plt.subplots(figsize=(7.4, 4.6), dpi=200)
ys = np.arange(1, len(levers) + 1)[::-1]
for y, (lab, v) in zip(ys, levers):
    if len(v) < 2:
        continue
    m, lo, hi = boot_ratio(v, B)
    c = RE if m > 1.05 else (FE if m < 0.95 else MUTE)
    ax.errorbar([m], [y], xerr=[[m - lo], [hi - m]], fmt="o", color=c, ms=7, capsize=3, lw=1.4)
    ax.text(0.08, y, f"{lab}  (n={len(v)})", va="center", fontsize=8.6, color=INK)
    ax.text(hi + 0.04, y, f"×{m:.2f}", va="center", fontsize=8.6, color=c, fontweight="bold")
hJ = [r["J"] for r in rows if "H" in r["els"]]
ax.scatter([np.median(hJ) / np.median(B)], [0], marker="x", s=70, color=FE, zorder=5)
ax.text(0.3, 0, f"H interstitial  (n={len(hJ)}, single compound)   ×{np.median(hJ)/np.median(B):.2f}", va="center", fontsize=8.6, color=FE, fontweight="bold")
ax.axvline(1, color=INK, lw=1); ax.text(1.0, len(levers) + 0.45, f"baseline: all Fe-only hosts, n={len(B)}, median J_eff {np.median(B):.2f}", fontsize=7.8, color=INK, ha="center")
ax.set_yticks([]); ax.set_xlim(0.05, 2.1); ax.set_ylim(-0.6, len(levers) + 0.8)
ax.set_yticks([])
ax.set_xlabel("median J_eff relative to baseline  (bootstrap 95 % CI)", fontsize=9.5)
ax.set_title("What each design lever does to the RE-TM coupling, measured on the same 180 labels", fontsize=9.5, color=INK)
ax.grid(alpha=0.25, axis="x")
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "principles_effects.png")); plt.close(fig)

# ---------------------------------------------------------------- 5. Campbell projection of Ms
C_T = 9.274e-24 * 4 * 3.14159e-7 / 1e-30
GJJ = {"Pr": 3.20, "Nd": 3.27, "Sm": 0.71, "Gd": -7.0, "Tb": -9.0, "Dy": -10.0, "Ho": -10.0, "Er": -9.0, "Tm": -7.0}
hosts = []
for rel, rec in res.items():
    if not rec.get("credible"):
        continue
    fe = rec["ferri"]; tm = abs(fe["tm_moment_total"]); V = fe["volume_A3"]; n = fe["n_re"]
    name = rel.split("/")[-1]
    hosts.append((name, {k: (tm + n * g) / V * C_T for k, g in GJJ.items()}, abs(rec["dE_per_RE_meV"])))
hosts.sort(key=lambda h: -h[1]["Nd"]); hosts = hosts[:14]
def pretty(n):
    n = re.sub(r"_(sub|nat|validation)$", "", n)
    return re.sub(r"(\d+)", lambda m: "".join("₀₁₂₃₄₅₆₇₈₉"[int(c)] for c in m.group(1)), n)
fig, ax = plt.subplots(figsize=(8.6, 5.4), dpi=200)
yy = np.arange(len(hosts))[::-1]
mk = {"Nd": ("o", FE), "Sm": ("s", GOLD), "Gd": ("D", RE), "Tb": ("v", "#1F5F7A"), "Dy": ("<", "#123E52")}
for k, (m, c) in mk.items():
    ax.scatter([h[1][k] for h in hosts], yy, marker=m, s=46, c=c, edgecolor="white", linewidth=0.5, label=f"Gd → {k}" if k != "Gd" else "Gd (computed, ferri)", zorder=4)
for y, h in zip(yy, hosts):
    ax.plot([h[1]["Dy"], h[1]["Nd"]], [y, y], color="#D5DDE8", lw=2, zorder=1)
ax.set_yticks(yy); ax.set_yticklabels([pretty(h[0]) for h in hosts], fontsize=8)
for x, lab, tc in ((2.0, "MAGNITO target 2 T", INK), (1.78, "Sm(Fe,Co)₁₂ 1.78 T · 859 K", MUTE), (1.66, "NdFe₁₂N 1.66 T · 823 K", MUTE), (1.61, "Nd₂Fe₁₄B 1.61 T · 585 K", MUTE), (1.54, "Sm₂Fe₁₇N₃ 1.54 T · 749 K", MUTE), (1.25, "Sm₂Co₁₇ 1.25 T · 1190 K", MUTE)):
    ax.axvline(x, color=tc, lw=1.2 if tc == INK else 0.8, ls="-" if tc == INK else ":")
    ax.text(x, -1.1, lab, rotation=90, fontsize=6.8, color=tc, va="top", ha="center")
ax.set_xlim(-0.7, 2.3); ax.set_ylim(-6.2, len(hosts) - 0.4); ax.set_xlabel("projected μ₀Ms at 0 K  (T)   negative = RE sublattice dominates", fontsize=9.5)
ax.axvline(0, color=INK, lw=0.6)
ax.legend(fontsize=7.5, loc="lower left", frameon=False, ncol=3, bbox_to_anchor=(0.0, 0.0))
ax.set_title("Campbell's rule on the 14 best hosts: RE choice moves Ms by up to 2.5 T, host choice by 0.4 T", fontsize=9.5, color=INK)
ax.grid(alpha=0.25, axis="x")
fig.tight_layout(); fig.savefig(os.path.join(ASSETS, "campbell_ms.png")); plt.close(fig)
print("done; baseline n=%d median %.2f" % (len(B), np.median(B)))
