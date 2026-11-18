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

## The new baseline batch (`wp1f_fullclim_seed101`-`104`, `106`)

Ranges across the five seeds, from their `metrics.json`
(`realism.py --group 'wp1f_fullclim_seed10?'`). Contingency is over the
ten pairs (`realism.py --cross`).

| Measure | Range |
|---|---|
| World population at 8000 | 108-178M |
| Growth by millennium, 2000-8000 (%/yr) | -0.005 to 0.064; each millennium spans 0.02-0.05 across seeds |
| Log population, sd around 200-yr mean after 3000 | 0.014-0.040 |
| Largest 100-yr fall after 3000 (log) | -0.32 to -0.07 |
| Herding share, peak | 0.31-0.37, at years 1970-2310 |
| Urban share at the end | 0.077-0.103 |
| Rank-size slope at the end | -0.38 to -0.36 |
| Largest city, share of world | 0.07-0.09% |
| Minority share of heads, end | 0.8-1.5% |
| Polities | 2,550-5,834 |
| Never above one city | 67-76%; median life 35-100 yr |
| Ended 3+ city states, lifespan | median 150-310 yr; mean 275-490; CV 1.1-1.5; over 1,000 yr 5-12%; longest 2,960-4,245 |
| Largest state | 3.5-7.9M km² (2.9-6.5% of land) |
| Top-10 states, median land pieces / groups joined by sea | 5.5-9.5 / 1-2 |
| Wars | 1,760-7,383 |
| Wars ending inside one tick / within 5 yr | 65-71% / 81-85% |
| Wars with 0-1 sieges | 54-60% |
| Peer wars | 1.5-2.4% |
| Sieges taken | 23-24% |
| Siege odds at launch, median: attacker / counter-offensive | 0.068-0.122 / 0.006-0.022 |
| ... share under 0.1: attacker / counter-offensive | 46-55% / 82-90% |
| States at war, by millennium after 3000 | 0.03-0.11 |
| City food: trade / rent / provincial / capital | 0.35-0.44 / 0.30-0.34 / 0.12-0.16 / 0.13-0.15 |
| Deaths: dragon / feud / raid / hunger / plague | 0.56-0.64 / 0.17-0.22 / 0.07-0.10 / 0.02-0.06 / 0.02-0.11 |
| Pop share coast or river (land 0.18) | 0.62-0.65 |
| Pop share alluvial fill (land 0.099) | 0.082-0.097 |
| Population in a state / land area / land cells | 0.81-0.91 / 0.35-0.52 / 0.22-0.35 |
| Same people, cell by cell (chance) | 0.57-0.73 (0.21-0.27) |
| City sites within one cell (chance) | 0.45-0.76 (0.08-0.12) |
| Correlation of log(1 + cell population) | 0.91-0.94 |

Against `al_seed103`, which ran with different levers: city food leans
more on trade and rent and less on the capital's take, and the defender
falls far less often when it holds 5+ cities (0.01-0.08 against 0.11).
