#!/usr/bin/env python3
"""Classify every NOT_CONVERGED configuration for harden_runs.py.

Two failure modes need different medicine, and the local mirror lets us tell
them apart from the OUTCARs:
  diverged  - the SCF blew up: final energy far from its converged partner
              config (or absurd per atom)      -> hardened mixing + ALGO=All
  limping   - sane energy, just hit NELM        -> hardened mixing + NELM 400
Runs whose OUTCAR is a bare stub (walltime kill before any SCF) are treated
as limping. Writes two path lists under batch/ for the remote harden step and
prints what it found, including how many are NUPDOWN-locked (the lock is kept).

Usage:  python3 prepare_hardening.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, "results.json")))

def final_energy(outcar):
    try:
        with open(outcar, "rb") as f:
            f.seek(0, 2); f.seek(max(0, f.tell() - 800_000)); t = f.read().decode(errors="replace")
    except OSError:
        return None
    m = re.findall(r"free  energy\s+TOTEN\s*=\s*(-?\d+\.\d+)", t)
    return float(m[-1]) if m else None

def natoms(poscar):
    try:
        return sum(int(x) for x in open(poscar).read().splitlines()[6].split())
    except Exception:
        return None

diverged, limping, locked = [], [], 0
for rel, rec in sorted(res.items()):
    for cfg in ("fm", "ferri"):
        c = rec.get(cfg) or {}
        if c.get("status") != "NOT_CONVERGED":
            continue
        d = os.path.join(HERE, "runs", rel, cfg)
        if not os.path.isfile(os.path.join(d, "INCAR")):
            continue
        e = final_energy(os.path.join(d, "OUTCAR"))
        other = (rec.get("ferri" if cfg == "fm" else "fm") or {})
        e_other = other.get("E0_eV") if other.get("status") == "converged" else None
        n = natoms(os.path.join(d, "POSCAR")) or 1
        bad = False
        if e is not None:
            if e_other is not None and abs(e - e_other) > 5.0:
                bad = True                       # eV-scale off its partner: not a magnetic state
            elif abs(e) / n > 15.0 or e > 0:
                bad = True                       # absurd per-atom energy
        (diverged if bad else limping).append(os.path.relpath(d, HERE))
        if c.get("constrained"):
            locked += 1

os.makedirs(os.path.join(HERE, "batch"), exist_ok=True)
for name, lst in (("harden_diverged.txt", diverged), ("harden_limping.txt", limping)):
    with open(os.path.join(HERE, "batch", name), "w") as f:
        f.write("\n".join(lst) + ("\n" if lst else ""))
print(f"NOT_CONVERGED configs: {len(diverged) + len(limping)}   diverged (ALGO=All): {len(diverged)}   "
      f"limping (mixing+NELM): {len(limping)}   of which NUPDOWN-locked: {locked}")
print("lists: batch/harden_diverged.txt  batch/harden_limping.txt")
if diverged:
    print("\ndiverged examples:")
    for p in diverged[:6]:
        print("  ", p)
