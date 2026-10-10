#!/bin/bash
# Pull DOSCARs (plus the matching OUTCAR/OSZICAR/CONTCAR/INCAR) for an analysis,
# in a way that stays correct when the local tree is weeks behind NERSC.
#
#   ./pull_doscar.sh                 # credible compounds (local results.json), ground-state config
#   ./pull_doscar.sh --all           # every run dir on NERSC with a finished OUTCAR
#   ./pull_doscar.sh --dry-run       # build + verify the list, transfer nothing
#   ./pull_doscar.sh --doscar-only   # skip OUTCAR/OSZICAR/CONTCAR/INCAR refresh
#   ./pull_doscar.sh --list-only     # just print the local candidate list (no ssh)
#
# Why not a plain file list from results.json: that file describes the LOCAL
# OUTCARs, which may be several generations behind. The remote live DOSCAR
# always belongs to the LATEST run in a directory. If the compound was re-run
# since the last sync, a DOSCAR pulled against the old energies would mix
# generations. So:
#   1. candidates come from local results.json (or --all), but
#   2. the list of files is built ON NERSC: a dir is included only if its live
#      OUTCAR is finished (VASP timing block) and DOSCAR is non-empty,
#   3. OUTCAR/OSZICAR/CONTCAR/INCAR of BOTH configs are pulled with the DOSCAR
#      so the whole compound is one generation locally,
#   4. afterwards each compound's TOTEN is compared with results.json; any
#      change means the remote generation moved -> re-run analyze.py BEFORE
#      exchange_trends.py. The script says so explicitly.
# Pull direction only; nothing on NERSC is written. Archived *_NN files are
# never transferred.
set -euo pipefail
cd "$(dirname "$0")"

: "${NERSC_USER:=gpanchap}"
HOST="${NERSC_HOST:-perlmutter.nersc.gov}"
REMOTE="${REMOTE_DIR:-/pscratch/sd/g/gpanchap/workflow}"

ALL=0; DRY=0; DOSCAR_ONLY=0; LIST_ONLY=0
for a in "$@"; do
  case "$a" in
    --all) ALL=1 ;; --dry-run) DRY=1 ;; --doscar-only) DOSCAR_ONLY=1 ;; --list-only) LIST_ONLY=1 ;;
    *) echo "unknown option $a"; exit 1 ;;
  esac
done
mkdir -p batch
CAND=batch/doscar_candidates.txt      # "rel_compound_dir gs_config" per line
LIST=batch/doscar_files.txt           # files-from list for rsync
SKIP=batch/doscar_skipped.txt

# ---- 1. candidates ---------------------------------------------------------
if [ "$ALL" = 1 ]; then
  echo "candidates: every compound dir on NERSC (built remotely)"
  : > "$CAND"
else
  python3 - "$CAND" <<'PY'
import json, sys
r = json.load(open("results.json"))
with open(sys.argv[1], "w") as f:
    n = 0
    for k, v in sorted(r.items()):
        if v.get("credible"):
            f.write(f"{k} {v.get('ground_state_config') or 'ferri'}\n"); n += 1
print(f"candidates: {n} credible compounds from local results.json", file=sys.stderr)
PY
fi
if [ "$LIST_ONLY" = 1 ]; then cat "$CAND"; exit 0; fi

# ---- 2. verify on NERSC and build the file list ------------------------------
echo "verifying on $HOST (finished OUTCAR + non-empty DOSCAR) ..."
ssh "$NERSC_USER@$HOST" bash -s "$REMOTE" "$ALL" "$DOSCAR_ONLY" < <(cat <<'REMOTE'
cd "$1" || exit 1
ALL="$2"; DOSCAR_ONLY="$3"
done_run() { tail -n 5000 "$1/OUTCAR" 2>/dev/null | grep -q "General timing and accounting" \
             || grep -q "General timing and accounting" "$1/OUTCAR" 2>/dev/null; }
emit() {  # compound_rel gs
  local comp="$1" gs="$2" d="runs/$1/$2"
  if ! [ -f "$d/OUTCAR" ]; then echo "SKIP $comp no OUTCAR in $gs" >&2; return; fi
  if ! done_run "$d"; then echo "SKIP $comp $gs not finished (walltime kill / still running)" >&2; return; fi
  if ! [ -s "$d/DOSCAR" ]; then echo "SKIP $comp no DOSCAR in $gs" >&2; return; fi
  echo "$d/DOSCAR"
  if [ "$DOSCAR_ONLY" != 1 ]; then
    for cfg in fm ferri; do
      for f in OUTCAR OSZICAR CONTCAR INCAR; do [ -f "runs/$comp/$cfg/$f" ] && echo "runs/$comp/$cfg/$f"; done
    done
  fi
}
if [ "$ALL" = 1 ]; then
  find runs -type d -name ferri | sort | while read -r d; do
    comp="${d#runs/}"; comp="${comp%/ferri}"
    # ground state unknown remotely: take whichever config has the lower final energy
    efm=$(grep "free  energy" "runs/$comp/fm/OUTCAR" 2>/dev/null | tail -1 | awk '{print $5}')
    efe=$(grep "free  energy" "runs/$comp/ferri/OUTCAR" 2>/dev/null | tail -1 | awk '{print $5}')
    gs=ferri; [ -n "$efm" ] && [ -n "$efe" ] && awk "BEGIN{exit !($efm < $efe)}" && gs=fm
    emit "$comp" "$gs"
  done
else
  while read -r comp gs; do [ -n "$comp" ] && emit "$comp" "$gs"; done
fi
REMOTE
) < "$CAND" > "$LIST" 2> "$SKIP"

n_files=$(grep -c . "$LIST" || true); n_dos=$(grep -c '/DOSCAR$' "$LIST" || true); n_skip=$(grep -c . "$SKIP" || true)
echo "  will pull $n_dos DOSCARs ($n_files files incl. companions); skipped $n_skip:"
sed 's/^/     /' "$SKIP" | head -20; [ "$n_skip" -gt 20 ] && echo "     ... see $SKIP"
[ "$n_dos" -gt 0 ] || { echo "nothing to pull"; exit 0; }

# ---- 3. transfer ---------------------------------------------------------------
RS=(-a --progress --files-from="$LIST" --exclude='*_[0-9][0-9]')
[ "$DRY" = 1 ] && RS+=(--dry-run)
rsync "${RS[@]}" "$NERSC_USER@$HOST:$REMOTE/" ./
[ "$DRY" = 1 ] && { echo "(dry run - nothing written)"; exit 0; }

# ---- 4. did any generation move? -------------------------------------------------
python3 - "$CAND" <<'PY'
import json, re, sys, os
r = json.load(open("results.json"))
moved = []
for line in open(sys.argv[1]):
    if not line.strip(): continue
    comp, gs = line.split()
    for cfg in ("fm", "ferri"):
        oc = f"runs/{comp}/{cfg}/OUTCAR"
        old = r.get(comp, {}).get(cfg, {}).get("E0_eV")
        if old is None or not os.path.exists(oc): continue
        # the final energy is within the last few hundred kB even after the
        # LDAUPRINT occupancy dump (~260 lines per Gd) - no need to read 2 MB
        with open(oc, "rb") as fh:
            fh.seek(0, 2); fh.seek(max(0, fh.tell() - 800_000))
            tail = fh.read().decode(errors="replace")
        m = re.findall(r"energy\(sigma->0\)\s*=\s*(-?\d+\.\d+)", tail)
        if m and abs(float(m[-1]) - old) > 1e-3:
            moved.append((comp, cfg, old, float(m[-1])))
have = sum(os.path.exists(f"runs/{l.split()[0]}/{l.split()[1]}/DOSCAR") for l in open(sys.argv[1]) if l.strip())
print(f"\nlocal DOSCARs for candidates: {have}")
if moved:
    print(f"WARNING: {len(moved)} run(s) changed generation since results.json was written - "
          f"run `python3 analyze.py` BEFORE exchange_trends.py:")
    for comp, cfg, old, new in moved[:15]:
        print(f"   {comp}/{cfg}: {old:.3f} -> {new:.3f} eV")
    if len(moved) > 15: print(f"   ... {len(moved)-15} more")
else:
    print("all pulled OUTCARs match results.json energies - DOS features are consistent with the analysed dE.")
PY
