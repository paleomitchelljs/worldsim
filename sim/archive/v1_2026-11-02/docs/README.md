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
| Map data the model reads | [world-data.md](world-data.md) |
| Rosters (sets of peoples) | [scenarios.md](scenarios.md) |
| Past runs and what each tested | [run-log.md](run-log.md) |
| Known problems and open decisions | [open-questions.md](open-questions.md) |

Code: `../worldsim.py` (model; constants at the top), `../peoples*.py`
(rosters). Every number quoted in these docs is a constant or roster value
there; if they disagree, the code wins and the doc needs fixing.

Provenance marks used throughout: **U** = specified by the user;
**U→C** = the user gave the direction, Claude chose the number;
**C** = Claude's proposal, not yet confirmed.
