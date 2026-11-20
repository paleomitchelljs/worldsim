"""Clean biome map of a world file: the climate biomes (syn_biome) with
light relief shading, rivers, lakes and a legend of areas.

    python biome_map.py ../gis/world_v2.gpkg ../gis/qa/biome_map.png
"""
import sqlite3
import sys

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LightSource
from matplotlib.patches import Patch

NY, NX = 360, 720
BIOMES = [("Jungle", "#2f6b34"), ("Temperate forest", "#7fa35a"),
          ("Grassland", "#c9cf86"), ("Desert", "#e3c48f"),
          ("Tundra", "#d9dcd6")]
OCEAN, SEA_ICE, LAKE, RIVER = "#a9c4d8", "#e8eef2", "#5f8fb8", "#3c6e9e"


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255


def main(gpkg, out):
    con = sqlite3.connect(gpkg)
    d = pd.read_sql("select row, col, area_km2, fic_elev_km, fic_sea_ice, "
                    "syn_lake, syn_biome from cells", con)
    grid = lambda c: d.pivot(index="row", columns="col", values=c).to_numpy()
    biome = grid("syn_biome")
    land = pd.notna(biome)
    elev = grid("fic_elev_km").astype(float)

    img = np.tile(rgb(OCEAN), (NY, NX, 1))
    img[grid("fic_sea_ice").astype(bool) & ~land] = rgb(SEA_ICE)
    for name, col in BIOMES:
        img[biome == name] = rgb(col)
    # relief shading on land only, gentle so the biome colours stay true
    shade = LightSource(azdeg=315, altdeg=45).hillshade(
        np.where(land, np.clip(elev, 0, None), 0), vert_exag=40)
    k = np.where(land, 0.75 + 0.25 * shade, 1.0)[..., None]
    img = np.clip(img * k, 0, 1)
    img[grid("syn_lake").astype(bool)] = rgb(LAKE)

    ext = (-180, 180, -90, 90)
    fig, ax = plt.subplots(figsize=(16, 8.6))
    ax.imshow(img, extent=ext, interpolation="nearest")
    ax.contour(np.linspace(-180, 180, NX), np.linspace(90, -90, NY),
               land.astype(float), [0.5], colors="#3a3a3a", linewidths=0.4)
    rivers = gpd.read_file(gpkg, layer="rivers")
    for s, g in rivers.groupby("strahler"):
        g.plot(ax=ax, color=RIVER, linewidth=0.35 + 0.35 * s)

    area = {n: d.loc[d.syn_biome == n, "area_km2"].sum() / 1e6
            for n, _ in BIOMES}
    total = sum(area.values())
    handles = [Patch(color=c, label=f"{n}  {area[n]:.1f}M km²  "
                     f"({100 * area[n] / total:.0f}%)") for n, c in BIOMES]
    handles += [Patch(color=LAKE, label="Lake"),
                plt.Line2D([], [], color=RIVER, lw=1.2, label="River")]
    ax.legend(handles=handles, loc="lower left", fontsize=9, framealpha=0.9)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xticks(range(-180, 181, 30))
    ax.set_yticks(range(-90, 91, 30))
    ax.grid(color="white", lw=0.3, alpha=0.5)
    ax.tick_params(labelsize=8)
    ax.set_title("Biomes of world_v2 (climate model)", fontsize=13)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(out, {n: round(a, 1) for n, a in area.items()})


if __name__ == "__main__":
    main(*sys.argv[1:3])
