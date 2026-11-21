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
    insolation. Since 2026-11-21, a second term and dry-land warming are
    added (Earth-check fixes, below).
  - Cooled by up to 4 °C beside upwelling coasts, using the paleo ocean
    model's vertical velocity, scaled so 1.5e-6 m/s counts as full.
  - Lowered 6.5 °C per km of `fic_elev_km`.
  - Lowered by up to 6 °C × sin² lat in continental interiors.
  - Warmed or cooled by ocean currents (below), carried inland.
- **Ocean currents** (U, 2026-11-20). The world file has no surface
  currents, so they come from the wind-driven gyres of each basin:
  - **Basins.** A basin is open sea at least 2,000 km wide along the
    row, bounded by landmasses of 0.5M km² or more; currents pass
    smaller islands.
  - **Subtropical gyres** (about 8–48°): warm water runs poleward on
    the basin's western side, up to +4 °C, fading over 400 km from the
    coast. Cold water runs equatorward on its eastern side, up to
    −3 °C over 800 km.
  - **Subpolar gyres** (about 45–70°): the reverse, a warm drift on the
    eastern side and a cold current on the western.
  - **Inland.** The anomaly is carried inland on the prevailing
    (equinox) wind, fading over 1,000 km.
  - **Effect.** It sets sea temperature, and so the moisture the air
    takes up, and land temperature.
  - **Map:** `../gis/qa/climate_sst_anomaly_c.png`.
- **Continentality** is 1 − exp(−d / 1,000 km). d is the mean of two
  distances: land crossed along the prevailing wind since the last sea
  cell, and plain distance to the coast.
- **Seasons.** The half-amplitude is 1 + 22 |sin lat| × (0.25 + 0.75 ×
  continentality) °C. `syn_temp_range_c` is twice that: warmest minus
  coldest month.
- **Precipitation.** The air's rain potential q is carried along each
  row with the band's prevailing wind, separately for each of the 12
  months (U, 2026-11-20), and the months' rain is averaged:
  - **Wind bands:** trade easterlies equatorward of φ_H (30°), westerlies
    to 60°, polar easterlies beyond.
  - **Seasons.** In each month the sun's side s = sin(month phase): +1
    at the northern summer solstice.
    - **ITCZ.** It sits at s × (5° + 13° × the land fraction within 30°
      of the equator in the summer hemisphere, by longitude, averaged
      over 10°). It reaches 18° over longitudes all land, because the
      summer continent's heat low draws it: the monsoon. Since
      2026-11-21 high plateaus add to the pull (below).
    - **Trades** blow toward the ITCZ, not toward the equator. Between
      the equator and a displaced ITCZ the meridional wind runs toward
      the summer pole, bringing equatorial moisture onto the summer
      continent.
    - **Monsoon westerly** (U, 2026-11-20). Air crossing the equator
      toward a displaced ITCZ is turned east by the Coriolis force. So
      between the equator and the ITCZ the wind is westerly, fading over
      5° below the ITCZ (MONSOON_W 1). Each month a second march walks
      the summer-side trade rows eastward. Its rain replaces the
      easterly march's rain by that weight. How far the ITCZ has moved
      already holds the land fraction and the season.
    - **What it changes.** Within the westerly zone, July rain moves
      −20% to +15% (5th-95th percentile), toward western coasts. Over
      the year, land rain moves at most ±9%, and no biome area changes
      by 0.1M km². Most monsoon rain in this model arrives with the
      meridional flow from the equatorial ocean, which the westerly
      does not change. An isolated march, with no meridional exchange,
      is far more sensitive to the wind's direction (−73% to +324%).
    - **Band edges and the polar front** move 5° poleward in the summer
      hemisphere and 5° equatorward in the winter one.
    - **ITCZ width.** The ITCZ's half-width is 5°, its width at one
      moment. Before the seasons it was 10°, standing for the annual
      mean band.
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
  - **Across band edges.** Rows on either side of a band edge are walked
    in opposite directions, so a second pass takes those neighbours'
    values from the first pass at the same longitude. Before, there was
    no exchange across a band edge.
  - Two laps round the globe; the result is smoothed by one cell.
  - **Seams.** The step in rain between neighbouring rows at ±30° was
    about twice the typical step (0.08–0.09 against 0.04, in log rain)
    with fixed bands. With the monthly band edges it is 0.04–0.05, the
    same as elsewhere. The moving edges do most of this; the
    cross-edge pass alone barely changes it.
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
  - AET by Budyko's curve in Fu's form, ω = 2.6, times the rain-timing
    factor below.
  - **Rain timing** (U, 2026-11-20: "use rain seasonality").
    - A monthly soil-water bucket (S_MAX 0.15 m of plant-available
      water, a typical 100-200 mm) takes each month's rain and loses up
      to that month's PET. Water above S_MAX runs off.
    - Its evaporation with the real monthly rain, over its evaporation
      with the same total spread evenly, is the timing factor. Fu's
      curve stands for rain spread through the year.
    - Rain in a short wet season or in the cold season runs off unused,
      so the factor is below 1. Rain in phase with the warm season is a
      little above 1.
    - Monthly rain comes from the circulation's months (the sun's side
      s, with southern cells taking −s), rescaled to the annual total.
  - Runoff = P − AET; aridity = P / PET (the UNEP index).
  - `syn_aridity_season` is aridity × the timing factor. The biome rule
    reads it, and so do the sim's yields under `climate_fields`.
  - `syn_gdd` is degree-days above 5 °C.

### Earth-check fixes (U, 2026-11-21)

**Asked by U (2026-11-21):** "Please implement those climate model
changes", the fixes (a)-(d) of [earth-climate-check.md](earth-climate-check.md).
Every form and number is C. Off (T_MID 0, T_DRY 0, Z_CONV 0, H_BL very
large, W_ITCZ_LAND = W_ITCZ, L_SUB very large), the fields are identical
to before.

- **(a) Temperature.**
  - **Flatter tropics.** The sea-level profile gains the energy-balance
    model's next Legendre term (P4), written T_MID × 4 sin² cos² lat:
    heat carried poleward by the circulation. T_MID 6 °C is its warming
    at 45°: cos² alone gives 6 °C there, and Earth's zonal-mean sea
    surface is about 12 °C.
  - **Dry land is warmer.** Land gains T_DRY × (1 − AET/PET), with AET
    from Fu's curve: what a surface does not evaporate it sheds as heat.
    T_DRY 5 °C is the warming of a surface that evaporates nothing.
    PET is computed once without it, then again with it.
- **(b) Summer rain over warm land.**
  - **Convection.** In each month, land adds a rain-out factor Z_CONV
    (1, the polar front's) × the month's warmth, from 0 at 18 °C to 1 at
    26 °C. It rains only the water the air already carries.
  - **The subtropical high's western flank.** In summer, over land
    within L_CONT (1,000 km) of a wide ocean basin to the east
    (BASIN_MIN, as for the gyres; narrower seas count as land), the
    trade rows' meridional flow turns poleward: moist air from the
    ocean, not dry air from the continent. East Asia, the eastern United
    States and eastern Australia lie there.
- **(c) Plateaus pull the ITCZ.** The summer ITCZ's land fraction gains,
  within PLAT_LAT (40°) of the equator, each land cell's height above
  H_BL (1.5 km, the summer boundary layer sea-level land heats) over
  H_BL. A plateau heats air that sea-level land does not reach. The land
  fraction may then exceed 1, and the ITCZ 18°.
- **(d) Wider rain belt, drier subtropics.**
  - **Width.** The ITCZ's half-width is W_ITCZ (5°) over open sea and
    W_ITCZ_LAND (8°) at an all-land longitude, by land fraction. The
    monsoon westerly's fade uses the same width.
  - **Sinking air dries.** The Hadley cell's sinking branch replaces the
    moist low air with dry air from aloft, without rain: over land, 1 −
    1/e of the air's water is lost per L_SUB (2,000 km). It acts
    equatorward of the Hadley edge (fading over 5° either side of it),
    less toward the ITCZ's core. It does not act on the summer western
    flanks above. Before this, air under sinking motion kept its water
    and rained it wherever rain-out rose, so deserts were wet.
- **What was tried and changed on the way** (on Earth, before the
  values above were final):
  - Convection alone made every warm land wet: Earth's deserts fell to
    3M km² (observed 31). The sinking-air drying came from this.
  - The drying at first acted wherever the ITCZ and front were weak. It
    turned Siberia and the eastern United States to desert, so it was
    limited to the Hadley band.
  - The western flank first only lifted the sinking; East China barely
    changed (0.48 → 0.52 m/yr), because its trades still blew from the
    continent. Turning the flow poleward gave 0.60.
- **On Earth** (`../earth_climate.py --tag fix1`; outputs
  `../gis/qa/earth_climate_fix1*`):
  - Biome agreement 0.46 → 0.54; mean recall 0.50 → 0.57.
  - Land temperature bias −5.0 → +0.3 °C.
  - Tundra 51.8 → 31.6M km² (observed 24.5); desert 12.4 → 18.0 (30.6).
  - The Sahara's rain is 0.27 m/yr (0.31 before; 0.02 observed).
  - **India still fails**: 0.49 m/yr against 1.10. Its July trough is at
    15-17°N; Earth's is near 25°N.
  - Siberia is grassland, not boreal forest: too dry (0.21 vs 0.46),
    a fault older than these fixes.
  - More in [earth-climate-check.md](earth-climate-check.md).
- **On this world** (`world_v2`): biome areas (M km²) jungle 23.8 →
  28.9, desert 5.5 → 10.2, grassland 33.9 → 38.0, temperate forest
  27.3 → 24.4, tundra 31.5 → 20.5. Agreement with the drawn map rose
  from 0.35 to 0.44, though nothing was fitted to it. Land rain 0.89 →
  1.02 m/yr; P0 3.29.

### ITCZ by moist static energy (U, 2026-11-21: "the bigger fix")

The fix earth-climate-check.md proposed for India's monsoon. Every form
and number is C; ITCZ_ITER 0 gives fields identical to the version
before.

- **The rule.** A monsoon's convergence zone sits at the maximum of
  near-surface moist static energy (Privé and Plumb 2007; Emanuel 1995).
  In each month off the equinox:
  - the land-fraction rule (with plateaus) places a first ITCZ, and the
    month is run;
  - at each longitude, h = T_month + 9.8 °C/km × height + (L/cp) ×
    specific humidity is computed in the summer hemisphere within 40° of
    the equator;
  - the ITCZ moves to its soft maximum (TAU_MSE 2 °C), smoothed over 10°
    of longitude, and the month is run again (ITCZ_ITER 1; a second
    pass changes almost nothing).
- **Humidity.** Over sea, relative humidity 0.8 (the marine boundary
  layer). Over land, the dew point of the PET rule (FAO-56: the night
  minimum, lower in clear dry air), with cloud from the first pass's
  rain; pressure falls with height.
- **Tried first:** humidity from the march's rain potential. Over dry
  land that potential is nearly nil (northern India 0.6 g/kg, against
  real desert air's 5-10), so the ocean always won and the ITCZ stayed
  at 5°N over India.
- **Also tried, not adopted:** a near-surface lapse rate of 5 °C/km
  instead of 6.5. High land is too cold on Earth (Tibet by 9.5 °C,
  the Colorado Plateau by 6), but the change barely moved India's ITCZ
  and warmed land by 1.5 °C overall.
- **Where the July ITCZ sits now** (by longitude): Africa 13-14°N (was
  18), East Asia 18-22°N (was 11-16), India 12-16°N (was 15-17; Earth's
  trough is near 25°N).
- **On Earth** (`earth_climate.py --tag fix2`): agreement 0.54 (0.54 with
  fixes (a)-(d) alone); the Congo is 80% jungle (60%); East China 0.66
  m/yr (0.60); India 0.41 (0.49); the Sahel 0.29 (0.43; observed 0.52).
  **India's monsoon still fails.**
- **On this world:** jungle 28.1, desert 9.5, grassland 37.8, temperate
  forest 26.1, tundra 20.5M km²; agreement with the drawn map 0.44.

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
  - the ITCZ 5° half-width, moving with the months; the polar front at
    50°;
  - rain-out under sinking air (Z_BASE) 0.1, 1/20 of the ITCZ's factor
    (lowered from 0.25 on 2026-11-20, U);
  - rain-out over 2,000 km of land, with half of land rain recycled;
  - T_eq 27 °C, T_pole −15 °C.
- One constant is calibrated: P0, the air's rain potential, set so mean
  precipitation over the whole globe is 1.0 m/yr. That is the planetary
  water cycle, set by the surface energy budget. Result: P0 4.07 m/yr;
  land averages 0.90 m/yr.
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
| Jungle | 26.3 | 23.8 | 0.29 |
| Desert | 12.3 | 5.5 | 0.08 |
| Grassland | 29.0 | 33.9 | 0.37 |
| Temperate forest | 38.1 | 27.3 | 0.20 |
| Tundra | 16.4 | 31.5 | 0.99 |

With rain timing (2026-11-20), the pieces change:

- jungle at the rain belt's seasonal margins becomes savanna
  (grassland), −1.1M km²;
- winter-rain temperate forest at 30–40° becomes grassland, −3.5M km²;
- grassland gains 4.6M km²;
- desert and tundra do not change.

The climate's pattern is zonal:

- a wet equatorial belt;
- monsoon lobes: the summer ITCZ wets the continents to about 20° of
  latitude, savanna and grassland beyond, and savanna wherever the rain
  comes in one season;
- desert only where the monsoon does not reach: the supercontinent's
  interior at 25–35°S, and the northern continents' centres at 20–30°N;
- temperate forest at 35–50°;
- tundra from about 55° poleward on the southern supercontinent.

Median values on land by latitude band (m/yr; RH the annual mean):

| \|lat\| | P | PET | RH | Sunshine | P/PET | with timing | timing factor | warm-half rain share |
|---|---|---|---|---|---|---|---|---|
| 0–10 | 1.95 | 1.25 | 0.78 | 0.42 | 1.55 | 1.35 | 0.88 | 0.79 |
| 10–20 | 1.01 | 1.34 | 0.70 | 0.53 | 0.77 | 0.64 | 0.86 | 0.87 |
| 20–30 | 0.31 | 1.29 | 0.57 | 0.72 | 0.24 | 0.24 | 1.00 | 0.44 |
| 30–40 | 0.59 | 0.75 | 0.60 | 0.63 | 0.74 | 0.60 | 0.78 | 0.30 |
| 40–50 | 0.83 | 0.44 | 0.62 | 0.57 | 1.82 | 1.79 | 1.00 | 0.45 |

(RH and sunshine as before the timing change, which does not touch them.)

Desert area, by version:

| Version | Desert (M km²) | Subtropical land rain (m/yr) |
|---|---|---|
| degree-day PET, Z_BASE 0.25 | 1.2 | |
| Penman–Monteith, Z_BASE 0.25 | 5.0 | 0.31 |
| Penman–Monteith, Z_BASE 0.1 | 22.8 | 0.18 |
| + monthly circulation, currents, cross-edge pass | 5.5 | 0.31 |
| + monsoon westerly, rain timing (current) | 5.5 | 0.31 |

The monsoon brings the subtropics' rain back. Switching the pieces off
one at a time (Z_BASE 0.1, ITCZ half-width still 10°):

| Piece switched off | Desert (M km²) |
|---|---|
| none | 3.8 |
| ITCZ and band movement | 22.8 |
| the ITCZ's extra reach over land | 18.9 |
| band movement only | 6.6 |
| currents | 3.5 |
| cross-edge pass | 3.0 |

The land monsoon does most of it. On Earth the monsoon reaches
15–20° over Africa and 20–25° over South Asia; the great deserts lie
poleward of that and on the western sides of continents.

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
| `syn_aridity_season` | ratio | P / PET × the rain-timing factor; read by the biome rule and the sim |
| `syn_warm_rain_share` | share | the year's rain falling in the warm half-year |
| `syn_runoff_climate_m_yr` | m/yr | P − AET (the same as `syn_runoff_m_yr` in this world) |
| `syn_biome` | class | the biome the rule gives; replaces `fic_biome` in this world |

Sea cells carry the fields too, except `syn_biome`.

QA maps, one per field: `../gis/qa/climate_<field>.png`; relative
humidity and sunshine are drawn there (`climate_rel_humidity.png`,
`climate_sunshine.png`) but not written to the world; so are the timing
factor (`climate_season_factor.png`) and July and January rain
(`climate_precip_jul.png`, `climate_precip_jan.png`). A clean biome map
with rivers and lakes is `../gis/qa/biome_map.png`
(`docs/upgrade/tools/biome_map.py`).

### Rivers on `world_v2` (WP8 stage B)

`syn_runoff_m_yr` on `world_v2` is the climate's runoff, P − AET, and
rain on lakes is the climate's precipitation. Discharge, rivers, basins,
lakes, alluvial fill, wetness, soils and bedrock are then derived as
before, with the same thresholds, from `syn_biome`.

The result (physical refit, lake sizing, Penman–Monteith PET, monthly
circulation, rain timing):

- **River cells:** 6,243 → 4,447 (10.7% → 9.0% of land).
- **The largest river** reaches the sea at 129°E, 58°S (126,000 m³/s).
  It drains 12.3M km² of the southern supercontinent's temperate belt,
  from 30°S to 60°S. Next is the river at 80°W, 14°N (125,000 m³/s),
  which was the largest before the rain timing. The old world's largest
  (152,000 m³/s, mouth at 10°E, 72°S) is gone: that land is tundra now.
- **Lakes and closed basins.**
  - A closed basin's lake covers only as much area as evaporation less
    rain on it can balance the basin's inflow. It fills from the lowest
    cells, and the rest of the basin floor is alluvial fill (dry
    sediment) (`derive_world.drainage`, C; U 2026-11-19).
  - Lake cells: 931, 1.4% of land (1,000 before the rain timing).
    Before sizing it was 2,249; on the old world it is 508. Endorheic
    cells: 7,090.
  - `world.gpkg` on disk predates the lake sizing. A rebuild of it would
    now size its closed-basin lakes too.

Earlier versions, for the record:
[run-log.md](run-log.md), "2026-11-19 WP8".

### Known limits

- **Monsoon winds.** The westerly is a second march blended in by
  weight, not a wind field: within a month each row still walks one
  way in each march.
- **Rain timing** has no lag: the months' rain follows the sun's
  position exactly, and spring and autumn are alike.
- **Currents** are schematic gyres from basin geometry, not an ocean
  model. There is no circumpolar current beyond what open rows imply,
  and no sea ice.
- The straight-edged strips at 100–120°E (above) show in temperature
  and precipitation too, through elevation.

### Plateau warming (U, 2026-11-21)

- **The rule.** T += MASS_K × min(z_broad, z), with z_broad the land
  elevation (sea 0) smoothed by a gaussian of L_MASS = 300 km, and
  MASS_K = 1 °C/km (C; the mass-elevation effect of the Tibetan
  interior is about 4-6 °C). The cap at the cell's own height keeps a
  lowland beside a plateau from being raised. MASS_K 0 gives the fields
  before.
- **On Earth** (`--tag fix3`): Tibet −7.8 °C (−13.7 before; observed
  −3.7), the Colorado Plateau 5.7 (3.8; 9.5); India's rain unchanged at
  0.42 m/yr; agreement 0.543.
- **On this world:** land 0.7 °C warmer; jungle 29.4, desert 9.5,
  grassland 37.9, temperate forest 26.0, tundra 19.2M km²; agreement
  with the drawn map 0.44.
