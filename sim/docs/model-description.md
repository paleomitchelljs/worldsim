# Model description

A description of `worldsim.py` and the `peoples_balanced` roster as of
2026-10-29. Description only.

Notation: `clip(x, a, b)` limits x to [a, b]; `σ(x) = 1 / (1 + e^−x)`;
`DT` = 5 years; "per tick" = per 5 years; rates given "per year" are
multiplied by DT each tick. Chances and compounding shares given "per 5
years" (WP5 stage C, 2026-11-18, C) are applied over a step of DT years
as 1 − (1 − p)^(DT / 5), which is p at DT = 5; truces, war ages and the
plague gap are counted in years. Logit-normal jitter of a value x by s means
`σ(logit(clip(x, 0.02, 0.98)) + N(0, 2.5 s))`.

---

## 1. Run settings

### 1.1 Command line (defaults)

| Flag | Default | Current runs |
|---|---|---|
| `--seed` | 1 | 101–107 |
| `--years` | 6000 | 6400 |
| `--frame-every` | 20 ticks | 100 (a frame per 500 years) |
| `--homelands` | continents | continents |
| `--vary` | 0 (per-run jitter of each people's traits) | 0 |
| `--peoples` | `peoples` | `peoples_balanced` |
| `--start-pool` | 0.02 | 0.02 |
| `--starts` | 3 founding groups per people | 20 |
| `--start-vary` | 0.05 | 0.1 |
| `--drift` | 0.06 (mutation sd at secession, colony) | 0.06 |
| `--cluster-km` | 0 | 0 |
| `--settle-drift` | 0.03 (mutation sd when settling a new region) | 0.03 |
| `--size-food` | kleiber | kleiber |
| `--city-pop` | 6000 | 6000 |
| `--city-cap` | off | off |
| `--start-mode` | wander | wander |
| `--wander-steps` | 2000 | 2000 |
| `--dragon-shun` | 0 | 0 |
| `--dragon-penalty` | 0.036 | 0.036 |
| `--off` | none | none |
| `--set NAME=VALUE` | none (overrides a numeric constant; repeatable) | none |
| `--shuffle-sites` | off (resource sites and hearths from `sites.json`) | off |

`--vary s` (if > 0) jitters each people's TRAITS (stream 10,000 + seed) and
XTRAITS (stream 20,000 + seed) logit-normally by s.

### 1.2 Switches

Each switch is on unless named in `--off`; `--off all` turns all off:

`costs, fiscal, unrest, succession, vassals, balance, pastoral, land,
climate, supply, minority, acculturation, immunity, diagnostics, roads,
improvements, dragons, separation, hierarchy, patience, conformity,
proselytism, dispersal, fishing, dominance, ore_trade, food_units,
shuffle, dynasty, logistics, domestication, craft, resources, guarded,
trade_assets, war_motive, salinity, war_goals, scale, development,
density_cap, experience, mission, dragon_hosts, land_pressure,
war_v2, raid_order, sod`.

Below, a rule tagged `[x]` applies only when switch x is on; a rule tagged
`[not x]` applies only when it is off.

### 1.3 Random streams

| Stream | Seed | Used for |
|---|---|---|
| main | seed | everything not listed below |
| climate | 50,000 + seed | climate series, fields, abrupt events, river course changes |
| dragons | 70,000 + seed | all dragon draws |
| extra traits | 80,000 + seed | XTRAIT mutation |
| sites | 90,000 + seed | site placement with `--shuffle-sites` |

### 1.4 Tick order

1. Late founding groups arrive.
2. Technology and acculturation.
3. Capacity is prepared (drought factor, climate, city boosts).
4. Famine movement `[climate]`.
5. Dragons `[dragons]`.
6. Growth, then land use.
7. Migration: drift, budding (twice), pioneer leaps, voyages, settler lineages.
8. Raids.
9. Cells under 5 people are emptied.
10. Cities end and are founded.
11. Territory.
12. Roads, every 50 years `[roads]`.
13. Polity statistics (strength, cohesion, unrest, assimilation, adjacency, tribute).
14. Trade ties.
15. Minorities `[minority]`.
16. Diplomacy (vassal politics, alliances, fusion).
17. War declarations and sieges.
18. Rebellions and successions.
19. Disasters (drought, plague).
20. Cells under 5 people are emptied.
21. Records.

---

## 2. World

### 2.1 Grid and cell data

- 0.5° grid, 360 rows × 720 columns; longitude wraps. Land cells only
  (66,895).
- Read from `../gis/world_v2.gpkg` (read-only; the default since WP8, U
  2026-11-19). It is `world.gpkg` plus climate fields, with the biome
  the climate implies (`syn_biome`) in place of the drawn one and rivers
  routed on the climate's runoff ([world-data.md](world-data.md)).
  `--world v1` reads `world.gpkg`. Columns: position, area, elevation,
  biome, soil, relief, discharge, river flag, lake flag, coastal-sea
  productivity, distances to copper, tin and iron, surface lithology,
  alluvial fill, runoff, flow direction, basin id, wetness (0–1),
  distance to coast.
- Biomes: Jungle, Desert, Grassland, Temperate forest, Tundra.
- Neighbours: 8 per cell. Step length: dy = 55.6 km × row step, dx = 55.6
  km × cos(lat) × column step, at least 1 km.
- Coastal cell: any neighbour is sea. Sea productivity `pn` =
  clip((max productivity of adjacent sea − 0.0003) / 0.0006, 0, 1).
- Landmasses: 8-connected land regions.
- Sea links: coastal cell pairs within 160 km and more than 90 km apart,
  travel cost 2 × distance.

### 2.2 Terrain

- Defence = biome factor × (1 + 0.6 × clip(relief km, 0, 1.5)) × (1 + 0.6
  × wetness). Biome factors: Grassland 1.0, Temperate forest 1.1, Tundra
  1.3, Desert 1.6, Jungle 1.7.
- Colonization ease = exp(−relief km / 0.7) × (1 − 0.5 × wetness).
- Travel cost per cell = (1 + 1.5 × clip(relief, 0, 2)) × biome cost ×
  0.7 on rivers × (1 − 0.5 × road stock) `[roads]`. Biome costs: Jungle
  1.7, Temperate forest 1.25, Grassland 1.0, Desert 1.5, Tundra 1.8. Edge
  cost = step length × mean of the two cells' costs. The travel graph is
  land edges plus sea links.

### 2.3 Land productivity (people/km²)

- Fertility = clip((soil + 3.75) / 5.5, 0, 1), 0.3 where missing.
- Elevation factor = clip(1 − (elev km − 1.5) / 1.5, 0.2, 1) / (1 + 0.5 ×
  clip(relief, 0, 2)).
- Wet factor = 1.3 on alluvium × 1.2 on lake cells.
- Steppe = clip((distance to coast − 400) / 1200, 0, 1) on grassland and
  desert, else 0.
- Near river = river cell or discharge > 50 m³/s.
- Forage = FORAGE[biome] × (1 + 2 × coastal × pn) × (1 + 0.8 × near
  river). FORAGE: Jungle 0.25, Temperate forest 0.18, Grassland 0.15,
  Desert 0.02, Tundra 0.03.
- Rain-fed = 1.8 × fertility^1.3 × FARM[biome] × elevation factor. FARM:
  Jungle 0.45, Temperate forest 0.75, Grassland 1.0, Desert 0.04, Tundra
  0.03.
- Irrigation = 9.0 × sqrt(clip(discharge / 3000, 0, 1)) × IRRIG[biome] ×
  river. IRRIG: Jungle 0.4, Temperate forest 0.6, Grassland 0.9, Desert
  1.0, Tundra 0.05.
- Coastal fish yield = coastal × pn.
- Farm = (rain-fed + irrigation) × wet factor + fish yield. With
  `[pastoral]` rain-fed is × (1 − 0.65 × steppe).
- Herd density = HERD[biome] × clip(1 − (elev − 2.5) / 1.5, 0.2, 1) × (1
  + 0.5 × steppe). HERD: Grassland 0.45, Desert 0.08, Tundra 0.06,
  Temperate forest 0.12, Jungle 0.02.
- Waterside (0–1) = max(coastal × (0.5 + 0.5 pn), river 1, lake 1, near
  river 0.5).
- Dryness = clip(1 − runoff (m/yr) / 0.5, 0, 1).
- City locus = 1 + 0.6 river + 0.4 coastal + 0.3 (copper and tin both
  within 150 km) + 0.2 (iron within 100 km).
- `[climate_fields]` (WP8 stage B, C; on by default; no effect on a world
  file without climate fields, i.e. `world.gpkg`):
  - Steppe = clip((0.65 − aridity) / 0.45, 0, 1) on grassland and
    desert. Aridity is P/PET from the world file; 0.65 and 0.2 are the
    UNEP dry-subhumid and arid bounds.
  - The steppe no longer cuts rain-fed farming: the farming term below
    carries aridity already. It still raises herding.
  - Dryness = clip(1 − aridity, 0, 1).
  - Rain-fed × farm term. The term is clip(GDD / 2000, 0, 1) ×
    clip(aridity / 0.65, 0, 1), divided by its area-weighted mean in the
    cell's biome, capped at 3 × that mean, and renormalised to a mean of
    1. The normalisation is a choice (C): the biome factors (FARM, HERD)
    stay the base and the term adds only the gradient within a biome.
  - Herd density × herd term: the same with clip(GDD / 800, 0, 1) ×
    clip(aridity / 0.2, 0, 1).
- `[floodplain]` (WP8 stage C, C; on by default since U 2026-11-19):
  - Irrigation = 20 × irrigable area / cell area × IRRIG[biome]. That
    replaces 9 × sqrt(Q/3000) × IRRIG over the whole cell.
  - Irrigable area = valley length in the cell × floodplain width,
    capped at the cell's area. Valley length is the step to the cell it
    drains to, or √area at an outlet.
  - Width (km) = 5 × √(Q / 1,000 m³/s) × 3 on alluvium (surface
    alluvium or alluvial fill) × exp(−relief km / 0.5). A delta (a
    coastal river cell on alluvium) is at least 40 km wide. Alluvial fill
    alone marks filled inland depressions, never a coast, so it cannot
    find deltas.
  - Source of the form: floodplain and meander-belt width scale with
    channel width, which scales with √Q (hydraulic geometry, Leopold and
    Maddock 1953). 5 km at 1,000 m³/s and the ×3 on alluvium are C:
    the Nile's valley is 10–20 km wide at ~2,800 m³/s, and a
    Mesopotamian-type alluvial plain is far wider.
  - 20 people/km² is a density on irrigated land: about 10 × the best
    rain-fed density (1.8), the ratio of irrigated to rain-fed peasant
    densities. It is not the brief's ~100/km², because the model's
    densities run several times below real ones throughout.
  - `irr_share` (salinisation, climate) follows.
- Ecotones: for each cell, the biome a drier climate pushes toward
  (Jungle → Grassland, Temperate forest → Grassland, Grassland → Desert)
  and a wetter one (Desert → Grassland, Grassland → Temperate forest or
  Jungle), with proximity exp(−(max(d, 1) − 1) / 2), d in cells to the
  nearest cell of that biome.

### 2.4 Rivers

- Drainage network from the flow directions; discharge is accumulated
  runoff × area downstream.
- River cell: discharge > 300 m³/s, drained area > 30,000 km², not a lake
  (recomputed after a course change).
- Everything in 2.3 that depends on rivers, and travel costs, are
  recomputed when a river changes course.

### 2.5 Sites

Read from `sites.json` (written by `make_sites.py` with seed 1), or drawn
the same way from the sites stream with `--shuffle-sites`.

- **Unique resources** (36): each kind placed on cells meeting its rule,
  at least 1500 km from others of its kind and 300 km from any site.

  | Kind | Count | Rule |
  |---|---|---|
  | amber | 4 | coastal, \|lat\| > 40, temperate forest or tundra |
  | incense | 4 | desert, or grassland with dryness > 0.5 |
  | electrum | 4 | river, relief > 0.4 km |
  | lapis | 3 | relief > 0.9 km; desert, grassland or tundra |
  | ivory | 4 | jungle or grassland, \|lat\| < 30 |
  | purple dye | 4 | coastal, sea productivity > 0.5, \|lat\| < 40 |
  | spice | 4 | coastal jungle |
  | jade | 3 | relief > 0.6 km, temperate forest |
  | pearls | 3 | coastal, sea productivity > 0.3, \|lat\| < 30 |
  | silver | 3 | relief > 0.7 km |

- **Domestication hearths** (13): crops in grassland (2), temperate forest
  (2), jungle (2) and desert (1, on a river); animals in grassland (2),
  desert, tundra, temperate forest and jungle (1 each). Each on a cell in
  the top 30% of its biome's farm (crops) or herd (animals) density, at
  least 2000 km from hearths of the same kind and biome.

- **Sites v2** (`--sites sites_v2.json`, `make_sites.py --v2`): hearths as
  above. 45 unique-resource sites shared among landmasses of 0.1M km² or
  more: at least 1 each, the rest by area (largest remainder); smallest
  landmass first, each slot takes the kind with fewest sites so far whose
  rule has a cell there (same-kind spacing 1500 km, then 800 km; any
  site 300 km); at most 5 per kind. A landmass no rule fits takes the
  least-placed kind anywhere on it. Then 16 precious-metal sites shared
  by area with no minimum (placer gold 5, lode gold 5, silver 6).

  | Kind | Rule |
  |---|---|
  | amber, incense, electrum, lapis, ivory, purple dye, spice, jade, pearls | as above |
  | fragrant timber | temperate forest, relief > 0.5 km |
  | dark hardwood | inland jungle, relief < 0.6 km |
  | fine fibre | river, grassland or temperate forest, relief < 0.5 km |
  | cotton fibre | river, \|lat\| < 35, desert or grassland with dryness > 0.4 |
  | fine clay | river, jungle or temperate forest, relief < 0.3 km |
  | obsidian | relief > 0.9 km |
  | placer gold (precious) | river, relief > 0.4 km |
  | lode gold (precious) | relief > 0.8 km |
  | silver (precious) | relief > 0.7 km |

- **Sites v3** (`--sites sites_v3.json`, `make_sites.py --v3`; the
  standard since 2026-11-19, U): the v2 rules and quotas on
  `world_v2.gpkg` (the climate's biomes and rivers, with `climate_fields`
  and `floodplain` on), and hearths placed afresh by the v1 rule on the
  same world; the old hearths sat on the drawn biomes. Seed 1.

---

## 3. Peoples and lineages

### 3.1 Roster (`peoples_balanced`)

Columns: growth rate r; cultural traits (violence, expansion, separation,
cohesion, statecraft, innovation, seafaring, trade, tolerance); extra
traits (hierarchy, patience, conformity, proselytism, dominance,
craftsmanship); biome
affinity (Grassland, Temperate forest, Jungle, Desert, Tundra); head start
(years); body size; trait variance; wetland preference.

| People | r | viol | expn | sep | coh | state | innov | sea | trade | tol |
|---|---|---|---|---|---|---|---|---|---|---|
| Humans | 0.024 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |
| Goblins | 0.040 | 0.85 | 0.70 | 0.10 | 0.40 | 0.30 | 0.10 | 0.20 | 0.30 | 0.20 |
| Lizardfolk | 0.020 | 0.50 | 0.50 | 0.50 | 0.75 | 0.50 | 0.50 | 0.50 | 0.75 | 0.30 |
| Frogloks | 0.040 | 0.50 | 0.35 | 0.10 | 0.40 | 0.30 | 0.10 | 0.05 | 0.30 | 0.50 |
| Snake folk | 0.019 | 0.50 | 0.50 | 0.50 | 0.50 | 0.75 | 0.50 | 0.50 | 0.50 | 0.30 |
| Elves | 0.015 | 0.25 | 0.30 | 0.50 | 0.50 | 0.70 | 0.50 | 0.50 | 0.50 | 0.10 |
| Trolls | 0.019 | 0.85 | 0.18 | 0.50 | 0.65 | 0.25 | 0.20 | 0.15 | 0.20 | 0.20 |
| Ogres | 0.020 | 0.85 | 0.20 | 0.50 | 0.75 | 0.35 | 0.20 | 0.10 | 0.15 | 0.20 |
| Giants | 0.017 | 0.80 | 0.15 | 0.70 | 0.90 | 0.55 | 0.30 | 0.20 | 0.30 | 0.30 |
| Dwarves | 0.019 | 0.40 | 0.10 | 0.05 | 0.95 | 0.80 | 0.85 | 0.10 | 0.80 | 0.20 |

| People | hier | pati | conf | pros | dom | craft | G | F | J | D | T | head | size | variance | wet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Humans | 0.50 | 0.50 | 0.10 | 0.75 | 0.75 | 0.50 | 1.2 | 1.0 | 0.9 | 0.9 | 0.7 | 0 | 1.0 | 2.0 | 0 |
| Goblins | 0.50 | 0.10 | 0.50 | 0.50 | 0.20 | 0.20 | 0.9 | 1.0 | 1.1 | 0.7 | 0.5 | 0 | 0.35 | 1.0 | 0 |
| Lizardfolk | 0.50 | 0.75 | 0.50 | 0.75 | 0.50 | 0.50 | 0.8 | 1.1 | 1.4 | 1.0 | 0.02 | 150 | 1.0 | 1.0 | 0 |
| Frogloks | 0.50 | 0.50 | 0.50 | 0.50 | 0.20 | 0.20 | 0.15 | 0.35 | 1.6 | 0.02 | 0.02 | 150 | 0.5 | 1.0 | 1.0 |
| Snake folk | 0.75 | 0.75 | 0.50 | 0.10 | 0.80 | 0.50 | 0.7 | 0.6 | 1.2 | 1.3 | 0.02 | 400 | 1.0 | 1.0 | 0 |
| Elves | 0.50 | 0.75 | 0.90 | 0.10 | 0.25 | 0.90 | 0.6 | 1.4 | 1.0 | 0.4 | 0.6 | 400 | 1.0 | 1.0 | 0 |
| Trolls | 0.80 | 0.10 | 0.50 | 0.50 | 0.20 | 0.10 | 0.7 | 0.8 | 1.4 | 0.5 | 0.3 | 0 | 10.0 | 1.0 | 0 |
| Ogres | 0.80 | 0.10 | 0.50 | 0.50 | 0.20 | 0.10 | 1.2 | 0.8 | 0.8 | 0.8 | 0.6 | 0 | 20.0 | 1.0 | 0 |
| Giants | 0.80 | 0.10 | 0.50 | 0.50 | 0.50 | 0.10 | 1.0 | 1.0 | 0.7 | 0.6 | 1.2 | 0 | 30.0 | 1.0 | 0 |
| Dwarves | 0.50 | 0.50 | 0.90 | 0.50 | 0.50 | 0.90 | 0.9 | 1.0 | 0.6 | 0.8 | 1.0 | 0 | 0.6 | 1.0 | 0 |

- Dragon hosts (`dragon_host`): Goblins and Frogloks.
- Lifespan (`lifespan`, biological, a multiple of a human life; fixed per
  people): Humans 1.0, Goblins 0.43, Frogloks 0.71, Lizardfolk 1.15, Snake
  folk 1.15, Ogres 0.9, Giants 1.5, Trolls 2.0, Dwarves 2.5, Elves 10.
  Not yet used.
- Food per head = size^0.75 (`--size-food kleiber`; 1 with `none`).
- City threshold per people (heads) = 6000 × roster `city` factor (1 for
  all) / food per head.

### 3.2 Lineage state

Each lineage holds: people; parent; founding year; end
year; the nine TRAITS; the six XTRAITS; r; biome affinities; technology
levels (farming, metallurgy, sailing, fishing, administration, craft,
one level per domestication package); guarded techniques held; war
memory; trait change from experience since the last Price snapshot; metal
stages in use (bronze, iron, steel); stages known `[supply]`; ticks
without supply per stage `[supply]`; landmasses seen; colour. Each land
cell holds a people, a lineage and a population (or none), plus at most
one minority people, lineage and population `[minority]`. The table
holds at most 60,000 lineages; once full, a would-be daughter lineage is
not created and its cells stay with the parent.

### 3.3 New lineages

A new lineage is a founding group (no parent) or a daughter (secession,
settler, colony, union, fusion). For mutation size s:

- s = s × the people's variance; `[conformity]` s × (1.5 − conformity)
  (the parent's, or the people's mean for a founding group).
- XTRAITS: copied from the parent (or the people's means), then
  logit-normal jitter by s (extra-traits stream).
- TRAITS: copied from the parent (or the people's means), then
  logit-normal jitter by s (main stream).
- r and biome affinities: copied unchanged.
- Technology: copied from the parent. A founding group starts with farming
  0.25, metallurgy 0, administration 0, fishing 0.1, sailing 0.025
  `[dispersal]` or 0.05 × seafaring `[not dispersal]`.
- Mutation sizes: founding group `--start-vary`; secession and colony
  `--drift`; settler `--settle-drift`; union and fusion 0 (traits set
  afterwards).

### 3.4 Similarity and acceptance

- Distance d = |ΔTRAITS| (seafaring excluded `[dispersal]`) + 0.3 ×
  |Δ log biome affinities|.
- Similarity: same people exp(−d / 0.8); different peoples 0.15 + 0.35 ×
  exp(−d / 0.8).
- Acceptance at level (need, width) = σ((tol_a − need × (1 − sim)) /
  width) × σ((tol_b − need × (1 − sim)) / width). Levels: trade (0.4,
  0.15), alliance (0.8, 0.08), fusion (1.0, 0.06).

---

## 4. Start

### 4.1 Arrival times

- Groups per people = `--starts` (or a roster `starts`), in random order.
- With H = the largest head start, a people's groups arrive at year H −
  head. Snake folk and Elves at year 0; Lizardfolk and Frogloks at 250;
  the rest at 400.

### 4.2 Wander mode

- Suitability = area × (0.75 forage + 0.25 farm) × biome fit (exponent
  2.5) × (1 + (0.25 + 0.75 × 0.1) × waterside) `[fishing]` (or × (1 + 0.5
  × seafaring × coastal) `[not fishing]`). With homelands = continents,
  zero on landmasses under 4 million km² (15 million with 5 or fewer
  peoples), except for peoples flagged `anywhere`. A people with a
  `region` (a list of parts, each the landmass at a point, optionally only
  within a radius of it) has suitability 0 outside it.
- Reference = the people's 95th-percentile suitability. Look-ahead =
  (Gaussian smoothing, σ 3 cells, of suitability / reference + 10⁻⁶)².
  Stay chance = min(0.95, suitability / reference).
- Each group starts on a random cell of positive suitability and takes
  2000 steps: it stays with the stay chance, else moves to a neighbour
  chosen in proportion to look-ahead.
- Groups not yet arrived take 3 more steps per tick, avoiding settled
  cells.
- On arrival a group settles its cell, or if that is taken, the
  best-suitability empty cell within 8 rings.

### 4.3 Score mode

- Site score = area × (0.5 forage + 0.5 farm) × biome fit (exponent 2.5),
  zero in biomes under 0.9 × the people's best affinity, and on small
  landmasses as above. `[not dispersal]` × 0.5 on coasts for peoples with
  seafaring < 0.5.
- Sites are kept at least sep₀ = clip(3500 / sqrt(groups), 500, 1800) km
  from chosen sites (shrinking × 0.7 until a site is free, down to 100
  km). A site is drawn from the best max(60, start-pool × candidates) in
  proportion to score.

### 4.4 Founding

Founding population 400 food-equivalents (400 / food per head heads)
`[food_units]`, or 400 heads `[not food_units]`. A new lineage with
mutation `--start-vary`.

---

## 5. Capacity

### 5.1 Cell factors

- Drought factor per cell (1 at rest): every 5 years it recovers 35% of
  the way to 1; `[not climate]` random droughts lower it (section 17).
- City cells: × (1.5 + 2 × min(1.5, ruling state's trade volume)), or ×
  1.5 if unruled; `[development]` × (1 + 0.25 × the ruler's development).
- City cap (only with `--city-cap a b`): city cell food-equivalents ≤ 6000
  × (a + b × admin²).

### 5.2 Biome fit

- Adaptation = 0.5 × clip((farming − 0.25) / 0.75, 0, 1) + 0.5 ×
  clip(metallurgy / 2.6, 0, 1).
- Fit = best × (affinity / best)^k, with k = 2.5 × (1 − 0.6 ×
  adaptation).
- `[climate]` near a biome edge, fit blends toward the fit of the biome
  the cell is shifting to, by the shift share f (section 6).
- Wetland peoples: fit × (1 + 2 × wet × cell wetness).

### 5.3 Carrying capacity K (heads) of cell j for lineage L

- Farm density:
  - `[climate]` rain-fed × climate rain factor + irrigation × climate
    irrigation factor + fish yield (rain-fed × (1 − 0.65 steppe)
    `[pastoral]`);
  - `[improvements]` rain-fed × (1 + 0.3 × improvement) + irrigation ×
    (0.4 + 0.6 × improvement) + fish yield (with climate factors if on);
  - `[sod]` on grassland the rain-fed part × 0.35 before bronze, × 0.6
    with bronze in use, × 1 with iron in use (irrigation and fish
    untouched).
  - `[land]` × land condition.
  - `[salinity]` × (1 − 0.7 × salt × irrigated share).
  - `[domestication]` × (0.5 + 0.5 × c), c = the lineage's best crop
    level for the cell's biome: max over crop packages of level × (1 in
    the package's biome, 0.3 elsewhere).
- Density = forage × (1 − farming) + farm × farming × tools; tools = 1 +
  0.25 iron + 0.25 steel. Forage × climate forage factor `[climate]`.
- `[domestication]` herd density × (0.3 + 0.7 × a), a = best animal level
  for the cell's biome, as for crops.
- Water factor = 1 + (0.25 + 0.75 × fishing) × waterside `[fishing]`, or 1
  + 0.5 × seafaring × coastal `[not fishing]`.
- `[development]` water factor × (1 + 0.25 × development) (section 15.6).
- Farming K = min(area × density × fit × cell factor × water factor / food
  per head, cap / food per head). Cap = the city cap (if on), and
  `[density_cap]` 150 food-equivalents per km² × area (500 in a city
  cell).
- `[pastoral]` herding share h = clip((farming − 0.35) / 0.4, 0, 1);
  herding density = forage × (1 − h) + herd density × h (× climate herd
  factor); herding K likewise. K = max(farming K, herding K).

### 5.4 Spacing `[separation]`

Outside city cells a lineage fills only pref = 1 − 0.8 × separation² of
K. Growth, migration pressure and room use K × pref.

---

## 6. Climate `[climate]`

- Moisture anomaly per cell m = Σ patterns × series + local field − abrupt
  events.
- Patterns (each standardized), weights normalized with the local term:
  world 0.35, latitude (cos 4·lat) 0.25, inland (distance to coast) 0.25,
  4 regional Gaussian fields (σ 20 cells) 0.35 each; local field 0.45
  (σ 6 cells, on the full grid; `CLIM_LOCAL_COARSE` > 1 draws it
  coarser and interpolates, for speed; default 1, U 2026-11-17).
- Each pattern's series sums five standardized components: white 30%;
  damped oscillator period 60 yr damping 60 yr 15%; period 200, damping
  250, 20%; period 1500, damping 1500, 20%; red noise τ 400 yr 15%.
- Local field: a new Gaussian field (σ 6 cells) each tick.
- Abrupt dry events: rate 1 per 2000 years; one in four worldwide, else a
  regional footprint (Gaussian field σ 25, positive part, scaled to max
  1); length U(150, 400) years; depth U(1.5, 2.5) sd; sets in over 25
  years and lifts over 75.
- Precipitation anomaly pa = clip((0.10 + 0.12 × dryness) × m, −0.7,
  0.7); elasticity e = 1 + dryness.
- Rain factor = clip(1 + e × pa, 0.1, 1.6). Forage factor = clip(1 + 0.8
  × e × pa, 0.2, 1.5).
- Irrigation factor = sqrt(clip(Qₜ / Q, 0.2, 2)), where Qₜ accumulates
  runoff × clip(1 + 1.5 × pa, 0.05, ∞) over the catchment.
- Biome edge shift f = clip(0.35 × (|m| − 0.5), 0, 0.7) × proximity of the
  drier (m < 0) or wetter ecotone biome. Rain, forage and herd factors ×
  (1 − f + f × table value of the target biome / that of the cell's
  biome).
- Granaries: each factor moves toward its raw value with α = DT / (DT +
  τ), τ = 15 × the ruling lineage's administration years inside a state
  (0 outside); `[patience]` τ × (0.5 + patience).
- River course changes: river cells on alluvium with relief < 0.3 km,
  elevation < 0.3 km and discharge > 1000 m³/s change course with chance
  DT × 2.5×10⁻⁴ × clip(Qₜ / Q, 0.3, 3)² per tick, at most 3 per tick. The
  new course runs to a neighbour no more than 0.03 km higher that does not
  drain back through the cell (or to the sea from a coastal cell), chosen
  with weight exp(−(elev − min elev) / 0.01).

### 6.1 Famine movement

- Each cell with pop − 1.05 K > max(10, 0.05 K) is a source; at most the
  600 largest excesses.
- Each source tries 16 random cells within ±8 rows and columns on the
  same landmass, empty or of the same lineage. Room = (K − pop) × (colon
  ease if empty).
- The source moves min(0.5 × excess, room) to its roomiest target if room
  > 10; one band per target per tick. Empty targets take the source's
  lineage.

---

## 7. Growth

- r_eff = r' × (0.6 + 0.4 × farming) × frontier, with r' = R_SCALE × r
  and frontier = 1 + FRONT_K × clip(1 − pop / (FRONT_END × K), 0, 1);
  FRONT_K 1.5, FRONT_END 0.5. r_eff is capped at R_MAX where R_MAX > 0
  (declines are not capped). R_SCALE 0.5, R_MAX 0.03 by default
  (**U->C**: adopted 2026-11-18, decision D7, from the WP6 stage A
  experiment; until then 1.0 and no cap). FRONT_K and FRONT_END are **C**.
- `[dragons]` r_b = r' − dragon cut (section 8); r_eff = r_b × (0.6 + 0.4
  farming) × (frontier if r_b > 0, else 1), capped at R_MAX.
- pop ← K × pop / (pop + (K − pop) × e^(−r_eff × DT)) where r_eff ≥ 0;
  where r_eff < 0 (a dragon's cut above the growth rate) pop ← min(pop ×
  e^(r_eff × DT), K). (Before 2026-11-01 the closed form was used for
  r_eff < 0 as well; there K repels, and cells above K ran off to huge or
  negative numbers for one tick: the one-tick population spikes.)
- `[minority]` a minority grows logistically to 0.2 × its own K at its own
  r_eff (no frontier term, with the dragon cut; same rule for r_eff < 0);
  the majority's K is
  reduced by the minority's food-equivalents.
- Dragon deaths recorded = (growth without the cut) − (growth with it).

### 7.1 Land use

- `[pastoral]` a cell herds if herding K > farming K and h > 0.
- `[land]` farming intensity = farming × clip(pop / farming K, 0, 1) on
  farmed cells. Land condition changes per year by 0.004 × (1 − condition)
  − 0.0003 × intensity × (1 + 3 × irrigated share) × condition
  (`[patience]` wear × (1.5 − patience)); limited to [0.3, 1].
- `[improvements]` use = farming intensity on farmed cells. Improvement
  changes per year by 0.003 × use × (0.5 + admin of the ruling lineage
  inside a state) × (1 − imp) (`[patience]` × (0.5 + patience)) − (1/400) ×
  (1 − use) × imp; limited to [0, 1].
- `[upkeep]` (WP6 C, 2026-11-18, **C**) improvement also loses 0.1 ×
  shortfall × imp per year, shortfall = clip((0.7 × pmem − pop) / (0.7 ×
  pmem), 0, 1), 0 on herding cells; pmem = the cell's people, exponential
  mean over 50 years (updated after the improvement step).
  `[works_lag]` (WP12 C, 2026-11-22, U; 0.85 **C**) 0.85 in place of 0.7.
- `[salinity]` salt (0–1) changes per year by 0.002 × use × irrigated
  share × (1 − salt) (`[patience]` × (1.5 − patience)) − 0.003 × (1 −
  use) × salt.
- `[clearing]` (2026-11-20, U; **C**) on jungle and temperate-forest
  cells, clear (0–1) moves toward a target: use on farmed cells, 0.5 ×
  clip(pop / herding K, 0, 1) on herding cells, 0 on empty ones. It rises
  at 0.01 × gap per year and falls at (1/150) × gap. In capacity (5.3),
  rain-fed farming, forage and herd are each × (1 + clear × (grassland's
  FARM, FORAGE or HERD / the cell's biome's − 1)).
- `[fire]` (2026-11-20, U; **C**) on temperate-forest cells, burn (0–1)
  moves toward 0.3 × (1 − agri) × clip(pop / farming K, 0, 1) on
  non-herding cells (0 elsewhere). It rises at 0.1 × gap per year and
  falls at (1/20) × gap. In capacity, forage is × (1 + 0.25 × burn ×
  (1 − clear)). Before clearing moves, clear = max(clear, min(burn,
  target)).
- `[clear_terrain]` (2026-11-20, U; **C**) every 50 years, in cells where
  |clear − clear_at| ≥ 0.05, clear_at = clear. Travel cost (2.2, MOVE) and
  terrain defence (TERRAIN_DEF) are each × (1 + clear_at × (grassland's
  value / the biome's − 1)) on jungle and temperate forest.

---

## 8. Dragons `[dragons]`

### 8.1 Setup

- Territory = cells within 80 km of the home. Homes of wild dragons are at
  least 110 km apart.
- Year 0: a random packing of all land cells at 110 km spacing; each site
  is held with chance 0.625.
- Each dragon: age U(0, 3000); tolerance = σ(logit 0.4 + N(0, 1));
  violence = σ(logit 0.5 + N(0, 1)); strength = exp(N(0, 0.3)).
- Grown strength = strength × clip(age / 300, 0.05, 1).

### 8.2 Each tick

1. **Aging.** Age + 5. Death at age 3000; wild dragons also die with
   chance 1/10,000 per year.
2. **Allies.** An ally whose state has ended goes wild. An ally whose home
   is outside its state moves to the capital.
3. **Hunting.** Each wild dragon adds hunting weight w = grown strength ×
   (0.5 + violence) × (1.3 − 0.6 × tolerance) to every cell of its
   territory. Hazard = Σw. Mean strength in a cell = Σ(w × grown strength)
   / Σw. Cells in an ally's territory: hazard × 0.1.
4. **Ward size** of cell j = 3000 / (size^0.75 × (1 + bronze + iron + 1.5
   steel) × (1 + admin × in a state)), × mean strength. A cell is warded
   if its people (with minority) ≥ ward size. `[dragon_hosts]` a cell of a
   dragon-host people has an infinite ward size: never warded, never
   confronted, and never blocking a dragon's site. Young and driven-off
   dragons settle only where every settled cell in reach is of a host
   people (or empty).
5. **Growth cut** (used in growth) = 0.036 × hazard × g(n), g(n) = n / (n
   + n₀) / (1 + (n / ward size)^4), n₀ = 150 / food per head
   `[food_units]` or 150 `[not food_units]`.
6. **Confrontations.** For each wild dragon, the number of cells in its
   territory where people / unscaled ward ≥ its grown strength is counted;
   a confrontation happens with chance 1 − exp(−0.01 × 5 × count). The
   fight is in the most populous such cell, which loses min(0.5, 0.02 ×
   grown strength × (0.5 + violence)) of its people. Then:
   - **Alliance** if the cell is in a state and the joint tolerance (mean
     of the cell lineage's and the dragon's) ≥ 0.75, with chance (joint −
     0.75) / 0.25. The dragon's home moves to the cell.
   - else **slain** with chance min(0.95, (0.3 + 0.5 × lineage violence) ×
     (0.5 + dragon violence) / grown strength);
   - else **pushed**: a new site is sought (below); with none, the dragon
     is lost.
7. **Breeding.** Each dragon aged ≥ 300 breeds with chance 1/1200 per
   year into a new site. The young dragon's tolerance and violence are its
   parent's on the logit scale + N(0, 0.15); its strength is the parent's
   × exp(N(0, 0.15)); age 0.
8. **Site search.** Up to 12 tries: distance 110 km + 300 km × Exp(1) in
   a random direction from the old home. A site is free if no home lies
   within 110 km and no cell within 80 km is blocked. Pushed dragons:
   blocked = warded (or, with `--dragon-shun` s > 0, people ≥ s × ward
   size). Young: blocked = warded or people ≥ 0.05 × ward size.
9. **Host alliances** `[dragon_hosts]`: a wild dragon whose territory
   holds settled cells of a host people inside a state may ally with
   that state with chance 0.01 per year: in the most populous such cell,
   the same joint-tolerance test as in 6, no fight.
10. **Allied strength** per state = Σ grown strength of its allied dragons.

### 8.3 Effects of allies

- State strength × (1 + √(allied strength)).
- Reach × (1 + 0.3 × √(allied strength)).

---

## 9. Movement and settlement

### 9.1 Drift within a lineage

- Pressure = pop / (K × pref).
- Hostility h = 1 − tolerance `[separation]`, else separation.
- Leaving share = 0.04 + 0.3 × expansion × clip(pressure − (0.9 − 0.6 ×
  expansion), 0, 1.5).
- Leavers go to neighbouring cells of the same lineage in proportion to
  room (clip(1 − pop / (K × pref), 0, 1)) × √K / edge cost × (1 − 0.9 ×
  h × [another people borders that cell]).

### 9.2 Budding (run twice per tick)

- A cell buds if pressure > 0.45 − 0.35 × expansion and pop > 20.
- Target: the empty neighbour with the highest √K / edge cost × colon
  ease × (2 if both cells are river cells) × (1 − 0.95 × h × [another
  people borders it]) × U(0.6, 1.4), with K > 20.
- Band = clip(max(10, (0.2 + 0.25 × expansion) × pop), 0.15 × K_target,
  0.5 × pop).
- Where several bands claim one cell, the largest wins; the others return.

### 9.3 Colon ease

Colon ease = cell colonization ease; for wetland peoples the wetness
penalty is reduced in proportion to `wet`; `[improvements]` × (1 + 2 ×
improvement), at most 1.

### 9.4 Pioneer leaps

- Each lineage with cells holding > 300 food-equivalents makes Poisson(3
  × expansion² × (1 + log₁₀(1 + cells))) leaps per tick from those cells,
  weighted by pop × clip(pressure, 0.05, 2).
- From a river cell, with chance 0.6, a river leap: the band follows the
  river up or down (equal chance; upstream branches weighted by discharge)
  for 6 + 30 × sailing cells and settles a random empty cell on the path.
- Otherwise a random offset of 2–6 cells; the target must be empty, on the
  same landmass, pass a colon-ease draw, and have K × food per head ≥ 200.
- Band = min(120 / food per head, 0.2 × source pop).

### 9.5 Voyages

- Sources: coastal cells with > 400 food-equivalents and pressure > 0.5.
- Voyages per lineage per tick = Poisson(2.5 × x × (0.1 + sailing) ×
  √(source cells)), x = expansion `[dispersal]` or seafaring `[not
  dispersal]`; at most 6.
- Range D = 40 + 2500 × sailing^1.5 km. Targets: empty coastal cells
  within min(4D, 9000) km with K × food per head > 300, weighted by K ×
  exp(−distance / D) × colon ease.
- Band = min(200 / food per head, 0.2 × source pop).
- Landing on a landmass new to the lineage (> 200,000 km²) founds a
  daughter lineage (colony, mutation `--drift`).

### 9.5a Colonies `[colonies]`

- Targets also include thinly held coastal cells of other peoples (not
  city cells; natives < 3000 food-equivalents), only when no empty coast
  is in reach and then with chance 0.2 per voyage, weighted ×
  exp(−natives / 3000).
- Natives fewer than the band (in food-equivalents): pushed out, the band
  takes the cell. Otherwise the band joins the cell as its minority.
- A band from a state's cell landing on another landmass, outside that
  state, settles as that state's colony lineage for the landmass (founded
  the first time, one per state and landmass). A city that lineage
  founds outside any state joins the tied state with chance 0.3 + 0.7 ×
  the ruler's statecraft (same people only).

### 9.6 Settler lineages

Cells newly settled in a 5° × 5° block their people has never held found
a daughter lineage (mutation `--settle-drift`) for those cells.

---

## 10. Raids

- On every land edge between two peoples, each side raids with chance
  min(0.9, p), p = DT × 0.02 × violence × (0.5 + pressure) × (1 + h) ×
  τ(0.5) × (0.2 if both cells are in the same state) × (1.5
  if the raider herds `[pastoral]`) × (1 + 1.5 × clip(pressure − 1, 0, 1)
  `[climate]`).
- `[raid_order]` × (1 − 0.6 × admin of the ruler) for each side in a
  state; across a border between two states, × (1 − trade tie), and ×
  0.3 if allied or in truce.
- τ(k) = 1 `[separation]`, or 1 − k × tolerance `[not separation]`.
- Damage = 0.12 × violence × √(raider size / defender size) / defence,
  × 1.6 if the raider herds `[pastoral]`, × (1 + 0.8 × defender expansion
  × clip(1 − 2 × defender pop / K, 0, 1)) `[costs]`; at most 0.6.
- The defender's cell (and minority) loses that share; improvements lose
  0.3 × that share; the raider loses 1%.
- **Take-over:** if the defender is below 0.15 of K, the raider above 0.6
  of K, and a violence draw succeeds, 25% of the raider's cell moves in
  and the cell changes people and lineage. `[minority]` the old people
  stays as a minority of 0.5 × its former population.

---

## 11. Cities and territory

### 11.1 Cities

- A city ends if its cell's people changes, or its population falls below
  0.35 × the people's city threshold.
- Candidates: settled population (herding cells × 0.3) above the city
  threshold; city potential (food-equivalents × locus; herding cells ×
  0.3) is the maximum in its 5 × 5 window; no city within 2 cells.
- A new city in a state's territory joins that state with chance 0.3 +
  0.7 × the ruler's statecraft (same people) or 0.7 (other people);
  otherwise it founds a new state (cohesion 0.6) ruled by its cell's
  lineage.
- A ruin within 2 cells is marked re-founded.

`[urban_city]` (2026-11-09) a city also ends when its urban population
stays below 2,000 for 50 years, and none is founded in famine; see
[structural.md](structural.md).

### 11.2 Territory

- Every cell is assigned to its nearest city by travel cost, if within
  the reach of that city's state.
- Reach = 120 + 900 × admin, × (0.6 + 0.4 × fed) `[fiscal]`, × (1 + 0.5
  × herding share) `[pastoral]`, × (1 + 0.3 √(allied dragon strength)).

### 11.3 Roads `[roads]`

- Every 50 years: road stock × exp(−50 / life), life 1500 years inside a
  state and 300 outside.
- Each state of 2+ cities adds 0.6 × admin × (1 − road) along the
  cheapest path from its capital to each city (and the capital), within
  1.5 × reach; `[patience]` × (0.5 + patience).
- Travel cost × (1 − 0.5 × road stock).

---

## 12. States

### 12.1 State record

Ruling lineage, people, capital, cities, cohesion S, trade, fed, crowding,
elite load, stress, herding share, vassal years, next succession year,
population, strength.

### 12.2 Each tick

- A ruling lineage with no people left passes to the capital cell's
  lineage.
- **Strength base** = Σ over the state's cells of pop × size: own people
  × 1; other peoples × (0.4 + 0.5 × ruler tolerance); herding cells ×
  1.6 `[pastoral]`; minorities likewise `[minority]`.
- **Strength** = base × (0.5 + violence) × (1 + bronze + iron + 1.5 steel)
  × (0.3 + 0.7 S); × (0.4 + 0.6 fed) `[fiscal]`; × (0.85 + 0.3 ×
  hierarchy) `[hierarchy]`; × (1 + √(allied dragon strength)).
- **Fed and crowding** (`[fiscal]`, `[unrest]`, `[pastoral]` or
  `[climate]`): fed = Σ min(pop, K) / Σ pop; crowding = Σ pop² / K / Σ pop;
  each moves 20% of the way toward its new value per tick.
- **Elites** `[unrest]`: elite ← clip(elite + DT × g × elite × (crowding −
  0.75) / 0.25, 0.3, 4), g = 0.004 (× (0.5 + hierarchy) `[hierarchy]`).
- **Stress** `[unrest]` = max(0, crowding² × elite − 0.6) × (1 + 2 × x ×
  hunger) `[costs]` × (1 + 4 × hunger); hunger = 1 − fed; x = hierarchy
  `[hierarchy]` else statecraft. `[mission]` + 10 × the state's churn
  (people-weighted, 16.1).
- **Cohesion:** S changes per year by 0.04 × cohesion trait × S × (1 −
  S) × (0.3 + frontier share) − 0.004 × S × (1 + 0.5 ln(1 + cities)) × (1
  + age / 600); limited to [0.02, 1]. Age = years since the current
  dynasty began `[dynasty]` (the state's founding, a change of ruling
  lineage, or a disputed succession), or since the state's founding
  `[not dynasty]`. Frontier share = border edges facing
  another people (or `[pastoral]` a herding/farming divide) / all border
  edges.
- **Assimilation:** cells of the ruler's people but another lineage take
  the ruling lineage with chance DT × 0.008 × (0.5 + ruler statecraft)
  (× (0.5 + ruler proselytism) `[proselytism]`).
- **Adjacency:** states sharing a land edge, plus states with coastal
  cities within 2 × the sailing range of either ruler (recomputed every 20
  years).
- **Tribute** `[vassals]`: 25% of a vassal's strength moves to its lord.
- **Land value:** a state's capacity in food-equivalents per km² over its
  settled cells.
- **Room** `[land_pressure]`: settleable empty cells (capacity × food per
  head > 200 for the lineage next to them) touching the state's settled
  cells, ÷ (0.1 × the state's cells), at most 1.
- **Land pressure** `[land_pressure]` = clip((crowding − θ) / (1 − θ), 0,
  1) × (1 − room), θ = 1 − 0.35 × the ruler's dominance.

### 12.3 Trade

- Ties between non-adjacent or warring states fall × 0.9 per 5 years and
  vanish under 0.02.
- For adjacent states at peace: growth g = trade_a × trade_b × (0.4 + 0.3
  × (tol_a + tol_b)), with trade_a, trade_b the ruling lineages' trade
  traits, × acceptance × (1 + mean share of cities on rivers) × (1.5 if
  they share a river basin).
  - `[not trade_assets]` acceptance = trade acceptance; tie ← tie + DT ×
    0.03 × g × (1 − tie).
  - `[trade_assets]` acceptance a = acceptance at level (0.3, 0.15),
    raised to a + (1 − a) × min(1, X), with X the pair's exchange value
    (12.7); g × (1 + min(X, 2)); tie ← 1 − (1 − tie) × exp(−DT × 0.045 ×
    g).
  - `[development]` g × (1 + 0.5 × the mean development of the two
    rulers).
  - `[war_v2]` g × (1.25 − 0.5 × the mean dominance of the two rulers).
- A state's trade volume = Σ of its ties (+ 0.3 per resource kind held
  `[resources]`); used in the city capacity factor.

### 12.4 Minorities `[minority]`

- For each tie ≥ 0.5 between peoples, each side with chance DT × 0.01 ×
  tie settles merchants at the other's capital: 0.03 × tie × capital pop
  × (host food per head / guest food per head).
- A foreign minority in a state is expelled with chance DT × 0.01 × h ×
  τ(1) of the ruler.
- A minority under 5 (or under 20 in an empty cell) vanishes; one of the
  majority's people merges; one that outweighs the majority in
  food-equivalents becomes the majority (a city carries on under it).
- At most one minority people per cell. Contact weight for borrowing and
  acculturation 2.0.
- `[shared_cells]` (WP7 C, 2026-11-18; U: presence table, niche overlap,
  raids inside a cell; numbers **C**) replaces the last two points: any
  number of peoples per cell, one row each (one lineage per people per
  cell). Each tick the rows of a cell are ordered by food-equivalents
  (plurality first; a city follows its plurality); rows of one people
  merge; rows under 5 heads (20 in a cell with no main people) vanish.
  - Growth: a non-main row grows (no frontier term) toward K_i − Σ_j
    α_ij (w_j / w_i) f_j / e_i, α_ij = 0.9 × overlap_ij, w from the
    dominion weights, f food-equivalents, e food per head; the main row's
    K loses the same sum. A merchant quarter keeps its cap (0.2 K).
    overlap = 1 − 0.5 |herds_i − herds_j| − 0.5 × TV(biome affinities),
    TV half the summed absolute difference of the normalised vectors.
  - Movement: a row above its migration threshold (0.9 − 0.6 expansion,
    crowding against K × fill preference) sends 0.1 × expansion × the
    excess of its heads per tick (at most half the room) to the
    neighbouring cell held by another people with the largest room ×
    √K / edge cost × (1 − 0.9 (1 − holders' tolerance) min(1, w_holder /
    w_mover)); room = K − 0.9 × overlap with the holders × (Σ w f of the
    others) / w / e − heads already there. Settlers of the ruling people
    inside their own state meet no resistance.
  - Raids inside a cell between rows of different peoples: chance DT ×
    0.02 × violence × (0.5 + crowding) × (1 + hostility), × 0.2 inside a
    state; damage 0.12 × violence × √(size ratio) / defence × hardiness,
    at most 0.6; raiders lose 1% × hardiness.
  - Further rows take the minority's share of raid, ravage, sack and
    plague losses, and count as minorities in state strength, extraction,
    the food flows, dragons' head counts and Price.
- `[displacement]` (WP7 D; U: share fleeing = 1 − violence): of those
  removed by a raid takeover, a sack, a clearance or an expulsion, a share
  1 − the attacker's (or ruler's) violence flees; each band goes to the
  cell with most room among 16 drawn within 3 cells on its landmass where
  its people already live or the land is empty. Those with no room die.

### 12.5 Diplomacy

- **Threat** for each neighbouring pair: the strongest common neighbour's
  strength / (sum of the pair + 1); if over 1, threat = min(1, (ratio −
  1) / 2) `[balance]`.
- **Alliance breaks** with chance DT × 0.004 × (1 − alliance acceptance) ×
  (1 − threat).
- **Alliance forms** with chance DT × 0.005 × alliance acceptance × (0.3 +
  tie) + DT × 0.005 × 4 × threat × trade acceptance.
- **Fusion:** allied states with tie ≥ 0.3 fuse with chance DT × 0.0025 ×
  fusion acceptance × mean statecraft. The more populous state keeps its
  id and takes the other's cities; cohesion is the larger. In the merged
  territory each ruling lineage is replaced by a new lineage of its
  people whose TRAITS and XTRAITS are the population-weighted mean of the
  two, technology the better of the two, stages in use and known the
  union.

### 12.5a Alliance rules

- `[ally_duty]` A state attacked calls each ally not allied to the
  attacker; the ally joins with chance 0.3 + 0.7 × min(1, (ally +
  defender strength) / attacker strength), else refuses and the alliance
  ends. Only joined allies help defend (0.35 × projected strength); they
  count as at war for experience and war cost.
- `[ally_lapse]` Any alliance lapses at 0.002 per year.
- `[ally_balance]` Alliances are formed for affinity or for balance (the
  balancing term). A balance alliance ends at 0.02 per year once no
  common neighbour outweighs the pair. Any alliance ends at 0.01 × min(1,
  (ratio − 3) / 3) per year when one ally is more than 3 × as strong.
- `[betrayal]` Allies may attack each other at 0.15 × the war chance; the
  alliance ends.

### 12.5b Trading posts `[trade_posts]`

- Each tick a state with a coastal city plants a post with chance 5 ×
  0.02 × trade × sailing: its merchants (0.02 of the city) settle as the
  minority of a foreign coastal city within 4 × its sailing range that is
  not a neighbouring state and not of its people, chosen by city size ×
  exp(−distance / (2 × range)).
- The two states form trade ties as neighbours do while the merchants
  remain (minority expulsion, city loss or the planter's end removes the
  post).

### 12.6 Vassals `[vassals]`

- A vassal throws off its lord with chance DT × 0.01 × min(2, 2 × vassal
  strength / lord strength) × (1.5 − lord S) × (1.5 if of another people);
  truce 10 years.
- A lord annexes a vassal of its own people with ≤ 3 cities and ≥ 50
  vassal years with chance DT × 0.004 × (0.5 + lord statecraft).
- A vassal does not fight its lord; an ally pair is dissolved when one
  submits.

### 12.7 Assets

- Kinds held `[resources]`: the kinds of resource sites inside the
  state's territory on settled cells.
- Ores in hand: those of its ruling lineage (15.4).
- Craft `[craft]` and guarded techniques `[guarded]`: those of its ruling
  lineage.
- What state a offers state b = (kinds b lacks) + 0.3 × (ores b lacks) +
  max(0, craft_a − craft_b) + (techniques b lacks).
- Exchange value X = √(offer(a, b) × offer(b, a)).

---

### 12.8 Value of goods `[goods_value]` and precious metals `[precious]`

- Each lineage values kind k at (0.5 + craftsmanship) × preference_k.
- Preferences per people: lognormal (median 1, σ 0.5) × starting bias by
  group: favoured × 2, disdained × 0.25. Groups: plant (incense, spice,
  fragrant timber, dark hardwood, fine fibre, cotton fibre), gem (lapis,
  jade, obsidian, pearls), metal (electrum, gold, silver), animal (ivory,
  purple dye, pearls), amber, ivory.

  | People | Favoured | Disdained |
  |---|---|---|
  | Elves | plant, gem | |
  | Lizardfolk | amber | |
  | Dwarves | gem, metal | |
  | Goblins, Frogloks | gem, animal | plant |
  | Giants, Ogres, Trolls | ivory, metal, gem | |
  | Humans, Snake folk | | |

- Daughter lineages inherit preferences × lognormal(0, drift). Each tick
  lineages under a ruler of another lineage move 0.01 of the way to the
  ruler's preferences; ruling lineages of trading states move 0.01 × tie
  toward each other.
- A kind state a holds and b lacks is worth b's value of it in trade
  offers and as a war prize (instead of 1).
- Precious sites (v2): reserve 1 at the start. Worked while held by a
  state (lode gold and silver need bronze), a site yields output =
  reserve, and reserve falls by 1/600 per year (placer gold 1/300). A
  state's output O per metal: trade offer + value × O / (1 + partner's
  O); war prize + value × O; strength × (1 + 0.3 × min(1, total O)).

## 13. War

### 13.1 Declaration

For each adjacent pair not at war, not allied, not in truce, not
lord–vassal, each side in turn; `[shuffle]` the pairs in random order and
the first side at random:

- p = DT × 0.012 × violence × S × min(3, strength ratio)^1.2 / 2 × (0.5 +
  (1 − similarity) × (1 + 1.5 × h)) × (1 − tie) × τ(0.4).
- `[war_v2]` replaces everything below in this section:
  - chance = DT × 0.12 × S × (0.5 + violence) × (1 − tie) × deterrence ×
    c(0.004 + Σ motives), with c(x) = x / (1 + x / 2).
  - `[war_odds]` deterrence = f + (1 − f) / (1 + exp(−(ln R − ln 0.7) /
    0.35)), f = 0.05 × min(1, R / 0.7) × min(1, (1 − fed) + enmity + faith motives). A
    siege is laid only at win probability ≥ 0.15; below it the attacker
    ravages the hinterland (chance = violence; 0.1 × violence of its
    people die, improvements × (1 − 0.3 × that)) or sits. No siege for
    15 years ends the war ("abandoned"). Before a siege a defender
    facing odds p ≥ 0.6 submits with chance clip((p − 0.6) / 0.4) ×
    (1.2 − cohesion) × (0.5 + attacker's dominance) (otherwise: only
    at a 3:1 projected edge, at half that chance), and it never cedes
    its last city.
  - `[site_defence]` terrain defence at a city × the site's own m =
    clip(exp(0.18 × t₃), 0.5, 3), drawn once per cell (0.12 until
    2026-11-18; U: wider).
  - `[ruler_mil]` a besieging (or cession-pressing) state's projected
    strength × (1 + g + legacy); g ~ exponential(0.1) capped at 1 per
    ruler; legacy → 0.5 × (legacy + g) at each succession.
  - `[not war_odds]` deterrence = min(1, 2 R² / (1 + R²)), R = the attacker's strength
    projected to the target's city nearest the attacker's capital, over
    the target's there (with its allies at 0.35, × 1.4 × terrain defence
    × 1.25 at a capital × (1 + 0.5 × development) `[development]`), as in
    13.2.
  - Motives:

    | Motive | Value |
    |---|---|
    | land | (2 × (1 − fed) `[climate]` + 1.5 × land pressure `[land_pressure]`) × clip(target's land value / own, 0.5, 2) |
    | prey | 1.5 × dominance × min(1.2, crowding) × clip((R − 1) / 2, 0, 1) |
    | rule | dominance × min(2, target population / own) `[dominance]` |
    | resource | (target's resource kinds the attacker lacks + 0.3 × ores worked in the target's territory the attacker lacks + max(0, craft gap) + guarded techniques the attacker lacks) × (0.5 + dominance) |
    | enmity | 1.5 × (1 − similarity) × hostility |
    | faith | as below `[mission]` |
    | irredentism | 1.5 × min(1, cities the target holds that the attacker once held / 2) |

  - With chance Σ motives / (0.004 + Σ motives) the war has a goal
    `[war_goals]`, from the largest motive: land, prey, enmity → the
    target's city nearest the attacker's capital; rule, faith → its
    capital; resource → as below; irredentism → a lost city.
  - While at war, the people of both states lose 0.1% per year.
- `[not war_v2]`, the two rules below apply.
- `[not war_motive]`:
  - `[dominance]` × (0.5 + dominance) × (1 + 0.5 × dominance × min(2,
    target population / own population));
  - `[climate]` × (1 + 2 × (1 − fed)).
- `[war_motive]` p = 0.5 × p + p_m, with motives resource = offer(target,
  attacker) (12.7), rule = dominance × min(2, target population / own
  population) `[dominance]`, land = 2 × (1 − fed) `[climate]` (+ 1.5 ×
  land pressure, and a prey motive as in `[war_v2]` with the plain
  strength ratio, `[land_pressure]`), faith =
  (1 − similarity) × (own proselytism + target's proselytism × (1 − own
  tolerance)) `[mission]`; summed
  motive m, saturated as m / (1 + m / 2); p_m = DT × 0.012 × 3 × (0.5 +
  violence) × S × min(3, strength ratio)^1.2 / 2 × (1 − tie) × the
  saturated motive.
- War with chance min(p, DT × 0.1); the tie is cut.
- `[war_goals]` with chance p_m / p the war has a goal, from the largest
  motive: resource → the target's city whose territory holds a site of a
  kind the attacker lacks (else its capital); rule → the target's capital;
  land → the target's city nearest the attacker's capital; faith → the
  target's capital.

### 13.2 Sieges

- Logistics of a state G = admin × (0.5 + statecraft) of its ruling
  lineage.
- Sieges per war per tick: 1 + floor(2 × G of the attacker)
  `[logistics]`, else 1. Each siege below is repeated while the defender
  has cities.
- `[war_goals]` before the sieges, a defender whose goal city (land,
  prey, resource or irredentism goals) is held cedes it with chance 0.3
  per 5 years × clip(A / D − 1, 0, 1)
  at that city (D with the × 1.4 × defence term): the city passes without
  losses, the war ends, truce 30 years.
- Target: the goal city while held and not yet taken `[war_goals]`, else
  the defender's city nearest the attacker's capital.
- Projected strength = strength × exp(−distance / (1.5 × reach × (1 + G
  `[logistics]`))).
- Defender: + 0.35 × each ally's projected strength (not allies of the
  attacker); `[vassals]` + 0.5 × its lord's, + 0.35 × each of its
  vassals'. × 1.4 × defence × 1.25 at a capital; `[development]` × (1 +
  0.5 × the defender's development).
- `[vassals]` if the defender is not a vassal and attacker > 3 ×
  defender, the defender submits with chance 0.5 × (1.2 − S_def) (× (0.5
  + attacker dominance) `[dominance]`); the war ends, truce 30 years.
- `[devastation]` each siege (either side's) lays waste, with chance
  0.03, one cell chosen at random among the besieged city and its
  neighbouring cells held by the city's holder: the cell's capacity
  factor drops to 0 and recovers by DT / 100 per tick (full after 100
  years); K × that factor (U 2026-11-01; numbers C).
- Otherwise the target loses 3%; the attacker takes it with chance A² /
  (A² + D²), else loses 0.02 × (1.5 − G / 1.5 `[logistics]`) of S.
- The war ends with chance, per 5 years, (0.12 + 0.006 × years elapsed)
  × (1 − 0.6 × G / 1.5 `[logistics]`), at least 0.8 once the goal city
  is taken `[war_goals]`, or when the defender falls; truce 30 years.

- `[pol_step]` (WP5 D, 2026-11-18, C) the war step runs every year
  inside the tick, with the chances above per 5 years applied as 1 − (1
  − p)^(1/5) and per-year rates × 1. A siege lasts ceil(Exp(1.0 × D))
  years, 1-8, D = 1.4 × terrain × site × walls × 1.25 at a capital; the
  city loses 3% over the siege; it is decided at its end on the odds
  then. Each side runs 1 + floor(2 × G) sieges at once at distinct
  cities. After a year in which a city changed hands territory is
  redrawn and strength scaled by the change in weighted population.

- `[army]` (WP5 E, 2026-11-18, C) states at war raise a field army
  toward 4% of their people, closing dtp / 2 of the gap a year, from
  their own people's cells; the army eats from those cells' capacity
  (at most half; `taken_army`); in peace survivors return. Field share
  f = army / (0.04 × people): siege and cession strength × f, city
  defence × (0.5 + 0.5 f). A decided siege kills 20% of the loser's
  army and 5% of the winner's ("battle"). Ending chance per 5 years =
  0.12 + 25 × max over sides of soldiers lost / people (instead of
  0.006 × years). No WAR_COST.
- `[muster]` (WP13 B, 2026-11-21, C) a declaring state's army starts at
  0.5 of its full levy, raised at once from its own cells.
- `[campaign]` (WP13 B, C) a land, rule or resource war that takes its
  goal aims next at the defender's city nearest the attacker's capital
  while the attacker's strength there is ≥ 0.7 of the defence.
- `[ruler_odds]` (WP13 B, U 2026-11-21) the attacker's strength ratio in
  the war decision × its offense.
- `[camp_tribute]` (WP13 B, C) a herding camp (herding share ≥ 0.5)
  makes the states of cities it wins or is ceded its tributary vassals
  instead of annexing them, and annexes no vassal.
- `[vassal_annex_cross]` (WP13 B, C) lords annex vassals of another
  people at the kin rate (0.004 a year × (0.5 + statecraft)) × (1 −
  vassal's tolerance) × lord's dominance.

### 13.2a Counteroffensives `[two_sided]`

- In each 5 years of a war the defender strikes back with chance 0.5 ×
  R² / (1 + R²), R = defender / attacker strength: as many sieges as its
  logistics allow, at the attacker's cities it lost in this war first,
  else any, nearest its capital first.
- Odds PB² / (PB² + PA²); PA = the attacker's projected strength at the
  city with its allies (0.35 × theirs, those not allied to the defender),
  lord and vassals × 1.4 × terrain × 1.25 if capital × walls. (The
  allies' share was missing from the code until 2026-11-07.) A capture is
  a capture as in 13.3; a failure costs the defender cohesion as a failed
  siege costs an attacker.
- An attacker that has lost more cities than it took ends the war at 0.8
  per 5 years ("repulsed").

### 13.3 Capture

`[war_terms]` (2026-11-09) a won siege may instead make the defender a
tributary or be a sack that leaves the city to it; see
[rules/war.md](rules/war.md) and [structural.md](structural.md). Food
flows `[food_flow]` (rent, tax, carriage, trade food) are described there
too, and `[trade_debit]` (WP4 stage B, 2026-11-17; on by default since
WP4 D, 2026-11-18), under which trade food is debited from the exporting
state's surplus cells and loses carriage on the way between the two
states' nearest cities.

- `[improvements]` the city's hinterland improvements × (1 − 0.3 ×
  violence), the city's × (1 − 0.6 × violence).
- The city (and minority) loses (0.1 + 0.4 × violence) × (1 − 0.5 ×
  dominance `[dominance]`).
- Attacker S + 0.03 (at most 1).
- **Clearance** of a city of another people with chance h × violence ×
  τ(1) × (1 − dominance `[dominance]`): that people's hinterland
  cells × 0.15, the city × 0.3, improvements there × 0.5.
- `[minority]` a garrison of the conqueror's people: 0.04 × city pop ×
  food-per-head ratio.
- **Capital taken:** defender S × 0.6. With no cities left, it ends. A
  same-people defender with ≤ 3 cities left is absorbed. Otherwise with
  chance 0.4 it shatters: each remaining city founds a state (cohesion
  0.5) under its cell's lineage. Otherwise the most populous city becomes
  the capital.

---

### 13.4 Camp polities `[camps]`

(WP5 F, 2026-11-18; U: build, outside the city table; C numbers.)
- Every 25 years per lineage: stateless cells within 500 km of its
  densest stateless cell; score = heads × cohesion trait × (0.5 +
  hierarchy); score ≥ 2.1×10⁴ → a camp polity at that cell with chance
  0.2. Every 25 years a camp disperses if its lineage's score in its
  land < 7,000.
- Seat moves every 10 years to its lineage's densest cell in its land.
  Reach 300 × S × (1 + 1.5 × herding share). No rent, tax or tribute.
  Successions as for states.
- Not besieged: a battle at the seat, once a year, at odds ≥ 0.15, the
  camp's strength × 1.5; won: vassal with chance (0.5 + dominance) / 2,
  else scattered. Lost: the attacker's cohesion as for a failed siege.
- Holding a city makes it an ordinary state (capital: its largest city).

## 14. Rebellion and succession

### 14.1 Revolts

- Each non-capital city of a state with 2+ cities revolts with chance DT
  × 0.0009 × (distance to capital / reach)² × (1.5 − S) × (1 + 3 × (1 −
  similarity of its lineage to the ruler) × (1 − 0.6 × ruler tolerance)) ×
  (1 + 0.2 ln cities) × (1 + 3 × stress `[unrest]`).
- `[state_view]` (WP15, 2026-11-22, U; form **U**, no new numbers) the
  similarity is of the city's culture to the state's view, and the
  tolerance is the view's: view = ruler lineage + its tolerance ×
  (state culture − ruler lineage). The same view's tolerance sets
  foreign subjects' weight in strength and the expulsion rate.
- `[unrest]` a revolt cuts elite × 0.8 (minimum 0.3).
- **The breakaway:** a new state (cohesion 0.75). If the city's lineage
  is the ruling lineage, the rebels found a daughter lineage (mutation
  `--drift`) for the hinterland cells of the breakaway. Cities of the same
  people within 400 km of the rebel city and nearer to it than to the
  capital join with chance 0.6 each. The old state's S × 0.9.

### 14.2 Succession `[succession]`

- States of 1+ cities (SUCC_MIN_CITIES; 3+ until 2026-11-18, U: small
  states too): reigns last Exp(25 years), at least 5.
- Crisis chance per reign = 0.12 × (1.3 − 0.6 × statecraft) (× (0.5 +
  violence) `[costs]`).
- A crisis: S × 0.8, elite × 0.85; with chance min(0.9, 0.3 + 0.3 ×
  stress) a pretender takes the largest provincial city (a revolt).

---

### 14.3 Rulers `[rulers]` (replaces 14.2 when on)

- Each state's ruler reigns Exp(25 × lifespan) years (first reign 25 ×
  lifespan).
- At a ruler's death, in order:
  - partition with chance partibility × min(1, cities / 6) (4+ cities):
    2–4 heirs (min(2 + U{0,1,2}, cities / 2)); seats are the capital and
    the cities farthest from other seats (× √pop); every city goes to the
    nearest seat; each seat but the capital becomes a state of the same
    lineage; truce among heirs 20 years;
  - else a disputed succession as in 14.2, chance × (1 + 0.3 × max(0,
    reign / expected − 1));
  - for 10 years: revolt chance × 2; neighbours' war chance against the
    state × (1 + their dominance);
  - each alliance lapses with chance 0.3 × (1 − trade tie);
  - each vassal defects with chance 0.2 (× 1.5 if of another people);
  - union of crowns: for each ally, chance 0.01 (U cut from 0.03, 2026-11-01) × accept(1.0, 0.06): the
    two states fuse (first success only).
- Partibility: a cultural trait, 0.1 for every people at the start;
  daughter lineages drift on the logit scale (2.5 × drift), not
  acculturated.

## 15. Technology

### 15.1 Contact

Between living lineages: shared land edges (1 each), rule (0.5 per ruled
cell of another lineage), `[minority]` minority presence (2.0 per cell),
symmetrized; plus 30 × tie between ruling lineages. Contact C = clip(sum
/ 60, 0, 1).

### 15.2 Borrowing

Borrowing of a technology at factor f = f × max over contacts of (C ×
positive gap) × (0.3 + innovation) × (1 − 0.5 × cohesion `[costs]`).
`[closed_borrow]` (WP14 B, 2026-11-22, U; **C**): innovation in place of
(0.3 + innovation).

### 15.3 Progress per year

- Size factor g = 0.5 + 0.5 × clip(log₁₀(1 + lineage pop) / 6, 0, 1),
  lineage pop in food-equivalents `[food_units]` or heads `[not
  food_units]`.
- `[scale]` invention factor F = clip((pool / 100,000)^0.3, 0.3, 5) × (1 +
  0.05 × (D − 1)), and g = F. Pool (food-equivalents) = the lineage's own
  people, or for a ruling lineage its state's people if more, plus 0.25 ×
  tie × each of its state's trade partners' people. D = number of biomes
  making up ≥ 5% of the cells of its state (or of its own cells, if more)
  + resource kinds held + landmasses reached − 1. Without `[scale]`, F =
  1.
- Every invention term below is × F; borrowing is not.
- Farming += 0.0009 × innovation × g × (1 − farming) + borrowing (0.004);
  limited to [0, 1].
- Metallurgy += 0.0005 × innovation² × [farming > 0.5] × (1 + ln(1 +
  cities) / 3) + borrowing (0.0008). Cap 1.2 before bronze, 2.0 before
  iron, 3.5 after (bronze/iron known `[supply]`, in use otherwise).
  `[tech_forget]` (WP14 B, 2026-11-22, U; **C**) a known stage out of
  use for 300 years is forgotten with the stages above it, and
  metallurgy = min(metallurgy, its threshold − 0.2) (thresholds 1.0, 1.8,
  2.6).
- `[fishing]` fishing += 0.001 × innovation × (waterside share + 0.05) ×
  (1 − fishing) + borrowing (0.002); limited to [0, 1].
- Sailing += 0.0012 × y × (coastal share + 0.1) × (1 − sailing) +
  borrowing (0.001); y = innovation × (0.5 + fishing) (`[dispersal]` and
  `[fishing]`), innovation (`[dispersal]` only), seafaring (`[not
  dispersal]`).
- Administration += 0.0008 × statecraft × (1 − admin) × √(clip(cities /
  5, 0, 1)) (× (1 + war share) `[experience]`, 16.2) + borrowing (0.002).
- `[craft]` craft += 0.0006 × craftsmanship × (0.5 + patience) ×
  √(min(1, cities / 3)) × (1 − craft) + borrowing (0.001); `[supply]` −
  0.001 × idle × craft.
- `[domestication]` each package: lineages with a cell of > 300
  food-equivalents within 300 km of its hearth develop it at 0.002 ×
  innovation × F × (1 − level); all borrow it (factor 0.003) × (0.3 + 0.7
  × share of their people in the package's biome).
- `[guarded]` a lineage ruling a state of ≥ 3 cities with craft ≥ 0.6
  develops a new guarded technique with chance 1/3000 per year (at most 6
  in the world: silk, porcelain, glass, lacquer, fine steel, true dye).
  Each leaks to each contact with chance 1 − Π over holders of (1 − DT ×
  0.0003 × C × (1.5 − cohesion) × (1.5 − conformity) of the holder) per
  tick. On a capture, each technique of the defender's ruler passes to
  the attacker's ruler with chance 0.25 (0.5 at the capital).
- `[supply]` idle share = share of the lineage's people outside any state;
  administration − 0.002 × idle, metallurgy − 0.0004 × idle; both kept ≥
  0, administration ≤ 1.
- `[supply]` loss by disuse, per year:
  - farming − 0.001 × u × (farming − 0.25), u = share of the lineage's
    people in herding cells or in cells below 0.1 × K;
  - fishing − 0.001 × (1 − waterside share) × (fishing − 0.1) `[fishing]`;
  - sailing − 0.001 × (1 − coastal share) × (sailing − 0.025).
- Shares (waterside, coastal) are population-weighted over the lineage's
  cells; cities counts the lineage's city cells.

### 15.4 Metal stages

- Worked deposit: a cell within 120 km of the ore with > 1000
  food-equivalents.
- Ore in hand: copper, tin, iron each held if the lineage has a worked
  deposit, or a contact stronger than 0.4 with a lineage that does.
- `[ore_trade]` copper and tin are also held by every lineage with people
  in a state joined, by a chain of trade ties each ≥ 0.3, to a state whose
  territory holds a worked deposit (the state itself included).
- Bronze: metallurgy ≥ 1.0, copper and tin. Iron: ≥ 1.8, iron, and bronze
  (known or now). Steel: iron conditions, ≥ 2.6, and ≥ 6 cities.
- `[supply]` a stage reached is known for good; in use while its
  conditions hold, and for 20 years after they lapse.
- `[not supply]` a stage once reached stays in use.

### 15.5 Effects

- Metal: strength × (1 + bronze + iron + 1.5 steel); tools on farm yield;
  ward size divided by the same factor; adaptation of biome fit.
- Farming: density blend; growth × (0.6 + 0.4 farming); herding
  `[pastoral]`; adaptation.
- Sailing: voyage range and rate; river leap length; sea adjacency.
- Fishing: water factor on K; sailing invention.
- Administration: reach; granaries `[climate]`; roads; improvements;
  ward size in a state; city cap (if on); logistics.
- Craft: assets (12.7); prestige in acculturation; guarded techniques.
- Domestication: farm and herd density (5.3).

### 15.6 Development `[development]`

- Development (0–1) = mean of (farming − 0.25) / 0.75, metallurgy / 3.5,
  sailing, (fishing − 0.1) / 0.9, administration, craft `[craft]`, and
  the best domestication level `[domestication]`, each clipped to [0, 1].
- Effects: capacity × (1 + 0.25 dev); city-cell factor × (1 + 0.25 dev
  of the ruler); siege defence × (1 + 0.5 dev of the defender); trade tie
  growth × (1 + 0.5 × the pair's mean dev).

---

## 16. Acculturation `[acculturation]`

- Traits moved: the TRAITS and the XTRAITS; seafaring is not moved
  `[dispersal]`.
- **Contact pull** `[not mission]`: weight of contact j on lineage i = C_ij × √(pop_j),
  pop_j in food-equivalents `[food_units]` or heads `[not food_units]`
  (× (0.5 + proselytism_j) `[proselytism]`) (× (1 + craft_j) `[craft]`). Target = weighted mean
  traits of the contacts.
- Openness = tolerance (+ 0.5 × weighted mean proselytism of contacts
  `[proselytism]`).
- Change per year = 0.001 × openness × min(1, Σ C_i) (× (1.5 −
  conformity) `[conformity]`) × (target − own).
- **Mission** `[mission]` (replaces the contact pull): contacts split
  into Cb (shared borders and minorities, C as in 15.1 from those alone)
  and Ct (trade and rule). Lineage i moves per year by Σ_j W_ij × (T_j −
  T_i) / max(1, Σ_j (Cb_ij + Ct_ij)) (× (1.5 − conformity)
  `[conformity]`), with W_ij = 0.0005 × Cb_ij × proselytism_j × S'_ij +
  0.002 × Ct_ij × tolerance_i × S_ij; S = similarity (3.4), S' = S + 0.5
  × proselytism_j × (1 − S).
- **Foreign rule:** a lineage with cells ruled by a lineage of another
  people moves toward the population-weighted mean traits of its rulers
  at 0.01 × (share of its people so ruled) (× (1.5 − conformity)
  `[conformity]`) per year.
- In all, a fall in innovation, seafaring or statecraft is × 0.25.

### 16.1 Churn `[mission]`

A lineage's churn = the summed absolute change of all its traits from
mixing and foreign rule, per century, smoothed with time constant 25
years. It raises political stress (12.2).

### 16.2 Experience `[experience]`

Per lineage, per year: s = share of its people in states at war
(attacker or defender); v = trade volume of the states its people live
in, people-weighted, each at most 1.5, and v₁ = min(1, v); q = share of
its people in cells hit by plague or famine since the last tick; r =
share of its people in cells that raided or were raided since the last
tick; m and h = s and q smoothed with time constant 50 years (war and
hardship memory); safety = (1 − m)(1 − h). A rise of trait x at rate k
is k × (1 − x), a fall k × x; traits kept in [0.01, 0.99].

| Trait | Rises at | Falls at |
|---|---|---|
| tolerance | 0.0005 v | 0.001 s + 0.005 q + 0.005 r |
| trade | 0.00025 v | 0.00005 (1 − v₁) |
| violence | 0.001 s + 0.01 r | 0.00025 v + 0.0002 (1 − m) |
| cohesion | 0.0005 s | 0.0001 v₁ + 0.00005 (1 − m) |
| hierarchy | 0.0005 s | 0.00005 (1 − m) |
| conformity | 0.0005 s + 0.005 q | 0.00025 v₁ + 0.0002 × safety |

---

### 16.3 Experience revisions

- `[trade_mean]` v = min(1.5, 3 × the state's mean trade tie over its
  neighbouring states) (in place of the sum, capped 1.5).
- `[tol_path]` Of the trade push 0.0005 v, the share φ = 0.3 + 0.7 ×
  sigmoid((tol − 0.2) / 0.08) raises tolerance and 1 − φ lowers it.
- `[trade_floor]` Trade acceptance = 0.2 + 0.8 × the usual acceptance
  (before the goods term).
- `[revolt_exp]` u = a lineage's population-weighted mean, over cells, of
  the share of their state's cities lost to revolt this tick (rebels
  included; at most 1). Violence + 0.01 u;
  tolerance − 0.005 u; conformity + 0.005 u; separation + 0.005 u, falling
  at 0.00005 (1 − war memory).
- `[life_memory]` Memory spans × lifespan × (0.5 + patience): experience
  memory (50 years), churn memory (25 years), and grievance: a lost city
  counts for irredentism for 150 years × the same factor.
- `[spiky]` Steady experience change × 0.5. At each generation turnover
  (every 25 × lifespan years, phase by lineage) a lineage takes 12.5
  years of experience change at once; a major event touching its state
  that tick (war begun, capital lost, a revolt taking 20%+ of the
  state's cities, disputed succession, partition, plague) adds 10 years
  (by population share; one per state per tick). A step never
  crosses more than half the way to the balance point.

- `[trait_path]` (U 2026-11-01; form and numbers C) Experience moves a
  culture less when it runs against what the culture already is. For
  each experience-driven trait (tolerance, trade, violence, separation,
  cohesion, hierarchy, conformity), with g = sigmoid((x − pivot) / 0.1),
  the pushes up are × 2 (m + (1 − m) g) / (1 + m) and the pushes down
  × 2 (m + (1 − m) (1 − g)) / (1 + m), m = PATH_MIN: 1 at the pivot.
  PATH_MIN 0.6 (0.75 to 1.25; U 2026-11-01 weaker, number C, under
  tuning: was 0.3, 0.46 to 1.54, which ran traits to the bounds). Pivot
  0.5, but 0.2 for tolerance (the `tol_path` pivot). Acculturation is not
  affected.
- `[superiority]` (U 2026-11-01; form and numbers C) A cultural trait
  (0-1): how far a culture rejects influence from other peoples. Every
  pull on a lineage from lineages of another people (contact
  acculturation weights, and each cell's pull toward a foreign ruler) ×
  (1 − the lineage's superiority), on top of `[acc_cross]`. It is
  inherited by daughter lineages with drift (own random stream,
  89000 + seed), moves toward the superiority of same-people contacts
  only, and moves by experience under `[sup_exp]`. Roster: 0.75, Humans and
  Lizardfolk 0.50, Elves 0.90 (U→C). Recorded in lineages.csv and as
  `superiority_<people>` in timeseries.csv.
- `[sup_exp]` (U 2026-11-01: asymmetries move superiority, symmetric
  causes; rates C) Per tick, for a state's lineages by population share:
  up 0.01 × the share of its cities gained from states of another people
  (a submitting vassal's cities / its own); down 0.01 × the share it
  lost to them (all, if it submits); up 0.0005 × adv, adv = min(1, 3 ×
  mean over its trade partners of another people of tie × (max(0, dev −
  partner's dev) + max(0, craft − partner's craft))); down 0.0005 × the
  same with the partner ahead;
  down 0.00005 throughout (dropped under `[causal_exp]`). Same push form as other experience (spiky,
  path dependence with pivot 0.5). Superiority acts between peoples
  only; resistance within a people is conformity's (U).
- `[causal_exp]` (U 2026-11-01: no secular directionality; forms and
  numbers C) Terms that ran without a cause now need one. Order = share
  of the lineage in a state × its ruler's administration.
  - violence: the peace pull 0.0002 (1 − war memory) × order (life in an
    ordered state pacifies; stateless peace does not);
  - cohesion: the calm pull × order; conformity: the safety pull × order;
  - hierarchy: falls with stateless life, 0.00005 × (1 − in-state share),
    instead of with peace;
  - separation: falls with trade, 0.00005 × min(v, 1), instead of with
    peace;
  - trade disposition: falls with war and raids, 0.0005 × (s + r),
    instead of when unused;
  - superiority: no steady fall.
- `[kin_raids]` (U 2026-11-01; numbers C) Neighbouring cells of different
  lineages of one people raid each other at 0.1 × (0.5 + 0.5 × (1 −
  their similarity)) × the usual chance; `[raid_order]` applies as to
  any raid. Kin raids count as raid experience on both sides.
- All experience pushes × EXP_SCALE (U 2026-11-01: slower experience, so
  inheritance carries more; 0.5, under tuning with PATH_MIN; was 1).
- `[flat_drift]` (U 2026-11-01) Drift at lineage splits adds N(0, 0.625
  sd) in trait units, reflected into [0.01, 0.99] (was N(0, 2.5 sd) on
  the logit scale, which leaned toward 0.5). Goods preferences × exp(e −
  sd²/2), mean 1 (was exp(e), mean above 1).
- `[goods_appetite]` (U 2026-11-01: demand driven by craft, technology,
  administration, violence and trade; form and numbers C) Each lineage's
  appetite for goods moves, over the experience memory span, toward 0.5
  + 1.5 × mean(craft level, development, administration, violence,
  min(1, trade volume)), and falls when they fall. The value of every
  kind of goods × appetite (trade offers, resource war motive).
- `[feuding]` (U 2026-11-02: violence has an internal cost, so stateless
  peoples can stay violent but vary; form and numbers C) Each tick a
  cell loses DT × 0.004 × f × (1 − order) of its people, f = clip((violence
  − 0.6) / 0.4, 0, 1), order = in a state × the ruler's administration.
  Outside a state at violence 0.99 the settled density falls to about
  0.65-0.8 of capacity. More violent lineages lose more, so selection
  acts on violence within a people.
- `[collapse_cost]` (WP12 C, 2026-11-22, U; numbers **C**) disorder per
  cell: 1 when its city's polity changes, its city is gone, or its state
  ends leaving it stateless (checked at each territory redraw); − DT / 50
  per tick. order (feuding), the admin term in raid order, works
  building, the rent rate (`food_flow`), the marketable surplus
  (`trade_debit`) and a city's trade weight are × (1 − disorder).
- `[war_hardy]` (U 2026-11-02: biological; Trolls lose much less from
  losing fights; number U→C) The roster's `hardy` (default 1; Trolls 0.3)
  scales a people's own losses from raids (as defender and attacker),
  war levies, sieges, sacks and clearances. It does not change who wins.
- `[travel_reach]` (U 2026-11-02: roads extend reach; maritime empires
  possible; sailing extends reach over water; form and numbers C) A
  state's revolt risk in a city ((d / reach)²) and its projected
  strength there (exp(−d / 1.5 reach)) use d = travel distance from its
  seats of power, not straight-line km from the capital. Land: cheapest
  route on the travel graph (relief, biome, rivers, roads, straits) ÷
  2.34, the median cost per km of unroaded land, so a full road halves a
  route. Sea, between coastal cells: km × (1.5 − 1.2 × the ruler's
  sailing), from 1.5 with no sailing to 0.3 at full sailing. No route:
  km × 1.5. Recomputed whenever the seats, the travel graph (roads, river
  changes) or, for a coastal seat, the ruler's sailing change
  (2026-11-07; was every 2 ticks or when the seats changed).
- `[provinces]` (U 2026-11-02: provincial reach; form and numbers C)
  Every 50 years a state of 4+ cities names int(0.5 × admin × √cities)
  provincial seats among cities held 100+ years, chosen greedily for
  distance from the capital and other seats × √population. Distance to a
  city = least over capital and seats of 0.3 × (capital to seat) + (seat
  to city). Roads are built out from each seat. A seat that revolts
  takes with it (chance 0.6 each) the cities of its people nearer to it
  than to the capital or another seat.
- `[trait_path]` PATH_TOL (default 1) = 0 leaves tolerance to `tol_path`
  alone.
- `[acc_cross]` (U 2026-11-01; numbers C) Contact acculturation weights
  between lineages of different peoples × 0.1 (with `mission` off, the
  rate also × the foreign-weighted share of contact). Under a ruler of
  another people, each cell's pull toward the ruler's customs × (0.05 +
  0.95 × sigmoid((g − 3.5) / 0.5)), g = generations (25 × the subject
  people's lifespan years) the cell has had the same ruling and subject
  people.

## 17. Disasters

### 17.1 Drought `[not climate]`

Each tick with chance 0.08: centre a random cell; radius U(400, 1500) km;
severity U(0.35, 0.7); drought factor = min(current, 1 − severity × clip(1
− distance / radius, 0, 1)).

### 17.2 Plague

`[epidemic]` (WP6 C, 2026-11-18; U: spread over time and outside states;
numbers **C**) replaces the rule below:
- Onset per city per year: 5e-5 × min(1, city cell people in fe / 3e4) ×
  (1 + min(1, Σ trade ties of its state)); host = the city's people; no
  gap; a city inside an epidemic starts none.
- Each tick an epidemic spreads up to 60 rings over the land grid and
  short sea crossings; each infected neighbour infects with p = 0.9 × d /
  (d + 1) (d = target people per km², majority + minority) × (1 − 0.8 ×
  immunity) × (0.7 if the target's majority is not the host); and with
  chance 0.3 × tie per tick to each tied state's largest unstruck city.
- Struck cells (once per epidemic) lose m × (1 − 0.8 × immunity), m =
  U(0.15, 0.35) per epidemic, × 0.3 for peoples other than the host; city
  cells a further 0.3 × that; immunity ≥ 0.8. Ends when no new cell is
  reached, or after 100 years.
- `[rural_onset]` (WP12 C, 2026-11-22, U; numbers **C**) also
  onset per occupied cell per year: 2e-6 × min(1, people per km² / 5),
  host = the cell's people; a cell inside an epidemic starts none.

Without `[epidemic]`:
- Each year with chance 0.008 × min(1, city population / 3 million) (×
  DT per tick), city population in food-equivalents `[food_units]` or
  heads, at most once per 50 years.
- Origin: a city drawn by population; its state is hit. Spread for 4
  rounds to adjacent states with chance 0.25 + 0.6 × tie (× 0.7 to states
  of another people `[immunity]`).
- Mortality m = U(0.15, 0.35) over all cells of hit states; city cells of
  hit states lose a further 0.3 × m.
- `[immunity]` deaths × (1 − 0.8 × immunity); peoples other than the
  origin city's × 0.3. Immunity set to ≥ 0.8 in hit cells, decaying ×
  e^(−0.012 × 5) per tick; cities over 5 × threshold hold ≥ 0.5.

---

## 18. Records and outputs

- `timeseries.csv` (every tick): population, cells, cities, lineages,
  farming and metallurgy per people; mean violence, tolerance, expansion
  (world and per people); states, cities per state and trait spread per
  people; war, alliance, vassal, revolt, capture and dragon counts;
  structural measures (at-war share, herding share, land condition,
  moisture, dry share, famine movers, river changes, road cells,
  improvements, minority population, mean stress, bronze users); dragon
  measures `[dragons]`; population-weighted mean cohesion, conformity,
  hierarchy and trade (world and per people); mean craft, development and best domestication
  level, guarded techniques, resource kinds held, trade ties > 0.3
  between peoples; salt on settled irrigated land `[salinity]`; war goal
  counts (resource, rule, land, faith), goals met, cities ceded; mean
  churn `[mission]`; share of cities whose minority holds more than 10% of
  the city cell's food-equivalents.
- `price.csv` `[diagnostics]`, every 100 years: Price decomposition of the
  change in each TRAIT and XTRAIT (seafaring omitted `[dispersal]`), per
  people and world, with lineages alive at the last snapshot as units;
  offspring = the population of the lineage and its descendant lineages
  (cells assimilated into them included), in food-equivalents
  `[food_units]` or heads.
  Columns: mean, change, selection (Cov(w, z) / w̄), transmission (E(w
  Δz) / w̄), experience (the part of transmission from 16.2: E(w Δz_exp)
  / w̄, Δz_exp = experience-driven change of the offspring group), w̄,
  lineages, immigrant share.
- `lineages.csv` (with war, trade, hardship and raid memory per
  lineage), `polities.csv` (with each state's peak share of food-
  equivalents from peoples other than its ruler's, as majorities or
  minorities), `cities.csv` (with the minority peoples ever present, the
  peak minority share, years with a minority above 10%, and the number of
  times the majority people changed), `city_sizes.csv` (every 25 years,
  with the minority people and share), `relations.csv` (on frame ticks,
  every pair of neighbouring live states by land or sea: peoples, capital
  landmasses, cities, similarity, each side's enmity and faith motives,
  trade tie, war, alliance, truce, and the ruling lineages' similarity;
  similarity and motives are those the war rule reads, from 2026-11-07),
  `events.txt`, `chronicle.txt`, `traits.txt`, `checks.txt`
  `[diagnostics]`, `dragons.csv` `[dragons]`, `run.json`,
  `final_state.npz` (with minority people, lineage and population per
  cell), `history.mp4`, `frames/`, `final.png`, `legacy.png`,
  `lineages.png`, `population.png`, `violence.png`.
- `wars.csv` (each war: dates, sides, peoples, capital landmasses,
  cities and strengths at the start, goal, goal met, how it ended,
  sieges, captures, recaptures, food-equivalents taken each way, allies
  who helped), `sieges.csv` (each siege: side, city, size, capital,
  strengths, odds, outcome), `revolts.csv` (every revolt), `rulers.csv`
  `[rulers]` (each reign: state, people, years, cities, how the
  succession went).
- City size (records only) = urban population (2026-11-09): the people
  the city cell holds beyond what its own land feeds at the base boost
  (1.5 × (1 + DEV_CITY × development)), in food-equivalents, at most the
  cell's people ([diagnostics.md](diagnostics.md#records-of-2026-11-09)).
  Before: 0.08 × city cell pop + 0.04 × hinterland pop, × the city
  people's food per head `[food_units]` (`size_old`). A city's end cause is the most serious blow in the 50 years before
  it ended (clearance, sack, raid take-over, river lost, plague, drought,
  dragon, raid, siege), else salted land (salt > 0.5), worn land
  (condition < 0.6), dry climate (moisture < −1) or decline.
