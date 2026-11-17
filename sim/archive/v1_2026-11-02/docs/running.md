# Running

Environment: `~/.venvs/worldsim` (Python 3.12 with numpy, scipy, pillow and
matplotlib). The map is opened read-only through sqlite3, so geopandas isn't
needed.

Current scenario (ten peoples, head starts):

    ~/.venvs/worldsim/bin/python worldsim.py --peoples peoples_headstart \
        --starts 20 --start-vary 0.1 --seed 91 --years 6400 --vary 0.12 \
        --out runs/terrain_seed91

A run took about 7 minutes before the structural mechanics; four run in parallel comfortably on 8 cores.
The same seed gives the same history.

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
| `--out` | `runs/seed<N>` | output folder |

With `--off all --city-cap 3 40` the model reproduces the pre-structural one draw for draw
(checked: identical `events.txt` and `polities.csv` over 1,500 years, seed
91). The archived copy is `../archive/worldsim_2026-10-29_pre_structural.py`.

## Outputs (per run folder)

| File | What |
|---|---|
| `history.gif`, `frames/`, `final_maps.png` | animation and last frame. The top panel shows states, the bottom peoples by density (red dots: dragons). Dots are cities; ringed dots are capitals. |
| `final.png` | 2x2 summary (`figures.py`, 2026-11-01): states; peoples by density; peoples in flat colours with trading posts standing at the end (stars, in the merchants' colour) and the 12 strongest trade links between (landmass, people) groups at the last frame (width = summed trade tie; arrowhead from the merchants' home to the host where posts show a direction); major wars per 250 years by landmass group |
| `wars.png` | major wars per 250 years on each landmass (S, W1, W2, W3-W5, N1, N2-N4, E1), one line per pair of peoples (top 4 per panel), with large states that collapsed in revolt as triangles. Major war (C): both sides held 5+ cities at the start and 2+ cities were taken, or a side holding 10+ cities fell; placed at the defender's capital. Revolt collapse (C): a state loses 5+ cities and 40%+ of its cities to revolts in one tick |
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
| `run.json` | the settings of the run, including the mechanics switched on |
| `price.csv` | Price-equation decomposition of each cultural trait, per century, per people and world-wide ([diagnostics.md](diagnostics.md)) |
| `dragons.csv` | every dragon: birth, first home, end, fate, ally (with `dragons`) |
| `relations.csv` | every pair of neighbouring live states on each frame tick: similarity, enmity and faith motives both ways, trade tie, war, alliance, truce |
| `city_sizes.csv` | every city and ruin every 25 years ([structural.md](structural.md#city-histories-bookkeeping-only)) |
| `checks.txt` | the run against rough historical regularities, plus a summary of `price.csv` ([diagnostics.md](diagnostics.md)) |

Analysis tools: `landmasses.py` holds short codes per landmass (S, W1-W5,
N1-N4, E1, X1-X4; groups S, W, N, E, X) and draws `docs/landmass_key.png`.
`landmass_report.py RUNS --lm W` reports peoples, cities, states, wars,
relations, culture, revolts, successions and trading posts for a group of
landmasses. `timeline.py RUN --landmass W1,W2` takes the same codes.
`figures.py RUNS` rebuilds `final.png` and `wars.png` for finished runs
(runs before 2026-11-01 lack `posts.csv`; their posts are rebuilt from
the events still standing at the end).
