# WP0: foundations

**Goal.** Make the project safe to change: version control, runs that
Dropbox cannot evict, a record of exactly what produced each run, and output
that survives a killed run. No mechanic changes. Testing: one sanity run
per stage (`GUIDE.md`).

**Why.** The project has no git: `archive/` holds about 40 full copies of
`worldsim.py` and two of `wsim/`. Runs live in Dropbox on a disk that is
93% full; Dropbox has already turned run files into placeholders, 19 jobs
of one batch died at launch, and `realism.py` had to learn to skip runs it
cannot read (run-log, 2026-11-09). `run.json` records switches and
`--set` overrides but no code version. All output is written by
`write_outputs` after the last tick, so a killed run leaves nothing.

Read first: `docs/README.md`, `docs/running.md`, `worldsim.py`,
`wsim/output.py`, `wsim/sim.py` (`__init__`, `run`), `snapcheck.py`.

## Stage A: git (needs U: D1)

1. Initialise a repository at `art/world` (it holds `sim/`, the world
   build scripts and `gis/`). If D1 is "separate git dir", use
   `git init --separate-git-dir <path outside Dropbox>`.
2. Write `.gitignore`: `sim/runs/`, `__pycache__/`, `*.pyc`, `.DS_Store`,
   `gis/world.gpkg` and other large binaries (`gis/previews/`, `gis/qa/`
   if large), saved states (`*.pkl`), `*.aux`, `*.log`.
3. First commit: the tree as it stands, `archive/` included, so nothing is
   lost. Second commit: remove `archive/worldsim_*.py` copies and
   `archive/wsim_*` folders. Keep `archive/v1_2026-11-02/` (the docs cite
   it as the last single-file model) and `archive/snaps/` unless the user
   says otherwise.

Done when: `git status` is clean and `git log` shows the two commits.

## Stage B: runs out of Dropbox (needs U: D2, D3)

1. Add a runs root: environment variable `WORLDSIM_RUNS`, default
   `~/worldsim_runs`. `worldsim.py` uses it when `--out` is not given;
   `realism.py`, `figures.py`, `landmass_report.py`, `timeline.py`,
   `bigcities.py`, `turnover.py` and `snapcheck.py` resolve a bare run name
   against it.
2. Do not move or delete the existing `runs/` folder yourself. List for
   the user which batches `docs/run-log.md` cites (by prefix), and let them
   decide (D3). Many of those files are placeholders; do not read them.
3. Update `docs/running.md`.

Done when: a run with no `--out` lands in the runs root, and every
analysis script accepts both a bare name and a path.

## Stage C: run manifest and overrides

1. `run.json` gains: git commit hash and a dirty flag, the full command
   line, the Python and numpy versions, wall time, and **every** numeric
   constant's value as used (not only the overrides).
2. Fix `--set`. Today `setp` (`worldsim.py`) patches a name in every
   loaded `wsim` module, because each module did `from .params import *`.
   Two weaknesses: a constant computed from another at import time keeps
   its old value, and a module imported later gets the default. Do this:
   - parse `--set`, `--city-pop`, `--city-cap`, `--dragon-*` **before**
     importing any `wsim` module except `params`, and write the values
     into `wsim.params`;
   - move any constant in `params.py` that is derived from another into a
     `derive()` function called after overrides (list them in the commit
     message; if there are none, say so);
   - keep `setp` for `snapcheck.py`, which changes constants on a loaded
     state.
   A full move to a params object (`P.NAME` everywhere) is not part of
   this stage: it touches every line that uses a constant and gains
   little once the two weaknesses are closed.
3. Check once that a run with a changed value records it in `run.json`.

## Stage D: streamed output

Today `Sim` appends to in-memory lists (`events`, `ts`, `city_ts`, `rel`,
`war_log`, `siege_log`, `revolt_log`, `ruler_log`, `price_rows`,
`food_rows`, `death_rows`, `frames`, `hist`) and `write_outputs` writes
them at the end.

1. Append-only tables (events, timeseries, city sizes, sieges, revolts,
   relations, price, city food, deaths): open a writer at the start, flush
   every `FLUSH_EVERY` ticks (C: 100) and at the end.
2. Tables whose rows are finished later (wars, rulers) or updated in place
   (cities, polities, lineages): rewrite the whole file at each flush, to a
   temporary name and then rename, so a reader never sees half a file.
3. Frames: save each PNG when it is rendered and drop it from memory;
   build `history.gif` at the end from the files.
4. `history.npz`: write at each flush the same way as (2).
5. `write_outputs` keeps only what needs the finished run (`checks.txt`,
   `chronicle.txt`, final maps, `final_state.npz`).
6. Keep each file's columns and formats as they are, since the analysis
   scripts read them. `timeseries.csv`
   takes its header from the first row; columns added later in a run would
   break streaming, so check that the column set is fixed from tick 1 and
   fix it if not.

Done when: a run killed partway leaves readable tables up to its last
flush, and `realism.py` still reads a finished run.

## Stage E: clean-up

1. Remove dead code:
   - statements after a `return` in `culture.drift_trait`,
     `war.war_prize`, `economy.kind_value`, `economy.offer`,
     `settlement.colon`;
   - branches behind flags that are always one value: `sup`, `tp`, `ce`,
     `col`, `imm_on`, `no_drought`, `betray`, `kinf = 1.0` and similar.
     Grep for local booleans assigned once; keep the live branch.
   - unused imports in every `wsim` module (each file imports the same
     dozen modules).
2. `World()` takes 13-15 s, most of it turning SQLite rows into arrays.
   Cache the loaded columns in an `.npz` beside the runs root, keyed on the
   world file's size and modification time. Every analysis script that
   builds a `World` gets the benefit.

Done when: the sanity run finishes.
