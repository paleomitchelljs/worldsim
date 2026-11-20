# Patterns a run is judged on (WP9 stage A, frozen 2026-11-20)

This list is fixed **before** the sensitivity screen (WP9 stage B) and
before any later batch is read. Adding a pattern later is allowed, but it
must be dated and marked as added after the fact. Dropping one or
changing its definition is not allowed.

Rules (U, `README.md`; GUIDE):

- **Judge on variance.** For every pattern, read the range across seeds
  first. A run is unrealistic when diversity collapses or explodes, not
  when a mean misses a reference.
- **References are rough orders of magnitude, never targets.** No value
  may be chosen to move a pattern toward its reference.
- **A pattern that has been used to choose a value is spent.** It can no
  longer count as evidence for the model. Column "Status" says which:
  - **spent**: a value or form was picked after reading it;
  - **seen**: read while a lever was tried, but nothing was adopted on it;
  - **held out**: no one has chosen anything on it.

Every definition is a function in `wsim/metrics.py`, named `function:
key`. `realism.py --group 'NAME_seed10?'` prints them with the range
across seeds. Ranges in the last column are the current baseline,
`wp8h_seed101`-`104` and `106` (8,000 years).

## Population and timeline

| # | Pattern | Definition | Reference (source; how rough) | Scale | Status | wp8h range |
|---|---|---|---|---|---|---|
| P1 | World population at the end | `population` | none for a fantasy world | world | **spent**: development 0.25 picked on population at 6,000 (2026-10-30); D7 read it (2026-11-18) | 31-38M |
| P2 | Timeline: first city, 10M people, metals | `wp6_growth.py`; `population` | first cities ~5,000 years after farming (order of magnitude) | world | **spent**: D7 (R_SCALE 0.5, R_MAX 0.03) chosen on these, U, 2026-11-18; development 0.25 also read metal dates | first city 520-875; 10M at 2,710-3,105; steel in 1 of 5 |
| P3 | Long-run growth | `growth` | 0.04-0.1%/yr pre-modern (McEvedy and Jones 1978; rough) | world | seen (realism review) | -0.010 to 0.048%/yr by millennium |
| P4 | Volatility and recovery | `volatility`, `landmass_volatility`; recovery from `wp6_growth.py` | crises of tens of percent over a century or two are common (Turchin and Nefedov 2009; rough) | world, landmass | **spent**: D7 read recovery times | largest 100-yr fall -0.20 to -0.07 (log); recovery 80-110 yr |
| P5 | Urban share | `population: urban share` | 5-15% pre-modern (Bairoch 1988; rough) | world | **spent**: FF_RENT and FF_TRADE set with urban share 0.17 vs 0.11 in view (2026-11-09) | 0.017-0.029 |

## Cities

| # | Pattern | Definition | Reference | Scale | Status | wp8h range |
|---|---|---|---|---|---|---|
| C1 | Rank-size slope | `city_hierarchy` | about -1; pre-modern -0.6 to -1 (Zipf; de Vries 1984; rough) | world | **seen**: the capital levers FF_TAX, FF_CAP_KM, FF_ABS were tried against it (2026-11-09) and not adopted | -1.41 to -0.96 |
| C2 | Largest city, share of world, and against the 10th | `city_hierarchy` | 0.2-0.5% of world population (Chandler 1987; rough) | world | **seen**: as C1 ("put the largest city in the reference range"; levers not adopted) | 0.05-0.11% |
| C3 | Where city food comes from | `food` | towns lived mostly on rent and tax, trade-fed cities the exception (qualitative) | city | **spent**: FF_RENT 0.12, FF_TRADE 0.003 chosen on the mix (2026-11-09) | trade 0.01-0.02, rent 0.45-0.51, capital 0.40-0.50 |
| C4 | City turnover | `city_lives` | none | city | held out | 88-92% of cities ended, nearly all abandoned |
| C5 | City spacing against local density | `spacing` | central-place theory: denser land, closer towns (Christaller 1933; sign only) | city | **held out** (new) | rho -0.70 to -0.51; nearest city median 229-278 km |
| C6 | Ports and river towns by size class | `waterside` | larger cities more often on navigable water (Bairoch 1988; qualitative) | city | **held out** (new) | coast or river, small / middle / large thirds: 0.87-1 / 0.86-0.97 / 0.87-0.97 |

## States and war

| # | Pattern | Definition | Reference | Scale | Status | wp8h range |
|---|---|---|---|---|---|---|
| S1 | State lifespans (3+ cities) | `lifespans` | mean ~200-250 yr, roughly exponential, CV ~1 (Arbesman 2011) | state | seen: the 2026-11-06 turnover sweep read it; no setting adopted | median 515-1,180 yr; CV 0.45-0.92 |
| S2 | Size of the largest states | `states` | 3% (Rome) to 16% (Mongols) of land (Taagepera 1978, 1997) | state | held out | 0.3-1.2% of land |
| S3 | Heavy-tailed state sizes (top) | `states: skew of log peak cells` | roughly log-normal (Taagepera 1997) | state | held out | skew -0.41 to 0.89 |
| S4 | Size distribution below the top ten | `minor_states` | none; judge on spread | state | **held out** (new) | slope, ranks 11-100: peak -0.70 to -0.43, end -1.03 to -0.64 |
| S5 | One-city states | `states: never above one city` | none | state | held out | 95-98% |
| S6 | How long a region stays under one state | `rule_spells` | none; judge on spread | cell | **held out** (new) | median 100 yr; p90 375-525 yr; over 500 yr 7-10% |
| S7 | Contiguity of large states | `contiguity` | land empires mostly one block; sea empires scattered (qualitative) | state | held out | top-10 median pieces 1 |
| W1 | War count and frequency | `wars`, `war_time` | great powers at war in most years (Levy 1983); uncertain for city-state systems | world | **spent**: WAR_BASE 0.12 chosen on war and capture counts (2026-10-30) | 147-368 wars |
| W2 | How wars end; siege odds | `wars`, `sieges` | none | war | **spent**: the gate's form chosen over the flat floor on long-odds wars and wars without a siege (WP5 B, 2026-11-18) | one-tick 2-5%; sieges taken 32-40% |
| W3 | Durations of wars between peers | `peer_wars` | Levy 1983 for great powers (rough) | war | **held out** (new) | 0-7 peer wars per run: too few to read |

## Land and settlement

| # | Pattern | Definition | Reference | Scale | Status | wp8h range |
|---|---|---|---|---|---|---|
| L1 | People on rivers, coasts, alluvium | `settlement` | early dense populations on floodplains (qualitative) | world | held out | river cells 0.35-0.41 of people on 0.088 of land |
| L2 | People by latitude and biome | `settlement` | none for this world | world | held out | \|lat\| 0-15: 0.62-0.69 |
| L3 | Biome areas of the world file | `climate_fit.json` | the drawn map (`fic_biome`) | world | **spent**: the first climate fit was fitted to the drawn map (removed 2026-11-19); Z_BASE lowered by U after the desert area was read (2026-11-20) | desert 5.5M km² |
| L4 | Land in states, occupied land | `settlement` | none | world | held out | 0.03-0.05 of land in a state |

## Peoples and culture

| # | Pattern | Definition | Reference | Scale | Status | wp8h range |
|---|---|---|---|---|---|---|
| K1 | Shares of peoples | people shares (`timeseries.csv`) | none: there is no "ought" | people | **spent**: rosters rebalanced on shares (bal runs, 2026-10-29) | largest 23-32% |
| K2 | Trait spread between peoples; pinning at bounds | `price`; the grid measures (run-log 2026-11-01) | must not collapse (principle) | people | **spent**: PATH_MIN 0.6, EXP_SCALE 0.5 and KIN_RAID 0.1 chosen so spread survives (allowed by the principles, but spent) | not read on wp8h |
| K3 | Spread between the cities of one lineage | `lineage_cities` | none; judge on spread | lineage | **held out** (new); the 2026-11-02 records read the spread by people and by state, not by lineage | 0.009-0.036 (between lineages of a people: 0.073-0.102) |
| K4 | Turnover of peoples in cells | `turnover` | none | cell | held out | 1.4-2.2% of cells per 500 yr after 3,500 |
| K5 | Contingency across seeds | `metrics.cross` | none; the question `BASELINE.md` raises | world | held out | not remeasured on wp8h |

## Notes

- **The new patterns (C5, C6, S4, S6, W3, K3)** are measured, not judged.
  Their ranges above are the first reading. Their constants
  (SPACING_KM 300, PEER_RATIO 0.5) are C, set before any reading.
- **W3 cannot discriminate now.** With 10-36 states of 3+ cities, peer
  wars are almost absent, so the duration of wars between peers can only
  be read where states are larger.
- **S6's median is exactly 100 years in every seed.** That is likely the
  one-city states abandoned at the first tick URBAN_GRACE allows
  (run-log 2026-11-09). Read the p90 and the share over 500 years
  instead.
- **Spent patterns stay in the list.** They are still printed, because
  a sudden change in one is news. They do not count as evidence that the
  model is right.
