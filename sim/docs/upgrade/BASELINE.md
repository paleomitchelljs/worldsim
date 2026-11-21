# Baseline measurements (2026-11-16)

The numbers the upgrade is judged against, and how each was computed.
They are checks, not targets (`GUIDE.md`).

**Limits of this baseline.** Most figures come from one run,
`runs/al_seed103` (8,000 years, seed 103, `food_flow` + `war_terms` +
`urban_city` + the three capital levers). Cross-seed figures use six runs
of mixed settings. WP2 stage B turns these into functions and WP1 stage F
reruns them on a clean six-seed batch; treat the values below as
provisional until then.

**Update, 2026-11-17 (WP1 stage F).** The baseline for later packages is
now `wp1f_fullclim_seed101`-`104` and `106`, in `sim/runs/`. They use named
random streams (668ac79) and the full-grid climate field, which is the
default again since 96d0de8. The `realism.py` table and the comparison
with the old `ub_` batch and with `wp1f_base_` (half-resolution field) are
in `docs/run-log.md`, "2026-11-17 WP1 stage F". Median end population is
147M (108-178M), against 137M (124-160M) for `ub_`. Saved states at years
3,000 and 5,000 of seeds 101 and 103 (`runs/wp1f_s10{1,3}_y{3000,5000}.pkl`)
are from the same settings (runs `wp1g_states_seed101`, `103`).

**Update, 2026-11-18 (WP6 stage B).** The baseline is now
`wp6b_seed101`-`104` and `106` (last section), after WP4, WP5 and the
adopted growth settings.

**Update, 2026-11-20 (WP8, fifth).** The baseline is now
`wp8k_seed101`-`104` and `106` (last section): cleared land as terrain
and foragers' burning.

**Update, 2026-11-21 (WP8, seventh).** The baseline was
`wp8j_seed101`-`104` and `106` (last section): land clearing.

**Update, 2026-11-20 (WP8, sixth).** The baseline was
`wp8i_seed101`-`104` and `106` (last section): the monsoon westerly and
rain timing.

**Update, 2026-11-20 (WP8, fifth).** The baseline was
`wp8h_seed101`-`104` and `106` (last section): monthly circulation (ITCZ
migration, land monsoon), gyre ocean currents, and exchange across band
edges.

**Update, 2026-11-20 (WP8, fourth).** The baseline was
`wp8g_seed101`-`104` and `106`: the rain-out floor under
sinking air lowered from 0.25 to 0.1.

**Update, 2026-11-20 (WP8, third).** The baseline was
`wp8f_seed101`-`104` and `106`: potential evaporation by
Penman-Monteith, with sunshine and humidity.

**Update, 2026-11-19 (WP8, second).** The baseline was
`wp8e_seed101`-`104` and `106`: the climate refit on
physical grounds, closed-basin lakes sized, and `sites_v3.json`.

**Update, 2026-11-19 (WP8).** The baseline was `wp8d_seed101`-`104`
and `106`: the default world is `world_v2.gpkg`, with
climate fields and the climate's biomes (D10). `floodplain` and
`climate_fields` are on.

**Update, 2026-11-17 (WP2 stage B).** Every measure below is now a
function in `wsim/metrics.py`; each run writes them to `metrics.json`,
and `realism.py` prints them (`--group`, `--cross`). Run on `al_seed103`,
the functions reproduce every figure in the sections below except three,
corrected in place and marked *corrected*: land in a state (32% was the
share of cells; by area it is 51%), the herding peak, and the siege odds,
now split by side. The last section gives the same measures on the new
baseline batch. `docs/upgrade/tools/analyze_run.py` is kept only as the
record of how the first figures were made.

## War and states (`al_seed103`)

| Measure | Value | How |
|---|---|---|
| Wars | 7,875 | rows of `wars.csv` |
| Wars ending inside one tick | 69% | `years == 0` |
| Wars ending within 5 years | 84% | `years <= 5` |
| Wars with 0-1 sieges | 57% | `sieges <= 1` |
| Peer wars | 296 (3.8%) | `cities_att >= 5` and `cities_dfn >= 5` |
| Sieges, share taken | 20,514; 21.5% | `sieges.csv`, `taken` |
| Median siege win probability at launch | 0.064 pooled; attacker's sieges 0.076 (n 19,087, 54% under 0.1); counter-offensives 0.0066 (n 1,427, 87% under 0.1) | `sieges.csv`, `odds`, by `side` (*corrected*: the pooled figure hid the split) |
| States (2+ cities) at war, by millennium | 0.06-0.12 after year 3000 | `timeseries.csv`, `at_war_share` |
| Wars per millennium | 14, 59, 235, 434, 927, 2,619, 3,587 | `wars.csv`, `start // 1000`, from year 1000 |
| Polities | 5,872 | rows of `polities.csv` |
| Never above one city | 66%, median life 35 yr | `peak_cities <= 1` |
| Ended states with 3+ cities | 910; mean 300 yr, median 160 | `polities.csv` |
| ... lasting over 1,000 yr | 54; longest 4,720 yr | same |
| Largest state at the end | 1,909 cells in 23 pieces; largest piece 36% | `final_state.npz`, 8-connected components of `polity` |
| Top-10 states, pieces | 23, 26, 8, 20, 8, 15, 22, 1, 7, 13 | same |
| Top-10 states, groups once pieces within sailing range are joined | 2, 2, 2, 1, 1, 1, 1, 1, 3, 2; largest group 90-100% | range `SAIL_D0 + SAIL_D1 x sail^1.5` of the state's lineage: 1,900-2,400 km (added 2026-11-17) |
| Population in a state / land in a state | 89% / 51% of land area (32% of land cells) | `final_state.npz` (*corrected*: 32% was cells) |

## Food and deaths (`al_seed103`, end of run)

| Measure | Value | How |
|---|---|---|
| Food brought into cities: trade / rent / provincial / capital | 0.275 / 0.155 / 0.207 / 0.363 | `cityfood.csv`, last year, sums of `from_*` |
| Trade food created per tick | 5.1M food-equivalents | `timeseries.csv`, `n_ff_trade` |
| Deaths by cause | dragon 0.54, feud 0.20, raid 0.10, hunger 0.07, plague 0.05, war levies 0.02, siege 0.01, sack 0.01 | `deaths.csv`, summed over the run |

The realism batch (`fw_`, run-log 2026-11-09) put trade at 0.36-0.41 of
city food.

## Population and land (`al_seed103`)

| Measure | Value |
|---|---|
| World population at years 1000 ... 8000 (M) | 15, 27, 32, 44, 59, 82, 136, 155 |
| Growth, %/yr by millennium from 2000 | 0.056, 0.018, 0.030, 0.031, 0.032, 0.050, 0.013 |
| Log population, sd around its 200-yr mean after 3000 | 0.023 |
| Largest 100-yr fall after 3000 (log) | -0.26 |
| Herding share of population, peak | 0.28 at year 2430 (*corrected*: was read as 0.25 near 3000) |
| Pop share: coastal / river / coast or river | 0.22 / 0.42 / 0.61 on 0.075 / 0.107 / 0.179 of land |
| Pop share on alluvial fill | 0.093 on 0.099 of land |
| Pop share within 15° / 30° of the equator | 0.51 / 0.84 on 0.31 / 0.56 of land |
| Density by biome (per km²) | jungle 1.42, desert 0.16, grassland 1.20, temperate forest 2.12, tundra 0.04 |
| Cell density, p50 / p90 / p99 / max | 0.3 / 2.3 / 12.8 / 106 |

From the code: `grow` multiplies r by up to 2.5 on thin land
(`front = 1 + 1.5 x clip(1 - 2p/K)`), so Humans (r 0.024) grow at up to
4-6% a year on a frontier.

## Peoples (`al_seed103`, `history.npz`)

Share of cells occupied at both ends of a 500-year window whose people
changed:

| Window | Changed | Occupied cells inside a state at window end |
|---|---|---|
| 1000-3000 | 0.008-0.009 | 0.003-0.03 |
| 3000-5000 | 0.017-0.020 | 0.05-0.15 |
| 5000-8000 | 0.028-0.050 | 0.20-0.40 |

Minorities are 1.1% of heads at the end.

## Contingency across seeds (final maps)

Pairs among `tx_seed101/103/104`, `al_seed101/103`, `ub_seed101`:

| Measure | Different seeds | Same seed, different levers | Chance |
|---|---|---|---|
| Cells held by the same people | 0.64-0.77 | 0.85-0.90 | 0.20-0.25 |
| City sites (ever) within one cell of the other run's | 0.66-0.79 | 0.77-0.81 | 0.11-0.13 |
| Correlation of log(1 + cell population) | 0.90-0.95 | 0.95-0.98 | - |

The roster (`peoples_regional`) fixes each people's homeland, which
explains part of the first row by design.

## Speed (profile of 2026-11-16)

`tools/profile_phases.py` on seed 101, 6,000 years, sweep settings. The
machine was heavily loaded by other jobs, so only shares are reliable.
Full output: `baseline/phases_2026-11-16.txt`. `Kf` is nested inside the
other phases.

| Phase | Share of step time |
|---|---|
| `migrate` | 33% |
| `Kf` (about 209 calls per tick) | 25% |
| `raids` | 18% |
| `prepare_capacity` (mostly `climate`) | 10% |
| `technology` | 8% |
| `grow` | 5% |
| `wars_step` | 4.5%, rising to 12% in the last millennium |
| `polity_stats` | 3.5% |

Step time per millennium is roughly flat from year 0. Inside the last 500
years: `K2` 16% of time, `voyages` 15%, `raids` 14%, `power_dist` 9%
(192,441 calls in 100 ticks), `dev` 6% (255,213 calls), `eff` 1.68M calls.
`render` is 0.13 s per frame; `write_outputs` 2 s; `World()` 13-15 s.

Reproduce:

    ~/.venvs/worldsim/bin/python docs/upgrade/tools/profile_phases.py \
        "$PWD" 6000 <output folder outside Dropbox>

## Model size

400 constants in `wsim/params.py` (362 numeric scalars), 27 switches in
`FEATURES`.

## The baseline batch of WP6 B (`wp6b_seed101`-`104`, `106`)

**Replaced 2026-11-19 (WP8)** by the next section.

**Replaced 2026-11-18 (WP6 stage B).** The table below was the
`wp1f_fullclim_` batch until WP6 B; that table is in git history
(before this commit) and in `docs/run-log.md`, "2026-11-17 WP1 stage F".
The new batch is the code after WP4 (food ledger, debited trade), WP5
(odds-gated war, yearly politics, army stock, camps) and WP6 B
(R_SCALE 0.5, R_MAX 0.03). Ranges across the five seeds, from their
`metrics.json` (`realism.py --group 'runs/wp6b_seed10?'`); timeline rows
from `docs/upgrade/tools/wp6_growth.py`. The `wp1f` column is given for
scale only: it differs from `wp6b` by three packages, not by growth alone.

| Measure | wp6b (current) | wp1f_fullclim (old) |
|---|---|---|
| First city (year) | 565-1,120 | 350-465 |
| 10M people (year) | 2,260-2,795 | 785-900 |
| First steel (year) | 4,995-7,345 | 3,995-7,130 |
| World population at 8000 | 56-97M | 108-178M |
| Growth by millennium, 2000-8000 (%/yr) | 0.010 to 0.065 | -0.005 to 0.064 |
| Log population, sd around 200-yr mean after 3000 | 0.010-0.024 | 0.014-0.040 |
| Largest 100-yr fall after 3000 (log) | -0.20 to -0.11 | -0.32 to -0.07 |
| Plague recovery, years back to 90%, median | 65-90 | (not measured) |
| Herding share, peak | 0.21-0.34, at years 2550-3665 | 0.31-0.37, at 1970-2310 |
| Urban share at the end | 0.046-0.063 | 0.077-0.103 |
| Rank-size slope at the end | -0.56 to -0.46 | -0.38 to -0.36 |
| Largest city, share of world | 0.06-0.13% | 0.07-0.09% |
| Minority share of heads, end | 1.6-2.2% | 0.8-1.5% |
| Polities | 2,329-4,286 | 2,550-5,834 |
| Never above one city | 78-90%; median life 100 yr | 67-76%; 35-100 yr |
| Ended 3+ city states, lifespan | median 204-474 yr; mean 389-767; CV 1.07-1.32; over 1,000 yr 9-23% | median 150-310; mean 275-490; CV 1.1-1.5; 5-12% |
| Largest state | 2.6-5.0M km² (2.1-4.1% of land) | 3.5-7.9M km² (2.9-6.5%) |
| Top-10 states, median land pieces | 2.5-5.5 | 5.5-9.5 |
| Wars | 1,264-6,006 | 1,760-7,383 |
| Wars ending inside one tick / within 5 yr | 7-14% / 51-57% | 65-71% / 81-85% |
| Peer wars | 0.2-0.9% | 1.5-2.4% |
| Sieges taken | 50-53% | 23-24% |
| Siege odds at launch, median (attacker) | 0.40-0.48 | 0.068-0.122 |
| City food: trade / rent / provincial / capital | 0.08-0.11 / 0.44-0.46 / 0.15-0.19 / 0.27-0.33 | 0.35-0.44 / 0.30-0.34 / 0.12-0.16 / 0.13-0.15 |
| Deaths: feud / raid / plague / hunger | 0.46-0.63 / 0.21-0.28 / 0.04-0.20 / 0.02-0.05 | (dragon in the table then; not comparable since WP4 C) |
| Pop share coast or river (land 0.18) | 0.63-0.67 | 0.62-0.65 |
| Pop share alluvial fill (land 0.099) | 0.089-0.116 | 0.082-0.097 |
| Population in a state / land area / land cells | 0.65-0.82 / 0.19-0.33 / 0.12-0.20 | 0.81-0.91 / 0.35-0.52 / 0.22-0.35 |
| Occupied land cells, end | 0.69-0.74 | 0.76-0.81 |
| Elves' share of people, end | 29-56% | 20-69% |

Not remeasured: contingency across seeds (`--cross`). The saved states
for branching (`runs/wp1f_s10{1,3}_y{3000,5000}.pkl`) are from the old
code and should not be used as a baseline any more.

## The baseline batch of WP8 D10 (`wp8d_seed101`-`104`, `106`, 2026-11-19)

**Replaced the same day** by the next section.

These runs use the code after WP8 on the new defaults:

- world `world_v2.gpkg`: climate fields; the climate's biome in place of
  the drawn one everywhere (D10, U); rivers routed on the climate's
  runoff;
- `climate_fields` and `floodplain` on;
- the standard settings.

Ranges are across the five seeds (`realism.py --group 'wp8d_seed10?'`).
Timeline rows come from `docs/upgrade/tools/wp6_growth.py`.

The `wp6b` column is for scale only. It differs from `wp8d` by WP6 C,
WP7 and WP8, not by the world alone, and was run on another machine.
A reference on the old world with the same mechanics is
`wp8_v1_seed101`: one seed, run before `floodplain` became a default, so
the same as `--world v1 --off floodplain` now. It reached 51.7M at 8,000.

The world moved a lot:

- desert covers 36.7M km² against 12.3M drawn;
- river cells fall from 10.7% to 5.4% of land.

| Measure | wp8d (current) | wp6b (previous) |
|---|---|---|
| First city (year) | 670-805 | 565-1,120 |
| 10M people (year) | 3,285-3,700 | 2,260-2,795 |
| First steel (year) | 6,005-7,420 | 4,995-7,345 |
| World population at 8000 | 35-50M | 56-97M |
| Growth by millennium, 2000-8000 (%/yr) | 0.015 to 0.059 | 0.010 to 0.065 |
| Log population, sd around 200-yr mean after 3000 | 0.015-0.024 | 0.010-0.024 |
| Largest 100-yr fall after 3000 (log) | -0.20 to -0.07 | -0.20 to -0.11 |
| Plague recovery, years back to 90%, median | 75-95 | 65-90 |
| Herding share, peak | 0.22-0.35, at years 2110-2990 | 0.21-0.34, at years 2550-3665 |
| Urban share at the end | 0.045-0.062 | 0.046-0.063 |
| Rank-size slope at the end | -0.93 to -0.64 | -0.56 to -0.46 |
| Largest city, share of world | 0.16-0.21% | 0.06-0.13% |
| Minority share of heads, end | 2.4-2.9% | 1.6-2.2% |
| Polities | 1,039-1,795 | 2,329-4,286 |
| Never above one city | 83-89%; median life 100 yr | 78-90%; median life 100 yr |
| Ended 3+ city states, lifespan | median 266-345 yr; mean 483-644; CV 1.14-1.38; over 1,000 yr 13-20% | median 204-474 yr; mean 389-767; CV 1.07-1.32; over 1,000 yr 9-23% |
| Largest state | 2.0-4.0M km² (1.7-3.3% of land) | 2.6-5.0M km² (2.1-4.1% of land) |
| Top-10 states, median land pieces | 2-5.5 | 2.5-5.5 |
| Wars | 409-1,808 | 1,264-6,006 |
| Wars ending inside one tick / within 5 yr | 5-10% / 54-60% | 7-14% / 51-57% |
| Peer wars | 0.1-0.5% | 0.2-0.9% |
| Sieges taken | 46-54% | 50-53% |
| Siege odds at launch, median (attacker) | 0.40-0.51 | 0.40-0.48 |
| City food: trade / rent / provincial / capital | 0.04-0.07 / 0.38-0.44 / 0.16-0.20 / 0.33-0.35 | 0.08-0.11 / 0.44-0.46 / 0.15-0.19 / 0.27-0.33 |
| Deaths: feud / raid / plague / hunger | 0.46-0.53 / 0.33-0.36 / 0.09-0.16 / 0.03-0.04 | 0.46-0.63 / 0.21-0.28 / 0.04-0.20 / 0.02-0.05 |
| Pop share on river cells | 0.35-0.37 (land 0.054) | (not in the table) |
| Pop share coast or river | 0.58-0.63 (land 0.13) | 0.63-0.67 (land 0.18) |
| Pop share alluvial fill | 0.070-0.082 (land 0.024) | 0.089-0.116 (land 0.099) |
| Pop share, \|lat\| 0-15 / 15-30 / beyond 45 | 0.35-0.47 / 0.41-0.48 / 0.014-0.025 (land 0.31 / 0.25 / 0.28) | (not in the table) |
| Population in a state / land area / land cells | 0.68-0.80 / 0.10-0.16 / 0.06-0.10 | 0.65-0.82 / 0.19-0.33 / 0.12-0.20 |
| Occupied land cells, end | 0.62-0.68 | 0.69-0.74 |
| Elves' share of people, end | 35-47% (Dwarves 2-18%) | 29-56% |

Not remeasured: contingency across seeds (`--cross`).

## The baseline batch of the physical refit (`wp8e_seed101`-`104`, `106`, 2026-11-19)

**Replaced 2026-11-20** by the next section.

The code is that of `wp8d`, with three changes asked for by U on
2026-11-19:

- **The climate is refit on physical grounds**, not to the drawn map.
  Only P0 is calibrated, to 1.0 m/yr of global rain.
- **Closed-basin lakes are sized** to their water balance.
- **The resource sites and hearths are placed on `world_v2`**
  (`--sites sites_v3.json`, now in the standard command).

World areas (M km²):

| Biome | `wp8e` | `wp8d` |
|---|---|---|
| Jungle | 19.7 | 15.1 |
| Desert | 1.2 | 36.7 |
| Grassland | 39.6 | 16.4 |
| Temperate forest | 30.0 | 26.8 |
| Tundra | 31.5 | 27.0 |

Rivers and lakes:

- river cells 7.9% of land (`wp8d` 5.4%);
- lake cells 959 (`wp8d` 2,249).

The sites file has 12 hearths of the rule's 13. There are no desert
river cells, so the desert crop hearth finds no cell; the desert animal
hearth is placed.

Ranges are across the five seeds (`realism.py --group 'wp8e_seed10?'`;
timeline rows from `docs/upgrade/tools/wp6_growth.py`).

| Measure | wp8e (current) | wp8d (previous) |
|---|---|---|
| First city (year) | 710-995 | 670-805 |
| 10M people (year) | 2,790-3,220 | 3,285-3,700 |
| First steel (year) | 6,125-6,880; none in 2 of 5 | 6,005-7,420 |
| World population at 8000 | 33-51M | 35-50M |
| Population at 1000 / 4000 / 7000 (M) | 2.4-3.2 / 13.9-19.6 / 24.1-40.7 | 1.9-2.5 / 11.4-14.5 / 22.7-36.6 |
| Growth by millennium, 2000-8000 (%/yr) | -0.017 to 0.054 | 0.015 to 0.059 |
| Largest 100-yr fall after 3000 (log) | -0.23 to -0.07 | -0.20 to -0.07 |
| Plague recovery, years back to 90%, median | 90-125 | 75-95 |
| Herding share, peak | 0.22-0.31, at years 2350-6415 | 0.22-0.35, at years 2110-2990 |
| Urban share at the end | 0.021-0.037 | 0.045-0.062 |
| Rank-size slope at the end | -1.27 to -0.76 | -0.93 to -0.64 |
| Largest city, share of world | 0.05-0.13% (17-63k) | 0.16-0.21% (64-105k) |
| Minority share of heads, end | 2.1-2.8% | 2.4-2.9% |
| Polities | 1,559-2,672 | 1,039-1,795 |
| Never above one city | 90-96% | 83-89% |
| States with 3+ cities | 22-93 | 70-157 |
| Ended 3+ city states, lifespan | median 652-1,862 yr; mean 880-1,878; CV 0.71-1.04; over 1,000 yr 26-62% | median 266-345 yr; mean 483-644; CV 1.14-1.38; over 1,000 yr 13-20% |
| Largest state | 0.6-2.6M km² (0.5-2.1% of land) | 2.0-4.0M km² (1.7-3.3% of land) |
| Top-10 states, median land pieces | 1 | 2-5.5 |
| Wars | 306-1,138 | 409-1,808 |
| Wars ending inside one tick / within 5 yr | 3-8% / 46-56% | 5-10% / 54-60% |
| Peer wars | 0 | 0.1-0.5% |
| Sieges taken | 32-45% | 46-54% |
| Siege odds at launch, median (attacker) | 0.29-0.39 | 0.40-0.51 |
| City food: trade / rent / provincial / capital | 0.02-0.03 / 0.48-0.51 / 0.03-0.12 / 0.38-0.48 | 0.04-0.07 / 0.38-0.44 / 0.16-0.20 / 0.33-0.35 |
| Deaths: feud / raid / plague / hunger | 0.56-0.63 / 0.30-0.32 / 0.03-0.09 / 0.02-0.03 | 0.46-0.53 / 0.33-0.36 / 0.09-0.16 / 0.03-0.04 |
| Pop share on river cells | 0.36-0.38 (land 0.081) | 0.35-0.37 (land 0.054) |
| Pop share coast or river | 0.49-0.57 (land 0.15) | 0.58-0.63 (land 0.13) |
| Pop share alluvial fill | 0.070-0.111 (land 0.053) | 0.070-0.082 (land 0.024) |
| Pop share, \|lat\| 0-15 / 15-30 / beyond 45 | 0.63-0.71 / 0.15-0.23 / 0.017-0.033 | 0.35-0.47 / 0.41-0.48 / 0.014-0.025 |
| Pop share by biome: jungle / grassland / temperate forest / desert / tundra | 0.24-0.38 / 0.30-0.46 / 0.17-0.45 / 0.002 / 0.01-0.02 | 0.27-0.36 / 0.09-0.16 / 0.50-0.60 / 0.02-0.03 / 0.01 |
| Population in a state / land area / land cells | 0.37-0.57 / 0.05-0.11 / 0.03-0.07 | 0.68-0.80 / 0.10-0.16 / 0.06-0.10 |
| Occupied land cells, end | 0.63-0.67 | 0.62-0.68 |
| Largest people at the end | Humans, Snake folk or Dwarves, 31-41% | Elves, 35-47% |
| Elves' share, end | 1-8% | 35-47% |

**What moved.**

- **Peoples.** The Elves lose their lead: 35-47% in `wp8d`, 1-8% now.
  The end shares are more even: the largest people holds 31-41%, and
  it is Humans, Snake folk or Dwarves by seed.
- **States.** Fewer and smaller:
  - fewer states with 3+ cities, and fewer people in states;
  - larger states are compact (top-10 median land pieces 1);
  - states that do form last longer.
- **People move to the equator.** The wet equatorial belt holds 63-71% of
  people, against 35-47% in `wp8d`.

None of these is tuned. Not remeasured: contingency across seeds
(`--cross`).

## The baseline batch of Penman-Monteith PET (`wp8f_seed101`-`104`, `106`, 2026-11-20)

**Replaced the same day** by the next section.

The code is that of `wp8e`, with potential evaporation by FAO-56
Penman-Monteith (U, 2026-11-20: "bring in sunshine & humidity"):

- monthly insolation;
- sunshine from cloud;
- dew-point humidity.

`world_v2` and `sites_v3.json` were rebuilt; the sites file has all 13
hearths, desert crop included.

World areas (M km²):

| Biome | `wp8f` | `wp8e` |
|---|---|---|
| Jungle | 20.4 | 19.7 |
| Desert | 5.0 | 1.2 |
| Grassland | 43.1 | 39.6 |
| Temperate forest | 22.0 | 30.0 |
| Tundra | 31.5 | 31.5 |

Rivers and lakes:

- river cells 6.8% of land (`wp8e` 7.9%);
- lake cells 852 (959).

Run time was about 5,200 s per run against about 650 s for `wp8e`: the
machine was in Low Power Mode on a low battery, not a code change.

| Measure | wp8f (current) | wp8e (previous) |
|---|---|---|
| First city (year) | 685-785 | 710-995 |
| 10M people (year) | 3,115-3,270 | 2,790-3,220 |
| First steel (year) | 5,555-6,760; none in 3 of 5 | 6,125-6,880; none in 2 of 5 |
| World population at 8000 | 34-63M | 33-51M |
| Population at 1000 / 4000 / 7000 (M) | 2.5-3.1 / 11.3-17.5 / 28.8-49.5 | 2.4-3.2 / 13.9-19.6 / 24.1-40.7 |
| Growth by millennium, 2000-8000 (%/yr) | -0.011 to 0.069 | -0.017 to 0.054 |
| Largest 100-yr fall after 3000 (log) | -0.32 to -0.07 | -0.23 to -0.07 |
| Plague recovery, years back to 90%, median | 90-100 | 90-125 |
| Herding share, peak | 0.28-0.35, at years 1485-2740 | 0.22-0.31, at years 2350-6415 |
| Urban share at the end | 0.022-0.048 | 0.021-0.037 |
| Rank-size slope at the end | -1.27 to -0.49 | -1.27 to -0.76 |
| Largest city, share of world | 0.08-0.15% (26-72k) | 0.05-0.13% (17-63k) |
| Minority share of heads, end | 1.4-3.0% | 2.1-2.8% |
| Polities | 1,330-2,922 | 1,559-2,672 |
| Never above one city | 87-95% | 90-96% |
| States with 3+ cities | 20-161 | 22-93 |
| Ended 3+ city states, lifespan | median 464-1,181 yr; mean 593-1,493; CV 0.73-0.90; over 1,000 yr 14-63% | median 652-1,862 yr; mean 880-1,878; CV 0.71-1.04; over 1,000 yr 26-62% |
| Largest state | 0.6-2.5M km² (0.5-2.0% of land) | 0.6-2.6M km² (0.5-2.1% of land) |
| Top-10 states, median land pieces | 1-2 | 1 |
| Wars | 263-3,128 | 306-1,138 |
| Wars ending inside one tick / within 5 yr | 1-8% / 47-63% | 3-8% / 46-56% |
| Peer wars | 0-0.4% | 0 |
| Sieges taken | 30-43% | 32-45% |
| Siege odds at launch, median (attacker) | 0.27-0.37 | 0.29-0.39 |
| City food: trade / rent / provincial / capital | 0.02-0.04 / 0.46-0.55 / 0.05-0.12 / 0.33-0.40 | 0.02-0.03 / 0.48-0.51 / 0.03-0.12 / 0.38-0.48 |
| Deaths: feud / raid / plague / hunger | 0.53-0.61 / 0.26-0.34 / 0.03-0.15 / 0.02-0.03 | 0.56-0.63 / 0.30-0.32 / 0.03-0.09 / 0.02-0.03 |
| Pop share on river cells | 0.32-0.39 (land 0.069) | 0.36-0.38 (land 0.081) |
| Pop share coast or river | 0.46-0.53 (land 0.14) | 0.49-0.57 (land 0.15) |
| Pop share alluvial fill | 0.063-0.107 (land 0.052) | 0.070-0.111 (land 0.053) |
| Pop share, \|lat\| 0-15 / 15-30 / beyond 45 | 0.65-0.73 / 0.14-0.22 / 0.018-0.027 | 0.63-0.71 / 0.15-0.23 / 0.017-0.033 |
| Pop share by biome: jungle / grassland / temperate forest / desert / tundra | 0.20-0.32 / 0.32-0.48 / 0.19-0.41 / 0.003-0.006 / 0.008-0.016 | 0.24-0.38 / 0.30-0.46 / 0.17-0.45 / 0.002 / 0.01-0.02 |
| Population in a state / land area | 0.35-0.69 / 0.04-0.17 | 0.37-0.57 / 0.05-0.11 |
| Occupied land cells, end | 0.65-0.68 | 0.63-0.67 |
| Largest people at the end | Dwarves, Humans or Snake folk, 31-43% | Humans, Snake folk or Dwarves, 31-41% |
| Dwarves' / Elves' share, end | 10-35% / 1-3% | 1-32% / 1-8% |

**What moved.** Little, beside `wp8e`:

- the world is a little drier: more desert, fewer river cells;
- the seeds spread wider (wars 263-3,128; population 34-63M);
- the Dwarves are in the top three in every seed;
- the Elves stay at 1-3%.

None is tuned. Not remeasured: contingency across seeds (`--cross`).

## The baseline batch of the lowered rain-out floor (`wp8g_seed101`-`104`, `106`, 2026-11-20)

**Replaced the same day** by the next section.

The code is that of `wp8f`, with the rain-out factor under sinking air
(`climate_world` Z_BASE) lowered from 0.25 to 0.1 (U, 2026-11-20).
`world_v2` and `sites_v3.json` were rebuilt; all 13 hearths are placed.

| Biome | `wp8g` (M km²) | `wp8f` (M km²) |
|---|---|---|
| Jungle | 22.3 | 20.4 |
| Desert | 22.8 | 5.0 |
| Grassland | 23.4 | 43.1 |
| Temperate forest | 22.0 | 22.0 |
| Tundra | 31.5 | 31.5 |

- **Rain:** subtropical land (20-30°) gets 0.18 m/yr, against 0.31.
  Desert forms belts at about 15-35° on every continent.
- **Rivers and lakes:** river cells 7.0% of land; lake cells 867.

| Measure | wp8g (current) | wp8f (previous) |
|---|---|---|
| First city (year) | 605-1,240 | 685-785 |
| 10M people (year) | 2,915-3,365 | 3,115-3,270 |
| First steel (year) | none in any seed | 5,555-6,760; none in 3 of 5 |
| World population at 8000 | 26-40M | 34-63M |
| Population at 1000 / 4000 / 7000 (M) | 2.6-3.2 / 10.4-19.7 / 22.1-37.8 | 2.5-3.1 / 11.3-17.5 / 28.8-49.5 |
| Growth by millennium, 2000-8000 (%/yr) | -0.014 to 0.066 | -0.011 to 0.069 |
| Largest 100-yr fall after 3000 (log) | -0.23 to -0.08 | -0.32 to -0.07 |
| Plague recovery, years back to 90%, median | 85-100 | 90-100 |
| Herding share, peak | 0.26-0.36, at years 2075-2750 | 0.28-0.35, at years 1485-2740 |
| Urban share at the end | 0.019-0.030 | 0.022-0.048 |
| Rank-size slope at the end | -1.28 to -0.99 | -1.27 to -0.49 |
| Largest city, share of world | 0.06-0.17% (16-60k) | 0.08-0.15% (26-72k) |
| Minority share of heads, end | 2.3-3.0% | 1.4-3.0% |
| Polities | 1,257-1,676 | 1,330-2,922 |
| Never above one city | 94-97% | 87-95% |
| States with 3+ cities | 17-46 | 20-161 |
| Ended 3+ city states, lifespan | median 776-2,102 yr; mean 1,123-2,391; CV 0.59-0.90; over 1,000 yr 41-64% | median 464-1,181 yr; mean 593-1,493; CV 0.73-0.90; over 1,000 yr 14-63% |
| Largest state | 0.5-1.4M km² (0.4-1.2% of land) | 0.6-2.5M km² (0.5-2.0% of land) |
| Top-10 states, median land pieces | 1 | 1-2 |
| Wars | 155-418 | 263-3,128 |
| Wars ending inside one tick / within 5 yr | 3-5% / 52-68% | 1-8% / 47-63% |
| Peer wars | 0-0.2% | 0-0.4% |
| Sieges taken | 34-39% | 30-43% |
| Siege odds at launch, median (attacker) | 0.27-0.33 | 0.27-0.37 |
| City food: trade / rent / provincial / capital | 0.01-0.03 / 0.49-0.56 / 0.02-0.12 / 0.32-0.47 | 0.02-0.04 / 0.46-0.55 / 0.05-0.12 / 0.33-0.40 |
| Deaths: feud / raid / plague / hunger | 0.55-0.63 / 0.32-0.34 / 0.03-0.09 / 0.02-0.03 | 0.53-0.61 / 0.26-0.34 / 0.03-0.15 / 0.02-0.03 |
| Pop share on river cells | 0.38-0.41 (land 0.071) | 0.32-0.39 (land 0.069) |
| Pop share coast or river | 0.49-0.54 (land 0.14) | 0.46-0.53 (land 0.14) |
| Pop share alluvial fill | 0.077-0.100 (land 0.055) | 0.063-0.107 (land 0.052) |
| Pop share, \|lat\| 0-15 / 15-30 / beyond 45 | 0.64-0.81 / 0.09-0.16 / 0.022-0.037 | 0.65-0.73 / 0.14-0.22 / 0.018-0.027 |
| Pop share by biome: jungle / grassland / temperate forest / desert / tundra | 0.31-0.39 / 0.19-0.31 / 0.21-0.44 / 0.03-0.07 / 0.012-0.018 | 0.20-0.32 / 0.32-0.48 / 0.19-0.41 / 0.003-0.006 / 0.008-0.016 |
| Population in a state / land area | 0.29-0.50 / 0.03-0.05 | 0.35-0.69 / 0.04-0.17 |
| Occupied land cells, end | 0.62-0.66 | 0.65-0.68 |
| Largest people at the end | Dwarves or Humans, 24-35% | Dwarves, Humans or Snake folk, 31-43% |

**What moved.**

- **People and land.** There are fewer people (26-40M): grassland, the
  best farm and herd land outside the equator, halves. People crowd
  further onto the equator.
- **States.** Fewer and smaller:
  - 17-46 with 3+ cities;
  - the largest covers 1.2% of land at most;
  - 29-50% of people live in states;
  - states that form last long (median 776-2,102 yr).
- **War and technology.** Wars fall to 155-418, and no seed reaches
  steel.

None is tuned. Not remeasured: contingency across seeds (`--cross`).

## The baseline batch of the monthly circulation (`wp8h_seed101`-`104`, `106`, 2026-11-20)

The code is that of `wp8g`, with three expansions of the climate model
(U, 2026-11-20; [../world-data.md](../world-data.md)):

- **Seasons.** The circulation runs month by month: the ITCZ follows
  the sun, further over land (monsoon), with the trades blowing toward
  it. The ITCZ's half-width is now 5°, its width in one month.
- **Ocean currents.** Gyre currents from basin geometry warm or cool the
  sea, and the wind carries the anomaly inland.
- **Band edges.** Moisture is exchanged across them.

`world_v2` and `sites_v3.json` were rebuilt; all 13 hearths are placed.

| Biome | `wp8h` (M km²) | `wp8g` (M km²) |
|---|---|---|
| Jungle | 24.9 | 22.3 |
| Desert | 5.5 | 22.8 |
| Grassland | 29.3 | 23.4 |
| Temperate forest | 30.8 | 22.0 |
| Tundra | 31.5 | 31.5 |

- **Rain:** subtropical land (20-30°) gets 0.31 m/yr, against 0.18; the
  monsoon wets the subtropics to about 20°.
- **Rivers and lakes:** river cells 8.7% of land; lake cells 1,000.

| Measure | wp8h (current) | wp8g (previous) |
|---|---|---|
| First city (year) | 520-875 | 605-1,240 |
| 10M people (year) | 2,710-3,105 | 2,915-3,365 |
| First steel (year) | 7,460 in one seed; none in 4 | none in any seed |
| World population at 8000 | 31-38M | 26-40M |
| Population at 1000 / 4000 / 7000 (M) | 2.5-3.5 / 13.7-16.7 / 26.4-33.0 | 2.6-3.2 / 10.4-19.7 / 22.1-37.8 |
| Growth by millennium, 2000-8000 (%/yr) | -0.010 to 0.048 | -0.014 to 0.066 |
| Largest 100-yr fall after 3000 (log) | -0.20 to -0.07 | -0.23 to -0.08 |
| Plague recovery, years back to 90%, median | 80-110 | 85-100 |
| Herding share, peak | 0.27-0.42, at years 1710-2610 | 0.26-0.36, at years 2075-2750 |
| Urban share at the end | 0.017-0.029 | 0.019-0.030 |
| Rank-size slope at the end | -1.41 to -0.96 | -1.28 to -0.99 |
| Largest city, share of world | 0.05-0.11% (17-43k) | 0.06-0.17% (16-60k) |
| Minority share of heads, end | 2.2-3.5% | 2.3-3.0% |
| Polities | 1,460-1,806 | 1,257-1,676 |
| Never above one city | 95-98% | 94-97% |
| States with 3+ cities | 10-36 | 17-46 |
| Ended 3+ city states, lifespan | median 515-1,180 yr; mean 781-1,295; CV 0.45-0.92; over 1,000 yr 14-57% | median 776-2,102 yr; mean 1,123-2,391; CV 0.59-0.90; over 1,000 yr 41-64% |
| Largest state | 0.3-1.4M km² (0.3-1.2% of land) | 0.5-1.4M km² (0.4-1.2% of land) |
| Top-10 states, median land pieces | 1 | 1 |
| Wars | 147-368 | 155-418 |
| Wars ending inside one tick / within 5 yr | 2-5% / 50-59% | 3-5% / 52-68% |
| Peer wars | 0 | 0-0.2% |
| Sieges taken | 32-40% | 34-39% |
| Siege odds at launch, median (attacker) | 0.27-0.33 | 0.27-0.33 |
| City food: trade / rent / provincial / capital | 0.01-0.02 / 0.45-0.51 / 0.01-0.09 / 0.40-0.50 | 0.01-0.03 / 0.49-0.56 / 0.02-0.12 / 0.32-0.47 |
| Deaths: feud / raid / plague / hunger | 0.57-0.63 / 0.32-0.35 / 0.03-0.05 / 0.01-0.02 | 0.55-0.63 / 0.32-0.34 / 0.03-0.09 / 0.02-0.03 |
| Pop share on river cells | 0.35-0.41 (land 0.088) | 0.38-0.41 (land 0.071) |
| Pop share coast or river | 0.48-0.53 (land 0.16) | 0.49-0.54 (land 0.14) |
| Pop share alluvial fill | 0.093-0.108 (land 0.059) | 0.077-0.100 (land 0.055) |
| Pop share, \|lat\| 0-15 / 15-30 / beyond 45 | 0.62-0.69 / 0.17-0.22 / 0.025-0.039 | 0.64-0.81 / 0.09-0.16 / 0.022-0.037 |
| Pop share by biome: jungle / grassland / temperate forest / desert / tundra | 0.33-0.47 / 0.20-0.26 / 0.24-0.45 / 0.010-0.013 / 0.013-0.021 | 0.31-0.39 / 0.19-0.31 / 0.21-0.44 / 0.03-0.07 / 0.012-0.018 |
| Population in a state / land area | 0.28-0.43 / 0.03-0.05 | 0.29-0.50 / 0.03-0.05 |
| Occupied land cells, end | 0.63-0.65 | 0.62-0.66 |
| Largest people at the end | Dwarves or Humans, 23-32% | Dwarves or Humans, 24-35% |

**What moved.** Little in the society, though the world changed a lot:

- seeds agree more closely (population 31-38M);
- people spread a little further from the equator, into the monsoon
  subtropics;
- states stay few and small (10-36 with 3+ cities), and wars number
  147-368.

None is tuned. Not remeasured: contingency across seeds (`--cross`).

## The baseline batch of the monsoon westerly and rain timing (`wp8i_seed101`-`104`, `106`, 2026-11-20)

The code is that of `wp8h`, with two more climate changes (U,
2026-11-20; [../world-data.md](../world-data.md)):

- **Monsoon westerly.** Between the equator and a displaced summer ITCZ
  the wind is westerly. It moves July rain −20% to +15% within its zone,
  but no biome area.
- **Rain timing.** A monthly soil-water bucket gives a timing factor.
  The biome rule and the sim's yields (`syn_aridity_season`) read
  aridity times that factor.

`world_v2` and `sites_v3.json` were rebuilt; all 13 hearths are placed.
Biomes (M km²): jungle 23.8 (24.9), desert 5.5 (5.5), grassland 33.9
(29.3), temperate forest 27.3 (30.8), tundra 31.5 (31.5). River cells are
9.0% of land and lake cells 931.

| Measure | wp8i (current) | wp8h (previous) |
|---|---|---|
| First city (year) | 490-810 | 520-875 |
| 10M people (year) | 2,790-2,990 | 2,710-3,105 |
| First bronze / iron (year) | 4,550-5,800 / 5,385-7,420 | 4,380-6,555 / 6,285-7,560 |
| First steel (year) | 6,140 and 6,765 in two seeds; none in 3 | 7,460 in one seed |
| World population at 8000 (M) | 35-57 | 31-38 |
| Population at 1000 / 4000 / 7000 (M) | 2.7-3.4 / 16.6-18.2 / 29.8-42.4 | 2.5-3.5 / 13.7-16.7 / 26.4-33.0 |
| Largest 100-yr fall after 3000 (log) | -0.19 to -0.06 | -0.20 to -0.07 |
| Herding share, peak | 0.26-0.35, at years 2085-2695 | 0.27-0.42, at 1710-2610 |
| Urban share at the end | 0.026-0.042 | 0.017-0.029 |
| Rank-size slope at the end | -1.27 to -0.77 | -1.41 to -0.96 |
| Largest city, share of world | 0.08-0.16% | 0.05-0.11% |
| Polities | 1,865-2,676 | 1,460-1,806 |
| Never above one city | 93-96% | 95-98% |
| States with 3+ cities | 18-64 | 10-36 |
| Ended 3+ city states, lifespan | median 642-1,626 yr; CV 0.63-0.95; over 1,000 yr 36-91% | median 515-1,180 yr; CV 0.45-0.92; over 1,000 yr 14-57% |
| Largest state | 0.8-2.4M km² (0.7-2.0% of land) | 0.3-1.4M km² (0.3-1.2%) |
| Largest state, land pieces | 1-6 | 1 |
| Wars | 289-1,225 | 147-368 |
| Wars ending inside one tick / within 5 yr | 3-6% / 51-59% | 2-5% / 50-59% |
| Peer wars (ended, held-out definition) | 1-12 | 0-7 |
| Sieges taken | 38-45% | 32-40% |
| City food: trade / rent / provincial / capital | 0.01-0.03 / 0.43-0.52 / 0.05-0.11 / 0.38-0.50 | 0.01-0.02 / 0.45-0.51 / 0.01-0.09 / 0.40-0.50 |
| Deaths: feud / raid / plague / hunger | 0.56-0.62 / 0.28-0.33 / 0.04-0.09 / 0.01-0.03 | 0.57-0.63 / 0.32-0.35 / 0.03-0.05 / 0.01-0.02 |
| Pop share on river cells | 0.41-0.43 (land 0.092) | 0.35-0.41 (land 0.088) |
| Pop share coast or river | 0.53-0.61 (land 0.165) | 0.48-0.53 (land 0.161) |
| Pop share, \|lat\| 0-15 / 15-30 | 0.66-0.69 / 0.14-0.19 | 0.62-0.69 / 0.17-0.22 |
| Pop share by biome: jungle / grassland / temperate forest / desert / tundra | 0.35-0.47 / 0.22-0.31 / 0.24-0.37 / 0.007-0.011 / 0.009-0.017 | 0.31-0.45 / 0.24-0.31 / 0.21-0.43 / 0.010-0.013 / 0.013-0.021 |
| Population in a state / land area | 0.41-0.60 / 0.05-0.12 | 0.28-0.43 / 0.03-0.05 |
| Held out: spacing vs density (rho) | -0.62 to -0.48 | -0.70 to -0.51 |
| Held out: state slope, ranks 11-100 (peak / end) | -0.70 to -0.47 / -1.07 to -0.95 | -0.70 to -0.43 / -1.03 to -0.64 |
| Held out: rule spells, p90 / over 500 yr | 400-500 yr / 7-10% | 375-525 yr / 7-10% |
| Held out: traits between a lineage's cities (sd) | 0.009-0.012 | 0.009-0.036 |
| Largest people at the end | Snake folk in 3 seeds (29-34%), Goblins (19%), Dwarves (25%) | Dwarves or Humans, 23-32% |

**What moved.** The society is larger and more political on the same
land:

- population up by about a quarter to a half;
- 18-64 states with 3+ cities, living longer;
- two to three times the wars;
- steel in two seeds.

The likely path (not traced): rain timing turned seasonal jungle into
grassland, which farms at FARM 1.0 against jungle's 0.45. The world
gained farmland where most people already live.

None is tuned. Not remeasured: contingency across seeds (`--cross`).

## The baseline batch of land clearing (`wp8j_seed101`-`104`, `106`, 2026-11-20)

The code is that of `wp8i` with `clearing` on (U, 2026-11-20;
[../structural.md](../structural.md#land-clearing-clearing)):

- farmers clear the forest they work, and herders burn for pasture;
- the cleared share farms, forages and herds at grassland's values;
- unused clearings grow back.

The world file is unchanged. Forest cleared at year 8,000 is
12.9-15.0M km², 25-29% of jungle and temperate forest together.

| Measure | wp8j (current) | wp8i (previous) |
|---|---|---|
| First city (year) | 535-1,035 | 490-810 |
| 10M people (year) | 2,555-2,940 | 2,790-2,990 |
| First bronze / iron (year) | 4,150-6,715 / 4,820-7,405 | 4,550-5,800 / 5,385-7,420 |
| First steel (year) | 5,370-7,000 in three seeds; none in 2 | 6,140 and 6,765 in two |
| World population at 8000 (M) | 40-46 | 35-57 |
| Population at 1000 / 4000 / 7000 (M) | 2.5-4.1 / 17.3-19.3 / 27.0-41.4 | 2.7-3.4 / 16.6-18.2 / 29.8-42.4 |
| Largest 100-yr fall after 3000 (log) | -0.23 to -0.06 | -0.19 to -0.06 |
| Herding share, peak | 0.23-0.31, at years 1835-2530 | 0.26-0.35 |
| Urban share at the end | 0.027-0.043 | 0.026-0.042 |
| Rank-size slope at the end | -1.30 to -0.88 | -1.27 to -0.77 |
| Largest city, share of world | 0.09-0.13% | 0.08-0.16% |
| Polities | 2,118-2,441 | 1,865-2,676 |
| Never above one city | 89-94% | 93-96% |
| States with 3+ cities | 46-117 | 18-64 |
| Ended 3+ city states, lifespan | median 367-967 yr; CV 0.75-1.29; over 1,000 yr 19-44% | median 642-1,626 yr; CV 0.63-0.95; over 1,000 yr 36-91% |
| Largest state | 0.7-1.6M km² (0.6-1.3% of land) | 0.8-2.4M km² (0.7-2.0%) |
| Wars | 697-1,306 | 289-1,225 |
| Wars ending inside one tick / within 5 yr | 4-9% / 50-52% | 3-6% / 51-59% |
| Peer wars (ended, held-out definition) | 3-28 | 1-12 |
| Sieges taken | 41-45% | 38-45% |
| City food: trade / rent / provincial / capital | 0.02-0.04 / 0.43-0.47 / 0.04-0.12 / 0.41-0.48 | 0.01-0.03 / 0.43-0.52 / 0.05-0.11 / 0.38-0.50 |
| Deaths: feud / raid / plague / hunger | 0.58-0.62 / 0.28-0.33 / 0.04-0.10 / 0.01-0.02 | 0.56-0.62 / 0.28-0.33 / 0.04-0.09 / 0.01-0.03 |
| Pop share on river cells | 0.37-0.44 | 0.41-0.43 |
| Pop share, \|lat\| 0-15 / 15-30 | 0.63-0.73 / 0.13-0.19 | 0.66-0.69 / 0.14-0.19 |
| Pop share by biome: jungle / grassland / temperate forest | 0.43-0.55 / 0.22-0.32 / 0.21-0.30 | 0.35-0.47 / 0.22-0.31 / 0.24-0.37 |
| Population in a state / land area | 0.41-0.57 / 0.06-0.10 | 0.41-0.60 / 0.05-0.12 |
| Held out: spacing vs density (rho) | -0.56 to -0.40 | -0.62 to -0.48 |
| Held out: state slope, ranks 11-100 (peak / end) | -0.63 to -0.46 / -1.13 to -0.82 | -0.70 to -0.47 / -1.07 to -0.95 |
| Held out: rule spells, p90 / over 500 yr | 425-500 yr / 8-10% | 400-500 yr / 7-10% |
| Held out: traits between a lineage's cities (sd) | 0.010-0.014 | 0.009-0.012 |
| Largest people at the end | Snake folk in every seed, 18-41% | Snake folk in 3 seeds |

**What moved.**
- **Seeds agree more on population** (40-46M) and less on the timeline
  (first city 535-1,035).
- **States and wars.** Many more states (46-117 with 3+ cities) and
  wars, and states live shorter: their lifespan CV is now 0.75-1.29,
  closer to the exponential reference (Arbesman: CV ~1). S1 is "seen",
  not evidence.
- **Jungle holds more people** (0.43-0.55), since cleared jungle farms at
  2.2x.
- **Steel** in three seeds.

None is tuned. Not remeasured: contingency across seeds (`--cross`).

## The current baseline batch (`wp8k_seed101`-`104`, `106`, 2026-11-21)

The code is that of `wp8j` with two new switches on (U, 2026-11-20:
"prepare the extensions"; [../structural.md](../structural.md)):
- **`clear_terrain`:** cleared forest is crossed and defended as open
  country.
- **`fire`:** foragers burn temperate forest open.

The world file is unchanged. Cleared forest at 8,000 is 14.8-17.4M km²;
the burnt forest peaks at 0.55-1.15M km² and ends at 0.31-0.39M km².

| Measure | wp8k (current) | wp8j (previous) |
|---|---|---|
| World population at 8000 (M) | 44-73 | 40-46 |
| Population at 1000 / 4000 / 7000 (M) | 2.3-3.2 / 18.1-21.2 / 37.8-45.1 | 2.5-4.1 / 17.3-19.3 / 27.0-41.4 |
| First city / 10M (year) | 550-1,400 / 2,655-3,015 | 535-1,035 / 2,555-2,940 |
| First bronze / iron (year) | 4,330-6,505 / 5,035-7,675 | 4,150-6,715 / 4,820-7,405 |
| First steel | 5,720-7,995 in four seeds | 5,370-7,000 in three |
| Urban share at the end | 0.047-0.062 | 0.027-0.043 |
| Rank-size slope at the end | -0.77 to -0.56 | -1.30 to -0.88 |
| Largest city, share of world | 0.10-0.18% | 0.09-0.13% |
| Never above one city | 84-91% | 89-94% |
| States with 3+ cities | 71-174 | 46-117 |
| Ended 3+ city states, lifespan median / CV | 230-752 yr / 1.00-1.43 | 367-967 yr / 0.75-1.29 |
| Largest state (M km²) | 1.2-3.4 | 0.7-1.6 |
| Wars | 1,110-2,076 | 697-1,306 |
| Sieges taken | 38-48% | 41-45% |
| City food from trade | 0.022-0.046 | 0.021-0.038 |
| Deaths: feud / raid | 0.48-0.58 / 0.29-0.32 | 0.58-0.62 / 0.28-0.33 |
| Pop share: river / jungle / grassland / temperate forest | 0.39-0.43 / 0.51-0.60 / 0.19-0.27 / 0.17-0.26 | 0.37-0.44 / 0.43-0.55 / 0.22-0.32 / 0.21-0.30 |
| Population in a state | 0.59-0.75 | 0.41-0.57 |
| Largest people at the end | Snake folk in every seed, 25-45% | the same, 18-41% |

**Which switch** (seed 101; both on / `clear_terrain` only / `fire` only
/ `wp8j`):
- urban share 0.057 / 0.064 / 0.044 / 0.043;
- largest state 1.6 / 2.6 / 1.2 / 1.1M km²;
- states with 3+ cities 144 / 170 / 88 / 117;
- wars 2,076 / 2,442 / 1,489 / 1,306;
- rank-size slope -0.76 / -0.58 / -1.06 / -0.88.

**`clear_terrain` carries the shift.** Cleared farmland is cheaper to
cross and easier to take:
- states reach further and grow larger;
- food carries further, so cities grow and the slope flattens;
- more wars are fought.

`fire` alone stays near `wp8j`.

None is tuned. The sensitivity screen (docs/sensitivity.md) ran on
`wp8j` code; its rankings predate this shift.

## `wp8l`: Earth-check climate fixes (2026-11-21)

**Asked by U (2026-11-21):** "Please implement those climate model
changes." Fixes (a)-(d) of earth-climate-check.md in `climate_world.py`
(world-data.md, "Earth-check fixes"); `world_v2` and `sites_v3.json`
rebuilt. The society code is that of `wp8k`.

**The world changed** (M km²): jungle 23.8 → 28.9, desert 5.5 → 10.2,
grassland 33.9 → 38.0, temperate forest 27.3 → 24.4, tundra 31.5 →
20.5. Land is about 5 °C warmer away from the tropics; land rain 0.89 →
1.02 m/yr.

| Measure | wp8l (current) | wp8k (previous) |
|---|---|---|
| World population at 8000 (M) | 48-87 | 44-73 |
| Population at 1000 / 4000 (M) | 3.1-3.6 / 13.4-20.1 | 2.3-3.2 / 18.1-21.2 |
| First city / 10M (year) | 475-830 / 2,420-3,015 | 550-1,400 / 2,655-3,015 |
| First bronze / iron / steel (year) | 4,615-6,240 / 5,170-7,445 / 5,645-7,390 | 4,330-6,505 / 5,035-7,675 / 5,720-7,995 |
| Urban share at the end | 0.043-0.071 | 0.047-0.062 |
| Rank-size slope at the end | -1.14 to -0.55 | -0.77 to -0.56 |
| Largest city, share of world | 0.14-0.19% | 0.10-0.18% |
| States with 3+ cities | 59-257 | 71-174 |
| Largest state (M km²) | 1.2-2.7 | 1.2-3.4 |
| Wars | 1,019-3,690 | 1,110-2,076 |
| Sieges taken | 39-47% | 38-48% |
| City food from trade | 0.026-0.055 | 0.022-0.046 |
| Pop share: river | 0.36-0.39 | 0.39-0.43 |
| Pop share: \|lat\| 0-15 / 15-30 / 30-45 | 0.54-0.61 / 0.22-0.29 / 0.09-0.16 | 0.71-0.80 / 0.11-0.15 / 0.07-0.13 |
| Pop share: jungle / grassland / temperate forest | 0.53-0.64 / 0.12-0.27 / 0.18-0.24 | 0.51-0.60 / 0.19-0.27 / 0.17-0.26 |
| Population in a state | 0.53-0.80 | 0.59-0.75 |
| Largest people at the end | Snake folk in 4 seeds (22-37%), Lizardfolk in one (33%) | Snake folk in every seed, 25-45% |

**What moved.**
- **Population left the equator**: the 15-30° belt holds 22-29% of
  people, against 11-15%. The jungle spread there, and the warmer
  subtropics farm.
- **Larger totals and a wider spread** between seeds: population 48-87M,
  wars 1,019-3,690, states 59-257. Seed 103 is the high one in each.
- **L2 (population at |lat| 0-15), which no dial moved in the screen,
  moved here** (0.71-0.80 → 0.54-0.61): it is set by the map, as the
  screen said.
- **Snake folk lead less** (22-37%); Lizardfolk lead in seed 102.
  Reported only.

None is tuned.

## `wp8m`: ITCZ by moist static energy (2026-11-21)

**Asked by U (2026-11-21):** "Let's do the bigger fix." Each summer
month the ITCZ moves to the maximum of near-surface moist static energy
(world-data.md, "ITCZ by moist static energy"); `world_v2` and
`sites_v3.json` rebuilt. Society code as `wp8k`.

**The world** (M km²): jungle 28.9 → 28.1, desert 10.2 → 9.5, grassland
38.0 → 37.8, temperate forest 24.4 → 26.1, tundra 20.5 (unchanged).

| Measure | wp8m (current) | wp8l (previous) |
|---|---|---|
| World population at 8000 (M) | 47-70 | 48-87 |
| Population at 1000 / 4000 (M) | 2.6-3.4 / 16.1-19.5 | 3.1-3.6 / 13.4-20.1 |
| First city / 10M (year) | 520-985 / 2,310-2,845 | 475-830 / 2,420-3,015 |
| First bronze / iron / steel (year) | 4,015-5,870 / 4,735-6,945 / 5,215-7,840 | 4,615-6,240 / 5,170-7,445 / 5,645-7,390 |
| Urban share at the end | 0.055-0.066 | 0.043-0.071 |
| Rank-size slope at the end | -0.80 to -0.56 | -1.14 to -0.55 |
| States with 3+ cities | 95-275 | 59-257 |
| Largest state (M km²) | 1.2-2.7 | 1.2-2.7 |
| Wars | 871-2,781 | 1,019-3,690 |
| Sieges taken | 43-48% | 39-47% |
| City food from trade | 0.036-0.060 | 0.026-0.055 |
| Pop share: \|lat\| 0-15 / 15-30 / 30-45 | 0.56-0.58 / 0.25-0.30 / 0.09-0.11 | 0.54-0.61 / 0.22-0.29 / 0.09-0.16 |
| Population in a state | 0.61-0.77 | 0.53-0.80 |
| Largest people at the end | Snake folk in every seed, 30-56% | Snake folk in 4 seeds (22-37%), Lizardfolk in one |

**What moved.** Small changes to the world, and the batch stays within
`wp8l`'s range on most measures, with a narrower spread. Bronze and iron
come 400-600 years earlier at the low end. **Snake folk lead again in
every seed, at 30-56%**, their largest share yet. Reported only (U:
peoples later).

None is tuned.

## `wp8n`: plateau warming (2026-11-21)

**Asked by U (2026-11-21):** "A small cold highland change would be
good." Broad plateaus gain 1 °C per km of elevation smoothed over 300 km
(world-data.md, "Plateau warming"); `world_v2` and `sites_v3.json`
rebuilt. Society code as `wp8k`.

**The world** (M km²): jungle 28.1 → 29.4, desert 9.5 (unchanged),
grassland 37.8 → 37.9, temperate forest 26.1 → 26.0, tundra 20.5 →
19.2. Land 0.7 °C warmer.

| Measure | wp8n (current) | wp8m (previous) |
|---|---|---|
| World population at 8000 (M) | 52-81 | 47-70 |
| Population at 1000 / 4000 (M) | 2.9-3.3 / 17.7-20.6 | 2.6-3.4 / 16.1-19.5 |
| First city / 10M (year) | 555-1,475 / 2,555-2,760 | 520-985 / 2,310-2,845 |
| First bronze / iron / steel (year) | 4,675-6,260 / 4,905-7,325 / 5,130-7,010 | 4,015-5,870 / 4,735-6,945 / 5,215-7,840 |
| Urban share at the end | 0.047-0.059 | 0.055-0.066 |
| Rank-size slope at the end | -0.74 to -0.57 | -0.80 to -0.56 |
| States with 3+ cities | 73-174 | 95-275 |
| Largest state (M km²) | 1.6-1.9 | 1.2-2.7 |
| Wars | 1,004-3,607 | 871-2,781 |
| Sieges taken | 41-45% | 43-48% |
| City food from trade | 0.032-0.049 | 0.036-0.060 |
| Pop share: \|lat\| 0-15 / 15-30 / 30-45 | 0.52-0.70 / 0.20-0.33 / 0.06-0.12 | 0.56-0.58 / 0.25-0.30 / 0.09-0.11 |
| Largest people at the end | Snake folk in 4 seeds (27-33%), Humans in one (36%) | Snake folk in every seed, 30-56% |

**What moved.** Population ends higher (52-81M), and fewer states reach
3+ cities. Most measures overlap `wp8m`'s range. **Snake folk's lead
shrank**: 27-33% in four seeds, and Humans lead seed 102 with 36%.
Reported only (U: refine the world first; don't tune peoples).

**Empty land** (measured on `wp8m`, 2026-11-21): settlement reaches
87-88% of land by year 6000 and stops; the 12% never settled is mostly
tundra. Settled land is thin: median 0.1 people per km² on grassland,
0.12-0.14 in temperate forest. Taken up as WP11.
