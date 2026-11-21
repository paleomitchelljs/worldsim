"""WP11: what holds each biome's density down (records only).

    python wp11_trace.py --seed 101 --years 8000 [--md out.md] [--png out.png]
        [--window 1000] [worldsim.py options ...]

Runs the Sim in memory to --years with the run's defaults (no run files:
the output stream is replaced by a no-op), then at the end splits the
capacity of every occupied cell into the factors of land.K2 for its main
lineage, and compares it with the best capacity any people's most
developed lineage would have there (Kf raw, before what states take).
Per biome: people per km², capacity per km², fill (people / capacity),
the farming and foraging terms and each multiplier, the share of cells
where herding beats farming, and the best capacity. Numbers are
area-weighted means over occupied cells unless named otherwise.

Stage B part 1, the half-fill: per biome, the main rows' people as a
share of land capacity (raw K with no devastation and no drought), and
the gap split in the order grow meets it: drought, devastation, what
the state takes (own people's rent and tax, armies' food, subjects'
rent and tribute, trade sold), what it sends back (capital's take, a
city's rent, spending and trade), what other peoples' rows in the cell
eat (`shared_cells`), the share a people chooses not to fill
(`separation`), and what is left: population below its own capacity
(lag, plus whatever left or died since grow in the last tick). The
terms add up to 1 - fill exactly. Over the last --window years, a
per-biome account of heads by phase (each phase's change plus the
deaths recorded in it, so `grow` is natural increase) and of deaths by
cause, and fill every 500 years.
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIM = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, SIM)
os.chdir(SIM)


class _NoStream:
    def __init__(self, sim, out):
        pass

    def frame(self, img):
        pass

    def flush(self):
        pass


def run(argv, window):
    import worldsim
    from wsim import output, sim as simmod
    output.Stream = _NoStream
    simmod.render = lambda s: None
    s, out, t0 = worldsim.make_sim(argv)
    s.wp11 = Account(s, s.years - window)
    s.run(verbose=False)
    return s


class Account:
    """Records hooked onto one Sim (instance attributes, so the class's
    methods are untouched): heads by biome at each phase mark and deaths
    by biome and cause, from year `start`; fill by biome every 500
    years."""

    def __init__(self, s, start):
        self.s, self.start = s, start
        nb = int(s.W.biome.max()) + 1
        self.nb = nb
        self.phase, self.cause, self.order = {}, {}, []
        self.last = None
        self.dsince = np.zeros(nb)
        self.heads0 = None
        self.fill = []
        self.ticks = 0
        mark, dead, forgone, step = s.acct_mark, s.dead, s.forgone, s.step

        def on():
            return s.year >= start

        def acct_mark(phase):
            mark(phase)
            if not on():
                return
            h = self.heads()
            if self.last is not None:
                if phase not in self.phase:
                    self.phase[phase] = np.zeros(nb)
                    self.order.append(phase)
                self.phase[phase] += h - self.last + self.dsince
            else:
                self.heads0 = h
            self.last = h
            self.dsince = np.zeros(nb)

        def dead_(cause, cells, lost, minority=False, rows=False):
            dead(cause, cells, lost, minority=minority, rows=rows)
            if on():
                self.add(cause, cells, lost, minority, rows)

        def forgone_(cells, lost, minority=False, rows=False):
            forgone(cells, lost, minority=minority, rows=rows)
            if on():
                b = self.biome(cells, rows)
                v = np.bincount(b, weights=np.maximum(lost, 0),
                                minlength=nb)
                self.forg = getattr(self, "forg", 0) + v

        def step_():
            step()
            if on():
                self.ticks += 1
            if s.year % 500 == 0:
                occ = np.nonzero((s.lin >= 0) & (s.pop > 0))[0]
                K = s.Kf(s.lin[occ], occ, raw=True)
                b = s.W.biome[occ]
                self.fill.append((s.year, np.bincount(
                    b, weights=s.pop[occ], minlength=nb), np.bincount(
                    b, weights=K, minlength=nb)))

        s.acct_mark, s.dead, s.forgone, s.step = \
            acct_mark, dead_, forgone_, step_

    def biome(self, cells, rows):
        s = self.s
        c = np.arange(s.W.N) if cells is None else np.atleast_1d(cells)
        return s.W.biome[s.rc[c] if rows else c]

    def add(self, cause, cells, lost, minority, rows):
        s = self.s
        cul = s.rp if rows else s.mcul if minority else s.cul
        c = cul if cells is None else cul[cells]
        b = self.biome(cells, rows)
        lost = np.broadcast_to(np.atleast_1d(lost), b.shape)
        ok = (np.atleast_1d(c) >= 0) & (lost > 0)
        v = np.bincount(b[ok], weights=lost[ok], minlength=self.nb)
        self.cause[cause] = self.cause.get(cause, 0) + v
        self.dsince += v

    def heads(self):
        """Heads by biome, as Sim.heads counts them (soldiers away from
        their cells excluded)."""
        s, nb, B = self.s, self.nb, self.s.W.biome
        a, m, x = s.cul >= 0, s.mlin >= 0, s.xrows()
        return np.bincount(B[a], weights=s.pop[a], minlength=nb) + \
            np.bincount(B[m], weights=s.mpop[m], minlength=nb) + \
            np.bincount(B[s.rc[x]], weights=s.rh[x], minlength=nb)


def factors(s, L, j):
    """K2's parts for lineages L in cells j, as a dict of arrays."""
    from wsim.params import (BIOMES, BURN_GAIN, IMP_RAIN, IMP_IRR0,
                             SALT_MAX, DOM_FLOOR, STEPPE_MIN)
    from wsim.land import CLEAR_X
    W = s.W
    a, tools, sf, eat, fk, pw, dv, h = s.lterms(L)
    cm = s.cm
    b = W.biome[j]
    clear = 1 + s.clear[j] * CLEAR_X[0, b] if "clearing" in s.on else 1
    rain = W.rain_ws[j] * clear
    steppe = 1 - (1 - STEPPE_MIN) * W.steppe_cut[j]
    imp = s.imp[j]
    rainc = rain * cm[0, j] * (1 + IMP_RAIN * imp)
    irr = W.irr_w[j] * cm[1, j] * (IMP_IRR0 + (1 - IMP_IRR0) * imp)
    grass = b == BIOMES.index("Grassland")
    sod = np.where(grass, 1 - (1 - sf), 1.0)
    farm = (rainc * sod + irr + W.fish[j]) * s.land[j] * \
        (1 - SALT_MAX * s.salt[j] * W.irr_share[j])
    FIT, CR, AN = s.ltab()
    crf = DOM_FLOOR + (1 - DOM_FLOOR) * CR[L, b]
    forage = W.forage[j] * cm[2, j]
    if "clearing" in s.on:
        forage = forage * (1 + s.clear[j] * CLEAR_X[1, b])
    if "fire" in s.on:
        unc = 1 - s.clear[j] if "clearing" in s.on else 1
        forage = forage * (1 + BURN_GAIN * s.burn[j] * unc)
    Kc, Kh = s.K2(L, j)
    return dict(a=a, tools=tools, sod=sod, steppe=steppe,
                rain_land=W.rain_w[j], clim_rain=cm[0, j], irr=irr,
                fish=W.fish[j], farm=farm, crop=crf, forage=forage,
                fit=FIT[L, b], Kcell=s.Kcell[j], coast_dev=(1 + fk * W.water[j])
                * dv, eat=eat, herd_wins=(Kh > Kc).astype(float),
                Kc=Kc, Kh=Kh)


def split(s, occ):
    """The main rows' capacity chain in cells occ, as arrays: land
    capacity (no drought, no devastation), the losses to each step down
    to grow's k, and people. Reads state only (Kcell is swapped and put
    back)."""
    from wsim.params import SHARE_ALPHA
    L = s.lin[occ]
    out = {}
    kc = s.Kcell
    try:
        s.Kcell = s.cboost.copy()
        K00 = s.Kf(L, occ, raw=True)
        s.Kcell = s.drought * s.cboost
        Kd = s.Kf(L, occ, raw=True)
    finally:
        s.Kcell = kc
    Kraw = s.Kf(L, occ, raw=True)
    Knet = s.Kf(L, occ)
    out["land K"] = K00
    out["drought"] = K00 - Kd
    out["devastation"] = Kd - Kraw
    if s.ff_on:
        c = s.Lpeople[L]
        own = c == s.rul_c[occ]
        out["rent+tax (own)"] = Kraw * own * s.ff_xo[occ]
        out["army food"] = Kraw * own * s.army_x[occ]
        out["rent+tribute (subjects)"] = Kraw * ~own * s.ext_x[occ]
        out["trade sold"] = Kraw * s.tr_x[occ] if s.td_on else 0 * Kraw
        out["received"] = -(own * s.ext_in[occ] + (c == s.city_c[occ]) *
                            s.loc_in[occ]) / s.peat[c]
        out["(state residual)"] = Kraw - Knet - sum(
            out[k] for k in ("rent+tax (own)", "army food",
                             "rent+tribute (subjects)", "trade sold",
                             "received"))
    else:
        out["state, net"] = Kraw - Knet
    k = np.maximum(Knet, 1e-3)
    if s.sh_on:
        rh = s.rh.copy()      # grow_shared also grows the other rows
        try:
            k2 = s.grow_shared(occ, k)
        finally:
            s.rh = rh
    else:
        k2 = k
    out["other rows eat"] = k - k2
    k3 = k2 * s.pref(L, occ)
    out["separation"] = k2 - k3
    out["below own k (lag)"] = k3 - s.pop[occ]
    out["people"] = s.pop[occ]
    # other rows' heads in the same cells, for scale
    x = s.xrows()
    oth = np.zeros(s.W.N)
    np.add.at(oth, s.rc[x], s.rh[x])
    mo = s.mlin >= 0
    oth[mo] += s.mpop[mo]
    out["other rows' people"] = oth[occ]
    out["stageA K"] = Kraw
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    ap.add_argument("--png")
    ap.add_argument("--window", type=int, default=1000)
    a, rest = ap.parse_known_args()
    s = run(rest, a.window)
    from wsim.params import BIOMES
    W = s.W
    occ = np.nonzero((s.lin >= 0) & (s.pop > 0))[0]
    L = s.lin[occ]
    f = factors(s, L, occ)
    K = s.Kf(L, occ, raw=True)
    # the best capacity any people's most developed lineage would have
    alive = np.unique(np.concatenate([s.lin[s.lin >= 0],
                                      s.mlin[s.mlin >= 0]]))
    dev = s.dev(alive)
    best = np.zeros(W.N)
    for p in np.unique(s.Lpeople[alive]):
        m = s.Lpeople[alive] == p
        Lb = alive[m][np.argmax(dev[m])]
        best = np.maximum(best, s.Kf(np.full(W.N, Lb), np.arange(W.N),
                                     raw=True))
    area = W.area
    lines = [f"Seed {s.seed}, year {s.year}: population "
             f"{s.pop.sum() / 1e6:.1f}M main rows; {len(occ)} occupied "
             "cells.", ""]
    cols = ["people/km2", "K/km2", "fill", "best K/km2", "farm", "forage",
            "agri", "tools", "sod", "steppe", "clim_rain", "crop", "fit",
            "Kcell", "coast_dev", "herd wins"]
    lines.append("| Biome | area M km² | occupied | " + " | ".join(cols) +
                 " |")
    lines.append("|---|" + "---|" * (len(cols) + 2))
    for bi, name in enumerate(BIOMES):
        m = W.biome[occ] == bi
        allb = W.biome == bi
        if not m.any():
            continue
        c, w = occ[m], area[occ[m]]

        def mean(v):
            return float((np.asarray(v)[m] * w).sum() / w.sum())
        row = [s.pop[c].sum() / w.sum(), K[m].sum() / w.sum(),
               s.pop[c].sum() / max(K[m].sum(), 1),
               best[allb].sum() / area[allb].sum(),
               mean(f["farm"]), mean(f["forage"]), mean(f["a"]),
               mean(f["tools"]), mean(f["sod"]), mean(f["steppe"]),
               mean(f["clim_rain"]), mean(f["crop"]), mean(f["fit"]),
               mean(f["Kcell"]), mean(f["coast_dev"]),
               mean(f["herd_wins"])]
        lines.append(f"| {name} | {area[allb].sum() / 1e6:.1f} | "
                     f"{w.sum() / area[allb].sum():.2f} | " +
                     " | ".join(f"{v:.3g}" for v in row) + " |")
    lines += [""] + halffill(s, occ) + [""] + flows(s)
    text = "\n".join(lines)
    print(text)
    if a.md:
        with open(a.md, "w") as fh:
            fh.write(text + "\n")
    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from wsim.params import NX, NY
        img = np.full((NY, NX, 2), np.nan)
        dens = np.zeros(W.N)
        dens[occ] = K / area[occ]
        img[W.row, W.col, 0] = dens
        img[W.row, W.col, 1] = best / area
        fig, ax = plt.subplots(2, 1, figsize=(9, 8))
        for k, t in enumerate(("Capacity of the people there (per km²)",
                               "Best capacity, any people's most developed "
                               "lineage (per km²)")):
            im = ax[k].imshow(np.log10(np.maximum(img[20:330, :, k], 1e-3)),
                              vmin=-2, vmax=1.5, cmap="viridis",
                              extent=[-180, 180, -75, 80])
            ax[k].set_title(t, loc="left", fontsize=11)
            ax[k].set_xticks([])
            fig.colorbar(im, ax=ax[k], label="log10 people per km²")
        plt.tight_layout()
        plt.savefig(a.png, dpi=110)


def halffill(s, occ):
    """The half-fill table: each term's share of land capacity, by
    biome and for all occupied land."""
    from wsim.params import BIOMES
    sp = split(s, occ)
    terms = [k for k in sp if k not in ("land K", "people",
                                        "other rows' people", "stageA K")]
    B = s.W.biome[occ]
    cols = ["land K/km²", "fill (people/land K)", "fill (stage A)"] + \
        terms + ["other rows' people"]
    lines = ["Half-fill: main rows' people as a share of land capacity "
             "(raw K, no drought or devastation), and the gap split by "
             "step; each term is a share of land capacity, and fill + "
             "the terms = 1. `received` is negative (food sent in). "
             "`other rows' people` is for scale.", "",
             "| Biome | " + " | ".join(cols) + " |",
             "|---|" + "---|" * len(cols)]
    groups = [(n, B == i) for i, n in enumerate(BIOMES)] + \
        [("All occupied", np.ones(len(occ), bool))]
    for name, m in groups:
        if not m.any():
            continue
        K0 = sp["land K"][m].sum()
        row = [K0 / s.W.area[occ][m].sum(), sp["people"][m].sum() / K0,
               sp["people"][m].sum() / sp["stageA K"][m].sum()] + \
            [np.asarray(sp[t])[m].sum() / K0 for t in terms] + \
            [sp["other rows' people"][m].sum() / K0]
        lines.append(f"| {name} | " + " | ".join(f"{v:.3f}" for v in row)
                     + " |")
    return lines


def flows(s):
    """The window's account: heads by phase and deaths by cause per
    biome, as a share of the biome's heads per century; and fill over
    time."""
    from wsim.params import BIOMES
    A = s.wp11
    yrs = A.ticks * 5
    h = np.maximum(A.heads0, 1)
    nb = [i for i in range(A.nb) if A.heads0[i] > 1e4]
    lines = [f"Flows over the last {yrs} years: heads by phase (change + "
             "deaths recorded in it; `grow` is natural increase) and "
             "deaths by cause, per century, as a share of the biome's "
             "heads at the window's start (all rows, soldiers away "
             "excluded).", "",
             "| | " + " | ".join(BIOMES[i] for i in nb) + " |",
             "|---|" + "---|" * len(nb)]
    end = A.last
    lines.append("| heads at start (M) | " + " | ".join(
        f"{A.heads0[i] / 1e6:.2f}" for i in nb) + " |")
    lines.append("| heads at end (M) | " + " | ".join(
        f"{end[i] / 1e6:.2f}" for i in nb) + " |")
    for ph in A.order:
        v = A.phase[ph] / h * 100 / yrs
        if np.abs(v[nb]).max() >= 5e-4:
            lines.append(f"| phase {ph} | " + " | ".join(
                f"{v[i]:+.3f}" for i in nb) + " |")
    for c in sorted(A.cause, key=lambda c: -A.cause[c].sum()):
        v = A.cause[c] / h * 100 / yrs
        if v[nb].max() >= 5e-4:
            lines.append(f"| deaths: {c} | " + " | ".join(
                f"{v[i]:.3f}" for i in nb) + " |")
    v = getattr(A, "forg", np.zeros(A.nb)) / h * 100 / yrs
    lines.append("| growth forgone under dragons (not deaths) | " +
                 " | ".join(f"{v[i]:.3f}" for i in nb) + " |")
    lines += ["", "Fill (main rows' people / raw K, as stage A) by year:",
              "", "| Year | " + " | ".join(BIOMES[i] for i in nb) + " |",
              "|---|" + "---|" * len(nb)]
    for y, p, K in A.fill:
        if y % 1000 == 0 or y >= s.years - 1000:
            lines.append(f"| {y} | " + " | ".join(
                f"{p[i] / max(K[i], 1):.2f}" for i in nb) + " |")
    return lines


if __name__ == "__main__":
    main()
