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
| 1 | D migration, raids, climate, wars | partial (budding, voyages, raids, adjacency) | 2026-11-17 | 17e54e7 |
| 1 | E branching from a saved state | not started | | |
| 1 | F RNG streams and new baseline | not started | | |
| 2 | A structured events | not started | | |
| 2 | B run loader and metrics | not started | | |
| 2 | C tidy tables | not started | | |
| 2 | D GIS export | not started | | |
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
