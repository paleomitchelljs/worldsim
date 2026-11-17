"""How often land changes hands, from history.npz (2026-11-06).

    python turnover.py RUN [RUN ...] [--window 500]

Per window: share of occupied cells whose people changed; share of ruled
cells whose ruling people changed; share of occupied land in a state;
share of ruled land held by a people other than its rulers; and each
people's share of heads at the window's end (spread between peoples).
"""
import argparse
import os
import numpy as np

import runroot


def ruler_people(h):
    """Ruling people per cell for every snapshot (-1 outside states)."""
    S = h["polity"]
    out = -np.ones_like(S)
    for k in range(len(S)):
        sel = h["st_t"] == k
        if not sel.any():
            continue
        lut = np.full(max(S[k].max(), h["st_id"][sel].max()) + 1, -1)
        lut[h["st_id"][sel]] = h["st_people"][sel]
        m = S[k] > 0
        out[k, m] = lut[S[k, m]]
    return out


def report(run, window):
    h = np.load(os.path.join(run, "history.npz"))
    Y, P, pop = h["year"], h["people"].astype(int), h["pop"]
    R = ruler_people(h)
    step = max(1, int(round(window / (Y[1] - Y[0]))))
    nP = P.max() + 1
    print(f"\n{run}")
    print(f"{'years':>11} {'people':>7} {'ruler':>7} {'in state':>8} "
          f"{'foreign':>7}  heads by people (%)")
    for a in range(step - 1, len(Y) - step, step):
        b = a + step
        occ = (P[a] >= 0) & (P[b] >= 0)
        rul = (R[a] >= 0) & (R[b] >= 0)
        inb = R[b] >= 0
        ch_p = (P[a] != P[b])[occ].mean() if occ.any() else np.nan
        ch_r = (R[a] != R[b])[rul].mean() if rul.any() else np.nan
        ins = inb[P[b] >= 0].mean() if (P[b] >= 0).any() else np.nan
        frn = (R[b] != P[b])[inb].mean() if inb.any() else np.nan
        hp = np.bincount(np.maximum(P[b], 0), weights=pop[b] * (P[b] >= 0),
                         minlength=nP)
        sh = " ".join(f"{100 * x / max(hp.sum(), 1):4.0f}" for x in hp)
        print(f"{Y[a]:5d}-{Y[b]:5d} {ch_p:7.3f} {ch_r:7.3f} {ins:8.2f} "
              f"{frn:7.3f}  {sh}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--window", type=int, default=500)
    a = ap.parse_args()
    for r in runroot.expand(a.runs):
        report(r, a.window)
