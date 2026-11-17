"""
Realism checks on finished runs (2026-11-09), side by side. From the
review of 2026-11-09 (reviewdocs/REALISM_REVIEW.md): the city hierarchy,
the largest states, how wars end, how cities fare in crises, and what
kills people. References are rough orders of magnitude, not targets
(docs/diagnostics.md); judge across seeds.

  ~/.venvs/worldsim/bin/python realism.py runs/base_seed101 runs/ff_seed101 ...
  ~/.venvs/worldsim/bin/python realism.py --group runs/base_seed10? runs/ff_seed10?

--group pools runs whose names differ only in the seed (prefix before
"_seed") and shows the range across seeds.
"""
import argparse
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

import runroot

HERE = os.path.dirname(os.path.abspath(__file__))
GPKG = os.path.join(HERE, "..", "gis", "world.gpkg")
SF_DATALESS = 0x40000000
READS = ("timeseries", "city_sizes", "polities", "wars", "sieges", "cities",
         "deaths")


def land_km2():
    con = sqlite3.connect(f"file:{os.path.abspath(GPKG)}?mode=ro", uri=True)
    v = con.execute("select sum(area_km2) from cells where fic_land > 0"
                    ).fetchone()[0]
    con.close()
    return float(v)


def slope(sizes, n=200):
    s = np.sort(np.asarray(sizes, float))[::-1][:n]
    s = s[s > 0]
    if len(s) < 20:
        return np.nan
    return np.polyfit(np.log(np.arange(1, len(s) + 1)), np.log(s), 1)[0]


def near(years, y):
    return years[np.argmin(np.abs(years - y))]


def why_kind(s):
    return re.sub(r"\s*\(.*", "", s or "")


def measure(run, LAND):
    m = {}
    ts = pd.read_csv(os.path.join(run, "timeseries.csv"))
    keys = [c[4:] for c in ts.columns if c.startswith("pop_")]
    pop = ts[[f"pop_{k}" for k in keys]].sum(axis=1).to_numpy()
    yr = ts["year"].to_numpy()
    m["years"] = int(yr[-1])
    m["pop end (M)"] = pop[-1] / 1e6
    if "urban_share" in ts:
        m["urban share end"] = ts["urban_share"].iloc[-1]
        m["cities below URBAN_MIN, share"] = ts["cities_low_urban"].iloc[-1] / \
            max(1, ts[[c for c in ts.columns if c.startswith("cities_")
                       and c[7:] in keys]].sum(axis=1).iloc[-1])
    # city hierarchy
    cs = pd.read_csv(os.path.join(run, "city_sizes.csv"))
    cs = cs[cs.status == "city"]
    cy = np.sort(cs.year.unique())
    for y in (2000, 4000, 6000, 8000):
        if y <= cy[-1] + 25:
            m[f"rank-size slope, yr {y}"] = slope(
                cs[cs.year == near(cy, y)]["size"])
    last = cs[cs.year == cy[-1]]
    top = np.sort(last["size"].to_numpy())[::-1]
    if len(top) >= 10:
        m["largest city (k fe)"] = top[0] / 1e3
        m["largest / 10th city"] = top[0] / max(top[9], 1)
        m["largest city, share of world"] = top[0] / max(pop[-1], 1)
    if "size_old" in last:
        m["old-size slope, end"] = slope(last["size_old"])
    # states
    pol = pd.read_csv(os.path.join(run, "polities.csv"))
    km = pd.to_numeric(pol["peak_km2"], errors="coerce").dropna()
    km = np.sort(km.to_numpy())[::-1]
    if len(km) >= 10:
        m["largest state (M km2)"] = km[0] / 1e6
        m["largest state, share of land"] = km[0] / LAND
        m["largest / 10th state"] = km[0] / max(km[9], 1)
    if "vassals" in ts:
        m["vassals standing, mean yr 4000+"] = ts.loc[ts.year >= 4000,
                                                      "vassals"].mean()
    # wars
    wp = os.path.join(run, "wars.csv")
    if os.path.exists(wp):
        w = pd.read_csv(wp)
        w = w[w.why.fillna("") != "ongoing"]
        k = w.why.fillna("").map(why_kind)
        m["wars"] = len(w)
        for kind in ("defender fell", "tributary", "submitted", "ceded",
                     "goal met", "peace", "attacker fell", "repulsed"):
            m[f"war ends: {kind}"] = float((k == kind).mean())
        big = w.cities_dfn >= 5
        if big.any():
            m["defender fell | defender 5+ cities"] = float(
                (k[big] == "defender fell").mean())
        m["defender fell | defender 1 city"] = float(
            (k[w.cities_dfn == 1] == "defender fell").mean())
        m["wars settled within a tick"] = float((w.years == 0).mean())
    sp = os.path.join(run, "sieges.csv")
    if os.path.exists(sp):
        s = pd.read_csv(sp)
        if "terms" in s:
            won = s[s.taken == 1]
            for t in ("annex", "tributary", "sack"):
                m[f"won sieges: {t}"] = float((won.terms == t).mean()) \
                    if len(won) else np.nan
    # cities through time and crises
    c = pd.read_csv(os.path.join(run, "cities.csv"))
    m["cities founded"] = len(c)
    m["cities ended, share"] = float(c.ended.notna().mean())
    m["cities abandoned (urban_city), share"] = float(
        (c.end_reason == "abandoned").mean())
    f0 = 4000
    if yr[-1] >= f0 + 2000:
        a = c[(c.founded <= f0) & (c.ended.isna() | (c.ended > f0))]
        m["ended within 2000 yrs, of those alive at 4000"] = float(
            (a.ended.notna() & (a.ended <= f0 + 2000)).mean())
    # the largest fall of world population within 300 years, from year
    # 3000 (before then there are too few cities to read)
    win = int(300 / (yr[1] - yr[0]))
    best, at, i0 = 0.0, None, None
    s0 = int(np.searchsorted(yr, 3000))
    for i in range(s0, len(pop)):
        j = max(s0, i - win)
        k0 = j + int(np.argmax(pop[j:i + 1]))
        d = 1 - pop[i] / max(pop[k0], 1)
        if d > best:
            best, at, i0 = d, i, k0
    if at is not None and best > 0.1:
        m["worst 300-yr population fall"] = best
        m["  ...at year"] = int(yr[at])
        ccol = [x for x in ts.columns if x.startswith("cities_")
                and x[7:] in keys]
        n = ts[ccol].sum(axis=1).to_numpy()
        m["  ...cities, change over the fall"] = n[at] / max(n[i0], 1) - 1
        if "urban_fe" in ts:
            u = ts["urban_fe"].to_numpy()
            i2 = min(len(u) - 1, at + 20)
            m["  ...urban population, lowest vs before"] = \
                u[i0:i2 + 1].min() / max(u[i0], 1) - 1
            lo = ts["cities_low_urban"].to_numpy()
            m["  ...cities below URBAN_MIN, before -> most"] = \
                f"{lo[i0]} -> {lo[i0:i2 + 1].max()}"
    # what kills people
    dp = os.path.join(run, "deaths.csv")
    if os.path.exists(dp):
        d = pd.read_csv(dp)
        tot = d.deaths.sum()
        for cause, v in d.groupby("cause").deaths.sum().sort_values(
                ascending=False).items():
            m[f"deaths: {cause}"] = v / max(tot, 1)
    return m


def fmt(v):
    if isinstance(v, str):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    if isinstance(v, (int, np.integer)) or float(v).is_integer() and \
            abs(v) >= 100:
        return f"{int(v)}"
    return f"{v:.3g}" if abs(v) < 100 else f"{v:.0f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--group", action="store_true",
                    help="pool runs by the name before _seed")
    a = ap.parse_args()
    LAND = land_km2()
    # a run still going (or killed) is measured up to its last flush
    # (output.Stream); one that has not flushed yet has no polities.csv
    runs = sorted({r for r in runroot.expand(a.runs)
                   if os.path.exists(os.path.join(r, "timeseries.csv"))
                   and os.path.exists(os.path.join(r, "polities.csv"))
                   and os.path.getsize(os.path.join(r, "polities.csv")) > 0})
    # Dropbox can leave files online-only (macOS "dataless"); reading one
    # can hang, so skip the run and say so
    gone = [r for r in runs if any(
        getattr(os.stat(f), "st_flags", 0) & SF_DATALESS
        for f in (os.path.join(r, n + ".csv") for n in READS)
        if os.path.exists(f))]
    if gone:
        print("skipped, files online-only:",
              " ".join(os.path.basename(r) for r in gone), file=sys.stderr)
        runs = [r for r in runs if r not in gone]
    if not runs:
        sys.exit("no finished runs")
    res = {os.path.basename(r.rstrip("/")): measure(r, LAND) for r in runs}
    if a.group:
        groups = {}
        for name, mm in res.items():
            groups.setdefault(name.split("_seed")[0], []).append(mm)
        cols = {}
        for g, ms in groups.items():
            ks = list(dict.fromkeys(k for mm in ms for k in mm))
            col = {}
            for k in ks:
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
        cols = {n: {k: fmt(v) for k, v in mm.items()} for n, mm in
                res.items()}
    rows = list(dict.fromkeys(k for c in cols.values() for k in c))
    w0 = max(len(r) for r in rows)
    ws = {n: max(len(n), *(len(c.get(r, "")) for r in rows)) for n, c in
          cols.items()}
    print(f"land area {LAND / 1e6:.1f}M km2\n")
    print(" " * w0 + "  " + "  ".join(n.rjust(ws[n]) for n in cols))
    for r in rows:
        print(r.ljust(w0) + "  " + "  ".join(
            cols[n].get(r, "").rjust(ws[n]) for n in cols))


if __name__ == "__main__":
    main()
