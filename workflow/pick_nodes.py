#!/usr/bin/env python3
"""Pick the node count that minimises TIME TO RESULTS = queue wait + run time,
using live NERSC queue statistics.

Queue wait on Perlmutter GPU is a strong, non-monotonic function of how many nodes
you ask for (NERSC favours capability jobs, so 1-node jobs wait longest and there
are cliffs at the band edges). Asking for more nodes shortens the run but can land
in a slower band, so the optimum is a real trade-off - and it moves with machine
load, which is why this queries Iris instead of hard-coding a table.

Data: https://iris.nersc.gov/graphql_web (public, no login), the same source as
https://www.nersc.gov/users/status/queue-wait-times

Usage:
    python3 pick_nodes.py --runs 706 --per-run-min 30
    python3 pick_nodes.py --runs 706 --per-run-min 30 --shell   # eval-able output
    python3 pick_nodes.py --runs 706 --per-run-min 30 --offline # cached fallback
"""
import argparse
import json
import math
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()

IRIS = "https://iris.nersc.gov/graphql_web"
QUERY = """query($hostname:String,$qos:String,$startMin:String,$startMax:String){
  queueWaitTime { queueWaitTime(hostname:$hostname,qos:$qos,startMin:$startMin,startMax:$startMax){
    nodes hours waitHours jobCount } } }"""

# Snapshot of Perlmutter GPU / gpu_regular average wait (h) by node band, used
# only with --offline or if Iris is unreachable.
FALLBACK = {1: 50.7, 2: 34.9, 4: 31.1, 8: 35.4, 16: 27.3, 32: 18.7,
            64: 45.4, 128: 63.9, 256: 64.9, 512: 56.7}


def band_lo(n):
    """Lower edge of the power-of-two node band containing n (1,2,4,8,...)."""
    return 1 if n < 2 else 2 ** int(math.floor(math.log2(n)))


def fetch(days, hostname, qos, timeout=60):
    now = datetime.utcnow()
    variables = {"hostname": hostname, "qos": qos,
                 "startMin": (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S"),
                 "startMax": now.strftime("%Y-%m-%dT%H:%M:%S")}
    req = urllib.request.Request(
        IRIS, data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "magnito-scheduler/0.1"})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "graphql error"))
    return payload["data"]["queueWaitTime"]["queueWaitTime"] or []


def wait_model(rows, min_cell_jobs):
    """(band, walltime_hours) and band -> job-count-weighted mean wait.

    Per-(band, walltime) cells are mostly 1-10 jobs, so a raw minimum over them
    just finds the luckiest single job. Cells below min_cell_jobs are discarded
    and the band average (hundreds to thousands of jobs) is used instead.
    """
    by_band_hours, by_band = {}, {}
    for r in rows:
        n, h, w, c = r["nodes"], r["hours"], r["waitHours"], r["jobCount"]
        if not c or n is None or w is None or w < 0:
            continue
        b = band_lo(max(1, int(n)))
        for key, tbl in (((b, int(h or 0)), by_band_hours), (b, by_band)):
            s, wc = tbl.get(key, (0.0, 0.0))
            tbl[key] = (s + w * c, wc + c)
    bh = {k: s / c for k, (s, c) in by_band_hours.items() if c >= min_cell_jobs}
    band = {k: (s / c, c) for k, (s, c) in by_band.items() if c}
    return bh, band


def predict(nodes, walltime_h, bh, band, overall):
    key = band_lo(nodes)
    v = bh.get((key, int(math.ceil(walltime_h))))
    if v is not None:
        return v
    if key in band:
        return band[key][0]
    if band:                           # unseen band: nearest observed band
        near = min(band, key=lambda k: abs(math.log2(k) - math.log2(key)))
        return band[near][0]
    return overall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, required=True)
    ap.add_argument("--per-run-min", type=float, default=30.0)
    ap.add_argument("--max-wall-h", type=float, default=12.0, help="QOS walltime cap")
    ap.add_argument("--headroom", type=float, default=1.3, help="walltime request margin")
    ap.add_argument("--max-nodes", type=int, default=256)
    ap.add_argument("--days", type=int, default=30, help="history window")
    ap.add_argument("--hostname", default="perlmutter gpu")
    ap.add_argument("--qos", default="gpu_regular")
    ap.add_argument("--min-cell-jobs", type=int, default=100,
                    help="ignore (band,walltime) cells with fewer jobs than this")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--shell", action="store_true", help="print PACK_NODES=.. WALLTIME=..")
    args = ap.parse_args()

    source = "iris (live)"
    def snapshot():
        return {}, {k: (v, 0) for k, v in FALLBACK.items()}, 40.0, "built-in snapshot"
    if args.offline:
        bh, band, overall, source = snapshot()
    else:
        try:
            rows = fetch(args.days, args.hostname, args.qos)
            if not rows:
                raise RuntimeError("no rows returned")
            bh, band = wait_model(rows, args.min_cell_jobs)
            overall = (sum(v for v, _ in band.values()) / len(band)) if band else 40.0
        except Exception as ex:
            print(f"# Iris query failed ({type(ex).__name__}: {ex}); using snapshot",
                  file=sys.stderr)
            bh, band, overall, source = snapshot()

    per_run_h = args.per_run_min / 60.0
    best, table = None, []
    for n in range(1, args.max_nodes + 1):
        waves = math.ceil(args.runs / n)
        runtime = waves * per_run_h
        request = min(runtime * args.headroom, args.max_wall_h)
        if runtime > args.max_wall_h:
            continue                    # cannot finish inside the QOS cap
        w = predict(n, request, bh, band, overall)
        total = w + runtime
        table.append((n, w, waves, runtime, total))
        if best is None or total < best[-1]:
            best = (n, w, waves, runtime, total)

    if best is None:
        sys.exit("no node count finishes within the walltime cap; raise --max-wall-h")

    n, w, waves, runtime, total = best
    wall_min = int(math.ceil(min(runtime * args.headroom, args.max_wall_h) * 60))
    walltime = f"{wall_min // 60:02d}:{wall_min % 60:02d}:00"

    if args.shell:
        # machine-readable for submit_batch.sh; SOURCE says whether the live Iris
        # query succeeded or we silently fell back to the built-in snapshot
        tag = "iris-live" if source.startswith("iris") else "snapshot-fallback"
        print(f"PACK_NODES={n} WALLTIME={walltime} SOURCE={tag} "
              f"WAIT_H={w:.1f} RUN_H={runtime:.1f} BAND={band_lo(n)}")
        return

    print(f"# queue data: {source} | {args.hostname} / {args.qos} | last {args.days} d")
    if band and any(c for _, c in band.values()):
        print("# observed wait by node band:  " + "  ".join(
            f"{k}+:{v:.0f}h({c:.0f}j)" for k, (v, c) in sorted(band.items())))
    print(f"# {args.runs} runs x {args.per_run_min:.0f} min "
          f"= {args.runs * per_run_h:.0f} node-hours of work\n")
    print(f"{'nodes':>6}{'wait':>9}{'waves':>7}{'run':>8}{'TOTAL':>9}")
    shown = {r[0] for r in table if r[0] in
             (1, 2, 4, 8, 16, 31, 32, 48, 63, 64, 96, 128, 200, 256)} | {n}
    for row in table:
        if row[0] in shown:
            mark = "  <-- best" if row[0] == n else ""
            print(f"{row[0]:>6}{row[1]:>8.1f}h{row[2]:>7}{row[3]:>7.1f}h"
                  f"{row[4]:>8.1f}h{mark}")
    print(f"\nrecommended:  PACK_NODES={n}  WALLTIME={walltime}")
    print(f"  expected ~{w:.1f} h queued + {runtime:.1f} h running = {total:.1f} h to results")


if __name__ == "__main__":
    main()
