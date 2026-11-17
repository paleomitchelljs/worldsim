# Cultural traits

> **Draft structural mechanics (2026-10-29)** change this topic: costs (cohesion, statecraft, violence, expansion), acculturation across peoples. See [structural.md](../structural.md); they switch off with `--off`.

Values run 0–1, one per lineage.
- **Variation:** jittered between runs (`--vary`) and between founding
  groups (`--start-vary`) on the logit scale.
- **Inheritance:** daughter lineages mutate them (`--drift` at secession and
  sea colonies, `--settle-drift` when settling a new region).
- **Fusion:** a fused state's lineages get the population-weighted mean.

Code: the `LT` columns, named by `TRAIT_ATTR` (`viol`, `expn`, ...).

## What each does

| Trait | Effect in the code |
|---|---|
| violence | War strength x (0.5 + v). Chance of declaring war ∝ v. Raid frequency and damage ∝ v. Population lost when a city is taken: 10% + 40% x v. Chance of clearing conquered foreigners ∝ separation x violence x (1 − tolerance). |
| expansion | Migration starts at lower crowding and moves more people. Budding: bands split off before the cell is full, and are bigger. Pioneer leaps ∝ expansion². |
| separation | With `separation` on (default since 2026-10-29, U): preferred spacing. A lineage fills only 1 − 0.8 x sep² of a cell's capacity (cities excepted) before moving on ([../structural.md](../structural.md#separation-as-spacing-separation)). With it off (the old meaning): avoids moving or budding next to other peoples, and raises raids, war on foreigners and clearance; with it on, those effects use (1 − tolerance). |
| cohesion | Rate at which a state's cohesion (asabiya) regrows ([../rules/states.md](../rules/states.md)). |
| statecraft | Rate of administrative progress. Chance a new city joins its own people's state. Speed at which kin lineages are absorbed. Chance of fusion. |
| innovation | Rate of invention (farming ∝ i, metal ∝ i²). Speed of copying technology from contacts (x (0.3 + i)). |
| seafaring | Rate of sailing progress, starting sail level, voyage frequency. Coastal carrying capacity x (1 + 0.5 s). Founders with s < 0.5 avoid coasts in `score` mode. **Under `dispersal` (U, 2026-10-29) seafaring does nothing:** expansion drives voyages, fishing drives sailing, and `fishing` replaces the coastal bonus ([../structural.md](../structural.md)). |
| trade | Growth of trade ties (∝ product of both sides' trade). |
| tolerance | Gates trade, alliance and fusion by dissimilarity ([../rules/diplomacy.md](../rules/diplomacy.md)). Lowers war declaration (x (1 − 0.4 t)), clearance and raids. Conquered foreigners add (0.4 + 0.5 t) of their strength. Lowers unrest among foreign subjects. |

| hierarchy | With `hierarchy` on (C): elite growth x (0.5 + h); the unrest of a hungry state ∝ hierarchy (was statecraft); strength x (0.85 + 0.3 h). Not yet in similarity, acculturation or `price.csv`. |
| patience | With `patience` on (C): improvements and roads built x (0.5 + p); granaries smooth over 15 x admin x (0.5 + p) years; land wears x (1.5 − p). Not yet in similarity, acculturation or `price.csv`. |

| conformity | With `conformity` on (C): drift at lineage splits x (1.5 − c); acculturation x (1.5 − c). Fidelity of transmission. |
| proselytism | With `proselytism` on (C): in acculturation a contact's pull x (0.5 + p), and the receiver's openness = tolerance + 0.5 x the contacts' mean proselytism; a ruling lineage absorbs kin lineages x (0.5 + p). Peoples are near-species, so it spreads customs and lineage identity, not membership of a people. |
| dominance | With `dominance` on (U, 2026-10-29; forms and numbers C): war chance x (0.5 + d) x (1 + 0.5 d x min(2, target's people / own)); capture losses x (1 − 0.5 d); clearance chance x (1 − d); a weaker defender's chance to submit x (0.5 + d). Roster: Snake folk 0.8, Humans 0.75; Lizardfolk, Giants, Dwarves 0.5; Elves 0.25; Goblins, Frogloks, Ogres, Trolls 0.2. |
| craftsmanship | With `craft` on (U, 2026-10-29; levels U, numbers U→C): drives invention of the craft technology. Roster: Elves, Dwarves 0.9; Humans, Lizardfolk, Snake folk 0.5; Giants 0.3 (U 2026-11-02, was 0.1); Frogloks, Goblins 0.2; Ogres, Trolls 0.1. |

The four new traits (hierarchy, patience, conformity, proselytism) are not
yet in similarity or `price.csv`, and do not themselves acculturate.

## Values (`peoples_balanced.py`, current since 2026-10-29)

From the user's descriptions (U); the numbers are Claude's (U→C): very low
0.10, low 0.20–0.25, moderate 0.50, high 0.70–0.80, very or extremely high
0.90–0.95. Unmentioned traits keep their `peoples_headstart` values; the
new traits default to 0.5.

| People | r | Viol | Expn | Sep | Coh | State | Innov | Sea | Trade | Tol | Hier | Pati | Variance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Humans | 0.024 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 2.0 |
| Goblins | 0.035 | 0.85 | 0.70 | 0.10 | 0.40 | 0.30 | 0.10 | 0.20 | 0.30 | 0.20 | 0.50 | 0.10 | 1 |
| Lizardfolk | 0.020 | 0.50 | 0.50 | 0.50 | 0.75 | 0.50 | 0.50 | 0.50 | 0.75 | 0.30 | 0.50 | 0.75 | 1 |
| Frogloks | 0.040 | 0.50 | 0.35 | 0.10 | 0.40 | 0.30 | 0.10 | 0.05 | 0.30 | 0.50 | 0.50 | 0.50 | 1 |
| Snake folk | 0.019 | 0.50 | 0.50 | 0.50 | 0.50 | 0.75 | 0.50 | 0.50 | 0.50 | 0.30 | 0.75 | 0.75 | 1 |
| Elves | 0.015 | 0.25 | 0.30 | 0.50 | 0.50 | 0.70 | 0.50 | 0.50 | 0.50 | 0.10 | 0.50 | 0.75 | 1 |
| Trolls | 0.019 | 0.85 | 0.18 | 0.50 | 0.65 | 0.25 | 0.20 | 0.15 | 0.20 | 0.20 | 0.80 | 0.10 | 1 |
| Ogres | 0.020 | 0.85 | 0.20 | 0.50 | 0.75 | 0.35 | 0.20 | 0.10 | 0.15 | 0.20 | 0.80 | 0.10 | 1 |
| Giants | 0.017 | 0.70 | 0.15 | 0.70 | 0.90 | 0.55 | 0.30 | 0.20 | 0.30 | 0.35 | 0.80 | 0.10 | 1 |
| Dwarves | 0.019 | 0.40 | 0.10 | 0.05 | 0.95 | 0.80 | 0.85 | 0.10 | 0.80 | 0.20 | 0.50 | 0.50 | 1 |

- **Kept from `peoples_headstart`** (unmentioned):
  - Goblins and Frogloks: expansion, cohesion, statecraft, seafaring,
    trade;
  - Ogres, Trolls and Giants: expansion, statecraft, seafaring, trade;
  - Dwarves: violence and statecraft;
  - all peoples: growth rate, except Frogloks and Goblins.
- **New traits defaulted to 0.5 (C)** where the user gave none: hierarchy
  for Humans, Lizardfolk, Elves, Frogloks, Goblins and Dwarves.
- **Frogloks' and Goblins' growth rate is C.** U: high enough that
  dragons can share their cells without depleting them, but they should
  not run over everyone.
  - 0.06 let them grow at the human rate under a dragon, and they came to
    hold about 90% of all people (bal3).
  - Now 0.04: 1.7x the human rate, and just above zero growth under one
    dragon at the worst group size.
- **Conformity (U→C):** Elves and Dwarves 0.90, Humans 0.10, the rest
  0.50.
- **Proselytism (U→C):** Humans and Lizardfolk 0.75, Elves and Snake folk
  0.10, the rest 0.50.
- **All values are a people's means (U).** Founding groups (`--start-vary`)
  and daughter lineages (drift, x `variance`, x (1.5 − conformity)) vary
  around them. `--vary` instead shifts each people's means for the whole
  run, so runs of this roster use `--vary 0`.
- **Biomes (U, 2026-10-29; numbers C):**
  - Frogloks are tied to jungle more tightly than any other people:
    affinity G/F/J/D/T 0.15/0.35/1.6/0.02/0.02, seafaring 0.05.
  - Lizardfolk and Snake folk are shut out of tundra (0.02).
  - Under `BIOME_K` = 2.5, a Froglok cell in temperate forest carries
    about 2% of a jungle cell, and grassland about 0.4%. These loosen
    only as farming and metal adapt them, and Froglok innovation is 0.10.
  - The world has no separate swamp class, so Frogloks get a wetland
    preference (U), roster key `wet` = 1.0 (C):
    - capacity x (1 + 2 x wetness), up to 3x on the wettest ground;
    - the settling penalty for wet ground does not apply to them.

    Wetness is zero on about 90% of land cells. Wet cells are mostly in
    jungle (95th percentile 0.73) and temperate forest (0.44).
- **"Technological advancement" was read as innovation.** Frogloks and
  Goblins 0.10; Ogres and Trolls 0.20.

## Values (`peoples_headstart.py`, until 2026-10-29)

| People | Violence | Expansion | Separation | Cohesion | Statecraft | Innovation | Seafaring | Trade | Tolerance |
|---|---|---|---|---|---|---|---|---|---|
| Humans | 0.40 | 0.60 | 0.35 | 0.55 | 0.75 | 0.85 | 0.50 | 0.75 | 0.85 |
| Goblins | 0.85 | 0.70 | 0.55 | 0.40 | 0.30 | 0.20 | 0.20 | 0.30 | 0.15 |
| Lizardfolk | 0.45 | 0.60 | 0.45 | 0.60 | 0.75 | 0.80 | 0.45 | 0.65 | 0.45 |
| Frogloks | 0.55 | 0.65 | 0.55 | 0.40 | 0.30 | 0.20 | 0.40 | 0.30 | 0.15 |
| Snake folk | 0.70 | 0.60 | 0.70 | 0.65 | 0.80 | 0.75 | 0.35 | 0.50 | 0.25 |
| Elves | 0.20 | 0.25 | 0.30 | 0.30 | 0.25 | 0.25 | 0.20 | 0.25 | 0.25 |
| Trolls | 0.80 | 0.18 | 0.80 | 0.65 | 0.25 | 0.20 | 0.15 | 0.20 | 0.15 |
| Ogres | 0.90 | 0.20 | 0.75 | 0.75 | 0.35 | 0.25 | 0.10 | 0.15 | 0.10 |
| Giants | 0.70 | 0.15 | 0.85 | 0.65 | 0.55 | 0.45 | 0.20 | 0.30 | 0.20 |
| Dwarves | 0.40 | 0.15 | 0.65 | 0.85 | 0.80 | 0.85 | 0.35 | 0.65 | 0.40 |

## Provenance and justification

- **Trolls, Ogres, Giants, Dwarves:**
  - **U** (the user's original table), except for expansion and tolerance.
  - Expansion 0.15–0.20: **U→C** ("less expansion-oriented than the
    others").
  - Tolerance: **C**.
- **Humans:**
  - **U** except tolerance.
  - Tolerance 0.85: **U→C** ("highest tolerance").
- **Goblins:**
  - Violence 0.85, innovation 0.20, tolerance 0.15: **U→C** ("low tech, low
    tolerance, high violence").
  - Trade 0.30: **C**.
  - The rest: **U** (the original table).
- **Lizardfolk:** **U→C** ("close to Humans but lower tolerance").
- **Snake folk:** **U→C** ("more violent and less tolerant than
  Lizardfolk").
- **Frogloks:** **U→C** ("like Goblins but lower violence").
- **Elves:** **U→C** ("basically low for everything"), set at 0.20–0.30.
