# Scenarios (rosters)

A roster is a module with a list called `PEOPLES`, chosen with `--peoples`.

**Per-people keys:**
- `key`, `label`, `color`;
- the intrinsic traits `r`, `affinity` and `size` (plus an optional `eat`);
- the nine cultural traits, plus optional `hierarchy` and `patience`
  (default 0.5);
- optional `wet` (0–1): a wetland preference. Capacity x (1 + 2 x wet x
  wetness), and no settling penalty for wet ground, in proportion
  (default 0);
- optional `variance`: multiplies the founding-group jitter and the
  drift at lineage splits for that people (default 1);
- optional `head` (head start, in years), `starts` (founding groups),
  `city` (city threshold factor) and `start` (a fixed lon/lat for the first
  group).

Peoples are placeholders pending the book's naming pass; don't coin names.

| Module | Peoples | Status |
|---|---|---|
| `peoples_balanced.py` | the 10 fantasy peoples rebalanced from the user's descriptions (2026-10-29; U→C), with hierarchy, patience, conformity, proselytism, per-people variance and a wetland preference for Frogloks; Frogloks r = 0.04, Goblins 0.035 (C; was 0.06, toned down, U; Goblins lowered again 2026-11-02, U); Giants violence 0.70, tolerance 0.35, craft 0.30 and Trolls `hardy` 0.3 (U, 2026-11-02) | **current** |
| `peoples_headstart.py` | the 10 fantasy peoples, with head starts, sizes and the trait changes in [traits/](traits/) | until 2026-10-29 |
| `peoples_fantasy.py` | the 10 fantasy peoples, with the user's original trait and biome tables (**U**) plus tolerance (**C**) | earlier runs |
| `peoples.py` | 5 archetypes A–E: valley farmers, horse raiders, sea traders, forest clans, temple builders (**C**) | first runs |

The values used in each run are written to that run's `traits.txt`.


## peoples_regional (2026-10-30)

`peoples_balanced` with regional homelands (U, from the user's sketch):
founders start and wander only in their people's homeland; Goblins start
anywhere, small islands included (`anywhere`); dragons are everywhere
already. Homelands: Humans, Lizardfolk and Frogloks both the western
island and the island east of it (U, 2026-10-30; first set: Humans the
western island, Lizardfolk and Frogloks the eastern one); Elves the northern island; Snake folk the eastern
island; Dwarves two mountain regions of the southern continent (1,200 km
each); Trolls (1,200 km), Giants (1,500 km), Ogres (1,200 km) regions of
the southern continent. Points read off the sketch and radii are C.
