# WP6: growth and recovery

**Goal.** Population that can fall behind its land and take generations to
recover, so that crises last and regions differ in more than their
carrying capacity.

**Evidence** (`BASELINE.md`).
- `land.grow`: `r = Lr x (0.6 + 0.4 x agri) x front`, with
  `front = 1 + 1.5 x clip(1 - 2p/K, 0, 1)`. Roster growth rates run from
  0.017 (Giants) to 0.024 (Humans) a year, so thinly settled land grows at
  up to 4-6% a year. Pre-modern populations are not known to have sustained
  much above about 3% a year, even on open frontiers (C; from memory, not
  checked against a source).
- At `p > K/2` Humans recover from a 30% loss in roughly 60-90 years.
- World population varies by 2.3% (log sd) around its 200-year mean after
  year 3000. Only two of six seeds in the realism batch had a slow fall.
- Long-run growth after year 3000 is 0.02-0.05% a year, inside the
  reference range; that comes from technology raising capacity, and is
  not what this package changes.

So population tracks capacity almost exactly, and the history of
population is the history of K.

Read first: `wsim/land.py` (`grow`, `famine`, `logistic` in `geo.py`),
`docs/rules/population.md`, `docs/traits/intrinsic.md`,
`docs/startup.md`, the rosters (`peoples_balanced.py`,
`peoples_regional.py`), the realism review item on intrinsic r
(`../reviewdocs/REALISM_REVIEW.md`, "Outputs to add", 2).

This is a small package, but it moves the whole timeline, so it starts as
an experiment.

## Stage A: experiment batch (needs U: D7 only to adopt, not to test)

1. Make the two hard-wired numbers constants:
   `FRONT_K` (1.5) and the half-capacity point (the `2` in `2p/K`). Add
   `R_SCALE` (1.0), a multiplier on every lineage's growth rate, and
   `R_MAX` (no cap), a ceiling on the effective yearly rate.
2. One run each of seed 101, 8,000 years (a second seed if two settings
   are hard to tell apart):
   - baseline;
   - `R_MAX = 0.03`;
   - `R_SCALE = 0.5`, `R_MAX = 0.03`;
   - `R_SCALE = 0.33`, `R_MAX = 0.02`.
   Rosters stay as written: the ratios between peoples are the user's.
3. Measure:
   - the year of the first city per people, of 1M and 10M people, and of
     bronze, iron and steel (how far the timeline stretches);
   - recovery: for each plague that kills over 10% of a state, years until
     its cells are back to 90% of their earlier population;
   - log-population sd around the 200-year mean, world and per landmass
     group; the largest 100- and 300-year falls;
   - whether a fall reaches the cities (`realism.py`'s "cities, change
     over worst fall");
   - shares of each people by millennium, and the spread between peoples
     (slow breeders may be squeezed further; Trolls, Ogres and Giants are
     already under 1%);
   - land occupied by year, and the head-start arrivals (`place_arrivals`):
     do late peoples still find empty land?
4. Report the table and a recommendation. Say plainly what each setting
   costs in timeline. If slower growth means steel arrives after year
   8000, that conflicts with "steel as the final technology over 8,000
   years is intended" (U, 2026-11-09): put that to the user as the
   trade-off, with the option of longer runs.

## Stage B: adopt (needs U: D7)

1. Set the chosen values as defaults; update `docs/rules/population.md`
   and `docs/model-description.md` with provenance U->C.
2. If the timeline stretched, update the default `--years`, the
   head-start guidance in `docs/running.md` and `docs/startup.md`.
3. Rerun the baseline (a run or two) and replace the baseline table in
   `docs/run-log.md` and `BASELINE.md`.

## Not in this package

- Age structure or explicit births and deaths. If recovery is still too
  fast or too smooth after this, the next step is lagged capacity
  (destroyed improvements and herds taking decades to rebuild, which
  `imp`, `land` and `waste` partly do already), not a cohort model.
- Disease. Plague reaches only cells inside states (`land.disasters`
  masks by polity), so the 11% of people outside states never catch it.
  Note it in `docs/open-questions.md`; do not fix it here.
