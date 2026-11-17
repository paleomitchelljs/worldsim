# Startup: founding groups

Code: `Sim.start_sites`, `wander_setup`, `wander`, `place_arrivals`,
`found_group`, `vary_peoples`.

## Groups and variation

- **Number of groups.** Each people starts as `--starts` founding groups
  (scenario default 20, **U**). A roster can set `starts` per people.
- **Each group is a lineage** of 400 people in one cell, with farming at
  0.25 and no other technology.
- **Per-run variation.** `--vary` (0.12 in current runs) jitters the people's
  cultural traits once per run, on the logit scale with sd 2.5 x vary.
- **Per-group variation.** `--start-vary` (0.1) jitters each founding group's
  cultural traits the same way.
- **Intrinsic traits are never jittered**: growth, biome fit and size, see
  [traits/intrinsic.md](traits/intrinsic.md).
- **Why 20 groups** (**U**): to widen the spread of traits within a people
  from the start. More groups widen the range of trait values, not their
  standard deviation; the standard deviation comes from `--start-vary`.

## Placement: wandering (default, U)

1. Each group is dropped on a random cell with nonzero suitability for its
   people. With `--homelands continents`, only landmasses of at least
   4M km² count (15M if there are 5 or fewer peoples).
2. **Suitability** = cell area x (0.75 forage + 0.25 farm density) x
   sharpened biome fit x (1 + 0.5 seafaring x coastal). Biome fit is
   `best * (affinity / best) ** 2.5`, the start-of-run sharpness.
3. **Each step, the group stays** with probability
   `min(0.95, suitability / its people's 95th-percentile suitability)`. The
   0.95 cap is **U**.
4. **Otherwise it moves** to one of its 8 neighbours, weighted by the square
   of suitability smoothed over about 3 cells (Gaussian, sigma 3 cells).
   - *Why smoothed* (**C**): with only immediate neighbours to judge by, a
     group dropped in the vast polar tundra random-walked and never got out.
5. **Number of steps**: 2000 (`--wander-steps`). Groups typically travel
   900–2,000 km before settling.

## Head starts (U, numbers U→C)

- **Mechanism.** A roster key `head` (years) gives a people a head start.
  Peoples with the largest `head` found at year 0; the others arrive
  `max_head - head` years later.
- **Latecomers keep wandering.** While waiting, they take 3 steps per tick
  and treat settled cells as unsuitable.
- **Arrival.** A latecomer founds at its wander position. If that cell is
  taken, it uses the best empty cell within 8 rings; if there's none, it
  falls back to `score` placement.
- **Values in `peoples_headstart`:**

  | People | Head start |
  |---|---|
  | Elves, Snake folk | 400 years |
  | Lizardfolk, Frogloks | 150 years |
  | Everyone else | 0 |

- **Why 400/150 rather than 1500/500.** With 20 groups per people, a
  1500-year head start let Snake folk and Elves fill the habitable world
  before anyone else arrived. The latecomers landed on polar tundra and
  never recovered (runs `size_seed51`–`54`).

## Placement: score (legacy, `--start-mode score`)

- Picks a site directly among cells of the people's best biome or biomes
  (affinity within 10% of the best).
- Sites are weighted by suitability.
- Founders keep at least `3500/sqrt(groups)` km (500–1800 km) apart; the
  distance shrinks if no site is left.
