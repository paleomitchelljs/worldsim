"""
Measures of a run (WP2 stage B, 2026-11-17).

Each single-run function takes a runio.Run and returns a flat dict of
numbers (an occasional string where a number would mislead). They are
checks, not targets (docs/upgrade/GUIDE.md): read them across seeds.
Definitions follow docs/upgrade/BASELINE.md; where a measure came from
realism.py or the old write_checks, the definition is unchanged.

    from wsim.runio import Run
    from wsim import metrics
    m = metrics.measure(Run("wp1f_fullclim_seed103"))   # {function: dict}
    metrics.cross([Run(a), Run(b)])                      # pairwise maps

`measure` is what worldsim.py writes to metrics.json at the end of a run
and what realism.py prints.
"""
import json
import math
import os
import re
import sys

import numpy as np
import pandas as pd
from scipy import ndimage
from scipy.spatial import cKDTree

from .params import NX, SAIL_D0, SAIL_D1, BIOMES, TRAITS
from .runio import Missing

EARTH_R = 6371.0


def near(years, y):
    """The year in `years` closest to y."""
    return years[np.argmin(np.abs(years - y))]


def rank_slope(sizes, n=200):
    """Slope of log size on log rank over the n largest (Zipf: about -1);
    NaN under 20."""
    s = np.sort(np.asarray(sizes, float))[::-1][:n]
    s = s[s > 0]
    if len(s) < 20:
        return np.nan
    return float(np.polyfit(np.log(np.arange(1, len(s) + 1)), np.log(s), 1)[0])


def share(mask):
    mask = np.asarray(mask)
    return float(mask.mean()) if len(mask) else np.nan


# ---- population ----------------------------------------------------------

def _end(yr):
    """The run's nominal end: the last row is one tick before it."""
    return int(yr[-1] + (yr[1] - yr[0]))


def population(run):
    """World population through time (at y, the last tick before y),
    urban share, herding share."""
    yr, pop = run.world_pop
    ts = run.timeseries
    m = {"years": _end(yr), "pop end (M)": pop[-1] / 1e6}
    for y in range(1000, _end(yr) + 1, 1000):
        i = min(int(np.searchsorted(yr, y - 5)), len(yr) - 1)
        m[f"pop yr {y} (M)"] = pop[i] / 1e6
    if "urban_share" in ts:
        m["urban share end"] = float(ts["urban_share"].iloc[-1])
        ccol = [c for c in ts.columns if c.startswith("cities_")
                and c[7:] in run.keys]
        m["cities below URBAN_MIN, share"] = float(
            ts["cities_low_urban"].iloc[-1] /
            max(1, ts[ccol].sum(axis=1).iloc[-1]))
    if "herd_share" in ts:
        i = int(ts["herd_share"].idxmax())
        m["herding share, peak"] = float(ts["herd_share"].iloc[i])
        m["herding share, peak year"] = int(yr[i])
    if "minority_pop" in ts:
        m["minority share of heads, end"] = float(
            ts["minority_pop"].iloc[-1] / max(pop[-1], 1))
    return m


def growth(run):
    """Growth, %/yr, over each millennium (log change of world population
    from year y-1000 to the last tick before y)."""
    yr, pop = run.world_pop
    m = {}
    for y in range(1000, _end(yr) + 1, 1000):
        i = min(int(np.searchsorted(yr, y - 5)), len(yr) - 1)
        j = int(np.searchsorted(yr, y - 1000)) if y > 1000 else 0
        m[f"growth %/yr, {y - 1000}-{y}"] = float(
            np.log(pop[i] / max(pop[j], 1)) / max(yr[i] - yr[j], 1) * 100)
    return m


def _wobble(yr, lp, step):
    """sd of log population around its centred 200-year mean, and the
    largest 100-year fall, for a series `step` years apart."""
    k = max(1, int(round(200 / step)))
    sm = np.convolve(lp, np.ones(k) / k, "same")
    res = (lp - sm)[k:-k] if len(lp) > 2 * k else np.array([])
    h = max(1, int(round(100 / step)))
    d = lp[h:] - lp[:-h] if len(lp) > h else np.array([np.nan])
    return (float(res.std()) if len(res) else np.nan, float(np.min(d)))


def timeline(run):
    """First city; years the world reaches 1M, 10M and 100M people; first
    bronze, iron and steel anywhere (as docs/upgrade/tools/wp6_growth.py;
    in metrics.json from WP9 stage B, 2026-11-20). NaN when never."""
    c = run.cities
    yr, pop = run.world_pop
    m = {"first city (yr)": float(c.founded.min()) if len(c) else np.nan}
    for x, nm in ((1e6, "1M"), (1e7, "10M"), (1e8, "100M")):
        i = np.nonzero(pop >= x)[0]
        m[f"year of {nm}"] = float(yr[i[0]]) if len(i) else np.nan
    ev = run.events
    t = ev[ev["kind"] == "tech"]
    for metal, pat in (("bronze", "cast bronze"), ("iron", "work iron"),
                       ("steel", "steel")):
        k = t[t["text"].str.contains(pat) &
              ~t["text"].str.contains("out of use|no longer")]
        m[f"first {metal} (yr)"] = float(k.year.min()) if len(k) else np.nan
    return m


def volatility(run):
    """World population after year 3000: sd of log population around its
    200-year mean, the largest 100-year fall (log), and the largest fall
    within 300 years with what cities did over it (from realism.py)."""
    yr, pop = run.world_pop
    ts = run.timeseries
    m = {}
    s = yr >= 3000
    if s.sum() > 100:
        step = float(yr[1] - yr[0])
        sd, fall = _wobble(yr[s], np.log(np.maximum(pop[s], 1)), step)
        m["log pop sd around 200-yr mean, after 3000"] = sd
        m["largest 100-yr fall (log), after 3000"] = fall
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
        m["worst 300-yr population fall"] = float(best)
        m["  ...at year"] = int(yr[at])
        ccol = [x for x in ts.columns if x.startswith("cities_")
                and x[7:] in run.keys]
        n = ts[ccol].sum(axis=1).to_numpy()
        m["  ...cities, change over the fall"] = float(n[at] / max(n[i0], 1) - 1)
        if "urban_fe" in ts:
            u = ts["urban_fe"].to_numpy()
            i2 = min(len(u) - 1, at + 20)
            m["  ...urban population, lowest vs before"] = float(
                u[i0:i2 + 1].min() / max(u[i0], 1) - 1)
            lo = ts["cities_low_urban"].to_numpy()
            m["  ...cities below URBAN_MIN, before"] = int(lo[i0])
            m["  ...cities below URBAN_MIN, most"] = int(lo[i0:i2 + 1].max())
    return m


def landmass_volatility(run):
    """The same two volatility measures per landmass group (landmasses.py:
    S, W, N, E, X), from history.npz. Its snapshots are 25 years apart
    from WP3 stage A, 100 before; with 100, the 200-year mean is over 3
    snapshots, so these are coarser than the world figures."""
    from .runio import SIM
    if SIM not in sys.path:
        sys.path.insert(0, SIM)
    from landmasses import CODES, GROUPS
    H, W = run.history, run.W
    hy = H["year"]
    s = hy >= 3000
    m = {}
    if s.sum() < 6:
        return m
    lm = W.landmass
    for g, codes in GROUPS.items():
        ids = [i for i, c in CODES.items() if c in codes]
        cells = np.isin(lm, ids)
        p = H["pop"][s][:, cells].sum(axis=1)
        if p.min() <= 0:
            continue
        sd, fall = _wobble(hy[s], np.log(p), float(hy[1] - hy[0]))
        m[f"{g}: log pop sd around 200-yr mean, after 3000"] = sd
        m[f"{g}: largest 100-yr fall (log), after 3000"] = fall
    return m


# ---- cities --------------------------------------------------------------

def city_hierarchy(run):
    """Rank-size slope of cities (status 'city' in city_sizes.csv) at
    2000-year marks and at the end; the largest city against the 10th and
    the world."""
    yr, pop = run.world_pop
    cs = run.city_sizes
    cs = cs[cs.status == "city"]
    m = {}
    if not len(cs):
        return m
    cy = np.sort(cs.year.unique())
    for y in range(2000, int(cy[-1]) + 26, 2000):
        if y <= cy[-1] + 25:
            m[f"rank-size slope, yr {y}"] = rank_slope(
                cs[cs.year == near(cy, y)]["size"])
    last = cs[cs.year == cy[-1]]
    m["rank-size slope, end (top 200)"] = rank_slope(last["size"])
    top = np.sort(last["size"].to_numpy())[::-1]
    if len(top) >= 10:
        m["largest city (k fe)"] = top[0] / 1e3
        m["largest / 10th city"] = top[0] / max(top[9], 1)
        m["largest city, share of world"] = top[0] / max(pop[-1], 1)
    if "size_old" in last:
        m["old-size slope, end"] = rank_slope(last["size_old"])
    return m


def city_lives(run):
    """Cities founded and ended; how many alive at year 4000 ended within
    2000 years."""
    c = run.cities
    yr, _ = run.world_pop
    m = {"cities founded": len(c),
         "cities ended, share": share(c.ended.notna()),
         "cities abandoned (urban_city), share":
             share(c.end_reason == "abandoned")}
    f0 = 4000
    if yr[-1] >= f0 + 2000:
        a = c[(c.founded <= f0) & (c.ended.isna() | (c.ended > f0))]
        m["ended within 2000 yrs, of those alive at 4000"] = share(
            a.ended.notna() & (a.ended <= f0 + 2000))
    return m


# ---- states --------------------------------------------------------------

def states(run):
    """Polities: how many, how many never pass one city, the largest at its
    peak, and the size distribution of those with 3+ cities."""
    pol = run.polities
    land = float(run.W.area.sum())
    m = {"polities": len(pol)}
    one = pol.peak_cities <= 1
    m["never above one city, share"] = share(one)
    life1 = pol.loc[one & pol.ended.notna(), "years"]
    m["never above one city, median life (yr)"] = float(life1.median()) \
        if len(life1) else np.nan
    if "origin" in pol:
        # founded by a city outside any state: mostly one city whose
        # abandonment ends it (WP5 stage A); reported apart (U, 2026-11-18)
        out = pol.origin.fillna("") == "city_outside"
        m["founded by a city outside a state, share"] = share(out)
        m["never above one city, others, share"] = share(one[~out])
        life2 = pol.loc[one & ~out & pol.ended.notna(), "years"]
        m["never above one city, others, median life (yr)"] = float(
            life2.median()) if len(life2) else np.nan
    km = np.sort(pd.to_numeric(pol["peak_km2"], errors="coerce")
                 .dropna().to_numpy())[::-1]
    if len(km) >= 10:
        m["largest state (M km2)"] = km[0] / 1e6
        m["largest state, share of land"] = km[0] / land
        m["largest / 10th state"] = km[0] / max(km[9], 1)
    big = pol[pol.peak_cities >= 3]
    sz = np.sort(big.peak_cells.to_numpy(float))[::-1]
    if len(sz) >= 10:
        lg = np.log(sz[sz > 0])
        m["states with 3+ cities"] = len(sz)
        m["peak cells, largest"] = sz[0]
        m["peak cells, 10th"] = sz[9]
        m["peak cells, median"] = float(np.median(sz))
        m["skew of log peak cells"] = float(
            ((lg - lg.mean()) ** 3).mean() / max(lg.std(), 1e-9) ** 3)
    if "peoples_ruled" in big:
        m["3+ city states ruling >1 people, share"] = share(
            big.peoples_ruled.fillna("").str.split().str.len() > 1)
    ts = run.timeseries
    if "vassals" in ts:
        m["vassals standing, mean yr 4000+"] = float(
            ts.loc[ts.year >= 4000, "vassals"].mean())
    return m


def lifespans(run):
    """Lifespans of ended states that held 3+ cities (reference: mean
    ~200-250 yrs, roughly exponential, CV ~1; Arbesman 2011)."""
    pol = run.polities
    L = pol.loc[(pol.peak_cities >= 3) & pol.ended.notna(), "years"
                ].to_numpy(float)
    if not len(L):
        return {}
    return {"ended 3+ city states": len(L),
            "lifespan mean (yr)": float(L.mean()),
            "lifespan median (yr)": float(np.median(L)),
            "lifespan CV": float(L.std() / max(L.mean(), 1)),
            "lifespan over 1000 yr, share": float((L > 1000).mean()),
            "lifespan over 1000 yr, count": int((L > 1000).sum()),
            "lifespan longest (yr)": float(L.max())}


def _components(rows, cols):
    """8-connected pieces of a set of grid cells, joined across the
    longitude seam; labels 0..n-1 in the input order."""
    r0 = rows.min()
    g = np.zeros((rows.max() - r0 + 1, NX), bool)
    g[rows - r0, cols] = True
    lab, n = ndimage.label(g, structure=np.ones((3, 3)))
    parent = list(range(n + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for r in range(g.shape[0]):
        a = lab[r, NX - 1]
        if not a:
            continue
        for dr in (-1, 0, 1):
            if 0 <= r + dr < g.shape[0] and lab[r + dr, 0]:
                parent[find(a)] = find(lab[r + dr, 0])
    lc = np.array([find(x) for x in lab[rows - r0, cols]])
    _, out = np.unique(lc, return_inverse=True)
    return out


def _sea_join(lab, xyz, reach_km):
    """Join pieces whose nearest cells are within reach_km (great circle)
    of each other: threshold single linkage, by repeated nearest-piece
    merges (Boruvka). Returns new labels."""
    chord = 2 * math.sin(min(reach_km / EARTH_R, math.pi) / 2)
    lab = lab.copy()
    while True:
        pieces = np.unique(lab)
        if len(pieces) == 1:
            return np.zeros_like(lab)
        merged = False
        for p in pieces:
            inn = lab == p
            if not inn.any():
                continue
            d, j = cKDTree(xyz[~inn]).query(xyz[inn], k=1)
            k = int(np.argmin(d))
            if d[k] <= chord:
                q = lab[~inn][j[k]]
                lab[lab == q] = p
                merged = True
        if not merged:
            _, lab = np.unique(lab, return_inverse=True)
            return lab


def contiguity(run):
    """The ten largest states at the end (cells of final_state.npz):
    land pieces (8-connected cells), and groups of pieces once those
    within the state's sailing range of each other are joined (range
    SAIL_D0 + SAIL_D1 x sail^1.5 km, sail of the state's lineage in
    polities.csv, read from lineages.csv). Each with its largest share."""
    F = run.final
    pol = F["polity"]
    ids, n = np.unique(pol[pol >= 0], return_counts=True)
    top = ids[np.argsort(-n, kind="stable")][:10]
    P = run.polities.set_index("id")
    sail = run.lineages.set_index("id")["sail"] if run.has("lineages") \
        else None
    W = run.W
    lon, lat = np.radians(W.lon), np.radians(W.lat)
    xyz = np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon),
                np.sin(lat)]
    m, land_n, sea_n = {}, [], []
    for k, pid in enumerate(top, 1):
        c = np.nonzero(pol == pid)[0]
        lab = _components(F["row"][c], F["col"][c])
        sz = np.bincount(lab)
        m[f"state {k}: cells"] = len(c)
        m[f"state {k}: land pieces"] = len(sz)
        m[f"state {k}: largest land piece, share"] = sz.max() / len(c)
        land_n.append(len(sz))
        if sail is not None and pid in P.index:
            lin = int(str(P.loc[pid, "lineage"]).lstrip("L"))
            s = float(sail.get(lin, 0.0))
            reach = SAIL_D0 + SAIL_D1 * max(s, 0) ** 1.5
            g = np.bincount(_sea_join(lab, xyz[c], reach))
            m[f"state {k}: sailing range (km)"] = reach
            m[f"state {k}: groups joined by sea"] = len(g)
            m[f"state {k}: largest group, share"] = g.max() / len(c)
            sea_n.append(len(g))
    if land_n:
        m["top 10, median land pieces"] = float(np.median(land_n))
    if sea_n:
        m["top 10, median groups joined by sea"] = float(np.median(sea_n))
    return m


# ---- war -----------------------------------------------------------------

def why_kind(s):
    return re.sub(r"\s*\(.*", "", s or "")


def wars(run):
    """Wars: every row of wars.csv (BASELINE.md). How they end counts only
    wars that ended."""
    w = run.wars
    m = {"wars": len(w),
         "wars ending inside one tick, share": share(w.years == 0),
         "wars ending within 5 yrs, share": share(w.years <= 5),
         "wars with 0-1 sieges, share": share(w.sieges <= 1)}
    peer = (w.cities_att >= 5) & (w.cities_dfn >= 5)
    m["peer wars (both 5+ cities)"] = int(peer.sum())
    m["peer wars, share"] = share(peer)
    yr, _ = run.world_pop
    for y in range(1000, _end(yr), 1000):
        m[f"wars started {y}-{y + 1000}"] = int(
            ((w.start >= y) & (w.start < y + 1000)).sum())
    e = w[w.why.fillna("") != "ongoing"]
    k = e.why.fillna("").map(why_kind)
    for kind in ("defender fell", "tributary", "submitted", "ceded",
                 "goal met", "peace", "attacker fell", "repulsed"):
        m[f"war ends: {kind}"] = share(k == kind)
    big = e.cities_dfn >= 5
    if big.any():
        m["defender fell | defender 5+ cities"] = share(
            k[big] == "defender fell")
    m["defender fell | defender 1 city"] = share(
        k[e.cities_dfn == 1] == "defender fell")
    return m


def sieges(run):
    """Sieges: share taken, terms of those won, and the besieger's win
    probability at launch (`odds`), by side: 'att' the attacker's sieges,
    'dfn' the defender's counter-offensives."""
    s = run.sieges
    m = {"sieges": len(s), "sieges taken, share": share(s.taken == 1)}
    if "terms" in s:
        won = s[s.taken == 1]
        for t in ("annex", "tributary", "sack"):
            m[f"won sieges: {t}"] = share(won.terms == t) if len(won) \
                else np.nan
    if "odds" in s:
        groups = [("all", s)]
        if "side" in s:
            groups += [(v, s[s.side == v]) for v in ("att", "dfn")]
        for name, g in groups:
            o = g.odds.dropna()
            m[f"siege odds at launch, {name}: n"] = len(o)
            m[f"siege odds at launch, {name}: median"] = float(o.median()) \
                if len(o) else np.nan
            m[f"siege odds at launch, {name}: share < 0.1"] = share(o < 0.1)
    return m


def war_time(run):
    """Share of states (2+ cities) at war: mean over the run and by
    millennium (reference: high in pre-modern state systems; Levy 1983;
    uncertain)."""
    ts = run.timeseries
    if "at_war_share" not in ts:
        return {}
    m = {"at war, mean over run": float(ts.at_war_share.mean())}
    for y in range(0, _end(ts.year.to_numpy()), 1000):
        v = ts.loc[(ts.year >= y) & (ts.year < y + 1000), "at_war_share"]
        m[f"at war, {y}-{y + 1000}"] = float(v.mean())
    return m


# ---- food, deaths, where people live -------------------------------------

def food(run):
    """Where city food came from in the last year of cityfood.csv: shares
    of trade, rent, provincial spending and capital in their sum; trade
    food created in the last tick (n_ff_trade)."""
    m = {}
    cf = run.cityfood
    last = cf[cf.year == cf.year.max()]
    cols = ["from_trade", "from_rent", "from_prov", "from_capital"]
    tot = last[cols].to_numpy().sum()
    for c in cols:
        m[f"city food {c[5:]}, share"] = float(last[c].sum() / max(tot, 1e-9))
    ts = run.timeseries
    if "n_ff_trade" in ts:
        m["trade food created, last tick (fe)"] = float(ts.n_ff_trade.iloc[-1])
    return m


def food_ledger(run):
    """The world food account (food.csv, WP4 stage A), by millennium,
    from the century means: food created (trade food and the city boost)
    as a share of food produced and of food in cities; the account's gap
    (taken - received - lost) and the take with no city to arrive in, as
    shares of the take; capital food that reached no ruling people;
    under `trade_debit`, food sold and the share lost on the way."""
    f = run.food
    w = f[f.scope == "world"]
    m = {}
    yr = w.year.to_numpy()
    for y in range(0, _end(yr), 1000):
        s = w[(w.year > y) & (w.year <= y + 1000)].sum(numeric_only=True)
        if s.produced <= 0:
            continue
        t = f"{y}-{y + 1000}"
        m[f"created / produced, {t}"] = s.created / s.produced
        m[f"created / city food, {t}"] = s.created / max(s.city_food, 1e-9)
        m[f"trade / created, {t}"] = s.created_trade / max(s.created, 1e-9)
        m[f"eaten / produced, {t}"] = s.eaten / s.produced
        m[f"taken / produced, {t}"] = s.taken / s.produced
        if "trade_out" in s:          # from WP4 stage B
            m[f"trade out / produced, {t}"] = s.trade_out / s.produced
            m[f"trade lost / trade out, {t}"] = \
                s.lost_trade / max(s.trade_out, 1e-9)
    s = w.sum(numeric_only=True)
    tk = max(s.taken, 1e-9)
    m["gap / taken, run"] = s.gap / tk
    m["unplaced / taken, run"] = s.unplaced / tk
    m["capital food reaching no ruling people / received capital, run"] = \
        s.cap_unused / max(s.received_capital, 1e-9)
    return m


def deaths(run):
    """Deaths by cause, as shares of all counted deaths over the run."""
    d = run.deaths
    tot = d.deaths.sum()
    return {f"deaths: {c}": float(v / max(tot, 1)) for c, v in
            d.groupby("cause").deaths.sum().sort_values(
                ascending=False).items()}


def growth_account(run):
    """The world's growth account over the run (growth.csv, WP4 stage
    C), in heads: natural increase, removals and growth forgone under
    dragons, each against natural increase; each phase's net change for
    the world, which should be 0 (people only move between peoples), as
    a share of natural increase; the largest |residual| of a century."""
    g = run.growth
    w = g[g.people == "ALL"]
    s = w.sum(numeric_only=True)
    nat = max(s.natural, 1e-9)
    m = {"natural increase, run (M)": s.natural / 1e6,
         "removals / natural": s.removals / nat,
         "forgone under dragons / natural": s.forgone_dragon / nat,
         "change / natural": s.change / nat}
    for c in [c for c in w.columns if c.startswith("net_")]:
        m[f"{c} (world) / natural"] = s[c] / nat
    m["largest |residual| of a century"] = float(w.residual.abs().max())
    return m


def settlement(run):
    """Where people live at the end (final_state.npz): population share
    against land share by coast, river (as at the end), alluvial fill,
    latitude band and biome; density; how much is in states."""
    F, W = run.final, run.W
    p = F["pop"]
    tot, area = max(p.sum(), 1), W.area
    land = area.sum()
    river = F["river"].astype(bool) if "river" in F else W.river
    m = {}
    for nm, k in (("coast", W.coastal), ("river", river),
                  ("coast or river", W.coastal | river),
                  ("alluvial fill", W.alluvial)):
        m[f"{nm}: pop share"] = float(p[k].sum() / tot)
        m[f"{nm}: land share"] = float(area[k].sum() / land)
    lat = np.abs(W.lat)
    for lo, hi in ((0, 15), (15, 30), (30, 45), (45, 60), (60, 90)):
        k = (lat >= lo) & (lat < hi)
        m[f"|lat| {lo}-{hi}: pop share"] = float(p[k].sum() / tot)
        m[f"|lat| {lo}-{hi}: land share"] = float(area[k].sum() / land)
    for b, name in enumerate(BIOMES):
        k = W.biome == b
        m[f"{name}: pop share"] = float(p[k].sum() / tot)
        m[f"{name}: density (/km2)"] = float(p[k].sum() / max(area[k].sum(), 1))
    d = p / area
    m["density, world (/km2)"] = float(tot / land)
    for q, v in zip((50, 90, 99, 100),
                    np.percentile(d[p > 0], [50, 90, 99, 100])):
        m[f"cell density p{q} (/km2)"] = float(v)
    m["occupied share of land cells"] = float((p > 0).mean())
    inst = F["polity"] >= 0
    m["population in a state, share"] = float(p[inst].sum() / tot)
    m["land area in a state, share"] = float(area[inst].sum() / land)
    m["land cells in a state, share"] = float(inst.mean())
    return m


def turnover(run):
    """history.npz, per 500-year window from 1000: of cells occupied at
    both ends, the share whose people changed; of occupied cells at the
    window's end, the share inside a state; of cells occupied at its
    start, the share emptied."""
    H = run.history
    hy, hpe, hpol = H["year"], H["people"], H["polity"]
    m = {}
    for y0 in range(1000, int(hy[-1]), 500):
        i, j = np.searchsorted(hy, y0), np.searchsorted(hy, y0 + 500)
        if j >= len(hy):
            break
        a, b = hpe[i], hpe[j]
        occ = (a >= 0) & (b >= 0)
        w = f"{y0}-{y0 + 500}"
        m[f"people changed, {w}"] = float(((a != b) & occ).sum() /
                                          max(occ.sum(), 1))
        m[f"in a state at end, {w}"] = float(
            ((hpol[j] >= 0) & (b >= 0)).sum() / max((b >= 0).sum(), 1))
        m[f"emptied, {w}"] = float(((a >= 0) & (b < 0)).sum() /
                                   max((a >= 0).sum(), 1))
    return m


def price(run):
    """Price decomposition of trait change, summed over the run: the world
    (lineages as units), and the mean over peoples of each people's sums."""
    pr = run.price
    m = {}
    for t in TRAITS:
        r = pr[(pr.people == "ALL") & (pr.trait == t)]
        if not len(r):
            continue
        m[f"{t}: selection, world"] = float(r.selection.sum())
        m[f"{t}: transmission, world"] = float(r.transmission.sum())
        q = pr[(pr.people != "ALL") & (pr.trait == t)].groupby("people")
        if len(q):
            m[f"{t}: selection, mean over peoples"] = float(
                q.selection.sum().mean())
            m[f"{t}: transmission, mean over peoples"] = float(
                q.transmission.sum().mean())
    return m


# ---- held-out patterns (WP9 stage A, 2026-11-20) --------------------------
# Patterns no value has been chosen on (docs/patterns.md). Each is read on
# its spread across seeds; none has a target.

SPACING_KM = 300.0      # radius of the local density around a city (C)


def _km(chord):
    return 2 * EARTH_R * np.arcsin(np.clip(chord / 2, 0, 1))


def spacing(run):
    """Cities standing at the end: distance to the nearest other city
    against the density of people within SPACING_KM (central-place
    spacing: denser land, closer cities). Spearman rank correlation."""
    from scipy.stats import spearmanr
    cs = run.city_sizes
    cs = cs[cs.status == "city"]
    cells = np.unique(cs.loc[cs.year == cs.year.max(), "cell"].to_numpy())
    if len(cells) < 10:
        return {}
    W, p = run.W, run.final["pop"]
    d, _ = cKDTree(W.xyz[cells]).query(W.xyz[cells], k=2)
    nn = _km(d[:, 1])
    r = 2 * math.sin(SPACING_KM / EARTH_R / 2)
    tree = cKDTree(W.xyz)
    dens = np.array([p[j].sum() / W.area[j].sum() for j in
                     tree.query_ball_point(W.xyz[cells], r)])
    rho = spearmanr(nn, dens)[0]
    return {"cities at the end": len(cells),
            "nearest city, median (km)": float(np.median(nn)),
            "nearest city, p10-p90 ratio": float(
                np.percentile(nn, 90) / max(np.percentile(nn, 10), 1)),
            "spacing vs local density, Spearman rho": float(rho)}


def minor_states(run):
    """Size distribution of states below the top ten: rank-size slope of
    peak cells over ranks 11-100 of every polity, and over ranks 11-100 of
    the states standing at the end (cells of final_state.npz)."""
    m = {}
    pk = np.sort(run.polities.peak_cells.to_numpy(float))[::-1]
    for nm, s in (("peak", pk),
                  ("end", np.sort(np.bincount(
                      run.final["polity"][run.final["polity"] >= 0]))[::-1])):
        s = s[s > 0]
        m[f"states at rank 11+, {nm}"] = int(max(len(s) - 10, 0))
        t = s[10:100]
        if len(t) >= 20:
            rk = np.arange(11, 11 + len(t))
            m[f"rank-size slope, ranks 11-100, {nm}"] = float(
                np.polyfit(np.log(rk), np.log(t), 1)[0])
            m[f"10th / 100th or last, {nm}"] = float(s[9] / t[-1])
    return m


PEER_RATIO = 0.5        # weaker / stronger strength at declaration (C)


def peer_wars(run):
    """Durations of wars between peers: both sides 2+ cities and the
    weaker at least PEER_RATIO of the stronger's strength at declaration."""
    w = run.wars
    w = w[w.end.notna()]
    sa, sd = w.strength_att.astype(float), w.strength_dfn.astype(float)
    peer = ((w.cities_att >= 2) & (w.cities_dfn >= 2) &
            (np.minimum(sa, sd) >= PEER_RATIO * np.maximum(sa, sd)))
    y = w.loc[peer, "years"].to_numpy(float)
    m = {"peer wars (ended)": len(y), "peer wars, share of ended": share(peer)}
    if len(y) >= 5:
        m["peer war years, median"] = float(np.median(y))
        m["peer war years, mean"] = float(y.mean())
        m["peer war years, CV"] = float(y.std() / max(y.mean(), 1e-9))
        m["peer war years, over 20, share"] = float((y > 20).mean())
    return m


def waterside(run):
    """Cities at the last cityfood.csv year in thirds by urban size: the
    share on a coast, on a river, on either."""
    cf = run.cityfood
    cf = cf[cf.year == cf.year.max()].sort_values("urban")
    m = {}
    if len(cf) < 9:
        return m
    cut = np.linspace(0, len(cf), 4).astype(int)
    for k, nm in enumerate(("small", "middle", "large")):
        g = cf.iloc[cut[k]:cut[k + 1]]
        m[f"{nm} third: coastal"] = share(g.coastal > 0)
        m[f"{nm} third: river"] = share(g.river > 0)
        m[f"{nm} third: coast or river"] = share((g.coastal > 0) |
                                                 (g.river > 0))
    return m


def rule_spells(run):
    """history.npz: spells of a cell under one state (the same polity id
    in consecutive snapshots). Only spells that began and ended inside the
    record count; lengths in years."""
    H = run.history
    P, yr = H["polity"].T, H["year"]          # cells x snapshots
    dt = float(np.median(np.diff(yr)))
    ch = np.ones((P.shape[0], P.shape[1] + 1), bool)
    ch[:, 1:-1] = P[:, 1:] != P[:, :-1]
    i, j = np.nonzero(ch)                     # spell starts and ends
    out = []
    for c in np.unique(i):
        b = j[i == c]
        s, e = b[:-1], b[1:]
        ok = (P[c, s] >= 0) & (s > 0) & (e < P.shape[1])
        out.append((e - s)[ok])
    L = np.concatenate(out) * dt if out else np.array([])
    m = {"rule spells (completed)": len(L)}
    if len(L):
        m["rule spell years, median"] = float(np.median(L))
        m["rule spell years, p90"] = float(np.percentile(L, 90))
        m["rule spell over 500 yr, share"] = float((L > 500).mean())
    return m


def lineage_cities(run):
    """citytraits.csv, last year: the spread of commons traits between the
    cities of one lineage (3+ cities), against the spread between lineage
    means within a people (3+ lineages). SDs averaged over traits."""
    ct = run.citytraits
    ct = ct[ct.year == ct.year.max()]
    cols = [c for c in ct.columns if c.startswith("m_")]
    m = {}
    g = ct.groupby("lineage")
    big = g.size()[lambda s: s >= 3].index
    if len(big):
        within = ct[ct.lineage.isin(big)].groupby("lineage")[cols].std()
        m["lineages with 3+ cities"] = len(big)
        m["between cities of a lineage, sd (median)"] = float(
            within.mean(axis=1).median())
    means = g[cols].mean().join(g.people.first())
    pp = means.groupby("people")
    sd = pp[cols].std()[pp.size() >= 3]
    if len(sd):
        m["between lineages of a people, sd (median)"] = float(
            sd.mean(axis=1).median())
    return m


# counters (timeseries n_*) through which heads or cells change people
MEMBERSHIP = ["flip_to_ruler", "flip_other", "lineage_absorb",
              "lineage_absorb_whole", "lineage_fuse", "fusion",
              "settler_heads", "infiltrate_heads", "colony_displace",
              "refugees", "cq_settlers", "deported", "assimilated"]


def peoples(run):
    """Who lives where, and how it changes (WP10 stage A, records only):
    the largest people and its share of heads by millennium and every
    people's share at the end (timeseries pop_*); heads outside their
    cell's plurality people (minority_pop) by millennium; land whose
    plurality people changed from 2000 to the end, of land occupied at
    both (history.npz, by area); the membership counters summed by
    millennium; refugees (refugees.csv, `displacement`): the share that
    reached empty land, and cascades, the share of refugee heads whose
    destination itself sends refugees within 50 years."""
    ts = run.timeseries
    yr = ts["year"].to_numpy()
    keys = run.keys
    P = ts[[f"pop_{k}" for k in keys]].to_numpy()
    tot = np.maximum(P.sum(1), 1)
    end = _end(yr)
    m = {}
    for y in list(range(1000, end, 1000)) + [end]:
        i = min(int(np.searchsorted(yr, y - 5)), len(yr) - 1)
        j = int(np.argmax(P[i]))
        tag = "end" if y == end else f"yr {y}"
        m[f"largest people, {tag}"] = keys[j]
        m[f"largest share, {tag}"] = float(P[i, j] / tot[i])
        if "minority_pop" in ts:
            m[f"outside plurality, heads share, {tag}"] = float(
                ts["minority_pop"].iloc[i] / tot[i])
    for k, v in zip(keys, P[-1] / tot[-1]):
        m[f"{k} share, end"] = float(v)
    try:
        H = run.history
        hy, hpe = H["year"], H["people"]
        a, b = hpe[np.searchsorted(hy, 2000)], hpe[-1]
        occ = (a >= 0) & (b >= 0)
        area = run.W.area
        m["plurality changed 2000-end, land share"] = float(
            area[occ & (a != b)].sum() / max(area[occ].sum(), 1))
    except Missing:
        pass
    mil = (yr // 1000).astype(int)
    for c in MEMBERSHIP:
        if f"n_{c}" in ts:
            v = ts[f"n_{c}"].to_numpy()
            m[f"{c}, total"] = float(v.sum())
            for k in range(int(mil.max()) + 1):
                m[f"{c}, {k}000-{k + 1}000"] = float(v[mil == k].sum())
    try:
        R = run.refugees
    except Missing:
        return m
    if len(R):
        h = R["heads"].to_numpy()
        m["refugee heads, total"] = float(h.sum())
        m["refugees to empty land, share"] = float(
            h[R["dst_empty"].to_numpy() > 0].sum() / max(h.sum(), 1))
        src = R.groupby("src")["year"].apply(np.sort).to_dict()
        hit = np.array([s is not None and np.any((s > y) & (s <= y + 50))
                        for s, y in ((src.get(d), y) for d, y in
                                     zip(R["dst"], R["year"]))])
        m["refugee cascades (50 yr), heads share"] = float(
            h[hit].sum() / max(h.sum(), 1))
        for c, g in R.groupby("cause")["heads"]:
            m[f"refugees by {c}, share"] = float(g.sum() / max(h.sum(), 1))
    return m


SINGLE = [population, timeline, growth, volatility, landmass_volatility,
          city_hierarchy, city_lives, states, lifespans, contiguity, wars,
          sieges, war_time, food, food_ledger, deaths, growth_account,
          settlement, turnover,
          price,
          spacing, minor_states, peer_wars, waterside, rule_spells,
          lineage_cities, peoples]


def measure(run, only=None):
    """{function name: its dict} for every single-run measure the run's
    files allow; '_missing' lists what could not be read."""
    out, missing = {}, []
    for f in SINGLE:
        if only and f.__name__ not in only:
            continue
        try:
            out[f.__name__] = {k: clean(v) for k, v in f(run).items()}
        except Missing as e:
            missing.append(f"{f.__name__}: {e}")
    if missing:
        out["_missing"] = missing
    return out


def clean(v):
    """Python numbers for JSON; NaN as None."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return None if math.isnan(v) else float(v)
    return v


def write(run, path=None):
    m = measure(run)
    path = path or os.path.join(run.dir, "metrics.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(m, fh, indent=1)
    os.replace(tmp, path)
    return m


# ---- across runs ---------------------------------------------------------

def cross(runs):
    """For each pair of runs, on their final maps: the share of cells
    occupied in both held by the same people (chance: from each run's
    shares of peoples); the share of a's city sites (cells that ever held
    a city) within one cell of one of b's (chance: the share of land
    within one cell of b's sites); the correlation of log(1 + cell
    population). No chance level is given for the correlation: shuffling
    cells gives about 0, which says nothing about how much the land alone
    fixes."""
    out = []
    W = runs[0].W
    for x in range(len(runs)):
        for y in range(x + 1, len(runs)):
            a, b = runs[x], runs[y]
            Fa, Fb = a.final, b.final
            pa, pb = Fa["people"], Fb["people"]
            occ = (pa >= 0) & (pb >= 0)
            k = max(pa.max(), pb.max()) + 1
            na = np.bincount(pa[occ], minlength=k) / max(occ.sum(), 1)
            nb = np.bincount(pb[occ], minlength=k) / max(occ.sum(), 1)
            g = np.zeros((W.row.max() + 2, NX), bool)
            cb = Fb["city_peak"] > 0
            g[W.row[cb], W.col[cb]] = True
            gd = ndimage.binary_dilation(g, np.ones((3, 3)))
            ca = Fa["city_peak"] > 0
            la, lb = np.log1p(Fa["pop"]), np.log1p(Fb["pop"])
            out.append({"a": a.name, "b": b.name,
                        "same people": float((pa == pb)[occ].mean()),
                        "same people, chance": float(na @ nb),
                        "city sites within 1 cell": float(
                            gd[W.row[ca], W.col[ca]].mean()),
                        "city sites within 1 cell, chance": float(
                            gd[W.row, W.col].mean()),
                        "corr log(1 + pop)": float(np.corrcoef(la, lb)[0, 1])})
    return out
