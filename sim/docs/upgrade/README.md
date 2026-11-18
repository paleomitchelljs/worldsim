# worldsim upgrade plan (2026-11-16)

Written after an adversarial review of the simulator: a read of `wsim/` and
the docs, measurements on finished runs, and a timed 6,000-year profile.
Everything here is **C** (Claude's proposal) unless marked **U**. Nothing in
this folder is a decision until the user confirms it; the decisions that
need confirming are listed in [Decision register](#decision-register).

## What the review found

| Area | Finding | Evidence (see [BASELINE.md](BASELINE.md)) |
|---|---|---|
| Accounting | Trade food is created, not moved. Deaths mix removals with forgone growth. | Trade is 27.5% of food brought into cities (`al_seed103`); "dragon" is 54% of `deaths.csv` |
| War | A per-tick lottery; mostly large states taking newborn one-city states | 69% of wars end inside one tick; 3.8% are between two states of 5+ cities; median siege win probability at launch 0.064 |
| States | Two thirds never pass one city; a tail lasts millennia; large states are scattered pieces | 66% one-city (median life 35 yr); 54 of 910 states lasted 1,000+ yr; the largest state is 23 pieces |
| Land | No climate field, only five biome classes; irrigation applies to whole 0.5° cells | 51% of people within 15° of the equator; 10.7% of land (river cells) holds 42% of people |
| Demography | Population sits on carrying capacity | frontier growth up to 6%/yr; world population varies 2.3% around its 200-yr mean |
| Peoples | Barely move or mix | 0.8-5% of cells change people per 500 yr; minorities 1.1% of heads |
| Contingency | The map is mostly fixed by geography and the roster | city sites agree 66-79% across seeds (chance 12%); cell population correlates 0.90-0.95 |
| Validation | 400 constants and 27 switches against about ten stylized facts | `wsim/params.py` |
| Speed | Cost scales with cells, not states | `migrate` 33%, `Kf` 25% (nested), `raids` 18%, climate 10% |
| Structure | No version control; runs in Dropbox on a full disk; all output written at the end | `archive/` holds ~40 copies; `realism.py` skips online-only runs |

## Work packages

Each brief is self-contained and split into stages sized for one session.
**Testing is deliberately light (U, 2026-11-16: this is a toy): one
sanity run per stage, as `GUIDE.md` says.**
Do them in this order unless a brief says otherwise.

| # | Brief | Changes the rules? | Depends on |
|---|---|---|---|
| 0 | [WP0-foundations.md](WP0-foundations.md): git, runs out of Dropbox, streamed output, run manifest, checks | no | - |
| 1 | [WP1-speed.md](WP1-speed.md): capacity factoring and cache, polity table, branching from a saved state, then RNG streams | no | 0 |
| 2 | [WP2-outputs-analysis.md](WP2-outputs-analysis.md): structured events, run loader, metrics, GIS export | no | 0 |
| 3 | [WP3-visualization.md](WP3-visualization.md): snapshots, separate renderer, equal-area maps, state colours, video | no | 2 |
| 4 | [WP4-food-ledger.md](WP4-food-ledger.md): closed food account, debited trade, honest deaths table | yes | 1, 2 |
| 5 | [WP5-politics-war.md](WP5-politics-war.md): odds-gated war, yearly political step, army stock, cityless polities | yes | 1, 2 |
| 6 | [WP6-demography.md](WP6-demography.md): growth rates and recovery | yes | 2 |
| 7 | [WP7-shared-cells.md](WP7-shared-cells.md): several peoples per cell, displacement | yes | 1, 4 |
| 8 | [WP8-climate-land.md](WP8-climate-land.md): climate fields in the world build, continuous yields, floodplain area | yes (new world file) | 2 |
| 9 | [WP9-validation.md](WP9-validation.md): sensitivity screen, Earth test | no | 2; best after 4-8 |

Why this order:

- **0 first.** Every later package needs version control, runs that
  cannot be evicted by Dropbox, and output that survives a killed run.
- **1 and 2 before any mechanic changes.** A speed-up is easiest to trust
  while the rules are standing still. WP2 supplies the measures every
  later package is judged on.
- **4 before 5 and 7.** War prizes and shared cells both read food; fix the
  account before building on it.
- **8 late.** A new world file moves rivers and city sites, so it
  rebaselines everything. Do it once, after the mechanics settle.
- **3 any time after 2.** It touches no mechanics.

## How to run a session

One stage of one work package per session. Open the session in
`~/Desktop/world/sim` (formerly `art/world/sim` in Dropbox) and give it:

> Read `docs/upgrade/GUIDE.md`, then `docs/upgrade/WP<n>-<name>.md`. Do
> stage <letter> only. Follow the guide's rules on testing (light) and
> reporting. When done, append a handoff entry to `docs/upgrade/STATUS.md`.

If a stage is marked **needs U**, settle the decision with the user before
starting the session, and put the answer in the prompt.

## Decision register

Recommendations are mine (C). Record answers here with the date.

| # | Decision | Recommendation | Answer |
|---|---|---|---|
| D1 | Where the git metadata lives (a `.git` folder inside Dropbox can be corrupted by sync) | `git init --separate-git-dir ~/git/worldsim.git` in `art/world` | 2026-11-17 (U): the project moved out of Dropbox to `~/Desktop/world`, so a plain `.git` there; remote `origin` = github.com/paleomitchelljs/worldsim, pushing allowed |
| D2 | Where runs live | `~/worldsim_runs` (outside Dropbox), with `WORLDSIM_RUNS` to override; keep only `metrics.json`, `run.json` and chosen figures in Dropbox | 2026-11-17 (U): `sim/runs/` in the project (git-ignored), `WORLDSIM_RUNS` overrides |
| D3 | What to do with the ~900 existing run folders | keep the batches the run log cites; delete or archive the rest to an external disk | 2026-11-17 (U): leave all 446 in the old Dropbox folder untouched; read them by full path |
| D4 | New Python packages in `~/.venvs/worldsim` (xarray + netCDF4, geopandas, SALib) | yes; pin in a `requirements.txt` | 2026-11-17 (U): yes to xarray + netCDF4 and geopandas (+ shapely, pyogrio); installed and pinned in `sim/requirements.txt`. SALib not yet asked for (WP9) |
| D5 | Trade food must come from somewhere, and world population will fall when it does | accept the fall; do not retune to restore city sizes | 2026-11-17 (U): accept the fall |
| D6 | Keep the base city-cell boost (1.5 x development), which also adds capacity from nothing | keep, but show it as its own ledger line | 2026-11-17 (U): keep, as recommended (shown as `produced_boost` in `food.csv`) |
| D7 | Lower growth rates, which stretches the early timeline (first cities arrive later) | try a few settings first; decide on the results | |
| D8 | Cityless polities (tribes, confederations, herder states) | build, as "camp" seats | |
| D9 | Several peoples per cell (the 2026-11-06 option A in full, plus C, displacement) | build after WP4; design note signed off first | |
| D10 | When derived climate disagrees with the hand-drawn biome map | the drawn map wins; climate fields vary conditions within a biome | |
| D11 | Earth test (needs public datasets downloaded) | scope it in WP9 stage C; decide after the sensitivity screen | |
| D12 | Break seed-for-seed continuity with old runs when the RNG is split into named streams | yes, at the end of WP1, followed by a fresh baseline run or two | 2026-11-17 (U): yes, no problem; also yes to a fresh seed for a branch (`--branch-seed`) and to drawing the climate's local field at reduced resolution |

## Files here

| File | What |
|---|---|
| [GUIDE.md](GUIDE.md) | Rules every session follows: principles, environment, how little to test, reporting |
| [BASELINE.md](BASELINE.md) | The measured numbers above, how each was computed, and the profile |
| [STATUS.md](STATUS.md) | Handoff log; one entry per finished stage |
| `tools/profile_phases.py` | Per-phase timing by millennium plus cProfile of the last 500 years |
| `tools/analyze_run.py` | The review's measurements on finished runs |
| `baseline/phases_2026-11-16.txt` | Profile output of 2026-11-16 |
