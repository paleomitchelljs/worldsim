# WP8: climate and land

**Goal.** Continuous temperature and moisture fields in the world build,
derived from process, so that yields, runoff and rivers follow climate
instead of five biome classes; and irrigable land sized by the floodplain,
not the grid cell.

**Evidence** (`BASELINE.md`).
- `world.gpkg` (89 columns) has no temperature and no precipitation.
  `syn_runoff_m_yr` is assumed by biome; discharge, the river network and
  irrigation follow from it.
- The sim reads biome as a class with one farming, foraging and herding
  factor each (`FARM`, `FORAGE`, `HERD`, `IRRIG` in `params.py`), soil
  fertility, elevation and relief. Dryness inside a biome is a stand-in
  from distance to the coast (`W.steppe`, `STEPPE_KM`), which
  `docs/open-questions.md` already lists as a gap.
- 51% of people live within 15° of the equator on 31% of the land; 84%
  within 30° on 56%.
- `geo.derive_rivers`: irrigation is
  `IRRIG_MAX_DENS x sqrt(Q / 3000) x biome factor` on every cell flagged a
  river, times the whole cell's area (about 2,900 km² at the equator).
  River cells are 10.7% of land and hold 42% of people.
- `syn_alluvial_fill` is read only to decide where rivers change course.
  Land on alluvial fill holds 9.3% of people on 9.9% of land.

**Standing instructions from the user** (memory, 2026-10-25): the world is
modern biota on Silurian-baseline geography; derive from first principles
of geomorphology, sedimentology and tectonics rather than copying Earth
patterns; treat the Silurian ocean model's magnitudes as pattern only; do
not flag forests or grasslands as anachronistic.

**I have not read `derive_world.py` or `build_world_gis.py`** (about
80 KB together). The first task of stage A is to read them and correct
this brief where it is wrong about what they do.

Read first: `../derive_world.py`, `../build_world_gis.py`,
`../tectonic_history.py`, `docs/world-data.md`, `wsim/geo.py`
(`World.__init__`, `derive_rivers`, `ecotones`), `wsim/land.py` (`K2`,
`climate`), `../reviewdocs/REALISM_REVIEW.md` ("Stage 1 data quality").

Rules for this package:

- Never overwrite `gis/world.gpkg`. Write `gis/world_v2.gpkg` and add a
  `--world` option to `worldsim.py`. The file is 210 MB and may be a
  Dropbox placeholder; check before reading.
- A new world file moves rivers and therefore cities. The baseline is
  rerun at the end. Do this package once.

## Stage A: climate fields (needs U: D10)

Add to the world build, per land cell (and per sea cell where cheap):

1. **Temperature.** Annual mean and seasonal range from latitude
   (insolation), a lapse rate with `fic_elev_km`, continentality from
   distance to the coast, and an ocean term where the paleo ocean model
   gives a pattern. Then growing-degree days.
2. **Precipitation.** Zonal circulation bands (rising air near the
   equator, sinking in the subtropics, westerlies beyond), moisture
   carried from upwind ocean and rained out with distance, lifted and
   wrung out by relief (windward wet, lee dry). Trace along the prevailing
   wind of each band across the grid.
3. **Water balance.** Potential evaporation from temperature; runoff =
   precipitation less actual evaporation; an aridity index.

Constraint (D10, recommended): **the hand-drawn biome map is the user's
and stays the truth.** The derived climate has free parameters (band
positions and widths, rain-out distance, orographic strength). Fit them so
that a simple climate-to-biome rule reproduces `fic_biome` as well as it
can, and report the agreement by biome and a map of the disagreements.
Where they still disagree the biome class stands, and the climate fields
describe conditions within it. Do not redraw biomes. Large, coherent
disagreements are findings for the user (the drawn map may be asking for
a wind or a current the model lacks).

Outputs: new `syn_temp_c`, `syn_temp_range_c`, `syn_gdd`,
`syn_precip_m_yr`, `syn_pet_m_yr`, `syn_aridity` columns; a QA figure per
field in `gis/qa/`; a section in `docs/world-data.md`.

## Stage B: yields and runoff in the sim (switch `climate_fields`)

1. **Runoff.** Replace the by-biome runoff with the water balance; reroute
   discharge; rederive `syn_river`, basins and lakes with the existing
   thresholds (`Q > 300` m³/s and catchment over 30,000 km²). Report how
   the river network changed: cells gained and lost, and the ten largest
   rivers before and after.
2. **Farming.** Keep the biome factor as the base, and multiply by a
   continuous term from growing-degree days and aridity, normalised so
   that its area-weighted mean within each biome is 1. That keeps each
   biome's total as now and adds the gradient inside it. Say in the docs
   that the normalisation is a choice (C) made to isolate the gradient.
3. **Steppe.** Replace the distance-to-coast stand-in (`W.steppe`,
   `W.dryness`) with the aridity index. `HERD` gets the same treatment as
   farming.
4. **The climate anomaly** (`land.climate`) scales rain-fed yield by
   `W.dryness`; point it at the new aridity.
5. `ecotones` uses distance to the nearest other biome to decide which
   cells shift in a dry or wet spell; with an aridity field, the cells
   near a threshold are known directly. Change it only if it is simple;
   otherwise note it.

Run seed 101 on `world_v2.gpkg`, switch on and off. Measures:
population by latitude band, biome, coast and river; city sites against
the old world (how many moved); the `realism.py` table.

## Stage C: floodplain area (switch `floodplain`)

1. Irrigable area per river cell = river length in the cell x floodplain
   width, capped at the cell's area. Width grows with discharge and with
   alluvial fill (wide on `syn_alluvial_fill` lowland, narrow in relief);
   deltas (river cells at the coast on alluvium) get their own, larger
   width. State the form and its source in the docs (C).
2. Irrigated capacity = `IRRIG_MAX_DENS` x irrigable area, not x cell
   area. `IRRIG_MAX_DENS` is then a density on irrigated land and should
   rise to a value for real irrigated farmland (C: on the order of 100
   people/km², to be justified in the docs), since it no longer spreads
   over the whole cell.
3. `W.irr_share` (used by salinisation and the climate) follows.

Expected: fewer people on small rivers, more on great floodplains and
deltas; salinisation concentrated where irrigation is. Measures: share of
people on river cells; the largest cities' sites; the rank-size slope.

## Done when

- `world_v2.gpkg` builds from the scripts with one command, documented in
  `docs/world-data.md`;
- both switches are tried and written up in `docs/run-log.md`;
- the user has the before/after maps (population density, rivers, city
  sites) and decides whether `world_v2` becomes the default;
- if it does, the baseline is rerun and `BASELINE.md` updated.

## Not in this package

- A finer grid. At 0.5° a cell is 55 km across; sub-cell terms like the
  floodplain are the way to add detail.
- Changing the drawn maps, the soil classes, or the ore sites.
- The data strips at 100-120°E, 25-35°S (`docs/world-data.md`): fix them
  only if stage A's rebuild touches those inputs anyway.
