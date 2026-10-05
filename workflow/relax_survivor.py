#!/usr/bin/env python3
"""Ionic relaxation (fixed cell) for a specific high-value compound.

Why: every Gd-surrogate uses a geometry frozen from a DIFFERENT lanthanide's
GNoME-relaxed structure (build_campaign.py substitutes the element label only,
no relaxation). For Co16Gd2Mn_sub the cell volume/shape checked out (residual
pressure -2.6/-5.0 kB, ~1-2 meV energy consequence - negligible), but residual
FORCES did not: fm 0.099, ferri 0.188 eV/A - ferri is ~2x fm's and above a
"well relaxed" threshold. That asymmetry means relaxing ions could lower
ferri's energy more than fm's, which a volume-only check cannot see.

Two stages, run per configuration (fm/ferri), same archive-then-overwrite
pattern as rerun_constrained.py:

  relax    ISIF=2 (ions only - the cell already checked out), NUPDOWN locked to
           this config's OWN already-converged total moment (read from its
           existing OSZICAR) so ionic motion cannot drift the SCF into the
           other magnetic configuration while positions move. Writes
           LWAVE/LCHARG so 'release' can restart from it.
  release  copies the relaxed CONTCAR -> POSCAR, then one final UNCONSTRAINED
           static (no NUPDOWN) restarting from the relax step's WAVECAR/CHGCAR.
           This is the energy that actually gets compared - 'relax' itself is
           a fixed-spin-moment number, same caveat as the Stage A/B protocol.

Usage
  python3 relax_survivor.py --compound Co16Gd2Mn_sub --stage relax
  python3 relax_survivor.py --compound Co16Gd2Mn_sub --stage release
"""
import argparse
import os
import re
import shutil
import sys

from rerun_constrained import ARCHIVE, next_index, read_incar, write_incar
from analyze import total_moment

HERE = os.path.dirname(os.path.abspath(__file__))

RELAX_OVERRIDES = {
    "IBRION": 2, "ISIF": 2, "NSW": 60, "EDIFFG": -0.02, "EDIFF": "1E-06",
    "ISTART": 0, "ICHARG": 2, "LWAVE": ".TRUE.", "LCHARG": ".TRUE.",
}
RELEASE_OVERRIDES = {
    "IBRION": -1, "NSW": 0, "EDIFF": "1E-07",
    "ISTART": 1, "ICHARG": 0, "LWAVE": ".FALSE.", "LCHARG": ".FALSE.",
}


def find_compound_dir(name):
    for root, dirs, _ in os.walk(os.path.join(HERE, "runs")):
        if os.path.basename(root) == name:
            return root
    sys.exit(f"no run directory named {name} found under runs/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compound", required=True)
    ap.add_argument("--stage", choices=["relax", "release"], required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = find_compound_dir(args.compound)
    print(f"{args.compound}: {os.path.relpath(base, HERE)}  [{args.stage}]")

    for cfg in ("fm", "ferri"):
        d = os.path.join(base, cfg)
        if not os.path.isdir(d):
            print(f"  {cfg}: no such directory, skipping"); continue

        if args.stage == "release":
            # take the JUST-COMPLETED relax run's CONTCAR as the new POSCAR
            # before archiving it away
            contcar = os.path.join(d, "CONTCAR")
            if not (os.path.exists(contcar) and os.path.getsize(contcar) > 100):
                print(f"  {cfg}: no relaxed CONTCAR present - run --stage relax "
                      f"and let it finish first"); continue
            if not args.dry_run:
                shutil.copy(contcar, os.path.join(d, "POSCAR"))
            print(f"  {cfg}: CONTCAR -> POSCAR (relaxed geometry adopted)")

        nup = None
        if args.stage == "relax":
            osz = os.path.join(d, "OSZICAR")
            if os.path.exists(osz):
                m = total_moment(osz)
                if m is not None:
                    nup = int(round(abs(m)))
            if nup is None:
                print(f"  {cfg}: WARNING no prior OSZICAR/moment found - "
                      f"relaxing WITHOUT a locked moment (risk of spin drift)")

        inc = read_incar(os.path.join(d, "INCAR"))
        if not inc:
            print(f"  {cfg}: no INCAR present, skipping"); continue
        newinc = dict(inc)
        overrides = RELAX_OVERRIDES if args.stage == "relax" else RELEASE_OVERRIDES
        newinc.update({k: str(v) for k, v in overrides.items()})
        if args.stage == "relax":
            if nup is not None:
                newinc["NUPDOWN"] = str(nup)
        else:
            newinc.pop("NUPDOWN", None)

        if args.dry_run:
            print(f"  {cfg}: would archive -> _{next_index(d):02d}, "
                  f"stage={args.stage}, NUPDOWN={nup}")
            continue

        idx = next_index(d)
        keep_restart = args.stage == "release"  # release restarts FROM these
        for f in ARCHIVE:
            p = os.path.join(d, f)
            if os.path.exists(p):
                shutil.move(p, os.path.join(d, f"{f}_{idx:02d}"))
        if not keep_restart:
            for f in ("WAVECAR", "CHGCAR"):
                p = os.path.join(d, f)
                if os.path.exists(p) and args.stage == "relax":
                    pass  # relax stage has nothing to restart FROM; leave as-is
        write_incar(os.path.join(d, "INCAR"), newinc)
        print(f"  {cfg}: archived -> _{idx:02d}, wrote {args.stage} INCAR"
              + (f" (NUPDOWN={nup})" if nup is not None else ""))

    if not args.dry_run:
        print(f"\nsubmit with:  MANIFEST=<list containing {args.compound}'s "
              f"fm/ferri dirs> ./submit_batch.sh")


if __name__ == "__main__":
    main()
