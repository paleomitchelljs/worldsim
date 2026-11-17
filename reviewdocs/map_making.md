# Plan for a single combined map

Goal: one map from `world.gpkg` and `sw300_seed101/` showing major geographic regions, large cities, important ports and major nations.

## Join keys

`cell` in `cities.csv` and `city_sizes.csv` is an index into the land-cell arrays of `final_state.npz`, not `row*720+col`. Cell 21725 resolves to row 229, col 169, which matches the stated lon -95.25, lat -24.75. Join to `world.gpkg` on `(row, col)`.

`final_state.npz` also carries `polity`, `people`, `pop`, `river`, `city_peak` and `flow_to`, so it is the backbone.

## Tooling

- Installed: matplotlib, pandas, PIL.
- Not installed: geopandas, shapely, rasterio, scipy, GDAL.
- Plan for a pure raster pipeline. Paint the 720 x 360 grid with matplotlib, draw polity borders from label differences between neighbouring cells, and read the gpkg through `sqlite3`.
- A gpkg-to-GeoJSON step is only needed for QGIS or an interactive web map later.

## Step 1: choose the snapshot

- Use year 7995 (final) for one map. A second map at about year 4000 shows how the layout changes.
- `history.npz` has 80 snapshots (about every 100 years) of `people`, `pop` and `polity`, so any of those years works for polities.
- `city_sizes.csv` is sampled every 25 years.

## Step 2: base layer

- Hillshade from `fic_elev_km`, tinted by `fic_biome` using the legend colours.
- Ocean shaded by depth.
- Rivers from `syn_river`, filtered to `syn_strahler >= 3` so they read at map scale.
- Coast from `syn_coast_status`.

## Step 3: major geographic regions

`syn_block` is useless for this. Gondwana is 51,247 of 66,895 land cells (77%). Build regions two ways:

- Connected components of `syn_setting` (craton, platform, passive margin, orogen, interior basin, volcanic arc), keeping those above a size threshold.
- Large drainage basins from `syn_basin_id`.

Label the 10 to 25 largest with spaced italic type. The source data has no region names, so either auto-name them ("Great Orogen", "Northern Basin") or output a CSV of region IDs for naming.

## Step 4: nations

- Take the top 15 to 25 polities by cells at the snapshot year from `final_state.npz`.
- Colour by ruling people (colours are in `run.json`).
- Draw borders where the polity label changes between neighbouring cells, thicker for the largest states.
- Place a label at the capital (`capital_lon`, `capital_lat` in `polities.csv`).
- Polity IDs are `P####`, not names. Add a name column to `polities.csv` (generated or supplied) before this step.
- `minority_people` in `final_state.npz` could drive hatching for multi-ethnic states.

## Step 5: large cities

- Take the top 40 to 60 cities by `size` at the snapshot year from `city_sizes.csv`.
- Join to coordinates through `cities.csv` (`lon`, `lat`) and symbolise by size on a log scale.
- Mark capitals with a ring.
- Show founding year in a small label only for the top 10.

## Step 6: important ports

- The `port` flag lives in `citygaps.csv` (per city-year, 0/1). Take cities with `port=1` and size in the top 25, plus the endpoints of `posts.csv` (92 trade posts, with `lon`, `lat`, `people_planter` and `people_host`).
- Mark with an anchor glyph.
- `trade_city` is saturated (range 1.414 to 1.5), so do not rank ports by it. Rank by size and by `syn_reach_productivity` or distance to a river mouth instead.

## Step 7: build and check

- Render at 4800 x 2400 px (about 3 px per cell) to PNG, with a legend and scale bar.
- Output a CSV of every plotted feature (ID, name, lon, lat, source column) so each mark traces to a data row.
- Spot-check 5 cities and 3 polity capitals against `final_state.npz` cells, and confirm every city falls on a land cell.
- Review for label collisions. This step needs a human pass.

## Open decisions

1. **Names.** Auto-generate names for regions, polities and cities, or output blank ID tables to fill in?
2. **Snapshot year.** Final (7995) only, or also a mid-era map?
3. **Size.** One dense reference map, or a poster plus per-region insets?

## Caveat

The cap finding in `REALISM_REVIEW.md` affects the map. If city sizes really top out near 50,000, the proportional symbols will all look similar, and the map will show that flatness rather than a clear urban hierarchy.
