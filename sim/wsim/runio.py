"""
Reading a finished (or running) run folder (WP2 stage B, 2026-11-17).

    from wsim.runio import Run
    r = Run("wp1f_fullclim_seed103")     # bare name: under the runs root
    r.wars                               # pandas DataFrame, read once
    r.history["pop"]                     # arrays from history.npz
    r.has("sieges")                      # False if absent or online-only

Tables are read on first use and kept. A file Dropbox has left online-only
(macOS "dataless": a non-empty file with no blocks on disk) is reported as
missing rather than read, since reading one can hang.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.dirname(HERE)
SF_DATALESS = 0x40000000

# table name -> file in the run folder
FILES = {
    "timeseries": "timeseries.csv",
    "timeseries_long": "timeseries_long.csv",
    "cities": "cities.csv",
    "polities": "polities.csv",
    "wars": "wars.csv",
    "sieges": "sieges.csv",
    "revolts": "revolts.csv",
    "refugees": "refugees.csv",
    "city_sizes": "city_sizes.csv",
    "cityfood": "cityfood.csv",
    "citytraits": "citytraits.csv",
    "deaths": "deaths.csv",
    "food": "food.csv",
    "growth": "growth.csv",
    "lineages": "lineages.csv",
    "price": "price.csv",
    "events": "events.jsonl",
    "history": "history.npz",
    "final": "final_state.npz",
    "config": "run.json",
    "metrics": "metrics.json",
}

# what a run kept with --keep summary (the default; U, 2026-11-21): enough
# for realism.py, the chronicle and a look at the end state
SUMMARY = ("run.json", "metrics.json", "checks.txt", "timeseries.csv",
           "chronicle.txt", "traits.txt", "final.png", "population.png")


def shrink(folder):
    """Delete everything in a run folder but SUMMARY; returns bytes freed."""
    import shutil
    freed = 0
    for f in os.listdir(folder):
        if f in SUMMARY:
            continue
        p = os.path.join(folder, f)
        if os.path.isdir(p):
            freed += sum(os.path.getsize(os.path.join(d, x))
                         for d, _, xs in os.walk(p) for x in xs)
            shutil.rmtree(p)
        else:
            freed += os.path.getsize(p)
            os.remove(p)
    return freed


class Missing(Exception):
    """A table the run does not have, or has only online."""


def resolve(name):
    """A run folder from a bare name (under the runs root) or a path."""
    if os.path.isdir(name):
        return name
    if SIM not in sys.path:
        sys.path.insert(0, SIM)
    import runroot
    return runroot.path(name)


def online_only(path):
    """True for a Dropbox placeholder whose data is not on this machine."""
    st = os.stat(path)
    return bool(getattr(st, "st_flags", 0) & SF_DATALESS) or \
        (st.st_size > 0 and st.st_blocks == 0)


class Run:
    def __init__(self, path, W=None):
        self.dir = resolve(path).rstrip("/")
        if not os.path.isdir(self.dir):
            raise FileNotFoundError(self.dir)
        self.name = os.path.basename(self.dir)
        self._W = W
        self._cache = {}

    def __repr__(self):
        return f"Run({self.dir!r})"

    def path(self, table):
        return os.path.join(self.dir, FILES.get(table, table))

    def status(self, table):
        """'ok', 'absent', 'empty' or 'online-only'."""
        p = self.path(table)
        if table == "events" and not os.path.exists(p):
            p = os.path.join(self.dir, "events.txt")
        if table == "timeseries_long" and not os.path.exists(p):
            p = self.path("timeseries")
        if table == "history" and not os.path.exists(p):
            parts = history_parts(self.dir)
            if parts:
                p = parts[0]
        if not os.path.exists(p):
            return "absent"
        if online_only(p):
            return "online-only"
        if os.path.getsize(p) == 0:
            return "empty"
        return "ok"

    def has(self, table):
        return self.status(table) == "ok"

    def get(self, table):
        if table in self._cache:
            return self._cache[table]
        s = self.status(table)
        if s != "ok":
            raise Missing(f"{self.name}: {FILES.get(table, table)} {s}")
        p = self.path(table)
        if table == "events":
            v = read_events(self.dir)
        elif table == "history":
            v = load_history(self.dir)
        elif table == "timeseries_long" and not os.path.exists(p):
            # runs before WP2 stage C: melted from the wide table
            v = long_table(self.timeseries, self.keys)
        elif p.endswith(".csv"):
            v = pd.read_csv(p, low_memory=False)
        elif p.endswith(".npz"):
            with np.load(p, allow_pickle=False) as z:
                v = {k: z[k] for k in z.files}
        elif p.endswith(".json"):
            with open(p) as fh:
                v = json.load(fh)
        else:
            raise KeyError(table)
        self._cache[table] = v
        return v

    def __getattr__(self, table):
        if table.startswith("_") or table not in FILES:
            raise AttributeError(table)
        return self.get(table)

    @property
    def W(self):
        """The world grid (geo.World) the run used (run.json's `world`,
        beside the default world file; world.gpkg for runs before WP8),
        built on first use (about 15 s)."""
        if self._W is None:
            from .geo import World
            from .params import GPKG_V1
            try:
                name = self.config.get("world")
            except Missing:
                name = None
            self._W = World(os.path.join(os.path.dirname(GPKG_V1), name)
                            if name else GPKG_V1)
        return self._W

    # ---- conveniences used by several measures

    @property
    def keys(self):
        ts = self.timeseries
        return [c[4:] for c in ts.columns if c.startswith("pop_")]

    @property
    def world_pop(self):
        """(years, world population) from timeseries.csv."""
        ts = self.timeseries
        return (ts["year"].to_numpy(),
                ts[[f"pop_{k}" for k in self.keys]].sum(axis=1).to_numpy())


def read_events(run_dir):
    """events.jsonl as a DataFrame; for runs before WP2 stage A, the
    year, kind and text of events.txt."""
    p = os.path.join(run_dir, "events.jsonl")
    if os.path.exists(p):
        with open(p) as fh:
            return pd.DataFrame([json.loads(line) for line in fh
                                 if line.strip()])
    rows = []
    with open(os.path.join(run_dir, "events.txt")) as fh:
        for line in fh:
            if line.strip():
                y, k, t = line.rstrip("\n").split(None, 2)
                rows.append(dict(year=int(y), kind=k, text=t))
    return pd.DataFrame(rows)


def split_col(name, keys):
    """(people, variable) for a timeseries.csv column (WP2 stage C):
    `pop_Hum` -> (Hum, pop), `violence_world` -> (ALL, violence), any
    other column -> (ALL, name)."""
    head, _, tail = name.rpartition("_")
    if head and tail in keys:
        return tail, head
    if head and tail == "world":
        return "ALL", head
    return "ALL", name


def long_table(ts, keys):
    """The wide timeseries as year, people, variable, value, without
    empty values."""
    m = ts.melt(id_vars="year", var_name="col").dropna(subset=["value"])
    pv = {c: split_col(c, keys) for c in m["col"].unique()}
    m["people"] = m["col"].map(lambda c: pv[c][0])
    m["variable"] = m["col"].map(lambda c: pv[c][1])
    return m[["year", "people", "variable", "value"]].reset_index(drop=True)


def history_parts(run_dir):
    """A running or killed run's snapshot files (history_parts/), in
    order."""
    d = os.path.join(run_dir, "history_parts")
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d))
            if f.endswith(".npz")]


def load_history(run_dir):
    """history.npz as a dict of arrays, from the whole file or, for a run
    that has not finished, its parts. `pop` is always there as float32
    heads: files from WP3 stage A on store it as float16 log1p."""
    p = os.path.join(run_dir, "history.npz")
    files = [p] if os.path.exists(p) else history_parts(run_dir)
    if not files:
        raise FileNotFoundError(p)
    zs = []
    for f in files:
        with np.load(f, allow_pickle=False) as z:
            zs.append({k: z[k] for k in z.files})
    H = zs[0] if len(zs) == 1 else {
        k: np.concatenate([z[k] for z in zs]) for k in zs[0]}
    if "pop" not in H:
        H["pop"] = np.expm1(H["pop_log1p"].astype(np.float32))
    return H
