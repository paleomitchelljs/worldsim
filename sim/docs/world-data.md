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
`../gis/previews_v2/`). It refits the climate each time (about 40 s).
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
  - PET = 1.75e-4 m per degree-day above 0 °C (the year taken as a
    sinusoid).
  - AET by Budyko's curve in Fu's form, ω = 2.6.
  - Runoff = P − AET; aridity = P / PET (the UNEP index).
  - `syn_gdd` is degree-days above 5 °C.

### Fit against the drawn biomes (D10: U, 2026-11-19)

The climate-to-biome rule is fixed at standard thresholds:

- tundra if the warmest month is under 10 °C (Köppen E);
- otherwise desert if P/PET < 0.2 (UNEP arid);
- otherwise grassland if P/PET < 0.65 (UNEP semi-arid and dry subhumid);
- otherwise jungle if the coldest month is 18 °C or more (Köppen A);
- otherwise temperate forest.

Twelve parameters were fitted to maximise the mean, over drawn biomes, of
the share of each biome's area the rule reproduces: 300 random draws
inside bounds, then four rounds of coordinate steps. Result
(`../gis/qa/climate_fit.json`):

| Drawn biome | Area (M km²) | Climate agrees | Climate says instead (largest) |
|---|---|---|---|
| Jungle | 26.3 | 0.25 | tundra 0.25, desert 0.23, temperate forest 0.22 |
| Desert | 12.3 | 0.89 | grassland 0.09 |
| Grassland | 29.0 | 0.26 | desert 0.50, temperate forest 0.18 |
| Temperate forest | 38.1 | 0.41 | jungle 0.18, grassland 0.16, desert 0.14 |
| Tundra | 16.4 | 0.99 | - |

Mean agreement is 0.56; by area, 0.47 of land agrees.

Fitted values: T_eq 26.7 °C, T_pole −10.9 °C, φ_H 35°, polar front 51°,
P0 6.0 m/yr, L_rain 630 km, K_oro 0.48, RECYCLE 0.18, V_mer 0.6.
Five parameters ended at a bound:

- ITCZ width 5° and strength 0.5, both at the minimum;
- P0 and V_mer at the maximum;
- K_eddy 0, at the minimum.

The fit wants no equatorial rain belt, and wet coasts with dry
interiors.

**The disagreements are large and coherent. They are findings for U, not
noise** (map: `../gis/qa/climate_biome_disagreement.png`).

- **The southern supercontinent's jungle belt.** The drawn map has 6.4M km²
  of jungle at 60–70°S and 1.4M km² at 70–80°S, along the edge of the
  polar tundra. Most of the supercontinent's jungle and temperate forest
  lies at 40–70°S, with desert at 20–40°S north of it. That is the
  latitude order of a climate centred near 35°S. No circulation with a
  cold south pole gives it: the rule calls that belt tundra or desert.
  The drawn map would need a warm, wet source to the south (a warm
  current or a warm polar sea), and the tundra beside it says there is
  none. Alternatively, "jungle" there means a cool temperate rainforest.
- **Temperate forest in the tropics.** 16.6M km² of temperate forest lies
  at 0–30°N, where the rule gives jungle or grassland. The drawn jungle
  there is coastal and patchy.
- **Grassland as desert.** Half the drawn grassland is desert to the
  rule. These are mostly continental interiors far from the windward
  ocean, which the rain-out march dries more than the drawn map does.

**Decision (D10, U, 2026-11-19).** The southern belt is "probably an old
error" in the drawn map. The climate's biome replaces the drawn one
wherever they disagree, in `world_v2` only: column `syn_biome`, which
the simulator and the rest of the build read in place of `fic_biome`.
`fic_biome` keeps the drawn map, and the fit above is still made against
it.

| Biome | Drawn (M km²) | `world_v2` (M km²) |
|---|---|---|
| Jungle | 26.3 | 15.1 |
| Desert | 12.3 | 36.7 |
| Grassland | 29.0 | 16.4 |
| Temperate forest | 38.1 | 26.8 |
| Tundra | 16.4 | 27.0 |

Desert triples: the march dries continental interiors more than the
drawn map did. The fitted parameters were chosen to match the drawn map,
errors included.

### Columns added in `world_v2.gpkg`

| Column | Units | What |
|---|---|---|
| `syn_temp_c` | °C | annual mean temperature |
| `syn_temp_range_c` | °C | warmest minus coldest month |
| `syn_gdd` | °C·days | growing-degree days above 5 °C |
| `syn_precip_m_yr` | m/yr | precipitation |
| `syn_pet_m_yr` | m/yr | potential evaporation |
| `syn_aet_m_yr` | m/yr | actual evaporation |
| `syn_aridity` | ratio | P / PET |
| `syn_runoff_climate_m_yr` | m/yr | P − AET (the same as `syn_runoff_m_yr` in this world) |
| `syn_biome` | class | the biome the rule gives; replaces `fic_biome` in this world |

Sea cells carry the fields too, except `syn_biome`.

QA maps, one per field: `../gis/qa/climate_<field>.png`.

### Rivers on `world_v2` (WP8 stage B)

`syn_runoff_m_yr` on `world_v2` is the climate's runoff, P − AET, and
rain on lakes is the climate's precipitation. Discharge, rivers, basins,
lakes, alluvial fill, wetness, soils and bedrock are then derived as
before, with the same thresholds, from `syn_biome`.

The result is fewer, more coastal rivers:

- river cells fall from 6,243 to 2,779 (10.7% → 5.4% of land);
- endorheic cells rise from 1,024 to 8,443, and lake cells from 508 to
  2,249;
- the old largest river (152,000 m³/s, mouth at 10°E, 72°S) is gone. The
  largest now reaches the sea at 114°E on the equator (87,000 m³/s).

(Before D10 was decided, a version that kept each drawn biome's mean
runoff gave 3,332 river cells; [run-log.md](run-log.md), "2026-11-19 WP8
stages B and C".)

### Known limits

- There are no seasons in the circulation: no monsoon, and no migrating
  ITCZ.
- Moisture moves along rows. Meridional transport is a share per step,
  and only between rows walked the same way, so precipitation shows a
  seam at the band edge (35°).
- The straight-edged strips at 100–120°E (above) show in temperature
  and precipitation too, through elevation.
