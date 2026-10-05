#!/usr/bin/env python3
"""Redo the Tier-2 native heavy-RE relax stage with the total moment LOCKED.

Why: native_hree_series.py started all five compounds in unconstrained ISIF=2
relax mode (mirroring the original, lucky, unconstrained Co16Gd2Mn_sub
discovery). That doesn't generalise - per-site inspection of the completed
runs showed the two (chemically equivalent) RE sites breaking symmetry from
each other, Mn's moment collapsing whenever they did, and Er's "fm" run
falling all the way into a ferri-like alignment. Only Tb-ferri and Dy-fm came
out clean, symmetric and physically coherent; nothing else is trustworthy.

Fix: same NUPDOWN-locked relax used throughout the rest of this campaign
(rerun_constrained.py / relax_survivor.py) - lock the total moment to the
intended fm/ferri target so the SCF cannot drift into (or split into) a
different magnetic configuration while the ions move, then release
(unconstrained static) once relaxed for the real comparison energy.

NUPDOWN targets are built from the TM sublattice moment MEASURED on this
campaign's own two clean, symmetric runs (Tb-ferri: Co~1.477, Mn~3.338;
Dy-fm: Co~1.539, Mn~3.120 - averaged), not textbook values, following the
same convention as rerun_constrained.py's own NOMINAL_TM table:
  fm target    = round(2 x RE_2S + TM_total)
  ferri target = round(|TM_total - 2 x RE_2S|)

VASP never rewrites POSCAR during relaxation (only CONTCAR), so every one of
these five directories still holds its pristine native GNoME geometry -
no need to regenerate from the CIFs, just archive the current (untrustworthy)
attempt and rewrite INCAR.

Usage
  python3 lock_native_relax.py --dry-run
  python3 lock_native_relax.py
"""
import argparse
import os

from rerun_constrained import ARCHIVE, DELETE, next_index, read_incar, write_incar

HERE = os.path.dirname(os.path.abspath(__file__))

# Hund's-rule 2S for RE3+ (same table as native_hree_series.py)
TWO_S = {"Tb": 6.0, "Dy": 5.0, "Ho": 4.0, "Er": 3.0, "Tm": 2.0}

# TM sublattice moment measured on this campaign's own clean, symmetric runs
CO_MEASURED = (1.477 + 1.539) / 2      # Tb-ferri, Dy-fm
MN_MEASURED = (3.338 + 3.120) / 2      # Tb-ferri, Dy-fm
TM_TOTAL = 16 * CO_MEASURED + MN_MEASURED   # 16 Co + 1 Mn, same for all five

RELAX_OVERRIDES = {
    "IBRION": 2, "ISIF": 2, "NSW": 60, "EDIFFG": -0.02, "EDIFF": "1E-06",
    "ISTART": 0, "ICHARG": 2, "LWAVE": ".TRUE.", "LCHARG": ".TRUE.",
}


def find_compound_dir(name):
    for root, dirs, _ in os.walk(os.path.join(HERE, "runs")):
        if os.path.basename(root) == name:
            return root
    return None


def nupdown_for(re_symbol, config):
    two_s = TWO_S[re_symbol]
    if config == "fm":
        return int(round(2 * two_s + TM_TOTAL))
    return int(round(abs(TM_TOTAL - 2 * two_s)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"TM_total (measured) = 16*{CO_MEASURED:.3f} + {MN_MEASURED:.3f} = {TM_TOTAL:.3f}\n")

    for re_symbol in TWO_S:
        name = f"Co16{re_symbol}2Mn_native"
        base = find_compound_dir(name)
        if base is None:
            print(f"{name}: no run directory found, skipping")
            continue
        print(f"{name}: {os.path.relpath(base, HERE)}")

        for cfg in ("fm", "ferri"):
            d = os.path.join(base, cfg)
            if not os.path.isdir(d):
                print(f"  {cfg}: no such directory, skipping"); continue

            nup = nupdown_for(re_symbol, cfg)
            inc = read_incar(os.path.join(d, "INCAR"))
            if not inc:
                print(f"  {cfg}: no INCAR present, skipping"); continue

            if args.dry_run:
                print(f"  {cfg}: would archive -> _{next_index(d):02d}, "
                      f"lock NUPDOWN={nup}, relax from pristine POSCAR")
                continue

            idx = next_index(d)
            for f in ARCHIVE:
                p = os.path.join(d, f)
                if os.path.exists(p):
                    os.rename(p, os.path.join(d, f"{f}_{idx:02d}"))
            for f in DELETE:
                p = os.path.join(d, f)
                if os.path.exists(p):
                    os.remove(p)

            newinc = dict(inc)
            newinc.update({k: str(v) for k, v in RELAX_OVERRIDES.items()})
            newinc["NUPDOWN"] = str(nup)
            write_incar(os.path.join(d, "INCAR"), newinc)
            print(f"  {cfg}: archived -> _{idx:02d}, wrote locked-relax INCAR "
                  f"(NUPDOWN={nup})")

    if not args.dry_run:
        print("\nPOSCAR untouched throughout (VASP never rewrites it during a "
              "relax) - every run restarts from its pristine native geometry, "
              "this time with the moment locked. Submit with a manifest built "
              "from the same runs/*_native/{fm,ferri} paths, then run "
              "relax_survivor.py-style release (--stage release logic, or a "
              "small follow-up) once relax finishes.")


if __name__ == "__main__":
    main()
