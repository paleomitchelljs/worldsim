import csv
import itertools
import os
import sys

import numpy as np

SIM = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, SIM)
R = os.path.join(SIM, "runs")
from wsim.geo import World  # noqa: E402

W = World()
print("land cells", W.N, "land Mkm2", round(W.area.sum() / 1e6, 1))


def ts(run):
    with open(os.path.join(R, run, "timeseries.csv")) as fh:
        return list(csv.DictReader(fh))


def f(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return np.nan


run = "al_seed103"
T = ts(run)
yr = np.array([f(r["year"]) for r in T])
pk = [k for k in T[0] if k.startswith("pop_")]
pop = np.array([sum(f(r[k]) for k in pk) for r in T])
print("\n== A. trajectory", run)
for y in range(1000, 8001, 1000):
    i = np.searchsorted(yr, y - 5)
    j = np.searchsorted(yr, y - 1000) if y > 1000 else 0
    g = np.log(pop[i] / max(pop[j], 1)) / max(yr[i] - yr[j], 1) * 100
    seg = slice(j, i + 1)
    print(f"yr {y}: pop {pop[i]/1e6:7.1f}M  growth {g:6.3f}%/yr  cities "
          f"{sum(f(T[i][k]) for k in T[0] if k.startswith('cities_') and not k.startswith('cities_per') and k not in ('cities_low_urban','cities_mixed_share')):5.0f}"
          f"  states {f(T[i]['n_polities']):5.0f}  at_war "
          f"{np.nanmean([f(r['at_war_share']) for r in T[seg]]):.3f}  wars_now {f(T[i]['wars']):4.0f}"
          f"  largest Mkm2 {f(T[i]['largest_polity_Mkm2']):.2f}  urban {f(T[i].get('urban_share')):.3f}"
          f"  herd {f(T[i]['herd_share']):.3f}")
# detrended volatility of world population after year 3000
m = yr >= 3000
lp = np.log(pop[m])
k = 40                                   # 200-yr moving mean
sm = np.convolve(lp, np.ones(k) / k, "same")
res = (lp - sm)[k:-k]
print("pop residual sd around 200-yr mean (log):", round(float(res.std()), 4),
      " largest 100-yr drop:", round(float(min(lp[20:] - lp[:-20])), 3))
# per-people shares at the end
tot = pop[-1]
print("people shares end:", {k[4:]: round(f(T[-1][k]) / tot, 3) for k in pk})
for y in (2000, 4000, 6000):
    i = np.searchsorted(yr, y)
    print(" shares yr", y, {k[4:]: round(f(T[i][k]) / pop[i], 3) for k in pk})

# wars
with open(os.path.join(R, run, "wars.csv")) as fh:
    Wr = list(csv.DictReader(fh))
dur = np.array([f(r["years"]) for r in Wr])
dur = dur[np.isfinite(dur)]
print("\nwars", len(Wr), "duration: share 0y", round(float((dur == 0).mean()), 3),
      "<=5y", round(float((dur <= 5).mean()), 3), "median", np.median(dur),
      "p90", np.percentile(dur, 90), "max", dur.max())
sg = np.array([f(r["sieges"]) for r in Wr])
print("sieges per war: mean", round(float(np.nanmean(sg)), 2), "share 0-1", round(float((sg <= 1).mean()), 3))
big = [r for r in Wr if f(r["cities_att"]) >= 5 and f(r["cities_dfn"]) >= 5]
print("wars between two 5+ city states:", len(big), "of", len(Wr),
      " why:", {w: sum(r["why"] == w for r in big) for w in set(r["why"] for r in big)})

# polities
with open(os.path.join(R, run, "polities.csv")) as fh:
    P = list(csv.DictReader(fh))
one = sum(f(r["peak_cities"]) <= 1 for r in P)
print("polities", len(P), "never above 1 city:", one, round(one / len(P), 3))
life1 = np.array([f(r["years"]) for r in P if f(r["peak_cities"]) <= 1 and r["ended"] not in ("", "None")])
print("one-city state lifespans: median", np.median(life1), "mean", round(float(life1.mean())))
multi = sum(len(r["peoples_ruled"].split()) > 1 for r in P if f(r["peak_cities"]) >= 3)
n3 = sum(f(r["peak_cities"]) >= 3 for r in P)
print("3+ city states ruling >1 people:", multi, "of", n3)

# history: turnover of peoples
hp = os.path.join(R, run, "history.npz")
H = np.load(hp)
hy, hpe, hpol = H["year"], H["people"], H["polity"]
print("\n== turnover of people per cell (history.npz)", run)
for y0 in range(1000, 7501, 500):
    i, j = np.searchsorted(hy, y0), np.searchsorted(hy, y0 + 500)
    if j >= len(hy):
        break
    a, b = hpe[i], hpe[j]
    occ = (a >= 0) & (b >= 0)
    ch = (a != b) & occ
    pa, pb = hpol[i], hpol[j]
    print(f"{y0}-{y0+500}: occupied both {occ.sum():6d}  people changed {ch.sum()/max(occ.sum(),1):.4f}"
          f"  in-state share {((pb>=0)&(b>=0)).sum()/max((b>=0).sum(),1):.3f}"
          f"  emptied {((a>=0)&(b<0)).sum()/max((a>=0).sum(),1):.4f}")

# B. cross-seed agreement
print("\n== B. cross-seed agreement of the final map")
runs = ["tx_seed101", "tx_seed103", "tx_seed104", "al_seed101", "al_seed103", "ub_seed101"]
F = {}
for r in runs:
    try:
        F[r] = np.load(os.path.join(R, r, "final_state.npz"))
    except Exception as e:  # noqa: BLE001
        print("skip", r, e)
for a, b in itertools.combinations(F, 2):
    pa, pb = F[a]["people"], F[b]["people"]
    occ = (pa >= 0) & (pb >= 0)
    same = (pa == pb) & occ
    # chance agreement given marginal shares
    na = np.bincount(pa[occ], minlength=12) / occ.sum()
    nb = np.bincount(pb[occ], minlength=12) / occ.sum()
    ca = F[a]["city_peak"] > 0
    cb = F[b]["city_peak"] > 0
    # city sites ever used: share of a's within 1 cell of b's
    g = np.zeros((360, 720), bool)
    g[W.row[cb], W.col[cb]] = True
    from scipy import ndimage
    gd = ndimage.binary_dilation(g, np.ones((3, 3)))
    near = gd[W.row[ca], W.col[ca]].mean()
    la, lb = np.log1p(F[a]["pop"]), np.log1p(F[b]["pop"])
    print(f"{a} vs {b}: same people {same.sum()/occ.sum():.3f} (chance {float(na@nb):.3f})"
          f"  city sites within 1 cell {near:.3f} (chance {gd[W.row, W.col].mean():.3f})"
          f"  corr log pop {np.corrcoef(la, lb)[0,1]:.3f}")

# C. where people live
print("\n== C. where people live at the end", run)
S = F[run]
p = S["pop"]
tot = p.sum()
for nm, m in (("coastal", W.coastal), ("river", W.river), ("coast or river", W.coastal | W.river),
              ("alluvial", W.alluvial), ("irrigable (irr_share>0.3)", W.irr_share > 0.3)):
    print(f"{nm:28s} land share {W.area[m].sum()/W.area.sum():.3f}  pop share {p[m].sum()/tot:.3f}")
for k, b in enumerate(["Jungle", "Desert", "Grassland", "Temperate forest", "Tundra"]):
    m = W.biome == k
    print(f"{b:28s} land share {W.area[m].sum()/W.area.sum():.3f}  pop share {p[m].sum()/tot:.3f}"
          f"  density {p[m].sum()/W.area[m].sum():.2f}/km2")
d = p / W.area
print("world density", round(tot / W.area.sum(), 2), "/km2; cell density p50 p90 p99 max:",
      [round(float(x), 1) for x in np.percentile(d[p > 0], [50, 90, 99, 100])])
print("occupied share of land cells", round(float((p > 0).mean()), 3),
      " in a state:", round(float((S['polity'] >= 0).mean()), 3))
lat = np.abs(W.lat)
for lo, hi in ((0, 15), (15, 30), (30, 45), (45, 60), (60, 90)):
    m = (lat >= lo) & (lat < hi)
    print(f"|lat| {lo}-{hi}: land {W.area[m].sum()/W.area.sum():.3f} pop {p[m].sum()/tot:.3f}")
# deaths
with open(os.path.join(R, run, "deaths.csv")) as fh:
    D = list(csv.DictReader(fh))
c = {}
for r in D:
    c[r["cause"]] = c.get(r["cause"], 0) + f(r["deaths"])
s = sum(c.values())
print("deaths by cause:", {k: round(v / s, 3) for k, v in sorted(c.items(), key=lambda x: -x[1])})
