# Guide for upgrade sessions

Read this before any work-package brief. It holds the rules that apply to
every stage. Where a brief and this guide disagree, the brief wins for its
own stage; say so in your handoff.

## What the project is

A zero-player simulation on a 0.5-degree world grid (`../gis/world.gpkg`,
66,895 land cells): peoples grow, migrate, farm, found cities, form states,
trade, raid, fight and collapse over about 8,000 years at 5 years per tick.
It serves a fantasy book series; the user wants to see where cities form
and how states and peoples change, on physically and historically plausible
mechanics. The user is an evolutionary biologist.

Start with `docs/README.md` (goals, principles, file index). The code is in
`wsim/`; `worldsim.py` is the command line. The docs describe the model;
where they disagree with the code, the code is right and the doc needs
fixing.

## Principles you must not break

These come from the user (`docs/README.md`, "Principles").

- **No causeless trends.** A cultural trait changes only when something
  causes it, plus noise. Never add a term that pulls a trait in a set
  direction with no cause.
- **No targets.** Never set a parameter so that a run hits a reference
  value. References (city rank-size slope, largest-state share, and so on)
  are checks. If a mechanism is right and a number moves away from its
  reference, report that; do not tune it back.
- **Judge on variance.** Report spread between and within peoples, and
  across seeds, before means.
- **Peoples never interbreed.** They may share land, trade, rule one
  another and fuse politically.
- **Do not coin names.** Continents, cities, states and gods stay unnamed
  (IDs and landmass codes only).
- **Provenance.** Mark every new rule and number in the docs: **U** (the
  user specified it), **U->C** (the user's direction, your number), **C**
  (your proposal). Almost everything you add is C.

## Environment

- Python: `~/.venvs/worldsim/bin/python` (3.12; numpy, scipy, pillow,
  matplotlib, pandas; from 2026-11-17 also xarray, netCDF4, geopandas,
  shapely; versions pinned in `sim/requirements.txt`). No numba, no pytest. Ask before installing anything
  not approved in the decision register (`README.md`, D4).
- `ffmpeg` and `git` are installed.
- **Commit and push to `origin` (GitHub) after every commit (U,
  2026-11-17).** The repository is public and that is fine.
- The machine has 4 performance cores. Run at most 8 simulations at once;
  check `uptime` first, because the user often has other jobs running.
- An 8,000-year run takes about 14 minutes on an idle machine.

### Dropbox hazards

As of 2026-11-17 the project lives at `~/Desktop/world`, outside Dropbox,
under git (remote: github.com/paleomitchelljs/worldsim). The cautions below
still apply to old run folders and saved states that remain in Dropbox.

The project sat in Dropbox and the disk is nearly full, so Dropbox turns
files into online-only placeholders. Reading one can hang for minutes.

- Never run `find`, `du`, `grep -r` or `wc` across `runs/` or `archive/`.
- Before reading a run file, check it: `ls -lO <file>` shows `dataless` for
  a placeholder. Skip those or ask the user to make the folder local.
- Write new runs, saved states and scratch files outside Dropbox (after
  WP0: `$WORLDSIM_RUNS`; before it: a folder under `/tmp` or `~`).
- Give long commands a timeout.

## Standard commands

The sweep's settings, used for every comparison:

    ~/.venvs/worldsim/bin/python worldsim.py --peoples peoples_regional \
        --starts 20 --start-vary 0.1 --vary 0 --sites sites_v3.json \
        --seed 101 --years 8000 --frame-every 100 --out <folder>

- Seed 101 is the usual test seed (101-106 if a batch is wanted). Always
  `--frame-every 100` for tests.
- `--set NAME=VALUE` overrides a numeric constant; `--off a,b` switches
  mechanics off.
- `realism.py RUNS --group` prints the realism measures side by side.

## How much to test

**Very little. This is a toy (U, 2026-11-16): do not test each step.**
Spend the session on the change, not on proving it.

- **Per stage, one sanity run at the end.** A 3,000-year run of seed 101
  with the standard settings (about 5 minutes) that finishes without an
  error, plus a glance at its last progress lines and `final_maps.png`:
  people on the map, cities and states present, population of the usual
  order. If a stage only touches analysis or drawing code, run that code
  on one existing run instead.
- **No byte-for-byte comparisons, no `snapcheck` runs, no per-commit
  testing, no scaffolding** (reference implementations kept beside new
  ones, debug assertions, test suites). Histories may differ from old
  runs after any change; that is accepted.
- **Mechanic changes: one or two full runs, then look.** Run seed 101
  (and 103 if you want a second opinion) for 8,000 years, print
  `realism.py`, and say what moved and whether it is what you expected.
  A six-seed batch is for when the user asks, or when a result is
  surprising enough that you need to know if it is the seed.
- **Switches.** Put a new mechanic behind a switch in `FEATURES` when
  that is cheap, so the user can turn it off. Do not prove that "off"
  reproduces the old model.
- If something looks wrong in the sanity run, fix it. If you cannot tell
  whether it is wrong, say so in the handoff and move on.

Still required:

- Never report a result you did not measure. Say which runs you made.
- A new array or record on `Sim` needs an entry in `upgrade()`
  (`sim.py`) if old saved states are still in use.
- Records must not change the simulation's state.

## Code conventions

- Match the existing style: numpy over Python loops on the cell grid, short
  docstrings that say what a method does and why, comments that explain
  reasons.
- Every constant goes in `wsim/params.py` with a comment and a provenance
  mark in the docs.
- Do not leave dead code after a `return`, or branches behind a flag that
  is always true. Delete what you replace; git has the history.
- Do not copy files into `archive/` any more (after WP0). Commit instead.
- Keep changes scoped to the stage. If you find a bug outside it, record it
  in `docs/open-questions.md` and leave it, unless it blocks you.

## Documentation to update with every change

| What changed | Update |
|---|---|
| A rule or a constant | `docs/model-description.md` and the matching file in `docs/rules/` or `docs/traits/`; `docs/structural.md` for structural mechanics |
| A switch | `docs/switch-inventory.md` |
| An output file or column | `docs/running.md`, `docs/diagnostics.md` |
| A batch of runs | `docs/run-log.md`: what it tested, the table of ranges, what was found |
| A problem found or a decision needed | `docs/open-questions.md` |

Write these in plain sentences. Lead with the result, give numbers with
their ranges, and say which numbers are yours (C).

## When to stop and ask

Stop and ask the user (do not guess) when:

- a stage is marked **needs U** and the prompt does not give the answer;
- the sanity run breaks and you cannot find why within the stage;
- a mechanic change collapses diversity (peoples converging, one people
  flooding the map) or empties the world;
- the fix that works would break a principle above;
- you would need to delete runs, overwrite `world.gpkg`, or change a
  roster's values.

## Handoff

At the end of the stage, append to `docs/upgrade/STATUS.md`:

- the work package and stage, the date, and the commit hash;
- what was done, in a few lines;
- which runs you made and what they showed;
- what was not done, and why;
- anything the next stage needs to know, including surprises.
