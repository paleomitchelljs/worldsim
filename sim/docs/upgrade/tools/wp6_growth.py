"""
WP6 stage A measures (growth and recovery) for one or more runs.

    ~/.venvs/worldsim/bin/python docs/upgrade/tools/wp6_growth.py RUN [RUN...]

Prints, per run: timeline years (first city per people, 1M / 10M people,
first bronze / iron / steel), plague recovery, volatility (world and per
landmass group, from wsim.metrics), people shares by millennium, land
occupied by year, and the head-start arrivals' wander distances.
"""
import json
import os
import re
import sys

import numpy as np

SIM = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, SIM)
from wsim.runio import Run  # noqa: E402
from wsim import metrics  # noqa: E402


def first_year(yr, pop, x):
    i = np.nonzero(pop >= x)[0]
    return int(yr[i[0]]) if len(i) else None


def timeline(r):
    m = {}
    c = r.cities
    for k, g in c.groupby("people"):
        m[f"first city {k}"] = int(g["founded"].min())
    m["first city (any)"] = int(c["founded"].min()) if len(c) else None
    yr, pop = r.world_pop
    m["year of 1M"] = first_year(yr, pop, 1e6)
    m["year of 10M"] = first_year(yr, pop, 1e7)
    m["year of 100M"] = first_year(yr, pop, 1e8)
    ev = r.events
    t = ev[ev["kind"] == "tech"]
    for metal, pat in [("bronze", "cast bronze"), ("iron", "work iron"),
                       ("steel", "steel")]:
        s = t[t["text"].str.contains(pat) &
              ~t["text"].str.contains("out of use|no longer")]
        m[f"first {metal}"] = int(s["year"].min()) if len(s) else None
    return m


def plague_recovery(r):
    """For each state in each plague: its cells' population in the
    snapshot before, the lowest of the next 50 years; for a fall over 10%,
    years until the same cells are back to 90% of before."""
    H = r.history
    hy, pol = H["year"], H["polity"]
    pop = H["pop"]
    ev = r.events
    out = []
    for _, e in ev[ev["kind"] == "plague"].iterrows():
        # an epidemic (WP6 C) is logged when it ends; measure from its start
        y0 = e["start"] if "start" in e and e["start"] == e["start"] \
            else e["year"]
        i0 = int(np.searchsorted(hy, y0)) - 1
        if i0 < 0 or i0 + 1 >= len(hy):
            continue
        for p in e["polities"]:
            cells = pol[i0] == p
            if not cells.any():
                continue
            s = pop[:, cells].sum(axis=1).astype(float)
            before = s[i0]
            j1 = int(np.searchsorted(hy, y0 + 50))
            win = s[i0 + 1:j1 + 1]
            if not len(win) or before <= 0:
                continue
            low = win.min()
            if low / before > 0.9:
                continue
            k = i0 + 1 + int(np.argmin(win))
            back = np.nonzero(s[k:] >= 0.9 * before)[0]
            yrs = int(hy[k + back[0]] - y0) if len(back) else None
            out.append((int(y0), int(p), 1 - low / before, yrs))
    m = {"plague state-falls over 10%": len(out)}
    if out:
        rec = [o[3] for o in out if o[3] is not None]
        m["  never back to 90%"] = sum(o[3] is None for o in out)
        m["  fall, median"] = float(np.median([o[2] for o in out]))
        if rec:
            m["  years to 90%, median"] = float(np.median(rec))
            m["  years to 90%, 10-90%"] = (
                f"{np.percentile(rec, 10):.0f}-{np.percentile(rec, 90):.0f}")
    return m


def shares(r):
    ts = r.timeseries
    cols = [c for c in ts.columns if c.startswith("pop_")
            and c[4:] in r.keys]
    m = {}
    for y in range(1000, 8001, 1000):
        i = min(int(np.searchsorted(ts["year"], y - 5)), len(ts) - 1)
        row = ts[cols].iloc[i].to_numpy(float)
        tot = row.sum()
        if tot <= 0:
            continue
        sh = row / tot
        m[f"yr {y}"] = " ".join(f"{c[4:]}{100 * v:.1f}"
                                for c, v in zip(cols, sh))
        m[f"yr {y} log-share sd"] = float(np.std(np.log(np.maximum(sh, 1e-4))))
    return m


def land(r):
    H = r.history
    hy, lin = H["year"], H["lineage"]
    m = {}
    for y in [250, 400, 500, 1000, 2000, 3000, 5000, 8000]:
        i = min(int(np.searchsorted(hy, y)), len(hy) - 1)
        m[f"land occupied yr {int(hy[i])}"] = float((lin[i] >= 0).mean())
    ev = r.events
    o = ev[ev["kind"] == "origin"]
    for y, g in o.groupby("year"):
        d = g["text"].str.extract(r"\((\d+) km\)")[0].astype(float)
        m[f"arrivals yr {y}: wander km median"] = float(d.median())
    return m


def main(names):
    for n in names:
        r = Run(n)
        print(f"===== {n}")
        for f in (timeline, plague_recovery, metrics.volatility,
                  metrics.landmass_volatility, shares, land):
            try:
                d = f(r)
            except Exception as x:  # noqa: BLE001
                d = {f"{f.__name__} failed": repr(x)}
            for k, v in d.items():
                print(f"  {k:48s} {v:.4g}" if isinstance(v, float)
                      else f"  {k:48s} {v}")


if __name__ == "__main__":
    main(sys.argv[1:])
