# Population and carrying capacity

> **Draft structural mechanics (2026-10-29)** change this topic: `pastoral` (herding, steppe stand-in), `land` (land condition), `climate`, `minority` (one minority people per cell). See [structural.md](../structural.md); they switch off with `--off`.

Code: `World.__init__` (base densities), `Sim.prepare_capacity`, `Kf`, `grow`,
`migrate`.

A cell holds one people and one lineage, or nobody. One tick is 5 years.

## Carrying capacity K of cell j for lineage L

    K = area x [forage x (1 − farming) + farm x farming x tools]
          x biome_fit(L, biome) x Kcell x (1 + 0.5 x seafaring x coastal)
          / food_per_head,   capped at the city cap / food_per_head
                                      (only with --city-cap; off by default)

- **Forage density** (people/km²) depends on the biome:

  | Jungle | Temperate forest | Grassland | Tundra | Desert |
  |---|---|---|---|---|
  | 0.25 | 0.18 | 0.15 | 0.03 | 0.02 |

  - It is multiplied by (1 + 2 x coastal ocean productivity).
  - It is multiplied by 1.8 near rivers (a river cell, or discharge over
    50 m³/s).
- **Farm density** = 1.8 x soil fertility^1.3 x biome farm suitability x an
  elevation and relief penalty. Then:
  - plus irrigation on river cells: 9 x sqrt(discharge/3000), times the
    biome's response;
  - x 1.3 on alluvium and x 1.2 on lakes;
  - plus a coastal fishing term.

  Biome farm suitability:

  | Grassland | Temperate forest | Jungle | Desert | Tundra |
  |---|---|---|---|---|
  | 1.0 | 0.75 | 0.45 | 0.04 | 0.03 |

  Irrigation response is highest in dry biomes:

  | Desert | Grassland | Temperate forest | Jungle | Tundra |
  |---|---|---|---|---|
  | 1.0 | 0.9 | 0.6 | 0.4 | 0.05 |

- **Tools** = 1 + 0.25 x iron + 0.25 x steel.
- **Kcell** = drought factor x city boost. The city boost is
  1.5 + 2 x min(1.5, the state's total trade).

Justification (**C**): the densities were cut 3.5x after the first runs
reached about 460M people. Peaks now run around 100–170M.

## Growth

Logistic growth toward K over each 5-year tick, at rate:

    min(R_MAX, R_SCALE x r x (0.6 + 0.4 x farming) x
        (1 + FRONT_K x clip(1 − pop / (FRONT_END x K))))

The last term is frontier fecundity: thinly settled land grows up to
1 + FRONT_K (2.5x) faster, falling to 1x at FRONT_END (0.5) of K.

WP6 stage A (2026-11-18, **C**) made the two numbers constants and added
R_SCALE (a multiplier on every lineage's r) and R_MAX (a ceiling on the
effective yearly rate; 0 = no cap). Stage B adopted R_SCALE 0.5 and
R_MAX 0.03 (**U->C**, 2026-11-18, decision D7; before then 1.0 and no
cap). Every lineage grows at half its roster rate, so the ratios between
peoples are unchanged, and no cell grows faster than 3% a year. The cost
is time: the first city comes about 500-750 years later (about year
900-1,100 against 360), 10M people about 1,400-2,000 years later, and the
metals up to about 1,000 years later; steel still arrives before year
8,000 (5,400-6,000 in the stage A runs). Recovery after a plague is about
20-40% slower (median 75-85 years back to 90%). Population still sits
near capacity once land fills. R_SCALE does not scale the dragon cut, so a lower R_SCALE puts more
peoples below zero under dragons. The minority's rate takes R_SCALE and
R_MAX too (it has no frontier term).

**Upkeep** (`upkeep`, WP6 C, 2026-11-18, **C**). Improvements (cleared
fields, terraces, canals; up to 1.3x rain-fed and 2.5x irrigated yield)
need people to keep them, and are sized to the people who kept them.
Where a cell's people fall below 0.7 of their mean over the last 50 years
(an exponential mean), the works decay by an extra 0.1 a year x the
shortfall ((0.7 x mean − pop) / (0.7 x mean)); an emptied cell loses them
in about a decade. They are rebuilt at the old rate (0.003 a year at
most), so a crash lowers the land's capacity for decades to centuries.
Herders' cells keep the old slow silting only. A first form measured the
shortfall against farming K; that halved improvements everywhere and all
the time (many settled cells sit below 0.7 of farming K, since rent and
tax take part of it), so it was replaced the same day.

## Movement within a lineage

- **Who moves.** People leave crowded cells. Moving starts at crowding
  above 0.9 − 0.6 x expansion. The share that moves is
  0.04 + 0.3 x expansion x the excess crowding.
- **Where to.** Movers go only to neighbouring cells of the same lineage,
  weighted by:
  - room;
  - sqrt(K);
  - 1/travel cost;
  - 1 − 0.9 x separation, if the cell borders a foreign people.
- **New land.** Empty land is taken by colonization, not by this flow
  ([colonization.md](colonization.md)).

## Accounting for people (WP4 stage C, 2026-11-17)

Records, except two fixes marked below. `growth.csv` closes a
per-century, per-people account in heads (cell majorities plus
minorities):

    change = natural increase - removals + made + sum of phase nets

- **Natural increase** is the change during `grow` plus the removals
  recorded there (hunger, feud). It covers majorities and minorities.
- **Removals** are the causes of `deaths.csv`:
  - hunger: a crowd above what the land feeds dying back in `grow`,
    counted once. `famine` only moves people, and its remainder dies
    back in `grow` the next tick. From 2026-11-17 a minority's die-back
    counts too.
  - feud, raid, war levies, siege, sack, clearance, plague.
  - dragon attack: a dragon's fight with a settlement, in `dragons`.
  - three causes new on 2026-11-17, below.
- **Forgone growth under dragons** is not a removal. Dragons cut the
  growth rate, so it is growth that did not happen (majority and
  minority). It was the "dragon" cause in `deaths.csv`, 54-58% of all
  "deaths"; it is now `forgone_dragon` in `growth.csv`.
- **Made**: heads added from no cell. A merchant quarter, a trading
  post and a conqueror's garrison each add a minority without taking it
  from anywhere (C, an existing mechanic; now shown).
- **Phase nets.** Each phase's change plus its removals, less heads
  made. For the world they must be 0, since people only move between
  peoples. Over 300 years from year 5,000 of seed 101, every one is 0.

**Fixes and new causes (2026-11-17, C).** Each was a bookkeeping gap
that the account found.
- Raid takeover: the half of the old majority that does not stay on is
  now recorded as raid deaths, and so is an old minority overwritten by
  the new underclass. Before, both vanished without a record.
- Raid takeover, a mechanic fix: an attacking cell that sent two
  takeover bands in one tick paid for only one. Each band is now
  debited (`np.subtract.at`).
- Voyages, a mechanic fix: colonists landing where another people's
  minority already lives were taken from the source and never placed.
  They now stay home.
- Voyages: thin natives pushed out of a cell are recorded as
  `displaced`.
- Expulsion of a foreign minority (`minorities`) is recorded as
  `expelled`.
- `tidy` removes cells under 5 heads and tiny minorities. That is
  recorded as `dwindled`.
