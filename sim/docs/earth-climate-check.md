# Earth climate check (WP9 stage C, step C; 2026-11-20)

**Asked by U (2026-11-20):** "Please do the climate check."

**What was run.** `climate_world.py`, unchanged (PARAMS as of 2026-11-20),
on Earth's land and elevation at 0.5°. It is compared with Earth's
observed climate (WorldClim 2.1, 1970-2000), with both put through the
same definitions and the same biome rule.

- Tool: `earth_climate.py` (world root).
- Outputs: `gis/qa/earth_climate.json` and four figures,
  `gis/qa/earth_climate_{biomes,fields,zonal,monsoon}.png`.
- The WorldClim files are in `gis/earth/worldclim/` (191 MB). They are
  not in git; their terms allow non-commercial use but not
  redistribution.

**The model's own rule sets P0.** Global mean precipitation is held at
1.0 m/yr, which puts P0 at 3.77 on Earth (4.07 on the fantasy world;
"2.3" here before 2026-11-21 was the parameter table's stale default).
Nothing was fitted to Earth.

**Earth has no upwelling input.** The fantasy world gets one from its
paleo ocean model; here cold coasts come only from the gyre rule.

**What this tests.** The climate model only. The biome rule is the same
on both sides, so whether the rule matches Earth's vegetation is not
tested here.

## Results

**Overall.**
- Biomes agree on 46% of land by area. The mean recall over the five
  biomes is 0.50.
- Over land, area-weighted:

| Field | Model | Observed | Bias | Correlation |
|---|---|---|---|---|
| Annual mean temperature (°C) | 4.4 | 9.3 | -5.0 | 0.97 |
| Seasonal range (°C) | 18.9 | 19.6 | -0.6 | 0.84 |
| Precipitation (m/yr) | 0.73 | 0.76 | -0.03 | 0.60 |
| PET (m/yr) | 0.79 | 1.10 | -0.31 | 0.85 |
| Aridity with timing (log10) | 0.16 | -0.11 | +0.26 | 0.59 |
| Warm half-year's share of rain | 0.57 | 0.59 | -0.01 | 0.30 |

**Biome areas** (M km², Antarctica included as tundra):

| | Jungle | Desert | Grassland | Temperate forest | Tundra |
|---|---|---|---|---|---|
| Model | 21.8 | 12.4 | 35.2 | 32.5 | 51.8 |
| Observed climate | 24.5 | 30.6 | 32.8 | 41.3 | 24.5 |

**Recall by observed biome:**

| Jungle | Desert | Grassland | Temperate forest | Tundra |
|---|---|---|---|---|
| 0.69 | 0.25 | 0.29 | 0.29 | 1.00 |

Half of the observed temperate forest comes out as tundra, and half of
the observed desert comes out as grassland.

## What the model gets right

- **The equatorial belt.** The Amazon and Congo are jungle (all of the
  area, in both). Equatorial temperature is within 1°C.
- **Where the ITCZ is in each season.** The equatorial rain follows the
  sun into each summer hemisphere: the Sahel and Central America in
  July, the southern Amazon and southern Africa in January.
- **The shape of the temperature field** (correlation 0.97) and the
  seasonal range (0.84), with continentality and the lapse rate.
- **The zonal pattern of rain.** It peaks at the equator, dips in the
  subtropics and rises again toward 45-50°. Total land rain is right
  (0.73 against 0.76 m/yr).
- **Mid-latitude west coasts** (British Columbia, Chile, Norway) get
  orographic rain.

## What it gets wrong (largest first)

1. **Too cold away from the tropics.**
   - About 3-5°C too cold at 30-60° at sea level, and up to 9°C in places
     (the Sahara 16 vs 25°C, Western Europe 0 vs 9°C).
   - That turns the boreal forest (Canada, Siberia, much of Europe) into
     tundra: 52 vs 25M km² of tundra.
   - It also cuts PET by a quarter, which turns hot deserts into
     grassland.
   - Two causes:
     - The temperature profile T_POLE + (T_EQ - T_POLE) cos² falls off too
       early. Earth's tropics are flatter, because heat is carried
       poleward.
     - There is no rule that makes clear, dry land warmer than its
       latitude (the Sahara, Arabia and interior Australia run 5-10°C
       above their zonal profile).
2. **No summer rain over the continents outside the ITCZ.**
   - East Asia's summer monsoon, the eastern United States and the
     Russian summer maximum are missing.
   - At 30-45°, the model rains mostly in winter (warm-half share about
     0.3); Earth's continents get half or more of their rain in summer.
   - The model's winds are zonal bands: it has no flow up the western
     side of the subtropical highs, which brings ocean air onto east
     coasts in summer.
   - Its land rain comes from rain-out along the wind. It has no warm-land
     convection.
3. **The South Asian monsoon fails.**
   - India comes out desert: 0.25 vs 1.1 m/yr, and a July-to-January
     ratio of 1.3 vs 32.
   - The model's ITCZ moves at most 18° over land. It reaches only about
     10-15°N at India's longitudes, while Earth's monsoon trough sits at
     about 25°N, held there by the heating of the Tibetan plateau.
   - Southeast Asia is wetter in July in the model too, but too little
     (a ratio of 10 vs 37).
4. **Subtropical deserts too wet, the rain belt too narrow.**
   - The ITCZ rain is a narrow line (W_ITCZ 5°), heavy where it is, and
     the sinking-air floor (Z_BASE 0.1) still leaves the Sahara 0.31 m/yr
     against 0.02.
   - Earth's tropical rain zone is broader, and its deserts drier.
5. **Continental interiors far from the sea are too dry**
   (Siberia 0.20 vs 0.46 m/yr). Central Asia is the reverse (0.88 vs
   0.21): air from the Atlantic and the Mediterranean, crossing short
   seas, recharges and rains too far inland.
6. **The Atacama and other cold coasts are too wet** (0.22 vs 0.03 m/yr).
   That is expected without the upwelling input, and is not a fault of
   the model as built.

## What this means for the fantasy world

The same physics builds world_v2, so the same biases are likely there,
except the monsoon one, which is about Tibet:
- too much tundra (31.5M km²);
- too few hot deserts (5.5M km²);
- mid-latitude continents with too little summer rain.

Its biome areas are no evidence either way: the drawn map is not an
observed climate.

## Possible fixes (as first proposed; made 2026-11-21, below)

Each would be a physical rule, not a fit to Earth.

- **(a) Temperature.** Replace the cos² profile with a two-term
  energy-balance profile (the next Legendre term, P4), so heat transport
  flattens the tropics. Add a warming of clear-sky dry land (from the
  same sunshine the PET rule computes).
- **(b) Summer rain.**
  - A summer convective term over warm land, proportional to the air's
    water and the land's warmth, so it is limited by the moisture
    already modelled.
  - Or a meridional inflow up the western side of each subtropical high
    in summer (the east-coast monsoon).
- **(c) Height in the ITCZ shift.** Let high, wide plateaus pull the
  summer ITCZ further, like land does.
- **(d) A broader rain belt.** Widen W_ITCZ over land, and/or a drier
  sinking-air floor.

**Two cautions.**
- **Timing.** A change rebuilds world_v2, which changes the baseline and
  everything run on it. It should wait for the sensitivity screen to
  finish (it reads world_v2 at the start of each run).
- **The test gets spent.** A fix motivated by this check makes it, from
  then on, a calibration source for the climate model rather than an
  independent test. A rerun after a fix would show whether the fix
  worked, not that the model is right. The society test on observed
  climate (plan option a) is unaffected.

## Fixes made (U, 2026-11-21)

**Asked by U (2026-11-21):** "Please implement those climate model
changes." All four were made. Forms and values are in
[world-data.md](world-data.md), "Earth-check fixes". In brief:
- **(a)** the P4 term (6 °C at 45°) and dry-land warming (5 °C at no
  evaporation);
- **(b)** summer convection over land warmer than 18-26 °C, and poleward
  summer flow on the subtropical highs' western flanks;
- **(c)** plateaus above 1.5 km add to the ITCZ's pull;
- **(d)** an ITCZ half-width of 8° over land, and drying under the
  Hadley cell's sinking branch.

**The check is now spent for the climate model.** The fixes were
developed against Earth: several forms were changed after seeing Earth's
response (world-data.md lists them). The values were set from physical
reasoning, and none was searched for a best score, but the rerun below
shows whether the fixes worked, not that the model is right. The
fantasy world's drawn map was printed alongside but chose no form; its
agreement rose from 0.35 to 0.44.

**Rerun** (`earth_climate.py --tag fix1`; outputs
`gis/qa/earth_climate_fix1*`; the first check's outputs are kept):

| | Before | After | Observed |
|---|---|---|---|
| Biome agreement (land area) | 0.46 | 0.54 | |
| Mean recall | 0.50 | 0.57 | |
| Land temperature (°C) | 4.4 (r 0.97) | 9.6 (r 0.98) | 9.3 |
| Precipitation (m/yr) | 0.73 (r 0.60) | 0.85 (r 0.58) | 0.76 |
| PET (m/yr) | 0.79 | 0.96 | 1.10 |
| Jungle (M km²) | 21.8 | 27.1 | 24.5 |
| Desert | 12.4 | 18.0 | 30.6 |
| Grassland | 35.2 | 41.3 | 32.8 |
| Temperate forest | 32.5 | 35.8 | 41.3 |
| Tundra | 51.8 | 31.6 | 24.5 |

**By region** (rain m/yr, model before → after, observed):

| Region | Rain | Biome after (observed) |
|---|---|---|
| Sahara | 0.31 → 0.27 (0.02) | desert 71% (100%) |
| Arabia | 0.33 → 0.50 (0.12) | desert 39% (100%) |
| India | 0.25 → 0.49 (1.10) | desert 69% (grassland 87%) |
| Southeast Asia | 0.92 → 2.44 (1.80) | jungle 68% (78%) |
| East China | 0.46 → 0.60 (1.00) | grassland 59% (forest 72%) |
| Eastern US | 0.72 → 0.84 (1.17) | forest 76% (100%) |
| Western Europe | 0.86 → 1.05 (0.86) | forest 95% (99%) |
| Siberia | 0.20 → 0.21 (0.46) | grassland 84% (forest 97%) |
| Central Asia | 0.88 → 0.72 (0.21) | forest 62% (desert 75%) |
| Interior Australia | 0.28 → 0.62 (0.28) | grassland 60% (desert 95%) |
| Congo basin | 1.31 → 1.12 (1.72) | jungle 60% (100%) |

**What the fixes did.**
- **Temperature is fixed.** The bias is +0.3 °C. Western Europe and
  the boreal belt are no longer tundra.
- **Summer rain over the continents is partly there.** The warm
  half-year's share is about right in East China (July/January 3.7
  against 6.2) and the eastern US (1.0 against 1.3). Both are still too
  dry over the year: their spring and autumn rain is missing.
- **Deserts grew but are still too small** (18 against 31M km²).

**What remains wrong.**
- **India's monsoon still fails.** Its July trough reaches 15-17°N, and
  Earth's is near 25°N. The plateau term, a share of land averaged over
  40° of latitude and 10° of longitude, dilutes Tibet. A fix would place
  the ITCZ where near-surface moist static energy peaks, a larger
  change.
- **Interior Australia got wetter** (0.28 → 0.62): summer convection
  rains Pacific air that the western flank no longer dries.
- **The Congo and central Amazon are drier**: in the off-season they lie
  under the sinking branch.
- **Siberia is too dry for forest** and Central Asia too wet: the older
  fault 5 above.
- **The Horn of Africa and the Red Sea coast** come out jungle.

## The ITCZ by moist static energy (U, 2026-11-21: "the bigger fix")

Made as proposed above (world-data.md has the rule and what was tried):
each summer month, the ITCZ moves to where near-surface moist static
energy peaks, and the month is run again. Rerun: `earth_climate.py
--tag fix2`.

**It did not fix India.** India's July ITCZ is at 12-16°N, against
Earth's 25°N. India gets 0.41 m/yr of rain, against 1.10 observed and
0.49 with (a)-(d) alone. On these fields the equatorial ocean's moist
static energy beats northern India's, for two reasons:
- **High land is too cold.** Tibet is 9.5 °C below observed, the
  Colorado Plateau 6 °C and Iran 4 °C: the lapse rate from sea level
  misses a large plateau's own heating. A 5 °C/km near-surface lapse
  rate barely moved India's ITCZ, so it was not adopted.
- **The Arabian Sea is as warm as the open tropics.** On Earth it is
  cooled by upwelling under the monsoon's own jet, which this check has
  no input for.

**What it did fix:**
- Africa's July rain belt sits at 13-14°N (it was 18; Earth's is about
  10-12).
- The Congo is jungle again: 80% of the box, against 60% with (a)-(d)
  alone.
- East Asia's rain belt reaches 18-22°N in July. East China gets 0.66
  m/yr (0.60 before; observed 1.00).

**What it made worse:**
- The Sahel is drier: 0.29 m/yr against 0.43 with (a)-(d) alone, and
  0.52 observed.
- India got 0.41 m/yr, against 0.49 with (a)-(d) alone.

**Overall:** agreement 0.54, mean recall 0.58, desert 19.7M km².

## Plateau warming (U, 2026-11-21: "a small cold highland change")

The mass-elevation effect: a broad plateau heats the air above it, so
its surface is warmer than the free air at the same height (about 4-6
°C on the Tibetan interior). Land gains MASS_K = 1 °C per km of
elevation smoothed over 300 km, never more than its own height. The
value is from that literature range, not fitted here; world-data.md has
the rule. Rerun: `earth_climate.py --tag fix3`.

| Region | Before (°C) | After | Observed |
|---|---|---|---|
| Tibet | −13.7 | −7.8 | −3.7 |
| Colorado Plateau | 3.8 | 5.7 | 9.5 |
| Altiplano | 7.8 | 9.9 | 12.4 |
| Iran plateau | 13.6 | 14.6 | 17.9 |

- **High land is still too cold**, by about half as much as before.
- **India is unchanged:** 0.42 m/yr, against 1.10 observed. Cold
  plateaus were not what held its ITCZ south; the Arabian Sea's missing
  upwelling remains.
- **Land is now 0.9 °C too warm overall** (0.3 before). Lowland at
  30-50° was already 1.3-2.0 °C too warm, which the cold plateaus had
  hidden.
- **Overall:** agreement 0.543 (0.542), mean recall 0.577.
