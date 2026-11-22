"""WP12 stage A: falls in population and how long they last (records
only).

    python wp12_trace.py --seed 101 --years 8000 [--md out.md] [--png out.png]
        [worldsim.py options ...]

Runs the Sim in memory as wp11_trace.py does (no run files). Every 25
years it records, per landmass group (landmasses.py: S, W, N, E, X), the
heads (all rows) and the raw capacity of the main rows (Kf raw: before
what states take); per state, its people and the cells it holds; and,
between records, deaths by cause per group and per state (from `dead`).

A fall is a drop to under (1 - DROP) of the running peak since the last
fall ended. It ends when heads are back to 90% of that peak (or at the
end of the run, unrecovered). For each: depth, years from peak to
trough, years from trough to 90%, and what went with it, as shares of
the peak's heads over peak-to-trough: excess deaths by cause (deaths
less the series' median rate by cause over the run), the fall in raw
capacity, and for states the share of the peak's people in cells the
state no longer held at the trough (land lost). The label is the
largest of these.

Time below capacity: heads / raw capacity per group (`fill`); the share
of records after 3000 with fill under 0.8, and under 0.8 x the group's
own median fill after 3000 (WP11 found every biome at about half of raw
capacity, so the first is near 1 by construction). Fill rises all run,
so the second measures the trend; WP12 C adds fill under 0.8 x its own
centred 500-year running median.

Cells that change hands (WP12 C, for `collapse_cost`): between two
records, an occupied cell whose state changes to another state, or to
none. Over the next CH_YEARS, its deaths per head (all causes; feud and
raids) and its heads at the end over its heads before, against cells of
the same landmass group whose state did not change (held, or stateless
throughout, shown apart), weighted by heads. Cells are counted
once per record they change in; later changes inside the window are
not removed.
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, SIM)
sys.path.insert(0, HERE)
os.chdir(SIM)

from wp11_trace import _NoStream  # noqa: E402

EVERY = 25          # years between records
DROP = 0.2          # a fall: under 80% of the running peak
STATE_MIN = (3, 200)    # states with 3+ cities at peak, 200+ years of records
RUN_MED = 500       # years in the running median of fill
CH_YEARS = 100      # years followed after a change of hands


class Trace:
    """Records hooked onto one Sim's instance (state is only read)."""

    def __init__(self, s):
        from landmasses import CODES, GROUPS
        self.s = s
        W = s.W
        self.names = list(GROUPS)
        gid = {c: i for i, (g, cc) in enumerate(GROUPS.items()) for c in cc}
        self.grp = np.full(W.N, -1)
        for lm, c in CODES.items():
            self.grp[W.landmass == lm] = gid[c]
        self.ng = len(self.names)
        self.years, self.heads, self.K = [], [], []
        self.gdead, self.sdead = [], []      # per record: {cause: array}
        self.spop, self.pol, self.cpop = [], [], []
        self.cur_g, self.cur_s = {}, {}
        self.cdead, self.cfeud, self.craid = [], [], []
        self.cur_c = np.zeros(W.N)
        self.cur_f = np.zeros(W.N)
        self.cur_r = np.zeros(W.N)
        dead, step = s.dead, s.step

        def dead_(cause, cells, lost, minority=False, rows=False):
            dead(cause, cells, lost, minority=minority, rows=rows)
            self.add(cause, cells, lost, minority, rows)

        def step_():
            step()
            if s.year % EVERY == 0:
                self.record()

        s.dead, s.step = dead_, step_

    def add(self, cause, cells, lost, minority, rows):
        s = self.s
        cul = s.rp if rows else s.mcul if minority else s.cul
        c = np.arange(s.W.N) if cells is None else np.atleast_1d(cells)
        cc = s.rc[c] if rows else c
        lost = np.broadcast_to(np.atleast_1d(lost), cc.shape)
        ok = (np.atleast_1d(cul[c]) >= 0) & (lost > 0)
        cc, lost = cc[ok], lost[ok]
        np.add.at(self.cur_c, cc, lost)
        if cause == "feud":
            np.add.at(self.cur_f, cc, lost)
        elif cause == "raid":
            np.add.at(self.cur_r, cc, lost)
        g = self.grp[cc]
        m = g >= 0
        self.cur_g[cause] = self.cur_g.get(cause, 0) + np.bincount(
            g[m], weights=lost[m], minlength=self.ng)
        p = s.cell_pol[cc]
        m = p >= 0
        if m.any():
            d = self.cur_s.setdefault(cause, {})
            u, inv = np.unique(p[m], return_inverse=True)
            v = np.bincount(inv, weights=lost[m])
            for pid, x in zip(u.tolist(), v.tolist()):
                d[pid] = d.get(pid, 0.0) + x

    def record(self):
        s, G, ng = self.s, self.grp, self.ng
        h = np.zeros(s.W.N)
        a, m, x = s.cul >= 0, s.mlin >= 0, s.xrows()
        h[a] += s.pop[a]
        h[m] += s.mpop[m]
        np.add.at(h, s.rc[x], s.rh[x])
        occ = np.nonzero((s.lin >= 0) & (s.pop > 0))[0]
        K = np.zeros(s.W.N)
        K[occ] = s.Kf(s.lin[occ], occ, raw=True)
        ok = G >= 0
        self.years.append(s.year)
        self.heads.append(np.bincount(G[ok], weights=h[ok], minlength=ng))
        self.K.append(np.bincount(G[ok], weights=K[ok], minlength=ng))
        self.gdead.append(self.cur_g)
        self.sdead.append(self.cur_s)
        self.cur_g, self.cur_s = {}, {}
        for lst, cur in ((self.cdead, self.cur_c), (self.cfeud, self.cur_f),
                         (self.craid, self.cur_r)):
            lst.append(cur.astype(np.float32))
            cur[:] = 0
        self.spop.append({pid: (P["pop"], len(P["cities"]))
                          for pid, P in s.polities.items()
                          if P["ended"] is None})
        self.pol.append(s.cell_pol.astype(np.int32).copy())
        self.cpop.append(h.astype(np.float32))


def falls(y, x):
    """Falls in series x (years y): (i_peak, i_trough, i_end or None)."""
    out, i, n = [], 0, len(x)
    pk = 0
    while i < n:
        if x[i] > x[pk]:
            pk = i
        if x[pk] > 0 and x[i] < (1 - DROP) * x[pk]:
            tr, j = i, i
            while j < n and x[j] < 0.9 * x[pk]:
                if x[j] < x[tr]:
                    tr = j
                j += 1
            out.append((pk, tr, j if j < n else None))
            if j >= n:
                break
            i = pk = j
        i += 1
    return out


def hands(T, y):
    """Cells that change hands against cells that keep them (WP12 C)."""
    n = CH_YEARS // EVERY
    P = np.array(T.pol)
    C = np.array(T.cpop)
    Dd = [np.array(T.cdead), np.array(T.cfeud), np.array(T.craid)]
    kinds = {"to another state": [], "to no state": [],
             "kept, in a state": [], "stateless throughout": []}
    for i in range(1, len(y) - n):
        if y[i] < 1000:
            continue
        p0, p1, h0 = P[i - 1], P[i], C[i - 1]
        occ = (h0 > 0) & (T.grp >= 0)
        sel = {"to another state": occ & (p0 >= 0) & (p1 >= 0) & (p0 != p1),
               "to no state": occ & (p0 >= 0) & (p1 < 0),
               "kept, in a state": occ & (p0 == p1) & (p0 >= 0),
               "stateless throughout": occ & (p0 < 0) & (p1 < 0)}
        for k, m in sel.items():
            if not m.any():
                continue
            # deaths from the change on (record i holds deaths since i-1)
            d = [float(D[i:i + n + 1, m].sum()) for D in Dd]
            kinds[k].append((float(h0[m].sum()), *d,
                             float(C[i + n, m].sum()), int(m.sum())))
    out = [f"Cells that change hands after 1000, and the {CH_YEARS} years "
           "that follow (deaths per head at the change; heads at the end "
           "over heads before), against cells whose state did not change.",
           "", "| Cells | Changes (cell-records) | Deaths per head | Feud "
           "| Raids | Heads after / before |", "|---|---|---|---|---|---|"]
    for k, r in kinds.items():
        if not r:
            out.append(f"| {k} | 0 | | | | |")
            continue
        a = np.array(r)
        h = a[:, 0].sum()
        out.append(f"| {k} | {int(a[:, 5].sum())} | {a[:, 1].sum() / h:.3f}"
                   f" | {a[:, 2].sum() / h:.3f} | {a[:, 3].sum() / h:.3f} | "
                   f"{a[:, 4].sum() / h:.3f} |")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    ap.add_argument("--png")
    a, rest = ap.parse_known_args()
    import worldsim
    from wsim import output, sim as simmod
    output.Stream = _NoStream
    simmod.render = lambda s: None
    s, _, _ = worldsim.make_sim(rest)
    T = Trace(s)
    s.run(verbose=False)
    y = np.array(T.years)
    H = np.array(T.heads)
    K = np.array(T.K)
    allc = sorted({c for r in T.gdead for c in r})
    lines = [f"Seed {s.seed}, {len(y)} records every {EVERY} years to "
             f"{s.year}; heads {H[-1].sum() / 1e6:.1f}M at the end.", ""]

    # ---- landmass groups
    lines += ["Falls of 20%+ by landmass group: depth, years peak to "
              "trough and trough to 90% of the peak (- unrecovered), and "
              "what went with it (shares of the peak's heads: excess "
              "deaths by cause above the group's median rate; fall in raw "
              "capacity).", "",
              "| Group | Peak year | Depth | Peak to trough | To 90% | "
              "Label | Capacity fall | Excess deaths (largest three) |",
              "|---|---|---|---|---|---|---|---|"]
    gfalls = []
    for g, name in enumerate(T.names):
        x = H[:, g]
        if x.max() < 1e5:
            continue
        D = {c: np.array([np.asarray(r.get(c, np.zeros(T.ng)))[g]
                          for r in T.gdead]) for c in allc}
        base = {c: float(np.median(v)) for c, v in D.items()}
        for pk, tr, en in falls(y, x):
            ex = {c: (D[c][pk + 1:tr + 1].sum() - base[c] * (tr - pk)) /
                  x[pk] for c in allc}
            kf = 1 - K[tr, g] / max(K[pk, g], 1)
            parts = dict(ex)
            parts["capacity"] = kf
            lab = max(parts, key=parts.get)
            top = sorted(ex.items(), key=lambda kv: -kv[1])[:3]
            depth = 1 - x[tr] / x[pk]
            rec = "-" if en is None else f"{y[en] - y[tr]}"
            gfalls.append((name, y[pk], depth, y[tr] - y[pk],
                           None if en is None else y[en] - y[tr], lab))
            lines.append(
                f"| {name} | {y[pk]} | {depth:.2f} | {y[tr] - y[pk]} | "
                f"{rec} | {lab} | {kf:+.2f} | " + ", ".join(
                    f"{c} {v:+.2f}" for c, v in top) + " |")
    if not gfalls:
        lines.append("| (none) | | | | | | | |")

    # ---- time below capacity
    lines += ["", "Heads / raw capacity by landmass group after 3000: "
              "median, and share of 25-year records under 0.8 and under "
              f"0.8 x the group's own median, and under 0.8 x its centred "
              f"{RUN_MED}-year running median.", "",
              "| Group | Median fill | Under 0.8 | Under 0.8 x own median "
              "| Under 0.8 x running median |",
              "|---|---|---|---|---|"]
    late = y >= min(3000, y[-1] // 2)
    for g, name in enumerate(T.names):
        if H[late, g].max() < 1e5:
            continue
        fa = H[:, g] / np.maximum(K[:, g], 1)
        h = RUN_MED // EVERY // 2
        rm = np.array([np.median(fa[max(0, i - h):i + h + 1])
                       for i in range(len(fa))])
        f = fa[late]
        md = float(np.median(f))
        lines.append(f"| {name} | {md:.2f} | {(f < 0.8).mean():.2f} | "
                     f"{(f < 0.8 * md).mean():.2f} | "
                     f"{(f < 0.8 * rm[late]).mean():.2f} |")

    # ---- states
    pids = sorted({p for r in T.spop for p in r})
    rows = []
    for pid in pids:
        x = np.array([r.get(pid, (np.nan, 0))[0] for r in T.spop])
        nc = np.array([r.get(pid, (0, 0))[1] for r in T.spop])
        alive = ~np.isnan(x)
        if nc.max() < STATE_MIN[0] or alive.sum() * EVERY < STATE_MIN[1]:
            continue
        idx = np.nonzero(alive)[0]
        xs = x[idx]
        D = {c: np.array([r.get(c, {}).get(pid, 0.0)
                          for r in np.array(T.sdead, object)[idx]])
             for c in allc}
        base = {c: float(np.median(v)) for c, v in D.items()}
        for pk, tr, en in falls(y[idx], xs):
            ex = {c: (D[c][pk + 1:tr + 1].sum() - base[c] * (tr - pk)) /
                  xs[pk] for c in allc}
            i0, i1 = idx[pk], idx[tr]
            held0 = T.pol[i0] == pid
            lostc = held0 & (T.pol[i1] != pid)
            land = float(T.cpop[i0][lostc].sum() /
                         max(T.cpop[i0][held0].sum(), 1))
            parts = dict(ex)
            parts["land lost"] = land
            lab = max(parts, key=parts.get)
            # unrecovered if the state ended or the run did
            rec = None if en is None else y[idx[en]] - y[i1]
            rows.append((pid, y[i0], 1 - xs[tr] / xs[pk], y[i1] - y[i0],
                         rec, lab, land, nc.max()))
    lines += ["", f"Falls of 20%+ in states ({STATE_MIN[0]}+ cities at "
              f"peak, {STATE_MIN[1]}+ years): {len(rows)} falls in "
              f"{len({r[0] for r in rows})} states.", ""]
    if rows:
        import collections
        lab = collections.Counter(r[5] for r in rows)
        dep = np.array([r[2] for r in rows])
        rc = np.array([np.nan if r[4] is None else r[4] for r in rows])
        lines += ["| Label | Falls | Median depth | Recovered | Median "
                  "years to 90% (recovered) |", "|---|---|---|---|---|"]
        for k, n in lab.most_common():
            m = np.array([r[5] == k for r in rows])
            r_ = rc[m]
            ok = ~np.isnan(r_)
            lines.append(f"| {k} | {n} | {np.median(dep[m]):.2f} | "
                         f"{ok.mean():.2f} | "
                         f"{np.median(r_[ok]) if ok.any() else float('nan'):.0f} |")
    lines += [""] + hands(T, y)
    text = "\n".join(lines)
    print(text)
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(text + "\n")
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
        fig, ax = plt.subplots(2, 1, figsize=(8, 6.5), sharex=True,
                               facecolor="#fcfcfb")
        for g, name in enumerate(T.names):
            if H[:, g].max() < 1e5:
                continue
            ax[0].plot(y, H[:, g] / 1e6, color=cols[g], lw=1.6, label=name)
            ax[1].plot(y, H[:, g] / np.maximum(K[:, g], 1), color=cols[g],
                       lw=1.6, label=name)
        for f in gfalls:
            g = T.names.index(f[0])
            ax[0].axvspan(f[1], f[1] + f[3], color=cols[g], alpha=0.15)
        ax[0].set_yscale("log")
        ax[0].set_ylabel("Heads (M, log)")
        ax[1].set_ylabel("Heads / raw capacity")
        ax[1].set_xlabel("Year")
        ax[0].set_title(f"Landmass groups, seed {s.seed}: heads and fill "
                        "(shaded: falls of 20%+, peak to trough)",
                        loc="left", fontsize=11)
        ax[0].legend(frameon=False, ncol=5, fontsize=9)
        for x_ in ax:
            x_.set_facecolor("#fcfcfb")
            for sp in ("top", "right"):
                x_.spines[sp].set_visible(False)
        plt.tight_layout()
        plt.savefig(a.png, dpi=120, facecolor="#fcfcfb")


if __name__ == "__main__":
    main()
