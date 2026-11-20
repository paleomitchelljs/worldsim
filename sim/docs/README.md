# worldsim docs: index

## Goals

- Zero-player simulation on the world map (`../gis/world.gpkg`), to show where
  cities form, where empires stretch, and how peoples spread, fight, trade
  and collapse over thousands of years.
- Peoples never interbreed; they interact through war, trade, alliance and
  (rarely) political fusion.
- Mechanics should be physically and historically plausible, adjustable,
  and documented with their reasons.
- Model first, tuning of individual peoples second.

## Principles for culture and for judging runs (U, 2026-11-01)

- **No imposed secular trends.** A cultural trait changes only when
  something causes it (war, raids, trade, hardship, revolt, rule, contact,
  victory or defeat, life in an ordered state), plus random noise. No
  term may pull a trait in a set direction in the absence of a cause:
  no "peace pulls violence down" when nothing is happening, no decay of
  an unused disposition. Self-reinforcing loops with a cause (e.g.
  administration and technology) are fine.
- **Minimal causeless bias.** Where a form adds bias without a cause
  (e.g. a drift that leans toward the middle), keep it as small as
  possible and name it in the docs.
- **There is no "ought".** The sims show how a world evolves from a
  given start. No people has a target value, and a split that ignores
  the starting values is acceptable.
- **Judge runs on variance, not means.** A run is unrealistic when
  diversity collapses (every people converging, all lineages within a
  people identical) or explodes, not when a mean differs from what was
  expected. Check spread between peoples and within peoples, over time.
- **Parameter choices are not targets.** A rate may be set so that
  diversity survives (e.g. KIN_RAID 0.1), but never to steer a people
  toward an end state. Record such choices as C, with the reason.

## Pointers

| Topic | File |
|---|---|
| The whole model and every parameter, description only | [model-description.md](model-description.md) |
| How to run, options, outputs | [running.md](running.md) |
| Founding: wandering, head starts, founder variation | [startup.md](startup.md) |
| Intrinsic traits (growth, biome, size, food) | [traits/intrinsic.md](traits/intrinsic.md) |
| Cultural traits (violence ... tolerance) | [traits/cultural.md](traits/cultural.md) |
| Technology (farming, metal, sailing, admin) | [traits/technology.md](traits/technology.md) |
| Rules: population and carrying capacity | [rules/population.md](rules/population.md) |
| Rules: colonization and dispersal | [rules/colonization.md](rules/colonization.md) |
| Rules: cities and territory | [rules/cities.md](rules/cities.md) |
| Rules: states, cohesion, rebellion | [rules/states.md](rules/states.md) |
| Rules: war, conquest, raids | [rules/war.md](rules/war.md) |
| Rules: similarity, trade, alliance, fusion | [rules/diplomacy.md](rules/diplomacy.md) |
| Rules: lineages, inheritance, extinction | [rules/lineages.md](rules/lineages.md) |
| Rules: plague and drought | [rules/disasters.md](rules/disasters.md) |
| Draft structural mechanics (costs, fiscal, vassals, herding, land, climate, ...) | [structural.md](structural.md) |
| Diagnostics: Price decomposition, historical checks | [diagnostics.md](diagnostics.md) |
| Patterns runs are judged on (frozen; spent and held out) | [patterns.md](patterns.md) |
| Earth test: plan and cost (WP9 C; scoping only, D11) | [earth-test-plan.md](earth-test-plan.md) |
| Map data the model reads | [world-data.md](world-data.md) |
| Rosters (sets of peoples) | [scenarios.md](scenarios.md) |
| Past runs and what each tested | [run-log.md](run-log.md) |
| Known problems and open decisions | [open-questions.md](open-questions.md) |
| Upgrade plan of 2026-11-16 (review findings, work packages, session guide; all C until confirmed) | [upgrade/README.md](upgrade/README.md) |

Code (split into modules 2026-11-02; the single-file v1 is in
`../archive/v1_2026-11-02/`):

| File | Holds |
|---|---|
| `../worldsim.py` | command line (`main`; `make_sim` builds a Sim from the same arguments) |
| `../snapcheck.py` | checks a code change against a saved late-game state ([running.md](running.md)) |
| `../realism.py` | realism checks on finished runs, side by side ([diagnostics.md](diagnostics.md)) |
| `../export.py` | a finished run as NetCDF, GeoPackage and a blank names table for QGIS ([running.md](running.md#gis-export-exportpy)) |
| `../wsim/params.py` | constants and the remaining switches |
| `../wsim/geo.py` | world grid, distances, small math helpers |
| `../wsim/sim.py` | `Sim`: state, setup, the yearly `step` |
| `../wsim/land.py` | carrying capacity, climate, land, disasters |
| `../wsim/settlement.py` | founders, migration, budding, voyages, minorities |
| `../wsim/culture.py` | lineages, drift, similarity, experience |
| `../wsim/states.py` | cities, states, diplomacy, roads, rulers, revolts |
| `../wsim/war.py` | raids and wars |
| `../wsim/economy.py` | sites, goods, trade |
| `../wsim/technology.py` | invention and borrowing (and, for now, acculturation) |
| `../wsim/dragons.py` | dragons |
| `../wsim/diagnostics.py` | records, Price decomposition |
| `../wsim/render.py`, `../wsim/output.py` | maps, plots, output files |
| `../wsim/maps.py`, `../wsim/colors.py` | map drawing from one snapshot, projections (plate carrée, Mollweide), state colours; shared by the live render and `render_run.py` |
| `../viewer.py` | a run as one self-contained HTML page: time slider, layers, click a city or state for its record and events ([running.md](running.md#reading-a-run-in-the-browser-viewerpy)) |
| `../render_run.py` | a finished run's maps from `history.npz`, as MP4, GIF or PNG frames, without rerunning ([running.md](running.md#drawing-a-finished-run-render_runpy)) |

Rosters: `../peoples*.py`. `--set NAME=VALUE` overrides a numeric constant:
`worldsim.py` writes it into `wsim/params.py`'s namespace before any other
`wsim` module is imported, so every module and every default argument sees
it (2026-11-17), and `run.json` records all constants as used. Every number quoted in these docs is a constant or roster value;
if they disagree, the code wins and the doc needs fixing.

Provenance marks used throughout: **U** = specified by the user;
**U→C** = the user gave the direction, Claude chose the number;
**C** = Claude's proposal, not yet confirmed.
