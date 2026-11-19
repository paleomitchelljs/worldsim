"""
WP7 stage C/D measures for one or more runs.

    ~/.venvs/worldsim/bin/python docs/upgrade/tools/wp7_mixing.py RUN [RUN...]

From final_state.npz (the presence table, or main + minority arrays for
older runs): cells with 2+ peoples over 10% of the cell's heads, the share
of heads not in their cell's plurality people, rows per occupied cell,
mixed city cells. From timeseries.csv: heads moved into held cells,
refugees and raids inside cells per 1,000 years.
"""
import os
import sys

import numpy as np
import pandas as pd


def table(d):
    N = len(d["pop"])
    if "rows_cell" in d.files:
        return d["rows_cell"], d["rows_people"], d["rows_heads"], N
    rc = np.concatenate([np.arange(N), np.arange(N)])
    rp = np.concatenate([d["people"], d["minority_people"]])
    rh = np.concatenate([d["pop"], d["minority_pop"]])
    return rc, rp, rh, N


def measure(run):
    d = np.load(os.path.join(run, "final_state.npz"))
    rc, rp, rh, N = table(d)
    live = (rp >= 0) & (rh > 0)
    rc, rp, rh = rc[live], rp[live], rh[live]
    tot = np.bincount(rc, weights=rh, minlength=N)
    share = rh / tot[rc]
    big = np.bincount(rc, weights=share > 0.1, minlength=N)
    occ = tot > 0
    top = np.zeros(N)
    np.maximum.at(top, rc, rh)
    m = {
        "occupied cells": int(occ.sum()),
        "rows per occupied cell": len(rc) / max(occ.sum(), 1),
        "cells with 2+ peoples": int((np.bincount(rc, minlength=N) >= 2).sum()),
        "cells with 2+ peoples over 10%": int((big >= 2).sum()),
        "cells with 3+ peoples over 10%": int((big >= 3).sum()),
        "heads not in the cell's plurality, share":
            1 - top[occ].sum() / tot[occ].sum(),
    }
    cities = pd.read_csv(os.path.join(run, "cities.csv"))
    alive = cities[cities["ended"].isna()] if "ended" in cities else cities
    cc = alive["cell"].to_numpy(int) if "cell" in alive else np.zeros(0, int)
    if len(cc):
        m["city cells with 2+ peoples over 10%"] = int((big[cc] >= 2).sum())
        m["city cells"] = len(cc)
    ts = pd.read_csv(os.path.join(run, "timeseries.csv"))
    for k in ("infiltrate_heads", "refugees", "raid_inner"):
        col = f"n_{k}"
        if col in ts:
            mil = (ts["year"] // 1000).astype(int)
            v = ts.groupby(mil)[col].sum()
            m[f"{k} by millennium"] = " ".join(f"{x:.3g}" for x in v)
    return m


def main():
    for run in sys.argv[1:]:
        print("=====", run)
        for k, v in measure(run).items():
            print(f"  {k:48s} {v if not isinstance(v, float) else f'{v:.4g}'}")


if __name__ == "__main__":
    main()
