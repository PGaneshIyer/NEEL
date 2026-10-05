#!/usr/bin/env python3
"""Re-run the compounds whose fm/ferri comparison did not actually answer the question.

Why a plain re-run is not enough
--------------------------------
The dominant failure in the first campaign was not poor convergence, it was the
ferri SCF finding the WRONG STATE: instead of Gd-down / Fe-up it fell into a
collapsed or low-spin Fe solution. That state is higher in energy for reasons
that have nothing to do with the rare earth, so dE came out positive and the
compound looked ferromagnetic. Re-running with the same INCAR would reproduce
the same artefact.

So the rerun CONSTRAINS the total moment with NUPDOWN, fixing N(up) - N(down) at
the value the intended configuration must have:

    NUPDOWN(fm)    = | M_TM + 7*n_Gd |
    NUPDOWN(ferri) = | M_TM - 7*n_Gd |

with Gd taken as a rigid 7 mu_B (half-filled 4f) and M_TM inferred from the
previous fm run ONLY if that run converged and kept its configuration, else from
nominal atomic moments. Deriving the constraint from a run that collapsed - the
very failure being fixed - would just re-impose the artefact.

That pins each run inside its own basin, so the two energies describe the two
spin configurations rather than whatever the SCF happened to find. It is a
fixed-spin-moment comparison: both states are constrained minima of their own
basin, which is exactly the two-state question being asked. Convergence settings
are also hardened for the runs that simply failed to converge.

What it does to each run directory
----------------------------------
  * archives the previous attempt with an index: OUTCAR -> OUTCAR_01, etc.
    (a second pass writes _02, so history is never lost)
  * DELETES WAVECAR / CHG* - a rerun must not restart from the old, wrong
    spin density, and they are large
  * writes a new INCAR with NUPDOWN and hardened SCF settings
  * leaves POSCAR / POTCAR / KPOINTS untouched

Because the completed OUTCAR is renamed away, `submit_batch.sh` sees these runs
as pending again and submits exactly them - no separate submission path needed.

Usage
  python3 rerun_constrained.py --dry-run
  python3 rerun_constrained.py
  python3 rerun_constrained.py --only TM_SUBLATTICE_CHANGED
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

ARCHIVE = ["OUTCAR", "OSZICAR", "CONTCAR", "vasp.log", "INCAR", "XDATCAR",
           "vasprun.xml", "EIGENVAL", "DOSCAR", "PROCAR", "REPORT", ".node",
           "job.slurm"]
DELETE = ["WAVECAR", "CHGCAR", "CHG", "WAVEDER", "TMPCAR", "PCDAT"]

# Stage A: a short CONSTRAINED run whose only product is a wavefunction/charge
# density sitting in the intended magnetic basin. Its energy is never used, so
# the constraint penalty that invalidated the last attempt cannot contaminate
# anything. LWAVE/LCHARG must be on or stage B has nothing to restart from -
# they were .FALSE. throughout the first campaign, which is why every WAVECAR on
# disk is 0 bytes.
STAGE_A = {
    "NELM": 60,
    "EDIFF": "1E-05",      # loose: we only need to be inside the basin
    "ALGO": "Normal",
    "AMIX": 0.2, "BMIX": 0.0001, "AMIX_MAG": 0.8, "BMIX_MAG": 0.0001,
    "ISTART": 0, "ICHARG": 2,
    # CHGCAR only. The magnetic BASIN is fixed by the spin density, which CHGCAR
    # carries; the wavefunction adds nothing for that purpose and is ~50x larger.
    # Writing WAVECAR for 394 runs consumed ~700 GB of scratch on the first pass
    # and the resulting disk pressure appears to have cost ~60 runs their restart
    # files outright.
    "LWAVE": ".FALSE.", "LCHARG": ".TRUE.",
}

# hardened SCF block for the rerun; NUPDOWN is added per configuration
HARDENED = {
    "NELM": 400,          # the first pass hit NELM=200 on 44 runs
    "EDIFF": "1E-07",
    "ALGO": "Normal",
    "AMIX": 0.2,          # conservative mixing: these are slow, magnetic, +U
    "BMIX": 0.0001,
    "AMIX_MAG": 0.8,
    "BMIX_MAG": 0.0001,
    "ISTART": 0,          # no restart - the old WAVECAR/CHGCAR are deleted
    "ICHARG": 2,
}


def flags_of(v):
    f = []
    for cfg in ("fm", "ferri"):
        st = v.get(cfg, {}).get("status")
        if st and st != "converged":
            f.append(f"{cfg}:{st}")
        elif v.get(cfg, {}).get("kept_intended_config") is False:
            f.append(f"{cfg}:FLIPPED")
    f += [x for x in (v.get("validity") or []) if x != "ok"]
    return f


def next_index(d):
    """Lowest unused archive index in this directory."""
    used = set()
    for f in os.listdir(d):
        m = re.search(r"_(\d{2})$", f)
        if m:
            used.add(int(m.group(1)))
    i = 1
    while i in used:
        i += 1
    return i


def read_incar(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path):
        line = line.split("#")[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def write_incar(path, d):
    with open(path, "w") as f:
        for k, v in d.items():
            f.write(f"{k} = {v}\n")


# Sublattice moments MEASURED on this campaign's own freely-relaxed runs, rather
# than textbook values. The first pass assumed 2.2 mu_B/Fe and that was the single
# biggest source of unphysical constraints: the real high-spin mean is 1.69, and
# in P-containing compounds Fe is genuinely low-spin at 0.25 mu_B (n=64), because
# Fe-P hybridisation broadens the 3d band and quenches the moment.
M_GD = 7.0          # Gd 4f7 is a half-filled shell: rigidly ~7 mu_B, not fitted
NOMINAL_TM = {"Fe": 1.69, "Co": 1.09, "Mn": 1.5, "Ni": 0.5, "Cr": 0.8}
LOWSPIN_TM = {"Fe": 0.25, "Co": 0.25, "Mn": 0.3, "Ni": 0.1, "Cr": 0.2}
LOWSPIN_TRIGGER = {"P"}   # elements that put the TM sublattice in the low-spin branch


def tm_table(counts):
    """Pick the high- or low-spin reference for this chemistry."""
    return (LOWSPIN_TM, "low-spin (P present)") if (set(counts) & LOWSPIN_TRIGGER) \
        else (NOMINAL_TM, "high-spin")


def species_counts(rundir):
    p = os.path.join(rundir, "POSCAR")
    if not os.path.exists(p):
        return {}
    try:
        L = open(p).read().splitlines()
        return dict(zip(L[5].split(), (int(x) for x in L[6].split())))
    except Exception:
        return {}


def tm_moment_estimate(res, rundir):
    """Total TM-sublattice moment in mu_B, and where the number came from.

    Preference order matters: the previous fm run is only usable if it actually
    converged and kept its configuration. Deriving the constraint from a run that
    collapsed - which is the failure being fixed - would just re-impose the
    artefact. Gd is taken as a rigid 7 mu_B (half-filled 4f), so subtracting it
    from the cell total isolates the TM contribution INCLUDING the interstitial
    density that sphere projections miss.
    """
    counts = species_counts(rundir)
    n_re = sum(n for el, n in counts.items() if el == "Gd")
    table, branch = tm_table(counts)
    nominal = sum(table.get(el, 0.0) * n for el, n in counts.items() if el in table)
    fm = res.get("fm", {})
    m_fm = fm.get("total_moment_uB")
    # A CONSTRAINED run's moment is whatever NUPDOWN forced it to be, so using it
    # as the reference would simply re-impose the previous (wrong) target. Only a
    # freely-relaxed, converged run that kept its configuration may be used.
    usable = (fm.get("status") == "converged"
              and not fm.get("constrained")
              and fm.get("kept_intended_config") is not False
              and m_fm is not None and n_re)
    if usable:
        m_tm = m_fm - M_GD * n_re
        n_tm_atoms = sum(n for el, n in counts.items() if el in NOMINAL_TM)
        # sanity: a believable TM sublattice carries >= 0.5 mu_B per TM atom
        if n_tm_atoms and abs(m_tm) >= 0.5 * n_tm_atoms:
            return m_tm, n_re, "from converged FREE fm run"
    return nominal, n_re, f"nominal {branch}"


def magmom_line(rundir, cfg):
    """Per-species MAGMOM using the measured branch for this chemistry.

    The first campaign initialised every TM at 2.5 mu_B. In the P-containing
    compounds the true moment is 0.25, so the SCF started ~10x too high and had
    to fall a long way - part of why those runs ended up in odd states.
    """
    p = os.path.join(rundir, "POSCAR")
    if not os.path.exists(p):
        return None
    L = open(p).read().splitlines()
    syms, counts = L[5].split(), [int(x) for x in L[6].split()]
    table, _ = tm_table(dict(zip(syms, counts)))
    parts = []
    for sym, n in zip(syms, counts):
        if sym == "Gd":
            m = -M_GD if cfg == "ferri" else M_GD
        else:
            m = table.get(sym, 0.0)
        parts.append(f"{n}*{m:.2f}")
    return "  ".join(parts)


def nupdown_for(res, rundir, cfg):
    """Total moment the intended configuration must carry, as an integer."""
    m_tm, n_re, src = tm_moment_estimate(res, rundir)
    if not n_re:
        return None, src
    m_re = M_GD * n_re
    val = abs(m_tm + m_re) if cfg == "fm" else abs(m_tm - m_re)
    return int(round(val)), src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=os.path.join(HERE, "results.json"))
    ap.add_argument("--runs", default=os.path.join(HERE, "runs"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="restrict to one failure class, e.g. TM_SUBLATTICE_CHANGED")
    ap.add_argument("--no-nupdown", action="store_true",
                    help="harden convergence only, do not constrain the moment")
    ap.add_argument("--restart-from", choices=["wavecar", "chgcar"], default="chgcar",
                    help="stage B: what to restart from (chgcar is much smaller)")
    ap.add_argument("--stage", choices=["a", "b", "single"], default="single",
                    help="a = short constrained run that writes a restart file; "
                         "b = free run restarting from stage A (energy comes from here)")
    args = ap.parse_args()

    if not os.path.exists(args.results):
        sys.exit(f"no {args.results} - run analyze.py first")
    results = json.load(open(args.results))

    # Stage B selects from the FILESYSTEM, not from results.json. What qualifies a
    # run for stage B is that stage A actually left a restart file for it - and
    # results.json may describe a different tree entirely (it is written wherever
    # analyze.py last ran, and archiving OUTCARs makes every run look "not_run").
    if args.stage == "b":
        want = "CHGCAR" if args.restart_from == "chgcar" else "WAVECAR"
        todo, ready, missing = [], 0, 0
        seen = set()
        for root, dirs, files in os.walk(args.runs):
            if os.path.basename(root) not in ("fm", "ferri"):
                continue
            base = os.path.dirname(root)
            rel = os.path.relpath(base, args.runs)
            f = os.path.join(root, want)
            # A run is eligible only if it still carries a stage-A INCAR (has
            # NUPDOWN). Once converted to stage B the CHGCAR is still there, so
            # without this check every later pass would re-convert finished runs.
            inc = read_incar(os.path.join(root, "INCAR"))
            if "NUPDOWN" not in inc:
                continue
            if os.path.exists(f) and os.path.getsize(f) > 1024:
                ready += 1
                if rel not in seen:
                    seen.add(rel)
                    todo.append((rel, results.get(rel, {}), [f"stage-A {want} present"]))
            else:
                missing += 1
        print(f"stage B: {ready} runs have a stage-A {want}; {missing} do not and are skipped")
        print(f"         -> {len(todo)} compounds to set up")
        if not todo:
            sys.exit(f"no stage-A {want} found - did stage A finish, and did it "
                     f"write restart files? (LCHARG must be .TRUE.)")
        _todo_ready = True
    else:
        _todo_ready = False

    todo = todo if _todo_ready else []
    for rel, v in ([] if _todo_ready else results.items()):
        fl = flags_of(v)
        if not fl:
            continue
        if args.only and args.only not in fl:
            continue
        todo.append((rel, v, fl))
    print(f"compounds needing a constrained rerun: {len(todo)} "
          f"(of {len(results)} analysed)")
    from collections import Counter
    print("by reason:", dict(Counter(f for _, _, fl in todo for f in fl)))

    touched = n_arch = n_del = 0
    log = []
    for rel, v, fl in todo:
        base = os.path.join(args.runs, rel)
        for cfg in ("fm", "ferri"):
            d = os.path.join(base, cfg)
            if not os.path.isdir(d):
                continue
            if args.stage == "b":
                want = "CHGCAR" if args.restart_from == "chgcar" else "WAVECAR"
                f = os.path.join(d, want)
                if not (os.path.exists(f) and os.path.getsize(f) > 1024):
                    continue          # stage A left nothing to restart from here
                if "NUPDOWN" not in inc:
                    continue          # already converted to stage B
            nup, nup_src = (None, 'disabled') if args.no_nupdown else nupdown_for(v, d, cfg)
            inc = read_incar(os.path.join(d, "INCAR"))
            if not inc:
                continue
            newinc = dict(inc)
            if args.stage == "a":
                newinc.update({k: str(x) for k, x in STAGE_A.items()})
                mm = magmom_line(d, cfg)
                if mm:
                    newinc["MAGMOM"] = mm
                if nup is not None:
                    newinc["NUPDOWN"] = str(nup)
            elif args.stage == "b":
                newinc.update({k: str(x) for k, x in HARDENED.items()})
                newinc.pop("NUPDOWN", None)        # released: this energy is physical
                if args.restart_from == "chgcar":
                    # CHGCAR is orders of magnitude smaller than WAVECAR and still
                    # carries the SPIN density, which is what fixes the magnetic
                    # basin - enough for our purpose and far cheaper on scratch.
                    newinc["ISTART"] = "0"
                    newinc["ICHARG"] = "1"
                else:
                    newinc["ISTART"] = "1"         # full restart from the wavefunction
                    newinc["ICHARG"] = "0"
                # do NOT write another set: stage B is the last run, and 394 more
                # WAVECARs would be the largest thing in the campaign
                newinc["LWAVE"] = ".FALSE."
                newinc["LCHARG"] = ".FALSE."
            else:
                newinc.update({k: str(x) for k, x in HARDENED.items()})
                if nup is not None:
                    newinc["NUPDOWN"] = str(nup)
            if args.dry_run:
                touched += 1
                if touched <= 6:
                    print(f"   {rel}/{cfg}: NUPDOWN={nup} ({nup_src})  archive->_{next_index(d):02d}")
                continue

            idx = next_index(d)
            arch = [f for f in ARCHIVE if not (args.stage == "b" and f in ("WAVECAR", "CHGCAR"))]
            for f in arch:
                p = os.path.join(d, f)
                if os.path.exists(p):
                    shutil.move(p, os.path.join(d, f"{f}_{idx:02d}"))
                    n_arch += 1
            if args.stage != "b":          # stage B restarts FROM these
                for f in DELETE:
                    p = os.path.join(d, f)
                    if os.path.exists(p):
                        os.remove(p)
                        n_del += 1
            write_incar(os.path.join(d, "INCAR"), newinc)
            touched += 1
            log.append({"run": f"{rel}/{cfg}", "archive_index": idx,
                        "nupdown": nup, "nupdown_source": nup_src, "reasons": fl})

    if args.dry_run:
        print(f"\n(dry run) would touch {touched} run directories")
        return
    json.dump(log, open(os.path.join(HERE, "rerun_log.json"), "w"), indent=1)
    print(f"\nrewrote {touched} run directories")
    print(f"  archived {n_arch} files, deleted {n_del} WAVECAR/CHG* files")
    print(f"  log: {os.path.join(HERE, 'rerun_log.json')}")
    print("\nThese runs no longer have a completed OUTCAR, so submit_batch.sh now "
          "treats them as pending and will submit exactly these:")
    print("  DRY=1 PACK_NODES=optimal ./submit_batch.sh all")
    print("\nNOTE: NUPDOWN fixes the total moment, so each energy is a "
          "fixed-spin-moment result for its own configuration. That is the right "
          "comparison for a two-state question, but the moments are constrained "
          "rather than freely relaxed - re-check the winner without NUPDOWN before "
          "quoting a final Ms.")


if __name__ == "__main__":
    main()
