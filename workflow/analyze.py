#!/usr/bin/env python3
"""Analyze paired fm/ferri VASP runs: energy difference, converged site moments,
and whether each run actually stayed in its intended spin configuration.

Stdlib only (runs anywhere, including Perlmutter login nodes).

Usage:  python3 analyze.py [runs_dir]
Writes results.json next to runs/ and prints a summary table.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def final_energy(oszicar):
    """Last E0 from OSZICAR (sigma->0 energy)."""
    e = None
    with open(oszicar) as f:
        for line in f:
            m = re.search(r"E0=\s*([-+.\dEe]+)", line)
            if m:
                e = float(m.group(1))
    return e


def electronic_converged(outcar_text, nelm):
    """True unless the last SCF loop hit NELM without EDIFF being reached."""
    if "aborting loop because EDIFF is reached" in outcar_text:
        return True
    # count electronic steps of last ionic step from OSZICAR-style lines in OUTCAR
    its = re.findall(r"Iteration\s+\d+\(\s*(\d+)\)", outcar_text)
    return bool(its) and int(its[-1]) < nelm


def site_moments(outcar_text):
    """Per-ion total moments from the last 'magnetization (x)' block."""
    blocks = outcar_text.split("magnetization (x)")
    if len(blocks) < 2:
        return None
    rows = []
    for line in blocks[-1].splitlines():
        m = re.match(r"\s*(\d+)\s+([-+.\d]+\s+)+", line)
        if m:
            rows.append(float(line.split()[-1]))
        elif rows and ("----" in line or "tot" in line):
            break
    return rows or None


def species_list(poscar):
    with open(poscar) as f:
        lines = f.read().splitlines()
    syms, counts = lines[5].split(), [int(x) for x in lines[6].split()]
    out = []
    for s, n in zip(syms, counts):
        out += [s] * n
    return out


def total_moment(oszicar):
    """Net cell moment in mu_B, from the 'mag=' field of the last ionic line.

    This is the real net moment: the Gd POTCAR keeps 4f in the valence, so the
    rare-earth contribution is already in it (unlike the f-in-core potentials the
    big databases use, where the reported magnetisation EXCLUDES the 4f).
    """
    mag = None
    with open(oszicar) as f:
        for line in f:
            m = re.search(r"mag=\s*([-+.\dEe]+)", line)
            if m:
                mag = float(m.group(1))
    return mag


def cell_volume(rundir):
    """Cell volume in A^3. Prefer OUTCAR's own value, else compute from POSCAR."""
    outc = os.path.join(rundir, "OUTCAR")
    if os.path.exists(outc):
        v = None
        with open(outc, errors="replace") as f:
            for line in f:
                m = re.search(r"volume of cell\s*:\s*([\d.]+)", line)
                if m:
                    v = float(m.group(1))
        if v:
            return v
    for name in ("CONTCAR", "POSCAR"):
        p = os.path.join(rundir, name)
        if not os.path.exists(p):
            continue
        try:
            L = open(p).read().splitlines()
            scale = float(L[1].split()[0])
            a, b, c = ([float(x) * scale for x in L[i].split()[:3]] for i in (2, 3, 4))
            return abs(a[0] * (b[1] * c[2] - b[2] * c[1])
                       - a[1] * (b[0] * c[2] - b[2] * c[0])
                       + a[2] * (b[0] * c[1] - b[1] * c[0]))
        except Exception:
            pass
    return None


# mu0 * mu_B / Angstrom^3, in tesla: 1 mu_B per A^3 == 11.654 T
MU0MB_PER_A3 = 11.654

# Free-ion total moments g_J * J, in mu_B, for the RE that could sit on the site
# the calculation put Gd on.
#
# The sign convention is the whole point. A collinear calculation returns SPIN
# moments, and by the Campbell chain the 4f spin is antiparallel to Fe for EVERY
# rare earth. What differs is Hund's third rule:
#   heavy RE (more than half-filled, J = L + S): total moment follows the spin
#                                                 -> antiparallel to Fe, ferrimagnet
#   light RE (less than half-filled, J = |L - S|): total moment OPPOSES the spin
#                                                 -> parallel to Fe, ferromagnet
# So a light RE flips the sign of the contribution without changing the exchange.
GJ_J = {"Gd": 7.0, "Tb": 9.0, "Dy": 10.0, "Ho": 10.0, "Er": 9.0, "Tm": 7.0,
        "Nd": 3.27, "Sm": 0.71, "Pr": 3.20, "Ce": 2.14}
LIGHT_RE = {"Ce", "Pr", "Nd", "Sm"}          # J = |L - S|: moment opposes spin


def mu0Ms(moment_uB, volume_A3):
    if moment_uB is None or not volume_A3:
        return None
    return round(MU0MB_PER_A3 * abs(moment_uB) / volume_A3, 3)


def parent_moment(m_total, re_site_moments, parent_el):
    """Predicted net moment of the parent compound, in mu_B.

    The calculation is on the Gd surrogate. Swap the computed Gd contribution out
    and the parent's free-ion moment in, keeping the SIGN that the calculation
    found - that sign is the physics the campaign measured, and by the Campbell
    chain it is the same for every heavy RE.
    """
    if m_total is None or not re_site_moments:
        return None
    gj = GJ_J.get(parent_el)
    if gj is None:
        return None
    flip = -1 if parent_el in LIGHT_RE else 1
    swapped = sum(flip * (1 if m >= 0 else -1) * gj for m in re_site_moments)
    return round(m_total - sum(re_site_moments) + swapped, 3)


def analyze_run(d, re_el, tm_els):
    osz, outc, posc = (os.path.join(d, f) for f in ("OSZICAR", "OUTCAR", "POSCAR"))
    if not (os.path.exists(osz) and os.path.exists(outc)):
        return {"status": "not_run"}
    text = open(outc, errors="replace").read()
    e0 = final_energy(osz)
    nelm_m = re.search(r"NELM\s*=\s*(\d+)", text)
    conv = electronic_converged(text, int(nelm_m.group(1)) if nelm_m else 200)
    moms = site_moments(text)
    vol = cell_volume(d)
    mtot = total_moment(osz)
    # Was the total moment constrained (NUPDOWN)? A fixed-spin-moment energy is
    # not comparable with a freely-relaxed one, so both halves of a pair must
    # have been run the same way for dE to mean anything.
    nup = re.search(r"NUPDOWN\s*=\s*([-\d.]+)", text)
    nupdown = float(nup.group(1)) if nup else None
    if nupdown is not None and nupdown < 0:
        nupdown = None          # VASP prints -1 when the moment is unconstrained
    # A constrained run can only be trusted if its state is not absurdly far
    # above the freely-relaxed one: NUPDOWN forces a total moment, and where the
    # true moment is very different (Fe is genuinely low-spin in the phosphides,
    # for instance) it manufactures a high-energy state that is not the ground
    # state at all. Compare against the archived unconstrained attempt.
    e_free = None
    for prev in sorted(f for f in os.listdir(d) if f.startswith("OSZICAR_")):
        e_free = final_energy(os.path.join(d, prev)) or e_free
    natoms = None
    try:
        natoms = sum(int(x) for x in open(posc).read().splitlines()[6].split())
    except Exception:
        pass
    penalty = None
    if e0 is not None and e_free is not None and natoms:
        penalty = round((e0 - e_free) * 1000.0 / natoms, 1)   # meV/atom

    res = {"status": "converged" if conv else "NOT_CONVERGED", "E0_eV": e0,
           "nupdown": nupdown, "constrained": nupdown is not None,
           "E_unconstrained_eV": e_free, "constraint_penalty_meV_atom": penalty,
           "volume_A3": round(vol, 2) if vol else None,
           "total_moment_uB": mtot,
           "mu0Ms_T": mu0Ms(mtot, vol)}
    if moms:
        species = species_list(posc)
        fe = [m for s, m in zip(species, moms) if s in tm_els]
        rem = [m for s, m in zip(species, moms) if s == re_el]
        res["tm_moment_avg"] = round(sum(fe) / len(fe), 3) if fe else None
        res["tm_moment_total"] = round(sum(fe), 3) if fe else None
        res["re_moment_avg"] = round(sum(rem) / len(rem), 3) if rem else None
        res["re_moment_total"] = round(sum(rem), 3) if rem else None
        res["re_site_moments"] = [round(m, 3) for m in rem]
        res["n_re"] = len(rem)
        # Any OTHER magnetic element besides the declared RE/TM (Mn, Cr, Ni, ...
        # showing up as a GNoME-generated minority substituent) is otherwise
        # invisible to the consistency check below. Record its average moment
        # per species so a hidden third sublattice can be screened too.
        other = {}
        for s, m in zip(species, moms):
            if s in tm_els or s == re_el:
                continue
            other.setdefault(s, []).append(m)
        if other:
            res["other_moments_avg"] = {el: round(sum(v) / len(v), 3)
                                        for el, v in other.items()}
    return res


def main():
    runs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "runs")
    meta = {}
    for reg_file in ("compounds.json", "compounds_campaign.json"):
        p = os.path.join(HERE, reg_file)
        if os.path.exists(p):
            for c in json.load(open(p))["compounds"]:
                meta[c["name"]] = c
    # runs are nested as runs/<arity>/<HREE>/<polytype>/<compound>/<fm|ferri>;
    # find every directory that has an fm or ferri child.
    bases = sorted(root for root, dirs, _ in os.walk(runs)
                   if {"fm", "ferri"} & set(dirs))
    results = {}
    for base in bases:
        name = os.path.basename(base)
        rel = os.path.relpath(base, runs)   # arity/HREE/polytype/compound
        c = meta.get(name, {})
        mp = os.path.join(base, "meta.json")   # written by make_inputs.py
        if os.path.exists(mp):
            try:
                c = {**c, **json.load(open(mp))}
            except Exception:
                pass
        re_el, tm_els = c.get("re_element", "Gd"), c.get("tm_elements", ["Fe"])
        r = {cfg: analyze_run(os.path.join(base, cfg), re_el, tm_els)
             for cfg in ("fm", "ferri")}
        # did each run keep its intended RE orientation?
        for cfg, want in (("fm", +1), ("ferri", -1)):
            mre, mtm = r[cfg].get("re_moment_avg"), r[cfg].get("tm_moment_avg")
            if mre is not None and mtm is not None and abs(mtm) > 0.3:
                ok = (mre * mtm > 0) == (want > 0)
                r[cfg]["kept_intended_config"] = ok
        efm, eferri = r["fm"].get("E0_eV"), r["ferri"].get("E0_eV")
        if efm is not None and eferri is not None:
            n_re = r["fm"].get("n_re") or 1
            de = (eferri - efm) * 1000.0
            r["dE_ferri_minus_fm_meV"] = round(de, 2)
            r["dE_per_RE_meV"] = round(de / n_re, 2)
            r["ground_state"] = "ferrimagnetic" if de < 0 else "ferromagnetic"

            # Magnetisation of the GROUND STATE - the configuration that actually
            # wins, not whichever config happens to have the bigger moment.
            gs = "ferri" if de < 0 else "fm"
            g = r[gs]
            r["ground_state_config"] = gs
            r["net_moment_uB"] = g.get("total_moment_uB")
            r["mu0Ms_T"] = g.get("mu0Ms_T")

            # The calculation is on Gd. Predict each parent HREE's magnetisation
            # by swapping Gd's computed contribution for the parent free-ion
            # moment, keeping the sign the calculation found.
            prov0 = (c.get("provenance") or {})
            parents = prov0.get("parent_hree") or ([re_el] if re_el else [])
            preds = {}
            for p_el in parents:
                mp_ = parent_moment(g.get("total_moment_uB"),
                                    g.get("re_site_moments"), p_el)
                if mp_ is not None:
                    preds[p_el] = {"net_moment_uB": mp_,
                                   "mu0Ms_T": mu0Ms(mp_, g.get("volume_A3"))}
            if preds:
                r["predicted_by_RE"] = preds
            # Every Gd result also predicts its LIGHT-RE analogue: same exchange,
            # opposite J projection, so the RE moment adds instead of subtracting.
            light = {}
            for p_el in ("Sm", "Nd"):
                mp_ = parent_moment(g.get("total_moment_uB"),
                                    g.get("re_site_moments"), p_el)
                if mp_ is not None:
                    light[p_el] = {"net_moment_uB": mp_,
                                   "mu0Ms_T": mu0Ms(mp_, g.get("volume_A3"))}
            if light:
                r["predicted_light_RE"] = light

            # --- is the fm/ferri comparison even valid? -------------------
            # dE only means "RE-TM coupling" if the two runs differ ONLY by the
            # RE flip. Two silent ways that fails, both seen in this campaign:
            #   * the TM sublattice also changes (the ferri SCF finds a low-spin
            #     or collapsed Fe solution instead of Gd-down/Fe-up), so dE is a
            #     TM-sublattice energy, not a coupling energy;
            #   * there is no TM moment at all, so there is nothing to couple to
            #     and the compound is not a magnet whatever the sign says.
            # a constrained energy cannot be compared with an unconstrained one
            if r["fm"].get("constrained") != r["ferri"].get("constrained"):
                r.setdefault("_mixed", True)
            tf = r["fm"].get("tm_moment_avg")
            tfe = r["ferri"].get("tm_moment_avg")
            problems = []
            # An unconverged run has no energy worth comparing. This was never
            # in the validity list - B2Fe7Gd3_sub (ferri NOT_CONVERGED) and
            # Fe14Gd3Lu_sub (both NOT_CONVERGED) were reported as credible
            # ferromagnets with dE of 336 and 479 meV/RE (found 2026-10-10).
            for cfg in ("fm", "ferri"):
                st = r[cfg].get("status")
                if st and st != "converged":
                    problems.append(f"{cfg}:{st}")
            # Within one configuration every RE site must be in the same state:
            # same sign, and magnitudes within ~1 mu_B of each other (Gd 4f7 is
            # 6.7-7.1 everywhere it converged cleanly). A site at +6.7 among
            # -7.0s, or at 4.1 among 6.9s, is a partially flipped / half-
            # collapsed cell, not a magnetic configuration - the per-site
            # tables of the two false positives above, and of the broken
            # Tier-2 heavy-RE runs, all look like this.
            for cfg in ("fm", "ferri"):
                rs = r[cfg].get("re_site_moments") or []
                if len(rs) >= 2:
                    if any(m * rs[0] < 0 for m in rs):
                        problems.append(f"{cfg}:RE_SITES_SPLIT")
                    elif max(rs) - min(rs) > 1.0:
                        problems.append(f"{cfg}:RE_SITES_UNEQUAL")
            if tf is not None and tfe is not None:
                scale = max(abs(tf), abs(tfe), 1e-9)
                if abs(abs(tf) - abs(tfe)) > 0.25 * scale:
                    problems.append("TM_SUBLATTICE_CHANGED")
            gmt = g.get("tm_moment_avg")
            if gmt is not None and abs(gmt) < 0.5:
                problems.append("NO_TM_MOMENT")
            if abs(de / (n_re or 1)) < 25:
                problems.append("dE_WITHIN_NOISE")
            # Every credible ferrimagnet in this campaign sits within -50 to
            # -400 meV/Gd - the real scale of RE-TM exchange. A dE of several
            # eV/Gd is not a coupling energy; it is almost always the LDA+U
            # multi-minima problem (LDAUTYPE=2 landing in a different
            # self-consistent occupation matrix, unrelated to magnetism), and
            # none of the other checks catch it because both runs converge,
            # keep their configuration, and keep the same TM moment.
            if abs(de / (n_re or 1)) > 600:
                problems.append("EXCHANGE_ENERGY_IMPLAUSIBLE")
            # A third magnetic element (Mn, Cr, Ni ... a minority GNoME
            # substituent) must keep BOTH its magnitude and its orientation
            # relative to the TM sublattice between fm and ferri. Magnitude:
            # collapsing/exploding like Fe/Co in the TM_SUBLATTICE_CHANGED cases.
            # Sign relative to TM: if it flips, the two runs differ by more than
            # the RE reversal and dE is not the RE-TM coupling energy. An earlier
            # version of this check deliberately ignored sign ("the spectator
            # may legitimately track the RE") - that let Co16Gd2Mn through as
            # the campaign's one "credible ferromagnet": Mn kept |m|~3.1-3.4 but
            # sat with Co in fm and against Co in ferri, i.e. the ferri run was a
            # metastable basin ~650 meV above the true ferrimagnet (Mn with Co),
            # found only when the locked relax was released (2026-10-10).
            om_fm = r["fm"].get("other_moments_avg") or {}
            om_fe = r["ferri"].get("other_moments_avg") or {}
            for el in sorted(set(om_fm) | set(om_fe)):
                a, b = om_fm.get(el), om_fe.get(el)
                if a is None or b is None or max(abs(a), abs(b)) < 0.3:
                    continue
                scale = max(abs(a), abs(b), 1e-9)
                if abs(abs(a) - abs(b)) > 0.25 * scale:
                    problems.append(f"OTHER_SUBLATTICE_CHANGED:{el}")
                if tf is not None and tfe is not None and abs(tf) > 0.3 and abs(tfe) > 0.3:
                    if (a * tf > 0) != (b * tfe > 0):
                        problems.append(f"SPECTATOR_FLIPPED:{el}")
            if r.pop("_mixed", False):
                problems.insert(0, "MIXED_CONSTRAINT")
            for cfg in ("fm", "ferri"):
                pen = r[cfg].get("constraint_penalty_meV_atom")
                if pen is not None and pen > 50:
                    problems.append(f"{cfg}:CONSTRAINT_UNPHYSICAL")
                if pen is not None and pen < -500:
                    problems.append(f"{cfg}:ENERGY_DIVERGED")
            r["validity"] = problems or ["ok"]
            r["credible"] = not problems
        prov = c.get("provenance") or {}
        r["kind"] = c.get("kind") or prov.get("kind")
        r["polytype"] = c.get("polytype")
        if prov.get("parents"):
            r["applies_to_parents"] = prov["parents"]
            r["parent_hree"] = prov.get("parent_hree")
        results[rel] = r

    out = os.path.join(HERE, "results.json")
    json.dump(results, open(out, "w"), indent=1)

    def flags_for(r):
        f = []
        for cfg in ("fm", "ferri"):
            st = r[cfg].get("status")
            if st == "not_run":
                f.append(f"{cfg}:not_run")
            elif st == "NOT_CONVERGED":
                f.append(f"{cfg}:NOT_CONVERGED")
            elif r[cfg].get("kept_intended_config") is False:
                f.append(f"{cfg}:FLIPPED")
        f += [v for v in (r.get("validity") or []) if v != "ok"]
        return f

    print(f"{'arity/HREE/polytype/compound':<42}{'dE/RE (meV)':>12}{'ground state':>15}"
          f"{'net m (uB)':>11}{'u0Ms (T)':>10}  flags")
    done = 0
    for name, r in results.items():
        fl = flags_for(r)
        if r.get("ground_state"):
            done += 1
        print(f"{name:<42}"
              f"{str(r.get('dE_per_RE_meV', '-')):>12}"
              f"{str(r.get('ground_state', '-')):>15}"
              f"{str(r.get('net_moment_uB', '-')):>11}"
              f"{str(r.get('mu0Ms_T', '-')):>10}  {' '.join(fl) or 'ok'}")

    # flat CSV, one row per compound, with the per-parent magnetisation estimates
    csv_path = os.path.join(HERE, "results_summary.csv")
    cols = ["path", "compound", "kind", "polytype", "ground_state", "dE_per_RE_meV",
            "net_moment_uB", "mu0Ms_T", "volume_A3", "tm_moment_total",
            "re_moment_total", "n_re", "flags", "validity", "credible",
            "predicted_RE", "applies_to_parents"]
    with open(csv_path, "w") as f:
        f.write(",".join(cols) + "\n")
        for name, r in results.items():
            g = r.get(r.get("ground_state_config") or "fm", {})
            preds = r.get("predicted_by_RE") or {}
            pred_s = " ".join(f"{k}:{v['mu0Ms_T']}T" for k, v in sorted(preds.items())
                              if v.get("mu0Ms_T") is not None)
            row = [name, os.path.basename(name), r.get("kind") or "", r.get("polytype") or "",
                   r.get("ground_state") or "", r.get("dE_per_RE_meV"),
                   r.get("net_moment_uB"), r.get("mu0Ms_T"), g.get("volume_A3"),
                   g.get("tm_moment_total"), g.get("re_moment_total"), g.get("n_re"),
                   ";".join(flags_for(r)) or "ok",
                   ";".join(r.get("validity") or []), r.get("credible"), pred_s,
                   " ".join(r.get("applies_to_parents") or [])]
            f.write(",".join('"%s"' % ("" if v is None else v) for v in row) + "\n")

    # rank the magnets, not the calculations
    ranked = sorted(((r.get("mu0Ms_T") or 0, n, r) for n, r in results.items()
                     if r.get("mu0Ms_T") and r.get("credible")
                     and not flags_for(r)), reverse=True)[:10]
    if ranked:
        print(f"\nhighest magnetisation, CREDIBLE results only ({done} compounds complete):")
        print(f"  {'compound':<28}{'u0Ms (T)':>9}{'state':>16}   predicted for parent RE")
        for ms, n, r in ranked:
            preds = r.get("predicted_by_RE") or {}
            ps = "  ".join(f"{k} {v['mu0Ms_T']}T" for k, v in sorted(preds.items())
                           if v.get("mu0Ms_T") is not None)
            print(f"  {os.path.basename(n):<28}{ms:>9.2f}{r.get('ground_state',''):>16}   {ps}")

    print(f"\nwrote {out}")
    print(f"wrote {csv_path}")
    print("dE = E(ferri) - E(fm); negative => ferrimagnet wins (expected for heavy RE).")
    print("u0Ms = 11.654 * |net moment| / volume, evaluated in the WINNING "
          "configuration. The Gd POTCAR keeps 4f in the valence, so the RE "
          "contribution is already in the net moment.")
    print("predicted_RE: the same cell with Gd's computed moment swapped for the "
          "parent RE's free-ion g_J*J, keeping the calculated sign. Volume is held "
          "fixed, so it ignores lanthanide contraction (a few % on Ms).")


if __name__ == "__main__":
    main()
