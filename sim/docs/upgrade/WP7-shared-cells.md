# WP7: several peoples in a cell, and displacement

**Goal.** Peoples that can move into, live among and be pushed out of one
another's land. This is options A and C of `docs/open-questions.md`,
"Peoples do not move" (2026-11-06), in their general form. Peoples still
never interbreed.

**Needs U: D9.** This is the largest refactor in the plan. Stage A is a
design note; build nothing until the user has confirmed it.

**Evidence** (`BASELINE.md`).
- Cells whose people changed per 500 years: under 1% before year 3000,
  3-5% late. `dominion` raised it from about 1%.
- Minorities are 1.1% of heads.
- Across seeds the same people holds 64-77% of cells.

**What the code does.**
- A cell holds one people and lineage (`cul`, `lin`, `pop`) and at most
  one minority (`mcul`, `mlin`, `mpop`, `mcap`).
- `migrate` moves people only into cells of their own lineage; `budding`,
  `pioneers` and `voyages` only into empty cells (voyages may displace or
  join very thin natives).
- A minority lives on `MIN_CAP` (0.2) of capacity, or under `dominion`
  shares the land by competitive weight (`land.comp_w`, `SHARE_ALPHA`).
  `tidy_minorities` swaps the two when the minority outweighs the
  majority.
- Clearance, sacks and raids kill; nobody flees.
- The minority slot is special-cased in `grow`, `raids`, `capture`,
  `sack`, `disasters`, `polity_stats`, `extraction`, `food_flows`,
  `technology`, `city_culture`, `minorities`, `trade_posts`, `settlers`
  and the records.

Read first: `wsim/settlement.py` (all), `wsim/land.py` (`grow`, `famine`,
`comp_w`, `Kf`), `wsim/war.py` (`raids`, `capture`),
`docs/open-questions.md` ("Peoples do not move", "Mixed settlement",
"Multi-origin cities"), `docs/structural.md` (`dominion`).

Do WP1 (capacity is cheap per pair) and WP4 (the food account) first.

## Stage A: design note

Write `docs/upgrade/WP7-design.md` (two or three pages) and get it
confirmed. It must settle:

1. **Representation.** Recommended: a *presence table*, one row per
   (cell, people) that is present: cell, people, lineage, heads. `Kf`
   already takes (lineage, cell) pairs, so capacity needs no change. Most
   cells hold one people, so the table is little longer than the grid. A
   dense `pop[cell, people]` array is simpler to write but makes every
   per-cell operation ten times wider. Keep derived per-cell arrays for
   the plurality people and lineage (`cul`, `lin`), because rendering,
   territory, cities and most records read them.
2. **One lineage per people per cell, or several?** Recommended: one (the
   largest); arrivals of another lineage of the same people merge into it.
   That keeps today's rule.
3. **Competition.** Each people has its own capacity on the cell. Growth
   of people *i*: logistic toward its capacity less what the others eat,
   weighted: `K_i - sum over j of alpha_ij x heads_j x food_j / food_i`,
   with `alpha` from `comp_w` (technology, and the ruling people's state
   bonus). State the form, show it reduces to today's `dominion` rule for
   two peoples, and say what stops the strongest from always excluding
   the rest (different biome fits and food sources give different
   capacities; say whether that is enough or a floor is needed, and name
   the floor as a causeless term if so).
4. **Movement into held cells.** Who may move in, and what resists:
   tolerance of both, the state's rule (settlers of the ruling people,
   deported subjects), trade (merchant quarters), relative strength.
   `migrate`'s drift toward room then works per people across any
   neighbouring cell, with resistance where others hold it.
5. **Displacement.** Survivors of clearance, sack, lost raids and famine
   move to neighbouring cells where their people is present or the land is
   empty, raising pressure there (the cascade the user asked for).
   Say what share dies, what share flees, and how far.
6. **What "the cell's people" means downstream.** Go through each routine
   in the list above and say what it reads: plurality, a share, or every
   row. City culture already has a composition rule ("Multi-origin
   cities"); raids happen between rows in neighbouring cells and inside a
   cell; extraction charges each row by whether it is the ruling people.
7. **Records and Price.** `price()` uses lineages as units and cell
   populations as offspring; with shares it sums rows. Say what changes.
8. **Order of building.** There is no "off" switch for a representation.
   (a) Build the presence table with today's rules (one people plus one
   minority) and see that a run still looks like the old model; (b) then
   relax the rules behind switches.

## Stage B: presence table under today's rules

Replace `cul/lin/pop` + `mcul/mlin/mpop/mcap` with the table and derived
arrays; every routine keeps its present behaviour (at most two rows per
cell, the second capped as now). This is the stage that touches the most
files; keep the commits small (one routine each). At the end, one full
run whose `realism.py` table looks like the baseline's is enough.

## Stage C: competition and settlement (switch `shared_cells`)

Lift the two-row limit and the `MIN_CAP` cap; apply the competition form
and movement into held cells from the design note. Remove
`tidy_minorities`' swap (plurality is now derived) and the `mcap` flag
(a merchant quarter is a row with its own cap rule, if it needs one).

Run seeds 101 and 103, on and off. Measures:

- cells whose plurality people changed per 500 years, by window;
- cells with two or more peoples above 10%; share of heads living as a
  non-plurality;
- shares of each people by millennium and the spread between peoples.
  **Stop and report if one people passes about two thirds of all heads or
  between-people spread collapses** (the risk named on 2026-11-06, when
  Goblins held 39-54%);
- cross-seed agreement of the final people map;
- mixed cities, and whether `city_culture`'s composition rule behaves;
- run time.

## Stage D: displacement (switch `displacement`)

Implement point 5 of the design note. Measures: refugees per event
(recorded as moves, not deaths, in WP4's account); how often a
displacement is followed within 50 years by a raid, war or further
displacement in the receiving cells (cascades); the measures of stage C
again.

## Guardrails

- Peoples never interbreed: no rule may convert a row of one people into
  another.
- No causeless trends: resistance and attraction terms need causes
  (tolerance, rule, trade, strength).
- Do not change roster values to keep a people alive. A people dying out
  is an outcome to report.
