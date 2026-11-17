# World data

The source is `../gis/world.gpkg`, layer `cells`: a 0.5° grid of 360 x 720
cells, with 66,895 land cells.
- **Build:** the file is produced by `../build_world_gis.py` and
  `../derive_world.py`.
- **Access:** the simulator opens it read-only.
- **Every column** is described in the file's own `field_dictionary` table.

## Columns the simulator uses

| Column | Use |
|---|---|
| `area_km2`, `lon`, `lat`, `row`, `col` | geometry, distances |
| `fic_biome` | 5 biomes: Jungle, Desert, Grassland, Temperate forest, Tundra |
| `fic_elev_km`, `syn_relief_km` | farm penalty, travel cost, terrain defence, colonizability |
| `fic_soil_bar_value` | soil fertility |
| `syn_river`, `syn_discharge_m3s` | irrigation, forage bonus, travel, city locus, river leaps, river trade |
| `syn_runoff_m_yr`, `syn_alluvial_fill`, `fic_dist_coast_km` | climate dryness and discharge; avulsion-prone cells; steppe stand-in and the inland climate pattern |
| `syn_flow_to` | downstream cell, for river leaps, discharge routing and course changes (with `climate`, rivers move during a run). **0-based cell index (fid − 1)**, not a fid. |
| `syn_basin_id` | river basins, for basin trade |
| `syn_lake`, `syn_surface_lith` (alluvium) | farm bonuses |
| `syn_wetness` | terrain defence and colonizability (see below) |
| `syn_reach_productivity` | coastal ocean productivity |
| `syn_dist_copper/tin/iron_km` | ore access for metal stages, city locus |

## Swamp layer (added 2026-10-29, U)

    syn_wetness = alluvial fill x clip(1 − relief/0.3 km) x clip(runoff/0.6 m/yr),
                  or 1 on a lake
    syn_swamp   = syn_wetness ≥ 0.5

- **Extent:** 1,773 swamp cells (2.7% of land), 508 of them lakes. They
  cluster in the jungle belt of the southeastern continent, with patches of
  polar-lowland bog.
- **Code:** the rule lives in `derive_world.swamp_wetness`, with constants
  `SWAMP_*`, so a rebuild reproduces it.
- **This copy:** the columns were written into the current file without a
  rebuild, by adding them to a copy and swapping it in.
- **Preview:** `../gis/previews/syn_swamp.png`.

## Known artifacts

Wetness shows straight-edged strips around 100–120°E, 25–35°S. They are
inherited from the alluvial-fill and relief inputs, not from the swamp rule.
Other layers there have not yet been checked for the same problem.

## Derived in the simulator (`World`)

- **Neighbour graph:** 8 neighbours per cell, with travel cost per edge.
- **Sea links** between coasts up to 160 km apart.
- **Landmasses.**
- **Coastal mask.**
- **Base forage and farm densities** ([rules/population.md](rules/population.md)).
- **City locus** ([rules/cities.md](rules/cities.md)).
- **Terrain defence and colonizability** ([rules/war.md](rules/war.md),
  [rules/colonization.md](rules/colonization.md)).
- **River network** (downstream and upstream lists).
