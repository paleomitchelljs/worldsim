# Diagnostics (`diagnostics`)

Code: `Sim.price`, `write_checks`; extra columns in `timeseries.csv`.

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

Unlike `events.txt`, which logs only events involving larger states,
these counters include every event.
