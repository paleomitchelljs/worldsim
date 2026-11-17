# WP2: outputs and analysis

**Goal.** Make a run's history queryable and its measures comparable
across runs without rereading large files: structured events, one loader
for run folders, one metrics module, tidy tables, and exports that GIS
software reads directly. No mechanic changes.

**Why.**
- `events.txt` is free text. `chronicle.txt` is built from it by regular
  expressions (`P(\d+)\(`, `([\d.]+)M` in `wsim/output.py`), and the
  analysis scripts parse it again. A question such as "what happened
  within 500 km of this city between 3000 and 3400" cannot be asked.
- `realism.py`, `landmass_report.py`, `timeline.py`, `bigcities.py`,
  `turnover.py` and `figures.py` each read the CSVs in their own way.
- Cross-run comparison rereads 30-75 MB per run and fails when Dropbox has
  evicted a file.
- `timeseries.csv` has 321 columns keyed by people (`pop_Hum`, ...).
- `history.npz` and `final_state.npz` are indexed by land cell, so nothing
  outside the sim can read them.
- The review's measures (`BASELINE.md`) are in a one-off script.

Read first: `wsim/output.py`, `wsim/diagnostics.py` (`record`),
`realism.py`, `figures.py` (`world`, `rows`), `docs/running.md`,
`docs/diagnostics.md`, `docs/upgrade/tools/analyze_run.py`.

None of this should change what the simulation does. Testing: run the
new code on one finished run and read the output (`GUIDE.md`).

## Stage A: structured events

1. Extend `Sim.log(kind, text)` to `log(kind, text, **data)`. Store a dict
   per event: `year`, `kind`, `text`, and whichever of these the call site
   knows: `cell` (the place), `polities` (ids), `peoples` (keys),
   `lineages`, `cities` (ids), `n` (a magnitude: people dead, cities
   taken). Add `lon`, `lat` and the landmass code from `cell` when writing.
2. Go through the call sites (grep `self.log(` and `self.first(`; about a
   hundred) and pass the fields each already has in hand. Do not compute
   anything new for a log call.
3. Write `events.jsonl` (one JSON object per line). Keep writing
   `events.txt` from the same records.
4. Build `chronicle.txt` from the fields (state ids in `polities`,
   magnitudes in `n`) instead of regular expressions.
5. The counters in `self.cnt` (every event, including small ones) stay as
   they are.

## Stage B: run loader and metrics

1. `wsim/runio.py`: `Run(path)` with lazily loaded, cached tables
   (`timeseries`, `cities`, `polities`, `wars`, `sieges`, `revolts`,
   `events`, `city_sizes`, `cityfood`, `deaths`, `history`, `final`,
   `config`). It resolves bare names against the runs root, and reports a
   placeholder file (`ls -lO` shows `dataless`; `os.stat().st_blocks == 0`
   on a non-empty file is the test in code) as missing instead of hanging.
   Use pandas (already installed, already used by `realism.py`).
2. `wsim/metrics.py`: one function per measure, each taking a `Run` and
   returning a flat dict of numbers. Move in everything `realism.py`
   prints and `write_checks` computes, then add the review's measures,
   defined exactly as in `BASELINE.md`:
   - share of wars ending inside one tick; within 5 years; with 0-1 sieges;
   - peer-war share (both sides 5+ cities at the start);
   - siege win probability at launch: median and share below 0.1, **split
     by `side`** (attacker's sieges and counter-offensives separately;
     the baseline pooled them);
   - share of polities that never pass one city, and their median life;
   - state lifespans: median, share over 1,000 years, longest;
   - contiguity of the ten largest states at the end: pieces, and the
     largest piece's share, with pieces joined across water closer than
     the state's sailing range counted separately from land pieces;
   - share of cells whose people changed per 500 years, by window;
   - minority share of heads;
   - share of city food from trade, rent, provincial spending, capital;
   - population share by coast, river, alluvial fill, latitude band, biome;
   - log-population sd around its 200-year mean after year 3000; largest
     100-year fall; the same per landmass group (`landmasses.py`);
   - growth rate by millennium.
3. Cross-run measures, taking a list of runs: share of cells held by the
   same people, city sites within one cell, and correlation of
   log(1 + cell population), each with its chance level.
4. Write `metrics.json` at the end of every run (call the single-run
   functions from `write_outputs`). `realism.py` becomes a thin table
   printer over `metrics.json`, with `--rebuild` to recompute from the
   raw files.
5. Check on `al_seed103` that the new measures come out near
   `BASELINE.md`. Where one does not, find out which is wrong and correct
   `BASELINE.md`.

## Stage C: tidy tables

1. Add `timeseries_long.csv` (or Parquet if D4 allows `pyarrow`):
   `year, people, variable, value`, with `people = ALL` for world columns.
   Keep the wide `timeseries.csv`; `figures.py` and old scripts read it.
2. `polities.csv`: add `end_reason` (it is in the `kill_polity` call),
   `origin` (see WP5 stage A) and `capital_cell`.
3. `docs/running.md` and `docs/diagnostics.md`: one table of every output
   file with its columns and units. "Size" has meant three things
   (`size`, `size_old`, `cell_pop`); say which is which.

## Stage D: GIS export (needs U: D4)

`export.py RUN` writes, from `history.npz`, `final_state.npz` and the
CSVs, without rerunning anything:

1. **Raster, with time.** A NetCDF file (CF conventions; dimensions
   `time, lat, lon` on the full 360 x 720 grid; sea as the fill value)
   with `people`, `population`, `density`, `polity`, and from the final
   state `road`, `improvements`, `land`, `salt`. QGIS opens it as a mesh
   or raster with the temporal controller. Needs `xarray` + `netCDF4`.
2. **Vector.** A GeoPackage with:
   - `cities`: points with founded, ended, peak size, people, end reason,
     and `t_start` / `t_end` fields for the temporal controller;
   - `states`: one polygon (multi-polygon) per state per snapshot,
     dissolved from its cells, with id, people, cities, area and the
     snapshot year;
   - `roads`: cells with road stock over 0.3 at the end, as lines along
     the travel graph if cheap, else as cell polygons;
   - `events`: points from `events.jsonl` with kind, year and text.
   Needs `geopandas` + `shapely`. Cells are 0.5-degree squares in
   EPSG:4326; dissolve with `shapely.unary_union`.
3. A blank ID table for the map's names (`names.csv`: id, kind, lon, lat,
   peak size or area, empty `name` column). The book assigns names in its
   own pass; never fill that column.
4. Read both files back once with geopandas/xarray to see that they
   open and that city points fall on land.
