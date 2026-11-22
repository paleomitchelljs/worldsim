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

## The state's view (`state_view`, 2026-11-22)

Three decisions read the state's view, not the ruling lineage alone:
subjects' weight in strength (the tolerance above), the revolt's alien
term below, and expulsion of foreign minorities. The view is the ruling
lineage's values moved toward the state's culture (its capital's) by the
lineage's own tolerance:

    view = ruler + tolerance x (state culture − ruler)

A tolerant ruling lineage takes on its state's culture; an intolerant
one keeps its own. Under `--off state_view` (or without `city_culture`)
the three read the ruling lineage.

## Assimilation

Cells of the ruler's own people but a different lineage switch to the
ruling lineage at 0.8% x (0.5 + statecraft) per year.

## Rebellion

- **Chance.** Each non-capital city may revolt each tick with probability

      5 x 0.0009 x (distance/reach)² x (1.5 − S)
        x (1 + 3 (1 − similarity)(1 − 0.6 x tolerance))
        x (1 + 0.2 ln cities)

  Similarity and tolerance are the state's view's (above): similarity
  of the view to the city's culture.
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
- **Disorder after a fall** (`collapse_cost`, WP12 C, 2026-11-22, U;
  form and numbers C). A cell takes disorder 1 when its city passes to
  another state (conquest, revolt, cession, partition, union or
  annexation alike), when its city is gone, or when its state ends and
  leaves it stateless. Cells that only move with a state's reach at the
  border do not. Disorder falls to 0 over 50 years. Meanwhile the
  state's order against feud, its hold on raids (RAID_ADMIN x
  administration) and the building of works are all x (1 − disorder).
  So are (U, 2026-11-22) the cell's rent, the surplus it sells in trade,
  and, for a city, its share of the trade food arriving in its state: a
  fallen land feeds no landlord and no market until order returns.
  Before WP12 a cell left with no state already lost about 8% of its
  heads over the next century against a held cell, and a change of
  ruler 3-5%, with no rule of their own.

## Polities without cities (`camps`, WP5 stage F, 2026-11-18)

U (2026-11-18): build them as camps kept outside the city table; a
defeated camp scatters or becomes a vassal. Numbers C; the design note
is `docs/upgrade/WP5F-camps-design.md`.
- **Forming.** Every 25 years, for each lineage with stateless cells,
  take those within 500 km of its densest stateless cell. Score them:
  heads x cohesion trait x (0.5 + hierarchy). At 21,000 or more a camp
  polity forms at the densest cell, with chance 0.2 per check. The
  threshold is the score the median one-city state's own lineage has
  in its land (`wp5d_seed101` at year 5,000).
- **The camp.** A seat cell, not a city. Its people's land is its
  territory, out to a reach of 300 x cohesion x (1 + 1.5 x herding
  share) cost-km. Every 10 years the seat moves to the densest cell of
  its lineage in its land. It takes no rent, tax or tribute. Its
  strength is reckoned as for any state. It has successions.
- **War.** A camp declares war as any state does and besieges cities.
  It cannot be besieged. Each year an attacker (or a defender striking
  back) at odds of 0.15 or more fights a battle at the seat, where the
  camp's strength counts 1.5 times. A won battle makes the camp a
  vassal with chance (0.5 + the victor's dominance) / 2; otherwise the
  camp scatters and its land is stateless again.
- **A city.** A camp polity that takes a city, is ceded one, or has one
  founded and joining in its land becomes an ordinary state with that
  city as capital.
- **Ending.** Every 25 years, a camp whose own lineage scores under a
  third of the threshold in its land disperses.

## Annexing vassals (WP13 B, 2026-11-21)

- A lord annexes a vassal of 3 or fewer cities that has been its vassal
  50+ years with chance per year VASSAL_ANNEX (0.004; unnamed before
  WP13) x (0.5 + the lord's statecraft) x w. w = 1 for a vassal of the
  lord's own people. For a vassal of another people, w = (1 - the
  vassal's tolerance) x the lord's dominance under `vassal_annex_cross`
  (U 2026-11-21, D15; form C), else 0. The annexed cities' people stay
  where they are, as subjects.
- A herding camp lord (`camp_tribute`) does not annex.
