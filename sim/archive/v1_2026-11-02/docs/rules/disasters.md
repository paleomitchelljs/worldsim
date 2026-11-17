# Plague and drought

> **Draft structural mechanics (2026-10-29)** change this topic: `immunity` (plague hosts and immunity), `climate` (a structured climate that replaces the random droughts below when on). See [structural.md](../structural.md); they switch off with `--off`.

Code: `Sim.disasters`.

## Drought

- **How often:** each tick, with probability 0.08.
- **Where:** a random cell gets a drought of radius 400–1500 km.
- **How bad:** carrying capacity drops by 35–70% at the centre, tapering
  linearly to the edge.
- **Recovery:** 35% of the remaining deficit per tick.
- **Logged** as a great drought when more than 1M people are in the
  stricken core.

## Plague

- **How often:** each tick, with probability
  0.04 x min(1, urban population / 3M), and at least 50 years apart.
- **Where it starts:** in a city chosen in proportion to its population.
- **Spread:** to neighbouring states, up to 4 hops, each with probability
  0.25 + 0.6 x trade tie.
- **Deaths:** 15–35% of everyone in the states it reaches, and city cells
  lose 30% of that again.
- **Logged** when more than 200k die.

## Justification (C)

Plague scales with urbanization and moves along trade, so connected,
city-dense worlds suffer most. Drought is random and regional.
