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

## Climate fields and `world_v2.gpkg` (WP8, 2026-11-19)

`world_v2.gpkg` is `world.gpkg` with climate fields added, the biome the
climate implies in place of the drawn one, and rivers routed on the
climate's runoff. It is the simulator's default world since 2026-11-19
(U); `world.gpkg` itself is never changed and is `--world v1`. Build both
from the source maps:

    ~/.venvs/worldsim/bin/python ../build_world_gis.py      # world.gpkg
    ~/.venvs/worldsim/bin/python ../derive_world.py --v2     # world_v2.gpkg

The second command copies `world.gpkg`, runs every derivation again with
`climate=True`, and writes `../gis/world_v2.gpkg` (previews in
`../gis/previews_v2/`). It recalibrates P0 each time (a few seconds).
`run.json` records the world file a run used as `world`.

**Rebuild check (2026-11-19).** `world.gpkg` was rebuilt from the scripts on
a new machine. Every preview PNG and `qa/registration.json` came out
byte-identical to the committed copies, with 66,895 land cells.

### The model (`../climate_world.py`; every form and number C)

- **Temperature.**
  - Sea-level annual mean T_pole + (T_eq − T_pole) cos² lat. This is the
    leading Legendre term of an energy-balance model under annual-mean
    insolation.
  - Cooled by up to 4 °C beside upwelling coasts, using the paleo ocean
    model's vertical velocity, scaled so 1.5e-6 m/s counts as full.
  - Lowered 6.5 °C per km of `fic_elev_km`.
  - Lowered by up to 6 °C × sin² lat in continental interiors.
- **Continentality** is 1 − exp(−d / 1,000 km). d is the mean of two
  distances: land crossed along the prevailing wind since the last sea
  cell, and plain distance to the coast.
- **Seasons.** The half-amplitude is 1 + 22 |sin lat| × (0.25 + 0.75 ×
  continentality) °C. `syn_temp_range_c` is twice that: warmest minus
  coldest month.
- **Precipitation.** The air's rain potential q is carried along each
  row with the band's prevailing wind:
  - Wind bands: trade easterlies equatorward of φ_H, westerlies to 60°,
    polar easterlies beyond.
  - Over sea, q relaxes toward saturation over 800 km. Saturation is
    P0 × exp(0.07 (T_sea − 25)) (Clausius-Clapeyron).
  - Over land, each cell rains out a share z × oro × dx / L_rain of q.
    z is the band's rain-out factor: a Gaussian at the ITCZ, one at the
    polar front, and a floor under sinking air. oro is
    (1 + K_oro × upwind rise in m/km) × exp(−0.1 × descent in m/km).
  - The share RECYCLE of the rain goes back into the air.
  - At each step the air also takes a share V_mer from the row upwind
    in latitude (the wind's meridional part) and mixes K_eddy with both
    neighbouring rows.
  - Two laps round the globe; the result is smoothed by one cell.
- **Water balance.**
  - PET by FAO-56 Penman–Monteith (U, 2026-11-20: "bring in sunshine &
    humidity"), summed over 12 months of temperature T + A sin(month):
    - radiation: that month's top-of-atmosphere insolation (FAO-56
      eq. 21), with summer in phase with the warm months;
    - sunshine fraction 0.85 under clear air, falling toward 0.35 as
      rain rises (1 − e^(−P / 1 m/yr) of the way); Ångström
      Rs = (0.25 + 0.5 n/N) Ra; albedo 0.23; FAO-56 net longwave;
    - humidity: the dew point is the night minimum (month mean less half
      the day-night range, 6 °C under cloud to 16 °C under clear sky),
      less up to 2.5 °C in clear dry air (FAO-56 Annex 6);
    - wind 2 m/s; months below 0 °C add nothing.
    - A version that also capped humidity by the moisture the wind
      carries made the raining equator dry (RH 0.56), because the march
      counts rained-out air as gone; it was dropped.
  - AET by Budyko's curve in Fu's form, ω = 2.6.
  - Runoff = P − AET; aridity = P / PET (the UNEP index).
  - `syn_gdd` is degree-days above 5 °C.

### Parameters and biomes (refit on physical grounds, U 2026-11-19)

The climate-to-biome rule is fixed at standard thresholds:

- tundra if the warmest month is under 10 °C (Köppen E);
- otherwise desert if P/PET < 0.2 (UNEP arid);
- otherwise grassland if P/PET < 0.65 (UNEP semi-arid and dry subhumid);
- otherwise jungle if the coldest month is 18 °C or more (Köppen A);
- otherwise temperate forest.

**The parameters are not fitted to the drawn map.**

- They take physically motivated values (`climate_world.PARAMS`, C):
  - band edges at 30° and 60° (the Hadley and Ferrel cells);
  - the ITCZ 10° wide, the polar front at 50°;
  - rain-out over 2,000 km of land, with half of land rain recycled;
  - T_eq 27 °C, T_pole −15 °C.
- One constant is calibrated: P0, the air's rain potential, set so mean
  precipitation over the whole globe is 1.0 m/yr. That is the planetary
  water cycle, set by the surface energy budget. Result: P0 2.29 m/yr;
  land averages 0.81 m/yr.
- **History.** A first version fitted twelve parameters to the drawn map.
  Mean agreement was 0.56, but the fit learnt the map's errors (no
  equatorial rain belt, very dry interiors; P0, V_mer, the ITCZ at
  their bounds). U (2026-11-19) asked for a refit on physical grounds.

**The drawn map was wrong in large coherent regions** (D10). The first
fit found:

- jungle and temperate forest at 40–75°S beside the polar tundra
  (6.4M km² of jungle at 60–70°S), with desert at 20–40°S, the
  latitude order of a climate centred near 35°S;
- 16.6M km² of temperate forest at 0–30°N.

**Decision (D10, U, 2026-11-19).** The southern belt is "probably an old
error". The climate's biome replaces the drawn one everywhere, in
`world_v2` only: column `syn_biome`, which the simulator and the rest of
the build read in place of `fic_biome`. `fic_biome` keeps the drawn map.

Biome areas (`../gis/qa/climate_fit.json`):

| Biome | Drawn (M km²) | `world_v2` (M km²) | Share of drawn area the climate agrees with |
|---|---|---|---|
| Jungle | 26.3 | 20.4 | 0.27 |
| Desert | 12.3 | 5.0 | 0.15 |
| Grassland | 29.0 | 43.1 | 0.48 |
| Temperate forest | 38.1 | 22.0 | 0.18 |
| Tundra | 16.4 | 31.5 | 0.99 |

The climate's pattern is zonal:

- a wet equatorial belt;
- semi-arid subtropics, with desert in their interiors (20–35°S on the
  supercontinent, the northern continents' centres);
- temperate forest at 35–50°;
- tundra from about 55° poleward on the southern supercontinent.

Median values on land by latitude band (m/yr; RH the annual mean):

| \|lat\| | P | PET | RH | Sunshine | P/PET |
|---|---|---|---|---|---|
| 0–10 | 2.07 | 1.24 | 0.78 | 0.41 | 1.73 |
| 10–20 | 0.66 | 1.41 | 0.65 | 0.61 | 0.46 |
| 20–30 | 0.31 | 1.27 | 0.57 | 0.72 | 0.25 |
| 30–40 | 0.42 | 0.78 | 0.57 | 0.68 | 0.50 |
| 40–50 | 0.55 | 0.48 | 0.57 | 0.64 | 1.07 |

Subtropical PET (1.27 m/yr) is now near Earth's range but below its
deserts' 1.5–2. Subtropical rain is 0.31 m/yr against well under 0.1 in
Earth's great deserts: the floor on rain-out under sinking air (Z_BASE
0.25) keeps the subtropics semi-arid. With the degree-day PET used
before (2026-11-19), desert was 1.2M km².

### Columns added in `world_v2.gpkg`

| Column | Units | What |
|---|---|---|
| `syn_temp_c` | °C | annual mean temperature |
| `syn_temp_range_c` | °C | warmest minus coldest month |
| `syn_gdd` | °C·days | growing-degree days above 5 °C |
| `syn_precip_m_yr` | m/yr | precipitation |
| `syn_pet_m_yr` | m/yr | potential evaporation (Penman–Monteith) |
| `syn_aet_m_yr` | m/yr | actual evaporation |
| `syn_aridity` | ratio | P / PET |
| `syn_runoff_climate_m_yr` | m/yr | P − AET (the same as `syn_runoff_m_yr` in this world) |
| `syn_biome` | class | the biome the rule gives; replaces `fic_biome` in this world |

Sea cells carry the fields too, except `syn_biome`.

QA maps, one per field: `../gis/qa/climate_<field>.png`; relative
humidity and sunshine are drawn there (`climate_rel_humidity.png`,
`climate_sunshine.png`) but not written to the world.

### Rivers on `world_v2` (WP8 stage B)

`syn_runoff_m_yr` on `world_v2` is the climate's runoff, P − AET, and
rain on lakes is the climate's precipitation. Discharge, rivers, basins,
lakes, alluvial fill, wetness, soils and bedrock are then derived as
before, with the same thresholds, from `syn_biome`.

The result (physical refit, lake sizing, Penman–Monteith PET):

- **River cells:** 6,243 → 3,298 (10.7% → 6.8% of land).
- **The largest river** reaches the sea at 88°W, 15°N
  (146,000 m³/s). The old world's largest (152,000 m³/s, mouth at 10°E,
  72°S) is gone: that land is tundra now.
- **Lakes and closed basins.**
  - A closed basin's lake covers only as much area as evaporation less
    rain on it can balance the basin's inflow. It fills from the lowest
    cells, and the rest of the basin floor is alluvial fill (dry
    sediment) (`derive_world.drainage`, C; U 2026-11-19).
  - Lake cells: 852, 1.3% of land. Before sizing it was 2,249; on the
    old world it is 508. Endorheic cells: 7,572.
  - `world.gpkg` on disk predates the lake sizing. A rebuild of it would
    now size its closed-basin lakes too.

Earlier versions, for the record:
[run-log.md](run-log.md), "2026-11-19 WP8".

### Known limits

- There are no seasons in the circulation: no monsoon, and no migrating
  ITCZ.
- Moisture moves along rows. Meridional transport is a share per step,
  and only between rows walked the same way, so precipitation shows a
  seam at the band edges (30° and 60°).
- The straight-edged strips at 100–120°E (above) show in temperature
  and precipitation too, through elevation.
