#!/usr/bin/env python3
"""Release stage for a whole manifest: one unconstrained static per run at the
geometry its locked ISIF=2 relax arrived at. Generalises relax_survivor.py
--stage release (same archive-then-overwrite pattern, same overrides).

Why a separate step: a NUPDOWN-locked energy carries the constraint penalty,
and the penalty differs from state to state (Co16Gd2Mn_sub's locked ferri sat
0.5 eV / -42 kB above its free value). Only released energies are comparable -
between fm and ferri, between Mn sites, between Mn-parallel and Mn-opposed.

Per run directory it:
  1. requires a FINISHED relax (VASP timing block) - unfinished runs are
     skipped with a reason, never released from a half-relaxed geometry
  2. copies CONTCAR -> POSCAR (adopts the relaxed geometry)
  3. archives INCAR/OUTCAR/OSZICAR/CONTCAR/... to the next _NN index; keeps
     WAVECAR/CHGCAR in place because the release restarts FROM them
  4. writes the release INCAR: IBRION=-1 NSW=0 EDIFF=1E-07, NUPDOWN removed,
     ISTART=1/ICHARG=0 if a non-empty WAVECAR exists, else ICHARG=1 from
     CHGCAR, else a cold start - and says which. Hardened mixing / NELM /
     ALGO settings already in the INCAR are left alone.

Usage
  python3 release_batch.py --manifest batch/manifests/x.manifest --dry-run
  python3 release_batch.py --manifest batch/manifests/x.manifest
  python3 release_batch.py --dirs runs/.../fm runs/.../ferri
Prints a manifest of the released dirs to pass straight to submit_batch.sh.
"""
import argparse
import os
import shutil

from rerun_constrained import ARCHIVE, next_index, read_incar, write_incar

HERE = os.path.dirname(os.path.abspath(__file__))

RELEASE = {"IBRION": -1, "NSW": 0, "EDIFF": "1E-07", "LWAVE": ".FALSE.", "LCHARG": ".FALSE."}


def finished(outcar):
    if not os.path.isfile(outcar):
        return False
    with open(outcar, "rb") as f:
        f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 400_000))
        if b"General timing and accounting" in f.read():
            return True
    return b"General timing and accounting" in open(outcar, "rb").read()


def nonempty(p):
    return os.path.isfile(p) and os.path.getsize(p) > 0


def release_dir(d, dry_run):
    d = os.path.abspath(d)
    tag = "/".join(d.split("/")[-2:])
    if not finished(os.path.join(d, "OUTCAR")):
        return None, f"{tag}: relax not finished - skipped"
    contcar = os.path.join(d, "CONTCAR")
    if not (os.path.isfile(contcar) and os.path.getsize(contcar) > 100):
        return None, f"{tag}: no CONTCAR - skipped"
    inc = read_incar(os.path.join(d, "INCAR"))
    if not inc:
        return None, f"{tag}: no INCAR - skipped"
    if "NUPDOWN" not in inc and inc.get("IBRION") == "-1":
        return None, f"{tag}: already a released static - skipped"

    if nonempty(os.path.join(d, "WAVECAR")):
        restart = {"ISTART": 1, "ICHARG": 0}; how = "WAVECAR"
    elif nonempty(os.path.join(d, "CHGCAR")):
        restart = {"ISTART": 0, "ICHARG": 1}; how = "CHGCAR"
    else:
        restart = {"ISTART": 0, "ICHARG": 2}; how = "cold start"

    new = dict(inc)
    new.update({k: str(v) for k, v in RELEASE.items()})
    new.update({k: str(v) for k, v in restart.items()})
    nup = new.pop("NUPDOWN", None)
    idx = next_index(d)
    msg = f"{tag}: release from {how}, drop NUPDOWN={nup}, archive -> _{idx:02d}"
    if dry_run:
        return d, msg

    shutil.copy(contcar, os.path.join(d, "POSCAR"))
    for f in ARCHIVE:
        p = os.path.join(d, f)
        if os.path.exists(p):
            os.rename(p, os.path.join(d, f"{f}_{idx:02d}"))
    write_incar(os.path.join(d, "INCAR"), new)
    return d, msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest")
    ap.add_argument("--dirs", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=None, help="write the released-dir manifest here")
    args = ap.parse_args()

    dirs = list(args.dirs)
    if args.manifest:
        dirs += [l.strip() for l in open(args.manifest) if l.strip()]
    if not dirs:
        ap.error("give --manifest and/or --dirs")

    released = []
    for d in dirs:
        rd, msg = release_dir(d, args.dry_run)
        print(("  would: " if args.dry_run else "  ") + msg)
        if rd:
            released.append(rd)

    out = args.out or (args.manifest.replace(".manifest", "_release.manifest")
                       if args.manifest else "batch/manifests/release.manifest")
    print(f"\n{len(released)} of {len(dirs)} dirs released" + (" (dry run)" if args.dry_run else ""))
    if not args.dry_run and released:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            f.write("\n".join(released) + "\n")
        print(f"manifest: {out}\nsubmit:   MANIFEST={out} ./submit_batch.sh")


if __name__ == "__main__":
    main()
