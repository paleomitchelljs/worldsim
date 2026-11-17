# States: cohesion, assimilation, rebellion

> **Draft structural mechanics (2026-10-29)** change this topic: `fiscal` (fed share scales strength and reach), `unrest` (elites and political stress), `succession`. See [structural.md](../structural.md); they switch off with `--off`.

Code: `Sim.new_polity`, `polity_stats`, `rebellions`, `revolt`,
`kill_polity`, `recapital`.

A state is a set of cities under one capital, ruled by a lineage. Its
`culture` is the ruling lineage's people.

## Cohesion (asabiya, after Turchin)

S runs from 0.02 to 1. Each year it changes by:

    dS = 0.04 x cohesion_trait x S(1 − S) x (0.3 + foreign-frontier share)
         − 0.004 x S x (1 + 0.5 ln(1 + cities)) x (1 + age/600)

- **What raises it:** border friction with other peoples. Each city taken
  adds +0.03.
- **What lowers it:** size and age. Each failed siege multiplies it by
  0.98, losing the capital by 0.6, and each revolt by 0.9.
- **New states start at** 0.6. A breakaway starts at 0.75, and a city-state
  left after its capital fell at 0.5.

## Strength

    strength = Σ cells: pop x size x (1 if own people, else 0.4 + 0.5 x tolerance)
               x (0.5 + violence) x metal multiplier x (0.3 + 0.7 S)

## Assimilation

Cells of the ruler's own people but a different lineage switch to the
ruling lineage at 0.8% x (0.5 + statecraft) per year.

## Rebellion

- **Chance.** Each non-capital city may revolt each tick with probability

      5 x 0.0009 x (distance/reach)² x (1.5 − S)
        x (1 + 3 (1 − similarity)(1 − 0.6 x ruler tolerance))
        x (1 + 0.2 ln cities)

- **Who joins.** The rebel city takes with it nearby cities of its own
  people, each with probability 0.6, if the city is within 400 km of the
  rebel and closer to it than to the capital.
- **New lineages.** Rebels of the ruling lineage found a daughter lineage
  ([lineages.md](lineages.md)). Rebels of another lineage or people restore
  their own.
- **Logged as:** "secession" (ruling lineage), "kin revolt" (same people,
  other lineage), "ethnic revolt" (other people).

## Falls

- **No cities left:** the state is "conquered".
- **Capital taken:**
  - same people with 3 or fewer cities left: it is absorbed;
  - otherwise, 40% of the time it shatters into city-states;
  - otherwise it moves its capital.
