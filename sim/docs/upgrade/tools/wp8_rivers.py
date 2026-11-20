"""WP8 stage B: how the river network changed between two world files.

    ~/.venvs/worldsim/bin/python docs/upgrade/tools/wp8_rivers.py \
        ../gis/world.gpkg ../gis/world_v2.gpkg

Prints river cells in each, cells gained and lost, river cells by drawn
biome, and the ten largest rivers (basins by outlet discharge) in each,
with where their outlets are and whether the other world has a river
reaching the sea within one cell of the same outlet.
"""
import sqlite3
import sys

import numpy as np
import pandas as pd

COLS = ["row", "col", "lon", "lat", "area_km2", "fic_land", "fic_biome",
        "syn_river", "syn_discharge_m3s", "syn_drainage_area_km2",
        "syn_basin_id", "syn_runoff_m_yr"]


def load(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    df = pd.read_sql(f"select {','.join(COLS)} from cells where fic_land = 1", con)
    con.close()
    return df.set_index(["row", "col"])


def largest(df, n=10):
    """Rivers by the discharge at their basin's outlet (the basin's largest
    discharge)."""
    r = df[df.syn_river == 1].reset_index()
    i = r.groupby("syn_basin_id").syn_discharge_m3s.idxmax()
    top = r.loc[i].nlargest(n, "syn_discharge_m3s")
    cells = r.groupby("syn_basin_id").size()
    top = top.assign(river_cells=top.syn_basin_id.map(cells).values)
    return top[["row", "col", "lon", "lat", "syn_discharge_m3s",
                "syn_drainage_area_km2", "river_cells"]]


def main(a, b):
    A, B = load(a), load(b)
    ra, rb = A.syn_river == 1, B.syn_river == 1
    print(f"river cells: {int(ra.sum())} -> {int(rb.sum())}; "
          f"gained {int((rb & ~ra).sum())}, lost {int((ra & ~rb).sum())}, "
          f"kept {int((ra & rb).sum())}")
    print(f"river share of land area: {A.area_km2[ra].sum() / A.area_km2.sum():.3f} -> "
          f"{B.area_km2[rb].sum() / B.area_km2.sum():.3f}")
    t = pd.DataFrame({"river cells before": A[ra].groupby("fic_biome").size(),
                      "after": B[rb].groupby("fic_biome").size(),
                      "runoff (m/yr) before, mean": A.groupby("fic_biome").syn_runoff_m_yr.mean(),
                      "after, p10": B.groupby("fic_biome").syn_runoff_m_yr.quantile(0.1),
                      "p50": B.groupby("fic_biome").syn_runoff_m_yr.median(),
                      "p90": B.groupby("fic_biome").syn_runoff_m_yr.quantile(0.9)})
    print("\nriver cells and runoff by drawn biome\n" + t.round(3).to_string())
    ta, tb = largest(A), largest(B)
    for name, top, other in (("before", ta, B), ("after", tb, A)):
        o = other[other.syn_river == 1].reset_index()
        hit = [bool(((o.row - r).abs() <= 1).mul((o.col - c).abs() <= 1).any())
               for r, c in zip(top.row, top.col)]
        print(f"\nten largest rivers, {name} (outlet; 'other' = a river cell within "
              "one cell of it in the other world)")
        print(top.assign(other=hit).round(1).to_string(index=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
