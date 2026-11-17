# WP4: a closed food account

**Goal.** Every unit of food in the model is produced on some cell, and is
eaten, moved or lost. Trade moves food instead of creating it. The deaths
table counts deaths.

**Evidence** (`BASELINE.md`).
- `states.food_flows` adds trade food to cities as
  `FF_TRADE x V x (city weight)`, where `V` sums
  `tie x sqrt(FE_a x FE_b)` over a state's trade ties. No cell is debited.
  It is 27.5% of all food brought into cities in `al_seed103`, and
  0.36-0.41 in the realism batch.
- The base city boost multiplies a city cell's capacity by
  `1.5 x (1 + DEV_CITY x development)` (`land.prepare_capacity`, `cb0`).
  That is also capacity from nothing; it may be defensible (gardens,
  manure, fishing fleets), but it is not shown anywhere.
- Rent, tax and tribute are debited from cells and arrive scaled by
  `EXT_EFF` (0.6). The received side is smoothed (`FISC_EMA`) and the paid
  side is not, so within a tick the two do not match.
- `deaths.csv`: "dragon" is 54% of the total. It is the growth a cell
  would have had without the dragon penalty (`land.grow`), not deaths.

Read first: `wsim/land.py` (`prepare_capacity`, `Kf`, `grow`, `famine`),
`wsim/states.py` (`extraction`, `food_flows`, `food_dist`),
`wsim/geo.py` (`food_graph`), `wsim/diagnostics.py` (`urban`, `dead`,
`record`), `docs/structural.md` ("2026-11-09" sections),
`docs/open-questions.md` ("Realism review").

Before starting, WP1 (so capacity is cheap) and WP2 stage B (metrics)
should be done.

## Stage A: the ledger (records only)

1. Per tick, in food-equivalents, per cell and summed per state and for
   the world:
   - **produced**: the raw capacity of occupied cells (`Kf(..., raw=True)
     x food per head`), split into land and the city boost;
   - **eaten**: what the cell's people need;
   - **taken**: rent, tax, tribute (already computed as `T`, `rent`,
     `tax`);
   - **lost in carriage**: the `1 - EXT_EFF` share and the
     `1 - exp(-distance / FF_CAP_KM)` share that never reaches a capital;
   - **received**: local (`loc_in`), capital (`ext_in`), from a vassal;
   - **created**: trade food, and the city boost.
2. Write `food.csv` per century: world and per-people totals of each
   line, plus `created / produced`.
3. Look at one run's `food.csv`: on the unsmoothed flows, taken should
   equal received + lost. If it is far off, find the leak.
4. Report, for one baseline run: created food as a share of produced
   food and of city food, by millennium. This is the number the next stage
   removes.

## Stage B: debited trade (needs U: D5, D6)

A mechanic change, behind a new switch `trade_debit`.

Design (C; simplest form that conserves food):

1. For each pair of states with a tie `t`, the wanted flow is today's
   gravity term. Its direction is from the state with more marketable
   surplus per head to the one with less.
2. A state's **marketable surplus** is what its cells produce beyond what
   their people eat and the state already takes:
   `sum over cells of max(produced - eaten - taken, 0)`, times a share
   `TRADE_SURPLUS` (C: 0.5; farmers sell part of a surplus, not all).
3. The flow is the smaller of the wanted flow and the exporter's remaining
   surplus. Debit it across the exporter's surplus cells in proportion to
   their surplus, as one more rate in `Kf` beside rent and tax. Because it
   is capped at surplus, it cannot cause hunger in the exporting cells.
4. It arrives in the importer's cities (weights as now), less a carriage
   loss over the food graph between the two states' nearest ports or
   capitals (`food_dist` gives the distance; use the same exponential form
   as tax carriage).
5. Smooth both sides with the same `FISC_EMA`, or neither.
6. Leave the base city boost alone unless D6 says otherwise; stage A now
   shows it.

Expected: world population
falls; cities shrink, the largest most, since capitals and ports took the
most created food; exporting regions stop growing at their ceiling. If
the city hierarchy flattens again, report it and stop. Raising `FF_TRADE`
or any lever to restore city sizes is tuning to a target (`GUIDE.md`).
The remedy for weak primacy is a mechanism (WP5's tribute and conquest
income, WP8's water transport of bulk food), not a rate.

Run seed 101 with the switch on and off. Compare the `realism.py` table,
the ledger, urban share, the largest city's share of the world, the
rank-size slope by millennium, and which states export.

## Stage C: deaths and growth account

Records only.

1. Split the table: `deaths.csv` keeps removals (hunger, feud, raid, war
   levies, siege, sack, clearance, plague). Dragon losses move to a
   `forgone_growth` column or file, labelled as growth that did not happen.
2. Add a per-century, per-people account that closes:
   `change in population = natural increase - removals by cause
   + arrivals - departures`. Natural increase is the residual of `grow`
   before removals. Migration nets to zero for the world; check that it
   does.
3. `famine` moves people and the rest "dies back as the land allows"
   inside `grow`; make sure that die-back is counted once, as hunger.
4. Look at whether the account closes over a run. A large gap is a
   bookkeeping bug somewhere in the step (population created or destroyed
   without a record): list it in `docs/open-questions.md` and fix it if
   the fix is simple.

## Done when

- `food.csv` closes with zero created trade food under `trade_debit`;
- the deaths account closes;
- `docs/structural.md`, `docs/rules/population.md`,
  `docs/diagnostics.md` and `docs/run-log.md` describe the new forms and
  the runs;
- the decision on making `trade_debit` the default is put to the user
  with the comparison table.
