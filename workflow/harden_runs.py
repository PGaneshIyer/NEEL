#!/usr/bin/env python3
"""Re-arm failed locked relaxes with the hardened SCF settings.

The native heavy-RE runs fail in two ways the lock alone cannot stop:
  - SCF divergence (E ~ +-1e6 eV in the first ionic step) - charge sloshing in
    an ill-conditioned LDA+U f-manifold; cured for Tm by conservative mixing
  - limping SCF (NELM=200 hit on every ionic step, 30 min/step, walltime kill)
Both get the campaign's hardened block (rerun_constrained.HARDENED mixing,
NELM 400). Runs that actually diverged additionally get ALGO=All (all-bands
CG - slower, far more robust than blocked Davidson for a sick first SCF).

Keeps everything else - the lock, ISIF=2/NSW=60, POTCARs - and archives the
failed attempt to the next _NN index. With --continue, CONTCAR (if present
and non-trivial) becomes POSCAR first, so a run that stopped at step 60 with
falling forces resumes from where it got to instead of starting over.

Usage
  python3 harden_runs.py --dirs runs/.../fm runs/.../ferri        # mixing + NELM
  python3 harden_runs.py --diverged runs/.../fm                   # + ALGO=All
  python3 harden_runs.py --continue --dirs runs/.../ferri         # CONTCAR->POSCAR
  add --dry-run to preview; prints a manifest for submit_batch.sh
"""
import argparse
import os
import shutil

from rerun_constrained import ARCHIVE, DELETE, next_index, read_incar, write_incar

HARDEN = {"NELM": 400, "AMIX": 0.2, "BMIX": 0.0001, "AMIX_MAG": 0.8, "BMIX_MAG": 0.0001}


def harden(d, diverged, cont, dry_run):
    d = os.path.abspath(d); tag = "/".join(d.split("/")[-2:])
    inc = read_incar(os.path.join(d, "INCAR"))
    if not inc:
        return None, f"{tag}: no INCAR - skipped"
    new = dict(inc)
    new.update({k: str(v) for k, v in HARDEN.items()})
    if diverged:
        new["ALGO"] = "All"
    # a fresh SCF: never restart from the density/wavefunction of a run that failed
    new.update({"ISTART": "0", "ICHARG": "2"})
    contcar = os.path.join(d, "CONTCAR")
    use_cont = cont and os.path.isfile(contcar) and os.path.getsize(contcar) > 100
    idx = next_index(d)
    msg = (f"{tag}: NELM=400 + hardened mixing" + (" + ALGO=All" if diverged else "")
           + (" , continue from CONTCAR" if use_cont else "")
           + f", lock NUPDOWN={new.get('NUPDOWN')}, archive -> _{idx:02d}")
    if dry_run:
        return d, msg
    if use_cont:
        shutil.copy(contcar, os.path.join(d, "POSCAR"))
    for f in ARCHIVE:
        p = os.path.join(d, f)
        if os.path.exists(p):
            os.rename(p, os.path.join(d, f"{f}_{idx:02d}"))
    for f in DELETE:            # WAVECAR/CHGCAR of a failed SCF are not a restart point
        p = os.path.join(d, f)
        if os.path.exists(p):
            os.remove(p)
    write_incar(os.path.join(d, "INCAR"), new)
    return d, msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=[], help="limping runs: mixing + NELM")
    ap.add_argument("--diverged", nargs="*", default=[], help="diverged runs: also ALGO=All")
    ap.add_argument("--continue", dest="cont", action="store_true",
                    help="adopt CONTCAR as POSCAR where one exists")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="batch/manifests/hardened.manifest")
    args = ap.parse_args()
    if not args.dirs and not args.diverged:
        ap.error("give --dirs and/or --diverged")

    done = []
    for d in args.dirs:
        rd, msg = harden(d, False, args.cont, args.dry_run); print("  " + msg); done += [rd] if rd else []
    for d in args.diverged:
        rd, msg = harden(d, True, args.cont, args.dry_run); print("  " + msg); done += [rd] if rd else []
    print(f"\n{len(done)} runs re-armed" + (" (dry run)" if args.dry_run else ""))
    if done and not args.dry_run:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        open(args.out, "w").write("\n".join(done) + "\n")
        print(f"manifest: {args.out}")


if __name__ == "__main__":
    main()
