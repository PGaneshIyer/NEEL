#!/usr/bin/env python3
"""Gaussian-process wave selection for the NEEL screen.

Training data
  * the credible Gd fm/ferri pairs (results.json): label h = TM-tied RE 5d
    polarisation from the pair (apply_5d_method), gap = |dE| per Gd
  * every ingested f-in-core wave run (analysis/pool/labels.csv): label h
    measured directly, with the RE one-hot recording that it is a light-RE run
Features: wave_features.py geometry descriptors + RE one-hot (Gd/Nd/Sm/Pr).

Model: two-stage, following the causal picture (every host lever acts through
the 5d polarisation)
  stage 1  h ~ GP( mean = ridge regression on features, kernel = Matern-5/2 + white )
  stage 2  gap_RE = 1574 * h * (gJ-1)J_RE / 3.5   (deterministic, calibrated r = 0.89)
           T*     = gap_RE / (2 k_B)
  Ms       analytic from the pool row (Fe/Co moments x density + free-ion RE)
Acquisition (two options)
  ts  (default)  batch Thompson sampling: one joint posterior draw per pick, the
                 constraints evaluated under the draw, utility Ms x min(1, gap/gap_min).
                 Diversity comes from posterior uncertainty, as in Bagchi et al.,
                 arXiv:2504.05539 (HPC-driven ensemble sampling).
  ucb            feasibility P(gap_RE >= gap_min) x 1[Ms] x 1[hull] x (1 + kappa sigma),
                 greedy with a kriging-believer penalty - the deterministic baseline.
  Both keep a per-prototype cap. The 'score' column is the number of posterior draws
  a candidate won (ts) or the UCB score (ucb).
Writes analysis/pool/wave_<k>.csv (the wave) and analysis/pool/gp_report.txt.

Usage:  python3 wave_gp.py --wave 1 --size 120 [--acq ts|ucb --gap-min 100 --ms-min 1.5 --hull-max 30 --proto-cap 6]
        python3 wave_gp.py --cv            # leave-one-out check of the GP on the training set
"""
import argparse
import csv
import json
import os
import sys

import numpy as np
from pymatgen.core import Structure

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wave_features as WF

OUT = os.path.join(HERE, "analysis", "pool")
K_H = 1574.0
KB = 0.08617
GJ1J = {"Gd": 3.5, "Nd": 1.227, "Sm": 1.786, "Pr": 0.8}
RE_ONEHOT = ["Gd", "Nd", "Sm", "Pr"]


# ------------------------------------------------------------------ training set
def gd_training_rows():
    import apply_5d_method as A5
    res = json.load(open(os.path.join(HERE, "results.json")))
    rows = []
    for rel, rec in res.items():
        if not rec.get("credible"):
            continue
        base = os.path.join(HERE, "runs", rel)
        pos = os.path.join(base, "ferri", "POSCAR")
        if not os.path.isfile(pos):
            continue
        try:
            els = A5.species(pos)
            a = A5.re_nonf(os.path.join(base, "fm/OUTCAR"), els); b = A5.re_nonf(os.path.join(base, "ferri/OUTCAR"), els)
            s = Structure.from_file(pos)
        except Exception:
            continue
        if not a or not b:
            continue
        f = WF.features(s, "Gd")
        if f is None:
            continue
        f.update({"name": rel.split("/")[-1], "h": -(a[0] + b[0]) / 2, "gap_meV": abs(rec["dE_per_RE_meV"]),
                  "label_source": "Gd-pair", "polytype": rel.split("/")[2]})
        rows.append(f)
    return rows


def wave_training_rows():
    p = os.path.join(OUT, "labels.csv")
    if not os.path.isfile(p):
        return []
    rows = []
    for r in csv.DictReader(open(p)):
        if r.get("h") in ("", None):
            continue
        rr = {k: float(r[k]) for k in WF.FEATURES if r.get(k) not in ("", None)}
        rr.update({"re_el": r["re_el"], "name": r["name"], "h": float(r["h"]), "label_source": "f-in-core", "polytype": r.get("polytype", "")})
        rows.append(rr)
    return rows


def design(rows):
    X = np.array([[float(r[k]) for k in WF.FEATURES] + [1.0 if r["re_el"] == e else 0.0 for e in RE_ONEHOT] for r in rows])
    return X


# ------------------------------------------------------------------ model
class TwoStageGP:
    def __init__(self):
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        self.sc = StandardScaler()
        self.mean = Ridge(alpha=1.0)
        k = ConstantKernel(0.05, (1e-3, 1.0)) * Matern(length_scale=np.ones(len(WF.FEATURES) + len(RE_ONEHOT)) * 2.0, length_scale_bounds=(0.3, 30.0), nu=2.5) \
            + WhiteKernel(1e-3, (1e-5, 1e-1))
        self.gp = GaussianProcessRegressor(kernel=k, normalize_y=False, n_restarts_optimizer=3, random_state=0)

    def fit(self, X, y):
        Xs = self.sc.fit_transform(X)
        self.mean.fit(Xs, y)
        self.gp.fit(Xs, y - self.mean.predict(Xs))
        return self

    def predict(self, X):
        Xs = self.sc.transform(X)
        mu_r, sd = self.gp.predict(Xs, return_std=True)
        return self.mean.predict(Xs) + mu_r, sd


def loo(X, y, names):
    from sklearn.model_selection import KFold
    pred, sd = np.zeros_like(y), np.zeros_like(y)
    for tr, te in KFold(10, shuffle=True, random_state=0).split(X):
        m = TwoStageGP().fit(X[tr], y[tr]); pred[te], sd[te] = m.predict(X[te])
    r = np.corrcoef(pred, y)[0, 1]; rmse = np.sqrt(np.mean((pred - y) ** 2))
    z = (y - pred) / sd
    print(f"10-fold CV on h: r = {r:.2f}  RMSE = {rmse:.3f} muB  (y sd {y.std():.3f})   |z|<2 for {np.mean(np.abs(z) < 2)*100:.0f}% (calibration)")
    worst = np.argsort(-np.abs(pred - y))[:5]
    for i in worst:
        print(f"   miss: {names[i]:<24} h={y[i]:.3f} pred={pred[i]:.3f}±{sd[i]:.3f}")
    return r, rmse


# ------------------------------------------------------------------ acquisition
def acquire(pool, mu, sd, A, train_X_s, sc):
    from scipy.stats import norm
    gap_min, ms_min, hull_max = A.gap_min, A.ms_min, A.hull_max
    score = np.zeros(len(pool)); feas = np.zeros(len(pool)); gap_mu = np.zeros(len(pool))
    for i, r in enumerate(pool):
        re_ = r["re_el"]; scale = K_H * GJ1J[re_] / 3.5
        gm, gs = mu[i] * scale, sd[i] * scale
        gap_mu[i] = gm
        p_gap = 1 - norm.cdf((gap_min - gm) / max(gs, 1e-6))
        ms_ok = float(r["Ms_proj_T"] or 0) >= ms_min
        eh = r.get("E_hull_meV")
        hull_ok = (eh not in ("", None)) and float(eh) <= hull_max
        feas[i] = p_gap * (1.0 if ms_ok else 0.0) * (1.0 if hull_ok else 0.0)
    expl = sd / max(np.median(sd), 1e-6)
    score = feas * (1 + A.kappa * expl)
    # greedy with kriging-believer style penalty + prototype cap
    Xp = sc.transform(design(pool))
    chosen, per_proto = [], {}
    live = score.copy()
    for _ in range(A.size):
        j = int(np.argmax(live))
        if live[j] <= 0:
            break
        proto = (pool[j]["spacegroup"], round(float(pool[j]["TM_per_RE"]) * 2) / 2)   # family = space group + TM:RE ratio
        if per_proto.get(proto, 0) >= A.proto_cap:
            live[j] = 0; continue
        chosen.append(j); per_proto[proto] = per_proto.get(proto, 0) + 1
        d = np.linalg.norm(Xp - Xp[j], axis=1)
        live *= (1 - 0.6 * np.exp(-(d / 1.0) ** 2))     # neighbours in feature space lose 60 % of their score
        live[j] = 0
    return chosen, score, feas, gap_mu


def acquire_ts(pool, model, A, seed=0):
    """Batch Thompson sampling with constraints (Bagchi et al. 2025 style, BoTorch-free).
    Each pick: draw ONE joint posterior sample of h over the whole pool, convert it to
    gap_RE, keep the candidates that satisfy the constraints UNDER THAT SAMPLE, and take
    the one with the largest sampled utility  U = Ms_proj * min(1, gap_s / gap_min)
    (Ms is the quantity we want large; the gap is a threshold that must be met, so it
    enters as a soft saturation rather than a product that would reward over-coupling).
    Diversity comes from the posterior itself: candidates the GP is unsure about win
    some draws and lose others. A prototype cap is kept as a guard."""
    rng = np.random.default_rng(seed)
    Xs = model.sc.transform(design(pool))
    mean = model.mean.predict(Xs)
    n_draw = max(4 * A.size, 64)
    samples = model.gp.sample_y(Xs, n_samples=n_draw, random_state=int(rng.integers(1e9)))   # (n_pool, n_draw) residuals
    scale = np.array([K_H * GJ1J[r["re_el"]] / 3.5 for r in pool])
    ms = np.array([float(r["Ms_proj_T"] or 0) for r in pool])
    hull_ok = np.array([(r.get("E_hull_meV") not in ("", None)) and float(r["E_hull_meV"]) <= A.hull_max for r in pool])
    base_ok = hull_ok & (ms >= A.ms_min)
    chosen, per_proto, wins = [], {}, np.zeros(len(pool))
    for d in range(n_draw):
        gap_s = (mean + samples[:, d]) * scale
        util = np.where(base_ok, ms * np.minimum(1.0, gap_s / A.gap_min), -1.0)
        util = np.where(gap_s >= A.gap_min, util, -1.0)        # infeasible under this draw -> cannot win it
        order = np.argsort(-util)
        for j in order:
            if util[j] <= 0:
                break
            proto = (pool[j]["spacegroup"], round(float(pool[j]["TM_per_RE"]) * 2) / 2)   # family = space group + TM:RE ratio
            if j in chosen or per_proto.get(proto, 0) >= A.proto_cap:
                continue
            chosen.append(int(j)); per_proto[proto] = per_proto.get(proto, 0) + 1; wins[j] += 1
            break
        if len(chosen) >= A.size:
            break
    mu, sd = model.predict(design(pool))
    gap_mu = mu * scale
    from scipy.stats import norm
    feas = (1 - norm.cdf((A.gap_min - gap_mu) / np.maximum(sd * scale, 1e-6))) * base_ok
    return chosen, wins, feas, gap_mu


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--acq", choices=["ts", "ucb"], default="ts", help="ts = batch Thompson sampling (default); ucb = feasibility x (1 + kappa sigma) greedy")
    ap.add_argument("--wave", type=int, default=1)
    ap.add_argument("--size", type=int, default=40)
    ap.add_argument("--gap-min", type=float, default=100.0, help="meV per RE for the ACTUAL RE; 100 meV ~ T* 580 K, the Nd2Fe14B level (its Gd gap 304 meV scales to 107 meV for Nd)")
    ap.add_argument("--ms-min", type=float, default=1.5)
    ap.add_argument("--hull-max", type=float, default=30.0)
    ap.add_argument("--kappa", type=float, default=1.0)
    ap.add_argument("--proto-cap", type=int, default=6)
    ap.add_argument("--cv", action="store_true")
    ap.add_argument("--only-source", default="", help="restrict the pool to these sources (comma list), e.g. kagome")
    A = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    train = gd_training_rows() + wave_training_rows()
    X = design(train); y = np.array([r["h"] for r in train]); names = [r["name"] for r in train]
    print(f"training rows: {len(train)}  (Gd pairs {sum(r['label_source']=='Gd-pair' for r in train)}, f-in-core {sum(r['label_source']=='f-in-core' for r in train)})")
    if A.cv:
        loo(X, y, names); return
    model = TwoStageGP().fit(X, y)
    pool_csv = os.path.join(OUT, "pool.csv")
    if not os.path.isfile(pool_csv):
        sys.exit("no pool.csv - run wave_pool.py first")
    pool = [r for r in csv.DictReader(open(pool_csv)) if r.get("re_el")]
    # a same-model hull cannot be more than a few tens of meV BELOW the MP hull; anything wilder is a
    # bookkeeping failure (composition/energy mismatch) and must not pass as 'stable'
    for r in pool:
        if r.get("E_hull_meV") not in ("", None) and not (-80.0 <= float(r["E_hull_meV"]) <= 2000.0):
            r["E_hull_meV"] = ""
    # the same (formula, space group) can enter from several sources / pool runs: keep the lowest-hull copy
    best = {}
    for r in pool:
        key = (r["formula"], r["spacegroup"])
        eh = float(r["E_hull_meV"]) if r.get("E_hull_meV") not in ("", None) else 1e9
        if key not in best or eh < best[key][0]:
            best[key] = (eh, r)
    pool = [v[1] for v in best.values()]
    if A.only_source:
        pool = [r for r in pool if r["source"] in A.only_source.split(",")]
    # exclude anything already run or queued
    done = set()
    for p in (os.path.join(OUT, "labels.csv"), *[os.path.join(OUT, f"wave_{k}.csv") for k in range(1, A.wave)]):
        if os.path.isfile(p):
            done |= {r["cid"] for r in csv.DictReader(open(p)) if r.get("cid")}
    pool = [r for r in pool if r["cid"] not in done]
    mu, sd = model.predict(design(pool))
    if A.acq == "ts":
        chosen, score, feas, gap_mu = acquire_ts(pool, model, A)
    else:
        chosen, score, feas, gap_mu = acquire(pool, mu, sd, A, None, model.sc)
    rows = []
    for j in chosen:
        r = dict(pool[j]); r.update({"h_pred": round(mu[j], 3), "h_sd": round(sd[j], 3), "gap_pred_meV": round(gap_mu[j], 0),
                                     "T_star_pred_K": round(gap_mu[j] / (2 * KB), 0), "p_feasible": round(feas[j], 3), "score": round(score[j], 3), "wave": A.wave})
        rows.append(r)
    out = os.path.join(OUT, f"wave_{A.wave}.csv")
    keys = ["cid", "wave", "tag", "source", "parent", "formula", "spacegroup", "re_el", "Ms_proj_T", "E_hull_meV", "h_pred", "h_sd", "gap_pred_meV", "T_star_pred_K", "p_feasible", "score", "TM_per_RE", "tm_density", "f_Fe", "poscar"]
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    with open(os.path.join(OUT, "gp_report.txt"), "a") as f:
        f.write(f"wave {A.wave} [{A.acq}]: pool {len(pool)}  feasible {int((feas>0).sum())}  chosen {len(rows)}  "
                f"kernel {model.gp.kernel_}\n")
    print(f"pool {len(pool)}, feasible {int((feas > 0).sum())}, chosen {len(rows)} -> {out}")
    print(f"{'formula':<16}{'RE':>3}{'Ms':>6}{'Ehull':>7}{'h_pred':>8}{'±':>6}{'gap':>6}{'T*':>6}{'P':>6}{'score':>7}  source")
    for r in rows[:25]:
        print(f"{r['formula']:<16}{r['re_el']:>3}{float(r['Ms_proj_T']):6.2f}{float(r['E_hull_meV'] or 0):7.1f}{r['h_pred']:8.3f}{r['h_sd']:6.3f}{r['gap_pred_meV']:6.0f}{r['T_star_pred_K']:6.0f}{r['p_feasible']:6.2f}{r['score']:7.2f}  {r['source']}")
    print(f"kernel: {model.gp.kernel_}")


if __name__ == "__main__":
    main()
