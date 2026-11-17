# Intrinsic traits (biology)

These traits belong to a people. They are:
- never jittered between runs or founding groups;
- passed to daughter lineages unchanged;
- kept by each people when states fuse.

Code: `Sim.__init__` (psize, peat), `biome_fit`, `Kf`, `grow`.

## What each does

| Trait | Roster key | Effect |
|---|---|---|
| Growth rate | `r` | Logistic growth per year, times (0.6 + 0.4 x farming), times up to 2.5 on thinly settled land ("frontier fecundity"). |
| Biome affinity | `affinity` (5 biomes) | Multiplies carrying capacity. The fit is sharpened: `best * (affinity / best) ** k`. `k` starts at 2.5 and falls to 1 with technology ([technology.md](technology.md)). |
| Body size | `size` | Combat worth per head relative to a human. Multiplies war strength and raid damage ([../rules/war.md](../rules/war.md)). |
| Food per head | derived: `size ** 0.75` (or a roster `eat`) | Divides carrying capacity. Also converts the city threshold and band sizes from heads to food ([../rules/cities.md](../rules/cities.md)). |

## Justifications

- **Sharpened biome fit** (**U**: "strengthen biome preferences"; form
  **C**). Raising the ratio to the best biome to a power keeps each people's
  best biome at its table value while the others fall off steeply. For
  example, a biome rated 0.7 against a best of 1.2 starts at 26% of the
  best, not 58%.
- **Food per head ∝ size^0.75** (**C**, accepted by the user). This is
  Kleiber's law: metabolic need scales with body mass to the 3/4 power.
  Without it, a cell fed as many Giants as Humans, and at x30 combat worth
  Giants would be unbeatable. With it, a Giant cell is worth about 30/12.8
  = 2.3 Human cells in a fight.
- **Size multiplies strength per head** (**U**). Giants are worth 30
  Humans, Ogres 20, Trolls 10; Humans, Lizardfolk and Snake folk are
  equal.

## Values (`peoples_headstart.py`)

| People | r | Size | Food/head | Grassland | Temp. forest | Jungle | Desert | Tundra |
|---|---|---|---|---|---|---|---|---|
| Humans | 0.024 | 1 | 1 | 1.2 | 1.0 | 0.9 | 0.9 | 0.7 |
| Goblins | 0.035 | 0.35 | 0.46 | 0.9 | 1.0 | 1.1 | 0.7 | 0.5 |
| Lizardfolk | 0.020 | 1 | 1 | 0.8 | 0.8 | 1.4 | 1.0 | 0.3 |
| Frogloks | 0.021 | 0.5 | 0.59 | 0.5 | 0.9 | 1.5 | 0.2 | 0.2 |
| Snake folk | 0.019 | 1 | 1 | 0.7 | 0.6 | 1.2 | 1.3 | 0.2 |
| Elves | 0.015 | 1 | 1 | 0.6 | 1.4 | 1.0 | 0.4 | 0.6 |
| Trolls | 0.019 | 10 | 5.6 | 0.7 | 0.8 | 1.4 | 0.5 | 0.3 |
| Ogres | 0.020 | 20 | 9.5 | 1.2 | 0.8 | 0.8 | 0.8 | 0.6 |
| Giants | 0.017 | 30 | 12.8 | 1.0 | 1.0 | 0.7 | 0.6 | 1.2 |
| Dwarves | 0.019 | 0.6 | 0.68 | 0.9 | 1.0 | 0.6 | 0.8 | 1.0 |

**Provenance**
- **Biome affinities:** **U** (the user's table).
- **Growth rates:**
  - Trolls, Ogres, Giants, Dwarves and Elves: **U**.
  - Humans and Goblins: **U→C** ("highest growth"). Goblins 0.06 ->
    0.04 (U: tone down) -> 0.035 (U, 2026-11-02: slightly lower).
- **Hardiness** (`war_hardy`, U 2026-11-02): Trolls take 0.3 of the usual
  war losses (U→C); everyone else 1.
- **Fortress** (`fortress`, U 2026-11-02): Dwarves 1 (C), everyone else 0.
  Attackers of a fortress people lose extra people in raids and sieges
  ([../structural.md](../structural.md)).
  - Lizardfolk, Frogloks and Snake folk: **U→C**.
- **Size:**
  - Giants, Ogres, Trolls: **U**.
  - Humans, Lizardfolk, Snake folk at 1: **U**.
  - Elves at 1: **C**.
  - Dwarves 0.6, Frogloks 0.5, Goblins 0.35: **U→C** (the user said
    "penalty").
