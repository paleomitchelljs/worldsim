"""
Report on a group of landmasses for one or more runs: peoples, cities,
states, wars, relations, culture, revolts, successions, posts, colonies.

Run:
  ~/.venvs/worldsim/bin/python landmass_report.py runs/batch1_seed10[1-7] --lm W
  ~/.venvs/worldsim/bin/python landmass_report.py runs/X --lm W1,W2
Codes as in landmasses.py (docs/landmass_key.png).
"""
import argparse
import collections
import csv
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import landmasses as LM  # noqa: E402

PID = re.compile(r"P(\d+)\((\w+)\)")
LOC = re.compile(r"([-+]\d+\.?\d*),([-+]\d+\.?\d*)")
TRAITS = ["tolerance", "violence", "trade", "seafaring", "conformity",
          "separation"]


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


class Geo:
    def __init__(self):
        import worldsim
        self.W = worldsim.World()
        self.lm = self.W.landmass

    def at(self, lon, lat):
        W = self.W
        return int(self.lm[np.argmin((W.lon - lon) ** 2 + (W.lat - lat) ** 2)])


def report(run, keep, G, years=(1000, 2000, 4000, 6000, 8000)):
    lm = G.lm
    meta = json.load(open(os.path.join(run, "run.json")))
    keys = [p["key"] for p in meta["peoples"]]
    F = np.load(os.path.join(run, "final_state.npz"))
    pop, ppl, pol, lin = F["pop"], F["people"], F["polity"], F["lineage"]
    inW = np.isin(lm, list(keep))
    out = collections.OrderedDict()
    out["run"] = os.path.basename(run)

    # peoples: final population by landmass
    tab = {}
    for l in sorted(keep, key=lambda l: LM.code(l)):
        m = lm == l
        tot = pop[m].sum()
        d = {keys[k]: pop[m & (ppl == k)].sum() / 1e6 for k in range(len(keys))
             if pop[m & (ppl == k)].sum() > 0}
        tab[LM.code(l)] = (tot / 1e6, dict(sorted(d.items(), key=lambda x: -x[1])))
    out["pop"] = tab

    # cities by people over time
    C = rows(os.path.join(run, "cities.csv"))
    for c in C:
        c["lm"] = int(lm[int(c["cell"])])
    Cw = [c for c in C if c["lm"] in keep]
    ct = {}
    for y in years:
        live = [c for c in Cw if int(c["founded"]) <= y and
                (c["ended"] == "" or int(c["ended"]) > y)]
        ct[y] = collections.Counter(c["people"] for c in live)
    out["cities"] = ct
    first = {}
    for c in sorted(Cw, key=lambda c: int(c["founded"])):
        first.setdefault(LM.code(c["lm"]) + ":" + c["people"], int(c["founded"]))
    out["first_city"] = first

    # states
    P = {int(r["id"]): r for r in rows(os.path.join(run, "polities.csv"))}
    for r in P.values():
        r["lm"] = G.at(float(r["capital_lon"]), float(r["capital_lat"]))
    Pw = {i: r for i, r in P.items() if r["lm"] in keep}
    live = np.unique(pol[inW & (pol >= 0)])
    span = []
    for i in np.unique(pol[pol >= 0]):
        ls = set(np.unique(lm[pol == i]))
        if ls & keep and len(ls) > 1:
            span.append((i, P[i]["people"], sorted(LM.code(x) for x in ls),
                         int((pol == i).sum())))
    big = sorted(Pw.values(), key=lambda r: -int(r["peak_cities"]))[:8]
    ended = [r for r in Pw.values() if r["ended"] and int(r["peak_cities"]) >= 3]
    out["states"] = dict(
        ever=len(Pw), ever3=sum(int(r["peak_cities"]) >= 3 for r in Pw.values()),
        live=len(live),
        live_cells_top=sorted(((int((pol == i).sum()), int(i), P[int(i)]["people"],
                                P[int(i)]["peoples_ruled"]) for i in live),
                              reverse=True)[:5],
        span=sorted(span, key=lambda x: -x[3])[:6],
        median_life3=float(np.median([int(r["years"]) for r in ended])) if ended else None,
        biggest=[(int(r["id"]), r["people"], int(r["peak_cities"]),
                  int(r["peak_year"] or 0), int(r["founded"]),
                  r["ended"] or "-", r["peoples_ruled"],
                  LM.code(r["lm"])) for r in big])

    # wars
    Wr = [r for r in rows(os.path.join(run, "wars.csv"))
          if int(r["landmass_att"]) in keep or int(r["landmass_dfn"]) in keep]
    out["wars"] = dict(
        n=len(Wr),
        inter_people=sum(r["people_att"] != r["people_dfn"] for r in Wr),
        cross_lm=sum(r["landmass_att"] != r["landmass_dfn"] for r in Wr),
        from_outside=sum(int(r["landmass_att"]) not in keep for r in Wr),
        pairs=collections.Counter(
            tuple(sorted((r["people_att"], r["people_dfn"]))) for r in Wr
            if r["people_att"] != r["people_dfn"]).most_common(6),
        why=collections.Counter(re.sub(r" \(.*", "", r["why"]) for r in Wr).most_common(8),
        captures=sum(int(r["captures"] or 0) for r in Wr),
        recaptures=sum(int(r["recaptures"] or 0) for r in Wr),
        helped=sum(bool(r["helpers"]) for r in Wr),
        per_kyr=[sum(k * 1000 <= int(r["start"]) < (k + 1) * 1000 for r in Wr)
                 for k in range(8)])

    # relations at the last frame and over time
    R = rows(os.path.join(run, "relations.csv"))
    byy = collections.defaultdict(list)
    for r in R:
        if int(r["landmass_a"]) in keep and int(r["landmass_b"]) in keep:
            byy[int(r["year"])].append(r)
    rel = {}
    for y in [y for y in sorted(byy) if y in years or y == max(byy, default=0)]:
        g = byy[y]
        cross = [r for r in g if r["people_a"] != r["people_b"]]
        en = lambda rr: float(np.mean([max(float(r["enmity_ab"]), float(r["enmity_ba"]))
                                       for r in rr])) if rr else float("nan")
        rel[y] = dict(pairs=len(g), cross=len(cross),
                      allied=sum(r["allied"] == "1" for r in g),
                      allied_cross=sum(r["allied"] == "1" for r in cross),
                      war=sum(r["war"] == "1" for r in g),
                      war_cross=sum(r["war"] == "1" for r in cross),
                      enmity=en(g), enmity_cross=en(cross),
                      tie=float(np.mean([float(r["tie"]) for r in g])) if g else float("nan"),
                      tie_cross=float(np.mean([float(r["tie"]) for r in cross])) if cross else float("nan"))
    out["relations"] = rel

    # culture of living lineages on the landmasses, population-weighted
    L = {int(r["id"]): r for r in rows(os.path.join(run, "lineages.csv"))}
    m = inW & (lin >= 0) & (pop > 0)
    w = collections.defaultdict(lambda: collections.defaultdict(float))
    for li, p_ in zip(lin[m], pop[m]):
        r = L.get(int(li))
        if r is None:
            continue
        w[r["people"]]["_pop"] += p_
        for t in TRAITS:
            w[r["people"]][t] += p_ * float(r[t])
    cul = {}
    for k, d in w.items():
        cul[k] = {t: d[t] / d["_pop"] for t in TRAITS}
        cul[k]["pop"] = d["_pop"] / 1e6
    out["culture"] = dict(sorted(cul.items(), key=lambda x: -x[1]["pop"]))
    hows = collections.Counter(L[int(li)]["how"] for li in np.unique(lin[m])
                               if int(li) in L)
    out["lineage_origin"] = dict(hows)

    # revolts, successions, posts, unions, voyages/landings
    Rv = [r for r in rows(os.path.join(run, "revolts.csv")) if int(r["landmass"]) in keep]
    out["revolts"] = dict(n=len(Rv), kinds=dict(collections.Counter(r["kind"] for r in Rv)),
                          per_kyr=[sum(k * 1000 <= int(r["year"]) < (k + 1) * 1000 for r in Rv)
                                   for k in range(8)])
    ev = collections.Counter()
    posts = collections.Counter()
    landings = []
    for line in open(os.path.join(run, "events.txt")):
        mm = re.match(r"\s*(\d+)\s+(\w+)\s+(.*)", line)
        if not mm:
            continue
        y, k, t = int(mm.group(1)), mm.group(2), mm.group(3)
        ids = [int(x) for x, _ in PID.findall(t)]
        if k == "trade" and "trading post" in t:
            loc = LOC.search(t)
            if loc and G.at(float(loc.group(1)), float(loc.group(2))) in keep:
                host = PID.findall(t)[-1][1]
                posts[(PID.findall(t)[0][1], host)] += 1
        elif k == "succession" and ids and ids[0] in Pw:
            ev["partition" if "partition" in t else "succession"] += 1
        elif k == "union" and ids and ids[0] in Pw:
            ev["union_crowns" if "crown" in t else "union_treaty"] += 1
        elif k in ("voyage", "contact"):
            loc = LOC.search(t)
            if loc and G.at(float(loc.group(1)), float(loc.group(2))) in keep:
                landings.append(f"{y} {k} {t[:110]}")
    out["succession"] = dict(ev)
    out["posts"] = posts.most_common(8)
    out["voyages"] = landings[:10]
    return out


def fmt(o, keys_order=None):
    p = []
    p.append(f"### {o['run']}")
    p.append("Population at 8000 (M), by people:")
    for c, (tot, d) in o["pop"].items():
        p.append(f"  {c:3s} {tot:6.2f}  " + ", ".join(f"{k} {v:.2f}" for k, v in d.items()))
    p.append("Cities by people:")
    for y, c in o["cities"].items():
        p.append(f"  {y:5d} n={sum(c.values()):4d}  " +
                 ", ".join(f"{k} {v}" for k, v in c.most_common()))
    fc = collections.defaultdict(list)
    for lk, y in o["first_city"].items():
        l, k = lk.split(":")
        fc[l].append(f"{k} {y}")
    p.append("First city per people: " + "; ".join(f"{l}: " + ", ".join(v)
                                                   for l, v in sorted(fc.items())))
    s = o["states"]
    p.append(f"States: {s['ever']} ever ({s['ever3']} with 3+ cities), {s['live']} "
             f"at end; median life of ended 3+ city states {s['median_life3']}")
    p.append("  biggest ever (id, people, peak cities, peak yr, founded, ended, ruled, capital):")
    for b in s["biggest"]:
        p.append("   " + str(b))
    p.append("  biggest at end (cells, id, people, ruled): " + str(s["live_cells_top"]))
    p.append("  spanning landmasses at end: " + str(s["span"]))
    w = o["wars"]
    p.append(f"Wars: {w['n']} (inter-people {w['inter_people']}, cross-landmass "
             f"{w['cross_lm']}, attacker from outside {w['from_outside']}); per kyr "
             f"{w['per_kyr']}; captures {w['captures']}, recaptures {w['recaptures']}, "
             f"with allies {w['helped']}")
    p.append(f"  inter-people pairs {w['pairs']}")
    p.append(f"  ends {w['why']}")
    p.append("Relations (pairs within group): year pairs cross | allied (cross) | "
             "war (cross) | enmity all/cross | tie all/cross")
    for y, r in o["relations"].items():
        p.append(f"  {y:5d} {r['pairs']:4d} {r['cross']:4d} | {r['allied']:3d} "
                 f"({r['allied_cross']:3d}) | {r['war']:2d} ({r['war_cross']:2d}) | "
                 f"{r['enmity']:.2f}/{r['enmity_cross']:.2f} | "
                 f"{r['tie']:.2f}/{r['tie_cross']:.2f}")
    p.append("Culture at end (pop-weighted): people pop " + " ".join(t[:4] for t in TRAITS))
    for k, d in o["culture"].items():
        p.append(f"  {k} {d['pop']:6.2f} " + " ".join(f"{d[t]:.2f}" for t in TRAITS))
    p.append(f"Living lineages by origin: {o['lineage_origin']}")
    p.append(f"Revolts: {o['revolts']}")
    p.append(f"Successions: {o['succession']}")
    p.append(f"Trading posts in group (planter, host): {o['posts']}")
    p.append("Voyages/contacts: " + " | ".join(o["voyages"]))
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--lm", default="W")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    keep = LM.ids(a.lm)
    G = Geo()
    allo = []
    for r in a.runs:
        o = report(r, keep, G)
        allo.append(o)
        print(fmt(o))
        print()
    if a.json:
        json.dump(allo, open(a.json, "w"), default=str)


if __name__ == "__main__":
    main()
