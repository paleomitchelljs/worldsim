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

## Plague as an epidemic (`epidemic`, on by default; WP6 C, 2026-11-18)

U (2026-11-18): plagues should spread over time and reach people outside
states. The form and every number are **C**.

- **Where it starts.** Each city can start one. A crowd disease needs a
  large enough community to keep going, and contact to bring it in. So a
  city's chance per year is 5e-5 x min(1, its people in food-equivalents
  / 30,000) x (1 + its state's trade ties, summed, up to 1). The city's
  people is the host. A city already inside an epidemic starts no other.
  Several epidemics can run at once; there is no minimum gap.
- **Spread.** Each tick (5 years) the epidemic moves up to 60 rings of
  cells over land and short sea crossings. Each infected neighbour passes
  it on with chance 0.9 x d / (d + 1), d being the target cell's people
  per km², times the target's susceptibility (1 − 0.8 x immunity), and
  x 0.7 into cells of a people other than the host. Dense land carries it
  fast; thin forager country barely carries it. Along trade it jumps: each
  tick, a state it is in passes it to each tied state's largest city with
  chance 0.3 x tie.
- **Who catches it.** Everyone in a struck cell, inside a state or not.
- **Deaths.** One mortality per epidemic, drawn from 15-35%. The host
  people die at that rate and others at 0.3 of it, all times
  (1 − 0.8 x immunity); city cells lose a further 0.3 of that. A cell is
  struck once per epidemic; survivors get immunity 0.8, which fades by
  1.2% a year.
- **End.** When the epidemic reaches no new cell (or after 100 years).
  In practice most deaths come in the first 5-20 years, as the wave
  crosses dense land; a thin tail then creeps through sparse country for
  decades, and flares again if it reaches another dense region. (A first
  form moved 10 rings a tick, about 110 km a year, so that every large
  epidemic was still spreading at the 100-year cap; 60 rings is about
  650 km a year.)
- **Logged** at its end, as `plague` over 200k dead and `outbreak` below,
  with its start year, cells, states and deaths.

### Before WP6 C (`--off epidemic`)

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
city-dense worlds suffer most. Under `epidemic` it also moves along
dense settled land at a finite speed, so a wave crosses a region over
decades and peters out in thin country; it no longer needs a state to
reach people. Drought is random and regional.
