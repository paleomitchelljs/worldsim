# Upgrade status

One entry per finished stage, newest last. See `GUIDE.md`, "Handoff", for
what an entry holds.

| WP | Stage | Status | Date | Commit |
|---|---|---|---|---|
| 0 | A git | done | 2026-11-17 | 04a5711 |
| 0 | B runs out of Dropbox | done | 2026-11-17 | 0ec5f91 |
| 0 | C run manifest and overrides | done | 2026-11-17 | d17745c |
| 0 | D streamed output | done | 2026-11-17 | 858b205 |
| 0 | E clean-up | done | 2026-11-17 | 44ef835 + fix a5b8d95 |
| 1 | A polity table | done | 2026-11-17 | 48ce872 |
| 1 | B capacity factoring | partial (lineage tables) | 2026-11-17 | 48ce872 |
| 1 | C resident capacity cache | measured, not adopted | 2026-11-17 | - |
| 1 | D migration, raids, climate, wars | partial (see entries) | 2026-11-17 | 17e54e7, b8c092b, 4466cfd |
| 1 | E branching from a saved state | done | 2026-11-17 | 8aba7b8 |
| 1 | F RNG streams and new baseline | done | 2026-11-17 | 668ac79 |
| 2 | A structured events | done | 2026-11-17 | 1f51f62 |
| 2 | B run loader and metrics | done | 2026-11-17 | 8b516c7 |
| 2 | C tidy tables | done | 2026-11-17 | 8499650 |
| 2 | D GIS export | done | 2026-11-17 | 3b8fe04 |
| 3 | A snapshots | done | 2026-11-17 | 5bf9a66 |
| 3 | B renderer and projection | done | 2026-11-17 | 1149de9 |
| 3 | C state colours and change layers | done | 2026-11-17 | 1149de9 |
| 3 | D video and viewer | done | 2026-11-17 | 42d3a85, 374139a |
| 4 | A ledger (records only) | done | 2026-11-17 | 83775fa |
| 4 | B debited trade | done (switch off by default; default needs U) | 2026-11-17 | 672415b |
| 4 | C deaths and growth account | done | 2026-11-17 | f777567 |
| 5 | A diagnosis | done (B-F forms need U) | 2026-11-18 | 75c481c |
| 5 | B odds-gated war | done (on by default) | 2026-11-18 | 583d7ee |
| 5 | C time constants in years | done (+ U: site spread, small-state succession) | 2026-11-18 | c04c487 |
| 5 | D yearly political step | done (on by default) | 2026-11-18 | 0b1c30d |
| 5 | E army stock | done (on by default) | 2026-11-18 | c65846f |
| 5 | F cityless polities | done (on by default) | 2026-11-18 | 0c236c7 |
| 6 | A experiment batch | done (B needs U: D7) | 2026-11-18 | d3aa08e |
| 6 | B adopt | done (D7: R_SCALE 0.5, R_MAX 0.03) | 2026-11-18 | b1913d7 |
| 6 | C epidemics and upkeep (U, not in the brief) | done (both on by default) | 2026-11-18 | b1bafe1 |
| 7 | A design note | confirmed (U, D9: presence table, niche overlap, inner raids, flight = 1 − violence) | 2026-11-18 | 5138b4c |
| 7 | B presence table | done (storage only; exact rerun) | 2026-11-18 | 1a17b6e |
| 7 | C competition and settlement | done (`shared_cells` on by default) | 2026-11-18 | a7dc06b |
| 7 | D displacement | done (`displacement` on by default; cascades not measured) | 2026-11-18 | a7dc06b |
| 8 | A climate fields | done (D10, U: report first; agreement 0.56, findings for U) | 2026-11-19 | e293026 |
| 8 | B yields and runoff | done (`climate_fields` on) | 2026-11-19 | ad5305c |
| 8 | C floodplain area | done (`floodplain` on by default, U) | 2026-11-19 | ad5305c |
| 8 | D10, defaults, baseline (U) | done (`world_v2` default, climate biomes; baseline `wp8d_`) | 2026-11-19 | 9c0afdd |
| 8 | Physical refit, lakes, sites v3 (U) | done (baseline `wp8e_`) | 2026-11-19 | 6d9eea2 |
| 8 | Penman-Monteith PET (U) | done (baseline `wp8f_`) | 2026-11-20 | aa0f052 |
| 8 | Rain-out under sinking air lowered (U) | done (baseline `wp8g_`) | 2026-11-20 | e08aeda |
| 8 | Monthly circulation, currents, seams (U) | done (baseline `wp8h_`) | 2026-11-20 | 5d07290 |
| 8 | Monsoon westerly, rain timing (U) | done (baseline `wp8i_`) | 2026-11-20 | 23e3c6e |
| 8 | Land clearing (U) | done (`clearing` on; baseline `wp8j_`) | 2026-11-20 | 53610b9 |
| 9 | A metrics freeze | done (`docs/patterns.md`; six held-out measures) | 2026-11-20 | 90e91c0 |
| 9 | B sensitivity screen | running on `wp8j` code (U: SALib, launch, summaries only) | 2026-11-20 | 6a63c34 |
| 9 | C Earth test scoping | done (`docs/earth-test-plan.md`; D11 open) | 2026-11-20 | 785fb84 |

## Entries

### WP0 stage A: git (2026-11-17, 04a5711)

**Done.** The repository is a plain `.git` at `~/Desktop/world`, not the
separate git dir the brief proposed, because the project has moved out of
Dropbox (D1, U). Commit 3338050 imports the tree as it stood, with
`archive/`. Commit 04a5711 removes the 31 `archive/worldsim_*.py` copies and
the two `archive/wsim_*` folders. It keeps `archive/v1_2026-11-02/`,
`archive/snaps/`, and the archived rosters, sites and notes. The brief said
not to push. The user asked for the repository on GitHub, so `origin` is
github.com/paleomitchelljs/worldsim and `main` is pushed.

`.gitignore` (C) leaves out `sim/runs/`, caches, `.DS_Store`, `*.pkl`,
`*.aux`, `*.log`, `.claude/`, `gis/world.gpkg` and the `gis/qa/` images.
`gis/qa/registration.json` is kept. `gis/previews/` (3.9 MB) is committed.

**Runs.** None. This stage changes no code.

**Next stage needs to know.**
- `gis/world.gpkg` (210 MB) is not in git, because it is over GitHub's
  100 MB file limit. A fresh clone cannot run the simulation until the
  file is rebuilt or copied in. Git LFS would hold it; that needs U.
- Stage B's premise has changed. The project is no longer in Dropbox, but
  `sim/runs/` (6 folders, 176 MB) is still inside the working tree,
  ignored. D2 and D3 still need answers.
- No hard-coded Dropbox or absolute paths turned up in the code. Comments in
  `realism.py`, `snapcheck.py`, `derive_world.py` and `docs/running.md`
  still mention Dropbox.

### WP0 stage B: runs root (2026-11-17, 0ec5f91)

**Done.** `runroot.py` sets the runs root: `$WORLDSIM_RUNS`, or else
`sim/runs/`, which git ignores (D2, U). Without `--out`, `worldsim.py`
writes `seed<N>` there, and `--out NAME` with no `/` also goes there.
`realism.py`, `figures.py`, `landmass_report.py`, `timeline.py`,
`bigcities.py`, `turnover.py` and `snapcheck.py` (its state file) look a bare
name up in the root. A quoted glob pattern is expanded there too. A path is
used as given. The 446 old runs stay in
`Dropbox/Personal/_book/art/world/sim/runs/` (D3, U). By prefix, the docs
cite about 343 of them and not about 103. `archive/README.md` explains how
to get back the archive copies the docs still cite (from commit 3338050).

**Runs.** `wp0b_sanity_seed101`: 3,000 years with the standard settings,
249 s. At year 3,000 it had 28.3M people, 43 cities, 39 states and 819
lineages, with all ten peoples on the map and no wars yet. `realism.py`
gave the same output for `c_seed106` and `runs/c_seed106`. `turnover.py`
found `'c_seed1*'` in the root.

**Not done.** None of the old runs were moved or read (D3).

**Next stage needs to know.** `--out runs/x` run from `sim/` still works,
because it is a path.

### WP0 stage C: run manifest and overrides (2026-11-17, d17745c)

**Done.** `worldsim.py` now imports only `wsim.params` at the top. The
options `--set`, `--city-pop`, `--city-cap` and `--dragon-*` are written
into `wsim.params` before `geo`, `sim` and the rest are imported, so
`from .params import *` and default arguments bound at import time see the
new values. `setp` still patches modules that are already loaded, for
`snapcheck.py`. Code that used `worldsim.World`, `worldsim.font` or
`worldsim.NY` still works, through a module `__getattr__`. `run.json` gains
`code` (commit, dirty), `command`, `python`, `numpy`, `wall_seconds` and
`constants` (all 385 numeric constants as used).

There are no derived numeric constants in `params.py`, so no `derive()` was
needed. The only derived names are `GPKG` (from `HERE`) and `TI` (from
`TRAITS`). The old `setp` missed two import-time bindings:
`culture.py` `push(piv=PATH_PIVOT)` and `cities.py` `CITY_COLS`. Both now
see overrides.

**Runs.** One 100-year run with `--set PATH_PIVOT=0.45 --city-pop 6500`:
`run.json` recorded both values, the commit and the dirty flag. The
3,000-year sanity run of this stage was stopped at year 2,250, because
Stage D's new `output.py` would have been loaded at its end. Up to then its
progress lines matched `wp0b_sanity_seed101` exactly. Stage D's sanity run
covers this stage's code.

### WP0 stage D: streamed output (2026-11-17, 858b205)

**Done.** `output.Stream` (created in `Sim.run()`) saves each frame when it
is rendered. Every `FLUSH_EVERY` ticks (C: 100) and at the end it appends
new rows to the append-only tables, and rewrites wars, rulers, cities,
polities, lineages, dragons, posts, `history.npz` and `run.json` under a
temporary name before renaming. `write_outputs` keeps the GIF, final maps,
plots, `traits.txt`, `chronicle.txt`, `checks.txt`, `final_state.npz` and
`figures.py`. `run.json` gains `year_reached`.

The lists stay in memory instead of being drained, for three reasons:
`population.png`, `violence.png` and `checks.txt` read the whole run, war
ids are `len(war_log)`, and draining would change what the Sim holds. Only
frames left memory. The timeseries columns are fixed from tick 1 (they
depend only on the switches). `realism.py` now measures a partial or
killed run up to its last flush, instead of skipping it.

**Runs.**
- A run killed with SIGKILL at year 750 kept every table readable up to
  its last flush, year 500. That includes `history.npz`, `run.json`
  (`year_reached` 500) and the last line of `events.txt`. `realism.py` read it.
- `wp0d_sanity_seed101`: 3,000 years, standard settings, 224 s, 28.3M
  people, 43 cities, 39 states. The guide does not require byte
  comparisons, but this one was cheap: 13 tables, including events,
  timeseries, cities, polities and wars, are byte-identical to
  `wp0b_sanity_seed101`, which wrote everything at the end.

**Next stage needs to know.** Memory use is unchanged apart from the
frames. If memory becomes a problem, the append lists could be drained
once their readers move to the files.

### WP0 stage E: clean-up (2026-11-17, 44ef835)

**Correction.** Commit 44ef835 did not hold exactly the code that was
sanity-run. When I split its hunks from WP1 stage A's working-tree
edits, the line `pc[pid], pl[pid] = P["culture"], P["lin"]` in
`extraction()` was lost. In that phase every state's ruling people then
read as -1 and its lineage as 0. a5b8d95 restores the line. With it, the
per-phase state hashes over 100 ticks equal stage D's. Any run made at
44ef835 itself has the wrong `extraction`; I made none apart from a
profile, which I discarded. Lesson: do not split one working tree into
two commits by hunk. Commit each stage before starting the next.

**Done.**
- **Dead code after `return`:** removed in `culture.drift_trait`,
  `war.war_prize`, `economy.kind_value`, `economy.offer` and
  `settlement.colon`.
- **Branches behind flags that were always `True`:** `tp` and `ce`
  (`culture.experience`), `no_drought` and `imm_on` (`land.disasters`),
  `col` (`settlement.voyages`), `sup` (`technology.technology`) and
  `betray` (`war.wars_step`). Also removed the overwritten `kinf = 1.0` in
  `war.raids`. These flags are the former switches that
  `switch-inventory.md` lists as core. A search for other local booleans
  assigned once and used in a test found none.
- **Constants:** `EXP_UNUSED` and `EXP_SUP_CALM` were read only by the
  removed branches, so they are gone. `structural.md` and the
  `params.py` comments say so.
- **Unused imports:** dropped from every `wsim` module. A name was kept
  where a module that star-imports the file uses it without importing it
  itself. `params.py` no longer imports the default roster. A static check
  found no undefined names afterwards.
- **World cache:** `World()` keeps the cells table in
  `<runs root>/_world_cache.npz` (83 MB), keyed on the world file's path,
  size and modification time. A load takes 1.7 s from the cache against
  3.8 s from SQLite. The brief's 13-15 s was probably measured while the
  file was in Dropbox. A World built from the cache matched one built from
  SQLite in all 60 arrays.

**Runs.** `wp0e_sanity_seed101`: 3,000 years, 225 s. `events.txt`,
`timeseries.csv`, `cities.csv`, `polities.csv`, `wars.csv` and
`lineages.csv` are byte-identical to `wp0d_sanity_seed101`, so the removed
branches were dead.

**Next stage needs to know.**
- `docs/upgrade/tools/profile_phases.py` now streams output through
  `Stream`, as `Sim.run()` does. Without that it broke after stage D.
- The cache key holds the world file's path as given, without resolving
  symlinks. A copy of the code that reaches `gis/` through a symlink
  therefore rebuilds the cache once.

### WP1 stages A and B: polity table, lineage capacity tables (2026-11-17, 48ce872)

One commit for both stages; after the WP0 E mistake I did not split by hunk.

**Done.**
- A. `ptab()` holds the live polities as arrays by id (ruling lineage,
  people, capital; -1 for ended ones), keyed on `(pver, next_pid)`.
  `padm()` gives the ruling lineage's administration, with 0 for ended
  ids, and is read fresh because administration changes within a tick.
  `pver` is bumped at every write to a polity's lin, culture, capital or
  ended (grep `pver += 1`). Eight loops now use these arrays.
  `extraction` keeps its own loop for `xr`, which calls `eff`. `eff`
  reads `CITY_COLS` and `RT_IDX`.
- B (lineage half only). `ltab()` holds K2's per-lineage biome tables
  (fit, crop and animal package weights; `MAXL x 5`). It adds rows for
  new lineages and rebuilds when `lver` moves. `lver` is bumped after
  every write to agri, metal or domlv of an existing lineage
  (technology x2, `blend`, `lineage_fusion`).

**Not done.**
- The cell-only vectors of stage B. They need refreshes after
  `land_use`, `raids`, `capture` and `sack`, which is more places to get
  wrong. Kf is no longer the top cost (table below). I would fold them
  into stage C's resident cache, where the same invalidation is needed
  anyway, rather than build them twice.
- The `polity_stats` and `food_flows` loops named in the brief. The first
  writes the lineage hand-over; the second builds a filtered live list.
  Neither just rebuilds `pl`.

**Checks.**
- A wrapper compared the new K2 with the old formula on every call for 40
  ticks from year 4,000: 5,274 calls, 30.0M values, worst relative
  difference 0.
- State hashes (pop, lin, RNG state) after every phase for 100 ticks
  equal stage D's. The 6,000-year profiles below end with the same
  cities, polities and lineage counts (381, 2,168, 3,993).

**Profile** (`docs/upgrade/tools/profile_phases.py`, seed 101, 6,000
years). Seconds per 1,000-year era; both run at the same time on a
machine with other load, so compare within the pair, not with the
2026-11-16 baseline.

| phase | E (a5b8d95) 0k / 3k / 5k | A+B 0k / 3k / 5k |
|---|---|---|
| TOTAL | 29.8 / 63.9 / 117.0 | 27.6 / 58.1 / 110.0 |
| migrate | 10.6 / 18.8 / 34.3 | 9.2 / 17.1 / 30.7 |
| Kf | 5.6 / 14.7 / 21.6 | 3.4 / 8.9 / 13.7 |
| raids | 2.8 / 14.0 / 18.4 | 2.5 / 12.1 / 16.5 |
| technology | 2.0 / 6.0 / 8.8 | 1.8 / 5.2 / 8.1 |

Over the whole run: 392 s against 362 s of phase time (-8%); 401 s
against 369 s wall time. Kf is down 37% in the last era. The polity
table saves little directly: most of the loops it replaces cost well
under 1 s per era. The largest costs are now migrate, raids and
wars_step (13.7 s in the last era, unchanged). Those belong to stage D.

**Next.** Stage C (resident capacity cache), with the cell vectors
inside it.


### WP1 stage D, first part (2026-11-17, 17e54e7)

**Done.** These edits were already in the working tree, uncommitted and
not logged, when this session started. I checked them line by line and
committed them on their own:
- `K2`: the lineage-only factors (agri, tools, sod, food per head,
  fishing, wetland skill, development, herding share) come from
  `lterms()`. When `L` has one entry per cell, `lterms()` works them out
  once per lineage and gathers. This is the lineage half of stage B's
  vectors.
- `budding` scores only empty neighbours with room for a band. Before,
  every other cell scored 0 and could never win.
- `voyages` re-tests only the cells already kept for each ball. A landing
  only removes candidates.
- `raids`: kin similarity without the Python `zip`; capacity once per
  unique cell (a cell borders several others); the first-contact loop is
  skipped when every pair in the tick has already met.
- `adjacency_by_people`: one scatter per direction, not a loop over peoples.
- `trade_ties`: `dev()` once for all lineages.

**Runs.** Seed 101, 2,000 years, at 5ebae60 and at 17e54e7: `events.txt`,
`timeseries.csv`, `cities.csv`, `polities.csv` and `lineages.csv` are
byte-identical.

### WP1 stage C: resident capacity cache (2026-11-17, not adopted)

**Built, measured, removed.** The cache held raw K2 (Kc, Kh) per cell and
applied the state's take on each read, so `extraction` did not invalidate
it. It found dirty cells by comparing K2's inputs (8 cell arrays, 13
lineage arrays, `W.gver`) with copies, instead of hooks at each write. It
served `famine`, `grow`, `migrate`, `raids`/`raid_K`, `technology`,
`polity_stats`, `food_flows`, `update_cities` and `diagnostics.urban`.

It was correct:
- 6,000 years of seed 101: `events`, `timeseries`, `cities`, `polities`,
  `lineages` and `wars` were byte-identical to 17e54e7.
- Over 40 ticks from year 4,000, all 717 cached calls (10.4M values)
  equalled a fresh `K2` exactly.

It was not faster:
- The 6,000-year profile pair (run at the same time) gave 316 s of phase
  time before and 319 s after. Kf's nested time rose from 34 s to 38 s.
- Miss rates over 20 ticks from year 3,000: `famine` 1.00 (climate
  rewrites `cm` on every cell each tick), `migrate` 0.94 (`land_use`
  rewrites `land`, `salt` and `imp` on every occupied cell), `technology`
  1.00. The cache hit in `grow` (0.00), `raids` (0.00), `polity_stats`
  (0.11) and `food_flows` (0.00). That is about a third of the cells
  asked for. The input comparison cost 0.35-0.43 ms per call, about 21
  calls per tick, and that ate the saving.
- After stages A, B and the `lterms` gather, K2 is 8% of the last 500
  years (4.8 of 57 s). Its 21,968 calls per 100 ticks are mostly small:
  `river_leap` alone makes 21,869 one-cell calls. The remaining cost is
  call overhead, which a cell cache does not touch.

**Next stage needs to know.** Stage C's premise (big redundant capacity
arrays) no longer holds. Do not rebuild it unless K2 gets expensive
again. The largest items now, by cumulative time in the last 500 years
of seed 101: `migrate` 15.2 s (of which `voyages` 8.1 s), `wars_step`
(`power_dist` 6.1 s over 192,441 calls), `raids` 6.5 s, `gc_km` 3.5 s
(62,083 calls), `climate` 3.4 s, `eff` 2.1 s (1.68M calls), `similarity`
1.9 s (321k calls).

### WP1 stage D, second part (2026-11-17, b8c092b)

**Done.**
- **State distances survive distant graph changes.** At year 5,500,
  `power_dist` cost 0.4 us a call on a hit, but `W.gver` moved about every
  three ticks (river avulsions; roads every `ROAD_EVERY`). Each move threw
  away every state's Dijkstra result: 497 rebuilds per 20 ticks, each a
  Dijkstra plus a whole-grid `gc_km`. `World.travel()` and `food_graph()`
  now record which cells each change touched (`note_change`,
  `changed_since`; the last 64 versions). For the travel graph the record
  comes from the edge-cost diff; for the food graph it comes from the
  sparse-matrix diff. `power_dist` keeps its arrays when none of those
  cells was reached within the search limit, and so does `food_dist`.
  That leaves every distance exactly as it was: a path through a changed
  edge reaches one end of it first, over unchanged edges, already past
  the limit. The `pdist` entries gain an 8th item, the cells reached.
  Entries from older pickles, which lack it, rebuild once.
- **Raids:** kin pairs encoded as one int64 for `np.unique`, instead of
  `axis=0`.

**Runs.**
- Profile pair, seed 101, 6,000 years, run at the same time: phase time
  315 s at 17e54e7 and 292 s at b8c092b (-7%). `raids` 46 -> 32 s,
  `wars_step` 23 -> 16 s. `events`, `timeseries`, `cities`, `polities`,
  `lineages` and `wars` are byte-identical. That run is also this stage's
  sanity run: `final_maps.png` at year 6,000 shows 381 cities and 134
  states, all ten peoples present.
- 20 ticks from a year-5,500 state, after 20 ticks of warm-up: 1,090
  Dijkstra calls (0.95 s) before, 636 (0.63 s) after; wall time 8.8 s
  against 7.9 s.

**Not done, and why.**
- `voyages` (about 12% of step time late on). Random draws and landings
  alternate inside the loop, so batching across lineages would reorder
  the draws. The rest of its cost is Python per lineage.
- `climate`. `accumulate` is now small (0.026 s of 0.88 s per 60 ticks
  early on). The cost is `avulse` (0.36 s, mostly `reroute`) and the
  local-noise Gaussian filter (0.27 s, about 5% of early step time). The
  brief's fix (draw at quarter resolution, then upsample) changes the
  climate realisation, so it is not a pure refactor. **Needs U** if
  wanted; it is worth about 5% early and 1-2% late.
- `gc_km`: most of its time was inside `power_dist` rebuilds, which are
  now fewer.
- The per-tick memo of `power_dist` that the brief proposes would need
  hooks at about 20 places that write a state's cities, seats or capital.
  Hits already cost 0.4 us, so a memo would gain little and add a
  staleness risk.

**Where the time is now** (seed 101, phase seconds for the 5,000-6,000
era, 89.5 s in all): `migrate` 27.1, `wars_step` 10.2, `Kf` 10.1 (nested
in the others), `raids` 8.3, `technology` 7.7, `prepare_capacity` 6.1,
`trade_ties` 3.5, `diplomacy` 3.5, `extraction` 3.2.

**Next.** Stage E (branching from a saved state). Saved states are now
about 450 MB at year 5,500, not the brief's 300 MB.

### WP1 stage D, climate noise (2026-11-17, 2fdcab2)

**Done (U, 2026-11-17: yes).** The local moisture field is drawn on every
second row and column, with sigma 3 coarse cells (the same 6 fine cells,
about 330 km), and read off bilinearly at the land cells
(`CLIM_LOCAL_COARSE` = 2, C). Spatial correlation at lags 1, 3, 6 and 12
cells: 0.993, 0.939, 0.781 and 0.372, against 0.993, 0.938, 0.777 and
0.387 for the full-grid field. It costs 2.7 ms per tick against 5.8 ms.
The climate's realisation changes, so histories differ from earlier runs.
Documented in `structural.md` and `model-description.md`.

**Runs.** `wp1d_clim_sanity_seed101` (in `sim/runs/`): 3,000 years, 96 s.
At year 3,000 it had 29.3M people, 37 cities, 36 states and all ten
peoples; `wp0b_sanity_seed101` had 28.3M, 43 and 39.

### WP1 stage E: branching from a saved state (2026-11-17, 8aba7b8)

**Done.**
- `worldsim.py --save-state YEAR PATH` (repeatable) pickles the Sim after
  the tick that reaches YEAR (`Sim.save`). A path inside Dropbox is
  refused. `pdist` and `fdist` are left out of the file, and
  `state_info` (the run.json as of the save) goes in.
- `--from-state PATH` loads a state. `--set` and the other constant
  options are written into `wsim.params` before unpickling imports the
  modules, as on a fresh run. `--off` removes switches (`Sim.flags()`
  now sets the shorthand flags, in `__init__` and on a branch).
  `--years` and `--frame-every` default to the state's. `Sim.run()`
  continues from the current tick. `run.json` gains `branch`: the state,
  the branch year, the `--set` and `--off` given, every changed constant
  (old and new), and the state's own run.json.
- Documented in `docs/running.md`, "Branching from a saved state", with
  the brief's caveat: branch 500+ years before the period compared, and
  never for a mechanic that acts from year 0.

**Surprise.** The first check failed. A branch with no changes diverged
from the run that saved it within one tick. Unpickling rebuilds Python
sets with new hash tables, so their iteration order can change, at once
(`Pblk`) or after later insertions, and the history then changes. An
in-process test showed this, and showed that a state already unpickled
once round-trips exactly. Fix: after saving, the run carries on from
`pickle.loads` of the bytes it wrote, so the run and every branch from
that file continue alike. A run with `--save-state` can therefore differ,
after the save year, from the same run without it. `snapcheck.py` was
never affected: it always compares two loads of one file.

**Runs** (scratch, deleted):
- A: seed 101, 2,000 years, saving at 1,500 (250 MB).
- B: branched from A's state with no changes. `events`, `timeseries`,
  `cities`, `polities`, `lineages` and `deaths` are byte-identical to A.
- C: branched with `--set PATH_PIVOT=0.45 --off food_flow --years 2500`.
  It finished (40 s), its map is normal, and `run.json` records all
  three changes and the state's run.json.
- `--save-state` into `~/Dropbox` and `--years` before the branch year
  are both refused.

**Not done.** Choosing a fresh seed for the branch (replicates from one
state) is not in the brief. Until WP1 stage F splits the RNG into
streams, it would mean reseeding `self.rng` at the branch. Ask U if
wanted.

**Next.** Stage F (RNG streams and a new baseline; D12 needs U).

### WP1 stage F: named random streams and a new baseline (2026-11-17, 668ac79)

**Done (U: D12 yes; a fresh seed for a branch, yes).**
- `geo.stream(seed, name)`: a `SeedSequence` child keyed on
  `crc32(name)`. A stream's draws depend only on the seed and its name,
  so adding a stream or drawing more from one shifts no other.
- `self.rng` is removed. Its 51 uses are grouped by subsystem: start,
  lineage, migrate, famine, disasters, trade, tech, cities, polity,
  diplomacy, revolt, succession, raid, war, colour. The old offset
  streams (climate, dragons, rulers, city_culture, lineage_sup,
  lineage_pref, lineage_x, and at setup vary, vary_x, prefs) use the same
  scheme. `Sim.R(name)` makes a stream on first use and keeps it in
  `self.rngs`.
- `Sim.reseed(seed)` and `worldsim.py --branch-seed N` give a branch
  fresh streams. What was drawn at setup stays as saved: the climate
  series, abrupt events, sites and founders. `run.json` gains
  `stream_seed`. `upgrade()` puts an older state on fresh named streams.

**Runs.**
- `wp1f_base_seed101`-`104` and `106`: 8,000 years, sweep settings; 7.5-8.5
  minutes each on a lightly loaded machine. Seeds 101 and 103 saved states
  at years 3,000 and 5,000 (`runs/wp1f_s10{1,3}_y{3000,5000}.pkl`,
  260-290 MB). Results and the comparison with `ub_` are in
  `docs/run-log.md`; most measures overlap. End population is wider and
  lower: median 116M (86-164M) against 137M (124-160M). Dragon deaths are
  0.60-0.64 of all deaths against 0.53-0.61. Cities ended are 0.62-0.76
  of those founded against 0.50-0.64.
- `wp1f_fullclim_seed*` (the same five seeds, `CLIM_LOCAL_COARSE=1`):
  median end population 147M (108-178M). The climate statistics match
  the coarse batch (moisture sd, drought shares, great droughts), so I
  read the population gap as seed noise. It is unresolved and logged in
  `open-questions.md`.
- Branch tests from `wp1f_s101_y5000.pkl`, run to 5,300: with the state's
  own streams, `events.txt` matches the base run line for line; with
  `--branch-seed 7` it differs from the first tick. Both took 44 s.

**Not done.** BASELINE.md's detailed sections still describe `al_seed103`
and the old code; it now points to the new batch. Recomputing those
sections is WP2 stage B's job.

**WP1 summary.** Stages A, B, D and E are done, C was measured and not
adopted, and F is done. Within-pair speed-ups on seed 101, 6,000 years:
-8% (A+B, 392 -> 362 s) and -7% (D, 315 -> 292 s). The pairs ran under
different loads, so their absolute times do not chain. The `lterms` and
budding edits had no profile pair of their own. A full 8,000-year run now
takes about 8 minutes on a lightly loaded machine; the guide's figure was
about 14.

**Next.** WP2 stage A (structured events), as `README.md` orders it.

### After WP1: climate field back on the full grid (2026-11-17, 96d0de8)

U chose to set `CLIM_LOCAL_COARSE` back to 1. With factor 1 the field is
read straight off the grid, giving exactly the old field and draws: a new
seed-101 run's `events.txt` equals `wp1f_fullclim_seed101`'s. The
baseline is therefore `wp1f_fullclim_` (BASELINE.md). The four saved
states were remade under the default, from runs `wp1g_states_seed101` and
`103`.

### WP2 stage A: structured events (2026-11-17, 1f51f62)

**Done.**
- `Sim.log(kind, text, **data)` stores a dict: year, kind, text, and
  what the call site has in hand: `cell`, `polities` (actor first),
  `peoples` (keys), `lineages`, `cities` (city ids), `n` (a magnitude).
  `first()` passes the fields through.
- All 48 call sites pass their fields. `kill_polity(pid, why, by=None)`:
  its 8 callers pass the state that ended it, so a fall names both
  states, as its text does.
- `output.Stream` writes `events.jsonl` beside `events.txt`, both from
  the same records. Rows with a cell gain `lon`, `lat`, `landmass` and
  `landmass_code` (`landmasses.CODES`).
- `chronicle.txt` is built from `polities` and `n`; `re` is gone from
  `output.py`. `upgrade()` turns an older state's tuple events into
  dicts, with no fields.
- I also wrapped the 7 lines that the stage F stream renames had pushed
  past 79 characters.

**Runs.**
- `wp2a_sanity_seed101` (3,000 years): `events.txt` is byte-identical
  to `wp1f_fullclim_seed101` and `wp1g_states_seed101` before year
  3,000, so logging changes nothing. Every kind carries its fields.
- Branches from the old-format states: `wp2a_branch` (year 3,000 to
  4,000) and `wp2a_branch5` (seed 103, 5,000 to 5,600, 1,654 events).
  Old regex rule against new field rule for the chronicle: 916 lines
  against 917. The one difference is a plague whose `polities` (the
  states it passed through) includes one of the 15 largest states that
  its text never names. That fits the chronicle's rule ("events touching
  the 15 largest states"), so I kept it. No event names a state in its
  text without listing it in `polities`.

**Not done.**
- `n` for droughts and plagues is exact, but the old rule read the
  rounded text (for example 1.96M printed as "2.0M"). Events within
  rounding of 2M can switch in or out of the chronicle.
- `timeline.py` and `figures.py` still parse `events.txt`. Moving them
  to `events.jsonl` belongs with WP2 stage B's loader.

**Next.** WP2 stage B (run loader and metrics).

### WP2 stage B: run loader and metrics (2026-11-17, 8b516c7)

**Done.**
- `wsim/runio.py`: `Run(name or path)` reads each table on first use and
  keeps it. The tables are `timeseries`, `cities`, `polities`, `wars`,
  `sieges`, `revolts`, `events` (from `events.jsonl`, else `events.txt`),
  `city_sizes`, `cityfood`, `deaths`, `lineages`, `price`, `history`,
  `final`, `config` and `metrics`. A file Dropbox has made online-only
  (the `SF_DATALESS` flag, or a non-empty file with no blocks) raises
  `Missing` instead of being read. `Run.W` builds the world on first use.
- `wsim/metrics.py`: 17 single-run functions, listed in diagnostics.md.
  They hold everything `realism.py` printed and the old `write_checks`
  computed, plus the review measures of BASELINE.md. `cross(runs)` gives
  the pairwise final-map measures.
- Each run writes `metrics.json` at its end; `checks.txt` is formatted
  from it. A metrics failure is printed and does not stop the other
  outputs.
- `realism.py` now prints `metrics.json`, and measures runs that lack
  one. It has `--rebuild`, `--save`, `--only` and `--cross`.

**Checks.**
- On `al_seed103`, the functions reproduce BASELINE.md except three,
  corrected there:
  - Land in a state: 32% was the share of cells; by area it is 51%.
  - The herding peak is 0.28 at year 2430, not 0.25 near 3000.
  - Siege odds by side: the attacker's sieges have median 0.076,
    counter-offensives 0.0066. The pooled 0.064 hid that split.
- New: once pieces within a state's sailing range (1,900-2,400 km at the
  end) are joined, the ten largest states are 1-3 groups each, against
  1-26 land pieces.
- `checks.txt` from `metrics.json` matches the old file for
  `wp1f_fullclim_seed103`, except one price term that differs in the last
  digit (price.csv stores rounded terms) and the rank-size source: the
  last `city_sizes.csv` year rather than the live city list, with the
  same slope.
- `wp2b_short` (seed 101, 1,500 years) wrote `metrics.json` and
  `checks.txt` at its end. `wars` and `sieges` are listed under
  `_missing` because no war happened.
- `metrics.json` was written into the five baseline runs. Their ranges,
  and the contingency pairs, are in BASELINE.md's last section.

**Choices to check (C).**
- Volatility per landmass group comes from `history.npz`, whose
  snapshots are 100 years apart. Its 200-year mean covers 3 snapshots,
  so it is coarser than the world figure.
- The sailing range is that of the lineage in `polities.csv`, which may
  be the founder's rather than the current ruler's.
- `cross` gives no chance level for the population correlation. Shuffling
  cells gives about 0, which does not show how much the land alone fixes.
- War counts and durations use every row of `wars.csv`, including wars
  still going at the end, as BASELINE.md did. How wars end counts only
  ended wars, as `realism.py` did.

**Not done.**
- `timeline.py`, `figures.py`, `landmass_report.py`, `bigcities.py` and
  `turnover.py` still read files their own way. They can move to
  `runio.Run` when next touched.

**Next.** WP2 stage C (tidy tables).

### WP2 stage C: tidy tables (2026-11-17, 8499650)

**Done.**
- `timeseries_long.csv` (`year, people, variable, value`), written by
  `Stream.flush_long` alongside the wide `timeseries.csv`, which stays.
  `runio.split_col` splits a column name: `<variable>_<key>` gives
  that people; `<variable>_world` and everything else give `ALL`. Empty
  values are left out. CSV, not Parquet, because D4 (pyarrow) is
  unanswered. `Run.timeseries_long` melts the wide table for older runs.
- `polities.csv` gains `capital_cell`, `origin`, `end_reason` and
  `ended_by`. `new_polity(..., origin=)` is tagged at all four call
  sites: `city_outside`, `city_inside`, `colony`, `revolt_<kind>`,
  `partition`, `shatter`. That is WP5 stage A's item 1 (the tag only,
  not its table). `kill_polity(..., code=)` stores a one-word reason
  (`lost_last_city`, `ceded`, `conquered`, `absorbed`, `shattered`,
  `annexed`, `fusion`, `union`) and the state that ended it. In
  `revolt()`, the lines that work out `kind` and `key` moved above
  `new_polity`. They draw no random numbers.
- `docs/running.md`, "Table columns and units": every table, one row
  each, with its columns and units. Heads against food-equivalents.
  The three city "sizes" (`size`, `size_old`, `cell_pop`).
  `docs/diagnostics.md` points to it.

**Runs.**
- `wp2c_sanity_seed101` (3,000 years, 186 s): 30.5M people, 44 cities,
  43 states. `events.txt` is byte-identical to `wp2a_sanity_seed101`, so
  the records change nothing. `timeseries_long.csv` is 5.3 MB against
  1.6 MB for the wide file (181,286 rows). An 8,000-year run will give
  about 15 MB.
- Only `city_outside` and two revolts occur in those 3,000 years, so
  `wp2c_branch` continues `wp1f_s101_y5000.pkl` to year 5,600. Its 404
  new states: 129 city_outside, 84 revolt_secession, 73 revolt_kin, 62
  revolt_ethnic, 21 partition, 16 revolt_pretender, 13 city_inside, 6
  shatter, 0 colony. The 1,297 states from before the branch have a
  blank origin.
- `Run("wp1f_fullclim_seed101").timeseries_long` (melted): 497,647
  rows; 19 variables per people.

**Not done.**
- No `colony` origin appeared in either run, so that tag is unexercised.
  The `n_colony_city` counter shows colonist cities do get founded. In
  those cases the city joined its home state.
- No metric reads `origin` yet. WP5 stage A tabulates it.
- Polities in a saved state from before this stage have a blank
  `origin`. If they end after the branch, they still get an
  `end_reason`.

**Next.** WP2 stage D (GIS export), which needs U on D4 (`xarray`,
`netCDF4`, `geopandas`).

### WP2 stage D: GIS export (2026-11-17, 3b8fe04)

D4 (U, 2026-11-17): yes. Installed xarray, netCDF4 (with cftime),
geopandas, shapely and pyogrio. numpy did not change (2.5.4). The
environment's versions are pinned in `sim/requirements.txt`.

**Done.** `export.py RUN` writes `<run>/export/`:
- `run.nc`: CF-1.8 NetCDF on the full 360 x 720 grid. Over time it holds
  `people`, `population`, `density` and `polity`; at the end, `road`,
  `improvements`, `land` and `salt`. Time is `days since 0001-01-01` on
  a noleap calendar, so each snapshot is its run year's 1 January. Sea
  is the fill value: NaN for numbers, -9 for ids, so -1 keeps its
  meaning of "none".
- `run.gpkg`: `cities`, `states` (one multipolygon per state per
  snapshot, built with `shapely.coverage_union_all` over cell boxes),
  `roads` (neighbour-to-neighbour lines over the travel graph, road
  over 0.3) and `events` (from `events.jsonl`). Each temporal layer has
  `t_start` / `t_end` as GeoPackage DATETIME. They are written from
  `datetime64[s]`, because pandas' default nanosecond unit cannot hold
  years before 1677. Year 0 is written as year 1, because Python dates
  start there.
- `names.csv`: cities, states and the 15 coded landmasses, with an empty
  `name` column.
- The script reads both files back and checks that city points fall on
  land.

**Runs (exports only; no simulation).**
- `wp1f_fullclim_seed101` (8,000 years): 8 s. `run.nc` 28 MB (80
  snapshots), `run.gpkg` 8 MB (1,880 cities, 7,197 state snapshots,
  4,213 road segments). All 1,880 cities are on land, and every state
  polygon is valid. There is no events layer, because the run predates
  `events.jsonl`. Population summed from the grid at 8,000: 140.5M.
- `wp2c_branch` (5,000 to 5,600) and `wp2c_sanity_seed101`: both have
  events layers (185 and 226 points). All cities are on land.

**Not opened in QGIS.** I checked the files only with xarray and
geopandas. Whether QGIS's temporal controller takes the noleap NetCDF
time axis and the DATETIME fields as intended is untested. GDAL's
NetCDF driver may show time as bands rather than as a time axis; the
mesh layer should read the time axis.

**Choices to check (C).**
- Density uses the cell's land area (`area_km2` in the world file), not
  the full 0.5° square.
- Roads join each pair of neighbouring cells whose stock is over 0.3. They
  are not routed along the actual travel paths, so parallel neighbours
  give a ladder pattern in dense road areas.
- State snapshots come from `history.npz` (every 100 years); the
  `people` and `cities` values come from its `st_*` arrays.

**Next.** WP2 is complete. In the README's order, WP3 (visualization)
can start now; WP4 needs WP1, which is partial (see the stage B and D
entries).

### WP1 stage D, voyages (2026-11-17, 4466cfd)

U, 2026-11-17: do it, the change in histories is fine.

**Done.** `voyages` no longer works lineage by lineage:
- It draws all of a tick's voyages at once: one Poisson draw for the
  number per lineage, and one uniform draw for each voyage's source cell.
- It runs one `query_ball_point` with a radius per voyage.
- It works out the fixed part of each target's weight in one pass: `Kf`,
  distance, terrain and the K x eat > 300 floor. A landing changes none
  of these, because K depends on the lineage and the cell's land, not
  on who lives there.
- Ships then land one at a time, and each rechecks its remaining targets
  against the landings before it.

Random draws come in a new order, so histories differ. One small change
in rule (C): a cell counts as a target (thin natives, not a city) only
from the start of the tick. A source cell that drops under COL_THIN
while sending colonists cannot be landed on until the next tick.
Documented in `docs/rules/colonization.md`.

**Runs.**
- Profile, 40 ticks from `wp1f_s101_y5000.pkl`: `voyages` went from
  0.96 s to 0.64 s (-33%). Its share of step time fell from 7.9% to
  5.6%. `Kf` calls dropped from 2,502 to 40. Most of what is left is
  the per-voyage loop: about 70-140 voyages a tick reach it, at about
  65 us each.
- `wp1d_voy_seed101` (8,000 years, 463 s, sharing the machine with
  another run): 126M people at the end against 140M for
  `wp1f_fullclim_seed101`. The five baseline seeds ranged from 108 to
  178M. It had 644 cities and all ten peoples. The realism measures
  fall within the baseline's spread. The largest state is bigger (4.45M
  against 3.49M km2), and more of the cities alive at year 4,000 had
  ended by 6,000 (0.48 against 0.32). With one seed I cannot tell
  whether either is more than noise.
- Its war maps were redrawn with `figures.py`. The run had loaded
  `runio` before `load_history` was added to it (WP3 stage A was being
  edited during the run).

### WP3 stage A: snapshots (2026-11-17, 5bf9a66)

**Done.**
- `--hist-every` (ticks). The default HIST_EVERY is now 5, or 25
  years (C; it was 20). `run.json` records `hist_every` and
  `frame_every`.
- `Sim.snapshot` stores a dict per snapshot:
  - per cell: people (int8), lineage (int32), polity (int32), minority
    people (int8), population as float16 log1p, and the herding flag;
  - per snapshot: the state and trade-tie tables as before, plus a city
    table (cell, id, urban size, polity, capital flag).
  `upgrade()` turns an older state's tuples into these dicts, with
  lineage and minority set to -1, herding to False and no cities, and
  keeps its cadence at 20.
- Writing: each flush writes only its new snapshots, to
  `history_parts/h<first index>.npz`. The end of the run writes
  `history.npz` whole and deletes the parts. A new run in an old folder
  first clears the old parts and `history.npz`. The flushes no longer
  recompress the whole history each time.
- `runio.load_history` reads the whole file or, for a killed run, the
  parts. It always returns `pop` as float32 heads, decoding
  `pop_log1p`. `Run.history`, `figures.py` and `turnover.py` use it.
- Readers that assumed 100-year spacing:
  - `tradewars.gif` keeps one frame per GIF_STEP = 100 years.
  - `export.py` has `--every-years` (default 100), which replaces
    `--states-every`. 320 snapshots of float grids would be about 1 GB.
  - `metrics.turnover` and `turnover.py` find their windows by year.
  - `landmass_volatility` takes the spacing from the file; its numbers
    are now less coarse.

**Runs.** `wp3a_seed101` (8,000 years, 482 s, on a shared machine)
gives 126.34M people and 644 cities at the end, the same as
`wp1d_voy_seed101`, so snapshots read state only.
- `history.npz`: 32.2 MB for 320 snapshots, against 13.5 MB for 80
  before. That is under the brief's 60 MB, so I did not store polity or
  lineage as changes between snapshots. Population is 21.4 MB of it;
  lineage 6.2 MB; herding 1.3 MB; people 1.2 MB; polity 0.7 MB.
- The float16 log1p round trip: largest relative error 0.39% (median
  0.18%) on 1M values from 5 to 40,000 heads. The last snapshot against
  `final_state.npz` also differs by at most 0.39%.
- The last snapshot holds 644 cities (216 capitals). 29% of cells are
  herding and 1,505 have a minority.
- `export.py` and `turnover.py` still read the older 100-year files
  (`wp2c_sanity_seed101`).

**Next.** Stage B (offline renderer, Mollweide). It is mostly written in
the working tree and not committed; see its entry.

### WP3 stages B and C: offline renderer, Mollweide, state colours, change layers (2026-11-17, 1149de9)

One commit for both. The offline renderer needed state colours from
polity ids, which is stage C's first item, so I wrote that directly
instead of a stopgap.

**B, done.**
- `wsim/maps.py` holds the drawing:
  - `Snap`: one moment of a run.
  - `Proj`: grid to pixels, plate carrée or Mollweide.
  - Layers drawn on the 360 x 720 grid; `panel` and `frame` assemble
    them.
  `render(sim)` (`render.py`) builds a `Snap` from the live Sim and
  calls `maps.frame`, so the run's frames and the offline ones share
  the code. `legacy_map` and `lineage_map` are unchanged.
- Projection: Mollweide as an index array from the closed-form
  inverse, computed once per run. Points go through the forward
  projection, with 8 Newton steps on 2 theta + sin 2 theta =
  pi sin(lat). Borders are found on the projected label image. The map
  keeps the plate carrée crop's latitudes. At scale 2 a Mollweide
  frame is 1440 x 1164; plate carrée stays 1440 x 1104.
- `render_run.py RUN`: `--layer`, `--proj`, `--format mp4|gif|png`,
  `--every`, `--from-year`/`--to-year`, `--scale`, `--fps`. It reads
  `history.npz`, `run.json`, `wars.csv` (for the header's war count),
  `polities.csv` (parents) and the cached world, and imports no
  simulation step. MP4 is H.264, yuv420p, padded to even size; stage D
  only has to add layouts.
- `docs/running.md`, "Drawing a finished run".

**C, done.**
- `wsim/colors.py`: one colour per state for life. The hue stays within
  0.045 of its people's; lightness ranges 0.28-0.80 and saturation
  0.30-0.95 (HLS). States are coloured in order of first appearance.
  Each takes the first of 32 candidates (seeded by its id) that is at
  least 70 ("redmean" distance) from every already-coloured state it
  ever borders, in any snapshot, and from its parent. Otherwise it takes
  the candidate farthest from them. It uses the snapshots alone, so old
  runs get it too. The live render still uses `polity_color`, which is
  untouched.
- Layers `state_age` and `people_age`: years since the cell last changed
  state or people, on a log scale from 25 to 2,000 years.
- Turnover strip under the maps: per landmass group, the share of ruled
  cells whose state differs from 100 years before, with the current
  year marked.
- Labels for the ten largest states sit at the centre of the largest
  piece: 8-connected, joined across the date line, at the cell nearest
  the piece's mean position. Labels that would overlap are skipped.
  This applies to the live frames too.

**Runs and checks.**
- `wp3b_sanity_seed101` (3,000 years, 103 s): 29.0M people, 41 cities,
  38 states, with frames from the new `render(sim)`. Its
  `final_maps.png` looks as before. The run began before the label
  change, so its frames still put labels at the capital.
- Live render against the committed one, on `wp1f_s101_y5000.pkl`: the
  same size, with 0.15% of pixels different (labels and rings, now
  chosen by counting the state's cells). 0.06 s a frame against 0.04 s;
  Mollweide 0.10 s.
- `render_run.py wp3a_seed101`: 320 frames in 27 s, a 3.4 MB MP4. It
  also reads old 100-year runs (`wp1f_fullclim_seed101`, no city dots).
- **Before/after pair, year 8,000 of `wp3a_seed101`:**
  `runs/wp3a_seed101/final_maps.png` (old live render, plate carrée,
  colours from `polity_color`) and
  `runs/wp3a_seed101/render/states+peoples_mollweide/f00000.png`
  (Mollweide, `colors.py`). The southern continent and the polar strip
  shrink to their true relative area. Neighbouring states of one people,
  near-identical before, are now distinct, while each people's hue
  still reads.
- Year 6,000, `states,state_age,people_age`: young state borders are
  bright around the Elf, Dwarf and Snake-folk state clusters. The
  people-age layer is almost all dark (2,000+ years) apart from coasts
  and a few frontiers, which matches the review's finding that peoples
  barely move. The strip starts at 1.0, because new states count as
  change, and then sits at about 0.1-0.4, noisily.

**Choices to check (C).** The colour constants (hue spread, ranges,
minimum distance); the age scale (25 to 2,000 years, inferno); "changed
state" counts a cell passing to or from no state; the strip is not
smoothed.

**Not done.** The offline frames have no dragons, because
`history.npz` does not hold them. Their header has population only, not
lineage counts or technology stages.

**Next.** Stage D (video layouts; the HTML viewer is optional and needs
U).

### WP3 stage D: video (2026-11-17, 42d3a85)

**Done.**
- `render_run.make()` is callable from code. MP4 is H.264, yuv420p,
  8 frames a second, as stage B set it up. The GIF option stays.
- Each finished run writes `history.mp4`: states above peoples,
  Mollweide, one frame per snapshot, with the turnover strip.
  `write_outputs` calls `render_run.make` after the metrics, and a
  failure there loses nothing else. `worldsim.py --no-video` skips it.
  `history.gif` from the in-run frames is still written: dropping it
  would change what the user is used to, so that is U's call.
- `render_run.py --landmass G`: only that group's (or code's) box, at
  scale 4 by default. `maps.frame(crop=)` crops each panel, and the
  header's legend wraps to the width.

**Runs.**
- `wp3d_sanity_seed101` (3,000 years, 113 s against 103 s without the
  video): 29.0M people, 41 cities, 38 states. `history.mp4` has 120
  frames (1440 x 1280) at 1.1 MB.
- `render_run.py wp3a_seed101 --landmass W --layer states` at year
  7,000: a 737 x 1038 frame of the western group, with legend in two
  columns and the strip.

**Not done.** The optional HTML viewer (item 3). The brief says to ask
U first.

### WP3 stage D: HTML viewer; history.gif dropped (2026-11-17, 374139a)

U, 2026-11-17: yes to the viewer, and `history.gif` is not needed.

**Done.**
- `history.gif` is no longer written; `history.mp4` replaces it. The
  in-run `frames/` stay, because `final_maps.png` is the last of them.
  The docs and `worldsim.py`'s docstring are updated.
- `viewer.py RUN` writes `<run>/viewer.html`, and every run now writes
  one at its end. The page holds:
  - a time slider with play, four layers and both projections;
  - a click on a city or state for its CSV row and its events;
  - event years that jump the map there;
  - views that can be linked by URL hash.
  The browser draws the maps from embedded per-cell data, by the same
  rules as `maps.py`. The data is stored as gzipped changes between
  snapshots; see running.md.

**Checks.**
- `wp3a_seed101`: 3.6 MB, built in about 2 s. `wp1f_fullclim_seed101`,
  an older run with no city table: 1.8 MB.
- Headless Chrome screenshots:
  - The default view, year 8,000: the map matches `render_run.py`'s
    frame.
  - `#year=6000&layer=state_age&state=1240`: state P1240's row (origin
    `revolt_secession`) and its 1,451 events.
  - `#year=7000&layer=peoples&proj=platecarree&city=1500`: city 1500
    ringed, with its row.
- **Not tested:** mouse clicks, play, and the arrow keys. They were not
  driven in a browser; only the hash path to the same `show()` and
  highlight code was.

**Choices to check (C).** Density in the peoples layer has 16 levels,
not continuous. Events are listed newest-last, with the first 400
shown.


### WP4 stage A: food ledger (2026-11-17, 83775fa)

**Done.**
- `food_flows` passes its unsmoothed flows to `food_ledger`
  (`diagnostics.py`), which sums each tick per world, people and state.
  `record()` writes the century means to `food.csv`.
- The lines are produced (land, city boost), eaten, taken (rent, tax,
  tribute), lost (EXT_EFF, vassal carriage), received (local, capital,
  vassal) and created (trade, boost). Two shares go with them, and some
  leak checks: `gap`, `unplaced`, `cap_unused`, `received_smoothed` and
  `taken_capacity`.
- New `metrics.food_ledger`, by millennium, in `metrics.json`.
  `runio.Run.food`.
- `upgrade()` adds the accumulator to old states (`new_state_v3`).
- Documented in `running.md` (outputs, table columns),
  `diagnostics.md` (new section and metrics row), `open-questions.md`
  and `run-log.md`.

**Runs.**
- `wp4a_short` (600 years): a smoke test.
- `wp4a_seed101` (8,000 years, `--no-video`, 475 s): 126.34M people
  and 644 cities, identical to `wp1d_voy_seed101`, so the records
  change nothing.
  - Created food as a share of produced: 0.001 in the first millennium
    rising to 0.095 in the last.
  - As a share of city food: 0.31-0.42.
  - Trade is 0-27% of created food; the city boost is the rest. Table
    in `run-log.md`.
- `wp4a_branch` (`wp1f_s101_y5000.pkl` to 6,000): exercises `upgrade()`
  and the `taken_capacity` column.

**Findings.**
- Taken = received + lost exactly on the unsmoothed flows (gap 0 in
  every century). That holds by construction, since both sides come
  from `T`.
- The brief's "1 - exp(-d/FF_CAP_KM) share that never reaches a
  capital" is not lost. The code spends it in the cell's own city.
- **Leak:** a minority's capacity is debited at its people's rate, but
  `T` counts only the main lineage. That food (3.7-4.8% of the take)
  vanishes. A one-off split at year 5,000: main-lineage debit 1.9647M
  against T 1.9650M; minority debit 0.089M, uncounted.
- Capital food at a cell with no ruling people feeds nobody (1.1%).
- Neither leak is fixed (records-only stage). Both are logged in
  `open-questions.md`.

**Decisions for stage B (U, 2026-11-17).** D5: accept the population
fall. D6: keep the city boost ("city limit") with the modifications.
U also asked for stages B and C to follow tonight, with provisional
decisions marked for review.

### WP4 stage B: debited trade (2026-11-17, 672415b)

D5 and D6 answered by U (above). U asked for B and C to follow tonight,
with provisional decisions marked for review in the morning.

**Done.**
- New switch `trade_debit`. It is the first entry of a new
  `params.OPTIONAL` list, switched on by `worldsim.py --on trade_debit`
  (also on a branch).
- **Provisional (C): off by default.** "Done when" puts the default to
  U, and every other switch is on by default, so a separate list was
  needed. `--off all` and old states are unchanged.
- `states.debit_trade`: surplus = TRADE_SURPLUS (0.5, C) x max(0,
  produced - eaten - taken).
  - The flow per tie is today's gravity term, one way, from more to
    less surplus per head.
  - It is scaled to the exporter's surplus and debited across its
    surplus cells as `tr_x` (main lineage only) in `Kf`, smoothed at
    FISC_EMA like `loc_in`.
  - It arrives at the importer less exp(-d / FF_CAP_KM).
- Provisional choices (C):
  - d is capital to capital (`food_dist` exists only from capitals);
  - pairs beyond the food graph's reach do not trade food;
  - each tie carries one term one way, half of what was created before;
  - an exporter's flows are scaled together, so they do not depend on
    tie order.
- Ledger: `trade_out`, `trade_in`, `lost_trade`, `gap_trade`.
  `created_trade` is 0 under the switch. The metric gains trade sold
  and lost by millennium.
- Docs: structural.md (new section), model-description.md,
  rules/cities.md, switch-inventory.md (an "Optional switches" table),
  running.md (`--on`, columns), diagnostics.md, run-log.md,
  open-questions.md (the default decision, with the table).

**Runs.**
- `wp4b_smoke`: a branch from 5,000 to 5,300 with the switch on.
- `wp4b_{on,off}_seed{101,103}`: 8,000 years, `--no-video`, 530-680 s
  each, two at a time.
- With the switch on:
  - population -11% in both seeds;
  - urban share down a third;
  - largest city -45% and -31%; largest / 10th 2.34 -> 1.70 and
    3.22 -> 2.61;
  - rank-size slope steeper, not flatter (-0.36 -> -0.42, -0.35 -> -0.43);
  - trade feeds 3-4% of city food instead of about 40%; 63% of traded
    food is lost in carriage;
  - net exporters are smaller states with spare land;
  - states -20% and wars -30%, which the brief did not predict.
- `gap_trade` is 0. `final_maps.png` of `wp4b_on_seed101` looks normal:
  ten peoples, 190 states, 729 cities.

**The brief's stop rule.** "If the city hierarchy flattens again, report
it and stop." The overall slope did not flatten; the top did (largest /
10th). I read this as not triggering the stop. Since the switch is off
by default, nothing in the default model changed. Review this.

**Surprise.** `wp4a_seed101` and `wp4b_off_seed101` run the same
mechanics. They differ only in summation order inside `food_flows`,
yet end at 126M and 156M. Single-seed differences under about 20% are
noise.

**Not done.** Making the switch the default (U). Port-to-port carriage.
The minority leak from stage A (open-questions).

### WP4 stage C: deaths and growth account (2026-11-17, f777567)

**Done.**
- The dragon growth cut is moved out of `deaths.csv` into `growth.csv`
  (`forgone_dragon`, majority and minority). A dragon's fight with a
  settlement is now the cause "dragon attack".
- `growth.csv` per century, per people and `ALL`: start, end, change,
  natural, removals by cause, `made`, `forgone_dragon`, `net_<phase>`
  for 13 step phases, and `residual`.
  - `acct_mark` after each phase of `step` (two bincounts each) diffs
    heads and the cumulative removals recorded by `dead()`.
  - Natural increase is `grow`'s change plus its removals.
- Item 3: `famine`'s remainder dies back in `grow` and is counted once
  as hunger. A minority's die-back was not counted and now is.
- Gaps found by the account:
  - recorded as removals: raid takeover losses, `displaced`,
    `expelled`, `dwindled`;
  - shown as `made`: merchant quarters, posts and garrisons.
- **Mechanic fixes (simple, as the brief allows):**
  - a double takeover band is debited twice;
  - refused colonists stay home.
- A branched state's first century subtracts the deaths it carried in,
  so it closes too.
- New `metrics.growth_account`; `runio.Run.growth`; `upgrade()` adds the
  account (`new_state_v4`).
- Docs: rules/population.md (new section), structural.md, diagnostics.md,
  running.md, run-log.md, open-questions.md.

**Runs.**
- `wp4c_smoke`: branches from year 5,000, used while finding the gaps.
- `wp4c_seed101` and `wp4c_seed103`: 8,000 years, `--no-video`.
  - The account closes: residual 0 in every row.
  - All world phase nets are 0 except founding arrivals, about 5e-5 of
    natural increase.
  - Seed 101 ended at 109M (156M and 126M before, from two runs of the
    same older code). Seed 103 ended at 161M (166M before).
  - I read the seed 101 difference as noise, but did not run a batch.

**Choices to check (C).**
- The phases are grouped (for example, "states" covers tidy through
  `pref_spread`). Expelled, displaced and dwindled are listed as
  removals, though in a richer model they would go somewhere.
- `made` is shown, not removed. Merchants and garrisons still appear
  from nothing; making them come from the guest's cells would change
  the mechanic.

**WP4 "done when".**
- `food.csv` closes with zero created trade food under `trade_debit`:
  yes. `created_trade` is 0 and `gap_trade` 0. The city boost is still
  created, as D6 keeps it.
- The deaths account closes: yes.
- Docs: yes.
- The `trade_debit` default is put to U: open-questions.md, "Make
  `trade_debit` the default?", with run-log's table.

**For the morning (U).**
1. Make `trade_debit` the default? I recommend yes.
2. Port-to-port carriage for traded food: 63% is lost capital to
   capital.
3. Fix the minority leak in the take, from stage A
   (open-questions.md)?

### WP4 D: the three morning decisions (2026-11-18, 45cd42d)

**Decisions (U, 2026-11-18):** make `trade_debit` the default; carry
traded food port to port; fix the minority leak from stage A.

**Done.**
- `trade_debit` moved from `OPTIONAL` (now empty) to `FEATURES`.
  `--on` also accepts defaults, so a branch from an older state can turn
  it on (old states keep their own switches, as before).
- Carriage between the nearest pair of the two states' cities
  (`states.trade_dist`, multi-source Dijkstra over the food graph from
  the exporter's cities, cached; entries of ended states pruned).
- The take is worked out per lineage: own and subject groups each pay
  their rate on their own capacity, "peasants eat first" per group.
  `ff_xo`/`ext_x` are the groups' effective rates. The trade debit
  `tr_x` is now charged to both lineages. `produced` includes the
  minority's harvest.
- Docs: structural.md (new section), run-log.md, open-questions.md
  (both questions marked decided/fixed), switch-inventory.md,
  running.md, model-description.md, rules/cities.md.

**Choice to check (C).** "Port to port" is implemented as the nearest
city pair. Over water that is port to port, because sea edges are cheap;
between land neighbours it is border town to border town. A strict
ports-only rule would have stopped land neighbours without ports from
trading food. Say if you want the strict form.

**Runs.** `wp4d_smoke` (branch, 300 years), `wp4d_seed101`,
`wp4d_seed103` (8,000 years). Table in run-log.md.
- `taken_capacity` = `taken` exactly; ledger gaps and growth residual 0.
- Carriage loss 63% -> 20-25%. Traded food 3-4% of city food.
- Population at 8,000: 106M (101) and 166M (103), against 109M and 161M
  with created trade food (stage C code). B's -11% fall did not recur;
  two seeds and three simultaneous changes cannot say why. Within noise.
- Largest city 68k and 106k fe (92k and 125k with created trade food).

WP4 is complete. Nothing pending for U from WP4 beyond the check above.

### WP5 stage A: diagnosis (2026-11-18, 75c481c)

**Done.**
- Records (no effect on the run: seed 101 ends at 105.45M, as
  `wp4d_seed101`):
  - `sieges.csv` gains `cities_besieger`, `cities_holder`;
  - `polities.csv` gains `nb_land_mean`, `nb_sea_mean`, `nb_max`,
    `nb_none_years`, from `Sim.neighbour_record`, run each tick on the
    pairs `wars_step` draws from. No `upgrade()` entry is needed; it reads
    with defaults.
- `war_diagnosis.py RUN ...`: the five tables of the brief, as Markdown.
  Item 1 uses the `origin` tag from WP2 stage C.
- Docs: run-log.md (findings), open-questions.md ("WP5 stages B-F: what
  stage A says", needs U), diagnostics.md, running.md (columns).

**Runs.** `wp5a_smoke` (branch to 5,200; deleted), `wp5a_seed101`,
`wp5a_seed103` (8,000 years, 529 s and 710 s).

**Findings** (seed 101 / 103):
1. One-city states come mainly from cities founded outside a state. 95-97%
   of these never gain a second city, and 70-79% end when the city is
   abandoned, not in war. Ethnic revolts live a median of 20 years.
2. Siege odds follow relative size. Between equal size classes the median
   is 0.02-0.05; a 10+ city state against a 1-city state, 0.45-0.56.
   Counter-offensives are at 0.002-0.07 everywhere.
3. 64% / 73% of wars end inside a tick, 72-80% of them against a one-city
   defender. They end by a fall at the first siege (20%), by cession or
   capture with no siege (about 28%), or by submission or tribute
   (22-23%). A finer clock would not lengthen these.
4. Wars ended "defender fell" when the defender ceded its only city;
   this is a recording quirk.
5. More than half of the states that lasted over 1,000 years had 1-2
   cities and fought about one war per thousand years. They are not
   island states; they had no sea contacts. Long-lived 3+ city states
   have 1-1.4 sea-only neighbours against 10-14 for shorter-lived ones,
   with the same land neighbours. This holds within a founding cohort.
6. From year 6,000, 86-92% of the largest states' extra land pieces are
   within sailing range. Fragmentation is mostly sea empire.

**Not done.** Stages B-F. The brief says to put the findings and a
recommended form to the user first: open-questions.md, items 1-6. In
short: build B with item 3 first; defer D until B is measured; deal
with one-city founding states in F (or leave them); decide whether sea
adjacency is in scope; drop persistent borders.

**Choices to check (C).**
- Size classes: 1, 2-4, 5-9, 10+ cities.
- Contiguity reads the sailing range at the end of the run.
- Neighbour counts cover only the pairs that may go to war: land
  borders, plus coastal cities within twice the sailing range.

### WP5 stage B: odds-gated war (2026-11-18, 583d7ee)

**Decision (U, 2026-11-18):** proceed with B as stage A recommended (item
3 first); stage A's choices stand.

**Done** (switch `war_odds`, in `FEATURES`, so on by default):
- **Declaring.** Deterrence is a logistic in log R (ODDS_MID 0.7,
  ODDS_W 0.35). Its floor is ODDS_FLOOR (0.05) x min(1, R / 0.7) x
  min(1, desperation + enmity + faith). `war_bound` still bounds it.
- **Besieging.** Sieges, and counter-offensives, are laid only at
  odds >= SIEGE_MIN (0.15). Below that the attacker ravages the target
  city's hinterland (chance = its violence; RAVAGE_K 0.1 x violence
  die; improvements fall as in a raid) or sits. A war with no siege for
  WAR_STALL (15 yr) ends "abandoned".
- **Item 3.** Before each siege, a defender facing odds >= SUBMIT_ODDS
  (0.6) submits with chance SUBMIT_K x the scaled excess x (1.2 -
  cohesion) x (0.5 + dominance). The old rule fired only at odds of
  about 0.9. A defender never cedes its last city.
- **Record fix (all settings).** A cession closes the war as "ceded"
  before the city moves.
- Also: `wars.csv` `ravages`; death cause and city shock "ravage";
  `growth.csv` `dead_ravage`. Metrics report city-outside foundings
  apart (`founded by a city outside a state, share`, and the one-city
  measures without them), as recommended in stage A.
- Docs: rules/war.md, model-description.md, structural.md,
  switch-inventory.md, running.md, run-log.md, open-questions.md.

**Runs.**
- `wp5b_smoke`: branch, 300 years; deleted.
- `wp5b_seed101`, `103`: first form, with a flat floor.
- `wp5b2_seed101`, `103`: the adopted form.
- Table in run-log.md.

**Results, adopted form against stage A** (seed 101 / 103):
- wars -33% / -9%;
- sieges taken 0.46 / 0.51, from 0.22 / 0.24;
- submission or tribute ends 0.29-0.30 of wars, from 0.20;
- wars ending inside a tick 0.59 / 0.63, from 0.63 / 0.73;
- one-city states: median life 100 / 70 yr, from 100 / 35;
- largest state 4.2 / 7.0 M km2, from 5.0 / 6.9;
- population 104.9M / 135.2M, from 105.5M / 165.7M.

**Surprises.**
- **The flat floor was looser than the old rule** at long odds. Wars at
  a strength ratio under 0.5 rose from 1% to 13-14%, and population
  fell 15-19% in both seeds. I replaced it with the R-scaled floor; the
  numbers and the reason are in params.py.
- **Peer wars fell** (share 0.012-0.016, from 0.021-0.027).
- **Seed 103's population is 18% lower**, through natural increase, not
  war deaths, which fell. I could not tell this apart from seed noise
  with one seed. Logged in open-questions.md.

**Not done.**
- Sea adjacency: not in scope; left unchanged.
- No 5-seed batch. Suggested before stage D, for the population and
  peer-war questions.

**Choices to check (C).**
- Every number above.
- `war_odds` is on by default, as switches are (`--off war_odds`
  restores the old rules except the record fix).
- Counter-offensives get the same siege threshold.
- Ravaging uses the attacker's violence as both its chance and its
  scale.

**Next.** Stage C (time constants in years) needs no decision. Stage D
waits on the batch, per open-questions.md.

### WP5 stage B addendum: site defence, ruler generalship (2026-11-18, c87fa80)

**Asked by U (2026-11-18).**
- Each city gets a random defence boost: most alike, a few vulnerable,
  a few very hard to take.
- Some rulers are better at offense. This does not change their chance
  of going to war, but at war their state punches above its weight, with
  the boost fading over later reigns.

**Done** (two switches, on by default; numbers C):
- `site_defence`: a per-site multiplier on terrain defence,
  clip(exp(0.12 t3), 0.5, 3). It is drawn once per cell on its own
  stream (`new_state_v5`, also in `upgrade()`). `Sim.city_def` reads it
  in sieges, counter-offensives, cessions and deterrence.
- `ruler_mil`: each ruler's talent g ~ exponential(0.1), capped at 1.
  The state attacks at 1 + g + legacy; at each succession, legacy
  becomes 0.5 x (legacy + g). It applies to the besieger's strength and
  the cession test, not to defence or deterrence. rulers.csv has
  `offense`.
- Docs: rules/war.md, model-description.md, structural.md,
  switch-inventory.md, running.md, run-log.md.

**Runs.**
- `wp5x_smoke`: branch, 300 years; deleted.
- `wp5x_seed101`, `wp5x_seed103`: 8,000 years. Table in run-log.md.

**Results** (seed 101 / 103):
- Talented rulers (g over 0.3) take cities or vassals 1.4-1.9x as fast
  as the rest.
- The site effect is weak. Hard sites are sacked about half as often in
  seed 103; seed 101 shows no clear pattern. Because of the siege
  threshold, a hard site is attacked only at good odds.
- Wars -29% / -24% against `war_odds` alone; not traced.
- Population 92.6M / 154.8M against 104.9M / 135.2M, opposite
  directions, so read as noise.

**For U.**
- Is the site spread wide enough? 1 in 200 sites is above 2.0x.
- A ruler of a 1-2 city state never succeeds (succession runs only at
  3+ cities), so a small state keeps its founder's talent until it
  grows.

### WP5 stage C: time constants in years (2026-11-18, c04c487)

**Asked by U (2026-11-18), alongside the stage:** widen SITE_DEF_SD a
bit; let rulers of small states have successions, so that a gifted ruler
might make a small state grow fast (as Cyrus did).

**Done.**
- `params.over(p, years, span)`: the chance over a step of an event
  quoted per SPAN (5) years, or the share lost. At DT = 5 it returns p.
- Converted (values unchanged at DT 5):
  - truces: war end 6 ticks -> TRUCE_WAR 30 yr; vassal breakaway and
    defection at a lord's death 2 ticks -> TRUCE_VASSAL 10; partition
    heirs 4 ticks -> TRUCE_HEIRS 20. `self.truce` holds years.
  - war age and last siege held in years (`w["start"]`,
    `w["last_siege"]`); ending WAR_END0 0.12 + WAR_END_K 0.006 x years,
    per 5 years via over(); WAR_DONE, WAR_CEDE, COUNTER_K per 5 years
    via over().
  - WAR_COST 0.005 per tick -> 0.001 per year x DT; the 0.5 cap on the
    chance of war -> WAR_P_CAP 0.1 per year x DT (in `war_bound` too).
  - FISC_EMA 0.2 per 5 years via over() (fed, crowd, extraction, local
    and trade food smoothing).
  - trade-tie decay x 0.9 per tick -> TIE_DECAY 0.1 per 5 years.
  - `sea_adjacency` every 4 ticks -> SEA_ADJ_EVERY 20 years.
  - SUPPLY_GRACE 4 ticks -> 20 years.
  - plague 0.04 per tick, gap 10 ticks -> PLAGUE_P 0.008 per year,
    PLAGUE_GAP 50 years; drought relief 0.35 -> DROUGHT_REC per 5 years.
  - siege toll and failed-siege cohesion named SIEGE_TOLL, SIEGE_COH.
- `upgrade()` converts truces, war clocks and the plague gap of old
  saved states from ticks to years (flag `clock_years`).
- **U's changes:** SITE_DEF_SD 0.12 -> 0.18 (C value: 1 site in 65
  above 2x, was 1 in 194; 1 in 18 above 1.5x). SUCC_MIN_CITIES = 1 (was
  a literal 3); successions now run in their own pass after revolts.
  `--set SUCC_MIN_CITIES=3` restores the old rule.
- Docs: model-description.md, rules/war.md, structural.md, run-log.md,
  open-questions.md (two entries).

**Left as they are (stage C), with reasons.**
- Siege toll, cohesion per failed siege, submission and ravage draws,
  capture and sack effects: they are per siege, not per time. What
  needs a decision is how many sieges a war gets per year. Now it gets
  1 + floor(2 x logistics) per tick. This is the main choice for stage
  D; open-questions.md.
- "Once per tick" caps (one sack per war, one cultural spike per state),
  and the per-tick accumulators `revolted`, `sup_win`, `sup_loss` that
  culture reads and resets. Listed for stage D.
- The minimum reign `max(DT, ...)`.
- Diplomacy and rebellion rates were already per year x DT; their bare
  numbers (0.004, 0.005, 0.0025, vassal annexation 0.004) stay unnamed.
- Event-level numbers in `capture`, `sack`, `revolt`, `disputed`.

**Runs** (8,000 years, standard settings): `wp5c_seed101`,
`wp5c_seed103`, and `wp5c_s3_seed101` (old succession rule). Table in
run-log.md.

**Results.**
- Nothing broke. Population 81.4M / 142M (stage B addendum: 92.6M /
  155M). Peoples, cities and states as usual on the seed 101 map.
- War counts in single runs are mostly path noise. Seed 101 went from
  1,761 to 2,988 wars between two runs that differ only in the site
  spread and the order of draws.
- **Small-state succession gives no Cyrus-like bursts.** Reigns that
  begin in a 1-2 city state reach 5+ cities about 2 times in 1,000,
  whatever the ruler's talent. The largest such expansions were under
  rulers of low talent with long (Elf) reigns. The reason: talent does
  not enter the decision to declare (U's form), and a one-city state
  declares about once in 300-400 years. Rulers of talent over 0.3
  declare less often than the rest (0.14-0.18 per century against
  0.19-0.35), on 28-32 wars per run.
- Reigns logged rose from about 2,000 to 8,000-15,000 per run.

**For U.**
- If you want the bursts, the ruler's edge has to enter the attacker's
  own reading of its odds, so that a gifted ruler of a small state
  picks fights. That reverses "does not change their chance of going to
  war". Your call; open-questions.md.
- Growth in 7000-8000 fell to 0.009%/yr in both seeds with small-state
  succession (0.029 in seed 101 without it). One seed each; a 5-seed
  batch would settle it.

**Next.** Stage D (yearly political step) needs a decision on sieges per
year (open-questions.md). The 5-seed batch suggested after stage B is
still not done.

### WP5 stage D: yearly political step (2026-11-18, 0b1c30d)

**Decision (U, 2026-11-18):** do D, E and F in order; sieges get a
length; D8 yes (camps).

**Done** (switch `pol_step`, on by default; numbers C):
- `Sim.politics` runs diplomacy, war and rebellion DT / DT_POL (5)
  times a tick, with `self.year` at each sub-year and `self.dtp` the
  sub-step's length. Every rate inside reads `self.dtp`; chances per 5
  years go through `over(p, self.dtp)`.
- After a sub-step in which a city changed hands, `pol_refresh` redraws
  territory and scales strength by the change in weighted people. A
  state founded in the tick takes its parent's strength per head.
- Sieges have a length: ceil(exponential(SIEGE_YEARS 1.0 x defence))
  years, 1 to SIEGE_MAX 8. The defence is 1.4 x terrain x site x walls,
  x 1.25 at a capital. The toll is spread over the siege and the siege
  is decided at its end on the odds then. Logistics slots run at
  distinct cities. Code: `siege_odds`, `sieges_open`, `siege_start`,
  `sieges_run`, `siege_end`.
- Off: one step per tick, sieges decided when laid (the old path).
- `sieges.csv` gains `siege_years`. Docs: rules/war.md,
  model-description.md, structural.md, switch-inventory.md, running.md,
  run-log.md.

**Runs.** `wp5d_seed101` (also saved its state at year 5,000 in the
scratchpad, for branch tests), `wp5d_seed103`. Table in run-log.md.

**Results.**
- Median war 4-5 years, from 0. Wars ending within 5 years: 0.50 / 0.60,
  from 0.73 / 0.79.
- Still about one siege per war. The ending rule closes most wars before
  a second siege. "Peace" endings rose and cessions fell.
- Population 64.1M / 125M, from 81.4M / 142M. Not through war deaths,
  which fell or held. Plague differs most, and it follows the run's
  path. Unresolved with one seed each.
- Run time -8% / +16%.

**Not done.** "Once per tick" caps (one cultural spike per state, the
`revolted` / `sup_*` accumulators) left as they are.

**Next.** Stage E. It replaces the age term of the ending rule with
exhaustion, which may let campaigns run to several sieges.

### WP5 stage E: armies as a stock (2026-11-18, c65846f)

**Done** (switch `army`, on by default; forms from the brief's four
points, numbers C):
- `army_step`: states at war (and allies who joined) raise toward
  ARMY_SHARE 0.04 of their people, closing dtp / ARMY_RAISE (2 yr) of
  the gap, from their own people's cells. Survivors go home in peace;
  an ended state's army is lost.
- Food: `Sim.army_x` adds to the ruling people's removal rate in `Kf`,
  the army's heads over their capacity (`K_own`), at most 0.5. New
  `food.csv` line `taken_army`, also inside `taken_capacity`.
- Field share f scales siege, counter-offensive and cession strength;
  city defence x (0.5 + 0.5 f). Declaring still reads whole strength.
- A decided siege kills 20% of the loser's army and 5% of the winner's
  (deaths "battle", `growth.csv` `dead_battle`). The fortress toll
  falls on the army.
- Ending per 5 years: WAR_END0 + EXH_K 25 x the larger side's soldiers
  lost / people (replaces the age term). Replaces WAR_COST.
- `heads()` counts soldiers, so the people account stays closed
  (residual 0 in the branch test).
- Fixes needed for branching: `upgrade()` restarts the food-ledger
  accumulator when its length changes; streamed CSV headers are the
  union of row keys.
- Docs: rules/war.md, model-description.md, structural.md,
  switch-inventory.md, running.md, run-log.md.

**Runs.** Branch test from `wp5d_seed101`'s year-5,000 state (400 yr,
deleted); `wp5e_seed101`, `wp5e_seed103`. Table in run-log.md.

**Results.**
- Sieges per war 0.73 / 0.72 (from 1.0 / 0.86); wars of 3+ sieges
  6.5-7%. The muster delay leaves a new war's attacker below SIEGE_MIN.
- War length unchanged (median 4-5 yr, 90th percentile 15).
- Battle deaths 22M / 94M, larger than the levies they replace.
- Population 83.4M / 128M (from 64.1M / 125M); wars up 104% / 21%.

**For U.** The campaigns of several sieges the brief expected have not
come from D or E. The likely lever is the muster: an attacker that
chose its war could start with its army partly raised. Not built.

**Stage F.** Design note `WP5F-camps-design.md`, with three decisions
for U. No code.

### WP5 stage F: polities without cities (2026-11-18, 0c236c7)

**Decisions (U, 2026-11-18):** camps outside the city table; a defeated
camp scatters or becomes a vassal; no number in mind for the threshold.

**Done** (switch `camps`, on by default; numbers C; design note
`WP5F-camps-design.md`, with the two departures marked):
- A camp polity has `P["camp"]` (seat, also the capital) and no cities.
  `territory` adds camp seats as sources; reach = CAMP_REACH 300 x
  cohesion x (1 + 1.5 x herding share). No rent, tax or tribute.
  Successions as for states.
- `camps_step`, every 25 years: per lineage, score the stateless cells
  near its densest one (heads x cohesion trait x (0.5 + hierarchy)). At
  CAMP_N or more, with chance 0.2, score the cells within a new camp's
  reach; at CAMP_N a camp forms. A camp disperses under CAMP_N / 3. The
  seat moves every 10 years.
- CAMP_N = 2.1e4: the median one-city state's own lineage's score in
  its land (`wp5d_seed101`, year 5,000).
- War: `seated()` gates declaring. A camp cannot be besieged;
  `camp_battle` once a year at the seat (camp strength x 1.5). Won:
  vassal with chance (0.5 + dominance) / 2, else scattered. `decamp`
  makes a camp holding a city an ordinary state.
- Records: `polities.csv` `camp_years`, origin `camp`, ends `dispersed`
  and `scattered`; `wars.csv` `battles`, why `camp scattered`; events of
  kind `camp`.
- Docs: rules/states.md, model-description.md (13.4), structural.md,
  switch-inventory.md, running.md, run-log.md.

**Departures from the design note.**
- Reach base CAMP_REACH 300, not REACH0 120. REACH0 gave a camp one
  cell.
- Formation scored on the land the camp would rule, not 500 km. The
  first form (`wp5f1_*`) made about 6,000 short-lived camps per run.

**Runs.** Branch tests from the year-5,000 state (deleted);
`wp5f1_seed101`, `103` (first form); `wp5f_seed101`, `103`. Table in
run-log.md.

**Results** (seed 101 / 103):
- 487 / 527 camps; median life about 270 years; 24-31% take a city;
  almost none grow past 3 cities.
- Land in a state at the end did not grow: +0.008 / -0.04 of land
  cells. 3+ city states -24% / -15%.
- Population and minority shares about as before.

**For U.**
- The brief's hoped-for herder route to large states is not there.
  Camps that take a city become one-city states with the usual odds.
- Camps may crowd city states out of land; untraced.
- WP5 is now complete in its stages. The 5-seed batch suggested since
  stage B would settle which of B-F's population and war-count shifts
  are real.

### WP6 stage A: growth-rate experiment (2026-11-18, d3aa08e)

**Done.**
- New constants (C) in `params.py`, used by `land.grow` for majority and
  minority: FRONT_K 1.5 and FRONT_END 0.5 (the old literals 1.5 and the
  `2` in 2p/K); R_SCALE 1.0 (multiplies each lineage's r); R_MAX 0 (no
  cap; else a ceiling on the effective yearly rate, declines uncapped).
  Defaults reproduce the old model: `wp6a_base` matched `wp5f_seed101`.
- R_SCALE does not scale the dragon cut, which is a separate cause of
  death. A lower R_SCALE therefore makes dragons relatively deadlier.
- `docs/upgrade/tools/wp6_growth.py`: the brief's measures (timeline,
  plague recovery, shares by millennium, land occupied, arrivals), plus
  the volatility measures from `wsim.metrics`.
- Docs: rules/population.md, model-description.md section 7,
  run-log.md (table), open-questions.md (plague confound).

**Runs.** Seed 101 at four settings (`wp6a_base`, `wp6a_rmax03`,
`wp6a_s05`, `wp6a_s033`) and seed 103 at three (`wp6a_*_s103`; base =
`wp5f_seed103`), all 8,000 years. The seed 103 runs took about 2.5
hours each because the machine was loaded (load average up to 30).

**Results** (run-log.md has the table; seed 101 / 103):
- R_MAX 0.03 alone is a small change: first city +150-300 years,
  recovery unchanged (55 / 70 years median to 90%).
- R_SCALE 0.5 with R_MAX 0.03: first city 1,120 / 865 (from 360),
  10M people +1,400-2,000 years, steel 5,425 / 5,955 (from 6,050 /
  4,940). Recovery 85 / 75 years (from 60 / 65). Population at 8,000
  -25 / -42%. Wars -64 / -74%.
- R_SCALE 0.33 with R_MAX 0.02: steel none / 7,695. Recovery 155 / 100
  years. Population at 8,000 34 / 36M.
- Volatility fell as growth slowed, the opposite of the brief's aim.
  The cause is that plague frequency scales with urban population, so
  slow worlds have fewer plagues (1-10 against 15-23).
- Population still tracks capacity once land fills (mean pop / K
  0.8-0.9). The brief's diagnosis ("the history of population is the
  history of K") is unchanged by any setting. Slower r stretches the
  timeline more than it lengthens crises.

**Recommendation (C), for D7.** If U accepts a later first city (about
year 900-1,100) and 10M people about 2,000 years later, adopt R_SCALE
0.5 with R_MAX 0.03: steel still arrives before 8,000 in both seeds,
and recovery is about 20-40% slower. R_SCALE 0.33 conflicts with "steel
as the final technology over 8,000 years" (U, 2026-11-09) unless runs
lengthen to about 10,000 years. If the aim is crises that last,
neither setting does much. The next step is the lagged capacity named
in the brief (destroyed improvements and herds rebuilding over
decades), or plague that is not tied to city size. Either needs U.

**Not done.** Stage B (adopt) waits on D7. No 5-seed batch.

**Next stage needs to know.** Under R_SCALE, early-history measures
(first city, war counts) shift by more than the seed spread, so any
later baseline must be rerun after B.

### WP6 stage B: adopt (2026-11-18, b1913d7)

**Decision (U, 2026-11-18, D7):** R_SCALE 0.5 and R_MAX 0.03 as the
defaults; runs stay 8,000 years.

**Done.**
- `params.py`: R_SCALE 0.5, R_MAX 0.03 (U->C). FRONT_K and FRONT_END
  unchanged (C).
- Docs: rules/population.md (what the setting costs in timeline),
  model-description.md section 7, startup.md (the head start is worth
  less now; values left as they are), README.md decision register (D7),
  BASELINE.md (new baseline table), run-log.md, open-questions.md.
- `--years` stays 8,000 (U). `running.md` needed no change: it holds no
  growth numbers, and the head-start note went into startup.md, where
  the head starts are described.

**Runs.** `wp6b_seed101`-`104`, `106`, 8,000 years, standard settings.
Seed 101 reproduces `wp6a_s05` exactly. Five seeds rather than "a run or
two" because the baseline table it replaces is a five-seed range.

**Results** (ranges over five seeds; run-log.md and BASELINE.md):
- First city 565-1,120; 10M people 2,260-2,795; steel 4,995-7,345 (all
  seeds reach it; two within about 850 years of the end).
- Population at 8,000 56-97M (108-178M in `wp1f_fullclim_`).
- Plague recovery to 90%: median 65-90 years.
- Fewer states reach three cities (129-416, from 334-914 in `wp1f`),
  but they live longer (median 204-474 years). Part of this is WP5.
- Elves are the largest people in four of five seeds (29-56%); they were
  already 20-69% in `wp1f`.

**Not done.**
- Contingency (`realism.py --cross`) not remeasured.
- Saved states for branching not remade (open-questions.md).
- Head-start values not changed: with slower growth the early peoples
  hold about a third as much land when the latecomers arrive (1.1-1.4%
  against 3.7-3.9%). Whether to lengthen the head starts is for U.

**Next stage needs to know.** Compare against `wp6b_` from now on, not
`wp1f_fullclim_`. Population still sits near capacity once land fills;
if crises are to last, the next step is lagged capacity or plague not
tied to city size (stage A entry), both needing U.

### WP6 stage C: epidemics and upkeep (2026-11-18, b1bafe1)

Not in the brief. **U (2026-11-18):** build both plague that spreads over
time and slow rebuilding of food capacity, at once; plague should reach
people outside states; which does what can be tested later with a switch
off. Forms and numbers C.

**Done.**
- `epidemic` (on): `plague_onset` (per city: 5e-5/yr x min(1, people in
  fe / 3e4) x (1 + trade ties)); `plague_step` spreads each epidemic up to
  60 rings a tick over the land grid and short sea crossings, chance per
  infected neighbour 0.9 x d/(d+1) x susceptibility, plus jumps along
  trade ties to tied states' largest cities; each cell struck once;
  stateless people included. Old rule kept as `plague_burst` (`--off
  epidemic`). New state `Sim.epi` (in `upgrade()`).
- `upkeep` (on): improvements lose up to 0.1 a year where a cell's people
  fall below 0.7 of their 50-year mean (`Sim.pmem`, in `upgrade()`).
- Records: events `plague` / `outbreak` at an epidemic's end, with
  `start` and `trail` (cells and deaths per tick). `wp6_growth.py`
  measures recovery from `start`.
- Docs: rules/disasters.md, rules/population.md, model-description.md
  (7, 17.2), structural.md, switch-inventory.md, running.md, run-log.md,
  open-questions.md.

**Runs.** `wp6c_seed101`, `103`, 8,000 years. A first form of each was
run on both seeds and discarded (see run-log.md): 10 rings a tick left
every big epidemic at the 100-year cap; upkeep against farming K halved
improvements everywhere.

**Results** (against `wp6b_`, seed 101 / 103):
- 18 / 25 epidemics, most after year 5,000; median 1.3 / 3.4M dead; the
  largest reach 11-13% of land cells and 109-154 states. Most deaths in
  the first 5-20 years, then a thin tail.
- Recovery to 90% median 100 / 80 years (85 / 75); in seed 101 the slow
  tail is longer (90th percentile 365 against 210 years).
- Volatility did not rise consistently; the largest 100-year falls are
  smaller, because a wave spreads deaths over decades.
- Population at 8,000 -17 / -25%; steel at 7,340 / 6,500 (5,425 /
  5,955); 3+ city states -34 / -32%; wars -40 / -14%.

**For U.**
- Steel came within 660 years of the end in seed 101. A 5-seed batch
  would show whether slow growth plus epidemics pushes steel past 8,000
  often enough to need longer runs.
- "Crises that last" got only a little closer: recovery is slower, and
  the world is smaller, but population still tracks capacity.
- `wp6b_` is no longer the current-default baseline; `wp6c_` (two seeds)
  is. A fresh 5-seed batch was not run.

### WP7 stage A: design note (2026-11-18, 5138b4c)

`docs/upgrade/WP7-design.md`. Main departure from the brief: slot arrays
(S = 4, slot 0 the plurality, today's `pop`/`mpop` as views) instead of
a presence table, so stage B changes storage only and can be checked by
an exact rerun. Coexistence by niche overlap (herding vs farming, biome
fit) rather than a floor. Four questions for U at its end. Nothing built.

### WP7 stage B: presence table (2026-11-18, 1a17b6e)

**Decisions (U, 2026-11-18, D9):** presence table rather than slots; niche
overlap for coexistence; raids between peoples in one cell; the share
fleeing = 1 − the attacker's violence. Layout (U): the first two rows of
each cell at fixed positions (row = cell, row = N + cell), further rows
appended from 2N on. Recorded in `WP7-design.md` and the README register.

**Done.** `Sim.rows_new` / `rows_bind`: the table (`rc`, `rp`, `rl`, `rh`,
`rm`); today's per-cell arrays are views of its first 2N rows, so no
routine changed. `__getstate__` / `__setstate__` keep the views tied to
the table across saves; `upgrade()` converts older states. Docs:
structural.md.

**Runs.** `wp7b_seed101` (8,000 years): `events.txt` and
`timeseries.csv` byte-identical to `wp6c_seed101`. A save at year 3,000
continued to 3,500 ended identical to the run that saved it (test runs
deleted).

**Next stage needs to know.**
- Stage C adds rows past 2N. Appending must grow the arrays, then call
  `rows_bind()`; any routine holding a local reference to `self.pop` etc.
  across an append would then hold a stale array. Keep appends at the
  ends of routines (settlement, minorities), or re-read after.
- Rows past 2N are invisible to every routine that reads `pop`/`mpop`.
  Stage C must go through the list in `WP7-design.md` section 6 and make
  each routine that should see every row read the table (`rc`, `rh`, ...)
  instead. The design note's per-routine table is the checklist.
- Price (`diagnostics.price`) still counts main rows only (design note
  section 7).

### WP7 stages C and D: shared cells and flight (2026-11-18, a7dc06b)

U asked for the rest of WP7 in one session, results to review next
morning. Both switches on by default; numbers C.

**Done.** `wsim/shared.py`: extra rows in the presence table (queued
writes, flush at phase boundaries, compaction), niche-overlap competition
(`grow_shared`), movement into held cells (`infiltrate`), raids inside a
cell (`inner_raids`), ordering rows by food-equivalents (`rows_sort`,
replacing the swap), flight (`flee`, `lost_rows`; share 1 − attacker
violence, U). Hooks in growth, raids, war, plague, states, food ledger,
dragons, minorities, Price, records. Counters `n_infiltrate_heads`,
`n_refugees`, `n_raid_inner`; `final_state.npz` holds the table. Tool
`docs/upgrade/tools/wp7_mixing.py`. Docs: model-description 12.4,
rules/population.md, switch-inventory, structural, running, run-log,
open-questions.

**Faults found and fixed during the stage:** the row sort keyed minority
places by the wrong cell (minority rows were never filled); a per-cell
violence array passed to rows unmapped (crash); merchant quarters lost
their cap; `infiltrate` read crowding against raw K rather than K x fill
preference. The first pair of 8,000-year runs had the last two faults
and was discarded.

**Runs.** `wp7c_seed101`, `103` (8,000 years), against `wp7b_seed101` and
`wp6c_seed103` (switches off).

**Results** (run-log.md):
- Mixing rose only a little: heads outside their cell's plurality 2.6% /
  2.0% (2.2% / 2.2% off); ~140 cells per run now hold 3+ peoples over
  10%; plurality turnover slightly up.
- Movement into held cells is small (at most 0.2-0.6M heads per
  millennium); entry room is what limits it.
- No people floods the map (largest 26% / 48%); spread between peoples
  unchanged.
- Refugees up to 0.2M / 1.0M per millennium late.
- Population, states and wars move by about the seed difference, in
  opposite directions between seeds. Runs about 25% slower.

**For U.**
- Shared cells work, but on their own they do not make peoples move much.
  The open-questions entry names the causes that would (conquest that
  settles land, deportation, ruler weight against resistance); each needs
  U.
- Cascades (stage D's measure) are not measured: refugees are not
  recorded by destination.
- Some routines still ignore third and further peoples (structural.md).

### WP8 stages A, B and C: climate fields, climate in the sim, floodplain (2026-11-19, e293026, ad5305c)

U asked for all of WP8 in one session. D10 (U): report first. D4 (U):
rebuild the world from the scripts on the new machine, so the build's
own packages (opencv-python-headless, rasterio, scikit-image) were
added. All forms and numbers are C.

**Machine setup.** This is a new machine: no `~/.venvs/worldsim`, no
`gis/world.gpkg`, and run folders without their contents.
- Recreated the venv on Python 3.12 (Homebrew python@3.12) from
  `requirements.txt` plus the three build packages, now pinned.
- Rebuilt `world.gpkg` with `build_world_gis.py`. Every committed preview
  and `registration.json` came out byte-identical.
- No earlier run is available here, so new reference runs are needed.

**Done.**
- **A** (`climate_world.py`):
  - The fields: temperature (insolation profile, lapse rate,
    continentality, upwelling), seasonal range, GDD, precipitation
    (moisture carried on each circulation band's prevailing wind, with
    meridional transport and orographic lift), PET, Budyko AET, runoff
    and aridity.
  - Twelve parameters are fitted so a fixed Köppen/UNEP rule reproduces
    `fic_biome`.
  - `derive_world.py --v2` writes `gis/world_v2.gpkg`.
  - `worldsim.py --world v2`; `run.json` records `world`, and the run
    loader uses it.
  - QA maps: `gis/qa/climate_*.png`.
- **B:**
  - `world_v2`'s runoff and lake rain keep each drawn biome's mean and
    take the climate's gradient within it. Rivers, basins, lakes and
    soils are rederived.
  - Switch `climate_fields` (on, but it acts only on a world with the
    fields): steppe and dryness from aridity, and farming and herding
    terms from GDD × aridity, normalised within each biome. The
    steppe's cut on rain-fed farming is dropped under it.
- **C:** switch `floodplain` (OPTIONAL, off by default). Irrigation is
  20/km² on valley length × width, where width = 5 km × √(Q/1000), × 3
  on alluvium, × exp(−relief/0.5), and at least 40 km at deltas.
- Docs: world-data, model-description 2.3, rules/population,
  switch-inventory, running, run-log, open-questions; README D4 and D10.

**Runs:** `wp8_v1_seed101` (old world), `wp8b_off_seed101`,
`wp8b_on_seed101` and `wp8c_fp_seed101`, all seed 101, 8,000 years.

**Results** (run-log.md, maps in `gis/qa/climate_runs_seed101.png`):
- **Climate against the drawn biomes: mean agreement 0.56.** By biome:
  tundra 0.99, desert 0.89, temperate forest 0.41, grassland 0.26,
  jungle 0.25. The conflict is coherent:
  - the drawn map has jungle and forest at 40-75°S beside the ice cap;
  - and temperate forest across 0-30°N.

  The fit's parameters at their bounds say the drawn map wants no
  equatorial rain belt. `gis/qa/climate_biome_disagreement.png` maps
  it.
- **Rivers:** 6,243 → 3,332 cells (10.7% → 5.8% of land). They become
  coastal, and the southern supercontinent's interior network is mostly
  gone. Endorheic cells rise 1,024 → 5,800 and lakes 508 → 1,594.
- **Population at 8,000:** 52M (v1), 40M (v2 off), 80M (v2 on), 70M
  (v2 on + floodplain).
  - Under `climate_fields`, people move toward the tropics: 51-55% at
    |lat| < 15°, and under 2% beyond 45°, against 10% on v1.
  - With denser coasts come 3-4 × the states with 3+ cities and 5-6 ×
    the wars.
- **The Dwarves collapse under `climate_fields`.** Their homeland near
  68°S is drawn jungle and forest, but it has 0 GDD. Their share goes
  20% → 5%, and under 0.5% with floodplain on. That is the guide's
  stop condition (diversity), so it is reported, not tuned.
- **Floodplain**, statically: irrigation × 0.29 on small rivers, × 1.76
  on great rivers, × 1.78 on 51 delta cells. In the run, the largest
  city is 121k against 95k, and the river share of people is about the
  same.

**For U (decisions):**
1. D10: what the drawn southern jungle belt is. If it is cool temperate
   rainforest, the jungle class there could use a different rule. If
   the drawn map stays the truth even against GDD, the farming term
   could use aridity only. Either change would stop the Dwarves'
   collapse.
2. Whether `world_v2` becomes the default. If it does, rerun the
   baseline and update BASELINE.md (the brief's last step, not done).
3. Whether `floodplain` becomes a default.

**Not done.**
- Ecotones unchanged; the aridity field could replace them (open
  questions).
- Lakes in closed basins are not sized by their water balance.
- Plotting tools other than the run loader still build the old world.
- One seed only.

### WP8: D10, new defaults and baseline (2026-11-19, 9c0afdd)

**Decisions (U, 2026-11-19).**
- The drawn southern jungle belt is "probably an old error".
- The climate's biome replaces the drawn one wherever they disagree (U
  chose "everywhere" over the frozen belt only, or south of 40°).
- `world_v2` is the default world, and `floodplain` is a default switch.

**Done.**
- `world_v2` has `syn_biome`, the climate rule's biome. The build
  (runoff, soils) and the simulator read it in place of `fic_biome`.
  `fic_biome` and `world.gpkg` are untouched.
- Runoff and lake rain are the climate's own; the within-biome
  normalisation of runoff is gone. The farming and herding terms keep
  theirs (C: the biome factors stay the base).
- `params.GPKG` is `world_v2.gpkg`, and `GPKG_V1` / `--world v1` the old
  world. `floodplain` moved to FEATURES; OPTIONAL is empty again.
- Runs without `world` in `run.json` load `world.gpkg`.
- Docs: world-data, model-description, rules/population,
  switch-inventory, running, open-questions, README (D10), BASELINE.

**Runs.** New baseline `wp8d_seed101`-`104` and `106`, 8,000 years:

- population 35-50M;
- 82-89% of people within 30° of the equator;
- rivers hold 35-37% of people on 5.4% of land;
- Dwarves 2-18%, largest people (Elves) 35-47%.

The full table is in BASELINE.md, and run-log.md has the entry.

**For the next session / U.**
- The climate's parameters were fitted against the drawn map, errors
  included. With the map no longer the truth, the fit's target is open.
  The fit wanted no equatorial rain belt and dry interiors, and desert
  now covers 30% of land. A refit against a physical prior (an ITCZ,
  Earth-like rain-out lengths) instead of the drawn map would be the
  next step, if U wants one.
- `sites_v2.json` (resource sites) was placed on the old world's biomes
  and not regenerated (U's world file; ask first).
- Lakes in closed basins are not sized by their water balance: 2,249
  lake cells.

### WP8: physical climate refit, lake sizing, sites v3 (2026-11-19, 6d9eea2)

**Asked by U (2026-11-19).**
- Refit the climate.
- Fix the lakes.
- Regenerate the resource sites.

**Done.**
- **`climate_world.py`.**
  - The drawn-map fit (`fit`, FIT_KEYS, BOUNDS) is gone.
  - PARAMS take physical values: L_RAIN 2,000 km. P0 is calibrated so
    global rain is 1.0 m/yr (`calibrate`).
  - Agreement with the drawn map is reported, not fitted (mean 0.38).
- **`derive_world.drainage`.** A closed basin's lake fills from its
  lowest cells only as far as net evaporation balances the inflow; the
  rest of the basin is alluvial fill. Lake cells 959 on `world_v2`.
- **`make_sites.py --v3`.** Writes `sites_v3.json`: the v2 rules on
  `world_v2`, with hearths re-placed by the v1 rule. It is in the
  standard command (GUIDE, running). The old site files stay.
- **Docs:** world-data, model-description, open-questions, run-log,
  BASELINE.

**Runs.** New baseline `wp8e_seed101`-`104` and `106`
(BASELINE.md, last section):

- population 33-51M;
- the Elves fall from 35-47% to 1-8%, and the end shares are more even;
- states are fewer and smaller but longer-lived; 37-57% of people live
  in states;
- the urban share halves.

**For the next session / U.**
- **Desert nearly vanishes (1.2M km²).** PET from degree-days is too low
  in the subtropics; a radiation- or humidity-based PET is the
  physically grounded fix. Not done, because it changes the world again.
- **No desert crop hearth** (no desert river cells). Resolved by the
  Penman-Monteith rebuild (2026-11-20): all 13 hearths are placed.
- **The Elves' fall and the weaker states** are results of the new world,
  not tuned; worth U's look.

### WP8: Penman-Monteith PET (2026-11-20, aa0f052)

**Asked by U (2026-11-20).** "Bring in sunshine & humidity & rerun".

**Done.**
- **`climate_world.penman_pet`.** FAO-56 Penman-Monteith over 12
  months, replacing degree-day PET (PET_K is gone). Inputs:
  - monthly insolation;
  - sunshine 0.85 to 0.35 by rain;
  - dew point at the night minimum, less up to 2.5 °C in clear air;
  - day-night range 6-16 °C by sunshine.
- New QA maps: `climate_rel_humidity.png`, `climate_sunshine.png`.
- `world_v2` and `sites_v3.json` were rebuilt; desert is 5.0M km².
- Docs: world-data, open-questions, run-log, BASELINE.

**Runs.** Baseline `wp8f_seed101`-`104` and `106`:

- population 34-63M;
- Dwarves 10-35%, Elves 1-3%;
- otherwise close to `wp8e`.

**For the next session / U.**
- **Subtropical rain is about 0.3 m/yr.** The rain-out floor under
  sinking air (Z_BASE 0.25) keeps the subtropics semi-arid; Earth's
  great deserts get under 0.1. Not changed.
- **The Elves' fall** (35-47% at `wp8d`, now 1-3%) is a result of the
  new world, not tuned.

### WP8: rain-out under sinking air lowered (2026-11-20, e08aeda)

**Asked by U (2026-11-20).** "Let's lower it", and refine the physical
world first, before any work on the peoples.

**Done.**
- `climate_world` Z_BASE 0.25 → 0.1. `world_v2` and `sites_v3.json` were
  rebuilt.
- Desert 22.8M km², grassland 23.4M km², in subtropical desert belts at
  about 15-35°.
- Docs: world-data, open-questions, run-log, BASELINE.

**Runs.** Baseline `wp8g_seed101`-`104` and `106`:

- population 26-40M;
- 17-46 states with 3+ cities;
- 155-418 wars;
- no steel in any seed.

**For the next session / U.**
- **U's priority** is the physical world before the peoples.
- **Still simplified in the climate:**
  - no seasons in the circulation (no monsoon, no migrating ITCZ);
  - rows show seams at the band edges (30°, 60°);
  - no ocean currents beyond upwelling;
  - `world.gpkg` on disk predates the lake sizing.

### WP8: monthly circulation, ocean currents, seams (2026-11-20, 5d07290)

**Asked by U (2026-11-20).** The three expansions: seasons and monsoon,
band-edge seams, ocean currents.

**Done** (`climate_world.py`).
- **Twelve-month circulation** (`SEASONS`, `fields`).
  - The ITCZ is at s × (ITCZ_SEA 5° + 13° × land fraction).
  - The trades blow toward it (per-cell meridional direction in
    `march`).
  - BAND_SHIFT 5°; W_ITCZ 10 → 5.
- **Gyre currents** (`coast_distance`, `current_anomaly`), carried
  inland by `carry`. QA map `climate_sst_anomaly_c.png`.
- **Cross-edge exchange** (`march(prev=)`), a second pass per month.
- `world_v2` and `sites_v3.json` were rebuilt.
- Docs: world-data (model, ablation, limits), open-questions, run-log,
  BASELINE.

**Runs.** Baseline `wp8h_seed101`-`104` and `106`:

- desert 5.5M km² (was 22.8);
- population 31-38M;
- 10-36 states with 3+ cities.

**For the next session / U.**
- **Desert is small again.** The land monsoon (ITCZ_LAND 18°, Earth's
  value for an all-land column) wets the subtropics. Whether that
  reach suits these continents is open. The drawn map had far more
  desert.
- **The zonal wind still blows one way per row all year**, so there is
  no westerly summer monsoon.
- **Biomes use annual totals**, not the rain's season.

### WP9 stage A: patterns frozen (2026-11-20, 90e91c0)

**Done.**
- `docs/patterns.md` lists 30 patterns. Each has its definition (a
  function in `wsim/metrics.py`), reference and source, how rough it is,
  scale, status and the `wp8h` range.
- **Spent** (a value or form was chosen on it):
  - population at the end and the timeline (development 0.25; D7);
  - recovery;
  - urban share and city food sources (FF_RENT, FF_TRADE);
  - war count (WAR_BASE);
  - war endings (WP5 B gate form);
  - biome areas (the first climate fit; Z_BASE);
  - people shares (roster balancing);
  - trait spread between peoples (PATH_MIN, EXP_SCALE, KIN_RAID).
- **Seen, nothing adopted:**
  - rank-size slope and largest city (the capital levers);
  - state lifespans (the turnover sweep);
  - long-run growth.
- **Held out, new** (`wsim/metrics.py`; registered `citytraits` in
  `runio`):
  - `spacing`;
  - `minor_states`;
  - `peer_wars`;
  - `waterside`;
  - `rule_spells`;
  - `lineage_cities`.
- Docs: diagnostics (measure table), README index, run-log.

**Runs.** None new; the measures were read on `wp8h_seed101`-`104` and
`106` (run-log).

**Next stage needs to know.**
- **Stage B needs U** (D4: SALib, or hand-roll Morris). It is about 248
  runs: at about 600 s each, 8 at a time, that is about 5-6 hours.
- **Disk.** Each run writes about 65 MB, so 248 runs need about 16 GB;
  9.6 GB is free. The screen should run with `--no-video`, drop the
  frames, or prune as it goes.
- **Two of the new patterns are weak at present:**
  - W3: peer wars are almost absent;
  - C6: nearly every city is waterside.
- **S6's median sits on URBAN_GRACE.** Read its p90 instead.
- **Climate questions the user left open** (`wp8h` entry):
  - the monsoon's reach over land;
  - the zonal monsoon wind;
  - the rain's season in biomes.

### WP8: monsoon westerly and rain timing (2026-11-20, 23e3c6e)

**Asked by U (2026-11-20).** "Yes to monsoons having their own wind,
please do use rain seasonality, and a westerly wind is good."

**Done** (`climate_world.py`; world-data.md has the model).
- **Monsoon westerly.**
  - Each month, a second march walks the summer-side trade rows
    eastward.
  - Its rain weighs in between the equator and the displaced ITCZ,
    fading over W_ITCZ (MONSOON_W 1).
  - A first form also weighted it by land fraction × sun. It changed
    land rain by ±4%, so that weight was dropped: the ITCZ's
    displacement already holds both.
- **Rain timing.**
  - A monthly bucket (S_MAX 0.15 m) compares the real rain timing with
    the same rain spread evenly; the ratio is the timing factor.
  - AET = Fu × the factor.
  - `syn_aridity_season` (aridity × the factor) is read by the biome
    rule and, in `wsim/geo.py`, by the sim's yields.
- **New columns:** `syn_aridity_season`, `syn_warm_rain_share`.
- **New QA maps:** timing factor, seasonal aridity, warm-half rain share,
  July and January rain.
- `world_v2` and `sites_v3.json` were rebuilt.
- Docs: world-data, open-questions, run-log, BASELINE.

**Runs.** Baseline `wp8i_seed101`-`104` and `106`:
- population 35-57M;
- 18-64 states with 3+ cities;
- 289-1,225 wars;
- steel in two seeds.

**For the next session / U.**
- **The westerly barely matters**, because the meridional supply
  (V_MER 0.3) brings most monsoon rain.
- **The society grew on the same land.** Savanna farms better than
  jungle in the model; this is not traced.
- **Snake folk now lead** in three seeds. Reported only (U: peoples
  later).

### WP9 stage B: sensitivity screen (running since 2026-11-20, 23e3c6e)

**U (2026-11-20).**
- SALib or hand-rolled: either.
- Launch.
- Keep only the summaries, plus the final map.

**Set-up.**
- `tools/wp9_screen.py` holds the design: 30 parameters, Morris with
  r = 8 trajectories and 4 levels, so 248 points on seed 101, plus
  `base_seed105`. The design is in `baseline/wp9b_design.json` (SALib
  1.6.0, seed 9).
- **Ranges.** A factor of 2 either way, log-scaled, except PATH_MIN
  0.3-0.9, BUD_PRESS 0.3-0.6 and ODDS_MID 0.5-1.0.
- **Five literals were named** for it: RAID_RATE, BUD_PRESS, AGRI_INV,
  METAL_INV, CLIM_AMP. A 1,000-year run of seed 101 is identical.
- **What each run keeps** (`runs/wp9b/<point>/`): metrics.json,
  run.json, final_maps.png and the log tail. The run folder is deleted.
- **Seed noise** comes from `wp8i_seed101`-`104`, `106` and
  `base_seed105`.
- `tools/wp9_analyze.py` gives mu*, mu, sigma and mu* / noise per
  pattern of docs/patterns.md.
- **Restart** after a stop: `wp9_screen.py run -j 8` skips points
  already done.
- **When done:** write `docs/sensitivity.md` from `wp9_analyze.py --md`,
  with the brief's conclusions. Do not use the screen to pick values.

### WP8: land clearing (2026-11-20, 53610b9)

**Asked by U (2026-11-20).**
- "Can humans clear forest to make grass/farm land?"
- Then: "cancel the screen for the moment, build this, and then rerun the
  screen after." The screen had no finished point; its eight partial
  run folders were removed.

**Done.**
- **Switch `clearing`, on.** `Sim.clear` is the cleared share of jungle
  and temperate-forest cells.
- **Clearing.** Farmers clear toward the land in use and herders burn
  toward 0.5 × use, at CLEAR_RATE 0.01/yr of the gap.
- **Regrowth** at CLEAR_REGROW 1/150 per year.
- **Effect.** In K2 the cleared share farms, forages and herds at
  grassland's values (the ecotone blend).
- **Improvements** now stand for field works only.
- **Records:** `cleared_km2` (timeseries) and `clear` (final_state).
- Docs: structural, model-description 7.1, switch-inventory, rules/
  population, running, diagnostics.

**Runs.** Baseline `wp8j_seed101`-`104` and `106` (run-log, BASELINE).
- 13-15M km² cleared.
- Population 40-46M.
- 46-117 states with 3+ cities.
- Steel in three seeds.
- Snake folk lead everywhere (reported only).

**Not modelled:**
- clearing's effect on movement and defence (fixed edge costs);
- its effect on climate and erosion;
- burning by foragers;
- clearing in wars.

### WP9 stage B relaunched (2026-11-20, 6a63c34)

The screen restarted on the `wp8j` code by `runs/wp8j_then_screen.sh`,
after the baseline. The design is the same 249 points. Seed noise comes
from `wp8j` plus `base_seed105` (`wp9_analyze.py` defaults to `wp8j`).

### WP9 stage C: Earth test scoped (2026-11-20, 785fb84)

**Done.** `docs/earth-test-plan.md` covers:
- **Inputs.** Datasets with licences to confirm and rough sizes, and a
  new builder `earth_world.py` producing the same columns.
- **Two climate routes:**
  - observed climate, which tests the society model alone;
  - `climate_world.py` on Earth, which also tests the climate model.
- **Roster.** One people, dragons off, two kinds of start (known hearths
  or the sim's own rules), and a fixed time zero.
- **Scoring against nulls:**
  - Reba et al. city sites;
  - HYDE density;
  - Seshat or Turchin's state areas;
  - timing to the nearest millennium.
- **What a failure means.**
- **Cost:** steps A-G, about 6-9 sessions.

**Runs.** None; nothing was downloaded.

**For U (D11).**
1. Do the climate check alone?
2. Do the whole test?
3. Neither?

Recommended: 1 now; decide on 2 after the screen.
