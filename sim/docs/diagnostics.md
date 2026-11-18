# Diagnostics (`diagnostics`)

Code: `Sim.price`, `write_checks`; extra columns in `timeseries.csv`.

Every output table, its columns and their units are listed once, in
[running.md](running.md#table-columns-and-units) (WP2 stage C,
2026-11-17). That section also says which of the three city "sizes" is
which: `size` (urban population, food-equivalents), `size_old` (the
formula before 2026-11-09, food-equivalents) and `cell_pop` (everyone in
the city cell, heads). `timeseries.csv` is also written long, as
`timeseries_long.csv` (`year, people, variable, value`). `polities.csv`
gained `capital_cell`, `origin`, `end_reason` and `ended_by` (records).

## Price decomposition (`price.csv`)

Every 100 years the run takes a snapshot of every living lineage: its
population and cultural traits.

At the next snapshot:
- **Ancestor.** Each living lineage is traced back through `Lparent` to its
  nearest ancestor in the previous snapshot.
- **Offspring.** An ancestor's offspring is the population of itself plus
  its descendants.
- **Fitness.** `w` = offspring / the ancestor's population then.
- **Offspring trait.** z′ = the population-weighted trait of that offspring.

With weights equal to the ancestors' populations:

    wbar Δzbar = Cov(w, z) + E(w Δz)
    selection    = Cov(w, z) / wbar
    transmission = E(w Δz) / wbar

**Rows.** Each row is one century, one people (or `ALL`) and one trait.
- **Per people:** within-people change.
- **`ALL`:** lineages of every people together. Its selection term includes
  change in the mix of peoples.

**Notes on reading it:**
- **Cells assimilated into a lineage count as its offspring.** In this
  model that is how a culture reproduces. Selection therefore includes
  spread by rule, not only by births.
- **Transmission** collects mutation at secession and settling, averaging at
  union and fusion, and acculturation.
- **`immigrant_share`** is the share of today's population with no ancestor
  in the last snapshot (new arrivals). It is left out of both terms.

## Stylized-fact checks (`checks.txt`)

The references are rough orders of magnitude, not tuning targets.

| Measure | Run statistic | Reference |
|---|---|---|
| State lifespan | mean, median and CV of ended states that held 3+ cities | mean ~200–250 years, roughly exponential, CV ~1 (Arbesman 2011, *Ann. NY Acad. Sci.*) |
| State size | peak cells of states with 3+ cities; skew of log size | heavy-tailed, roughly log-normal (Taagepera 1978, 1979, 1997) |
| City rank-size | log-log slope of the top 200 cities at the end | about −1 (Zipf); pre-modern systems often −0.6 to −1 |
| War | mean share of states with 2+ cities at war each tick | high; great powers at war in most years (Levy 1983). Uncertain for city-state systems. |

`checks.txt` also sums `price.csv` over the run.

## Extra `timeseries.csv` columns (always written)

| Column | What |
|---|---|
| `at_war_share` | share of states with 2+ cities that are at war |
| `revolts` | revolts this tick (including pretenders) |
| `vassals` | number of vassal ties |
| `herd_share` | share of world population living by herding |
| `land_mean` | population-weighted land condition on farmed cells |
| `moisture`, `dry_pop_share` | population-weighted moisture anomaly; share of people below −1.5 sd |
| `famine_movers` | people moved by famine migration this tick |
| `avulsions` | river course changes so far |
| `road_cells`, `improvements` | cells with road stock over 0.3; population-weighted improvements |
| `minority_pop` | people living as minorities |
| `dragons_wild`, `dragons_allied` | dragons alive (with `dragons`) |
| `dragon_kills`, `dragon_kills_<people>` | people lost to dragons this tick: the shortfall against growth without them |
| `dragons_allied_<people>` | allied dragons held by each people's states |
| `dragon_land` | share of land cells inside a wild dragon's territory |
| `dragon_tol`, `dragon_viol`, `dragon_str` | mean tolerance, violence and strength of wild dragons |
| `warded_cells` | cells with enough people to ward off a dragon |
| `near_empty` | share of land cells below 0.02 food-equivalent people/km² |
| `n_dragon_slain`, `_pushed`, `_lost`, `_ally`, `_freed`, `_born`, `_died` | dragons slain, driven to a new site, driven off with nowhere to go, taken as allies, freed by their state's end, born, dead of age |
| `stress_mean` | mean political stress of states with 2+ cities |
| `bronze_users` | lineages with bronze in use |
| `n_ally_same`, `n_ally_cross` | alliances formed this tick, within and across peoples |
| `n_ally_balance` | of those, formed only because of the balancing term |
| `n_ally_break` | alliances broken (not counting ones ended by war or a fall) |
| `n_union`, `n_fusion` | mergers within and across peoples |
| `n_vassal_submit_same`, `_cross` | submissions within and across peoples |
| `n_vassal_defect`, `n_vassal_annex`, `n_vassal_freed` | vassals breaking away, annexed, or freed by their lord's fall |
| `n_war_same`, `n_war_cross` | wars declared within and across peoples |
| `n_capture_same`, `n_capture_cross` | cities taken from the conqueror's own people or another |
| `n_revolt_<kind>`, `n_revolt_<kind>_cities` | revolts and cities lost to them; kind = secession (ruling lineage), kin (same people, other lineage), ethnic (other people), pretender (disputed succession) |
| `city_years` | city-years this tick, the denominator for rates |
| `states_<people>`, `cities_per_state_<people>` | live states of each people and their mean size |
| `spread_<people>` | cultural spread inside a people: population-weighted mean distance of its lineages' traits from the people's mean |

Unlike `events.txt` and `events.jsonl`, which log only events involving larger states,
these counters include every event.

## Run measures (`wsim/metrics.py`, 2026-11-17)

`wsim/metrics.py` holds every measure of a finished run, one function per
group, each taking a `wsim.runio.Run` and returning a flat dict; the run
writes them all to `metrics.json` at its end. They took in the realism
checks of 2026-11-09 (`realism.py`, below), the old `checks.txt`
computations, and the review measures of `docs/upgrade/BASELINE.md`:

| Function | What |
|---|---|
| `population` | world population at each 1000 years, urban share, cities below URBAN_MIN, herding peak, minority share of heads |
| `growth` | %/yr over each millennium |
| `volatility` | sd of log world population around its 200-year mean after 3000; largest 100-year fall; worst 300-year fall and what cities did over it |
| `landmass_volatility` | the first two per landmass group (`landmasses.py`), from `history.npz` (100-year snapshots, so coarser) |
| `city_hierarchy` | rank-size slope at 2000-year marks and at the end; largest city against the 10th and the world |
| `city_lives` | cities founded, ended, abandoned; of those alive at 4000, ended within 2000 years |
| `states` | polities; never above one city (share, median life); largest state against land and the 10th; size distribution of 3+ city states; multi-people states; vassals |
| `lifespans` | ended 3+ city states: mean, median, CV, share over 1000 years, longest |
| `contiguity` | ten largest states at the end: land pieces (8-connected, joined across the date line) and groups once pieces within the state's sailing range are joined, each with its largest share |
| `wars` | count; ending inside one tick, within 5 years; 0-1 sieges; peer wars; wars per millennium; how ended wars ended |
| `sieges` | share taken; terms; win probability at launch (`odds`): n, median, share under 0.1, for all and by `side` (`att` the attacker's sieges, `dfn` counter-offensives) |
| `war_time` | share of 2+ city states at war, over the run and by millennium |
| `food` | shares of city food from trade, rent, provincial spending, capital (last `cityfood.csv` year) |
| `deaths` | deaths by cause, shares |
| `settlement` | population against land share by coast, river, alluvial fill, latitude band, biome; density percentiles; population, land area and land cells inside states |
| `turnover` | per 500 years: share of cells whose people changed; occupied cells inside a state; cells emptied |
| `price` | Price decomposition summed over the run |

`metrics.cross(runs)` compares final maps pairwise: cells held by the same
people, city sites within one cell, correlation of log(1 + cell
population); the first two with a chance level. `realism.py` prints
these (`--cross`).

## Realism checks (`realism.py`, 2026-11-09)

Prints the measures above side by side, from each run's `metrics.json`
(computing them for runs without one). The realism review of 2026-11-09
(open-questions.md) read: rank-size slope of
cities over time, the largest city against the 10th and against the
world, the largest state as a share of the land (122M km²) and against
the 10th, standing vassals, how wars end (overall and by the defender's
size), how won sieges were settled (`war_terms`), city founding,
survival and abandonment (`urban_city`), the worst 300-year fall in world
population after year 3000 with the change in cities over it, the lowest
urban population against before, and the cities below URBAN_MIN before
and at most (per seed), and deaths by cause.

    ~/.venvs/worldsim/bin/python realism.py --group 'base_seed10?' 'ff_seed10?'

`--group` pools runs named alike up to `_seed` and prints the range
across seeds. Rough historical references, not targets: pre-modern
rank-size slopes about -0.6 to -1; largest pre-modern cities about 0.2-0.5%
of the world's people; the largest states about 3% (Rome, Achaemenids)
to 16% (Mongols) of the land; urban share about 5-15%; long-run growth
about 0.04-0.1% a year. Judge on spread across seeds and on whether a
crisis reaches the cities, not on hitting a number.

## Records of 2026-11-09

- **Urban population** (`urban`, diagnostics.py; U: 2A). A city's size is
  the share of its cell's people fed by what is brought in (trade, rent,
  tax and tribute) rather than by its own land at the base boost (1.5 x
  (1 + DEV_CITY x development)), taken as that share of the cell's
  capacity, and at most what the food brought in feeds; in
  food-equivalents. At equilibrium it is the people beyond what the land
  feeds. Until the realism batch's end (2026-11-09) it was that excess
  outright (the cell's people less what its land feeds), which put every
  loss in a city cell (plague, siege, sack) on its rural part first; the
  batch's runs use that form. Without `food_flow` this is the trade term of the old boost
  plus `dominion`'s tribute. It replaces 0.08 x city cell + 0.04 x
  hinterland, which `city_sizes.csv` keeps as `size_old`. Records only.
- `timeseries.csv`: `urban_fe`, `urban_share` (of the world's
  food-equivalents), `largest_city_fe`, `cities_low_urban` (cities with
  urban population below URBAN_MIN = 2,000: what 2B would abandon),
  `n_war_tributary`, `n_war_sack`, `n_ff_rent`, `n_ff_tax`, `n_ff_trade`
  (food taken as rent and tax, and trade food created, per tick).
- `cityfood.csv` (every 25 yrs, every city): capital, coastal, river,
  cell and hinterland population, hinterland cells, `k_rural` (what the
  cell's own land feeds), `urban`, food arriving from trade, rent,
  provincial tax spending and the capital's take (`from_*`), and the
  largest of these with the land as `main_source`.
- `deaths.csv` (every century, per people and cause): hunger (a crowd
  above what the land feeds dying back in growth), dragon, feud, raid,
  war levies, siege, sack, clearance, plague. Famine movers are not
  deaths.
- `polities.csv` `peak_km2` for every state (was blank below 120 cells).

