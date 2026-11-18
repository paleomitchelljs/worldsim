"""
Measures of finished runs side by side (2026-11-09; since WP2 stage B,
2026-11-17, a printer over each run's metrics.json, made by
wsim/metrics.py). References are rough orders of magnitude, not targets
(docs/diagnostics.md); judge across seeds.

  ~/.venvs/worldsim/bin/python realism.py runs/base_seed101 runs/ff_seed101 ...
  ~/.venvs/worldsim/bin/python realism.py --group 'wp1f_fullclim_seed10?'
  ~/.venvs/worldsim/bin/python realism.py --only wars,sieges RUN ...
  ~/.venvs/worldsim/bin/python realism.py --cross RUN RUN ...

--group pools runs whose names differ only in the seed (prefix before
"_seed") and shows the range across seeds. A run without metrics.json (or
any run, with --rebuild) is measured from its raw files; --save then
writes metrics.json into it. --cross prints the pairwise map measures
(metrics.cross) instead.
"""
import argparse
import json
import os
import sys

import numpy as np

import runroot
from wsim import metrics
from wsim.runio import Missing, Run


def fmt(v):
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    if isinstance(v, (int, np.integer)) or float(v).is_integer() and \
            abs(v) >= 100:
        return f"{int(v)}"
    return f"{v:.3g}" if abs(v) < 100 else f"{v:.0f}"


def load(r, rebuild, only, save, W):
    if not rebuild and r.has("metrics"):
        m = r.metrics
        if only:
            m = {k: v for k, v in m.items() if k in only}
        return m
    r._W = W[0] if W else None
    m = metrics.measure(r, only)
    W[:] = [r.W] if r._W is not None else W
    if save and not only:
        metrics.write(r)
    return m


def table(cols):
    rows = list(dict.fromkeys(k for c in cols.values() for k in c))
    w0 = max(len(r) for r in rows)
    ws = {n: max(len(n), *(len(c.get(r, "")) for r in rows)) for n, c in
          cols.items()}
    print(" " * w0 + "  " + "  ".join(n.rjust(ws[n]) for n in cols))
    for r in rows:
        if r.startswith("== "):
            print(r)
            continue
        print(r.ljust(w0) + "  " + "  ".join(
            cols[n].get(r, "").rjust(ws[n]) for n in cols))


def flat(m):
    """{function: {measure: v}} -> ordered {row label: v} with headers."""
    out = {}
    for f, d in m.items():
        if f.startswith("_") or not isinstance(d, dict):
            continue
        out[f"== {f}"] = ""
        out.update(d)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--group", action="store_true",
                    help="pool runs by the name before _seed")
    ap.add_argument("--rebuild", action="store_true",
                    help="measure from the raw files, ignoring metrics.json")
    ap.add_argument("--save", action="store_true",
                    help="write metrics.json into runs measured here")
    ap.add_argument("--only", help="comma-separated measure functions")
    ap.add_argument("--cross", action="store_true",
                    help="pairwise final-map measures across the runs")
    a = ap.parse_args()
    only = set(a.only.split(",")) if a.only else None
    runs = []
    for p in runroot.expand(a.runs):
        try:
            r = Run(p)
        except FileNotFoundError:
            print("no such run:", p, file=sys.stderr)
            continue
        # a run still going (or killed) is measured up to its last flush
        s = [r.status(t) for t in ("timeseries", "polities")]
        if s != ["ok", "ok"] and not r.has("metrics"):
            print(f"skipped {r.name}: timeseries {s[0]}, polities {s[1]}",
                  file=sys.stderr)
            continue
        runs.append(r)
    if not runs:
        sys.exit("no finished runs")
    if a.cross:
        rows = metrics.cross(runs)
        for d in rows:
            print(f"{d['a']} vs {d['b']}: " + "  ".join(
                f"{k} {fmt(v)}" for k, v in d.items() if k not in ("a", "b")))
        return
    W, res = [], {}
    for r in runs:
        try:
            m = load(r, a.rebuild, only, a.save, W)
        except Missing as e:
            print("skipped:", e, file=sys.stderr)
            continue
        for x in m.get("_missing", []):
            print(f"{r.name}: not measured, {x}", file=sys.stderr)
        res[r.name] = flat(m)
    if a.group:
        groups = {}
        for name, mm in res.items():
            groups.setdefault(name.split("_seed")[0], []).append(mm)
        cols = {}
        for g, ms in groups.items():
            ks = list(dict.fromkeys(k for mm in ms for k in mm))
            col = {}
            for k in ks:
                if k.startswith("== "):
                    col[k] = ""
                    continue
                v = [mm[k] for mm in ms if k in mm and mm[k] is not None
                     and not (isinstance(mm[k], float) and np.isnan(mm[k]))]
                if not v:
                    col[k] = "-"
                elif isinstance(v[0], str):
                    col[k] = ", ".join(v)
                elif len(v) == 1:
                    col[k] = fmt(v[0])
                else:
                    col[k] = f"{fmt(min(v))} .. {fmt(max(v))}"
            col["seeds"] = str(len(ms))
            cols[f"{g} (n={len(ms)})"] = col
    else:
        cols = {n: {k: ("" if k.startswith("== ") else fmt(v))
                    for k, v in mm.items()} for n, mm in res.items()}
    table(cols)


if __name__ == "__main__":
    main()
