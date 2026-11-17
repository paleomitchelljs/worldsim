"""Do repeated runs put their big cities in the same places?

    python bigcities.py runs/ct_seed10{1..6}

For each pair of runs, the share of one run's big-city sites with a big-city
site of the other within R km, against a null of the same number of sites
drawn from every cell that ever held a city of those peoples in the other
run (so the null knows where cities can be at all). Run for the top N by
peak size, the top N alive at set years, and each people's top 5. Then
clusters the top-N sites of all runs (greedy, R km) and lists the places
that recur in several runs; written to e.g. runs/ct_bigcities.csv for
runs/ct_seed*.
"""
import sys

import numpy as np
import pandas as pd

import runroot

N, R = 25, 150.0


def xyz(df):
    la, lo = np.radians(df.lat.values), np.radians(df.lon.values)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo),
                     np.sin(la)], 1)


def km(a, b):
    return 6371 * np.arccos(np.clip(a @ b.T, -1, 1))


def main(dirs):
    rng = np.random.default_rng(0)
    C = {d: pd.read_csv(d + "/cities.csv") for d in dirs}
    S = {d: pd.read_csv(d + "/city_sizes.csv") for d in dirs}
    loc = {d: C[d].set_index("id")[["lon", "lat"]] for d in dirs}

    def by_peak(d, people=None, n=N):
        c = C[d] if people is None else C[d][C[d].people == people]
        return c.sort_values("peak_size", ascending=False) \
            .drop_duplicates("cell").head(n)

    def test(sel, label):
        obs, nul = [], []
        for i in dirs:
            for j in dirs:
                if i == j:
                    continue
                a, b = sel(i), sel(j)
                pool = C[j][C[j].people.isin(b.people.unique())] \
                    .drop_duplicates("cell")
                if len(a) < 3 or len(b) < 3 or len(pool) < len(b):
                    continue
                xa = xyz(a)
                obs.append((km(xa, xyz(b)).min(1) < R).mean())
                nul.append(np.mean([(km(xa, xyz(pool.sample(
                    len(b), random_state=int(rng.integers(1e9))))).min(1)
                    < R).mean() for _ in range(30)]))
        if obs:
            print(f"{label:30s} observed {np.mean(obs):.2f} "
                  f"({min(obs):.2f}-{max(obs):.2f})  null {np.mean(nul):.2f}")

    print(f"share of big-city sites with a match within {R:.0f} km "
          f"in another run")
    test(by_peak, f"top {N} by peak size")
    for yr in (2000, 3000, 4000, 5000, 6000, 7000):
        def alive(d, yr=yr):
            s = S[d][(S[d].year == yr) & (S[d].status == "city")]
            return s.nlargest(N, "size").join(loc[d], on="city_id")
        test(alive, f"top {N} alive at yr {yr}")
    for p in sorted(set.intersection(*[set(c.people) for c in C.values()])):
        test(lambda d, p=p: by_peak(d, p, 5), f"{p} top 5 by peak")

    # the places that recur
    T = pd.concat([by_peak(d).assign(run=d) for d in dirs]) \
        .sort_values("peak_size", ascending=False).reset_index(drop=True)
    D = km(xyz(T), xyz(T))
    cl = -np.ones(len(T), int)
    for i in range(len(T)):
        if cl[i] < 0:
            cl[(D[i] < R) & (cl < 0)] = i
    T["place"] = cl
    g = T.groupby("place").agg(
        runs=("run", "nunique"), lon=("lon", "first"), lat=("lat", "first"),
        peoples=("people", lambda x: ",".join(sorted(set(x)))),
        max_peak=("peak_size", "max"),
        first_peak=("peak_year", "min"), last_peak=("peak_year", "max"))
    g = g.sort_values(["runs", "max_peak"], ascending=False)
    print(f"\ntop-{N} places by number of runs they appear in:")
    print(g.runs.value_counts().sort_index(ascending=False).to_string())
    print(g[g.runs >= max(3, len(dirs) // 2)].to_string())
    out = dirs[0].rstrip("/").split("_seed")[0] + "_bigcities.csv"
    g.to_csv(out)
    print("->", out)


if __name__ == "__main__":
    main(runroot.expand(sys.argv[1:]))
