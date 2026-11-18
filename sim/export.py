"""
Export a finished run for GIS software (WP2 stage D, 2026-11-17).

    python export.py RUN [RUN ...] [--states-every 1] [--no-states]

Writes into <run>/export/, from history.npz, final_state.npz and the
CSVs, without rerunning anything:

- run.nc: NetCDF (CF-1.8) on the full 360 x 720 half-degree grid, sea as
  the fill value. Over time (the history.npz snapshots, every 100 years):
  people (index into run.json's peoples; -1 empty land), population
  (heads), density (heads per km2 of land), polity (state id; -1 none).
  At the end only: road, improvements, land, salt. QGIS opens it as a
  raster or mesh; time steps work with the temporal controller.
- run.gpkg: layers cities (points), states (one multipolygon per state
  per snapshot, dissolved from its cells), roads (lines between
  neighbouring cells whose road stock is over ROAD_MIN at the end),
  events (points for events with a place). Temporal layers carry
  t_start / t_end as DATETIME fields: the run's year as a calendar year,
  so year 3000 of the run is 3000-01-01. A range is [t_start, t_end):
  a state snapshot holds until the next snapshot, an event for one tick,
  and a city standing at the end until the run's last year.
- names.csv: one row per city, state and coded landmass with an empty
  `name` column. The book assigns names in its own pass; this script
  never fills that column.

Needs xarray + netCDF4 and geopandas + shapely (D4, U 2026-11-17).
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from wsim.params import NY, NX  # noqa: E402
from wsim.runio import Run  # noqa: E402
import landmasses as LM  # noqa: E402

ROAD_MIN = 0.3      # road stock drawn as a road (C)
FILL_INT = -9       # sea in the integer grids (-1 keeps its meaning: none)


def lonlat(row, col):
    """Cell centre of grid row, col (row 0 at the north edge)."""
    return -180 + 0.25 + 0.5 * np.asarray(col), \
        90 - 0.25 - 0.5 * np.asarray(row)


def dates(years):
    """Run years as DATETIME values (year Y -> Y-01-01), for QGIS's
    temporal controller. Python dates start at year 1, so year 0 (the
    run's opening events) is written as year 1."""
    return pd.Series(np.array([f"{max(int(y), 1):04d}-01-01"
                               for y in years],
                              dtype="datetime64[s]"))


def grid(vals, row, col, fill):
    """Land-cell values (..., N) onto the full grid (..., NY, NX)."""
    out = np.full(vals.shape[:-1] + (NY, NX), fill,
                  dtype=np.result_type(vals.dtype, np.asarray(fill).dtype))
    out[..., row, col] = vals
    return out


def write_netcdf(r, path):
    import xarray as xr
    H, F = r.history, r.final
    row, col = F["row"], F["col"]
    area = r.W.area
    years = H["year"].astype(int)
    lon, lat = lonlat(0, np.arange(NX))[0], lonlat(np.arange(NY), 0)[1]
    keys = r.keys
    pop = H["pop"].astype(np.float32)
    dens = (H["pop"] / np.maximum(area, 1e-9)).astype(np.float32)
    tdims, dims = ("time", "lat", "lon"), ("lat", "lon")
    ds = xr.Dataset(
        {
            "people": (tdims, grid(H["people"].astype(np.int16), row, col,
                                   np.int16(FILL_INT)),
                       dict(long_name="people holding the cell (index into "
                                      "the `peoples` attribute); -1 empty")),
            "population": (tdims, grid(pop, row, col, np.float32(np.nan)),
                           dict(long_name="population", units="1",
                                comment="heads (individuals)")),
            "density": (tdims, grid(dens, row, col, np.float32(np.nan)),
                        dict(long_name="population density",
                             units="km-2",
                             comment="heads per km2 of the cell's land")),
            "polity": (tdims, grid(H["polity"].astype(np.int32), row, col,
                                   np.int32(FILL_INT)),
                       dict(long_name="state id (polities.csv); -1 none")),
            "year": (("time",), years,
                     dict(long_name="year of the run")),
        },
        coords=dict(
            time=("time", (years - 1) * 365,
                  dict(standard_name="time", units="days since 0001-01-01",
                       calendar="noleap", axis="T")),
            lat=("lat", lat, dict(standard_name="latitude",
                                  units="degrees_north", axis="Y")),
            lon=("lon", lon, dict(standard_name="longitude",
                                  units="degrees_east", axis="X"))),
        attrs=dict(Conventions="CF-1.8", title=f"worldsim run {r.name}",
                   source="worldsim export.py (WP2 stage D)",
                   peoples=" ".join(keys),
                   comment="sea cells hold the fill value"))
    for k, what in (("road", "road stock (0-1)"),
                    ("improvements", "land improvements (0-1)"),
                    ("land", "land condition (1 = unspoilt)"),
                    ("salt", "salinization (0-1)")):
        ds[k] = (dims, grid(F[k].astype(np.float32), row, col,
                            np.float32(np.nan)),
                 dict(long_name=f"{what} at the end of the run",
                      comment=f"year {int(r.config.get('year_reached', 0))}"))
    enc = {v: dict(zlib=True, complevel=4) for v in ds.data_vars}
    for v in ("people", "polity"):
        enc[v]["_FillValue"] = FILL_INT
    for v in ("population", "density", "road", "improvements", "land",
              "salt"):
        enc[v]["_FillValue"] = np.float32(np.nan)
    enc["time"] = dict(dtype="int32")
    ds.to_netcdf(path, encoding=enc, engine="netcdf4")


def cells_poly(row, col):
    import shapely
    lon, lat = lonlat(row, col)
    return shapely.box(lon - 0.25, lat - 0.25, lon + 0.25, lat + 0.25)


def states_layer(r, every):
    """One multipolygon per live state per snapshot, dissolved from its
    cells (shapely coverage union: the cells tile, never overlap)."""
    import shapely
    H, F = r.history, r.final
    row, col, area = F["row"], F["col"], r.W.area
    boxes = cells_poly(row, col)
    years = H["year"].astype(int)
    last = int(r.config.get("year_reached") or years[-1])
    st = pd.DataFrame({k: H[f"st_{k}"] for k in
                       ("t", "id", "cap", "people", "cities")})
    keys = r.keys
    rows, geoms = [], []
    for t in range(0, len(years), every):
        pol = H["polity"][t]
        pop = H["pop"][t]
        m = pol >= 0
        if not m.any():
            continue
        cells = np.nonzero(m)[0]
        order = cells[np.argsort(pol[cells], kind="stable")]
        ids, starts = np.unique(pol[order], return_index=True)
        info = st[st.t == t].set_index("id")
        # each snapshot holds until the next; the last for one step
        step = int(years[1] - years[0]) if len(years) > 1 else 100
        t_end = years[t + every] if t + every < len(years) else \
            max(last, int(years[t])) + step
        for pid, grp in zip(ids, np.split(order, starts[1:])):
            geoms.append(shapely.coverage_union_all(boxes[grp]))
            s = info.loc[pid] if pid in info.index else None
            rows.append(dict(
                state=int(pid), year=int(years[t]),
                people=keys[int(s["people"])] if s is not None else "",
                cities=int(s["cities"]) if s is not None else 0,
                capital_cell=int(s["cap"]) if s is not None else -1,
                cells=len(grp), area_km2=round(float(area[grp].sum())),
                population=round(float(pop[grp].sum())),
                t0=int(years[t]), t1=int(t_end)))
    return rows, geoms


def write_gpkg(r, path, every, states=True):
    import geopandas as gpd
    import shapely
    if os.path.exists(path):
        os.remove(path)
    last = int(r.config.get("year_reached") or r.history["year"][-1])

    def layer(df, geom, name):
        if "t0" in df:
            df["t_start"], df["t_end"] = dates(df.pop("t0")), \
                dates(df.pop("t1"))
        gpd.GeoDataFrame(df, geometry=geom, crs="EPSG:4326").to_file(
            path, layer=name, driver="GPKG")

    c = r.cities
    end = c["ended"].fillna(last).astype(int)
    layer(pd.DataFrame(dict(
        id=c["id"], cell=c["cell"], people=c["people"],
        founded=c["founded"], ended=c["ended"].astype("Int64"),
        end_reason=c["end_reason"].fillna(""), peak_size=c["peak_size"],
        peak_year=c["peak_year"], t0=c["founded"], t1=end)),
        shapely.points(c["lon"], c["lat"]), "cities")

    if states:
        rows, geoms = states_layer(r, every)
        if rows:
            layer(pd.DataFrame(rows), geoms, "states")

    # roads: lines between neighbouring cells both over ROAD_MIN
    F, W = r.final, r.W
    road = F["road"]
    lon, lat = W.lon, W.lat
    a = np.repeat(np.arange(W.N), W.nb.shape[1])
    b = W.nb.ravel()
    ok = (b > a) & (road[a] > ROAD_MIN) & (road[np.maximum(b, 0)] > ROAD_MIN)
    a, b = a[ok], b[ok]
    ok = np.abs(lon[a] - lon[b]) < 180          # not across the date line
    a, b = a[ok], b[ok]
    if len(a):
        lines = shapely.linestrings(
            np.stack([np.stack([lon[a], lat[a]], 1),
                      np.stack([lon[b], lat[b]], 1)], 1))
        layer(pd.DataFrame(dict(
            cell_a=a, cell_b=b,
            road=np.round(np.minimum(road[a], road[b]), 3))), lines, "roads")

    e = r.events
    dt = int(r.config.get("dt", 5))     # an event lasts one tick
    if "lon" in e:
        e = e[e["lon"].notna()].reset_index(drop=True)
        lists = lambda col: e[col].map(
            lambda v: " ".join(map(str, v)) if isinstance(v, list) else "") \
            if col in e else ""
        layer(pd.DataFrame(dict(
            year=e["year"].astype(int), kind=e["kind"], text=e["text"],
            cell=e["cell"].astype(int), polities=lists("polities"),
            peoples=lists("peoples"), cities=lists("cities"),
            n=e["n"] if "n" in e else np.nan,
            landmass_code=e.get("landmass_code", ""),
            t0=e["year"].astype(int), t1=e["year"].astype(int) + dt)),
            shapely.points(e["lon"], e["lat"]), "events")


def write_names(r, path):
    """Blank names table: cities, states and the coded landmasses."""
    c, p, W = r.cities, r.polities, r.W
    rows = [dict(id=int(x.id), kind="city", lon=x.lon, lat=x.lat,
                 size=x.peak_size, size_unit="peak urban fe", name="")
            for x in c.itertuples()]
    rows += [dict(id=int(x.id), kind="state", lon=x.capital_lon,
                  lat=x.capital_lat, size=x.peak_km2,
                  size_unit="peak km2", name="")
             for x in p.itertuples()]
    for lm, code in LM.CODES.items():
        m = W.landmass == lm
        rows.append(dict(id=code, kind="landmass",
                         lon=round(float(W.lon[m].mean()), 2),
                         lat=round(float(W.lat[m].mean()), 2),
                         size=round(float(W.area[m].sum())),
                         size_unit="km2", name=""))
    pd.DataFrame(rows).to_csv(path, index=False)


def check(out):
    """Read both files back: they open, and city points fall on land."""
    import geopandas as gpd
    import pyogrio
    import xarray as xr
    with xr.open_dataset(os.path.join(out, "run.nc")) as ds:
        t = ds.sizes["time"]
        last = ds["people"].isel(time=-1)
        land = ds["land"].notnull()
        cities = gpd.read_file(os.path.join(out, "run.gpkg"),
                               layer="cities")
        on = land.sel(lon=xr.DataArray(cities.geometry.x.to_numpy()),
                      lat=xr.DataArray(cities.geometry.y.to_numpy()),
                      method="nearest").to_numpy()
        print(f"  run.nc: {t} snapshots, {int(land.sum())} land cells, "
              f"{int((last >= 0).sum())} occupied at the end")
    gp = os.path.join(out, "run.gpkg")
    layers = pyogrio.list_layers(gp)
    print("  run.gpkg: " + ", ".join(
        f"{n} {pyogrio.read_info(gp, layer=n)['features']}"
        for n, _ in layers))
    print(f"  cities on land: {int(on.sum())} of {len(on)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--states-every", type=int, default=1,
                    help="snapshots between state-polygon layers")
    ap.add_argument("--no-states", action="store_true")
    ap.add_argument("--no-check", action="store_true")
    a = ap.parse_args()
    for name in a.runs:
        r = Run(name)
        out = os.path.join(r.dir, "export")
        os.makedirs(out, exist_ok=True)
        print(r.name)
        write_netcdf(r, os.path.join(out, "run.nc"))
        write_gpkg(r, os.path.join(out, "run.gpkg"), a.states_every,
                   not a.no_states)
        write_names(r, os.path.join(out, "names.csv"))
        if not a.no_check:
            check(out)
        print(f"  -> {out}")


if __name__ == "__main__":
    main()
