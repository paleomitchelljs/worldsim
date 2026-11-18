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
| 1 | D migration, raids, climate, wars | partial (see entries) | 2026-11-17 | 17e54e7, b8c092b |
| 1 | E branching from a saved state | done | 2026-11-17 | 8aba7b8 |
| 1 | F RNG streams and new baseline | done | 2026-11-17 | 668ac79 |
| 2 | A structured events | done | 2026-11-17 | 1f51f62 |
| 2 | B run loader and metrics | done | 2026-11-17 | 8b516c7 |
| 2 | C tidy tables | done | 2026-11-17 | 8499650 |
| 2 | D GIS export | done | 2026-11-17 | (this commit) |
| 3 | A snapshots | not started | | |
| 3 | B renderer and projection | not started | | |
| 3 | C state colours and change layers | not started | | |
| 3 | D video and viewer | not started | | |
| 4 | A ledger (records only) | not started | | |
| 4 | B debited trade | not started | | |
| 4 | C deaths and growth account | not started | | |
| 5 | A diagnosis | not started | | |
| 5 | B odds-gated war | not started | | |
| 5 | C time constants in years | not started | | |
| 5 | D yearly political step | not started | | |
| 5 | E army stock | not started | | |
| 5 | F cityless polities | not started | | |
| 6 | A experiment batch | not started | | |
| 6 | B adopt | not started | | |
| 7 | A design note | not started | | |
| 7 | B presence table | not started | | |
| 7 | C competition and settlement | not started | | |
| 7 | D displacement | not started | | |
| 8 | A climate fields | not started | | |
| 8 | B yields and runoff | not started | | |
| 8 | C floodplain area | not started | | |
| 9 | A metrics freeze | not started | | |
| 9 | B sensitivity screen | not started | | |
| 9 | C Earth test scoping | not started | | |

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

### WP2 stage D: GIS export (2026-11-17)

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

