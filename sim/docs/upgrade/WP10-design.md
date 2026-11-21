# WP10 design note: peoples that move and mix (stage B, 2026-11-21)

Everything here is C until U decides. Measures are from stage A
(`metrics.peoples`, patterns.md K6) on `wp8n` seeds 101-104 and 106.

## What stage A found

**1. The lead changes hands; it is not held from the start.**

| Year | Largest people (5 seeds) | Its share |
|---|---|---|
| 1000 | Frogfolk 2, Goblins 3 | 32-52% |
| 3000 | Goblins 5 | 25-38% |
| 5000 | Snake folk 3, Goblins 1, Humans 1 | 20-32% |
| 8000 | Snake folk 4, Humans 1 | 27-36% |

**2. Snake folk rise by density, not by conquest.** In seeds 101 and
103:
- Snake folk hold 12-15M km² at the end, about 60-70% of it jungle.
  Their density rose from 0.3-0.4 people per km² at year 3000 to
  1.2-1.6 at year 8000.
- Goblins hold 45-47M km², over a third of all land, mostly grassland
  and temperate forest, at 0.15 people per km².
- People living in jungle roughly tripled from year 5000 to 8000.

So peoples' shares follow how fast their home biome's capacity grows.
Thin grassland (WP11) keeps the largest landholder small in heads.

**3. Peoples barely mix, and conquest moves few people.**
- 2.3-2.8% of heads live outside their cell's plurality people at the
  end.
- The plurality people changed on 9-15% of occupied land between 2000
  and 8000.
- Cities taken from another people: 47-154 per run. Captures inside
  one people are two to three times as common (175-325).
- Conquerors' settlers: 0.25-0.73M heads over a whole run, against
  1.0-2.8M refugees and 1.0-2.6M heads who moved in peacefully
  ("infiltration").
- **Refugees** (seed 101, the new `refugees.csv`): 1.4M heads over the
  run. 44% fled expulsion, 40% sacks and 16% raids. Almost none reach
  empty land (0.2%); they join their own people. 6% of refugee heads
  arrive somewhere that sends out refugees itself within 50 years
  (cascades).
- A captured city keeps its people: the conqueror leaves a garrison of
  MIN_GARRISON (4%) of its population.

**4. Some of the brief's items exist already.**
- **A war aim of rule exists** (`war_goal_rule`, 20-25% of war aims).
  The brief's "no motive to rule" is out of date. What is missing is not
  the aim but its consequence: ruling a city changes little about who
  lives there.
- **State backing already removes resistance** to the ruling people's
  movers inside its own state (infiltration's `res` is 0 when the
  movers are the state's ruling people). Brief item 3 is done.
- **ACC moves traits, not membership.** Acculturation pulls a lineage's
  traits toward its neighbours'. It changes no one's people. The screen
  found it inert because no frozen pattern reads trait convergence
  between peoples. It is not a lever for mixing.

## Options

### A. Conquest that settles (recommended)

A captured city of another people gets settlers of the conqueror's
people in the city and its hinterland (cells of the city's catchment),
in place of the flat 4% garrison.
- **Size:** a share of the city's people, scaled by the conqueror's
  expansion and the state's establishment (the same `est` as
  SH_STATE). Round value: up to 20% of the population, to match
  MIN_CAP (C).
- **Where they come from:** the conqueror's own crowded cells, so the
  heads move rather than appear.
- **The conquered people:** stays, as the majority or as a minority
  under shared cells. Violence decides how many are pushed out, by the
  same flight rule as `displacement` (share fleeing = 1 − violence,
  U 2026-11-18).
- **Expected effect:** larger states seed their people across what they
  rule. With 47-154 cross-people captures per run, the effect is bounded
  by how rare those captures are.

### B. Deportation

A state moves part of a subject people out of a rebellious or newly
taken region to its core, or moves its own people in. Historical cases:
Assyria, Inca *mitma*. A new decision with its own rate, numbers all C.
- **Recommendation:** not now. A covers the "moves its own people in"
  half more simply. Revisit after A's batch.

### C. Assimilation under long rule

Today a cell changes people only when a minority outgrows the majority
(`tidy_minorities`). A subject people under a foreign state for many
generations could shift some heads to the ruler's people each year,
faster with the subject's tolerance and the ruler's proselytism.
- `acc_cross` already moves subjects' traits toward the ruler's under
  foreign rule (`rule_since`, ACC_RULE0, ACC_GENS). C would add
  membership on the same clock.
- **Recommendation:** yes, as a second switch after A. It is the
  mechanism by which empires historically changed who people say they
  are, more than by settlement.

### D. Wait for WP11 first

Since shares follow biome density (finding 2), any WP10 change will be
read against density effects that WP11 may change.
- **Recommendation:** run WP11 stage A (a trace, no rule changes)
  before building, so the WP10 batch is read on known densities.
  Building A and C does not depend on it.

## Decisions for U

1. Build A (conquest that settles)? Up to 20% of the city, scaled by
   expansion and establishment; violence decides how many are pushed
   out.
2. Build C (assimilation under long rule) as a second switch?
3. Leave B (deportation) out for now?
4. Do WP11 stage A before WP10 stage C, or after?

Whatever is built, peoples' shares are reported and not tuned.
