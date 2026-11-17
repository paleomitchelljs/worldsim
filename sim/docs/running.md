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
The same seed gives the same history. From 2026-11-07 the climate no
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

## Options

| Option | Default | Meaning |
|---|---|---|
| `--seed` | 1 | random seed |
| `--years` | 6000 | length; use 6400 with `peoples_headstart` so latecomers get 6000 |
| `--frame-every` | 20 | ticks between animation frames |
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
| `--out` | `seed<N>` | output folder; a bare name goes in the runs root |

With `--off all --city-cap 3 40` the model reproduces the pre-structural one draw for draw
(checked: identical `events.txt` and `polities.csv` over 1,500 years, seed
91). The archived copy is `archive/worldsim_2026-10-29_pre_structural.py` in git commit 3338050 (see `archive/README.md`).

## Outputs (per run folder)

From 2026-11-17 the run writes as it goes (`wsim/output.py`, `Stream`).
Each frame is saved to `frames/` when it is rendered. Every `FLUSH_EVERY`
ticks (C: 100 ticks, 500 years) and at the end, the append-only tables
(`events.txt`, `timeseries.csv`, `city_sizes.csv`, `sieges.csv`,
`revolts.csv`, `relations.csv`, `price.csv`, `cityfood.csv`, `deaths.csv`,
`citylevel.csv`, `citygaps.csv`, `citytraits.csv`, `lineage_events.csv`,
`lineage_pairs.csv`) get their new rows. `wars.csv`, `rulers.csv`,
`cities.csv`, `polities.csv`, `lineages.csv`, `dragons.csv`, `posts.csv`,
`history.npz` and `run.json` are rewritten under a temporary name and then
renamed into place. A killed run therefore keeps readable tables up to its
last flush, and `run.json`'s `year_reached` says how far that was.
`realism.py` reads such a partial run. The rest is written only when the
run ends: `history.gif`, `final_maps.png`, the plots, `traits.txt`,
`chronicle.txt`, `checks.txt`, `final_state.npz` and `figures.py`'s
figures.

| File | What |
|---|---|
| `history.gif`, `frames/`, `final_maps.png` | animation and last frame. The top panel shows states, the bottom peoples by density (red dots: dragons). Dots are cities; ringed dots are capitals. |
| `final.png` | 2x2 summary (`figures.py`, 2026-11-01): states; peoples by density; peoples in flat colours with trading posts standing at the end (stars, in the merchants' colour) and the 12 strongest trade links between (landmass, people) groups at the last frame (width = summed trade tie; arrowhead from the merchants' home to the host where posts show a direction); major wars per 250 years by landmass group |
| `wars.png` | major wars per 250 years on each landmass (S, W1, W2, W3-W5, N1, N2-N4, E1), one line per pair of peoples (top 4 per panel), with large states that collapsed in revolt as triangles. Major war (C): both sides held 5+ cities at the start and 2+ cities were taken, or a side holding 10+ cities fell; placed at the defender's capital. Revolt collapse (C): a state loses 5+ cities and 40%+ of its cities to revolts in one tick |
| `trade.png` | the peoples-and-trade panel of `final.png`, full size (2026-11-04) |
| `history.npz` | map snapshot every HIST_EVERY ticks (100 years; 2026-11-04): people, population and state per cell, each live state's capital, people and cities, and the trade ties. Reads state only, so it does not change a run |
| `war01.png` ... `war24.png` | the 24 most important wars (C: cities of the smaller side at the start x (1 + cities captured), so a clash of powers outranks an empire swallowing a city), in order of start, each on the peoples map at the snapshot nearest its start: both states outlined (attacker red, defender amber), a line between the capitals in two halves whose widths follow each side's cities, an arrowhead at the loser's capital and a star on the winner's (none for a draw), a zoomed inset when the war is small; the title gives the outcome and net cities. Winner: attacker if the defender fell, submitted, ceded or the goal was met; defender if the attacker fell or was repulsed; else a draw. Net cities = captures + a ceded city - recaptures. Needs `history.npz` |
| `tradewars.gif` | one frame per snapshot: peoples map, the 16 strongest trade links between (landmass, people) groups (width = summed tie), and every war fought since the previous snapshot, one line per pair of states: the 20 most important pairs drawn as in `war*.png` (borders, start year and the winner's net cities for the top 8), the rest as faint lines. Needs `history.npz` |
| `posts.csv` | trading posts standing at the end: planter, host, city, year planted, peoples |
| `lineages.png` | final map. Hue = people, shade = lineage. |
| `legacy.png` | every city that ever stood, plus the peak extent of the largest states |
| `population.png` | population, cities, number of states and size of the largest state over time |
| `violence.png` | population-weighted mean violence and tolerance over time, for the world and each people |
| `chronicle.txt` | major events: world-firsts, great plagues and droughts, the 15 largest states, fusions, extinctions |
| `events.txt` | every logged event |
| `traits.txt` | the traits actually used: people base values plus each founding group |
| `lineages.csv` | every lineage, with parent, origin, traits and the technology stage reached |
| `cities.csv`, `polities.csv` | lon/lat, founding and end years, peaks, rulers, peoples ruled (loads into QGIS) |
| `timeseries.csv`, `final_state.npz` | per-tick statistics; final per-cell grid (row/col match `cells`), including roads, improvements, land condition, rivers and the drainage network as it ended |
| `run.json` | the settings of the run, including the mechanics switched on. From 2026-11-17 also `code` (git commit and whether tracked files differed from it), `command` (the full command line), `python` and `numpy` versions, `wall_seconds` (from start to the last write of `run.json`), `year_reached`, and `constants`: every numeric constant in `wsim/params.py` as used, after `--set` and the other overrides |
| `price.csv` | Price-equation decomposition of each cultural trait, per century, per people and world-wide ([diagnostics.md](diagnostics.md)) |
| `dragons.csv` | every dragon: birth, first home, end, fate, ally (with `dragons`) |
| `relations.csv` | every pair of neighbouring live states on each frame tick: similarity, enmity and faith motives both ways, trade tie, war, alliance, truce, and `similarity_lin` (the ruling lineages'). From 2026-11-07 similarity and motives are those the war rule reads (the states' cultures under `city_culture`); before, they were always the ruling lineages', so they did not show what drove wars |
| `city_sizes.csv` | every city and ruin every 25 years ([structural.md](structural.md#city-histories-bookkeeping-only)); from 2026-11-09 `size` is the urban population and `size_old` the old 0.08/0.04 formula ([diagnostics.md](diagnostics.md#records-of-2026-11-09)) |
| `cityfood.csv` | every city every 25 years: where its food comes from (land, trade, rent, provincial tax, the capital's take) and its urban population (2026-11-09) |
| `deaths.csv` | deaths per century by people and cause (2026-11-09) |
| `checks.txt` | the run against rough historical regularities, plus a summary of `price.csv` ([diagnostics.md](diagnostics.md)) |

Analysis tools: `realism.py RUNS [--group]` prints the realism checks
side by side ([diagnostics.md](diagnostics.md#realism-checks-realismpy-2026-11-09));
a run still going, or killed, is measured up to its last flush (its
`years` row says how far). It skips runs whose files Dropbox has made
online-only (reading those can hang), and names them.
`landmasses.py` holds short codes per landmass (S, W1-W5,
N1-N4, E1, X1-X4; groups S, W, N, E, X) and draws `docs/landmass_key.png`.
`landmass_report.py RUNS --lm W` reports peoples, cities, states, wars,
relations, culture, revolts, successions and trading posts for a group of
landmasses. `timeline.py RUN --landmass W1,W2` takes the same codes.
`figures.py RUNS` rebuilds `final.png`, `wars.png`, `trade.png` and (with `history.npz`) the war maps and `tradewars.gif` for finished runs
(runs before 2026-11-01 lack `posts.csv`; their posts are rebuilt from
the events still standing at the end).
