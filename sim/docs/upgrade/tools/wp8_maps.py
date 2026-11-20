"""WP8: before/after maps of population density, rivers and city sites.

    ~/.venvs/worldsim/bin/python docs/upgrade/tools/wp8_maps.py OUT.png RUN ...

One panel per run, each on its own world file: log population density at
the end, river cells at the end (blue), and every cell that ever held a
city (red dots).
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from wsim.params import NX, NY  # noqa: E402
from wsim.runio import Run  # noqa: E402


def main(out, names):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(names), 1, figsize=(12, 5.2 * len(names)))
    axs = np.atleast_1d(axs)
    for ax, name in zip(axs, names):
        run = Run(name)
        W, F = run.W, run.final
        river = F["river"].astype(bool) if "river" in F else W.river
        d = np.full((NY, NX), np.nan)
        d[W.row, W.col] = np.log10(np.maximum(F["pop"] / W.area, 1e-3))
        ax.imshow(np.where(np.isnan(d), np.nan, 1), extent=(-180, 180, -90, 90),
                  cmap="Greys", vmin=0, vmax=4)
        im = ax.imshow(np.where(d > -3, d, np.nan), extent=(-180, 180, -90, 90),
                       cmap="YlOrBr", vmin=-2, vmax=1.5)
        ax.scatter(W.lon[river], W.lat[river], s=0.4, c="#1f5fbf", lw=0)
        c = F["city_peak"] > 0
        ax.scatter(W.lon[c], W.lat[c], s=4, c="#c00000", lw=0)
        ax.set_title(f"{run.name} ({run.config.get('world', 'world.gpkg')}): "
                     f"{F['pop'].sum() / 1e6:.0f}M; blue river cells, red city sites")
        fig.colorbar(im, ax=ax, shrink=0.7, label="log10 people / km2")
    fig.savefig(out, dpi=80, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
