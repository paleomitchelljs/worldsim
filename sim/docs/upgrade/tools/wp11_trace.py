"""WP11 stage A: what holds each biome's density down (records only).

    python wp11_trace.py --seed 101 --years 8000 [--md out.md] [--png out.png]
        [worldsim.py options ...]

Runs the Sim in memory to --years with the run's defaults (no run files:
the output stream is replaced by a no-op), then at the end splits the
capacity of every occupied cell into the factors of land.K2 for its main
lineage, and compares it with the best capacity any people's most
developed lineage would have there (Kf raw, before what states take).
Per biome: people per km², capacity per km², fill (people / capacity),
the farming and foraging terms and each multiplier, the share of cells
where herding beats farming, and the best capacity. Numbers are
area-weighted means over occupied cells unless named otherwise.
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


def run(argv):
    import worldsim
    from wsim import output, sim as simmod
    output.Stream = _NoStream
    simmod.render = lambda s: None
    s, out, t0 = worldsim.make_sim(argv)
    s.run(verbose=False)
    return s


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md")
    ap.add_argument("--png")
    a, rest = ap.parse_known_args()
    s = run(rest)
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


if __name__ == "__main__":
    main()
