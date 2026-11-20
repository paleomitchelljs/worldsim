"""WP9 stage B: elementary effects from the Morris screen (wp9_screen.py).

    python wp9_analyze.py [--baseline wp8i] [--md out.md]

For each pattern (docs/patterns.md) and parameter: mu* (mean |EE|), mu
(mean EE) and sigma (sd of EE), with EE = (y_after - y_before) / delta in
the unit-scaled parameter space (delta = 2/3 at 4 levels; log-scaled
parameters are scaled on log10). Seed noise: the sd of the pattern over
six seeds at the default point (the baseline batch's five, base_seed105).
An EE made of two single-seed runs has noise sqrt(2) sd / delta; `ratio`
is mu* over that. Points whose run failed are skipped, with the EEs
that use them.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, SIM)
import runroot  # noqa: E402

DESIGN = os.path.join(HERE, "..", "baseline", "wp9b_design.json")
OUT = os.path.join(runroot.root(), "wp9b")

# (pattern id of docs/patterns.md, metrics function, key)
PATTERNS = [
    ("P1", "population", "pop end (M)"),
    ("P2", "timeline", "first city (yr)"),
    ("P2b", "timeline", "year of 10M"),
    ("P2c", "timeline", "first bronze (yr)"),
    ("P3", "growth", "growth %/yr, 6000-7000"),
    ("P4", "volatility", "largest 100-yr fall (log), after 3000"),
    ("P5", "population", "urban share end"),
    ("C1", "city_hierarchy", "rank-size slope, end (top 200)"),
    ("C2", "city_hierarchy", "largest city, share of world"),
    ("C3", "food", "city food trade, share"),
    ("C4", "city_lives", "cities ended, share"),
    ("C5", "spacing", "spacing vs local density, Spearman rho"),
    ("C6", "waterside", "large third: coast or river"),
    ("S1", "lifespans", "lifespan median (yr)"),
    ("S2", "states", "largest state, share of land"),
    ("S3", "states", "skew of log peak cells"),
    ("S4", "minor_states", "rank-size slope, ranks 11-100, peak"),
    ("S5", "states", "never above one city, share"),
    ("S6", "rule_spells", "rule spell years, p90"),
    ("S7", "contiguity", "state 1: land pieces"),
    ("W1", "wars", "wars"),
    ("W2", "sieges", "sieges taken, share"),
    ("W3", "peer_wars", "peer wars (ended)"),
    ("L1", "settlement", "river: pop share"),
    ("L2", "settlement", "|lat| 0-15: pop share"),
    ("L4", "settlement", "population in a state, share"),
    ("K3", "lineage_cities", "between cities of a lineage, sd (median)"),
    ("K4", "turnover", "people changed, 7500-8000"),
]


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def value(m, fn, key):
    if not m or fn not in m:
        return np.nan
    v = m[fn].get(key)
    if v is None:
        # keys that vary in wording between versions: first that starts so
        hit = [x for k, x in m[fn].items() if k.startswith(key)]
        v = hit[0] if hit else None
    return float(v) if isinstance(v, (int, float)) else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="wp8j")
    ap.add_argument("--md")
    a = ap.parse_args()
    with open(DESIGN) as fh:
        d = json.load(fh)
    names, k = d["problem"]["names"], d["problem"]["num_vars"]
    lo = np.array([b[0] for b in d["problem"]["bounds"]])
    hi = np.array([b[1] for b in d["problem"]["bounds"]])
    X = (np.array(d["unit_X"]) - lo) / (hi - lo)
    pts = [p for p in d["points"] if p["name"].startswith("p")]
    M = [load(os.path.join(OUT, p["name"], "metrics.json")) for p in pts]
    seeds = [load(os.path.join(runroot.root(), f"{a.baseline}_seed{s}",
                               "metrics.json")) for s in (101, 102, 103, 104, 106)]
    seeds.append(load(os.path.join(OUT, "base_seed105", "metrics.json")))
    seeds = [m for m in seeds if m]
    lines = [f"Points done: {sum(m is not None for m in M)} of {len(M)}; "
             f"seeds at the default point: {len(seeds)}.", ""]
    rows = []
    for pid, fn, key in PATTERNS:
        y = np.array([value(m, fn, key) for m in M])
        ys = np.array([value(m, fn, key) for m in seeds])
        sd = float(np.nanstd(ys, ddof=1)) if np.isfinite(ys).sum() >= 3 else np.nan
        ee = {n: [] for n in names}
        for t in range(len(pts) // (k + 1)):
            for i in range(t * (k + 1), (t + 1) * (k + 1) - 1):
                dx = X[i + 1] - X[i]
                j = int(np.argmax(np.abs(dx)))
                if np.isfinite(y[i]) and np.isfinite(y[i + 1]) and dx[j]:
                    ee[names[j]].append((y[i + 1] - y[i]) / dx[j])
        noise = math.sqrt(2) * sd / (2 / 3) if np.isfinite(sd) else np.nan
        stats = []
        for n in names:
            e = np.array(ee[n])
            if len(e):
                ms = float(np.abs(e).mean())
                stats.append((n, ms, float(e.mean()),
                              float(e.std(ddof=1)) if len(e) > 1 else np.nan,
                              len(e), ms / noise if noise > 0 else np.nan))
        stats.sort(key=lambda s: -s[1])
        rows.append((pid, fn, key, sd, float(np.nanmean(ys)), noise, stats))
        lines.append(f"### {pid}: {fn}: {key}")
        lines.append("")
        lines.append(f"Default point: mean {np.nanmean(ys):.4g}, seed sd "
                     f"{sd:.3g}; EE noise {noise:.3g}.")
        lines.append("")
        lines.append("| Parameter | mu* | mu | sigma | n | mu* / noise |")
        lines.append("|---|---|---|---|---|---|")
        for n, ms, mu, sg, cnt, r in stats[:8]:
            lines.append(f"| {n} | {ms:.3g} | {mu:.3g} | {sg:.3g} | {cnt} | {r:.2f} |")
        above = [s[0] for s in stats if s[5] > 1]
        lines.append("")
        lines.append(f"Above seed noise: {', '.join(above) or 'none'}.")
        lines.append("")
    # parameters above noise on no pattern
    hit = {n: 0 for n in names}
    for *_, stats in rows:
        for s in stats:
            if s[5] > 1:
                hit[s[0]] += 1
    lines.append("### Patterns each parameter moves above seed noise")
    lines.append("")
    lines.append("| Parameter | patterns |")
    lines.append("|---|---|")
    for n in sorted(names, key=lambda n: -hit[n]):
        lines.append(f"| {n} | {hit[n]} |")
    text = "\n".join(lines)
    print(text)
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(text + "\n")


if __name__ == "__main__":
    main()
