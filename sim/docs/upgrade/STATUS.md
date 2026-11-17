# Upgrade status

One entry per finished stage, newest last. See `GUIDE.md`, "Handoff", for
what an entry holds.

| WP | Stage | Status | Date | Commit |
|---|---|---|---|---|
| 0 | A git | done | 2026-11-17 | 04a5711 |
| 0 | B runs out of Dropbox | not started | | |
| 0 | C run manifest and overrides | not started | | |
| 0 | D streamed output | not started | | |
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
