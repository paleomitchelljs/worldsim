# WP12 stage B: design note (2026-11-21)

For U to decide before any code. Measures are from stage A,
`tools/wp12_trace.py` on seeds 101 and 103 (8,000 years, the `wp13b`
rules, records every 25 years): `baseline/wp12a_falls_seed101.md`,
`baseline/wp12a_falls_seed103.md` and their charts. Every proposal and
number here is C.

**Decided (U, 2026-11-22, D16):** the recommendations. Build A
(`works_lag`, IMP_HANDS 0.85 as WORKS_HANDS); hold B; measure C first
(added to `wp12_trace.py`); a later steel is reported, not tuned back.
Then (U, 2026-11-22): build B too. It is `rural_onset`, off unless
`--on` until its batch is read; PL_RURAL 2e-6, PL_D_ON 5 (C).

## What stage A shows

### Falls in landmass groups

A fall is a drop below 80% of the running peak; recovery is the years
from the trough back to 90% of the peak.

| Seed | Group | Peak year | Depth | Peak to trough (yr) | Trough to 90% (yr) | Cause (excess deaths, share of peak) | Capacity fall |
|---|---|---|---|---|---|---|---|
| 101 | E | 4625 | 0.20 | 25 | 100 | plague 0.20 | +0.13 |
| 101 | E | 5200 | 0.20 | 75 | 175 | plague 0.19 | -0.04 |
| 101 | E | 6425 | 0.24 | 50 | 150 | plague 0.29 | -0.01 |
| 101 | E | 7450 | 0.22 | 25 | 200 | plague 0.24 | -0.02 |
| 103 | E | 5600 | 0.22 | 50 | 125 | plague 0.23 | -0.05 |
| 103 | E | 6400 | 0.29 | 25 | 125 | plague 0.30 | +0.01 |
| 103 | E | 6825 | 0.21 | 25 | 75 | plague 0.24 | -0.02 |

- **Every real fall is a plague in E**, the most crowded group (fill
  0.6). S, W and N never fall 20% in either seed.
- **Depth 0.20-0.29, crash in 25-75 years, back to 90% in 75-200
  years.** That is three to eight generations, but at the scale of a
  landmass it shows as a notch in the curve, not a dark age (charts).
- **Plague deaths match the depth.** The excess plague deaths (0.19-0.30
  of the peak) are about the whole fall. Feud and raids add 0.00-0.04.
- **Capacity does not fall with the people** (-0.05 to +0.13; one case
  above 0.05). Nothing lags.
- **No fall comes from war, hunger, or climate.**
- The two X falls (3200, 3300; "clearance", depth 0.43-0.51) are an
  artefact. X is first settled then by a few hundred people, and the
  label was the largest of all-zero shares. They are left out above.

### Falls in states

States with 3+ cities at their peak and 200+ years of records.

| Label | Falls (101 / 103) | Median depth | Recovered | Median years to 90% |
|---|---|---|---|---|
| land lost | 77 / 129 | 0.44 / 0.42 | 0.53 / 0.60 | 125 / 75 |
| plague | 10 / 12 | 0.27 / 0.23 | 1.00 / 0.92 | 100 / 75 |
| feud | 2 / 0 | 0.30 | 1.00 | 50 |
| ravage | 1 / 0 | 0.21 | 1.00 | 25 |

- **86-91% of state falls are land lost.** A state loses cities to
  conquest or revolt, and the people pass to another ruler. They do not
  die, so state falls leave no mark on the landmass curve.
- About half of these never recover: the state ends first.
- Plague falls in states are shallower and nearly all recover.

### Time below capacity

| Group | Median fill after 3000 (101 / 103) | Records under 0.8 | Records under 0.8 x own median |
|---|---|---|---|
| S | 0.34 / 0.25 | 1.00 / 1.00 | 0.12 / 0.04 |
| W | 0.31 / 0.32 | 1.00 / 1.00 | 0.10 / 0.28 |
| N | 0.49 / 0.58 | 1.00 / 0.97 | 0.27 / 0.13 |
| E | 0.59 / 0.62 | 1.00 / 0.98 | 0.01 / 0.06 |
| X | 0.22 / 0.23 | 1.00 / 1.00 | 0.26 / 0.24 |

- **"Under 0.8" is always true and says nothing.** WP11 B found
  people held at 0.3-0.6 of raw capacity in a steady state of growth
  against deaths (feud, raids, plague).
- **"Under 0.8 x own median" measures the trend, not crises.** Fill
  rises through the whole run in every group (chart, lower panel), so
  the early records after 3000 fall below the median. E has all the
  plagues and the smallest share (0.01-0.06).
- In short, the world spends no measurable time in depression.

## Why falls are short

1. **The steady state pulls people back.** In a logistic with deaths
   proportional to people, the settled level is about
   k x (1 - deaths / growth). A cull lowers the people but not k. Growth
   is then faster and the death rate the same, so the curve climbs back
   to where it was. Only a fall in k, or in growth against deaths, moves
   the level itself.
2. **Works do not fall after a plague.** `upkeep` adds decay only
   where a cell's people drop below IMP_HANDS (0.7) of their 50-year
   mean. An epidemic kills PL_MORT 0.15-0.35 of a cell, less for the
   immune (IMP_PROTECT 0.8). Most struck cells stay above 0.7, so their
   works never lapse. (This is read from the parameters, not measured.)
   Rebuilding, by contrast, is already slow: IMP_BUILD 0.003 a year x
   use x (0.5 + admin) x (0.5 + patience), a time constant of centuries.
   So the lag is there, but nothing triggers it.
3. **Losing a state costs no lives.** Cells that change ruler keep
   their people, their works, and (if they pass to another state) their
   order.
4. **Plague begins only in cities.** Onset needs a city community near
   PL_CCS (3e4) and is raised by trade, so plagues start where the
   cities are: E. Spread is already rural (WP6 C: cell to cell by
   density; stateless people catch it). The brief's option 2 is
   therefore half built.

## Proposals

### A. Works that lapse after any loss of hands (`works_lag`)

The brief's "lagged capacity", built on what exists.

**Rule.** With the switch on, `upkeep` decays works for any shortfall
below the 50-year mean (IMP_HANDS 0.7 to 1.0, C), not only below 70%
of it. Cleared land already shrinks toward the land in use (`clearing`)
and grows back at CLEAR_REGROW. Nothing else changes; rebuilding is as
now. A middle choice is IMP_HANDS 0.85.

**Expected (C, rough).** Take a 25% plague in improved farmland. The
lapse starts at 0.1 x 0.25 = 0.025 a year and shrinks as the mean
catches up. Over about 50 years works lose perhaps a third. That is
roughly 5-10% of capacity on rain-fed land (IMP_RAIN 0.3) and more on
irrigated land (IMP_IRR0 0.4). It takes centuries to rebuild. The
settled level follows k, so recovery to 90% could go from 75-200 years
to 150-400, and E's falls would deepen a little.

**Risks.**
- **A ratchet.** Every dip, from raids, feud or noise, now costs
  works. Works stay lower on average, so the world holds fewer people
  everywhere, not only after crises. The 50-year mean smooths noise,
  but the level effect could be a few percent of world population.
- **The timeline.** Fewer people and fewer cities may delay metals. In
  `wp10c` steel comes between 5,130 and 7,685, so a delay of a few
  centuries pushes some seeds past 8000.
- It acts only where there are works: farmland, mostly E and the river
  valleys. Herders' cells are excluded as now.

### B. Plague that starts outside cities (`rural_onset`)

The brief's "plague not tied to city size", reduced to what is missing.

**Rule.** Add an onset term per cell, not per city: PL_RURAL x
min(1, people per km2 / PL_D_ON), for every occupied cell, herders
included (a reservoir in herds or wild rodents). The term works
alongside the city onset. Mortality, spread and immunity are as now.

**Expected (C).** Outbreaks in S, W and N, and before cities exist. On
thin land the density-based spread (PL_BETA x d / (d + PL_D0)) will
not carry them far, so most stay small. Where they do spread, they
recover as the E plagues do. The result is more notches, not longer
ones, so it adds frequency rather than duration.

**Risks.**
- More plague deaths every century lower the steady state everywhere,
  as A does.
- Early outbreaks hit small founding populations, so expansion and the
  timeline may slow.
- Immunity built in the countryside would blunt later city plagues.

### C. Disorder after a fall of state (`collapse_cost`), from stage A

Not in the brief. Stage A suggests it, because most state falls cost
no lives.

**Rule.** A cell whose state ends, or that changes ruler by revolt or
conquest, carries a disorder share starting at 1 that decays over
CHAOS_YEARS (C: 50). While it lasts:
- order in `feud` is multiplied by (1 - disorder), so feud rises;
- building works is multiplied by (1 - disorder), which ties into A;
- the cell is open to raids as if stateless.

**Expected (C).** State falls cost people. A cascade of falls, such as
a large state breaking apart, would leave a landmass emptier for a
century or more. This is the closest the model can come to a Bronze Age
collapse or the post-Roman West.

**Risks.**
- **It feeds on war.** `wp13b` has 919-8,258 wars per run, so
  seeds with many wars would depopulate and could stall.
- It is a new mechanism with three couplings. It is the hardest of the
  three to read in the results.
- **Measure first.** Before building, extend `wp12_trace.py` to record
  excess deaths and the change in fill in cells that change hands. It
  is a records-only stage on two seeds. If disorder already costs
  lives (for example through raids on newly stateless cells), C may not
  be needed.

### Not proposed

- **Climate crises.** CLIM_AMP did not move P4 in the screen, and U has
  settled the physical model. Long droughts would be a change to the
  world, not to the peoples (U: refine the physical world first, and
  do not tune peoples to counter it). They could be revisited as a physical change if A-C leave no
  dark ages.
- **Tuning plague mortality or FEUD_K** to make deeper falls. That
  sets a target rather than adding a cause.

## Measures for stage C

- The stage A tables on five seeds: group and state falls, depth, and
  years to 90%.
- Replace "time below capacity" with fill below 0.8 x its own 500-year
  running median. This removes the trend.
- P2-P4 from `patterns.md`, world population at 8000, and first
  bronze, iron and steel, against `wp13b`.

## For U

1. **A (`works_lag`)**: build it, with IMP_HANDS 1.0 or 0.85?
   Recommended: build it, at 0.85. It is the cheapest change, uses
   existing rules, and lengthens recovery where it matters.
2. **B (`rural_onset`)**: build or hold? Recommended: hold. Spread is
   already rural, and B adds more dips, not longer ones.
3. **C (`collapse_cost`)**: measure first (a records-only addition to
   stage A), build directly, or drop? Recommended: measure first.
4. **The timeline**: is steel after 8000 in some seeds acceptable if A
   (or C) delays metals? If not, stage C would report the delay and
   stop, rather than tune it back.

## Built (stage C, 2026-11-22)

A is `works_lag` (on by default) and B is `rural_onset` (optional). C was
measured, not built. Results are in run-log.md (2026-11-22) and STATUS.
In short: neither A nor B lengthens recovery from a plague (50-300
years to 90%). B spreads plague falls beyond E. A fall of state already
costs a cell about 8% of its heads over the next century.

Then (U, 2026-11-22): `rural_onset` a default and C built as
`collapse_cost` (`wp12e`). It barely changes what follows a change of
hands; three landmass falls now last 375-425 years. See run-log.md.

