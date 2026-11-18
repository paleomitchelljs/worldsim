# Running

Environment: `~/.venvs/worldsim` (Python 3.12 with numpy, scipy, pillow and
matplotlib). The map is opened read-only through sqlite3, so geopandas isn't
needed.

## Where runs go

Runs go in the runs root: `$WORLDSIM_RUNS` if set, else `sim/runs/`
(D2, U, 2026-11-17; git ignores it). `--out NAME` with no `/` puts the
run in the root; a path is used as given. `realism.py`, `figures.py`,
`landmass_report.py`, `timeline.py`, `bigcities.py` and `turnover.py`
take either a bare run name (`base_seed101`, or a quoted pattern
`'base_seed10?'`), looked up in the root, or a path. `snapcheck.py` does
the same for its saved-state file. The lookup is in `runroot.py`.

`World()` caches the world file's cell columns in the runs root as
`_world_cache.npz` (about 83 MB), keyed on the file's path, size and
modification time, and rebuilds it when any of them changes (2026-11-17).
A load from the cache takes about 1.7 s, against 3.8 s from SQLite.

The runs made before 2026-11-17 (446 folders, many online-only) stay in
the old Dropbox folder `Dropbox/Personal/_book/art/world/sim/runs/` (D3,
U); give their full path to read them.

Current scenario (ten peoples, head starts):

    ~/.venvs/worldsim/bin/python worldsim.py --peoples peoples_headstart \
        --starts 20 --start-vary 0.1 --seed 91 --years 6400 --vary 0.12 \
        --out terrain_seed91

An 8,000-year run (seed 101, the sweep's settings) takes about 14 minutes
with two running side by side (2026-11-07; 23 minutes before that day's
speed-ups). The machine has 4 performance and 4 efficiency cores, so
runs beyond about 8 at once only queue.
The same seed gives the same history. Since WP1 stage F (2026-11-17)
each subsystem draws from its own named stream (`geo.stream`: start,
migrate, famine, raid, war, diplomacy, revolt, succession, climate,
dragons, rulers, city_culture and so on), seeded from the run seed and
the stream's name. A change that alters how often one subsystem draws
leaves every other stream's draws as they were, though the history
still diverges once the changed subsystem's effects reach the others.
Runs from before stage F do not repeat under the same seed. From 2026-11-07 the climate no
longer depends on `--years`, so a shorter run of a seed is the start of a
longer one's climate (the rest of the history matches only while nothing
else differs).

## Checking that a change leaves runs unchanged (`snapcheck.py`)

A test from year 0 reaches few cities, wars or voyages before year
3000 (seed 101: no war before 1590, 19 by 3000), so a 1,500-year check
says little about that code. `snapcheck.py` saves a late-game state once
and runs a few ticks from it under two versions of the code, comparing a
digest of every part of the state:

    ~/.venvs/worldsim/bin/python snapcheck.py save /tmp/s5000.pkl --year 5000 -- \
        --peoples peoples_regional --starts 20 --start-vary 0.1 --vary 0 \
        --sites sites_v2.json --seed 101 --years 8000
    ~/.venvs/worldsim/bin/python snapcheck.py run /tmp/s5000.pkl --ticks 20 --code OLD --digest old.json
    ~/.venvs/worldsim/bin/python snapcheck.py run /tmp/s5000.pkl --ticks 20 --digest new.json
    ~/.venvs/worldsim/bin/python snapcheck.py diff old.json new.json

The state is about 300 MB at year 5000; git ignores `*.pkl`. `OLD` is
a folder holding a copy of `wsim/` and the roster modules, with the map
at `OLD/../gis/world.gpkg`. A whole-run check is still worth doing for a
change that touches the early years.

## Branching from a saved state

Early millennia cost as much as late ones, so variants that differ only
after some year can share the run up to it (WP1 stage E, 2026-11-17, C).

    # once: the base run, saving states on the way
    ~/.venvs/worldsim/bin/python worldsim.py --peoples peoples_regional \
        --starts 20 --start-vary 0.1 --vary 0 --sites sites_v2.json \
        --seed 101 --years 8000 --frame-every 100 --out base_seed101 \
        --save-state 3000 s101_y3000.pkl --save-state 5000 s101_y5000.pkl
    # each variant
    ~/.venvs/worldsim/bin/python worldsim.py --from-state s101_y5000.pkl \
        --set PATH_PIVOT=0.45 --out var_pivot045_seed101

- A bare `PATH` is in the runs root, like `--out`. A path inside Dropbox
  is refused. States are about 250 MB at year 1,500 and 450 MB at year
  5,500 (seed 101); git ignores `*.pkl`. The travel and food distance
  caches are left out of the file and rebuilt, to the same values, when
  asked.
- With `--from-state`, `--set`, `--city-pop`, `--city-cap` and
  `--dragon-*` take effect from the branch year. `--off` switches
  mechanics off from the branch year. A mechanic that was off in the
  state cannot be switched on. `--years` and `--frame-every` default to
  the state's. The founding options (`--seed`, `--peoples`, `--starts`,
  `--vary` and the rest) are the state's and are ignored. So is a
  constant that was read only at setup: the climate series, the sites,
  the founders' placement.
- `--branch-seed N` starts every random stream afresh from seed N at
  the branch year, for replicates from one state. Whatever was drawn at
  setup stays as saved: the climate's series and abrupt events, sites
  and founders. A branch's local climate noise and river avulsions
  change, though, because they are drawn each tick.
- The branch's tables hold the whole history, from year 0, and so do its
  `history.npz` and `history.mp4`. Its `frames/` cover only the years
  after the branch. `run.json` gains
  `branch`: the state file, the branch year, the `--set` and `--off`
  given, every constant whose value changed (old and new), the end year,
  and the run.json of the run that saved the state, as of the save.
- A branch with no changes reproduces the run that saved the state
  exactly (checked: seed 101, saved at 1,500, run to 2,000, all tables
  byte-identical). Unpickling rebuilds Python sets, and their iteration
  order can differ from the originals', which changes the history. So a
  run carries on from its own saved copy after each save. A run that
  saves a state can therefore differ, after the save year, from the same
  run without `--save-state`. Compare branches with branches, or with
  the run that saved them.
- **Switch-on transients.** A mechanic or constant changed at the branch
  year needs time to settle; the urban batch showed one. Branch at least
  500 years before the period you compare. Never use branching for a
  mechanic that acts from year 0, such as settlement, growth rates or
  founders.

## Options

| Option | Default | Meaning |
|---|---|---|
| `--seed` | 1 | random seed |
| `--years` | 6000 | length; use 6400 with `peoples_headstart` so latecomers get 6000 |
| `--frame-every` | 20 | ticks between animation frames |
| `--hist-every` | 5 | ticks between `history.npz` snapshots (WP3 stage A; was 20) |
| `--no-video` | off | do not draw `history.mp4` at the end |
| `--peoples` | `peoples` | roster module ([scenarios.md](scenarios.md)) |
| `--vary` | 0 | per-run jitter of each people's cultural traits ([startup.md](startup.md)) |
| `--starts` | 3 | founding groups per people |
| `--start-vary` | 0.05 | jitter of each founding group's cultural traits |
| `--start-mode` | `wander` | `wander` or `score` founder placement ([startup.md](startup.md)) |
| `--wander-steps` | 2000 | steps of the pre-run wander |
| `--start-pool` | 0.02 | `score` mode only: share of good cells a founder may pick |
| `--homelands` | `continents` | founders only on large landmasses; `anywhere` lifts it |
| `--cluster-km` | 0 | `score` mode only: keep a people's groups near its first |
| `--drift` | 0.06 | cultural mutation at secession and sea colonies |
| `--settle-drift` | 0.03 | cultural mutation when settling a new 5-degree region |
| `--size-food` | `kleiber` | food per head = size^0.75; `none` = all eat alike |
| `--city-pop` | 6000 | food-equivalent people that found a city |
| `--city-cap` | off | turn on the city cap = city-pop x (CAP0 + CAP1 x admin^2); runs before `nocap_*` used 3 40 |
| `--dragon-shun` | 0 | dragons do not settle near cells holding this share of their ward size (0 = off) |
| `--dragon-penalty` | 0.036 | cut in the yearly growth rate per unit of dragon hazard at the worst group size ([structural.md](structural.md#dragons-dragons)); replaced `--dragon-kill` |
| `--off` | none | structural mechanics to switch off, comma-separated, or `all` ([structural.md](structural.md)) |
| `--on` | none | optional mechanics to switch on (`params.OPTIONAL`: `trade_debit`, WP4 stage B); also on a branch ([switch-inventory.md](switch-inventory.md#optional-switches-off-unless-named-in---on)) |
| `--out` | `seed<N>` | output folder; a bare name goes in the runs root |
| `--save-state YEAR PATH` | none | save the whole Sim after the tick that reaches YEAR (repeatable); see [Branching](#branching-from-a-saved-state) |
| `--from-state PATH` | none | continue a saved state as a new run; see [Branching](#branching-from-a-saved-state) |
| `--branch-seed N` | the state's | with `--from-state`: fresh random streams from seed N after the branch year (replicates from one state) |

With `--off all --city-cap 3 40` the model reproduces the pre-structural one draw for draw
(checked: identical `events.txt` and `polities.csv` over 1,500 years, seed
91). The archived copy is `archive/worldsim_2026-10-29_pre_structural.py` in git commit 3338050 (see `archive/README.md`).

## Outputs (per run folder)

From 2026-11-17 the run writes as it goes (`wsim/output.py`, `Stream`).
Each frame is saved to `frames/` when it is rendered. Every `FLUSH_EVERY`
ticks (C: 100 ticks, 500 years) and at the end, the append-only tables
(`events.txt`, `events.jsonl`, `timeseries.csv`, `timeseries_long.csv`,
`city_sizes.csv`, `sieges.csv`,
`revolts.csv`, `relations.csv`, `price.csv`, `cityfood.csv`, `deaths.csv`,
`food.csv`, `citylevel.csv`, `citygaps.csv`, `citytraits.csv`, `lineage_events.csv`,
`lineage_pairs.csv`) get their new rows. `wars.csv`, `rulers.csv`,
`cities.csv`, `polities.csv`, `lineages.csv`, `dragons.csv`, `posts.csv`,
`history.npz` and `run.json` are rewritten under a temporary name and then
renamed into place. A killed run therefore keeps readable tables up to its
last flush, and `run.json`'s `year_reached` says how far that was.
`realism.py` reads such a partial run. The rest is written only when the
run ends: `history.mp4`, `final_maps.png`, the plots, `traits.txt`,
`chronicle.txt`, `checks.txt`, `final_state.npz` and `figures.py`'s
figures.

| File | What |
|---|---|
| `history.mp4` | the run as video (WP3 stage D, 2026-11-17): states above peoples, Mollweide, one frame per `history.npz` snapshot (25 years), 8 frames a second, with the turnover strip; drawn by `render_run.py` at the end of the run (about 10 s for 3,000 years, 30 s for 8,000). `--no-video` skips it |
| `viewer.html` | the run in one self-contained page (WP3 stage D, U 2026-11-17; `viewer.py`, below): open it in a browser |
| `frames/`, `final_maps.png` | the frames drawn while the run goes (every `--frame-every` ticks) and the last of them. The top panel shows states, the bottom peoples by density (red dots: dragons). Dots are cities; ringed dots are capitals. `history.gif`, made from these frames, was dropped on 2026-11-17 (U) in favour of `history.mp4` |
| `final.png` | 2x2 summary (`figures.py`, 2026-11-01): states; peoples by density; peoples in flat colours with trading posts standing at the end (stars, in the merchants' colour) and the 12 strongest trade links between (landmass, people) groups at the last frame (width = summed trade tie; arrowhead from the merchants' home to the host where posts show a direction); major wars per 250 years by landmass group |
| `wars.png` | major wars per 250 years on each landmass (S, W1, W2, W3-W5, N1, N2-N4, E1), one line per pair of peoples (top 4 per panel), with large states that collapsed in revolt as triangles. Major war (C): both sides held 5+ cities at the start and 2+ cities were taken, or a side holding 10+ cities fell; placed at the defender's capital. Revolt collapse (C): a state loses 5+ cities and 40%+ of its cities to revolts in one tick |
| `trade.png` | the peoples-and-trade panel of `final.png`, full size (2026-11-04) |
| `history.npz` | map snapshot every `--hist-every` ticks (default HIST_EVERY = 5, 25 years, from WP3 stage A, 2026-11-17; 100 years before). Per cell, as (snapshot, cell) arrays: `people` (int8, -1 empty), `lineage` (int32), `polity` (int32, -1 none), `minority` (people of the cell's minority, int8), `pop_log1p` (float16 of log(1 + heads); `wsim.runio.load_history` adds `pop` = expm1 as float32; within 0.5%), `herding` (bool). Per snapshot, flat tables with their snapshot index (`*_t`): live states (`st_id, st_cap, st_people, st_cities`), trade ties (`tie_a, tie_b, tie`), cities (`city_cell, city_id, city_size` in urban fe, `city_polity, city_capital`). `year` gives each snapshot's year. Runs before WP3 stage A hold only `year, people, pop, polity` and the state and tie tables. While a run goes, each flush writes its new snapshots to `history_parts/`; the end joins them into `history.npz` and deletes the folder, and `load_history` reads the parts of a killed run. Reads state only, so it does not change a run |
| `war01.png` ... `war24.png` | the 24 most important wars (C: cities of the smaller side at the start x (1 + cities captured), so a clash of powers outranks an empire swallowing a city), in order of start, each on the peoples map at the snapshot nearest its start: both states outlined (attacker red, defender amber), a line between the capitals in two halves whose widths follow each side's cities, an arrowhead at the loser's capital and a star on the winner's (none for a draw), a zoomed inset when the war is small; the title gives the outcome and net cities. Winner: attacker if the defender fell, submitted, ceded or the goal was met; defender if the attacker fell or was repulsed; else a draw. Net cities = captures + a ceded city - recaptures. Needs `history.npz` |
| `tradewars.gif` | one frame per snapshot: peoples map, the 16 strongest trade links between (landmass, people) groups (width = summed tie), and every war fought since the previous snapshot, one line per pair of states: the 20 most important pairs drawn as in `war*.png` (borders, start year and the winner's net cities for the top 8), the rest as faint lines. Needs `history.npz` |
| `posts.csv` | trading posts standing at the end: planter, host, city, year planted, peoples |
| `lineages.png` | final map. Hue = people, shade = lineage. |
| `legacy.png` | every city that ever stood, plus the peak extent of the largest states |
| `population.png` | population, cities, number of states and size of the largest state over time |
| `violence.png` | population-weighted mean violence and tolerance over time, for the world and each people |
| `chronicle.txt` | major events: world-firsts, great plagues and droughts (2M+ people, from the event's `n`), events naming one of the 15 largest states (from its `polities`), fusions, extinctions |
| `events.txt` | every logged event, as text: year, kind, text |
| `events.jsonl` | the same events, one JSON object per line (WP2 stage A, 2026-11-17): `year`, `kind`, `text`, and what the event knows of `cell` (land-cell index), `polities` (state ids, the actor first: attacker, rebel, conqueror), `peoples` (keys such as `Hum`), `lineages` (ids), `cities` (city ids, as in `cities.csv`), `n` (a magnitude: people dead for plague, people under drought, peak cities for a fall, cities taken in a revolt, heirs in a partition, landmass km² for a voyage, years for a dry spell, cells losing a river); with a cell, also `lon`, `lat` (cell centre), `landmass` (id) and `landmass_code` (`landmasses.py`; none under 0.05M km²) |
| `traits.txt` | the traits actually used: people base values plus each founding group |
| `lineages.csv` | every lineage, with parent, origin, traits and the technology stage reached |
| `cities.csv`, `polities.csv` | lon/lat, founding and end years, peaks, rulers, peoples ruled (loads into QGIS) |
| `timeseries_long.csv` | the same numbers as `timeseries.csv`, one per row: `year, people, variable, value` (WP2 stage C, 2026-11-17). A column named `<variable>_<key>` gives that people (`pop_Hum`: people `Hum`, variable `pop`); `<variable>_world` and every other column give `people = ALL`. Empty values are left out. Older runs: `Run(name).timeseries_long` melts their wide table the same way |
| `timeseries.csv`, `final_state.npz` | per-tick statistics; final per-cell grid (row/col match `cells`), including roads, improvements, land condition, rivers and the drainage network as it ended |
| `run.json` | the settings of the run, including the mechanics switched on. From 2026-11-17 also `code` (git commit and whether tracked files differed from it), `command` (the full command line), `python` and `numpy` versions, `wall_seconds` (from start to the last write of `run.json`), `year_reached`, and `constants`: every numeric constant in `wsim/params.py` as used, after `--set` and the other overrides. A run started with `--from-state` also has `branch` ([Branching](#branching-from-a-saved-state)) |
| `price.csv` | Price-equation decomposition of each cultural trait, per century, per people and world-wide ([diagnostics.md](diagnostics.md)) |
| `dragons.csv` | every dragon: birth, first home, end, fate, ally (with `dragons`) |
| `relations.csv` | every pair of neighbouring live states on each frame tick: similarity, enmity and faith motives both ways, trade tie, war, alliance, truce, and `similarity_lin` (the ruling lineages'). From 2026-11-07 similarity and motives are those the war rule reads (the states' cultures under `city_culture`); before, they were always the ruling lineages', so they did not show what drove wars |
| `city_sizes.csv` | every city and ruin every 25 years ([structural.md](structural.md#city-histories-bookkeeping-only)); from 2026-11-09 `size` is the urban population and `size_old` the old 0.08/0.04 formula ([diagnostics.md](diagnostics.md#records-of-2026-11-09)) |
| `cityfood.csv` | every city every 25 years: where its food comes from (land, trade, rent, provincial tax, the capital's take) and its urban population (2026-11-09) |
| `deaths.csv` | deaths per century by people and cause (2026-11-09) |
| `food.csv` | the food ledger (WP4 stage A, 2026-11-17): per century, for the world, each people and each state, what was produced, eaten, taken, lost in carriage, received and created (below; [diagnostics.md](diagnostics.md#food-ledger-foodcsv)). Only with `food_flow` on |
| `checks.txt` | the run against rough historical regularities, plus a summary of `price.csv` ([diagnostics.md](diagnostics.md)); since 2026-11-17 formatted from `metrics.json`, its city rank-size from the last `city_sizes.csv` year |
| `metrics.json` | every measure of `wsim/metrics.py` (WP2 stage B, 2026-11-17), as `{function: {measure: value}}`, computed from the files above at the end of the run; `_missing` names measures whose files were absent ([diagnostics.md](diagnostics.md#run-measures-wsimmetricspy-2026-11-17)) |

Analysis tools: `realism.py RUNS [--group] [--only wars,sieges]`
prints each run's `metrics.json` side by side
([diagnostics.md](diagnostics.md#run-measures-wsimmetricspy-2026-11-17)).
A run without one (older runs, or a run still going, measured up to its
last flush) is measured from its files; `--rebuild` forces that, `--save`
writes the result into the run, and `--cross` prints the pairwise
final-map measures instead. Scripts read run folders through
`wsim.runio.Run(name)`, which reads each table once and reports a file
Dropbox has made online-only as missing (reading one can hang).
`landmasses.py` holds short codes per landmass (S, W1-W5,
N1-N4, E1, X1-X4; groups S, W, N, E, X) and draws `docs/landmass_key.png`.
`landmass_report.py RUNS --lm W` reports peoples, cities, states, wars,
relations, culture, revolts, successions and trading posts for a group of
landmasses. `timeline.py RUN --landmass W1,W2` takes the same codes.
`figures.py RUNS` rebuilds `final.png`, `wars.png`, `trade.png` and (with `history.npz`) the war maps and `tradewars.gif` for finished runs
(runs before 2026-11-01 lack `posts.csv`; their posts are rebuilt from
the events still standing at the end).

## Drawing a finished run (`render_run.py`)

`render_run.py RUN` (WP3 stage B, 2026-11-17) draws a run's maps from
`history.npz`, `run.json` and the cached world, without rerunning or
importing the simulation step. An 8,000-year run with 25-year snapshots
takes about 30 s: 320 frames, a 3.4 MB MP4.

| Option | Default | Meaning |
|---|---|---|
| `--layer` | `states,peoples` | one or more of `states`, `peoples`, `density` (heads per km², log scale 0.1-1,000), `lineages` (hue = people, shade = lineage; runs from WP3 stage A), `state_age` (ruled cells by years since they last changed state, from bright yellow, under 25 years, to dark purple, 2,000+; borders drawn), `people_age` (occupied cells by years since their people last changed, same scale), stacked top to bottom |
| `--no-strip` | off | leave out the turnover strip. With `states` or `state_age`, a strip under the maps shows, for each landmass group (S, W, N, E, X), the share of ruled cells whose state differs from 100 years before, over the whole run, with the frame's year marked |
| `--proj` | `mollweide` | `mollweide` (equal-area) or `platecarree` (the raw grid, as `final_maps.png` and the book's source maps) |
| `--format` | `mp4` | `mp4` (H.264, yuv420p), `gif`, or `png` frames in a folder |
| `--every` | 1 | snapshots between frames |
| `--from-year`, `--to-year` | all | the span drawn |
| `--scale`, `--fps` | 2 (4 with `--landmass`), 8 | pixels per grid cell (across); frames per second |
| `--landmass` | whole map | only one landmass group or code (`landmasses.py`: S, W, N, E, X, or W1, ...), cropped to its box; a group across the date line gets the whole width |

The ten largest states (150+ cells) are labelled at the centre of their
largest piece, not at the capital. A label that would overlap one
already placed is left out. The live frames do the same.

It writes `<run>/render/<layers>_<proj>[_<landmass>].<format>`. States are coloured
by `wsim/colors.py`. Each state keeps one colour for its whole life, in
its people's family of hues, and differs from every state it ever
borders and from its parent. The live frames (`frames/`,
`final_maps.png`) still use the colour each state drew at founding.
What `history.npz` lacks, the offline frames lack: no dragons, no
lineage counts or technology stages in the header, and for runs before
WP3 stage A no city dots. The war count in the header comes from
`wars.csv`.

Mollweide is drawn by inverse-projecting every output pixel once to a
grid cell (closed form), so a frame is one array lookup. City dots and
labels go through the forward projection, and borders are found on the
projected image, so they stay one pixel wide. The map keeps the
latitudes of the plate carrée crop.

## Reading a run in the browser (`viewer.py`)

`viewer.py RUN [--every-years 25]` (WP3 stage D, U 2026-11-17) writes
`<run>/viewer.html`, one file that needs no server or network. Each run
writes it at its end (about 2 s). For an 8,000-year run with 25-year
snapshots it is 3.6 MB; a run with 100-year snapshots is 1.8 MB.

- A time slider, play and pause (4, 8 or 16 snapshots a second), and
  the arrow keys to step.
- Layers: states, peoples, years since a cell last changed state, years
  since it last changed people. Mollweide or plate carrée. The maps
  follow the same rules and colours as `render_run.py`, with the
  ten-largest-state labels and city dots.
- Click a city dot for its row in `cities.csv` and the events that list
  it. Click a state for its row in `polities.csv` (with `origin`,
  `end_reason`) and every event that names it. Click an event's year to
  jump there. The selected state is lightened on the map, and the
  selected city ringed.
- A view can be linked: `viewer.html#year=5000&layer=state_age&proj=platecarree&state=1240`
  (or `&city=45`).

The page draws the maps itself. Python embeds each snapshot's state and
people per land cell (with a 16-level density), each stored as its
change from the previous snapshot and gzipped (about 1.5 MB for 320
snapshots). It also embeds the projections' pixel-to-cell tables, city
and label positions, the colours, and the tables and events. The
browser unpacks them with `DecompressionStream` (current Chrome,
Firefox, Safari).

## GIS export (`export.py`)

`export.py RUN [RUN ...]` (WP2 stage D, 2026-11-17) writes three files
into `<run>/export/` from `history.npz`, `final_state.npz` and the CSVs,
without rerunning anything. An 8,000-year run takes about 8 s, giving a
28 MB `run.nc` and an 8 MB `run.gpkg`. Needs the packages in
`requirements.txt` (xarray, netCDF4, geopandas, shapely).

| File | What |
|---|---|
| `run.nc` | NetCDF, CF-1.8, on the full 360 x 720 half-degree grid (`lat` from north to south, `lon` from -180), sea cells as the fill value (NaN for numbers, -9 for ids). Over `time` (one step per kept `history.npz` snapshot, `--every-years`, default 100; `year` holds the run year): `people` (index into the file's `peoples` attribute; -1 empty land), `population` (heads), `density` (heads per km² of the cell's land), `polity` (state id; -1 none). At the end only: `road`, `improvements`, `land`, `salt`. Time is `days since 0001-01-01` on a 365-day calendar, so step Y is Y-01-01. QGIS opens it as a raster or mesh layer with the temporal controller. xarray decodes the fill value to NaN, which turns `people` and `polity` into floats; `mask_and_scale=False` keeps them as integers |
| `run.gpkg` | GeoPackage, EPSG:4326. `cities`: points with id, cell, people, founded, ended, end reason, peak size (urban fe) and peak year. `states`: one multipolygon per state per snapshot, dissolved from its 0.5° cells, with state id, snapshot year, people, cities, capital cell, cells, area (km²) and population (heads); `--every-years N` (default 100) keeps the snapshots in years divisible by N, plus the last, for both files; `--no-states` writes no state layer. `roads`: a line between each pair of neighbouring cells whose road stock at the end is over 0.3 (C), with the lower stock. Lines are not drawn across the date line. `events`: points for events with a place (`events.jsonl`; runs before 2026-11-17 have none), with year, kind, text, cell, the ids in `polities`, `peoples` and `cities` as space-separated text, `n` and the landmass code. Each layer but roads has `t_start` and `t_end` (DATETIME, run year Y as Y-01-01; year 0 as year 1). A range runs from `t_start` up to, but not including, `t_end`. A state snapshot lasts until the next one. An event lasts one tick. A city standing at the end lasts until the run's last year |
| `names.csv` | a blank table of names: `id, kind` (city, state, landmass), `lon, lat` (city; state's last capital; landmass cell mean), `size` with `size_unit` (city: peak urban fe; state: peak km²; landmass: km²), and an empty `name`. The book assigns names in its own pass; the code never fills `name` |

After writing, the script reads both files back and prints the counts and how many city points fall on land cells.

## Table columns and units

Every table a run writes, with its columns (WP2 stage C, 2026-11-17).
Units, unless a row says otherwise: years are calendar years of the run
(5-year ticks); `cell` is a land-cell index (row and column in
`final_state.npz`); `lon`, `lat` are the cell centre in degrees;
`people` is a people's key (`Hum`, ...); state, city, war and lineage
ids match across tables. Population counts are of two kinds:

- **heads**: individuals (`pop` in the code). `timeseries.csv` `pop_*`,
  `cell_pop`, `hinter_pop`, `peak_pop`, `deaths`.
- **food-equivalents (fe)**: heads x body size^0.75 (`--size-food`), so
  a troll counts for more than a goblin. City sizes are in fe.

**"Size" of a city** has meant three things. Say which.

| Name | Where | Meaning | Unit |
|---|---|---|---|
| `size` | `city_sizes.csv`; `peak_size` in `cities.csv`; `largest_city_fe` | urban population: the part of the city cell fed by food brought in (trade, rent, tax, tribute), not by its own land ([diagnostics.md](diagnostics.md#records-of-2026-11-09)) | fe |
| `size_old` | `city_sizes.csv` | the formula before 2026-11-09: 0.08 x city cell + 0.04 x hinterland | fe |
| `cell_pop` | `city_sizes.csv`, `cityfood.csv` | everyone living in the city's cell, farmers included | heads |

| File | One row per | Columns |
|---|---|---|
| `timeseries.csv` | tick | `year`; world measures; per-people columns `<variable>_<key>` and world means `<variable>_world`; `n_<counter>`: events of that kind during the tick. Meanings in [diagnostics.md](diagnostics.md#extra-timeseriescsv-columns-always-written) |
| `timeseries_long.csv` | tick x column | `year, people, variable, value` (see above) |
| `polities.csv` | state | `id`; `people` (the ruling people), `lineage` (`L<id>`, at the end), `peoples_ruled`; `founded`, `ended` (blank if alive), `years`; `parent` (state it broke from, if any); `peak_cells`, `peak_km2`, `peak_year`, `peak_cities`, `peak_pop` (heads); `capital_lon`, `capital_lat`, `capital_cell` (the last capital); `peak_foreign_share` (share of heads not of the ruling people); `origin`, `end_reason`, `ended_by` (below) |
| `cities.csv` | city ever founded | `id, cell, lon, lat, people, founded, ended`; `end_reason` (text), `cause`; `years`; `peak_size` (fe), `peak_year`; `n_sacks, n_rulers`; `prev_city`, `refounded`, `successor` (city ids and the year a ruin was resettled); `ruin_years, ruin_empty_years`; `rulers` (state ids in order); `minority_peoples, minority_peak_share, minority_years, majority_changes` |
| `city_sizes.csv` | city or ruin, every 25 yr | `year, city_id, cell, status` (`city`, `ruin, settled`, `ruin, empty`); `size` (fe), `cell_pop` (heads), `size_old` (fe); `people, polity` (-1 none); `minority`, `minority_share` |
| `cityfood.csv` | city, every 25 yr | `year, city_id, cell, people, polity, capital, coastal, river`; `cell_pop`, `hinter_pop` (heads), `hinter_cells`; `k_rural` (what the cell's land feeds), `urban`, `from_trade, from_rent, from_prov, from_capital` (fe); `main_source` |
| `wars.csv` | war | `id, start, end, years, att, dfn`; peoples, landmasses, cities and `strength` (model units: the state's weighted population x military x (0.3 + 0.7 cohesion), `states.py`) of each side at the start; `goal, goal_city, goal_met, why` (how it ended, `ongoing` if alive); `sieges, captures, recaptures, moved, moved_back, helpers, sacks` |
| `sieges.csv` | siege | `year, war, side` (`att`: the attacker's siege; `dfn`: a counter-offensive), `city, city_fe` (fe), `capital`, `besieger, holder`, `P_besieger, P_holder` (strength brought), `odds` (win probability at launch), `taken`, `terms` |
| `revolts.csv` | revolt | `year, state, new_state, people_ruler, people_rebels, kind` (secession, kin, ethnic, pretender), `cities_taken, cities_left, landmass, lon, lat` |
| `relations.csv` | neighbouring pair of live states, every frame tick | ids, peoples, landmasses and cities of `a` and `b`; `similarity`, `similarity_lin` (0-1); `enmity_ab, enmity_ba, faith_ab, faith_ba`; `tie` (trade); `war, allied, truce` (0/1) |
| `rulers.csv` | reign | `ruler, state, people, start, end, years, cities, succession` (how it ended), `dynasty`; ruler traits `violence, dominance, expansion, statecraft`; `w`, `gap` ([rules](rules/)) |
| `lineages.csv` | lineage | `id, people, parent, parent2, how, founded, ended, fate, peak_pop` (heads); `stage, agri, metal, sail, fishing`; memories `war_mem` ... `raid_mem`; `admin`, `r` (growth per year); cultural traits (0-1) |
| `lineage_events.csv`, `lineage_pairs.csv` | fusion or absorption; pair of lineages sharing a state | `year, kind, people, a, b, to, state, years_together, pop_a, pop_b, share, distance` ...; `hazard` |
| `deaths.csv` | people x cause, every century | `year, people, cause, deaths` (heads over the century) |
| `food.csv` | scope x key, every century | `year`; `scope` (`world`, `people`, `state`) and `key` (`ALL`, a people's key, a state id). Every other column is a mean per tick over the century ending at `year`, in fe (how many food-equivalents that food feeds), except the two shares. Produced: `produced` = `produced_land` + `produced_boost` (the city boost). `eaten` (people and minority). Taken: `taken` = `taken_rent` + `taken_tax` + `taken_tribute`. Lost: `lost` = `lost_eff` (the 1 - EXT_EFF share) + `lost_vassal` (tribute to a lord lost over the distance). Received: `received` = `received_local` (in the cell's own city) + `received_capital` (at capitals; includes `received_vassal`). Created: `created` = `created_trade` + `produced_boost`. `city_food` (produced on city cells plus everything received there); `cap_unused` (capital food at a cell where no ruling people live); `received_smoothed` (`ext_in` + `loc_in`, what capacity reads); `taken_capacity` (what the rates in `Kf` remove from capacity, minorities included); `unplaced` (a capital's take with no city to arrive in); `gap` = `taken - received - lost`. From WP4 stage B: `trade_out` (food sold from a cell under `trade_debit`), `trade_in` (traded food arriving in cities; `created_trade` is then 0), `lost_trade` (lost on the way, by exporter), `gap_trade` = `trade_out - trade_in - lost_trade`; `created_share` = created / produced; `created_share_city` = created / city food |
| `price.csv` | people (and world) x trait, every century | Price-equation terms ([diagnostics.md](diagnostics.md#price-decomposition-pricecsv)) |
| `citylevel.csv`, `citygaps.csv`, `citytraits.csv` | trait, city | city-level cultural measures ([diagnostics.md](diagnostics.md)) |
| `dragons.csv` | dragon | `id, born, parent, home0` (cell), traits, `ended, fate, ally, ally_people, ally_year, moves` |
| `posts.csv` | trading post standing at the end | `planter, host` (states), `city` (cell), `lon, lat, year`, peoples |
| `events.jsonl` | event | see the files table above |

**`polities.csv` `origin`** (records, WP2 stage C; C): how the state
began. `city_outside`: a city founded outside any state.
`city_inside`: a city founded inside a state that it did not join.
`colony`: a city of a colonist lineage that did not join its home
state. `revolt_secession`, `revolt_kin`, `revolt_ethnic`,
`revolt_pretender`: a breakaway (the kinds of `revolts.csv`).
`partition`: an heir's share of a divided realm. `shatter`: a city left
on its own when its state shattered after losing its capital. Blank for
runs before 2026-11-17.

**`end_reason`**: `lost_last_city` (its last city depopulated, abandoned or taken over by another people), `ceded`,
`conquered`, `absorbed` (a same-people state of 3 or fewer cities taken
whole), `shattered`, `annexed` (by its lord), `fusion` (with another
people's state), `union` (with its own people's). **`ended_by`**: the
state that ended it, where there is one. The full text of each fall is in
`events.jsonl` (kind `fall`, for states of 3+ cities or 150+ cells).

