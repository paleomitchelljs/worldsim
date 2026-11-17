"""
Significant-event timeline for one run, filtered by landmass or people.

Reads a run's events.txt and polities.csv, and wars.csv, sieges.csv and
revolts.csv where the run wrote them. Each candidate event gets an
importance score (food-equivalents at stake, how unlikely the outcome
was, whether a state ended), and the top N are printed in order of year.

Run:
  ~/.venvs/worldsim/bin/python timeline.py runs/reg4_seed105 --landmass W1,W2
  ~/.venvs/worldsim/bin/python timeline.py runs/X --people Elf --top 60
  ~/.venvs/worldsim/bin/python timeline.py runs/X --list-landmasses
"""
import argparse
import collections
import csv
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EV = re.compile(r"\s*(\d+)\s+(\w+)\s+(.*)")
PID = re.compile(r"P(\d+)\((\w+)\)")
LOC = re.compile(r"([-+]\d+\.?\d*),([-+]\d+\.?\d*)")


def rows(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return list(csv.DictReader(fh))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--landmass", default="",
                    help="landmass codes or ids, comma-separated, e.g. W or W1,N1 (docs/landmass_key.png)")
    ap.add_argument("--people", default="", help="people keys, e.g. Elf,Hum")
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--min-cities", type=int, default=8,
                    help="states this large at peak count as major")
    ap.add_argument("--list-landmasses", action="store_true")
    a = ap.parse_args()

    import sys
    sys.path.insert(0, HERE)
    import worldsim
    W = worldsim.World()
    lm = W.landmass
    if a.list_landmasses:
        for l in np.argsort(-W.landmass_area)[:20]:
            m = lm == l
            print(f"{l:3d}  {W.landmass_area[l] / 1e6:5.1f}M km2  centre "
                  f"{W.lon[m].mean():+6.1f},{W.lat[m].mean():+6.1f}")
        return
    import landmasses
    LMS = landmasses.ids(a.landmass)
    PPL = {x for x in a.people.split(",") if x}

    def lm_at(lon, lat):
        return int(lm[np.argmin((W.lon - lon) ** 2 + (W.lat - lat) ** 2)])

    P = {}
    for r in rows(os.path.join(a.run, "polities.csv")):
        P[int(r["id"])] = dict(
            people=r["people"], pc=int(r["peak_cities"]),
            pp=float(r["peak_pop"] or 0), py=r["peak_year"],
            f=int(float(r["founded"])), e=r["ended"], ruled=r["peoples_ruled"],
            lm=lm_at(float(r["capital_lon"]), float(r["capital_lat"])))

    def keep_state(i):
        p = P.get(i)
        if p is None:
            return False
        return (not LMS or p["lm"] in LMS) and (not PPL or p["people"] in PPL)

    def keep_place(lon, lat, peoples=()):
        ok_l = not LMS or lm_at(lon, lat) in LMS
        ok_p = not PPL or bool(PPL & set(peoples))
        return ok_l and ok_p

    major = lambda i: i in P and P[i]["pc"] >= a.min_cities
    out = []          # (score, year, kind, text)

    # rises and falls of major states
    for i, p in P.items():
        if major(i) and keep_state(i):
            out.append((p["pp"], p["f"], "rise",
                        f"P{i}({p['people']}) founded; peak {p['pc']} cities "
                        f"in {p['py']}, ruling {p['ruled']}"))
    for line in open(os.path.join(a.run, "events.txt")):
        m = EV.match(line)
        if not m:
            continue
        y, k, t = int(m.group(1)), m.group(2), m.group(3)
        ids = [int(x) for x, _ in PID.findall(t)]
        loc = LOC.search(t)
        if k == "fall" and ids and major(ids[0]) and keep_state(ids[0]):
            out.append((1.5 * P[ids[0]]["pp"], y, k, t))
        elif k in ("fusion", "union") and len(ids) > 1 and \
                any(major(i) and keep_state(i) for i in ids):
            out.append((0.5 * max(P[i]["pp"] for i in ids if i in P), y, k, t))
        elif k == "succession" and ids and major(ids[0]) and keep_state(ids[0]):
            out.append((0.3 * P[ids[0]]["pp"], y, k, t))
        elif k in ("plague", "drought") and loc:
            n = re.search(r"~?([\d.]+)M (dead|people)", t)
            if keep_place(float(loc.group(1)), float(loc.group(2)),
                          [x for _, x in PID.findall(t)] or PPL):
                out.append(((float(n.group(1)) if n else 1) * 1e6, y, k, t))
        elif k in ("voyage", "dragon", "contact", "tech", "trade") and \
                (loc is None or keep_place(float(loc.group(1)),
                                           float(loc.group(2)), PPL)) and \
                (not PPL or any(f"({x})" in t or f" {x} " in t + " "
                                for x in PPL)):
            out.append((2e5, y, k, t))

    # wars that moved people or ended a state
    for r in rows(os.path.join(a.run, "wars.csv")):
        att, dfn = int(r["att"]), int(r["dfn"])
        if not (keep_state(att) or keep_state(dfn)):
            continue
        moved = float(r["moved"] or 0)
        fell = "fell" in r["why"] or "ended" in r["why"]
        if moved <= 0 and not fell:
            continue
        sc = moved + (P[dfn]["pp"] if fell and dfn in P else 0)
        out.append((sc, int(r["start"]), "war",
                    f"war {r['id']}: P{att}({r['people_att']}) against "
                    f"P{dfn}({r['people_dfn']}), {r['start']}-{r['end']}; "
                    f"goal {r['goal'] or 'none'}, {r['captures']} cities "
                    f"taken in {r['sieges']} sieges, "
                    f"{float(moved) / 1e6:.2f}M changed hands; ends: {r['why']}"
                    + (f"; helped by {r['helpers']}" if r["helpers"] else "")))

    # pivotal sieges: a big city or a capital taken against the odds
    for r in rows(os.path.join(a.run, "sieges.csv")):
        if r["taken"] != "1":
            continue
        att, dfn = int(r["besieger"]), int(r["holder"])
        if not (keep_state(att) or keep_state(dfn)):
            continue
        odds, fe = float(r["odds"]), float(r["city_fe"])
        sc = fe * (1 - odds) * (2 if r["capital"] == "1" else 1)
        if odds < 0.35 or r["capital"] == "1":
            c = int(r["city"])
            out.append((sc, int(r["year"]), "siege",
                        f"P{att} takes {'the capital' if r['capital'] == '1' else 'a city'}"
                        f" of P{dfn} at {W.lon[c]:+.1f},{W.lat[c]:+.1f} "
                        f"({fe / 1e3:.0f}k) at odds {odds:.2f} (war {r['war']})"))

    # breakups: many revolts from one state in one tick
    rv = collections.defaultdict(list)
    for r in rows(os.path.join(a.run, "revolts.csv")):
        rv[(int(r["state"]), int(r["year"]))].append(r)
    for (pid, y), g in rv.items():
        if not keep_state(pid):
            continue
        n = sum(int(r["cities_taken"]) for r in g)
        if len(g) >= 3:
            kinds = collections.Counter(r["kind"] for r in g)
            out.append((P[pid]["pp"] * min(1.0, n / max(P[pid]["pc"], 1)) * 2,
                        y, "breakup",
                        f"P{pid}({P[pid]['people']}) breaks up: {len(g)} "
                        f"revolts take {n} cities, {g[0]['cities_left']} left ("
                        + ", ".join(f"{v} {k}" for k, v in kinds.items()) + ")"))

    out.sort(key=lambda x: -x[0])
    keep = sorted(out[:a.top], key=lambda x: x[1])
    for sc, y, k, t in keep:
        print(f"{y:5d}  {k:9s} {t}")
    print(f"\n{len(keep)} of {len(out)} candidate events shown")


if __name__ == "__main__":
    main()
