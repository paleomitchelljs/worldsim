# Realism review of the world and history-simulation outputs

Scope: outputs in `world.gpkg`, `qa/`, `previews/` and `sw300_seed101/` (seed 101, 8,000 years, dt = 5, 10 peoples). I did not have the simulation code or the project goals. Everything below is read from the output files, and where I name a mechanism it is a hypothesis. Realism is the only criterion. Balance between peoples is out of scope.

## What the folder is

- **Stage 1, the world (`world.gpkg`, 201 MB).** A 720 x 360 grid at 0.5° (259,200 cells, 66,895 land). It fuses a paleoclimate model (`paleo_*`) with a redrawn fictional map (`fic_*`) and derives hydrology, tectonic setting, lithology and soil (`syn_*`). Source maps are extracted from JPEGs. Registration fit scores run 0.477 to 0.904, and only topography is high (0.904).
- **Stage 2, the history run (`sw300_seed101/`).** 10 peoples, dragons, about 14 heritable traits per lineage. Output is 27,273 lineages, 9,388 polities, 7,323 wars, 1,091 cities and 4,716 rulers, plus a 312-column time series and 80 snapshots in `history.npz`.
- No code, README or environment file is in the folder. `checks.txt` cites `docs/diagnostics.md`, which is absent.

## Largest deficiencies

### 1. City size has a ceiling

Top-200 rank-size slope over time:

| Year | Slope |
|---|---|
| 2000 | -0.78 |
| 3000 | -0.69 |
| 4000 | -0.54 |
| 5000 | -0.30 |
| 7000 | -0.27 |
| 7975 | -0.23 (top-50: -0.17) |

The slope flattens as the world grows. Growth is strongly size-dependent. Mean log growth per 25 years:

| City size | Mean 25-yr log growth |
|---|---|
| under 5,000 | +0.060 |
| 5,000 to 10,000 | +0.014 |
| 10,000 to 20,000 | -0.002 |
| over 20,000 | -0.010 |

Real city systems grow roughly proportionally, which is what produces Zipf. Here large cities shrink on average, so everything is squeezed toward a common ceiling. At 7975 the top five are 50,330, 44,669, 42,031, 40,396 and 39,987.

Supporting evidence:
- `size / cell_pop` sits in a band of 0.108 to 0.249 (5th to 95th percentile). A city is close to a fixed fraction of its own cell's population.
- `trade_city` in `citygaps.csv` ranges only 1.414 to 1.5 (median 1.5). It is saturated and cannot differentiate cities.
- Ports are smaller than non-ports (size ratio 0.173 against 0.209), the wrong sign.
- Urban share is 6.4% at year 7975, which is realistic. The miss is at the top end. The largest city is about 0.027% of world population (50,330 of 188.5M), where real largest cities ran roughly 0.2% to 0.5%.

Hypothesis: cities are capped by their own hinterland and cannot import food or tribute. Rome, Alexandria and Baghdad depended on exactly that. This is unverified without the code.

### 2. No empires

- Largest polity ever: 692 cells, 1.994 Mkm², about 1.0% of the implied land area.
- Real maxima run from about 3% (Rome, Achaemenids) to over 15% (Mongols).
- Top 10 peak sizes span 470 to 692 cells, so the largest is only 1.47 times the tenth.
- State-size slope across the top 300 states with 3+ cities: -0.33.
- `adm_reach` appears in the feature list and is a plausible cause.

### 3. War endings are the wrong shape

- Siege mechanics look sound: taken rate rises from 3.1% at odds under 0.1 to 78.5% at odds above 0.6. Goal-met rate rises with strength ratio from 4.6% to 57.3%.
- Endings are not. 5,327 of 7,312 wars (73%) end with "defender fell". 712 (10%) end in peace and 54 in "repulsed".
- 63% of wars last 0 years (one time step).
- Real pre-modern wars commonly end in tribute, truce, vassalage or stalemate. Total extinction of a state is a minority outcome.

### 4. Technology saturates by about year 3,500

- `metal_` reaches its cap of 3.5 for 7 of 10 peoples, and `agri_` reaches 1.0.
- Population keeps growing, from 76M (year 5000) to 190M.
- Either a continuing productivity term or a stated reason it stops is needed.

### 5. City turnover is very low

- Only 152 of 1,091 cities ever ended (14%). 865 were sacked at least once, with a maximum of 25 sacks, and few died.
- Founding per millennium rises monotonically: 4, 21, 49, 138, 150, 209, 248, 272.
- There is no collapse episode comparable to the Late Bronze Age. I did not check population series for dips, so this is a flag rather than a finding.

## What looks acceptable

- Urban share (6.4%), world density (about 1.3 people per km²) and mean state lifespan (256 years) are plausible.
- Top-20 city overlap across 500 years is 8 to 14 of 20. That persistence is somewhat high but not alarming.
- Lineage counts are lopsided (8,386 Snake folk and 4,313 Elves of 15,089 surviving lineages, against 1,249 Humans). I see no strong a priori reason to expect balance, so I do not count this as a defect.

## Stage 1 data quality

- Layers are extracted from JPEGs by colorbar inversion. Registration fit is 0.477 (soil) to 0.904 (topography).
- The data dictionary admits `fic_river` is an "incomplete extraction" and soil classes are "names unassigned".
- Elevation is quantized to 0.25 km bands, with everything above 2 km set to 2.25.
- Three independent redraws disagree on 6% to 10% of land cells (`ore_vs_soil_agree_pct` 94.39, `ore_vs_biome_agree_pct` 90.39).
- `syn_river` uses "discharge > 300.0 m3/s and area > 30000.0 km2" with runoff "assumed by biome". At 0.5° this is adequate for a simulation and coarse for a local map.

## Outputs to add, in priority order

1. **City food balance per city-year.** Local food, imports and tribute, and which constraint binds. This directly tests the hinterland-cap hypothesis.
2. **Net birth, death and growth rates per people per era.** The intrinsic `r` for Humans is 0.024 per year. Real long-run pre-modern growth was about 0.04% to 0.1%, so the realized rate is the check.
3. **War deaths and population loss per war, plus famine and plague deaths.** `famine_movers` counts movers, not deaths. Without mortality accounting you cannot check demographics.
4. **Trade volumes and routes per year.** `price.csv` is the Price equation, not prices. Only `trade.png` shows trade.
5. **Polity area and population over time for every polity.** `peak_km2` is blank in 8,878 of 9,388 rows.
6. **Reign records for all polities.** At present only a small subset appears to be logged.
7. **Per-cell population by distance to river and coast.** Real pre-modern populations clustered on rivers and coasts, and the distance layers already exist.

## What I could not determine
- Whether the cell cap is real. I read it off the narrow `size / cell_pop` band. That is evidence but not proof, and the code is the only way to settle it.

## Folder hygiene

- `events.txt` (2.4 MB) overlaps `chronicle.txt` (414 KB, described as the major-events subset).
