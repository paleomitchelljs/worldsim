# Upgrade status

One entry per finished stage, newest last. See `GUIDE.md`, "Handoff", for
what an entry holds.

| WP | Stage | Status | Date | Commit |
|---|---|---|---|---|
| 0 | A git | done | 2026-11-17 | 04a5711 |
| 0 | B runs out of Dropbox | done | 2026-11-17 | 0ec5f91 |
| 0 | C run manifest and overrides | done | 2026-11-17 | d17745c |
| 0 | D streamed output | done | 2026-11-17 | 858b205 |
| 0 | E clean-up | not started | | |
| 1 | A polity table | not started | | |
| 1 | B capacity factoring | not started | | |
| 1 | C resident capacity cache | not started | | |
| 1 | D migration, raids, climate, wars | not started | | |
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

