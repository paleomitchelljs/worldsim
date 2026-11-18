"""
State colours for drawn maps (WP3 stage C, 2026-11-17; all C).

A state keeps one colour for its whole life. The hue stays near its
ruling people's (within HUE_SPREAD), so the peoples still read, while
lightness and saturation vary widely, so a successor state of the same
people looks different from the state it replaced. States are coloured
in order of first appearance; each takes the first of its candidate
colours that is at least MIN_DIST from every state it ever borders and
from its parent state (polities.csv), among those already coloured, or
else the candidate farthest from them. Candidates come from a generator
seeded by the state id, so a state's colour depends only on the run's
history, never on the simulation's random streams.

Computed from history.npz alone, so older runs get the same treatment.
The live render (final_maps.png) still uses the colour each state drew
at founding (`states.polity_color`).
"""
import colorsys

import numpy as np

from .params import NY, NX

HUE_SPREAD = 0.045      # hue offset from the people's, either way (0-1)
LIGHT = (0.28, 0.80)    # HLS lightness range
SAT = (0.30, 0.95)      # HLS saturation range
MIN_DIST = 70.0         # least colour distance to neighbours ("redmean")
N_CAND = 32             # candidate colours per state


def dist(a, b):
    """'Redmean' colour distance between RGB rows a (n, 3) and b (3,):
    Euclidean with weights that follow the eye better than plain RGB."""
    r = (a[:, 0] + b[0]) / 2
    d = a - b
    return np.sqrt((2 + r / 256) * d[:, 0] ** 2 + 4 * d[:, 1] ** 2 +
                   (2 + (255 - r) / 256) * d[:, 2] ** 2)


def neighbour_pairs(W, polity):
    """Every pair of states that shared a border in any snapshot.
    polity: (snapshots, cells). Returns a set of (a, b) with a < b."""
    g = np.full((NY, NX), -1, np.int64)
    m = 1 << 32
    keys = set()
    for p in polity:
        g[W.row, W.col] = p
        for a, b in ((g[:, :-1], g[:, 1:]), (g[:-1, :], g[1:, :]),
                     (g[:, -1:], g[:, :1])):          # across the date line
            ok = (a >= 0) & (b >= 0) & (a != b)
            lo = np.minimum(a[ok], b[ok])
            hi = np.maximum(a[ok], b[ok])
            keys.update(np.unique(lo * m + hi).tolist())
    return {(k >> 32, k & (m - 1)) for k in keys}


def state_colors(W, H, colors, parents=None):
    """(max state id + 1, 3) colours for the states in history H.
    colors: the peoples' RGB; parents: {state: parent state}."""
    sid, sp, st_t = H["st_id"], H["st_people"], H["st_t"]
    pol = H["polity"]
    n = int(max(pol.max(), sid.max() if len(sid) else -1)) + 1
    out = np.full((max(n, 1), 3), 128.0)     # grey: not in the table
    if not len(sid):
        return out
    # people and first snapshot of each state, from the state table
    o = np.lexsort((sid, st_t))
    first = {}
    for i in o:
        first.setdefault(int(sid[i]), (int(st_t[i]), int(sp[i])))
    nb = {}
    for a, b in neighbour_pairs(W, pol):
        nb.setdefault(a, []).append(b)
        nb.setdefault(b, []).append(a)
    for s, p in (parents or {}).items():
        if p is not None and p >= 0:
            nb.setdefault(s, []).append(p)
            nb.setdefault(p, []).append(s)
    done = np.zeros(len(out), bool)
    for s in sorted(first, key=lambda s: (first[s][0], s)):
        h0, _, _ = colorsys.rgb_to_hls(*(colors[first[s][1]] / 255))
        rng = np.random.default_rng(s)
        hue = (h0 + rng.uniform(-HUE_SPREAD, HUE_SPREAD, N_CAND)) % 1
        light = rng.uniform(*LIGHT, N_CAND)
        sat = rng.uniform(*SAT, N_CAND)
        cand = 255 * np.array([colorsys.hls_to_rgb(h, l, v)
                               for h, l, v in zip(hue, light, sat)])
        others = [o for o in nb.get(s, ()) if o < len(out) and done[o]]
        if others:
            dmin = np.min([dist(cand, out[o]) for o in others], axis=0)
            ok = np.nonzero(dmin >= MIN_DIST)[0]
            k = ok[0] if len(ok) else int(np.argmax(dmin))
        else:
            k = 0
        out[s] = cand[k]
        done[s] = True
    return out
