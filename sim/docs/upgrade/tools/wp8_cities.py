"""WP8 stages B and C: where people and the largest cities are, by run.

    ~/.venvs/worldsim/bin/python docs/upgrade/tools/wp8_cities.py RUN ...

Per run, on its own world file (run.json's `world`): the share of people
on river cells and in each drawn biome at the end, and the ten cities
with the largest peak size, with their site's biome, discharge and
whether it is on the coast, on alluvium or at a delta.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from wsim.params import BIOMES  # noqa: E402
from wsim.runio import Run  # noqa: E402


def main(names):
    for name in names:
        run = Run(name)
        W, F = run.W, run.final
        p = F["pop"]
        river = F["river"].astype(bool) if "river" in F else W.river
        al = W.alluvial | getattr(W, "alluvium", W.alluvial)
        print(f"\n== {run.name} ({run.config.get('world', 'world.gpkg')}): "
              f"{p.sum() / 1e6:.1f}M people; on river cells "
              f"{p[river].sum() / p.sum():.3f} (land {W.area[river].sum() / W.area.sum():.3f})")
        print("  by drawn biome: " + ", ".join(
            f"{b} {p[W.biome == k].sum() / p.sum():.2f}" for k, b in enumerate(BIOMES)))
        c = run.cities.nlargest(10, "peak_size")
        k = c.cell.values.astype(int)
        t = pd.DataFrame({"lon": c.lon.values, "lat": c.lat.values,
                          "peak": c.peak_size.values.astype(int),
                          "biome": np.array(BIOMES)[W.biome[k]],
                          "Q m3/s": W.Q[k].round(0), "river": river[k],
                          "coast": W.coastal[k], "alluvium": al[k],
                          "delta": river[k] & W.coastal[k] & al[k]})
        print(t.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1:])
