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

    r x (0.6 + 0.4 x farming) x (1 + 1.5 x clip(1 − 2 pop/K))

The last term is frontier fecundity: thinly settled land grows up to 2.5x
faster.

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
