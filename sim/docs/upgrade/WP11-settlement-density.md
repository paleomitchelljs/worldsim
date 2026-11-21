# WP11: farming density on open land

**Goal.** Grassland and forest that fill with farmers and herders once
farming has had time to spread, where the land and the technology allow.

**Evidence** (`wp8m`, year 8000; measured 2026-11-21).
- Settlement spreads fast, then stops: 45-55% of land by year 2000,
  81-85% by 5000, and 87-88% from year 6000 on. The 12% never settled is
  almost all tundra. Almost nothing is abandoned.
- Settled land is thin:

  | Biome | Area (M km²) | Median people per km² |
  |---|---|---|
  | Jungle | 28 | 0.4-0.6 |
  | Temperate forest | 26 | 0.12-0.14 |
  | Grassland | 38 | about 0.1 |
  | Desert | 9.5 | 0.03 |

- For scale (C, from memory): hunter-gatherers 0.01-0.1 per km², early
  farming regions 1-10. Most grassland and forest sits at forager
  density after 8,000 years; only the jungle river belts and a few cores
  reach farming density.
- Candidate causes in the rules (C, not yet traced):
  - the steppe cut: rain-fed farming on grassland and desert falls
    away from 400 to 1,600 km from the coast (STEPPE_KM);
  - herding density (HERD: grassland 0.45);
  - herding at low farming is never worse than foraging, which loosens
    the early farming penalty on poor land (open-questions.md);
  - biome affinity and how fast farming and metal free a lineage from it
    (`land.adapt`, BIOME_K, BIOME_ADAPT);
  - climate yields (`farm_clim`, `herd_clim`) on `world_v2`.

Read first: `wsim/land.py` (`Kf`, `K2`, `ltab`, `adapt`), `wsim/geo.py`
(capacity layers, `herd_density`), `docs/rules/population.md`,
`docs/world-data.md` (yields).

## Stage A: trace (records only)

1. For each biome, split capacity at year 8000 into its factors: soil,
   climate yield, steppe cut, elevation, affinity, technology, and
   herding against farming. Write the table and a capacity map at 8000.
2. Compare where people are against where the capacity is: is thin
   land thin because capacity is low, or because no farming lineage
   has reached it?
3. Report which factor holds each biome down. No rule changes.

## Stage B: fix (needs U)

From stage A, propose the change with physical or historical grounds
for each factor that is out of line. Set no density target: the
reference numbers are for reporting, not tuning. Sanity run, then a
5-seed batch; report the shift in peoples' shares.

## Not in this package

- Climate or biome changes (the physical model is settled, U 2026-11-21).
