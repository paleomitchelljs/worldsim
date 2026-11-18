"""
WP5 stage A (2026-11-18): the five diagnoses of states and wars, as
Markdown tables for docs/run-log.md. Reads a finished run only.

  1. where polities come from (polities.csv `origin`): count, life, ends
  2. siege odds by side and by the size of both states (sieges.csv)
  3. why wars are short: wars ending inside one tick
  4. states that lasted over 1,000 years against shorter 3+ city states
  5. contiguity of the 20 largest states at each millennium
     (history.npz), by land and within sailing range

Run:
  ~/.venvs/worldsim/bin/python war_diagnosis.py RUN [RUN ...] [--only 1,3]
"""
import argparse
import math
import os
import sys

import numpy as np
import pandas as pd

from wsim.runio import Run
from wsim.metrics import _components, _sea_join, why_kind
from wsim.params import SAIL_D0, SAIL_D1, DT
import landmasses

SIZES = [(1, 1, "1"), (2, 4, "2-4"), (5, 9, "5-9"), (10, 10 ** 6, "10+")]


def size_class(n):
    for lo, hi, lab in SIZES:
        if lo <= n <= hi:
            return lab
    return "0"


def md(df, floatfmt="{:.3g}"):
    """A DataFrame as a Markdown table."""
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |",
           "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for v in r:
            if isinstance(v, float):
                cells.append("" if math.isnan(v) else
                             str(int(v)) if v.is_integer() and abs(v) >= 1
                             else floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def shares(s, top=4):
    """The commonest values of s as 'value 0.42, ...'."""
    v = s.fillna("").replace("", "alive").value_counts(normalize=True)
    return ", ".join(f"{k} {x:.2f}" for k, x in v.head(top).items())


# ---- 1 -------------------------------------------------------------------

def origins(run):
    p = run.polities.copy()
    p["origin"] = p.origin.fillna("").replace("", "(before branch)")
    rows = []
    for o, g in p.groupby("origin"):
        e = g[g.ended.notna()]
        rows.append(dict(
            origin=o, n=len(g), share=len(g) / len(p),
            **{"median life, ended (yr)": float(e.years.median())
               if len(e) else np.nan},
            **{"alive at end": float(g.ended.isna().mean())},
            **{"ever 2+ cities": float((g.peak_cities >= 2).mean())},
            **{"ever 3+ cities": float((g.peak_cities >= 3).mean())},
            ends=shares(g.end_reason)))
    return pd.DataFrame(rows).sort_values("n", ascending=False)


# ---- 2 -------------------------------------------------------------------

def siege_sizes(run):
    s = run.sieges
    if "cities_besieger" not in s:
        return None
    s = s.dropna(subset=["cities_besieger", "cities_holder"]).copy()
    s["besieger"] = s.cities_besieger.astype(int).map(size_class)
    s["holder"] = s.cities_holder.astype(int).map(size_class)
    rows = []
    order = [lab for _, _, lab in SIZES]
    for side in ("att", "dfn"):
        for b in order:
            for h in order:
                g = s[(s.side == side) & (s.besieger == b) & (s.holder == h)]
                if len(g) < 20:
                    continue
                rows.append({"side": side, "besieger cities": b,
                             "holder cities": h, "n": len(g),
                             "share of side": len(g) / (s.side == side).sum(),
                             "median odds": float(g.odds.median()),
                             "odds < 0.1": float((g.odds < 0.1).mean()),
                             "taken": float(g.taken.mean())})
    return pd.DataFrame(rows)


# ---- 3 -------------------------------------------------------------------

def short_wars(run):
    w = run.wars
    w = w[w.why.fillna("") != "ongoing"].copy()
    w["kind"] = w.why.fillna("").map(why_kind)
    w["dfn size"] = w.cities_dfn.map(size_class)
    w["att size"] = w.cities_att.map(size_class)
    one = w[w.years == 0]
    s = run.sieges
    first = s[s.side == "att"].groupby("war").odds.first()
    lines = [f"Ended wars: {len(w)}; ending inside one tick: {len(one)} "
             f"({len(one) / len(w):.2f})."]
    t = pd.crosstab(one["dfn size"], one.kind, margins=True,
                    margins_name="all")
    t = t.reindex([lab for _, _, lab in SIZES if lab in t.index] + ["all"])
    t = t.reset_index().rename(columns={"dfn size": "defender cities"})
    lines.append("\nWars ending inside one tick, by the defender's size "
                 "and how they ended (counts):\n")
    lines.append(md(t, "{:.0f}"))
    sg = one.sieges.clip(upper=3).map({0: "0", 1: "1", 2: "2", 3: "3+"})
    t2 = pd.crosstab(sg, one.kind).reset_index().rename(
        columns={"sieges": "sieges"})
    lines.append("\nThe same wars by sieges fought:\n")
    lines.append(md(t2, "{:.0f}"))
    fell1 = one[(one.cities_dfn == 1) & (one.sieges == 1) &
                (one.kind == "defender fell")]
    lines.append(
        f"\nA one-city defender falling at the first siege: {len(fell1)} "
        f"({len(fell1) / len(one):.2f} of one-tick wars, "
        f"{len(fell1) / len(w):.2f} of all ended wars). Attacker's size in "
        f"those: " + ", ".join(f"{k} {v:.2f}" for k, v in fell1[
            "att size"].value_counts(normalize=True).items()) +
        f". Median odds of their siege: "
        f"{first.reindex(fell1.id).median():.3f}; median odds of the "
        f"first siege in wars that lasted past one tick: "
        f"{first.reindex(w[w.years > 0].id).median():.3f}.")
    nos = one[one.sieges == 0]
    lines.append(f"\nOne-tick wars with no siege: {len(nos)}; how they "
                 f"ended: {shares(nos.kind, 6)}.")
    return "\n".join(lines)


# ---- 4 -------------------------------------------------------------------

def long_states(run, min_years=1000):
    p = run.polities.copy()
    W = run.W
    p["landmass"] = [landmasses.code(W.landmass[int(c)])
                     for c in p.capital_cell]
    lm_km2 = {landmasses.code(i): a for i, a in
              enumerate(W.landmass_area)}
    w = run.wars
    nwar = pd.concat([w.att, w.dfn]).value_counts()
    natt = w.att.value_counts()
    rv = run.revolts.state.value_counts() if run.has("revolts") else \
        pd.Series(dtype=int)
    rpath = os.path.join(run.dir, "rulers.csv")
    dyn = pd.read_csv(rpath).groupby("state").dynasty.nunique() \
        if os.path.exists(rpath) else pd.Series(dtype=int)
    p["wars"] = p.id.map(nwar).fillna(0)
    p["wars started"] = p.id.map(natt).fillna(0)
    p["revolts"] = p.id.map(rv).fillna(0)
    p["dynasties"] = p.id.map(dyn).fillna(0)
    c = p.years / 100
    for k in ("wars", "revolts", "dynasties"):
        p[f"{k}/century"] = p[k] / c.clip(lower=0.05)
    nb = "nb_land_mean" in p
    if nb:
        p["no neighbour, share of life"] = p.nb_none_years / \
            p.years.clip(lower=DT)
    long = p[p.years > min_years]
    mid = p[(p.years <= min_years) & (p.years >= 100) &
            (p.peak_cities >= 3)]
    cols = ["peak_cities", "peak_km2", "wars/century", "revolts/century",
            "dynasties/century"]
    if nb:
        cols += ["nb_land_mean", "nb_sea_mean", "nb_max",
                 "no neighbour, share of life"]
    ls, lb = long[long.peak_cities <= 2], long[long.peak_cities >= 3]
    g = pd.DataFrame({
        f"> {min_years} yr, peak 1-2 cities (n {len(ls)})":
            ls[cols].median(),
        f"> {min_years} yr, peak 3+ cities (n {len(lb)})": lb[cols].median(),
        f"100-{min_years} yr, peak 3+ cities (n {len(mid)})":
            mid[cols].median(),
    }).T.reset_index().rename(columns={"index": "group (medians)"})
    lines = [md(g)]
    lm = long.landmass.value_counts()
    lmm = mid.landmass.value_counts(normalize=True)
    lines.append("\nCapital landmass of the long-lived states (count; "
                 "share among 100-1,000 yr 3+ city states; landmass "
                 "area M km2): " + ", ".join(
                     f"{k} {v} ({lmm.get(k, 0):.2f}; "
                     f"{lm_km2.get(k, 0) / 1e6:.2f})"
                     for k, v in lm.items()))
    lines.append(f"\nLong-lived states, share of all polities: "
                 f"{len(long) / len(p):.3f}; how they ended: "
                 f"{shares(long.end_reason, 6)}. Dynasties are counted "
                 f"only in states of 3+ cities (succession runs only "
                 f"there).")
    lines.append("\nThe 25 longest:\n")
    show = ["id", "people", "founded", "ended", "years", "origin",
            "end_reason", "landmass", "peak_cities", "peak_km2", "wars",
            "revolts", "dynasties"]
    if nb:
        show += ["nb_land_mean", "nb_sea_mean", "nb_none_years"]
    t = long.sort_values("years", ascending=False)[show].head(25).copy()
    t["ended"] = t.ended.map(lambda v: "" if pd.isna(v) else int(v))
    for k in ("peak_km2", "wars", "revolts", "dynasties"):
        t[k] = t[k].fillna(0).astype(int)
    t["origin"] = t.origin.fillna("")
    t["end_reason"] = t.end_reason.fillna("")
    lines.append(md(t))
    return "\n".join(lines)


# ---- 5 -------------------------------------------------------------------

def contiguity(run, top=20):
    H, F = run.history, run.final
    P = run.polities.set_index("id")
    sail = run.lineages.set_index("id")["sail"]
    W = run.W
    lon, lat = np.radians(W.lon), np.radians(W.lat)
    xyz = np.c_[np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon),
                np.sin(lat)]
    rows = []
    for y in range(1000, int(H["year"].max()) + 1, 1000):
        i = int(np.argmin(np.abs(H["year"] - y)))
        pol = H["polity"][i]
        ids, n = np.unique(pol[pol >= 0], return_counts=True)
        keep = n >= 10
        ids, n = ids[keep], n[keep]
        sel = ids[np.argsort(-n, kind="stable")][:top]
        if not len(sel):
            continue
        land, sea, big_l, big_s, cells = [], [], [], [], []
        for pid in sel:
            c = np.nonzero(pol == pid)[0]
            lab = _components(F["row"][c], F["col"][c])
            sz = np.bincount(lab)
            lin = int(str(P.loc[pid, "lineage"]).lstrip("L")) \
                if pid in P.index else -1
            s = float(sail.get(lin, 0.0))
            reach = SAIL_D0 + SAIL_D1 * max(s, 0) ** 1.5
            g = np.bincount(_sea_join(lab, xyz[c], reach))
            land.append(len(sz))
            sea.append(len(g))
            big_l.append(sz.max() / len(c))
            big_s.append(g.max() / len(c))
            cells.append(len(c))
        land, sea = np.array(land), np.array(sea)
        extra = (land - 1).sum()
        rows.append({
            "year": int(H["year"][i]), "states": len(sel),
            "cells, median": float(np.median(cells)),
            "land pieces, median": float(np.median(land)),
            "land pieces, max": int(land.max()),
            "one piece": float((land == 1).mean()),
            "largest piece, median share": float(np.median(big_l)),
            "sea groups, median": float(np.median(sea)),
            "one sea group": float((sea == 1).mean()),
            "largest group, median share": float(np.median(big_s)),
            "extra pieces joined by sea": float((land - sea).sum() / extra)
            if extra else np.nan})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--only", default="1,2,3,4,5")
    a = ap.parse_args()
    only = set(a.only.split(","))
    for name in a.runs:
        run = Run(name)
        print(f"\n## {os.path.basename(run.dir)}\n")
        if "1" in only:
            print("### 1. Where polities come from\n")
            print(md(origins(run)))
        if "2" in only:
            print("\n### 2. Siege odds by side and size\n")
            t = siege_sizes(run)
            print("(no size columns in sieges.csv)" if t is None else md(t))
        if "3" in only:
            print("\n### 3. Why wars are short\n")
            print(short_wars(run))
        if "4" in only:
            print("\n### 4. Long-lived states\n")
            print(long_states(run))
        if "5" in only:
            print("\n### 5. Contiguity of the 20 largest states\n")
            print(md(contiguity(run)))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
