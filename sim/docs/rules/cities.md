# Cities and territory

> **Draft structural mechanics (2026-10-29)** change this topic: herders count 0.3 toward founding a city; a city whose minority becomes the majority carries on. See [structural.md](../structural.md); they switch off with `--off`.

Code: `Sim.update_cities`, `territory`, `prepare_capacity`, `record`;
`World.locus`.

## Founding

A cell becomes a city when all three hold:
1. its population, converted to food-equivalents, exceeds **6000** (the
   people's threshold);
2. it is the local maximum of food-equivalent population x locus in a 5x5
   window;
3. it is not within 2 cells of an existing city.

**Locus** = 1 + 0.6 x river + 0.4 x coastal + 0.3 x (copper or tin within
150 km) + 0.2 x (iron within 100 km).

**The threshold in heads** is 6000 ÷ food-per-head, times the roster's
optional `city` factor (above 1 means fewer cities):

| People | Heads needed |
|---|---|
| Giants | about 470 |
| Ogres | about 630 |
| Trolls | about 1,070 |
| Humans | 6,000 |
| Goblins | about 13,200 |

**What the new city joins:**
- inside a state of the same people: that state, with probability
  0.3 + 0.7 x statecraft;
- inside a state of another people: that state, with probability 0.7;
- otherwise it founds a new state.

## Size cap (off by default since 2026-10-29, U)

Dropped at the user's request: city cells now grow to their carrying
capacity like any other cell. `--city-cap 3 40` restores the rule below,
which all runs before `nocap_*` used.


- The city cell's population is capped at
  `6000 x (3 + 40 x admin²)` food-equivalents, where admin is the ruling
  lineage's administration.
- That gives 18k at admin 0, 78k at 0.5 and 258k at 1.
- The cap enters K directly, so migration respects it too.

## Abandonment

A city ends when its people is replaced, or when its population falls below
0.35 x the threshold. Under `urban_city` (2026-11-09) it also ends,
"abandoned", when its urban population stays below 2,000
food-equivalents for 50 years (after 100 years of grace); no city is
founded in a cell in famine or within 2 cells of a city abandoned in the
last 100 years ([structural.md](../structural.md)).

## Territory

- Each city rules the cells nearest to it by travel cost.
- The search runs through the land graph plus sea links between coasts up
  to 160 km apart, which cost twice their distance.
- It reaches out to 120 + 900 x admin of the ruling lineage.
- **Travel cost per km** depends on the biome:

  | Grassland | Temperate forest | Desert | Jungle | Tundra |
  |---|---|---|---|---|
  | 1.0 | 1.25 | 1.5 | 1.7 | 1.8 |

  It is multiplied by (1 + 1.5 x relief) and by 0.7 on rivers.

**City size** (records only; 2026-11-09) is the urban population: the
people the city cell holds beyond what its own land feeds at the base
boost, in food-equivalents ([diagnostics.md](../diagnostics.md#records-of-2026-11-09)).
Until then it was 0.08 x the city cell + 0.04 x its hinterland, kept as
`size_old`.

**City-cell capacity** is the cell's own capacity x (1.5 + 2 x min(1.5,
the state's trade)) x (1 + DEV_CITY x development). Under `food_flow`
(2026-11-09) the trade term goes and the city's people receive rent,
provincial tax spending and trade food instead, and the ruling people the
state's take at the capital ([structural.md](../structural.md)). Under
`trade_debit` (WP4 stage B; the default since WP4 D) trade food is sold from
another state's surplus instead of being created; the base boost stays
(D6, U 2026-11-17) and shows in `food.csv` as `produced_boost`.

## Justifications

- **Threshold in food, not heads** (**C**, after Giants never founded a
  city). Settlement scale tracks how much food a place commands, not body
  count.
- **Per-people `city` factor and command-line threshold** (**U**:
  "adjustable values for cities").
- **Admin cap** (**U**). The numbers are **C**: the cap sits between the old
  median city cell (about 44k) and its maximum (about 260k).
- **River pull.** 86–91% of cities sit on river cells, which are 9% of
  land. That bias comes from irrigation, the forage bonus and locus; it was
  judged sufficient and not raised.
