# Colonization and dispersal

> **Draft structural mechanics (2026-10-29)** change this topic: raid take-overs leave the old people as a minority. See [structural.md](../structural.md); they switch off with `--off`.

Code: `Sim.budding`, `settle`, `pioneers`, `river_leap`, `voyages`,
`settler_lineages`, `raids` (take-overs); `World.colonize`.

Four ways a lineage takes empty land. All of them are weighted by **terrain
colonizability**:

    exp(−relief_km / 0.7) x (1 − 0.5 x wetness)

1 km of relief cuts the chance to about a quarter; swamp halves it.

## 1. Budding (two passes per tick)

- **When.** A cell buds once its crowding passes 0.45 − 0.35 x expansion.
- **Where.** It sends one band to its best empty neighbour, scored by:
  - sqrt(K) ÷ travel cost;
  - x terrain colonizability;
  - x 2 if both cells are river cells;
  - x (1 − 0.95 x separation) next to foreigners;
  - x random noise (0.6–1.4).
- **Band size.** (0.2 + 0.25 x expansion) x the source population, at least
  0.15 x the target's K and at most half the source.

## 2. Pioneer leaps

- **How often.** About 3 x expansion² x (1 + log10(cells)) attempts per
  lineage per tick, drawn from cells holding at least 300 food-equivalents
  and weighted by crowding.
- **Off-river leap.** The band jumps 2–6 cells on the same landmass, and
  settles only if the target is empty, holds at least 200 food-equivalents
  of K, and passes a colonizability roll.
- **River leap.** A leap that starts on a river follows the river with
  probability 0.6, up or downstream (`syn_flow_to`), for 6 + 30 x sail
  cells. It settles a random empty cell along the way, with the same checks.
- **Band size.** min(120 food-equivalents, 20% of the source).

## 3. Sea voyages

- **Who sails.** Crowded coastal cells (crowding > 0.5, at least 400
  food-equivalents) make about 2.5 x seafaring x (0.1 + sail) x
  sqrt(number of such cells) attempts per tick, at most 6.
- **Targets.** Empty coastal cells within 4D, weighted by:
  - K;
  - x exp(−distance/D), where D = 40 + 2500 x sail^1.5 km;
  - x terrain colonizability.
- **Band size.** min(200 food-equivalents, 20% of the source).
- **New landmass.** Landing on a landmass the lineage has never held (over
  0.2M km²) founds a daughter lineage ([lineages.md](lineages.md)).
- **Order within a tick** (C, 2026-11-17, a speed change). All of a
  tick's voyages are drawn first: how many each lineage makes and from
  which of its cells. Their targets' fixed weights (K, distance, terrain)
  are computed together. The ships then land one after another, and each
  rechecks its targets against the landings before it. Since then the
  random draws come in a different order, so histories differ from
  earlier runs. One small difference in rule: a cell becomes a target
  (thin natives under 3,000 fe, not a city) only as the tick starts.
  A source cell that drops under that line by sending colonists cannot
  be landed on until the next tick.

## 4. Raid take-overs

- **When.** A raid can empty a neighbouring foreign cell (down below 15% of
  its K) while the attacker's cell is above 60% of its K.
- **Then.** With probability equal to the raider's violence, the raider
  moves in a quarter of its population ([war.md](war.md)).

## Justifications

- **Terrain colonizability** (**U**: "topography should play a role in
  colonization"; form **C**). Mountains and swamps are slow to settle.
- **River leaps and the river budding bonus** (**U**: "rivers should
  magnify dispersal"; form **C**). Rivers are corridors for movement and
  for boats.
- **Budding replaced diffusion into empty land** (**C**). Bands that were
  too small kept getting discarded, which stalled spread.
