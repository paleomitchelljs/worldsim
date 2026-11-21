# Earth test: plan and cost (WP9 stage C, 2026-11-20)

**Scoping only.** Nothing has been downloaded or built. D11 (the user's
decision) is whether to do any of it. Everything here is **C**.

## The question

The strongest available check of "where do cities and states form" is
to run the same rules on real geography and compare with history.
Turchin et al. (2013, *PNAS*) did this for the Old World with a far
simpler model.

On the fantasy map, city sites agree 66-79% across seeds (chance about
12%; BASELINE.md). The test also measures how much of that pattern is
geography alone. Earth is the only map where the answer can be checked.

**The test is held out.** No parameter may be calibrated to Earth; that
would spend it (WP9 brief). The model runs with the constants it has on
the day of the test, and the results are reported whatever they are.

## 1. Inputs: an Earth world file

The simulator reads one GeoPackage at 0.5° with the columns of
`wsim/geo.py` (CELL_COLS, CELL_OPT): land, elevation, relief, biome, soil
value, rivers and discharge, flow direction and basins, lakes, alluvial
fill, wetness, runoff, distance to coast, ocean productivity reach,
distances to copper, tin and iron, surface lithology, and the climate
fields (aridity with rain timing, GDD). `make_sites.py` also reads the
`ore_deposits` layer.

**Two ways to get the climate**, which test different things:

- **(a) Observed climate** (Köppen-Geiger, WorldClim or CRU). This tests
  the society model alone on true conditions.
- **(b) This project's `climate_world.py` on Earth's land and elevation.**
  It also tests the climate model: whether it puts the Sahara, the
  monsoon and the boreal forest where they are. That check is cheap and
  worth doing even if the rest of the test is not.

Recommended (C): (b) first, compared against (a) as a climate check
before any society run. Then run the society on (a), so a climate error
does not count against the society model.

| Input | Dataset | Licence (to confirm before download) | Size, roughly |
|---|---|---|---|
| Elevation, land mask, relief | ETOPO 2022 (NOAA NCEI), 60 arc-second | US government, public domain | ~0.5-2 GB |
| Rivers, discharge, flow direction, basins, lakes | HydroSHEDS: HydroRIVERS (modelled mean discharge), HydroBASINS, HydroLAKES | free with attribution (HydroSHEDS licence) | ~1-3 GB |
| Biome (five classes) | Köppen-Geiger present-day 1 km (Beck et al. 2018 / 2023), collapsed by the project's own BIOME_RULE thresholds; or potential natural vegetation (Ramankutty and Foley 1999), not present land use | CC BY 4.0 (Beck); SAGE free use | ~0.1-1 GB |
| Observed climate for (a) | WorldClim 2.1, 10 arc-minute monthly temperature and precipitation | CC BY 4.0 | ~0.5 GB |
| Soils | HWSD v2.0 (FAO/IIASA), mapped to the project's soil value | FAO terms (non-commercial; to confirm) | ~1 GB |
| Ocean productivity | VGPM net primary production climatology (Oregon State) | free for research | ~0.1 GB |
| Surface lithology | GLiM (Hartmann and Moosdorf 2012) | CC BY | ~1 GB |
| Copper, tin, iron | Districts known in antiquity, compiled by hand from the literature (e.g. Cyprus, Timna and Faynan, Anatolia, Iberia, Cornwall, the Erzgebirge, Afghanistan, Yunnan, the Malay tin belt); USGS MRDS as a cross-check | literature; MRDS public domain | MRDS ~0.3 GB |

All of it is resampled to the 720 × 360 grid by a new builder,
`earth_world.py`, beside `derive_world.py`. Its output is
`gis/earth.gpkg` with the same columns, plus `fic_*` placeholders where
the simulator expects a drawn-map column.

## 2. Roster and starts

- **One people: Humans**, with the roster's Human traits and no
  variation between founding groups. Peoples here are fantasy;
  splitting Earth's people by region would be a choice to defend.
- **Dragons off** (`--off dragons`). They have no Earth counterpart.
- **Starts.** Two options, testing different things:
  - **(i) Founding groups at the record's early farming regions**: the
    Fertile Crescent, the Yangtze and Yellow River, Mesoamerica, the
    Andes, New Guinea, the Sahel, eastern North America. Hearths go at
    the known domestication centres. This tests what the rules do after
    farming has begun: where cities and states follow.
  - **(ii) The sim's own rules**: `wander` starts and `make_sites.py`'s
    hearth rule. This also tests whether the rules find the hearths.
  - Recommended: (i) first. (ii) is the harder test and can follow.
- **Time.** Model year 0 is set to the start of farming in the first
  hearth (about 9500 BCE), once, before any run. Results are read to the
  nearest millennium only (WP9 brief). Re-setting the zero after seeing
  results would be calibration.
- **Landmass codes.** `landmasses.py` hard-codes this world's
  continents. Earth needs its own table (Afro-Eurasia, the Americas,
  Australia and New Guinea, islands) for `landmass_volatility`.

## 3. Scoring (all checks, none tuned on)

| Check | Reference | Measure |
|---|---|---|
| City sites | Reba, Reitsma and Seto (2016, *Sci. Data*): city locations and populations from 3700 BCE (SEDAC; CC BY, to confirm) | rank correlation of city density on a 5° grid by millennium; share of the sim's cities within 200 and 500 km of a recorded city of the time, against the same for random land cells |
| Population density | HYDE 3.3 (PBL; licence to confirm), by region and date | rank correlation by region; ratio of totals, read on a log scale only |
| Where large states recur | Seshat polity areas, or Turchin et al. 2013's map of imperial density (CC BY-NC-SA for Seshat) | correlation of the sim's state-occupation frequency per cell with the reference's |
| Timing | first cities, bronze and iron by region | difference in millennia only |

Every score is reported against a null: the same score for the sim's
fantasy-map seeds placed at random, and for a "geography only" null that
puts cities at the largest rivers' best cells.

## 4. What a failure means

- **Cities on every large river regardless of history.** The geography
  null then scores as well as the sim. The sim adds nothing beyond
  rivers; the fantasy map's agreement across seeds is geography too.
- **Cities in the right regions but at the wrong times.** That is a
  rate problem (growth, invention), and the screen says which rates
  matter.
- **States in the wrong places** (for example none in the Near East, or
  huge ones in Amazonia). The land and food model is wrong there:
  jungle capacity, clearing, irrigation.
- **The climate model fails the Earth check** (option b). That is a
  finding about `climate_world.py` and would be worth fixing for the
  fantasy world too, without fitting it to Earth.

## 5. Steps, effort and risks

| Step | Effort (sessions) | Needs |
|---|---|---|
| A. Download and check licences | 0.5 | U consent (downloads, ~5-10 GB disk) |
| B. `earth_world.py`: resample, rivers from HydroSHEDS, soils, lithology, ores | 2-3 | A |
| C. Climate check: `climate_world.py` on Earth against Köppen-Geiger | 1 | B |
| D. Earth roster, hearths, landmass table; one short sanity run | 1 | B |
| E. Batch: 5-6 seeds, 8,000 years | 0.5 (+ about 15-20 min per run) | D |
| F. Scoring tool and nulls | 1-2 | E and the reference data |
| G. Write-up | 0.5 | F |

That is about 6-9 sessions in all. Step C alone (1-2 sessions with A
and part of B) is a self-contained check of the climate model.

**Risks.**
- **Resolution.** At 0.5° (55 km) the Nile valley is one cell wide, and
  the floodplain term carries it. Small hearths (highland New Guinea,
  the Andes) are a few cells.
- **Coasts and sea level.** The mid-Holocene coast was close to today's,
  except the Persian Gulf head and some deltas. Present coasts are
  accepted (C).
- **Present climate and vegetation stand in for the Holocene.** The
  Green Sahara (about 9000-5000 BP) is the largest difference. One
  option is a run with a wetter Sahara; it must be chosen before the
  results.
- **The constants were set on a fantasy world with ten peoples** and
  dragons, and the Earth run uses one people and none. Some mechanisms
  (raids between peoples, cross-people acculturation) fall silent. The
  test is of the remaining rules.
- **Disk.** About 9.6 GB is free. The downloads need space, and the
  reference data should be pruned to what is used.
- **Temptation.** Once Earth results exist, any later change to a
  constant that improves them spends the test. Changes after the test
  should be judged on the fantasy-world patterns (docs/patterns.md)
  first.

## Step C done (2026-11-20)

U chose the climate check alone (option 1). Results are in
[earth-climate-check.md](earth-climate-check.md).
- Biomes agree on 46% of land.
- The model is about 5°C too cold away from the tropics.
- It has no summer rain over continents outside the ITCZ.
- The South Asian monsoon fails.

Possible fixes are listed there, for U.

## Decision for U (D11)

1. Do the climate check alone (A, part of B, C)?
2. Do the whole test (A-G)?
3. Neither for now.

Recommendation (C): option 1 now, since the climate model is still being
refined. Decide on the rest after the sensitivity screen
(docs/sensitivity.md), as the README recommends.

**Answer (U, 2026-11-21):** skip the society test. Work moves to the
society model (phase 2, upgrade/README.md).
