"""Shrink full run folders to the summary (runio.SUMMARY), U 2026-11-21.

    python shrink_runs.py RUNS...           # list what would go
    python shrink_runs.py RUNS... --yes     # delete it

RUNS are names or patterns under the runs root (quote patterns), such as
'wp10c_seed10?'. metrics.json is made first where it is missing. Keep the
current baseline full (docs/upgrade/GUIDE.md, "Run storage").
"""
import argparse
import os

import runroot
from wsim import metrics
from wsim.runio import SUMMARY, Run, shrink


def size(folder):
    return sum(os.path.getsize(os.path.join(d, x))
               for d, _, xs in os.walk(folder) for x in xs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--yes", action="store_true", help="delete; without it "
                    "only list")
    a = ap.parse_args()
    total = 0
    for p in runroot.expand(a.runs):
        if not os.path.isdir(p):
            print(f"{p}: not found")
            continue
        r = Run(p)
        if not r.has("metrics"):
            if not a.yes:
                print(f"{r.name}: no metrics.json (made before shrinking)")
            else:
                metrics.write(r)
        gone = size(p) - sum(os.path.getsize(os.path.join(p, f))
                             for f in SUMMARY
                             if os.path.exists(os.path.join(p, f)))
        total += gone
        if a.yes:
            shrink(p)
        print(f"{r.name}: {gone / 1e6:.0f} MB {'removed' if a.yes else 'would go'}")
    print(f"total {total / 1e6:.0f} MB" + ("" if a.yes else
                                           " (--yes to delete)"))


if __name__ == "__main__":
    main()
